"""
Job filtering utilities for Job Aggregator.
"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime


class JobFilter:
    """Filter jobs based on various criteria."""
    
    def __init__(
        self,
        keywords: List[str] = None,
        designations: List[str] = None,
        fields: List[str] = None,
        locations: List[str] = None
    ):
        """
        Initialize filter with criteria.
        
        Args:
            keywords: Keywords to match in title/description
            designations: Job designations to match
            fields: Job fields/categories to match
            locations: Locations to match
        """
        self.keywords = [k.lower() for k in (keywords or [])]
        self.designations = [d.lower() for d in (designations or [])]
        self.fields = [f.lower() for f in (fields or [])]
        self.locations = [l.lower() for l in (locations or [])]
    
    def _text_contains_any(self, text: str, terms: List[str]) -> bool:
        """Check if text contains any of the terms."""
        if not terms:
            return True  # No filter means accept all
        
        text_lower = text.lower()
        return any(term in text_lower for term in terms)
    
    def _text_matches_pattern(self, text: str, patterns: List[str]) -> bool:
        """Check if text matches any regex pattern."""
        if not patterns:
            return True
        
        text_lower = text.lower()
        for pattern in patterns:
            if re.search(pattern.lower(), text_lower):
                return True
        return False
    
    def matches_keywords(self, job: Dict[str, Any]) -> bool:
        """Check if job matches keyword criteria."""
        if not self.keywords:
            return True
        
        # Check title and description
        title = job.get('title', '')
        description = job.get('description', '')
        company = job.get('company', '')
        tags = ' '.join(job.get('tags', []))
        
        searchable_text = f"{title} {description} {company} {tags}".lower()
        
        return any(keyword in searchable_text for keyword in self.keywords)
    
    def matches_designation(self, job: Dict[str, Any]) -> bool:
        """Check if job matches designation criteria."""
        if not self.designations:
            return True
        
        title = job.get('title', '').lower()
        return any(designation in title for designation in self.designations)
    
    def matches_field(self, job: Dict[str, Any]) -> bool:
        """Check if job matches field/category criteria."""
        if not self.fields:
            return True
        
        category = job.get('category', '').lower()
        field = job.get('field', '').lower()
        tags = [t.lower() for t in job.get('tags', [])]
        
        searchable = f"{category} {field} {' '.join(tags)}"
        return any(f in searchable for f in self.fields)
    
    def matches_location(self, job: Dict[str, Any]) -> bool:
        """Check if job matches location criteria."""
        if not self.locations:
            return True
        
        location = job.get('location', '').lower()
        
        # Special handling for "remote"
        if 'remote' in self.locations:
            remote_indicators = ['remote', 'anywhere', 'worldwide', 'work from home', 'wfh']
            if any(indicator in location for indicator in remote_indicators):
                return True
        
        return any(loc in location for loc in self.locations)
    
    def filter_job(self, job: Dict[str, Any]) -> bool:
        """
        Check if a single job passes all filters.
        
        Returns:
            True if job passes all filters, False otherwise
        """
        return (
            self.matches_keywords(job) and
            self.matches_designation(job) and
            self.matches_field(job) and
            self.matches_location(job)
        )
    
    def filter_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter a list of jobs.
        
        Returns:
            List of jobs that pass all filters
        """
        return [job for job in jobs if self.filter_job(job)]
    
    def get_matched_keywords(self, job: Dict[str, Any]) -> List[str]:
        """Get list of keywords that matched for a job."""
        if not self.keywords:
            return []
        
        title = job.get('title', '')
        description = job.get('description', '')
        company = job.get('company', '')
        
        searchable_text = f"{title} {description} {company}".lower()
        
        return [kw for kw in self.keywords if kw in searchable_text]
    
    def enrich_job_with_matches(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Add matched keywords to job data."""
        job['keywords_matched'] = self.get_matched_keywords(job)
        return job
    
    @staticmethod
    def filter_by_date(
        jobs: List[Dict[str, Any]],
        cutoff_date: datetime,
        date_field: str = 'posted_date'
    ) -> List[Dict[str, Any]]:
        """
        Filter jobs by posting date.
        
        Args:
            jobs: List of jobs
            cutoff_date: Only include jobs posted after this date
            date_field: Field name containing the posted date
        
        Returns:
            Filtered list of jobs
        """
        from .timezone import TimezoneHandler

        tz = TimezoneHandler()
        cutoff_utc = tz.to_utc(cutoff_date) if cutoff_date.tzinfo else tz.utc.localize(cutoff_date)
        filtered = []
        for job in jobs:
            posted_date = job.get(date_field)
            if posted_date:
                if isinstance(posted_date, str):
                    posted_date = tz.parse_iso_date(posted_date)
                elif isinstance(posted_date, datetime):
                    posted_date = tz.to_utc(posted_date)
                else:
                    posted_date = None
                
                if posted_date and posted_date >= cutoff_utc:
                    filtered.append(job)
            else:
                # Include jobs without date (assume they're recent)
                filtered.append(job)
        
        return filtered

