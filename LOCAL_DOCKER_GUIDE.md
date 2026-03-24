# 🐳 Local Docker Setup Guide

Quick guide to run AI Document Processor locally with Docker.

## Prerequisites

- ✅ Docker Desktop installed and running
- ✅ OpenAI API key with GPT-4o access
- ✅ 4GB+ free RAM
- ✅ 2GB+ free disk space

## 🚀 Quick Start (3 steps)

### 1. Clone & Configure

```bash
# Clone the repository
git clone https://github.com/morlock52/ai-document-processor.git
cd ai-document-processor

# Copy environment template
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-your-key-here
```

### 2. Start with Docker

```bash
# Easy way - use the script
./start-local.sh

# Or manually with docker-compose
docker-compose -f docker-compose.local.yml up -d
```

### 3. Access the Application

Open your browser to:
- 🌐 **Frontend**: http://localhost:3000
- 🔧 **API**: http://localhost:8000
- 📚 **API Docs**: http://localhost:8000/docs

## 📊 What's Running

```
┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   Backend API   │
│   Port 3000     │     │   Port 8000     │
└─────────────────┘     └─────────────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
        ┌─────────────────────────┐
        │  PostgreSQL  │  Redis   │
        │  Port 5432   │  6379    │
        └─────────────────────────┘
```

## 🎯 Using the Application

1. **Upload PDF**: Drag & drop any PDF file
2. **Processing**: Watch real-time progress
3. **View Results**: See extracted data
4. **Download Excel**: Get formatted spreadsheet

## 🛠️ Useful Docker Commands

```bash
# View logs
docker-compose -f docker-compose.local.yml logs -f

# View specific service logs
docker-compose -f docker-compose.local.yml logs -f api
docker-compose -f docker-compose.local.yml logs -f frontend

# Stop all services
docker-compose -f docker-compose.local.yml down

# Stop and remove volumes (full reset)
docker-compose -f docker-compose.local.yml down -v

# Rebuild after code changes
docker-compose -f docker-compose.local.yml up --build

# Check service status
docker-compose -f docker-compose.local.yml ps

# Access backend shell
docker-compose -f docker-compose.local.yml exec api bash

# Access database
docker-compose -f docker-compose.local.yml exec postgres psql -U docuser -d docprocessor
```

## 🔍 Troubleshooting

### Docker not running?
```bash
# Check Docker status
docker info

# If not running, start Docker Desktop
```

### Port already in use?
```bash
# Check what's using the port
lsof -i :3000  # Frontend
lsof -i :8000  # Backend

# Or use our port checker
python scripts/check_ports.py
```

### Backend not starting?
```bash
# Check logs
docker-compose -f docker-compose.local.yml logs api

# Common issues:
# - Missing OPENAI_API_KEY in .env
# - Database connection issues
```

### Frontend not loading?
```bash
# Check if backend is running first
curl http://localhost:8000/health

# Check frontend logs
docker-compose -f docker-compose.local.yml logs frontend
```

### Slow performance?
```bash
# Allocate more resources in Docker Desktop:
# Settings > Resources > Advanced
# - CPUs: 4+
# - Memory: 4GB+
```

## 📁 File Locations

- **Uploaded PDFs**: `./uploads/`
- **Database data**: Docker volume `postgres_data`
- **Logs**: Use `docker-compose logs`

## 🔄 Development Workflow

1. **Make code changes**
2. **Rebuild containers**:
   ```bash
   docker-compose -f docker-compose.local.yml up --build
   ```
3. **Test changes**
4. **View logs** for debugging

## 🧪 Testing the API

```bash
# Upload a PDF
curl -X POST -F "file=@sample.pdf" http://localhost:8000/api/v1/documents/upload

# Check status
curl http://localhost:8000/api/v1/documents/1/status

# Interactive API testing
open http://localhost:8000/docs
```

## 🛑 Stopping Everything

```bash
# Graceful shutdown
docker-compose -f docker-compose.local.yml down

# Full cleanup (removes data)
docker-compose -f docker-compose.local.yml down -v
rm -rf uploads/*
```

## 💡 Tips

- The first build takes 5-10 minutes
- Subsequent starts are much faster
- Backend hot-reloads on code changes
- Frontend requires rebuild for changes
- Check Docker Desktop resources if slow

## Need Help?

- Check logs first: `docker-compose logs`
- Ensure `.env` has valid `OPENAI_API_KEY`
- Restart Docker Desktop if issues persist
- File an issue on GitHub for bugs