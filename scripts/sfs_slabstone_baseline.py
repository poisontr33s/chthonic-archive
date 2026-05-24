#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: sfs_slabstone_baseline.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
SFS Slabstone Baseline - generated anchor for the SFS design canon.

Builds a reproducible markdown slab that binds the three canon design docs to
the live extension assets they govern: the SFS color theme, the file icon
theme, the product icon theme, and the referenced tooling/scripts that support
the lane.

This closes the gap between "docs that describe the baseline" and "files that
actually implement the baseline" by emitting one auditable anchor artifact.

@SID:           TOOL_SFS_SLABSTONE_BASELINE_V1
@Shabti:          Utility
@Context:       Design baseline / SFS / SVG + theme reproducibility
@Purpose:       SFS Slabstone Baseline - generated anchor for the SFS design canon.

Usage:
  uv run scripts/sfs_slabstone_baseline.py --report
  uv run scripts/sfs_slabstone_baseline.py --report --strict
  uv run scripts/sfs_slabstone_baseline.py --json
"""

from __future__ import annotations


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import argparse
import hashlib
import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.lib.shared import configure_utf8_output, find_repo_root

RE_MD_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
RE_CODE_SPAN = re.compile(r"`([^`\n]+)`")
RE_FENCED_CODE = re.compile(r"```.*?```", re.DOTALL)
RE_SID = re.compile(r"^sid:\s*(.+)$", re.IGNORECASE | re.MULTILINE)
RE_AT_SID = re.compile(r"@SID:\s*(\S+)")
EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "tel:", "#", "ftp://", "vscode://")
PATHLIKE_EXTENSIONS = {
    ".md", ".py", ".ts", ".tsx", ".js", ".json", ".svg", ".woff", ".toml", ".ps1", ".cjs",
}
SKIP_DIRS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    "target",
    ".venv",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    ".next",
    "book",
}


@dataclass(slots=True)
class ReferenceRecord:
    doc: Path
    kind: str
    raw: str
    rendered: str
    resolved: Path | None
    exists: bool


REPO_ROOT = find_repo_root(Path(__file__).resolve())
OUTPUT_PATH = REPO_ROOT / "docs" / "design" / "SFS_SLABSTONE_BASELINE.md"
CANON_DOCS = [
    REPO_ROOT / "docs" / "design" / "ANKH_ICON_GRAMMAR.md",
    REPO_ROOT / "docs" / "design" / "ANKH_THEME_REFERENCE.md",
    REPO_ROOT / "docs" / "design" / "SFS_WPTG_ITERATION_PLAN.md",
]
SFS_THEME_PATH = REPO_ROOT / "extensions" / "chthonic-archive" / "themes" / "chthonic-geology-color-theme.json"
FILE_ICON_THEME_PATH = REPO_ROOT / "extensions" / "chthonic-archive" / "themes" / "chthonic-file-icon-theme.json"
PRODUCT_ICON_THEME_PATH = REPO_ROOT / "extensions" / "chthonic-archive" / "themes" / "chthonic-product-icon-theme.json"
EXTENSION_MANIFEST_PATH = REPO_ROOT / "extensions" / "chthonic-archive" / "package.json"
ICONS_DIR = REPO_ROOT / "extensions" / "chthonic-archive" / "themes" / "icons"
PRODUCT_ICONS_DIR = ICONS_DIR / "product"
PRODUCT_FONTS_DIR = REPO_ROOT / "extensions" / "chthonic-archive" / "themes" / "fonts"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def short_hash(path: Path) -> str:
    raw = path.read_bytes()
    # Normalize CRLF→LF for text-like files so hashes are platform-independent
    if path.suffix.lower() not in {".png", ".woff", ".woff2", ".ttf", ".otf", ".svg"}:
        try:
            normalized = raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
            raw = normalized
        except UnicodeDecodeError:
            pass  # binary file — use raw bytes
    digest = hashlib.sha256(raw).hexdigest()
    return digest[:12]


def repo_rel(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()


def render_rel(raw_repo_path: str, output_path: Path) -> str:
    return os.path.relpath(REPO_ROOT / raw_repo_path, start=output_path.parent).replace("\\", "/")


def build_basename_index() -> dict[str, list[Path]]:
    index: dict[str, list[Path]] = defaultdict(list)
    for root, dirs, files in os.walk(REPO_ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        root_path = Path(root)
        for name in files:
            index[name].append(root_path / name)
    return index


def extract_sid(text: str) -> str | None:
    frontmatter_match = RE_SID.search(text)
    if frontmatter_match:
        return frontmatter_match.group(1).strip().strip('"')
    inline_match = RE_AT_SID.search(text)
    if inline_match:
        return inline_match.group(1).strip()
    return None


def normalize_target(raw: str) -> str:
    return raw.split("#", 1)[0].strip()


def is_pathlike(raw: str) -> bool:
    if any(raw.startswith(prefix) for prefix in EXTERNAL_PREFIXES):
        return False
    normalized = normalize_target(raw)
    if not normalized:
        return False
    if any(char in normalized for char in ("\n", "\r", "|", "<", ">")):
        return False
    if normalized.split(" ", 1)[0] in {"uv", "bun", "bunx", "cd", "git", "cargo", "pwsh", "powershell"}:
        return False
    if any(ch.isspace() for ch in normalized):
        return False
    if re.match(r"^[A-Za-z]:[\\/]", normalized) or normalized.startswith("%"):
        return True
    if normalized.startswith(("./", "../", ".\\", "..\\", "/")):
        return True
    if "/" in normalized or "\\" in normalized:
        segments = [segment for segment in normalized.replace("\\", "/").split("/") if segment]
        return len(segments) >= 2
    suffix = Path(normalized).suffix.lower()
    return suffix in PATHLIKE_EXTENSIONS


def strip_code_for_link_scan(text: str) -> str:
    text = RE_FENCED_CODE.sub("", text)
    return RE_CODE_SPAN.sub("", text)


def resolve_reference(raw: str, doc_path: Path, basename_index: dict[str, list[Path]]) -> Path | None:
    normalized = normalize_target(raw).replace("\\", "/")
    if not normalized:
        return None

    candidate_path = Path(normalized)
    candidates: list[Path] = []
    if candidate_path.is_absolute():
        candidates.append(candidate_path)
    elif "/" in normalized:
        candidates.append((doc_path.parent / candidate_path).resolve())
        candidates.append((REPO_ROOT / candidate_path).resolve())
    else:
        local = (doc_path.parent / candidate_path).resolve()
        repo_local = (REPO_ROOT / candidate_path).resolve()
        candidates.extend([local, repo_local])
        by_name = basename_index.get(candidate_path.name, [])
        if len(by_name) == 1:
            candidates.append(by_name[0].resolve())

    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        if candidate.exists():
            return candidate
    return None


def extract_doc_references(doc_path: Path, basename_index: dict[str, list[Path]]) -> list[ReferenceRecord]:
    text = doc_path.read_text(encoding="utf-8")
    link_scan_text = strip_code_for_link_scan(text)
    records: list[ReferenceRecord] = []
    seen: set[tuple[str, str]] = set()

    for match in RE_MD_LINK.finditer(link_scan_text):
        target = match.group(2).strip()
        if any(target.startswith(prefix) for prefix in EXTERNAL_PREFIXES):
            continue
        resolved = resolve_reference(target, doc_path, basename_index)
        key = ("link", target)
        if key in seen:
            continue
        seen.add(key)
        records.append(
            ReferenceRecord(
                doc=doc_path,
                kind="link",
                raw=target,
                rendered=target,
                resolved=resolved,
                exists=resolved is not None,
            )
        )

    for match in RE_CODE_SPAN.finditer(text):
        raw = match.group(1).strip()
        if not is_pathlike(raw):
            continue
        key = ("cite", raw)
        if key in seen:
            continue
        seen.add(key)
        resolved = resolve_reference(raw, doc_path, basename_index)
        records.append(
            ReferenceRecord(
                doc=doc_path,
                kind="cite",
                raw=raw,
                rendered=raw,
                resolved=resolved,
                exists=resolved is not None,
            )
        )

    return records


def summarize_doc(doc_path: Path, references: list[ReferenceRecord]) -> dict[str, Any]:
    text = doc_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    link_refs = [ref for ref in references if ref.kind == "link"]
    cite_refs = [ref for ref in references if ref.kind == "cite"]
    return {
        "path": repo_rel(doc_path),
        "sid": extract_sid(text),
        "line_count": len(lines),
        "sha12": short_hash(doc_path),
        "link_total": len(link_refs),
        "link_missing": sum(1 for ref in link_refs if not ref.exists),
        "cite_total": len(cite_refs),
        "cite_missing": sum(1 for ref in cite_refs if not ref.exists),
    }


def load_sfs_theme_metrics() -> dict[str, Any]:
    theme = load_json(SFS_THEME_PATH)
    return {
        "name": theme.get("name"),
        "workbench_keys": len(theme.get("colors", {})),
        "token_rules": len(theme.get("tokenColors", [])),
        "semantic_keys": len(theme.get("semanticTokenColors", {})),
    }


def load_file_icon_metrics() -> dict[str, Any]:
    theme = load_json(FILE_ICON_THEME_PATH)
    icon_definitions = theme.get("iconDefinitions", {})
    svg_names = sorted(path.name for path in ICONS_DIR.glob("*.svg"))
    file_svgs = [name for name in svg_names if name.startswith("file-")]
    folder_svgs = [name for name in svg_names if name.startswith("folder-")]
    specialized_folder_svgs = [
        name for name in folder_svgs if name not in {"folder-default.svg", "folder-open.svg"}
    ]
    return {
        "icon_definitions": len(icon_definitions),
        "file_svgs": len(file_svgs),
        "folder_svgs_total": len(folder_svgs),
        "folder_svgs_specialized": len(specialized_folder_svgs),
        "file_extensions": len(theme.get("fileExtensions", {})),
        "file_names": len(theme.get("fileNames", {})),
        "language_ids": len(theme.get("languageIds", {})),
        "folder_names": len(theme.get("folderNames", {})),
        "folder_names_expanded": len(theme.get("folderNamesExpanded", {})),
    }


def load_product_icon_metrics() -> dict[str, Any]:
    theme = load_json(PRODUCT_ICON_THEME_PATH)
    product_svgs = sorted(path.name for path in PRODUCT_ICONS_DIR.glob("*.svg"))
    fonts = sorted(path.name for path in PRODUCT_FONTS_DIR.glob("*"))
    return {
        "icon_definitions": len(theme.get("iconDefinitions", {})),
        "fonts": len(theme.get("fonts", [])),
        "font_assets": fonts,
        "source_svgs": len(product_svgs),
    }


def load_extension_baseline_metrics() -> dict[str, Any]:
    manifest = load_json(EXTENSION_MANIFEST_PATH)
    contributes = manifest.get("contributes", {})
    views = contributes.get("views", {}).get("chthonic-archive", [])
    return {
        "themes": len(contributes.get("themes", [])),
        "icon_themes": len(contributes.get("iconThemes", [])),
        "product_icon_themes": len(contributes.get("productIconThemes", [])),
        "languages": len(contributes.get("languages", [])),
        "grammars": len(contributes.get("grammars", [])),
        "commands": len(contributes.get("commands", [])),
        "views": len(views),
    }


def build_payload() -> dict[str, Any]:
    basename_index = build_basename_index()
    references_by_doc: dict[str, list[ReferenceRecord]] = {}
    doc_rows: list[dict[str, Any]] = []
    all_link_missing: list[ReferenceRecord] = []
    all_cite_missing: list[ReferenceRecord] = []
    scripts_index: dict[str, set[str]] = defaultdict(set)

    for doc_path in CANON_DOCS:
        refs = extract_doc_references(doc_path, basename_index)
        references_by_doc[repo_rel(doc_path)] = refs
        doc_rows.append(summarize_doc(doc_path, refs))
        for ref in refs:
            if ref.kind == "link" and not ref.exists:
                all_link_missing.append(ref)
            if ref.kind == "cite" and not ref.exists:
                all_cite_missing.append(ref)
            target = ref.resolved if ref.resolved is not None else resolve_reference(ref.raw, doc_path, basename_index)
            if target and target.suffix in {".py", ".ts", ".ps1"} and repo_rel(target).startswith("scripts/"):
                scripts_index[repo_rel(target)].add(repo_rel(doc_path))
            elif ref.raw.startswith("scripts/") or ref.raw.endswith((".py", ".ts", ".ps1")):
                rendered = normalize_target(ref.raw).replace("\\", "/")
                if rendered.startswith("scripts/"):
                    scripts_index[rendered].add(repo_rel(doc_path))

    script_rows = []
    for script_path, doc_set in sorted(scripts_index.items()):
        resolved = (REPO_ROOT / script_path).resolve()
        exists = resolved.exists()
        script_rows.append(
            {
                "path": script_path,
                "exists": exists,
                "docs": sorted(doc_set),
            }
        )

    core_assets = [
        SFS_THEME_PATH,
        FILE_ICON_THEME_PATH,
        PRODUCT_ICON_THEME_PATH,
        EXTENSION_MANIFEST_PATH,
        ICONS_DIR,
        PRODUCT_ICONS_DIR,
    ]
    core_asset_rows = [
        {
            "path": repo_rel(path),
            "exists": path.exists(),
            "kind": "dir" if path.is_dir() else "file",
        }
        for path in core_assets
    ]

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "strict_status": "pass" if not all_link_missing and all(row["exists"] for row in core_asset_rows) else "fail",
        "canon_docs": doc_rows,
        "references_by_doc": {
            doc: [
                {
                    "kind": ref.kind,
                    "raw": ref.raw,
                    "exists": ref.exists,
                    "resolved": repo_rel(ref.resolved) if ref.resolved else None,
                }
                for ref in refs
            ]
            for doc, refs in references_by_doc.items()
        },
        "missing_links": [
            {
                "doc": repo_rel(ref.doc),
                "raw": ref.raw,
            }
            for ref in all_link_missing
        ],
        "missing_citations": [
            {
                "doc": repo_rel(ref.doc),
                "raw": ref.raw,
            }
            for ref in all_cite_missing
        ],
        "sfs_theme": load_sfs_theme_metrics(),
        "file_icon_theme": load_file_icon_metrics(),
        "product_icon_theme": load_product_icon_metrics(),
        "extension_baseline": load_extension_baseline_metrics(),
        "script_references": script_rows,
        "core_assets": core_asset_rows,
    }


def render_markdown(payload: dict[str, Any], output_path: Path = OUTPUT_PATH) -> str:
    lines: list[str] = []
    append = lines.append

    append("# SFS Slabstone Baseline")
    append("")
    append("> Generated by `scripts/sfs_slabstone_baseline.py` (`TOOL_SFS_SLABSTONE_BASELINE_V1`)")
    append(f"> Generated: `{payload['generated_at']}`")
    append(f"> Strict status: **{payload['strict_status'].upper()}**")
    append("")
    append("This slabstone is the reproducible anchor for the SFS design lane.")
    append("It binds the canon docs to the live extension assets, scripts, and")
    append("theme/icon state they govern.")
    append("")
    append("---")
    append("")
    append("## Canon Matrix")
    append("")
    append("| File | SID | Lines | SHA12 | Linked Paths | Missing Links | Cited Paths | Missing Citations |")
    append("|------|-----|------:|-------|-------------:|--------------:|------------:|------------------:|")
    for row in payload["canon_docs"]:
        rendered_path = render_rel(row["path"], output_path)
        append(
            f"| [{Path(row['path']).name}]({rendered_path}) | `{row['sid'] or '—'}` | "
            f"{row['line_count']} | `{row['sha12']}` | {row['link_total']} | "
            f"{row['link_missing']} | {row['cite_total']} | {row['cite_missing']} |"
        )
    append("")

    append("## Live SFS Extension Baseline")
    append("")
    ext = payload["extension_baseline"]
    append("| Layer | Live State |")
    append("|-------|------------|")
    append(f"| Registered themes | {ext['themes']} |")
    append(f"| File icon themes | {ext['icon_themes']} |")
    append(f"| Product icon themes | {ext['product_icon_themes']} |")
    append(f"| Local languages | {ext['languages']} |")
    append(f"| Local grammars | {ext['grammars']} |")
    append(f"| Commands | {ext['commands']} |")
    append(f"| Views in `chthonic-archive` | {ext['views']} |")
    append("")

    sfs = payload["sfs_theme"]
    append("### SFS Theme Metrics")
    append("")
    append("| Theme | Workbench Keys | Token Rules | Semantic Keys |")
    append("|-------|---------------:|------------:|--------------:|")
    append(
        f"| {sfs['name']} | {sfs['workbench_keys']} | {sfs['token_rules']} | {sfs['semantic_keys']} |"
    )
    append("")

    file_icons = payload["file_icon_theme"]
    product_icons = payload["product_icon_theme"]
    append("### Icon Corpus Metrics")
    append("")
    append("| Corpus | Live Count | Notes |")
    append("|--------|-----------:|-------|")
    append(
        f"| File SVGs | {file_icons['file_svgs']} | actual `file-*.svg` corpus under `themes/icons/` |"
    )
    append(
        f"| Folder SVGs (total) | {file_icons['folder_svgs_total']} | includes default/open baseline pair |"
    )
    append(
        f"| Folder SVGs (specialized) | {file_icons['folder_svgs_specialized']} | excludes `folder-default.svg` + `folder-open.svg` |"
    )
    append(
        f"| File icon definitions | {file_icons['icon_definitions']} | `chthonic-file-icon-theme.json` iconDefinitions |"
    )
    append(
        f"| Product source SVGs | {product_icons['source_svgs']} | source glyphs under `themes/icons/product/` |"
    )
    append(
        f"| Product icon definitions | {product_icons['icon_definitions']} | font-backed runtime glyphs |"
    )
    append(
        f"| Product fonts | {product_icons['fonts']} | assets: `{', '.join(product_icons['font_assets']) or '—'}` |"
    )
    append("")

    append("## Core Asset Coupling")
    append("")
    append("| Path | Kind | Exists |")
    append("|------|------|--------|")
    for row in payload["core_assets"]:
        rendered_path = render_rel(row["path"], output_path)
        append(f"| [{Path(row['path']).name}]({rendered_path}) | {row['kind']} | {'YES' if row['exists'] else 'NO'} |")
    append("")

    append("## Script Reference Matrix")
    append("")
    append("| Script | Exists | Mentioned By |")
    append("|--------|--------|--------------|")
    for row in payload["script_references"]:
        rendered_script_path = render_rel(row["path"], output_path)
        docs = "<br>".join(
            f"[{Path(doc).name}]({render_rel(doc, output_path)})" for doc in row["docs"]
        )
        append(
            f"| [{Path(row['path']).name}]({rendered_script_path}) | "
            f"{'YES' if row['exists'] else 'NO'} | {docs} |"
        )
    append("")

    append("## Canon Reference Audit")
    append("")
    for doc in payload["canon_docs"]:
        doc_path = doc["path"]
        append(f"### [{Path(doc_path).name}]({render_rel(doc_path, output_path)})")
        append("")
        refs = payload["references_by_doc"][doc_path]
        missing_links = [ref for ref in refs if ref["kind"] == "link" and not ref["exists"]]
        missing_cites = [ref for ref in refs if ref["kind"] == "cite" and not ref["exists"]]
        existing_links = [ref for ref in refs if ref["kind"] == "link" and ref["exists"]]
        append(f"- Linked paths resolved: {len(existing_links)}")
        append(f"- Missing linked paths: {len(missing_links)}")
        append(f"- Missing cited paths: {len(missing_cites)}")
        if missing_links:
            append("- Broken links:")
            for ref in missing_links:
                append(f"  - `{ref['raw']}`")
        if missing_cites:
            append("- Missing cited files:")
            for ref in missing_cites:
                append(f"  - `{ref['raw']}`")
        append("")

    append("## Reproduction")
    append("")
    append("```powershell")
    append("uv run scripts/ankh_theme_reference.py --output docs/design/ANKH_THEME_REFERENCE.md")
    append("uv run scripts/sfs_slabstone_baseline.py --report --strict")
    append("uv run scripts/icon_svg_audit.py")
    append("uv run scripts/theme_token_coverage.py")
    append("uv run scripts/product_icon_census.py")
    append("```")
    append("")

    append("## Interpretation")
    append("")
    append("- Markdown links are contract links and should resolve cleanly.")
    append("- Inline code citations are allowed to name future or optional files; this slabstone records whether they currently exist.")
    append("- The live SFS metrics come from the actual extension manifests and SVG corpora, not prose estimates.")
    append("")

    return "\n".join(lines) + "\n"


def main() -> int:
    configure_utf8_output()

    parser = argparse.ArgumentParser(
        description="Generate the SFS slabstone baseline from canon docs and live extension assets."
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON payload to stdout.")
    parser.add_argument(
        "--emit-json",
        metavar="FILE",
        type=Path,
        default=None,
        help="Write JSON payload to FILE instead of stdout (default: docs/design/SFS_SLABSTONE_BASELINE.json when flag is bare).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output path. Defaults to docs/design/SFS_SLABSTONE_BASELINE.md when --report is set.",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Write the default markdown slabstone report to docs/design/SFS_SLABSTONE_BASELINE.md.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when a canon markdown link is broken or a core asset is missing.",
    )
    args = parser.parse_args()

    payload = build_payload()

    # --- JSON output branch ---
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        if args.strict:
            has_missing_links = bool(payload["missing_links"])
            has_missing_core_assets = any(not row["exists"] for row in payload["core_assets"])
            return 1 if (has_missing_links or has_missing_core_assets) else 0
        return 0

    if args.emit_json is not None:
        json_target: Path = args.emit_json if str(args.emit_json) != "-" else REPO_ROOT / "docs" / "design" / "SFS_SLABSTONE_BASELINE.json"
        json_target.parent.mkdir(parents=True, exist_ok=True)
        json_payload = json.dumps(payload, indent=2, ensure_ascii=False)
        json_target.write_text(json_payload + "\n", encoding="utf-8")
        print(f"[emit-json] wrote {repo_rel(json_target)}")

    # --- Markdown output branch ---
    render_target = args.output if args.output else OUTPUT_PATH
    rendered = render_markdown(payload, output_path=render_target)

    output_path = args.output
    if args.report and output_path is None:
        output_path = OUTPUT_PATH

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered if rendered.endswith("\n") else rendered + "\n", encoding="utf-8")
    elif not args.emit_json:
        print(rendered)

    # Exit codes:
    #   0 — success (no --strict issues found)
    #   1 — strict mode: broken canon links OR missing core assets
    if args.strict:
        has_missing_links = bool(payload["missing_links"])
        has_missing_core_assets = any(not row["exists"] for row in payload["core_assets"])
        return 1 if (has_missing_links or has_missing_core_assets) else 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
