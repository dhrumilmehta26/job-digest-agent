"""
Database operations for Job Aggregator.
Handles CRUD operations, deduplication, and cleanup.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo import UpdateOne, DESCENDING
from pymongo.errors import DuplicateKeyError, BulkWriteError

from .models import JobModel


class JobOperations:
    """Handle all job-related database operations."""
    
    def __init__(self, database: Database):
        """
        Initialize with database connection.
        
        Args:
            database: MongoDB database instance
        """
        self.db = database
        self.collection: Collection = database[JobModel.COLLECTION_NAME]
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Create indexes if they don't exist."""
        try:
            existing_indexes = self.collection.list_indexes()
            existing_names = {idx['name'] for idx in existing_indexes}
            
            for index_spec in JobModel.get_indexes():
                keys = index_spec['keys']
                name = '_'.join(f"{k}_{v}" for k, v in keys)
                
                if name not in existing_names:
                    self.collection.create_index(
                        keys,
                        unique=index_spec.get('unique', False),
                        background=True
                    )
            
            print("   ✓ Database indexes verified")
            
        except Exception as e:
            print(f"   ⚠ Index creation warning: {e}")
    
    def insert_job(self, job: Dict[str, Any]) -> Optional[str]:
        """
        Insert a single job.
        
        Args:
            job: Job document
        
        Returns:
            Inserted ID or None if duplicate
        """
        try:
            doc = JobModel.create(job)
            result = self.collection.insert_one(doc)
            return str(result.inserted_id)
        except DuplicateKeyError:
            return None
        except Exception as e:
            print(f"   ⚠ Insert error: {e}")
            return None
    
    def upsert_jobs(self, jobs: List[Dict[str, Any]]) -> Tuple[int, int, int]:
        """
        Upsert multiple jobs (insert or update).
        
        Args:
            jobs: List of job documents
        
        Returns:
            Tuple of (inserted_count, updated_count, failed_count)
        """
        if not jobs:
            return (0, 0, 0)
        
        operations = []
        
        for job in jobs:
            try:
                doc = JobModel.create(job)
                operations.append(
                    UpdateOne(
                        {'job_id': doc['job_id']},
                        {
                            '$set': doc,
                            '$setOnInsert': {'first_seen': datetime.utcnow()}
                        },
                        upsert=True
                    )
                )
            except ValueError as e:
                print(f"   ⚠ Skipping invalid job: {e}")
                continue
        
        if not operations:
            return (0, 0, 0)
        
        try:
            result = self.collection.bulk_write(operations, ordered=False)
            inserted = result.upserted_count
            updated = result.modified_count
            return (inserted, updated, 0)
        except BulkWriteError as e:
            # Some succeeded, some failed
            details = e.details
            inserted = details.get('nUpserted', 0)
            updated = details.get('nModified', 0)
            failed = len(details.get('writeErrors', []))
            return (inserted, updated, failed)
    
    def find_existing_hashes(self, hashes: List[str]) -> set:
        """
        Find which job hashes already exist in database.
        
        Args:
            hashes: List of job hashes to check
        
        Returns:
            Set of hashes that exist
        """
        if not hashes:
            return set()
        
        cursor = self.collection.find(
            {'hash': {'$in': hashes}},
            {'hash': 1}
        )
        
        return {doc['hash'] for doc in cursor}
    
    def deduplicate_jobs(self, jobs: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Separate new jobs from existing ones.
        
        Args:
            jobs: List of jobs to check
        
        Returns:
            Tuple of (new_jobs, existing_jobs)
        """
        if not jobs:
            return ([], [])
        
        # Get all hashes
        hashes = [job.get('hash', '') for job in jobs if job.get('hash')]
        existing_hashes = self.find_existing_hashes(hashes)
        
        new_jobs = []
        existing_jobs = []
        
        for job in jobs:
            job_hash = job.get('hash', '')
            if job_hash in existing_hashes:
                job['is_new'] = False
                existing_jobs.append(job)
            else:
                job['is_new'] = True
                new_jobs.append(job)
        
        return (new_jobs, existing_jobs)
    
    def get_jobs_since(
        self,
        hours: int = 24,
        source: str = None,
        keywords: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get jobs fetched within the last N hours.
        
        Args:
            hours: Number of hours to look back
            source: Filter by source (optional)
            keywords: Filter by matched keywords (optional)
        
        Returns:
            List of job documents
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        query = {'fetched_date': {'$gte': cutoff}}
        
        if source:
            query['source'] = source
        
        if keywords:
            query['keywords_matched'] = {'$in': keywords}
        
        cursor = self.collection.find(query).sort('posted_date', DESCENDING)
        
        return [JobModel.to_display(doc) for doc in cursor]
    
    def get_new_jobs_since(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get only new (not previously seen) jobs from the last N hours.
        
        Args:
            hours: Number of hours to look back
        
        Returns:
            List of new job documents
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        query = {
            'fetched_date': {'$gte': cutoff},
            'is_new': True
        }
        
        cursor = self.collection.find(query).sort('posted_date', DESCENDING)
        
        return [JobModel.to_display(doc) for doc in cursor]
    
    def cleanup_old_jobs(self, days: int = 2) -> int:
        """
        Delete jobs older than N days.
        
        Args:
            days: Number of days to keep
        
        Returns:
            Number of deleted documents
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        result = self.collection.delete_many({
            'fetched_date': {'$lt': cutoff}
        })
        
        deleted_count = result.deleted_count
        if deleted_count > 0:
            print(f"   🗑️ Cleaned up {deleted_count} jobs older than {days} days")
        
        return deleted_count
    
    def get_job_count(self, hours: int = None) -> int:
        """
        Get total job count.
        
        Args:
            hours: Optionally limit to last N hours
        
        Returns:
            Number of jobs
        """
        if hours:
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            return self.collection.count_documents({'fetched_date': {'$gte': cutoff}})
        
        return self.collection.count_documents({})
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with stats
        """
        total = self.get_job_count()
        last_24h = self.get_job_count(hours=24)
        last_48h = self.get_job_count(hours=48)
        
        # Get counts by source
        pipeline = [
            {'$group': {'_id': '$source', 'count': {'$sum': 1}}}
        ]
        sources = {doc['_id']: doc['count'] for doc in self.collection.aggregate(pipeline)}
        
        # Get new jobs count
        new_jobs = self.collection.count_documents({
            'is_new': True,
            'fetched_date': {'$gte': datetime.utcnow() - timedelta(hours=24)}
        })
        
        return {
            'total_jobs': total,
            'jobs_last_24h': last_24h,
            'jobs_last_48h': last_48h,
            'new_jobs_last_24h': new_jobs,
            'by_source': sources,
            'last_updated': datetime.utcnow().isoformat()
        }
    
    def get_all_jobs_for_ui(self, hours: int = 24, limit: int = 500) -> List[Dict[str, Any]]:
        """
        Get jobs formatted for UI display.
        
        Args:
            hours: Number of hours to look back
            limit: Maximum number of jobs to return
        
        Returns:
            List of jobs formatted for UI
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        cursor = self.collection.find(
            {'fetched_date': {'$gte': cutoff}}
        ).sort('posted_date', DESCENDING).limit(limit)
        
        jobs = []
        for doc in cursor:
            display = JobModel.to_display(doc)
            jobs.append({
                'id': display.get('_id'),
                'title': display.get('title', ''),
                'company': display.get('company', ''),
                'location': display.get('location', ''),
                'url': display.get('url', ''),
                'source': display.get('source', ''),
                'posted_date': display.get('posted_date_formatted', ''),
                'keywords': display.get('keywords_matched', []),
                'is_new': display.get('is_new', False),
                'logo': display.get('company_logo', ''),
            })
        
        return jobs




