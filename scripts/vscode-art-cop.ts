#!/usr/bin/env bun
/**
 * SID: VSCODE_ART_COP_2026_02_20
 * Purpose: Analyze UI screenshots via local OpenAI-compatible LLM endpoint and emit mailbox report.
 */

import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';

type Finding = {
  severity: 'high' | 'medium' | 'low';
  area: string;
  issue: string;
  recommendation: string;
};

type ArtCopResult = {
  overall_score: number;
  verdict: 'ship' | 'iterate' | 'block';
  strengths: string[];
  findings: Finding[];
  next_actions: string[];
};

type ChatCompletionResponse = {
  choices?: Array<{ message?: { content?: string } }>;
};

function argValue(name: string): string | undefined {
  const prefix = `--${name}=`;
  const withEq = process.argv.find((a) => a.startsWith(prefix));
  if (withEq) return withEq.slice(prefix.length);
  const idx = process.argv.indexOf(`--${name}`);
  if (idx >= 0 && process.argv[idx + 1]) return process.argv[idx + 1];
  return undefined;
}

function argFlag(name: string): boolean {
  return process.argv.includes(`--${name}`);
}

function parseImages(): string[] {
  const csv = argValue('images') || '';
  const list = csv
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);

  const repeated: string[] = [];
  for (let i = 0; i < process.argv.length; i++) {
    if (process.argv[i] === '--image' && process.argv[i + 1]) {
      repeated.push(process.argv[i + 1]);
    }
  }

  return Array.from(new Set([...list, ...repeated]));
}

function mimeForPath(filePath: string): string {
  const ext = path.extname(filePath).toLowerCase();
  if (ext === '.png') return 'image/png';
  if (ext === '.jpg' || ext === '.jpeg') return 'image/jpeg';
  if (ext === '.webp') return 'image/webp';
  return 'application/octet-stream';
}

async function toDataUrl(filePath: string): Promise<string> {
  const file = Bun.file(filePath);
  if (!(await file.exists())) {
    throw new Error(`image missing: ${filePath}`);
  }
  const buffer = Buffer.from(await file.arrayBuffer());
  const mime = mimeForPath(filePath);
  return `data:${mime};base64,${buffer.toString('base64')}`;
}

function parseJsonObject(raw: string): ArtCopResult | null {
  const trimmed = raw.trim();
  const candidates = [trimmed];
  const start = trimmed.indexOf('{');
  const end = trimmed.lastIndexOf('}');
  if (start >= 0 && end > start) {
    candidates.push(trimmed.slice(start, end + 1));
  }

  for (const candidate of candidates) {
    try {
      const parsed = JSON.parse(candidate) as ArtCopResult;
      if (typeof parsed.overall_score === 'number' && typeof parsed.verdict === 'string') {
        return parsed;
      }
    } catch {
      // continue
    }
  }
  return null;
}

function fallbackResult(error: string): ArtCopResult {
  return {
    overall_score: 0,
    verdict: 'iterate',
    strengths: [],
    findings: [
      {
        severity: 'high',
        area: 'local-llm-lane',
        issue: error,
        recommendation: 'Verify local OpenAI-compatible vision endpoint/model, then rerun art-cop.',
      },
    ],
    next_actions: [
      'Confirm endpoint supports image input in chat.completions format.',
      'Set ART_COP_MODEL to a local VLM.',
      'Rerun with --images and inspect mailbox report diff.',
    ],
  };
}

async function main() {
  const images = parseImages();
  const endpoint = argValue('endpoint') || process.env.ART_COP_ENDPOINT || 'http://127.0.0.1:5000/v1/chat/completions';
  const model = argValue('model') || process.env.ART_COP_MODEL || 'local-vlm';
  const mailboxDir = argValue('mailbox-dir') || path.join('codex', 'mailbox');
  const noLlm = argFlag('no-llm');

  mkdirSync(mailboxDir, { recursive: true });
  mkdirSync(path.join(mailboxDir, 'archive', 'art-cop'), { recursive: true });

  if (images.length === 0) {
    throw new Error('no images provided. use --images a.png,b.png or repeated --image <path>');
  }

  const capturedAt = new Date().toISOString();
  const runId = capturedAt.replace(/[:.]/g, '-');

  let result: ArtCopResult;
  let rawModelText = '';
  let transportNote = '';

  if (noLlm) {
    result = fallbackResult('LLM disabled via --no-llm');
    transportNote = 'LLM call skipped by flag.';
  } else {
    try {
      const content: Array<{ type: string; text?: string; image_url?: { url: string } }> = [
        {
          type: 'text',
          text: [
            'Audit these VS Code UI screenshots as an art director + usability critic.',
            'Return strict JSON only with keys: overall_score, verdict, strengths, findings, next_actions.',
            'Scoring rubric: hierarchy, contrast, spacing rhythm, iconography consistency, cognitive load, panel balance.',
            'Verdict: ship|iterate|block.',
          ].join(' '),
        },
      ];

      for (const imgPath of images) {
        content.push({
          type: 'image_url',
          image_url: { url: await toDataUrl(imgPath) },
        });
      }

      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      if (process.env.LOCAL_LLM_API_KEY) {
        headers.Authorization = `Bearer ${process.env.LOCAL_LLM_API_KEY}`;
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          model,
          temperature: 0.2,
          response_format: { type: 'json_object' },
          messages: [
            {
              role: 'system',
              content: 'You are ArtCop. Be direct, deterministic, and JSON-only.',
            },
            {
              role: 'user',
              content,
            },
          ],
        }),
        signal: AbortSignal.timeout(20000),
      });

      if (!response.ok) {
        throw new Error(`endpoint returned ${response.status}`);
      }

      const payload = (await response.json()) as ChatCompletionResponse;
      rawModelText = payload.choices?.[0]?.message?.content || '';
      const parsed = parseJsonObject(rawModelText);
      if (!parsed) {
        throw new Error('model did not return parseable JSON');
      }
      result = parsed;
      transportNote = 'LLM analysis completed.';
    } catch (error) {
      const msg = (error as Error).message;
      result = fallbackResult(msg);
      transportNote = `LLM analysis failed; fallback report emitted. Error: ${msg}`;
    }
  }

  const lines: string[] = [];
  lines.push('# ArtCop VS Code UI Report');
  lines.push('');
  lines.push(`- Captured: ${capturedAt}`);
  lines.push(`- Endpoint: ${endpoint}`);
  lines.push(`- Model: ${model}`);
  lines.push(`- Note: ${transportNote}`);
  lines.push('');
  lines.push('## Images');
  lines.push('');
  images.forEach((img) => lines.push(`- ${img}`));
  lines.push('');
  lines.push('## Verdict');
  lines.push('');
  lines.push(`- Score: ${result.overall_score}`);
  lines.push(`- Verdict: ${result.verdict}`);
  lines.push('');
  lines.push('## Strengths');
  lines.push('');
  for (const s of result.strengths || []) {
    lines.push(`- ${s}`);
  }
  if (!result.strengths || result.strengths.length === 0) {
    lines.push('- (none)');
  }
  lines.push('');
  lines.push('## Findings');
  lines.push('');
  for (const f of result.findings || []) {
    lines.push(`- [${f.severity}] ${f.area}: ${f.issue} -> ${f.recommendation}`);
  }
  if (!result.findings || result.findings.length === 0) {
    lines.push('- (none)');
  }
  lines.push('');
  lines.push('## Next Actions');
  lines.push('');
  for (const a of result.next_actions || []) {
    lines.push(`- ${a}`);
  }
  if (!result.next_actions || result.next_actions.length === 0) {
    lines.push('- (none)');
  }

  if (rawModelText) {
    lines.push('');
    lines.push('## Raw Model Output');
    lines.push('');
    lines.push('```json');
    lines.push(rawModelText);
    lines.push('```');
  }

  const latest = path.join(mailboxDir, 'ART_COP_REPORT_LATEST.md');
  const archive = path.join(mailboxDir, 'archive', 'art-cop', `ART_COP_REPORT_${runId}.md`);

  writeFileSync(latest, lines.join('\n') + '\n', 'utf8');
  writeFileSync(archive, lines.join('\n') + '\n', 'utf8');

  console.log(`[art-cop] wrote ${latest}`);
  console.log(`[art-cop] wrote ${archive}`);
}

await main().catch((error) => {
  console.error(`[art-cop] fatal: ${(error as Error).message}`);
  process.exit(1);
});
