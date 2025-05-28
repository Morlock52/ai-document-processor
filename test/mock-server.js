const http = require('http');
const fs = require('fs');
const path = require('path');

// Simple mock server for testing
const FRONTEND_PORT = 3003;
const BACKEND_PORT = 8001;

// Backend API mock
const backendServer = http.createServer((req, res) => {
  res.setHeader('Content-Type', 'application/json');
  res.setHeader('Access-Control-Allow-Origin', '*');
  
  if (req.url === '/health') {
    res.writeHead(200);
    res.end(JSON.stringify({ 
      status: 'healthy', 
      version: '1.0.0',
      service: 'Document Processor API (Mock)'
    }));
  } else if (req.url === '/docs') {
    res.setHeader('Content-Type', 'text/html');
    res.writeHead(200);
    res.end(`
      <!DOCTYPE html>
      <html>
      <head><title>API Documentation</title></head>
      <body>
        <div class="swagger-ui">
          <div class="info">
            <h1 class="title">Document Processor API</h1>
            <p>Mock API Documentation</p>
          </div>
        </div>
      </body>
      </html>
    `);
  } else {
    res.writeHead(404);
    res.end(JSON.stringify({ error: 'Not found' }));
  }
});

// Frontend mock
const frontendServer = http.createServer((req, res) => {
  res.setHeader('Content-Type', 'text/html');
  res.writeHead(200);
  res.end(`
    <!DOCTYPE html>
    <html>
    <head>
      <title>Document Processor</title>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <style>
        body { font-family: sans-serif; margin: 0; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: #333; }
        .upload-area { 
          border: 2px dashed #ccc; 
          padding: 40px; 
          text-align: center; 
          margin: 20px 0;
          border-radius: 8px;
        }
        .tabs { display: flex; gap: 10px; margin: 20px 0; }
        .tab { 
          padding: 10px 20px; 
          border: 1px solid #ccc; 
          cursor: pointer;
          background: #f5f5f5;
        }
        .tab[role="tab"] { display: inline-block; }
        .tab.active { background: #fff; border-bottom: none; }
        .content { padding: 20px; border: 1px solid #ccc; }
        input[type="file"] { display: none; }
      </style>
    </head>
    <body>
      <div class="container">
        <h1>🚀 Document Processor</h1>
        <p>AI-powered PDF data extraction and Excel export</p>
        
        <div class="tabs">
          <div class="tab active" role="tab">Upload Documents</div>
          <div class="tab" role="tab">Document List</div>
        </div>
        
        <div class="content">
          <div class="upload-area" role="button">
            <h2>📄 Drag & drop PDF files here</h2>
            <p>or click to select</p>
            <p>Supports batch upload up to 100 files</p>
            <input type="file" accept=".pdf" multiple />
          </div>
          
          <div id="document-list" style="display: none;">
            <h2>Processed Documents</h2>
            <p>No documents uploaded yet.</p>
          </div>
        </div>
      </div>
      
      <script>
        // Simple tab switching
        document.querySelectorAll('[role="tab"]').forEach((tab, index) => {
          tab.addEventListener('click', () => {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            if (index === 0) {
              document.querySelector('.upload-area').style.display = 'block';
              document.querySelector('#document-list').style.display = 'none';
            } else {
              document.querySelector('.upload-area').style.display = 'none';
              document.querySelector('#document-list').style.display = 'block';
            }
          });
        });
        
        // File input handling
        const uploadArea = document.querySelector('.upload-area');
        const fileInput = document.querySelector('input[type="file"]');
        
        uploadArea.addEventListener('click', () => fileInput.click());
        
        fileInput.addEventListener('change', (e) => {
          const files = e.target.files;
          if (files.length > 0) {
            alert(\`Selected \${files.length} file(s): \${files[0].name}\`);
          }
        });
      </script>
    </body>
    </html>
  `);
});

// Start servers
backendServer.listen(BACKEND_PORT, () => {
  console.log(`✅ Mock Backend API running at http://localhost:${BACKEND_PORT}`);
});

frontendServer.listen(FRONTEND_PORT, () => {
  console.log(`✅ Mock Frontend running at http://localhost:${FRONTEND_PORT}`);
});

console.log('\n🧪 Mock servers started for testing');
console.log('Press Ctrl+C to stop\n');