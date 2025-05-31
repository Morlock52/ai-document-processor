#!/bin/bash

# AI Document Processor Installer
# This script clones the repository, sets up environment variables, and starts the application using Docker.

set -e

REPO_URL="https://github.com/yourusername/ai-document-processor.git"
INSTALL_DIR="ai-document-processor"

# Check for required commands
for cmd in git docker docker-compose; do
    if ! command -v $cmd >/dev/null 2>&1; then
        echo "Error: $cmd is not installed." >&2
        exit 1
    fi
done

# Clone repo if directory doesn't exist
if [ ! -d "$INSTALL_DIR" ]; then
    echo "Cloning repository from $REPO_URL..."
    git clone "$REPO_URL" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# Create .env if missing
if [ ! -f .env ]; then
    echo "Copying .env.example to .env"
    cp .env.example .env
fi

# Prompt for OpenAI API key if not set
if ! grep -q "OPENAI_API_KEY=" .env; then
    read -p "Enter your OpenAI API key: " OPENAI_API_KEY
    echo "OPENAI_API_KEY=$OPENAI_API_KEY" >> .env
fi

# Start the application
./scripts/start.sh --detach

echo "Installer finished. Access the app at the URLs printed above."
