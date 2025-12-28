const puppeteer = require('puppeteer-core');
const path = require('path');
const fs = require('fs');

const CHROMIUM_PATH = '/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome';
const OUTPUT_DIR = path.join(__dirname, '..', 'docs', 'images');
const BASE_URL = 'http://localhost:3000';

async function takeScreenshots() {
  // Ensure output directory exists
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  console.log('Launching browser...');
  const browser = await puppeteer.launch({
    executablePath: CHROMIUM_PATH,
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-gpu',
    ],
  });

  const page = await browser.newPage();

  // Set viewport to recommended size
  await page.setViewport({
    width: 1440,
    height: 900,
    deviceScaleFactor: 2, // Retina quality
  });

  try {
    // 1. Hero Screenshot - Main interface
    console.log('Taking hero screenshot...');
    await page.goto(BASE_URL, { waitUntil: 'networkidle0', timeout: 30000 });
    await page.waitForSelector('.space-y-12', { timeout: 10000 });
    await new Promise(r => setTimeout(r, 1000)); // Wait for animations
    await page.screenshot({
      path: path.join(OUTPUT_DIR, 'hero-screenshot.png'),
      fullPage: false,
    });
    console.log('✓ hero-screenshot.png saved');

    // 2. Upload Screenshot - Focus on upload area
    console.log('Taking upload screenshot...');
    // Click on the Upload tab if not already active
    const uploadTab = await page.$('button[data-state="active"][value="upload"], button[value="upload"]');
    if (uploadTab) {
      await uploadTab.click();
      await new Promise(r => setTimeout(r, 500));
    }

    // Scroll to upload section and take a focused screenshot
    const uploadCard = await page.$('.rounded-3xl.bg-white\\/80');
    if (uploadCard) {
      await uploadCard.screenshot({
        path: path.join(OUTPUT_DIR, 'upload.png'),
      });
    } else {
      // Fallback to full page with scroll
      await page.screenshot({
        path: path.join(OUTPUT_DIR, 'upload.png'),
        fullPage: false,
      });
    }
    console.log('✓ upload.png saved');

    // 3. Processing Screenshot - Show the "How It Works" section
    console.log('Taking processing screenshot...');
    // Scroll to the "How It Works" section
    await page.evaluate(() => {
      const howItWorks = document.querySelector('h2.text-2xl');
      if (howItWorks) {
        howItWorks.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    });
    await new Promise(r => setTimeout(r, 500));
    await page.screenshot({
      path: path.join(OUTPUT_DIR, 'processing.png'),
      fullPage: false,
    });
    console.log('✓ processing.png saved');

    // 4. Results Screenshot - Show the Documents tab
    console.log('Taking results screenshot...');
    // Click on Documents tab
    const docsTab = await page.$('button[value="documents"]');
    if (docsTab) {
      await docsTab.click();
      await new Promise(r => setTimeout(r, 1000));
    }
    await page.screenshot({
      path: path.join(OUTPUT_DIR, 'results.png'),
      fullPage: false,
    });
    console.log('✓ results.png saved');

    // 5. Excel Screenshot - Show template mode enabled
    console.log('Taking excel/template screenshot...');
    // Go back to upload and enable template mode
    await page.goto(BASE_URL, { waitUntil: 'networkidle0' });
    await new Promise(r => setTimeout(r, 500));

    // Click the template mode toggle
    const templateToggle = await page.$('button:has(span:contains("Disabled")), button:has(.lucide-toggle-left)');
    if (templateToggle) {
      await templateToggle.click();
      await new Promise(r => setTimeout(r, 500));
    }

    // Take screenshot showing template mode
    await page.screenshot({
      path: path.join(OUTPUT_DIR, 'excel.png'),
      fullPage: false,
    });
    console.log('✓ excel.png saved');

    console.log('\nAll screenshots saved to:', OUTPUT_DIR);

  } catch (error) {
    console.error('Error taking screenshots:', error);
  } finally {
    await browser.close();
  }
}

takeScreenshots().catch(console.error);
