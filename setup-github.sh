#!/bin/bash

# GitHub Repository Setup Script
# This script helps you create and push the project to GitHub

echo "🚀 AI Document Processor - GitHub Setup"
echo "======================================"
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install git first."
    exit 1
fi

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "⚠️  GitHub CLI (gh) is not installed."
    echo "Install it from: https://cli.github.com/"
    echo ""
    echo "Or proceed with manual setup..."
    USE_GH_CLI=false
else
    USE_GH_CLI=true
fi

# Initialize git if not already
if [ ! -d .git ]; then
    echo "📁 Initializing Git repository..."
    git init
    git add .
    git commit -m "Initial commit: AI Document Processor"
fi

# Get GitHub username
read -p "Enter your GitHub username: " GITHUB_USERNAME
echo ""

# Repository name
REPO_NAME="ai-document-processor"
read -p "Repository name (default: $REPO_NAME): " INPUT_REPO_NAME
if [ ! -z "$INPUT_REPO_NAME" ]; then
    REPO_NAME=$INPUT_REPO_NAME
fi

# Create repository using gh CLI or provide manual instructions
if [ "$USE_GH_CLI" = true ]; then
    echo "Creating repository on GitHub..."
    gh repo create $REPO_NAME --public --description "Transform PDFs into structured data with GPT-4o Vision" --source=. --remote=origin --push
    
    if [ $? -eq 0 ]; then
        echo "✅ Repository created successfully!"
        REPO_URL="https://github.com/$GITHUB_USERNAME/$REPO_NAME"
    else
        echo "❌ Failed to create repository. Please create it manually."
        exit 1
    fi
else
    echo "📝 Manual Setup Instructions:"
    echo "=============================="
    echo ""
    echo "1. Go to https://github.com/new"
    echo "2. Repository name: $REPO_NAME"
    echo "3. Description: Transform PDFs into structured data with GPT-4o Vision"
    echo "4. Make it Public"
    echo "5. Don't initialize with README, .gitignore, or license"
    echo "6. Click 'Create repository'"
    echo ""
    read -p "Press Enter after creating the repository..."
    
    REPO_URL="https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"
fi

# Add remote and push
echo ""
echo "📤 Pushing code to GitHub..."

# Update README with correct username
sed -i.bak "s/yourusername/$GITHUB_USERNAME/g" README.md
rm README.md.bak

# Commit the username update
git add README.md
git commit -m "docs: Update README with correct GitHub username"

# Add remote if not exists
if ! git remote | grep -q "origin"; then
    git remote add origin $REPO_URL
fi

# Push to GitHub
git branch -M main
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Success! Your project is now on GitHub!"
    echo ""
    echo "🔗 Repository URL: https://github.com/$GITHUB_USERNAME/$REPO_NAME"
    echo ""
    echo "📋 Next steps:"
    echo "1. Add your OpenAI API key as a GitHub Secret (for CI/CD)"
    echo "2. Enable GitHub Pages for documentation (optional)"
    echo "3. Set up branch protection rules"
    echo "4. Invite collaborators"
    echo ""
    echo "⭐ Don't forget to star your own repository!"
else
    echo ""
    echo "❌ Failed to push to GitHub. Please check your credentials and try again."
    echo ""
    echo "Manual push commands:"
    echo "git remote add origin $REPO_URL"
    echo "git branch -M main"
    echo "git push -u origin main"
fi