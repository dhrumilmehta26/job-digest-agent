"""
RemoteOK job scraper.
Free API, no authentication required.
"""

from typing import List, Dict, Any
from datetime import datetime
from .base_scraper import BaseScraper


class RemoteOKScraper(BaseScraper):
    """Scraper for RemoteOK remote jobs API."""
    
    SOURCE_NAME = "remoteok"
    BASE_URL = "https://remoteok.com/api"
    
    def __init__(self):
        super().__init__()
        # RemoteOK requires specific headers
        self.session.headers.update({
            'User-Agent': 'JobAggregator/1.0 (job search application)',
        })
    
    def fetch_jobs(self, keywords: List[str] = None, location: str = None) -> List[Dict[str, Any]]:
        """
        Fetch jobs from RemoteOK API.
        
        RemoteOK returns all jobs; filtering is done client-side.
        """
        response = self._make_request(self.BASE_URL)
        
        if not response:
            return []
        
        # RemoteOK returns a list with a legal notice as first item
        jobs = []
        for item in response:
            if isinstance(item, dict) and 'id' in item and 'position' in item:
                jobs.append(item)
        
        return jobs
    
    def normalize_job(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize RemoteOK job data."""
        # Parse the date
        date_str = raw_job.get('date')
        posted_date = self._parse_date(date_str) if date_str else None
        
        # Build location string
        location = raw_job.get('location', '')
        if not location:
            location = 'Remote'
        
        # Build tags
        tags = raw_job.get('tags', [])
        if isinstance(tags, str):
            tags = [tags]
        
        # Build URL
        slug = raw_job.get('slug', raw_job.get('id', ''))
        url = raw_job.get('url', f"https://remoteok.com/remote-jobs/{slug}")
        
        return {
            'job_id': f"{self.SOURCE_NAME}_{raw_job.get('id', '')}",
            'source': self.SOURCE_NAME,
            'title': raw_job.get('position', ''),
            'company': raw_job.get('company', ''),
            'location': location,
            'description': raw_job.get('description', ''),
            'url': url,
            'posted_date': posted_date,
            'fetched_date': datetime.utcnow(),
            'salary': raw_job.get('salary', ''),
            'job_type': 'Remote',
            'category': '',
            'tags': tags if isinstance(tags, list) else [],
            'keywords_matched': [],
            'hash': self._generate_hash(raw_job),
            'company_logo': raw_job.get('company_logo', raw_job.get('logo', '')),
        }
    
    def _generate_hash(self, job: Dict[str, Any]) -> str:
        """Generate hash for RemoteOK jobs."""
        import hashlib
        content = f"{job.get('position', '')}{job.get('company', '')}{job.get('id', '')}"
        return hashlib.md5(content.encode()).hexdigest()


