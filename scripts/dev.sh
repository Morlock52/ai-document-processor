#!/bin/bash

# Development startup script with automatic port detection
# For local development without Docker

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_ROOT"

echo "Starting Document Processor in Development Mode..."
echo "================================================="
echo ""

# Step 1: Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Step 2: Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed."
    exit 1
fi

# Step 3: Check and assign ports
echo "Checking port availability..."
python3 scripts/check_ports.py

# Load port configuration
if [ -f .env.ports ]; then
    export $(cat .env.ports | grep -v '^#' | xargs)
fi

# Step 4: Check if .env exists
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your OPENAI_API_KEY"
    echo ""
    read -p "Press Enter to continue after adding your API key..."
fi

# Step 5: Install backend dependencies
echo ""
echo "Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing backend dependencies..."
pip install -r requirements.txt

# Step 6: Start backend in background
echo ""
echo "Starting backend server on port $BACKEND_PORT..."
python start.py &
BACKEND_PID=$!

# Step 7: Install frontend dependencies
cd ../frontend

if [ ! -d "node_modules" ]; then
    echo ""
    echo "Installing frontend dependencies..."
    npm install
fi

# Step 8: Wait for backend to be ready
echo ""
echo "Waiting for backend to start..."
sleep 5

# Check if backend is running
if ! curl -s http://localhost:$BACKEND_PORT/health > /dev/null; then
    echo "❌ Backend failed to start"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo "✅ Backend is running at http://localhost:$BACKEND_PORT"

# Step 9: Start frontend
echo ""
echo "Starting frontend server on port $FRONTEND_PORT..."
PORT=$FRONTEND_PORT npm run dev &
FRONTEND_PID=$!

# Step 10: Print access information
sleep 3
echo ""
echo "================================================="
echo "🚀 Document Processor is running!"
echo "================================================="
echo "Frontend: http://localhost:$FRONTEND_PORT"
echo "Backend API: http://localhost:$BACKEND_PORT"
echo "API Documentation: http://localhost:$BACKEND_PORT/docs"
echo "================================================="
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Cleanup function
cleanup() {
    echo ""
    echo "Shutting down services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "Services stopped."
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Wait for processes
wait