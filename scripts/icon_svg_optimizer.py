#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: icon_svg_optimizer.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Icon SVG Optimizer — Structural refinement: strip redundant attributes,
normalize coordinates, collapse groups, remove whitespace, and report
per-file size deltas.

Covers WPTG Stage 2.0 (Structural Refinement).

@SID:           TOOL_ICON_SVG_OPTIMIZER_V1
@Shabti:          Utility
@Purpose:       Icon SVG Optimizer — Structural refinement: strip redundant attributes,
"""

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from scripts.lib.shared import configure_utf8_output


def find_repo_root() -> Path:
    p = Path(__file__).resolve().parent
    while p != p.parent:
        if (p / "Cargo.toml").exists():
            return p
        p = p.parent
    return Path(__file__).resolve().parent.parent


def find_icons_dir(repo: Path) -> Path:
    return repo / "extensions" / "chthonic-archive" / "themes" / "icons"


# ═══════════════════════════════════════════════════════════════════════════════
# SVG Optimization Passes
# ═══════════════════════════════════════════════════════════════════════════════

def strip_xml_declaration(text: str) -> str:
    """Remove <?xml ...?> declaration — VS Code doesn't need it."""
    return re.sub(r'<\?xml[^?]*\?>\s*', '', text)


def strip_comments(text: str) -> str:
    """Remove XML comments but preserve the first one (motif label)."""
    comments = list(re.finditer(r'<!--\s*(.*?)\s*-->', text, re.DOTALL))
    if not comments:
        return text
    # Keep the first comment (motif identifier), remove the rest
    for match in reversed(comments[1:]):
        text = text[:match.start()] + text[match.end():]
    return text


def normalize_whitespace(text: str) -> str:
    """Collapse multiple blank lines, trim trailing whitespace on each line."""
    lines = text.split('\n')
    out = []
    prev_blank = False
    for line in lines:
        stripped = line.rstrip()
        if not stripped:
            if not prev_blank:
                out.append('')
            prev_blank = True
        else:
            out.append(stripped)
            prev_blank = False
    # Remove trailing blank line
    while out and not out[-1]:
        out.pop()
    return '\n'.join(out) + '\n'


def round_coordinates(text: str) -> str:
    """Round coordinate values to max 2 decimal places to trim noise."""
    def _round(m: re.Match) -> str:
        val = float(m.group(0))
        rounded = round(val, 2)
        # Drop trailing zeros: 3.50 -> 3.5, 3.00 -> 3
        if rounded == int(rounded):
            return str(int(rounded))
        return f'{rounded:.2f}'.rstrip('0')

    # Only round numbers inside attribute values (after = and inside quotes)
    # Process fill, stroke, cx, cy, r, x, y, width, height, stroke-width, etc.
    # Match decimal numbers preceded by = or space within SVG element context
    result = re.sub(
        r'(?<=[="\s,])(\d+\.\d{3,})',
        _round,
        text
    )
    return result


def remove_default_attrs(text: str) -> str:
    """Remove attributes that equal their SVG defaults."""
    defaults = {
        'fill-opacity="1"': '',
        'stroke-opacity="1"': '',
        'opacity="1"': '',
        'fill-rule="nonzero"': '',
        'clip-rule="nonzero"': '',
    }
    for old, new in defaults.items():
        text = text.replace(old, new)
    # Clean up double spaces left behind
    text = re.sub(r'  +', ' ', text)
    # Clean up space before />
    text = re.sub(r' />', '/>', text)
    return text


def collapse_empty_groups(text: str) -> str:
    """Remove <g> wrappers that have no attributes (pass-through groups)."""
    # Match <g> ... </g> where <g> has no attributes
    text = re.sub(r'<g>\s*(.*?)\s*</g>', r'\1', text, flags=re.DOTALL)
    return text


def optimize_svg(text: str) -> str:
    """Run all optimization passes in sequence."""
    text = strip_xml_declaration(text)
    text = strip_comments(text)
    text = remove_default_attrs(text)
    text = collapse_empty_groups(text)
    text = round_coordinates(text)
    text = normalize_whitespace(text)
    return text


def process_file(svg_path: Path, dry_run: bool = False) -> dict:
    """Optimize a single SVG file. Returns stats."""
    original = svg_path.read_text(encoding='utf-8')
    original_size = len(original.encode('utf-8'))

    optimized = optimize_svg(original)
    optimized_size = len(optimized.encode('utf-8'))

    delta = original_size - optimized_size
    pct = (delta / original_size * 100) if original_size > 0 else 0

    if not dry_run and optimized != original:
        svg_path.write_text(optimized, encoding='utf-8')

    return {
        'file': svg_path.name,
        'original_bytes': original_size,
        'optimized_bytes': optimized_size,
        'delta_bytes': delta,
        'reduction_pct': round(pct, 1),
        'changed': optimized != original,
    }


def main() -> None:
    configure_utf8_output()

    parser = argparse.ArgumentParser(
        description='Icon SVG Optimizer — Stage 2.0 structural refinement.'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Report what would change without writing files.',
    )
    parser.add_argument(
        '--include-product',
        action='store_true',
        help='Also optimize product icons.',
    )
    parser.add_argument(
        '--repo',
        type=Path,
        default=None,
        help='Repository root (auto-detected if omitted).',
    )
    args = parser.parse_args()

    repo = args.repo or find_repo_root()
    icons_dir = find_icons_dir(repo)

    if not icons_dir.exists():
        print(f'ERROR: Icons directory not found: {icons_dir}', file=sys.stderr)
        sys.exit(1)

    svgs = sorted(icons_dir.glob('*.svg'))
    if args.include_product:
        product_dir = icons_dir / 'product'
        if product_dir.exists():
            svgs.extend(sorted(product_dir.glob('*.svg')))

    print('=' * 72)
    print(' ☥ ICON SVG OPTIMIZER — WPTG Stage 2.0')
    print('=' * 72)
    if args.dry_run:
        print('  MODE: dry-run (no files modified)')
    print()

    total_saved = 0
    total_orig = 0
    changed_count = 0
    results = []

    for svg in svgs:
        r = process_file(svg, dry_run=args.dry_run)
        results.append(r)
        total_orig += r['original_bytes']
        total_saved += r['delta_bytes']
        if r['changed']:
            changed_count += 1

        status = '✂️' if r['changed'] else '✅'
        delta_str = f'-{r["delta_bytes"]}B ({r["reduction_pct"]}%)' if r['delta_bytes'] > 0 else 'no change'
        print(f'  {status} {r["file"]:<36s} {r["original_bytes"]:>5d}B → {r["optimized_bytes"]:>5d}B  {delta_str}')

    print()
    print('─' * 72)
    total_pct = (total_saved / total_orig * 100) if total_orig > 0 else 0
    print(f'  Total: {len(svgs)} SVGs, {changed_count} modified, {total_saved}B saved ({total_pct:.1f}%)')
    print(f'  Before: {total_orig:,}B → After: {total_orig - total_saved:,}B')
    print()


if __name__ == '__main__':
    main()
