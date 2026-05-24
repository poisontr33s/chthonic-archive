#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: icon_scaffold_contract_audit.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Icon Scaffold Contract Audit — classify the Chthonic icon scaffold without
assuming ownership over the art itself.

Buckets are structural, not aesthetic:
- canonical
- alias
- active consumer
- active workbench override
- dormant but valid
- upcycle candidate
- authored substrate
- broad utility mapping
- vendor spillover

@SID:           TOOL_ICON_SCAFFOLD_CONTRACT_AUDIT_V1
@Shabti:          Utility
@Purpose:       Icon Scaffold Contract Audit — classify the Chthonic icon scaffold without
"""

from __future__ import annotations


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

# sys.path guard: ensure repo root is importable regardless of invocation CWD
_REPO_ROOT_CANDIDATE = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT_CANDIDATE) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT_CANDIDATE))

from scripts.icon_surface_map import (
    build_file_icon_entries,
    build_folder_icon_entries,
    build_product_entries,
    collect_package_surfaces,
    collect_source_surfaces,
    gather_workspace_examples,
    load_json,
)
from scripts.lib.shared import configure_utf8_output, find_repo_root
from scripts.product_icon_census import (
    THEME_PATH,
    classify_tier,
    find_codicon_csv,
    functional_category,
    load_codicon_ids,
)


REPORT_PATH = Path("docs/design/ICON_SCAFFOLD_CONTRACT_AUDIT.md")
FALLBACK_CODICON_IDS = Path("extensions/chthonic-archive/themes/codicon_ids_raw.txt")

SPILLOVER_ROOTS: set[str] = {
    "meta-ide",
}

SPILLOVER_SEGMENTS: set[str] = {
    "node_modules",
    "site-packages",
    "vendor",
    ".vscode-test",
}


def rel(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root).as_posix()


def load_valid_runtime_ids(repo_root: Path) -> set[str]:
    csv_path = find_codicon_csv()
    if csv_path is not None:
        return set(load_codicon_ids(csv_path))
    fallback = repo_root / FALLBACK_CODICON_IDS
    if fallback.exists():
        return set(fallback.read_text(encoding="utf-8").splitlines())
    return set()


def choose_alias_primary(group: list[dict], repo_root: Path) -> str:
    def score(entry: dict) -> tuple[int, int, int, str]:
        source_exists = (repo_root / entry["source_svg"]).exists()
        large_penalty = 1 if entry["icon_id"].endswith("-large") else 0
        local_consumer_penalty = 0 if (entry["package_surfaces"] or entry["source_surfaces"]) else 1
        source_penalty = 0 if source_exists else 1
        return (source_penalty, large_penalty, local_consumer_penalty, entry["icon_id"])

    return sorted(group, key=score)[0]["icon_id"]


def classify_workspace_path(example: str) -> str:
    parts = PurePosixPath(example).parts
    if not parts:
        return "authored"
    if parts[0] in SPILLOVER_ROOTS:
        return "spillover"
    if any(part in SPILLOVER_SEGMENTS for part in parts):
        return "spillover"
    if any(part.startswith(".venv") for part in parts):
        return "spillover"
    return "authored"


def classify_mapping_surface(workspace_examples: list[str]) -> dict[str, object]:
    if not workspace_examples:
        return {
            "status": "mapped but unseen",
            "authored_examples": [],
            "spillover_examples": [],
        }

    authored_examples = [example for example in workspace_examples if classify_workspace_path(example) == "authored"]
    spillover_examples = [example for example in workspace_examples if classify_workspace_path(example) == "spillover"]

    if authored_examples and spillover_examples:
        status = "broad utility mapping"
    elif authored_examples:
        status = "authored substrate"
    else:
        status = "vendor spillover"

    return {
        "status": status,
        "authored_examples": authored_examples,
        "spillover_examples": spillover_examples,
    }


def build_product_scaffold(repo_root: Path, product_entries: list[dict]) -> dict[str, object]:
    valid_runtime_ids = load_valid_runtime_ids(repo_root)
    groups: dict[str, list[dict]] = defaultdict(list)
    for entry in product_entries:
        groups[entry["font_character"]].append(entry)

    alias_groups: list[dict[str, object]] = []
    alias_lookup: dict[str, dict[str, object]] = {}
    canonical_entries: list[dict[str, object]] = []

    for font_character, group in sorted(
        groups.items(),
        key=lambda item: choose_alias_primary(item[1], repo_root),
    ):
        sorted_group = sorted(group, key=lambda entry: entry["icon_id"])
        icon_ids = [entry["icon_id"] for entry in sorted_group]
        primary_id = choose_alias_primary(sorted_group, repo_root)
        primary_entry = next(item for item in sorted_group if item["icon_id"] == primary_id)
        resolved_group_sources: list[str] = []
        for entry in sorted_group:
            source_svg = entry["source_svg"]
            if not (repo_root / source_svg).exists():
                source_svg = primary_entry["source_svg"]
            if source_svg not in resolved_group_sources:
                resolved_group_sources.append(source_svg)
        group_record = {
            "font_character": font_character,
            "primary_id": primary_id,
            "runtime_ids": icon_ids,
            "aliases": [icon_id for icon_id in icon_ids if icon_id != primary_id],
            "source_svgs": resolved_group_sources,
        }
        if len(sorted_group) > 1:
            alias_groups.append(group_record)
        for entry in sorted_group:
            tier = classify_tier(entry["icon_id"])
            local_consumer = bool(entry["package_surfaces"] or entry["source_surfaces"])
            is_alias = entry["icon_id"] != primary_id
            source_svg = entry["source_svg"]
            source_exists = (repo_root / source_svg).exists()
            if is_alias and not source_exists:
                source_svg = primary_entry["source_svg"]
                source_exists = (repo_root / source_svg).exists()
            if local_consumer:
                scaffold_status = "active consumer"
            elif tier == 1:
                scaffold_status = "active workbench override"
            else:
                scaffold_status = "dormant but valid"

            canonical_record = {
                "icon_id": entry["icon_id"],
                "source_svg": source_svg,
                "declared_source_svg": entry["source_svg"],
                "source_svg_exists": source_exists,
                "font_character": font_character,
                "valid_runtime_id": entry["icon_id"] in valid_runtime_ids,
                "tier": tier,
                "functional_category": functional_category(entry["icon_id"]),
                "package_surfaces": entry["package_surfaces"],
                "source_surfaces": entry["source_surfaces"],
                "local_consumer": local_consumer,
                "scaffold_status": scaffold_status,
                "is_alias": is_alias,
                "canonical_id": primary_id,
                "alias_group": icon_ids,
                "upcycle_candidate": (
                    not is_alias
                    and not local_consumer
                    and tier in {3, 4}
                ),
            }
            canonical_entries.append(canonical_record)
            alias_lookup[entry["icon_id"]] = canonical_record

    summary = {
        "runtime_ids": len(product_entries),
        "unique_glyphs": len(groups),
        "aliases": sum(max(0, len(group) - 1) for group in groups.values()),
        "active_consumers": sum(1 for entry in canonical_entries if entry["scaffold_status"] == "active consumer"),
        "active_workbench_overrides": sum(1 for entry in canonical_entries if entry["scaffold_status"] == "active workbench override"),
        "dormant_but_valid": sum(1 for entry in canonical_entries if entry["scaffold_status"] == "dormant but valid"),
        "upcycle_candidates": sum(1 for entry in canonical_entries if entry["upcycle_candidate"]),
        "invalid_runtime_ids": sum(1 for entry in canonical_entries if not entry["valid_runtime_id"]),
    }

    return {
        "summary": summary,
        "entries": canonical_entries,
        "alias_groups": alias_groups,
    }


def build_mapping_scaffold(entries: list[dict], *, kind: str) -> dict[str, object]:
    classified_entries: list[dict[str, object]] = []
    for entry in entries:
        if entry.get("is_default"):
            continue
        mapping = classify_mapping_surface(entry["workspace_examples"])
        record = {
            "status": mapping["status"],
            "authored_examples": mapping["authored_examples"],
            "spillover_examples": mapping["spillover_examples"],
        }
        if kind == "file":
            record.update(
                {
                    "icon_id": entry["icon_id"],
                    "source_svg": entry["source_svg"],
                    "trigger_extensions": entry["triggers"]["extensions"],
                    "trigger_filenames": entry["triggers"]["filenames"],
                    "trigger_language_ids": entry["triggers"]["language_ids"],
                }
            )
        else:
            record.update(
                {
                    "closed_icon_id": entry["closed_icon_id"],
                    "open_icon_id": entry["open_icon_id"],
                    "closed_source_svg": entry["closed_source_svg"],
                    "open_source_svg": entry["open_source_svg"],
                    "folder_names": entry["folder_names"],
                }
            )
        classified_entries.append(record)

    counts = Counter(entry["status"] for entry in classified_entries)
    return {
        "summary": {
            "authored_substrate": counts["authored substrate"],
            "broad_utility_mapping": counts["broad utility mapping"],
            "vendor_spillover": counts["vendor spillover"],
            "mapped_but_unseen": counts["mapped but unseen"],
        },
        "entries": classified_entries,
    }


def build_report(data: dict[str, object]) -> str:
    product = data["product_scaffold"]
    file_scaffold = data["file_scaffold"]
    folder_scaffold = data["folder_scaffold"]

    lines: list[str] = []
    lines.append("# Icon Scaffold Contract Audit")
    lines.append("")
    lines.append("> Generated by `scripts/icon_scaffold_contract_audit.py` (`TOOL_ICON_SCAFFOLD_CONTRACT_AUDIT_V1`)")
    lines.append("")
    lines.append("This audit classifies the icon scaffold structurally. It does not claim ownership")
    lines.append("over the art. The buckets are existence, linkage, aliasing, consumer pressure,")
    lines.append("and spillover risk.")
    lines.append("")
    lines.append("## Product Scaffold Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|---|---:|")
    for key in (
        "runtime_ids",
        "unique_glyphs",
        "aliases",
        "active_consumers",
        "active_workbench_overrides",
        "dormant_but_valid",
        "upcycle_candidates",
        "invalid_runtime_ids",
    ):
        label = key.replace("_", " ")
        lines.append(f"| {label} | {product['summary'][key]} |")
    lines.append("")
    lines.append(
        "Structural rule: "
        f"`{product['summary']['runtime_ids']}` runtime IDs, "
        f"`{product['summary']['unique_glyphs']}` unique glyphs, "
        f"`{product['summary']['aliases']}` aliases."
    )
    lines.append("")

    lines.append("## Product Alias Groups")
    lines.append("")
    lines.append("| Canonical | Aliases | Source SVGs |")
    lines.append("|---|---|---|")
    if product["alias_groups"]:
        for group in product["alias_groups"]:
            aliases = ", ".join(group["aliases"]) if group["aliases"] else "—"
            sources = ", ".join(PurePosixPath(path).name for path in group["source_svgs"])
            lines.append(f"| `{group['primary_id']}` | `{aliases}` | `{sources}` |")
    else:
        lines.append("| — | — | — |")
    lines.append("")

    def emit_product_table(title: str, predicate) -> None:
        rows = [entry for entry in product["entries"] if predicate(entry)]
        lines.append(f"## {title}")
        lines.append("")
        lines.append("| Runtime ID | Tier | Category | Source SVG | Consumer Evidence |")
        lines.append("|---|---:|---|---|---|")
        if rows:
            for entry in sorted(rows, key=lambda item: item["icon_id"]):
                evidence = entry["package_surfaces"] + entry["source_surfaces"]
                evidence_text = "<br>".join(evidence) if evidence else "—"
                lines.append(
                    f"| `{entry['icon_id']}` | {entry['tier']} | {entry['functional_category']} | "
                    f"`{PurePosixPath(entry['source_svg']).name}` | {evidence_text} |"
                )
        else:
            lines.append("| — | — | — | — | — |")
        lines.append("")

    emit_product_table("Active Consumers", lambda entry: entry["scaffold_status"] == "active consumer")
    emit_product_table(
        "Active Workbench Overrides",
        lambda entry: entry["scaffold_status"] == "active workbench override" and not entry["is_alias"],
    )
    emit_product_table(
        "Dormant But Valid Product Icons",
        lambda entry: entry["scaffold_status"] == "dormant but valid" and not entry["is_alias"],
    )
    emit_product_table("Upcycle Candidates", lambda entry: entry["upcycle_candidate"])

    lines.append("## File Scaffold Summary")
    lines.append("")
    lines.append("| Bucket | Count |")
    lines.append("|---|---:|")
    for key in ("authored_substrate", "broad_utility_mapping", "vendor_spillover", "mapped_but_unseen"):
        label = key.replace("_", " ")
        lines.append(f"| {label} | {file_scaffold['summary'][key]} |")
    lines.append("")

    lines.append("## Folder Scaffold Summary")
    lines.append("")
    lines.append("| Bucket | Count |")
    lines.append("|---|---:|")
    for key in ("authored_substrate", "broad_utility_mapping", "vendor_spillover", "mapped_but_unseen"):
        label = key.replace("_", " ")
        lines.append(f"| {label} | {folder_scaffold['summary'][key]} |")
    lines.append("")

    def emit_mapping_table(title: str, entries: list[dict[str, object]], *, kind: str) -> None:
        lines.append(f"## {title}")
        lines.append("")
        if kind == "folder":
            lines.append("| Family | Mapped Names | Authored Examples | Spillover Examples |")
            lines.append("|---|---|---|---|")
            if entries:
                for entry in entries:
                    family = PurePosixPath(entry["closed_source_svg"]).name
                    mapped_names = ", ".join(f"`{name}`" for name in entry["folder_names"])
                    authored = "<br>".join(entry["authored_examples"]) if entry["authored_examples"] else "—"
                    spillover = "<br>".join(entry["spillover_examples"]) if entry["spillover_examples"] else "—"
                    lines.append(f"| `{family}` | {mapped_names} | {authored} | {spillover} |")
            else:
                lines.append("| — | — | — | — |")
        else:
            lines.append("| SVG | Triggers | Authored Examples | Spillover Examples |")
            lines.append("|---|---|---|---|")
            if entries:
                for entry in entries:
                    trigger_parts: list[str] = []
                    if entry["trigger_extensions"]:
                        trigger_parts.append("ext " + ", ".join(f"`{ext}`" for ext in entry["trigger_extensions"]))
                    if entry["trigger_filenames"]:
                        trigger_parts.append("names " + ", ".join(f"`{name}`" for name in entry["trigger_filenames"]))
                    if entry["trigger_language_ids"]:
                        trigger_parts.append("lang " + ", ".join(f"`{lang}`" for lang in entry["trigger_language_ids"]))
                    triggers = "<br>".join(trigger_parts) if trigger_parts else "—"
                    authored = "<br>".join(entry["authored_examples"]) if entry["authored_examples"] else "—"
                    spillover = "<br>".join(entry["spillover_examples"]) if entry["spillover_examples"] else "—"
                    lines.append(
                        f"| `{PurePosixPath(entry['source_svg']).name}` | {triggers} | {authored} | {spillover} |"
                    )
            else:
                lines.append("| — | — | — | — |")
        lines.append("")

    emit_mapping_table(
        "Folder Families: Authored Substrate",
        sorted(
            [entry for entry in folder_scaffold["entries"] if entry["status"] == "authored substrate"],
            key=lambda item: PurePosixPath(item["closed_source_svg"]).name,
        ),
        kind="folder",
    )
    emit_mapping_table(
        "Folder Families: Broad Utility Mapping",
        sorted(
            [entry for entry in folder_scaffold["entries"] if entry["status"] == "broad utility mapping"],
            key=lambda item: PurePosixPath(item["closed_source_svg"]).name,
        ),
        kind="folder",
    )
    emit_mapping_table(
        "Folder Families: Vendor Spillover",
        sorted(
            [entry for entry in folder_scaffold["entries"] if entry["status"] == "vendor spillover"],
            key=lambda item: PurePosixPath(item["closed_source_svg"]).name,
        ),
        kind="folder",
    )
    emit_mapping_table(
        "Folder Families: Mapped But Unseen",
        sorted(
            [entry for entry in folder_scaffold["entries"] if entry["status"] == "mapped but unseen"],
            key=lambda item: PurePosixPath(item["closed_source_svg"]).name,
        ),
        kind="folder",
    )
    emit_mapping_table(
        "File Icons: Vendor Spillover",
        sorted(
            [entry for entry in file_scaffold["entries"] if entry["status"] == "vendor spillover"],
            key=lambda item: PurePosixPath(item["source_svg"]).name,
        ),
        kind="file",
    )
    emit_mapping_table(
        "File Icons: Mapped But Unseen",
        sorted(
            [entry for entry in file_scaffold["entries"] if entry["status"] == "mapped but unseen"],
            key=lambda item: PurePosixPath(item["source_svg"]).name,
        ),
        kind="file",
    )

    lines.append("## Interpretation")
    lines.append("")
    lines.append("- `canonical` and `alias` describe scaffold structure, not artistic merit.")
    lines.append("- `active consumer` means local package/source evidence exists in this repo.")
    lines.append("- `active workbench override` means no local static consumer was found, but the runtime ID is a live Tier 1 workbench slot.")
    lines.append("- `dormant but valid` means the runtime ID is legal and mapped, but no local consumer pressure is currently proven.")
    lines.append("- `upcycle candidate` is a bonus-mission bucket, not a deletion signal.")
    lines.append("- `vendor spillover` records where broad mappings currently pay for bundled or external lanes.")
    lines.append("")

    return "\n".join(lines) + "\n"


def build_audit(repo_root: Path) -> dict[str, object]:
    ext_root = repo_root / "extensions" / "chthonic-archive"
    extension_package = load_json(ext_root / "package.json")
    file_theme = load_json(ext_root / "themes" / "chthonic-file-icon-theme.json")
    product_theme = load_json(THEME_PATH)

    ext_examples, file_name_examples, folder_examples = gather_workspace_examples(repo_root)
    package_product_surfaces, package_resource_surfaces = collect_package_surfaces(extension_package)
    source_product_surfaces, source_resource_surfaces = collect_source_surfaces(ext_root / "src", repo_root)
    _ = package_resource_surfaces, source_resource_surfaces

    file_entries = build_file_icon_entries(repo_root, file_theme, ext_examples, file_name_examples)
    folder_entries = build_folder_icon_entries(repo_root, file_theme, folder_examples)
    product_entries = build_product_entries(
        repo_root,
        product_theme,
        package_product_surfaces,
        source_product_surfaces,
    )

    product_scaffold = build_product_scaffold(repo_root, product_entries)
    file_scaffold = build_mapping_scaffold(file_entries, kind="file")
    folder_scaffold = build_mapping_scaffold(folder_entries, kind="folder")

    return {
        "repo_root": rel(repo_root, repo_root),
        "product_scaffold": product_scaffold,
        "file_scaffold": file_scaffold,
        "folder_scaffold": folder_scaffold,
    }


def _print_audit_diff(prev: dict, curr: dict) -> None:
    """Print a human-readable diff summary between two audit JSON snapshots."""
    sections = ["product_scaffold", "file_scaffold", "folder_scaffold"]
    print("\n[diff] Audit comparison:")
    changed = False
    for section in sections:
        prev_sec = prev.get(section, {})
        curr_sec = curr.get(section, {})
        # Compare entry counts
        prev_count = len(prev_sec.get("entries", []))
        curr_count = len(curr_sec.get("entries", []))
        if prev_count != curr_count:
            delta = curr_count - prev_count
            sign = "+" if delta > 0 else ""
            print(f"  {section}: entries {prev_count} → {curr_count} ({sign}{delta})")
            changed = True
        # Compare summary dicts if present
        for key in ("by_tier", "by_bucket", "by_category"):
            prev_val = prev_sec.get(key, {})
            curr_val = curr_sec.get(key, {})
            if prev_val != curr_val:
                all_keys = set(prev_val) | set(curr_val)
                for k in sorted(all_keys):
                    pv = prev_val.get(k, 0)
                    cv = curr_val.get(k, 0)
                    if pv != cv:
                        sign = "+" if cv - pv > 0 else ""
                        print(f"  {section}.{key}[{k!r}]: {pv} → {cv} ({sign}{cv - pv})")
                        changed = True
    if not changed:
        print("  No structural changes detected.")


def main() -> int:
    configure_utf8_output()

    parser = argparse.ArgumentParser(description="Audit the Chthonic icon scaffold contract.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of markdown.")
    parser.add_argument(
        "--output",
        type=Path,
        help="Write output to a file. Defaults to stdout when omitted.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero if runtime IDs are invalid or any mapped SVG source is missing.",
    )
    parser.add_argument(
        "--diff",
        type=Path,
        metavar="PREV_JSON",
        help="Compare current audit JSON against a previous JSON snapshot and print diff summary.",
    )
    args = parser.parse_args()

    repo_root = find_repo_root(Path(__file__).resolve())
    audit = build_audit(repo_root)

    if args.json:
        output = json.dumps(audit, indent=2, ensure_ascii=False) + "\n"
    else:
        output = build_report(audit)

    if args.output:
        if not args.output.parent.exists():
            args.output.parent.mkdir(parents=True, exist_ok=True)
            print(f"  mkdir: {args.output.parent}", file=sys.stderr)
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")

    # --diff: compare current JSON against previous snapshot
    if getattr(args, "diff", None) and args.diff.is_file():
        try:
            prev = json.loads(args.diff.read_text(encoding="utf-8"))
            curr = json.loads(json.dumps(audit, ensure_ascii=False))  # normalise
            _print_audit_diff(prev, curr)
        except Exception as exc:  # noqa: BLE001
            print(f"  [diff] failed to compare: {exc}", file=sys.stderr)

    if args.strict:
        product_entries = audit["product_scaffold"]["entries"]
        invalid_runtime = any(not entry["valid_runtime_id"] for entry in product_entries)

        missing_sources = False
        for entry in audit["file_scaffold"]["entries"]:
            if not (repo_root / entry["source_svg"]).exists():
                missing_sources = True
                break
        if not missing_sources:
            for entry in audit["folder_scaffold"]["entries"]:
                if not (repo_root / entry["closed_source_svg"]).exists():
                    missing_sources = True
                    break
                if not (repo_root / entry["open_source_svg"]).exists():
                    missing_sources = True
                    break
        if not missing_sources:
            for entry in product_entries:
                if not entry["source_svg_exists"]:
                    missing_sources = True
                    break

        return 1 if invalid_runtime or missing_sources else 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
