#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: dependabot_index.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
scripts/dependabot_index.py - Pull Dependabot alerts and structurize.

Mirrors the data-plane / render-plane separation of git_rot_index.py.
The user owns the signal; the dashboard is a derived view, not a director.

Calls `gh api repos/<owner>/<repo>/dependabot/alerts --paginate`, parses
the JSON, classifies each alert by severity / state / ecosystem / scope /
relationship / fix-availability, surfaces hotspot packages (same alert
class against the same package multiple times), and emits:

  manifest/dependabot_index.json   - machine-readable snapshot
  manifest/dependabot_index.md     - human-readable digest, prioritized

Re-run anytime to refresh. JSON is cache, not truth. Truth is GitHub.

Usage:
  uv run scripts/dependabot_index.py             # full index (current repo)
  uv run scripts/dependabot_index.py --repo a/b  # different repo
  uv run scripts/dependabot_index.py --no-md     # skip markdown digest
  uv run scripts/dependabot_index.py --state open  # filter (open/fixed/dismissed)

@SID:           DEPENDABOT_INDEX_V1
@Shabti:        CLI Script
@Purpose:       scripts/dependabot_index.py - Pull Dependabot alerts and structurize.
"""

from __future__ import annotations


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# @SID: DEPENDABOT_INDEX_V1

import argparse
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SEVERITY_RANK = {"critical": 0, "high": 1, "moderate": 2, "low": 3, "unknown": 4}


def gh_api(path: str) -> list[dict]:
    result = subprocess.run(
        ["gh", "api", path, "--paginate"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(f"gh api {path} failed: {result.stderr}")
    # --paginate concatenates pages as multiple JSON arrays; gh joins them
    # into one stream. Parse defensively.
    out = result.stdout.strip()
    if not out:
        return []
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        # Multiple arrays concatenated — flatten.
        alerts: list[dict] = []
        for chunk in out.split("]["):
            chunk = chunk.strip()
            if not chunk.startswith("["):
                chunk = "[" + chunk
            if not chunk.endswith("]"):
                chunk = chunk + "]"
            try:
                alerts.extend(json.loads(chunk))
            except json.JSONDecodeError:
                continue
        return alerts


def classify(alert: dict) -> dict:
    """Flatten one alert into a stable schema."""
    dep = alert.get("dependency") or {}
    pkg = dep.get("package") or {}
    adv = alert.get("security_advisory") or {}
    vuln = alert.get("security_vulnerability") or {}
    return {
        "number": alert.get("number"),
        "state": alert.get("state"),
        "severity": (adv.get("severity") or vuln.get("severity") or "unknown").lower(),
        "ecosystem": pkg.get("ecosystem"),
        "package": pkg.get("name"),
        "manifest_path": dep.get("manifest_path"),
        "scope": dep.get("scope"),
        "relationship": dep.get("relationship"),  # direct / transitive
        "cve_id": adv.get("cve_id"),
        "ghsa_id": adv.get("ghsa_id"),
        "summary": (adv.get("summary") or "").strip(),
        "fix_available": vuln.get("first_patched_version") is not None,
        "fixed_in": (vuln.get("first_patched_version") or {}).get("identifier"),
        "created_at": alert.get("created_at"),
        "url": alert.get("html_url"),
    }


def build_index(repo: str, state_filter: str | None) -> dict:
    print(f"[dependabot_index] fetching alerts for {repo} ...", file=sys.stderr)
    raw = gh_api(f"repos/{repo}/dependabot/alerts")
    print(f"[dependabot_index] {len(raw)} alerts total", file=sys.stderr)

    alerts = [classify(a) for a in raw]
    if state_filter:
        alerts = [a for a in alerts if a["state"] == state_filter]

    by_state = Counter(a["state"] for a in alerts)
    by_severity = Counter(a["severity"] for a in alerts)
    by_ecosystem = Counter(a["ecosystem"] for a in alerts)
    by_scope = Counter(a["scope"] for a in alerts)
    by_relationship = Counter(a["relationship"] for a in alerts)
    fix_available = sum(1 for a in alerts if a["fix_available"])

    # Hotspots: packages with multiple alerts (same dependency, multiple CVEs).
    pkg_counts: Counter[tuple[str | None, str | None]] = Counter(
        (a["ecosystem"], a["package"]) for a in alerts
    )
    hotspots = [
        {"ecosystem": e, "package": p, "alert_count": n}
        for (e, p), n in pkg_counts.most_common()
        if n >= 2
    ]

    # Prioritize: open + (critical|high) + fix_available + direct dependency.
    def priority_key(a: dict) -> tuple:
        return (
            0 if a["state"] == "open" else 1,
            SEVERITY_RANK.get(a["severity"], 9),
            0 if a["fix_available"] else 1,
            0 if a["relationship"] == "direct" else 1,
            (a["ecosystem"] or "zzz"),
            (a["package"] or "zzz"),
        )

    alerts_sorted = sorted(alerts, key=priority_key)

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo": repo,
        "state_filter": state_filter,
        "summary": {
            "total": len(alerts),
            "by_state": dict(by_state),
            "by_severity": dict(by_severity),
            "by_ecosystem": dict(by_ecosystem),
            "by_scope": dict(by_scope),
            "by_relationship": dict(by_relationship),
            "fix_available_count": fix_available,
            "hotspot_package_count": len(hotspots),
        },
        "hotspots": hotspots,
        "alerts": alerts_sorted,
    }


def write_md(index: dict, top_n: int = 25) -> str:
    s = index["summary"]
    lines = [
        "# Dependabot index digest",
        "",
        f"Generated: {index['generated_at']}",
        f"Repo: `{index['repo']}`",
        f"Source: `manifest/dependabot_index.json` (regenerate via `uv run scripts/dependabot_index.py`)",
        "",
        "## Summary",
        "",
        f"- Total alerts: {s['total']}",
        f"- Fix available: {s['fix_available_count']} / {s['total']}",
        f"- Hotspot packages (>=2 alerts each): {s['hotspot_package_count']}",
        "",
        "### By state",
        "",
    ]
    for k, n in sorted(s["by_state"].items(), key=lambda kv: -kv[1]):
        lines.append(f"- `{k}`: {n}")
    lines += ["", "### By severity", ""]
    for k, n in sorted(s["by_severity"].items(), key=lambda kv: -kv[1]):
        lines.append(f"- `{k}`: {n}")
    lines += ["", "### By ecosystem", ""]
    for k, n in sorted(s["by_ecosystem"].items(), key=lambda kv: -kv[1]):
        lines.append(f"- `{k}`: {n}")
    lines += ["", "### By relationship (direct = actionable, transitive = upstream wait)", ""]
    for k, n in sorted(s["by_relationship"].items(), key=lambda kv: -kv[1]):
        lines.append(f"- `{k}`: {n}")

    if index["hotspots"]:
        lines += ["", "## Hotspot packages (one package, multiple CVEs)", ""]
        for h in index["hotspots"][:15]:
            lines.append(f"- `{h['ecosystem']}/{h['package']}` — {h['alert_count']} alerts")

    lines += ["", f"## Top {top_n} alerts (priority order)", ""]
    lines.append("Sort key: open before non-open, severity rank, fix-available, direct over transitive.")
    lines.append("")
    for a in index["alerts"][:top_n]:
        fix = f"fix:{a['fixed_in']}" if a["fix_available"] else "no-fix-yet"
        rel = a["relationship"] or "?"
        lines.append(
            f"### [{(a['severity'] or '?').upper()} / {a['state']}] "
            f"`{a['ecosystem']}/{a['package']}` ({rel}, {fix})"
        )
        lines.append("")
        if a["summary"]:
            summary = a["summary"].split("\n")[0]
            if len(summary) > 200:
                summary = summary[:200] + "..."
            lines.append(f"- {summary}")
        if a["cve_id"]:
            lines.append(f"- {a['cve_id']} · {a['ghsa_id']}")
        if a["manifest_path"]:
            lines.append(f"- manifest: `{a['manifest_path']}`")
        if a["url"]:
            lines.append(f"- view: {a['url']}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(prog="dependabot_index")
    p.add_argument("--repo", default="poisontr33s/chthonic-archive",
                   help="owner/repo (default: poisontr33s/chthonic-archive)")
    p.add_argument("--state", default=None,
                   help="filter to a state: open / fixed / dismissed / auto_dismissed")
    p.add_argument("--top", type=int, default=25,
                   help="entries in markdown digest top-N")
    p.add_argument("--no-md", action="store_true", help="skip markdown digest")
    p.add_argument("--out-json", default="manifest/dependabot_index.json")
    p.add_argument("--out-md", default="manifest/dependabot_index.md")
    args = p.parse_args()

    index = build_index(args.repo, args.state)
    out_json = REPO_ROOT / args.out_json
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[dependabot_index] wrote {out_json}")

    if not args.no_md:
        out_md = REPO_ROOT / args.out_md
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_md.write_text(write_md(index, top_n=args.top), encoding="utf-8")
        print(f"[dependabot_index] wrote {out_md}")

    s = index["summary"]
    print(f"[dependabot_index] {s['total']} alerts; "
          f"severity={s['by_severity']}; "
          f"fix_available={s['fix_available_count']}; "
          f"hotspots={s['hotspot_package_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
