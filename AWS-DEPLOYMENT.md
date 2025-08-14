# AWS Production Deployment Guide

Complete guide to deploy your US Visa Tracker to AWS with multiple options.

## 🚀 Deployment Options

### Option 1: AWS EC2 (Recommended for Full Control)
### Option 2: AWS Elastic Beanstalk (Easiest)
### Option 3: AWS ECS Fargate (Serverless Containers)

---

## 📋 Prerequisites

1. **AWS Account** with proper permissions
2. **AWS CLI** installed and configured
3. **Docker** installed locally (for testing)
4. **Gmail App Password** for email notifications

---

## 🔧 Option 1: AWS EC2 Deployment

### Step 1: Launch EC2 Instance

```bash
# 1. Create EC2 instance via AWS Console
# - AMI: Amazon Linux 2
# - Instance Type: t3.micro (free tier) or t3.small
# - Security Group: Allow ports 22, 80, 5000
# - Key Pair: Create or use existing

# 2. Connect to your instance
ssh -i your-key.pem ec2-user@your-instance-ip
```

### Step 2: Run Automated Setup

```bash
# Copy our deployment script to the instance
scp -i your-key.pem deploy-ec2.sh ec2-user@your-instance-ip:~/
ssh -i your-key.pem ec2-user@your-instance-ip

# Run the deployment script
chmod +x deploy-ec2.sh
./deploy-ec2.sh
```

### Step 3: Configure Environment

```bash
# Edit the environment file with your credentials
cd visa-tracker
nano .env

# Add your email configuration:
VISA_TRACKER_EMAIL=your-email@gmail.com
VISA_TRACKER_PASSWORD=your-gmail-app-password
FLASK_ENV=production
```

### Step 4: Start Application

```bash
# Start with Docker Compose
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f
```

---

## 🌐 Option 2: AWS Elastic Beanstalk

### Step 1: Prepare Application

```bash
# Create application.py (EB entry point)
cat > application.py << 'EOF'
#!/usr/bin/env python3
from web_app import app as application

if __name__ == "__main__":
    application.run()
EOF

# Create .ebextensions directory
mkdir .ebextensions

# Create environment configuration
cat > .ebextensions/01_environment.config << 'EOF'
option_settings:
  aws:elasticbeanstalk:application:environment:
    VISA_TRACKER_EMAIL: your-email@gmail.com
    VISA_TRACKER_PASSWORD: your-gmail-app-password
    FLASK_ENV: production
    PYTHONPATH: /var/app/current
EOF
```

### Step 2: Deploy to Elastic Beanstalk

```bash
# Install EB CLI
pip install awsebcli

# Initialize EB application
eb init visa-tracker --region us-east-1 --platform python-3.11

# Create environment and deploy
eb create visa-tracker-prod --instance-type t3.micro
eb deploy

# Get application URL
eb status
```

---

## 🐳 Option 3: AWS ECS Fargate

### Step 1: Build and Push Docker Image

```bash
# Create ECR repository
aws ecr create-repository --repository-name visa-tracker --region us-east-1

# Get login token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Build and tag image
docker build -t visa-tracker .
docker tag visa-tracker:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/visa-tracker:latest

# Push image
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/visa-tracker:latest
```

### Step 2: Create ECS Service

```bash
# Create task definition
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json

# Create ECS cluster
aws ecs create-cluster --cluster-name visa-tracker-cluster

# Create service
aws ecs create-service \
  --cluster visa-tracker-cluster \
  --service-name visa-tracker-service \
  --task-definition visa-tracker:1 \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345],securityGroups=[sg-12345],assignPublicIp=ENABLED}"
```

---

## 🔒 Security Configuration

### Environment Variables

```bash
# Never commit these to git!
export VISA_TRACKER_EMAIL="your-email@gmail.com"
export VISA_TRACKER_PASSWORD="your-gmail-app-password"
export FLASK_SECRET_KEY="your-super-secret-key"
```

### AWS Secrets Manager (Recommended)

```bash
# Store secrets in AWS Secrets Manager
aws secretsmanager create-secret \
  --name "visa-tracker/email-config" \
  --description "Email configuration for Visa Tracker" \
  --secret-string '{"email":"your-email@gmail.com","password":"your-app-password"}'
```

---

## 📊 Monitoring & Maintenance

### CloudWatch Monitoring

```bash
# View application logs
aws logs describe-log-groups --log-group-name-prefix="/aws/elasticbeanstalk/visa-tracker"

# Set up CloudWatch alarms
aws cloudwatch put-metric-alarm \
  --alarm-name "visa-tracker-high-cpu" \
  --alarm-description "High CPU usage" \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average \
  --period 300 \
  --threshold 80.0 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2
```

### Health Checks

```bash
# Test application health
curl http://your-app-url/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2025-08-14T15:30:45",
  "files": {
    "subscriptions": true,
    "stats": true,
    "email_log": true
  },
  "subscriptions_count": 5,
  "version": "1.0.0"
}
```

---

## 🔄 Auto-Scaling Configuration

### EC2 Auto Scaling

```bash
# Create launch template
aws ec2 create-launch-template \
  --launch-template-name visa-tracker-template \
  --launch-template-data file://launch-template.json

# Create auto scaling group
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name visa-tracker-asg \
  --launch-template LaunchTemplateName=visa-tracker-template,Version=1 \
  --min-size 1 \
  --max-size 3 \
  --desired-capacity 1 \
  --target-group-arns arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/visa-tracker/1234567890123456
```

---

## 💰 Cost Optimization

### Free Tier Resources
- **EC2**: t3.micro (750 hours/month)
- **EBS**: 30GB storage
- **Data Transfer**: 15GB out/month
- **CloudWatch**: 10 custom metrics

### Monthly Cost Estimates
- **EC2 t3.micro**: $0 (free tier) - $8.50/month
- **Application Load Balancer**: $16.20/month
- **EBS Storage**: $3/month for 30GB
- **Data Transfer**: $0.09/GB after free tier

---

## 🚨 Troubleshooting

### Common Issues

1. **Application won't start**
   ```bash
   # Check logs
   docker-compose logs visa-tracker
   
   # Check environment variables
   docker-compose exec visa-tracker env | grep VISA_TRACKER
   ```

2. **Email notifications not working**
   ```bash
   # Test email configuration
   curl -X POST http://your-app/test-email
   
   # Check Gmail App Password
   # - Enable 2FA on Gmail
   # - Generate App Password
   # - Use App Password, not regular password
   ```

3. **High memory usage**
   ```bash
   # Monitor resource usage
   docker stats
   
   # Reduce scraping frequency
   # Edit web_app.py: time.sleep(600) -> time.sleep(1800)
   ```

---

## 🔗 Useful Commands

```bash
# Application Management
docker-compose up -d              # Start in background
docker-compose down               # Stop and remove
docker-compose restart            # Restart services
docker-compose logs -f            # Follow logs

# AWS Management
aws ec2 describe-instances        # List EC2 instances
aws elbv2 describe-load-balancers # List load balancers
aws logs tail /aws/elasticbeanstalk/visa-tracker/var/log/eb-docker/containers/eb-current-app/stdouterr.log --follow

# Health Monitoring
curl http://your-app/health       # Health check
curl http://your-app/admin/stats  # Application stats
```

---

## 📞 Support

- **AWS Support**: Use AWS Support Center
- **Application Issues**: Check GitHub repository
- **Email Issues**: Verify Gmail App Password setup

Remember to:
- ✅ Backup your data regularly
- ✅ Monitor costs with AWS Billing alerts
- ✅ Keep dependencies updated
- ✅ Use HTTPS in production (add SSL certificate)
