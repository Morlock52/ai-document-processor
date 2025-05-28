# 🖼️ AI Document Processor - App Preview

## 🏠 Main Dashboard
```
┌─────────────────────────────────────────────────────────────┐
│ 🚀 Document Processor                                       │
│ AI-powered PDF data extraction and Excel export            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [Upload Documents] [Document List]                         │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │                                                       │  │
│  │         📄 Drag & drop PDF files here               │  │
│  │              or click to select                      │  │
│  │                                                       │  │
│  │     Supports batch upload up to 100 files           │  │
│  │                                                       │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  How it works:                                             │
│  1️⃣ Upload PDFs    2️⃣ AI Processing    3️⃣ Export Excel    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 📤 Upload Progress
```
┌─────────────────────────────────────────────────────────────┐
│ Uploaded Files                                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 📄 invoice-2024-001.pdf                      ✅ Uploaded    │
│     2.3 MB                                                  │
│     ████████████████████████████████████ 100%             │
│                                                             │
│ 📄 receipt-store-receipt.pdf                 ⏳ Processing  │
│     1.1 MB                                                  │
│     ████████████████░░░░░░░░░░░░░░░░░░░ 65%              │
│                                                             │
│ 📄 application-form.pdf                      📤 Uploading   │
│     3.5 MB                                                  │
│     ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░ 25%              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 📊 Document List View
```
┌─────────────────────────────────────────────────────────────┐
│ Documents                                    [↻ Refresh]    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ □ Filename              Status      Progress   Actions      │
│ ─────────────────────────────────────────────────────────  │
│ ☑ invoice-2024-001.pdf  ✅ Done     100%      [📥] [🗑️]    │
│ ☑ receipt-march.pdf     ✅ Done     100%      [📥] [🗑️]    │
│ □ form-application.pdf  ⚡ Processing 45%     [  ] [🗑️]    │
│ □ report-annual.pdf     ⏳ Pending    0%      [  ] [🗑️]    │
│                                                             │
│ [Download Selected (2)]                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Extracted Data Preview
```
┌─────────────────────────────────────────────────────────────┐
│ invoice-2024-001.pdf - Extracted Data                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Document Type: Invoice (98% confidence)                     │
│                                                             │
│ ┌─────────────────────────────────────────────────────┐   │
│ │ Invoice Number: INV-2024-001                        │   │
│ │ Date: March 15, 2024                                │   │
│ │ Vendor: Tech Solutions Inc.                         │   │
│ │ Customer: ABC Corporation                           │   │
│ │                                                     │   │
│ │ Line Items:                                         │   │
│ │ - Software License x 10     $500.00                │   │
│ │ - Support Contract x 1      $150.00                │   │
│ │                                                     │   │
│ │ Subtotal: $650.00                                  │   │
│ │ Tax (8%): $52.00                                   │   │
│ │ Total: $702.00                                     │   │
│ └─────────────────────────────────────────────────────┘   │
│                                                             │
│ [📥 Download Excel]  [🔄 Reprocess]  [📝 Edit]            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 📈 Excel Export Preview
```
┌─────────────────────────────────────────────────────────────┐
│ 📊 Excel File Generated: invoice-2024-001_extracted.xlsx    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Sheet 1: Extracted Data                                     │
│ ┌─────┬──────────────┬──────────────┬──────────────┐      │
│ │ Doc │ Invoice No   │ Date         │ Total        │      │
│ ├─────┼──────────────┼──────────────┼──────────────┤      │
│ │ 1   │ INV-2024-001 │ 2024-03-15   │ $702.00      │      │
│ └─────┴──────────────┴──────────────┴──────────────┘      │
│                                                             │
│ Sheet 2: Metadata                                           │
│ - Extraction Date: 2024-03-20 14:23:45                    │
│ - AI Model: GPT-4o                                         │
│ - Confidence: 98.5%                                        │
│ - Processing Time: 23.4s                                   │
│                                                             │
│ Sheet 3: Field Statistics                                   │
│ - Total Fields: 12                                         │
│ - Filled: 11 (91.7%)                                      │
│ - Missing: 1 (8.3%)                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 API Documentation (Swagger UI)
```
┌─────────────────────────────────────────────────────────────┐
│ 📚 Document Processor API - v1.0.0                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 📁 Documents                                                │
│   POST   /api/v1/documents/upload         Upload PDF       │
│   GET    /api/v1/documents/{id}/status    Check status     │
│   GET    /api/v1/documents/{id}/excel     Download Excel   │
│   DELETE /api/v1/documents/{id}           Delete document  │
│                                                             │
│ 📋 Schemas                                                  │
│   GET    /api/v1/schemas/                 List schemas     │
│   POST   /api/v1/schemas/detect           Auto-detect      │
│                                                             │
│ [Try it out ▶️]                                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Features Demonstrated

1. **Drag & Drop Upload** - Simple file upload interface
2. **Real-time Progress** - Live status updates
3. **Batch Processing** - Handle multiple files
4. **AI Extraction** - Intelligent data parsing
5. **Excel Export** - Formatted spreadsheets with metadata
6. **API Access** - Full REST API with documentation

## 💻 Running the Demo

To see this in action:

```bash
# Quick demo (with Docker)
./demo.sh

# Development mode (without Docker)
./scripts/dev.sh

# Just check if it would work
./scripts/check-ports.sh
```

The app will automatically:
- ✅ Check available ports
- ✅ Start all services
- ✅ Open in your browser
- ✅ Show live logs