// @SID: SCRIPT_BUN_CDP_PAGE_V1
#!/usr/bin/env bun

// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: bun-cdp-page.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: ORANGE
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ║ Ogdoad-Ceque Radiance:
// ║   └─◄ bun-playwright-poc/src/bun-cdp-element.ts
// ║   └─◄ bun-playwright-poc/src/bun-cdp-frame.ts
// ║   └─◄ bun-playwright-poc/src/index.ts
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * BunCDP Page - High-level page automation API
 *
 * @SID           LIB_BUN_CDP_PAGE_V1
 * @Shabti        Library Module
 * @Heka-Ayni     CONCEPT_CDP_PAGE_AUTOMATION
 * @Ankh-Tinku    STATE_CDP_PAGE_OPERATIONAL
 * @Purpose       High-level page automation API built on raw CDP, providing
 *                familiar Playwright-like methods (goto, click, fill, evaluate,
 *                screenshot, waitForSelector, dialog handling).
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
import { FrameRegistry, CDPFrame, type FrameInfo } from './bun-cdp-frame';

export interface PageOptions {
  timeout?: number;
  /** Auto-dismiss JavaScript dialogs (alert/confirm/prompt). Default: true */
  autoDialogDismiss?: boolean;
}

/** Dialog event info */
export interface DialogInfo {
  type: 'alert' | 'confirm' | 'prompt' | 'beforeunload';
  message: string;
  defaultPrompt?: string;
}

/** Dialog handler function */
export type DialogHandler = (dialog: DialogInfo) => { accept: boolean; promptText?: string } | void;

export type { ElementHandle, FrameInfo };

export class CDPPage {
  private pageWs: WebSocket | null = null;
  private pageMessageId = 0;
  private pagePendingMessages = new Map<number, {
    resolve: (value: any) => void;
    reject: (error: Error) => void;
  }>();
  private eventListeners = new Map<string, Set<(params: any) => void>>();
  
  // Network tracking state
  private networkEnabled = false;
  private inflightRequests = new Set<string>();  // requestId set
  
  // Frame registry
  private frameRegistry: FrameRegistry | null = null;
  
  // Dialog handling
  private dialogHandler: DialogHandler | null = null;
  private autoDialogDismiss: boolean;
  
  constructor(
    private browser: BunCDP,
    public readonly targetId: string,
    private options: PageOptions = {}
  ) {
    this.autoDialogDismiss = options.autoDialogDismiss ?? true;
  }

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
    
    // Setup dialog auto-dismissal
    this.setupDialogHandler();
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
   * Setup automatic dialog (alert/confirm/prompt) handling
   * Without this, any JS dialog will freeze the driver indefinitely
   */
  private setupDialogHandler(): void {
    this.on('Page.javascriptDialogOpening', async (params) => {
      const dialogInfo: DialogInfo = {
        type: params.type,
        message: params.message,
        defaultPrompt: params.defaultPrompt,
      };

      let response = { accept: true, promptText: '' };

      // If user registered a custom handler, call it
      if (this.dialogHandler) {
        const result = this.dialogHandler(dialogInfo);
        if (result) {
          response = { accept: result.accept, promptText: result.promptText || '' };
        }
      } else if (this.autoDialogDismiss) {
        // Default: accept alerts, dismiss confirms/prompts
        response = {
          accept: params.type === 'alert' || params.type === 'beforeunload',
          promptText: params.defaultPrompt || '',
        };
      }

      // Dismiss the dialog to unblock CDP
      await this.sendToTarget('Page.handleJavaScriptDialog', response);
    });
  }

  /**
   * Register a custom dialog handler
   * 
   * @example
   * page.setDialogHandler((dialog) => {
   *   if (dialog.type === 'confirm') {
   *     return { accept: dialog.message.includes('delete') ? false : true };
   *   }
   * });
   */
  setDialogHandler(handler: DialogHandler | null): void {
    this.dialogHandler = handler;
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

  // ═══════════════════════════════════════════════════════════════════════════
  // Network Tracking (for SPA support)
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Enable network domain and start tracking requests
   */
  private async enableNetwork(): Promise<void> {
    if (this.networkEnabled) return;

    await this.sendToTarget('Network.enable');
    this.networkEnabled = true;

    // Track request starts
    this.on('Network.requestWillBeSent', (params) => {
      this.inflightRequests.add(params.requestId);
    });

    // Track request completions
    this.on('Network.loadingFinished', (params) => {
      this.inflightRequests.delete(params.requestId);
    });

    // Track request failures
    this.on('Network.loadingFailed', (params) => {
      this.inflightRequests.delete(params.requestId);
    });

    // Track redirects (they complete the original request)
    this.on('Network.responseReceived', (params) => {
      // Response received but loading may continue
    });
  }

  /**
   * Get current number of in-flight network requests
   */
  get pendingRequestCount(): number {
    return this.inflightRequests.size;
  }

  /**
   * Wait for network to become idle (no pending requests for specified duration)
   * 
   * State machine:
   * 1. Start tracking when inflightRequests.size === 0
   * 2. If a new request starts, reset the idle timer
   * 3. Resolve when idle duration is reached
   * 
   * @param idleTime - How long (ms) network must be idle. Default 500ms.
   * @param timeout - Max time to wait. Default 30000ms.
   */
  async waitForNetworkIdle(options?: { idleTime?: number; timeout?: number }): Promise<void> {
    const idleTime = options?.idleTime ?? 500;
    const timeout = options?.timeout ?? 30000;

    // Ensure network tracking is enabled
    await this.enableNetwork();

    return new Promise((resolve, reject) => {
      let idleTimer: ReturnType<typeof setTimeout> | null = null;
      const startTime = Date.now();

      const checkIdle = () => {
        // Timeout check
        if (Date.now() - startTime > timeout) {
          cleanup();
          reject(new Error(`Network idle timeout (${this.inflightRequests.size} requests pending)`));
          return;
        }

        if (this.inflightRequests.size === 0) {
          // Start idle timer if not already running
          if (!idleTimer) {
            idleTimer = setTimeout(() => {
              cleanup();
              resolve();
            }, idleTime);
          }
        } else {
          // Requests in flight - reset timer
          if (idleTimer) {
            clearTimeout(idleTimer);
            idleTimer = null;
          }
        }
      };

      // Event handlers
      const onRequestStart = () => {
        if (idleTimer) {
          clearTimeout(idleTimer);
          idleTimer = null;
        }
      };

      const onRequestEnd = () => {
        checkIdle();
      };

      const cleanup = () => {
        if (idleTimer) clearTimeout(idleTimer);
        this.off('Network.requestWillBeSent', onRequestStart);
        this.off('Network.loadingFinished', onRequestEnd);
        this.off('Network.loadingFailed', onRequestEnd);
      };

      // Subscribe to events
      this.on('Network.requestWillBeSent', onRequestStart);
      this.on('Network.loadingFinished', onRequestEnd);
      this.on('Network.loadingFailed', onRequestEnd);

      // Initial check
      checkIdle();
    });
  }

  /**
   * THE DECORATOR'S OBSERVATORY: Visual Stability Protocol (2026 Edition)
   * 
   * Succeeds networkIdle by observing DOM mutations directly.
   * Crucial for RSC (React Server Components) and streaming SSR where
   * network connections remain open "forever".
   * 
   * @param stabilityDuration - Time (ms) DOM must stay static. Default 500ms.
   * @param timeout - Max time to wait. Default 30000ms.
   */
  async waitForVisualStability(options?: { stabilityDuration?: number; timeout?: number }): Promise<void> {
    const stabilityDuration = options?.stabilityDuration ?? 500;
    const timeout = options?.timeout ?? 30000;

    await this.evaluate(`
      new Promise((resolve, reject) => {
        let timer;
        const observer = new MutationObserver(() => {
          if (timer) clearTimeout(timer);
          timer = setTimeout(() => {
            observer.disconnect();
            resolve();
          }, ${stabilityDuration});
        });

        observer.observe(document.body, {
          attributes: true,
          childList: true,
          subtree: true,
          characterData: true
        });

        setTimeout(() => {
          observer.disconnect();
          reject(new Error("Visual stability not reached within ${timeout}ms"));
        }, ${timeout});

        timer = setTimeout(() => {
          observer.disconnect();
          resolve();
        }, ${stabilityDuration});
      })
    `);
  }

  /**
   * Navigate to a URL and wait for load
   */
  async goto(url: string, options?: { 
    timeout?: number; 
    waitUntil?: 'load' | 'domcontentloaded' | 'networkidle' | 'visual-stability'
  }): Promise<void> {
    const timeout = options?.timeout || this.options.timeout || 30000;
    const waitUntil = options?.waitUntil || 'load';
    
    // Enable Page.lifecycleEvent if not already
    await this.sendToTarget('Page.setLifecycleEventsEnabled', { enabled: true });
    
    // For networkidle, enable network tracking before navigation
    if (waitUntil === 'networkidle') {
      await this.enableNetwork();
    }
    
    // Set up the wait BEFORE navigating to avoid race condition
    let loadPromise: Promise<any>;
    
    if (waitUntil === 'networkidle') {
      loadPromise = this.waitForNetworkIdle({ timeout });
    } else if (waitUntil === 'visual-stability') {
      // For visual stability, we wait for 'load' first THEN stability
      loadPromise = this.waitForEvent('Page.loadEventFired', undefined, timeout)
        .then(() => this.waitForVisualStability({ timeout }));
    } else {
      loadPromise = this.waitForEvent('Page.loadEventFired', undefined, timeout);
    }
    
    // Navigate
    const { errorText } = await this.sendToTarget('Page.navigate', { url });
    if (errorText && errorText !== 'net::ERR_ABORTED') {
      throw new Error(`Navigation failed: ${errorText}`);
    }
    
    // Wait for completion
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

  // ═══════════════════════════════════════════════════════════════════════════
  // Frame Support (Cross-frame interaction)
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Initialize frame tracking (lazy)
   */
  private async ensureFrameRegistry(): Promise<FrameRegistry> {
    if (!this.frameRegistry) {
      this.frameRegistry = new FrameRegistry(this);
      await this.frameRegistry.init();
    }
    return this.frameRegistry;
  }

  /**
   * Get all frames in the page
   */
  async frames(): Promise<FrameInfo[]> {
    const registry = await this.ensureFrameRegistry();
    return registry.getFrames();
  }

  /**
   * Get a frame by name attribute
   * 
   * @example
   * const stripeFrame = await page.frame('stripe-card-element');
   * await stripeFrame.fill('input[name="cardnumber"]', '4242424242424242');
   */
  async frame(name: string): Promise<CDPFrame | null> {
    const registry = await this.ensureFrameRegistry();
    const frameInfo = registry.getFrameByName(name);
    if (!frameInfo) return null;
    return new CDPFrame(this, frameInfo, registry);
  }

  /**
   * Get a frame by URL pattern
   * 
   * @example
   * const oauthFrame = await page.frameByUrl('accounts.google.com');
   */
  async frameByUrl(urlPattern: string | RegExp): Promise<CDPFrame | null> {
    const registry = await this.ensureFrameRegistry();
    const frameInfo = registry.getFrameByUrl(urlPattern);
    if (!frameInfo) return null;
    return new CDPFrame(this, frameInfo, registry);
  }

  /**
   * Get the main frame
   */
  async mainFrame(): Promise<CDPFrame | null> {
    const registry = await this.ensureFrameRegistry();
    const mainFrameId = registry.mainFrame;
    if (!mainFrameId) return null;
    const frameInfo = registry.getFrameById(mainFrameId);
    if (!frameInfo) return null;
    return new CDPFrame(this, frameInfo, registry);
  }

  /**
   * Wait for a frame to appear by name
   */
  async waitForFrame(name: string, options?: { timeout?: number }): Promise<CDPFrame> {
    const timeout = options?.timeout || 30000;
    const start = Date.now();

    while (Date.now() - start < timeout) {
      const frame = await this.frame(name);
      if (frame) return frame;
      await new Promise(r => setTimeout(r, 100));
    }

    throw new Error(`Timeout waiting for frame: ${name}`);
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
