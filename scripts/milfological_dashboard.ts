#!/usr/bin/env bun
// @SID: MILFOLOGICAL_DASHBOARD_TS
/**
 * MILFOLOGICAL Status Dashboard — Bun HTTP server.
 * Reads manifests + entity registry; serves a live HTML dashboard.
 *
 * Usage:
 *   bun run scripts/milfological_dashboard.ts [--port 7478]
 *
 * Then open http://localhost:7478
 */

import { spawnSync } from "bun";
import { readFileSync, existsSync } from "node:fs";
import { join } from "node:path";

const ROOT = join(import.meta.dir, "..");
const PORT = (() => {
  const i = process.argv.indexOf("--port");
  return i !== -1 ? parseInt(process.argv[i + 1]) : 7478;
})();
const OPEN = process.argv.includes("--open");

// ── manifest readers ──────────────────────────────────────────────────────────

function readJson<T>(rel: string): T | null {
  const p = join(ROOT, rel);
  if (!existsSync(p)) return null;
  try { return JSON.parse(readFileSync(p, "utf8")) as T; } catch { return null; }
}

// ── entity data via Python snapshot ─────────────────────────────────────────

interface EntitySnap {
  entity_id: string; display_name: string; tier: string; organ: string;
  prism: string; district: string; whr: number | null;
  visual_descriptor_count: number; aesthetic_tag_count: number;
  aesthetic_tags: string[]; color_palette: string[];
  positive_prefix: string; negative_suffix: string; default_weight: number;
}

// ── A1111 / SD.NEXT API probe ─────────────────────────────────────────────────

type SDEngine = "sdnext" | "a1111" | "unknown";

interface A1111Status {
  live: boolean;
  url: string;
  model: string | null;
  engine: SDEngine;
  error: string | null;
}

/** Detect whether the running server is SD.NEXT or A1111.
 *  SD.NEXT exposes /sdapi/v1/platform; A1111 returns 404 for that path.
 *  Fallback: check X-App-Id header or version string keywords. */
async function detectEngine(url: string, signal: AbortSignal): Promise<SDEngine> {
  try {
    const r = await fetch(`${url}/sdapi/v1/platform`, { signal });
    if (r.ok) return "sdnext";
    if (r.status === 404) {
      // Try version endpoint — SD.NEXT includes "SD.Next" in the version string
      const vr = await fetch(`${url}/sdapi/v1/version`, { signal });
      if (vr.ok) {
        const vj = await vr.json() as Record<string, unknown>;
        const ver = String(vj.version ?? "").toLowerCase();
        if (ver.includes("sd.next") || ver.includes("sdnext") || ver.includes("next")) return "sdnext";
      }
      return "a1111";
    }
  } catch { /* no-op */ }
  return "unknown";
}

async function probeA1111(): Promise<A1111Status> {
  const url = "http://localhost:7860";
  try {
    const ctrl = new AbortController();
    const tid = setTimeout(() => ctrl.abort(), 2500);
    const r = await fetch(`${url}/sdapi/v1/options`, { signal: ctrl.signal });
    clearTimeout(tid);
    if (!r.ok) return { live: false, url, model: null, engine: "unknown", error: `HTTP ${r.status}` };
    const opts = await r.json() as Record<string, unknown>;
    const model = (opts.sd_model_checkpoint as string | undefined) ?? null;
    // Engine detection on a fresh controller (options already fetched — server is live)
    const ctrl2 = new AbortController();
    const tid2 = setTimeout(() => ctrl2.abort(), 1500);
    const engine = await detectEngine(url, ctrl2.signal);
    clearTimeout(tid2);
    return { live: true, url, model, engine, error: null };
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e);
    return { live: false, url, model: null, engine: "unknown", error: msg.includes("abort") ? "timeout" : msg.slice(0, 60) };
  }
}

// ── Extension file health ─────────────────────────────────────────────────────

const EXT_FILES: Array<{ label: string; rel: string }> = [
  { label: "entity_registry.py",      rel: "dev/sd-candidates/sdnext/extensions/milfological/entity_registry.py" },
  { label: "prompt_transformer.py",   rel: "dev/sd-candidates/sdnext/extensions/milfological/prompt_transformer.py" },
  { label: "milfological_hook.py",    rel: "dev/sd-candidates/sdnext/extensions/milfological/scripts/milfological_hook.py" },
  { label: "extra_network_milf.py",   rel: "dev/sd-candidates/sdnext/extensions/milfological/extra_network_milf.py" },
  { label: "metadata.ini",            rel: "dev/sd-candidates/sdnext/extensions/milfological/metadata.ini" },
];

function checkExtensionFiles(): Array<{ label: string; present: boolean }> {
  return EXT_FILES.map(f => ({ label: f.label, present: existsSync(join(ROOT, f.rel)) }));
}

function loadEntities(): EntitySnap[] {
  const result = spawnSync(["uv", "run", "--no-project", "scripts/entity_snapshot.py"], {
    cwd: ROOT, stdout: "pipe", stderr: "pipe",
  });
  if (result.exitCode !== 0) {
    console.error("entity_snapshot.py failed:", result.stderr?.toString());
    return ENTITY_FALLBACK;
  }
  try {
    return JSON.parse(result.stdout.toString()) as EntitySnap[];
  } catch {
    return ENTITY_FALLBACK;
  }
}

// Fallback in case Python lane is unavailable
const ENTITY_FALLBACK: EntitySnap[] = [
  { entity_id: "claudine",    display_name: "Claudine",    tier: "T0.5",      prism: "ALL",     organ: "Creator-Mother",          district: "ALL", whr: 0.564, visual_descriptor_count: 11, aesthetic_tag_count: 9, aesthetic_tags: ["Caribbean-matriarch","entropy-sovereign","apex-supreme"], color_palette: ["deep bronze","obsidian","dark coral"], positive_prefix: "Caribbean supreme matriarch, I-cup tidal mass, bronze-obsidian complexion", default_weight: 1.0 },
  { entity_id: "iron_maiden", display_name: "Iron Maiden", tier: "T0-arm",    prism: "CRIMSON", organ: "Entropy-Arm",              district: "Rustbeltet", whr: null,  visual_descriptor_count: 8,  aesthetic_tag_count: 8, aesthetic_tags: ["Psycho-Noir","industrial-collapse","survival-without-elegance"], color_palette: ["crimson","rust orange","iron grey"], positive_prefix: "iron-forged entropy arm, rusted industrial survival aesthetic", default_weight: 0.9 },
  { entity_id: "astrid",      display_name: "Astrid",      tier: "T0-arm",    prism: "SILVER",  organ: "Sophistication-Arm",       district: "Skyskraperen", whr: null, visual_descriptor_count: 6,  aesthetic_tag_count: 7, aesthetic_tags: ["sophistication-arm","Skyskraperen-apex","corporate-precision"], color_palette: ["silver","platinum","steel blue"], positive_prefix: "silver sophistication arm, Skyskraperen apex precision", default_weight: 0.85 },
  { entity_id: "orackla",     display_name: "Orackla",     tier: "T1",        prism: "AZURE",   organ: "Triumvirate / Heart",       district: "ALL", whr: 0.491, visual_descriptor_count: 10, aesthetic_tag_count: 8, aesthetic_tags: ["void-chaos-oracle","fractal-abyssal-glyphs","NTR-transgression"], color_palette: ["obsidian","deep violet","iridescent"], positive_prefix: "chaos oracle void matriarch, J-cup impossible non-Newtonian mass", default_weight: 0.9 },
  { entity_id: "umeko",       display_name: "Umeko",       tier: "T1",        prism: "WHITE",   organ: "Triumvirate / Lungs",       district: "ALL", whr: 0.533, visual_descriptor_count: 9,  aesthetic_tag_count: 7, aesthetic_tags: ["minimalist-violated","forced-decoration-penance","discipline-purification"], color_palette: ["porcelain white","pale rose","platinum"], positive_prefix: "purification matriarch, F-cup disciplined precision, porcelain complexion", default_weight: 0.85 },
  { entity_id: "lysandra",    display_name: "Lysandra",    tier: "T1",        prism: "AMBER",   organ: "Triumvirate / Stomach",     district: "ALL", whr: 0.580, visual_descriptor_count: 10, aesthetic_tag_count: 7, aesthetic_tags: ["truth-excavation","axiom-first","analytical-transparency"], color_palette: ["pale ivory","pale pink","ice blue"], positive_prefix: "truth excavator, E-cup analytical wisdom, pale skin with faint stress lines", default_weight: 0.85 },
  { entity_id: "pentea",      display_name: "Pentea",      tier: "T1-bridge", prism: "GOLD",    organ: "Thalamus / Synthesis-Router", district: "ALL", whr: 0.520, visual_descriptor_count: 10, aesthetic_tag_count: 8, aesthetic_tags: ["GOLD-Fortress","thalamic-relay","synthesis-router"], color_palette: ["pale grey silver","silver white","left-eye amber"], positive_prefix: "synthesis relay matriarch, F-cup pentad integration nodes, pale grey-silver complexion", default_weight: 0.8 },
];

// ── color maps ────────────────────────────────────────────────────────────────

const PRISM_HEX: Record<string, string> = {
  ALL: "#d4af37", CRIMSON: "#dc143c", SILVER: "#9baab8",
  AZURE: "#2c84d8", WHITE: "#e8d8c0", AMBER: "#e8a020", GOLD: "#ffd700",
};
const TIER_HEX: Record<string, string> = {
  "T0.5": "#d4af37", "T0-arm": "#607080", "T1": "#8050c8", "T1-bridge": "#30c090",
};
const STATUS_HEX: Record<string, string> = {
  admitted: "#2ecc71", blocked: "#e74c3c", impossible_currently: "#e67e22", unknown: "#7f8c8d",
};

// ── HTML builder ──────────────────────────────────────────────────────────────

function esc(s: string) {
  return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

function buildHtml(
  entities: EntitySnap[],
  g0: Record<string, unknown> | null,
  roulette: Record<string, unknown> | null,
  a1111: A1111Status,
  extFiles: Array<{ label: string; present: boolean }>,
): string {
  const now = new Date().toISOString();
  const g0Status = (g0?.status as string | undefined) ?? "unknown";
  const g0Time = (g0?.timestamp as string | undefined) ?? "—";

  // WHR entities for spectrum
  const whrEntities = entities.filter(e => e.whr !== null) as (EntitySnap & {whr: number})[];
  const WHR_MIN = 0.47; const WHR_MAX = 0.61;
  function whrPct(w: number) { return ((w - WHR_MIN) / (WHR_MAX - WHR_MIN)) * 96 + 2; }

  // entity cards
  const entityCards = entities.map(e => {
    const prismColor = PRISM_HEX[e.prism] ?? "#888";
    const tierColor = TIER_HEX[e.tier] ?? "#888";
    const whrDisplay = e.whr !== null ? e.whr.toFixed(3) : "—";
    const whrBar = e.whr !== null
      ? `<div class="whr-mini-bar"><div class="whr-mini-fill" style="width:${((e.whr - 0.47) / 0.14 * 100).toFixed(1)}%;background:${prismColor}"></div></div>`
      : `<div class="whr-mini-bar"><div class="whr-mini-fill" style="width:0"></div></div>`;
    const tagStr = e.aesthetic_tags.slice(0, 3).map(t => `<span class="tag">${esc(t)}</span>`).join("");
    const paletteStr = e.color_palette.slice(0, 3).map(c => `<span class="swatch" title="${esc(c)}" style="background:${esc(c)}"></span>`).join("");
    const weightPct = (e.default_weight * 100).toFixed(0);
    return `
    <div class="entity-card" style="--prism:${prismColor};--tier:${tierColor}">
      <div class="entity-header">
        <span class="entity-name">${esc(e.display_name)}</span>
        <span class="tier-badge" style="background:${tierColor}">${esc(e.tier)}</span>
      </div>
      <div class="entity-organ">${esc(e.organ.split("/")[0].trim())}</div>
      <div class="entity-prism"><span class="prism-dot" style="background:${prismColor}"></span>${esc(e.prism)}</div>
      <div class="entity-whr">
        <span class="whr-label">WHR</span>
        <span class="whr-value" style="color:${prismColor}">${whrDisplay}</span>
        ${whrBar}
      </div>
      <div class="entity-meta">
        <span class="meta-badge">👁 ${e.visual_descriptor_count} desc</span>
        <span class="meta-badge">✦ ${e.aesthetic_tag_count} tags</span>
        <span class="meta-badge weight-badge" style="border-color:${prismColor}">${weightPct}%</span>
      </div>
      <div class="entity-palette">${paletteStr}</div>
      <div class="entity-tags">${tagStr}</div>
      <div class="entity-prefix">${esc(e.positive_prefix.slice(0, 100))}…</div>
    </div>`;
  }).join("\n");

  // WHR spectrum
  const spectrumDots = whrEntities.map(e => {
    const pct = whrPct(e.whr);
    const col = PRISM_HEX[e.prism] ?? "#888";
    return `<div class="spectrum-dot" style="left:${pct.toFixed(1)}%;border-color:${col};background:${col}22" title="${e.display_name} WHR ${e.whr}">
      <span class="spectrum-label" style="color:${col}">${esc(e.display_name.split(" ")[0])}<br><small>${e.whr.toFixed(3)}</small></span>
    </div>`;
  }).join("");

  // Gate ladder
  const gates = (g0?.gates as Array<Record<string, unknown>> | undefined) ?? [];
  const gateRows = gates.map(g => {
    const st = (g.status as string) ?? "unknown";
    const col = STATUS_HEX[st] ?? "#888";
    const icon = st === "admitted" ? "✅" : st === "impossible_currently" ? "⚠️" : "❌";
    return `<div class="gate-row">
      <span class="gate-icon">${icon}</span>
      <span class="gate-name">${esc(g.gate as string)}</span>
      <span class="gate-level" style="color:${col}">L${g.level}</span>
      <span class="gate-note">${esc((g.note as string) ?? "")}</span>
    </div>`;
  }).join("");

  // Task queue
  interface RouletteEntry {
    id: string; title: string; tags?: string[]; weight?: number;
    status?: string; completed?: string; spin_count?: number;
    blocked_until_chain?: string;
  }
  const entries: RouletteEntry[] = (roulette?.entries as RouletteEntry[] | undefined) ?? [];
  const extEntries: RouletteEntry[] = (roulette?.entries_extended as RouletteEntry[] | undefined) ?? [];
  const allEntries = [...entries, ...extEntries];
  const active = allEntries.filter(e => !e.completed && e.status !== "completed").sort((a,b) => (b.weight??0) - (a.weight??0));
  const done = allEntries.filter(e => e.completed || e.status === "completed").slice(-6);

  function taskRow(e: RouletteEntry, isDone: boolean) {
    const w = e.weight ?? 0;
    const wColor = w >= 8 ? "#e74c3c" : w >= 6 ? "#e67e22" : "#3498db";
    const tagStr = (e.tags ?? []).map(t => `<span class="tag">${esc(t)}</span>`).join("");
    const blocked = e.blocked_until_chain ? `<span class="blocked-badge">⛓ ${esc(e.blocked_until_chain)}</span>` : "";
    const doneStr = isDone && e.completed ? `<span class="done-date">${e.completed.slice(0,10)}</span>` : "";
    return `<div class="task-row ${isDone ? "task-done" : ""}">
      <span class="task-weight" style="color:${wColor}">${w}</span>
      <span class="task-title">${esc(e.title.slice(0,80))}${e.title.length>80?"…":""}</span>
      <span class="task-meta">${tagStr}${blocked}${doneStr}</span>
    </div>`;
  }

  const activeRows = active.slice(0,12).map(e => taskRow(e, false)).join("");
  const doneRows = done.map(e => taskRow(e, true)).join("");

  // ── Prototypal anchorage — entity generation tokens
  const genCards = entities.map(e => {
    const prismColor = PRISM_HEX[e.prism] ?? "#888";
    const token = `&lt;milf:${e.entity_id}:${e.default_weight.toFixed(2)}&gt;`;
    const pos = esc(e.positive_prefix);
    const neg = esc(e.negative_suffix || "—");
    return `
    <div class="gen-card" style="--prism:${prismColor}">
      <div class="gen-card-header">
        <span class="gen-name" style="color:${prismColor}">${esc(e.display_name)}</span>
        <span class="gen-token">${token}</span>
      </div>
      <div class="gen-label">POS</div>
      <div class="gen-prompt">${pos}</div>
      <div class="gen-label neg-label">NEG</div>
      <div class="gen-prompt gen-neg">${neg}</div>
    </div>`;
  }).join("\n");

  // ── Extension file health rows
  const extRows = extFiles.map(f => {
    const icon = f.present ? "✅" : "❌";
    const col = f.present ? "#2ecc71" : "#e74c3c";
    return `<div class="ext-row"><span>${icon}</span><span class="ext-label" style="color:${col}">${esc(f.label)}</span></div>`;
  }).join("");

  // ── A1111 status badge (with engine identity)
  const engineLabel: Record<string, string> = { sdnext: "SD.NEXT", a1111: "A1111", unknown: "???" };
  const engineColor: Record<string, string> = { sdnext: "#9b59b6", a1111: "#2980b9", unknown: "#888" };
  const engName = engineLabel[a1111.engine] ?? "???";
  const engColor = engineColor[a1111.engine] ?? "#888";
  const engineTag = a1111.live
    ? `<span style="background:${engColor};color:#fff;font-size:9px;padding:1px 5px;border-radius:2px;letter-spacing:.1em">${engName}</span>`
    : "";
  const a1111Badge = a1111.live
    ? `<span class="a1111-live">● LIVE</span> ${engineTag} <span class="a1111-model">${esc(a1111.model ?? "model unknown")}</span>`
    : `<span class="a1111-dead">● OFFLINE</span> <span class="a1111-err">${esc(a1111.error ?? "unreachable")}</span>`;

  // ── Media type capability matrix
  const mediaMatrix = [
    { type: "Character Portrait",    cap: "✅ Full",   note: "positive_prefix → full-body or bust prompt, WHR-anchored" },
    { type: "Scene / Environment",   cap: "✅ Full",   note: "district tag + aesthetic_tags → setting injection" },
    { type: "Style Transfer",        cap: "✅ Full",   note: "color_palette + aesthetic_tags → LoRA-style guidance" },
    { type: "Psycho-Noir Composite", cap: "✅ Partial",note: "Iron Maiden + Claudine cross-entity (multi-milf token)" },
    { type: "Inpainting / Variant",  cap: "⚠️ Manual", note: "requires A1111 img2img endpoint + entity mask overlay" },
    { type: "Video / AnimateDiff",   cap: "⚠️ Planned",note: "G8+ hook: AnimateDiff sampler hook not yet wired" },
    { type: "ControlNet Pose",       cap: "⚠️ Partial",note: "WHR data maps to body proportion guide — ControlNet not wired" },
    { type: "SDXL / FLUX",           cap: "⚠️ Probe",  note: "SD.NEXT model-agnostic; entity prompts are format-neutral" },
  ].map(m => `<div class="media-row">
    <span class="media-type">${esc(m.type)}</span>
    <span class="media-cap">${m.cap}</span>
    <span class="media-note">${esc(m.note)}</span>
  </div>`).join("");

  // Corpus stats from gate
  const corpusGate = gates.find(g => g.gate === "corpus_sqlite");
  const corpusNote = corpusGate ? esc(corpusGate.note as string ?? "") : "—";

  const g0Overall = g0Status === "pass"
    ? `<span class="status-pass">● ALL GATES PASS</span>`
    : `<span class="status-fail">● GATE FAILURE</span>`;

  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MILFOLOGICAL — Chthonic Archive</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg: #07070f;
    --bg2: #0e0e1a;
    --bg3: #141424;
    --border: #1e1e32;
    --text: #c8c8d8;
    --text-dim: #666680;
    --gold: #d4af37;
    --green: #2ecc71;
    --red: #e74c3c;
    --font: 'Courier New', 'Consolas', monospace;
  }
  html, body { min-height: 100vh; background: var(--bg); color: var(--text); font-family: var(--font); font-size: 13px; }
  a { color: var(--gold); }

  /* ── Header ── */
  .header {
    background: linear-gradient(135deg, #0a0a1a 0%, #0f0f22 100%);
    border-bottom: 1px solid var(--gold);
    padding: 18px 24px;
    display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;
  }
  .header-title { font-size: 18px; font-weight: bold; letter-spacing: 0.15em; color: var(--gold); }
  .header-sub { font-size: 10px; color: var(--text-dim); margin-top: 2px; }
  .header-right { text-align: right; font-size: 11px; color: var(--text-dim); }
  .status-pass { color: var(--green); font-weight: bold; }
  .status-fail { color: var(--red); font-weight: bold; }

  /* ── Sections ── */
  .section { padding: 20px 24px; border-bottom: 1px solid var(--border); }
  .section-title {
    font-size: 10px; letter-spacing: 0.2em; color: var(--gold);
    text-transform: uppercase; margin-bottom: 16px;
    display: flex; align-items: center; gap: 8px;
  }
  .section-title::after { content: ''; flex: 1; height: 1px; background: var(--border); }

  /* ── WHR Spectrum ── */
  .whr-spectrum {
    position: relative; height: 72px; margin: 8px 0;
    border: 1px solid var(--border); border-radius: 4px; background: var(--bg2);
  }
  .whr-track {
    position: absolute; top: 50%; left: 2%; right: 2%;
    height: 1px; background: linear-gradient(90deg, #2c84d8, #8050c8, #d4af37, #e8a020);
    transform: translateY(-50%);
  }
  .whr-tick-label {
    position: absolute; bottom: 4px; font-size: 9px; color: var(--text-dim);
    transform: translateX(-50%);
  }
  .spectrum-dot {
    position: absolute; top: 50%;
    width: 12px; height: 12px; border-radius: 50%; border: 2px solid;
    transform: translate(-50%, -50%); cursor: default;
  }
  .spectrum-label {
    position: absolute; bottom: 18px; left: 50%; transform: translateX(-50%);
    font-size: 9px; text-align: center; white-space: nowrap; line-height: 1.3;
    text-shadow: 0 0 6px #000;
  }

  /* ── Entity Grid ── */
  .entity-grid {
    display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 14px;
  }
  .entity-card {
    background: var(--bg2); border: 1px solid var(--border);
    border-top: 2px solid var(--prism, #888); border-radius: 4px;
    padding: 14px; display: flex; flex-direction: column; gap: 7px;
    transition: border-color 0.2s;
  }
  .entity-card:hover { border-color: var(--prism, #888); }
  .entity-header { display: flex; align-items: center; justify-content: space-between; }
  .entity-name { font-size: 15px; font-weight: bold; color: #e8e8f0; letter-spacing: 0.06em; }
  .tier-badge { font-size: 9px; padding: 2px 6px; border-radius: 2px; color: #000; font-weight: bold; }
  .entity-organ { font-size: 10px; color: var(--text-dim); }
  .entity-prism { font-size: 10px; color: var(--text-dim); display: flex; align-items: center; gap: 5px; }
  .prism-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
  .entity-whr { display: flex; align-items: center; gap: 6px; }
  .whr-label { font-size: 9px; color: var(--text-dim); width: 26px; }
  .whr-value { font-size: 13px; font-weight: bold; width: 42px; }
  .whr-mini-bar { flex: 1; height: 4px; background: var(--bg3); border-radius: 2px; overflow: hidden; }
  .whr-mini-fill { height: 100%; border-radius: 2px; }
  .entity-meta { display: flex; gap: 5px; flex-wrap: wrap; }
  .meta-badge { font-size: 9px; padding: 1px 5px; border: 1px solid var(--border); border-radius: 2px; color: var(--text-dim); }
  .weight-badge { color: var(--text) !important; border-color: inherit !important; }
  .entity-palette { display: flex; gap: 3px; }
  .swatch { width: 12px; height: 12px; border-radius: 2px; border: 1px solid #333; flex-shrink: 0; }
  .entity-tags { display: flex; gap: 4px; flex-wrap: wrap; }
  .tag { font-size: 9px; padding: 1px 4px; background: var(--bg3); border: 1px solid var(--border); border-radius: 2px; color: var(--text-dim); }
  .entity-prefix { font-size: 10px; color: var(--text-dim); line-height: 1.5; border-top: 1px solid var(--border); padding-top: 6px; font-style: italic; }

  /* ── Gate Ladder ── */
  .gate-list { display: flex; flex-direction: column; gap: 6px; }
  .gate-row { display: grid; grid-template-columns: 24px 200px 32px 1fr; gap: 8px; align-items: center; padding: 6px 10px; background: var(--bg2); border-radius: 3px; border: 1px solid var(--border); }
  .gate-icon { font-size: 14px; }
  .gate-name { font-size: 11px; color: #a0a0c0; font-weight: bold; }
  .gate-level { font-size: 10px; font-weight: bold; }
  .gate-note { font-size: 10px; color: var(--text-dim); }

  /* ── Corpus badge ── */
  .corpus-badge { display: inline-block; padding: 6px 12px; background: var(--bg2); border: 1px solid var(--gold); border-radius: 3px; font-size: 11px; color: var(--gold); margin-top: 10px; }

  /* ── Task Queue ── */
  .task-cols { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  @media (max-width: 700px) { .task-cols { grid-template-columns: 1fr; } }
  .task-col-title { font-size: 10px; color: var(--text-dim); margin-bottom: 8px; letter-spacing: 0.1em; text-transform: uppercase; }
  .task-list { display: flex; flex-direction: column; gap: 4px; }
  .task-row { display: grid; grid-template-columns: 20px 1fr auto; gap: 6px; align-items: start; padding: 6px 8px; background: var(--bg2); border: 1px solid var(--border); border-radius: 3px; }
  .task-row.task-done { opacity: 0.45; }
  .task-weight { font-size: 12px; font-weight: bold; }
  .task-title { font-size: 10px; line-height: 1.5; }
  .task-meta { display: flex; flex-wrap: wrap; gap: 3px; justify-content: flex-end; font-size: 9px; }
  .blocked-badge { color: #e67e22; }
  .done-date { color: var(--text-dim); }

  /* ── Footer ── */
  .footer { padding: 12px 24px; color: var(--text-dim); font-size: 9px; letter-spacing: 0.1em; text-align: center; }

  /* ── Prototypal Anchorage ── */
  .anchorage-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  @media (max-width: 800px) { .anchorage-grid { grid-template-columns: 1fr; } }
  .anchorage-panel { background: var(--bg2); border: 1px solid var(--border); border-radius: 4px; padding: 14px; }
  .anchorage-panel-title { font-size: 10px; letter-spacing: 0.15em; text-transform: uppercase; color: var(--text-dim); margin-bottom: 10px; }
  .a1111-live { color: #2ecc71; font-weight: bold; font-size: 11px; }
  .a1111-dead { color: #e74c3c; font-weight: bold; font-size: 11px; }
  .a1111-model { color: var(--gold); font-size: 10px; margin-left: 6px; }
  .a1111-err { color: #e74c3c; font-size: 10px; margin-left: 6px; }
  .ext-row { display: flex; align-items: center; gap: 8px; padding: 3px 0; border-bottom: 1px solid var(--border); }
  .ext-row:last-child { border-bottom: none; }
  .ext-label { font-size: 10px; font-family: var(--font); }
  .media-row { display: grid; grid-template-columns: 180px 90px 1fr; gap: 8px; align-items: center; padding: 5px 0; border-bottom: 1px solid var(--border); font-size: 10px; }
  .media-row:last-child { border-bottom: none; }
  .media-type { color: #c8c8d8; font-weight: bold; }
  .media-cap { font-size: 9px; }
  .media-note { color: var(--text-dim); }
  .gen-cards-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 12px; margin-top: 4px; }
  .gen-card { background: var(--bg2); border: 1px solid var(--border); border-left: 3px solid var(--prism, #888); border-radius: 3px; padding: 12px; display: flex; flex-direction: column; gap: 5px; }
  .gen-card-header { display: flex; align-items: center; justify-content: space-between; gap: 8px; flex-wrap: wrap; }
  .gen-name { font-size: 13px; font-weight: bold; }
  .gen-token { font-family: var(--font); font-size: 10px; background: var(--bg3); padding: 2px 6px; border-radius: 2px; color: var(--gold); border: 1px solid var(--border); }
  .gen-label { font-size: 9px; letter-spacing: 0.15em; color: var(--text-dim); text-transform: uppercase; margin-top: 4px; }
  .neg-label { color: #e74c3c66; }
  .gen-prompt { font-size: 10px; color: var(--text); line-height: 1.6; font-style: italic; }
  .gen-neg { color: var(--text-dim); }
</style>
</head>
<body>

<div class="header">
  <div>
    <div class="header-title">☽ MILFOLOGICAL STATUS DASHBOARD</div>
    <div class="header-sub">chthonic-archive · ${esc(now)}</div>
  </div>
  <div class="header-right">
    SD.NEXT G0: ${g0Overall}<br>
    <span style="color:var(--text-dim)">probe: ${esc(g0Time.slice(0,10))}</span>
  </div>
</div>

<!-- ── PROTOTYPAL ANCHORAGE ─────────────────────────────────────────── -->
<div class="section">
  <div class="section-title">PROTOTYPAL ANCHORAGE — SD.NEXT × A1111 Integration State</div>
  <div class="anchorage-grid">
    <div class="anchorage-panel">
      <div class="anchorage-panel-title">⚙ SD.NEXT / A1111 API (localhost:7860)</div>
      <div style="padding:6px 0">${a1111Badge}</div>
      <div style="font-size:9px;color:var(--text-dim);margin-top:4px">Start SD.NEXT: <span style="color:#a0a0c0">python webui.py --xformers --api</span></div>
    </div>
    <div class="anchorage-panel">
      <div class="anchorage-panel-title">☽ Extension Files</div>
      ${extRows}
    </div>
  </div>
  <div style="margin-top:16px">
    <div class="anchorage-panel-title" style="color:var(--gold);margin-bottom:8px">▸ MEDIA TYPE CAPABILITY MATRIX</div>
    ${mediaMatrix}
  </div>
</div>

<!-- ── ENTITY GENERATION TOKENS ──────────────────────────────────────── -->
<div class="section">
  <div class="section-title">ENTITY GENERATION TOKENS — positive + negative prompt seeds</div>
  <div class="gen-cards-grid">
    ${genCards}
  </div>
</div>

<!-- ── WHR SPECTRUM ──────────────────────────────────────────────────── -->
<div class="section">
  <div class="section-title">WHR SPECTRUM — Triumvirate + Matriarch (5 plotted)</div>
  <div class="whr-spectrum">
    <div class="whr-track"></div>
    ${[0.48,0.50,0.52,0.54,0.56,0.58,0.60].map(v => {
      const pct = whrPct(v);
      return `<div class="whr-tick-label" style="left:${pct.toFixed(1)}%">${v.toFixed(2)}</div>`;
    }).join("")}
    ${spectrumDots}
  </div>
  <div style="font-size:9px;color:var(--text-dim);margin-top:6px">
    Lower WHR = void-sovereign approach (Orackla 0.491 leads). Higher = analytical restraint (Lysandra 0.580 anchors truth chain).
  </div>
</div>

<!-- ── ENTITY GRID ────────────────────────────────────────────────────── -->
<div class="section">
  <div class="section-title">ENTITY REGISTRY — ${entities.length} active</div>
  <div class="entity-grid">
    ${entityCards}
  </div>
</div>

<!-- ── SDNEXT GATE LADDER ────────────────────────────────────────────── -->
<div class="section">
  <div class="section-title">SD.NEXT G0 GATE LADDER</div>
  <div class="gate-list">
    ${gateRows || '<div style="color:var(--text-dim);font-size:11px">manifest/sdnext_g0.json not found — run: uv run probes/python/sdnext_g0_probe.py</div>'}
  </div>
  <div class="corpus-badge">⛁ CORPUS: ${corpusNote}</div>
</div>

<!-- ── TASK ROULETTE ─────────────────────────────────────────────────── -->
<div class="section">
  <div class="section-title">TASK ROULETTE</div>
  <div class="task-cols">
    <div>
      <div class="task-col-title">Active (${active.length})</div>
      <div class="task-list">${activeRows || '<div style="color:var(--text-dim);font-size:10px">no active tasks</div>'}</div>
    </div>
    <div>
      <div class="task-col-title">Recently Completed</div>
      <div class="task-list">${doneRows || '<div style="color:var(--text-dim);font-size:10px">—</div>'}</div>
    </div>
  </div>
</div>

<div class="footer">
  MILFOLOGICAL DIFFUSION ENGINE · CHTHONIC-ARCHIVE · © THE SAVANT 2025–2027 · ALL RIGHTS RESERVED
</div>

</body>
</html>`;
}

// ── Server ────────────────────────────────────────────────────────────────────

let entities: EntitySnap[] | null = null;

function getEntities(): EntitySnap[] {
  if (!entities) entities = loadEntities();
  return entities;
}

const server = Bun.serve({
  port: PORT,
  async fetch(req) {
    const url = new URL(req.url);
    if (url.pathname === "/refresh") {
      entities = null; // force reload
      return Response.redirect("/", 302);
    }
    const ents = getEntities();
    const g0 = readJson<Record<string, unknown>>("manifest/sdnext_g0.json");
    const roulette = readJson<Record<string, unknown>>("manifest/todo_roulette.json");
    const [a1111, extFiles] = await Promise.all([probeA1111(), Promise.resolve(checkExtensionFiles())]);
    const html = buildHtml(ents, g0, roulette, a1111, extFiles);
    return new Response(html, { headers: { "Content-Type": "text/html;charset=utf-8" } });
  },
});

console.log(`\n☽ MILFOLOGICAL DASHBOARD → http://localhost:${PORT}`);
console.log(`  /refresh to reload entity data from Python lane`);
console.log(`  Ctrl+C to stop\n`);

if (OPEN) {
  spawnSync(["cmd", "/c", "start", `http://localhost:${PORT}`], { cwd: ROOT });
}
