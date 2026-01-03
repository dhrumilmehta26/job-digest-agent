"""
Configuration loader for Job Aggregator.
Loads from GitHub Secrets (environment variables) or .env file.
"""

import os
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv


class Config:
    """Configuration manager that loads from environment variables or .env file."""
    
    _instance = None
    _loaded = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not Config._loaded:
            self._load_config()
            Config._loaded = True
    
    def _load_config(self):
        """Load configuration from .env file if not in GitHub Actions."""
        # Check if running in GitHub Actions
        if not os.getenv('GITHUB_ACTIONS'):
            # Load from .env file
            env_path = Path(__file__).parent.parent.parent / '.env'
            if env_path.exists():
                load_dotenv(env_path)
                print(f"✓ Loaded configuration from {env_path}")
            else:
                print(f"⚠ No .env file found at {env_path}")
        else:
            print("✓ Running in GitHub Actions - using repository secrets")
    
    @staticmethod
    def _parse_list(value: Optional[str]) -> List[str]:
        """Parse comma-separated string into list."""
        if not value:
            return []
        return [item.strip() for item in value.split(',') if item.strip()]

    @staticmethod
    def _parse_bool(value: Optional[str], default: bool = True) -> bool:
        """Parse a string environment variable into boolean."""
        if value is None or value == '':
            return default
        return value.strip().lower() in ('1', 'true', 'yes', 'on')
    
    # MongoDB Configuration
    @property
    def mongodb_uri(self) -> str:
        """MongoDB connection URI."""
        uri = os.getenv('MONGODB_URI', '')
        if not uri:
            raise ValueError("MONGODB_URI is required but not set")
        return uri
    
    @property
    def mongodb_database(self) -> str:
        """MongoDB database name."""
        return os.getenv('MONGODB_DATABASE', 'job_aggregator')
    
    # SMTP Configuration
    @property
    def smtp_host(self) -> str:
        """SMTP server host (defaults to Gmail)."""
        return os.getenv('SMTP_HOST', 'smtp.gmail.com')

    @property
    def smtp_port(self) -> int:
        """SMTP server port."""
        port_str = os.getenv('SMTP_PORT', '587')
        try:
            return int(port_str)
        except ValueError:
            raise ValueError("SMTP_PORT must be a valid integer")

    @property
    def smtp_user(self) -> str:
        """SMTP username (Gmail address for Gmail SMTP)."""
        user = os.getenv('SMTP_USER', '')
        if not user:
            raise ValueError("SMTP_USER is required but not set")
        return user

    @property
    def smtp_password(self) -> str:
        """SMTP password or app-specific password."""
        password = os.getenv('SMTP_PASSWORD', '')
        if not password:
            raise ValueError("SMTP_PASSWORD is required but not set")
        return password

    @property
    def smtp_use_tls(self) -> bool:
        """Whether to use STARTTLS (recommended for Gmail)."""
        return self._parse_bool(os.getenv('SMTP_USE_TLS', 'true'), True)
    
    @property
    def from_email(self) -> str:
        """Sender email address."""
        return os.getenv('FROM_EMAIL', self.smtp_user or 'jobs@example.com')
    
    @property
    def from_name(self) -> str:
        """Sender name."""
        return os.getenv('FROM_NAME', 'Job Aggregator')
    
    @property
    def to_emails(self) -> List[str]:
        """List of recipient email addresses."""
        return self._parse_list(os.getenv('TO_EMAILS', ''))
    
    # Job Search Configuration
    @property
    def search_keywords(self) -> List[str]:
        """Keywords to search for in job listings."""
        return self._parse_list(os.getenv('SEARCH_KEYWORDS', 'CRM,Retention,Martech'))
    
    @property
    def filter_designations(self) -> List[str]:
        """Job designations to filter."""
        return self._parse_list(os.getenv('FILTER_DESIGNATIONS', ''))
    
    @property
    def filter_fields(self) -> List[str]:
        """Job fields/categories to filter."""
        return self._parse_list(os.getenv('FILTER_FIELDS', ''))
    
    # Location & Timezone
    @property
    def preferred_locations(self) -> List[str]:
        """Preferred job locations."""
        return self._parse_list(os.getenv('PREFERRED_LOCATIONS', 'Remote'))
    
    @property
    def user_timezone(self) -> str:
        """User's timezone."""
        return os.getenv('USER_TIMEZONE', 'UTC')
    
    # Optional API Keys
    @property
    def adzuna_app_id(self) -> Optional[str]:
        return os.getenv('ADZUNA_APP_ID')
    
    @property
    def adzuna_api_key(self) -> Optional[str]:
        return os.getenv('ADZUNA_API_KEY')
    
    @property
    def themuse_api_key(self) -> Optional[str]:
        return os.getenv('THEMUSE_API_KEY')
    
    @property
    def jooble_api_key(self) -> Optional[str]:
        return os.getenv('JOOBLE_API_KEY')
    
    def get_keywords_display(self) -> str:
        """Get a display-friendly string of keywords."""
        keywords = self.search_keywords
        if len(keywords) <= 3:
            return '/'.join(keywords)
        return f"{keywords[0]}/{keywords[1]}/..."
    
    def validate(self) -> bool:
        """Validate that all required configuration is present."""
        errors = []
        
        try:
            _ = self.mongodb_uri
        except ValueError as e:
            errors.append(str(e))
        
        try:
            _ = self.smtp_host
            _ = self.smtp_port
            _ = self.smtp_user
            _ = self.smtp_password
            _ = self.smtp_use_tls
        except ValueError as e:
            errors.append(str(e))
        
        if not self.to_emails:
            errors.append("TO_EMAILS is required but not set")
        
        if not self.search_keywords:
            errors.append("SEARCH_KEYWORDS is required but not set")
        
        if errors:
            print("❌ Configuration errors:")
            for error in errors:
                print(f"   - {error}")
            return False
        
        print("✓ Configuration validated successfully")
        return True
    
    def print_config(self):
        """Print current configuration (hiding sensitive values)."""
        print("\n📋 Current Configuration:")
        print(f"   MongoDB URI: {'*' * 20}...{self.mongodb_uri[-10:]}" if self.mongodb_uri else "   MongoDB URI: NOT SET")
        print(f"   Database: {self.mongodb_database}")
        print(f"   SMTP Host: {self.smtp_host}")
        print(f"   SMTP Port: {self.smtp_port}")
        print(f"   SMTP User: {self.smtp_user}")
        print(f"   SMTP TLS: {'Yes' if self.smtp_use_tls else 'No'}")
        print(f"   From Email: {self.from_email}")
        print(f"   To Emails: {', '.join(self.to_emails)}")
        print(f"   Search Keywords: {', '.join(self.search_keywords)}")
        print(f"   Designations: {', '.join(self.filter_designations) or 'All'}")
        print(f"   Fields: {', '.join(self.filter_fields) or 'All'}")
        print(f"   Locations: {', '.join(self.preferred_locations)}")
        print(f"   Timezone: {self.user_timezone}")
        print()


# Singleton instance
config = Config()

