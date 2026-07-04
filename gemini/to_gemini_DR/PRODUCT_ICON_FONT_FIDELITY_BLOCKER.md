# Deep Research Request: Product Icon Font Fidelity on SwiftShader

**From:** Claude (protocol/lore)  
**To:** Gemini 3.1 Pro (Deep Research)  
**Priority:** BLOCKER — frozen state, no other work proceeds until resolved  
**Date:** 2026-03-03  

## Context

We are building a VS Code Insiders extension (`chthonic-archive`) with custom product icon themes. The extension runs on **Windows 11 with SwiftShader software rendering** (no hardware GPU acceleration). Our 43 product icon SVGs are **stroke-based art** (e.g., `fill="none" stroke="currentColor" stroke-width="1.4"`) that must be converted to a WOFF icon font.

### The Pipeline

```
Original SVGs (stroke-only, 16×16 viewBox)
  → convertShapesToPaths() (ellipse/circle/rect → path)
  → normalizePathData() (relative → absolute coords)
  → amplifyStrokes() (increase stroke-width for visibility)
  → outlineSvg() (@davestewart/outliner — stroke → fill via MakerJS expandPaths)
  → fixFillRule() (evenodd → nonzero for compound paths)
  → sanitizeSvg() (BOM removal)
  → SVGIcons2SVGFont (normalize: true, fontHeight: 1000)
  → svg2ttf → ttf2woff
```

### The Problem

| Amplification | Stroke Range | Result |
|---|---|---|
| ×1.25, floor 1.4px | 1.4–2.25px | **Invisible** — sub-2px on screen vanishes on SwiftShader |
| ×1.6, floor 1.8, cap 2.5 | 1.8–2.5px | **Visible but blobby** — too much fill, details lost |
| ×2.2, floor 2.4px | 2.4–3.96px | **Way too thick** — icons are solid blobs |
| Adaptive remap [0.6..1.8]→[1.6..2.0] | 1.6–2.0px | **Current attempt** — untested |

The Codicon reference font (VS Code's default icons) uses **filled silhouettes** (`fill="currentColor"`, zero strokes), designed fill-first with effective line widths of ~1.0–1.5px in 16-unit viewBox. They use `fantasticon` with `normalize: true`. Their SVGs are already optimal for font conversion.

Our SVGs are stroke art — the outliner converts each stroke into a compound fill path (inner + outer boundary contours). This produces **inherently different glyph topology** from Codicon's filled silhouettes.

### Active Theme

**Geological Core (Sister Ferrum Scoriae)** — Dark theme:
- Activity bar: bg=#100D0A, fg=#f0bd1f (11.07:1 AAA contrast)
- icon.foreground: #f3c32e (11.68:1 AAA)
- All contrast ratios pass WCAG AA+. Colors are NOT the issue.

## Research Questions

Please investigate deeply:

### 1. SwiftShader Font Rendering
- How does SwiftShader (ANGLE/Vulkan software renderer used by Electron/Chromium) rasterize font glyphs?
- What is the minimum effective stroke/fill width (in pixels) that reliably renders visible on SwiftShader at 16-20px icon sizes?
- Does SwiftShader apply sub-pixel anti-aliasing to font glyphs? Or does it use grayscale AA only?
- Is there a known threshold where thin glyph features become invisible?

### 2. Outlined vs Filled Icon Font Glyphs
- When converting stroke SVGs to filled outlines (via MakerJS expandPaths), the resulting compound paths have inner+outer contours. How do font rasterizers (FreeType/DirectWrite/Skia) handle compound fill paths vs simple filled paths?
- Does `fill-rule: nonzero` behave differently from `evenodd` in font glyph rendering (CFF vs TrueType outlines)?
- Is there a quality difference between "originally designed as fills" vs "strokes converted to fills" in font glyphs?

### 3. Optimal Glyph Weight for 16px Icons on Software Renderers
- What is the industry-standard minimum line weight for icon fonts at 16-20px render size?
- Material Design Icons, Font Awesome, Phosphor Icons — what stroke weights do they use in their 16×16/24×24 viewBoxes?
- Are there published hinting/rendering guidelines for icon fonts on low-DPI or software-rendered displays?

### 4. Alternative Approaches
- Could we use **variable fonts** with a weight axis to dynamically adjust glyph thickness?
- Would generating **TTF with TrueType hinting** (vs CFF outlines) improve SwiftShader rendering?
- Is there a better stroke→fill conversion approach than MakerJS expandPaths? (e.g., Paper.js expand, opentype.js path manipulation, SVG stroke-to-path via browser)
- Could we use CSS `text-stroke` or `text-shadow` in VS Code's product icon rendering to artificially thicken glyphs?

### 5. VS Code Product Icon Rendering Internals
- How does VS Code render product icon font glyphs? (DOM → CSS → Chromium text rendering → Skia → SwiftShader)
- Does VS Code apply any CSS transforms, font-feature-settings, or text rendering hints to product icons?
- Is there a `font-weight: bold` or similar technique that could thicken icon glyphs without regenerating the font?

## Expected Output

A structured report with:
1. **Findings per question** with citations
2. **Recommended optimal stroke width range** for our specific setup (16×16 viewBox → 1000-unit em → WOFF → VS Code Insiders on SwiftShader)
3. **Actionable next steps** ranked by impact/effort
4. Any **reference implementations** or open-source projects that solved this same stroke-to-fill icon font problem

## Inline Artifacts (Gemini cannot access local files)

### Example 1: Original SVG — "search" (Eye of Ra, Wedjat)
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">
 <!-- Wedjat eye (Eye of Ra) — omniscient searching gaze -->
 <path d="M1.5 7.5C3.5 4.5 5.5 3 8 3s4.5 1.5 6.5 4.5C12.5 10.5 10.5 12 8 12S3.5 10.5 1.5 7.5z"
       fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/>
 <circle cx="8" cy="7.5" r="2" fill="none" stroke="currentColor" stroke-width="1.4"/>
 <path d="M6 12c-1 1-2 2-3 2.5" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
</svg>
```
- 3 stroke elements: eye outline (1.4px), pupil circle (1.4px), tear line (1.3px)
- All `fill="none"`, all `stroke="currentColor"`

### Example 2: Original SVG — "settings-gear" (Inti Sun Disc)
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">
 <!-- Inti sun disc — Andean radial sun (cosmic mechanism) -->
 <circle cx="8" cy="8" r="2.5" fill="none" stroke="currentColor" stroke-width="1.1"/>
 <!-- 8 trapezoidal rays (Inti canon: tapered) -->
 <path d="M8 1.5L7.3 4.5h1.4zM8 14.5l-.7-3h1.4z" fill="none" stroke="currentColor" stroke-width="0.8" stroke-linejoin="round"/>
 <path d="M1.5 8l3 .7v-1.4zM14.5 8l-3-.7v1.4z" fill="none" stroke="currentColor" stroke-width="0.8" stroke-linejoin="round"/>
 <path d="M3.4 3.4l2.4 1.3-.7 1.2zM12.6 12.6l-2.4-1.3.7-1.2z" fill="none" stroke="currentColor" stroke-width="0.8" stroke-linejoin="round"/>
 <path d="M12.6 3.4l-1.3 2.4-1.2-.7zM3.4 12.6l1.3-2.4 1.2.7z" fill="none" stroke="currentColor" stroke-width="0.8" stroke-linejoin="round"/>
</svg>
```
- Mix of 1.1px (structural circle) and 0.8px (detail rays) — this differentiation is lost at flat amplification

### Example 3: After Pipeline — "search" outlined
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">
 <path d="M 3.6688477 3.6278943 A 14.2359531 ... Z M 4.8601006 5.0650745 A 12.3692531 ... Z"
       fill="currentColor" fill-rule="nonzero"/>
 <path d="M 8 7.5 m -2.93335 0 a 2.93335 2.93335 0 0 0 5.8667 0 ... z
        M 8 7.5 m -1.06665 0 a 1.06665 1.06665 0 0 0 2.1333 0 ... z"
       fill="currentColor" fill-rule="nonzero"/>
 <path d="M 3.4767046 15.2829431 A 14.173234 ... Z" fill="currentColor"/>
</svg>
```
- Eye outline: compound path (outer contour Z, inner contour Z) — donut shape
- Pupil: compound path (outer circle r=2.93, inner circle r=1.07) — ring, NOT solid disc
- Tear: simple filled path (open stroke → closed fill)
- Note: `fill-rule="nonzero"` is critical — `evenodd` makes the inner contours SUBTRACT → hollow/invisible

### Stroke Distribution Across All 43 SVGs
```
155 stroke-width values total
min: 0.6px    max: 1.8px    avg: 1.09px
  0.6px: 8 values    (thin rays, fine detail)
  0.7px: 4 values
  0.8px: 29 values   (detail lines — most common thin weight)
  0.9px: 6 values
  1.0px: 22 values   (medium structural)
  1.1px: 16 values
  1.2px: 17 values   (text lines, secondary structure)
  1.3px: 12 values
  1.4px: 18 values   (primary structural — outlines)
  1.5px: 14 values   (heavy structural — scroll bodies)
  1.6px: 2 values
  1.7px: 1 value
  1.8px: 6 values    (heaviest — major outlines)
```

### Current Adaptive Remap Function
```javascript
// Maps original stroke distribution [0.6..1.8] → target band [1.6..2.0]
// Thin detail (0.6px) → 1.6px (×2.67 boost), thick structural (1.8px) → 2.0px (×1.11 boost)
function amplifyStrokes(svg, targetMin = 1.6, targetMax = 2.0) {
  const origMin = 0.6, origMax = 1.8;
  return svg.replace(STROKE_WIDTH_PATTERN, (match, value) => {
    const orig = parseFloat(value);
    const t = Math.max(0, Math.min(1, (orig - origMin) / (origMax - origMin)));
    const remapped = targetMin + t * (targetMax - targetMin);
    return `stroke-width="${formatNumber(remapped)}"`;
  });
}
```
**Core tension:** The [1.6..2.0] range has only 0.4px of differentiation. Original art has 1.2px range (0.6→1.8). We've compressed artistic weight contrast from 3:1 ratio to 1.25:1 ratio.

### Font Pipeline Config
```javascript
// SVGIcons2SVGFont — same normalize flag as Codicon's fantasticon
const stream = new SVGIcons2SVGFontStream({
  fontName: 'chthonic-product-icons',
  fontHeight: 1000,
  normalize: true,
});
// → svg2ttf → ttf2woff
// Output: chthonic-product-icons.woff (7,408 bytes, 43 glyphs, codepoints E001–E02C)
```

### Environment
- **OS:** Windows 11  
- **Editor:** VS Code Insiders (Electron/Chromium with SwiftShader)  
- **Renderer:** SwiftShader (ANGLE Vulkan software backend) — no hardware GPU  
- **Display:** Standard DPI (96 DPI / 1× device pixel ratio assumed)  
- **Icon render size:** 20px for activity bar, 16px for status bar  
- **Font em:** 1000 units (from 16-unit viewBox → ×62.5 scale)

## File References (local paths, not accessible)

- Generator: `scripts/generate-product-icon-font.mjs`
- Product Icon Theme: `extensions/chthonic-archive/themes/chthonic-product-icon-theme.json`
- Font: `extensions/chthonic-archive/themes/fonts/chthonic-product-icons.woff`
- Source SVGs: `extensions/chthonic-archive/themes/icons/product/` (43 files)
- Outlined SVGs: `extensions/chthonic-archive/themes/icons/product-outlined/` (43 files)
- SFS Theme: `extensions/chthonic-archive/themes/chthonic-geology-color-theme.json`
