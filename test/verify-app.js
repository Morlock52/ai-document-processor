const puppeteer = require('puppeteer');

async function verifyApp() {
  console.log('🧪 Verifying AI Document Processor');
  console.log('=====================================');
  
  const browser = await puppeteer.launch({ 
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  try {
    const page = await browser.newPage();
    
    // Test 1: Check backend health
    console.log('\n📋 Test 1: Backend Health Check');
    await page.goto('http://localhost:18000/health');
    const healthResponse = await page.evaluate(() => document.body.textContent);
    const health = JSON.parse(healthResponse);
    console.log('✅ Backend is healthy:', health);
    
    // Test 2: Check API docs
    console.log('\n📋 Test 2: API Documentation');
    await page.goto('http://localhost:18000/docs');
    await page.waitForSelector('h2.title', { timeout: 5000 });
    console.log('✅ API documentation is accessible');
    
    // Test 3: Frontend loading
    console.log('\n📋 Test 3: Frontend Application');
    await page.goto('http://localhost:13000');
    await page.waitForSelector('h1', { timeout: 5000 });
    const title = await page.$eval('h1', el => el.textContent);
    console.log('✅ Frontend loaded with title:', title);
    
    // Test 4: Check API connectivity
    console.log('\n📋 Test 4: API Connectivity');
    
    // Set up request interception
    const apiRequests = [];
    page.on('request', request => {
      if (request.url().includes('/api/')) {
        apiRequests.push({
          url: request.url(),
          method: request.method()
        });
      }
    });
    
    page.on('response', response => {
      if (response.url().includes('/api/')) {
        console.log(`   API Response: ${response.url()} - Status: ${response.status()}`);
      }
    });
    
    // Reload page to capture API calls
    await page.reload({ waitUntil: 'networkidle0' });
    
    // Wait a bit for any API calls
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    if (apiRequests.length > 0) {
      console.log('✅ API requests detected:');
      apiRequests.forEach(req => {
        console.log(`   ${req.method} ${req.url}`);
      });
    } else {
      console.log('⚠️  No API requests detected on page load');
    }
    
    // Test 5: Check database connectivity
    console.log('\n📋 Test 5: Database Check');
    const apiResponse = await page.goto('http://localhost:18000/api/v1/documents/?limit=1');
    const apiData = await apiResponse.json();
    console.log('✅ Database query successful:', apiData);
    
    console.log('\n✅ All tests passed! The application is working correctly.');
    console.log('\n📌 Access URLs:');
    console.log('   Frontend: http://localhost:13000');
    console.log('   Backend API: http://localhost:18000');
    console.log('   API Docs: http://localhost:18000/docs');
    
  } catch (error) {
    console.error('\n❌ Test failed:', error.message);
    
    // Take screenshot on error
    const page = await browser.newPage();
    await page.goto('http://localhost:13000');
    await page.screenshot({ path: 'error-screenshot.png' });
    console.log('📸 Error screenshot saved as error-screenshot.png');
  } finally {
    await browser.close();
  }
}

verifyApp().catch(console.error);
