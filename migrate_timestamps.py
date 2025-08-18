#!/usr/bin/env python3
"""
Migrate UTC timestamps in subscriptions.json to IST timestamps
This is a one-time migration script to convert existing UTC timestamps to IST
"""

import json
import os
from datetime import datetime, timezone, timedelta

def utc_to_ist(utc_timestamp):
    """Convert UTC timestamp to IST timestamp"""
    try:
        # Parse the UTC timestamp
        if utc_timestamp.endswith('Z'):
            utc_dt = datetime.fromisoformat(utc_timestamp[:-1] + '+00:00')
        elif '+' in utc_timestamp or '-' in utc_timestamp[-6:]:
            utc_dt = datetime.fromisoformat(utc_timestamp)
        else:
            # Assume UTC if no timezone info
            utc_dt = datetime.fromisoformat(utc_timestamp).replace(tzinfo=timezone.utc)
        
        # Convert to IST (UTC+5:30)
        ist_tz = timezone(timedelta(hours=5, minutes=30))
        ist_dt = utc_dt.astimezone(ist_tz)
        
        # Return ISO format without timezone (since we'll store as IST)
        return ist_dt.strftime('%Y-%m-%dT%H:%M:%S')
    except Exception as e:
        print(f"Error converting timestamp {utc_timestamp}: {e}")
        return utc_timestamp

def migrate_subscriptions():
    """Migrate all UTC timestamps in subscriptions.json to IST"""
    subscriptions_file = 'subscriptions.json'
    backup_file = 'subscriptions_utc_backup.json'
    
    if not os.path.exists(subscriptions_file):
        print(f"❌ {subscriptions_file} not found")
        return
    
    try:
        # Load current subscriptions
        with open(subscriptions_file, 'r') as f:
            subscriptions = json.load(f)
        
        print(f"📂 Loaded {len(subscriptions)} subscriptions")
        
        # Create backup of original file
        with open(backup_file, 'w') as f:
            json.dump(subscriptions, f, indent=2)
        print(f"💾 Created backup: {backup_file}")
        
        # Convert timestamps
        converted_count = 0
        for subscription in subscriptions:
            if 'created_at' in subscription:
                old_created = subscription['created_at']
                subscription['created_at'] = utc_to_ist(old_created)
                print(f"🔄 Created: {old_created} → {subscription['created_at']}")
                converted_count += 1
            
            if 'updated_at' in subscription:
                old_updated = subscription['updated_at']
                subscription['updated_at'] = utc_to_ist(old_updated)
                print(f"🔄 Updated: {old_updated} → {subscription['updated_at']}")
                converted_count += 1
        
        # Save updated subscriptions
        with open(subscriptions_file, 'w') as f:
            json.dump(subscriptions, f, indent=2)
        
        print(f"✅ Migration complete! Converted {converted_count} timestamps to IST")
        print(f"📁 Original file backed up as: {backup_file}")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")

def migrate_other_files():
    """Migrate timestamps in other JSON files"""
    files_to_migrate = [
        'email_log.json',
        'last_check.json',
        'stats.json'
    ]
    
    for filename in files_to_migrate:
        if not os.path.exists(filename):
            print(f"⏭️  Skipping {filename} (not found)")
            continue
        
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            # Create backup
            backup_name = filename.replace('.json', '_utc_backup.json')
            with open(backup_name, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"📂 Migrating {filename}...")
            
            # Migrate based on file type
            if filename == 'email_log.json':
                for entry in data:
                    if 'timestamp' in entry:
                        old_ts = entry['timestamp']
                        entry['timestamp'] = utc_to_ist(old_ts)
                        print(f"   📧 {old_ts} → {entry['timestamp']}")
            
            elif filename == 'last_check.json':
                if 'last_check' in data:
                    old_ts = data['last_check']
                    data['last_check'] = utc_to_ist(old_ts)
                    print(f"   ⏰ {old_ts} → {data['last_check']}")
            
            elif filename == 'stats.json':
                # Stats file might have timestamp fields, check and convert
                for key, value in data.items():
                    if isinstance(value, str) and ('T' in value or '-' in value):
                        try:
                            # Try to parse as timestamp
                            datetime.fromisoformat(value.replace('Z', '+00:00'))
                            old_ts = value
                            data[key] = utc_to_ist(old_ts)
                            print(f"   📊 {key}: {old_ts} → {data[key]}")
                        except:
                            # Not a timestamp, skip
                            pass
            
            # Save migrated file
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"✅ {filename} migrated successfully")
            
        except Exception as e:
            print(f"❌ Error migrating {filename}: {e}")

if __name__ == '__main__':
    print("🕐 Starting UTC to IST timestamp migration...")
    print("=" * 50)
    
    migrate_subscriptions()
    print()
    migrate_other_files()
    
    print("\n" + "=" * 50)
    print("🎉 Migration complete!")
    print("💡 You can now delete the *_utc_backup.json files if everything looks good")
