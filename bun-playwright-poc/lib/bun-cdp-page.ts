/**
 * BunCDP Page - High-level page automation API
 * Built on top of raw CDP, providing familiar Playwright-like methods
 * 
 * @module bun-cdp/page
 */

import { BunCDP } from './bun-cdp';
import {
  querySelector,
  querySelectorAll,
  clickElement,
  typeIntoElement,
  clearElement,
  getTextContent,
  getAttribute,
  isVisible,
  waitForSelector,
  type ElementHandle,
} from './bun-cdp-element';

export interface PageOptions {
  timeout?: number;
}

export type { ElementHandle };

export class CDPPage {
  private pageWs: WebSocket | null = null;
  private pageMessageId = 0;
  private pagePendingMessages = new Map<number, {
    resolve: (value: any) => void;
    reject: (error: Error) => void;
  }>();
  private eventListeners = new Map<string, Set<(params: any) => void>>();
  
  constructor(
    private browser: BunCDP,
    public readonly targetId: string,
    private options: PageOptions = {}
  ) {}

  /**
   * Attach to the page target to enable page commands
   */
  async attach(): Promise<void> {
    // Get the page's WebSocket URL
    const resp = await fetch(`http://127.0.0.1:${this.browser.port}/json`);
    const targets = await resp.json() as Array<{ id: string; webSocketDebuggerUrl: string }>;
    const target = targets.find(t => t.id === this.targetId);
    
    if (!target?.webSocketDebuggerUrl) {
      throw new Error(`Target ${this.targetId} not found or has no WebSocket URL`);
    }

    // Connect to page WebSocket
    await this.connectPageWebSocket(target.webSocketDebuggerUrl);
    
    // Enable necessary domains
    await this.sendToTarget('Page.enable');
    await this.sendToTarget('Runtime.enable');
  }

  private async connectPageWebSocket(url: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => reject(new Error('Page WS timeout')), 10000);
      
      this.pageWs = new WebSocket(url);
      
      this.pageWs.onopen = () => {
        clearTimeout(timeout);
        resolve();
      };
      
      this.pageWs.onerror = (e) => {
        clearTimeout(timeout);
        reject(e);
      };
      
      this.pageWs.onmessage = (event) => {
        const data = JSON.parse(event.data as string);
        
        // Handle CDP events (no id field)
        if (data.method) {
          const listeners = this.eventListeners.get(data.method);
          if (listeners) {
            for (const listener of listeners) {
              listener(data.params);
            }
          }
          return;
        }
        
        // Handle command responses (has id field)
        if (data.id !== undefined) {
          const pending = this.pagePendingMessages.get(data.id);
          if (pending) {
            this.pagePendingMessages.delete(data.id);
            if (data.error) {
              pending.reject(new Error(`CDP Error: ${data.error.message}`));
            } else {
              pending.resolve(data.result);
            }
          }
        }
      };
    });
  }

  /**
   * Send command to this specific target (exposed for element module)
   */
  async sendToTarget<T = any>(method: string, params?: any): Promise<T> {
    if (!this.pageWs || this.pageWs.readyState !== WebSocket.OPEN) {
      throw new Error('Page not attached. Call attach() first.');
    }

    const id = ++this.pageMessageId;
    
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        this.pagePendingMessages.delete(id);
        reject(new Error(`Page CDP timeout: ${method}`));
      }, 30000);

      this.pagePendingMessages.set(id, {
        resolve: (result) => {
          clearTimeout(timeout);
          resolve(result);
        },
        reject: (error) => {
          clearTimeout(timeout);
          reject(error);
        },
      });

      this.pageWs!.send(JSON.stringify({ id, method, params }));
    });
  }

  /**
   * Subscribe to a CDP event on this page
   */
  on(event: string, handler: (params: any) => void): void {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, new Set());
    }
    this.eventListeners.get(event)!.add(handler);
  }

  /**
   * Unsubscribe from a CDP event
   */
  off(event: string, handler: (params: any) => void): void {
    this.eventListeners.get(event)?.delete(handler);
  }

  /**
   * Wait for a specific CDP event
   */
  private waitForEvent(event: string, predicate?: (params: any) => boolean, timeout = 30000): Promise<any> {
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.off(event, handler);
        reject(new Error(`Timeout waiting for ${event}`));
      }, timeout);

      const handler = (params: any) => {
        if (!predicate || predicate(params)) {
          clearTimeout(timer);
          this.off(event, handler);
          resolve(params);
        }
      };

      this.on(event, handler);
    });
  }

  /**
   * Navigate to a URL and wait for load
   */
  async goto(url: string, options?: { timeout?: number; waitUntil?: 'load' | 'domcontentloaded' }): Promise<void> {
    const timeout = options?.timeout || this.options.timeout || 30000;
    const waitUntil = options?.waitUntil || 'load';
    
    // Enable Page.lifecycleEvent if not already
    await this.sendToTarget('Page.setLifecycleEventsEnabled', { enabled: true });
    
    // Set up the wait BEFORE navigating to avoid race condition
    const loadPromise = this.waitForEvent(
      'Page.loadEventFired',
      undefined,
      timeout
    );
    
    // Navigate
    await this.sendToTarget('Page.navigate', { url });
    
    // Wait for load event
    await loadPromise;
  }

  /**
   * Get the page title
   */
  async title(): Promise<string> {
    const result = await this.sendToTarget<{ result: { value: string } }>(
      'Runtime.evaluate',
      { expression: 'document.title' }
    );
    return result.result.value;
  }

  /**
   * Get the page URL
   */
  async url(): Promise<string> {
    const result = await this.sendToTarget<{ result: { value: string } }>(
      'Runtime.evaluate',
      { expression: 'window.location.href' }
    );
    return result.result.value;
  }

  /**
   * Evaluate JavaScript in the page context
   */
  async evaluate<T = any>(expression: string): Promise<T> {
    const result = await this.sendToTarget<{ result: { value: T } }>(
      'Runtime.evaluate',
      { expression, returnByValue: true }
    );
    return result.result.value;
  }

  /**
   * Take a screenshot
   */
  async screenshot(options?: { format?: 'png' | 'jpeg'; quality?: number }): Promise<Uint8Array> {
    const result = await this.sendToTarget<{ data: string }>(
      'Page.captureScreenshot',
      {
        format: options?.format || 'png',
        quality: options?.quality,
      }
    );
    
    // Decode base64
    return Uint8Array.from(atob(result.data), c => c.charCodeAt(0));
  }

  /**
   * Close this page
   */
  async close(): Promise<void> {
    try {
      await this.browser.closeTarget(this.targetId);
    } catch {
      // Ignore errors on close
    }
    if (this.pageWs) {
      this.pageWs.close();
      this.pageWs = null;
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // Element Interaction Methods (Playwright-like API)
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Query a single element by CSS selector
   */
  async $(selector: string): Promise<ElementHandle | null> {
    return querySelector(this, selector);
  }

  /**
   * Query all elements matching a CSS selector
   */
  async $$(selector: string): Promise<ElementHandle[]> {
    return querySelectorAll(this, selector);
  }

  /**
   * Click an element by selector
   */
  async click(selector: string, options?: { timeout?: number }): Promise<void> {
    const handle = await waitForSelector(this, selector, { timeout: options?.timeout });
    await clickElement(this, handle);
  }

  /**
   * Type text into an element
   */
  async type(selector: string, text: string, options?: { delay?: number; timeout?: number }): Promise<void> {
    const handle = await waitForSelector(this, selector, { timeout: options?.timeout });
    await typeIntoElement(this, handle, text, { delay: options?.delay });
  }

  /**
   * Fill an input (clear first, then type)
   */
  async fill(selector: string, text: string, options?: { timeout?: number }): Promise<void> {
    const handle = await waitForSelector(this, selector, { timeout: options?.timeout });
    await clearElement(this, handle);
    await typeIntoElement(this, handle, text);
  }

  /**
   * Get text content of an element
   */
  async textContent(selector: string): Promise<string | null> {
    const handle = await this.$(selector);
    if (!handle) return null;
    return getTextContent(this, handle);
  }

  /**
   * Get an attribute value
   */
  async getAttribute(selector: string, name: string): Promise<string | null> {
    const handle = await this.$(selector);
    if (!handle) return null;
    return getAttribute(this, handle, name);
  }

  /**
   * Check if element is visible
   */
  async isVisible(selector: string): Promise<boolean> {
    const handle = await this.$(selector);
    if (!handle) return false;
    return isVisible(this, handle);
  }

  /**
   * Wait for an element to appear
   */
  async waitForSelector(selector: string, options?: { timeout?: number; visible?: boolean }): Promise<ElementHandle> {
    return waitForSelector(this, selector, options);
  }
}

/**
 * Create a new page in the browser
 */
export async function createPage(browser: BunCDP, url = 'about:blank'): Promise<CDPPage> {
  const targetId = await browser.createTarget(url);
  const page = new CDPPage(browser, targetId);
  await page.attach();
  return page;
}

export default CDPPage;
