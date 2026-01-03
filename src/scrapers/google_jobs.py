"""
Google Jobs scraper.
Scrapes job listings from Google Jobs search results.

Note: This scraper uses web scraping which may be less reliable than API-based approaches.
Google may block requests or change their HTML structure.
"""

import re
import json
import urllib.parse
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper


class GoogleJobsScraper(BaseScraper):
    """Scraper for Google Jobs search results."""
    
    SOURCE_NAME = "google_jobs"
    BASE_URL = "https://www.google.com/search"
    
    def __init__(self):
        super().__init__()
        # Use a more browser-like user agent
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def fetch_jobs(self, keywords: List[str] = None, location: str = None) -> List[Dict[str, Any]]:
        """
        Fetch jobs from Google Jobs.
        
        This uses the Google search with ibp=htl;jobs parameter to get job listings.
        """
        all_jobs = []
        
        # Build search queries from keywords
        search_terms = keywords or ['CRM', 'Retention', 'Martech']
        
        for term in search_terms[:3]:  # Limit to 3 search terms
            query = f"{term} jobs"
            if location:
                query += f" {location}"
            
            jobs = self._search_google_jobs(query)
            all_jobs.extend(jobs)
        
        # Remove duplicates based on title and company
        seen = set()
        unique_jobs = []
        for job in all_jobs:
            key = f"{job.get('title', '')}{job.get('company', '')}"
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        return unique_jobs
    
    def _search_google_jobs(self, query: str) -> List[Dict[str, Any]]:
        """
        Search Google Jobs for a specific query.
        """
        params = {
            'q': query,
            'ibp': 'htl;jobs',  # This triggers Google Jobs view
            'hl': 'en',
            'gl': 'us',
        }
        
        try:
            url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            return self._parse_google_jobs_html(response.text, query)
            
        except Exception as e:
            print(f"   ⚠ Google Jobs search failed for '{query}': {e}")
            return []
    
    def _parse_google_jobs_html(self, html: str, query: str) -> List[Dict[str, Any]]:
        """
        Parse job listings from Google Jobs HTML.
        
        Google Jobs data is embedded in JavaScript within the page.
        This is a simplified parser that extracts basic job information.
        """
        jobs = []
        soup = BeautifulSoup(html, 'lxml')
        
        # Method 1: Try to find job cards in the HTML
        job_cards = soup.find_all('div', {'class': re.compile(r'BjJfJf|PwjeAc|gws-plugins-horizon-jobs')})
        
        for card in job_cards:
            try:
                job = self._extract_job_from_card(card, query)
                if job:
                    jobs.append(job)
            except Exception:
                continue
        
        # Method 2: Try to extract from embedded JSON
        if not jobs:
            jobs = self._extract_jobs_from_script(html, query)
        
        # Method 3: Use alternative parsing for structured data
        if not jobs:
            jobs = self._extract_structured_jobs(soup, query)
        
        return jobs
    
    def _extract_job_from_card(self, card, query: str) -> Optional[Dict[str, Any]]:
        """Extract job data from a job card element."""
        # Try to find title
        title_elem = card.find(['div', 'h2', 'h3'], {'class': re.compile(r'BjJfJf|tJ9zfc')})
        title = title_elem.get_text(strip=True) if title_elem else None
        
        if not title:
            return None
        
        # Try to find company
        company_elem = card.find(['div', 'span'], {'class': re.compile(r'vNEEBe|company')})
        company = company_elem.get_text(strip=True) if company_elem else 'Unknown'
        
        # Try to find location
        location_elem = card.find(['div', 'span'], {'class': re.compile(r'Qk80Jf|location')})
        location = location_elem.get_text(strip=True) if location_elem else 'Not specified'
        
        # Try to find link
        link_elem = card.find('a', href=True)
        url = link_elem.get('href', '') if link_elem else ''
        if url and not url.startswith('http'):
            url = f"https://www.google.com{url}"
        
        return {
            'title': title,
            'company': company,
            'location': location,
            'description': '',
            'url': url or f"https://www.google.com/search?q={urllib.parse.quote(f'{title} {company} jobs')}",
            'date': datetime.utcnow().isoformat(),
            'source_query': query,
        }
    
    def _extract_jobs_from_script(self, html: str, query: str) -> List[Dict[str, Any]]:
        """Try to extract job data from embedded JavaScript."""
        jobs = []
        
        # Look for JSON-like data in script tags
        pattern = r'\["([^"]+)",\s*"([^"]+)",\s*"([^"]+)"[^\]]*\]'
        
        # Also try to find structured job data
        job_pattern = r'"title"\s*:\s*"([^"]+)".*?"company"\s*:\s*"([^"]+)"'
        
        matches = re.findall(job_pattern, html, re.DOTALL)
        
        for match in matches[:20]:  # Limit results
            if len(match) >= 2:
                jobs.append({
                    'title': match[0],
                    'company': match[1],
                    'location': 'Not specified',
                    'description': '',
                    'url': f"https://www.google.com/search?q={urllib.parse.quote(f'{match[0]} {match[1]} jobs')}",
                    'date': datetime.utcnow().isoformat(),
                    'source_query': query,
                })
        
        return jobs
    
    def _extract_structured_jobs(self, soup: BeautifulSoup, query: str) -> List[Dict[str, Any]]:
        """Extract jobs from structured data or alternative elements."""
        jobs = []
        
        # Try to find any job-related divs with data attributes
        for div in soup.find_all('div', attrs={'data-ved': True}):
            text = div.get_text(' ', strip=True)
            if len(text) > 20 and len(text) < 500:
                # Try to parse as potential job listing
                lines = text.split('\n')
                if len(lines) >= 2:
                    jobs.append({
                        'title': lines[0][:100] if lines else 'Unknown',
                        'company': lines[1][:100] if len(lines) > 1 else 'Unknown',
                        'location': lines[2][:100] if len(lines) > 2 else 'Not specified',
                        'description': '',
                        'url': f"https://www.google.com/search?q={urllib.parse.quote(query)}&ibp=htl;jobs",
                        'date': datetime.utcnow().isoformat(),
                        'source_query': query,
                    })
        
        return jobs[:10]  # Limit results
    
    def normalize_job(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Google Jobs data."""
        posted_date = self._parse_date(raw_job.get('date'))
        
        return {
            'job_id': self._generate_job_id(raw_job),
            'source': self.SOURCE_NAME,
            'title': raw_job.get('title', ''),
            'company': raw_job.get('company', ''),
            'location': raw_job.get('location', ''),
            'description': raw_job.get('description', ''),
            'url': raw_job.get('url', ''),
            'posted_date': posted_date,
            'fetched_date': datetime.utcnow(),
            'salary': raw_job.get('salary', ''),
            'job_type': '',
            'category': '',
            'tags': [raw_job.get('source_query', '')] if raw_job.get('source_query') else [],
            'keywords_matched': [],
            'hash': self._generate_hash(raw_job),
        }


