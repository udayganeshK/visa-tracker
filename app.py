#!/usr/bin/env python3
"""
Visa Tracker Web Application
Web UI for visa slot notifications with email alerts
"""

from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
import json
import os
from datetime import datetime
import threading
import time
import sys
import subprocess

app = Flask(__name__)
app.secret_key = 'visa_tracker_secret_key_2025'

# Configuration
NOTIFICATIONS_FILE = 'notifications.json'

def load_live_data():
    """Load the live data JSON file"""
    try:
        with open('live_visa_data.json', 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"❌ Error loading live data: {str(e)}")
        return None

def fetch_live_data():
    """Fetch live data by running the scraper"""
    try:
        result = subprocess.run([sys.executable, 'live_scraper.py'], 
                              capture_output=True, text=True, cwd='/Users/udaykanteti/visa-tracker')
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error fetching data: {str(e)}")
        return False

def create_visa_tables(data):
    """Create organized tables for each visa type"""
    if not data or 'result' not in data:
        return {}
    
    from collections import defaultdict
    
    # Group data by base visa type
    visa_groups = defaultdict(list)
    
    for visa_type, records in data['result'].items():
        base_type = visa_type.split('(')[0].strip()
        for record in records:
            enhanced_record = {
                **record,
                'base_visa_type': base_type,
                'full_visa_type': visa_type,
                'subtype': 'Dropbox' if '(Dropbox)' in visa_type else 'Regular',
                'dates': record.get('no_of_dates', 0),
                'appointments': record.get('no_of_apnts', 0),
                'relative_time': 'Recently'
            }
            visa_groups[base_type].append(enhanced_record)
    
    return visa_groups

def load_notifications():
    """Load notification subscriptions from file"""
    if os.path.exists(NOTIFICATIONS_FILE):
        try:
            with open(NOTIFICATIONS_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_notifications(notifications):
    """Save notification subscriptions to file"""
    with open(NOTIFICATIONS_FILE, 'w') as f:
        json.dump(notifications, f, indent=2)

def get_available_visa_types():
    """Get list of available visa types from current data"""
    try:
        data = load_live_data()
        if data and 'result' in data:
            visa_types = []
            for visa_type in data['result'].keys():
                # Extract base type
                base_type = visa_type.split('(')[0].strip()
                if base_type not in visa_types:
                    visa_types.append(base_type)
            return sorted(visa_types)
    except:
        pass
    
    # Default visa types if no data available
    return ['B1', 'B1/B2', 'B2', 'F1', 'H1B', 'L1', 'O1', 'J1', 'M1']

def get_available_locations():
    """Get list of available locations from current data"""
    try:
        data = load_live_data()
        if data and 'result' in data:
            locations = set()
            for records in data['result'].values():
                for record in records:
                    locations.add(record.get('visa_location', ''))
            return sorted(list(locations))
    except:
        pass
    
    # Default locations if no data available
    return ['CHENNAI', 'CHENNAI VAC', 'MUMBAI', 'MUMBAI VAC', 'NEW DELHI', 'NEW DELHI VAC', 
            'HYDERABAD', 'HYDERABAD VAC', 'KOLKATA', 'KOLKATA VAC']

def send_email_notification(email, visa_matches):
    """Send email notification for visa availability"""
    try:
        print(f"\n📧 EMAIL NOTIFICATION TO: {email}")
        print("="*50)
        print("🎯 US VISA SLOTS AVAILABLE!")
        print(f"📅 Found {len(visa_matches)} matching visa appointments\n")
        
        for match in visa_matches:
            print(f"🔹 {match['visa_type']} at {match['location']}")
            print(f"   📍 {match['subtype']} | 📅 {match['earliest_date']} | 🎫 {match['appointments']} slots")
        
        print(f"\n🔗 Check full details at: http://localhost:5000")
        print("="*50)
        
        return True
    except Exception as e:
        print(f"❌ Error sending email to {email}: {str(e)}")
        return False

def check_and_notify():
    """Check for visa availability and send notifications"""
    print("🔍 Checking for visa availability...")
    
    # Fetch latest data
    try:
        fetch_live_data()
        data = load_live_data()
        if not data:
            print("❌ No data available for notifications")
            return
    except Exception as e:
        print(f"❌ Error fetching data: {str(e)}")
        return
    
    notifications = load_notifications()
    if not notifications:
        print("📭 No notification subscriptions found")
        return
    
    print(f"📬 Checking {len(notifications)} notification subscriptions...")
    
    for notification in notifications:
        email = notification['email']
        visa_types = notification['visa_types']
        locations = notification['locations']
        
        matches = []
        
        # Check each visa type in the data
        for visa_type_key, records in data['result'].items():
            base_type = visa_type_key.split('(')[0].strip()
            
            # Check if this visa type matches user preferences
            if base_type in visa_types:
                for record in records:
                    location = record.get('visa_location', '')
                    
                    # Check if location matches (if specific locations selected)
                    if not locations or location in locations:
                        matches.append({
                            'visa_type': base_type,
                            'location': location,
                            'subtype': visa_type_key.split('(')[1].replace(')', '') if '(' in visa_type_key else 'Regular',
                            'earliest_date': record.get('earliest_date', 'N/A'),
                            'appointments': record.get('no_of_apnts', 0)
                        })
        
        # Send notification if matches found
        if matches:
            print(f"📧 Sending notification to {email} - {len(matches)} matches found")
            send_email_notification(email, matches)
        else:
            print(f"📭 No matches for {email}")

@app.route('/')
def index():
    """Main page"""
    try:
        # Try to load current data for display
        data = load_live_data()
        if data:
            visa_groups = create_visa_tables(data)
            current_data = True
        else:
            visa_groups = {}
            current_data = False
    except:
        visa_groups = {}
        current_data = False
    
    visa_types = get_available_visa_types()
    locations = get_available_locations()
    notifications = load_notifications()
    
    return render_template('index.html', 
                         visa_types=visa_types,
                         locations=locations,
                         notifications=notifications,
                         visa_groups=visa_groups,
                         current_data=current_data)

@app.route('/subscribe', methods=['POST'])
def subscribe():
    """Subscribe to visa notifications"""
    email = request.form.get('email', '').strip()
    visa_types = request.form.getlist('visa_types')
    locations = request.form.getlist('locations')
    
    if not email:
        flash('Please enter a valid email address', 'error')
        return redirect(url_for('index'))
    
    if not visa_types:
        flash('Please select at least one visa type', 'error')
        return redirect(url_for('index'))
    
    # Load existing notifications
    notifications = load_notifications()
    
    # Check if email already exists
    existing = next((n for n in notifications if n['email'] == email), None)
    
    if existing:
        # Update existing subscription
        existing['visa_types'] = visa_types
        existing['locations'] = locations
        existing['updated_at'] = datetime.now().isoformat()
        flash(f'Updated notification preferences for {email}', 'success')
    else:
        # Add new subscription
        notifications.append({
            'email': email,
            'visa_types': visa_types,
            'locations': locations,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        })
        flash(f'Subscribed {email} for visa notifications', 'success')
    
    save_notifications(notifications)
    return redirect(url_for('index'))

@app.route('/unsubscribe/<email>')
def unsubscribe(email):
    """Unsubscribe from notifications"""
    notifications = load_notifications()
    notifications = [n for n in notifications if n['email'] != email]
    save_notifications(notifications)
    flash(f'Unsubscribed {email} from notifications', 'success')
    return redirect(url_for('index'))

@app.route('/refresh')
def refresh_data():
    """Manually refresh visa data"""
    try:
        fetch_live_data()
        flash('Visa data refreshed successfully', 'success')
    except Exception as e:
        flash(f'Error refreshing data: {str(e)}', 'error')
    return redirect(url_for('index'))

@app.route('/check_notifications')
def check_notifications():
    """Manually trigger notification check"""
    try:
        check_and_notify()
        flash('Notification check completed', 'success')
    except Exception as e:
        flash(f'Error checking notifications: {str(e)}', 'error')
    return redirect(url_for('index'))

@app.route('/api/data')
def api_data():
    """API endpoint for current visa data"""
    try:
        data = load_live_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def background_checker():
    """Background thread to check for notifications periodically"""
    while True:
        try:
            check_and_notify()
        except Exception as e:
            print(f"❌ Background checker error: {str(e)}")
        
        # Wait 30 minutes before next check
        time.sleep(1800)

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Start background notification checker
    checker_thread = threading.Thread(target=background_checker, daemon=True)
    checker_thread.start()
    
    print("🚀 Starting Visa Tracker Web Application")
    print("📧 Email notifications enabled (demo mode)")
    print("🔄 Background checker started (30-minute intervals)")
    print("🌐 Access at: http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
