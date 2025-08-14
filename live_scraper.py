#!/usr/bin/env python3
"""
Live Visa Data Scraper
Attempts to extract actual visa data from checkvisaslots.com
Enhanced with multiple data sources and cache-busting
"""

import urllib.request
import urllib.parse
import json
import re
import time
import random
from datetime import datetime
from html.parser import HTMLParser

def fetch_webpage_data():
    """Fetch the webpage and return raw HTML content"""
    url = "https://checkvisaslots.com/latest-us-visa-availability.html"
    
    try:
        print(f"🌐 Fetching live data from: {url}")
        
        # Create request with headers to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=30) as response:
            content = response.read()
            
            # Handle gzip encoding
            if response.info().get('Content-Encoding') == 'gzip':
                import gzip
                content = gzip.decompress(content)
            
            html_content = content.decode('utf-8')
            
        print(f"✅ Successfully fetched {len(html_content):,} characters")
        return html_content
        
    except Exception as e:
        print(f"❌ Error fetching webpage: {str(e)}")
        return None

def extract_data_source_url(html_content):
    """Extract the JSON data source URL from the JavaScript"""
    try:
        # Look for the S3 URL in the JavaScript
        s3_pattern = r'https://[^"]*\.s3[^"]*\.amazonaws\.com/[^"]*\.json'
        matches = re.findall(s3_pattern, html_content)
        
        if matches:
            return matches[0]
        
        # Alternative patterns
        json_patterns = [
            r'url:\s*["\']([^"\']*\.json)["\']',
            r'fetch\(["\']([^"\']*\.json)["\']',
            r'ajax.*url.*["\']([^"\']*\.json)["\']'
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            if matches:
                return matches[0]
        
        return None
        
    except Exception as e:
        print(f"⚠️  Error extracting data source: {str(e)}")
        return None

def try_alternative_endpoints():
    """Try alternative endpoints that might have the data"""
    endpoints = [
        "https://checkvisaslots.com/api/slots",
        "https://checkvisaslots.com/data/slots.json",
        "https://checkvisaslots.com/latest-data.json",
        "https://api.checkvisaslots.com/slots",
    ]
    
    for endpoint in endpoints:
        try:
            print(f"🔄 Trying endpoint: {endpoint}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Referer': 'https://checkvisaslots.com/latest-us-visa-availability.html'
            }
            
            req = urllib.request.Request(endpoint, headers=headers)
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = response.read().decode('utf-8')
                if data.strip().startswith('{') or data.strip().startswith('['):
                    print(f"✅ Found JSON data at: {endpoint}")
                    return json.loads(data)
                    
        except Exception as e:
            print(f"   ❌ Failed: {str(e)}")
            continue
    
    return None

def extract_embedded_data(html_content):
    """Look for embedded JSON data in the HTML"""
    try:
        # Look for JavaScript variables with JSON data
        patterns = [
            r'var\s+slotsData\s*=\s*({.*?});',
            r'let\s+data\s*=\s*({.*?});',
            r'const\s+visaData\s*=\s*({.*?});',
            r'window\.visaSlots\s*=\s*({.*?});'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_content, re.DOTALL)
            if matches:
                try:
                    data = json.loads(matches[0])
                    print(f"✅ Found embedded JSON data")
                    return data
                except json.JSONDecodeError:
                    continue
        
        # Look for any JSON-like structures
        json_pattern = r'\{[^{}]*"[^"]*":\s*[\[{"][^}]*\}'
        matches = re.findall(json_pattern, html_content)
        
        for match in matches:
            try:
                if any(keyword in match.lower() for keyword in ['visa', 'location', 'date', 'slot']):
                    data = json.loads(match)
                    print(f"✅ Found potential visa data in HTML")
                    return data
            except json.JSONDecodeError:
                continue
        
        return None
        
    except Exception as e:
        print(f"⚠️  Error extracting embedded data: {str(e)}")
        return None

def analyze_html_structure(html_content):
    """Analyze the HTML structure to understand how data is loaded"""
    print("\n📊 WEBPAGE ANALYSIS:")
    print("=" * 50)
    
    # Check for dynamic loading indicators
    if 'jquery' in html_content.lower():
        print("✅ jQuery detected - likely uses AJAX")
    
    if 'ajax' in html_content.lower():
        print("✅ AJAX calls detected")
    
    if 'bootstrap-table' in html_content.lower():
        print("✅ Bootstrap Table detected - data loaded dynamically")
    
    if 'getSlotsInfo' in html_content:
        print("✅ getSlotsInfo function found - this loads the data")
    
    # Extract JavaScript functions
    js_functions = re.findall(r'function\s+(\w+)\s*\(', html_content)
    if js_functions:
        print(f"📝 JavaScript functions: {', '.join(js_functions[:10])}")
    
    # Look for API endpoints
    urls = re.findall(r'https://[^\s"\'<>]+', html_content)
    api_urls = [url for url in urls if any(ext in url for ext in ['.json', '/api/', '/data/'])]
    if api_urls:
        print(f"🔗 Potential API endpoints found:")
        for url in api_urls[:5]:
            print(f"   • {url}")
    
    # Check for data attributes
    data_attrs = re.findall(r'data-[a-zA-Z-]+=["\'][^"\']*["\']', html_content)
    if data_attrs:
        print(f"📋 Data attributes: {len(data_attrs)} found")
    
    return api_urls

def fetch_with_cache_busting():
    """Fetch data with cache-busting techniques"""
    base_url = "https://cvs-data-public.s3.us-east-1.amazonaws.com/last-availability.json"
    
    # Try multiple cache-busting strategies
    strategies = [
        f"{base_url}?t={int(time.time())}",  # Timestamp
        f"{base_url}?v={random.randint(1000, 9999)}",  # Random version
        f"{base_url}?refresh={int(time.time())}&r={random.randint(100, 999)}",  # Double bust
    ]
    
    for i, url in enumerate(strategies):
        try:
            print(f"🔄 Cache-busting attempt {i+1}: {url[-50:]}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0',
                'Referer': 'https://checkvisaslots.com/latest-us-visa-availability.html',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
            }
            
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=15) as response:
                content = response.read()
                
                # Handle gzip encoding
                if response.info().get('Content-Encoding') == 'gzip':
                    import gzip
                    content = gzip.decompress(content)
                
                data = json.loads(content.decode('utf-8'))
                
                # Check if this is fresh data by looking at timestamps
                if 'result' in data:
                    sample_records = []
                    for visa_type, records in data['result'].items():
                        if records:
                            sample_records.extend(records[:2])  # Sample first 2 records
                    
                    if sample_records:
                        latest_time = max(record.get('createdon', '2025-01-01 00:00:00') 
                                        for record in sample_records)
                        print(f"✅ Data fetched! Latest timestamp: {latest_time}")
                        return data
                
                print(f"⚠️ Got data but checking timestamps...")
                return data
                
        except Exception as e:
            print(f"❌ Attempt {i+1} failed: {e}")
            if i < len(strategies) - 1:
                time.sleep(2)  # Wait before next attempt
            continue
    
    return None

def main():
    """Main function with enhanced data fetching"""
    print("🔍 LIVE VISA DATA SCRAPER")
    print("=" * 40)
    
    # Step 1: Try cache-busting first
    print(f"\n🚀 TRYING CACHE-BUSTING TECHNIQUES:")
    print("-" * 35)
    
    fresh_data = fetch_with_cache_busting()
    if fresh_data:
        print(f"✅ SUCCESS! Got potentially fresher data")
        with open('live_visa_data.json', 'w') as f:
            json.dump(fresh_data, f, indent=2)
        print(f"💾 Data saved to: live_visa_data.json")
        
        # Show sample data quality
        if 'result' in fresh_data and 'B2 (Dropbox)' in fresh_data['result']:
            b2_records = fresh_data['result']['B2 (Dropbox)']
            for record in b2_records:
                if 'NEW DELHI VAC' in record.get('visa_location', ''):
                    print(f"🎯 B2 (Dropbox) NEW DELHI VAC: {record.get('createdon')} - {record.get('no_of_apnts')} appointments")
        
        return fresh_data
    
    # Step 2: Fall back to original method
    print(f"\n🔄 FALLING BACK TO ORIGINAL METHOD:")
    print("-" * 35)
    
    # Step 2a: Fetch the webpage
    html_content = fetch_webpage_data()
    if not html_content:
        print("❌ Could not fetch webpage content")
        return
    
    # Step 2b: Analyze the structure
    api_urls = analyze_html_structure(html_content)
    
    # Step 2c: Try to extract data source URL
    print(f"\n🔎 LOOKING FOR DATA SOURCE:")
    print("-" * 30)
    
    data_source_url = extract_data_source_url(html_content)
    if data_source_url:
        print(f"📍 Found data source URL: {data_source_url}")
        
        # Try to fetch from the data source
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Referer': 'https://checkvisaslots.com/latest-us-visa-availability.html'
            }
            req = urllib.request.Request(data_source_url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=15) as response:
                json_data = response.read().decode('utf-8')
                data = json.loads(json_data)
                print(f"✅ SUCCESS! Fetched live data with {len(str(data))} characters")
                
                # Save and display the data
                with open('live_visa_data.json', 'w') as f:
                    json.dump(data, f, indent=2)
                
                print(f"💾 Data saved to: live_visa_data.json")
                print(f"\n📊 LIVE DATA PREVIEW:")
                print(json.dumps(data, indent=2)[:1000] + "...")
                return data
                
        except Exception as e:
            print(f"❌ Could not fetch from data source: {str(e)}")
    
    # Continue with existing fallback methods...
    print(f"\n� RECOMMENDATIONS:")
    print("-" * 25)
    print(f"• The S3 data source may have a delay")
    print(f"• Website shows fresher data via JavaScript")
    print(f"• Consider using Selenium for real-time data")
    print(f"• Current data is still functional but may be ~5-6 hours delayed")
    
    return None

if __name__ == "__main__":
    main()
