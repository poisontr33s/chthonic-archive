/**
 * BunCDP Frame - Cross-frame interaction support
 * 
 * Manages iframe execution contexts for enterprise automation scenarios:
 * - Stripe payment forms
 * - OAuth popups
 * - Embedded widgets
 * - Legacy iframe-based apps
 * 
 * Architecture:
 * - FrameRegistry: Tracks Page.frameNavigated/frameDetached events
 * - CDPFrame: Page-like API scoped to a specific frame context
 * 
 * @module bun-cdp/frame
 */

import type { CDPPage } from './bun-cdp-page';
import {
  type ElementHandle,
  getBoundingBox,
  getElementCenter,
} from './bun-cdp-element';

export interface FrameInfo {
  frameId: string;
  parentFrameId?: string;
  name?: string;
  url: string;
  securityOrigin?: string;
  executionContextId?: number;
}

/**
 * Frame Registry - Maintains live map of frames in a page
 */
export class FrameRegistry {
  private frames = new Map<string, FrameInfo>();
  private contextToFrame = new Map<number, string>();  // executionContextId -> frameId
  private mainFrameId: string | null = null;
  private initialized = false;

  constructor(private page: CDPPage) {}

  /**
   * Initialize frame tracking
   */
  async init(): Promise<void> {
    if (this.initialized) return;

    // Enable Runtime domain to receive execution context events
    await (this.page as any).sendToTarget('Runtime.enable');

    // Get initial frame tree
    const frameTree = await (this.page as any).sendToTarget('Page.getFrameTree');
    this.processFrameTree(frameTree.frameTree);

    // Listen for frame events
    this.page.on('Page.frameNavigated', (params) => {
      this.onFrameNavigated(params.frame);
    });

    this.page.on('Page.frameDetached', (params) => {
      this.onFrameDetached(params.frameId);
    });

    // Track execution contexts for frames
    this.page.on('Runtime.executionContextCreated', (params) => {
      const ctx = params.context;
      if (ctx.auxData?.frameId) {
        const frameId = ctx.auxData.frameId;
        const frame = this.frames.get(frameId);
        if (frame && ctx.auxData?.isDefault) {
          frame.executionContextId = ctx.id;
          this.contextToFrame.set(ctx.id, frameId);
        }
      }
    });

    this.page.on('Runtime.executionContextDestroyed', (params) => {
      const frameId = this.contextToFrame.get(params.executionContextId);
      if (frameId) {
        const frame = this.frames.get(frameId);
        if (frame) {
          frame.executionContextId = undefined;
        }
        this.contextToFrame.delete(params.executionContextId);
      }
    });

    // Fetch existing execution contexts (for already-loaded frames)
    await this.fetchExecutionContexts();

    this.initialized = true;
  }

  /**
   * Fetch all current execution contexts and map to frames
   */
  private async fetchExecutionContexts(): Promise<void> {
    // Evaluate in each frame to trigger context creation events
    for (const [frameId] of this.frames) {
      try {
        // Use Runtime.evaluate with unique context via frameId
        const result = await (this.page as any).sendToTarget('Page.createIsolatedWorld', {
          frameId,
          worldName: 'buncdp-context-probe',
          grantUniveralAccess: true,
        });
        
        if (result?.executionContextId) {
          const frame = this.frames.get(frameId);
          if (frame && !frame.executionContextId) {
            frame.executionContextId = result.executionContextId;
            this.contextToFrame.set(result.executionContextId, frameId);
          }
        }
      } catch {
        // Frame may have navigated away - ignore
      }
    }
  }

  /**
   * Ensure frame has an execution context, fetching if needed
   */
  async ensureContextForFrame(frameId: string): Promise<number | undefined> {
    const frame = this.frames.get(frameId);
    if (!frame) return undefined;
    
    if (frame.executionContextId) {
      return frame.executionContextId;
    }

    // Create isolated world for this frame
    try {
      const result = await (this.page as any).sendToTarget('Page.createIsolatedWorld', {
        frameId,
        worldName: 'buncdp',
        grantUniveralAccess: true,
      });
      
      if (result?.executionContextId) {
        frame.executionContextId = result.executionContextId;
        this.contextToFrame.set(result.executionContextId, frameId);
        return result.executionContextId;
      }
    } catch {
      // Frame may be cross-origin or detached
    }

    return undefined;
  }

  private processFrameTree(node: any): void {
    const frame = node.frame;
    this.frames.set(frame.id, {
      frameId: frame.id,
      parentFrameId: frame.parentId,
      name: frame.name,
      url: frame.url,
      securityOrigin: frame.securityOrigin,
    });

    if (!frame.parentId) {
      this.mainFrameId = frame.id;
    }

    // Process child frames
    if (node.childFrames) {
      for (const child of node.childFrames) {
        this.processFrameTree(child);
      }
    }
  }

  private onFrameNavigated(frame: any): void {
    this.frames.set(frame.id, {
      frameId: frame.id,
      parentFrameId: frame.parentId,
      name: frame.name,
      url: frame.url,
      securityOrigin: frame.securityOrigin,
    });

    if (!frame.parentId) {
      this.mainFrameId = frame.id;
    }
  }

  private onFrameDetached(frameId: string): void {
    const frame = this.frames.get(frameId);
    if (frame?.executionContextId) {
      this.contextToFrame.delete(frame.executionContextId);
    }
    this.frames.delete(frameId);
  }

  /**
   * Get main frame ID
   */
  get mainFrame(): string | null {
    return this.mainFrameId;
  }

  /**
   * Get all frames
   */
  getFrames(): FrameInfo[] {
    return Array.from(this.frames.values());
  }

  /**
   * Get frame by ID
   */
  getFrameById(frameId: string): FrameInfo | undefined {
    return this.frames.get(frameId);
  }

  /**
   * Find frame by name attribute
   */
  getFrameByName(name: string): FrameInfo | undefined {
    for (const frame of this.frames.values()) {
      if (frame.name === name) {
        return frame;
      }
    }
    return undefined;
  }

  /**
   * Find frame by URL (partial match)
   */
  getFrameByUrl(urlPattern: string | RegExp): FrameInfo | undefined {
    for (const frame of this.frames.values()) {
      if (typeof urlPattern === 'string') {
        if (frame.url.includes(urlPattern)) {
          return frame;
        }
      } else if (urlPattern.test(frame.url)) {
        return frame;
      }
    }
    return undefined;
  }

  /**
   * Get child frames of a parent
   */
  getChildFrames(parentFrameId: string): FrameInfo[] {
    return Array.from(this.frames.values()).filter(
      f => f.parentFrameId === parentFrameId
    );
  }
}

/**
 * CDPFrame - Page-like API for a specific frame context
 */
export class CDPFrame {
  constructor(
    private page: CDPPage,
    private frameInfo: FrameInfo,
    private registry: FrameRegistry
  ) {}

  get frameId(): string {
    return this.frameInfo.frameId;
  }

  get name(): string | undefined {
    return this.frameInfo.name;
  }

  get url(): string {
    return this.frameInfo.url;
  }

  /**
   * Ensure we have an execution context for this frame
   */
  private async ensureContext(): Promise<number> {
    // Try existing context first
    if (this.frameInfo.executionContextId) {
      return this.frameInfo.executionContextId;
    }

    // Use registry to create context if needed
    const contextId = await this.registry.ensureContextForFrame(this.frameId);
    if (!contextId) {
      throw new Error(`Cannot access frame ${this.frameId} - may be cross-origin or detached`);
    }

    this.frameInfo.executionContextId = contextId;
    return contextId;
  }

  /**
   * Evaluate JavaScript in this frame's context
   */
  async evaluate<T = any>(expression: string): Promise<T> {
    const contextId = await this.ensureContext();

    const result = await (this.page as any).sendToTarget('Runtime.evaluate', {
      expression,
      contextId,
      returnByValue: true,
    });

    return result?.result?.value;
  }

  /**
   * Query element in this frame
   */
  async $(selector: string): Promise<ElementHandle | null> {
    const contextId = await this.ensureContext();

    // Check if element exists
    const exists = await this.evaluate(`!!document.querySelector(${JSON.stringify(selector)})`);
    if (!exists) return null;

    // Get element as remote object
    const evalResult = await (this.page as any).sendToTarget('Runtime.evaluate', {
      expression: `document.querySelector(${JSON.stringify(selector)})`,
      contextId,
      returnByValue: false,
    });

    if (!evalResult?.result?.objectId) {
      return null;
    }

    return {
      selector,
      objectId: evalResult.result.objectId,
    };
  }

  /**
   * Query all elements in this frame
   */
  async $$(selector: string): Promise<ElementHandle[]> {
    const contextId = await this.ensureContext();

    const evalResult = await (this.page as any).sendToTarget('Runtime.evaluate', {
      expression: `Array.from(document.querySelectorAll(${JSON.stringify(selector)}))`,
      contextId,
      returnByValue: false,
    });

    if (!evalResult?.result?.objectId) {
      return [];
    }

    const props = await (this.page as any).sendToTarget('Runtime.getProperties', {
      objectId: evalResult.result.objectId,
      ownProperties: true,
    });

    const handles: ElementHandle[] = [];
    for (const prop of props.result || []) {
      if (prop.value?.objectId && !isNaN(parseInt(prop.name))) {
        handles.push({
          selector: `${selector}[${prop.name}]`,
          objectId: prop.value.objectId,
        });
      }
    }

    return handles;
  }

  /**
   * Click element in this frame
   */
  async click(selector: string): Promise<void> {
    const handle = await this.waitForSelector(selector);
    
    // Scroll into view
    await (this.page as any).sendToTarget('Runtime.callFunctionOn', {
      objectId: handle.objectId,
      functionDeclaration: `function() { this.scrollIntoViewIfNeeded(); }`,
    });

    await new Promise(r => setTimeout(r, 50));

    const center = await getElementCenter(this.page, handle);
    if (!center) {
      throw new Error(`Cannot get position for ${selector} in frame ${this.frameId}`);
    }

    // Dispatch click
    await (this.page as any).sendToTarget('Input.dispatchMouseEvent', {
      type: 'mousePressed',
      x: center.x,
      y: center.y,
      button: 'left',
      clickCount: 1,
    });

    await (this.page as any).sendToTarget('Input.dispatchMouseEvent', {
      type: 'mouseReleased',
      x: center.x,
      y: center.y,
      button: 'left',
      clickCount: 1,
    });
  }

  /**
   * Type into element in this frame
   */
  async type(selector: string, text: string): Promise<void> {
    const handle = await this.waitForSelector(selector);

    // Focus
    await (this.page as any).sendToTarget('Runtime.callFunctionOn', {
      objectId: handle.objectId,
      functionDeclaration: `function() { this.focus(); }`,
    });

    // Type characters
    for (const char of text) {
      await (this.page as any).sendToTarget('Input.dispatchKeyEvent', {
        type: 'keyDown',
        text: char,
      });
      await (this.page as any).sendToTarget('Input.dispatchKeyEvent', {
        type: 'keyUp',
        text: char,
      });
    }
  }

  /**
   * Fill input in this frame (clear + type)
   */
  async fill(selector: string, text: string): Promise<void> {
    const handle = await this.waitForSelector(selector);

    // Focus and select all
    await (this.page as any).sendToTarget('Runtime.callFunctionOn', {
      objectId: handle.objectId,
      functionDeclaration: `function() { this.focus(); this.select(); }`,
    });

    // Delete
    await (this.page as any).sendToTarget('Input.dispatchKeyEvent', {
      type: 'keyDown',
      key: 'Delete',
      code: 'Delete',
    });
    await (this.page as any).sendToTarget('Input.dispatchKeyEvent', {
      type: 'keyUp',
      key: 'Delete',
      code: 'Delete',
    });

    // Type new text
    for (const char of text) {
      await (this.page as any).sendToTarget('Input.dispatchKeyEvent', {
        type: 'keyDown',
        text: char,
      });
      await (this.page as any).sendToTarget('Input.dispatchKeyEvent', {
        type: 'keyUp',
        text: char,
      });
    }
  }

  /**
   * Get text content of element in frame
   */
  async textContent(selector: string): Promise<string | null> {
    const handle = await this.$(selector);
    if (!handle) return null;

    const result = await (this.page as any).sendToTarget('Runtime.callFunctionOn', {
      objectId: handle.objectId,
      functionDeclaration: `function() { return this.textContent; }`,
      returnByValue: true,
    });

    return result?.result?.value || '';
  }

  /**
   * Wait for selector in this frame
   */
  async waitForSelector(selector: string, options?: { timeout?: number }): Promise<ElementHandle> {
    const timeout = options?.timeout || 30000;
    const start = Date.now();

    while (Date.now() - start < timeout) {
      const handle = await this.$(selector);
      if (handle) return handle;
      await new Promise(r => setTimeout(r, 100));
    }

    throw new Error(`Timeout waiting for ${selector} in frame ${this.frameId}`);
  }
}

export default { FrameRegistry, CDPFrame };
