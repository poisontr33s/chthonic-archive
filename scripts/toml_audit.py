#!/usr/bin/env python3
#-*- coding: utf-8 -*-
# @SID: TOOL_TOML_AUDIT_V1
"""
TOML Audit — chthonic-archive workspace TOML inventory + PyPI version comparison.

Discovers all .toml files across the repository, classifies them by type, and for
pyproject.toml files: extracts all declared dependencies (core + dependency-groups),
queries the PyPI JSON API for latest stable versions, and reports deltas.

Usage:
    uv run scripts/toml_audit.py                    # inventory only (no network)
    uv run scripts/toml_audit.py --compare-pypi     # add PyPI latest-stable lookup
    uv run scripts/toml_audit.py --json             # JSON output to stdout
    uv run scripts/toml_audit.py --report FILE      # write markdown report
    uv run scripts/toml_audit.py --authored-only    # only git-tracked authored files
    uv run scripts/toml_audit.py --pyproject-only   # only pyproject.toml files
"""

import argparse
import json
import subprocess
import sys
import tomllib
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent

_IGNORE_DIRS = frozenset(
    {
        ".git",
        ".venv",
        "node_modules",
        "__pycache__",
        "target",          # Rust build artifacts
        ".deprecated",
        "dumpster-dive",
        "debugging_data",
        "filesystem_root",
        "mcp_fs_root",
        "pr2_review",
    }
)

# Known TOML types by filename pattern
_TOML_TYPE_MAP = {
    "pyproject.toml": "python/uv",
    "Cargo.toml": "rust/cargo",
    "uv.toml": "uv-config",
    "bunfig.toml": "bun-config",
    "book.toml": "mdbook",
    "rproject.toml": "r-project",
    "rust-toolchain.toml": "rust-toolchain",
    "zig-toolchain.toml": "zig-toolchain",
    "mise.toml": "mise",
    "pixi.toml": "pixi",
    "config.toml": "config",
    ".air.toml": "air-config",
    "hugo.toml": "hugo",
    "netlify.toml": "netlify",
}

PYPI_API = "https://pypi.org/pypi/{package}/json"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class TomlFile:
    rel: str           # repo-relative path (posix)
    kind: str          # type classification
    origin: str        # "authored" | "framework" | "unknown"
    project_name: Optional[str] = None    # for pyproject.toml only
    project_ver: Optional[str] = None


@dataclass
class DepEntry:
    package: str       # normalised (lower, hyphens)
    spec: str          # raw spec string e.g. ">=3.6.1,<4"
    group: str         # "core" | dep-group name
    source_file: str   # repo-relative path
    latest_pypi: Optional[str] = None
    status: str = "unknown"   # "ok" | "behind" | "ahead" | "error" | "unknown"


@dataclass
class AuditResult:
    toml_files: list[TomlFile] = field(default_factory=list)
    dep_entries: list[DepEntry] = field(default_factory=list)
    pypi_queried: bool = False
    errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _git_tracked_set(repo: Path) -> set[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    return set(result.stdout.splitlines())


def _rel_posix(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _classify_kind(fname: str) -> str:
    return _TOML_TYPE_MAP.get(fname, "other")


def _normalise_pkg(name: str) -> str:
    return name.lower().replace("_", "-").strip()


def _parse_dep_spec(raw: str) -> tuple[str, str]:
    """Return (package_name, spec_string) from a PEP 508 dep string."""
    # Strip extras, env markers, comments
    raw = raw.split(";")[0].strip()
    raw = raw.split("#")[0].strip()
    # Split on first comparator or space
    import re
    m = re.match(r'^([A-Za-z0-9._-]+\[?[A-Za-z0-9,._-]*\]?)(.*)$', raw)
    if m:
        pkg = _normalise_pkg(m.group(1).split("[")[0])
        spec = m.group(2).strip()
        return pkg, spec
    return _normalise_pkg(raw), ""


def _discover_toml_files(authored_filter: bool = False) -> list[tuple[Path, str]]:
    """Walk repo and return (abs_path, rel_posix) for all .toml files."""
    tracked = _git_tracked_set(REPO_ROOT) if authored_filter else set()
    results: list[tuple[Path, str]] = []

    for toml_path in REPO_ROOT.rglob("*.toml"):
        # Skip ignored dirs
        parts = toml_path.relative_to(REPO_ROOT).parts
        if any(p in _IGNORE_DIRS for p in parts):
            continue
        rel = _rel_posix(toml_path)
        if authored_filter and rel not in tracked:
            continue
        results.append((toml_path, rel))

    return sorted(results, key=lambda x: x[1])


def _extract_pyproject_deps(toml_path: Path, rel: str) -> tuple[Optional[str], Optional[str], list[DepEntry]]:
    """Parse a pyproject.toml and return (project_name, project_version, [DepEntry])."""
    try:
        with open(toml_path, "rb") as f:
            data = tomllib.load(f)
    except Exception as e:
        return None, None, []

    project = data.get("project", {})
    name = project.get("name")
    ver = project.get("version")
    entries: list[DepEntry] = []

    # Core dependencies
    for raw in project.get("dependencies", []):
        if not raw or raw.startswith("#"):
            continue
        pkg, spec = _parse_dep_spec(raw)
        if pkg:
            entries.append(DepEntry(package=pkg, spec=spec, group="core", source_file=rel))

    # Dependency groups ([dependency-groups])
    dep_groups = data.get("dependency-groups", {})
    for grp_name, grp_deps in dep_groups.items():
        for raw in grp_deps:
            if not raw or not isinstance(raw, str) or raw.startswith("#"):
                continue
            # Skip workspace references like {path = ...} or {workspace = true}
            if raw.startswith("{"):
                continue
            pkg, spec = _parse_dep_spec(raw)
            if pkg:
                entries.append(DepEntry(package=pkg, spec=spec, group=grp_name, source_file=rel))

    # Optional deps ([project.optional-dependencies])
    opt_deps = project.get("optional-dependencies", {})
    for opt_name, opt_list in opt_deps.items():
        for raw in opt_list:
            if not raw or raw.startswith("#"):
                continue
            pkg, spec = _parse_dep_spec(raw)
            if pkg:
                entries.append(DepEntry(package=pkg, spec=spec, group=f"optional/{opt_name}", source_file=rel))

    return name, ver, entries


def _pypi_latest(package: str) -> tuple[Optional[str], Optional[str]]:
    """Return (latest_stable_version, error_message) from PyPI JSON API."""
    url = PYPI_API.format(package=package)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "chthonic-toml-audit/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
            body = json.loads(resp.read())
        ver = body.get("info", {}).get("version")
        return ver, None
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None, f"not-found (404)"
        return None, f"HTTP {e.code}"
    except Exception as e:
        return None, str(e)


def _compare_versions(spec: str, latest: str) -> str:
    """Rough comparison: is latest_stable satisfying the current constraint?"""
    if not spec or not latest:
        return "unknown"
    try:
        from packaging.requirements import Requirement
        from packaging.version import Version
        r = Requirement(f"pkg{spec}")
        v = Version(latest)
        if v in r.specifier:
            return "ok"
        else:
            return "behind"
    except Exception:
        return "unknown"


# ---------------------------------------------------------------------------
# Core pipeline
# ---------------------------------------------------------------------------


def run_audit(
    authored_only: bool = False,
    pyproject_only: bool = False,
    compare_pypi: bool = False,
) -> AuditResult:
    result = AuditResult(pypi_queried=compare_pypi)

    toml_files = _discover_toml_files(authored_filter=authored_only)
    tracked = _git_tracked_set(REPO_ROOT)

    for abs_path, rel in toml_files:
        fname = abs_path.name
        kind = _classify_kind(fname)
        origin_str = "authored" if rel in tracked else "framework" if tracked else "unknown"
        tf = TomlFile(rel=rel, kind=kind, origin=origin_str)

        if fname == "pyproject.toml":
            proj_name, proj_ver, deps = _extract_pyproject_deps(abs_path, rel)
            tf.project_name = proj_name
            tf.project_ver = proj_ver
            result.dep_entries.extend(deps)

        if pyproject_only and fname != "pyproject.toml":
            continue
        result.toml_files.append(tf)

    if compare_pypi and result.dep_entries:
        # Deduplicate: one lookup per unique package name
        seen: dict[str, str] = {}
        for entry in result.dep_entries:
            if entry.package not in seen:
                latest, err = _pypi_latest(entry.package)
                if err:
                    seen[entry.package] = f"error:{err}"
                elif latest:
                    seen[entry.package] = latest
                else:
                    seen[entry.package] = "unknown"

        for entry in result.dep_entries:
            raw = seen.get(entry.package, "unknown")
            if raw.startswith("error:"):
                entry.status = "error"
                entry.latest_pypi = raw[6:]
            else:
                entry.latest_pypi = raw
                entry.status = _compare_versions(entry.spec, raw)

    return result


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def _render_text(result: AuditResult, pyproject_only: bool) -> str:
    lines: list[str] = []

    lines.append("# TOML Audit Report — chthonic-archive\n")

    # TOML file inventory
    lines.append(f"## TOML Files ({len(result.toml_files)} found)\n")
    lines.append(f"{'File':<60} {'Type':<16} {'Origin'}")
    lines.append("-" * 90)
    for tf in result.toml_files:
        lines.append(f"{tf.rel:<60} {tf.kind:<16} {tf.origin}")
    lines.append("")

    if not result.dep_entries:
        return "\n".join(lines)

    # Group deps by source file
    from collections import defaultdict
    by_file: dict[str, list[DepEntry]] = defaultdict(list)
    for e in result.dep_entries:
        by_file[e.source_file].append(e)

    lines.append(f"## Python Dependencies ({len(result.dep_entries)} total)\n")

    for src_file, deps in sorted(by_file.items()):
        lines.append(f"### {src_file}\n")
        lines.append(f"{'Package':<35} {'Group':<20} {'Spec':<25} {'Latest':<15} Status")
        lines.append("-" * 110)
        for d in sorted(deps, key=lambda x: (x.group, x.package)):
            latest = d.latest_pypi or ("-" if result.pypi_queried else "(no lookup)")
            status = d.status if result.pypi_queried else ""
            status_icon = {"ok": "✓", "behind": "↑", "error": "✗", "unknown": "?", "": ""}.get(status, "")
            lines.append(
                f"{d.package:<35} {d.group:<20} {d.spec:<25} {latest:<15} {status_icon} {status}"
            )
        lines.append("")

    if result.pypi_queried:
        behind = [d for d in result.dep_entries if d.status == "behind"]
        ok = [d for d in result.dep_entries if d.status == "ok"]
        errors = [d for d in result.dep_entries if d.status == "error"]
        lines.append(f"## Summary")
        lines.append(f"  ✓ Up-to-date: {len(ok)}")
        lines.append(f"  ↑ Behind:     {len(behind)}")
        lines.append(f"  ✗ Errors:     {len(errors)}")
        if behind:
            lines.append("\n### Packages behind latest stable:")
            for d in behind:
                lines.append(f"  {d.package:<35} pinned: {d.spec:<20} latest: {d.latest_pypi} ({d.source_file})")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(
        description="TOML inventory + PyPI version audit for chthonic-archive workspace."
    )
    ap.add_argument("--compare-pypi", action="store_true",
                    help="Query PyPI JSON API for latest stable version of each dep")
    ap.add_argument("--json", action="store_true",
                    help="JSON output to stdout")
    ap.add_argument("--report", metavar="FILE",
                    help="Write markdown/text report to FILE")
    ap.add_argument("--authored-only", action="store_true",
                    help="Only include git-tracked authored files")
    ap.add_argument("--pyproject-only", action="store_true",
                    help="Only surface pyproject.toml files and their deps")
    args = ap.parse_args()

    result = run_audit(
        authored_only=args.authored_only,
        pyproject_only=args.pyproject_only,
        compare_pypi=args.compare_pypi,
    )

    if args.json:
        out = {
            "toml_files": [asdict(t) for t in result.toml_files],
            "dep_entries": [asdict(d) for d in result.dep_entries],
            "pypi_queried": result.pypi_queried,
            "errors": result.errors,
        }
        print(json.dumps(out, indent=2))
        return 0

    text = _render_text(result, pyproject_only=args.pyproject_only)

    if args.report:
        rp = Path(args.report)
        rp.parent.mkdir(parents=True, exist_ok=True)
        rp.write_text(text, encoding="utf-8")
        print(f"[toml-audit] Report written to {rp}")
    else:
        print(text)

    return 0


if __name__ == "__main__":
    sys.exit(main())
