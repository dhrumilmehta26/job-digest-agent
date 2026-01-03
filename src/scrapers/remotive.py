"""
Remotive.io job scraper.
Free API, no authentication required.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from .base_scraper import BaseScraper


class RemotiveScraper(BaseScraper):
    """Scraper for Remotive.io remote jobs API."""
    
    SOURCE_NAME = "remotive"
    BASE_URL = "https://remotive.com/api/remote-jobs"
    
    # Category mapping for Remotive
    CATEGORIES = {
        'marketing': 'marketing',
        'sales': 'sales',
        'customer_support': 'customer-support',
        'software_dev': 'software-dev',
        'product': 'product',
        'business': 'business',
        'data': 'data',
        'devops': 'devops',
        'finance': 'finance-legal',
        'hr': 'hr',
        'qa': 'qa',
        'writing': 'writing',
        'design': 'design',
        'all': 'all-others',
    }
    
    def fetch_jobs(self, keywords: List[str] = None, location: str = None) -> List[Dict[str, Any]]:
        """
        Fetch jobs from Remotive API.
        
        The Remotive API returns all jobs; filtering is done client-side.
        """
        params = {}
        
        # Remotive supports category filter
        # We'll fetch marketing and sales categories as they're most relevant for CRM/Martech
        categories_to_fetch = ['marketing', 'sales', 'customer_support', 'product', 'business']
        
        all_jobs = []
        
        # Fetch from relevant categories
        for category in categories_to_fetch:
            category_slug = self.CATEGORIES.get(category, category)
            params = {'category': category_slug}
            
            response = self._make_request(self.BASE_URL, params=params)
            
            if response and 'jobs' in response:
                all_jobs.extend(response['jobs'])
        
        # Also fetch all jobs to not miss any
        response = self._make_request(self.BASE_URL)
        if response and 'jobs' in response:
            # Add jobs not already in list (by ID)
            existing_ids = {job.get('id') for job in all_jobs}
            for job in response['jobs']:
                if job.get('id') not in existing_ids:
                    all_jobs.append(job)
        
        return all_jobs
    
    def normalize_job(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Remotive job data."""
        # Parse the publication date
        pub_date = raw_job.get('publication_date')
        posted_date = self._parse_date(pub_date) if pub_date else None
        
        # Build tags from category and job type
        tags = []
        if raw_job.get('category'):
            tags.append(raw_job['category'])
        if raw_job.get('job_type'):
            tags.append(raw_job['job_type'])
        if raw_job.get('tags'):
            tags.extend(raw_job['tags'])
        
        return {
            'job_id': f"{self.SOURCE_NAME}_{raw_job.get('id', '')}",
            'source': self.SOURCE_NAME,
            'title': raw_job.get('title', ''),
            'company': raw_job.get('company_name', ''),
            'location': raw_job.get('candidate_required_location', 'Remote'),
            'description': raw_job.get('description', ''),
            'url': raw_job.get('url', ''),
            'posted_date': posted_date,
            'fetched_date': datetime.utcnow(),
            'salary': raw_job.get('salary', ''),
            'job_type': raw_job.get('job_type', ''),
            'category': raw_job.get('category', ''),
            'tags': list(set(tags)),
            'keywords_matched': [],
            'hash': self._generate_hash(raw_job),
            'company_logo': raw_job.get('company_logo', ''),
        }


