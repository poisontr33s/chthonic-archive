// generate-product-icon-font.mjs
// One-shot: converts 7 product SVGs into a woff icon font for the product icon theme.
// Bypasses fantasticon CLI (broken glob on Windows) and uses underlying libs directly.
import { SVGIcons2SVGFontStream } from 'svgicons2svgfont';
import svg2ttf from 'svg2ttf';
import ttf2woff from 'ttf2woff';
import { createReadStream, writeFileSync, mkdirSync } from 'fs';
import { resolve, join } from 'path';

const ICONS = [
  // ── Existing (Pillar I) ──
  { name: 'comment-discussion', codepoint: 0xE001 },
  { name: 'flame',              codepoint: 0xE002 },
  { name: 'layers',             codepoint: 0xE004 },
  { name: 'paintcan',           codepoint: 0xE005 },
  { name: 'pulse',              codepoint: 0xE006 },
  { name: 'shield',             codepoint: 0xE007 },
  // ── Activity Bar ──
  { name: 'files',              codepoint: 0xE008 },
  { name: 'search',             codepoint: 0xE009 },
  { name: 'extensions',         codepoint: 0xE00A },
  { name: 'debug',              codepoint: 0xE00B },
  { name: 'debug-alt',          codepoint: 0xE00C },
  { name: 'remote',             codepoint: 0xE00D },
  { name: 'remote-explorer',    codepoint: 0xE00E },
  // ── Status Bar ──
  { name: 'sync',               codepoint: 0xE00F },
  { name: 'sync-ignored',       codepoint: 0xE010 },
  { name: 'error',              codepoint: 0xE011 },
  { name: 'error-small',        codepoint: 0xE012 },
  { name: 'warning',            codepoint: 0xE013 },
  { name: 'info',               codepoint: 0xE014 },
  { name: 'settings-gear',      codepoint: 0xE015 },
  { name: 'account',            codepoint: 0xE016 },
  // ── Notifications ──
  { name: 'bell',               codepoint: 0xE017 },
  { name: 'bell-dot',           codepoint: 0xE018 },
  { name: 'bell-slash',         codepoint: 0xE019 },
  { name: 'bell-slash-dot',     codepoint: 0xE01A },
  // ── Git / SCM ──
  { name: 'git-branch',                codepoint: 0xE01B },
  { name: 'git-branch-changes',        codepoint: 0xE01C },
  { name: 'git-branch-conflicts',      codepoint: 0xE01D },
  { name: 'git-branch-staged-changes', codepoint: 0xE01E },
  // ── Window Chrome ──
  { name: 'chrome-close',       codepoint: 0xE01F },
  { name: 'chrome-maximize',    codepoint: 0xE020 },
  { name: 'chrome-minimize',    codepoint: 0xE021 },
  { name: 'chrome-restore',     codepoint: 0xE022 },
  // ── Copilot (Eye of Horus) ──
  { name: 'copilot',              codepoint: 0xE023 },
  { name: 'copilot-blocked',      codepoint: 0xE024 },
  { name: 'copilot-error',        codepoint: 0xE025 },
  { name: 'copilot-in-progress',  codepoint: 0xE026 },
  { name: 'copilot-not-connected', codepoint: 0xE027 },
  { name: 'copilot-snooze',       codepoint: 0xE028 },
  { name: 'copilot-success',      codepoint: 0xE029 },
  { name: 'copilot-unavailable',  codepoint: 0xE02A },
  { name: 'copilot-warning',      codepoint: 0xE02B },
  // ── Build / Tools ──
  { name: 'tools',               codepoint: 0xE02C },
];

const svgDir = resolve('extensions/chthonic-archive/themes/icons/product');
const outDir = resolve('extensions/chthonic-archive/themes/fonts');
mkdirSync(outDir, { recursive: true });

// Step 1: SVG icons → SVG font
const svgFont = await new Promise((resolve, reject) => {
  let result = Buffer.alloc(0);
  const stream = new SVGIcons2SVGFontStream({
    fontName: 'chthonic-product-icons',
    fontHeight: 1000,
    normalize: true,
    log: () => {},
  });
  stream.on('data', (chunk) => { result = Buffer.concat([result, Buffer.from(chunk)]); });
  stream.on('end', () => resolve(result.toString()));
  stream.on('error', reject);

  for (const icon of ICONS) {
    const glyph = createReadStream(join(svgDir, `${icon.name}.svg`));
    glyph.metadata = { name: icon.name, unicode: [String.fromCodePoint(icon.codepoint)] };
    stream.write(glyph);
  }
  stream.end();
});

// Step 2: SVG font → TTF
const ttf = svg2ttf(svgFont, {});

// Step 3: TTF → WOFF
const woff = ttf2woff(Buffer.from(ttf.buffer));

// Write outputs
const woffPath = join(outDir, 'chthonic-product-icons.woff');
writeFileSync(woffPath, Buffer.from(woff.buffer));

// Write codepoint map for reference
const codepointMap = Object.fromEntries(
  ICONS.map(i => [i.name, `U+${i.codepoint.toString(16).toUpperCase().padStart(4, '0')}`])
);
writeFileSync(join(outDir, 'chthonic-product-icons.json'), JSON.stringify(codepointMap, null, 2));

console.log(`✓ Font: ${woffPath} (${(woff.buffer.byteLength / 1024).toFixed(1)} KB)`);
console.log(`✓ Codepoints:`, codepointMap);
