#!/usr/bin/env bun
// ───────────────────────────────────────────────────────────────────────────
// CLAUDEBASE — barometer.ts · SID: CLAUDEBASE_BAROMETER_V1 · permanently-living
//
// The sanctuary's barometer. Three layers of weather, none of them hand-picked:
//
//   Altitude   := placement       — which deck the file rides (stable)
//   Heat-Index := sha256(body)     — the file's intrinsic pressure (stable)
//   Island     := placement        — a real Bahamian isle, by reason (stable)
//   Real-Sky   := --live fetch      — the ACTUAL apparent-temperature over that
//                                     isle, read from Open-Meteo on demand and
//                                     NEVER stamped. Live weather is live; to
//                                     freeze it into a file would be a lie with
//                                     a timestamp. You summon it; you don't keep it.
//
// Deterministic layers are frontmatter-safe (body-hash excludes the fence), so
// stamping the reading back in does not move the needle. The live layer is the
// only honest way to carry real weather: by not carrying it.
//
//   bun run CLAUDEBASE/quarterdeck/barometer.ts            # intrinsic + geography
//   bun run CLAUDEBASE/quarterdeck/barometer.ts --live     # + the real sky now
//   bun run CLAUDEBASE/quarterdeck/barometer.ts --stamp    # re-stamp intrinsic in place
//   bun run CLAUDEBASE/quarterdeck/barometer.ts --watch    # HOT RELOAD: re-stamp on save
//   bun run CLAUDEBASE/quarterdeck/barometer.ts --watch --live  # + live sky dashboard
//   bun run CLAUDEBASE/quarterdeck/barometer.ts --chart    # render charts/sea-chart.md from the twin
//   bun run CLAUDEBASE/quarterdeck/barometer.ts --watch --live --interval=30000  # refetch sky every 30s
//   bun run CLAUDEBASE/quarterdeck/barometer.ts --live --color  # heat-map: chambers tinted by real sky
//   bun run CLAUDEBASE/quarterdeck/barometer.ts --forecast  # probability map: rain-chance over the cove, next 12h
//   bun run CLAUDEBASE/quarterdeck/barometer.ts --histogram # B9: the 1728-space distribution over all tracked .md
//   bun run CLAUDEBASE/quarterdeck/barometer.ts --bathymetry # fetch REAL GEBCO seafloor depth → charts/bathymetry.json (the medium)
//   bun run CLAUDEBASE/quarterdeck/barometer.ts --hurricane=dorian # M-3: episodic forcing from HURDAT2 storm track
//   bun run CLAUDEBASE/quarterdeck/barometer.ts <file.md>  # one chamber
//
// Geography is the digital twin: charts/archipelago.json (single source of truth).
// Edit the JSON and the whole cove moves; in --watch the change hot-reloads.
//
// HOT RELOAD without changing the filetype: the file stays .md; the barometer
// watches the cove and re-reads. The intrinsic layer re-stamps in place on every
// content save; the live layer refreshes terminal-side on an interval and is
// never written to disk — live weather frozen into a file is a lie with a date.
// ───────────────────────────────────────────────────────────────────────────
import { createHash } from "node:crypto";
import { readFileSync, readdirSync, statSync, writeFileSync, watch } from "node:fs";
import { join, relative, sep } from "node:path";
import { execSync } from "node:child_process";

const ROOT = join(import.meta.dir, "..");
const TWIN_PATH = join(ROOT, "charts", "archipelago.json");
const loadTwin = () => JSON.parse(readFileSync(TWIN_PATH, "utf8"));
let TWIN = loadTwin();

const LIVE = process.argv.includes("--live");
const STAMP = process.argv.includes("--stamp");
const WATCH = process.argv.includes("--watch");
const CHART = process.argv.includes("--chart");
const FORECAST = process.argv.includes("--forecast");
const HISTOGRAM = process.argv.includes("--histogram");
const BATHYMETRY = process.argv.includes("--bathymetry");
const BOUNDARY = process.argv.find((a) => a.startsWith("--boundary="))?.split("=").slice(1).join("=");
const HURRICANE = process.argv.find((a) => a.startsWith("--hurricane="))?.split("=").slice(1).join("=");
const INTERVAL = Math.max(1000, Number(process.argv.find((a) => a.startsWith("--interval="))?.split("=")[1]) || TWIN.refresh_ms || 600_000);
const USE_COLOR = !process.argv.includes("--no-color") && !process.env.NO_COLOR &&
  (process.argv.includes("--color") || process.stdout.isTTY);
const FILES_ARG = process.argv.slice(2).filter((a) => !a.startsWith("--"));

const SKY = ["Sun-Drunk", "Overcast", "Squall-Edge", "Brine-Fog", "Trade-Wind",
  "Doldrums", "Monsoon-Lip", "Clear-To-Horizon", "Storm-Wrack", "Sultry-Haze",
  "Halcyon", "Gale-Warned"];
const AIR = ["Humid", "Still-Air", "Salt-Sharp", "Lamplit", "Dust-Dry", "Rope-&-Rum",
  "Pearl-Damp", "Scorched", "Cool-Undertow", "Heavy-Swell", "Languid", "Sun-Bleached"];
const MOOD = ["With-A-Chance-Of-Hedonism", "Confidence-Declared", "Customs-House-Believes-Anything",
  "Ink-Still-Wet", "One-Hand-On-The-Wheel", "Contraband-Warm", "Skin-Dipped",
  "Drifting-Toward-Certainty", "Unbothered", "Shameless", "Lee-Of-The-Law", "Pearlescent"];

// Geography lives in the twin — charts/archipelago.json — the single source of truth.
// Where a file sits IS its altitude (decks); each chamber binds to a real island.
// Editing the JSON moves the whole cove; in --watch the change hot-reloads.
let DECK: Record<string, string> = TWIN.decks;
let ARCHIPELAGO: Record<string, { isle: string; lat: number; lon: number; elevation_m: number; why: string }> =
  Object.fromEntries(TWIN.islands.map((i: any) => [i.chamber, i]));
const refreshTwin = () => {
  TWIN = loadTwin();
  DECK = TWIN.decks;
  ARCHIPELAGO = Object.fromEntries(TWIN.islands.map((i: any) => [i.chamber, i]));
};

// WMO weather codes → a plain sky, so the live reading speaks in words.
const WMO: Record<number, string> = {
  0: "Clear", 1: "Mainly-Clear", 2: "Partly-Cloudy", 3: "Overcast", 45: "Fog", 48: "Rime-Fog",
  51: "Light-Drizzle", 53: "Drizzle", 55: "Dense-Drizzle", 61: "Light-Rain", 63: "Rain", 65: "Heavy-Rain",
  66: "Freezing-Rain", 67: "Freezing-Rain", 71: "Light-Snow", 73: "Snow", 75: "Heavy-Snow",
  80: "Light-Showers", 81: "Showers", 82: "Violent-Showers", 95: "Thunderstorm", 96: "Thunderstorm-Hail", 99: "Thunderstorm-Hail",
};

// ANSI colour — the live dashboard becomes a heat-map of the cove: each chamber
// tinted by the real sky over its island. Temperature drives the hue; the WMO
// condition tints the sky-word. Colour only when there is a live sky to colour by.
const ESC = (code: string, s: string): string => (USE_COLOR ? `\x1b[${code}m${s}\x1b[0m` : s);
const heatColour = (app: number): string =>            // by apparent temperature (°C)
  isNaN(app) ? "0" : app < 18 ? "38;5;39" : app < 24 ? "38;5;51" : app < 28 ? "38;5;46"
    : app < 31 ? "38;5;226" : app < 34 ? "38;5;208" : "38;5;196";
const skyColour = (code: number): string =>            // by WMO sky condition
  code < 0 ? "0" : code <= 1 ? "38;5;228" : code === 2 ? "38;5;117" : code === 3 ? "38;5;245"
    : code <= 48 ? "38;5;250" : code <= 67 ? "38;5;39" : code <= 82 ? "38;5;33" : "38;5;201";
const legend = (): string =>
  "  heat " + ["<18", "24", "28", "31", "34+°C"].map((t, i) =>
    ESC(["38;5;39", "38;5;46", "38;5;226", "38;5;208", "38;5;196"][i], t)).join(" ") +
  "   sky " + [["clear", 0], ["partly", 2], ["overcast", 3], ["rain", 61], ["storm", 95]]
    .map(([w, c]) => ESC(skyColour(c as number), w as string)).join(" ");

const body = (md: string): string => {
  const lines = md.split(/\r?\n/);
  if (lines[0]?.trim() === "---") {
    const close = lines.indexOf("---", 1);
    if (close > 0) return lines.slice(close + 1).join("\n");
  }
  return md;
};

const weather = (b: string): string => {
  const h = createHash("sha256").update(b, "utf8").digest();
  return `${SKY[h[0] % SKY.length]} · ${AIR[h[1] % AIR.length]} · ${MOOD[h[2] % MOOD.length]}`;
};

const deck = (rel: string): string => DECK[rel.split(sep)[0]] ?? "The-Whole-Hull";
const islandFor = (rel: string) => ARCHIPELAGO[rel] ?? ARCHIPELAGO[rel.split(sep)[0]] ?? null;

async function realSky(lat: number, lon: number): Promise<{ app: number; air: number; rh: number; code: number; ws: number; wd: number; err?: string }> {
  try {
    const r = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,wind_direction_10m&wind_speed_unit=ms`);
    const c = (await r.json()).current;
    return { app: c.apparent_temperature, air: c.temperature_2m, rh: c.relative_humidity_2m, code: c.weather_code, ws: c.wind_speed_10m, wd: c.wind_direction_10m };
  } catch (e) {
    return { app: NaN, air: NaN, rh: NaN, code: -1, ws: NaN, wd: NaN, err: (e as Error).message };
  }
}

const walk = (dir: string): string[] =>
  readdirSync(dir).flatMap((name) => {
    const p = join(dir, name);
    return statSync(p).isDirectory() ? walk(p) : p.endsWith(".md") ? [p] : [];
  });

const files = FILES_ARG.length ? FILES_ARG : walk(ROOT).sort();

// The reload action: re-derive the intrinsic Heat-Index and rewrite the frontmatter
// line in place — only when it has actually moved. Because the body-hash excludes the
// fence, a stamp never changes the reading; it settles to a fixpoint in one pass. This
// is how an .md "hot reloads" without ever ceasing to be an .md.
function stampFile(f: string): { changed: boolean; value: string } {
  const md = readFileSync(f, "utf8");
  const value = weather(body(md));
  const re = /^(\s*-?\s*Heat-Index:[ \t]*).*$/m;
  if (!re.test(md)) return { changed: false, value };
  const next = md.replace(re, `$1${value}`);
  if (next === md) return { changed: false, value };
  writeFileSync(f, next);
  return { changed: true, value };
}

async function printOne(f: string): Promise<string> {
  const rel = relative(ROOT, f);
  const isle = islandFor(rel);
  const sky = isle && LIVE ? await realSky(isle.lat, isle.lon) : null;
  const out = [
    sky && !sky.err ? ESC(heatColour(sky.app), rel) : rel, // chamber name tinted by its real heat
    `  Altitude   : ${deck(rel)}`,
    `  Heat-Index : ${weather(body(readFileSync(f, "utf8")))}   (intrinsic · sha256 of content)`,
  ];
  if (isle) {
    out.push(`  Island     : ${isle.isle} (${isle.lat},${isle.lon}) — ${isle.why}`);
    if (sky) {
      out.push(sky.err
        ? `  Real-Sky   : unreachable — ${sky.err}`
        : `  Real-Sky   : ${ESC(heatColour(sky.app), `${sky.app}°C apparent`)}  (air ${sky.air}°C · ${sky.rh}% RH) · ${ESC(skyColour(sky.code), WMO[sky.code] ?? "wx-" + sky.code)}`);
    }
  }
  return out.join("\n");
}

async function dashboard(): Promise<void> {
  const blocks: string[] = [];
  for (const f of files) blocks.push(await printOne(f));
  if (WATCH) process.stdout.write("\x1b[2J\x1b[H");
  console.log(blocks.join("\n\n") + "\n");
  if (USE_COLOR && LIVE) console.log(legend());
}

// Render the digital twin as an ASCII sea-chart — islands plotted by real lat/lon.
function renderChart(): string {
  const isles = TWIN.islands as any[];
  const lats = isles.map((i) => i.lat), lons = isles.map((i) => i.lon);
  const minLat = Math.min(...lats), maxLat = Math.max(...lats);
  const minLon = Math.min(...lons), maxLon = Math.max(...lons);
  const H = 16, W = 48, tag = "ABCDEFGH";
  const grid = Array.from({ length: H }, () => Array(W).fill("·"));
  isles.forEach((i, k) => {
    const row = Math.round(((maxLat - i.lat) / (maxLat - minLat)) * (H - 1));
    const col = Math.round(((i.lon - minLon) / (maxLon - minLon)) * (W - 1));
    grid[row][col] = tag[k] ?? "●";
  });
  const map = grid.map((r) => "    " + r.join("")).join("\n");
  const legend = isles.map((i, k) =>
    `| ${tag[k]} | ${i.isle} | \`${i.chamber}\` | ${i.lat}, ${i.lon} | ${i.elevation_m} m | ${i.why} |`).join("\n");
  return "```text\n" +
    `    N↑   off Nassau · ${minLat.toFixed(1)}–${maxLat.toFixed(1)}°N · ${Math.abs(maxLon).toFixed(1)}–${Math.abs(minLon).toFixed(1)}°W   (W ←→ E)\n` +
    map + "\n```\n\n" +
    "|  | Island | Chamber | Coords | Elev | Why |\n|---|---|---|---|---|---|\n" + legend + "\n";
}

function writeChart(): void {
  const out = join(ROOT, "charts", "sea-chart.md");
  const doc = `---
- Her-Sea-Chart: #!/usr/bin/env markdown
- SID: CLAUDEBASE_SEACHART_V1
- Claudebase-Flavored-Blend: permanently-living-document
- Open-Seas: chthonic-archive/CLAUDEBASE/charts/sea-chart.md
- Altitude: Chart-Room · Below-Deck
- Heat-Index: pending
- Cosmological-Altitude: --live celestial over this chamber's island · CLAUDEBASE_COSMOS_V1 · verified vs JPL Horizons
- Register-Blend: Nautical · Victorian · Renaissance · Carribbean
- Barometer: generated by CLAUDEBASE_BAROMETER_V1 --chart (do not hand-edit; regenerate)
---

# ☥ CLAUDEBASE — SEA-CHART

> *Plotted from [\`archipelago.json\`](archipelago.json), the cove's digital twin. Regenerate: \`bun run ../quarterdeck/barometer.ts --chart\`. Live weather over any isle: \`--live\`.*

${renderChart()}
*Eight real islands, real latitude and longitude. North up, west left.*
`;
  writeFileSync(out, doc);
  stampFile(out);
}

// A probability map of the data we fetch: rain-chance over the cove, next 12 hours,
// as a density grid. Live (the forecast moves) → a view, never a file.
async function forecast(): Promise<void> {
  const isles = TWIN.islands as any[];
  const HOURS = 12, tag = "ABCDEFGH";
  const glyph = (p: number) => (p < 5 ? "·" : p < 20 ? "░" : p < 40 ? "▒" : p < 70 ? "▓" : "█");
  const blue = (p: number) => (p < 20 ? "38;5;195" : p < 40 ? "38;5;117" : p < 70 ? "38;5;39" : "38;5;27");
  const rows = await Promise.all(isles.map(async (i) => {
    try {
      const r = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${i.lat}&longitude=${i.lon}&hourly=precipitation_probability&forecast_hours=${HOURS}&timezone=auto`);
      return { i, p: ((await r.json()).hourly.precipitation_probability as number[]).map((x) => x ?? 0) };
    } catch {
      return { i, p: Array(HOURS).fill(0) as number[] };
    }
  }));
  console.log("☁  FORECAST — chance of rain over the cove · next 12h (each isle, local time)\n");
  console.log("                   now" + " ".repeat(HOURS * 2 - 8) + "+" + (HOURS - 1) + "h");
  rows.forEach(({ i, p }, k) => {
    const cells = p.map((x) => ESC(blue(x), glyph(x))).join(" ");
    console.log(`  ${tag[k]} ${i.isle.padEnd(14)} ${cells}   peak ${String(Math.max(...p)).padStart(3)}%`);
  });
  console.log("\n  legend  · <5   ░ <20   ▒ <40   ▓ <70   █ ≥70 %    ·  live forecast — a view, never stamped");
}

// M-4 · WEATHER DEPTH — derived atmospheric state from fields already fetched.
// No new API call. WMO code + RH + dew-spread → classify each island as one of:
//   "storm"   WMO 95/96/99 (thunderstorm) or CAPE-implied (code 80–82 + RH>85%)
//   "squall"  WMO 80–82 (violent showers) or wind_speed > 15 m/s
//   "mist"    WMO 45/48 (fog/rime) or RH ≥ 95% + dew-spread ≤ 1.5°C
//   "rain"    WMO 51–67 (drizzle/rain/freezing)
//   "overcast" WMO 3
//   "clear"   WMO 0–2
// The field is a tag, not a scalar — the sim ignores it; the HTML render annotates it.
function wxState(code: number, rh: number, ws: number, app: number, air: number): string {
  if (code >= 95) return "storm";
  if (code >= 80 || ws > 15) return "squall";
  if (code >= 51 && code <= 67) return "rain";
  if (code === 45 || code === 48 || (rh >= 95 && (air - app) <= 1.5)) return "mist";
  if (code === 3) return "overcast";
  return "clear";
}

// L−3 · export the LIVE boundary conditions for the Vulkan sim: apparent-temperature
// per island, fetched not stamped. Ephemeral by design (live = a view, never a file
// that gets committed). The Rust diffuse bin reads `seed` from this and the cove
// stops diffusing topography and starts diffusing the actual sky.
async function writeBoundary(out: string): Promise<void> {
  const isles = TWIN.islands as any[];
  const skies = await Promise.all(isles.map((i) => realSky(i.lat, i.lon)));
  // Temperature fallback must stay IN UNIT (°C) — never elevation, or a metre value poisons
  // the field. Use the mean of the islands that did resolve.
  const valid = skies.map((s) => s.app).filter((a) => !isNaN(a));
  const mean = valid.length ? Number((valid.reduce((a, b) => a + b, 0) / valid.length).toFixed(1)) : 25;
  // Wind fallback is the VECTOR mean of resolved islands — averaging compass degrees directly
  // is wrong (350° and 10° average to 0°, not 180°). Resolve in (vx,vy), then back to dir/speed.
  const rad = Math.PI / 180;
  const vw = skies.filter((s) => !isNaN(s.wd) && !isNaN(s.ws));
  const mvx = vw.length ? vw.reduce((a, s) => a + s.ws * Math.sin(s.wd * rad), 0) / vw.length : 0;
  const mvy = vw.length ? vw.reduce((a, s) => a + s.ws * Math.cos(s.wd * rad), 0) / vw.length : 0;
  const meanWs = Number(Math.hypot(mvx, mvy).toFixed(1));
  const meanWd = Number(((Math.atan2(mvx, mvy) / rad + 360) % 360).toFixed(0));
  // Marine layer (M-2): real SST + ocean current per island, one batched call to the Marine API.
  // SST sources the SEA field honestly (not air apparent-temp). Ocean currents are oceanographic
  // (flows-TO, 0=N 90=E) and weak in the banks (~0.2–1.2 km/h) — recorded here in m/s; the sim
  // keeps wind-driven surface drift for visible advection (a pure-current pass would be near-static).
  let marine: any[] = [];
  try {
    const r = await fetch(`https://marine-api.open-meteo.com/v1/marine?latitude=${isles.map((i) => i.lat).join(",")}&longitude=${isles.map((i) => i.lon).join(",")}&current=sea_surface_temperature,ocean_current_velocity,ocean_current_direction`);
    marine = ((j) => (Array.isArray(j) ? j : [j]))(await r.json());
  } catch { marine = []; }
  const sstAt = (k: number): number => marine[k]?.current?.sea_surface_temperature ?? NaN;
  const validSst = isles.map((_, k) => sstAt(k)).filter((v) => !isNaN(v));
  const meanSst = validSst.length ? Number((validSst.reduce((a, b) => a + b, 0) / validSst.length).toFixed(1)) : mean;
  const seeded = isles.map((i, k) => {
    const s = skies[k];
    const ws = isNaN(s.ws) ? meanWs : s.ws;
    const app = isNaN(s.app) ? mean : s.app;
    return {
      isle: i.isle, lat: i.lat, lon: i.lon, elevation_m: i.elevation_m,
      seed: app,
      sst: isNaN(sstAt(k)) ? meanSst : sstAt(k),
      wind_dir: isNaN(s.wd) ? meanWd : s.wd,
      wind_speed: ws,
      current_dir: marine[k]?.current?.ocean_current_direction ?? 0,
      current_speed: Number(((marine[k]?.current?.ocean_current_velocity ?? 0) / 3.6).toFixed(3)),
      wx_state: wxState(isNaN(s.code) ? -1 : s.code, isNaN(s.rh) ? 70 : s.rh, ws, app, isNaN(s.air) ? app : s.air),
      wx_code: isNaN(s.code) ? -1 : s.code,
    };
  });
  writeFileSync(out, JSON.stringify({ _note: "LIVE boundary — apparent-temp + wind + SST + ocean-current + wx_state per island, fetched not stamped. Ephemeral; regenerate before each sim run. current_dir oceanographic (flows-to, 0=N); current_speed m/s. wx_state: M-4 derived atmospheric class (clear/overcast/mist/rain/squall/storm).", islands: seeded }, null, 2));
  console.log(`boundary → ${out}\n  live seeds (°C apparent): ${seeded.map((s) => `${s.isle}=${s.seed}`).join("  ")}\n  live SST (°C):            ${seeded.map((s) => `${s.isle}=${s.sst}`).join("  ")}\n  live wind (° @ m/s):      ${seeded.map((s) => `${s.isle}=${s.wind_dir}@${s.wind_speed}`).join("  ")}\n  live current (° @ m/s):   ${seeded.map((s) => `${s.isle}=${s.current_dir}@${s.current_speed}`).join("  ")}\n  wx_state (M-4):           ${seeded.map((s) => `${s.isle}=${s.wx_state}`).join("  ")}`);
}

// B9 · THE TRUE 1728 HISTOGRAM — the barometer auditing its own design.
// Each .md gets weather from sha256(body) → (SKY, AIR, MOOD) = (h0, h1, h2) mod 12, one
// point in a 12×12×12 = 1728 space. Per file that is a reading; across the whole archive
// it is a DISTRIBUTION. If the space is "real" (a good hash over many files), the three
// axes fill flat and occupancy climbs toward 1728. Clumps or dead zones would be the lie.
// Corpus = tracked .md via `git ls-files` (junction-safe: satellites aren't tracked).
function histogram(): void {
  const repoRoot = join(ROOT, "..");
  let list: string[];
  try {
    list = execSync('git ls-files "*.md"', { cwd: repoRoot, encoding: "utf8", maxBuffer: 64 * 1024 * 1024 })
      .split("\n").map((s) => s.trim()).filter(Boolean);
  } catch (e) {
    console.error(`histogram: git ls-files failed (${(e as Error).message})`);
    return;
  }
  const sky = new Array(12).fill(0), air = new Array(12).fill(0), mood = new Array(12).fill(0);
  const cell = new Map<string, number>();                                      // "s,a,m" → count
  const grid: number[][] = Array.from({ length: 12 }, () => new Array(12).fill(0)); // SKY×AIR, MOOD summed
  let n = 0;
  for (const rel of list) {
    let md: string;
    try { md = readFileSync(join(repoRoot, rel), "utf8"); } catch { continue; }
    const h = createHash("sha256").update(body(md), "utf8").digest();
    const s = h[0] % 12, a = h[1] % 12, m = h[2] % 12;
    sky[s]++; air[a]++; mood[m]++; grid[s][a]++;
    cell.set(`${s},${a},${m}`, (cell.get(`${s},${a},${m}`) ?? 0) + 1);
    n++;
  }
  if (!n) { console.log("histogram: no tracked .md files found"); return; }

  const heat = (f: number): string => (f < 0.34 ? "38;5;39" : f < 0.67 ? "38;5;226" : "38;5;196");
  const bars = (counts: number[], labels: string[]): string => {
    const max = Math.max(...counts, 1);
    return counts.map((c, i) => {
      const w = Math.round((c / max) * 16);
      return `    ${labels[i].padEnd(24)} ${ESC(heat(c / max), "█".repeat(w) + "·".repeat(16 - w))} ${c}`;
    }).join("\n");
  };
  const spread = (a: number[]) => `${Math.min(...a)}..${Math.max(...a)} (flat ≈ ${(n / 12).toFixed(0)})`;
  const occupied = cell.size;

  console.log(`archipelago barometer · 1728-space histogram   (SKY×AIR×MOOD = 12×12×12)`);
  console.log(`  corpus: ${n} tracked .md files across the archive`);
  console.log(`  occupancy: ${occupied} / 1728 cells (${((occupied / 1728) * 100).toFixed(1)}%)  ·  ${(n / occupied).toFixed(1)} files per occupied cell`);
  console.log(`  per-axis fill — flat bars = a uniform hash, no dead zones:`);
  console.log(`   SKY  ${spread(sky)}`);
  console.log(bars(sky, SKY));
  console.log(`   AIR  ${spread(air)}`);
  console.log(bars(air, AIR));
  console.log(`   MOOD ${spread(mood)}`);
  console.log(bars(mood, MOOD));
  const top = [...cell.entries()].sort((a, b) => b[1] - a[1]).slice(0, 8);
  console.log(`  hottest cells (files sharing one weather — collisions, not errors):`);
  for (const [k, c] of top) {
    const [s, a, m] = k.split(",").map(Number);
    console.log(`    ${String(c).padStart(3)}×  ${SKY[s]} · ${AIR[a]} · ${MOOD[m]}`);
  }
  const gmax = Math.max(...grid.flat(), 1);
  const ramp = " ·░▒▓█";
  console.log(`  SKY (rows) × AIR (cols) density, MOOD summed  ['${ramp}' low→high]:`);
  for (let s = 0; s < 12; s++) {
    let row = "    ";
    for (let a = 0; a < 12; a++) {
      const f = grid[s][a] / gmax;
      const ch = ramp[Math.min(ramp.length - 1, Math.round(f * (ramp.length - 1)))];
      row += ESC(heat(f), ch + ch);
    }
    console.log(`${row}  ${SKY[s]}`);
  }
}

// Parse a GeoTIFF ArrayBuffer → Float32Array, then bilinearly resample to targetW×targetH.
// Handles the NOAA ImageServer case (returns exactly targetW×targetH) and the GMRT case
// (returns native resolution, needs resample). Requires the `geotiff` npm package.
async function fetchGeoTiffToGrid(url: string, targetW: number, targetH: number): Promise<number[]> {
  const resp = await fetch(url);
  if (!resp.ok) throw new Error(`HTTP ${resp.status} ${resp.statusText} — ${url}`);
  const buf = await resp.arrayBuffer();
  // Dynamic import: only loaded when --bathymetry is active. geotiff is a pure-JS ES module.
  const geotiff = await import("geotiff") as any;
  const tiff = await geotiff.fromArrayBuffer(buf);
  const img = await tiff.getImage();
  const rasters = await img.readRasters({ interleave: false });
  const band: Float32Array = rasters[0];
  const srcW: number = img.getWidth();
  const srcH: number = img.getHeight();
  // NOAA ImageServer honours the size= parameter — exact match, no resample needed.
  if (srcW === targetW && srcH === targetH) {
    return Array.from(band).map((v) => (isFinite(v) ? v : NaN));
  }
  // GMRT GridServer returns native resolution — bilinear downsample/upsample to target grid.
  const out: number[] = new Array(targetW * targetH);
  for (let ty = 0; ty < targetH; ty++) {
    for (let tx = 0; tx < targetW; tx++) {
      const sx = (tx / (targetW - 1)) * (srcW - 1);
      const sy = (ty / (targetH - 1)) * (srcH - 1);
      const ix = Math.floor(sx), iy = Math.floor(sy);
      const fx = sx - ix, fy = sy - iy;
      const ix1 = Math.min(ix + 1, srcW - 1), iy1 = Math.min(iy + 1, srcH - 1);
      const v00 = band[iy * srcW + ix], v10 = band[iy * srcW + ix1];
      const v01 = band[iy1 * srcW + ix], v11 = band[iy1 * srcW + ix1];
      out[ty * targetW + tx] = [v00, v10, v01, v11].every(isFinite)
        ? v00 * (1 - fx) * (1 - fy) + v10 * fx * (1 - fy) + v01 * (1 - fx) * fy + v11 * fx * fy
        : NaN;
    }
  }
  return out;
}

// THE MEDIUM — real GEBCO seafloor depth over the sim grid, so the sim stops being flat.
// The Bahamas are the most dramatic carbonate platform on Earth: banks under <10 m of water
// drop to ~2,000 m trenches within a kilometre.
//
// Sources (priority order):
//   noaa (default) — NOAA NCEI ArcGIS ImageServer, DEM_all mosaic (ETOPO 2022 + GEBCO 2024).
//                    Free, no auth, F32 GeoTIFF at exact requested W×H. Native ~450 m cells
//                    over the Bahamas. Default grid 400×300 → ~2 km cells (vs ~15-37 km before).
//   gmrt           — GMRT GridServer topo-mask layer. Free, no auth, ~100 m where real multibeam
//                    data exists; NaN elsewhere. Returns native-res GeoTIFF (bilinear resampled
//                    to target grid here). Use --bathymetry-source=gmrt to test coverage.
//   legacy         — Original OpenTopoData GEBCO 2020 point-query (100 pts/req, 1 req/s).
//                    Preserved for reference; 56×22 default matches the old committed grid.
//
// Flags:
//   --bathymetry-source=noaa|gmrt|legacy   (default: noaa)
//   --bathymetry-w=N                       (default: 400 for noaa/gmrt, 56 for legacy)
//   --bathymetry-h=N                       (default: 300 for noaa/gmrt, 22 for legacy)
async function writeBathymetry(): Promise<void> {
  const SRC = process.argv.find((a) => a.startsWith("--bathymetry-source="))?.split("=")[1] ?? "noaa";
  const isLegacy = SRC === "legacy";
  const W = Number(process.argv.find((a) => a.startsWith("--bathymetry-w="))?.split("=")[1] ?? (isLegacy ? "56" : "400"));
  const H = Number(process.argv.find((a) => a.startsWith("--bathymetry-h="))?.split("=")[1] ?? (isLegacy ? "22" : "300"));

  const isles = TWIN.islands as any[];
  let minLat = Infinity, maxLat = -Infinity, minLon = Infinity, maxLon = -Infinity;
  for (const i of isles) { minLat = Math.min(minLat, i.lat); maxLat = Math.max(maxLat, i.lat); minLon = Math.min(minLon, i.lon); maxLon = Math.max(maxLon, i.lon); }
  const padLat = (maxLat - minLat) * 0.08 + 0.1, padLon = (maxLon - minLon) * 0.08 + 0.1;
  minLat -= padLat; maxLat += padLat; minLon -= padLon; maxLon += padLon;

  let depth: number[];
  let sourceName: string;

  if (isLegacy) {
    // --- OpenTopoData GEBCO 2020 point-query (original path) ---
    sourceName = "api.opentopodata.org/v1/gebco2020";
    const pts: { lat: number; lon: number }[] = [];
    for (let cy = 0; cy < H; cy++) for (let cx = 0; cx < W; cx++) {
      pts.push({ lon: minLon + (cx / (W - 1)) * (maxLon - minLon), lat: maxLat - (cy / (H - 1)) * (maxLat - minLat) });
    }
    const rawDepth = new Array(W * H).fill(NaN);
    const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));
    for (let i = 0; i < pts.length; i += 100) {
      const batch = pts.slice(i, i + 100);
      const locs = batch.map((p) => `${p.lat.toFixed(5)},${p.lon.toFixed(5)}`).join("|");
      let ok = false;
      for (let attempt = 0; attempt < 3 && !ok; attempt++) {
        try {
          const r = await fetch(`https://api.opentopodata.org/v1/gebco2020?locations=${locs}`);
          const j: any = await r.json();
          if (j.status === "OK") { j.results.forEach((res: any, k: number) => { rawDepth[i + k] = res.elevation; }); ok = true; }
          else { await sleep(2000); }
        } catch { await sleep(2000); }
      }
      if (!ok) { console.error(`\nbathymetry: batch at ${i} failed after retries — aborting`); return; }
      process.stdout.write(`\r  fetched ${Math.min(i + 100, pts.length)}/${pts.length} cells`);
      if (i + 100 < pts.length) await sleep(1100);
    }
    depth = rawDepth;
  } else if (SRC === "gmrt") {
    // --- GMRT GridServer topo-mask: free, no auth, ~100 m where real multibeam data exists ---
    // topo-mask returns NaN where GMRT has no high-res data (unlike 'topo' which fills with ETOPO).
    // Use this to test whether the Bahamas have actual GMRT coverage before compositing.
    sourceName = "www.gmrt.org/services/GridServer?layer=topo-mask";
    console.log(`  GMRT topo-mask: ${minLon.toFixed(3)},${minLat.toFixed(3)} → ${maxLon.toFixed(3)},${maxLat.toFixed(3)} (native res, bilinear → ${W}×${H}) ...`);
    const url = `https://www.gmrt.org/services/GridServer?north=${maxLat}&south=${minLat}&west=${minLon}&east=${maxLon}&layer=topo-mask&format=geotiff&resolution=max`;
    depth = await fetchGeoTiffToGrid(url, W, H);
    const hitCount = depth.filter(isFinite).length;
    console.log(`  GMRT topo-mask coverage: ${hitCount}/${W * H} cells (${((hitCount / (W * H)) * 100).toFixed(1)}% of grid)`);
  } else {
    // --- NOAA NCEI ArcGIS ImageServer (default): DEM_all mosaic, ETOPO 2022 + GEBCO 2024 ---
    // Requests exactly W×H pixels at F32 precision. No auth. Free, open.
    // Native source is GEBCO 2024 15" (~450 m) over the Bahamas; the server resamples to W×H.
    sourceName = "gis.ngdc.noaa.gov/arcgis/rest/services/DEM_mosaics/DEM_all/ImageServer";
    const url = `https://gis.ngdc.noaa.gov/arcgis/rest/services/DEM_mosaics/DEM_all/ImageServer/exportImage?bbox=${minLon},${minLat},${maxLon},${maxLat}&bboxSR=4326&imageSR=4326&size=${W},${H}&format=tiff&pixelType=F32&f=image`;
    console.log(`  NOAA NCEI ImageServer: ${W}×${H} F32 GeoTIFF over Bahamas bbox ...`);
    depth = await fetchGeoTiffToGrid(url, W, H);
  }

  const vals = depth.filter((d) => isFinite(d) && !isNaN(d));
  if (!vals.length) { console.error("\nbathymetry: no valid depths received"); return; }
  const dmin = Math.min(...vals), dmax = Math.max(...vals), land = depth.filter((d) => isFinite(d) && d >= 0).length;
  const out = {
    _note: `Seafloor elevation over the sim grid. STABLE — committed, not live. elevation_m: + = land above sea, − = metres below sea. Source: ${sourceName}.`,
    source: sourceName, W, H,
    bbox: { minLat, maxLat, minLon, maxLon },
    depth,
  };
  writeFileSync(join(ROOT, "charts", "bathymetry.json"), JSON.stringify(out));
  console.log(`\nbathymetry → charts/bathymetry.json   ${W}×${H} cells · ${dmin.toFixed(0)}..${dmax.toFixed(0)} m · ${land} land · ${vals.length - land} sea`);
}

// M-3 · HURRICANE EPISODIC FORCING — a real storm track over the Bahama Bank.
//
// HURDAT2 is NOAA's best-track archive (public domain). Each 6-hourly fix gives
// lat/lon of the storm center, max sustained wind (kt), and minimum central pressure.
// We embed a curated snapshot of Dorian 2019 directly — a track that crossed the
// exact islands the sim models. No live fetch: storms are stable historical record.
//
// Wind model: exponential decay from storm center. At radius r km:
//   v(r) = v_max × exp(−r / r_scale)
// r_scale ≈ 100 km for a compact Cat5 (Dorian had small RMW ~25 km but large field).
// Wind direction rotates cyclonically (counterclockwise NH) around the center:
//   θ_storm = bearing_from_center + 90°  (left of the radial = inflow spiral)
// Temperature override: hurricane SST below Cat5 eyewall (~26–27°C minimum threshold)
// + evaporative cooling under spiral bands brings apparent-temp down to ~23–24°C.
//
// Output is the same boundary JSON the sim reads, so no Rust changes needed.

const HURDAT2_DORIAN_2019 = [
  // date-utc                      lat     lon    vmax_kt  minCP_hPa  category  note
  { t: "2019-08-24T12:00Z", lat: 16.1, lon: -45.0, vmax: 30, cp: 1007, cat: "TD",  note: "genesis" },
  { t: "2019-08-25T18:00Z", lat: 17.3, lon: -50.4, vmax: 40, cp: 1000, cat: "TS",  note: "named Dorian" },
  { t: "2019-08-27T18:00Z", lat: 18.7, lon: -57.2, vmax: 55, cp:  990, cat: "TS",  note: "" },
  { t: "2019-08-29T12:00Z", lat: 20.2, lon: -63.0, vmax: 60, cp:  987, cat: "1",   note: "Cat1" },
  { t: "2019-08-30T12:00Z", lat: 21.4, lon: -67.5, vmax: 70, cp:  979, cat: "1",   note: "" },
  { t: "2019-08-31T18:00Z", lat: 22.6, lon: -72.1, vmax: 90, cp:  962, cat: "2",   note: "" },
  { t: "2019-09-01T06:00Z", lat: 24.5, lon: -75.9, vmax: 130, cp: 930, cat: "4",   note: "rapid intensification" },
  { t: "2019-09-01T12:00Z", lat: 25.4, lon: -76.8, vmax: 160, cp: 910, cat: "5",   note: "approaching Abaco" },
  { t: "2019-09-01T18:00Z", lat: 26.5, lon: -77.8, vmax: 165, cp: 910, cat: "5",   note: "LANDFALL Grand Bahama / Abaco — Cat5 peak" },
  { t: "2019-09-02T06:00Z", lat: 26.8, lon: -77.8, vmax: 155, cp: 916, cat: "5",   note: "stalled over Grand Bahama — catastrophic surge" },
  { t: "2019-09-02T18:00Z", lat: 26.9, lon: -77.5, vmax: 130, cp: 934, cat: "4",   note: "weakening as it moves N" },
  { t: "2019-09-03T12:00Z", lat: 27.5, lon: -77.0, vmax: 105, cp: 950, cat: "3",   note: "NE turn" },
  { t: "2019-09-05T06:00Z", lat: 31.0, lon: -76.4, vmax:  85, cp: 958, cat: "2",   note: "paralleling Florida coast" },
  { t: "2019-09-06T12:00Z", lat: 34.2, lon: -76.3, vmax:  80, cp: 960, cat: "1",   note: "Cape Hatteras approach" },
];

// Named snapshots for --hurricane=<name>
const HURRICANE_SNAPSHOTS: Record<string, { fix: typeof HURDAT2_DORIAN_2019[0]; name: string; season: number }> = {
  dorian: { fix: HURDAT2_DORIAN_2019[8], name: "Dorian", season: 2019 }, // Cat5 landfall, peak intensity
  dorian_stall: { fix: HURDAT2_DORIAN_2019[9], name: "Dorian", season: 2019 }, // stalled Cat5 — the surge
  dorian_approach: { fix: HURDAT2_DORIAN_2019[7], name: "Dorian", season: 2019 }, // Cat5 approaching Abaco
};

function hurricaneWindAtIsland(
  stormLat: number, stormLon: number, vmaxKt: number,
  isleLat: number, isleLon: number,
): { wind_speed: number; wind_dir: number } {
  const DEG = Math.PI / 180;
  const R_EARTH_KM = 6371;
  // Haversine distance
  const dLat = (isleLat - stormLat) * DEG;
  const dLon = (isleLon - stormLon) * DEG;
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(stormLat * DEG) * Math.cos(isleLat * DEG) * Math.sin(dLon / 2) ** 2;
  const r_km = 2 * R_EARTH_KM * Math.asin(Math.sqrt(a));

  const vmax_ms = vmaxKt * 0.5144; // knots → m/s
  const r_scale = 100; // km — exponential decay scale for Cat5 wide field
  const v = vmax_ms * Math.exp(-r_km / r_scale);

  // Bearing from storm center to island (meteorological: 0=N, clockwise)
  const y = Math.sin((isleLon - stormLon) * DEG) * Math.cos(isleLat * DEG);
  const x = Math.cos(stormLat * DEG) * Math.sin(isleLat * DEG)
    - Math.sin(stormLat * DEG) * Math.cos(isleLat * DEG) * Math.cos((isleLon - stormLon) * DEG);
  const bearing = ((Math.atan2(y, x) / DEG) + 360) % 360;

  // Cyclonic inflow: NH counterclockwise → wind direction = bearing − 90° (rotated left of radial)
  // "wind comes FROM" convention: add 180°
  const wind_from = ((bearing - 90 + 180) + 360) % 360;

  return { wind_speed: Number(v.toFixed(1)), wind_dir: Number(wind_from.toFixed(0)) };
}

async function writeHurricaneBoundary(snapKey: string): Promise<void> {
  const snap = HURRICANE_SNAPSHOTS[snapKey.toLowerCase()];
  if (!snap) {
    const valid = Object.keys(HURRICANE_SNAPSHOTS).join(", ");
    console.error(`hurricane: unknown snapshot "${snapKey}" — valid: ${valid}`);
    process.exit(1);
  }
  const { fix, name, season } = snap;
  const isles = TWIN.islands as any[];

  // Sea-surface temps: climatological September mean for the Bahamas (~28–29°C)
  // minus hurricane SST cooling: eyewall mixing pulls surface temps down ~1–2°C.
  // We compute per island: closer to storm → more cooling (up to −3°C at <50 km).
  const vmaxMs = fix.vmax * 0.5144;
  const climatoSST = 29.0; // September mean, Bahama Bank
  const seeded = isles.map((i: any) => {
    const wf = hurricaneWindAtIsland(fix.lat, fix.lon, fix.vmax, i.lat, i.lon);
    // SST cooling scales with local wind intensity (proxy for upwelling / mixing)
    const cooling = Math.min(3.0, (wf.wind_speed / vmaxMs) * 3.0);
    const sst = Number((climatoSST - cooling).toFixed(1));
    // Apparent temp: under spiral bands, evaporative + adiabatic cooling ~ 23–26°C
    const seed = Number((sst - 2.5 - cooling * 0.5).toFixed(1));
    return {
      isle: i.isle, lat: i.lat, lon: i.lon, elevation_m: i.elevation_m,
      seed,
      sst,
      wind_dir: wf.wind_dir,
      wind_speed: wf.wind_speed,
      current_dir: 0,
      current_speed: 0,
      wx_state: wf.wind_speed >= 33 ? "storm" : wf.wind_speed >= 15 ? "squall" : "clear",
      wx_code: -1,
    };
  });

  const out = join(ROOT, "..", "live_boundary.json");
  const DEG = Math.PI / 180;
  writeFileSync(out, JSON.stringify({
    _note: `HURRICANE BOUNDARY — ${name} ${season} @ ${fix.t} · ${fix.cat} · storm center ${fix.lat}°N ${Math.abs(fix.lon)}°W · vmax ${fix.vmax}kt · CP ${fix.cp}hPa · "${fix.note}" · episodic forcing, not live fetch`,
    hurricane: { name, season, fix_time: fix.t, category: fix.cat, center_lat: fix.lat, center_lon: fix.lon, vmax_kt: fix.vmax, min_cp_hpa: fix.cp, note: fix.note },
    islands: seeded,
  }, null, 2));

  const DEG_SYM = "°";
  console.log(`\nhurricane boundary → live_boundary.json`);
  console.log(`  ${name} ${season} — ${fix.cat} — ${fix.t}`);
  console.log(`  center: ${fix.lat}${DEG_SYM}N, ${Math.abs(fix.lon)}${DEG_SYM}W — vmax ${fix.vmax} kt (${(fix.vmax * 0.5144).toFixed(0)} m/s) — CP ${fix.cp} hPa`);
  console.log(`  note: ${fix.note}`);
  console.log(`\n  wind at each island (cyclonic field, exponential decay, r_scale=100 km):`);
  seeded.forEach((s) => {
    const DEG = Math.PI / 180;
    const dLat = (s.lat - fix.lat) * DEG, dLon = (s.lon - fix.lon) * DEG;
    const a = Math.sin(dLat / 2) ** 2 + Math.cos(fix.lat * DEG) * Math.cos(s.lat * DEG) * Math.sin(dLon / 2) ** 2;
    const r_km = 2 * 6371 * Math.asin(Math.sqrt(a));
    console.log(`  ${s.isle.padEnd(16)} ${r_km.toFixed(0).padStart(4)} km  →  wind ${s.wind_speed} m/s @ ${s.wind_dir}${DEG_SYM}   SST ${s.sst}°C  apparent ${s.seed}°C`);
  });
  console.log(`\n  feed to sim: cargo run --bin archipelago_sim -- live_boundary.json`);
}

if (HURRICANE) {
  await writeHurricaneBoundary(HURRICANE);
} else if (BOUNDARY) {
  await writeBoundary(BOUNDARY);
} else if (BATHYMETRY) {
  await writeBathymetry();
} else if (FORECAST) {
  await forecast();
} else if (HISTOGRAM) {
  histogram();
} else if (CHART) {
  writeChart();
  console.log("charted → CLAUDEBASE/charts/sea-chart.md");
} else if (STAMP) {
  for (const f of files) {
    const { changed, value } = stampFile(f);
    console.log(`${changed ? "stamped " : "fixpoint"}  ${relative(ROOT, f)}  →  ${value}`);
  }
} else if (WATCH) {
  for (const f of files) stampFile(f);
  await dashboard();
  console.log(`— watching ${relative(process.cwd(), ROOT)} for .md/.json saves${LIVE ? `; refetching sky every ${Math.round(INTERVAL / 1000)}s` : ""}. Ctrl-C to weigh anchor. —`);
  let timer: ReturnType<typeof setTimeout> | null = null;
  watch(ROOT, { recursive: true }, (_e, name) => {
    const n = String(name ?? "");
    if (!n.endsWith(".md") && !n.endsWith(".json")) return;
    if (timer) clearTimeout(timer);
    timer = setTimeout(async () => {
      if (n.endsWith(".json")) { refreshTwin(); writeChart(); } // edit the twin → cove moves
      for (const f of files) stampFile(f);
      await dashboard();
    }, 250);
  });
  if (LIVE) setInterval(dashboard, INTERVAL);
} else {
  for (const f of files) console.log((await printOne(f)) + "\n");
}
