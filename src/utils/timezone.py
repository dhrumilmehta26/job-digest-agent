"""
Timezone handling utilities for Job Aggregator.
"""

from datetime import datetime, timedelta
from typing import Optional
import pytz


class TimezoneHandler:
    """Handle timezone conversions and time-based operations."""
    
    def __init__(self, timezone_str: str = 'UTC'):
        """
        Initialize with a timezone string.
        
        Args:
            timezone_str: Timezone name (e.g., 'America/New_York', 'Europe/London')
        """
        try:
            self.timezone = pytz.timezone(timezone_str)
        except pytz.UnknownTimeZoneError:
            print(f"⚠ Unknown timezone '{timezone_str}', falling back to UTC")
            self.timezone = pytz.UTC
        
        self.utc = pytz.UTC
    
    def now(self) -> datetime:
        """Get current time in user's timezone."""
        return datetime.now(self.timezone)
    
    def now_utc(self) -> datetime:
        """Get current time in UTC."""
        return datetime.now(self.utc)
    
    def to_user_timezone(self, dt: datetime) -> datetime:
        """Convert datetime to user's timezone."""
        if dt.tzinfo is None:
            # Assume UTC if no timezone info
            dt = self.utc.localize(dt)
        return dt.astimezone(self.timezone)
    
    def to_utc(self, dt: datetime) -> datetime:
        """Convert datetime to UTC."""
        if dt.tzinfo is None:
            # Assume it's in user's timezone
            dt = self.timezone.localize(dt)
        return dt.astimezone(self.utc)
    
    def get_last_24h_cutoff(self) -> datetime:
        """Get the datetime 24 hours ago in UTC."""
        return self.now_utc() - timedelta(hours=24)
    
    def get_last_48h_cutoff(self) -> datetime:
        """Get the datetime 48 hours ago in UTC."""
        return self.now_utc() - timedelta(hours=48)
    
    def is_within_last_24h(self, dt: datetime) -> bool:
        """Check if datetime is within last 24 hours."""
        if dt.tzinfo is None:
            dt = self.utc.localize(dt)
        return dt >= self.get_last_24h_cutoff()
    
    def is_within_last_48h(self, dt: datetime) -> bool:
        """Check if datetime is within last 48 hours."""
        if dt.tzinfo is None:
            dt = self.utc.localize(dt)
        return dt >= self.get_last_48h_cutoff()
    
    def format_date(self, dt: Optional[datetime] = None, format_str: str = '%a, %b %d') -> str:
        """
        Format datetime for display.
        
        Args:
            dt: Datetime to format (defaults to now)
            format_str: strftime format string
        
        Returns:
            Formatted date string
        """
        if dt is None:
            dt = self.now()
        else:
            dt = self.to_user_timezone(dt)
        return dt.strftime(format_str)
    
    def format_datetime(self, dt: Optional[datetime] = None) -> str:
        """Format datetime with time for display."""
        return self.format_date(dt, '%a, %b %d at %I:%M %p %Z')
    
    def parse_iso_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse ISO format date string.
        
        Args:
            date_str: ISO format date string
        
        Returns:
            Datetime object or None if parsing fails
        """
        if not date_str:
            return None
        
        try:
            # Try various ISO formats
            formats = [
                '%Y-%m-%dT%H:%M:%S.%fZ',
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%d',
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return self.utc.localize(dt)
                except ValueError:
                    continue
            
            # Try dateutil parser as fallback
            from dateutil import parser
            dt = parser.parse(date_str)
            if dt.tzinfo is None:
                dt = self.utc.localize(dt)
            return dt
            
        except Exception:
            return None
    
    def get_cron_schedule_utc(self, hour: int = 7, minute: int = 30) -> str:
        """
        Get cron schedule in UTC for a given local time.
        
        Args:
            hour: Hour in user's timezone (0-23)
            minute: Minute (0-59)
        
        Returns:
            Cron schedule string for GitHub Actions
        """
        # Create a datetime in user's timezone
        local_dt = self.timezone.localize(
            datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
        )
        
        # Convert to UTC
        utc_dt = local_dt.astimezone(self.utc)
        
        return f"{utc_dt.minute} {utc_dt.hour} * * *"


