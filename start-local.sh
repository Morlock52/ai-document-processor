#!/bin/bash

# Simple local Docker startup script

echo "🐳 Starting AI Document Processor with Docker"
echo "==========================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running!"
    echo "Please start Docker Desktop and try again."
    exit 1
fi

# Check for .env file
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Add your OpenAI API key to .env file"
    echo "Edit the line: OPENAI_API_KEY=your-key-here"
    echo ""
    read -p "Press Enter after adding your API key..."
fi

# Check if OpenAI key exists
if ! grep -q "OPENAI_API_KEY=sk-" .env 2>/dev/null; then
    echo ""
    echo "⚠️  WARNING: OpenAI API key not found in .env"
    echo "The app will not work without it!"
    echo ""
fi

echo "🏗️  Building Docker images..."
echo "This will take a few minutes on first run..."
echo ""

# Build and start
docker-compose -f docker-compose.local.yml up --build -d

echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are running
echo ""
echo "🔍 Checking services..."

if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend API is running"
else
    echo "❌ Backend API is not responding"
fi

if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is running"
else
    echo "❌ Frontend is not responding"
fi

echo ""
echo "====================================="
echo "🎉 AI Document Processor is ready!"
echo "====================================="
echo ""
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "📝 To view logs:"
echo "   docker-compose -f docker-compose.local.yml logs -f"
echo ""
echo "🛑 To stop:"
echo "   docker-compose -f docker-compose.local.yml down"
echo ""

# Open browser
read -p "Open in browser? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open http://localhost:3000
    elif command -v xdg-open > /dev/null; then
        xdg-open http://localhost:3000
    fi
fi
