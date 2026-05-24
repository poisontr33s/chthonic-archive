#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: envelope_sync.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
envelope_sync.py — Script logic for envelope_sync.py.

@SID:           TOOL_ENVELOPE_SYNC_V1
@Shabti:        CLI Script
@Purpose:       Script logic for envelope_sync.py.
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


from __future__ import annotations

import argparse
import ast
import json
import re
from datetime import UTC, datetime
from pathlib import Path

SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".next", "dist", "build"}
TARGET_EXTS = {".py", ".ts", ".js", ".tsx", ".jsx"}
MANAGED_MARKER = "ENVELOPE-MANAGED: true"


def iter_source_files(root: Path) -> list[Path]:
    files: list[Path] = []
    if root.is_file() and root.suffix in TARGET_EXTS:
        return [root]
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix not in TARGET_EXTS:
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        files.append(path)
    return files


def detect_runtime(path: Path) -> str:
    p = path.as_posix()
    if path.suffix == ".py":
        return "python"
    if "/app/" in p or "/pages/" in p or "/components/" in p:
        return "nextjs"
    if path.suffix in {".ts", ".tsx"}:
        return "bun"
    if path.suffix in {".js", ".jsx"}:
        return "node"
    return "unknown"


def first_sentence(text: str) -> str:
    cleaned_lines = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        s = re.sub(r"^[*#\s]+", "", s)
        s = s.strip("║").strip()
        if s:
            cleaned_lines.append(s)
    cleaned = " ".join(cleaned_lines)
    if not cleaned:
        return ""
    match = re.match(r"(.+?[.!?])(\s|$)", cleaned)
    return match.group(1).strip() if match else cleaned[:160].strip()


def extract_labeled_purpose(text: str) -> str:
    for line in text.splitlines():
        clean = line.strip()
        clean = re.sub(r"^[*#\s]+", "", clean)
        clean = clean.strip("║").strip()
        m = re.search(r"Purpose:\s*(.+)$", clean, flags=re.IGNORECASE)
        if m and m.group(1).strip():
            return m.group(1).strip()
    return ""


def extract_python(file_path: Path, text: str) -> tuple[str, list[str], list[str]]:
    purpose = ""
    exports: list[str] = []
    xrefs: list[str] = []

    try:
        tree = ast.parse(text)
        doc = ast.get_docstring(tree) or ""
        purpose = extract_labeled_purpose(doc) or first_sentence(doc)
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and not node.name.startswith("_"):
                exports.append(node.name)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    xrefs.append(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                xrefs.append(node.module)
    except Exception:
        pass

    if not purpose:
        purpose = f"Script logic for {file_path.name}."
    return purpose, sorted(set(exports)), sorted(set(xrefs))


def extract_ts_js(file_path: Path, text: str) -> tuple[str, list[str], list[str]]:
    exports = set()
    xrefs = set()
    purpose = ""

    comment_match = re.search(r"/\*\*(.*?)\*/", text, flags=re.DOTALL)
    if comment_match:
        block = comment_match.group(1)
        purpose = extract_labeled_purpose(block) or first_sentence(block)

    export_patterns = [
        r"export\s+function\s+([A-Za-z_][A-Za-z0-9_]*)",
        r"export\s+class\s+([A-Za-z_][A-Za-z0-9_]*)",
        r"export\s+const\s+([A-Za-z_][A-Za-z0-9_]*)",
        r"export\s+default\s+function\s+([A-Za-z_][A-Za-z0-9_]*)"
    ]
    for pattern in export_patterns:
        for name in re.findall(pattern, text):
            exports.add(name)

    for mod in re.findall(r"import\s+.*?\s+from\s+['\"]([^'\"]+)['\"]", text):
        xrefs.add(mod)
    for mod in re.findall(r"require\(\s*['\"]([^'\"]+)['\"]\s*\)", text):
        xrefs.add(mod)

    if not purpose:
        purpose = f"Script logic for {file_path.name}."
    return purpose, sorted(exports), sorted(xrefs)


def detect_invoke(entrypoint: str, runtime: str) -> str:
    p = entrypoint
    if runtime == "python":
        return f"uv run {p}"
    if runtime == "bun":
        return f"bun {p}"
    if runtime in {"node", "nextjs"}:
        return f"bun run {p}"
    return p


def merge_metadata(existing: dict, generated: dict, prefer_source: bool) -> dict:
    merged = dict(existing)
    sticky_keys = {"purpose", "invoke", "exports", "xrefs", "owners", "tags", "license_spdx", "entrypoint"}
    for key, value in generated.items():
        if key == "role" and merged.get(key):
            continue
        if (not prefer_source) and key in sticky_keys and merged.get(key):
            continue
        merged[key] = value
    return merged


def build_metadata(repo_root: Path, file_path: Path) -> dict:
    text = file_path.read_text(encoding="utf-8")
    runtime = detect_runtime(file_path)

    if runtime == "python":
        purpose, exports, xrefs = extract_python(file_path, text)
    else:
        purpose, exports, xrefs = extract_ts_js(file_path, text)

    rel = file_path.relative_to(repo_root).as_posix()
    return {
        "id": rel,
        "title": file_path.name,
        "role": "script",
        "purpose": purpose,
        "invoke": detect_invoke(rel, runtime),
        "exports": exports,
        "xrefs": xrefs,
        "runtime": runtime,
        "entrypoint": rel,
        "updated_at": datetime.now(UTC).isoformat()
    }


def sidecar_path(file_path: Path) -> Path:
    return file_path.with_name(f"{file_path.name}.meta.json")


def write_sidecar(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def comparable(payload: dict) -> dict:
    out = dict(payload)
    out.pop("updated_at", None)
    return out


def _truncate(value: str, n: int = 96) -> str:
    s = value.strip()
    if len(s) <= n:
        return s
    return s[: n - 3].rstrip() + "..."


def _csv(items: list[str], limit: int = 10) -> str:
    if not items:
        return "none"
    return ", ".join(items[:limit])


def render_python_prologue(meta: dict) -> str:
    title = meta.get("title", "")
    role = meta.get("role", "script")
    purpose = _truncate(meta.get("purpose", ""))
    invoke = _truncate(meta.get("invoke", ""))
    exports = _truncate(_csv(meta.get("exports", [])))
    xrefs = _truncate(_csv(meta.get("xrefs", [])))
    return (
        "#!/usr/bin/env python3\n"
        "#-*- coding: utf-8 -*-\n\n"
        "\"\"\"\n"
        "╔══════════════════════════════════════════════════════════════════════════════\n"
        f"║ {title}\n"
        f"║ Role: {role}\n"
        f"║ Purpose: {purpose}\n"
        f"║ Invoke: {invoke}\n"
        f"║ Exports: {exports}\n"
        f"║ X-Refs: {xrefs}\n"
        f"║ {MANAGED_MARKER}\n"
        "╚══════════════════════════════════════════════════════════════════════════════\n"
        "\"\"\"\n\n"
    )


def render_ts_js_banner(meta: dict) -> str:
    title = meta.get("title", "")
    role = meta.get("role", "script")
    purpose = _truncate(meta.get("purpose", ""))
    invoke = _truncate(meta.get("invoke", ""))
    exports = _truncate(_csv(meta.get("exports", [])))
    xrefs = _truncate(_csv(meta.get("xrefs", [])))
    return (
        "/**\n"
        "╔══════════════════════════════════════════════════════════════════════════════\n"
        f"║ {title}\n"
        f"║ Role: {role}\n"
        f"║ Purpose: {purpose}\n"
        f"║ Invoke: {invoke}\n"
        f"║ Exports: {exports}\n"
        f"║ X-Refs: {xrefs}\n"
        f"║ {MANAGED_MARKER}\n"
        "╚══════════════════════════════════════════════════════════════════════════════\n"
        " */\n\n"
    )


def _split_python_prologue(lines: list[str]) -> tuple[list[str], bool]:
    idx = 0
    if idx < len(lines) and lines[idx].startswith("#!"):
        idx += 1
    if idx < len(lines) and lines[idx].strip() in {"#-*- coding: utf-8 -*-", "#-*- coding: utf-8 -*-"}:
        idx += 1
    while idx < len(lines) and not lines[idx].strip():
        idx += 1

    # Remove leading module docstring block if present.
    if idx < len(lines) and (lines[idx].startswith('"""') or lines[idx].startswith("'''")):
        quote = lines[idx][:3]
        idx += 1
        while idx < len(lines):
            if lines[idx].endswith(quote):
                idx += 1
                break
            idx += 1
    return lines[idx:], True


def _top_body_index(lines: list[str]) -> int:
    i = 0
    if i < len(lines) and lines[i].startswith("#!"):
        i += 1
    if i < len(lines) and lines[i].strip() in {"#-*- coding: utf-8 -*-", "#-*- coding: utf-8 -*-"}:
        i += 1
    while i < len(lines) and not lines[i].strip():
        i += 1
    return i


def _has_top_docstring_or_banner(text: str) -> bool:
    lines = text.splitlines()
    i = _top_body_index(lines)
    if i >= len(lines):
        return False
    s = lines[i].strip()
    return (
        s.startswith('"""')
        or s.startswith("'''")
        or s.startswith("/**")
        or s.startswith("# ╔")
        or s.startswith("// ╔")
    )


def inject_python(path: Path, meta: dict, force: bool) -> tuple[bool, str]:
    text = path.read_text(encoding="utf-8")
    managed = MANAGED_MARKER in text[:4000]
    if _has_top_docstring_or_banner(text) and not managed and not force:
        return False, "skipped_unmanaged_existing_prologue"

    lines = text.splitlines()
    i = _top_body_index(lines)
    # If managed block exists at top, drop it for replacement.
    if i < len(lines) and (lines[i].startswith('"""') or lines[i].startswith("'''")):
        quote = lines[i][:3]
        j = i + 1
        block = [lines[i]]
        while j < len(lines):
            block.append(lines[j])
            if lines[j].endswith(quote):
                j += 1
                break
            j += 1
        if MANAGED_MARKER in "\n".join(block):
            rebuilt = lines[:i] + lines[j:]
            lines = rebuilt
    tail, _ = _split_python_prologue(lines)
    new_text = render_python_prologue(meta) + ("\n".join(tail) + "\n" if tail else "")
    if new_text == text:
        return False, "no_change"
    path.write_text(new_text, encoding="utf-8")
    return True, "injected"


def inject_ts_js(path: Path, meta: dict, force: bool) -> tuple[bool, str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    idx = 0
    shebang = ""
    if idx < len(lines) and lines[idx].startswith("#!"):
        shebang = lines[idx] + "\n"
        idx += 1
    while idx < len(lines) and not lines[idx].strip():
        idx += 1

    remaining = lines[idx:]
    top_block = "\n".join(remaining[:40])
    first = remaining[0].strip() if remaining else ""
    has_top_comment = bool(remaining and (first.startswith("/**") or first.startswith("//")))
    managed = MANAGED_MARKER in top_block
    if has_top_comment and not managed and not force:
        return False, "skipped_unmanaged_existing_banner"

    if has_top_comment and first.startswith("/**"):
        j = 0
        while j < len(remaining):
            if "*/" in remaining[j]:
                j += 1
                break
            j += 1
        while j < len(remaining) and not remaining[j].strip():
            j += 1
        remaining = remaining[j:]
    elif has_top_comment and first.startswith("//"):
        # Managed single-line envelope block replacement path.
        if managed:
            j = 0
            while j < len(remaining) and remaining[j].strip().startswith("//"):
                j += 1
            while j < len(remaining) and not remaining[j].strip():
                j += 1
            remaining = remaining[j:]

    banner = render_ts_js_banner(meta)
    new_text = shebang + banner + ("\n".join(remaining) + "\n" if remaining else "")
    if new_text == text:
        return False, "no_change"
    path.write_text(new_text, encoding="utf-8")
    return True, "injected"


def inject_envelope(path: Path, meta: dict, force: bool) -> tuple[bool, str]:
    runtime = detect_runtime(path)
    if runtime == "python":
        return inject_python(path, meta, force)
    if path.suffix in {".ts", ".js", ".tsx", ".jsx"}:
        return inject_ts_js(path, meta, force)
    return False, "unsupported_runtime"


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract and sync universal script envelope metadata.")
    parser.add_argument("targets", nargs="+", help="File/directory targets")
    parser.add_argument("--repo-root", default=".", help="Repository root for relative IDs")
    parser.add_argument("--check", action="store_true", help="Check only; fail if sidecars are missing or stale")
    parser.add_argument("--inject", action="store_true", help="Inject rendered metadata envelopes into source files.")
    parser.add_argument("--force", action="store_true", help="Overwrite unmanaged existing prologues/banners.")
    parser.add_argument(
        "--prefer-source",
        action="store_true",
        help="Prefer extracted source metadata over sidecar values when merging conflicts.",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    all_files: list[Path] = []
    for target in args.targets:
        all_files.extend(iter_source_files(Path(target)))

    all_files = sorted(set(p.resolve() for p in all_files))
    changed = 0
    stale = 0
    scanned = 0
    injected = 0
    skipped_unmanaged = 0

    for file_path in all_files:
        scanned += 1
        generated = build_metadata(repo_root, file_path)
        meta_file = sidecar_path(file_path)
        existing = {}
        if meta_file.exists():
            try:
                existing = json.loads(meta_file.read_text(encoding="utf-8"))
            except Exception:
                existing = {}
        merged = merge_metadata(existing, generated, prefer_source=args.prefer_source)

        existing_normalized = json.dumps(comparable(existing), sort_keys=True, ensure_ascii=True)
        merged_normalized = json.dumps(comparable(merged), sort_keys=True, ensure_ascii=True)

        if existing_normalized != merged_normalized:
            if args.check:
                stale += 1
            else:
                write_sidecar(meta_file, merged)
                changed += 1

        if args.inject and not args.check:
            did_write, status = inject_envelope(file_path, merged, force=args.force)
            if did_write:
                injected += 1
            if status.startswith("skipped_unmanaged"):
                skipped_unmanaged += 1

    print(f"Scanned: {scanned}")
    if args.check:
        print(f"Stale/Missing sidecars: {stale}")
        return 1 if stale else 0

    print(f"Updated sidecars: {changed}")
    if args.inject:
        print(f"Injected envelopes: {injected}")
        print(f"Skipped unmanaged: {skipped_unmanaged}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
