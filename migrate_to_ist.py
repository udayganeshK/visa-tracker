#!/usr/bin/env python3
"""
Migration script to convert all UTC timestamps to IST in visa tracker data files
This ensures all timestamps match checkvisaslots.com IST timezone
"""

import json
import os
from datetime import datetime, timezone, timedelta

def get_ist_offset():
    """Get IST timezone offset (UTC+5:30)"""
    return timezone(timedelta(hours=5, minutes=30))

def convert_utc_to_ist(utc_timestamp_str):
    """Convert UTC timestamp string to IST timestamp string"""
    try:
        # Parse UTC timestamp
        utc_dt = datetime.fromisoformat(utc_timestamp_str.replace('Z', '+00:00'))
        
        # If no timezone info, assume UTC
        if utc_dt.tzinfo is None:
            utc_dt = utc_dt.replace(tzinfo=timezone.utc)
        
        # Convert to IST
        ist_dt = utc_dt.astimezone(get_ist_offset())
        
        # Return as ISO string without timezone info (since we know it's IST)
        return ist_dt.replace(tzinfo=None).isoformat()
    except Exception as e:
        print(f"Error converting timestamp {utc_timestamp_str}: {e}")
        return utc_timestamp_str

def migrate_subscriptions():
    """Migrate subscriptions.json timestamps from UTC to IST"""
    file_path = 'subscriptions.json'
    
    if not os.path.exists(file_path):
        print(f"❌ {file_path} not found")
        return
    
    print(f"🔄 Migrating {file_path}...")
    
    # Load current data
    with open(file_path, 'r') as f:
        subscriptions = json.load(f)
    
    # Convert timestamps
    for subscription in subscriptions:
        if 'created_at' in subscription:
            old_time = subscription['created_at']
            new_time = convert_utc_to_ist(old_time)
            subscription['created_at'] = new_time
            print(f"   📅 Created: {old_time} → {new_time}")
        
        if 'updated_at' in subscription:
            old_time = subscription['updated_at']
            new_time = convert_utc_to_ist(old_time)
            subscription['updated_at'] = new_time
            print(f"   📅 Updated: {old_time} → {new_time}")
    
    # Backup original file
    backup_path = f'{file_path}.utc_backup'
    os.rename(file_path, backup_path)
    print(f"📁 Backed up original to {backup_path}")
    
    # Save migrated data
    with open(file_path, 'w') as f:
        json.dump(subscriptions, f, indent=2)
    
    print(f"✅ Migrated {len(subscriptions)} subscriptions to IST")

def migrate_email_log():
    """Migrate email_log.json timestamps from UTC to IST"""
    file_path = 'email_log.json'
    
    if not os.path.exists(file_path):
        print(f"❌ {file_path} not found")
        return
    
    print(f"🔄 Migrating {file_path}...")
    
    # Load current data
    with open(file_path, 'r') as f:
        email_log = json.load(f)
    
    # Convert timestamps
    count = 0
    for entry in email_log:
        if 'timestamp' in entry:
            old_time = entry['timestamp']
            new_time = convert_utc_to_ist(old_time)
            entry['timestamp'] = new_time
            count += 1
    
    # Backup original file
    backup_path = f'{file_path}.utc_backup'
    os.rename(file_path, backup_path)
    print(f"📁 Backed up original to {backup_path}")
    
    # Save migrated data
    with open(file_path, 'w') as f:
        json.dump(email_log, f, indent=2)
    
    print(f"✅ Migrated {count} email log entries to IST")

def migrate_stats():
    """Migrate stats.json timestamps from UTC to IST"""
    file_path = 'stats.json'
    
    if not os.path.exists(file_path):
        print(f"❌ {file_path} not found")
        return
    
    print(f"🔄 Migrating {file_path}...")
    
    # Load current data
    with open(file_path, 'r') as f:
        stats = json.load(f)
    
    # Convert timestamp fields
    timestamp_fields = ['last_startup', 'last_check', 'last_email_sent']
    
    for field in timestamp_fields:
        if field in stats:
            old_time = stats[field]
            new_time = convert_utc_to_ist(old_time)
            stats[field] = new_time
            print(f"   📅 {field}: {old_time} → {new_time}")
    
    # Backup original file
    backup_path = f'{file_path}.utc_backup'
    os.rename(file_path, backup_path)
    print(f"📁 Backed up original to {backup_path}")
    
    # Save migrated data
    with open(file_path, 'w') as f:
        json.dump(stats, f, indent=2)
    
    print(f"✅ Migrated stats.json to IST")

def main():
    print("🇮🇳 US Visa Tracker - UTC to IST Migration")
    print("=" * 50)
    print("Converting all timestamps to IST to match checkvisaslots.com")
    print()
    
    # Migrate all data files
    migrate_subscriptions()
    print()
    migrate_email_log()
    print()
    migrate_stats()
    print()
    
    print("🎉 Migration completed!")
    print("📝 All timestamps are now in IST (India Standard Time)")
    print("🔄 Restart the web application to see the changes")

if __name__ == '__main__':
    main()
