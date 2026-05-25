import time
from datetime import datetime, timezone


def get_utc_now():
    """Get current UTC datetime"""
    return datetime.now(timezone.utc)


def get_timestamp():
    """Get current Unix timestamp"""
    return int(time.time())
