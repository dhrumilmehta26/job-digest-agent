"""
Base scraper class for Job Aggregator.
All scrapers should inherit from this class.
"""

import hashlib
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional
import requests
from fake_useragent import UserAgent


class BaseScraper(ABC):
    """Abstract base class for job scrapers."""
    
    # Scraper metadata - override in subclasses
    SOURCE_NAME = "base"
    BASE_URL = ""
    
    def __init__(self):
        """Initialize the scraper with a requests session."""
        self.session = requests.Session()
        self.ua = UserAgent()
        self._setup_session()
    
    def _setup_session(self):
        """Setup session with headers."""
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
        })
    
    @abstractmethod
    def fetch_jobs(self, keywords: List[str] = None, location: str = None) -> List[Dict[str, Any]]:
        """
        Fetch jobs from the source.
        
        Args:
            keywords: Keywords to search for
            location: Location filter
        
        Returns:
            List of job dictionaries
        """
        pass
    
    def normalize_job(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize job data to a standard format.
        
        Override in subclasses to handle source-specific formats.
        
        Returns:
            Normalized job dictionary with standard fields
        """
        return {
            'job_id': self._generate_job_id(raw_job),
            'source': self.SOURCE_NAME,
            'title': raw_job.get('title', ''),
            'company': raw_job.get('company', ''),
            'location': raw_job.get('location', ''),
            'description': raw_job.get('description', ''),
            'url': raw_job.get('url', ''),
            'posted_date': self._parse_date(raw_job.get('date')),
            'fetched_date': datetime.utcnow(),
            'salary': raw_job.get('salary', ''),
            'job_type': raw_job.get('job_type', ''),
            'category': raw_job.get('category', ''),
            'tags': raw_job.get('tags', []),
            'keywords_matched': [],
            'hash': self._generate_hash(raw_job),
        }
    
    def _generate_job_id(self, job: Dict[str, Any]) -> str:
        """Generate a unique job ID."""
        # Try to get source-specific ID first
        if 'id' in job:
            return f"{self.SOURCE_NAME}_{job['id']}"
        
        # Fall back to hash-based ID
        content = f"{job.get('title', '')}{job.get('company', '')}{job.get('url', '')}"
        return f"{self.SOURCE_NAME}_{hashlib.md5(content.encode()).hexdigest()[:12]}"
    
    def _generate_hash(self, job: Dict[str, Any]) -> str:
        """Generate a hash for deduplication."""
        content = f"{job.get('title', '')}{job.get('company', '')}{job.get('url', '')}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _parse_date(self, date_value: Any) -> Optional[datetime]:
        """Parse various date formats to datetime."""
        if date_value is None:
            return None
        
        if isinstance(date_value, datetime):
            return date_value
        
        if isinstance(date_value, str):
            # Try various formats
            formats = [
                '%Y-%m-%dT%H:%M:%S.%fZ',
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%d',
                '%d-%m-%Y',
                '%m/%d/%Y',
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_value, fmt)
                except ValueError:
                    continue
            
            # Try dateutil as fallback
            try:
                from dateutil import parser
                return parser.parse(date_value)
            except Exception:
                pass
        
        return None
    
    def _make_request(
        self,
        url: str,
        method: str = 'GET',
        params: Dict = None,
        json_data: Dict = None,
        timeout: int = 30
    ) -> Optional[Dict]:
        """
        Make an HTTP request with error handling.
        
        Returns:
            Response JSON or None if request failed
        """
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params, timeout=timeout)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=json_data, params=params, timeout=timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"⚠ Request failed for {self.SOURCE_NAME}: {e}")
            return None
        except ValueError as e:
            print(f"⚠ JSON decode error for {self.SOURCE_NAME}: {e}")
            return None
    
    def search(self, keywords: List[str] = None, location: str = None) -> List[Dict[str, Any]]:
        """
        Search for jobs and return normalized results.
        
        Args:
            keywords: Keywords to search for
            location: Location filter
        
        Returns:
            List of normalized job dictionaries
        """
        print(f"🔍 Fetching jobs from {self.SOURCE_NAME}...")
        
        try:
            raw_jobs = self.fetch_jobs(keywords=keywords, location=location)
            normalized_jobs = [self.normalize_job(job) for job in raw_jobs]
            
            print(f"   ✓ Found {len(normalized_jobs)} jobs from {self.SOURCE_NAME}")
            return normalized_jobs
            
        except Exception as e:
            print(f"   ❌ Error fetching from {self.SOURCE_NAME}: {e}")
            return []


