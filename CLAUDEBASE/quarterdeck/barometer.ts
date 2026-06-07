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

const ROOT = join(import.meta.dir, "..");
const TWIN_PATH = join(ROOT, "charts", "archipelago.json");
const loadTwin = () => JSON.parse(readFileSync(TWIN_PATH, "utf8"));
let TWIN = loadTwin();

const LIVE = process.argv.includes("--live");
const STAMP = process.argv.includes("--stamp");
const WATCH = process.argv.includes("--watch");
const CHART = process.argv.includes("--chart");
const FORECAST = process.argv.includes("--forecast");
const BOUNDARY = process.argv.find((a) => a.startsWith("--boundary="))?.split("=").slice(1).join("=");
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

async function realSky(lat: number, lon: number): Promise<{ app: number; air: number; rh: number; code: number; err?: string }> {
  try {
    const r = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code`);
    const c = (await r.json()).current;
    return { app: c.apparent_temperature, air: c.temperature_2m, rh: c.relative_humidity_2m, code: c.weather_code };
  } catch (e) {
    return { app: NaN, air: NaN, rh: NaN, code: -1, err: (e as Error).message };
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
- Cosmological-Altitude: Nautical · Victorian · Renaissance · Carribbean
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

// L−3 · export the LIVE boundary conditions for the Vulkan sim: apparent-temperature
// per island, fetched not stamped. Ephemeral by design (live = a view, never a file
// that gets committed). The Rust diffuse bin reads `seed` from this and the cove
// stops diffusing topography and starts diffusing the actual sky.
async function writeBoundary(out: string): Promise<void> {
  const isles = TWIN.islands as any[];
  const skies = await Promise.all(isles.map((i) => realSky(i.lat, i.lon)));
  // Fallback for a failed fetch must stay IN UNIT (°C) — never elevation, or a metre
  // value poisons the temperature field. Use the mean of the islands that did resolve.
  const valid = skies.map((s) => s.app).filter((a) => !isNaN(a));
  const mean = valid.length ? Number((valid.reduce((a, b) => a + b, 0) / valid.length).toFixed(1)) : 25;
  const seeded = isles.map((i, k) => ({
    isle: i.isle, lat: i.lat, lon: i.lon, elevation_m: i.elevation_m,
    seed: isNaN(skies[k].app) ? mean : skies[k].app,
  }));
  writeFileSync(out, JSON.stringify({ _note: "LIVE boundary — apparent-temp per island, fetched not stamped. Ephemeral; regenerate before each sim run.", islands: seeded }, null, 2));
  console.log(`boundary → ${out}\n  live seeds (°C apparent): ${seeded.map((s) => `${s.isle}=${s.seed}`).join("  ")}`);
}

if (BOUNDARY) {
  await writeBoundary(BOUNDARY);
} else if (FORECAST) {
  await forecast();
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
