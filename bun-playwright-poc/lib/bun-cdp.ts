/**
 * BunCDP - A lightweight CDP (Chrome DevTools Protocol) wrapper for Bun
 * 
 * This module provides browser automation capabilities using raw CDP over WebSocket,
 * bypassing Playwright's incompatible protocol layer while leveraging Bun's native
 * WebSocket and subprocess APIs.
 * 
 * PROVEN WORKING (2026-01-23):
 * - Bun.spawn() for Chrome process management ✓
 * - Native WebSocket for CDP communication ✓
 * - CDP commands: Browser.getVersion, Target.createTarget ✓
 * - Both headless and headed modes ✓
 * 
 * @module bun-cdp
 * @version 0.1.0
 */

export interface CDPResponse<T = any> {
  id: number;
  result?: T;
  error?: { code: number; message: string };
}

export interface CDPEvent {
  method: string;
  params?: any;
}

export interface BrowserVersion {
  protocolVersion: string;
  product: string;
  revision: string;
  userAgent: string;
  jsVersion: string;
}

export interface TargetInfo {
  targetId: string;
  type: string;
  title: string;
  url: string;
}

export interface BunCDPOptions {
  chromePath?: string;
  headless?: boolean;
  port?: number;
  args?: string[];
  startupTimeout?: number;
}

const DEFAULT_CHROMIUM_PATH = process.env.LOCALAPPDATA + 
  '\\ms-playwright\\chromium-1207\\chrome-win64\\chrome.exe';

export class BunCDP {
  private ws: WebSocket | null = null;
  private proc: ReturnType<typeof Bun.spawn> | null = null;
  private messageId = 0;
  private pendingMessages = new Map<number, {
    resolve: (value: any) => void;
    reject: (error: Error) => void;
  }>();
  private eventHandlers = new Map<string, Set<(params: any) => void>>();
  
  public port: number;
  public browserVersion: BrowserVersion | null = null;

  constructor(private options: BunCDPOptions = {}) {
    this.port = options.port || (19000 + Math.floor(Math.random() * 999));
  }

  /**
   * Launch Chrome and establish CDP connection
   */
  async launch(): Promise<void> {
    const chromePath = this.options.chromePath || DEFAULT_CHROMIUM_PATH;
    const headless = this.options.headless ?? true;
    const startupTimeout = this.options.startupTimeout || 10000;
    
    // Build Chrome args
    const args = [
      chromePath,
      `--remote-debugging-port=${this.port}`,
      '--no-first-run',
      '--no-sandbox',
      '--disable-gpu',
      ...(headless ? ['--headless=new'] : []),
      ...(this.options.args || []),
    ];

    // Spawn Chrome
    this.proc = Bun.spawn({
      cmd: args,
      stdout: 'pipe',
      stderr: 'pipe',
    });

    // Wait for DevTools to be ready
    const startTime = Date.now();
    let wsUrl: string | null = null;
    
    while (Date.now() - startTime < startupTimeout) {
      try {
        const resp = await fetch(`http://127.0.0.1:${this.port}/json/version`, {
          signal: AbortSignal.timeout(1000),
        });
        const data = await resp.json() as { webSocketDebuggerUrl: string; Browser: string };
        wsUrl = data.webSocketDebuggerUrl;
        break;
      } catch {
        await Bun.sleep(200);
      }
    }

    if (!wsUrl) {
      this.proc.kill();
      throw new Error(`Chrome DevTools not ready after ${startupTimeout}ms`);
    }

    // Connect WebSocket
    await this.connectWebSocket(wsUrl);
    
    // Get browser version
    this.browserVersion = await this.send<BrowserVersion>('Browser.getVersion');
  }

  private async connectWebSocket(url: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error('WebSocket connection timeout'));
      }, 10000);

      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        clearTimeout(timeout);
        resolve();
      };

      this.ws.onerror = (e) => {
        clearTimeout(timeout);
        reject(new Error(`WebSocket error: ${e}`));
      };

      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data as string);
        
        if (data.id !== undefined) {
          // Response to a command
          const pending = this.pendingMessages.get(data.id);
          if (pending) {
            this.pendingMessages.delete(data.id);
            if (data.error) {
              pending.reject(new Error(`CDP Error: ${data.error.message}`));
            } else {
              pending.resolve(data.result);
            }
          }
        } else if (data.method) {
          // Event
          const handlers = this.eventHandlers.get(data.method);
          if (handlers) {
            for (const handler of handlers) {
              handler(data.params);
            }
          }
        }
      };

      this.ws.onclose = () => {
        for (const pending of this.pendingMessages.values()) {
          pending.reject(new Error('WebSocket closed'));
        }
        this.pendingMessages.clear();
      };
    });
  }

  /**
   * Send a CDP command and wait for response
   */
  async send<T = any>(method: string, params?: any): Promise<T> {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket not connected');
    }

    const id = ++this.messageId;
    
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        this.pendingMessages.delete(id);
        reject(new Error(`CDP command timeout: ${method}`));
      }, 30000);

      this.pendingMessages.set(id, {
        resolve: (result) => {
          clearTimeout(timeout);
          resolve(result);
        },
        reject: (error) => {
          clearTimeout(timeout);
          reject(error);
        },
      });

      this.ws!.send(JSON.stringify({ id, method, params }));
    });
  }

  /**
   * Subscribe to CDP events
   */
  on(event: string, handler: (params: any) => void): void {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, new Set());
    }
    this.eventHandlers.get(event)!.add(handler);
  }

  /**
   * Unsubscribe from CDP events
   */
  off(event: string, handler: (params: any) => void): void {
    this.eventHandlers.get(event)?.delete(handler);
  }

  /**
   * Create a new browser target (page)
   */
  async createTarget(url = 'about:blank'): Promise<string> {
    const result = await this.send<{ targetId: string }>('Target.createTarget', { url });
    return result.targetId;
  }

  /**
   * Get all targets
   */
  async getTargets(): Promise<TargetInfo[]> {
    const result = await this.send<{ targetInfos: TargetInfo[] }>('Target.getTargets');
    return result.targetInfos;
  }

  /**
   * Close a target
   */
  async closeTarget(targetId: string): Promise<boolean> {
    const result = await this.send<{ success: boolean }>('Target.closeTarget', { targetId });
    return result.success;
  }

  /**
   * Navigate a target to a URL (requires attaching to target first)
   */
  async attachToTarget(targetId: string): Promise<string> {
    const result = await this.send<{ sessionId: string }>('Target.attachToTarget', {
      targetId,
      flatten: true,
    });
    return result.sessionId;
  }

  /**
   * Close the browser and cleanup
   */
  async close(): Promise<void> {
    if (this.ws) {
      try {
        await this.send('Browser.close');
      } catch {
        // Ignore errors during close
      }
      this.ws.close();
      this.ws = null;
    }

    if (this.proc) {
      this.proc.kill();
      this.proc = null;
    }
  }

  /**
   * Check if browser is connected
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

/**
 * Convenience function to create and launch a browser
 */
export async function launchBrowser(options?: BunCDPOptions): Promise<BunCDP> {
  const browser = new BunCDP(options);
  await browser.launch();
  return browser;
}

export default BunCDP;
