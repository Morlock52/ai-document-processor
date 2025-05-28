const puppeteer = require('puppeteer');

// Configuration - read from environment or use defaults
const FRONTEND_URL = process.env.FRONTEND_URL || 'http://localhost:3003';
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8001';

async function runTests() {
  console.log('🧪 Starting AI Document Processor Tests');
  console.log('=====================================');
  console.log(`Frontend URL: ${FRONTEND_URL}`);
  console.log(`Backend URL: ${BACKEND_URL}`);
  console.log('');

  let browser;
  let allTestsPassed = true;

  try {
    // Launch browser
    browser = await puppeteer.launch({
      headless: process.env.HEADLESS !== 'false',
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 800 });

    // Test 1: Backend Health Check
    console.log('📋 Test 1: Backend Health Check');
    try {
      const response = await page.goto(`${BACKEND_URL}/health`, { 
        waitUntil: 'networkidle0',
        timeout: 10000 
      });
      
      if (response && response.status() === 200) {
        const data = await response.json();
        console.log('✅ Backend is healthy:', data);
      } else {
        throw new Error(`Backend returned status ${response?.status()}`);
      }
    } catch (error) {
      console.log('❌ Backend health check failed:', error.message);
      allTestsPassed = false;
    }

    // Test 2: Frontend Loading
    console.log('\n📋 Test 2: Frontend Loading');
    try {
      await page.goto(FRONTEND_URL, { 
        waitUntil: 'networkidle0',
        timeout: 30000 
      });
      
      // Check for main heading
      const title = await page.$eval('h1', el => el.textContent).catch(() => null);
      if (title && title.includes('Document Processor')) {
        console.log('✅ Frontend loaded successfully');
        console.log('   Title:', title);
      } else {
        throw new Error('Main heading not found');
      }
      
      // Take screenshot
      await page.screenshot({ 
        path: path.join(__dirname, 'screenshots', 'homepage.png'),
        fullPage: true 
      });
      console.log('📸 Screenshot saved: homepage.png');
    } catch (error) {
      console.log('❌ Frontend loading failed:', error.message);
      allTestsPassed = false;
    }

    // Test 3: Upload Interface
    console.log('\n📋 Test 3: Upload Interface');
    try {
      const uploadAreaExists = await page.evaluate(() => {
        const text = document.body.textContent || '';
        return text.includes('Drag & drop') || text.includes('drop PDF');
      });
      
      if (uploadAreaExists) {
        console.log('✅ Upload interface is present');
      } else {
        throw new Error('Upload interface not found');
      }
    } catch (error) {
      console.log('❌ Upload interface test failed:', error.message);
      allTestsPassed = false;
    }

    // Test 4: API Documentation
    console.log('\n📋 Test 4: API Documentation');
    try {
      await page.goto(`${BACKEND_URL}/docs`, {
        waitUntil: 'networkidle0',
        timeout: 30000
      });
      
      await page.waitForSelector('.swagger-ui', { timeout: 10000 });
      console.log('✅ API documentation loaded');
      
      await page.screenshot({ 
        path: path.join(__dirname, 'screenshots', 'api-docs.png'),
        fullPage: true 
      });
      console.log('📸 Screenshot saved: api-docs.png');
    } catch (error) {
      console.log('❌ API documentation test failed:', error.message);
      allTestsPassed = false;
    }

    // Test 5: Responsive Design
    console.log('\n📋 Test 5: Responsive Design');
    try {
      await page.goto(FRONTEND_URL);
      
      // Mobile view
      await page.setViewport({ width: 375, height: 667 });
      await page.waitForTimeout(1000);
      await page.screenshot({ 
        path: path.join(__dirname, 'screenshots', 'mobile-view.png')
      });
      console.log('✅ Mobile view tested');
      
      // Tablet view
      await page.setViewport({ width: 768, height: 1024 });
      await page.waitForTimeout(1000);
      await page.screenshot({ 
        path: path.join(__dirname, 'screenshots', 'tablet-view.png')
      });
      console.log('✅ Tablet view tested');
    } catch (error) {
      console.log('❌ Responsive design test failed:', error.message);
      allTestsPassed = false;
    }

    // Test 6: Performance Metrics
    console.log('\n📋 Test 6: Performance Metrics');
    try {
      await page.goto(FRONTEND_URL);
      const metrics = await page.metrics();
      
      console.log('✅ Performance metrics collected:');
      console.log(`   JS Heap: ${(metrics.JSHeapUsedSize / 1024 / 1024).toFixed(2)} MB`);
      console.log(`   Documents: ${metrics.Documents}`);
      console.log(`   Nodes: ${metrics.Nodes}`);
      console.log(`   Event Listeners: ${metrics.JSEventListeners}`);
    } catch (error) {
      console.log('❌ Performance metrics test failed:', error.message);
      allTestsPassed = false;
    }

  } catch (error) {
    console.error('\n❌ Test suite error:', error);
    allTestsPassed = false;
  } finally {
    if (browser) {
      await browser.close();
    }
  }

  // Summary
  console.log('\n=====================================');
  if (allTestsPassed) {
    console.log('✅ All tests passed!');
    process.exit(0);
  } else {
    console.log('❌ Some tests failed');
    process.exit(1);
  }
}

// Create screenshots directory if it doesn't exist
const fs = require('fs');
const path = require('path');
const screenshotsDir = path.join(__dirname, 'screenshots');
if (!fs.existsSync(screenshotsDir)) {
  fs.mkdirSync(screenshotsDir, { recursive: true });
}

// Run tests
runTests().catch(console.error);