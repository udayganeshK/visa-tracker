#!/usr/bin/env python3
"""
Test time calculation to debug the difference with the official site
"""

from datetime import datetime, timezone, timedelta

def get_ist_now():
    """Get current datetime in IST (UTC+5:30)"""
    ist_offset = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist_offset)

def test_time_calculation():
    # The timestamp from our data
    data_timestamp = "2025-08-14 02:38:39"
    
    # Current IST time
    current_ist = get_ist_now()
    print(f"Current IST time: {current_ist}")
    print(f"Current IST (no tz): {current_ist.replace(tzinfo=None)}")
    
    # Parse the data timestamp
    dt = datetime.strptime(data_timestamp, "%Y-%m-%d %H:%M:%S")
    print(f"Data timestamp: {dt}")
    
    # Calculate difference
    now = current_ist.replace(tzinfo=None)
    diff = now - dt
    
    print(f"Time difference: {diff}")
    print(f"Total seconds: {diff.total_seconds()}")
    print(f"Hours: {diff.total_seconds() / 3600:.1f}")
    print(f"Minutes: {diff.total_seconds() / 60:.0f}")
    
    # Our app's calculation
    if diff.days > 0:
        result = f"{diff.days}d ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        result = f"{hours}h ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        result = f"{minutes}m ago"
    else:
        result = "Now"
    
    print(f"Our app shows: {result}")
    
    # Let's also check what 8:08 AM IST would be
    official_time = datetime.strptime("2025-08-14 08:08:00", "%Y-%m-%d %H:%M:%S")
    print(f"\nOfficial site timestamp (8:08 AM IST): {official_time}")
    
    diff_official = now - official_time
    print(f"Difference from 8:08 AM: {diff_official}")
    print(f"Hours from 8:08 AM: {diff_official.total_seconds() / 3600:.1f}")

if __name__ == "__main__":
    test_time_calculation()
