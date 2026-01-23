#!/usr/bin/env bun
/**
 * BunCDP Usage Example - Demonstrates working Bun + Chrome automation
 */

import { launchBrowser, createPage } from './lib';

async function main() {
  console.log('🚀 BunCDP Example');
  console.log('═'.repeat(50));
  
  // Launch browser
  console.log('\n[1] Launching browser...');
  const browser = await launchBrowser({
    headless: true,  // Set to false to see the browser
  });
  
  console.log(`    ✅ Browser: ${browser.browserVersion?.product}`);
  console.log(`    Port: ${browser.port}`);
  
  // Create a page
  console.log('\n[2] Creating page...');
  const targetId = await browser.createTarget('about:blank');
  console.log(`    ✅ Target: ${targetId}`);
  
  // List all targets
  console.log('\n[3] Listing targets...');
  const targets = await browser.getTargets();
  for (const t of targets) {
    console.log(`    - ${t.type}: ${t.url}`);
  }
  
  // Create and navigate a page using high-level API
  console.log('\n[4] Navigating to example.com...');
  const page = await createPage(browser, 'about:blank');
  await page.goto('https://example.com');  // Now properly waits for load!
  
  // Get page info - should now have correct values
  const title = await page.title();
  const url = await page.url();
  console.log(`    ✅ Title: "${title}"`);
  console.log(`    URL: ${url}`);
  
  // Evaluate JavaScript
  console.log('\n[5] Evaluating JavaScript...');
  const heading = await page.evaluate(`document.querySelector('h1')?.textContent`);
  console.log(`    ✅ H1 text: "${heading}"`);
  
  // Screenshot (optional)
  console.log('\n[6] Taking screenshot...');
  const screenshot = await page.screenshot({ format: 'png' });
  await Bun.write('example-screenshot.png', screenshot);
  console.log(`    ✅ Saved: example-screenshot.png (${screenshot.length} bytes)`);
  
  // Cleanup
  console.log('\n[7] Closing browser...');
  await browser.close();
  console.log('    ✅ Done!');
  
  console.log('\n' + '═'.repeat(50));
  console.log('✅ BunCDP automation complete!');
}

await main().catch(console.error);
