#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: codebase_crude_inventory.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: DIAGNOSTIC
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Crude codebase inventory (unbiased).
Reports total files + total bytes,
file counts by extension,
largest files,
and top directories by file count,
unbiased by any policed filtering,
as an inventory snapshot tool.

@SID:           TOOL_CODEBASE_CRUDE_INVENTORY_V1
@Shabti:        CLI Script
@Purpose:       Crude codebase inventory (unbiased).
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple


@dataclass
class InventoryResult:
    total_files: int
    total_bytes: int
    by_extension: Dict[str, int]
    largest_files: List[Tuple[str, int]]
    top_dirs: List[Tuple[str, int]]
    top_dirs_by_size: List[Tuple[str, int]]
    by_language: Dict[str, int]
    by_class: Dict[str, int]
    size_buckets: Dict[str, int]
    binary_count: int
    text_count: int
    max_depth: int
    avg_depth: float
    deepest_paths: List[Tuple[str, int]]


class CodebaseInventory:
    def __init__(self, root: Path):
        self.root = root
        self.by_extension: Dict[str, int] = {}
        self.total_files = 0
        self.total_bytes = 0
        self.largest: List[Tuple[str, int]] = []
        self.dir_counts: Dict[str, int] = {}
        self.dir_sizes: Dict[str, int] = {}
        self.by_language: Dict[str, int] = {}
        self.by_class: Dict[str, int] = {}
        self.size_buckets: Dict[str, int] = {
            "0-1KB": 0,
            "1-10KB": 0,
            "10-100KB": 0,
            "100KB-1MB": 0,
            "1-10MB": 0,
            "10MB+": 0,
        }
        self.binary_count = 0
        self.text_count = 0
        self.depths: List[int] = []
        self.deepest: List[Tuple[str, int]] = []
        self.ext_by_topdir: Dict[str, Dict[str, int]] = {}

    def _record_file(self, path: Path):
        try:
            size = path.stat().st_size
        except OSError:
            return

        self.total_files += 1
        self.total_bytes += size

        ext = path.suffix.lower() if path.suffix else "(no_ext)"
        self.by_extension[ext] = self.by_extension.get(ext, 0) + 1

        rel = str(path.relative_to(self.root)).replace("\\", "/")
        self.largest.append((rel, size))

        # Count by first-level directory
        parts = rel.split("/", 1)
        top = parts[0] if parts else "(root)"
        self.dir_counts[top] = self.dir_counts.get(top, 0) + 1
        self.dir_sizes[top] = self.dir_sizes.get(top, 0) + size

        # Extension distribution per top-level dir
        if top not in self.ext_by_topdir:
            self.ext_by_topdir[top] = {}
        self.ext_by_topdir[top][ext] = self.ext_by_topdir[top].get(ext, 0) + 1

        # Language mapping (descriptive)
        lang = _language_for_extension(ext)
        self.by_language[lang] = self.by_language.get(lang, 0) + 1

        # Directory class mapping (descriptive)
        class_label = _class_for_path(rel)
        self.by_class[class_label] = self.by_class.get(class_label, 0) + 1

        # Size buckets
        _bucket_size(self.size_buckets, size)

        # Binary vs text heuristic
        if _is_binary(path):
            self.binary_count += 1
        else:
            self.text_count += 1

        # Depth stats
        depth = rel.count("/")
        self.depths.append(depth)
        self.deepest.append((rel, depth))

    def scan(self, max_files: int | None = None):
        for path in self.root.rglob("*"):
            if not path.is_file():
                continue
            self._record_file(path)
            if max_files and self.total_files >= max_files:
                break

    def summarize(self, top_n: int = 20) -> InventoryResult:
        largest = sorted(self.largest, key=lambda x: x[1], reverse=True)[:top_n]
        top_dirs = sorted(self.dir_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
        top_dirs_by_size = sorted(self.dir_sizes.items(), key=lambda x: x[1], reverse=True)[:top_n]
        deepest = sorted(self.deepest, key=lambda x: x[1], reverse=True)[:top_n]
        avg_depth = (sum(self.depths) / len(self.depths)) if self.depths else 0.0
        return InventoryResult(
            total_files=self.total_files,
            total_bytes=self.total_bytes,
            by_extension=dict(sorted(self.by_extension.items(), key=lambda x: x[1], reverse=True)),
            largest_files=largest,
            top_dirs=top_dirs,
            top_dirs_by_size=top_dirs_by_size,
            by_language=dict(sorted(self.by_language.items(), key=lambda x: x[1], reverse=True)),
            by_class=dict(sorted(self.by_class.items(), key=lambda x: x[1], reverse=True)),
            size_buckets=self.size_buckets,
            binary_count=self.binary_count,
            text_count=self.text_count,
            max_depth=max(self.depths) if self.depths else 0,
            avg_depth=avg_depth,
            deepest_paths=deepest,
        )


def safe_print(msg: str):
    try:
        print(msg)
    except UnicodeEncodeError:
        data = msg.encode("utf-8", errors="replace") + b"\n"
        sys.stdout.buffer.write(data)
        sys.stdout.flush()


def _language_for_extension(ext: str) -> str:
    mapping = {
        ".py": "python",
        ".pyi": "python",
        ".pyc": "python-binary",
        ".ps1": "powershell",
        ".psm1": "powershell",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".js": "javascript",
        ".jsx": "javascript",
        ".mjs": "javascript",
        ".cjs": "javascript",
        ".rs": "rust",
        ".cpp": "cpp",
        ".c": "c",
        ".h": "c",
        ".hpp": "cpp",
        ".cu": "cuda",
        ".toml": "config",
        ".yml": "config",
        ".yaml": "config",
        ".json": "data",
        ".md": "docs",
        ".rst": "docs",
        ".txt": "text",
        ".sh": "shell",
        ".cmd": "shell",
        ".bat": "shell",
        ".map": "map",
        ".onnx": "binary-model",
        ".pb": "binary-protobuf",
        ".pyd": "binary",
        ".dll": "binary",
        ".exe": "binary",
        "(no_ext)": "no_ext",
    }
    return mapping.get(ext, "other")


def _class_for_path(rel_path: str) -> str:
    parts = rel_path.split("/")
    head = parts[0] if parts else ""
    classes = {
        "src": "source",
        "scripts": "source",
        "mas_mcp": "source",
        "mcp": "source",
        "extensions": "source",
        "chthonic-vscode-extension": "source",
        "docs": "docs",
        "dumpster-dive": "archive",
        ".git": "vcs",
        "build": "build",
        "dist": "build",
        "target": "build",
        "node_modules": "vendor",
        ".venv": "env",
        ".codex": "config",
        ".github": "config",
    }
    return classes.get(head, "other")


def _bucket_size(buckets: Dict[str, int], size: int) -> None:
    if size <= 1024:
        buckets["0-1KB"] += 1
    elif size <= 10 * 1024:
        buckets["1-10KB"] += 1
    elif size <= 100 * 1024:
        buckets["10-100KB"] += 1
    elif size <= 1024 * 1024:
        buckets["100KB-1MB"] += 1
    elif size <= 10 * 1024 * 1024:
        buckets["1-10MB"] += 1
    else:
        buckets["10MB+"] += 1


def _is_binary(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            chunk = f.read(4096)
            if b"\x00" in chunk:
                return True
    except OSError:
        return False
    return False


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Unbiased codebase inventory")
    parser.add_argument("--root", type=str, default=".", help="Repo root to scan")
    parser.add_argument("--top", type=int, default=20, help="Top N entries to show")
    parser.add_argument("--max-files", type=int, default=None, help="Optional limit")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    inv = CodebaseInventory(root)
    inv.scan(max_files=args.max_files)
    summary = inv.summarize(top_n=args.top)

    safe_print("Codebase Crude Inventory")
    safe_print("-" * 60)
    safe_print(f"Root: {root}")
    safe_print(f"Total files: {summary.total_files}")
    safe_print(f"Total bytes: {summary.total_bytes}")
    safe_print("")
    safe_print("Top directories by file count:")
    for name, count in summary.top_dirs:
        safe_print(f"  {name:<30} {count}")
    safe_print("")
    safe_print("Top directories by total size (bytes):")
    for name, size in summary.top_dirs_by_size:
        safe_print(f"  {name:<30} {size}")
    safe_print("")
    safe_print("Top extensions by top directory (top 5 each):")
    for name, _count in summary.top_dirs:
        ext_map = inv.ext_by_topdir.get(name, {})
        top_exts = sorted(ext_map.items(), key=lambda x: x[1], reverse=True)[:5]
        if not top_exts:
            continue
        ext_line = ", ".join([f"{ext}:{cnt}" for ext, cnt in top_exts])
        safe_print(f"  {name:<30} {ext_line}")
    safe_print("")
    safe_print("Directory classes (descriptive):")
    for name, count in list(summary.by_class.items())[:args.top]:
        safe_print(f"  {name:<15} {count}")
    safe_print("")
    safe_print("Top extensions by file count:")
    for ext, count in list(summary.by_extension.items())[:args.top]:
        safe_print(f"  {ext:<10} {count}")
    safe_print("")
    safe_print("Top languages by file count:")
    for lang, count in list(summary.by_language.items())[:args.top]:
        safe_print(f"  {lang:<15} {count}")
    safe_print("")
    safe_print("Size buckets:")
    for name, count in summary.size_buckets.items():
        safe_print(f"  {name:<10} {count}")
    safe_print("")
    safe_print(f"Binary vs text: binary={summary.binary_count} text={summary.text_count}")
    safe_print(f"Depth: max={summary.max_depth} avg={summary.avg_depth:.2f}")
    safe_print("")
    safe_print("Largest files:")
    for path, size in summary.largest_files:
        safe_print(f"  {size:>10}  {path}")
    safe_print("")
    safe_print("Deepest paths (by depth):")
    for path, depth in summary.deepest_paths:
        safe_print(f"  depth={depth:<3} {path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
