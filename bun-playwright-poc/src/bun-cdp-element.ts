// ╔════════════════════════════════════════════════════════════════════════════╗
// ║  THE DECORATOR'S BLESSING: bun-cdp-element.ts                            ║
// ║  TypeScript module: BoxModel, ElementHandle                                 ║
// ╠════════════════════════════════════════════════════════════════════════════╣
// ║  Spectral Frequency: ORANGE                                                 ║
// ║  Architectural Role: 🔭 THE OBSERVATORY                                      ║
// ║  Purpose: * BunCDP Element - Element interaction via CDP
 * 
 * Translates CSS s ║
// ║  Exports: BoxModel, ElementHandle                                           ║
// ╠════════════════════════════════════════════════════════════════════════════╣
// ║  Cross-References (Bidirectional):                                      ║
// ║  Dependencies (I rely on):                                               ║
// ║    ├─► bun-playwright-poc\src\bun-cdp-frame.ts                           ║
// ║    ├─► bun-playwright-poc\src\index.ts                                   ║
// ║  Dependents (Rely on me):                                                ║
// ║    └─◄ bun-playwright-poc\src\bun-cdp-frame.ts                           ║
// ║    └─◄ bun-playwright-poc\src\bun-cdp-page.ts                            ║
// ╚════════════════════════════════════════════════════════════════════════════╝

/**
 * BunCDP Element - Element interaction via CDP
 * 
 * Translates CSS selectors into CDP operations:
 * 1. selector → DOM.querySelector → nodeId
 * 2. nodeId → DOM.getBoxModel → coordinates
 * 3. coordinates → Input.dispatchMouseEvent → click
 * 
 * @module bun-cdp/element
 */

import type { CDPPage } from './bun-cdp-page';

export interface BoxModel {
  content: number[];  // [x1,y1, x2,y2, x3,y3, x4,y4] quad
  padding: number[];
  border: number[];
  margin: number[];
  width: number;
  height: number;
}

export interface ElementHandle {
  selector: string;
  objectId: string;
  nodeId?: number;
}

/**
 * Query a single element by CSS selector
 */
export async function querySelector(
  page: CDPPage,
  selector: string
): Promise<ElementHandle | null> {
  // Get element as remote object (single query, no redundant check)
  const evalResult = await (page as any).sendToTarget('Runtime.evaluate', {
    expression: `document.querySelector(${JSON.stringify(selector)})`,
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
 * Query all elements matching a CSS selector
 */
export async function querySelectorAll(
  page: CDPPage,
  selector: string
): Promise<ElementHandle[]> {
  const evalResult = await (page as any).sendToTarget('Runtime.evaluate', {
    expression: `Array.from(document.querySelectorAll(${JSON.stringify(selector)}))`,
    returnByValue: false,
  });

  if (!evalResult?.result?.objectId) {
    return [];
  }

  // Get array properties
  const props = await (page as any).sendToTarget('Runtime.getProperties', {
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
 * Get the bounding box of an element
 */
export async function getBoundingBox(
  page: CDPPage,
  handle: ElementHandle
): Promise<{ x: number; y: number; width: number; height: number } | null> {
  // Use Runtime.callFunctionOn to get bounding rect
  const result = await (page as any).sendToTarget('Runtime.callFunctionOn', {
    objectId: handle.objectId,
    functionDeclaration: `function() {
      const rect = this.getBoundingClientRect();
      return {
        x: rect.x,
        y: rect.y,
        width: rect.width,
        height: rect.height
      };
    }`,
    returnByValue: true,
  });

  return result?.result?.value || null;
}

/**
 * Get the center point of an element
 */
export async function getElementCenter(
  page: CDPPage,
  handle: ElementHandle
): Promise<{ x: number; y: number } | null> {
  const box = await getBoundingBox(page, handle);
  if (!box) return null;

  return {
    x: box.x + box.width / 2,
    y: box.y + box.height / 2,
  };
}

/**
 * Click an element by dispatching mouse events
 */
export async function clickElement(
  page: CDPPage,
  handle: ElementHandle,
  options?: { button?: 'left' | 'right' | 'middle'; clickCount?: number }
): Promise<void> {
  const center = await getElementCenter(page, handle);
  if (!center) {
    throw new Error(`Cannot get position for element: ${handle.selector}`);
  }

  const button = options?.button || 'left';
  const clickCount = options?.clickCount || 1;

  // Scroll element into view first
  await (page as any).sendToTarget('Runtime.callFunctionOn', {
    objectId: handle.objectId,
    functionDeclaration: `function() { this.scrollIntoViewIfNeeded(); }`,
  });

  // Small delay for scroll
  await new Promise(r => setTimeout(r, 50));

  // Re-get center after scroll
  const newCenter = await getElementCenter(page, handle);
  const { x, y } = newCenter || center;

  // Mouse down
  await (page as any).sendToTarget('Input.dispatchMouseEvent', {
    type: 'mousePressed',
    x,
    y,
    button,
    clickCount,
  });

  // Mouse up
  await (page as any).sendToTarget('Input.dispatchMouseEvent', {
    type: 'mouseReleased',
    x,
    y,
    button,
    clickCount,
  });
}

/**
 * Type text into an element (focus + key events)
 */
export async function typeIntoElement(
  page: CDPPage,
  handle: ElementHandle,
  text: string,
  options?: { delay?: number }
): Promise<void> {
  // Focus the element
  await (page as any).sendToTarget('Runtime.callFunctionOn', {
    objectId: handle.objectId,
    functionDeclaration: `function() { this.focus(); }`,
  });

  const delay = options?.delay || 0;

  // Type each character
  for (const char of text) {
    await (page as any).sendToTarget('Input.dispatchKeyEvent', {
      type: 'keyDown',
      text: char,
    });

    await (page as any).sendToTarget('Input.dispatchKeyEvent', {
      type: 'keyUp',
      text: char,
    });

    if (delay > 0) {
      await new Promise(r => setTimeout(r, delay));
    }
  }
}

/**
 * Clear an input element
 */
export async function clearElement(
  page: CDPPage,
  handle: ElementHandle
): Promise<void> {
  await (page as any).sendToTarget('Runtime.callFunctionOn', {
    objectId: handle.objectId,
    functionDeclaration: `function() { 
      this.focus();
      this.select();
    }`,
  });

  // Delete selected text
  await (page as any).sendToTarget('Input.dispatchKeyEvent', {
    type: 'keyDown',
    key: 'Delete',
    code: 'Delete',
  });

  await (page as any).sendToTarget('Input.dispatchKeyEvent', {
    type: 'keyUp',
    key: 'Delete',
    code: 'Delete',
  });
}

/**
 * Get element text content
 */
export async function getTextContent(
  page: CDPPage,
  handle: ElementHandle
): Promise<string> {
  const result = await (page as any).sendToTarget('Runtime.callFunctionOn', {
    objectId: handle.objectId,
    functionDeclaration: `function() { return this.textContent; }`,
    returnByValue: true,
  });

  return result?.result?.value || '';
}

/**
 * Get element inner HTML
 */
export async function getInnerHTML(
  page: CDPPage,
  handle: ElementHandle
): Promise<string> {
  const result = await (page as any).sendToTarget('Runtime.callFunctionOn', {
    objectId: handle.objectId,
    functionDeclaration: `function() { return this.innerHTML; }`,
    returnByValue: true,
  });

  return result?.result?.value || '';
}

/**
 * Get element attribute
 */
export async function getAttribute(
  page: CDPPage,
  handle: ElementHandle,
  name: string
): Promise<string | null> {
  const result = await (page as any).sendToTarget('Runtime.callFunctionOn', {
    objectId: handle.objectId,
    functionDeclaration: `function(attr) { return this.getAttribute(attr); }`,
    arguments: [{ value: name }],
    returnByValue: true,
  });

  return result?.result?.value ?? null;
}

/**
 * Check if element is visible
 */
export async function isVisible(
  page: CDPPage,
  handle: ElementHandle
): Promise<boolean> {
  const result = await (page as any).sendToTarget('Runtime.callFunctionOn', {
    objectId: handle.objectId,
    functionDeclaration: `function() {
      const style = window.getComputedStyle(this);
      return style.display !== 'none' && 
             style.visibility !== 'hidden' && 
             style.opacity !== '0' &&
             this.offsetParent !== null;
    }`,
    returnByValue: true,
  });

  return result?.result?.value || false;
}

/**
 * Wait for an element to appear
 */
export async function waitForSelector(
  page: CDPPage,
  selector: string,
  options?: { timeout?: number; visible?: boolean }
): Promise<ElementHandle> {
  const timeout = options?.timeout || 30000;
  const checkVisible = options?.visible || false;
  const start = Date.now();

  while (Date.now() - start < timeout) {
    const handle = await querySelector(page, selector);
    
    if (handle) {
      if (!checkVisible) {
        return handle;
      }
      
      const visible = await isVisible(page, handle);
      if (visible) {
        return handle;
      }
    }

    await new Promise(r => setTimeout(r, 100));
  }

  throw new Error(`Timeout waiting for selector: ${selector}`);
}

export default {
  querySelector,
  querySelectorAll,
  getBoundingBox,
  getElementCenter,
  clickElement,
  typeIntoElement,
  clearElement,
  getTextContent,
  getInnerHTML,
  getAttribute,
  isVisible,
  waitForSelector,
};
