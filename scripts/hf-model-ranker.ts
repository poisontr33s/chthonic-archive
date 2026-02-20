#!/usr/bin/env bun

/**
 * SID: HF_MODEL_RANKER_2026_02_20
 * Purpose: Snapshot and rank Hugging Face models (trend/download/likes) into SQLite + mailbox report.
 */

import { mkdirSync, writeFileSync } from 'node:fs';
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
};

const HF_BASE = 'https://huggingface.co';
const DEFAULT_LIMIT = 120;
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

function computeScore(model: HfModel, sourceHits: number): number {
  const trend = Math.min((model.trendingScore ?? 0) / 800, 1);
  const downloads = normLog(model.downloads ?? 0, 8.5);
  const likes = normLog(model.likes ?? 0, 4.5);
  const recency = recencyScore(model.createdAt);
  const source = Math.min(sourceHits / 6, 1);
  return Number((0.34 * trend + 0.28 * downloads + 0.2 * likes + 0.1 * recency + 0.08 * source).toFixed(6));
}

async function fetchModels(url: string): Promise<HfModel[]> {
  const response = await fetch(url, {
    headers: {
      'User-Agent': 'chthonic-hf-ranker/1.0',
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

async function main() {
  const limit = toInt(argValue('limit'), DEFAULT_LIMIT);
  const outDir = argValue('out-dir') || path.join('codex', 'mailbox', 'cache');
  const mailboxDir = argValue('mailbox-dir') || path.join('codex', 'mailbox');
  const searchCsv = argValue('search');
  const searchTerms = searchCsv
    ? searchCsv.split(',').map((s) => s.trim()).filter(Boolean)
    : DEFAULT_SEARCH_TERMS;

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
        if (!id || model.private) continue;

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
      return {
        id,
        score: computeScore(model, sourcesForModel.length),
        downloads: model.downloads ?? 0,
        likes: model.likes ?? 0,
        trendingScore: model.trendingScore ?? 0,
        createdAt: model.createdAt,
        pipelineTag: model.pipeline_tag,
        libraryName: model.library_name,
        tags: model.tags ?? [],
        sources: sourcesForModel,
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

  const insert = db.prepare(`
    INSERT INTO hf_model_rankings (
      snapshot_id, captured_at, model_id, score, downloads, likes, trending_score,
      created_at, pipeline_tag, library_name, sources_json, tags_json
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
  md.push(`- DB: ${dbPath}`);
  md.push('');
  md.push('## Top Models');
  md.push('');
  md.push('| Rank | Model | Score | Trend | Downloads | Likes | Created | Sources |');
  md.push('|---|---|---:|---:|---:|---:|---|---:|');

  top.forEach((row, idx) => {
    md.push(
      `| ${idx + 1} | ${row.id} | ${row.score.toFixed(4)} | ${row.trendingScore} | ${row.downloads} | ${row.likes} | ${row.createdAt ?? 'n/a'} | ${row.sources.length} |`,
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
