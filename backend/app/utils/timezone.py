"""
Timezone utility functions for consistent date handling
"""

from datetime import datetime, timezone, timedelta
from typing import Optional

def to_turkey_timezone(dt: Optional[datetime]) -> Optional[str]:
    """
    Convert a datetime to Turkey timezone and return as ISO string.
    Handles both timezone-aware and timezone-naive datetimes.
    
    Args:
        dt: datetime object (can be None, timezone-aware, or timezone-naive)
        
    Returns:
        ISO string in Turkey timezone (+03:00) or None if dt is None
    """
    if dt is None:
        return None
    
    # Turkey timezone
    turkey_tz = timezone(timedelta(hours=3))
    
    # If datetime is timezone-naive, assume it's UTC (MongoDB behavior)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    # Convert to Turkey timezone
    return dt.astimezone(turkey_tz).isoformat()

def to_utc_iso(dt: Optional[datetime]) -> Optional[str]:
    """
    Convert a datetime to UTC and return as ISO string.
    
    Args:
        dt: datetime object (can be None, timezone-aware, or timezone-naive)
        
    Returns:
        ISO string in UTC or None if dt is None
    """
    if dt is None:
        return None
    
    # If datetime is timezone-naive, assume it's UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    # Convert to UTC
    return dt.astimezone(timezone.utc).isoformat()


