#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: theme_contrast_audit.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🔥 THE FOUNDRY
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Theme Contrast Audit — WCAG 2.1 contrast validation for workbench color pairs.

Scans all chthonic color themes for foreground/background pairs that fall below
the minimum contrast ratio, catching invisible UI elements before VSIX packaging.

@SID:           TOOL_THEME_CONTRAST_AUDIT_V1
@Shabti:          Guardian
@Context:       Infrastructure / Visual Quality Gate
@Implements:    WPTG Pillar II — Color Theme Contrast Enforcement
@Purpose:       Theme Contrast Audit — WCAG 2.1 contrast validation for workbench color pairs.

Usage:
    uv run scripts/theme_contrast_audit.py                    # audit all themes
    uv run scripts/theme_contrast_audit.py --min-ratio 4.5    # stricter WCAG AA text
    uv run scripts/theme_contrast_audit.py --theme geology    # one theme only
    uv run scripts/theme_contrast_audit.py --json             # machine output
    uv run scripts/theme_contrast_audit.py --strict           # exit 1 on any failure
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from scripts.lib.shared import configure_utf8_output, find_repo_root, setup_logging

# =============================================================================
# WCAG 2.1 Contrast Computation
# =============================================================================

def hex_to_rgb(h: str) -> tuple[float, float, float]:
    """Convert hex color to (r, g, b) floats in [0, 1]."""
    h = h.lstrip("#")
    if len(h) == 8:
        h = h[:6]  # strip alpha channel
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4))


def relative_luminance(rgb: tuple[float, float, float]) -> float:
    """WCAG 2.1 relative luminance."""
    def linearize(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (linearize(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(color1: str, color2: str) -> float:
    """WCAG 2.1 contrast ratio between two hex colors."""
    l1 = relative_luminance(hex_to_rgb(color1))
    l2 = relative_luminance(hex_to_rgb(color2))
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


# =============================================================================
# Foreground / Background Pair Registry
# =============================================================================

# Each tuple is (foreground_key, background_key, category).
# Category helps group output and understand which UI surface is affected.
FG_BG_PAIRS: list[tuple[str, str, str]] = [
    # Activity bar
    ("activityBar.foreground", "activityBar.background", "Activity Bar"),
    ("activityBar.inactiveForeground", "activityBar.background", "Activity Bar"),
    ("activityBarTop.foreground", "activityBar.background", "Activity Bar"),
    ("activityBarTop.inactiveForeground", "activityBar.background", "Activity Bar"),
    ("activityBarBadge.foreground", "activityBarBadge.background", "Activity Bar"),
    # Sidebar
    ("sideBar.foreground", "sideBar.background", "Sidebar"),
    ("sideBarTitle.foreground", "sideBar.background", "Sidebar"),
    ("sideBarSectionHeader.foreground", "sideBarSectionHeader.background", "Sidebar"),
    # Editor
    ("foreground", "editor.background", "Editor"),
    ("descriptionForeground", "editor.background", "Editor"),
    ("disabledForeground", "editor.background", "Editor"),
    ("icon.foreground", "editor.background", "Editor"),
    ("editorCodeLens.foreground", "editor.background", "Editor"),
    ("editorInlayHint.foreground", "editor.background", "Editor"),
    ("editorLineNumber.foreground", "editor.background", "Editor"),
    ("editorGutter.foldingControlForeground", "editor.background", "Editor"),
    # Tabs
    ("tab.activeForeground", "tab.activeBackground", "Tabs"),
    ("tab.inactiveForeground", "tab.inactiveBackground", "Tabs"),
    ("tab.unfocusedInactiveForeground", "tab.unfocusedInactiveBackground", "Tabs"),
    # Title bar
    ("titleBar.activeForeground", "titleBar.activeBackground", "Title Bar"),
    ("titleBar.inactiveForeground", "titleBar.inactiveBackground", "Title Bar"),
    # Status bar
    ("statusBar.foreground", "statusBar.background", "Status Bar"),
    ("statusBar.debuggingForeground", "statusBar.debuggingBackground", "Status Bar"),
    ("statusBar.noFolderForeground", "statusBar.noFolderBackground", "Status Bar"),
    ("statusBarItem.errorForeground", "statusBarItem.errorBackground", "Status Bar Items"),
    ("statusBarItem.offlineForeground", "statusBarItem.offlineBackground", "Status Bar Items"),
    ("statusBarItem.prominentForeground", "statusBarItem.prominentBackground", "Status Bar Items"),
    ("statusBarItem.remoteForeground", "statusBarItem.remoteBackground", "Status Bar Items"),
    ("statusBarItem.warningForeground", "statusBarItem.warningBackground", "Status Bar Items"),
    # Panel
    ("panelTitle.activeForeground", "panel.background", "Panel"),
    ("panelTitle.inactiveForeground", "panel.background", "Panel"),
    ("peekViewTitleDescription.foreground", "peekViewTitle.background", "Panel"),
    # Lists / Trees
    ("list.activeSelectionForeground", "list.activeSelectionBackground", "Lists"),
    ("list.hoverForeground", "list.hoverBackground", "Lists"),
    ("list.inactiveForeground", "sideBar.background", "Lists"),
    ("list.deemphasizedForeground", "sideBar.background", "Lists"),
    # Breadcrumb
    ("breadcrumb.foreground", "breadcrumb.background", "Breadcrumb"),
    # Widgets
    ("editorWidget.foreground", "editorWidget.background", "Widgets"),
    ("input.foreground", "input.background", "Widgets"),
    ("input.placeholderForeground", "input.background", "Widgets"),
    ("inlineChatInput.placeholderForeground", "inlineChatInput.background", "Widgets"),
    ("button.foreground", "button.background", "Widgets"),
    ("badge.foreground", "badge.background", "Widgets"),
    ("menu.foreground", "menu.background", "Widgets"),
    ("quickInput.foreground", "quickInput.background", "Widgets"),
    # Notifications
    ("notificationCenterHeader.foreground", "notificationCenterHeader.background", "Notifications"),
    # Terminal
    ("terminal.foreground", "terminal.background", "Terminal"),
    # Git decorations (on sidebar)
    ("gitDecoration.modifiedResourceForeground", "sideBar.background", "Git"),
    ("gitDecoration.untrackedResourceForeground", "sideBar.background", "Git"),
    ("debugIcon.breakpointDisabledForeground", "sideBar.background", "Git"),
]


# =============================================================================
# Audit Engine
# =============================================================================

def audit_theme(theme_path: Path, min_ratio: float) -> dict:
    """Audit a single theme file. Returns structured results."""
    with open(theme_path, encoding="utf-8") as f:
        theme = json.load(f)

    colors = theme.get("colors", {})
    name = theme.get("name", theme_path.stem)
    results = []

    for fg_key, bg_key, category in FG_BG_PAIRS:
        fg = colors.get(fg_key)
        bg = colors.get(bg_key)
        if not fg or not bg:
            continue
        try:
            ratio = contrast_ratio(fg, bg)
            status = "ok" if ratio >= min_ratio else "fail"
            results.append({
                "fg_key": fg_key,
                "bg_key": bg_key,
                "fg_color": fg,
                "bg_color": bg,
                "ratio": round(ratio, 1),
                "category": category,
                "status": status,
            })
        except (ValueError, IndexError):
            continue

    failures = [r for r in results if r["status"] == "fail"]
    return {
        "theme": name,
        "file": theme_path.name,
        "total_pairs": len(results),
        "passing": len(results) - len(failures),
        "failing": len(failures),
        "min_ratio": min_ratio,
        "failures": failures,
    }


# =============================================================================
# CLI
# =============================================================================

def main() -> int:
    configure_utf8_output()

    parser = argparse.ArgumentParser(
        description="WCAG 2.1 contrast audit for chthonic color themes."
    )
    parser.add_argument(
        "--min-ratio", type=float, default=3.0,
        help="Minimum contrast ratio (default: 3.0 for UI elements, use 4.5 for text)"
    )
    parser.add_argument(
        "--theme", type=str, default=None,
        help="Audit only the named theme (e.g., 'geology', 'rogbiv')"
    )
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on any failure")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--quiet", "-q", action="store_true")
    args = parser.parse_args()

    log = setup_logging(verbose=args.verbose, quiet=args.quiet)
    repo_root = find_repo_root()
    themes_dir = repo_root / "extensions" / "chthonic-archive" / "themes"

    if not themes_dir.is_dir():
        log.error("Themes directory not found: %s", themes_dir)
        return 1

    theme_files = sorted(themes_dir.glob("*-color-theme.json"))
    if args.theme:
        theme_files = [f for f in theme_files if args.theme.lower() in f.name.lower()]
        if not theme_files:
            log.error("No theme matching '%s' found", args.theme)
            return 1

    all_results = []
    total_failures = 0

    for tf in theme_files:
        result = audit_theme(tf, args.min_ratio)
        all_results.append(result)
        total_failures += result["failing"]

    if args.json:
        print(json.dumps(all_results, indent=2))
    else:
        for result in all_results:
            if result["failing"] == 0:
                print(f"  OK  {result['theme']} — {result['total_pairs']}/{result['total_pairs']} pass (>= {args.min_ratio}:1)")
            else:
                print(f"FAIL  {result['theme']} — {result['failing']}/{result['total_pairs']} below {args.min_ratio}:1")
                for f in result["failures"]:
                    print(f"      {f['ratio']:4.1f}:1  [{f['category']}] {f['fg_key']}={f['fg_color']} on {f['bg_key']}={f['bg_color']}")

        print(f"\n{'ALL CLEAR' if total_failures == 0 else 'AUDIT FAILED'}: "
              f"{len(theme_files)} themes, {sum(r['total_pairs'] for r in all_results)} pairs checked, "
              f"{total_failures} below {args.min_ratio}:1")

    if args.strict and total_failures > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
