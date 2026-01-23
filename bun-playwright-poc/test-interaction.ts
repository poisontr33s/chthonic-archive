#!/usr/bin/env bun
/**
 * BunCDP Interaction Test - Validates click, type, fill operations
 */

import { launchBrowser, createPage } from './src';

async function main() {
  console.log('🎯 BunCDP Interaction Test');
  console.log('═'.repeat(50));
  
  const browser = await launchBrowser({ headless: true });
  console.log(`✅ Browser: ${browser.browserVersion?.product}`);
  
  const page = await createPage(browser, 'about:blank');
  
  // Test 1: Navigate and click a link
  console.log('\n[1] Navigate to example.com...');
  await page.goto('https://example.com');
  const title = await page.title();
  console.log(`    ✅ Title: "${title}"`);
  
  // Test 2: Query elements
  console.log('\n[2] Query elements...');
  const h1 = await page.$('h1');
  console.log(`    ✅ Found h1: ${h1 ? 'yes' : 'no'}`);
  
  const paragraphs = await page.$$('p');
  console.log(`    ✅ Found ${paragraphs.length} paragraphs`);
  
  // Test 3: Get text content
  console.log('\n[3] Get text content...');
  const h1Text = await page.textContent('h1');
  console.log(`    ✅ H1 text: "${h1Text}"`);
  
  // Test 4: Check visibility
  console.log('\n[4] Check visibility...');
  const isH1Visible = await page.isVisible('h1');
  console.log(`    ✅ H1 visible: ${isH1Visible}`);
  
  // Test 5: Get attribute
  console.log('\n[5] Get attribute...');
  const linkHref = await page.getAttribute('a', 'href');
  console.log(`    ✅ Link href: "${linkHref}"`);
  
  // Test 6: Click the "More information" link
  console.log('\n[6] Click link...');
  try {
    await page.click('a');
    // Wait a moment for navigation
    await new Promise(r => setTimeout(r, 2000));
    const newUrl = await page.url();
    console.log(`    ✅ Navigated to: ${newUrl}`);
  } catch (err: any) {
    console.log(`    ⚠️ Click error: ${err.message}`);
  }
  
  // Test 7: Navigate to a form page and test typing
  console.log('\n[7] Test form input (DuckDuckGo)...');
  await page.goto('https://duckduckgo.com');
  await page.waitForSelector('input[name="q"]', { timeout: 10000 });
  
  console.log('    - Typing search query...');
  await page.fill('input[name="q"]', 'BunCDP test query');
  
  // Verify the value was typed
  const inputValue = await page.evaluate(`document.querySelector('input[name="q"]').value`);
  console.log(`    ✅ Input value: "${inputValue}"`);
  
  // Screenshot
  console.log('\n[8] Taking screenshot...');
  const screenshot = await page.screenshot({ format: 'png' });
  await Bun.write('interaction-test.png', screenshot);
  console.log(`    ✅ Saved: interaction-test.png (${screenshot.length} bytes)`);
  
  // Cleanup
  await browser.close();
  
  console.log('\n' + '═'.repeat(50));
  console.log('✅ Interaction test complete!');
}

await main().catch(err => {
  console.error('❌ Fatal:', err.message);
  process.exit(1);
});
