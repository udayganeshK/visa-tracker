#!/bin/bash

echo "🔍 Checking GitHub setup..."

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed"
    exit 1
fi

# Check if SSH key exists
if [ ! -f ~/.ssh/id_rsa ] && [ ! -f ~/.ssh/id_ed25519 ]; then
    echo "❌ No SSH key found. Generate one with: ssh-keygen -t ed25519 -C 'your_email@example.com'"
    exit 1
fi

# Check SSH connection to GitHub
echo "🔑 Testing SSH connection to GitHub..."
ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"
if [ $? -eq 0 ]; then
    echo "✅ SSH connection to GitHub successful"
else
    echo "❌ SSH connection failed. Make sure your SSH key is added to GitHub"
    echo "Add your key with: cat ~/.ssh/id_ed25519.pub | pbcopy"
    exit 1
fi

# Check if GitHub CLI is available and authenticated
if command -v gh &> /dev/null; then
    gh auth status &> /dev/null
    if [ $? -eq 0 ]; then
        echo "✅ GitHub CLI authenticated"
    else
        echo "⚠️  GitHub CLI not authenticated. Run: gh auth login"
    fi
else
    echo "⚠️  GitHub CLI not installed. Install with: brew install gh"
fi

echo "✅ GitHub setup looks good!"
