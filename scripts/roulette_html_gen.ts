#!/usr/bin/env bun
// @SID: ROULETTE_HTML_GEN_V1

// ╔════════════════════════════════════════════════════════════════════════════
// ║ scripts/roulette_html_gen.ts
// ║
// ║ Generates docs/roulette.html — a self-contained Roulette POC dashboard.
// ║
// ║ Reads manifest/todo_roulette.json, computes live Euler scores, embeds
// ║ the data into a single-file HTML with an interactive spin wheel.
// ║
// ║ Usage:
// ║   bun run scripts/roulette_html_gen.ts
// ║   bun run scripts/roulette_html_gen.ts --open
// ╚════════════════════════════════════════════════════════════════════════════

import { readFileSync, writeFileSync, mkdirSync, existsSync } from "fs";
import { join } from "path";
import { execSync } from "child_process";

const ROOT = join(import.meta.dir, "..");
const MANIFEST_PATH = join(ROOT, "manifest", "todo_roulette.json");
const OUT_PATH = join(ROOT, "docs", "roulette.html");
const OPEN_FLAG = process.argv.includes("--open");

const KAPPA = 0.07;
const TAG_PHASE: Record<string, number> = {
  ssot:      0,
  entity:    Math.PI / 6,
  lore:      Math.PI / 3,
  infra:     Math.PI / 2,
  build:     (2 * Math.PI) / 3,
  ci:        (5 * Math.PI) / 6,
  game:      Math.PI,
  narrative: (7 * Math.PI) / 6,
  session:   (3 * Math.PI) / 2,
  handoff:   (5 * Math.PI) / 3,
  debt:      (11 * Math.PI) / 6,
  default:   Math.PI / 4,
};

const TAG_COLOR: Record<string, string> = {
  ssot:      "#c084fc",
  entity:    "#f472b6",
  lore:      "#fb923c",
  infra:     "#34d399",
  build:     "#60a5fa",
  ci:        "#a78bfa",
  game:      "#f87171",
  narrative: "#facc15",
  session:   "#2dd4bf",
  handoff:   "#e879f9",
  debt:      "#94a3b8",
  default:   "#6b7280",
};

interface TodoEntry {
  id: string;
  title: string;
  tags: string[];
  created: string;
  last_spun?: string;
  completed?: string;
  weight: number;
  origin: string;
  spin_count: number;
}

interface Manifest {
  version: string;
  created: string;
  last_spun?: string;
  total_spins: number;
  entries: TodoEntry[];
}

function stalenessDays(entry: TodoEntry): number {
  const ref = entry.last_spun ?? entry.created;
  return (Date.now() - new Date(ref).getTime()) / 86400000;
}

function primaryTag(entry: TodoEntry): string {
  return entry.tags[0] ?? "default";
}

function eulerScore(entry: TodoEntry): number {
  const s = stalenessDays(entry);
  const phi = TAG_PHASE[primaryTag(entry)] ?? TAG_PHASE.default;
  return entry.weight * Math.exp(KAPPA * s) * 0.5 * (1 + Math.sin(phi));
}

function polarDisplay(entry: TodoEntry): string {
  const phi = TAG_PHASE[primaryTag(entry)] ?? TAG_PHASE.default;
  const deg = ((phi * 180) / Math.PI).toFixed(0);
  const score = eulerScore(entry).toFixed(2);
  return `${score} ∠ ${deg}°`;
}

function loadManifest(): Manifest {
  if (!existsSync(MANIFEST_PATH)) {
    console.error(`Manifest not found: ${MANIFEST_PATH}`);
    process.exit(1);
  }
  return JSON.parse(readFileSync(MANIFEST_PATH, "utf8")) as Manifest;
}

function getGitLog(): string {
  try {
    return execSync('git log --oneline -8', { cwd: ROOT, encoding: "utf8" }).trim();
  } catch { return "(git unavailable)"; }
}

function buildHtml(manifest: Manifest, gitLog: string): string {
  const active = manifest.entries.filter(e => !e.completed);
  const completed = manifest.entries.filter(e => !!e.completed);
  const scored = active.map(e => ({ entry: e, score: eulerScore(e), polar: polarDisplay(e) }))
    .sort((a, b) => b.score - a.score);
  const totalScore = scored.reduce((sum, s) => sum + s.score, 0);

  // SVG wheel data
  const segments = scored.map((s, i) => ({
    ...s,
    pct: s.score / totalScore,
    color: TAG_COLOR[primaryTag(s.entry)] ?? TAG_COLOR.default,
    idx: i,
  }));

  // Build SVG arcs
  const cx = 200, cy = 200, r = 180;
  let svgArcs = "";
  let cumAngle = -Math.PI / 2; // start top
  for (const seg of segments) {
    const sweep = seg.pct * 2 * Math.PI;
    const x1 = cx + r * Math.cos(cumAngle);
    const y1 = cy + r * Math.sin(cumAngle);
    const x2 = cx + r * Math.cos(cumAngle + sweep);
    const y2 = cy + r * Math.sin(cumAngle + sweep);
    const large = sweep > Math.PI ? 1 : 0;
    const midAngle = cumAngle + sweep / 2;
    const labelR = r * 0.65;
    const lx = cx + labelR * Math.cos(midAngle);
    const ly = cy + labelR * Math.sin(midAngle);
    const truncTitle = seg.entry.title.length > 22
      ? seg.entry.title.slice(0, 20) + "…"
      : seg.entry.title;
    svgArcs += `<path d="M${cx},${cy} L${x1.toFixed(2)},${y1.toFixed(2)} A${r},${r} 0 ${large},1 ${x2.toFixed(2)},${y2.toFixed(2)} Z" fill="${seg.color}" fill-opacity="0.85" stroke="#0f172a" stroke-width="1.5" data-idx="${seg.idx}" class="wheel-seg"/>`;
    if (seg.pct > 0.05) {
      svgArcs += `<text x="${lx.toFixed(2)}" y="${ly.toFixed(2)}" text-anchor="middle" dominant-baseline="middle" font-size="9" fill="#f1f5f9" font-family="monospace" transform="rotate(${((midAngle * 180) / Math.PI + 90).toFixed(1)},${lx.toFixed(2)},${ly.toFixed(2)})">${truncTitle}</text>`;
    }
    cumAngle += sweep;
  }

  // Rows
  const rows = scored.map((s, i) => {
    const tag = primaryTag(s.entry);
    const color = TAG_COLOR[tag] ?? TAG_COLOR.default;
    const days = stalenessDays(s.entry).toFixed(1);
    const staleBadge = parseFloat(days) > 5
      ? `<span style="color:#f87171;font-size:10px">⚑ ${days}d</span>`
      : `<span style="color:#64748b;font-size:10px">${days}d</span>`;
    return `<tr data-idx="${i}" class="task-row" onclick="selectTask(${i})">
      <td style="padding:6px 8px;color:${color};font-weight:700">${i + 1}</td>
      <td style="padding:6px 8px;max-width:340px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${s.entry.title}</td>
      <td style="padding:6px 8px;font-family:monospace;color:#a5b4fc">${s.polar}</td>
      <td style="padding:6px 8px">${staleBadge}</td>
      <td style="padding:6px 8px"><span style="background:${color}22;color:${color};padding:2px 6px;border-radius:4px;font-size:11px">${tag}</span></td>
      <td style="padding:6px 8px;color:#64748b;font-size:11px">w${s.entry.weight} · ${s.entry.spin_count}×</td>
    </tr>`;
  }).join("\n");

  const gitLines = gitLog.split("\n").map(l => `<div style="margin:2px 0;font-size:11px;color:#94a3b8">${l}</div>`).join("");

  const manifestJson = JSON.stringify({ scored: scored.map(s => ({ id: s.entry.id, title: s.entry.title, score: s.score, tag: primaryTag(s.entry), color: TAG_COLOR[primaryTag(s.entry)] ?? TAG_COLOR.default })), totalScore }, null, 2);

  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Chthonic Roulette — Eulian TODO Engine</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg: #0a0f1a;
    --surface: #111827;
    --border: #1e293b;
    --text: #e2e8f0;
    --muted: #64748b;
    --accent: #a78bfa;
    --gold: #f59e0b;
    --win: #10b981;
  }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Segoe UI', system-ui, sans-serif;
    min-height: 100vh;
    padding: 24px;
  }
  h1 { font-size: 22px; font-weight: 700; color: var(--accent); letter-spacing: 0.5px; }
  h2 { font-size: 14px; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
  .header { display: flex; align-items: baseline; gap: 16px; margin-bottom: 24px; border-bottom: 1px solid var(--border); padding-bottom: 16px; }
  .header .meta { font-size: 12px; color: var(--muted); }
  .layout { display: grid; grid-template-columns: 420px 1fr; gap: 24px; align-items: start; }
  .wheel-panel { display: flex; flex-direction: column; align-items: center; gap: 16px; }
  #wheel-svg { filter: drop-shadow(0 0 18px #a78bfa33); cursor: pointer; }
  .wheel-seg { transition: filter 0.15s; }
  .wheel-seg:hover { filter: brightness(1.3); }
  #spin-btn {
    background: linear-gradient(135deg, #7c3aed, #4f46e5);
    color: #fff;
    border: none;
    padding: 10px 32px;
    font-size: 16px;
    font-weight: 700;
    border-radius: 8px;
    cursor: pointer;
    letter-spacing: 1px;
    transition: transform 0.1s, box-shadow 0.1s;
    box-shadow: 0 0 16px #7c3aed55;
  }
  #spin-btn:hover { transform: scale(1.04); box-shadow: 0 0 28px #7c3aed88; }
  #spin-btn:active { transform: scale(0.98); }
  #spin-btn.spinning { animation: pulse 0.4s infinite alternate; }
  @keyframes pulse { from { box-shadow: 0 0 16px #7c3aed55; } to { box-shadow: 0 0 40px #c084fccc; } }
  #winner-panel {
    min-height: 72px;
    width: 100%;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px 16px;
    transition: border-color 0.3s;
  }
  #winner-panel.has-winner { border-color: var(--win); }
  #winner-title { font-size: 15px; font-weight: 700; color: var(--win); margin-bottom: 4px; }
  #winner-meta { font-size: 12px; color: var(--muted); font-family: monospace; }
  #winner-convergence { font-size: 11px; color: #fbbf24; margin-top: 8px; }
  .right-panel { display: flex; flex-direction: column; gap: 20px; }
  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px;
  }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  thead th { padding: 6px 8px; text-align: left; color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid var(--border); }
  tbody tr { border-bottom: 1px solid #0f172a; transition: background 0.15s; }
  tbody tr:hover { background: #1e293b; }
  tbody tr.selected { background: #1e3a5f; }
  .git-log { font-family: monospace; }
  .closed-count { font-size: 12px; color: var(--muted); }
  #needle { transform-origin: 200px 200px; transition: transform 2.5s cubic-bezier(0.17,0.67,0.12,0.99); pointer-events: none; }
  .stats-row { display: flex; gap: 16px; font-size: 12px; color: var(--muted); }
  .stat { display: flex; flex-direction: column; align-items: center; gap: 2px; }
  .stat-val { font-size: 20px; font-weight: 700; color: var(--text); font-variant-numeric: tabular-nums; }
  @media (max-width: 900px) { .layout { grid-template-columns: 1fr; } }
</style>
</head>
<body>

<div class="header">
  <h1>⚡ Chthonic Roulette</h1>
  <span class="meta">Eulian TODO Engine · v1 · manifest/todo_roulette.json</span>
  <span class="meta" style="margin-left:auto">Generated: ${new Date().toISOString().slice(0,16).replace("T", " ")}</span>
</div>

<div class="layout">
  <div class="wheel-panel">
    <svg id="wheel-svg" width="400" height="400" viewBox="0 0 400 400">
      ${svgArcs}
      <!-- needle -->
      <g id="needle">
        <polygon points="200,22 196,56 204,56" fill="#f59e0b" stroke="#0a0f1a" stroke-width="1"/>
        <circle cx="200" cy="200" r="10" fill="#0a0f1a" stroke="#f59e0b" stroke-width="2"/>
      </g>
    </svg>

    <div class="stats-row">
      <div class="stat"><div class="stat-val">${active.length}</div><div>open</div></div>
      <div class="stat"><div class="stat-val">${completed.length}</div><div>closed</div></div>
      <div class="stat"><div class="stat-val">${manifest.total_spins}</div><div>spins</div></div>
      <div class="stat"><div class="stat-val">${totalScore.toFixed(0)}</div><div>total Σ</div></div>
    </div>

    <button id="spin-btn" onclick="spin()">⟳ SPIN</button>

    <div id="winner-panel">
      <div style="color:var(--muted);font-size:13px">Press SPIN to select the next Roulette Σ-item.</div>
    </div>
  </div>

  <div class="right-panel">
    <div class="card">
      <h2>Active tasks — ranked by Euler score</h2>
      <table>
        <thead><tr>
          <th>#</th><th>Title</th><th>score ∠ φ°</th><th>Age</th><th>Tag</th><th>Meta</th>
        </tr></thead>
        <tbody id="task-tbody">
          ${rows}
        </tbody>
      </table>
    </div>

    <div class="card git-log">
      <h2>Recent commits</h2>
      ${gitLines}
    </div>
  </div>
</div>

<script>
const DATA = ${manifestJson};

const CONVERGENCE_TEMPLATES = {
  ssot: (t) => \`¬missing_§10.3(\${t.slice(0,20)}) ∧ hash_verified\`,
  entity: (t) => \`entity_profile_modern ∧ §10.3_format_complete\`,
  lore: (t) => \`lore_loaded ∧ ∀m: m.spectral≠∅\`,
  infra: (t) => \`artifact_exists ∧ cargo_check_clean\`,
  build: (t) => \`binary_builds ∧ ¬patch_required\`,
  ci: (t) => \`gates_admitted ∧ exit_0\`,
  game: (t) => \`scene_renders ∧ entity_visible\`,
  narrative: (t) => \`arc_committed ∧ voice_trace_present\`,
  debt: (t) => \`deprecated_artifact_removed ∧ canonical_path_active\`,
  default: (t) => \`artifact_exists ∧ convergence_defined\`,
};

let currentWinnerIdx = null;

function selectTask(idx) {
  document.querySelectorAll('.task-row').forEach(r => r.classList.remove('selected'));
  const row = document.querySelector(\`[data-idx="\${idx}"]\`);
  if (row) row.classList.add('selected');
  showWinner(idx);
}

function showWinner(idx) {
  const item = DATA.scored[idx];
  if (!item) return;
  currentWinnerIdx = idx;
  const panel = document.getElementById('winner-panel');
  const tmpl = CONVERGENCE_TEMPLATES[item.tag] ?? CONVERGENCE_TEMPLATES.default;
  panel.classList.add('has-winner');
  panel.innerHTML = \`
    <div id="winner-title">Σ-0: \${item.title}</div>
    <div id="winner-meta">score \${item.score.toFixed(2)} · tag:\${item.tag} · id:\${item.id}</div>
    <div id="winner-convergence">Convergence: \${tmpl(item.title)}</div>
  \`;
  // Highlight wheel segment
  document.querySelectorAll('.wheel-seg').forEach(seg => {
    seg.style.filter = seg.dataset.idx == idx ? 'brightness(1.6) drop-shadow(0 0 8px #f59e0b)' : 'brightness(0.5)';
  });
}

function spin() {
  const btn = document.getElementById('spin-btn');
  btn.classList.add('spinning');
  btn.disabled = true;

  // Reset segments
  document.querySelectorAll('.wheel-seg').forEach(seg => { seg.style.filter = ''; });

  // Pick winner by weighted random
  const total = DATA.totalScore;
  let r = Math.random() * total;
  let winIdx = DATA.scored.length - 1;
  for (let i = 0; i < DATA.scored.length; i++) {
    r -= DATA.scored[i].score;
    if (r <= 0) { winIdx = i; break; }
  }

  // Compute needle target angle
  // segments are in order; find midpoint angle of winner
  let cumPct = 0;
  for (let i = 0; i < winIdx; i++) cumPct += DATA.scored[i].score / total;
  const winPct = DATA.scored[winIdx].score / total;
  const midPct = cumPct + winPct / 2;
  // needle starts at top (0deg = -90deg in SVG), spins clockwise
  // to land at midPct of wheel, needle must rotate to point at midPct * 360
  // but wheel is fixed and needle rotates — so spin at least 3 full revolutions + target
  const targetDeg = 360 * 3 + (midPct * 360);
  const needle = document.getElementById('needle');
  needle.style.transform = \`rotate(\${targetDeg}deg)\`;

  setTimeout(() => {
    btn.classList.remove('spinning');
    btn.disabled = false;
    selectTask(winIdx);
  }, 2700);
}
</script>

</body>
</html>`;
}

// ── Main ──────────────────────────────────────────────────────────────────────

const manifest = loadManifest();
const gitLog = getGitLog();
const html = buildHtml(manifest, gitLog);

if (!existsSync(join(ROOT, "docs"))) mkdirSync(join(ROOT, "docs"), { recursive: true });
writeFileSync(OUT_PATH, html, "utf8");

const active = manifest.entries.filter(e => !e.completed).length;
console.log(`✅ docs/roulette.html generated (${active} active tasks)`);
console.log(`   Open: ${OUT_PATH}`);

if (OPEN_FLAG) {
  try {
    execSync(`Start-Process "${OUT_PATH}"`, { shell: "pwsh", cwd: ROOT });
  } catch {
    execSync(`Invoke-Item "${OUT_PATH}"`, { shell: "pwsh", cwd: ROOT });
  }
}
