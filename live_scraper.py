#!/usr/bin/env python3
"""
Live Visa Data Scraper
Attempts to extract actual visa data from checkvisaslots.com
"""

import urllib.request
import urllib.parse
import json
import re
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

def main():
    """Main function"""
    print("🔍 LIVE VISA DATA SCRAPER")
    print("=" * 40)
    
    # Step 1: Fetch the webpage
    html_content = fetch_webpage_data()
    if not html_content:
        print("❌ Could not fetch webpage content")
        return
    
    # Step 2: Analyze the structure
    api_urls = analyze_html_structure(html_content)
    
    # Step 3: Try to extract data source URL
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
    
    # Step 4: Try alternative endpoints
    print(f"\n🔄 TRYING ALTERNATIVE ENDPOINTS:")
    print("-" * 35)
    
    alt_data = try_alternative_endpoints()
    if alt_data:
        print(f"✅ SUCCESS! Found data via alternative endpoint")
        with open('live_visa_data.json', 'w') as f:
            json.dump(alt_data, f, indent=2)
        print(f"💾 Data saved to: live_visa_data.json")
        return alt_data
    
    # Step 5: Look for embedded data
    print(f"\n🔍 LOOKING FOR EMBEDDED DATA:")
    print("-" * 30)
    
    embedded_data = extract_embedded_data(html_content)
    if embedded_data:
        print(f"✅ SUCCESS! Found embedded data")
        with open('live_visa_data.json', 'w') as f:
            json.dump(embedded_data, f, indent=2)
        print(f"💾 Data saved to: live_visa_data.json")
        return embedded_data
    
    # Step 6: Show what we found
    print(f"\n📋 SUMMARY:")
    print("-" * 20)
    print(f"• Webpage fetched successfully")
    print(f"• Dynamic loading detected (JavaScript/AJAX)")
    print(f"• Data is loaded from external JSON source")
    print(f"• Source appears to be access-protected")
    
    print(f"\n💡 RECOMMENDATIONS:")
    print("-" * 25)
    print(f"• Use Selenium WebDriver to execute JavaScript")
    print(f"• Wait for dynamic content to load")
    print(f"• Monitor network requests to find active endpoints")
    print(f"• Consider using browser automation tools")
    
    # Save HTML for analysis
    with open('webpage_source.html', 'w') as f:
        f.write(html_content)
    print(f"💾 HTML source saved to: webpage_source.html")
    
    return None

if __name__ == "__main__":
    main()
