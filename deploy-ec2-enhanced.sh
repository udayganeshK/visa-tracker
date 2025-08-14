#!/bin/bash

# Enhanced EC2 Deployment Script for Visa Tracker
# Run this script on your EC2 instance

set -e

echo "🚀 Starting EC2 deployment for Visa Tracker..."
echo "=============================================="

# Update system packages
echo "📦 Updating system packages..."
sudo yum update -y

# Install Git
echo "📥 Installing Git..."
sudo yum install -y git

# Install Docker
echo "🐳 Installing Docker..."
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user

# Install Docker Compose
echo "🔧 Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Re-login to apply docker group (for current session)
echo "🔄 Applying docker permissions..."
newgrp docker << EONG

# Clone the repository
echo "📂 Cloning visa tracker repository..."
cd /home/ec2-user
if [ -d "visa-tracker" ]; then
    echo "Repository already exists, pulling latest changes..."
    cd visa-tracker
    git pull origin main
else
    git clone https://github.com/udayganeshK/visa-tracker.git
    cd visa-tracker
fi

# Create environment file
echo "📝 Setting up environment variables..."
cat > .env << EOF
# Email Configuration for Notifications
VISA_TRACKER_EMAIL=uday.gnsh@gmail.com
VISA_TRACKER_PASSWORD=zsaeintazwxjvskf

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=false

# Application Port
PORT=5000
EOF

echo "✅ Environment file created with email configuration"

# Create data directory
echo "📁 Creating data directory..."
mkdir -p data
chmod 755 data

# Build and start the application
echo "🏗️ Building and starting the application..."
docker-compose down || true
docker-compose build
docker-compose up -d

# Wait for application to start
echo "⏳ Waiting for application to start..."
sleep 30

# Check if application is running
echo "🔍 Checking application status..."
if docker-compose ps | grep -q "Up"; then
    echo "✅ Application is running successfully!"
    
    # Get public IP
    PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
    echo "🌐 Application URL: http://$PUBLIC_IP:5000"
    
    # Test application
    echo "🧪 Testing application endpoint..."
    if curl -f http://localhost:5000 > /dev/null 2>&1; then
        echo "✅ Application is responding correctly!"
    else
        echo "⚠️ Application may still be starting up. Check logs with: docker-compose logs -f"
    fi
else
    echo "❌ Application failed to start. Check logs with: docker-compose logs"
    exit 1
fi

EONG

echo ""
echo "🎉 Deployment Complete!"
echo "======================="
echo "📊 Application Dashboard: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):5000"
echo "📋 Check status: cd visa-tracker && docker-compose ps"
echo "📝 View logs: cd visa-tracker && docker-compose logs -f"
echo "🔄 Restart app: cd visa-tracker && docker-compose restart"
echo "🛑 Stop app: cd visa-tracker && docker-compose down"
echo ""
echo "🔧 Management Commands:"
echo "  - ssh -i your-key.pem ec2-user@your-instance-ip"
echo "  - cd visa-tracker"
echo "  - docker-compose logs -f visa-tracker"
echo ""
echo "📧 Email notifications are configured and ready!"
echo "🎯 Users can now subscribe for visa alerts at your EC2 URL"
