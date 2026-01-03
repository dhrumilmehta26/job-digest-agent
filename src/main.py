"""
Main orchestrator for Job Aggregator.
Coordinates fetching, filtering, storing, and notifying.
"""

import sys
from datetime import datetime
from typing import List, Dict, Any, Tuple

from .utils.config import Config
from .utils.timezone import TimezoneHandler
from .utils.filters import JobFilter
from .scrapers import get_all_scrapers
from .database.connection import DatabaseConnection
from .database.operations import JobOperations
from .notifications.email_sender import EmailSender


class JobAggregator:
    """Main orchestrator for job aggregation pipeline."""
    
    def __init__(self):
        """Initialize the job aggregator."""
        self.config = Config()
        self.tz_handler = TimezoneHandler(self.config.user_timezone)
        self.db_conn = None
        self.job_ops = None
        self.email_sender = None
    
    def setup(self) -> bool:
        """
        Setup all components.
        
        Returns:
            True if setup successful, False otherwise
        """
        print("\n" + "=" * 60)
        print("🚀 JOB AGGREGATOR - Starting Up")
        print("=" * 60)
        print(f"⏰ Current time: {self.tz_handler.format_datetime()}")
        print()
        
        # Validate configuration
        if not self.config.validate():
            return False
        
        self.config.print_config()
        
        # Connect to database
        try:
            self.db_conn = DatabaseConnection(
                self.config.mongodb_uri,
                self.config.mongodb_database
            )
            db = self.db_conn.connect()
            self.job_ops = JobOperations(db)
        except Exception as e:
            print(f"❌ Database setup failed: {e}")
            return False
        
        # Setup email sender
        try:
            self.email_sender = EmailSender(
                smtp_host=self.config.smtp_host,
                smtp_port=self.config.smtp_port,
                smtp_user=self.config.smtp_user,
                smtp_password=self.config.smtp_password,
                from_email=self.config.from_email,
                from_name=self.config.from_name,
                use_tls=self.config.smtp_use_tls
            )
        except Exception as e:
            print(f"❌ Email sender setup failed: {e}")
            return False
        
        return True
    
    def fetch_all_jobs(self) -> List[Dict[str, Any]]:
        """
        Fetch jobs from all sources.
        
        Returns:
            List of all fetched jobs
        """
        print("\n" + "-" * 60)
        print("📥 FETCHING JOBS FROM ALL SOURCES")
        print("-" * 60)
        
        all_jobs = []
        scrapers = get_all_scrapers()
        
        # Get search parameters
        keywords = self.config.search_keywords
        location = ','.join(self.config.preferred_locations) if self.config.preferred_locations else None
        
        print(f"   Keywords: {', '.join(keywords)}")
        print(f"   Locations: {location or 'All'}")
        print()
        
        for scraper in scrapers:
            try:
                jobs = scraper.search(keywords=keywords, location=location)
                all_jobs.extend(jobs)
            except Exception as e:
                print(f"   ❌ Error with {scraper.SOURCE_NAME}: {e}")
        
        print(f"\n   📊 Total jobs fetched: {len(all_jobs)}")
        return all_jobs
    
    def filter_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply filters to jobs.
        
        Args:
            jobs: Raw jobs list
        
        Returns:
            Filtered jobs list
        """
        print("\n" + "-" * 60)
        print("🔍 FILTERING JOBS")
        print("-" * 60)
        
        job_filter = JobFilter(
            keywords=self.config.search_keywords,
            designations=self.config.filter_designations,
            fields=self.config.filter_fields,
            locations=self.config.preferred_locations
        )
        
        # Apply filters
        filtered_jobs = job_filter.filter_jobs(jobs)
        
        # Enrich with matched keywords
        for job in filtered_jobs:
            job_filter.enrich_job_with_matches(job)
        
        # Filter by date (last 24 hours posted)
        cutoff = self.tz_handler.get_last_48h_cutoff()
        date_filtered = JobFilter.filter_by_date(filtered_jobs, cutoff)
        
        print(f"   After keyword filter: {len(filtered_jobs)} jobs")
        print(f"   After date filter (24h): {len(date_filtered)} jobs")
        
        return date_filtered
    
    def store_jobs(self, jobs: List[Dict[str, Any]]) -> Tuple[int, int]:
        """
        Store jobs in database with deduplication.
        
        Args:
            jobs: Jobs to store
        
        Returns:
            Tuple of (new_count, existing_count)
        """
        print("\n" + "-" * 60)
        print("💾 STORING JOBS IN DATABASE")
        print("-" * 60)
        
        # Deduplicate against existing jobs
        new_jobs, existing_jobs = self.job_ops.deduplicate_jobs(jobs)
        
        print(f"   New jobs: {len(new_jobs)}")
        print(f"   Already in database: {len(existing_jobs)}")
        
        # Store all jobs (upsert)
        if jobs:
            inserted, updated, failed = self.job_ops.upsert_jobs(jobs)
            print(f"   Inserted: {inserted}, Updated: {updated}, Failed: {failed}")
        
        # Cleanup old jobs (keep only last 2 days)
        deleted = self.job_ops.cleanup_old_jobs(days=2)
        
        return len(new_jobs), len(existing_jobs)
    
    def send_notification(self, jobs: List[Dict[str, Any]]) -> bool:
        """
        Send email notification with jobs.
        
        Args:
            jobs: Jobs to include in email
        
        Returns:
            True if sent successfully
        """
        print("\n" + "-" * 60)
        print("📧 SENDING EMAIL NOTIFICATION")
        print("-" * 60)
        
        # Get only new jobs for notification
        new_jobs = [job for job in jobs if job.get('is_new', True)]
        
        print(f"   New jobs to notify: {len(new_jobs)}")
        print(f"   Recipients: {', '.join(self.config.to_emails)}")
        
        # Format jobs for email
        email_jobs = []
        for job in new_jobs[:50]:  # Limit to 50 jobs in email
            email_jobs.append({
                'title': job.get('title', 'Unknown Title'),
                'company': job.get('company', 'Unknown Company'),
                'location': job.get('location', 'Not specified'),
                'url': job.get('url', '#'),
                'source': job.get('source', 'Unknown'),
                'keywords': job.get('keywords_matched', []),
            })
        
        # Send email
        success = self.email_sender.send_job_digest(
            to_emails=self.config.to_emails,
            jobs=email_jobs,
            keywords=self.config.get_keywords_display(),
            date_str=self.tz_handler.format_date()
        )
        
        return success
    
    def run(self) -> bool:
        """
        Run the complete job aggregation pipeline.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Setup
            if not self.setup():
                return False
            
            # Fetch jobs
            all_jobs = self.fetch_all_jobs()
            
            if not all_jobs:
                print("\n⚠ No jobs fetched from any source")
                # Still send notification about no jobs
                self.send_notification([])
                return True
            
            # Filter jobs
            filtered_jobs = self.filter_jobs(all_jobs)
            
            # Store in database
            new_count, existing_count = self.store_jobs(filtered_jobs)
            
            # Send notification
            self.send_notification(filtered_jobs)
            
            # Print summary
            self._print_summary(len(all_jobs), len(filtered_jobs), new_count)
            
            return True
            
        except Exception as e:
            print(f"\n❌ Fatal error: {e}")
            import traceback
            traceback.print_exc()
            return False
            
        finally:
            # Cleanup
            if self.db_conn:
                self.db_conn.disconnect()
    
    def _print_summary(self, total_fetched: int, filtered: int, new: int):
        """Print run summary."""
        print("\n" + "=" * 60)
        print("✅ JOB AGGREGATION COMPLETE")
        print("=" * 60)
        print(f"   📥 Total fetched: {total_fetched}")
        print(f"   🔍 After filtering: {filtered}")
        print(f"   ✨ New jobs: {new}")
        print(f"   ⏰ Completed at: {self.tz_handler.format_datetime()}")
        print("=" * 60 + "\n")
    
    def export_jobs_json(self, output_path: str = None) -> str:
        """
        Export recent jobs to JSON file for UI.
        
        Args:
            output_path: Path to output file
        
        Returns:
            Path to exported file
        """
        import json
        from pathlib import Path
        
        if output_path is None:
            output_path = Path(__file__).parent.parent / 'ui' / 'jobs_data.json'
        
        # Get jobs from database
        jobs = self.job_ops.get_all_jobs_for_ui(hours=24)
        stats = self.job_ops.get_stats()
        
        data = {
            'jobs': jobs,
            'stats': stats,
            'generated_at': datetime.utcnow().isoformat(),
            'timezone': self.config.user_timezone,
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"   ✓ Exported {len(jobs)} jobs to {output_path}")
        return str(output_path)


def main():
    """Entry point for the job aggregator."""
    aggregator = JobAggregator()
    success = aggregator.run()
    
    if success:
        # Export jobs for UI
        try:
            aggregator.export_jobs_json()
        except Exception as e:
            print(f"   ⚠ Failed to export jobs JSON: {e}")
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()



