# bun-cdp

Lightweight Chrome DevTools Protocol driver for Bun. Bypasses Playwright's IPC layer that crashes on Bun.

## Why?

Playwright's CDP layer (`pw:protocol`) uses Node.js-specific IPC that crashes Bun's process without exception. This library uses **raw CDP over WebSocket**, which works flawlessly with Bun's native WebSocket and subprocess APIs.

## Features

- **Core Automation**: Navigate, click, type, fill, screenshot
- **SPA Support**: `NetworkIdle` wait for XHR/fetch completion  
- **Iframe Support**: Cross-frame element interaction via `FrameRegistry`
- **Safety Systems**: Auto-dismiss dialogs, detect popups/new tabs
- **Zero Dependencies**: Pure Bun - no Node.js polyfills needed

## Installation

```bash
# Uses Playwright's bundled Chromium
bunx playwright install chromium

# Then import directly
import { launchBrowser, createPage } from './src';
```

## Quick Start

```typescript
import { launchBrowser, createPage } from 'bun-cdp';

const browser = await launchBrowser({ headless: true });
const page = await createPage(browser, 'about:blank');

await page.goto('https://example.com');
console.log(await page.title()); // "Example Domain"

await page.click('a');
await page.fill('input[name="q"]', 'hello');
await page.screenshot({ format: 'png' });

await browser.close();
```

## API

### Browser

```typescript
const browser = await launchBrowser({
  headless: true,           // default: true
  chromePath: '/path/to/chrome',
  port: 9222,              // debug port
});

// Popup handling
browser.onPopup((target) => console.log('New tab:', target.url));
const popup = await browser.waitForPopup();

await browser.close();
```

### Page

```typescript
const page = await createPage(browser, 'about:blank');

// Navigation
await page.goto('https://example.com');
await page.goto('https://spa-app.com', { waitUntil: 'networkidle' });

// Elements
await page.click('button');
await page.fill('input', 'text');
await page.type('input', 'char-by-char');
const text = await page.textContent('h1');
const el = await page.$('selector');
const els = await page.$$('selector');
await page.waitForSelector('.lazy-loaded');

// Evaluation
const result = await page.evaluate('document.title');

// Screenshot
const png = await page.screenshot({ format: 'png' });

// Dialog handling
page.setDialogHandler((dialog) => {
  if (dialog.type === 'confirm') return { accept: true };
});
```

### Frames

```typescript
// List all frames
const frames = await page.frames();

// Get frame by name
const stripe = await page.frame('stripe-iframe');
await stripe.fill('input[name="cardnumber"]', '4242...');

// Get frame by URL
const oauth = await page.frameByUrl('accounts.google.com');
await oauth.click('button[type="submit"]');

// Wait for iframe to load
const popup = await page.waitForFrame('oauth-frame');
```

## Comparison with Playwright

| Feature | Playwright on Bun | bun-cdp |
|---------|-------------------|---------|
| Basic navigation | ❌ Crashes | ✅ Works |
| Element interaction | ❌ Crashes | ✅ Works |
| Screenshots | ❌ Crashes | ✅ Works |
| NetworkIdle | ❌ Crashes | ✅ Works |
| Iframes | ❌ Crashes | ✅ Works |
| Dialogs | ❌ Crashes | ✅ Auto-dismiss |
| Popups | ❌ Crashes | ✅ Target tracking |

## Architecture

```
src/
├── bun-cdp.ts         # Browser spawn + WebSocket (PopupHandler)
├── bun-cdp-page.ts    # Page API + NetworkIdle + DialogHandler
├── bun-cdp-element.ts # Stateless element interaction
├── bun-cdp-frame.ts   # FrameRegistry + CDPFrame
└── index.ts           # Exports
```

## Run Tests

```bash
bun run test        # Integration test
bun run test:safety # Dialog/popup test
bun run test:all    # All tests
```

## Limitations

- **Chromium only** - No Firefox/WebKit (CDP is Chrome's protocol)
- **No test runner** - This is a driver, not a test framework
- **No trace viewer** - Use Chrome DevTools for debugging

## Environment

- **Bun:** 1.3.6+
- **Chrome:** Playwright's Chromium-1207 (Chrome/144.0.7559.20)
- **OS:** Windows 11 (tested), Linux/macOS (should work)

## License

MIT
