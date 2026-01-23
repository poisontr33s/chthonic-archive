/**
 * BunCDP - Bun-native Chrome automation library
 * 
 * Bypasses Playwright's incompatible CDP layer by using raw WebSocket.
 * Provides Playwright-like API: page.goto(), page.click(), page.fill(), etc.
 */

// Core
export { BunCDP, launchBrowser, type BunCDPOptions, type BrowserVersion, type TargetInfo } from './bun-cdp';
export { CDPPage, createPage, type PageOptions, type ElementHandle, type FrameInfo } from './bun-cdp-page';

// Frame support
export { FrameRegistry, CDPFrame } from './bun-cdp-frame';

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
