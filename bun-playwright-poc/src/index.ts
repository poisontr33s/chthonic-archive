#!/usr/bin/env bun

// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: index.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: ORANGE
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ║ Ogdoad-Ceque Radiance:
// ║   └─◄ bun-playwright-poc/src/bun-cdp.ts
// ║   └─◄ bun-playwright-poc/src/bun-cdp-element.ts
// ║   └─◄ bun-playwright-poc/src/bun-cdp-frame.ts
// ║   └─◄ bun-playwright-poc/src/bun-cdp-page.ts
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * BunCDP - Bun-native Chrome automation library
 *
 * @SID           LIB_BUN_CDP_INDEX_V1
 * @Shabti        Library Module
 * @Purpose       Public barrel export for the BunCDP library. Bypasses
 *                Playwright's incompatible CDP layer by using raw WebSocket.
 *                Provides Playwright-like API: page.goto(), page.click(),
 *                page.fill(), etc.
 */

// Core
export { BunCDP, launchBrowser, type BunCDPOptions, type BrowserVersion, type TargetInfo } from './bun-cdp';
export { CDPPage, createPage, type PageOptions, type ElementHandle, type FrameInfo } from './bun-cdp-page';

// Frame support
export { FrameRegistry, CDPFrame } from './bun-cdp-frame';

// Crawler
export { 
  ChthonicCrawler, 
  createKeywordHeuristic, 
  createGitHubHeuristic,
  type CrawlConfig, 
  type CrawlNode, 
  type KnowledgeGraph 
} from './bun-cdp-crawler';

// Element utilities (for advanced usage)
export {
  querySelector,
  querySelectorAll,
  clickElement,
  typeIntoElement,
  clearElement,
  getTextContent,
  getInnerHTML,
  getAttribute,
  isVisible,
  waitForSelector,
  getBoundingBox,
  getElementCenter,
} from './bun-cdp-element';
