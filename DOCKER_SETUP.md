# Docker Setup Guide - AI Document Processor

Complete guide for setting up and running the AI Document Processor in a Docker environment.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Environment Configuration](#environment-configuration)
- [OpenAI Model Configuration](#openai-model-configuration)
- [Service Architecture](#service-architecture)
- [Detailed Setup Steps](#detailed-setup-steps)
- [Common Commands](#common-commands)
- [Troubleshooting](#troubleshooting)
- [Production Deployment](#production-deployment)

---

## Prerequisites

### Required Software
- **Docker**: Version 20.10 or later
- **Docker Compose**: Version 2.0 or later
- **Git**: For cloning the repository

### System Requirements
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: At least 10GB free space
- **OS**: Linux, macOS, or Windows 10/11 with WSL2

### Required API Keys
- **OpenAI API Key**: Required for document processing
  - Sign up at https://platform.openai.com/
  - Create an API key in your OpenAI dashboard
  - Ensure you have credits available

### Optional Services
- **AWS Account**: For S3 storage (optional but recommended for production)

---

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/Morlock52/ai-document-processor.git
cd ai-document-processor
```

### 2. Create Environment File
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```env
# Required - OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4o

# Required - Security
SECRET_KEY=your-secret-key-at-least-32-chars

# Optional - AWS S3 (for production storage)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
S3_BUCKET_NAME=your-bucket-name
AWS_REGION=us-east-1
```

### 3. Start All Services
```bash
docker-compose up -d
```

### 4. Verify Services Are Running
```bash
docker-compose ps
```

Expected output:
```
NAME                          STATUS
ai-document-processor-api     Up (healthy)
ai-document-processor-frontend Up
ai-document-processor-postgres Up (healthy)
ai-document-processor-redis   Up
ai-document-processor-worker  Up
ai-document-processor-nginx   Up
```

### 5. Access the Application
- **Frontend**: http://localhost (via nginx)
- **Frontend Direct**: http://localhost:3005
- **API**: http://localhost:8005
- **API Docs**: http://localhost:8005/api/v1/docs

---

## Environment Configuration

### Complete Environment Variables

#### Core Configuration
```env
# OpenAI Settings
OPENAI_API_KEY=sk-...                    # Required
OPENAI_MODEL=gpt-4o                      # Default (recommended)

# Security
SECRET_KEY=generate-a-secure-random-key  # Required (min 32 chars)

# Database (auto-configured in Docker)
DATABASE_URL=postgresql://docuser:docpass@postgres:5432/docprocessor

# Redis (auto-configured in Docker)
REDIS_URL=redis://redis:6379/0
```

#### Optional Configuration
```env
# AWS S3 Storage
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
S3_BUCKET_NAME=document-processor
AWS_REGION=us-east-1

# Server Ports (if different from defaults)
FRONTEND_PORT=3005
BACKEND_PORT=8005
POSTGRES_PORT=5434
REDIS_PORT=6379
```

### Generating a Secure Secret Key

**Linux/Mac:**
```bash
openssl rand -hex 32
```

**Python:**
```python
import secrets
print(secrets.token_hex(32))
```

**Node.js:**
```javascript
require('crypto').randomBytes(32).toString('hex')
```

---

## OpenAI Model Configuration

### Recommended Models (2025)

The project is configured to use **GPT-4o** by default, which is the optimal choice for document processing with vision capabilities.

#### Model Comparison

| Model | Use Case | Cost | Speed | Vision Quality |
|-------|----------|------|-------|----------------|
| **gpt-4o** (Default) | Production document processing | $5/1M tokens | Fast | Excellent ✅ |
| **gpt-4o-mini** | Cost-effective for simple documents | $0.15/1M tokens | Faster | Good |
| **gpt-4.1** | Complex text/coding tasks | $10/1M tokens | Moderate | Good |

#### Model Features (GPT-4o)
- ✅ **128K token context window**
- ✅ **Direct PDF support** (up to 100 pages, 32MB)
- ✅ **Superior OCR and vision capabilities**
- ✅ **50% cheaper than GPT-4 Turbo**
- ✅ **2x faster processing**
- ✅ **Multimodal: text + images**

### Changing the Model

**Option 1: Environment Variable**
```env
OPENAI_MODEL=gpt-4o-mini  # For cost savings
# or
OPENAI_MODEL=gpt-4o       # For best quality (default)
```

**Option 2: Docker Compose Override**
```bash
OPENAI_MODEL=gpt-4o-mini docker-compose up -d
```

### Cost Optimization Tips

1. **Use gpt-4o-mini for development/testing**
   ```bash
   export OPENAI_MODEL=gpt-4o-mini
   docker-compose restart api worker
   ```

2. **Monitor token usage** via OpenAI dashboard

3. **Set spending limits** in OpenAI account settings

4. **Use image preprocessing** to reduce token consumption
   - The project already includes image optimization
   - Adjust DPI settings in `document_processor.py` if needed

---

## Service Architecture

### Container Overview

```
┌─────────────────────────────────────────────────────────┐
│                        NGINX (Port 80)                   │
│                     Load Balancer/Proxy                  │
└──────────────────┬────────────────┬─────────────────────┘
                   │                │
        ┌──────────▼─────┐  ┌──────▼──────────┐
        │   Frontend     │  │   Backend API   │
        │   (Next.js)    │  │   (FastAPI)     │
        │   Port 3005    │  │   Port 8005     │
        └────────────────┘  └──────┬──────────┘
                                   │
                    ┌──────────────┼───────────────┐
                    │              │               │
            ┌───────▼────┐  ┌─────▼──────┐  ┌────▼─────┐
            │  Worker    │  │ PostgreSQL │  │  Redis   │
            │   (RQ)     │  │   Port     │  │  Port    │
            │            │  │   5434     │  │  6379    │
            └────────────┘  └────────────┘  └──────────┘
```

### Service Descriptions

#### 1. **Frontend** (Next.js)
- **Purpose**: User interface for uploading and managing documents
- **Port**: 3005 (external), 3000 (internal)
- **Technology**: Next.js 14, React, Tailwind CSS
- **Features**:
  - Drag-and-drop upload
  - Real-time processing status
  - Template mode for batch exports
  - Excel download

#### 2. **API** (FastAPI)
- **Purpose**: REST API for document processing
- **Port**: 8005 (external), 8000 (internal)
- **Technology**: FastAPI, Python 3.11
- **Endpoints**:
  - `/api/v1/documents` - Document management
  - `/api/v1/health` - System health checks
  - `/api/v1/docs` - Interactive API documentation

#### 3. **Worker** (Background Tasks)
- **Purpose**: Asynchronous document processing
- **Technology**: RQ (Redis Queue), Python
- **Functions**:
  - PDF to image conversion
  - Image preprocessing (deskew, denoise)
  - GPT-4o Vision API calls
  - Excel generation

#### 4. **PostgreSQL** (Database)
- **Purpose**: Document metadata and status storage
- **Port**: 5434 (external), 5432 (internal)
- **Version**: PostgreSQL 15 Alpine
- **Data**: Document records, processing history

#### 5. **Redis** (Message Queue)
- **Purpose**: Job queue and caching
- **Port**: 6379
- **Version**: Redis 7 Alpine
- **Usage**: Background task coordination

#### 6. **Nginx** (Reverse Proxy)
- **Purpose**: Load balancing and SSL termination
- **Port**: 80 (HTTP), 443 (HTTPS in production)
- **Features**: Request routing, static file serving

---

## Detailed Setup Steps

### Step 1: Install Docker

**Ubuntu/Debian:**
```bash
# Update package index
sudo apt-get update

# Install dependencies
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

**macOS:**
```bash
# Install via Homebrew
brew install --cask docker

# Or download Docker Desktop from:
# https://www.docker.com/products/docker-desktop/
```

**Windows:**
1. Install WSL2: https://docs.microsoft.com/en-us/windows/wsl/install
2. Download Docker Desktop: https://www.docker.com/products/docker-desktop/
3. Enable WSL2 integration in Docker Desktop settings

### Step 2: Verify Docker Installation
```bash
docker --version
# Expected: Docker version 24.0.0 or later

docker compose version
# Expected: Docker Compose version v2.0.0 or later
```

### Step 3: Clone and Configure

```bash
# Clone repository
git clone https://github.com/Morlock52/ai-document-processor.git
cd ai-document-processor

# Create .env file from example
cat > .env << 'EOF'
# OpenAI Configuration
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o

# Security
SECRET_KEY=$(openssl rand -hex 32)

# Optional: AWS S3
# AWS_ACCESS_KEY_ID=
# AWS_SECRET_ACCESS_KEY=
# S3_BUCKET_NAME=
# AWS_REGION=us-east-1
EOF

# Edit .env with your actual values
nano .env  # or vim, code, etc.
```

### Step 4: Build Images
```bash
# Build all services
docker-compose build

# Or build specific service
docker-compose build api
docker-compose build frontend
```

**Build output should show:**
```
✅ Building api...
✅ Building frontend...
✅ Building worker...
```

### Step 5: Initialize Database
```bash
# Start PostgreSQL only
docker-compose up -d postgres

# Wait for database to be ready
docker-compose exec postgres pg_isready -U docuser

# Run migrations (if using Alembic)
docker-compose run --rm api alembic upgrade head
```

### Step 6: Start All Services
```bash
# Start in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f api
```

### Step 7: Verify Health
```bash
# Check API health
curl http://localhost:8005/health

# Expected response:
# {"status":"healthy","version":"1.0.0"}

# Check detailed health (all services)
curl http://localhost:8005/api/v1/health/detailed
```

---

## Common Commands

### Service Management

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart a specific service
docker-compose restart api

# View logs (follow mode)
docker-compose logs -f

# View logs for specific service
docker-compose logs -f api

# Check service status
docker-compose ps

# Stop and remove volumes (⚠️ deletes data)
docker-compose down -v
```

### Development Workflow

```bash
# Rebuild after code changes
docker-compose build api
docker-compose up -d api

# Or rebuild and restart in one command
docker-compose up -d --build api

# View real-time logs
docker-compose logs -f api worker

# Execute commands in container
docker-compose exec api bash
docker-compose exec api python

# Run tests
docker-compose exec api pytest
docker-compose exec api pytest -v --cov

# Run linting
docker-compose exec api flake8 app/
docker-compose exec api black app/ --check
```

### Database Operations

```bash
# Access PostgreSQL CLI
docker-compose exec postgres psql -U docuser -d docprocessor

# Backup database
docker-compose exec postgres pg_dump -U docuser docprocessor > backup.sql

# Restore database
docker-compose exec -T postgres psql -U docuser docprocessor < backup.sql

# Reset database (⚠️ deletes all data)
docker-compose down -v
docker-compose up -d postgres
docker-compose exec api alembic upgrade head
```

### Redis Operations

```bash
# Access Redis CLI
docker-compose exec redis redis-cli

# View queue length
docker-compose exec redis redis-cli LLEN rq:queue:default

# Clear all keys (⚠️ use with caution)
docker-compose exec redis redis-cli FLUSHALL

# Monitor Redis commands
docker-compose exec redis redis-cli MONITOR
```

### Debugging

```bash
# View container resource usage
docker stats

# Inspect container
docker-compose exec api env

# View container networking
docker network inspect ai-document-processor_document-network

# Shell into container
docker-compose exec api /bin/bash

# View build history
docker-compose images
```

---

## Troubleshooting

### Common Issues

#### 1. Port Already in Use
**Error:** `bind: address already in use`

**Solution:**
```bash
# Check what's using the port
sudo lsof -i :8005
# or
netstat -tulpn | grep 8005

# Kill the process or change port in docker-compose.yml
# Edit docker-compose.yml and change port mapping:
ports:
  - "8006:8000"  # Changed from 8005
```

#### 2. OpenAI API Key Not Working
**Error:** `Invalid API key` or `401 Unauthorized`

**Checklist:**
- [ ] Verify key starts with `sk-`
- [ ] Check key has no extra spaces in `.env`
- [ ] Verify API key has credits in OpenAI dashboard
- [ ] Restart services after updating `.env`:
  ```bash
  docker-compose restart api worker
  ```

#### 3. Database Connection Failed
**Error:** `could not connect to server`

**Solution:**
```bash
# Check if postgres is healthy
docker-compose ps postgres

# View postgres logs
docker-compose logs postgres

# Restart postgres
docker-compose restart postgres

# If needed, recreate with fresh data
docker-compose down postgres
docker volume rm ai-document-processor_postgres_data
docker-compose up -d postgres
```

#### 4. Worker Not Processing Jobs
**Error:** Jobs stuck in "processing" status

**Solution:**
```bash
# Check worker logs
docker-compose logs -f worker

# Restart worker
docker-compose restart worker

# Check Redis connection
docker-compose exec redis redis-cli PING
# Should return: PONG

# Check queue status
docker-compose exec redis redis-cli LLEN rq:queue:default
```

#### 5. Out of Memory
**Error:** `Cannot allocate memory`

**Solution:**
```bash
# Increase Docker memory limit
# Docker Desktop: Settings → Resources → Memory → 6GB

# Or reduce worker memory in docker-compose.yml:
worker:
  deploy:
    resources:
      limits:
        memory: 1G  # Reduced from 2G
```

#### 6. Frontend Cannot Connect to API
**Error:** `Network Error` or `CORS Error`

**Checklist:**
- [ ] Verify API is running: `curl http://localhost:8005/health`
- [ ] Check environment variable in frontend:
  ```bash
  docker-compose exec frontend printenv NEXT_PUBLIC_API_URL
  # Should show: http://api:8000/api/v1
  ```
- [ ] Restart frontend:
  ```bash
  docker-compose restart frontend
  ```

#### 7. PDF Processing Fails
**Error:** `poppler-utils not found`

**Solution:**
```bash
# Verify poppler is installed in backend container
docker-compose exec api which pdftoppm
docker-compose exec api which pdfinfo

# If missing, rebuild backend
docker-compose build --no-cache backend
docker-compose up -d backend
```

### Performance Optimization

#### Reduce Build Time
```bash
# Use build cache
docker-compose build

# Build in parallel
COMPOSE_PARALLEL_LIMIT=4 docker-compose build

# Use BuildKit for faster builds
DOCKER_BUILDKIT=1 COMPOSE_DOCKER_CLI_BUILD=1 docker-compose build
```

#### Monitor Resource Usage
```bash
# Real-time stats
docker stats

# View disk usage
docker system df

# Clean up unused resources
docker system prune -a
docker volume prune
```

---

## Production Deployment

### Production Configuration

Create `docker-compose.prod.yml`:
```yaml
version: '3.8'

services:
  api:
    restart: always
    environment:
      - OPENAI_MODEL=gpt-4o
      - SECRET_KEY=${SECRET_KEY}  # Use strong secret
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '2'
          memory: 4G

  frontend:
    restart: always
    environment:
      - NODE_ENV=production

  postgres:
    restart: always
    volumes:
      - postgres_data:/var/lib/postgresql/data
    deploy:
      resources:
        limits:
          memory: 2G

  redis:
    restart: always
    command: redis-server --appendonly yes
```

### SSL/HTTPS with Nginx

Update `nginx.conf`:
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
    }
}
```

### Deploy to Production
```bash
# Build production images
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Start with production config
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f
```

### Monitoring

```bash
# Health check endpoint
curl https://your-domain.com/api/v1/health/detailed

# Setup monitoring with Prometheus/Grafana (optional)
# Add to docker-compose.prod.yml
```

---

## Advanced Configuration

### Using Different OpenAI Models

For testing/development with lower costs:
```bash
# Use GPT-4o-mini (87% cheaper)
echo "OPENAI_MODEL=gpt-4o-mini" >> .env
docker-compose restart api worker
```

### Custom Upload Directory
```yaml
# docker-compose.yml
services:
  api:
    environment:
      - UPLOAD_DIR=/custom/path
    volumes:
      - /host/custom/path:/custom/path
```

### S3 Configuration
```bash
# Create S3 bucket
aws s3 mb s3://your-document-processor-bucket

# Set CORS policy
aws s3api put-bucket-cors --bucket your-bucket --cors-configuration file://cors.json

# Update .env
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
S3_BUCKET_NAME=your-document-processor-bucket
```

---

## Support & Resources

### Documentation
- [Main README](README.md)
- [API Documentation](http://localhost:8005/api/v1/docs)
- [Contributing Guide](CONTRIBUTING.md)

### External Resources
- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

### Getting Help
- GitHub Issues: https://github.com/Morlock52/ai-document-processor/issues
- OpenAI Community: https://community.openai.com/

---

## Quick Reference

### Essential Commands
```bash
# Start everything
docker-compose up -d

# Stop everything
docker-compose down

# Rebuild and restart
docker-compose up -d --build

# View logs
docker-compose logs -f api

# Check health
curl http://localhost:8005/health

# Shell access
docker-compose exec api bash

# Database backup
docker-compose exec postgres pg_dump -U docuser docprocessor > backup.sql
```

### Default Ports
- Frontend: **3005**
- API: **8005**
- PostgreSQL: **5434**
- Redis: **6379**
- Nginx: **80**

### Default Credentials
- PostgreSQL User: `docuser`
- PostgreSQL Password: `docpass`
- PostgreSQL Database: `docprocessor`

---

**Last Updated:** October 2025
**Project Version:** 1.0.0
**Docker Compose Version:** 3.8
