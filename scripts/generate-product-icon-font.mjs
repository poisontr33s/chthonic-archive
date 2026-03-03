// generate-product-icon-font.mjs
// One-shot: converts 43 product SVGs into a woff icon font for the product icon theme.
// Bypasses fantasticon CLI (broken glob on Windows) and uses underlying libs directly.
// Stroke-to-fill preprocessing via @davestewart/outliner ensures glyph mass survives
// font rendering (the raw stroke art is too skeletal for font outline conversion).
import { SVGIcons2SVGFontStream } from 'svgicons2svgfont';
import svgpath from 'svgpath';
import svg2ttf from 'svg2ttf';
import ttf2woff from 'ttf2woff';
import { readFileSync, writeFileSync, mkdirSync, createReadStream } from 'fs';
import { resolve, join } from 'path';
import { outlineSvg } from '@davestewart/outliner';

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
const outlinedDir = resolve('extensions/chthonic-archive/themes/icons/product-outlined');
mkdirSync(outDir, { recursive: true });
mkdirSync(outlinedDir, { recursive: true });

const ATTRIBUTE_PATTERN = /([:\w-]+)\s*=\s*(?:"([^"]*)"|'([^']*)')/g;
const NUMBER_PATTERN = /-?(?:\d+\.?\d*|\.\d+)(?:e[-+]?\d+)?/gi;
const SHAPE_TAG_PATTERN = /<(circle|ellipse|rect|line|polyline|polygon)\b([^<>]*)\/?>/gi;
const PATH_D_PATTERN = /(<path\b[^<>]*\sd=)(["'])(.*?)\2/gi;

function parseAttributes(source) {
  const attributes = {};
  for (const match of source.matchAll(ATTRIBUTE_PATTERN)) {
    attributes[match[1]] = match[2] ?? match[3] ?? '';
  }
  return attributes;
}

function toNumber(value, fallback = 0) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function formatNumber(value) {
  const rounded = Number.parseFloat(value.toFixed(4));
  return Number.isFinite(rounded) ? `${rounded}` : '0';
}

function buildShapePath(tagName, attributes) {
  if (tagName === 'circle') {
    const cx = toNumber(attributes.cx);
    const cy = toNumber(attributes.cy);
    const r = toNumber(attributes.r);
    if (r <= 0) {
      return '';
    }
    return [
      `M ${formatNumber(cx - r)} ${formatNumber(cy)}`,
      `A ${formatNumber(r)} ${formatNumber(r)} 0 1 0 ${formatNumber(cx + r)} ${formatNumber(cy)}`,
      `A ${formatNumber(r)} ${formatNumber(r)} 0 1 0 ${formatNumber(cx - r)} ${formatNumber(cy)}`,
      'Z',
    ].join(' ');
  }

  if (tagName === 'ellipse') {
    const cx = toNumber(attributes.cx);
    const cy = toNumber(attributes.cy);
    const rx = toNumber(attributes.rx);
    const ry = toNumber(attributes.ry);
    if (rx <= 0 || ry <= 0) {
      return '';
    }
    return [
      `M ${formatNumber(cx - rx)} ${formatNumber(cy)}`,
      `A ${formatNumber(rx)} ${formatNumber(ry)} 0 1 0 ${formatNumber(cx + rx)} ${formatNumber(cy)}`,
      `A ${formatNumber(rx)} ${formatNumber(ry)} 0 1 0 ${formatNumber(cx - rx)} ${formatNumber(cy)}`,
      'Z',
    ].join(' ');
  }

  if (tagName === 'rect') {
    const x = toNumber(attributes.x);
    const y = toNumber(attributes.y);
    const width = toNumber(attributes.width);
    const height = toNumber(attributes.height);
    if (width <= 0 || height <= 0) {
      return '';
    }

    const rawRx = attributes.rx ?? attributes.ry ?? 0;
    const rawRy = attributes.ry ?? attributes.rx ?? 0;
    const rx = Math.min(Math.max(toNumber(rawRx), 0), width / 2);
    const ry = Math.min(Math.max(toNumber(rawRy), 0), height / 2);

    if (rx === 0 && ry === 0) {
      return [
        `M ${formatNumber(x)} ${formatNumber(y)}`,
        `H ${formatNumber(x + width)}`,
        `V ${formatNumber(y + height)}`,
        `H ${formatNumber(x)}`,
        'Z',
      ].join(' ');
    }

    return [
      `M ${formatNumber(x + rx)} ${formatNumber(y)}`,
      `H ${formatNumber(x + width - rx)}`,
      `A ${formatNumber(rx)} ${formatNumber(ry)} 0 0 1 ${formatNumber(x + width)} ${formatNumber(y + ry)}`,
      `V ${formatNumber(y + height - ry)}`,
      `A ${formatNumber(rx)} ${formatNumber(ry)} 0 0 1 ${formatNumber(x + width - rx)} ${formatNumber(y + height)}`,
      `H ${formatNumber(x + rx)}`,
      `A ${formatNumber(rx)} ${formatNumber(ry)} 0 0 1 ${formatNumber(x)} ${formatNumber(y + height - ry)}`,
      `V ${formatNumber(y + ry)}`,
      `A ${formatNumber(rx)} ${formatNumber(ry)} 0 0 1 ${formatNumber(x + rx)} ${formatNumber(y)}`,
      'Z',
    ].join(' ');
  }

  if (tagName === 'line') {
    const x1 = toNumber(attributes.x1);
    const y1 = toNumber(attributes.y1);
    const x2 = toNumber(attributes.x2);
    const y2 = toNumber(attributes.y2);
    return `M ${formatNumber(x1)} ${formatNumber(y1)} L ${formatNumber(x2)} ${formatNumber(y2)}`;
  }

  if (tagName === 'polyline' || tagName === 'polygon') {
    const values = (attributes.points ?? '').match(NUMBER_PATTERN)?.map(Number) ?? [];
    if (values.length < 4 || values.length % 2 !== 0) {
      return '';
    }

    const segments = [`M ${formatNumber(values[0])} ${formatNumber(values[1])}`];
    for (let index = 2; index < values.length; index += 2) {
      segments.push(`L ${formatNumber(values[index])} ${formatNumber(values[index + 1])}`);
    }
    if (tagName === 'polygon') {
      segments.push('Z');
    }
    return segments.join(' ');
  }

  return '';
}

function shapeAttributesToPathAttributes(tagName, attributes) {
  const geometryAttributes = new Set({
    circle: ['cx', 'cy', 'r'],
    ellipse: ['cx', 'cy', 'rx', 'ry'],
    rect: ['x', 'y', 'width', 'height', 'rx', 'ry'],
    line: ['x1', 'y1', 'x2', 'y2'],
    polyline: ['points'],
    polygon: ['points'],
  }[tagName]);

  const parts = [];
  for (const [name, value] of Object.entries(attributes)) {
    if (geometryAttributes.has(name)) {
      continue;
    }
    parts.push(`${name}="${value}"`);
  }
  return parts.length ? ` ${parts.join(' ')}` : '';
}

function convertShapesToPaths(svg) {
  return svg.replace(SHAPE_TAG_PATTERN, (match, tagName, attributeSource) => {
    const normalizedTag = tagName.toLowerCase();
    const attributes = parseAttributes(attributeSource);
    const d = buildShapePath(normalizedTag, attributes);
    if (!d) {
      return match;
    }
    const otherAttributes = shapeAttributesToPathAttributes(normalizedTag, attributes);
    return `<path d="${d}"${otherAttributes}/>`;
  });
}

function normalizePathData(svg) {
  return svg.replace(PATH_D_PATTERN, (match, prefix, quote, d) => {
    const normalized = svgpath(d).abs().unshort().round(4).toString();
    return `${prefix}${quote}${normalized}${quote}`;
  });
}

function sanitizeSvg(svg) {
  return svg
    .replace(/^\uFEFF/, '')
    .replace(/^&#xfeff;/i, '')
    .trim();
}

// Amplify stroke-widths so the outliner produces glyph paths with enough visual
// mass to survive font hinting and software (SwiftShader) rendering.
// At 20px icon size in a 1000-unit em from 16-unit viewBox:
//   1.8px stroke → 112.5 em-units → ~2.25px on screen (SwiftShader minimum).
//   2.5px stroke → 156.25 em-units → ~3.1px on screen (max before detail loss).
// factor: multiplier applied to every stroke-width value
// floor:  minimum stroke-width after amplification (visibility threshold)
// cap:    maximum stroke-width after amplification (detail preservation)
const STROKE_WIDTH_PATTERN = /stroke-width="([^"]+)"/g;
function amplifyStrokes(svg, factor = 1.6, floor = 1.8, cap = 2.5) {
  return svg.replace(STROKE_WIDTH_PATTERN, (match, value) => {
    const amplified = Math.min(Math.max(parseFloat(value) * factor, floor), cap);
    return `stroke-width="${formatNumber(amplified)}"`;
  });
}

// The outliner creates compound paths (inner+outer contour) and preserves the
// source fill-rule. With evenodd, the inner contour subtracts from the outer,
// producing hollow/invisible glyphs. Nonzero fills everything.
function fixFillRule(svg) {
  return svg.replace(/fill-rule="evenodd"/g, 'fill-rule="nonzero"');
}

// Step 0: Preprocess — stroke-to-fill conversion
const outlinedSvgs = [];
for (const icon of ICONS) {
  const raw = sanitizeSvg(readFileSync(join(svgDir, `${icon.name}.svg`), 'utf-8'));
  const withPathShapes = convertShapesToPaths(raw);
  const normalized = normalizePathData(withPathShapes);
  const amplified = amplifyStrokes(normalized);
  const outlined = fixFillRule(sanitizeSvg(outlineSvg(amplified, ['outline'])));
  outlinedSvgs.push({ ...icon, svg: outlined });
  writeFileSync(join(outlinedDir, `${icon.name}.svg`), outlined);
}
console.log(`✓ Outlined ${outlinedSvgs.length} SVGs (stroke ×1.6 → fill, floor 1.8px, cap 2.5px, nonzero fill)`);

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

  for (const icon of outlinedSvgs) {
    const glyph = createReadStream(join(outlinedDir, `${icon.name}.svg`));
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
