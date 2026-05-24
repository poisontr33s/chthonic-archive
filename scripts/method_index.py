#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: method_index.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: GOLD
# ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Meta-lens — compounds on git_rot_index, dependabot_index, github_activity_index)
# ╚════════════════════════════════════════════════════════════════════════════

"""
scripts/method_index.py - Meta-lens. Observes the methods that cleared prior lenses.

Methodology: "Gitological Noise As Structured Data — Lens observes the methods
that cleared the prior lenses." Compounds on top of git_rot_index, dependabot_index,
and github_activity_index. Methods become data, not memory.

Walks recent commits (default 60 days). Classifies each commit by diff signature:
which method-class did it apply? Aggregates per-class: frequency, last-used,
example SHAs, the noise-class it addresses, suggested invocation string.

Emits:
  manifest/method_index.json  - machine-readable snapshot
  manifest/method_index.md    - human-readable digest

Re-run anytime to refresh.

Usage:
  uv run scripts/method_index.py                    # default 60-day window
  uv run scripts/method_index.py --since 90         # 90-day window
  uv run scripts/method_index.py --no-md            # skip markdown digest

@SID:           METHOD_INDEX_V1
@Shabti:        CLI Script
@Purpose:       Meta-lens that observes successful methods per noise class.
"""

from __future__ import annotations

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


# @SID: METHOD_INDEX_V1

import argparse
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


METHOD_CATALOG: dict[str, dict] = {
    "uv-lock-upgrade": {
        "noise_class": "dependabot/pip-transitive",
        "suggested_invocation": "uv lock --upgrade-package <pkg>",
    },
    "python-constraint-bump": {
        "noise_class": "dependabot/pip-direct-pinned",
        "suggested_invocation": "edit pyproject.toml dependency cap, then uv lock",
    },
    "cargo-update": {
        "noise_class": "dependabot/rust-transitive",
        "suggested_invocation": "cargo update -p <pkg> (in directory of Cargo.lock)",
    },
    "rust-constraint-bump": {
        "noise_class": "dependabot/rust-direct-pinned",
        "suggested_invocation": "edit Cargo.toml dependency version, then cargo update",
    },
    "bun-update": {
        "noise_class": "dependabot/npm-transitive",
        "suggested_invocation": "bun update <pkg> (in directory of bun.lock)",
    },
    "npm-constraint-bump": {
        "noise_class": "dependabot/npm-direct-pinned",
        "suggested_invocation": "edit package.json dependency version, then bun update",
    },
    "tombstone-mark": {
        "noise_class": "rot/L1-surface-cluster",
        "suggested_invocation": "add `lifecycle: tombstone` to file frontmatter",
    },
    "stub-creation": {
        "noise_class": "rot/ROT-001-phantom-target",
        "suggested_invocation": "create new file with `lifecycle: stub` frontmatter",
    },
    "anchor-correction": {
        "noise_class": "rot/L3-anchor",
        "suggested_invocation": "fix link path or anchor (e.g., `../` -> `../../`)",
    },
    "path-rename-followup": {
        "noise_class": "rot/L4-lineage",
        "suggested_invocation": "batch-update broken refs across multiple files (one logical move)",
    },
    "code-fence-fix": {
        "noise_class": "rot/false-positive-code-block",
        "suggested_invocation": "wrap code block in triple-backtick fences",
    },
}


def git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr}")
    return result.stdout


def parse_log_stream(since_iso: str) -> list[dict]:
    """
    Walk recent commits with sentinel stream pattern.
    Each commit block:
      __C__<sha>
      <ISO date>
      <subject>
      <path 1>
      <path 2>
      ...
      (blank line between commits)
    Mirrors parse_sentinel_stream() from git_rot_index.py.
    """
    out = git(
        "log", "--name-only",
        f"--since={since_iso}",
        "--format=__C__%H%n%aI%n%s",
        check=False,
    )
    commits: list[dict] = []
    cur: dict | None = None
    for raw in out.splitlines():
        line = raw.rstrip()
        if line.startswith("__C__"):
            if cur is not None:
                commits.append(cur)
            cur = {
                "sha": line[5:].strip(),
                "date": "",
                "subject": "",
                "paths": [],
            }
            state = "date"
            continue
        if cur is None:
            continue
        if state == "date":
            cur["date"] = line.strip()
            state = "subject"
            continue
        if state == "subject":
            cur["subject"] = line.strip()
            state = "paths"
            continue
        if line.strip():
            cur["paths"].append(line.strip())
    if cur is not None:
        commits.append(cur)
    return commits


def get_diff(sha: str) -> str:
    """Cheap unified diff for one commit. Empty string on error."""
    try:
        return git("show", "--no-color", "--format=", "--unified=0", sha, check=False)
    except (RuntimeError, OSError):
        return ""


def _sibling_toml_changed(paths: list[str], lock_path: str, toml_name: str) -> bool:
    """True if Cargo.toml/pyproject.toml/package.json in the same dir as the lock was touched."""
    lock_dir = lock_path.rsplit("/", 1)[0] if "/" in lock_path else ""
    sibling = f"{lock_dir}/{toml_name}".lstrip("/")
    return sibling in paths or (lock_dir == "" and toml_name in paths)


def classify_commit(commit: dict) -> tuple[str | None, float]:
    """
    Return (method_name, confidence) or (None, 0.0) if no method matches.
    Cheap classification first (paths only); diff inspection only when needed.
    """
    paths = commit["paths"]
    subject = commit["subject"].lower()

    md_paths = [p for p in paths if p.endswith(".md")]
    pip_locks = [p for p in paths if p == "uv.lock"]
    pip_tomls = [p for p in paths if p == "pyproject.toml"]
    cargo_locks = [p for p in paths if p.endswith("/Cargo.lock") or p == "Cargo.lock"]
    cargo_tomls = [p for p in paths if p.endswith("/Cargo.toml") or p == "Cargo.toml"]
    bun_locks = [p for p in paths if p.endswith("/bun.lock") or p == "bun.lock"]
    pkg_jsons = [p for p in paths if p.endswith("/package.json") or p == "package.json"]

    # Python ecosystem
    if pip_locks and not pip_tomls:
        return ("uv-lock-upgrade", 1.0)
    if pip_tomls and pip_locks:
        diff = get_diff(commit["sha"])
        if re.search(r"^[-+]\s*\"[a-zA-Z0-9_.\-]+[<>=]", diff, re.MULTILINE):
            return ("python-constraint-bump", 1.0)
        return ("uv-lock-upgrade", 0.5)
    if pip_tomls and not pip_locks:
        return ("python-constraint-bump", 0.7)

    # Rust ecosystem (per-manifest sibling check)
    if cargo_locks and not any(
        _sibling_toml_changed(paths, lock, "Cargo.toml") for lock in cargo_locks
    ):
        return ("cargo-update", 1.0)
    if cargo_tomls and cargo_locks:
        return ("rust-constraint-bump", 1.0)
    if cargo_tomls and not cargo_locks:
        return ("rust-constraint-bump", 0.7)

    # JS ecosystem
    if bun_locks and not any(
        _sibling_toml_changed(paths, lock, "package.json") for lock in bun_locks
    ):
        return ("bun-update", 1.0)
    if pkg_jsons and bun_locks:
        return ("npm-constraint-bump", 1.0)
    if pkg_jsons and not bun_locks:
        # could be docs-style edit; require subject signal
        if any(k in subject for k in ("dep", "version", "upgrade", "bump", "update")):
            return ("npm-constraint-bump", 0.6)

    # Markdown methods
    if md_paths:
        diff = get_diff(commit["sha"])

        # tombstone-mark: diff adds `lifecycle: tombstone`
        if re.search(r"^\+\s*lifecycle:\s*tombstone\b", diff, re.MULTILINE):
            return ("tombstone-mark", 1.0)

        # stub-creation: diff adds `lifecycle: stub` (typically in a new file)
        if re.search(r"^\+\s*lifecycle:\s*stub\b", diff, re.MULTILINE):
            return ("stub-creation", 1.0)

        # code-fence-fix: diff adds triple-backtick fences
        plus_fences = len(re.findall(r"^\+```", diff, re.MULTILINE))
        minus_fences = len(re.findall(r"^-```", diff, re.MULTILINE))
        if plus_fences - minus_fences >= 2 and "fence" in subject:
            return ("code-fence-fix", 1.0)

        # path-rename-followup: >3 md files changed + same kind of link edit
        if len(md_paths) > 3 and re.search(r"^[-+].*\]\([^)]+\)", diff, re.MULTILINE):
            if any(k in subject for k in ("rename", "move", "consolidat", "link", "path", "anchor")):
                return ("path-rename-followup", 0.8)

        # anchor-correction: link path changed (depth shift, anchor fix)
        # Heuristic: same line has - and + with a markdown link, path component differs
        if re.search(r"^-.*\.\./.*\]\(", diff, re.MULTILINE) and \
           re.search(r"^\+.*\.\./.*\]\(", diff, re.MULTILINE):
            return ("anchor-correction", 0.8)
        # Also: subject mentions anchor/depth/rot
        if any(k in subject for k in ("anchor", "rot", "broken ref", "depth-bug", "link-rot")):
            return ("anchor-correction", 0.6)

    return (None, 0.0)


def build_index(since_days: int) -> dict:
    cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)
    since_iso = cutoff.isoformat()

    print(f"[method_index] scanning commits since {since_iso[:10]} ...", file=sys.stderr)
    commits = parse_log_stream(since_iso)
    print(f"[method_index] {len(commits)} commits in window", file=sys.stderr)

    classified: dict[str, list[dict]] = defaultdict(list)
    confidence_total: dict[str, float] = defaultdict(float)
    unclassified = 0

    for c in commits:
        name, conf = classify_commit(c)
        if name is None:
            unclassified += 1
            continue
        classified[name].append({
            "sha": c["sha"][:8],
            "date": c["date"],
            "subject": c["subject"],
            "confidence": conf,
        })
        confidence_total[name] += conf

    methods: list[dict] = []
    for name, entries in classified.items():
        entries_sorted = sorted(entries, key=lambda e: e["date"], reverse=True)
        cat = METHOD_CATALOG.get(name, {})
        methods.append({
            "name": name,
            "frequency": len(entries),
            "confidence_avg": round(confidence_total[name] / max(len(entries), 1), 2),
            "last_used_at": entries_sorted[0]["date"] if entries_sorted else None,
            "noise_class": cat.get("noise_class", "unknown"),
            "suggested_invocation": cat.get("suggested_invocation", ""),
            "example_commits": [
                {"sha": e["sha"], "subject": e["subject"]}
                for e in entries_sorted[:3]
            ],
        })

    methods.sort(key=lambda m: -m["frequency"])

    by_method = Counter()
    for name, entries in classified.items():
        by_method[name] = len(entries)

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "since": since_iso,
        "since_days": since_days,
        "summary": {
            "total_commits_scanned": len(commits),
            "total_methodful_commits": len(commits) - unclassified,
            "unclassified_commits": unclassified,
            "by_method": dict(by_method),
            "method_classes_seen": len(methods),
        },
        "methods": methods,
    }


def write_md(index: dict) -> str:
    s = index["summary"]
    lines = [
        "# Method index digest",
        "",
        f"Generated: {index['generated_at']}",
        f"Window: last {index['since_days']} days (since {index['since'][:10]})",
        f"Source: `manifest/method_index.json` (regenerate via `uv run scripts/method_index.py`)",
        "",
        "Methodology: meta-lens that observes which methods cleared prior lens noise.",
        "Compounds with `git_rot_index`, `dependabot_index`, `github_activity_index`.",
        "",
        "## Summary",
        "",
        f"- Commits scanned: {s['total_commits_scanned']}",
        f"- Methodful commits: {s['total_methodful_commits']}",
        f"- Unclassified: {s['unclassified_commits']}",
        f"- Distinct method classes seen: {s['method_classes_seen']}",
        "",
        "### By method (frequency)",
        "",
    ]
    for name, n in sorted(s["by_method"].items(), key=lambda kv: -kv[1]):
        lines.append(f"- `{name}`: {n}")

    lines += ["", "## Methods (priority: most-used first)", ""]
    for m in index["methods"]:
        lines.append(f"### `{m['name']}` — used {m['frequency']}x (conf {m['confidence_avg']})")
        lines.append("")
        lines.append(f"- Noise class: `{m['noise_class']}`")
        lines.append(f"- Last used: {(m['last_used_at'] or '')[:10]}")
        lines.append(f"- Invocation: `{m['suggested_invocation']}`")
        if m["example_commits"]:
            lines.append("- Examples:")
            for ex in m["example_commits"]:
                lines.append(f"  - `{ex['sha']}` — {ex['subject']}")
        lines.append("")

    # Catalog: classes defined but not yet seen
    seen = {m["name"] for m in index["methods"]}
    unseen = [n for n in METHOD_CATALOG if n not in seen]
    if unseen:
        lines += ["## Catalog (defined, not yet observed in window)", ""]
        for name in unseen:
            cat = METHOD_CATALOG[name]
            lines.append(f"- `{name}` → addresses `{cat['noise_class']}`")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(prog="method_index")
    p.add_argument("--since", type=int, default=60,
                   help="window in days (default: 60)")
    p.add_argument("--no-md", action="store_true", help="skip markdown digest")
    p.add_argument("--out-json", default="manifest/method_index.json")
    p.add_argument("--out-md", default="manifest/method_index.md")
    args = p.parse_args()

    index = build_index(args.since)
    out_json = REPO_ROOT / args.out_json
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[method_index] wrote {out_json}")

    if not args.no_md:
        out_md = REPO_ROOT / args.out_md
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_md.write_text(write_md(index), encoding="utf-8")
        print(f"[method_index] wrote {out_md}")

    s = index["summary"]
    print(f"[method_index] {s['total_methodful_commits']}/{s['total_commits_scanned']} commits classified; "
          f"classes={s['method_classes_seen']}; "
          f"top={list(s['by_method'].items())[:3]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
