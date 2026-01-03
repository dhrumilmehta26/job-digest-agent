"""
MongoDB models/schemas for Job Aggregator.
Using Python dictionaries with validation (similar to Mongoose schemas).
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from bson import ObjectId


class JobModel:
    """
    Job document model for MongoDB.
    
    Schema:
        _id: ObjectId (auto-generated)
        job_id: str - Unique identifier from source (e.g., "remotive_12345")
        source: str - Source name (remotive, remoteok, arbeitnow, google_jobs)
        title: str - Job title
        company: str - Company name
        location: str - Job location
        description: str - Job description (may be HTML)
        url: str - Application/details URL
        posted_date: datetime - When job was posted
        fetched_date: datetime - When we fetched the job
        salary: str - Salary information if available
        job_type: str - Full-time, Part-time, Contract, Remote, etc.
        category: str - Job category
        tags: List[str] - Tags/keywords
        keywords_matched: List[str] - Which search keywords matched this job
        hash: str - MD5 hash for deduplication
        is_new: bool - Whether this is a new job (not seen before)
        company_logo: str - URL to company logo (optional)
    """
    
    COLLECTION_NAME = 'jobs'
    
    # Required fields
    REQUIRED_FIELDS = ['job_id', 'source', 'title', 'url']
    
    # Default values
    DEFAULTS = {
        'company': '',
        'location': '',
        'description': '',
        'salary': '',
        'job_type': '',
        'category': '',
        'tags': [],
        'keywords_matched': [],
        'hash': '',
        'is_new': True,
        'company_logo': '',
    }
    
    @classmethod
    def create(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a validated job document.
        
        Args:
            data: Raw job data
        
        Returns:
            Validated job document ready for MongoDB
        
        Raises:
            ValueError: If required fields are missing
        """
        # Validate required fields
        missing = [f for f in cls.REQUIRED_FIELDS if not data.get(f)]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        
        # Build document with defaults
        doc = {**cls.DEFAULTS, **data}
        
        # Ensure datetime fields
        if not doc.get('posted_date'):
            doc['posted_date'] = None
        
        if not doc.get('fetched_date'):
            doc['fetched_date'] = datetime.utcnow()
        
        # Ensure lists
        if not isinstance(doc.get('tags'), list):
            doc['tags'] = []
        
        if not isinstance(doc.get('keywords_matched'), list):
            doc['keywords_matched'] = []
        
        return doc
    
    @classmethod
    def validate(cls, data: Dict[str, Any]) -> bool:
        """Validate job data."""
        return all(data.get(f) for f in cls.REQUIRED_FIELDS)
    
    @classmethod
    def to_display(cls, doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert MongoDB document to display format.
        
        Handles ObjectId conversion and date formatting.
        """
        display = dict(doc)
        
        # Convert ObjectId to string
        if '_id' in display:
            display['_id'] = str(display['_id'])
        
        # Format dates
        if 'posted_date' in display and display['posted_date']:
            if isinstance(display['posted_date'], datetime):
                display['posted_date_formatted'] = display['posted_date'].strftime('%Y-%m-%d %H:%M')
            else:
                display['posted_date_formatted'] = str(display['posted_date'])
        
        if 'fetched_date' in display and display['fetched_date']:
            if isinstance(display['fetched_date'], datetime):
                display['fetched_date_formatted'] = display['fetched_date'].strftime('%Y-%m-%d %H:%M')
            else:
                display['fetched_date_formatted'] = str(display['fetched_date'])
        
        return display
    
    @classmethod
    def get_indexes(cls) -> List[Dict[str, Any]]:
        """
        Get index definitions for the jobs collection.
        
        Returns:
            List of index specifications
        """
        return [
            {'keys': [('job_id', 1)], 'unique': True},
            {'keys': [('hash', 1)]},
            {'keys': [('source', 1)]},
            {'keys': [('fetched_date', -1)]},
            {'keys': [('posted_date', -1)]},
            {'keys': [('is_new', 1)]},
            {'keys': [('keywords_matched', 1)]},
        ]


