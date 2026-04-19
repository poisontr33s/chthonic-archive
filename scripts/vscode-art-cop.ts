#!/usr/bin/env bun
// @SID: SCRIPT_VSCODE_ART_COP_V1

/**
 * SID: VSCODE_ART_COP_2026_02_20
 * Purpose: Analyze UI screenshots via local OpenAI-compatible LLM endpoint and emit iterative mailbox reports.
 */

import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs';
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

type CycleSummary = {
  cycle: number;
  capturedAt: string;
  reportPath: string;
  imageCount: number;
  imageFingerprint: string;
  score: number;
  verdict: ArtCopResult['verdict'];
  note: string;
};

type AnalyzeOptions = {
  endpoint: string;
  model: string;
  noLlm: boolean;
  temperature: number;
  promptText: string;
};

const DEFAULT_PROMPT_TEMPLATE = [
  'You are ArtCop (Universal): a design critic and remediation engine.',
  'Evaluate only from visible and behavioral evidence.',
  'Preserve design identity while improving clarity and usability.',
  'Return strict JSON only with keys: overall_score, verdict, strengths, findings, next_actions.',
  'Verdict must be one of: ship|iterate|block.',
].join(' ');

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

function toInt(value: string | undefined, fallback: number): number {
  if (!value) return fallback;
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function toFloat(value: string | undefined, fallback: number): number {
  if (!value) return fallback;
  const parsed = Number.parseFloat(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
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

function collectLatestImages(imagesDir: string, maxImages: number): string[] {
  const root = path.resolve(imagesDir);
  if (!existsSync(root)) {
    return [];
  }
  const entries = readdirSync(root, { withFileTypes: true })
    .filter((entry) => entry.isFile())
    .map((entry) => {
      const fullPath = path.join(root, entry.name);
      const ext = path.extname(entry.name).toLowerCase();
      return { fullPath, ext, mtimeMs: statSync(fullPath).mtimeMs };
    })
    .filter((entry) => ['.png', '.jpg', '.jpeg', '.webp'].includes(entry.ext))
    .sort((left, right) => right.mtimeMs - left.mtimeMs)
    .slice(0, Math.max(1, maxImages))
    .map((entry) => entry.fullPath);

  return entries;
}

function imageSignature(filePath: string): string {
  const stat = statSync(filePath);
  const digest = createHash('sha1').update(readFileSync(filePath)).digest('hex').slice(0, 12);
  return `${path.basename(filePath)}:${stat.size}:${stat.mtimeMs}:${digest}`;
}

function imageFingerprint(images: string[]): string {
  if (images.length === 0) return 'none';
  const signatures = images.map((img) => imageSignature(img));
  return createHash('sha1').update(signatures.join('|')).digest('hex');
}

function resolveImages(explicitImages: string[], imagesDir: string | undefined, maxImages: number): string[] {
  const selected = explicitImages.length > 0 ? explicitImages : imagesDir ? collectLatestImages(imagesDir, maxImages) : [];
  return selected.map((img) => path.resolve(img));
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
      if (
        typeof parsed.overall_score === 'number' &&
        typeof parsed.verdict === 'string' &&
        Array.isArray(parsed.findings)
      ) {
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
      'Rerun with --images or --images-dir and inspect cycle trend.',
    ],
  };
}

function loadPromptTemplate(promptFile: string | undefined): string {
  const candidates = [
    promptFile,
    path.join('.temple', 'prompts', 'UNIVERSAL_ART_COP_PROMPT.md'),
  ].filter(Boolean) as string[];

  for (const candidate of candidates) {
    const resolved = path.resolve(candidate);
    if (existsSync(resolved)) {
      return readFileSync(resolved, 'utf8');
    }
  }
  return DEFAULT_PROMPT_TEMPLATE;
}

function buildPromptText(params: {
  cycle: number;
  cycles: number;
  goal: string;
  baseline: string | undefined;
  template: string;
  previousResult: ArtCopResult | null;
  previousScoreDelta: number | null;
}): string {
  const lines: string[] = [];
  lines.push(params.template.trim());
  lines.push('');
  lines.push(`Cycle: ${params.cycle}/${params.cycles}`);
  lines.push(`Goal: ${params.goal}`);
  if (params.baseline) {
    lines.push(`Baseline: ${params.baseline}`);
  }
  if (params.previousResult) {
    lines.push(`Previous verdict: ${params.previousResult.verdict}`);
    lines.push(`Previous score: ${params.previousResult.overall_score}`);
    if (params.previousScoreDelta !== null) {
      lines.push(`Previous score delta: ${params.previousScoreDelta >= 0 ? '+' : ''}${params.previousScoreDelta}`);
    }
    if (params.previousResult.findings.length > 0) {
      lines.push(
        `Focus unresolved findings first: ${params.previousResult.findings
          .slice(0, 3)
          .map((f) => `${f.area}:${f.issue}`)
          .join(' | ')}`,
      );
    }
  }
  lines.push('Return strict JSON only.');
  return lines.join('\n');
}

async function analyzeImages(
  images: string[],
  options: AnalyzeOptions,
): Promise<{ result: ArtCopResult; rawModelText: string; transportNote: string }> {
  if (options.noLlm) {
    return {
      result: fallbackResult('LLM disabled via --no-llm'),
      rawModelText: '',
      transportNote: 'LLM call skipped by flag.',
    };
  }

  try {
    const content: Array<{ type: string; text?: string; image_url?: { url: string } }> = [
      {
        type: 'text',
        text: options.promptText,
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

    const response = await fetch(options.endpoint, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        model: options.model,
        temperature: options.temperature,
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
      signal: AbortSignal.timeout(30000),
    });

    if (!response.ok) {
      throw new Error(`endpoint returned ${response.status}`);
    }

    const payload = (await response.json()) as ChatCompletionResponse;
    const rawModelText = payload.choices?.[0]?.message?.content || '';
    const parsed = parseJsonObject(rawModelText);
    if (!parsed) {
      throw new Error('model did not return parseable JSON');
    }

    return {
      result: parsed,
      rawModelText,
      transportNote: 'LLM analysis completed.',
    };
  } catch (error) {
    const msg = (error as Error).message;
    return {
      result: fallbackResult(msg),
      rawModelText: '',
      transportNote: `LLM analysis failed; fallback report emitted. Error: ${msg}`,
    };
  }
}

function reportMarkdown(params: {
  cycle: number;
  cycles: number;
  capturedAt: string;
  endpoint: string;
  model: string;
  transportNote: string;
  imagesDir: string | undefined;
  images: string[];
  imageFingerprint: string;
  result: ArtCopResult;
  rawModelText: string;
  scoreDelta: number | null;
  verdictChanged: boolean;
  promptText: string;
}): string {
  const lines: string[] = [];
  lines.push('# ArtCop VS Code UI Report');
  lines.push('');
  lines.push(`- Captured: ${params.capturedAt}`);
  lines.push(`- Cycle: ${params.cycle}/${params.cycles}`);
  lines.push(`- Endpoint: ${params.endpoint}`);
  lines.push(`- Model: ${params.model}`);
  lines.push(`- Note: ${params.transportNote}`);
  lines.push(`- Image Fingerprint: ${params.imageFingerprint}`);
  if (params.imagesDir) {
    lines.push(`- Images Directory: ${path.resolve(params.imagesDir)}`);
  }
  lines.push('');
  lines.push('## Images');
  lines.push('');
  params.images.forEach((img) => lines.push(`- ${img}`));
  lines.push('');
  lines.push('## Verdict');
  lines.push('');
  lines.push(`- Score: ${params.result.overall_score}`);
  lines.push(`- Verdict: ${params.result.verdict}`);
  if (params.scoreDelta !== null) {
    lines.push(`- Score Delta vs Previous Cycle: ${params.scoreDelta >= 0 ? '+' : ''}${params.scoreDelta}`);
  }
  lines.push(`- Verdict Changed: ${params.verdictChanged ? 'yes' : 'no'}`);
  lines.push('');
  lines.push('## Strengths');
  lines.push('');
  for (const s of params.result.strengths || []) {
    lines.push(`- ${s}`);
  }
  if (!params.result.strengths || params.result.strengths.length === 0) {
    lines.push('- (none)');
  }
  lines.push('');
  lines.push('## Findings');
  lines.push('');
  for (const f of params.result.findings || []) {
    lines.push(`- [${f.severity}] ${f.area}: ${f.issue} -> ${f.recommendation}`);
  }
  if (!params.result.findings || params.result.findings.length === 0) {
    lines.push('- (none)');
  }
  lines.push('');
  lines.push('## Next Actions');
  lines.push('');
  for (const a of params.result.next_actions || []) {
    lines.push(`- ${a}`);
  }
  if (!params.result.next_actions || params.result.next_actions.length === 0) {
    lines.push('- (none)');
  }

  lines.push('');
  lines.push('## Prompt Used');
  lines.push('');
  lines.push('```txt');
  lines.push(params.promptText);
  lines.push('```');

  if (params.rawModelText) {
    lines.push('');
    lines.push('## Raw Model Output');
    lines.push('');
    lines.push('```json');
    lines.push(params.rawModelText);
    lines.push('```');
  }

  return lines.join('\n') + '\n';
}

async function main() {
  const explicitImages = parseImages();
  const endpoint = argValue('endpoint') || process.env.ART_COP_ENDPOINT || 'http://127.0.0.1:5000/v1/chat/completions';
  const model = argValue('model') || process.env.ART_COP_MODEL || 'local-vlm';
  const mailboxDir = argValue('mailbox-dir') || path.join('codex', 'mailbox');
  const noLlm = argFlag('no-llm');
  const imagesDir = argValue('images-dir');
  const maxImages = toInt(argValue('max-images'), 4);
  const cycles = Math.max(1, toInt(argValue('cycles') || argValue('iterations'), 1));
  const intervalMs = Math.max(0, toInt(argValue('interval-ms'), 1500));
  const waitForChange = argFlag('wait-for-change');
  const maxWaitMs = Math.max(1000, toInt(argValue('max-wait-ms'), 120000));
  const stopOnShip = argFlag('stop-on-ship');
  const stopScore = Math.max(1, toInt(argValue('stop-score'), 101));
  const goal = argValue('goal') || 'Improve hierarchy, readability, interaction clarity, and mobile resilience.';
  const baseline = argValue('baseline');
  const temperature = toFloat(argValue('temperature'), 0.2);
  const promptTemplate = loadPromptTemplate(argValue('prompt-file'));

  mkdirSync(mailboxDir, { recursive: true });
  const artCopArchiveDir = path.join(mailboxDir, 'archive', 'art-cop');
  mkdirSync(artCopArchiveDir, { recursive: true });

  const runStartedAt = new Date().toISOString();
  const runRootId = runStartedAt.replace(/[:.]/g, '-');
  const cycleSummaries: CycleSummary[] = [];

  let previousFingerprint: string | null = null;
  let previousResult: ArtCopResult | null = null;
  let previousScoreDelta: number | null = null;

  for (let cycle = 1; cycle <= cycles; cycle++) {
    let images = resolveImages(explicitImages, imagesDir, maxImages);

    if (images.length === 0) {
      throw new Error('no images provided. use --images a.png,b.png or --images-dir <path>');
    }

    let currentFingerprint = imageFingerprint(images);
    if (waitForChange && previousFingerprint && currentFingerprint === previousFingerprint) {
      const waitStartedAt = Date.now();
      while (Date.now() - waitStartedAt < maxWaitMs) {
        await sleep(Math.max(250, intervalMs));
        images = resolveImages(explicitImages, imagesDir, maxImages);
        if (images.length === 0) continue;
        currentFingerprint = imageFingerprint(images);
        if (currentFingerprint !== previousFingerprint) break;
      }
    }

    const capturedAt = new Date().toISOString();
    const runId = `${capturedAt.replace(/[:.]/g, '-')}_c${String(cycle).padStart(2, '0')}`;
    const promptText = buildPromptText({
      cycle,
      cycles,
      goal,
      baseline,
      template: promptTemplate,
      previousResult,
      previousScoreDelta,
    });

    const { result, rawModelText, transportNote } = await analyzeImages(images, {
      endpoint,
      model,
      noLlm,
      temperature,
      promptText,
    });

    const scoreDelta = previousResult ? result.overall_score - previousResult.overall_score : null;
    const verdictChanged = previousResult ? result.verdict !== previousResult.verdict : false;

    const report = reportMarkdown({
      cycle,
      cycles,
      capturedAt,
      endpoint,
      model,
      transportNote,
      imagesDir,
      images,
      imageFingerprint: currentFingerprint,
      result,
      rawModelText,
      scoreDelta,
      verdictChanged,
      promptText,
    });

    const latest = path.join(mailboxDir, 'ART_COP_REPORT_LATEST.md');
    const archive = path.join(artCopArchiveDir, `ART_COP_REPORT_${runId}.md`);
    writeFileSync(latest, report, 'utf8');
    writeFileSync(archive, report, 'utf8');

    cycleSummaries.push({
      cycle,
      capturedAt,
      reportPath: archive,
      imageCount: images.length,
      imageFingerprint: currentFingerprint,
      score: result.overall_score,
      verdict: result.verdict,
      note: transportNote,
    });

    console.log(
      `[art-cop] cycle ${cycle}/${cycles} -> score=${result.overall_score} verdict=${result.verdict} archive=${archive}`,
    );

    previousScoreDelta = scoreDelta;
    previousResult = result;
    previousFingerprint = currentFingerprint;

    if (stopOnShip && result.verdict === 'ship') {
      console.log('[art-cop] stop-on-ship enabled and verdict=ship; ending loop.');
      break;
    }
    if (result.overall_score >= stopScore) {
      console.log(`[art-cop] score reached stop-score=${stopScore}; ending loop.`);
      break;
    }
    if (cycle < cycles && intervalMs > 0) {
      await sleep(intervalMs);
    }
  }

  const history = {
    runStartedAt,
    runRootId,
    endpoint,
    model,
    goal,
    baseline: baseline || null,
    noLlm,
    waitForChange,
    cyclesRequested: cycles,
    cyclesCompleted: cycleSummaries.length,
    cycles: cycleSummaries,
  };

  const historyLatest = path.join(mailboxDir, 'ART_COP_HISTORY_LATEST.json');
  const historyArchive = path.join(artCopArchiveDir, `ART_COP_HISTORY_${runRootId}.json`);
  writeFileSync(historyLatest, JSON.stringify(history, null, 2) + '\n', 'utf8');
  writeFileSync(historyArchive, JSON.stringify(history, null, 2) + '\n', 'utf8');

  console.log(`[art-cop] wrote ${historyLatest}`);
  console.log(`[art-cop] wrote ${historyArchive}`);
}

await main().catch((error) => {
  console.error(`[art-cop] fatal: ${(error as Error).message}`);
  process.exit(1);
});
