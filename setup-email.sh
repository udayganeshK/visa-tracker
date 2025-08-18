#!/bin/bash
# Email Configuration Setup for Visa Tracker

echo "🔧 VISA TRACKER EMAIL CONFIGURATION SETUP"
echo "==========================================="
echo ""
echo "This script will help you set up email notifications for the visa tracker."
echo ""
echo "📧 Gmail Setup Instructions:"
echo "1. You need a Gmail account with 2-Factor Authentication enabled"
echo "2. Generate an App Password at: https://myaccount.google.com/apppasswords"
echo "3. Choose 'Mail' and your device, then copy the 16-character password"
echo ""

read -p "Enter your Gmail address: " email_address
echo ""
read -p "Enter your Gmail App Password (16 characters, no spaces): " app_password
echo ""

# Export environment variables
export VISA_TRACKER_EMAIL="$email_address"
export VISA_TRACKER_PASSWORD="$app_password"

echo "✅ Environment variables set:"
echo "   VISA_TRACKER_EMAIL: $email_address"
echo "   VISA_TRACKER_PASSWORD: [hidden]"
echo ""

echo "🔄 You can now restart the visa tracker application."
echo "💡 To make these permanent, add these lines to your ~/.bashrc or ~/.zshrc:"
echo "   export VISA_TRACKER_EMAIL='$email_address'"
echo "   export VISA_TRACKER_PASSWORD='$app_password'"
echo ""

echo "🧪 Test the email configuration by visiting:"
echo "   http://localhost:7070/email-config"
echo "   http://localhost:7070/test-email"
echo "   http://localhost:7070/test-confirmation-email"
