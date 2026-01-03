"""
Arbeitnow job scraper.
Free API, no authentication required.
"""

from typing import List, Dict, Any
from datetime import datetime
from .base_scraper import BaseScraper


class ArbeitnowScraper(BaseScraper):
    """Scraper for Arbeitnow jobs API."""
    
    SOURCE_NAME = "arbeitnow"
    BASE_URL = "https://www.arbeitnow.com/api/job-board-api"
    
    def fetch_jobs(self, keywords: List[str] = None, location: str = None) -> List[Dict[str, Any]]:
        """
        Fetch jobs from Arbeitnow API.
        
        Arbeitnow API supports pagination.
        """
        all_jobs = []
        page = 1
        max_pages = 5  # Limit pages to avoid too many requests
        
        while page <= max_pages:
            params = {'page': page}
            response = self._make_request(self.BASE_URL, params=params)
            
            if not response or 'data' not in response:
                break
            
            jobs = response.get('data', [])
            if not jobs:
                break
            
            all_jobs.extend(jobs)
            
            # Check if there are more pages
            links = response.get('links', {})
            if not links.get('next'):
                break
            
            page += 1
        
        return all_jobs
    
    def normalize_job(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Arbeitnow job data."""
        # Parse the date (Unix timestamp)
        created_at = raw_job.get('created_at')
        posted_date = None
        if created_at:
            try:
                posted_date = datetime.fromtimestamp(created_at)
            except (ValueError, TypeError):
                posted_date = self._parse_date(str(created_at))
        
        # Build tags
        tags = raw_job.get('tags', [])
        if raw_job.get('remote'):
            tags.append('Remote')
        
        # Build location
        location = raw_job.get('location', '')
        if raw_job.get('remote') and not location:
            location = 'Remote'
        
        return {
            'job_id': f"{self.SOURCE_NAME}_{raw_job.get('slug', '')}",
            'source': self.SOURCE_NAME,
            'title': raw_job.get('title', ''),
            'company': raw_job.get('company_name', ''),
            'location': location,
            'description': raw_job.get('description', ''),
            'url': raw_job.get('url', ''),
            'posted_date': posted_date,
            'fetched_date': datetime.utcnow(),
            'salary': '',
            'job_type': 'Remote' if raw_job.get('remote') else 'On-site',
            'category': '',
            'tags': tags,
            'keywords_matched': [],
            'hash': self._generate_hash(raw_job),
        }
    
    def _generate_hash(self, job: Dict[str, Any]) -> str:
        """Generate hash for Arbeitnow jobs."""
        import hashlib
        content = f"{job.get('title', '')}{job.get('company_name', '')}{job.get('slug', '')}"
        return hashlib.md5(content.encode()).hexdigest()


