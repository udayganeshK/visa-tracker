#!/usr/bin/env python3
"""
Test the time adjustment to see if it works correctly
"""

from datetime import datetime, timedelta, timezone

def get_ist_now():
    """Get current datetime in IST (UTC+5:30)"""
    ist_offset = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist_offset)

def test_adjusted_time():
    # Current data timestamp
    data_timestamp = "2025-08-14 02:38:39"
    
    # Current IST time
    current_ist = get_ist_now().replace(tzinfo=None)
    print(f"Current IST time: {current_ist}")
    
    # Parse the data timestamp
    dt = datetime.strptime(data_timestamp, "%Y-%m-%d %H:%M:%S")
    print(f"Original data timestamp: {dt}")
    
    # Add 5.5 hours adjustment
    adjusted_dt = dt + timedelta(hours=5, minutes=30)
    print(f"Adjusted timestamp (+5.5h): {adjusted_dt}")
    
    # Calculate difference with original method
    original_diff = current_ist - dt
    print(f"Original time difference: {original_diff}")
    print(f"Original minutes ago: {original_diff.total_seconds() / 60:.0f}")
    
    # Calculate difference with adjusted method
    adjusted_diff = current_ist - adjusted_dt
    print(f"Adjusted time difference: {adjusted_diff}")
    print(f"Adjusted minutes ago: {adjusted_diff.total_seconds() / 60:.0f}")
    
    # Compare with official site (8:08 AM)
    official_time = datetime.strptime("2025-08-14 08:08:00", "%Y-%m-%d %H:%M:%S")
    official_diff = current_ist - official_time
    print(f"\nOfficial site time (8:08 AM): {official_time}")
    print(f"Official time difference: {official_diff}")
    print(f"Official minutes ago: {official_diff.total_seconds() / 60:.0f}")
    
    print(f"\n🎯 COMPARISON:")
    print(f"Official site shows: ~{official_diff.total_seconds() / 60:.0f} minutes ago")
    print(f"Our adjusted calculation: {adjusted_diff.total_seconds() / 60:.0f} minutes ago")
    print(f"Difference: {abs((adjusted_diff.total_seconds() - official_diff.total_seconds()) / 60):.0f} minutes")

if __name__ == "__main__":
    test_adjusted_time()
