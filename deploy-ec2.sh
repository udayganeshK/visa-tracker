#!/bin/bash

# AWS EC2 Deployment Script
# Run this on your EC2 instance to deploy the visa tracker

set -e

echo "🚀 Starting AWS EC2 deployment..."

# Update system
sudo yum update -y

# Install Docker
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone the repository
cd /home/ec2-user
git clone https://github.com/udayganeshK/visa-tracker.git
cd visa-tracker

# Copy environment variables
cp .env.example .env
echo "📝 Please edit .env file with your email credentials:"
echo "nano .env"
read -p "Press Enter after editing .env file..."

# Create data directory with proper permissions
mkdir -p data
chmod 755 data

# Build and start the application
docker-compose up -d

# Set up nginx (optional, for production domain)
read -p "Do you want to set up nginx reverse proxy? (y/n): " setup_nginx
if [ "$setup_nginx" = "y" ]; then
    sudo yum install -y nginx
    
    # Create nginx config
    sudo tee /etc/nginx/conf.d/visa-tracker.conf > /dev/null <<EOF
server {
    listen 80;
    server_name your-domain.com;  # Change this to your domain

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

    sudo systemctl start nginx
    sudo systemctl enable nginx
    
    echo "🌐 Nginx configured! Edit /etc/nginx/conf.d/visa-tracker.conf with your domain"
fi

echo "✅ Deployment complete!"
echo "🔗 Application running at: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):5000"
echo "📊 Check status: docker-compose ps"
echo "📋 View logs: docker-compose logs -f"
