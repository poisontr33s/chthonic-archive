# Bun-Playwright PoC

Proof-of-concept demonstrating browser automation with Bun runtime.

## ⚠️ Important Finding (2026-01-23)

**Playwright's CDP layer is incompatible with Bun.** The `playwright.chromium.launch()` and `connectOverCDP()` methods cause Bun process crashes without throwing exceptions.

**Solution:** Use the **BunCDP** library in `lib/` which uses raw CDP over WebSocket - this works perfectly.

See [BUNCDP_SUCCESS.md](./BUNCDP_SUCCESS.md) for full technical details.

## BunCDP - The Working Solution

```typescript
import { launchBrowser, createPage } from './lib';

const browser = await launchBrowser({ headless: true });
const page = await createPage(browser, 'https://example.com');

const title = await page.title();
const heading = await page.evaluate(`document.querySelector('h1')?.textContent`);
const screenshot = await page.screenshot({ format: 'png' });

await browser.close();
```

### Run the Example

```bash
bun run example-buncdp.ts
```

**Output:** `example-screenshot.png` with a screenshot of example.com

## Quick Start

```bash
# Install dependencies
bun install

# Install browsers (first time only)
bun run install:browsers

# Run BunCDP example (RECOMMENDED)
bun run example-buncdp.ts

# Run Playwright tests (may crash with Bun)
bun run test
```

## Library Structure

```
lib/
├── bun-cdp.ts        # Core CDP wrapper (BunCDP class)
├── bun-cdp-page.ts   # Page abstraction (CDPPage class)
└── index.ts          # Exports
```

## Key Findings

### ✅ Works (BunCDP)
- Chrome spawn via `Bun.spawn()` 
- Raw CDP over WebSocket
- `Page.navigate`, `Runtime.evaluate`
- Screenshots (`Page.captureScreenshot`)
- Both headless and headed modes

### ❌ Does NOT Work
- `playwright.chromium.launch()` - Crashes Bun
- `playwright.connectOverCDP()` - Crashes Bun
- Dynamic port via stderr parsing - Unreliable buffering

## Environment

- **Bun:** 1.3.6
- **Chrome:** Playwright's Chromium-1207 (Chrome/144.0.7559.20)
- **OS:** Windows 11

## Related Documentation

- [BUNCDP_SUCCESS.md](./BUNCDP_SUCCESS.md) - Technical success report
- [BUN_PLAYWRIGHT_VALIDATION.md](../BUN_PLAYWRIGHT_VALIDATION.md) - Original validation study
