#!/bin/bash

# Port checking and configuration script for Document Processor

# Default ports
FRONTEND_PORT=3000
BACKEND_PORT=8000
POSTGRES_PORT=5432
REDIS_PORT=6379

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 1  # Port is in use
    else
        return 0  # Port is free
    fi
}

# Function to find next available port
find_available_port() {
    local start_port=$1
    local port=$start_port
    
    while ! check_port $port; do
        ((port++))
        if [ $port -gt 65535 ]; then
            echo "No available ports found" >&2
            return 1
        fi
    done
    
    echo $port
}

echo "Checking port availability for Document Processor..."
echo "=================================================="

# Check and assign ports
if check_port $FRONTEND_PORT; then
    echo -e "${GREEN}✓${NC} Frontend port $FRONTEND_PORT is available"
else
    echo -e "${YELLOW}!${NC} Frontend port $FRONTEND_PORT is in use"
    FRONTEND_PORT=$(find_available_port $FRONTEND_PORT)
    echo -e "${GREEN}✓${NC} Using alternative frontend port: $FRONTEND_PORT"
fi

if check_port $BACKEND_PORT; then
    echo -e "${GREEN}✓${NC} Backend port $BACKEND_PORT is available"
else
    echo -e "${YELLOW}!${NC} Backend port $BACKEND_PORT is in use"
    BACKEND_PORT=$(find_available_port $BACKEND_PORT)
    echo -e "${GREEN}✓${NC} Using alternative backend port: $BACKEND_PORT"
fi

if check_port $POSTGRES_PORT; then
    echo -e "${GREEN}✓${NC} PostgreSQL port $POSTGRES_PORT is available"
else
    echo -e "${YELLOW}!${NC} PostgreSQL port $POSTGRES_PORT is in use"
    POSTGRES_PORT=$(find_available_port $POSTGRES_PORT)
    echo -e "${GREEN}✓${NC} Using alternative PostgreSQL port: $POSTGRES_PORT"
fi

if check_port $REDIS_PORT; then
    echo -e "${GREEN}✓${NC} Redis port $REDIS_PORT is available"
else
    echo -e "${YELLOW}!${NC} Redis port $REDIS_PORT is in use"
    REDIS_PORT=$(find_available_port $REDIS_PORT)
    echo -e "${GREEN}✓${NC} Using alternative Redis port: $REDIS_PORT"
fi

# Generate .env.local with port configurations
cat > .env.ports << EOF
# Auto-generated port configuration
# Generated on $(date)

# Service ports
FRONTEND_PORT=$FRONTEND_PORT
BACKEND_PORT=$BACKEND_PORT
POSTGRES_PORT=$POSTGRES_PORT
REDIS_PORT=$REDIS_PORT

# URLs with dynamic ports
NEXT_PUBLIC_API_URL=http://localhost:$BACKEND_PORT/api/v1
DATABASE_URL=postgresql://docuser:docpass@localhost:$POSTGRES_PORT/docprocessor
REDIS_URL=redis://localhost:$REDIS_PORT
EOF

echo ""
echo "Port configuration saved to .env.ports"
echo "=================================================="
echo "Frontend URL: http://localhost:$FRONTEND_PORT"
echo "Backend URL: http://localhost:$BACKEND_PORT"
echo "API Docs: http://localhost:$BACKEND_PORT/docs"
echo "=================================================="

# Export for use in other scripts
export FRONTEND_PORT
export BACKEND_PORT
export POSTGRES_PORT
export REDIS_PORT