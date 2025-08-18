#!/usr/bin/env python3
"""
Test the time adjustment logic
"""

from datetime import datetime, timedelta, timezone

def get_ist_now():
    """Get current datetime in IST (UTC+5:30)"""
    ist_offset = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist_offset)

def test_adjustment():
    # Test data from our records
    data_timestamp = "2025-08-14 02:38:39"  # What our data shows
    
    # Current time
    current_ist = get_ist_now().replace(tzinfo=None)
    print(f"Current IST time: {current_ist}")
    
    # Parse the data timestamp
    created_time = datetime.strptime(data_timestamp, '%Y-%m-%d %H:%M:%S')
    print(f"Data timestamp: {created_time}")
    
    # BEFORE adjustment
    diff_before = (current_ist - created_time).total_seconds() / 60
    print(f"Difference BEFORE adjustment: {diff_before:.0f} minutes ({diff_before/60:.1f} hours)")
    
    # AFTER adjustment (ADD 5.5 hours to make timestamp fresher)
    adjusted_time = created_time + timedelta(hours=5, minutes=30)
    print(f"Adjusted timestamp: {adjusted_time}")
    
    diff_after = (current_ist - adjusted_time).total_seconds() / 60
    print(f"Difference AFTER adjustment: {diff_after:.0f} minutes ({diff_after/60:.1f} hours)")
    
    # What the official site claims
    official_timestamp = "2025-08-14 08:08:00"  # Official site shows 8:08 AM
    official_time = datetime.strptime(official_timestamp, '%Y-%m-%d %H:%M:%S')
    diff_official = (current_ist - official_time).total_seconds() / 60
    print(f"Official site difference: {diff_official:.0f} minutes ({diff_official/60:.1f} hours)")
    
    print(f"\n✅ Adjustment brings us from {diff_before/60:.1f}h to {diff_after/60:.1f}h")
    print(f"✅ Official site shows {diff_official/60:.1f}h")
    print(f"✅ Difference: {abs(diff_after - diff_official):.0f} minutes")

if __name__ == "__main__":
    test_adjustment()
