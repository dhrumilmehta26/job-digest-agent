# Scrapers package
from .base_scraper import BaseScraper
from .remotive import RemotiveScraper
from .remoteok import RemoteOKScraper
from .arbeitnow import ArbeitnowScraper
from .google_jobs import GoogleJobsScraper

__all__ = [
    'BaseScraper',
    'RemotiveScraper', 
    'RemoteOKScraper',
    'ArbeitnowScraper',
    'GoogleJobsScraper'
]

# Registry of all available scrapers
SCRAPER_REGISTRY = {
    'remotive': RemotiveScraper,
    'remoteok': RemoteOKScraper,
    'arbeitnow': ArbeitnowScraper,
    'google_jobs': GoogleJobsScraper,
}


def get_all_scrapers():
    """Get instances of all available scrapers."""
    return [scraper_class() for scraper_class in SCRAPER_REGISTRY.values()]


def get_scraper(name: str):
    """Get a specific scraper by name."""
    scraper_class = SCRAPER_REGISTRY.get(name.lower())
    if scraper_class:
        return scraper_class()
    raise ValueError(f"Unknown scraper: {name}")


