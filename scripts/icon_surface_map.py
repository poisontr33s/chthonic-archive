#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: icon_surface_map.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Icon Surface Map — explain where Chthonic icon assets actually render.

Bridges source SVGs to their runtime surfaces:
- Explorer file icons
- Explorer folder icons
- Product icon glyph consumers
- Resource SVG surfaces

This resolves the common confusion where browsing `themes/icons/*.svg` makes it
look like the artwork is "not showing", when those files are only source assets.

@SID:           TOOL_ICON_SURFACE_MAP_V1
@Shabti:          Utility
@Purpose:       Icon Surface Map — explain where Chthonic icon assets actually render.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

from scripts.lib.shared import configure_utf8_output, find_repo_root

SKIP_DIRS: set[str] = {
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
    "dumpster-dive",
    ".next",
    "book",
}

NOISY_EXAMPLE_SEGMENTS: set[str] = {
    ".vscode-test",
    ".chthonic",
    ".venv",
    "node_modules",
    "site-packages",
    "vendor",
}

MAX_EXAMPLES = 4
THEME_ICON_RE = re.compile(r"\$\(([A-Za-z0-9-]+)\)")
NEW_THEME_ICON_RE = re.compile(r"ThemeIcon\s*\(\s*['\"]([A-Za-z0-9-]+)['\"]")
RESOURCE_ICON_RE = re.compile(r"resources/[A-Za-z0-9_.\-/]+\.svg")


def strip_json_comments(text: str) -> str:
    """Strip // and /* */ comments from JSONC while preserving string contents."""
    out: list[str] = []
    in_string = False
    in_line_comment = False
    in_block_comment = False
    escaped = False
    quote_char = ""
    i = 0

    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""

        if in_line_comment:
            if ch == "\n":
                in_line_comment = False
                out.append(ch)
            i += 1
            continue

        if in_block_comment:
            if ch == "*" and nxt == "/":
                in_block_comment = False
                i += 2
            else:
                i += 1
            continue

        if in_string:
            out.append(ch)
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote_char:
                in_string = False
            i += 1
            continue

        if ch in ("'", '"'):
            in_string = True
            quote_char = ch
            out.append(ch)
            i += 1
            continue

        if ch == "/" and nxt == "/":
            in_line_comment = True
            i += 2
            continue

        if ch == "/" and nxt == "*":
            in_block_comment = True
            i += 2
            continue

        out.append(ch)
        i += 1

    return "".join(out)


def strip_trailing_json_commas(text: str) -> str:
    """Strip trailing commas before } or ] while preserving string contents."""
    out: list[str] = []
    in_string = False
    escaped = False
    quote_char = ""
    i = 0

    while i < len(text):
        ch = text[i]

        if in_string:
            out.append(ch)
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote_char:
                in_string = False
            i += 1
            continue

        if ch in ("'", '"'):
            in_string = True
            quote_char = ch
            out.append(ch)
            i += 1
            continue

        if ch == ",":
            j = i + 1
            while j < len(text) and text[j] in " \t\r\n":
                j += 1
            if j < len(text) and text[j] in "}]":
                i += 1
                continue

        out.append(ch)
        i += 1

    return "".join(out)


def load_json(path: Path, *, jsonc: bool = False) -> dict:
    text = path.read_text(encoding="utf-8")
    if jsonc:
        text = strip_json_comments(text)
        text = strip_trailing_json_commas(text)
    return json.loads(text)


def rel(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def gather_workspace_examples(repo_root: Path) -> tuple[dict[str, list[str]], dict[str, list[str]], dict[str, list[str]]]:
    ext_examples: dict[str, list[str]] = defaultdict(list)
    file_name_examples: dict[str, list[str]] = defaultdict(list)
    folder_name_examples: dict[str, list[str]] = defaultdict(list)

    for dirpath, dirnames, filenames in os.walk(repo_root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        current_dir = Path(dirpath)

        for dirname in dirnames:
            folder_path = current_dir / dirname
            if is_noisy_example_path(folder_path):
                continue
            folder_key = dirname.lower()
            if len(folder_name_examples[folder_key]) < MAX_EXAMPLES:
                folder_name_examples[folder_key].append(rel(folder_path, repo_root))

        for filename in filenames:
            file_path = current_dir / filename
            if is_noisy_example_path(file_path):
                continue
            name_key = filename
            if len(file_name_examples[name_key]) < MAX_EXAMPLES:
                file_name_examples[name_key].append(rel(file_path, repo_root))

            suffix = file_path.suffix.lower().lstrip(".")
            if suffix and len(ext_examples[suffix]) < MAX_EXAMPLES:
                ext_examples[suffix].append(rel(file_path, repo_root))

    return ext_examples, file_name_examples, folder_name_examples


def append_unique(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)


def is_noisy_example_path(path: Path) -> bool:
    return any(part in NOISY_EXAMPLE_SEGMENTS for part in path.parts)


def collect_package_surfaces(extension_package: dict) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    product_surfaces: dict[str, list[str]] = defaultdict(list)
    resource_surfaces: dict[str, list[str]] = defaultdict(list)
    contributes = extension_package.get("contributes", {})

    for command in contributes.get("commands", []):
        icon = command.get("icon")
        command_id = command.get("command", "<unknown>")
        if isinstance(icon, str):
            match = THEME_ICON_RE.fullmatch(icon)
            if match:
                append_unique(product_surfaces[match.group(1)], f"package command {command_id}")

    for container in contributes.get("viewsContainers", {}).get("activitybar", []):
        icon = container.get("icon")
        container_id = container.get("id", "<unknown>")
        if isinstance(icon, str) and icon.startswith("resources/"):
            append_unique(resource_surfaces[icon], f"package activitybar {container_id}")

    for location, views in contributes.get("views", {}).items():
        for view in views:
            icon = view.get("icon")
            view_id = view.get("id", "<unknown>")
            if isinstance(icon, str):
                match = THEME_ICON_RE.fullmatch(icon)
                if match:
                    append_unique(product_surfaces[match.group(1)], f"package view {view_id}")
                elif icon.startswith("resources/"):
                    append_unique(resource_surfaces[icon], f"package view {view_id}")

    return product_surfaces, resource_surfaces


def collect_source_surfaces(src_root: Path, repo_root: Path) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    product_surfaces: dict[str, list[str]] = defaultdict(list)
    resource_surfaces: dict[str, list[str]] = defaultdict(list)

    for file_path in src_root.rglob("*.ts"):
        text = file_path.read_text(encoding="utf-8")
        rel_path = rel(file_path, repo_root)

        for lineno, line in enumerate(text.splitlines(), start=1):
            for match in NEW_THEME_ICON_RE.finditer(line):
                append_unique(
                    product_surfaces[match.group(1)],
                    f"source {rel_path}:{lineno}",
                )
            for match in THEME_ICON_RE.finditer(line):
                append_unique(
                    product_surfaces[match.group(1)],
                    f"source {rel_path}:{lineno}",
                )
            for match in RESOURCE_ICON_RE.finditer(line):
                append_unique(
                    resource_surfaces[match.group(0)],
                    f"source {rel_path}:{lineno}",
                )

    return product_surfaces, resource_surfaces


def build_file_icon_entries(
    repo_root: Path,
    file_theme: dict,
    ext_examples: dict[str, list[str]],
    file_name_examples: dict[str, list[str]],
) -> list[dict]:
    icon_definitions = file_theme.get("iconDefinitions", {})
    language_ids = file_theme.get("languageIds", {})
    file_extensions = file_theme.get("fileExtensions", {})
    file_names = file_theme.get("fileNames", {})

    triggers_by_icon: dict[str, dict[str, list[str]]] = defaultdict(
        lambda: {"extensions": [], "filenames": [], "language_ids": []}
    )

    for ext, icon_id in file_extensions.items():
        triggers_by_icon[icon_id]["extensions"].append(ext)
    for name, icon_id in file_names.items():
        triggers_by_icon[icon_id]["filenames"].append(name)
    for language_id, icon_id in language_ids.items():
        triggers_by_icon[icon_id]["language_ids"].append(language_id)

    entries: list[dict] = []
    for icon_id, definition in icon_definitions.items():
        icon_path = definition.get("iconPath", "")
        if not isinstance(icon_path, str) or not icon_path.startswith("./icons/file-"):
            continue

        source_path = repo_root / "extensions" / "chthonic-archive" / "themes" / icon_path.removeprefix("./")
        triggers = triggers_by_icon.get(icon_id, {"extensions": [], "filenames": [], "language_ids": []})
        examples: list[str] = []
        for ext in triggers["extensions"]:
            for example in ext_examples.get(ext, []):
                append_unique(examples, example)
        for name in triggers["filenames"]:
            for example in file_name_examples.get(name, []):
                append_unique(examples, example)

        entries.append(
            {
                "icon_id": icon_id,
                "source_svg": rel(source_path, repo_root),
                "triggers": {
                    "extensions": sorted(triggers["extensions"]),
                    "filenames": sorted(triggers["filenames"]),
                    "language_ids": sorted(triggers["language_ids"]),
                },
                "workspace_examples": examples[:MAX_EXAMPLES],
                "is_default": icon_id == file_theme.get("file"),
            }
        )

    entries.sort(key=lambda item: (not item["is_default"], item["source_svg"]))
    return entries


def build_folder_icon_entries(
    repo_root: Path,
    file_theme: dict,
    folder_examples: dict[str, list[str]],
) -> list[dict]:
    icon_definitions = file_theme.get("iconDefinitions", {})
    folder_names = file_theme.get("folderNames", {})
    folder_names_expanded = file_theme.get("folderNamesExpanded", {})

    folder_entries: dict[str, dict] = {}

    for folder_name, closed_icon_id in folder_names.items():
        open_icon_id = folder_names_expanded.get(folder_name)
        closed_path = icon_definitions.get(closed_icon_id, {}).get("iconPath", "")
        open_path = icon_definitions.get(open_icon_id, {}).get("iconPath", "") if open_icon_id else ""
        if not isinstance(closed_path, str) or not closed_path.startswith("./icons/folder-"):
            continue

        key = closed_icon_id
        entry = folder_entries.setdefault(
            key,
            {
                "closed_icon_id": closed_icon_id,
                "open_icon_id": open_icon_id,
                "closed_source_svg": rel(
                    repo_root / "extensions" / "chthonic-archive" / "themes" / closed_path.removeprefix("./"),
                    repo_root,
                ),
                "open_source_svg": rel(
                    repo_root / "extensions" / "chthonic-archive" / "themes" / open_path.removeprefix("./"),
                    repo_root,
                ) if open_path else None,
                "folder_names": [],
                "workspace_examples": [],
                "is_default": closed_icon_id == file_theme.get("folder"),
            },
        )

        append_unique(entry["folder_names"], folder_name)
        for example in folder_examples.get(folder_name.lower(), []):
            append_unique(entry["workspace_examples"], example)

    default_closed_id = file_theme.get("folder")
    default_open_id = file_theme.get("folderExpanded")
    if default_closed_id and default_closed_id in icon_definitions:
        default_closed_path = icon_definitions[default_closed_id].get("iconPath", "")
        default_open_path = icon_definitions.get(default_open_id, {}).get("iconPath", "") if default_open_id else ""
        if isinstance(default_closed_path, str) and default_closed_path.startswith("./icons/folder-"):
            folder_entries.setdefault(
                default_closed_id,
                {
                    "closed_icon_id": default_closed_id,
                    "open_icon_id": default_open_id,
                    "closed_source_svg": rel(
                        repo_root / "extensions" / "chthonic-archive" / "themes" / default_closed_path.removeprefix("./"),
                        repo_root,
                    ),
                    "open_source_svg": rel(
                        repo_root / "extensions" / "chthonic-archive" / "themes" / default_open_path.removeprefix("./"),
                        repo_root,
                    ) if default_open_path else None,
                    "folder_names": [],
                    "workspace_examples": [],
                    "is_default": True,
                },
            )

    entries = list(folder_entries.values())
    entries.sort(key=lambda item: (not item["is_default"], item["closed_source_svg"]))
    return entries


def build_product_entries(
    repo_root: Path,
    product_theme: dict,
    package_surfaces: dict[str, list[str]],
    source_surfaces: dict[str, list[str]],
) -> list[dict]:
    icon_definitions = product_theme.get("iconDefinitions", {})
    raw_entries: list[dict] = []

    for icon_id, definition in sorted(icon_definitions.items()):
        font_character = definition.get("fontCharacter", "")
        source_svg = repo_root / "extensions" / "chthonic-archive" / "themes" / "icons" / "product" / f"{icon_id}.svg"
        raw_entries.append(
            {
                "icon_id": icon_id,
                "source_svg": rel(source_svg, repo_root),
                "font_character": font_character,
                "package_surfaces": sorted(package_surfaces.get(icon_id, [])),
                "source_surfaces": sorted(source_surfaces.get(icon_id, [])),
            }
        )

    grouped_by_font: dict[str, list[dict]] = defaultdict(list)
    for entry in raw_entries:
        grouped_by_font[entry["font_character"]].append(entry)

    resolved_source_by_font: dict[str, str] = {}
    for font_character, group in grouped_by_font.items():
        existing = [entry for entry in group if (repo_root / entry["source_svg"]).exists()]
        if existing:
            existing.sort(key=lambda entry: (entry["icon_id"].endswith("-large"), len(entry["icon_id"]), entry["icon_id"]))
            resolved_source_by_font[font_character] = existing[0]["source_svg"]
        else:
            group_sorted = sorted(group, key=lambda entry: (entry["icon_id"].endswith("-large"), len(entry["icon_id"]), entry["icon_id"]))
            resolved_source_by_font[font_character] = group_sorted[0]["source_svg"]

    entries: list[dict] = []
    for entry in raw_entries:
        resolved_source = resolved_source_by_font.get(entry["font_character"], entry["source_svg"])
        entries.append(
            {
                **entry,
                "source_svg": resolved_source,
                "declared_source_svg": entry["source_svg"],
                "source_svg_exists": (repo_root / resolved_source).exists(),
            }
        )

    return entries


def build_resource_entries(
    repo_root: Path,
    package_surfaces: dict[str, list[str]],
    source_surfaces: dict[str, list[str]],
) -> list[dict]:
    surface_paths = sorted(set(package_surfaces) | set(source_surfaces))
    entries: list[dict] = []
    for resource_path in surface_paths:
        entries.append(
            {
                "resource_svg": resource_path,
                "package_surfaces": sorted(package_surfaces.get(resource_path, [])),
                "source_surfaces": sorted(source_surfaces.get(resource_path, [])),
            }
        )
    return entries


def collect_dormant_assets(
    repo_root: Path,
    file_entries: list[dict],
    folder_entries: list[dict],
    product_entries: list[dict],
) -> dict:
    theme_icons_root = repo_root / "extensions" / "chthonic-archive" / "themes" / "icons"

    mapped_sources: set[str] = set()
    for entry in file_entries:
        mapped_sources.add(entry["source_svg"])
    for entry in folder_entries:
        mapped_sources.add(entry["closed_source_svg"])
        if entry["open_source_svg"]:
            mapped_sources.add(entry["open_source_svg"])
    for entry in product_entries:
        mapped_sources.add(entry["source_svg"])

    unreferenced_source_svgs: list[str] = []
    for svg_path in sorted(theme_icons_root.rglob("*.svg")):
        if rel(svg_path, repo_root) not in mapped_sources:
            unreferenced_source_svgs.append(rel(svg_path, repo_root))

    mapped_but_unseen_files = [
        entry["source_svg"] for entry in file_entries
        if not entry["workspace_examples"] and not entry["is_default"]
    ]
    mapped_but_unseen_folders = [
        entry["closed_source_svg"] for entry in folder_entries
        if not entry["workspace_examples"] and not entry["is_default"]
    ]
    product_without_consumers = [
        entry["icon_id"] for entry in product_entries
        if not entry["package_surfaces"] and not entry["source_surfaces"]
    ]

    return {
        "unreferenced_source_svgs": unreferenced_source_svgs,
        "mapped_but_unseen_file_icons": mapped_but_unseen_files,
        "mapped_but_unseen_folder_icons": mapped_but_unseen_folders,
        "product_icons_without_consumers": product_without_consumers,
    }


def render_text_report(data: dict) -> str:
    lines: list[str] = []
    lines.append("Chthonic Icon Surface Map")
    lines.append("=========================")
    lines.append("")
    lines.append("What this answers:")
    lines.append("- Source SVGs do not usually render on themselves when browsed inside `themes/icons/`.")
    lines.append("- File icons render on matching files in the Explorer and tabs.")
    lines.append("- Folder icons render on matching folder names in the Explorer.")
    lines.append("- Product SVGs are source art only; runtime uses the font-backed product icon theme.")
    lines.append("")

    file_audio = next(
        (entry for entry in data["file_icons"] if entry["source_svg"].endswith("/file-audio.svg")),
        None,
    )
    product_folder_mapped = any(
        "product" in entry["folder_names"]
        for entry in data["folder_icons"]
    )

    lines.append("Direct Answer For The Screenshot")
    lines.append("-------------------------------")
    lines.append(
        "- `extensions/chthonic-archive/themes/icons/product/` is a source asset folder. "
        f"`product` is {'mapped' if product_folder_mapped else 'not mapped'}, so Explorer uses the default folder icon there."
    )
    if file_audio:
        extensions = ", ".join(file_audio["triggers"]["extensions"]) or "no mapped extensions"
        lines.append(
            "- `extensions/chthonic-archive/themes/icons/file-audio.svg` is source art. "
            f"Its runtime surface is files with extensions: {extensions}."
        )
    lines.append(
        "- The SVG library does not self-preview in the Explorer. Those files are still `.svg` documents, "
        "so they receive the `.svg` file icon when listed as source files."
    )
    lines.append("")

    settings = data["settings"]
    lines.append("Active Theme Selection")
    lines.append("----------------------")
    lines.append(f"- color theme: {settings.get('colorTheme', '<unset>')}")
    lines.append(
        f"- file icon theme: {settings.get('iconTheme', '<unset>')} "
        f"({'active' if settings.get('fileIconThemeActive') else 'mismatch'})"
    )
    lines.append(
        f"- product icon theme: {settings.get('productIconTheme', '<unset>')} "
        f"({'active' if settings.get('productIconThemeActive') else 'mismatch'})"
    )
    if data.get("installed_extension"):
        lines.append(f"- installed insiders extension: {data['installed_extension']}")
    lines.append("")

    lines.append("Explorer Folder Surfaces")
    lines.append("------------------------")
    for entry in data["folder_icons"]:
        if entry["is_default"]:
            continue
        lines.append(
            f"- {entry['closed_source_svg']} / {entry['open_source_svg']} -> "
            f"folder names: {', '.join(entry['folder_names'])}"
        )
        if entry["workspace_examples"]:
            lines.append(f"  examples: {', '.join(entry['workspace_examples'])}")
        else:
            lines.append("  examples: none in current workspace")
    lines.append("")

    lines.append("Explorer File Surfaces")
    lines.append("----------------------")
    for entry in data["file_icons"]:
        if entry["is_default"]:
            continue
        trigger_parts = []
        if entry["triggers"]["extensions"]:
            trigger_parts.append("ext " + ", ".join(entry["triggers"]["extensions"]))
        if entry["triggers"]["filenames"]:
            trigger_parts.append("names " + ", ".join(entry["triggers"]["filenames"]))
        if entry["triggers"]["language_ids"]:
            trigger_parts.append("lang " + ", ".join(entry["triggers"]["language_ids"]))
        trigger_text = "; ".join(trigger_parts) if trigger_parts else "no direct triggers recorded"
        lines.append(f"- {entry['source_svg']} -> {trigger_text}")
        if entry["workspace_examples"]:
            lines.append(f"  examples: {', '.join(entry['workspace_examples'])}")
    lines.append("")

    lines.append("Product Icon Surfaces")
    lines.append("---------------------")
    for entry in data["product_icons"]:
        lines.append(
            f"- {entry['source_svg']} -> product id `{entry['icon_id']}` "
            f"({entry['font_character']})"
        )
        if entry["package_surfaces"]:
            lines.append(f"  package: {', '.join(entry['package_surfaces'])}")
        if entry["source_surfaces"]:
            lines.append(f"  source: {', '.join(entry['source_surfaces'])}")
        if not entry["package_surfaces"] and not entry["source_surfaces"]:
            lines.append("  consumers: none found")
    lines.append("")

    lines.append("Resource SVG Surfaces")
    lines.append("---------------------")
    for entry in data["resource_icons"]:
        lines.append(f"- {entry['resource_svg']}")
        if entry["package_surfaces"]:
            lines.append(f"  package: {', '.join(entry['package_surfaces'])}")
        if entry["source_surfaces"]:
            lines.append(f"  source: {', '.join(entry['source_surfaces'])}")
    lines.append("")

    lines.append("Warnings")
    lines.append("--------")
    lines.append(
        "- Browsing files under `extensions/chthonic-archive/themes/icons/` shows their source files, "
        "not their runtime target. Those files themselves use the `.svg` file icon."
    )
    lines.append(
        "- Browsing `extensions/chthonic-archive/themes/icons/product/` does not show product icon runtime. "
        "Runtime uses `themes/fonts/chthonic-product-icons.woff` through the product icon theme."
    )
    for item in data["warnings"]["mapped_but_unseen_folder_icons"]:
        lines.append(f"- mapped folder icon with no current workspace example: {item}")
    for item in data["warnings"]["mapped_but_unseen_file_icons"]:
        lines.append(f"- mapped file icon with no current workspace example: {item}")
    for item in data["warnings"]["unreferenced_source_svgs"]:
        lines.append(f"- source svg on disk but not mapped by theme manifests: {item}")
    for item in data["warnings"]["product_icons_without_consumers"]:
        lines.append(f"- product icon id with no discovered static consumer: {item}")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    configure_utf8_output()

    parser = argparse.ArgumentParser(
        description="Map Chthonic source SVGs to their actual VS Code runtime surfaces."
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output file path. Defaults to stdout when omitted.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when icon themes are not active or unmapped source SVGs exist.",
    )
    args = parser.parse_args()

    repo_root = find_repo_root(Path(__file__).resolve())
    ext_root = repo_root / "extensions" / "chthonic-archive"

    workspace_settings = load_json(repo_root / ".vscode" / "settings.json", jsonc=True)
    extension_package = load_json(ext_root / "package.json")
    file_theme = load_json(ext_root / "themes" / "chthonic-file-icon-theme.json")
    product_theme = load_json(ext_root / "themes" / "chthonic-product-icon-theme.json")

    ext_examples, file_name_examples, folder_examples = gather_workspace_examples(repo_root)
    package_product_surfaces, package_resource_surfaces = collect_package_surfaces(extension_package)
    source_product_surfaces, source_resource_surfaces = collect_source_surfaces(ext_root / "src", repo_root)

    file_entries = build_file_icon_entries(repo_root, file_theme, ext_examples, file_name_examples)
    folder_entries = build_folder_icon_entries(repo_root, file_theme, folder_examples)
    product_entries = build_product_entries(
        repo_root,
        product_theme,
        package_product_surfaces,
        source_product_surfaces,
    )
    resource_entries = build_resource_entries(
        repo_root,
        package_resource_surfaces,
        source_resource_surfaces,
    )
    warnings = collect_dormant_assets(repo_root, file_entries, folder_entries, product_entries)

    installed_extension = None
    insiders_root = Path(os.environ.get("USERPROFILE", "")) / ".vscode-insiders" / "extensions"
    if insiders_root.exists():
        matches = sorted(insiders_root.glob("chthonic-archive.chthonic-archive-*"))
        if matches:
            installed_extension = rel(matches[-1], repo_root)

    contributed_file_theme_id = extension_package["contributes"]["iconThemes"][0]["id"]
    contributed_product_theme_id = extension_package["contributes"]["productIconThemes"][0]["id"]

    data = {
        "settings": {
            "colorTheme": workspace_settings.get("workbench.colorTheme"),
            "iconTheme": workspace_settings.get("workbench.iconTheme"),
            "productIconTheme": workspace_settings.get("workbench.productIconTheme"),
            "fileIconThemeActive": workspace_settings.get("workbench.iconTheme") == contributed_file_theme_id,
            "productIconThemeActive": workspace_settings.get("workbench.productIconTheme") == contributed_product_theme_id,
        },
        "installed_extension": installed_extension,
        "file_icons": file_entries,
        "folder_icons": folder_entries,
        "product_icons": product_entries,
        "resource_icons": resource_entries,
        "warnings": warnings,
    }

    if args.json:
        output_text = json.dumps(data, indent=2, ensure_ascii=False)
    else:
        output_text = render_text_report(data)

    if args.output:
        args.output.write_text(output_text + ("\n" if not output_text.endswith("\n") else ""), encoding="utf-8")
    else:
        print(output_text)

    if args.strict:
        strict_fail = (
            not data["settings"]["fileIconThemeActive"]
            or not data["settings"]["productIconThemeActive"]
            or bool(warnings["unreferenced_source_svgs"])
        )
        return 1 if strict_fail else 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
