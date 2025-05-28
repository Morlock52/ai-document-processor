#!/bin/bash

# Startup script with automatic port detection

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_ROOT"

echo "Starting Document Processor..."
echo ""

# Check ports first
echo "Step 1: Checking port availability..."
source scripts/check-ports.sh

# Load port configuration
if [ -f .env.ports ]; then
    export $(cat .env.ports | grep -v '^#' | xargs)
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo ""
    echo "Step 2: Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your OPENAI_API_KEY"
    echo ""
fi

# Merge .env.ports into .env if needed
if [ -f .env.ports ]; then
    echo "Step 3: Updating .env with port configuration..."
    
    # Backup original .env
    cp .env .env.backup
    
    # Update port-related variables in .env
    while IFS= read -r line; do
        if [[ ! "$line" =~ ^#.*$ ]] && [[ -n "$line" ]]; then
            var_name=$(echo "$line" | cut -d'=' -f1)
            var_value=$(echo "$line" | cut -d'=' -f2-)
            
            # Update or add the variable
            if grep -q "^$var_name=" .env; then
                sed -i.tmp "s|^$var_name=.*|$var_name=$var_value|" .env
            else
                echo "$line" >> .env
            fi
        fi
    done < .env.ports
    
    # Clean up temp files
    rm -f .env.tmp
fi

echo ""
echo "Step 4: Starting services with Docker Compose..."
echo ""

# Start services
if [ "$1" == "--detach" ] || [ "$1" == "-d" ]; then
    docker-compose up -d
else
    docker-compose up
fi