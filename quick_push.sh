#!/bin/bash

echo "🔍 Quick GitHub check and push..."

# Test GitHub connection
echo "🔑 Testing GitHub connection..."
ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"
if [ $? -ne 0 ]; then
    echo "❌ GitHub SSH connection failed"
    exit 1
fi
echo "✅ GitHub connection OK"

# Check git status
echo "📊 Checking git status..."
git status --porcelain

# Add and commit changes if any
if [ -n "$(git status --porcelain)" ]; then
    echo "📁 Adding changes..."
    git add .
    
    echo "💾 Committing changes..."
    git commit -m "Update subscription data and configurations"
    
    echo "🚀 Pushing to GitHub..."
    git push
    
    echo "✅ Successfully pushed changes!"
else
    echo "✅ No changes to push - everything up to date!"
fi
