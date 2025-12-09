"""
SSOT Glossary Generator — Generates master glossary output files.

Part of the SSOT Abbreviation System for the Chthonic Archive.
"""

from collections import defaultdict
from datetime import datetime
from pathlib import Path

from .models import AbbreviationStatus, SectionCoverage
from .registry import AbbreviationRegistry


def generate_markdown_glossary(registry: AbbreviationRegistry) -> str:
    """Generate complete markdown glossary from registry."""
    lines = [
        "# SSOT Master Abbreviation Glossary",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "**Source:** `copilot-instructions.md`",
        f"**Total Abbreviations:** {len(registry.entries)}",
        "",
        "---",
        "",
    ]

    # Generate statistics summary
    stats = registry.get_statistics()
    lines.extend([
        "## Statistics Summary",
        "",
        f"- **Total Entries:** {stats['total_entries']}",
        f"- **Validated:** {stats['validated']}",
        f"- **Deprecated:** {stats['deprecated']}",
        f"- **Pending Review:** {stats['pending_review']}",
        f"- **Categories:** {stats['by_category']}",
        "",
        "---",
        "",
    ])

    # Group by category
    by_category = defaultdict(list)
    for entry in registry.entries.values():
        by_category[entry.category].append(entry)

    # Category order (logical grouping)
    category_order = [
        "core_framework",
        "axioms",
        "entity_system",
        "crc_system",
        "linguistic_mandates",
        "protocols",
        "factions_prime",
        "factions_lesser",
        "physical_attributes",
        "special_archetypes",
        "tensor_framework",
        "development",
        "geometric_models",
        "uncategorized",
    ]

    category_titles = {
        "core_framework": "Core Framework",
        "axioms": "Foundational Axioms (FA¹⁻⁵)",
        "entity_system": "Entity System (Tiers)",
        "crc_system": "Conceptual Resonance Cores (CRCs)",
        "linguistic_mandates": "Linguistic Mandates",
        "protocols": "Protocols & Frameworks",
        "factions_prime": "Prime Factions (Tier 2)",
        "factions_lesser": "Lesser Factions (Tier 4)",
        "physical_attributes": "Physical & Attribute Systems",
        "special_archetypes": "Special Archetype Injections",
        "tensor_framework": "Tensor Framework (T³-MΨ)",
        "development": "Development Conventions",
        "geometric_models": "Geometric & Conceptual Models",
        "uncategorized": "Uncategorized",
    }

    # Generate each category section
    for category in category_order:
        if category not in by_category:
            continue

        entries = sorted(by_category[category], key=lambda e: e.abbreviation)
        title = category_titles.get(category, category.replace("_", " ").title())

        lines.extend([
            f"## {title}",
            "",
            "| Abbreviation | Full Term | Section | Status |",
            "|-------------|-----------|---------|--------|",
        ])

        for entry in entries:
            status_icon = {
                AbbreviationStatus.VALIDATED: "✅",
                AbbreviationStatus.DEPRECATED: "⚠️",
                AbbreviationStatus.PENDING_REVIEW: "🔍",
                AbbreviationStatus.DUPLICATE: "❌",
            }.get(entry.status, "❓")

            section = entry.section or "—"
            lines.append(f"| `{entry.abbreviation}` | {entry.full_term} | {section} | {status_icon} |")

        lines.extend(["", ""])

    # Add issues section if any
    issues = registry.get_issues()
    if issues:
        lines.extend([
            "---",
            "",
            "## Known Issues",
            "",
        ])
        for issue in issues:
            lines.append(f"- **{issue['abbreviation']}**: {issue['issue']}")
        lines.append("")

    # Add footer
    lines.extend([
        "---",
        "",
        "*This glossary is auto-generated from the SSOT parser.*",
        "*Manual edits will be overwritten on regeneration.*",
        "",
        "**🔥 ARCHITECTONIC INTEGRITY MAINTAINED 🔥**",
    ])

    return "\n".join(lines)


def generate_json_glossary(registry: AbbreviationRegistry) -> str:
    """Generate JSON export of glossary."""
    import json

    data = {
        "metadata": {
            "generated": datetime.now().isoformat(),
            "source": "copilot-instructions.md",
            "total_entries": len(registry.entries),
        },
        "statistics": registry.get_statistics(),
        "entries": [
            {
                "abbreviation": e.abbreviation,
                "full_term": e.full_term,
                "category": e.category,
                "section": e.section,
                "status": e.status.value,
                "notes": e.notes,
                "aliases": e.aliases,
                "first_seen_line": e.first_seen_line,
            }
            for e in sorted(registry.entries.values(), key=lambda x: x.abbreviation)
        ],
        "issues": registry.get_issues(),
    }

    return json.dumps(data, indent=2, ensure_ascii=False)


def generate_section_coverage_report(coverage: list[SectionCoverage]) -> str:
    """Generate section coverage report."""
    lines = [
        "# SSOT Section Coverage Report",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "---",
        "",
        "## Section Analysis",
        "",
        "| Section | Lines | Abbreviations | Has Guide | Status |",
        "|---------|-------|---------------|-----------|--------|",
    ]

    for section in coverage:
        guide_icon = "✅" if section.has_notation_guide else "❌"
        status_icon = "✅" if section.has_notation_guide else "⚠️ Needs Guide"
        lines.append(
            f"| {section.section_number}. {section.section_name} | "
            f"{section.line_start}-{section.line_end} | "
            f"{section.abbreviation_count} | {guide_icon} | {status_icon} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## Sections Missing Notation Guides",
        "",
    ])

    missing = [s for s in coverage if not s.has_notation_guide]
    if missing:
        for section in missing:
            lines.append(f"- **Section {section.section_number}** ({section.section_name})")
    else:
        lines.append("*All sections have notation guides.* ✅")

    return "\n".join(lines)


def generate_validation_report(validation_results: dict) -> str:
    """Generate validation report."""
    lines = [
        "# SSOT Abbreviation Validation Report",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "---",
        "",
    ]

    # Summary
    total_issues = sum(len(v) for v in validation_results.values())
    if total_issues == 0:
        lines.extend([
            "## ✅ Validation Passed",
            "",
            "No issues detected. Abbreviation system is architectonically sound.",
            "",
        ])
    else:
        lines.extend([
            f"## ⚠️ {total_issues} Issues Detected",
            "",
        ])

        # Detail each category
        issue_categories = [
            ("duplicates", "Duplicate Abbreviations"),
            ("too_long", "Excessively Long Abbreviations"),
            ("inconsistent_naming", "Inconsistent Naming"),
            ("missing_definitions", "Missing Definitions"),
            ("deprecated", "Deprecated Abbreviations Still In Use"),
        ]

        for key, title in issue_categories:
            issues = validation_results.get(key, [])
            if issues:
                lines.extend([
                    f"### {title}",
                    "",
                ])
                for issue in issues:
                    lines.append(f"- `{issue['abbreviation']}`: {issue['message']}")
                lines.append("")

    return "\n".join(lines)


def save_glossary_files(
    registry: AbbreviationRegistry,
    output_dir: Path,
    coverage: list[SectionCoverage] | None = None,
    validation_results: dict | None = None,
) -> dict[str, Path]:
    """Save all glossary files to output directory."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    files = {}

    # Master glossary (markdown)
    glossary_md = output_dir / "ABBREVIATION_GLOSSARY.md"
    glossary_md.write_text(generate_markdown_glossary(registry), encoding="utf-8")
    files["glossary_md"] = glossary_md

    # JSON export
    glossary_json = output_dir / "abbreviation_registry.json"
    glossary_json.write_text(generate_json_glossary(registry), encoding="utf-8")
    files["glossary_json"] = glossary_json

    # Coverage report
    if coverage:
        coverage_md = output_dir / "SECTION_COVERAGE.md"
        coverage_md.write_text(generate_section_coverage_report(coverage), encoding="utf-8")
        files["coverage_md"] = coverage_md

    # Validation report
    if validation_results:
        validation_md = output_dir / "VALIDATION_REPORT.md"
        validation_md.write_text(generate_validation_report(validation_results), encoding="utf-8")
        files["validation_md"] = validation_md

    return files
