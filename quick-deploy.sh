#!/bin/bash

# Quick AWS Deployment Script for Visa Tracker
# Run this script to deploy to AWS EC2 in under 5 minutes

echo "🚀 Quick AWS EC2 Deployment for Visa Tracker"
echo "=============================================="

# Check if we're on AWS EC2
if curl -s --connect-timeout 2 http://169.254.169.254/latest/meta-data/instance-id > /dev/null 2>&1; then
    echo "✅ Running on AWS EC2"
    INSTANCE_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
    echo "📍 Public IP: $INSTANCE_IP"
else
    echo "⚠️  Not running on AWS EC2. Use this for local testing."
    INSTANCE_IP="localhost"
fi

echo ""
echo "📦 Installing dependencies..."

# Update system and install Docker
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    sudo yum update -y
    sudo yum install -y docker
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -a -G docker $USER
fi

# Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Clone repository if not exists
if [ ! -d "visa-tracker" ]; then
    echo "Cloning repository..."
    git clone https://github.com/udayganeshK/visa-tracker.git
fi

cd visa-tracker

echo ""
echo "⚙️  Configuration Setup"
echo "======================="

# Create environment file
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << EOF
# Email Configuration
VISA_TRACKER_EMAIL=
VISA_TRACKER_PASSWORD=

# Flask Configuration
FLASK_ENV=production
FLASK_SECRET_KEY=$(openssl rand -hex 32)

# Application Settings
PORT=5000
HOST=0.0.0.0
EOF
    
    echo "📝 Please edit .env file with your email credentials:"
    echo "nano .env"
    echo ""
    echo "Required fields:"
    echo "  VISA_TRACKER_EMAIL=your-email@gmail.com"
    echo "  VISA_TRACKER_PASSWORD=your-gmail-app-password"
    echo ""
    read -p "Press Enter after editing .env file..."
fi

# Create data directory
mkdir -p data
chmod 755 data

echo ""
echo "🚀 Starting Application..."
echo "========================="

# Stop any existing containers
docker-compose down 2>/dev/null || true

# Build and start
docker-compose up -d

# Wait for application to start
echo "⏳ Waiting for application to start..."
sleep 10

# Check if application is running
if curl -f http://localhost:5000/health > /dev/null 2>&1; then
    echo "✅ Application started successfully!"
else
    echo "❌ Application failed to start. Checking logs..."
    docker-compose logs
    exit 1
fi

echo ""
echo "🎉 Deployment Complete!"
echo "======================"
echo ""
echo "🌐 Application URLs:"
echo "   Main App: http://$INSTANCE_IP:5000"
echo "   Health Check: http://$INSTANCE_IP:5000/health"
echo "   Admin Panel: http://$INSTANCE_IP:5000/admin/subscriptions"
echo ""
echo "📊 Management Commands:"
echo "   View logs: docker-compose logs -f"
echo "   Check status: docker-compose ps"
echo "   Restart app: docker-compose restart"
echo "   Stop app: docker-compose down"
echo ""
echo "📧 Test email: curl -X POST http://$INSTANCE_IP:5000/test-email"
echo ""

# Set up auto-start on boot
if [ "$INSTANCE_IP" != "localhost" ]; then
    echo "⚙️  Setting up auto-start on boot..."
    echo "cd $(pwd) && docker-compose up -d" | sudo tee -a /etc/rc.local > /dev/null
    sudo chmod +x /etc/rc.local
    echo "✅ Application will auto-start on server reboot"
fi

echo ""
echo "🔒 Security Note: Make sure your AWS Security Group allows:"
echo "   - Port 22 (SSH) from your IP"
echo "   - Port 5000 (App) from 0.0.0.0/0 or your IP range"
echo "   - Port 80/443 (HTTP/HTTPS) if using domain"
