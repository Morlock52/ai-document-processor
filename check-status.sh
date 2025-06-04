#!/bin/bash

# Status check script for local Docker deployment

echo "🔍 AI Document Processor - Status Check"
echo "======================================"
echo ""

# Function to check service
check_service() {
    local name=$1
    local url=$2
    
    if curl -s $url > /dev/null 2>&1; then
        echo "✅ $name is running at $url"
        return 0
    else
        echo "❌ $name is not responding at $url"
        return 1
    fi
}

# Check Docker
echo "Docker Status:"
if docker info > /dev/null 2>&1; then
    echo "✅ Docker is running"
    
    # Check containers
    echo ""
    echo "Container Status:"
    docker-compose -f docker-compose.local.yml ps
else
    echo "❌ Docker is not running"
    echo "Please start Docker Desktop"
    exit 1
fi

echo ""
echo "Service Health Checks:"
echo "---------------------"

# Check each service
check_service "Frontend" "http://localhost:3000"
check_service "Backend API" "http://localhost:8000/health"
check_service "API Documentation" "http://localhost:8000/docs"

# Check database
echo ""
if docker-compose -f docker-compose.local.yml exec -T postgres pg_isready > /dev/null 2>&1; then
    echo "✅ PostgreSQL is ready"
else
    echo "❌ PostgreSQL is not ready"
fi

# Check Redis
if docker-compose -f docker-compose.local.yml exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is ready"
else
    echo "❌ Redis is not ready"
fi

# Check environment
echo ""
echo "Environment Check:"
echo "-----------------"
if [ -f .env ]; then
    if grep -q "OPENAI_API_KEY=sk-" .env 2>/dev/null; then
        echo "✅ OpenAI API key is configured"
    else
        echo "⚠️  OpenAI API key not found in .env"
    fi
else
    echo "❌ .env file not found"
fi

# Show logs command
echo ""
echo "📋 To view logs:"
echo "   docker-compose -f docker-compose.local.yml logs -f"
echo ""
echo "🌐 Access the app at: http://localhost:3000"
echo ""
