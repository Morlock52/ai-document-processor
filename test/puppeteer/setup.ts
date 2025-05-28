import { Browser, Page } from 'puppeteer';

declare global {
  var browser: Browser;
  var page: Page;
}

// Increase timeout for all tests
jest.setTimeout(60000);

// Global setup
beforeAll(async () => {
  console.log('Starting Puppeteer tests...');
});

// Global teardown
afterAll(async () => {
  if (global.browser) {
    await global.browser.close();
  }
});