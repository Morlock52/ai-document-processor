const puppeteer = require('puppeteer-core');
const path = require('path');

const CHROMIUM_PATH = '/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome';
const OUTPUT_DIR = path.join(__dirname, '..', 'docs', 'images');
const BASE_URL = 'http://localhost:3000';

async function takeExcelScreenshot() {
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

  await page.setViewport({
    width: 1440,
    height: 900,
    deviceScaleFactor: 2,
  });

  try {
    console.log('Taking excel/template screenshot...');
    await page.goto(BASE_URL, { waitUntil: 'networkidle0', timeout: 30000 });
    await new Promise(r => setTimeout(r, 1000));

    // Find and click the template mode toggle button using evaluate
    await page.evaluate(() => {
      // Find all buttons and look for the one with ToggleLeft or "Disabled" text
      const buttons = document.querySelectorAll('button');
      for (const btn of buttons) {
        const text = btn.textContent || '';
        if (text.includes('Disabled') || text.includes('Template')) {
          btn.click();
          return;
        }
      }
    });

    await new Promise(r => setTimeout(r, 1000));

    // Scroll to show the template mode card
    await page.evaluate(() => {
      const templateCard = document.querySelector('[class*="from-emerald"]');
      if (templateCard) {
        templateCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    });

    await new Promise(r => setTimeout(r, 500));

    await page.screenshot({
      path: path.join(OUTPUT_DIR, 'excel.png'),
      fullPage: false,
    });
    console.log('✓ excel.png saved');

  } catch (error) {
    console.error('Error:', error);
  } finally {
    await browser.close();
  }
}

takeExcelScreenshot().catch(console.error);
