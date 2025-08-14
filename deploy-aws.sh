#!/bin/bash

# Quick AWS Deployment Setup Script
# Choose your deployment method and follow the guided setup

set -e

echo "🚀 US Visa Tracker - AWS Deployment Setup"
echo "=========================================="
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command_exists aws; then
    echo "❌ AWS CLI not found. Please install: https://aws.amazon.com/cli/"
    exit 1
fi

if ! command_exists docker; then
    echo "❌ Docker not found. Please install: https://docs.docker.com/get-docker/"
    exit 1
fi

echo "✅ Prerequisites satisfied"
echo ""

# Get AWS configuration
echo "🔧 AWS Configuration"
aws_account=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "")
aws_region=$(aws configure get region 2>/dev/null || echo "us-east-1")

if [ -z "$aws_account" ]; then
    echo "❌ AWS not configured. Run: aws configure"
    exit 1
fi

echo "✅ AWS Account: $aws_account"
echo "✅ AWS Region: $aws_region"
echo ""

# Choose deployment method
echo "🎯 Choose your deployment method:"
echo "1) EC2 with Docker (Full control, manual setup)"
echo "2) Elastic Beanstalk (Easy, managed platform)"
echo "3) ECS Fargate (Serverless containers)"
echo "4) Just build Docker image for manual deployment"
echo ""

read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo "🖥️  EC2 Deployment Selected"
        echo ""
        echo "📝 Manual steps required:"
        echo "1. Launch EC2 instance (Amazon Linux 2, t3.micro)"
        echo "2. Configure Security Group (ports 22, 80, 5000)"
        echo "3. Copy deploy-ec2.sh to instance and run it"
        echo ""
        echo "💡 Quick launch command:"
        echo "aws ec2 run-instances \\"
        echo "  --image-id ami-0c02fb55956c7d316 \\"
        echo "  --count 1 \\"
        echo "  --instance-type t3.micro \\"
        echo "  --key-name YOUR_KEY_PAIR \\"
        echo "  --security-group-ids YOUR_SECURITY_GROUP"
        ;;
        
    2)
        echo "🌐 Elastic Beanstalk Deployment"
        echo ""
        
        # Install EB CLI if not present
        if ! command_exists eb; then
            echo "📦 Installing EB CLI..."
            pip install awsebcli
        fi
        
        # Create application.py if not exists
        if [ ! -f "application.py" ]; then
            echo "✅ application.py already exists"
        fi
        
        # Initialize EB
        read -p "Enter application name (default: visa-tracker): " app_name
        app_name=${app_name:-visa-tracker}
        
        echo "🚀 Initializing Elastic Beanstalk..."
        eb init "$app_name" --region "$aws_region" --platform python-3.11
        
        # Create environment
        read -p "Enter environment name (default: visa-tracker-prod): " env_name
        env_name=${env_name:-visa-tracker-prod}
        
        echo "🌍 Creating environment..."
        eb create "$env_name" --instance-type t3.micro
        
        echo "🚀 Deploying application..."
        eb deploy
        
        echo "✅ Deployment complete!"
        eb open
        ;;
        
    3)
        echo "🐳 ECS Fargate Deployment"
        echo ""
        
        # Create ECR repository
        repo_name="visa-tracker"
        echo "📦 Creating ECR repository..."
        aws ecr create-repository --repository-name "$repo_name" --region "$aws_region" || echo "Repository might already exist"
        
        # Get ECR login
        echo "🔐 Logging into ECR..."
        aws ecr get-login-password --region "$aws_region" | docker login --username AWS --password-stdin "$aws_account.dkr.ecr.$aws_region.amazonaws.com"
        
        # Build and push image
        echo "🏗️  Building Docker image..."
        docker build -t "$repo_name" .
        docker tag "$repo_name:latest" "$aws_account.dkr.ecr.$aws_region.amazonaws.com/$repo_name:latest"
        
        echo "⬆️  Pushing to ECR..."
        docker push "$aws_account.dkr.ecr.$aws_region.amazonaws.com/$repo_name:latest"
        
        # Update task definition with actual account ID
        sed "s/YOUR_ACCOUNT_ID/$aws_account/g" ecs-task-definition.json > ecs-task-definition-updated.json
        
        echo "📋 Registering ECS task definition..."
        aws ecs register-task-definition --cli-input-json file://ecs-task-definition-updated.json --region "$aws_region"
        
        echo "✅ ECS setup complete!"
        echo "💡 Next steps:"
        echo "1. Create ECS cluster: aws ecs create-cluster --cluster-name visa-tracker-cluster"
        echo "2. Create service with proper networking configuration"
        echo "3. Configure Application Load Balancer"
        ;;
        
    4)
        echo "🐳 Building Docker image for manual deployment..."
        
        # Build image
        docker build -t visa-tracker .
        
        echo "✅ Docker image built successfully!"
        echo ""
        echo "🚀 To run locally:"
        echo "docker run -p 5000:5000 -e VISA_TRACKER_EMAIL=your-email@gmail.com -e VISA_TRACKER_PASSWORD=your-app-password visa-tracker"
        echo ""
        echo "📤 To push to your own registry:"
        echo "docker tag visa-tracker your-registry/visa-tracker:latest"
        echo "docker push your-registry/visa-tracker:latest"
        ;;
        
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📚 For detailed instructions, see: AWS-DEPLOYMENT.md"
echo "🔧 Don't forget to configure your email credentials:"
echo "   - VISA_TRACKER_EMAIL=your-email@gmail.com"
echo "   - VISA_TRACKER_PASSWORD=your-gmail-app-password"
echo ""
echo "🔗 Health check endpoint: /health"
echo "👥 Admin panel: /admin/subscriptions"
