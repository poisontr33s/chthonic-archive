#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: theme_artcop.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🔥 THE FOUNDRY
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Theme Art Cop — WCAG contrast auditor and palette quality checker.

Reads a VS Code theme JSON and reports:
- WCAG AA/AAA compliance for every foreground/background pair
- Color distribution (how many scopes per hex)
- Palette temperature analysis (warm vs cold)
- Missing UI chrome coverage

@SID:           TOOL_THEME_ARTCOP_V1
@Shabti:          Utility
@Purpose:       Theme Art Cop — WCAG contrast auditor and palette quality checker.
"""

import json
import math
import sys
from collections import Counter
from pathlib import Path


def hex_to_rgb(h: str) -> tuple[int, int, int]:
    """Parse #RRGGBB or #RRGGBBAA to (R, G, B)."""
    h = h.lstrip('#')
    if len(h) >= 6:
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return 0, 0, 0


def relative_luminance(r: int, g: int, b: int) -> float:
    """WCAG 2.1 relative luminance."""
    def linearize(c: int) -> float:
        s = c / 255.0
        return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4
    return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)


def contrast_ratio(fg: str, bg: str) -> float:
    """WCAG contrast ratio between two hex colors."""
    l1 = relative_luminance(*hex_to_rgb(fg))
    l2 = relative_luminance(*hex_to_rgb(bg))
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def color_temperature(hex_color: str) -> str:
    """Classify as warm/cold/neutral based on R-B channel balance."""
    r, g, b = hex_to_rgb(hex_color)
    warmth = r - b
    if warmth > 30:
        return 'warm'
    elif warmth < -30:
        return 'cold'
    return 'neutral'


# UI chrome keys that a complete theme should cover
EXPECTED_UI_KEYS = {
    'editor.background', 'editor.foreground',
    'sideBar.background', 'sideBar.foreground',
    'activityBar.background', 'activityBar.foreground',
    'statusBar.background', 'statusBar.foreground',
    'titleBar.activeBackground', 'titleBar.activeForeground',
    'tab.activeBackground', 'tab.activeForeground',
    'panel.background', 'panelTitle.activeForeground',
    'terminal.background', 'terminal.foreground',
    'editorError.foreground', 'editorWarning.foreground', 'editorInfo.foreground',
    'button.background', 'button.foreground',
    'input.background', 'input.foreground', 'input.border',
    'list.activeSelectionBackground', 'list.activeSelectionForeground',
    'dropdown.background', 'dropdown.border',
    'notifications.background', 'notifications.foreground',
    'gitDecoration.modifiedResourceForeground',
    'gitDecoration.deletedResourceForeground',
    'gitDecoration.untrackedResourceForeground',
    'editorLineNumber.foreground', 'editorLineNumber.activeForeground',
    'editorCursor.foreground',
    'editorBracketMatch.border',
    'breadcrumb.foreground',
    'scrollbarSlider.background',
    'minimap.errorHighlight',
    'peekView.border',
    'merge.currentHeaderBackground',
    'editorWidget.background', 'editorWidget.foreground',
    'badge.background', 'badge.foreground',
    'progressBar.background',
    'editorGutter.addedBackground', 'editorGutter.modifiedBackground', 'editorGutter.deletedBackground',
    'diffEditor.insertedTextBackground', 'diffEditor.removedTextBackground',
    'debugToolBar.background',
    'toolbar.hoverBackground',
}


def audit_theme(theme_path: str) -> dict:
    """Run full audit on a VS Code theme JSON."""
    with open(theme_path, 'r', encoding='utf-8') as f:
        theme = json.load(f)

    name = theme.get('name', 'Unknown')
    colors = theme.get('colors', {})
    tokens = theme.get('tokenColors', [])

    bg = colors.get('editor.background', '#1e1e1e')

    # --- WCAG Audit ---
    wcag_results = []
    for key, val in colors.items():
        if not val or not val.startswith('#') or len(val) < 7:
            continue
        if 'background' in key.lower() or 'border' in key.lower() or 'shadow' in key.lower():
            continue
        ratio = contrast_ratio(val, bg)
        level = 'AAA' if ratio >= 7.0 else 'AA' if ratio >= 4.5 else 'FAIL'
        wcag_results.append({
            'key': key,
            'color': val,
            'ratio': round(ratio, 1),
            'level': level
        })

    for tc in tokens:
        fg = tc.get('settings', {}).get('foreground')
        if fg and fg.startswith('#') and len(fg) >= 7:
            ratio = contrast_ratio(fg, bg)
            level = 'AAA' if ratio >= 7.0 else 'AA' if ratio >= 4.5 else 'FAIL'
            wcag_results.append({
                'key': f"token: {tc.get('name', 'unnamed')}",
                'color': fg,
                'ratio': round(ratio, 1),
                'level': level
            })

    # --- Color Distribution ---
    all_colors = []
    for val in colors.values():
        if val and val.startswith('#') and len(val) >= 7:
            all_colors.append(val[:7].upper())
    for tc in tokens:
        fg = tc.get('settings', {}).get('foreground')
        if fg and fg.startswith('#'):
            all_colors.append(fg[:7].upper())

    distribution = Counter(all_colors)

    # --- Temperature ---
    temps = Counter()
    for c in set(all_colors):
        temps[color_temperature(c)] += 1

    # --- Missing UI Chrome ---
    present_keys = set(colors.keys())
    missing = sorted(EXPECTED_UI_KEYS - present_keys)

    # --- Summary ---
    fails = [r for r in wcag_results if r['level'] == 'FAIL']
    overused = [(c, n) for c, n in distribution.most_common(5) if n > 4]

    return {
        'name': name,
        'background': bg,
        'total_ui_colors': len(colors),
        'total_token_rules': len(tokens),
        'wcag_fails': fails,
        'wcag_pass_rate': f"{(len(wcag_results) - len(fails))}/{len(wcag_results)}",
        'overused_colors': overused,
        'temperature': dict(temps),
        'missing_chrome': missing,
        'missing_count': len(missing),
    }


def print_report(result: dict) -> None:
    """Pretty-print the audit."""
    print(f"\n{'='*60}")
    print(f"  ART COP REPORT: {result['name']}")
    print(f"{'='*60}")
    print(f"  Background: {result['background']}")
    print(f"  UI colors: {result['total_ui_colors']}  |  Token rules: {result['total_token_rules']}")
    print(f"  WCAG pass rate: {result['wcag_pass_rate']}")
    print(f"  Temperature: {result['temperature']}")
    print(f"  Missing UI chrome: {result['missing_count']} keys")

    if result['wcag_fails']:
        print(f"\n  ❌ WCAG FAILURES (below 4.5:1):")
        for f in result['wcag_fails']:
            print(f"    {f['ratio']:4.1f}:1  {f['color']}  {f['key']}")

    if result['overused_colors']:
        print(f"\n  ⚠️  OVERUSED COLORS (>4 scopes):")
        for color, count in result['overused_colors']:
            temp = color_temperature(color)
            print(f"    {color} × {count}  ({temp})")

    if result['missing_chrome']:
        print(f"\n  📋 MISSING UI CHROME:")
        for k in result['missing_chrome'][:10]:
            print(f"    - {k}")
        if len(result['missing_chrome']) > 10:
            print(f"    ... and {len(result['missing_chrome']) - 10} more")

    print()


def main():
    if len(sys.argv) < 2:
        # Default: audit all themes in canonical extension
        theme_dir = Path(__file__).parent.parent / 'extensions' / 'chthonic-archive' / 'themes'
        if not theme_dir.exists():
            theme_dir = Path(__file__).parent.parent / 'extensions' / 'chthonic-mandala' / 'themes'
        themes = list(theme_dir.glob('*.json'))
    else:
        themes = [Path(a) for a in sys.argv[1:]]

    all_results = []
    for t in themes:
        result = audit_theme(str(t))
        all_results.append(result)
        if '--json' in sys.argv:
            continue
        print_report(result)

    if '--json' in sys.argv:
        print(json.dumps(all_results, indent=2))
        return

    # Summary comparison if multiple themes
    if len(all_results) > 1:
        print(f"{'='*60}")
        print(f"  COMPARISON SUMMARY")
        print(f"{'='*60}")
        for r in all_results:
            fails = len(r['wcag_fails'])
            missing = r['missing_count']
            temp = r['temperature']
            grade = '🟢' if fails == 0 and missing < 5 else '🟡' if fails < 3 else '🔴'
            print(f"  {grade} {r['name']}")
            print(f"     WCAG: {r['wcag_pass_rate']}  Missing: {missing}  Temp: {temp}")
        print()


if __name__ == '__main__':
    main()
