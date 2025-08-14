#!/usr/bin/env python3
"""
Live Visa Table Formatter
Creates organized tables showing visa availability by type, location, and subtype
Exports data to CSV and Excel formats
"""

import json
import csv
import os
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import sys

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

# IST timezone helper functions
def get_ist_now():
    """Get current datetime in IST (UTC+5:30)"""
    ist_offset = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist_offset)

def get_ist_timestamp():
    """Get current IST timestamp as ISO string"""
    return get_ist_now().isoformat()

def load_live_data():
    """Load the live data JSON file"""
    try:
        with open('live_visa_data.json', 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"❌ Error loading live data: {str(e)}")
        print("💡 Run live_scraper.py first to fetch the data")
        return None

def parse_date(date_str):
    """Parse date string to a comparable format"""
    try:
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

def get_relative_time(timestamp_str):
    """Calculate relative time from timestamp (adjusted for data source delay)"""
    try:
        dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        
        # Add 5.5 hours to compensate for known data source delay
        # This makes the times more accurate to actual visa slot updates
        adjusted_dt = dt + timedelta(hours=5, minutes=30)
        
        # Compare with IST time (remove timezone info for comparison)
        now = get_ist_now().replace(tzinfo=None)
        diff = now - adjusted_dt
        
        if diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours}h ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes}m ago"
        else:
            return "Now"
    except Exception:
        return "Unknown"

def extract_visa_subtype(visa_type):
    """Extract the subtype (Regular/Dropbox/Emergency) from visa type"""
    if '(Dropbox)' in visa_type:
        return 'Dropbox'
    elif '(Emergency)' in visa_type:
        return 'Emergency'
    elif '(Regular)' in visa_type:
        return 'Regular'
    elif '(Blanket)' in visa_type:
        return 'Blanket'
    else:
        return 'Other'

def extract_base_visa_type(visa_type):
    """Extract the base visa type (B1, B2, F1, etc.) from full visa type"""
    # Remove parenthetical parts
    base = visa_type.split('(')[0].strip()
    return base

def create_visa_tables(data):
    """Create organized tables for each visa type"""
    if not data or 'result' not in data:
        print("❌ No valid data to process")
        return
    
    print("\n" + "="*80)
    print("📊 US VISA AVAILABILITY - TABLE FORMAT")
    print("="*80)
    print(f"📡 Data Source: checkvisaslots.com")
    print(f"🕐 Generated: {get_ist_now().strftime('%Y-%m-%d %H:%M:%S IST')}")
    
    # Group data by base visa type
    visa_groups = defaultdict(list)
    
    for visa_type, records in data['result'].items():
        base_type = extract_base_visa_type(visa_type)
        for record in records:
            enhanced_record = {
                **record,
                'base_visa_type': base_type,
                'full_visa_type': visa_type,
                'subtype': extract_visa_subtype(visa_type),
                'parsed_date': parse_date(record.get('earliest_date', '')),
                'relative_time': get_relative_time(record.get('createdon', '')),
                'dates': record.get('no_of_dates', 0),
                'appointments': record.get('no_of_apnts', 0)
            }
            visa_groups[base_type].append(enhanced_record)
    
    # Sort visa types for consistent output
    sorted_visa_types = sorted(visa_groups.keys())
    
    for base_visa_type in sorted_visa_types:
        records = visa_groups[base_visa_type]
        
        # Sort records by location and subtype
        records.sort(key=lambda x: (x.get('visa_location', ''), x.get('subtype', '')))
        
        print(f"\n" + "="*60)
        print(f"🎯 {base_visa_type} VISA AVAILABILITY")
        print("="*60)
        
        # Count subtypes
        subtypes = set(r.get('subtype') for r in records)
        locations = set(r.get('visa_location') for r in records)
        total_dates = sum(r.get('dates', 0) for r in records)
        total_appointments = sum(r.get('appointments', 0) for r in records)
        
        print(f"📍 Locations: {len(locations)} | 📋 Subtypes: {', '.join(sorted(subtypes))}")
        print(f"📅 Total Dates: {total_dates} | 🎫 Total Appointments: {total_appointments}")
        
        # Create table header
        print(f"\n{'Location':<15} {'Type':<12} {'Earliest Date':<15} {'Dates':<8} {'Appts':<8} {'Last Seen':<12}")
        print("-" * 80)
        
        # Display records
        for record in records:
            location = record.get('visa_location', 'Unknown')[:14]
            subtype = record.get('subtype', 'Unknown')[:11]
            earliest = record.get('earliest_date', 'N/A')[:14]
            dates = str(record.get('dates', 0))
            appts = str(record.get('appointments', 0))
            last_seen = record.get('relative_time', 'Unknown')[:11]
            
            print(f"{location:<15} {subtype:<12} {earliest:<15} {dates:<8} {appts:<8} {last_seen:<12}")
    
    return visa_groups

def create_summary_table(visa_groups):
    """Create a summary table showing all visa types"""
    print(f"\n" + "="*80)
    print("📋 VISA TYPES SUMMARY")
    print("="*80)
    
    print(f"{'Visa Type':<15} {'Locations':<12} {'Subtypes':<20} {'Total Dates':<12} {'Total Appts':<12}")
    print("-" * 80)
    
    summary_data = []
    
    for visa_type, records in visa_groups.items():
        locations = len(set(r.get('visa_location') for r in records))
        subtypes = sorted(set(r.get('subtype') for r in records))
        subtypes_str = ', '.join(subtypes)[:19]
        total_dates = sum(r.get('dates', 0) for r in records)
        total_appts = sum(r.get('appointments', 0) for r in records)
        
        summary_data.append((visa_type, locations, subtypes_str, total_dates, total_appts))
    
    # Sort by total dates (descending)
    summary_data.sort(key=lambda x: x[3], reverse=True)
    
    for visa_type, locations, subtypes_str, total_dates, total_appts in summary_data:
        print(f"{visa_type:<15} {locations:<12} {subtypes_str:<20} {total_dates:<12} {total_appts:<12}")

def create_location_summary(visa_groups):
    """Create a location-wise summary"""
    print(f"\n" + "="*80)
    print("🏢 LOCATION SUMMARY")
    print("="*80)
    
    location_data = defaultdict(lambda: {'visa_types': set(), 'dates': 0, 'appointments': 0})
    
    for visa_type, records in visa_groups.items():
        for record in records:
            location = record.get('visa_location', 'Unknown')
            location_data[location]['visa_types'].add(visa_type)
            location_data[location]['dates'] += record.get('dates', 0)
            location_data[location]['appointments'] += record.get('appointments', 0)
    
    print(f"{'Location':<20} {'Visa Types':<12} {'Total Dates':<12} {'Total Appts':<12}")
    print("-" * 80)
    
    # Sort by total dates
    sorted_locations = sorted(location_data.items(), key=lambda x: x[1]['dates'], reverse=True)
    
    for location, data in sorted_locations:
        visa_count = len(data['visa_types'])
        dates = data['dates']
        appointments = data['appointments']
        
        print(f"{location:<20} {visa_count:<12} {dates:<12} {appointments:<12}")

def create_detailed_b_visa_table(visa_groups):
    """Create a detailed table specifically for B1/B2 visas"""
    b_visas = {}
    
    # Collect all B visa types
    for visa_type in visa_groups.keys():
        if any(b_type in visa_type.upper() for b_type in ['B1', 'B2', 'B1/B2']):
            b_visas[visa_type] = visa_groups[visa_type]
    
    if not b_visas:
        print("\n❌ No B1/B2 visa data found")
        return
    
    print(f"\n" + "="*100)
    print("🎯 B1/B2 BUSINESS & TOURISM VISAS - DETAILED VIEW")
    print("="*100)
    
    all_b_records = []
    for visa_type, records in b_visas.items():
        all_b_records.extend(records)
    
    # Sort by location and subtype
    all_b_records.sort(key=lambda x: (x.get('visa_location', ''), x.get('subtype', '')))
    
    print(f"{'Location':<18} {'Visa Type':<12} {'Subtype':<10} {'Earliest Date':<15} {'Dates':<6} {'Appts':<6} {'Last Seen':<12}")
    print("-" * 100)
    
    for record in all_b_records:
        location = record.get('visa_location', 'Unknown')[:17]
        base_type = record.get('base_visa_type', 'Unknown')[:11]
        subtype = record.get('subtype', 'Unknown')[:9]
        earliest = record.get('earliest_date', 'N/A')[:14]
        dates = str(record.get('dates', 0))
        appts = str(record.get('appointments', 0))
        last_seen = record.get('relative_time', 'Unknown')[:11]
        
        print(f"{location:<18} {base_type:<12} {subtype:<10} {earliest:<15} {dates:<6} {appts:<6} {last_seen:<12}")

def export_to_csv(visa_groups, timestamp):
    """Export visa data to CSV files"""
    output_dir = f"visa_exports_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n📁 Creating CSV exports in: {output_dir}/")
    
    # 1. Master table with all data
    master_data = []
    for visa_type, records in visa_groups.items():
        for record in records:
            master_data.append({
                'Base_Visa_Type': record.get('base_visa_type'),
                'Full_Visa_Type': record.get('full_visa_type'),
                'Location': record.get('visa_location'),
                'Subtype': record.get('subtype'),
                'Earliest_Date': record.get('earliest_date'),
                'Number_of_Dates': record.get('dates', 0),
                'Number_of_Appointments': record.get('appointments', 0),
                'Last_Updated': record.get('createdon'),
                'Relative_Time': record.get('relative_time')
            })
    
    # Save master CSV
    master_file = os.path.join(output_dir, 'master_visa_data.csv')
    with open(master_file, 'w', newline='', encoding='utf-8') as f:
        if master_data:
            writer = csv.DictWriter(f, fieldnames=master_data[0].keys())
            writer.writeheader()
            writer.writerows(master_data)
    print(f"✅ Master data: master_visa_data.csv ({len(master_data)} records)")
    
    # 2. Individual CSV files for each visa type
    for visa_type, records in visa_groups.items():
        filename = f"{visa_type.replace('/', '_').replace(' ', '_')}_visas.csv"
        filepath = os.path.join(output_dir, filename)
        
        visa_data = []
        for record in records:
            visa_data.append({
                'Location': record.get('visa_location'),
                'Subtype': record.get('subtype'),
                'Earliest_Date': record.get('earliest_date'),
                'Number_of_Dates': record.get('dates', 0),
                'Number_of_Appointments': record.get('appointments', 0),
                'Last_Updated': record.get('createdon'),
                'Relative_Time': record.get('relative_time')
            })
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            if visa_data:
                writer = csv.DictWriter(f, fieldnames=visa_data[0].keys())
                writer.writeheader()
                writer.writerows(visa_data)
        print(f"✅ {visa_type}: {filename} ({len(visa_data)} records)")
    
    # 3. B1/B2 specific CSV
    b_visa_data = []
    for visa_type, records in visa_groups.items():
        if any(b_type in visa_type.upper() for b_type in ['B1', 'B2', 'B1/B2']):
            for record in records:
                b_visa_data.append({
                    'Visa_Type': record.get('base_visa_type'),
                    'Location': record.get('visa_location'),
                    'Subtype': record.get('subtype'),
                    'Earliest_Date': record.get('earliest_date'),
                    'Number_of_Dates': record.get('dates', 0),
                    'Number_of_Appointments': record.get('appointments', 0),
                    'Last_Updated': record.get('createdon')
                })
    
    if b_visa_data:
        b_visa_file = os.path.join(output_dir, 'B1_B2_tourist_business_visas.csv')
        with open(b_visa_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=b_visa_data[0].keys())
            writer.writeheader()
            writer.writerows(b_visa_data)
        print(f"✅ B1/B2 Tourist & Business: B1_B2_tourist_business_visas.csv ({len(b_visa_data)} records)")
    
    # 4. Location summary CSV
    location_summary = []
    location_data = defaultdict(lambda: {'visa_types': set(), 'dates': 0, 'appointments': 0})
    
    for visa_type, records in visa_groups.items():
        for record in records:
            location = record.get('visa_location', 'Unknown')
            location_data[location]['visa_types'].add(visa_type)
            location_data[location]['dates'] += record.get('dates', 0)
            location_data[location]['appointments'] += record.get('appointments', 0)
    
    for location, data in location_data.items():
        location_summary.append({
            'Location': location,
            'Number_of_Visa_Types': len(data['visa_types']),
            'Visa_Types': ', '.join(sorted(data['visa_types'])),
            'Total_Dates_Available': data['dates'],
            'Total_Appointments': data['appointments']
        })
    
    location_file = os.path.join(output_dir, 'location_summary.csv')
    with open(location_file, 'w', newline='', encoding='utf-8') as f:
        if location_summary:
            writer = csv.DictWriter(f, fieldnames=location_summary[0].keys())
            writer.writeheader()
            writer.writerows(location_summary)
    print(f"✅ Location Summary: location_summary.csv ({len(location_summary)} locations)")
    
    return output_dir

def export_to_excel(visa_groups, timestamp):
    """Export visa data to Excel file with multiple sheets"""
    if not PANDAS_AVAILABLE:
        print("⚠️  Pandas not available - skipping Excel export")
        return None
    
    excel_filename = f"visa_availability_{timestamp}.xlsx"
    print(f"\n📊 Creating Excel file: {excel_filename}")
    
    with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
        # Sheet 1: Master data
        master_data = []
        for visa_type, records in visa_groups.items():
            for record in records:
                master_data.append({
                    'Base_Visa_Type': record.get('base_visa_type'),
                    'Full_Visa_Type': record.get('full_visa_type'),
                    'Location': record.get('visa_location'),
                    'Subtype': record.get('subtype'),
                    'Earliest_Date': record.get('earliest_date'),
                    'Number_of_Dates': record.get('dates', 0),
                    'Number_of_Appointments': record.get('appointments', 0),
                    'Last_Updated': record.get('createdon'),
                    'Relative_Time': record.get('relative_time')
                })
        
        if master_data:
            df_master = pd.DataFrame(master_data)
            df_master.to_excel(writer, sheet_name='Master_Data', index=False)
        
        # Sheet 2: B1/B2 visas
        b_visa_data = []
        for visa_type, records in visa_groups.items():
            if any(b_type in visa_type.upper() for b_type in ['B1', 'B2', 'B1/B2']):
                for record in records:
                    b_visa_data.append({
                        'Visa_Type': record.get('base_visa_type'),
                        'Location': record.get('visa_location'),
                        'Subtype': record.get('subtype'),
                        'Earliest_Date': record.get('earliest_date'),
                        'Number_of_Dates': record.get('dates', 0),
                        'Number_of_Appointments': record.get('appointments', 0),
                        'Last_Updated': record.get('createdon')
                    })
        
        if b_visa_data:
            df_b_visas = pd.DataFrame(b_visa_data)
            df_b_visas.to_excel(writer, sheet_name='B1_B2_Tourist_Business', index=False)
        
        # Sheet 3: Location summary
        location_data = defaultdict(lambda: {'visa_types': set(), 'dates': 0, 'appointments': 0})
        
        for visa_type, records in visa_groups.items():
            for record in records:
                location = record.get('visa_location', 'Unknown')
                location_data[location]['visa_types'].add(visa_type)
                location_data[location]['dates'] += record.get('dates', 0)
                location_data[location]['appointments'] += record.get('appointments', 0)
        
        location_summary = []
        for location, data in location_data.items():
            location_summary.append({
                'Location': location,
                'Number_of_Visa_Types': len(data['visa_types']),
                'Visa_Types': ', '.join(sorted(data['visa_types'])),
                'Total_Dates_Available': data['dates'],
                'Total_Appointments': data['appointments']
            })
        
        if location_summary:
            df_locations = pd.DataFrame(location_summary)
            df_locations.to_excel(writer, sheet_name='Location_Summary', index=False)
        
        # Sheet 4: Individual visa type sheets (top 5 most available)
        visa_type_counts = [(visa_type, sum(r.get('dates', 0) for r in records)) 
                           for visa_type, records in visa_groups.items()]
        visa_type_counts.sort(key=lambda x: x[1], reverse=True)
        
        for i, (visa_type, _) in enumerate(visa_type_counts[:5]):  # Top 5 visa types
            records = visa_groups[visa_type]
            visa_data = []
            for record in records:
                visa_data.append({
                    'Location': record.get('visa_location'),
                    'Subtype': record.get('subtype'),
                    'Earliest_Date': record.get('earliest_date'),
                    'Number_of_Dates': record.get('dates', 0),
                    'Number_of_Appointments': record.get('appointments', 0),
                    'Last_Updated': record.get('createdon')
                })
            
            if visa_data:
                df_visa = pd.DataFrame(visa_data)
                # Clean sheet name for Excel
                sheet_name = visa_type.replace('/', '_').replace(' ', '_')[:31]
                df_visa.to_excel(writer, sheet_name=sheet_name, index=False)
    
    print(f"✅ Excel file created: {excel_filename}")
    return excel_filename

def main():
    """Main function"""
    print("📊 VISA AVAILABILITY TABLE FORMATTER")
    print("=" * 50)
    
    # Load live data
    data = load_live_data()
    if not data:
        return
    
    # Create visa tables
    visa_groups = create_visa_tables(data)
    if not visa_groups:
        return
    
    # Create summary tables
    create_summary_table(visa_groups)
    create_location_summary(visa_groups)
    
    # Create detailed B visa table
    create_detailed_b_visa_table(visa_groups)
    
    # Generate timestamp for exports
    timestamp = get_ist_now().strftime('%Y%m%d_%H%M%S')
    
    # Export to text file
    filename = f"visa_tables_{timestamp}.txt"
    
    # Redirect output to file
    original_stdout = sys.stdout
    with open(filename, 'w') as f:
        sys.stdout = f
        
        # Regenerate all tables for file
        create_visa_tables(data)
        create_summary_table(visa_groups)
        create_location_summary(visa_groups)
        create_detailed_b_visa_table(visa_groups)
    
    sys.stdout = original_stdout
    
    print(f"\n💾 Tables saved to: {filename}")
    
    # Export to CSV files
    try:
        csv_dir = export_to_csv(visa_groups, timestamp)
        print(f"� CSV files directory: {csv_dir}/")
    except Exception as e:
        print(f"❌ Error creating CSV files: {str(e)}")
    
    # Export to Excel file
    try:
        excel_file = export_to_excel(visa_groups, timestamp)
        if excel_file:
            print(f"📊 Excel file: {excel_file}")
    except Exception as e:
        print(f"❌ Error creating Excel file: {str(e)}")
    
    print(f"\n🎯 EXPORT SUMMARY")
    print("=" * 50)
    print(f"�📄 Text tables: {filename}")
    if 'csv_dir' in locals():
        print(f"📁 CSV files: {csv_dir}/")
    if 'excel_file' in locals() and excel_file:
        print(f"📊 Excel file: {excel_file}")
    print(f"🕐 Generated at: {get_ist_now().strftime('%Y-%m-%d %H:%M:%S IST')}")
    
    # Show file sizes and record counts
    total_records = sum(len(records) for records in visa_groups.values())
    print(f"📊 Total records processed: {total_records}")
    print(f"🎯 Visa types found: {len(visa_groups)}")
    
    # B1/B2 specific summary
    b_visa_count = 0
    for visa_type, records in visa_groups.items():
        if any(b_type in visa_type.upper() for b_type in ['B1', 'B2', 'B1/B2']):
            b_visa_count += len(records)
    
    if b_visa_count > 0:
        print(f"🎫 B1/B2 Tourist & Business records: {b_visa_count}")
    
    print("\n✅ All exports completed successfully!")
    print("💡 Use the CSV files for data analysis or the Excel file for easy viewing")

if __name__ == "__main__":
    main()
