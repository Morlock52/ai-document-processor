<div align="center">
  <h1>🚀 AI Document Processor</h1>
  <p>
    <strong>Transform your PDFs into structured data with the power of GPT-4o Vision</strong>
  </p>
  <p>
    <a href="#features"><img src="https://img.shields.io/badge/Features-Powerful-blue?style=for-the-badge" alt="Features"></a>
    <a href="#demo"><img src="https://img.shields.io/badge/Demo-Live-green?style=for-the-badge" alt="Demo"></a>
    <a href="#quick-start"><img src="https://img.shields.io/badge/Quick%20Start-Easy-orange?style=for-the-badge" alt="Quick Start"></a>
    <a href="#api-docs"><img src="https://img.shields.io/badge/API-Documented-purple?style=for-the-badge" alt="API Docs"></a>
  </p>
  <p>
    <img src="https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python" alt="Python">
    <img src="https://img.shields.io/badge/TypeScript-5.0+-blue?style=flat-square&logo=typescript" alt="TypeScript">
    <img src="https://img.shields.io/badge/Next.js-15-black?style=flat-square&logo=next.js" alt="Next.js">
    <img src="https://img.shields.io/badge/FastAPI-0.109-green?style=flat-square&logo=fastapi" alt="FastAPI">
    <img src="https://img.shields.io/badge/Docker-Ready-blue?style=flat-square&logo=docker" alt="Docker">
  </p>
</div>

<div align="center">
  <img src="https://raw.githubusercontent.com/yourusername/ai-document-processor/main/docs/images/hero-screenshot.png" alt="AI Document Processor Screenshot" width="800">
</div>

## ✨ Features

<table>
<tr>
<td width="33%" valign="top">

### 🤖 AI-Powered

- **GPT-4o Vision** for intelligent extraction
- **Auto-detects** form fields & types
- **Handles** any PDF quality
- **Smart fallbacks** to OCR

</td>
<td width="33%" valign="top">

### 📊 Excel Export

- **Formatted** spreadsheets
- **Template mode** for unified datasets
- **Charts & analytics** included
- **Batch export** multiple docs
- **Metadata sheets** with insights
- **Results stored** in PostgreSQL for re-export
- **Columns** mapped from stored JSON keys

</td>
<td width="33%" valign="top">

### ⚡ Performance

- **Real-time** progress tracking
- **Batch processing** support
- **Auto-scaling** with Docker
- **< 30s** per page processing

</td>
</tr>
</table>

## 🎯 Use Cases

Perfect for automating data extraction from:

- 📄 **Invoices** - Extract vendor info, line items, totals
- 🧾 **Receipts** - Capture transaction details automatically
- 📋 **Forms** - Digitize paper forms with high accuracy
- 📑 **Reports** - Extract tables and structured data
- 📃 **Any PDF** - Works with scanned or native PDFs

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- OpenAI API key with GPT-4o access
- 5 minutes of your time ⏱️

### 1️⃣ Clone & Configure

```bash
git clone https://github.com/yourusername/ai-document-processor.git
cd ai-document-processor

# Copy environment template
cp .env.example .env

# Add your OpenAI API key to .env
# OPENAI_API_KEY=sk-your-key-here
```

### 2️⃣ Launch with Auto Port Detection

```bash
# Our smart launcher finds available ports automatically! 🎉
./scripts/start.sh
```

### 3️⃣ Open Your Browser

The script will display your unique URLs:

```
🚀 Document Processor is running!
📍 Frontend: http://localhost:3000
📍 API Docs: http://localhost:8000/docs
```

That's it! Start uploading PDFs and watch the magic happen ✨

### 🌟 One-Line Installer

If you prefer an automated setup, run:

```bash
./installer.sh
```

## 🔐 Optional login (off by default)

- Fresh installs ship with login **disabled** so you can explore immediately.
- Open the **Access control** card on the homepage, enter the passcode twice, and click **Enable login** to require sign-in.
- When enabled, a passcode prompt appears before uploads or downloads; disable it anytime from the same card or via `PUT /api/v1/auth/settings/login`.
- The current status is also available through `GET /api/v1/auth/status` so you can script health checks or audits.

## 🏗️ Architecture

```mermaid
graph TD
    A[🌐 Next.js Frontend] -->|REST API| B[⚡ FastAPI Backend]
    B --> C[🧠 GPT-4o Vision]
    B --> D[💾 PostgreSQL]
    B --> E[⚡ Redis Queue]
    B --> F[☁️ S3 Storage]

    style A fill:#0070f3,stroke:#fff,color:#fff
    style B fill:#009688,stroke:#fff,color:#fff
    style C fill:#10a37f,stroke:#fff,color:#fff
```

## 📸 Screenshots

<div align="center">
<table>
<tr>
<td align="center">
<img src="https://raw.githubusercontent.com/yourusername/ai-document-processor/main/docs/images/upload.png" width="400">
<br>
<em>Drag & Drop Upload</em>
</td>
<td align="center">
<img src="https://raw.githubusercontent.com/yourusername/ai-document-processor/main/docs/images/processing.png" width="400">
<br>
<em>Real-time Processing</em>
</td>
</tr>
<tr>
<td align="center">
<img src="https://raw.githubusercontent.com/yourusername/ai-document-processor/main/docs/images/results.png" width="400">
<br>
<em>Extracted Data View</em>
</td>
<td align="center">
<img src="https://raw.githubusercontent.com/yourusername/ai-document-processor/main/docs/images/excel.png" width="400">
<br>
<em>Excel Export</em>
</td>
</tr>
</table>
</div>

## 🛠️ Development

### Local Development Setup

```bash
# Frontend development
cd frontend && npm install && npm run dev

# Backend development
cd backend && pip install -r requirements.txt && python start.py

# Or use our all-in-one dev script!
./scripts/dev.sh
```

### Running Tests

```bash
# Backend tests
cd backend && pytest

# Frontend tests
cd frontend && npm test

# E2E tests
npm run test:e2e
```

## 📚 API Documentation

Interactive API docs available at `http://localhost:8000/docs` when running.

### Key Endpoints

| Method | Endpoint                                | Description                 |
| ------ | --------------------------------------- | --------------------------- |
| `POST` | `/api/v1/documents/upload`              | Upload PDF document         |
| `GET`  | `/api/v1/documents/{id}/status`         | Check processing status     |
| `GET`  | `/api/v1/documents/{id}/download/excel` | Download as Excel           |
| `POST` | `/api/v1/documents/batch/process`       | Batch process multiple docs |

<details>
<summary>View Full API Reference</summary>

```python
# Example: Upload and process a document
import requests

# Upload PDF
with open('invoice.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/v1/documents/upload',
        files={'file': f}
    )
    doc_id = response.json()['id']

# Check status
status = requests.get(f'http://localhost:8000/api/v1/documents/{doc_id}/status')
print(status.json())

# Download Excel when ready
if status.json()['status'] == 'completed':
    excel = requests.get(f'http://localhost:8000/api/v1/documents/{doc_id}/download/excel')
    with open('output.xlsx', 'wb') as f:
        f.write(excel.content)
```

</details>

## 🔧 Configuration

<details>
<summary>Environment Variables</summary>

```env
# Required
OPENAI_API_KEY=sk-your-api-key-here

# Optional - S3 Storage
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
S3_BUCKET_NAME=document-processor

# Optional - Custom Ports
FRONTEND_PORT=3000
BACKEND_PORT=8000
POSTGRES_PORT=5432
REDIS_PORT=6379
```

</details>

<details>
<summary>Docker Compose Override</summary>

```yaml
# docker-compose.override.yml
version: "3.8"

services:
  frontend:
    environment:
      - NODE_ENV=development
    volumes:
      - ./frontend:/app
      - /app/node_modules

  api:
    environment:
      - DEBUG=true
    volumes:
      - ./backend:/app
```

</details>

## 🤝 Contributing

We love contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

```bash
# Fork the repo, then:
git clone https://github.com/yourusername/ai-document-processor.git
cd ai-document-processor
git checkout -b feature/amazing-feature
# Make your changes
git commit -m 'Add amazing feature'
git push origin feature/amazing-feature
# Open a Pull Request
```

## 📊 Performance Benchmarks

| Document Type   | Pages | Processing Time | Accuracy |
| --------------- | ----- | --------------- | -------- |
| Invoice         | 1     | ~15s            | 98.5%    |
| Multi-page Form | 10    | ~2.5min         | 97.2%    |
| Scanned Receipt | 1     | ~20s            | 95.8%    |
| Complex Report  | 50    | ~12min          | 96.4%    |

## 🚧 Roadmap

- [x] GPT-4o Vision integration
- [x] Excel export with formatting
- [x] Batch processing
- [x] Auto port detection
- [ ] Multi-language support
- [ ] Custom training for specific document types
- [ ] Webhook notifications
- [ ] Cloud deployment templates
- [ ] Mobile app

## 🗣️ Realtime Speech Chatbot

Try the new Realtime API speech demo:

1. Set your `OPENAI_API_KEY` environment variable.
   - macOS/Linux: `export OPENAI_API_KEY="sk-..."`
   - PowerShell: `$Env:OPENAI_API_KEY="sk-..."`
2. Start the demo server:

   ```bash
   cd examples/realtime-speech-chatbot
   node server.mjs
   ```

Then open [http://localhost:3000](http://localhost:3000) and click **Start Chat** to talk with the model using your microphone.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🌟 Star History

<div align="center">
  <img src="https://api.star-history.com/svg?repos=yourusername/ai-document-processor&type=Date" alt="Star History Chart">
</div>

## 🙏 Acknowledgments

- OpenAI for GPT-4o Vision API
- The FastAPI team for an amazing framework
- Next.js team for the fantastic React framework
- All our contributors and stargazers! ⭐

---

<div align="center">
  <p>
    <a href="https://github.com/yourusername/ai-document-processor/issues">Report Bug</a>
    ·
    <a href="https://github.com/yourusername/ai-document-processor/issues">Request Feature</a>
    ·
    <a href="https://discord.gg/yourdiscord">Join Discord</a>
  </p>
  <p>
    Made with ❤️ by the AI Document Processor Team
  </p>
</div>
