#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: route_index.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: GOLD
# ║ Temple-Ayllu Zone: 🧭 THE COMPASS
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Sub-lens — compound router over git_rot_index, dependabot_index, method_index)
# ╚════════════════════════════════════════════════════════════════════════════

"""
scripts/route_index.py - Sub-lens compound router.

Reads the four observation lenses (git_rot_index, dependabot_index,
github_activity_index, method_index) and emits routing decisions:
for each open piece of noise, which method-class clears it and what
the suggested invocation is.

Default mode: propose-only (writes manifest, prints suggested
invocations, executes nothing). Use --apply to subprocess the
auto-applicable methods. Constraint-bumps and rot edits are
always propose-only (need user decision).

Emits:
  manifest/route_index.json  - machine-readable snapshot
  manifest/route_index.md    - human-readable digest

@SID:           ROUTE_INDEX_V1
@Shabti:        CLI Script
@Purpose:       Compound router over observation lenses.
"""

# @SID: ROUTE_INDEX_V1
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_DIR = REPO_ROOT / "manifest"

# Methods this router will auto-apply when --apply is set.
# Everything else stays propose-only because it needs user judgment
# (major-version policy, per-file edit decisions, etc.).
AUTO_APPLICABLE_METHODS = {"uv-lock-upgrade"}


def load_lens(name: str) -> dict | None:
    """Load a lens manifest or None if missing/invalid."""
    path = MANIFEST_DIR / f"{name}.json"
    if not path.exists():
        print(f"[route_index] missing lens: {path.name} (run lens-refresh first)",
              file=sys.stderr)
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"[route_index] invalid JSON in {path.name}: {e}", file=sys.stderr)
        return None


def build_routes(rot: dict | None, dep: dict | None, methods: dict | None) -> list[dict]:
    """Compute routes: noise_class -> method_name -> batch of packages/files."""
    if methods is None:
        return []

    methods_by_noise = {m["noise_class"]: m for m in methods["methods"]}
    routes: dict[str, dict] = {}

    # Dependabot routing (deterministic, ecosystem-based).
    if dep is not None:
        for a in dep.get("alerts", []):
            if a.get("state") != "open":
                continue
            ecosystem = a.get("ecosystem") or "unknown"
            relationship = a.get("relationship") or "unknown"
            # Try transitive/direct-pinned/direct in order of specificity.
            keys = [
                f"dependabot/{ecosystem}-{relationship}",
                f"dependabot/{ecosystem}-direct-pinned",
                f"dependabot/{ecosystem}-transitive",
            ]
            m = next((methods_by_noise[k] for k in keys if k in methods_by_noise), None)
            if m is None:
                continue
            route = routes.setdefault(m["name"], {
                "method": m["name"],
                "noise_class": m["noise_class"],
                "suggested_invocation": m["suggested_invocation"],
                "frequency_prior": m["frequency"],
                "auto_applicable": m["name"] in AUTO_APPLICABLE_METHODS,
                "items": [],
            })
            route["items"].append({
                "kind": "dependabot",
                "package": a.get("package"),
                "ecosystem": ecosystem,
                "severity": a.get("severity"),
                "fixed_in": a.get("fixed_in"),
                "manifest_path": a.get("manifest_path"),
                "alert_number": a.get("number"),
            })

    # Rot routing (propose-only — per-file edit decisions don't subprocess well).
    if rot is not None:
        rot_category_to_method = {
            "line_anchor_stale": "anchor-correction",
            "anchor_missing": "anchor-correction",
            "ambig_truly_ambiguous": "anchor-correction",
            "broken_no_known_target": "stub-creation-or-tombstone",
        }
        for e in rot.get("entries", []):
            cat = e.get("category")
            method_name = rot_category_to_method.get(cat)
            if method_name is None:
                continue
            m = methods_by_noise.get({
                "anchor-correction": "rot/L3-anchor",
                "stub-creation-or-tombstone": "rot/ROT-001-phantom-target",
            }.get(method_name))
            route = routes.setdefault(method_name, {
                "method": method_name,
                "noise_class": "rot/" + (m["noise_class"].split("/")[-1] if m else cat),
                "suggested_invocation": m["suggested_invocation"] if m else "per-file edit",
                "frequency_prior": m["frequency"] if m else 0,
                "auto_applicable": False,  # rot edits always need user judgment
                "items": [],
            })
            route["items"].append({
                "kind": "rot",
                "source": e.get("source"),
                "line": e.get("line"),
                "code": e.get("code"),
                "raw_target": e.get("raw_target"),
            })

    return sorted(routes.values(), key=lambda r: -len(r["items"]))


def build_invocation_uv_lock(packages: list[str]) -> list[str]:
    """uv lock --upgrade-package <pkg> [--upgrade-package <pkg> ...]"""
    cmd = ["uv", "lock"]
    for p in packages:
        cmd.extend(["--upgrade-package", p])
    return cmd


def apply_route(route: dict, dry_run: bool = True) -> dict:
    """Execute (or dry-run) a single auto-applicable route."""
    method = route["method"]
    packages = sorted({i["package"] for i in route["items"] if i.get("package")})
    result = {
        "method": method,
        "package_count": len(packages),
        "packages": packages,
        "executed": False,
        "dry_run": dry_run,
        "command": None,
        "exit_code": None,
        "stdout_tail": None,
        "stderr_tail": None,
    }

    if method == "uv-lock-upgrade":
        cmd = build_invocation_uv_lock(packages)
        result["command"] = " ".join(cmd)
        if dry_run:
            print(f"[route_index] dry-run: {result['command']}")
            return result
        print(f"[route_index] applying: {result['command']}")
        proc = subprocess.run(cmd, cwd=str(REPO_ROOT),
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace")
        result["executed"] = True
        result["exit_code"] = proc.returncode
        result["stdout_tail"] = proc.stdout[-2000:] if proc.stdout else None
        result["stderr_tail"] = proc.stderr[-2000:] if proc.stderr else None
        if proc.returncode != 0:
            print(f"[route_index] FAILED: {proc.stderr[:500]}", file=sys.stderr)
        return result

    # Other methods are propose-only.
    print(f"[route_index] {method} is not auto-applicable (propose-only)")
    return result


def write_md(index: dict) -> str:
    lines = [
        "# Route index digest",
        "",
        f"Generated: {index['generated_at']}",
        f"Source: `manifest/route_index.json` (regenerate via `uv run scripts/route_index.py`)",
        "",
        "Sub-lens: compound router over the 4 observation lenses.",
        "For each open noise item, names the method-class that clears it",
        "and the suggested invocation. Auto-applicable methods can be",
        "fired with `--apply`; others are propose-only (need user decision).",
        "",
        "## Summary",
        "",
        f"- Routes computed: {len(index['routes'])}",
        f"- Total noise items routed: {sum(len(r['items']) for r in index['routes'])}",
        f"- Auto-applicable routes: {sum(1 for r in index['routes'] if r['auto_applicable'])}",
        "",
        "## Routes (most items first)",
        "",
    ]
    for r in index["routes"]:
        applicable = "auto-applicable" if r["auto_applicable"] else "propose-only"
        lines.append(f"### `{r['method']}` — {len(r['items'])} items ({applicable})")
        lines.append("")
        lines.append(f"- Noise class: `{r['noise_class']}`")
        lines.append(f"- Frequency prior (from method_index): {r['frequency_prior']}x")
        lines.append(f"- Suggested invocation: `{r['suggested_invocation']}`")
        # Sample first 5 items
        sample = r["items"][:5]
        if sample and sample[0]["kind"] == "dependabot":
            pkgs = sorted({i["package"] for i in r["items"] if i.get("package")})
            lines.append(f"- Packages ({len(pkgs)}): {', '.join(pkgs[:10])}"
                         f"{'...' if len(pkgs)>10 else ''}")
        elif sample and sample[0]["kind"] == "rot":
            sources = sorted({i["source"] for i in r["items"][:10] if i.get("source")})
            lines.append(f"- Sample sources: {', '.join(sources[:5])}"
                         f"{'...' if len(sources)>5 else ''}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(prog="route_index")
    p.add_argument("--apply", action="store_true",
                   help="Subprocess the auto-applicable routes (default: propose-only)")
    p.add_argument("--method", default=None,
                   help="Limit --apply to a single method-name (e.g., uv-lock-upgrade)")
    p.add_argument("--no-md", action="store_true", help="skip markdown digest")
    p.add_argument("--out-json", default="manifest/route_index.json")
    p.add_argument("--out-md", default="manifest/route_index.md")
    args = p.parse_args()

    rot = load_lens("git_rot_index")
    dep = load_lens("dependabot_index")
    methods = load_lens("method_index")

    if methods is None:
        print("[route_index] method_index missing — cannot route. Run lens-refresh.",
              file=sys.stderr)
        return 1

    routes = build_routes(rot, dep, methods)

    application_results: list[dict] = []
    if args.apply:
        for r in routes:
            if not r["auto_applicable"]:
                continue
            if args.method and r["method"] != args.method:
                continue
            application_results.append(apply_route(r, dry_run=False))

    index = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "routes": routes,
        "applied": application_results,
        "summary": {
            "route_count": len(routes),
            "items_routed": sum(len(r["items"]) for r in routes),
            "auto_applicable_count": sum(1 for r in routes if r["auto_applicable"]),
            "applied_count": len(application_results),
        },
    }

    out_json = REPO_ROOT / args.out_json
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[route_index] wrote {out_json}")

    if not args.no_md:
        out_md = REPO_ROOT / args.out_md
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_md.write_text(write_md(index), encoding="utf-8")
        print(f"[route_index] wrote {out_md}")

    s = index["summary"]
    print(f"[route_index] {s['items_routed']} items routed across {s['route_count']} method(s); "
          f"auto-applicable={s['auto_applicable_count']}; applied={s['applied_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
