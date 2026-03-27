// @SID: SCRIPT_HF_MODEL_RANKER_V1
#!/usr/bin/env bun

/**
 * SID: HF_MODEL_RANKER_2026_02_20
 * Purpose: Snapshot and rank Hugging Face models with trend + adoption + hardware-fit + local benchmark fusion.
 */

import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { Database } from 'bun:sqlite';

type HfModel = {
  id: string;
  likes?: number;
  downloads?: number;
  trendingScore?: number;
  private?: boolean;
  createdAt?: string;
  pipeline_tag?: string;
  library_name?: string;
  tags?: string[];
  modelId?: string;
};

type BenchmarkEntry = {
  lane?: string;
  model_file?: string;
  composite_score?: number;
  avg_toks_per_s?: number;
  passes?: number;
  task_count?: number;
};

type BenchmarkPayload = {
  generated?: string;
  results?: BenchmarkEntry[];
};

type BenchmarkSignal = {
  lane: string;
  modelFile: string;
  quality: number;
  speed: number;
  matchConfidence: number;
};

type ScoreBreakdown = {
  trend: number;
  downloads: number;
  likes: number;
  recency: number;
  source: number;
  hardwareFit: number;
  benchQuality: number;
  benchSpeed: number;
};

type HardwareEstimate = {
  paramsBillions: number | null;
  quantHint: string | null;
  estimatedVramGb: number | null;
  fitScore: number;
};

type RankedModel = {
  id: string;
  score: number;
  downloads: number;
  likes: number;
  trendingScore: number;
  createdAt?: string;
  pipelineTag?: string;
  libraryName?: string;
  tags: string[];
  sources: string[];
  scoreBreakdown: ScoreBreakdown;
  hardware: HardwareEstimate;
  benchmark: BenchmarkSignal | null;
};

const HF_BASE = 'https://huggingface.co';
const DEFAULT_LIMIT = 120;
const DEFAULT_TARGET_VRAM_GB = 16;
const DEFAULT_SEARCH_TERMS = ['hermes', 'gemma 3 uncensored', 'qwen', 'deepseek', 'mistral'];

function argValue(name: string): string | undefined {
  const prefix = `--${name}=`;
  const withEq = process.argv.find((a) => a.startsWith(prefix));
  if (withEq) return withEq.slice(prefix.length);
  const idx = process.argv.indexOf(`--${name}`);
  if (idx >= 0 && process.argv[idx + 1]) return process.argv[idx + 1];
  return undefined;
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

function clamp01(value: number): number {
  return Math.max(0, Math.min(1, value));
}

function daysSince(dateIso?: string): number | null {
  if (!dateIso) return null;
  const parsed = Date.parse(dateIso);
  if (!Number.isFinite(parsed)) return null;
  return Math.floor((Date.now() - parsed) / (1000 * 60 * 60 * 24));
}

function recencyScore(createdAt?: string): number {
  const days = daysSince(createdAt);
  if (days === null) return 0.25;
  if (days <= 14) return 1.0;
  if (days <= 30) return 0.9;
  if (days <= 90) return 0.7;
  if (days <= 180) return 0.5;
  if (days <= 365) return 0.3;
  return 0.15;
}

function normLog(value: number, maxLog: number): number {
  if (!Number.isFinite(value) || value <= 0) return 0;
  return Math.min(Math.log10(value + 1) / maxLog, 1);
}

function normalizeText(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
}

function tokens(value: string): Set<string> {
  return new Set(
    normalizeText(value)
      .split(/\s+/)
      .map((token) => token.trim())
      .filter((token) => token.length >= 2),
  );
}

function quantBytes(quantHint: string | null): number {
  if (!quantHint) return 1.4;
  const q = quantHint.toLowerCase();
  if (q.includes('q2')) return 0.30;
  if (q.includes('q3')) return 0.40;
  if (q.includes('iq4') || q.includes('q4')) return 0.50;
  if (q.includes('q5')) return 0.63;
  if (q.includes('q6')) return 0.75;
  if (q.includes('q8')) return 1.00;
  if (q.includes('bf16') || q.includes('fp16')) return 2.00;
  if (q.includes('fp32')) return 4.00;
  return 1.4;
}

function detectQuantHint(model: HfModel): string | null {
  const source = `${model.id} ${(model.tags ?? []).join(' ')}`.toLowerCase();
  const match = source.match(/\b(i?q[2-8](?:[_-][a-z0-9]+)?|bf16|fp16|fp32)\b/i);
  return match?.[1] ?? null;
}

function detectParamsBillions(model: HfModel): number | null {
  const source = `${model.id} ${(model.tags ?? []).join(' ')}`;
  const matches = [...source.matchAll(/(\d+(?:\.\d+)?)\s*([bBtT])\b/g)];
  if (matches.length === 0) {
    return null;
  }
  let best = 0;
  for (const match of matches) {
    const value = Number.parseFloat(match[1]);
    const unit = match[2].toLowerCase();
    if (!Number.isFinite(value) || value <= 0) continue;
    const billions = unit === 't' ? value * 1000 : value;
    if (billions > best) {
      best = billions;
    }
  }
  return best > 0 ? best : null;
}

function estimateHardware(model: HfModel, targetVramGb: number): HardwareEstimate {
  const paramsBillions = detectParamsBillions(model);
  const quantHint = detectQuantHint(model);

  if (paramsBillions === null) {
    return {
      paramsBillions: null,
      quantHint,
      estimatedVramGb: null,
      fitScore: 0.45,
    };
  }

  const estimatedVramGb = Number((paramsBillions * quantBytes(quantHint) * 1.25).toFixed(2));
  const fitScore = estimatedVramGb <= targetVramGb
    ? 1
    : clamp01(Math.pow(targetVramGb / estimatedVramGb, 1.6));

  return {
    paramsBillions,
    quantHint,
    estimatedVramGb,
    fitScore: Number(fitScore.toFixed(6)),
  };
}

async function fetchModels(url: string): Promise<HfModel[]> {
  const response = await fetch(url, {
    headers: {
      'User-Agent': 'chthonic-hf-ranker/2.0',
      'Accept': 'application/json',
    },
  });
  if (!response.ok) {
    throw new Error(`HF request failed ${response.status} for ${url}`);
  }
  const payload = await response.json();
  if (!Array.isArray(payload)) {
    throw new Error(`Unexpected payload for ${url}`);
  }
  return payload as HfModel[];
}

function uniqueModelId(model: HfModel): string {
  return model.id || model.modelId || '';
}

function findLatestBenchmarkJson(repoRoot: string): string | null {
  const dir = path.join(repoRoot, 'claude-codex-gemini', 'session_resumption_pickup');
  if (!existsSync(dir)) {
    return null;
  }
  const candidates = readdirSync(dir)
    .filter((name) => /^LOCAL_UNCENSORED_BENCHMARK_\d+(?:_\d+)?\.json$/i.test(name))
    .map((name) => {
      const full = path.join(dir, name);
      return { full, mtime: statSync(full).mtimeMs };
    })
    .sort((a, b) => b.mtime - a.mtime);

  return candidates[0]?.full ?? null;
}

function loadBenchmarkEntries(filePath: string | null): BenchmarkEntry[] {
  if (!filePath || !existsSync(filePath)) {
    return [];
  }
  try {
    const raw = readFileSync(filePath, 'utf8');
    const payload = JSON.parse(raw) as BenchmarkPayload;
    if (!Array.isArray(payload.results)) {
      return [];
    }
    return payload.results;
  } catch {
    return [];
  }
}

function benchmarkMatch(modelId: string, entry: BenchmarkEntry): number {
  const modelTokens = tokens(modelId);
  const benchCorpus = `${entry.lane ?? ''} ${entry.model_file ?? ''} ${path.basename(entry.model_file ?? '')}`;
  const benchTokens = tokens(benchCorpus);

  if (modelTokens.size === 0 || benchTokens.size === 0) {
    return 0;
  }

  const sharedAlpha: string[] = [];
  let intersection = 0;
  for (const token of modelTokens) {
    if (!benchTokens.has(token)) continue;
    intersection += 1;
    if (/[a-z]/.test(token) && token.length >= 3) {
      sharedAlpha.push(token);
    }
  }

  if (sharedAlpha.length === 0) {
    return 0;
  }

  const familyTokens = new Set([
    'qwen',
    'llama',
    'deepseek',
    'mistral',
    'gemma',
    'gpt',
    'glm',
    'phi',
    'minimax',
  ]);

  const hasFamilyAffinity = sharedAlpha.some((token) => {
    if (familyTokens.has(token)) return true;
    for (const family of familyTokens) {
      if (token.startsWith(family)) return true;
    }
    return false;
  });
  if (!hasFamilyAffinity) {
    return 0;
  }

  const coverage = intersection / modelTokens.size;
  const density = intersection / Math.min(benchTokens.size, modelTokens.size + 6);
  return Number((0.7 * coverage + 0.3 * density).toFixed(6));
}

function benchmarkSignalForModel(modelId: string, entries: BenchmarkEntry[]): BenchmarkSignal | null {
  let best: { entry: BenchmarkEntry; confidence: number } | null = null;

  for (const entry of entries) {
    const confidence = benchmarkMatch(modelId, entry);
    if (!best || confidence > best.confidence) {
      best = { entry, confidence };
    }
  }

  if (!best || best.confidence < 0.18) {
    return null;
  }

  const quality = clamp01((best.entry.composite_score ?? 0) / 100);
  const speed = normLog(best.entry.avg_toks_per_s ?? 0, 2.1);

  return {
    lane: best.entry.lane ?? 'unknown',
    modelFile: best.entry.model_file ?? '',
    quality: Number(quality.toFixed(6)),
    speed: Number(speed.toFixed(6)),
    matchConfidence: Number(best.confidence.toFixed(6)),
  };
}

function weightedScore(features: ScoreBreakdown): number {
  const weights: Record<keyof ScoreBreakdown, number> = {
    trend: 0.24,
    downloads: 0.18,
    likes: 0.13,
    recency: 0.08,
    source: 0.07,
    hardwareFit: 0.15,
    benchQuality: 0.11,
    benchSpeed: 0.04,
  };

  if (features.benchQuality <= 0 && features.benchSpeed <= 0) {
    weights.trend += weights.benchQuality * 0.6 + weights.benchSpeed * 0.4;
    weights.downloads += weights.benchQuality * 0.3;
    weights.likes += weights.benchSpeed * 0.2;
    weights.benchQuality = 0;
    weights.benchSpeed = 0;
  }

  let totalWeight = 0;
  let weighted = 0;
  for (const [key, weight] of Object.entries(weights) as Array<[keyof ScoreBreakdown, number]>) {
    totalWeight += weight;
    weighted += features[key] * weight;
  }

  if (totalWeight <= 0) {
    return 0;
  }
  return Number((weighted / totalWeight).toFixed(6));
}

function ensureColumns(db: Database, table: string, columns: Record<string, string>): void {
  const existing = new Set<string>();
  const rows = db.query(`PRAGMA table_info(${table})`).all() as Array<{ name: string }>;
  for (const row of rows) {
    existing.add(row.name);
  }

  for (const [name, type] of Object.entries(columns)) {
    if (!existing.has(name)) {
      db.run(`ALTER TABLE ${table} ADD COLUMN ${name} ${type}`);
    }
  }
}

async function main() {
  const limit = toInt(argValue('limit'), DEFAULT_LIMIT);
  const repoRoot = process.cwd();
  const outDir = argValue('out-dir') || path.join('codex', 'mailbox', 'cache');
  const mailboxDir = argValue('mailbox-dir') || path.join('codex', 'mailbox');
  const searchCsv = argValue('search');
  const searchTerms = searchCsv
    ? searchCsv.split(',').map((s) => s.trim()).filter(Boolean)
    : DEFAULT_SEARCH_TERMS;
  const targetVramGb = toFloat(argValue('target-vram-gb') ?? process.env.LOCAL_GPU_VRAM_GB, DEFAULT_TARGET_VRAM_GB);

  const benchmarkPath = argValue('benchmark-json') || findLatestBenchmarkJson(repoRoot);
  const benchmarkEntries = loadBenchmarkEntries(benchmarkPath);

  mkdirSync(outDir, { recursive: true });
  mkdirSync(mailboxDir, { recursive: true });
  mkdirSync(path.join(mailboxDir, 'archive', 'hf-rankings'), { recursive: true });

  const sources: Array<{ name: string; url: string }> = [
    {
      name: 'trending_text_generation',
      url: `${HF_BASE}/api/models?filter=text-generation&sort=trendingScore&direction=-1&limit=${limit}`,
    },
    {
      name: 'downloads_text_generation',
      url: `${HF_BASE}/api/models?filter=text-generation&sort=downloads&direction=-1&limit=${limit}`,
    },
    {
      name: 'likes_text_generation',
      url: `${HF_BASE}/api/models?filter=text-generation&sort=likes&direction=-1&limit=${limit}`,
    },
  ];

  for (const term of searchTerms) {
    const q = encodeURIComponent(term);
    sources.push({
      name: `search_${term.replace(/\s+/g, '_')}`,
      url: `${HF_BASE}/api/models?search=${q}&sort=trendingScore&direction=-1&limit=${Math.min(80, limit)}`,
    });
  }

  const modelMap = new Map<string, HfModel>();
  const sourceMap = new Map<string, Set<string>>();

  for (const src of sources) {
    try {
      const models = await fetchModels(src.url);
      for (const model of models) {
        const id = uniqueModelId(model);
        if (!id || model.private) {
          continue;
        }

        const existing = modelMap.get(id);
        if (!existing) {
          modelMap.set(id, model);
        } else {
          modelMap.set(id, {
            ...existing,
            ...model,
            tags: model.tags ?? existing.tags,
          });
        }

        const set = sourceMap.get(id) ?? new Set<string>();
        set.add(src.name);
        sourceMap.set(id, set);
      }
    } catch (error) {
      console.error(`[hf-ranker] source failed: ${src.name} :: ${(error as Error).message}`);
    }
  }

  const ranked: RankedModel[] = Array.from(modelMap.values())
    .map((model) => {
      const id = uniqueModelId(model);
      const sourcesForModel = Array.from(sourceMap.get(id) ?? []);
      const benchmark = benchmarkSignalForModel(id, benchmarkEntries);
      const hardware = estimateHardware(model, targetVramGb);

      const breakdown: ScoreBreakdown = {
        trend: clamp01((model.trendingScore ?? 0) / 800),
        downloads: normLog(model.downloads ?? 0, 8.5),
        likes: normLog(model.likes ?? 0, 4.5),
        recency: recencyScore(model.createdAt),
        source: clamp01(sourcesForModel.length / 6),
        hardwareFit: hardware.fitScore,
        benchQuality: benchmark?.quality ?? 0,
        benchSpeed: benchmark?.speed ?? 0,
      };

      return {
        id,
        score: weightedScore(breakdown),
        downloads: model.downloads ?? 0,
        likes: model.likes ?? 0,
        trendingScore: model.trendingScore ?? 0,
        createdAt: model.createdAt,
        pipelineTag: model.pipeline_tag,
        libraryName: model.library_name,
        tags: model.tags ?? [],
        sources: sourcesForModel,
        scoreBreakdown: breakdown,
        hardware,
        benchmark,
      };
    })
    .sort((a, b) => b.score - a.score);

  const capturedAt = new Date().toISOString();
  const snapshotId = capturedAt.replace(/[:.]/g, '-');

  const dbPath = path.join(outDir, 'hf-model-rankings.db');
  const db = new Database(dbPath);

  db.run(`
    CREATE TABLE IF NOT EXISTS hf_model_rankings (
      snapshot_id TEXT NOT NULL,
      captured_at TEXT NOT NULL,
      model_id TEXT NOT NULL,
      score REAL NOT NULL,
      downloads INTEGER NOT NULL,
      likes INTEGER NOT NULL,
      trending_score REAL NOT NULL,
      created_at TEXT,
      pipeline_tag TEXT,
      library_name TEXT,
      sources_json TEXT,
      tags_json TEXT
    )
  `);

  ensureColumns(db, 'hf_model_rankings', {
    target_vram_gb: 'REAL',
    score_trend: 'REAL',
    score_downloads: 'REAL',
    score_likes: 'REAL',
    score_recency: 'REAL',
    score_source: 'REAL',
    score_hardware_fit: 'REAL',
    score_bench_quality: 'REAL',
    score_bench_speed: 'REAL',
    params_billions: 'REAL',
    quant_hint: 'TEXT',
    estimated_vram_gb: 'REAL',
    benchmark_lane: 'TEXT',
    benchmark_quality: 'REAL',
    benchmark_speed: 'REAL',
    benchmark_match_confidence: 'REAL',
    benchmark_model_file: 'TEXT',
  });

  const insert = db.prepare(`
    INSERT INTO hf_model_rankings (
      snapshot_id, captured_at, model_id, score, downloads, likes, trending_score,
      created_at, pipeline_tag, library_name, sources_json, tags_json,
      target_vram_gb, score_trend, score_downloads, score_likes, score_recency,
      score_source, score_hardware_fit, score_bench_quality, score_bench_speed,
      params_billions, quant_hint, estimated_vram_gb,
      benchmark_lane, benchmark_quality, benchmark_speed, benchmark_match_confidence, benchmark_model_file
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);

  const tx = db.transaction((rows: RankedModel[]) => {
    for (const row of rows) {
      insert.run(
        snapshotId,
        capturedAt,
        row.id,
        row.score,
        row.downloads,
        row.likes,
        row.trendingScore,
        row.createdAt ?? null,
        row.pipelineTag ?? null,
        row.libraryName ?? null,
        JSON.stringify(row.sources),
        JSON.stringify(row.tags),
        targetVramGb,
        row.scoreBreakdown.trend,
        row.scoreBreakdown.downloads,
        row.scoreBreakdown.likes,
        row.scoreBreakdown.recency,
        row.scoreBreakdown.source,
        row.scoreBreakdown.hardwareFit,
        row.scoreBreakdown.benchQuality,
        row.scoreBreakdown.benchSpeed,
        row.hardware.paramsBillions,
        row.hardware.quantHint,
        row.hardware.estimatedVramGb,
        row.benchmark?.lane ?? null,
        row.benchmark?.quality ?? null,
        row.benchmark?.speed ?? null,
        row.benchmark?.matchConfidence ?? null,
        row.benchmark?.modelFile ?? null,
      );
    }
  });
  tx(ranked);
  db.close();

  const top = ranked.slice(0, 40);
  const md: string[] = [];
  md.push('# HF Model Ranking Snapshot');
  md.push('');
  md.push(`- Captured: ${capturedAt}`);
  md.push(`- Snapshot ID: ${snapshotId}`);
  md.push(`- Candidates: ${ranked.length}`);
  md.push(`- Sources: ${sources.length}`);
  md.push(`- Target VRAM (GB): ${targetVramGb}`);
  md.push(`- Benchmark Source: ${benchmarkPath ?? 'none'}`);
  md.push(`- Benchmark Entries: ${benchmarkEntries.length}`);
  md.push(`- DB: ${dbPath}`);
  md.push('');
  md.push('## Top Models');
  md.push('');
  md.push('| Rank | Model | Score | Trend | DL | Likes | Fit | BenchQ | EstVRAM | Created |');
  md.push('|---|---|---:|---:|---:|---:|---:|---:|---:|---|');

  top.forEach((row, idx) => {
    md.push(
      `| ${idx + 1} | ${row.id} | ${row.score.toFixed(4)} | ${row.trendingScore} | ${row.downloads} | ${row.likes} | ${row.scoreBreakdown.hardwareFit.toFixed(2)} | ${row.scoreBreakdown.benchQuality.toFixed(2)} | ${row.hardware.estimatedVramGb ?? 'n/a'} | ${row.createdAt ?? 'n/a'} |`,
    );
  });

  md.push('');
  md.push('## Inputs');
  md.push('');
  for (const src of sources) {
    md.push(`- ${src.name}: ${src.url}`);
  }

  const latestMd = path.join(mailboxDir, 'HF_MODEL_RANKING_LATEST.md');
  const archiveMd = path.join(mailboxDir, 'archive', 'hf-rankings', `HF_MODEL_RANKING_${snapshotId}.md`);
  const latestJson = path.join(outDir, 'hf-model-rankings-latest.json');

  writeFileSync(latestMd, md.join('\n') + '\n', 'utf8');
  writeFileSync(archiveMd, md.join('\n') + '\n', 'utf8');
  writeFileSync(
    latestJson,
    JSON.stringify(
      {
        capturedAt,
        snapshotId,
        count: ranked.length,
        config: {
          targetVramGb,
          benchmarkPath,
          benchmarkEntries: benchmarkEntries.length,
        },
        top,
        sources,
      },
      null,
      2,
    ) + '\n',
    'utf8',
  );

  console.log(`[hf-ranker] wrote ${latestMd}`);
  console.log(`[hf-ranker] wrote ${archiveMd}`);
  console.log(`[hf-ranker] wrote ${latestJson}`);
  console.log(`[hf-ranker] sqlite ${dbPath}`);
}

await main().catch((error) => {
  console.error(`[hf-ranker] fatal: ${(error as Error).message}`);
  process.exit(1);
});
