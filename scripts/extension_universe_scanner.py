#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: extension_universe_scanner.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Polyglot extension universe scanner for Phase 0.

@SID:           WPTG_EXTENSION_UNIVERSE_SCANNER_V1
@Shabti:        CLI Script
@Purpose:       Scan tracked extensions, discover toolchains, and emit extension universe intelligence.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

# sys.path guard: ensure repo root is importable regardless of invocation CWD
_REPO_ROOT_CANDIDATE = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT_CANDIDATE) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT_CANDIDATE))

from scripts.wptg_common import (
    alchemy_opportunities,
    baseline_gold_tier,
    build_eol_report,
    compound_extension,
    dead_extensions,
    discover_toolchains,
    ensure_utf8,
    extension_category,
    now_iso,
    path_is_excluded,
    repo_root,
    runtime_support_for_extension,
    toolchains_to_report,
    tracked_files,
    viable_but_unrepresented_extensions,
    write_json,
)


def build_extension_universe(root: Path) -> dict:
    tracked = tracked_files(root)
    toolchains = discover_toolchains()
    by_extension: dict[str, dict] = {}
    category_buckets: dict[str, set[str]] = defaultdict(set)
    total_by_extension: Counter[str] = Counter()

    for rel_path in tracked:
        raw_extension = compound_extension(rel_path)
        extension = raw_extension or "[no_ext]"
        category = extension_category(extension)
        total_by_extension[extension] += 1
        category_buckets[category].add(extension)

        bucket = by_extension.setdefault(
            extension,
            {
                "count": 0,
                "directories": set(),
                "lane_excluded_count": 0,
                "lane_excluded": False,
                "category": category,
                "gold_grade": baseline_gold_tier(extension),
                "runtime_support": {},
            },
        )
        bucket["count"] += 1
        directory = str(Path(rel_path).parent).replace("\\", "/") or "."
        bucket["directories"].add(directory)
        if path_is_excluded(rel_path):
            bucket["lane_excluded_count"] += 1
            bucket["lane_excluded"] = True

    for extension, bucket in by_extension.items():
        bucket["directories"] = sorted(bucket["directories"])
        bucket["runtime_support"] = runtime_support_for_extension(extension, toolchains)

    viable = viable_but_unrepresented_extensions(tracked, toolchains)
    payload = {
        "timestamp": now_iso(),
        "codebase_extensions": {
            "total_unique": sum(1 for extension in by_extension if extension != "[no_ext]"),
            "inventory": {
                extension: {
                    "count": bucket["count"],
                    "directories": bucket["directories"],
                    "lane_excluded": bucket["lane_excluded"],
                    "lane_excluded_count": bucket["lane_excluded_count"],
                    "category": bucket["category"],
                    "gold_grade": bucket["gold_grade"],
                    "runtime_support": bucket["runtime_support"],
                }
                for extension, bucket in sorted(by_extension.items())
            },
            "by_category": {
                category: sorted(values)
                for category, values in sorted(category_buckets.items())
            },
        },
        "system_toolchains": {
            **toolchains_to_report(toolchains),
            "details": {
                key: {
                    "display_name": probe.display_name,
                    "installed": probe.installed,
                    "runtime_version": probe.runtime_version,
                    "runtime_output": probe.runtime_output,
                    "manager": probe.manager,
                    "manager_installed": probe.manager_installed,
                    "manager_version": probe.manager_version,
                    "oxidized": probe.oxidized,
                }
                for key, probe in sorted(toolchains.items())
            },
        },
        "extension_gap": {
            "viable_but_unrepresented": viable,
            "dead_extensions": dead_extensions(tracked, toolchains),
            "alchemy_opportunities": alchemy_opportunities(viable),
        },
        "eol_risk": build_eol_report(toolchains),
        "summary": {
            "tracked_files": len(tracked),
            "lane_excluded_files": sum(1 for path in tracked if path_is_excluded(path)),
            "non_excluded_files": sum(1 for path in tracked if not path_is_excluded(path)),
            "top_extensions": total_by_extension.most_common(10),
        },
    }
    return payload


def determine_exit_code(payload: dict) -> int:
    total_unique = payload["codebase_extensions"]["total_unique"]
    installed = set(payload["system_toolchains"]["installed"])
    required = {"rust", "python", "ruby", "go", "typescript"}
    if total_unique >= 45 and required.issubset(installed):
        return 0
    if total_unique >= 40:
        return 1
    return 2


def main() -> int:
    ensure_utf8()
    parser = argparse.ArgumentParser(description="Phase 0 polyglot extension universe scanner.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("audit-reports/extension_universe.json"),
        help="Output JSON path.",
    )
    parser.add_argument(
        "--diff",
        type=Path,
        metavar="PREV_JSON",
        help="Compare current scan against a previous JSON output and print diff summary.",
    )
    args = parser.parse_args()

    root = repo_root()
    payload = build_extension_universe(root)
    write_json(root / args.output, payload)
    print(f"Wrote {args.output}")

    if getattr(args, "diff", None) and args.diff.is_file():
        try:
            prev = json.loads(args.diff.read_text(encoding="utf-8"))
            _print_universe_diff(prev, payload)
        except Exception as exc:  # noqa: BLE001
            print(f"  [diff] failed to compare: {exc}", file=sys.stderr)

    return determine_exit_code(payload)


def _print_universe_diff(prev: dict, curr: dict) -> None:
    """Print a human-readable diff between two extension_universe JSON payloads."""
    print("\n[diff] Extension universe comparison:")
    changed = False

    prev_inv = prev.get("codebase_extensions", {}).get("inventory", {})
    curr_inv = curr.get("codebase_extensions", {}).get("inventory", {})
    added = set(curr_inv) - set(prev_inv)
    removed = set(prev_inv) - set(curr_inv)
    if added:
        print(f"  Extensions added   (+{len(added)}): {', '.join(sorted(added)[:10])}")
        changed = True
    if removed:
        print(f"  Extensions removed (-{len(removed)}): {', '.join(sorted(removed)[:10])}")
        changed = True

    # Count delta
    prev_total = prev.get("summary", {}).get("tracked_files", 0)
    curr_total = curr.get("summary", {}).get("tracked_files", 0)
    if prev_total != curr_total:
        delta = curr_total - prev_total
        sign = "+" if delta > 0 else ""
        print(f"  Tracked files: {prev_total} → {curr_total} ({sign}{delta})")
        changed = True

    # Toolchain installs delta
    prev_inst = set(prev.get("system_toolchains", {}).get("installed", []))
    curr_inst = set(curr.get("system_toolchains", {}).get("installed", []))
    new_inst = curr_inst - prev_inst
    lost_inst = prev_inst - curr_inst
    if new_inst:
        print(f"  Toolchains gained: {', '.join(sorted(new_inst))}")
        changed = True
    if lost_inst:
        print(f"  Toolchains lost:   {', '.join(sorted(lost_inst))}")
        changed = True

    if not changed:
        print("  No structural changes detected.")


if __name__ == "__main__":
    raise SystemExit(main())
