# US Visa Slot Tracker

A comprehensive application to track US visa appointment availability across Indian consulates by scraping and categorizing data from https://checkvisaslots.com/latest-us-visa-availability.html.

## Features

### 🔍 Data Scraping
- **Automated scraping** of visa slot availability data
- **Real-time monitoring** of multiple consulate locations
- **Categorization** by visa types (B1/B2, F1, H1B, L1, O1, J1)
- **Historical tracking** with timestamps

### 📊 Data Organization
- **Visa Categories**: Business/Tourism, Student, Skilled Worker, etc.
- **Location-based grouping**: Chennai, Hyderabad, Kolkata, Mumbai, New Delhi
- **Availability status**: Available, Limited, Unavailable
- **Time-based sorting**: Earliest available dates first

### 🌐 Multiple Interfaces
- **Web Dashboard**: Beautiful, responsive interface with real-time updates
- **Command Line**: Simple Python scripts for automation
- **JSON/CSV Export**: Data export in multiple formats

## Quick Start

### Option 1: Automated Setup (Recommended)
```bash
# Clone the repository
cd visa-tracker

# Run automated setup
./setup.sh

# Activate virtual environment
source venv/bin/activate

# Run simple scraper (no dependencies required)
python simple_scraper.py
```

### Option 2: Manual Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run full scraper
python visa_scraper.py
```

### Option 3: Web Interface
```bash
# Install web dependencies
pip install -r requirements-web.txt

# Start web server
python app.py

# Open browser to http://localhost:5000
```

## Usage Examples

### 1. Simple Command Line Scraping
```bash
python simple_scraper.py
```
Output:
```
🛂 US VISA AVAILABILITY SUMMARY
====================================
📊 Total Records: 6
🕐 Last Updated: 2025-08-14 15:30:45

📋 BY VISA CATEGORY:
   Business/Tourism: 6 locations, 37 total slots

🏢 BY CONSULATE LOCATION:
   KOLKATA VAC: 1 visa types, 25 slots
   HYDERABAD VAC: 1 visa types, 5 slots
   CHENNAI VAC: 1 visa types, 4 slots
```

### 2. Advanced Scraping with Browser Automation
```bash
python visa_scraper.py
```

### 3. Web Dashboard
```bash
python app.py
```
Then open http://localhost:5000 for:
- 📊 Interactive dashboard
- 📈 Real-time charts and statistics  
- 🔄 Auto-refresh every 5 minutes
- 📱 Mobile-responsive design

## Data Structure

Each visa record contains:
```json
{
  "visa_location": "CHENNAI VAC",
  "visa_type": "B1 (Regular)",
  "visa_category": "Business/Tourism",
  "earliest_date": "2025-09-25",
  "total_dates_available": 4,
  "last_seen_at": "2025-08-14T11:01:00",
  "relative_time": "12 minutes ago",
  "scraped_at": "2025-08-14T15:30:45.123456"
}
```

## Visa Categories

| Category | Visa Types | Description |
|----------|------------|-------------|
| Business/Tourism | B1, B2, B1/B2 | Business visitors and tourists |
| Student | F1 | Student visas |
| Skilled Worker | H1B | Specialty occupation workers |
| Intracompany Transfer | L1 | Intracompany transferees |
| Extraordinary Ability | O1 | Individuals with extraordinary ability |
| Exchange Visitor | J1 | Exchange visitors |

## API Endpoints

When running the web application:

- `GET /api/visa-data` - Get all visa data
- `GET /api/refresh` - Force refresh data  
- `GET /api/categories` - Get data grouped by categories
- `GET /api/locations` - Get data grouped by locations
- `GET /api/earliest` - Get earliest available slots

## File Structure

```
visa-tracker/
├── simple_scraper.py      # Lightweight scraper (no dependencies)
├── visa_scraper.py        # Full-featured scraper with Selenium
├── app.py                 # Flask web application
├── templates/
│   └── index.html         # Web dashboard
├── requirements.txt       # Core Python packages
├── requirements-web.txt   # Web application packages
├── setup.sh              # Automated setup script
└── README.md             # This file
```

## Dependencies

### Core (simple_scraper.py)
- Python 3.7+ standard library only
- No external dependencies required

### Full Scraper (visa_scraper.py)
- requests
- beautifulsoup4
- pandas
- selenium
- webdriver-manager

### Web Interface (app.py)
- flask
- All core scraper dependencies

## Scheduling Automated Runs

### Using cron (Linux/macOS)
```bash
# Edit crontab
crontab -e

# Add line to run every 30 minutes
*/30 * * * * cd /path/to/visa-tracker && source venv/bin/activate && python simple_scraper.py
```

### Using Python schedule
```python
import schedule
import time

def run_scraper():
    # Your scraper code here
    pass

schedule.every(30).minutes.do(run_scraper)

while True:
    schedule.run_pending()
    time.sleep(1)
```

## Troubleshooting

### Common Issues

1. **Import errors**: Make sure virtual environment is activated
   ```bash
   source venv/bin/activate
   ```

2. **Website access blocked**: Try the simple scraper which uses basic HTTP requests
   ```bash
   python simple_scraper.py
   ```

3. **Chrome driver issues**: Update Chrome and webdriver-manager
   ```bash
   pip install --upgrade webdriver-manager
   ```

4. **No data scraped**: Website structure might have changed
   - Check if the website is accessible
   - Inspect the HTML structure for changes

### Error Messages

- `Import "selenium" could not be resolved` → Install dependencies: `pip install -r requirements.txt`
- `ChromeDriver not found` → Run: `pip install webdriver-manager`
- `Connection timeout` → Check internet connection and try again

## Legal Notice

This tool is for educational and personal use only. Please:
- ✅ Respect the website's robots.txt and terms of service
- ✅ Use reasonable request intervals to avoid overwhelming servers
- ✅ Consider the website's server load
- ❌ Do not use for commercial purposes without permission

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Disclaimer

This application is not affiliated with the US Government, US Embassy, or CheckVisaSlots.com. The data provided is for informational purposes only and may not reflect real-time availability. Always verify information through official channels before making travel plans.
