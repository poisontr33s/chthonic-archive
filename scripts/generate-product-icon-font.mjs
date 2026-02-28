// generate-product-icon-font.mjs
// One-shot: converts 7 product SVGs into a woff icon font for the product icon theme.
// Bypasses fantasticon CLI (broken glob on Windows) and uses underlying libs directly.
import { SVGIcons2SVGFontStream } from 'svgicons2svgfont';
import svg2ttf from 'svg2ttf';
import ttf2woff from 'ttf2woff';
import { createReadStream, writeFileSync, mkdirSync } from 'fs';
import { resolve, join } from 'path';

const ICONS = [
  { name: 'comment-discussion', codepoint: 0xE001 },
  { name: 'flame',              codepoint: 0xE002 },
  { name: 'hammer',             codepoint: 0xE003 },
  { name: 'layers',             codepoint: 0xE004 },
  { name: 'paintcan',           codepoint: 0xE005 },
  { name: 'pulse',              codepoint: 0xE006 },
  { name: 'shield',             codepoint: 0xE007 },
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
