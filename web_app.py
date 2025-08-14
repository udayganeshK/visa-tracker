#!/usr/bin/env python3
"""
Visa Tracker Web Application with Email Notifications
Runs automated checks every 10 minutes and sends email alerts for fresh visa updates
"""

import os
import json
import smtplib
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

# Email imports
try:
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
except ImportError:
    try:
        from email.MIMEText import MIMEText
        from email.MIMEMultipart import MIMEMultipart
    except ImportError:
        print("Warning: Email functionality may not work properly")

# Import our existing scraper
import live_scraper
import table_formatter

app = Flask(__name__)
app.secret_key = 'visa-tracker-secret-key-2025'

# Global storage for subscriptions and data files
SUBSCRIPTIONS_FILE = 'subscriptions.json'
SUBSCRIPTIONS_BACKUP = 'subscriptions_backup.json'
LAST_CHECK_FILE = 'last_check.json'
EMAIL_LOG_FILE = 'email_log.json'
STATS_FILE = 'stats.json'

# Email configuration (using environment variables for security)
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'email': os.getenv('VISA_TRACKER_EMAIL', 'visa.tracker.alerts@gmail.com'),  # Set via environment variable
    'password': os.getenv('VISA_TRACKER_PASSWORD', 'your-gmail-app-password'),  # Set via environment variable
    'from_name': 'US Visa Tracker Alert'
}

def load_subscriptions():
    """Load user subscriptions from file with backup recovery"""
    try:
        # Try to load main file
        if os.path.exists(SUBSCRIPTIONS_FILE):
            with open(SUBSCRIPTIONS_FILE, 'r') as f:
                data = json.load(f)
                # Validate data structure
                if isinstance(data, list):
                    print(f"📂 Loaded {len(data)} subscriptions from {SUBSCRIPTIONS_FILE}")
                    return data
                else:
                    print(f"⚠️ Invalid data format in {SUBSCRIPTIONS_FILE}, trying backup...")
        
        # Try backup file if main file fails
        if os.path.exists(SUBSCRIPTIONS_BACKUP):
            with open(SUBSCRIPTIONS_BACKUP, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    print(f"📂 Restored {len(data)} subscriptions from backup")
                    # Restore main file from backup
                    save_subscriptions(data)
                    return data
        
        print("📂 No subscription data found, starting fresh")
        return []
        
    except Exception as e:
        print(f"❌ Error loading subscriptions: {e}")
        # Try to load backup as last resort
        try:
            if os.path.exists(SUBSCRIPTIONS_BACKUP):
                with open(SUBSCRIPTIONS_BACKUP, 'r') as f:
                    data = json.load(f)
                    print(f"📂 Emergency recovery: loaded {len(data)} subscriptions from backup")
                    return data
        except:
            pass
        return []

def save_subscriptions(subscriptions):
    """Save user subscriptions to file with backup"""
    try:
        # Validate data
        if not isinstance(subscriptions, list):
            raise ValueError("Subscriptions must be a list")
        
        # Create backup of existing file
        if os.path.exists(SUBSCRIPTIONS_FILE):
            try:
                import shutil
                shutil.copy2(SUBSCRIPTIONS_FILE, SUBSCRIPTIONS_BACKUP)
            except Exception as backup_error:
                print(f"⚠️ Warning: Could not create backup: {backup_error}")
        
        # Save new data
        with open(SUBSCRIPTIONS_FILE, 'w') as f:
            json.dump(subscriptions, f, indent=2, sort_keys=True)
        
        print(f"💾 Saved {len(subscriptions)} subscriptions to {SUBSCRIPTIONS_FILE}")
        
        # Update statistics
        update_stats('subscriptions_saved', len(subscriptions))
        
    except Exception as e:
        print(f"❌ Error saving subscriptions: {e}")
        raise

def load_email_log():
    """Load email sending log"""
    try:
        if os.path.exists(EMAIL_LOG_FILE):
            with open(EMAIL_LOG_FILE, 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error loading email log: {e}")
        return []

def log_email_sent(email, visa_alerts, success=True):
    """Log email sending activity"""
    try:
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'email': email,
            'alerts_count': len(visa_alerts),
            'success': success,
            'visa_types': [alert.get('visa_type', 'Unknown') for alert in visa_alerts]
        }
        
        # Load existing log
        email_log = load_email_log()
        email_log.append(log_entry)
        
        # Keep only last 1000 entries to prevent file from growing too large
        if len(email_log) > 1000:
            email_log = email_log[-1000:]
        
        # Save log
        with open(EMAIL_LOG_FILE, 'w') as f:
            json.dump(email_log, f, indent=2)
            
    except Exception as e:
        print(f"Warning: Could not log email activity: {e}")

def load_stats():
    """Load application statistics"""
    try:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, 'r') as f:
                return json.load(f)
        return {
            'emails_sent': 0,
            'emails_failed': 0,
            'subscriptions_created': 0,
            'subscriptions_updated': 0,
            'subscriptions_saved': 0,
            'checks_performed': 0,
            'last_startup': datetime.now().isoformat(),
            'app_version': '1.0'
        }
    except Exception as e:
        print(f"Error loading stats: {e}")
        return {}

def update_stats(key, value=None):
    """Update application statistics"""
    try:
        stats = load_stats()
        
        if value is not None:
            stats[key] = value
        else:
            # Increment counter
            stats[key] = stats.get(key, 0) + 1
        
        stats['last_updated'] = datetime.now().isoformat()
        
        with open(STATS_FILE, 'w') as f:
            json.dump(stats, f, indent=2)
            
    except Exception as e:
        print(f"Warning: Could not update stats: {e}")

def parse_relative_time(relative_time_str):
    """Parse relative time string to minutes"""
    if not relative_time_str or relative_time_str == 'Unknown':
        return float('inf')
    
    time_str = relative_time_str.lower().strip()
    
    if 'now' in time_str:
        return 0
    elif 'm ago' in time_str:
        return int(time_str.split('m')[0])
    elif 'h ago' in time_str:
        hours = int(time_str.split('h')[0])
        return hours * 60
    elif 'd ago' in time_str:
        days = int(time_str.split('d')[0])
        return days * 24 * 60
    else:
        return float('inf')

def send_confirmation_email(email, subscription_details):
    """Send subscription confirmation email to user"""
    try:
        msg = MIMEMultipart()
        msg['From'] = f"{EMAIL_CONFIG['from_name']} <{EMAIL_CONFIG['email']}>"
        msg['To'] = email
        msg['Subject'] = "✅ Visa Tracker Subscription Confirmed!"
        
        # Format visa types and locations for display
        visa_types_str = ", ".join(subscription_details['visa_types'])
        locations_str = ", ".join(subscription_details['locations']) if subscription_details['locations'] else "All locations"
        threshold_str = f"{subscription_details['alert_threshold']} minutes"
        
        # Create HTML email body
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #667eea; color: white; padding: 20px; text-align: center; border-radius: 10px; }}
                .content {{ background-color: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 10px; }}
                .subscription-details {{ background-color: white; padding: 15px; margin: 15px 0; border-left: 4px solid #667eea; }}
                .visa-list {{ background-color: #e3f2fd; padding: 10px; border-radius: 5px; margin: 10px 0; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #6c757d; }}
                .highlight {{ color: #667eea; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎉 Welcome to Visa Tracker!</h1>
                <p>Your subscription has been successfully confirmed</p>
            </div>
            
            <div class="content">
                <h2>📧 Subscription Confirmed for: {email}</h2>
                <p>Thank you for subscribing to our US Visa Slot Tracker! You will now receive automated email notifications when fresh visa appointments become available.</p>
                
                <div class="subscription-details">
                    <h3>📋 Your Subscription Details:</h3>
                    <div class="visa-list">
                        <strong>🎫 Visa Types:</strong><br>
                        {visa_types_str}
                    </div>
                    <p><strong>📍 Locations:</strong> {locations_str}</p>
                    <p><strong>⏰ Alert Threshold:</strong> {threshold_str}</p>
                    <p><strong>📅 Subscribed on:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                
                <h3>🤖 How it works:</h3>
                <ul>
                    <li><strong>Automated Monitoring:</strong> Our system checks for new visa slots every 10 minutes</li>
                    <li><strong>Smart Alerts:</strong> You'll get notifications only for appointments updated within your selected time threshold</li>
                    <li><strong>Personalized:</strong> Only visa types and locations you selected will trigger alerts</li>
                    <li><strong>Real-time:</strong> Get notified as soon as fresh appointments are detected</li>
                </ul>
                
                <div style="background-color: #d4edda; border: 1px solid #c3e6cb; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <strong>🔔 Next Steps:</strong>
                    <ul>
                        <li>Keep this email for your records</li>
                        <li>Add our email to your contacts to avoid spam filtering</li>
                        <li>You can update your subscription anytime by visiting our website</li>
                    </ul>
                </div>
            </div>
            
            <div class="footer">
                <p>🌐 Visit: <a href="http://localhost:7070">http://localhost:7070</a></p>
                <p>🤖 This confirmation was sent automatically by Visa Tracker</p>
                <p>📧 If you didn't subscribe, please ignore this email</p>
                <p>🕐 Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html'))
        
        # Send email
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()
        server.login(EMAIL_CONFIG['email'], EMAIL_CONFIG['password'])
        text = msg.as_string()
        server.sendmail(EMAIL_CONFIG['email'], email, text)
        server.quit()
        
        print(f"✅ Confirmation email sent to {email}")
        update_stats('emails_sent')
        log_email_sent(email, [{'visa_type': 'Confirmation Email', 'subtype': 'Welcome'}], success=True)
        return True
        
    except Exception as e:
        print(f"❌ Error sending confirmation email to {email}: {e}")
        update_stats('emails_failed')
        log_email_sent(email, [{'visa_type': 'Confirmation Email', 'subtype': 'Welcome'}], success=False)
        return False

def send_email_notification(email, visa_alerts):
    """Send email notification to user"""
    try:
        msg = MIMEMultipart()
        msg['From'] = f"{EMAIL_CONFIG['from_name']} <{EMAIL_CONFIG['email']}>"
        msg['To'] = email
        msg['Subject'] = f"🚨 Fresh Visa Slots Available! ({len(visa_alerts)} alerts)"
        
        # Create HTML email body
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
                .alert {{ background-color: #f8f9fa; border-left: 4px solid #28a745; margin: 10px 0; padding: 15px; }}
                .visa-type {{ font-weight: bold; color: #007bff; }}
                .location {{ color: #6c757d; }}
                .date {{ color: #dc3545; font-weight: bold; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #6c757d; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎯 Fresh Visa Slots Detected!</h1>
                <p>New appointments found within your alert threshold</p>
            </div>
            
            <h2>🚨 {len(visa_alerts)} New Visa Alerts</h2>
            <p>The following visa slots have been updated recently:</p>
        """
        
        for alert in visa_alerts:
            html_body += f"""
            <div class="alert">
                <div class="visa-type">{alert['visa_type']} ({alert['subtype']})</div>
                <div class="location">📍 {alert['location']}</div>
                <div class="date">📅 Earliest: {alert['earliest_date']}</div>
                <div>🎫 {alert['appointments']} appointments available ({alert['dates']} dates)</div>
                <div>🕐 Last updated: {alert['relative_time']}</div>
            </div>
            """
        
        html_body += f"""
            <div class="footer">
                <p>🤖 This is an automated alert from Visa Tracker</p>
                <p>📧 You're receiving this because you subscribed to visa notifications</p>
                <p>🕐 Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html'))
        
        # Send email
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()
        server.login(EMAIL_CONFIG['email'], EMAIL_CONFIG['password'])
        text = msg.as_string()
        server.sendmail(EMAIL_CONFIG['email'], email, text)
        server.quit()
        
        print(f"✅ Email sent to {email} with {len(visa_alerts)} alerts")
        update_stats('emails_sent')
        log_email_sent(email, visa_alerts, success=True)
        return True
        
    except Exception as e:
        print(f"❌ Error sending email to {email}: {e}")
        update_stats('emails_failed')
        log_email_sent(email, visa_alerts, success=False)
        return False

def check_for_fresh_visas():
    """Check for fresh visa updates and send notifications"""
    print(f"\n🔍 AUTOMATED VISA CHECK - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        update_stats('checks_performed')
        
        # Fetch latest data
        print("📡 Fetching latest visa data...")
        data = live_scraper.main()
        
        if not data or 'result' not in data:
            print("❌ No data fetched, skipping check")
            return
        
        # Load subscriptions
        subscriptions = load_subscriptions()
        if not subscriptions:
            print("📭 No active subscriptions")
            return
        
        print(f"👥 Checking {len(subscriptions)} subscriptions...")
        
        # Process visa data
        visa_groups = {}
        for visa_type, records in data['result'].items():
            base_type = table_formatter.extract_base_visa_type(visa_type)
            if base_type not in visa_groups:
                visa_groups[base_type] = []
            
            for record in records:
                enhanced_record = {
                    **record,
                    'base_visa_type': base_type,
                    'full_visa_type': visa_type,
                    'subtype': table_formatter.extract_visa_subtype(visa_type),
                    'relative_time': table_formatter.get_relative_time(record.get('createdon', '')),
                    'dates': record.get('no_of_dates', 0),
                    'appointments': record.get('no_of_apnts', 0)
                }
                visa_groups[base_type].append(enhanced_record)
        
        # Check each subscription
        alerts_sent = 0
        for subscription in subscriptions:
            email = subscription['email']
            visa_types = subscription['visa_types']
            locations = subscription.get('locations', [])
            user_threshold = subscription.get('alert_threshold', 15)  # User's alert threshold in minutes
            
            user_alerts = []
            
            print(f"👤 Checking subscription for {email}")
            print(f"   📋 Visa types: {visa_types}")
            print(f"   📍 Locations: {locations if locations else 'All locations'}")
            print(f"   ⏰ Alert threshold: {user_threshold} minutes")
            
            # Check subscribed visa types - direct match with data structure
            for subscribed_visa_type in visa_types:
                if subscribed_visa_type in data['result']:
                    records = data['result'][subscribed_visa_type]
                    print(f"   🔍 Found {len(records)} records for {subscribed_visa_type}")
                    
                    for record in records:
                        # Check if location matches (if specified)
                        record_location = record.get('visa_location', '')
                        if locations and record_location not in locations:
                            continue
                        
                        # Calculate time difference in minutes
                        created_time_str = record.get('createdon', '')
                        if created_time_str:
                            try:
                                created_time = datetime.strptime(created_time_str, '%Y-%m-%d %H:%M:%S')
                                time_diff_minutes = (datetime.now() - created_time).total_seconds() / 60
                                
                                print(f"      📊 {subscribed_visa_type} at {record_location}: {time_diff_minutes:.0f} min ago (threshold: {user_threshold})")
                                
                                # Check if update is fresh (within user's alert threshold)
                                if time_diff_minutes <= user_threshold:
                                    relative_time_str = table_formatter.get_relative_time(created_time_str)
                                    user_alerts.append({
                                        'visa_type': subscribed_visa_type,
                                        'subtype': table_formatter.extract_visa_subtype(subscribed_visa_type),
                                        'location': record_location,
                                        'earliest_date': record.get('earliest_date', 'N/A'),
                                        'dates': record.get('no_of_dates', 0),
                                        'appointments': record.get('no_of_apnts', 0),
                                        'relative_time': relative_time_str,
                                        'created_time': created_time_str
                                    })
                                    print(f"      ✅ ALERT! Fresh update within {user_threshold} min threshold")
                                else:
                                    print(f"      ⏰ Too old ({time_diff_minutes:.0f} min > {user_threshold} min)")
                            except ValueError as e:
                                print(f"      ❌ Error parsing date {created_time_str}: {e}")
                else:
                    print(f"   ❌ No data found for {subscribed_visa_type}")
            
            # Send email if there are alerts
            if user_alerts:
                print(f"   📧 Sending {len(user_alerts)} alerts to {email}")
                if send_email_notification(email, user_alerts):
                    alerts_sent += 1
                    print(f"   ✅ Email sent successfully to {email}")
                else:
                    print(f"   ❌ Failed to send email to {email}")
            else:
                print(f"   📭 No alerts for {email}")
        
        print(f"\n✅ Check complete: {alerts_sent} emails sent out of {len(subscriptions)} subscriptions")
        
        # Save last check time
        with open(LAST_CHECK_FILE, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'alerts_sent': alerts_sent,
                'subscriptions_checked': len(subscriptions)
            }, f)
        
    except Exception as e:
        print(f"❌ Error in automated check: {e}")

def automated_checker():
    """Run automated checks every 10 minutes"""
    print("🤖 Starting automated visa checker (every 10 minutes)")
    
    while True:
        try:
            check_for_fresh_visas()
            print(f"😴 Sleeping for 10 minutes... Next check at {(datetime.now() + timedelta(minutes=10)).strftime('%H:%M:%S')}")
            time.sleep(600)  # 10 minutes = 600 seconds
        except Exception as e:
            print(f"❌ Error in automated checker: {e}")
            time.sleep(60)  # Wait 1 minute before retrying

@app.route('/')
def index():
    """Main page with visa data and subscription form"""
    try:
        # Try to load existing visa data
        visa_data = None
        if os.path.exists('live_visa_data.json'):
            with open('live_visa_data.json', 'r') as f:
                data = json.load(f)
                if 'result' in data:
                    # Get available visa types and locations
                    visa_types = set()
                    locations = set()
                    preview_data = []
                    
                    for visa_type, records in data['result'].items():
                        base_type = table_formatter.extract_base_visa_type(visa_type)
                        visa_types.add(base_type)
                        
                        for record in records:
                            location = record.get('visa_location', 'Unknown')
                            locations.add(location)
                            
                            # Calculate relative time in minutes for sorting/display
                            relative_time = table_formatter.get_relative_time(record.get('createdon', ''))
                            relative_minutes = parse_relative_time(relative_time)
                            
                            preview_data.append({
                                'visa_type': visa_type,
                                'location': location,
                                'appointments': record.get('no_of_apnts', 0),
                                'earliest_date': record.get('earliest_date', 'N/A'),
                                'created_on': record.get('createdon', 'Unknown'),
                                'relative_time': relative_time,
                                'relative_minutes': relative_minutes
                            })
                    
                    # Sort by freshness (newest first)
                    preview_data.sort(key=lambda x: x['relative_minutes'])
                    
                    # Get the actual timestamp from the data file
                    last_updated_timestamp = data.get('createdon', datetime.now().timestamp() * 1000)
                    if isinstance(last_updated_timestamp, (int, float)):
                        # Convert from milliseconds to datetime
                        last_updated_dt = datetime.fromtimestamp(last_updated_timestamp / 1000)
                        last_updated_str = last_updated_dt.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        last_updated_str = str(last_updated_timestamp)
                    
                    visa_data = {
                        'visa_types': sorted(list(visa_types)),
                        'locations': sorted(list(locations)),
                        'preview': preview_data,
                        'total_records': len(preview_data),
                        'last_updated': last_updated_str
                    }
        
        if not visa_data:
            # Fallback data if no live data available
            visa_data = {
                'visa_types': ['B1', 'B2', 'B1/B2', 'F1', 'H1B', 'L1', 'H4', 'J1'],
                'locations': ['NEW DELHI VAC', 'MUMBAI VAC', 'CHENNAI VAC', 'HYDERABAD VAC', 'KOLKATA VAC'],
                'preview': [],
                'total_records': 0,
                'last_updated': None
            }
        
        # Load subscription count
        subscriptions = load_subscriptions()
        subscription_count = len(subscriptions)
        
        # Load last check info
        last_check_info = {}
        if os.path.exists(LAST_CHECK_FILE):
            with open(LAST_CHECK_FILE, 'r') as f:
                last_check_info = json.load(f)
        
        return render_template('index.html', 
                             visa_data=visa_data, 
                             subscription_count=subscription_count,
                             last_check_info=last_check_info)
        
    except Exception as e:
        flash(f'Error loading data: {str(e)}', 'error')
        return render_template('index.html', visa_data=None)

@app.route('/subscribe', methods=['POST'])
def subscribe():
    """Handle subscription form submission"""
    try:
        email = request.form.get('email', '').strip()
        visa_types = request.form.getlist('visa_types')
        locations = request.form.getlist('locations')
        alert_threshold = int(request.form.get('alert_threshold', 15))  # Default 15 minutes
        
        if not email or not visa_types:
            flash('Please provide email and select at least one visa type', 'error')
            return redirect(url_for('index'))
        
        # Load existing subscriptions
        subscriptions = load_subscriptions()
        
        # Check if email already exists
        existing_sub = None
        for i, sub in enumerate(subscriptions):
            if sub['email'] == email:
                existing_sub = i
                break
        
        # Create new subscription
        new_subscription = {
            'email': email,
            'visa_types': visa_types,
            'locations': locations if locations else [],
            'alert_threshold': alert_threshold,  # Store user's preference
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        if existing_sub is not None:
            subscriptions[existing_sub] = new_subscription
            flash(f'Subscription updated for {email}!', 'success')
            update_stats('subscriptions_updated')
            print(f"📝 Updated subscription: {email} for {visa_types}")
        else:
            subscriptions.append(new_subscription)
            flash(f'Successfully subscribed {email} for notifications!', 'success')
            update_stats('subscriptions_created')
            print(f"📝 New subscription: {email} for {visa_types}")
        
        # Save subscriptions
        save_subscriptions(subscriptions)
        
        # Send confirmation email
        try:
            if send_confirmation_email(email, new_subscription):
                flash(f'Confirmation email sent to {email}!', 'info')
                print(f"� Confirmation email sent to {email}")
            else:
                flash('Subscription successful, but confirmation email failed. Please check email configuration.', 'warning')
                print(f"⚠️ Failed to send confirmation email to {email}")
        except Exception as e:
            print(f"❌ Error sending confirmation email: {e}")
            flash('Subscription successful, but confirmation email failed.', 'warning')
        
    except Exception as e:
        flash(f'Error subscribing: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/test-alert', methods=['POST'])
def test_alert():
    """Send a test alert to verify email functionality"""
    try:
        email = request.form.get('email', '').strip()
        
        if not email:
            flash('Please provide an email address', 'error')
            return redirect(url_for('index'))
        
        # Create test alert
        test_alerts = [{
            'visa_type': 'B1/B2',
            'subtype': 'Regular',
            'location': 'NEW DELHI VAC',
            'earliest_date': '21 Aug, 25',
            'dates': 5,
            'appointments': 10,
            'relative_time': '5m ago'
        }]
        
        if send_email_notification(email, test_alerts):
            flash(f'Test email sent to {email}!', 'success')
        else:
            flash('Failed to send test email. Please check email configuration.', 'error')
        
    except Exception as e:
        flash(f'Error sending test email: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/fetch-latest')
def fetch_latest():
    """Manually fetch latest visa data"""
    try:
        print("🔄 Manual data fetch requested...")
        data = live_scraper.main()
        
        if data:
            # Run table formatter to create latest exports
            table_formatter.main()
            flash('Latest visa data fetched successfully!', 'success')
        else:
            flash('Failed to fetch latest data', 'error')
            
    except Exception as e:
        flash(f'Error fetching data: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/subscriptions')
def view_subscriptions():
    """View all active subscriptions"""
    subscriptions = load_subscriptions()
    return jsonify({
        'count': len(subscriptions),
        'subscriptions': subscriptions
    })

@app.route('/admin/subscriptions')
def admin_subscriptions():
    """View all subscriptions (admin route)"""
    try:
        subscriptions = load_subscriptions()
        email_log = load_email_log()
        stats = load_stats()
        
        return jsonify({
            "subscriptions": subscriptions,
            "total_subscriptions": len(subscriptions),
            "email_log_entries": len(email_log),
            "recent_emails": email_log[-10:] if email_log else [],
            "statistics": stats,
            "data_files": {
                "subscriptions_file": SUBSCRIPTIONS_FILE,
                "backup_file": SUBSCRIPTIONS_BACKUP,
                "email_log_file": EMAIL_LOG_FILE,
                "stats_file": STATS_FILE,
                "files_exist": {
                    "subscriptions": os.path.exists(SUBSCRIPTIONS_FILE),
                    "backup": os.path.exists(SUBSCRIPTIONS_BACKUP),
                    "email_log": os.path.exists(EMAIL_LOG_FILE),
                    "stats": os.path.exists(STATS_FILE)
                }
            }
        })
    except Exception as e:
        return jsonify({"error": f"Failed to load admin data: {str(e)}"}), 500

@app.route('/admin/backup', methods=['POST'])
def admin_backup():
    """Create manual backup of all data"""
    try:
        import shutil
        from datetime import datetime
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_files = {}
        
        # Backup subscriptions
        if os.path.exists(SUBSCRIPTIONS_FILE):
            backup_name = f"subscriptions_backup_{timestamp}.json"
            shutil.copy2(SUBSCRIPTIONS_FILE, backup_name)
            backup_files['subscriptions'] = backup_name
        
        # Backup email log
        if os.path.exists(EMAIL_LOG_FILE):
            backup_name = f"email_log_backup_{timestamp}.json"
            shutil.copy2(EMAIL_LOG_FILE, backup_name)
            backup_files['email_log'] = backup_name
        
        # Backup stats
        if os.path.exists(STATS_FILE):
            backup_name = f"stats_backup_{timestamp}.json"
            shutil.copy2(STATS_FILE, backup_name)
            backup_files['stats'] = backup_name
        
        return jsonify({
            "success": True,
            "message": f"Backup created with timestamp {timestamp}",
            "backup_files": backup_files
        })
        
    except Exception as e:
        return jsonify({"error": f"Backup failed: {str(e)}"}), 500

@app.route('/admin/export/<email>')
def admin_export_user(email):
    """Export data for a specific user"""
    try:
        subscriptions = load_subscriptions()
        email_log = load_email_log()
        
        # Find user subscription
        user_subscription = None
        for sub in subscriptions:
            if sub['email'] == email:
                user_subscription = sub
                break
        
        if not user_subscription:
            return jsonify({"error": f"No subscription found for {email}"}), 404
        
        # Find user's email history
        user_emails = [log for log in email_log if log.get('email') == email]
        
        return jsonify({
            "email": email,
            "subscription": user_subscription,
            "email_history": user_emails,
            "total_emails_sent": sum(1 for log in user_emails if log.get('success')),
            "total_emails_failed": sum(1 for log in user_emails if not log.get('success')),
            "export_timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": f"Export failed: {str(e)}"}), 500

@app.route('/admin/reset-data', methods=['POST'])
def admin_reset_data():
    """Reset all application data (DANGER!)"""
    try:
        # This is a dangerous operation, require confirmation
        confirmation = request.json.get('confirmation') if request.is_json else request.form.get('confirmation')
        
        if confirmation != 'RESET_ALL_DATA':
            return jsonify({"error": "Invalid confirmation. Send 'RESET_ALL_DATA' to confirm."}), 400
        
        # Create final backup before reset
        import shutil
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        reset_backup = {}
        if os.path.exists(SUBSCRIPTIONS_FILE):
            backup_name = f"FINAL_BACKUP_subscriptions_{timestamp}.json"
            shutil.copy2(SUBSCRIPTIONS_FILE, backup_name)
            reset_backup['subscriptions'] = backup_name
        
        # Reset files
        files_reset = []
        for filename in [SUBSCRIPTIONS_FILE, EMAIL_LOG_FILE, STATS_FILE]:
            if os.path.exists(filename):
                os.remove(filename)
                files_reset.append(filename)
        
        # Initialize fresh stats
        update_stats('app_reset', datetime.now().isoformat())
        
        return jsonify({
            "success": True,
            "message": "All data has been reset",
            "files_reset": files_reset,
            "final_backup": reset_backup,
            "timestamp": timestamp
        })
        
    except Exception as e:
        return jsonify({"error": f"Reset failed: {str(e)}"}), 500

@app.route('/update-threshold', methods=['POST'])
def update_threshold():
    """Update alert threshold for an existing subscription"""
    try:
        email = request.form.get('email', '').strip()
        new_threshold = int(request.form.get('alert_threshold', 15))
        
        if not email:
            flash('Please provide email address', 'error')
            return redirect(url_for('index'))
        
        # Load subscriptions
        subscriptions = load_subscriptions()
        
        # Find and update the subscription
        updated = False
        for subscription in subscriptions:
            if subscription['email'] == email:
                old_threshold = subscription.get('alert_threshold', 15)
                subscription['alert_threshold'] = new_threshold
                subscription['updated_at'] = datetime.now().isoformat()
                updated = True
                print(f"📝 Updated threshold for {email}: {old_threshold} → {new_threshold} minutes")
                break
        
        if updated:
            save_subscriptions(subscriptions)
            flash(f'Alert threshold updated to {new_threshold} minutes for {email}!', 'success')
            update_stats('subscriptions_updated')
        else:
            flash(f'No subscription found for {email}', 'error')
        
    except Exception as e:
        flash(f'Error updating threshold: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/my-subscription/<email>')
def my_subscription(email):
    """View subscription details for a specific email"""
    try:
        subscriptions = load_subscriptions()
        
        # Find user subscription
        user_subscription = None
        for sub in subscriptions:
            if sub['email'] == email:
                user_subscription = sub
                break
        
        if not user_subscription:
            return jsonify({"error": f"No subscription found for {email}"}), 404
        
        # Get email history
        email_log = load_email_log()
        user_emails = [log for log in email_log if log.get('email') == email]
        
        return jsonify({
            "subscription": user_subscription,
            "email_history": {
                "total_emails": len(user_emails),
                "successful_emails": sum(1 for log in user_emails if log.get('success')),
                "failed_emails": sum(1 for log in user_emails if not log.get('success')),
                "recent_emails": user_emails[-5:] if user_emails else []
            },
            "threshold_options": {
                "current": user_subscription.get('alert_threshold', 15),
                "options": [1, 5, 10, 15, 30, 60, 120, 180, 300, 600, 1440]
            }
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed to get subscription: {str(e)}"}), 500

if __name__ == '__main__':
    print("🚀 Starting Visa Tracker Web Application")
    print("=" * 50)
    
    # Initialize statistics on startup
    update_stats('last_startup', datetime.now().isoformat())
    stats = load_stats()
    subscriptions = load_subscriptions()
    
    print(f"📊 Application Statistics:")
    print(f"   👥 Active subscriptions: {len(subscriptions)}")
    print(f"   📧 Total emails sent: {stats.get('emails_sent', 0)}")
    print(f"   ❌ Email failures: {stats.get('emails_failed', 0)}")
    print(f"   🔍 Checks performed: {stats.get('checks_performed', 0)}")
    print(f"   📂 Data files:")
    for filename in [SUBSCRIPTIONS_FILE, SUBSCRIPTIONS_BACKUP, EMAIL_LOG_FILE, STATS_FILE]:
        exists = "✅" if os.path.exists(filename) else "❌"
        print(f"      {exists} {filename}")
    
    # Start background thread for automated checking
    checker_thread = threading.Thread(target=automated_checker, daemon=True)
    checker_thread.start()
    print("🤖 Starting automated visa checker (every 10 minutes)")
    
    print("🌐 Web interface starting on http://localhost:7070")
    print("🤖 Automated checks running every 10 minutes")
    print("📧 Email alerts for updates within user-defined thresholds")
    print()
    print("💡 Admin Panel: http://localhost:7070/admin/subscriptions")
    print("🔧 Email Config: http://localhost:7070/email-config")
    print()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=7070, debug=False)
