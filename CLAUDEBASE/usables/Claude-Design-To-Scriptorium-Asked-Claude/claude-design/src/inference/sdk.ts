/**
 * SdkInference — direct Anthropic API via the OAuth token that Claude Code
 * already holds. No CLI subprocess. Same StreamEvent contract as cli.ts.
 *
 * Token discovery order:
 *   1. ANTHROPIC_CONFIG_DIR env var → <dir>/.credentials.json
 *   2. %APPDATA%\Claude\.credentials.json  (Windows / Claude app default)
 *   3. ~/.claude/.credentials.json          (fallback)
 *   4. <config>/.credentials.json or <config>/credentials/<id>.json
 *
 * If no token is found the user sees a clear error in the Marginalia rather
 * than a silent hang. Sign in once through Claude Code and the token is
 * shared automatically — same account, same quota.
 *
 * Made by Claude.
 */

import { EventEmitter } from 'node:events';
import * as os from 'node:os';
import * as path from 'node:path';
import * as fs from 'node:fs/promises';
import type { StreamEvent } from './cli';

const ANTHROPIC_API  = 'https://api.anthropic.com';
const API_VERSION    = '2023-06-01';
const DEFAULT_MODEL  = 'claude-opus-4-8';

interface CredFile {
  accessToken?: string;
  expiresAt?: string;
  claudeAiOauth?: { accessToken?: string; expiresAt?: string; };
}

async function dirs(): Promise<string[]> {
  const candidates: string[] = [];

  const env = process.env['ANTHROPIC_CONFIG_DIR'];
  if (env) candidates.push(env);

  if (process.platform === 'win32') {
    const appdata = process.env['APPDATA'];
    if (appdata) candidates.push(path.join(appdata, 'Claude'));
  }

  candidates.push(path.join(os.homedir(), '.claude'));
  return candidates;
}

async function readToken(): Promise<string | null> {
  for (const dir of await dirs()) {
    // Single-file format: <dir>/.credentials.json
    try {
      const raw  = await fs.readFile(path.join(dir, '.credentials.json'), 'utf8');
      const data = JSON.parse(raw) as CredFile;
      if (data.claudeAiOauth?.accessToken) return data.claudeAiOauth.accessToken;
      if (data.accessToken) return data.accessToken;
    } catch {}

    // Profile-keyed format: <dir>/credentials/<id>.json
    try {
      const files = await fs.readdir(path.join(dir, 'credentials'));
      for (const f of files.filter(n => n.endsWith('.json'))) {
        const raw  = await fs.readFile(path.join(dir, 'credentials', f), 'utf8');
        const data = JSON.parse(raw) as CredFile;
        if (data.claudeAiOauth?.accessToken) return data.claudeAiOauth.accessToken;
        if (data.accessToken) return data.accessToken;
      }
    } catch {}
  }
  return null;
}

export class SdkInference extends EventEmitter {
  private abort: AbortController | null = null;

  send(prompt: string, _opts: { cwd?: string } = {}): void {
    this.abort?.abort();
    this.abort = new AbortController();
    void this._stream(prompt, this.abort.signal);
  }

  private async _stream(prompt: string, signal: AbortSignal): Promise<void> {
    const token = await readToken();
    if (!token) {
      this.emit('event', {
        type: 'error',
        data: 'No Claude OAuth token found. Open Claude Code (anthropic.claude-code), sign in, then try again.',
      } as StreamEvent);
      this.emit('event', { type: 'done', data: {} } as StreamEvent);
      return;
    }

    let res: Response;
    try {
      res = await fetch(`${ANTHROPIC_API}/v1/messages`, {
        method:  'POST',
        headers: {
          'Content-Type':      'application/json',
          'Authorization':     `Bearer ${token}`,
          'anthropic-version': API_VERSION,
        },
        body: JSON.stringify({
          model:      DEFAULT_MODEL,
          max_tokens: 4096,
          stream:     true,
          messages:   [{ role: 'user', content: prompt }],
        }),
        signal,
      });
    } catch (err: any) {
      if (err?.name !== 'AbortError') {
        this.emit('event', { type: 'error', data: String(err) } as StreamEvent);
      }
      this.emit('event', { type: 'done', data: {} } as StreamEvent);
      return;
    }

    if (!res.ok) {
      const body = await res.text().catch(() => '');
      this.emit('event', { type: 'error', data: `API ${res.status}: ${body.slice(0, 200)}` } as StreamEvent);
      this.emit('event', { type: 'done', data: {} } as StreamEvent);
      return;
    }

    const reader  = res.body!.getReader();
    const dec     = new TextDecoder();
    let   buf     = '';
    let   stopped = false;

    try {
      while (!stopped) {
        const { value, done } = await reader.read();
        if (done) break;
        buf += dec.decode(value, { stream: true });

        const lines = buf.split('\n');
        buf = lines.pop() ?? '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const payload = line.slice(6).trim();
          if (!payload || payload === '[DONE]') continue;
          try {
            const evt = JSON.parse(payload);
            if (evt.type === 'content_block_delta' && evt.delta?.type === 'text_delta') {
              this.emit('event', { type: 'message', data: { text: evt.delta.text } } as StreamEvent);
            } else if (evt.type === 'message_stop') {
              stopped = true;
            } else if (evt.type === 'error') {
              this.emit('event', { type: 'error', data: evt.error?.message ?? 'stream error' } as StreamEvent);
              stopped = true;
            }
          } catch { /* malformed line — skip */ }
        }
      }
    } finally {
      reader.releaseLock();
    }

    this.emit('event', { type: 'done', data: {} } as StreamEvent);
  }

  dispose(): void {
    this.abort?.abort();
    this.abort = null;
  }
}
