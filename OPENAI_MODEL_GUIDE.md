# OpenAI Model Configuration Guide

## Current Status (2025) ✅

**Your project is already using the optimal model configuration!**

The AI Document Processor is configured to use **GPT-4o**, which is the best OpenAI model for document processing with vision capabilities as of 2025.

---

## Model Overview

### Recommended Model: GPT-4o (Default)

**Current Configuration:**
- Model Name: `gpt-4o`
- Configured in: `backend/app/core/config.py`
- Environment Variable: `OPENAI_MODEL`

**Why GPT-4o is the best choice:**
- ✅ **Superior Vision Capabilities** - Best for OCR and document understanding
- ✅ **128K Token Context** - Can handle large multi-page documents
- ✅ **Direct PDF Support** - New in 2025: up to 100 pages, 32MB
- ✅ **Cost Effective** - 50% cheaper than GPT-4 Turbo
- ✅ **2x Faster** - Improved processing speed
- ✅ **Multimodal** - Handles text + images seamlessly

---

## Model Comparison (2025)

| Feature | gpt-4o (Current) | gpt-4o-mini | gpt-4.1 |
|---------|------------------|-------------|---------|
| **Best For** | Document processing ✅ | Simple docs, dev/testing | Text/coding tasks |
| **Vision Quality** | Excellent | Good | Good |
| **Speed** | Fast (2x GPT-4 Turbo) | Faster | Moderate |
| **Input Cost** | $5 / 1M tokens | $0.15 / 1M tokens | $10 / 1M tokens |
| **Output Cost** | $15 / 1M tokens | $0.60 / 1M tokens | $30 / 1M tokens |
| **Context Window** | 128K tokens | 128K tokens | 1M tokens |
| **PDF Support** | Yes (100 pages) | Yes (100 pages) | Yes |
| **Recommended Use** | Production | Development | Text-heavy tasks |

### Cost Savings Calculation

**Example: Processing 1000 invoices (avg 2 pages each)**

| Model | Estimated Tokens | Cost |
|-------|-----------------|------|
| gpt-4o | ~2M input, 500K output | **$17.50** |
| gpt-4o-mini | ~2M input, 500K output | **$0.60** |
| Savings with mini | - | **96.6%** |

💡 **Recommendation:** Use `gpt-4o-mini` for development/testing, `gpt-4o` for production.

---

## How to Change Models

### Method 1: Environment Variable (Recommended)

Edit your `.env` file:

```env
# For production (best quality)
OPENAI_MODEL=gpt-4o

# For development (cost savings)
OPENAI_MODEL=gpt-4o-mini

# For text-heavy documents
OPENAI_MODEL=gpt-4.1
```

Then restart the services:
```bash
docker-compose restart api worker
```

### Method 2: Docker Compose Override

```bash
# Temporarily use a different model
OPENAI_MODEL=gpt-4o-mini docker-compose up -d

# Or export for session
export OPENAI_MODEL=gpt-4o-mini
docker-compose up -d
```

### Method 3: Update Configuration File

Edit `backend/app/core/config.py`:
```python
# Change the default model
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
```

---

## New Features in 2025

### 1. Direct PDF Input
GPT-4o now supports PDF files directly in the API (announced 2025).

**Benefits:**
- No need to convert PDF → images
- Preserves text quality
- Faster processing
- Reduced token usage

**Limitations:**
- Max 100 pages per request
- Max 32MB total content
- Only works with vision-capable models

**Implementation Status:**
- Current: Project converts PDFs to images (proven approach)
- Future: Can migrate to direct PDF input for potential cost savings

### 2. Vision Fine-Tuning
GPT-4o now supports fine-tuning with images.

**Use Cases:**
- Train on your specific invoice formats
- Improve accuracy for domain-specific documents
- Custom field detection

**Real-world Results:**
- Automat: 61.67% success rate (up from 16.60%)
- Insurance docs: 7% F1 score improvement with just 200 images

### 3. Audio Models (Optional)
New audio-capable models available:
- `gpt-4o-audio-preview`
- `gpt-4o-mini-audio-preview`
- `gpt-4o-realtime-preview`

---

## Model Selection Decision Tree

```
┌─ Need document processing? ─────────────────────────┐
│                                                      │
│  ┌─ Is this production?                             │
│  │  └─ YES → Use gpt-4o (best quality) ✅           │
│  │                                                   │
│  └─ Is this development/testing?                    │
│     └─ YES → Use gpt-4o-mini (97% cheaper) 💰       │
│                                                      │
│  ┌─ Are documents text-heavy (no images)?          │
│  │  └─ YES → Consider gpt-4.1                       │
│  │                                                   │
│  └─ Need maximum accuracy?                          │
│     └─ YES → Use gpt-4o                             │
└──────────────────────────────────────────────────────┘
```

---

## Configuration Best Practices

### 1. Development Environment
```env
# .env.development
OPENAI_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-project-key-for-dev
```

### 2. Production Environment
```env
# .env.production
OPENAI_MODEL=gpt-4o
OPENAI_API_KEY=sk-production-key
SECRET_KEY=<strong-secret-key>
```

### 3. Cost Monitoring

**Set OpenAI spending limits:**
1. Go to https://platform.openai.com/account/limits
2. Set monthly budget cap
3. Enable email alerts at 75%, 90%

**Monitor usage:**
```bash
# Check API usage via OpenAI dashboard
# Or use OpenAI API:
curl https://api.openai.com/v1/usage \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### 4. Rate Limiting

**GPT-4o Rate Limits:**
- Tier 1: 500 RPM (requests per minute)
- Tier 2: 5,000 RPM
- Tier 3: 10,000 RPM

**Handling rate limits in code:**
- Project already implements exponential backoff
- Configured in `document_processor.py`

---

## Testing Different Models

### Quick Comparison Test

```bash
# Test with GPT-4o (production model)
OPENAI_MODEL=gpt-4o docker-compose up -d
# Upload a test document, note quality & cost

# Test with GPT-4o-mini (cost-saving model)
OPENAI_MODEL=gpt-4o-mini docker-compose restart api worker
# Upload same document, compare results

# Check logs for processing time
docker-compose logs api | grep "PROCESSING_TIME"
```

### A/B Testing Script

```python
# backend/scripts/test_models.py
import asyncio
from app.services.document_processor import DocumentProcessor

async def test_models():
    models = ["gpt-4o", "gpt-4o-mini"]
    test_pdf = "sample_invoice.pdf"

    for model in models:
        processor = DocumentProcessor(model=model)
        start = time.time()
        result = await processor.process_pdf(test_pdf)
        duration = time.time() - start

        print(f"{model}: {duration:.2f}s, Fields: {len(result)}")

asyncio.run(test_models())
```

---

## Migration Guide

### From GPT-4 Turbo to GPT-4o

If you were using the old model:

**Before:**
```python
OPENAI_MODEL = "gpt-4-turbo"  # or "gpt-4-vision-preview"
```

**After:**
```python
OPENAI_MODEL = "gpt-4o"  # Recommended
```

**Benefits:**
- ✅ 50% cost reduction
- ✅ 2x faster processing
- ✅ Better vision quality
- ✅ Same or better accuracy

**Migration Steps:**
1. Update `.env`: `OPENAI_MODEL=gpt-4o`
2. Restart services: `docker-compose restart api worker`
3. Test with sample documents
4. Monitor costs in OpenAI dashboard

---

## Troubleshooting

### Error: "Model not found"

**Cause:** Invalid model name or access issue

**Solution:**
```bash
# Verify model name is correct
echo $OPENAI_MODEL

# Valid names (2025):
# - gpt-4o
# - gpt-4o-mini
# - gpt-4.1
# - gpt-4.1-mini

# Check API key has access
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Error: "Rate limit exceeded"

**Cause:** Too many requests

**Solution:**
```bash
# Reduce worker concurrency in docker-compose.yml
worker:
  deploy:
    replicas: 1  # Reduce from higher number

# Or upgrade OpenAI tier at:
# https://platform.openai.com/account/limits
```

### High Costs

**Analysis:**
```bash
# Check token usage in logs
docker-compose logs api | grep "TOKENS_USED"

# Optimize by:
# 1. Using gpt-4o-mini for development
# 2. Reducing image DPI (in document_processor.py)
# 3. Implementing caching for repeated documents
```

---

## Future Roadmap

### Planned Enhancements

1. **Direct PDF Input**
   - Migrate from image-based to PDF-native processing
   - Estimated 30% cost reduction
   - Timeline: Q2 2025

2. **Fine-tuning Support**
   - Train custom model on invoice dataset
   - Improved accuracy for specific document types
   - Timeline: Q3 2025

3. **Hybrid Model Approach**
   - Use gpt-4o-mini for initial classification
   - Use gpt-4o only for complex documents
   - Estimated 60% cost reduction
   - Timeline: Q2 2025

4. **Model Selection API**
   - Allow users to choose model per document
   - Dynamic pricing based on model
   - Timeline: Q4 2025

---

## Resources

### Official Documentation
- [OpenAI GPT-4o Overview](https://platform.openai.com/docs/models/gpt-4o)
- [OpenAI Vision Guide](https://platform.openai.com/docs/guides/vision)
- [OpenAI Pricing](https://openai.com/pricing)

### Project Documentation
- [Docker Setup Guide](DOCKER_SETUP.md)
- [Main README](README.md)
- [Contributing Guide](CONTRIBUTING.md)

### External Resources
- [GPT-4o Announcement](https://openai.com/index/hello-gpt-4o/)
- [Fine-tuning with Vision](https://openai.com/index/introducing-vision-to-the-fine-tuning-api/)

---

## Summary

✅ **Your project is already optimized!**

The AI Document Processor uses **GPT-4o**, which is:
- The latest and best model for document processing (2025)
- 50% cheaper than previous generation
- 2x faster with superior vision capabilities
- Fully configurable via environment variables

**Quick Start:**
```bash
# Production (best quality)
OPENAI_MODEL=gpt-4o docker-compose up -d

# Development (cost savings)
OPENAI_MODEL=gpt-4o-mini docker-compose up -d
```

For detailed Docker setup instructions, see [DOCKER_SETUP.md](DOCKER_SETUP.md).

---

**Last Updated:** October 2025
**OpenAI API Version:** v1
**Recommended Model:** gpt-4o
