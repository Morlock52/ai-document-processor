# Production Deployment Instructions

## 🚨 **Important: Port Conflict Detected**

Your server already has nginx running on port 80. The app will be deployed on alternative ports:

- **Frontend**: http://74.208.184.195:3000
- **API**: http://74.208.184.195:8000

## 📦 **Quick Deployment Steps**

### 1. Transfer Files
```bash
scp document-processor.tar.gz root@74.208.184.195:/tmp/
```

### 2. Deploy on Server
```bash
ssh root@74.208.184.195

# Create app directory
mkdir -p /opt/document-processor
cd /opt/document-processor

# Extract files
tar -xzf /tmp/document-processor.tar.gz
rm /tmp/document-processor.tar.gz

# Create environment file
cat > .env << 'EOF'
OPENAI_API_KEY=sk-your-openai-key-here
DATABASE_URL=postgresql://docuser:docpass@postgres:5432/docprocessor
REDIS_URL=redis://redis:6379/0
UPLOAD_DIR=/app/uploads
MAX_UPLOAD_SIZE=104857600
EOF

# Install Docker & Docker Compose (if needed)
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
fi

if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Use production configuration
cp docker-compose.prod.yml docker-compose.yml

# Deploy
docker-compose up -d --build

# Check status
docker-compose ps
```

### 3. Configure OpenAI API Key
```bash
nano .env
# Replace sk-your-openai-key-here with your actual key
docker-compose restart
```

## 🌐 **Access URLs**

After deployment:
- **Main App**: http://74.208.184.195:3000
- **API Docs**: http://74.208.184.195:8000/docs

## ✅ **Verification**

```bash
# Check all services are running
docker-compose ps

# Test frontend
curl http://74.208.184.195:3000

# Test API
curl http://74.208.184.195:8000/health
```

## 🎨 **What's Deployed**

✅ Modern UI with dark/light themes  
✅ AI-powered PDF processing (GPT-4o)  
✅ Real-time status updates  
✅ Excel export functionality  
✅ Responsive design  
✅ All recent bug fixes included  

## 🔧 **Reverse Proxy (Optional)**

If you want to serve the app on port 80, you can configure nginx:

```nginx
# Add to your nginx config
location /document-processor/ {
    proxy_pass http://localhost:3000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

Then access at: http://74.208.184.195/document-processor/