"""
Timezone utility functions for consistent timezone handling
"""
from datetime import datetime, timezone, timedelta
from typing import Optional

# Turkish timezone offset
TURKISH_TIMEZONE = timezone(timedelta(hours=3))

def get_turkish_now() -> datetime:
    """Get current datetime in Turkish timezone"""
    return datetime.now(TURKISH_TIMEZONE)

def get_utc_now() -> datetime:
    """Get current datetime in UTC timezone"""
    return datetime.now(timezone.utc)

def to_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Convert datetime to UTC timezone"""
    if dt is None:
        return None
    
    if dt.tzinfo is None:
        # If no timezone info, assume it's Turkish time and convert to UTC
        return dt.replace(tzinfo=TURKISH_TIMEZONE).astimezone(timezone.utc)
    else:
        # Convert to UTC
        return dt.astimezone(timezone.utc)

def to_turkish_timezone(dt: Optional[datetime]) -> Optional[datetime]:
    """Convert datetime to Turkish timezone"""
    if dt is None:
        return None
    
    if dt.tzinfo is None:
        # If no timezone info, assume it's UTC and convert to Turkish time
        return dt.replace(tzinfo=timezone.utc).astimezone(TURKISH_TIMEZONE)
    else:
        # Convert to Turkish timezone
        return dt.astimezone(TURKISH_TIMEZONE)

def to_turkish_isoformat(dt: Optional[datetime]) -> Optional[str]:
    """Convert datetime to ISO format string with Turkish timezone"""
    if dt is None:
        return None
    
    # Convert to Turkish timezone first
    turkish_dt = to_turkish_timezone(dt)
    return turkish_dt.isoformat()

def from_isoformat_with_turkish_tz(iso_string: str) -> datetime:
    """Parse ISO format string and ensure it's in Turkish timezone"""
    dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
    return to_turkish_timezone(dt)
