# BunCDP - Working Bun + Chrome Automation

**Created:** 2026-01-23  
**Status:** ✅ FULLY WORKING  
**Verified:** Navigation waits for load, title/URL/evaluate all return correct values

## Summary

This session proved that **Playwright's CDP layer is incompatible with Bun**, but **raw CDP over WebSocket works perfectly**. We created a lightweight wrapper library that provides Playwright-like automation using direct CDP communication.

## What Works ✅

| Feature | Status | Notes |
|---------|--------|-------|
| Chrome spawn via `Bun.spawn()` | ✅ | Both headless and headed modes |
| WebSocket connection | ✅ | Must use `/devtools/page/{id}` not `/devtools/browser` |
| `Browser.getVersion` | ✅ | Returns Chrome/144.0.7559.20 |
| `Target.createTarget` | ✅ | Creates blank pages |
| `page.goto()` | ✅ | **Waits for Page.loadEventFired** |
| `page.title()` | ✅ | Returns "Example Domain" |
| `page.url()` | ✅ | Returns "https://example.com/" |
| `page.evaluate()` | ✅ | Returns H1 text correctly |
| `page.screenshot()` | ✅ | PNG/JPEG screenshots |
| Port discovery via HTTP | ✅ | Polling `/json/version` endpoint |

## What Doesn't Work ❌

| Feature | Issue | Root Cause |
|---------|-------|------------|
| Playwright `launch()` | Process crash | Bun incompatibility with pipe protocol |
| Playwright `connectOverCDP()` | Process crash | Same Bun issue |
| Dynamic port via stderr | Unreliable | Bun stdout/stderr buffering |
| `/devtools/browser` WebSocket | 101 error | Use `/devtools/page/{id}` instead |

## Library Structure

```
lib/
├── bun-cdp.ts        # Core CDP wrapper (BunCDP class)
├── bun-cdp-page.ts   # Page abstraction (CDPPage class)
└── index.ts          # Exports
```

## Usage Example

```typescript
import { launchBrowser, createPage } from './lib';

const browser = await launchBrowser({ headless: true });
const page = await createPage(browser, 'https://example.com');

const title = await page.title();
const heading = await page.evaluate(`document.querySelector('h1')?.textContent`);
const screenshot = await page.screenshot({ format: 'png' });

await browser.close();
```

## Key Technical Details

### Port Discovery
Instead of parsing stderr (unreliable with Bun), use a fixed port and poll the HTTP endpoint:

```typescript
const PORT = 19555;
// Spawn with --remote-debugging-port=${PORT}
// Poll http://127.0.0.1:${PORT}/json/version until ready
```

### WebSocket Connection
For page commands, connect to the page-specific WebSocket:

```typescript
// Get page WS URL
const targets = await fetch(`http://127.0.0.1:${port}/json`);
const target = targets.find(t => t.id === targetId);
const pageWs = new WebSocket(target.webSocketDebuggerUrl);
```

### CDP Command Pattern
```typescript
const send = (method: string, params?: any): Promise<any> => {
  const id = ++msgId;
  return new Promise((resolve, reject) => {
    pending.set(id, { resolve, reject });
    ws.send(JSON.stringify({ id, method, params }));
  });
};

// Usage
await send('Page.enable');
await send('Page.navigate', { url: 'https://example.com' });
const result = await send('Runtime.evaluate', { expression: 'document.title' });
```

## File Manifest

| File | Purpose | Status |
|------|---------|--------|
| `lib/bun-cdp.ts` | Core CDP wrapper | ✅ Production |
| `lib/bun-cdp-page.ts` | Page API | ✅ Production |
| `lib/index.ts` | Module exports | ✅ Production |
| `example-buncdp.ts` | Usage example | ✅ Working |
| `example-screenshot.png` | Proof of success | ✅ 8.4KB |

## Environment

- **Bun:** 1.3.6
- **Chrome:** Playwright's Chromium-1207 (Chrome/144.0.7559.20)
- **OS:** Windows 11 (enterprise-managed)
- **Path:** `%LOCALAPPDATA%\ms-playwright\chromium-1207\chrome-win64\chrome.exe`

## Conclusion

The Playwright MCP server failures were caused by **protocol-level incompatibility between Playwright's CDP implementation and Bun's WebSocket/subprocess handling**, NOT by enterprise security restrictions. The solution is to bypass Playwright entirely and use raw CDP via WebSocket, which works perfectly.
