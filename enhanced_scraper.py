#!/usr/bin/env python3
"""
Enhanced Live Scraper with Selenium Support
Gets fresh data by executing JavaScript on the actual website
"""

import urllib.request
import json
import re
import time
from datetime import datetime

def fetch_with_selenium():
    """Fetch data using Selenium to execute JavaScript"""
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.service import Service
        
        print("🤖 Using Selenium to get live data...")
        
        # Setup Chrome options
        options = Options()
        options.add_argument('--headless')  # Run in background
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        
        # Initialize driver with auto-managed ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        try:
            # Load the page
            url = "https://checkvisaslots.com/latest-us-visa-availability.html"
            print(f"🌐 Loading: {url}")
            driver.get(url)
            
            # Wait for the table to load
            print("⏳ Waiting for data to load...")
            wait = WebDriverWait(driver, 30)
            
            # Wait for the table to have content
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
            
            # Give extra time for all data to load
            time.sleep(5)
            
            # Try to extract data from the populated table
            rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
            
            if not rows:
                print("❌ No table rows found")
                return None
                
            print(f"✅ Found {len(rows)} data rows")
            
            # Extract data from table
            visa_data = {"result": {}}
            
            for row in rows:
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 6:
                        location = cells[0].text.strip()
                        visa_type = cells[1].text.strip()
                        earliest_date = cells[2].text.strip()
                        appointments = cells[3].text.strip()
                        updated_time = cells[4].text.strip()
                        relative_time = cells[5].text.strip()
                        
                        # Parse the updated time to our format
                        try:
                            # Try to parse the time format from the website
                            if "Aug 14, 2025" in updated_time:
                                # Extract just the time part
                                time_part = updated_time.split(",")[-1].strip()
                                if "AM" in time_part or "PM" in time_part:
                                    # Convert to 24-hour format
                                    parsed_time = datetime.strptime(f"2025-08-14 {time_part}", "%Y-%m-%d %I:%M %p")
                                    createdon = parsed_time.strftime("%Y-%m-%d %H:%M:%S")
                                else:
                                    createdon = "2025-08-14 00:00:00"
                            else:
                                createdon = "2025-08-14 00:00:00"
                        except:
                            createdon = "2025-08-14 00:00:00"
                        
                        # Parse appointments count
                        try:
                            appt_count = int(re.findall(r'\d+', appointments)[0]) if appointments else 0
                        except:
                            appt_count = 0
                        
                        record = {
                            "visa_location": location,
                            "visa_type": visa_type,
                            "createdon": createdon,
                            "no_of_dates": 1,
                            "no_of_apnts": appt_count,
                            "earliest_date": earliest_date
                        }
                        
                        # Group by visa type
                        if visa_type not in visa_data["result"]:
                            visa_data["result"][visa_type] = []
                        
                        visa_data["result"][visa_type].append(record)
                        
                except Exception as e:
                    print(f"⚠️ Error parsing row: {e}")
                    continue
            
            print(f"✅ Extracted data for {len(visa_data['result'])} visa types")
            return visa_data
            
        finally:
            driver.quit()
            
    except ImportError:
        print("❌ Selenium not installed. Install with: pip install selenium")
        return None
    except Exception as e:
        print(f"❌ Selenium error: {e}")
        return None

def fetch_fresh_data():
    """Try multiple methods to get the freshest data"""
    
    # Method 1: Try Selenium first (most reliable for fresh data)
    print("🔄 Method 1: Trying Selenium...")
    selenium_data = fetch_with_selenium()
    if selenium_data:
        print("✅ Got fresh data via Selenium!")
        return selenium_data
    
    # Method 2: Fall back to S3 bucket
    print("🔄 Method 2: Falling back to S3 bucket...")
    try:
        url = "https://cvs-data-public.s3.us-east-1.amazonaws.com/last-availability.json"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
            print("✅ Got data from S3 bucket (may be slightly delayed)")
            return data
            
    except Exception as e:
        print(f"❌ S3 bucket failed: {e}")
    
    print("❌ All methods failed")
    return None

if __name__ == "__main__":
    print("🚀 Enhanced Live Data Fetcher")
    print("=" * 40)
    
    data = fetch_fresh_data()
    if data:
        # Save the data
        with open('live_visa_data.json', 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"💾 Data saved to: live_visa_data.json")
        
        # Show some stats
        if 'result' in data:
            total_types = len(data['result'])
            total_records = sum(len(records) for records in data['result'].values())
            print(f"📊 {total_types} visa types, {total_records} total records")
            
            # Show B2 Dropbox data if available
            if 'B2 (Dropbox)' in data['result']:
                b2_records = data['result']['B2 (Dropbox)']
                for record in b2_records:
                    if 'NEW DELHI VAC' in record.get('visa_location', ''):
                        print(f"🎯 B2 (Dropbox) NEW DELHI VAC: {record.get('createdon')} - {record.get('no_of_apnts')} appointments")
    else:
        print("❌ Could not fetch any data")
