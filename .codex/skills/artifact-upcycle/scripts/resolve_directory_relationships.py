#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""
Directory relationship resolver for Artifact-Upcycle.

Scans file/directory references, classifies unresolved or ambiguous links,
and reports whether manual intervention is required.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


TEXT_EXTENSIONS = {
    ".md",
    ".txt",
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
    ".ps1",
    ".rs",
    ".json",
    ".toml",
    ".yaml",
    ".yml",
    ".html",
    ".css",
    ".scss",
}

SKIP_DIRS = {
    ".git",
    ".venv",
    ".ruff_cache",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    "target",
}

MD_LINK_RE = re.compile(r"\[[^\]]*]\(([^)]+)\)")
IMPORT_RE = re.compile(
    r"""(?:
        import\s+[^'"\n]+?\s+from\s+['"]([^'"]+)['"]|
        from\s+['"]([^'"]+)['"]\s+import|
        require\(\s*['"]([^'"]+)['"]\s*\)
    )""",
    re.VERBOSE,
)


@dataclass
class Reference:
    source: Path
    raw: str
    kind: str
    resolved: Optional[Path]
    exists: bool
    candidates: List[Path]
    reason: Optional[str] = None


def discover_repo_root(seed: Path) -> Path:
    current = seed if seed.is_dir() else seed.parent
    for node in [current, *current.parents]:
        if (node / ".git").exists() or (node / "AGENTS.md").exists():
            return node
    return current


def to_posix(path: Path) -> str:
    return path.as_posix()


def repo_rel(path: Path, repo_root: Path) -> str:
    try:
        return to_posix(path.relative_to(repo_root))
    except ValueError:
        return to_posix(path)


def relative_from(source_dir: Path, target_path: Path) -> str:
    try:
        return to_posix(Path(os.path.relpath(target_path, start=source_dir)))
    except ValueError:
        # Different drive edge-case on Windows; fall back to absolute POSIX.
        return to_posix(target_path)


def iter_text_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*"):
        if p.is_dir():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.suffix.lower() in TEXT_EXTENSIONS:
            yield p


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def extract_refs(source: Path, content: str) -> List[tuple[str, str]]:
    refs: List[tuple[str, str]] = []
    for match in MD_LINK_RE.finditer(content):
        refs.append(("md_link", match.group(1).strip()))

    if source.suffix.lower() in {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py"}:
        for match in IMPORT_RE.finditer(content):
            raw = next((g for g in match.groups() if g), "")
            raw = raw.strip()
            if raw:
                refs.append(("import", raw))

    return refs


def is_local_reference(raw: str) -> bool:
    if not raw:
        return False
    lowered = raw.lower()
    if lowered.startswith(("http://", "https://", "mailto:", "data:")):
        return False
    if lowered.startswith("#"):
        return False
    return True


def normalize_reference(raw: str) -> str:
    normalized = raw.strip().replace("\\", "/")
    if "#" in normalized:
        normalized = normalized.split("#", 1)[0]
    return normalized.strip()


def resolve_reference(source: Path, raw: str, repo_root: Path) -> Optional[Path]:
    normalized = normalize_reference(raw)
    if not normalized or not is_local_reference(normalized):
        return None

    if normalized.startswith("/"):
        target = (repo_root / normalized.lstrip("/")).resolve()
    else:
        target = (source.parent / normalized).resolve()
    return target


def candidate_paths_for_missing(raw: str, repo_files: List[Path]) -> List[Path]:
    normalized = normalize_reference(raw)
    name = Path(normalized).name
    if not name:
        return []
    return [p for p in repo_files if p.name == name]


def build_reference_indexes(
    repo_files: List[Path],
    repo_root: Path,
) -> Tuple[Dict[Path, List[Tuple[str, str]]], Dict[Path, List[Dict[str, Any]]], Dict[str, List[Path]]]:
    parsed_refs_by_file: Dict[Path, List[Tuple[str, str]]] = {}
    inbound_index: Dict[Path, List[Dict[str, Any]]] = {}
    name_index: Dict[str, List[Path]] = {}

    for source in repo_files:
        name_index.setdefault(source.name, []).append(source)
        content = read_text(source)
        refs = extract_refs(source, content)
        parsed_refs_by_file[source] = refs

        for kind, raw in refs:
            resolved = resolve_reference(source, raw, repo_root)
            if resolved is None:
                continue
            inbound_index.setdefault(resolved, []).append(
                {
                    "source": repo_rel(source, repo_root),
                    "kind": kind,
                    "raw": raw,
                }
            )

    return parsed_refs_by_file, inbound_index, name_index


def analyze_references_for_file(
    target_file: Path,
    repo_root: Path,
    repo_files: List[Path],
    parsed_refs_by_file: Optional[Dict[Path, List[Tuple[str, str]]]] = None,
    inbound_index: Optional[Dict[Path, List[Dict[str, Any]]]] = None,
    name_index: Optional[Dict[str, List[Path]]] = None,
) -> Dict[str, Any]:
    if parsed_refs_by_file is not None and target_file in parsed_refs_by_file:
        refs = parsed_refs_by_file[target_file]
    else:
        content = read_text(target_file)
        refs = extract_refs(target_file, content)

    outbound: List[Reference] = []
    manual_reasons: List[str] = []
    auto_fixes: List[Dict[str, Any]] = []

    for kind, raw in refs:
        resolved = resolve_reference(target_file, raw, repo_root)
        if resolved is None:
            continue

        exists = resolved.exists()
        candidates: List[Path] = []
        reason: Optional[str] = None

        if not exists:
            if name_index is not None:
                name = Path(normalize_reference(raw)).name
                candidates = list(name_index.get(name, [])) if name else []
            else:
                candidates = candidate_paths_for_missing(raw, repo_files)
            if len(candidates) == 1:
                candidate = candidates[0]
                rel = relative_from(target_file.parent.resolve(), candidate)
                auto_fixes.append(
                    {
                        "source": repo_rel(target_file, repo_root),
                        "kind": kind,
                        "raw": raw,
                        "suggested": rel,
                        "reason": "unique filename candidate",
                    }
                )
                reason = "missing_unique_candidate"
            elif len(candidates) > 1:
                reason = "missing_ambiguous_candidate"
                manual_reasons.append(
                    f"Ambiguous target for '{raw}' in {repo_rel(target_file, repo_root)} ({len(candidates)} candidates)."
                )
            else:
                reason = "missing_no_candidate"
                manual_reasons.append(
                    f"Unresolved reference '{raw}' in {repo_rel(target_file, repo_root)} with no candidates."
                )
        elif "\\" in raw:
            # Non-breaking normalization suggestion when path already resolves.
            rel = relative_from(target_file.parent.resolve(), resolved)
            auto_fixes.append(
                {
                    "source": repo_rel(target_file, repo_root),
                    "kind": kind,
                    "raw": raw,
                    "suggested": rel,
                    "reason": "normalize path separators",
                }
            )

        outbound.append(
            Reference(
                source=target_file,
                raw=raw,
                kind=kind,
                resolved=resolved,
                exists=exists,
                candidates=candidates,
                reason=reason,
            )
        )

    target_resolved = target_file.resolve()
    if inbound_index is not None:
        inbound = list(inbound_index.get(target_resolved, []))
    else:
        inbound = []
        for source in repo_files:
            if source == target_file:
                continue
            source_content = read_text(source)
            source_refs = extract_refs(source, source_content)
            for kind, raw in source_refs:
                resolved = resolve_reference(source, raw, repo_root)
                if resolved is not None and resolved == target_resolved:
                    inbound.append(
                        {
                            "source": repo_rel(source, repo_root),
                            "kind": kind,
                            "raw": raw,
                        }
                    )

    siblings = [
        repo_rel(p, repo_root)
        for p in target_file.parent.iterdir()
        if p.is_file() and p != target_file
    ]
    same_name = [
        repo_rel(p, repo_root)
        for p in repo_files
        if p.name == target_file.name and p.resolve() != target_resolved
    ]

    outbound_payload = [
        {
            "source": repo_rel(ref.source, repo_root),
            "kind": ref.kind,
            "raw": ref.raw,
            "resolved": repo_rel(ref.resolved, repo_root) if ref.resolved else None,
            "exists": ref.exists,
            "candidates": [repo_rel(c, repo_root) for c in ref.candidates],
            "reason": ref.reason,
        }
        for ref in outbound
    ]

    manual_required = len(manual_reasons) > 0

    return {
        "target": repo_rel(target_file, repo_root),
        "type": "file",
        "relationships": {
            "parent": repo_rel(target_file.parent, repo_root),
            "siblings": siblings,
            "same_name_candidates": same_name,
            "inbound_references": inbound,
            "outbound_references": outbound_payload,
        },
        "auto_fix_suggestions": auto_fixes,
        "manual_intervention_required": manual_required,
        "manual_reasons": manual_reasons,
    }


def analyze_directory(
    target_dir: Path,
    repo_root: Path,
    repo_files: List[Path],
    parsed_refs_by_file: Optional[Dict[Path, List[Tuple[str, str]]]] = None,
    inbound_index: Optional[Dict[Path, List[Dict[str, Any]]]] = None,
    name_index: Optional[Dict[str, List[Path]]] = None,
    include_file_reports: bool = True,
) -> Dict[str, Any]:
    scoped_files = [
        p
        for p in repo_files
        if target_dir.resolve() in p.resolve().parents or p.resolve() == target_dir.resolve()
    ]
    scoped_reports: List[Dict[str, Any]] = []
    manual_reasons: List[str] = []
    auto_fixes: List[Dict[str, Any]] = []
    manual_file_count = 0

    for file_path in scoped_files:
        if not file_path.is_file():
            continue
        report = analyze_references_for_file(
            file_path,
            repo_root,
            repo_files,
            parsed_refs_by_file=parsed_refs_by_file,
            inbound_index=inbound_index,
            name_index=name_index,
        )
        if include_file_reports:
            scoped_reports.append(report)
        auto_fixes.extend(report["auto_fix_suggestions"])
        manual_reasons.extend(report["manual_reasons"])
        if report["manual_intervention_required"]:
            manual_file_count += 1

    payload: Dict[str, Any] = {
        "target": repo_rel(target_dir, repo_root),
        "type": "directory",
        "file_count": len(scoped_files),
        "manual_file_count": manual_file_count,
        "auto_fix_suggestion_count": len(auto_fixes),
        "manual_intervention_required": len(manual_reasons) > 0,
        "manual_reasons": sorted(set(manual_reasons)),
        "auto_fix_suggestions": auto_fixes,
    }
    if include_file_reports:
        payload["files"] = scoped_reports
    return payload


def collect_markdown_suggestions(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    suggestions = report.get("auto_fix_suggestions", [])
    return [item for item in suggestions if item.get("kind") == "md_link"]


def prepare_markdown_fix_plan(
    report: Dict[str, Any],
    repo_root: Path,
) -> Tuple[Dict[Path, Dict[str, Any]], Dict[str, Any]]:
    suggestions = collect_markdown_suggestions(report)
    by_source: Dict[str, List[Dict[str, Any]]] = {}
    for item in suggestions:
        by_source.setdefault(item["source"], []).append(item)

    plan: Dict[Path, Dict[str, Any]] = {}
    fail_reasons: List[str] = []
    warnings: List[str] = []
    planned_replacements = 0
    preview: List[Dict[str, Any]] = []

    for rel_source, items in by_source.items():
        source = (repo_root / rel_source).resolve()
        if not source.exists():
            fail_reasons.append(f"Source file not found for suggestion set: {rel_source}")
            continue

        content = read_text(source)
        new_content = content
        file_replacements = 0

        for suggestion in items:
            raw = suggestion["raw"]
            new = suggestion["suggested"]
            if raw == new:
                continue
            candidate = resolve_reference(source, new, repo_root)
            if candidate is None or not candidate.exists():
                fail_reasons.append(
                    f"Suggested target does not resolve: {rel_source} :: {raw} -> {new}"
                )
                continue

            token_old = f"]({raw})"
            token_new = f"]({new})"
            hit_count = new_content.count(token_old)
            if hit_count == 0:
                fail_reasons.append(
                    f"Simulation token mismatch in {rel_source}: expected {token_old}"
                )
                continue

            new_content = new_content.replace(token_old, token_new)
            file_replacements += hit_count

        if new_content != content:
            plan[source] = {
                "source": rel_source,
                "new_content": new_content,
                "replacements": file_replacements,
            }
            planned_replacements += file_replacements
            preview.append(
                {
                    "source": rel_source,
                    "replacements": file_replacements,
                }
            )

    gate = {
        "mechanical_pass": len(fail_reasons) == 0,
        "apply_allowed": len(fail_reasons) == 0,
        "candidate_suggestion_count": len(suggestions),
        "plan_file_count": len(plan),
        "planned_replacements": planned_replacements,
        "plan_preview": preview,
        "fail_reasons": fail_reasons,
        "warnings": warnings,
    }
    return plan, gate


def apply_markdown_fix_plan(plan: Dict[Path, Dict[str, Any]]) -> Dict[str, int]:
    changed_files = 0
    replacements = 0
    for source, item in plan.items():
        source.write_text(item["new_content"], encoding="utf-8")
        changed_files += 1
        replacements += int(item["replacements"])
    return {"changed_files": changed_files, "replacements": replacements}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resolve file/directory relationships and classify manual intervention gates."
    )
    parser.add_argument("target", help="Target file or directory path")
    parser.add_argument(
        "--repo-root",
        help="Optional repo root override; defaults to auto-discovery from target path.",
    )
    parser.add_argument(
        "--emit-json",
        help="Optional path to write JSON report.",
    )
    parser.add_argument(
        "--apply-safe-fixes",
        action="store_true",
        help="Apply only safe markdown link rewrites from unambiguous suggestions.",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="For directory targets, omit per-file report payload to keep output compact.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    target = Path(args.target).resolve()
    if not target.exists():
        raise SystemExit(f"Target not found: {target}")

    repo_root = Path(args.repo_root).resolve() if args.repo_root else discover_repo_root(target)
    repo_files = [p.resolve() for p in iter_text_files(repo_root)]
    parsed_refs_by_file, inbound_index, name_index = build_reference_indexes(repo_files, repo_root)

    if target.is_file():
        report = analyze_references_for_file(
            target,
            repo_root,
            repo_files,
            parsed_refs_by_file=parsed_refs_by_file,
            inbound_index=inbound_index,
            name_index=name_index,
        )
    else:
        report = analyze_directory(
            target,
            repo_root,
            repo_files,
            parsed_refs_by_file=parsed_refs_by_file,
            inbound_index=inbound_index,
            name_index=name_index,
            include_file_reports=not args.summary_only,
        )

    plan, gate = prepare_markdown_fix_plan(report, repo_root)
    report["simulation_gate"] = gate

    if args.apply_safe_fixes:
        if not gate["apply_allowed"]:
            report["applied_fixes"] = {
                "changed_files": 0,
                "replacements": 0,
                "mechanical_pass": False,
                "blocked": True,
                "fail_reasons": gate["fail_reasons"],
            }
        else:
            apply_result = apply_markdown_fix_plan(plan)
            report["applied_fixes"] = {
                **apply_result,
                "mechanical_pass": True,
                "blocked": False,
            }

    if args.emit_json:
        out_path = Path(args.emit_json).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report, indent=2))
    if args.apply_safe_fixes and not gate["apply_allowed"]:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
