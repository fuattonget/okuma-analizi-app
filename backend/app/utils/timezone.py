"""
Timezone utility functions for consistent timezone handling

STANDARD: All dates are stored in UTC in MongoDB
Frontend converts UTC to Turkish timezone (UTC+3) for display
"""
from datetime import datetime, timezone, timedelta
from typing import Optional

def get_utc_now() -> datetime:
    """
    Get current datetime in UTC timezone
    
    This is the ONLY function that should be used for creating new timestamps
    in the backend. All dates are stored in UTC for consistency.
    """
    return datetime.now(timezone.utc)

def to_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Convert datetime to UTC timezone (legacy support)
    
    DEPRECATED: Use datetime.now(timezone.utc) directly instead.
    This function is kept for backward compatibility only.
    """
    if dt is None:
        return None
    
    if dt.tzinfo is None:
        # If no timezone info, assume it's UTC
        return dt.replace(tzinfo=timezone.utc)
    else:
        # Convert to UTC
        return dt.astimezone(timezone.utc)

def to_turkish_isoformat(dt: Optional[datetime]) -> Optional[str]:
    """
    Convert datetime to ISO format string with Turkish timezone
    
    DEPRECATED: Not recommended. Use .isoformat() directly and let frontend handle timezone.
    This function is kept for backward compatibility only.
    """
    if dt is None:
        return None
    
    # Convert to Turkish timezone first
    TURKISH_TIMEZONE = timezone(timedelta(hours=3))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    turkish_dt = dt.astimezone(TURKISH_TIMEZONE)
    return turkish_dt.isoformat()
