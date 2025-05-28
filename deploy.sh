#!/bin/bash

# Production deployment script for Document Processor
SERVER_IP="74.208.184.195"
SERVER_USER="root"
SERVER_PASSWORD="Morlock52$"
APP_DIR="/opt/document-processor"

echo "🚀 Starting deployment to $SERVER_IP..."

# Create deployment package
echo "📦 Creating deployment package..."
tar --exclude='node_modules' \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='uploads' \
    --exclude='.next' \
    -czf document-processor.tar.gz .

# Transfer files to server
echo "📤 Transferring files to server..."
sshpass -p "$SERVER_PASSWORD" scp document-processor.tar.gz $SERVER_USER@$SERVER_IP:/tmp/

# Deploy on server
echo "🔧 Deploying on server..."
sshpass -p "$SERVER_PASSWORD" ssh $SERVER_USER@$SERVER_IP << 'EOF'
    # Stop existing containers
    cd /opt/document-processor 2>/dev/null && docker-compose down 2>/dev/null || true
    
    # Create app directory
    mkdir -p /opt/document-processor
    cd /opt/document-processor
    
    # Extract new files
    tar -xzf /tmp/document-processor.tar.gz
    rm /tmp/document-processor.tar.gz
    
    # Create uploads directory
    mkdir -p uploads
    
    # Set up environment variables
    cat > .env << 'ENVEOF'
OPENAI_API_KEY=sk-your-openai-key-here
DATABASE_URL=postgresql://docuser:docpass@postgres:5432/docprocessor
REDIS_URL=redis://redis:6379/0
UPLOAD_DIR=/app/uploads
MAX_UPLOAD_SIZE=104857600
ENVEOF
    
    # Install Docker and Docker Compose if not present
    if ! command -v docker &> /dev/null; then
        curl -fsSL https://get.docker.com | sh
        systemctl enable docker
        systemctl start docker
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
    fi
    
    # Build and start containers
    docker-compose build
    docker-compose up -d
    
    # Wait for services to start
    sleep 10
    
    # Check status
    docker-compose ps
    
    echo "✅ Deployment complete!"
    echo "🌐 App should be available at: http://74.208.184.195"
EOF

echo "🎉 Deployment completed!"
echo "🌐 Access your app at: http://74.208.184.195"

# Clean up
rm document-processor.tar.gz