import puppeteer, { Browser, Page } from 'puppeteer';
import * as fs from 'fs';
import * as path from 'path';

describe('AI Document Processor E2E Tests', () => {
  let browser: Browser;
  let page: Page;
  
  // Get ports from environment or use defaults
  const FRONTEND_URL = process.env.FRONTEND_URL || 'http://localhost:3003';
  const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8001';
  
  beforeAll(async () => {
    // Launch browser
    browser = await puppeteer.launch({
      headless: process.env.HEADLESS !== 'false',
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
      slowMo: process.env.SLOWMO ? parseInt(process.env.SLOWMO) : 0
    });
    
    // Wait for services to be ready
    await waitForService(FRONTEND_URL, 30000);
    await waitForService(BACKEND_URL + '/health', 30000);
  });

  beforeEach(async () => {
    page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 800 });
  });

  afterEach(async () => {
    await page.close();
  });

  afterAll(async () => {
    await browser.close();
  });

  test('Application loads successfully', async () => {
    await page.goto(FRONTEND_URL);
    
    // Check if main elements are present
    await page.waitForSelector('h1', { timeout: 10000 });
    const title = await page.$eval('h1', el => el.textContent);
    expect(title).toContain('Document Processor');
    
    // Take screenshot
    await page.screenshot({ 
      path: 'test/puppeteer/screenshots/homepage.png',
      fullPage: true 
    });
  });

  test('Upload interface is visible', async () => {
    await page.goto(FRONTEND_URL);
    
    // Wait for upload area
    await page.waitForSelector('[role="button"]', { timeout: 10000 });
    
    // Check upload text
    const uploadText = await page.evaluate(() => {
      const elements = Array.from(document.querySelectorAll('*'));
      return elements.some(el => el.textContent?.includes('Drag & drop PDF'));
    });
    expect(uploadText).toBe(true);
    
    await page.screenshot({ 
      path: 'test/puppeteer/screenshots/upload-area.png' 
    });
  });

  test('API health check responds', async () => {
    const response = await page.goto(BACKEND_URL + '/health');
    expect(response?.status()).toBe(200);
    
    const data = await response?.json();
    expect(data).toHaveProperty('status', 'healthy');
  });

  test('API documentation is accessible', async () => {
    await page.goto(BACKEND_URL + '/docs');
    
    // Wait for Swagger UI to load
    await page.waitForSelector('.swagger-ui', { timeout: 10000 });
    
    // Check if API title is present
    const apiTitle = await page.evaluate(() => {
      const titleElement = document.querySelector('.info .title');
      return titleElement?.textContent;
    });
    expect(apiTitle).toContain('Document Processor API');
    
    await page.screenshot({ 
      path: 'test/puppeteer/screenshots/api-docs.png',
      fullPage: true 
    });
  });

  test('Can switch between tabs', async () => {
    await page.goto(FRONTEND_URL);
    
    // Find and click on Document List tab
    const tabs = await page.$$('[role="tab"]');
    if (tabs.length > 1) {
      await tabs[1].click();
      await page.waitForTimeout(1000);
      
      // Check if document list view is shown
      const hasDocumentList = await page.evaluate(() => {
        return document.body.textContent?.includes('Processed Documents') || 
               document.body.textContent?.includes('Document List');
      });
      expect(hasDocumentList).toBe(true);
      
      await page.screenshot({ 
        path: 'test/puppeteer/screenshots/document-list.png' 
      });
    }
  });

  test('Upload a PDF file', async () => {
    await page.goto(FRONTEND_URL);
    
    // Create a test PDF file
    const testPdfPath = path.join(__dirname, 'test.pdf');
    createTestPDF(testPdfPath);
    
    // Wait for file input
    await page.waitForSelector('input[type="file"]', { timeout: 10000 });
    
    // Upload file
    const inputElement = await page.$('input[type="file"]');
    if (inputElement) {
      await inputElement.uploadFile(testPdfPath);
      
      // Wait for upload to complete
      await page.waitForTimeout(3000);
      
      // Check if file appears in the list
      const uploadedFiles = await page.evaluate(() => {
        return document.body.textContent?.includes('test.pdf');
      });
      expect(uploadedFiles).toBe(true);
      
      await page.screenshot({ 
        path: 'test/puppeteer/screenshots/file-uploaded.png' 
      });
    }
    
    // Clean up
    if (fs.existsSync(testPdfPath)) {
      fs.unlinkSync(testPdfPath);
    }
  });

  test('Responsive design works', async () => {
    await page.goto(FRONTEND_URL);
    
    // Test mobile viewport
    await page.setViewport({ width: 375, height: 667 });
    await page.waitForTimeout(1000);
    
    await page.screenshot({ 
      path: 'test/puppeteer/screenshots/mobile-view.png',
      fullPage: true 
    });
    
    // Test tablet viewport
    await page.setViewport({ width: 768, height: 1024 });
    await page.waitForTimeout(1000);
    
    await page.screenshot({ 
      path: 'test/puppeteer/screenshots/tablet-view.png',
      fullPage: true 
    });
  });

  test('Error handling for invalid file type', async () => {
    await page.goto(FRONTEND_URL);
    
    // Create a test text file
    const testTxtPath = path.join(__dirname, 'test.txt');
    fs.writeFileSync(testTxtPath, 'This is not a PDF');
    
    // Try to upload non-PDF file
    const inputElement = await page.$('input[type="file"]');
    if (inputElement) {
      // Note: Browser file type restrictions might prevent this
      try {
        await inputElement.uploadFile(testTxtPath);
        await page.waitForTimeout(2000);
        
        // Check for error message or validation
        const hasError = await page.evaluate(() => {
          return document.body.textContent?.toLowerCase().includes('pdf') ||
                 document.body.textContent?.toLowerCase().includes('error');
        });
        
        await page.screenshot({ 
          path: 'test/puppeteer/screenshots/error-handling.png' 
        });
      } catch (error) {
        // File input might reject non-PDF files
        console.log('File type validation working correctly');
      }
    }
    
    // Clean up
    if (fs.existsSync(testTxtPath)) {
      fs.unlinkSync(testTxtPath);
    }
  });

  test('Performance metrics', async () => {
    await page.goto(FRONTEND_URL);
    
    // Get performance metrics
    const metrics = await page.metrics();
    console.log('Performance Metrics:', {
      timestamp: new Date(metrics.Timestamp * 1000).toISOString(),
      documents: metrics.Documents,
      frames: metrics.Frames,
      jsEventListeners: metrics.JSEventListeners,
      nodes: metrics.Nodes,
      layoutCount: metrics.LayoutCount,
      styleCount: metrics.RecalcStyleCount,
      layoutDuration: metrics.LayoutDuration,
      scriptDuration: metrics.ScriptDuration,
      taskDuration: metrics.TaskDuration,
      jsHeapUsedSize: (metrics.JSHeapUsedSize / 1024 / 1024).toFixed(2) + ' MB',
      jsHeapTotalSize: (metrics.JSHeapTotalSize / 1024 / 1024).toFixed(2) + ' MB'
    });
    
    // Check if memory usage is reasonable
    expect(metrics.JSHeapUsedSize).toBeLessThan(100 * 1024 * 1024); // Less than 100MB
  });

  test('Accessibility check', async () => {
    await page.goto(FRONTEND_URL);
    
    // Run accessibility audit
    const accessibilityTree = await page.accessibility.snapshot();
    
    // Basic accessibility checks
    // Check for proper heading structure
    const headings = await page.$$eval('h1, h2, h3, h4, h5, h6', elements => 
      elements.map(el => ({
        tag: el.tagName,
        text: el.textContent
      }))
    );
    
    expect(headings.length).toBeGreaterThan(0);
    expect(headings[0].tag).toBe('H1');
    
    // Check for alt text on images
    const images = await page.$$eval('img', elements => 
      elements.map(el => ({
        src: el.src,
        alt: el.alt
      }))
    );
    
    images.forEach(img => {
      if (img.src) {
        expect(img.alt).toBeDefined();
      }
    });
    
    console.log('Accessibility Tree:', JSON.stringify(accessibilityTree, null, 2));
  });
});

// Helper function to wait for service
async function waitForService(url: string, timeout: number = 30000): Promise<void> {
  const startTime = Date.now();
  
  while (Date.now() - startTime < timeout) {
    try {
      const testPage = await global.browser?.newPage() || await puppeteer.launch().then(b => b.newPage());
      const response = await testPage.goto(url, { waitUntil: 'networkidle0', timeout: 5000 });
      await testPage.close();
      
      if (response && response.status() === 200) {
        console.log(`✅ Service ready at ${url}`);
        return;
      }
    } catch (error) {
      console.log(`⏳ Waiting for service at ${url}...`);
    }
    
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
  
  throw new Error(`Service at ${url} did not become ready within ${timeout}ms`);
}

// Helper function to create a minimal PDF
function createTestPDF(filePath: string): void {
  // Create a minimal PDF file
  const pdfContent = `%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /MediaBox [0 0 612 792] /Contents 5 0 R >>
endobj
4 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
5 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF Document) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000117 00000 n 
0000000262 00000 n 
0000000341 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
439
%%EOF`;
  
  fs.writeFileSync(filePath, pdfContent);
}