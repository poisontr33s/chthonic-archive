#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: product_icon_census.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
product_icon_census.py — Product Icon Census (Stage 6.0).

@SID:           TOOL_PRODUCT_ICON_CENSUS_V1
@Shabti:        CLI Script
@Purpose:       Maps all VS Code codicon IDs against the current SFS product
                icon theme to identify coverage gaps. Reads the codicon CSV
                from the local VS Code Insiders installation as the
                authoritative source. Discovery-only: no modifications.
"""

import csv
import json
import sys
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
EXT_DIR = REPO_ROOT / "extensions" / "chthonic-archive"
THEME_PATH = EXT_DIR / "themes" / "chthonic-product-icon-theme.json"
AUDIT_OUT = EXT_DIR / "audit-reports" / "product_icon_census.json"

# VS Code Insiders codicon CSV — authoritative local source
VSCODE_INSIDERS_BASE = Path.home() / "AppData" / "Local" / "Programs" / "Microsoft VS Code Insiders"

# ── Visibility Tiers ──────────────────────────────────────────────────────
# Categorize codicon IDs by how often users see them in the VS Code UI.
# Tier 1 = always visible, Tier 4 = rarely seen.

TIER_1_ALWAYS_VISIBLE = {
    # Activity Bar
    "files", "search", "extensions", "extensions-large", "debug", "debug-alt",
    "account", "settings-gear", "remote-explorer", "remote",
    # Status Bar
    "error", "error-small", "warning", "info", "sync", "sync-ignored",
    "bell", "bell-dot", "bell-slash", "bell-slash-dot",
    "git-branch", "git-branch-changes", "git-branch-conflicts",
    "git-branch-staged-changes",
    # Window Chrome
    "chrome-close", "chrome-maximize", "chrome-minimize", "chrome-restore",
    # Copilot / AI (prominent in modern VS Code)
    "copilot", "copilot-large", "copilot-in-progress", "copilot-warning",
    "copilot-warning-large", "copilot-error", "copilot-blocked",
    "copilot-not-connected", "copilot-snooze", "copilot-success",
    "copilot-unavailable",
}

TIER_2_FREQUENTLY_VISIBLE = {
    # Editor Actions
    "close", "close-all", "split-horizontal", "split-vertical",
    "go-to-file", "edit", "edit-sparkle", "save", "save-as", "save-all",
    "fold", "fold-down", "fold-up", "unfold",
    "preview", "open-preview", "editor-layout",
    # Panel
    "terminal", "terminal-bash", "terminal-cmd", "terminal-powershell",
    "terminal-linux", "terminal-ubuntu", "terminal-debian",
    "terminal-git-bash", "terminal-tmux",
    "output", "debug-console",
    # Sidebar / Tree View
    "folder", "folder-active", "folder-library", "folder-opened",
    "file", "file-text", "file-code", "file-binary", "file-media",
    "file-pdf", "file-zip", "file-submodule",
    "root-folder", "root-folder-opened",
    # Common Actions
    "add", "add-small", "remove", "remove-small", "refresh",
    "filter", "filter-filled", "search-large", "search-sparkle",
    "collapse-all", "expand-all", "clear-all",
    "copy", "trash", "redo",
    # Layout
    "layout", "layout-activitybar-left", "layout-activitybar-right",
    "layout-centered", "layout-menubar",
    "layout-panel", "layout-panel-center", "layout-panel-dock",
    "layout-panel-justify", "layout-panel-left", "layout-panel-off",
    "layout-panel-right",
    "layout-sidebar-left", "layout-sidebar-left-dock", "layout-sidebar-left-off",
    "layout-sidebar-right", "layout-sidebar-right-dock", "layout-sidebar-right-off",
    "layout-statusbar",
    # Notifications
    "megaphone", "inbox",
}

TIER_3_CONTEXT_SPECIFIC = {
    # Debug
    "debug-all", "debug-alt-small", "debug-breakpoint-conditional",
    "debug-breakpoint-conditional-unverified", "debug-breakpoint-data",
    "debug-breakpoint-data-unverified", "debug-breakpoint-function",
    "debug-breakpoint-function-unverified", "debug-breakpoint-log",
    "debug-breakpoint-log-unverified", "debug-breakpoint-unsupported",
    "debug-connected", "debug-continue", "debug-continue-small",
    "debug-coverage", "debug-disconnect", "debug-line-by-line",
    "debug-pause", "debug-rerun", "debug-restart", "debug-restart-frame",
    "debug-reverse-continue", "debug-stackframe", "debug-stackframe-active",
    "debug-start", "debug-step-back", "debug-step-into", "debug-step-out",
    "debug-step-over", "debug-stop",
    # Testing
    "beaker", "beaker-stop", "pass", "pass-filled", "coverage",
    "run-all", "run-all-coverage", "run-above", "run-below",
    "run-coverage", "run-errors", "run-with-deps",
    # SCM / Git
    "git-commit", "git-compare", "git-fetch", "git-merge",
    "git-pull-request", "git-pull-request-closed", "git-pull-request-create",
    "git-pull-request-done", "git-pull-request-draft",
    "git-pull-request-go-to-changes", "git-pull-request-new-changes",
    "git-stash", "git-stash-apply", "git-stash-pop",
    "diff", "diff-added", "diff-ignored", "diff-modified",
    "diff-multiple", "diff-removed", "diff-renamed", "diff-single",
    "discard",
    # Chat / AI
    "chat-sparkle", "chat-sparkle-error", "chat-sparkle-warning",
    "comment", "comment-discussion", "comment-discussion-quote",
    "comment-discussion-sparkle", "comment-draft", "comment-unresolved",
    "sparkle", "sparkle-filled", "thinking",
    "wand", "robot", "agent", "mcp",
}

# Tier 4 = everything else (symbols, branding, decorative, rare)


def find_codicon_csv() -> Path | None:
    """Find the codicon.csv from VS Code Insiders installation."""
    if not VSCODE_INSIDERS_BASE.exists():
        return None
    # The version hash directory changes with updates
    for child in VSCODE_INSIDERS_BASE.iterdir():
        if child.is_dir() and child.name not in ("bin",):
            csv_path = (
                child / "resources" / "app" / "node_modules"
                / "@vscode" / "codicons" / "dist" / "codicon.csv"
            )
            if csv_path.exists():
                return csv_path
    return None


def load_codicon_ids(csv_path: Path) -> list[str]:
    """Load all codicon IDs from the CSV file."""
    ids = []
    with csv_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("short_name", "").strip()
            if name:
                ids.append(name)
    return sorted(ids)


def load_theme_definitions(theme_path: Path) -> list[str]:
    """Load icon definition names from the product icon theme."""
    with theme_path.open(encoding="utf-8") as f:
        theme = json.load(f)
    defs = theme.get("iconDefinitions", {})
    return sorted(defs.keys())


def classify_tier(icon_id: str) -> int:
    """Assign a visibility tier (1-4) to a codicon ID."""
    if icon_id in TIER_1_ALWAYS_VISIBLE:
        return 1
    if icon_id in TIER_2_FREQUENTLY_VISIBLE:
        return 2
    if icon_id in TIER_3_CONTEXT_SPECIFIC:
        return 3
    return 4


def functional_category(icon_id: str) -> str:
    """Assign a functional category based on naming patterns."""
    prefixes = [
        ("debug-", "debug"),
        ("git-", "scm"),
        ("diff-", "scm"),
        ("terminal-", "terminal"),
        ("layout-", "layout"),
        ("chrome-", "window-chrome"),
        ("symbol-", "symbols"),
        ("copilot-", "ai-copilot"),
        ("chat-", "ai-chat"),
        ("comment-", "comments"),
        ("bell-", "notifications"),
        ("arrow-", "navigation"),
        ("file-", "files"),
        ("folder-", "files"),
        ("run-", "testing"),
        ("vm-", "remote"),
        ("graph-", "visualization"),
    ]
    for prefix, category in prefixes:
        if icon_id.startswith(prefix):
            return category
    # Single-word matches
    singles = {
        "search": "search", "files": "files", "extensions": "files",
        "account": "accounts", "settings-gear": "settings",
        "error": "diagnostics", "warning": "diagnostics", "info": "diagnostics",
        "sync": "sync", "remote": "remote", "output": "panel",
        "terminal": "terminal", "debug": "debug", "beaker": "testing",
        "pass": "testing", "coverage": "testing", "discard": "scm",
        "sparkle": "ai-chat", "wand": "ai-chat", "robot": "ai-chat",
        "agent": "ai-chat", "mcp": "ai-chat", "thinking": "ai-chat",
        "flame": "misc", "pulse": "misc", "shield": "misc",
        "paintcan": "theme", "layers": "misc", "hammer": "build",
    }
    return singles.get(icon_id, "general")


def run_census():
    """Execute the product icon census."""
    # 1. Find codicon source
    csv_path = find_codicon_csv()
    if csv_path is None:
        # Fallback: read from pre-extracted file
        fallback = (
            Path(__file__).resolve().parent.parent
            / "extensions" / "chthonic-archive" / "themes" / "codicon_ids_raw.txt"
        )
        if fallback.exists():
            all_ids = sorted(fallback.read_text(encoding="utf-8").strip().splitlines())
            print(f"[codicon source] Fallback: {fallback} ({len(all_ids)} IDs)")
        else:
            print("ERROR: Cannot find codicon.csv or fallback file")
            sys.exit(1)
    else:
        all_ids = load_codicon_ids(csv_path)
        print(f"[codicon source] {csv_path} ({len(all_ids)} IDs)")

    # 2. Load current theme
    theme_defs = load_theme_definitions(THEME_PATH)
    print(f"[theme defs]     {THEME_PATH.name} ({len(theme_defs)} definitions)")

    # 3. Compute coverage
    codicon_set = set(all_ids)
    covered = [d for d in theme_defs if d in codicon_set]
    uncovered = [d for d in theme_defs if d not in codicon_set]

    # 4. Classify all codicons by tier and category
    tier_counts = {1: 0, 2: 0, 3: 0, 4: 0}
    tier_covered = {1: 0, 2: 0, 3: 0, 4: 0}
    tier_gaps = {1: [], 2: [], 3: [], 4: []}
    category_stats: dict[str, dict] = {}

    for icon_id in all_ids:
        tier = classify_tier(icon_id)
        cat = functional_category(icon_id)
        tier_counts[tier] += 1
        is_covered = icon_id in theme_defs

        if is_covered:
            tier_covered[tier] += 1

        if cat not in category_stats:
            category_stats[cat] = {"total": 0, "covered": 0, "gap": []}
        category_stats[cat]["total"] += 1
        if is_covered:
            category_stats[cat]["covered"] += 1
        else:
            category_stats[cat]["gap"].append(icon_id)
            tier_gaps[tier].append(icon_id)

    # 5. Format report
    print("\n" + "=" * 72)
    print("PRODUCT ICON CENSUS — Stage 6.0")
    print("=" * 72)

    print(f"\nTotal codicon IDs:    {len(all_ids)}")
    print(f"Theme definitions:    {len(theme_defs)}")
    print(f"Valid overrides:      {len(covered)}")
    if uncovered:
        print(f"Invalid (no codicon): {uncovered}")
    print(f"Coverage:             {len(covered)}/{len(all_ids)} ({100*len(covered)/len(all_ids):.1f}%)")

    print("\n── Tier Coverage ──")
    for tier in (1, 2, 3, 4):
        labels = {1: "Always Visible", 2: "Frequently Visible",
                  3: "Context-Specific", 4: "Rare / Symbolic"}
        total = tier_counts[tier]
        cov = tier_covered[tier]
        pct = 100 * cov / total if total else 0
        print(f"  Tier {tier} ({labels[tier]:>20}): {cov}/{total} ({pct:.1f}%)")

    print("\n── Category Coverage ──")
    for cat in sorted(category_stats, key=lambda c: -category_stats[c]["total"]):
        s = category_stats[cat]
        pct = 100 * s["covered"] / s["total"] if s["total"] else 0
        print(f"  {cat:>20}: {s['covered']}/{s['total']} ({pct:.1f}%)")

    print("\n── Tier 1 Gaps (Highest Priority) ──")
    for icon_id in sorted(tier_gaps[1]):
        print(f"  ⚠️  {icon_id}")

    print(f"\n── Tier 2 Gaps ({len(tier_gaps[2])} icons) ──")
    for icon_id in sorted(tier_gaps[2])[:20]:
        print(f"  ○  {icon_id}")
    if len(tier_gaps[2]) > 20:
        print(f"  ... and {len(tier_gaps[2]) - 20} more")

    # 6. Write audit JSON
    audit = {
        "stage": "6.0",
        "name": "Product Icon Census",
        "total_codicon_ids": len(all_ids),
        "theme_definitions": len(theme_defs),
        "valid_overrides": covered,
        "invalid_definitions": uncovered,
        "coverage_pct": round(100 * len(covered) / len(all_ids), 1),
        "tier_summary": {
            f"tier_{t}": {
                "label": {1: "always_visible", 2: "frequently_visible",
                          3: "context_specific", 4: "rare_symbolic"}[t],
                "total": tier_counts[t],
                "covered": tier_covered[t],
                "gap_count": len(tier_gaps[t]),
            }
            for t in (1, 2, 3, 4)
        },
        "category_summary": {
            cat: {
                "total": s["total"],
                "covered": s["covered"],
                "gap_count": len(s["gap"]),
            }
            for cat, s in sorted(category_stats.items())
        },
        "tier_1_gaps": sorted(tier_gaps[1]),
        "tier_2_gaps": sorted(tier_gaps[2]),
    }
    AUDIT_OUT.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(f"\n[audit] Written to {AUDIT_OUT.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    run_census()
