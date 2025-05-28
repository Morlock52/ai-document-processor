# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered document processing web application that extracts data from scanned PDFs using GPT-4o and exports to Excel. Built with Next.js frontend and FastAPI backend.

## Commands

### Development with Docker (Recommended)
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f [service_name]

# Stop services
docker-compose down
```

### Backend Development
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --port 8000

# Run tests
pytest

# Format code
black app/
flake8 app/

# Database migrations (when using Alembic)
alembic upgrade head
alembic revision --autogenerate -m "description"
```

### Frontend Development
```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build production
npm run build

# Run linting
npm run lint

# No test script defined yet - would use:
# npm test
```

## Architecture

### Service Communication Flow
```
User → Next.js (3000) → FastAPI (8000) → OpenAI API
                      ↓
                  PostgreSQL (5432)
                  Redis (6379)
```

### Backend Architecture

**Core Processing Pipeline**:
1. Document upload → Save to disk/S3
2. Create DB record with PENDING status
3. Background task triggered
4. PDF → Images conversion (pdf2image)
5. Image enhancement (OpenCV pipeline)
6. GPT-4o vision API call for extraction
7. Fallback to Tesseract OCR if needed
8. Excel generation with openpyxl
9. Update DB with results

**API Pattern**:
- RESTful endpoints under `/api/v1`
- Pydantic models for request/response validation
- Background tasks for async processing
- SQLAlchemy for database operations

**Key Services**:
- `DocumentProcessor`: Main extraction logic with GPT-4o
- `ImagePreprocessor`: Deskew, denoise, enhance scans
- `ExcelExporter`: Formatted Excel with charts/metadata, template mode support
- `SchemaDetector`: Auto-detect document types

### Frontend Architecture

**Component Structure**:
- `DocumentUploader`: Drag-drop upload with progress, template mode toggle
- `DocumentList`: Real-time status monitoring, template download feature
- API client using axios with typed endpoints
- React Query for server state management
- Tailwind + shadcn/ui for consistent styling

**Data Flow**:
1. Upload triggers immediate API call
2. Auto-starts processing on successful upload
3. Polls `/status` endpoint every 5 seconds
4. Downloads Excel via blob response

## Key Configuration

### Environment Variables
```env
# Backend (required)
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://docuser:docpass@localhost:5432/docprocessor

# Backend (optional)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
S3_BUCKET_NAME=

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### Database Schema
- `documents` table: Main document records with status, extracted_data (JSON), processing metadata
- Status enum: pending → processing → completed/failed
- Stores both raw extraction and confidence scores

## Development Patterns

### Adding New Document Types
1. Add schema to `backend/app/api/endpoints/schemas.py` PREDEFINED_SCHEMAS
2. Update prompt in `DocumentProcessor._build_extraction_prompt()`
3. Test with sample documents

### Modifying Extraction Logic
- Main logic in `backend/app/services/document_processor.py`
- Image preprocessing in `ImagePreprocessor` class
- Always handle "N/A" for missing fields

### Frontend State Updates
- Use React Query's `invalidateQueries` after mutations
- Real-time updates via polling (SSE endpoint defined but not implemented)
- Error handling with toast notifications

### Excel Export Customization
- Templates in `ExcelExporter._apply_template()`
- Auto-generates summary sheets with charts
- Metadata sheet includes field statistics
- Template mode: aggregates multiple documents into unified Excel with all detected fields as columns

### Template Mode Feature
- Enable via `template_mode: true` in processing request
- Consolidates all detected fields across documents into columns
- Each document becomes a row in the template sheet
- Download via `/api/v1/documents/template/download/excel` endpoint
- Frontend toggle in DocumentUploader component

## Critical Dependencies

- **OpenAI**: GPT-4o model specifically (not gpt-4)
- **PDF Processing**: Requires poppler-utils system package
- **OCR**: Tesseract must be installed for fallback
- **Database**: PostgreSQL 15+ required
- **Node**: v18+ for Next.js compatibility