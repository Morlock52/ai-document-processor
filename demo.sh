#!/bin/bash

# Demo script to show the application running locally
# This creates a quick demo environment

set -e

echo "🚀 AI Document Processor - Live Demo"
echo "===================================="
echo ""

# Check prerequisites
echo "Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required but not installed."
    echo "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

echo "✅ Docker is installed and running"

# Check for .env file
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please add your OpenAI API key to .env file"
    echo ""
    echo "Opening .env file for editing..."
    
    # Try to open in default editor
    if command -v code &> /dev/null; then
        code .env
    elif command -v nano &> /dev/null; then
        nano .env
    else
        echo "Please edit .env manually and add your OPENAI_API_KEY"
    fi
    
    echo ""
    read -p "Press Enter after adding your OpenAI API key..."
fi

# Check if OpenAI key is set
if ! grep -q "OPENAI_API_KEY=sk-" .env; then
    echo "❌ OpenAI API key not found in .env"
    echo "Please add: OPENAI_API_KEY=sk-your-key-here"
    exit 1
fi

echo "✅ OpenAI API key configured"
echo ""

# Run port check
echo "Checking port availability..."
python3 scripts/check_ports.py || ./scripts/check-ports.sh

# Load port configuration
if [ -f .env.ports ]; then
    export $(cat .env.ports | grep -v '^#' | xargs)
fi

echo ""
echo "🏗️  Building and starting services..."
echo "This may take a few minutes on first run..."
echo ""

# Start services
docker-compose up -d

# Wait for services to be ready
echo ""
echo "⏳ Waiting for services to start..."

# Function to check if service is ready
check_service() {
    local service=$1
    local url=$2
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s $url > /dev/null 2>&1; then
            return 0
        fi
        attempt=$((attempt + 1))
        printf "."
        sleep 2
    done
    return 1
}

# Check backend
printf "Waiting for backend"
if check_service "backend" "http://localhost:${BACKEND_PORT:-8000}/health"; then
    echo " ✅"
else
    echo " ❌"
    echo "Backend failed to start. Check logs: docker-compose logs api"
    exit 1
fi

# Check frontend
printf "Waiting for frontend"
if check_service "frontend" "http://localhost:${FRONTEND_PORT:-3000}"; then
    echo " ✅"
else
    echo " ❌"
    echo "Frontend failed to start. Check logs: docker-compose logs frontend"
    exit 1
fi

echo ""
echo "✅ All services are running!"
echo ""
echo "======================================"
echo "🎉 AI Document Processor is ready!"
echo "======================================"
echo ""
echo "📍 Frontend: http://localhost:${FRONTEND_PORT:-3000}"
echo "📍 Backend API: http://localhost:${BACKEND_PORT:-8000}"
echo "📍 API Documentation: http://localhost:${BACKEND_PORT:-8000}/docs"
echo ""
echo "📋 Quick Start:"
echo "1. Open http://localhost:${FRONTEND_PORT:-3000} in your browser"
echo "2. Drag and drop a PDF file"
echo "3. Watch AI extract the data"
echo "4. Download as Excel"
echo ""
echo "📊 View logs:"
echo "docker-compose logs -f"
echo ""
echo "🛑 To stop:"
echo "docker-compose down"
echo ""

# Ask if user wants to open browser
read -p "Would you like to open the application in your browser? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Try to open browser based on OS
    URL="http://localhost:${FRONTEND_PORT:-3000}"
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        open $URL
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v xdg-open &> /dev/null; then
            xdg-open $URL
        elif command -v gnome-open &> /dev/null; then
            gnome-open $URL
        fi
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        # Windows
        start $URL
    fi
fi

echo ""
echo "💡 Tips:"
echo "- Upload multiple PDFs at once for batch processing"
echo "- Check the API docs for integration examples"
echo "- View real-time logs: docker-compose logs -f"
echo ""
echo "Enjoy the demo! 🚀"