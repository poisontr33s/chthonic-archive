"""
Command-Line Interface for SSOT Abbreviation System

Provides CLI access to all abbreviation management functions.
Invoke via: uv run python -m abbreviation_system <command>

Part of the ASC Abbreviation System for Codex Brahmanica Perfectus governance.
"""

import argparse
import sys
from pathlib import Path

from .generator import AbbreviationGenerator
from .models import NotationPattern
from .parser import SSOTParser
from .registry import AbbreviationRegistry
from .reporter import AuditReporter
from .validator import ConsistencyValidator

# Default SSOT path relative to mas_mcp
DEFAULT_SSOT_PATH = Path(__file__).parent.parent.parent / ".github" / "copilot-instructions.md"


def cmd_parse(args: argparse.Namespace) -> int:
    """Parse SSOT and display statistics."""
    ssot_path = args.ssot or DEFAULT_SSOT_PATH

    if not Path(ssot_path).exists():
        print(f"❌ SSOT file not found: {ssot_path}", file=sys.stderr)
        return 1

    print(f"📖 Parsing SSOT: {ssot_path}")
    parser = SSOTParser(str(ssot_path))
    abbreviations = parser.parse()

    print(f"✅ Found {len(abbreviations)} abbreviations")
    print()

    # Pattern breakdown
    patterns: dict[str, int] = {}
    for abbrev in abbreviations:
        pattern_name = abbrev.pattern.value
        patterns[pattern_name] = patterns.get(pattern_name, 0) + 1

    print("📊 Pattern Distribution:")
    for pattern, count in sorted(patterns.items(), key=lambda x: -x[1]):
        print(f"   {pattern}: {count}")

    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate SSOT abbreviations for consistency issues."""
    ssot_path = args.ssot or DEFAULT_SSOT_PATH

    if not Path(ssot_path).exists():
        print(f"❌ SSOT file not found: {ssot_path}", file=sys.stderr)
        return 1

    print(f"🔍 Validating SSOT: {ssot_path}")

    parser = SSOTParser(str(ssot_path))
    abbreviations = parser.parse()
    registry = AbbreviationRegistry(abbreviations)
    validator = ConsistencyValidator(registry)

    issues = validator.validate()

    if not issues:
        print("✅ No issues found! SSOT abbreviation system is healthy.")
        return 0

    errors = [i for i in issues if i.severity.value == "error"]
    warnings = [i for i in issues if i.severity.value == "warning"]
    info = [i for i in issues if i.severity.value == "info"]

    print(f"⚠️  Found {len(issues)} issues:")
    print(f"   🔴 Errors: {len(errors)}")
    print(f"   ⚠️  Warnings: {len(warnings)}")
    print(f"   ℹ️  Info: {len(info)}")
    print()

    if errors and args.verbose:
        print("🔴 Errors:")
        for issue in errors[:10]:
            print(f"   - {issue.issue_type.value}: {issue.description}")
        if len(errors) > 10:
            print(f"   ... and {len(errors) - 10} more")

    return 1 if errors else 0


def cmd_report(args: argparse.Namespace) -> int:
    """Generate comprehensive audit report."""
    ssot_path = args.ssot or DEFAULT_SSOT_PATH

    if not Path(ssot_path).exists():
        print(f"❌ SSOT file not found: {ssot_path}", file=sys.stderr)
        return 1

    print(f"📝 Generating report for: {ssot_path}")

    reporter = AuditReporter.from_ssot(str(ssot_path))
    report = reporter.generate_full_report()

    if args.output:
        output_path = Path(args.output)
        fmt = "json" if output_path.suffix == ".json" else "markdown"
        reporter.save_report(str(output_path), format=fmt, report=report)
        print(f"✅ Report saved to: {output_path}")
    else:
        # Print to stdout
        print()
        print(reporter.render_markdown(report))

    return 0


def cmd_glossary(args: argparse.Namespace) -> int:
    """Generate master glossary of all abbreviations."""
    ssot_path = args.ssot or DEFAULT_SSOT_PATH

    if not Path(ssot_path).exists():
        print(f"❌ SSOT file not found: {ssot_path}", file=sys.stderr)
        return 1

    print(f"📚 Generating glossary for: {ssot_path}")

    reporter = AuditReporter.from_ssot(str(ssot_path))
    glossary = reporter.generate_glossary()

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(glossary, encoding='utf-8')
        print(f"✅ Glossary saved to: {output_path}")
    else:
        print()
        print(glossary)

    return 0


def cmd_lookup(args: argparse.Namespace) -> int:
    """Look up an abbreviation or term."""
    ssot_path = args.ssot or DEFAULT_SSOT_PATH

    if not Path(ssot_path).exists():
        print(f"❌ SSOT file not found: {ssot_path}", file=sys.stderr)
        return 1

    registry = AbbreviationRegistry.from_ssot(str(ssot_path))
    query = args.query

    # Try exact match first
    expanded = registry.expand(query)
    if expanded:
        print(f"✅ `{query}` = {expanded}")
        return 0

    # Try reverse lookup
    abbreviated = registry.abbreviate(query)
    if abbreviated:
        print(f"✅ {query} → `{abbreviated}`")
        return 0

    # Try fuzzy search
    results = registry.search(query)
    if results:
        print(f"🔍 Search results for '{query}':")
        for abbrev in results[:10]:
            term = registry.expand(abbrev.abbrev)
            print(f"   `{abbrev.abbrev}` = {term}")
        return 0

    print(f"❌ No matches found for: {query}")
    return 1


def cmd_suggest(args: argparse.Namespace) -> int:
    """Suggest abbreviations for a term."""
    term = args.term
    tier = args.tier or "default"

    generator = AbbreviationGenerator()
    suggestions = generator.suggest_abbreviation(term, tier=tier)

    if not suggestions:
        print(f"❌ Could not generate suggestions for: {term}")
        return 1

    print(f"💡 Suggestions for '{term}':")
    for i, suggestion in enumerate(suggestions, 1):
        notation = generator.generate_notation(
            suggestion,
            term,
            NotationPattern.PARENTHETICAL
        )
        print(f"   {i}. `{suggestion}` → {notation}")

    return 0


def cmd_export(args: argparse.Namespace) -> int:
    """Export registry to JSON for persistence."""
    ssot_path = args.ssot or DEFAULT_SSOT_PATH

    if not Path(ssot_path).exists():
        print(f"❌ SSOT file not found: {ssot_path}", file=sys.stderr)
        return 1

    registry = AbbreviationRegistry.from_ssot(str(ssot_path))

    output_path = Path(args.output)
    registry.export_json(str(output_path))

    print(f"✅ Exported {len(registry._abbreviations)} abbreviations to: {output_path}")
    return 0


def cmd_hash(args: argparse.Namespace) -> int:
    """Compute SSOT hash for governance verification."""
    import hashlib
    import unicodedata

    ssot_path = args.ssot or DEFAULT_SSOT_PATH

    if not Path(ssot_path).exists():
        print(f"❌ SSOT file not found: {ssot_path}", file=sys.stderr)
        return 1

    # Read and canonicalize
    content = Path(ssot_path).read_text(encoding='utf-8')

    # Canonicalization per SSOT-VP protocol
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    lines = [line.rstrip() for line in content.split('\n')]
    content = '\n'.join(lines)
    content = unicodedata.normalize('NFC', content)
    content = content.strip()

    # Compute hash
    hash_value = hashlib.sha256(content.encode('utf-8')).hexdigest()

    print("🔐 SSOT Hash (SHA-256):")
    print(f"   {hash_value}")
    print()
    print(f"   File: {ssot_path}")
    print(f"   Size: {len(content)} bytes (canonical)")

    return 0


def main() -> int:
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        prog="abbreviation_system",
        description="SSOT Abbreviation Management System for Codex Brahmanica Perfectus",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run python -m abbreviation_system parse
  uv run python -m abbreviation_system validate --verbose
  uv run python -m abbreviation_system report -o audit_report.md
  uv run python -m abbreviation_system lookup TRM-VRT
  uv run python -m abbreviation_system suggest "Triumvirate Parallel Execution"
  uv run python -m abbreviation_system hash
        """
    )

    parser.add_argument(
        "--ssot",
        type=str,
        help=f"Path to SSOT file (default: {DEFAULT_SSOT_PATH})"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # parse command
    subparsers.add_parser("parse", help="Parse SSOT and show statistics")

    # validate command
    validate_parser = subparsers.add_parser("validate", help="Validate for consistency issues")
    validate_parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed issues")

    # report command
    report_parser = subparsers.add_parser("report", help="Generate comprehensive audit report")
    report_parser.add_argument("-o", "--output", type=str, help="Output file path")

    # glossary command
    glossary_parser = subparsers.add_parser("glossary", help="Generate master glossary")
    glossary_parser.add_argument("-o", "--output", type=str, help="Output file path")

    # lookup command
    lookup_parser = subparsers.add_parser("lookup", help="Look up abbreviation or term")
    lookup_parser.add_argument("query", type=str, help="Abbreviation or term to look up")

    # suggest command
    suggest_parser = subparsers.add_parser("suggest", help="Suggest abbreviations for a term")
    suggest_parser.add_argument("term", type=str, help="Term to abbreviate")
    suggest_parser.add_argument("--tier", type=str, help="Entity tier (default, tier_1, tier_4, etc.)")

    # export command
    export_parser = subparsers.add_parser("export", help="Export registry to JSON")
    export_parser.add_argument("-o", "--output", type=str, required=True, help="Output JSON file path")

    # hash command
    subparsers.add_parser("hash", help="Compute SSOT hash")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    # Dispatch to command handler
    commands = {
        "parse": cmd_parse,
        "validate": cmd_validate,
        "report": cmd_report,
        "glossary": cmd_glossary,
        "lookup": cmd_lookup,
        "suggest": cmd_suggest,
        "export": cmd_export,
        "hash": cmd_hash,
    }

    handler = commands.get(args.command)
    if handler:
        return handler(args)
    else:
        print(f"❌ Unknown command: {args.command}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
