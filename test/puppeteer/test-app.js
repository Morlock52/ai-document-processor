const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');
const { Client } = require('pg');

// Configuration
const FRONTEND_URL = 'http://localhost:13000';
const BACKEND_URL = 'http://localhost:18000';
const DB_CONFIG = {
  host: 'localhost',
  port: 15432,
  user: 'postgres',
  password: 'postgres',
  database: 'document_processor'
};

async function testDatabaseConnection() {
  console.log('📋 Test 1: Database Connectivity (PostgreSQL at port 15432)');
  
  const client = new Client(DB_CONFIG);
  
  try {
    await client.connect();
    const res = await client.query('SELECT NOW()');
    console.log('✅ Database connection successful');
    console.log('   Current time from DB:', res.rows[0].now);
    
    // Test if tables exist
    const tablesQuery = `
      SELECT table_name 
      FROM information_schema.tables 
      WHERE table_schema = 'public' 
      ORDER BY table_name;
    `;
    const tablesRes = await client.query(tablesQuery);
    console.log('   Tables found:', tablesRes.rows.map(r => r.table_name).join(', ') || 'No tables');
    
    return true;
  } catch (error) {
    console.log('❌ Database connection failed:', error.message);
    console.log('   Make sure PostgreSQL is running on port 15432');
    return false;
  } finally {
    await client.end();
  }
}

async function runPuppeteerTests() {
  console.log('🧪 Starting AI Document Processor Tests');
  console.log('=====================================');
  console.log(`Frontend URL: ${FRONTEND_URL}`);
  console.log(`Backend URL: ${BACKEND_URL}`);
  console.log(`Database: PostgreSQL at port ${DB_CONFIG.port}`);
  console.log('');

  // Test database first
  const dbConnected = await testDatabaseConnection();
  console.log('');

  let browser;
  let allTestsPassed = dbConnected;

  try {
    // Launch browser
    browser = await puppeteer.launch({
      headless: process.env.HEADLESS !== 'false',
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
      dumpio: true // Show browser console output
    });

    const page = await browser.newPage();
    
    // Enable console logging from the page
    page.on('console', msg => {
      console.log('Browser console:', msg.text());
    });
    
    // Log network failures
    page.on('requestfailed', request => {
      console.log('Network request failed:', request.url(), request.failure().errorText);
    });

    await page.setViewport({ width: 1280, height: 800 });

    // Test 2: Backend Health Check
    console.log('📋 Test 2: Backend API Health Check');
    try {
      const response = await page.goto(`${BACKEND_URL}/health`, { 
        waitUntil: 'networkidle0',
        timeout: 10000 
      });
      
      if (response && response.status() === 200) {
        const contentType = response.headers()['content-type'];
        const text = await response.text();
        
        console.log('✅ Backend health endpoint responded');
        console.log('   Status:', response.status());
        console.log('   Content-Type:', contentType);
        
        try {
          const data = JSON.parse(text);
          console.log('   Response:', JSON.stringify(data, null, 2));
        } catch {
          console.log('   Response:', text.substring(0, 200));
        }
      } else {
        throw new Error(`Backend returned status ${response?.status()}`);
      }
    } catch (error) {
      console.log('❌ Backend health check failed:', error.message);
      allTestsPassed = false;
      
      // Try to see if backend is running at all
      try {
        const curlResponse = await page.evaluate(async (url) => {
          try {
            const response = await fetch(url);
            return {
              status: response.status,
              statusText: response.statusText,
              headers: Object.fromEntries(response.headers.entries())
            };
          } catch (e) {
            return { error: e.message };
          }
        }, BACKEND_URL);
        console.log('   Direct fetch attempt:', curlResponse);
      } catch (e) {
        console.log('   Could not reach backend at all');
      }
    }

    // Test 3: API Documentation
    console.log('\n📋 Test 3: API Documentation');
    try {
      await page.goto(`${BACKEND_URL}/docs`, {
        waitUntil: 'networkidle0',
        timeout: 30000
      });
      
      // Check for FastAPI docs elements
      const hasSwagger = await page.evaluate(() => {
        return document.querySelector('.swagger-ui') !== null || 
               document.querySelector('#swagger-ui') !== null ||
               document.title.includes('FastAPI') ||
               document.body.textContent.includes('FastAPI');
      });
      
      if (hasSwagger) {
        console.log('✅ API documentation loaded');
        
        // Take screenshot
        await page.screenshot({ 
          path: path.join(__dirname, 'screenshots', 'api-docs.png'),
          fullPage: true 
        });
        console.log('📸 Screenshot saved: api-docs.png');
      } else {
        throw new Error('API documentation page not recognized');
      }
    } catch (error) {
      console.log('❌ API documentation test failed:', error.message);
      allTestsPassed = false;
    }

    // Test 4: Frontend Loading
    console.log('\n📋 Test 4: Frontend Loading');
    try {
      await page.goto(FRONTEND_URL, { 
        waitUntil: 'networkidle0',
        timeout: 30000 
      });
      
      // Wait a bit for React to render
      await page.waitForTimeout(2000);
      
      // Check page content
      const pageContent = await page.evaluate(() => {
        return {
          title: document.title,
          h1: document.querySelector('h1')?.textContent,
          body: document.body.textContent?.substring(0, 500),
          hasUploadArea: document.body.textContent?.includes('drag') || 
                        document.body.textContent?.includes('Drop') ||
                        document.body.textContent?.includes('upload')
        };
      });
      
      console.log('✅ Frontend loaded');
      console.log('   Page title:', pageContent.title);
      console.log('   H1 heading:', pageContent.h1);
      console.log('   Has upload area:', pageContent.hasUploadArea);
      
      // Take screenshot
      await page.screenshot({ 
        path: path.join(__dirname, 'screenshots', 'homepage.png'),
        fullPage: true 
      });
      console.log('📸 Screenshot saved: homepage.png');
    } catch (error) {
      console.log('❌ Frontend loading failed:', error.message);
      allTestsPassed = false;
      
      // Take error screenshot
      await page.screenshot({ 
        path: path.join(__dirname, 'screenshots', 'frontend-error.png'),
        fullPage: true 
      });
      console.log('📸 Error screenshot saved: frontend-error.png');
    }

    // Test 5: Check API URL used by Frontend
    console.log('\n📋 Test 5: Frontend API Configuration');
    try {
      await page.goto(FRONTEND_URL);
      await page.waitForTimeout(2000);
      
      // Intercept network requests to see API calls
      const apiCalls = [];
      page.on('request', request => {
        if (request.url().includes('/api') || request.url().includes(':18000') || request.url().includes(':8000')) {
          apiCalls.push({
            url: request.url(),
            method: request.method()
          });
        }
      });
      
      // Try to trigger an API call by interacting with the page
      await page.evaluate(() => {
        // Look for any buttons that might trigger API calls
        const buttons = Array.from(document.querySelectorAll('button'));
        const uploadButton = buttons.find(b => 
          b.textContent.toLowerCase().includes('upload') ||
          b.textContent.toLowerCase().includes('browse')
        );
        if (uploadButton) uploadButton.click();
      });
      
      await page.waitForTimeout(2000);
      
      if (apiCalls.length > 0) {
        console.log('✅ Detected API calls:');
        apiCalls.forEach(call => {
          console.log(`   ${call.method} ${call.url}`);
        });
      } else {
        console.log('⚠️  No API calls detected');
        console.log('   Frontend might be using a different API URL or no API calls were triggered');
      }
      
      // Check if there's any API configuration in the page
      const apiConfig = await page.evaluate(() => {
        // Check window object for API configuration
        const config = window.__NEXT_DATA__ || window.__APP_CONFIG__ || {};
        return JSON.stringify(config, null, 2);
      });
      
      if (apiConfig && apiConfig !== '{}') {
        console.log('   Frontend configuration found:', apiConfig.substring(0, 200) + '...');
      }
    } catch (error) {
      console.log('❌ Frontend API configuration test failed:', error.message);
      allTestsPassed = false;
    }

    // Test 6: Responsive Design
    console.log('\n📋 Test 6: Responsive Design');
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

    // Test 7: Error Handling
    console.log('\n📋 Test 7: Error Handling');
    try {
      // Test 404 page
      await page.goto(`${FRONTEND_URL}/non-existent-page`, {
        waitUntil: 'networkidle0'
      });
      
      const is404 = await page.evaluate(() => {
        return document.body.textContent.includes('404') || 
               document.body.textContent.includes('not found') ||
               document.body.textContent.includes('Not Found');
      });
      
      if (is404) {
        console.log('✅ 404 error page works correctly');
      } else {
        console.log('⚠️  404 page might not be configured');
      }
    } catch (error) {
      console.log('❌ Error handling test failed:', error.message);
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
  console.log('Test Summary:');
  console.log('=====================================');
  if (allTestsPassed) {
    console.log('✅ All tests passed!');
    process.exit(0);
  } else {
    console.log('❌ Some tests failed');
    console.log('\nTroubleshooting tips:');
    console.log('1. Check if PostgreSQL is running on port 15432');
    console.log('2. Check if backend is running on port 18000');
    console.log('3. Check if frontend is running on port 13000');
    console.log('4. Check docker-compose logs for any errors');
    console.log('5. Verify environment variables are set correctly');
    process.exit(1);
  }
}

// Create screenshots directory if it doesn't exist
const screenshotsDir = path.join(__dirname, 'screenshots');
if (!fs.existsSync(screenshotsDir)) {
  fs.mkdirSync(screenshotsDir, { recursive: true });
}

// Run tests
runPuppeteerTests().catch(console.error);