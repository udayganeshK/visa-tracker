# EC2 Deployment Guide for Visa Tracker

## 🚀 Quick EC2 Deployment Steps

### Step 1: Launch EC2 Instance

1. **Go to AWS Console** → EC2 → Launch Instance
2. **Choose AMI**: Amazon Linux 2023 (free tier eligible)
3. **Instance Type**: t3.micro (free tier) or t3.small (recommended)
4. **Key Pair**: Create new or use existing
5. **Security Group**: Create with these rules:
   - SSH (22) - Your IP
   - HTTP (80) - Anywhere (0.0.0.0/0)
   - Custom TCP (5000) - Anywhere (0.0.0.0/0)
6. **Storage**: 8GB gp3 (free tier)
7. **Launch Instance**

### Step 2: Connect to EC2

```bash
# Download your .pem key file and set permissions
chmod 400 your-key.pem

# Connect to EC2 instance
ssh -i your-key.pem ec2-user@YOUR_EC2_PUBLIC_IP
```

### Step 3: Deploy Application

```bash
# Copy deployment script to EC2
scp -i your-key.pem deploy-ec2-enhanced.sh ec2-user@YOUR_EC2_PUBLIC_IP:~/

# SSH into EC2 and run deployment
ssh -i your-key.pem ec2-user@YOUR_EC2_PUBLIC_IP
chmod +x deploy-ec2-enhanced.sh
./deploy-ec2-enhanced.sh
```

### Step 4: Access Your Application

- **Application URL**: `http://YOUR_EC2_PUBLIC_IP:5000`
- **Admin Panel**: `http://YOUR_EC2_PUBLIC_IP:5000/admin/subscriptions`
- **Email Config**: `http://YOUR_EC2_PUBLIC_IP:5000/email-config`

### Step 5: Monitor & Manage

```bash
# Check application status
cd visa-tracker
docker-compose ps

# View application logs
docker-compose logs -f visa-tracker

# Restart application
docker-compose restart

# Stop application
docker-compose down

# Start application
docker-compose up -d
```

## 🔧 Important Notes

### Security Group Configuration
Make sure your EC2 security group allows:
- **Port 22** (SSH) from your IP
- **Port 5000** (App) from anywhere (0.0.0.0/0)
- **Port 80** (HTTP) from anywhere (optional for nginx)

### Environment Variables
The script automatically configures:
- `VISA_TRACKER_EMAIL=uday.gnsh@gmail.com`
- `VISA_TRACKER_PASSWORD=zsaeintazwxjvskf`

### Application Features
✅ Email notifications working  
✅ Automated visa checking every 10 minutes  
✅ Web interface for subscriptions  
✅ Admin panel for management  
✅ Data persistence with Docker volumes  

### Troubleshooting

**Application not accessible?**
```bash
# Check if docker is running
sudo systemctl status docker

# Check if app container is running
docker-compose ps

# Check application logs
docker-compose logs visa-tracker

# Check if port is open
curl http://localhost:5000
```

**Email not working?**
```bash
# Check environment variables
docker-compose exec visa-tracker env | grep VISA_TRACKER

# Test email from admin panel
# Go to: http://YOUR_EC2_IP:5000/email-config
```

## 🌐 Optional: Set Up Domain & SSL

### With Nginx Reverse Proxy
```bash
# Install nginx
sudo yum install -y nginx

# Configure nginx (create /etc/nginx/conf.d/visa-tracker.conf)
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Start nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

### With SSL (Certbot)
```bash
# Install certbot
sudo yum install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

## 💰 Cost Estimation

**t3.micro (free tier eligible)**:
- First 12 months: Free
- After: ~$8.5/month

**t3.small (recommended)**:
- ~$17/month

**Data transfer & storage**: Minimal cost

## 🎯 Next Steps

1. **Test the application** at your EC2 IP
2. **Subscribe with test emails** to verify notifications
3. **Monitor logs** for any issues
4. **Set up domain** (optional)
5. **Configure backups** for data persistence

Your visa tracker is now live and ready for users! 🎉
