#!/bin/bash

# Visa Tracker Setup Script
echo "🚀 Setting up US Visa Tracker Application"
echo "=========================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.7+ first."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Function to install packages with error handling
install_packages() {
    local requirements_file=$1
    local description=$2
    
    echo "📥 Installing $description..."
    if pip install -r "$requirements_file"; then
        echo "✅ $description installed successfully"
        return 0
    else
        echo "⚠️  Some packages in $description failed to install"
        return 1
    fi
}

# Try to install full requirements first, then fallback to basic
echo ""
echo "📋 Installing dependencies..."

if [ -f "requirements.txt" ]; then
    if install_packages "requirements.txt" "core packages"; then
        CORE_INSTALLED=true
    else
        CORE_INSTALLED=false
    fi
else
    echo "⚠️  requirements.txt not found, skipping core packages"
    CORE_INSTALLED=false
fi

if [ -f "requirements-web.txt" ]; then
    if install_packages "requirements-web.txt" "web packages"; then
        WEB_INSTALLED=true
    else
        WEB_INSTALLED=false
    fi
else
    echo "⚠️  requirements-web.txt not found, skipping web packages"
    WEB_INSTALLED=false
fi

echo ""
echo "🎯 Setup Summary:"
echo "=================="

if [ "$CORE_INSTALLED" = true ]; then
    echo "✅ Core scraping packages installed"
else
    echo "❌ Core scraping packages failed - you can still use simple_scraper.py"
fi

if [ "$WEB_INSTALLED" = true ]; then
    echo "✅ Web interface packages installed"
else
    echo "❌ Web interface packages failed - you can still use command line tools"
fi

echo ""
echo "🚀 Available Commands:"
echo "======================"
echo ""

# Check what can be run
if [ "$CORE_INSTALLED" = true ]; then
    echo "1. Full scraper with Selenium (recommended):"
    echo "   source venv/bin/activate && python visa_scraper.py"
    echo ""
fi

echo "2. Simple scraper (no external dependencies):"
echo "   source venv/bin/activate && python simple_scraper.py"
echo ""

if [ "$WEB_INSTALLED" = true ]; then
    echo "3. Web dashboard:"
    echo "   source venv/bin/activate && python app.py"
    echo "   Then open: http://localhost:5000"
    echo ""
fi

echo "4. Quick test (run simple scraper now):"
echo "   source venv/bin/activate && python simple_scraper.py"

echo ""
echo "📖 Usage Tips:"
echo "=============="
echo "• Always activate the virtual environment first: source venv/bin/activate"
echo "• The simple scraper works without any external dependencies"
echo "• Data is saved as JSON files with timestamps"
echo "• Run scraper periodically to track changes"

echo ""
echo "🏁 Setup complete! Choose a command above to get started."
