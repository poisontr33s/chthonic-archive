"""
SSOT Abbreviation System CLI — Command-line interface.

Usage:
    uv run python -m mas_mcp.scripts.ssot_abbrev.cli [command] [options]

Commands:
    audit       Run full abbreviation audit
    glossary    Generate master glossary
    validate    Validate abbreviation consistency
    backup      Create SSOT backup
    report      Generate specific reports
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from shutil import copy2


def get_ssot_path() -> Path:
    """Get path to SSOT document."""
    # Navigate from mas_mcp/scripts/ssot_abbrev to project root
    project_root = Path(__file__).parent.parent.parent.parent
    ssot_path = project_root / ".github" / "copilot-instructions.md"

    if not ssot_path.exists():
        # Try alternate locations
        alt_paths = [
            Path("c:/Users/erdno/chthonic-archive/.github/copilot-instructions.md"),
            Path(".github/copilot-instructions.md"),
        ]
        for alt in alt_paths:
            if alt.exists():
                return alt
        raise FileNotFoundError(f"SSOT not found at {ssot_path} or alternates")

    return ssot_path


def cmd_audit(args):
    """Run full abbreviation audit."""
    from .parser import SSOTParser
    from .registry import AbbreviationRegistry
    from .reporter import AbbreviationReporter
    from .validator import AbbreviationValidator

    print("\n🔍 SSOT Abbreviation Audit Starting...\n")

    ssot_path = get_ssot_path()
    print(f"📄 Reading: {ssot_path}")

    content = ssot_path.read_text(encoding="utf-8")

    # Parse
    parser = SSOTParser()
    entries = parser.parse_document(content)
    print(f"✅ Parsed {len(entries)} abbreviation entries")

    # Build registry
    registry = AbbreviationRegistry()
    for entry in entries:
        registry.add_entry(entry)

    # Validate
    validator = AbbreviationValidator(registry)
    issues = validator.validate_all()

    # Report
    reporter = AbbreviationReporter(registry)
    print(reporter.console_summary())

    if args.recommendations:
        print(reporter.standardization_recommendations())

    return 0


def cmd_glossary(args):
    """Generate master glossary."""
    from .generator import save_glossary_files
    from .parser import SSOTParser
    from .registry import AbbreviationRegistry

    print("\n📚 Generating Master Glossary...\n")

    ssot_path = get_ssot_path()
    content = ssot_path.read_text(encoding="utf-8")

    parser = SSOTParser()
    entries = parser.parse_document(content)

    registry = AbbreviationRegistry()
    for entry in entries:
        registry.add_entry(entry)

    # Output directory
    output_dir = Path(args.output) if args.output else ssot_path.parent / "glossary"

    files = save_glossary_files(registry, output_dir)

    print("✅ Generated glossary files:")
    for name, path in files.items():
        print(f"   📄 {path}")

    return 0


def cmd_validate(args):
    """Validate abbreviation consistency."""
    from .parser import SSOTParser
    from .registry import AbbreviationRegistry
    from .validator import AbbreviationValidator

    print("\n🔎 Validating Abbreviation Consistency...\n")

    ssot_path = get_ssot_path()
    content = ssot_path.read_text(encoding="utf-8")

    parser = SSOTParser()
    entries = parser.parse_document(content)

    registry = AbbreviationRegistry()
    for entry in entries:
        registry.add_entry(entry)

    validator = AbbreviationValidator(registry)
    results = validator.validate_all()

    total_issues = sum(len(v) for v in results.values())

    if total_issues == 0:
        print("✅ All validations passed! Abbreviation system is architectonically sound.")
        return 0
    else:
        print(f"⚠️ {total_issues} issues detected:\n")
        for category, issues in results.items():
            if issues:
                print(f"  {category}:")
                for issue in issues:
                    print(f"    • {issue['abbreviation']}: {issue['message']}")
        return 1


def cmd_backup(args):
    """Create SSOT backup."""
    from .parser import SSOTParser
    from .registry import AbbreviationRegistry
    from .reporter import AbbreviationReporter

    print("\n💾 Creating SSOT Backup...\n")

    ssot_path = get_ssot_path()

    # Create backup directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path(args.output) if args.output else ssot_path.parent.parent / "backups" / f"ssot_backup_{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Copy SSOT
    backup_ssot = backup_dir / "copilot-instructions.md"
    copy2(ssot_path, backup_ssot)
    print(f"✅ Copied SSOT to: {backup_ssot}")

    # Generate glossary in backup
    content = ssot_path.read_text(encoding="utf-8")
    parser = SSOTParser()
    entries = parser.parse_document(content)

    registry = AbbreviationRegistry()
    for entry in entries:
        registry.add_entry(entry)

    from .generator import save_glossary_files
    files = save_glossary_files(registry, backup_dir)

    # Generate manifest
    reporter = AbbreviationReporter(registry)
    manifest = reporter.generate_backup_manifest(backup_dir)
    (backup_dir / "MANIFEST.md").write_text(manifest, encoding="utf-8")

    print(f"✅ Backup complete: {backup_dir}")
    print(f"   📄 Files: {len(files) + 2}")

    return 0


def cmd_report(args):
    """Generate specific reports."""
    from .parser import SSOTParser
    from .registry import AbbreviationRegistry
    from .reporter import AbbreviationReporter

    ssot_path = get_ssot_path()
    content = ssot_path.read_text(encoding="utf-8")

    parser = SSOTParser()
    entries = parser.parse_document(content)

    registry = AbbreviationRegistry()
    for entry in entries:
        registry.add_entry(entry)

    reporter = AbbreviationReporter(registry)

    if args.category:
        print(reporter.detailed_category_report(args.category))
    elif args.issue:
        print(reporter.issue_drill_down(args.issue))
    else:
        print(reporter.console_summary())

    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="SSOT Abbreviation System — Audit, validate, and manage abbreviations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Audit command
    audit_parser = subparsers.add_parser("audit", help="Run full abbreviation audit")
    audit_parser.add_argument("-r", "--recommendations", action="store_true",
                              help="Include standardization recommendations")

    # Glossary command
    glossary_parser = subparsers.add_parser("glossary", help="Generate master glossary")
    glossary_parser.add_argument("-o", "--output", help="Output directory")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate abbreviation consistency")

    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Create SSOT backup")
    backup_parser.add_argument("-o", "--output", help="Backup directory")

    # Report command
    report_parser = subparsers.add_parser("report", help="Generate specific reports")
    report_parser.add_argument("-c", "--category", help="Report on specific category")
    report_parser.add_argument("-i", "--issue", help="Drill down on specific issue type")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    commands = {
        "audit": cmd_audit,
        "glossary": cmd_glossary,
        "validate": cmd_validate,
        "backup": cmd_backup,
        "report": cmd_report,
    }

    try:
        return commands[args.command](args)
    except Exception as e:
        print(f"❌ Error: {e}")
        if "--debug" in sys.argv:
            raise
        return 1


if __name__ == "__main__":
    sys.exit(main())
