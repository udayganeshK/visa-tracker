#!/bin/bash

set -e

REPO_NAME="visa-tracker"

echo "🚀 Preparing to push visa-tracker to GitHub..."

# Run GitHub checks first
./check_github.sh

# Initialize git if not already done
if [ ! -d .git ]; then
    echo "📦 Initializing git repository..."
    git init
    git branch -M main
fi

# Add all files
echo "📁 Adding files to git..."
git add .

# Commit changes
echo "💾 Committing changes..."
git commit -m "Initial commit: Visa tracker application with subscription management" || echo "No changes to commit"

# Check if remote exists
if ! git remote get-url origin &> /dev/null; then
    echo "🔗 Adding GitHub remote..."
    echo "Please enter your GitHub username:"
    read GITHUB_USERNAME
    git remote add origin git@github.com:${GITHUB_USERNAME}/${REPO_NAME}.git
fi

# Create repository on GitHub if GitHub CLI is available
if command -v gh &> /dev/null && gh auth status &> /dev/null; then
    echo "🏗️  Creating repository on GitHub..."
    gh repo create $REPO_NAME --public --source=. --remote=origin --push || echo "Repository might already exist"
else
    echo "⚠️  Please create the repository manually on GitHub: https://github.com/new"
    echo "Repository name: $REPO_NAME"
    echo "Then run: git push -u origin main"
fi

echo "✅ Done! Your visa-tracker project should now be on GitHub"
