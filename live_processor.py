#!/usr/bin/env python3
"""
Live Visa Data Processor
Processes the actual live data from checkvisaslots.com
"""

import json
from datetime import datetime
from collections import defaultdict

def load_live_data():
    """Load the live data JSON file"""
    try:
        with open('live_visa_data.json', 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"❌ Error loading live data: {str(e)}")
        return None

def categorize_visa_type(visa_type):
    """Categorize visa types into broader categories"""
    visa_type_upper = visa_type.upper()
    
    if any(term in visa_type_upper for term in ['B1', 'B2', 'B1/B2']):
        return 'Business/Tourism'
    elif 'F1' in visa_type_upper or 'F-1' in visa_type_upper:
        return 'Student'
    elif 'H1B' in visa_type_upper or 'H-1B' in visa_type_upper:
        return 'Skilled Worker'
    elif 'L1' in visa_type_upper or 'L-1' in visa_type_upper:
        return 'Intracompany Transfer'
    elif 'O1' in visa_type_upper or 'O-1' in visa_type_upper:
        return 'Extraordinary Ability'
    elif 'J1' in visa_type_upper or 'J-1' in visa_type_upper:
        return 'Exchange Visitor'
    elif 'H4' in visa_type_upper or 'H-4' in visa_type_upper:
        return 'H4 Dependent'
    else:
        return 'Other'

def parse_date(date_str):
    """Parse date string to a comparable format"""
    try:
        # Handle format like "27 Aug, 25" or "23 Sep, 25"
        if ',' in date_str:
            parts = date_str.replace(',', '').split()
            if len(parts) == 3:
                day, month_str, year_str = parts
                month_map = {
                    'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                    'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
                    'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
                }
                month = month_map.get(month_str, '01')
                year = f"20{year_str}" if len(year_str) == 2 else year_str
                return f"{year}-{month}-{day.zfill(2)}"
        return date_str
    except Exception:
        return date_str

def get_relative_time_from_timestamp(timestamp_str):
    """Calculate relative time from timestamp"""
    try:
        # Parse timestamp like "2025-08-14 06:01:34"
        dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        now = datetime.now()
        diff = now - dt
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"
    except Exception:
        return "Unknown"

def analyze_live_data(data):
    """Analyze the live visa data"""
    if not data or 'result' not in data:
        print("❌ No valid data to analyze")
        return
    
    print("\n" + "="*70)
    print("🌐 LIVE US VISA AVAILABILITY ANALYSIS")
    print("="*70)
    print(f"📡 Data Source: checkvisaslots.com")
    print(f"🕐 Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Data Last Updated: {data.get('createdon', 'Unknown')}")
    
    # Process all records
    all_records = []
    categories = defaultdict(list)
    locations = defaultdict(list)
    
    total_slots = 0
    total_appointments = 0
    
    for visa_type, records in data['result'].items():
        category = categorize_visa_type(visa_type)
        
        for record in records:
            # Enhance record with additional data
            enhanced_record = {
                **record,
                'visa_category': category,
                'parsed_date': parse_date(record.get('earliest_date', '')),
                'relative_time': get_relative_time_from_timestamp(record.get('createdon', '')),
                'total_dates_available': record.get('no_of_dates', 0),
                'total_appointments': record.get('no_of_apnts', 0)
            }
            
            all_records.append(enhanced_record)
            categories[category].append(enhanced_record)
            locations[record.get('visa_location', 'Unknown')].append(enhanced_record)
            
            total_slots += record.get('no_of_dates', 0)
            total_appointments += record.get('no_of_apnts', 0)
    
    print(f"📊 Total Records: {len(all_records)}")
    print(f"🎯 Total Available Dates: {total_slots}")
    print(f"📅 Total Appointments: {total_appointments}")
    print(f"🏢 Locations Covered: {len(locations)}")
    print(f"📋 Visa Categories: {len(categories)}")
    
    # Category Analysis
    print(f"\n📋 VISA CATEGORIES BREAKDOWN:")
    print("-" * 50)
    category_stats = []
    
    for category, records in categories.items():
        total_category_slots = sum(r.get('total_dates_available', 0) for r in records)
        total_category_appts = sum(r.get('total_appointments', 0) for r in records)
        unique_locations = len(set(r.get('visa_location') for r in records))
        
        category_stats.append((category, len(records), total_category_slots, total_category_appts, unique_locations))
        
        print(f"🔸 {category}:")
        print(f"   └── {len(records)} records across {unique_locations} locations")
        print(f"   └── {total_category_slots} available dates, {total_category_appts} appointments")
    
    # Location Analysis
    print(f"\n🏢 CONSULATE LOCATIONS ANALYSIS:")
    print("-" * 50)
    location_stats = []
    
    for location, records in locations.items():
        total_location_slots = sum(r.get('total_dates_available', 0) for r in records)
        total_location_appts = sum(r.get('total_appointments', 0) for r in records)
        visa_types = set(r.get('visa_type') for r in records)
        
        location_stats.append((location, total_location_slots, total_location_appts, len(visa_types)))
        
        status_emoji = "🟢" if total_location_slots > 10 else "🟡" if total_location_slots > 0 else "🔴"
        print(f"{status_emoji} {location}:")
        print(f"   └── {total_location_slots} available dates, {total_location_appts} appointments")
        print(f"   └── {len(visa_types)} visa types: {', '.join(list(visa_types)[:3])}")
        if len(visa_types) > 3:
            print(f"       (and {len(visa_types) - 3} more...)")
    
    # Earliest Available Dates
    print(f"\n⚡ EARLIEST AVAILABLE APPOINTMENTS:")
    print("-" * 50)
    
    # Sort by parsed date
    sorted_records = sorted(
        [r for r in all_records if r.get('earliest_date') and r.get('earliest_date') != 'No dates'],
        key=lambda x: x.get('parsed_date', '9999-12-31')
    )
    
    for i, record in enumerate(sorted_records[:10], 1):
        location = record.get('visa_location', 'Unknown')
        visa_type = record.get('visa_type', 'Unknown')
        date = record.get('earliest_date', 'Unknown')
        slots = record.get('total_dates_available', 0)
        appts = record.get('total_appointments', 0)
        relative = record.get('relative_time', 'Unknown')
        
        print(f"{i:2}. {location} - {visa_type}")
        print(f"    📅 {date} ({slots} dates, {appts} appointments) - Last seen: {relative}")
    
    # High Availability Locations
    print(f"\n🚀 HIGHEST AVAILABILITY LOCATIONS:")
    print("-" * 50)
    
    # Sort by total slots
    location_stats.sort(key=lambda x: x[1], reverse=True)
    
    for i, (location, slots, appts, types) in enumerate(location_stats[:8], 1):
        print(f"{i}. {location}: {slots} dates, {appts} appointments ({types} visa types)")
    
    # Key Insights
    print(f"\n💡 KEY INSIGHTS:")
    print("-" * 50)
    
    best_location = location_stats[0] if location_stats else None
    best_category = max(category_stats, key=lambda x: x[2]) if category_stats else None
    
    print(f"• Total availability: {total_slots} dates across {len(locations)} locations")
    if best_location:
        print(f"• Best location: {best_location[0]} ({best_location[1]} dates)")
    if best_category:
        print(f"• Most available category: {best_category[0]} ({best_category[2]} dates)")
    
    # Recent updates
    recent_records = sorted(all_records, key=lambda x: x.get('createdon', ''), reverse=True)[:5]
    print(f"• Most recent updates:")
    for record in recent_records:
        loc = record.get('visa_location', 'Unknown')
        rel_time = record.get('relative_time', 'Unknown')
        print(f"  - {loc}: {rel_time}")
    
    return {
        'total_records': len(all_records),
        'total_slots': total_slots,
        'total_appointments': total_appointments,
        'categories': dict(categories),
        'locations': dict(locations),
        'sorted_by_date': sorted_records,
        'category_stats': category_stats,
        'location_stats': location_stats
    }

def main():
    """Main function"""
    print("🌐 LIVE VISA DATA ANALYSIS")
    print("=" * 40)
    
    # Load live data
    data = load_live_data()
    if not data:
        print("❌ Could not load live data. Run live_scraper.py first.")
        return
    
    # Analyze the data
    analysis = analyze_live_data(data)
    
    if analysis:
        # Save processed analysis
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"live_analysis_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                'analysis_time': datetime.now().isoformat(),
                'source': 'checkvisaslots.com live data',
                'raw_data_file': 'live_visa_data.json',
                'summary': analysis
            }, f, indent=2, default=str)
        
        print(f"\n💾 Analysis saved to: {filename}")
        print(f"📄 Raw data available in: live_visa_data.json")

if __name__ == "__main__":
    main()
