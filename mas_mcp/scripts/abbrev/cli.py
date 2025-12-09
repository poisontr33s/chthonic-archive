"""
SSOT Abbreviation System: CLI Module

Command-line interface for abbreviation management.

Usage:
    uv run python -m mas_mcp.scripts.abbrev <command> [options]

Commands:
    generate    Generate master glossary
    validate    Run validation checks
    audit       Generate audit report
    backup      Create SSOT backup
    search      Search abbreviations
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime
import shutil

from .parser import SSOTParser
from .registry import AbbreviationRegistry
from .validator import AbbreviationValidator
from .generator import GlossaryGenerator, NotationGuideGenerator
from .reporter import ValidationReporter, AuditReporter


# Default paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
SSOT_PATH = PROJECT_ROOT / ".github" / "copilot-instructions.md"
DOCS_DIR = PROJECT_ROOT / "docs"
BACKUP_DIR = PROJECT_ROOT / "docs" / "ssot-backups"


def ensure_dirs():
    """Ensure output directories exist."""
    DOCS_DIR.mkdir(exist_ok=True)
    BACKUP_DIR.mkdir(exist_ok=True)


def cmd_generate(args):
    """Generate glossary and related documents."""
    ensure_dirs()
    
    print(f"📖 Parsing SSOT: {SSOT_PATH}")
    parser = SSOTParser(SSOT_PATH)
    registry = parser.parse()
    
    print(f"   Found {len(registry.abbreviations)} abbreviations")
    
    # Generate glossary
    glossary_path = DOCS_DIR / "ABBREVIATION_GLOSSARY.md"
    print(f"📝 Generating glossary: {glossary_path}")
    generator = GlossaryGenerator(registry)
    generator.generate_master_glossary(glossary_path)
    
    print("✅ Glossary generated successfully!")
    return 0


def cmd_validate(args):
    """Run validation checks."""
    ensure_dirs()
    
    print(f"🔍 Parsing SSOT: {SSOT_PATH}")
    parser = SSOTParser(SSOT_PATH)
    registry = parser.parse()
    
    print(f"   Found {len(registry.abbreviations)} abbreviations")
    
    # Run validation
    print("🔬 Running validation...")
    validator = AbbreviationValidator(registry)
    results = validator.validate_all()
    
    # Count by severity
    errors = sum(1 for r in results if r.severity.value == "error")
    warnings = sum(1 for r in results if r.severity.value == "warning")
    
    # Generate report
    report_path = DOCS_DIR / "VALIDATION_REPORT.md"
    print(f"📋 Generating report: {report_path}")
    reporter = ValidationReporter(validator)
    reporter.generate_report(report_path)
    
    # Summary
    if errors > 0:
        print(f"❌ Validation failed: {errors} errors, {warnings} warnings")
        return 1
    elif warnings > 0:
        print(f"⚠️  Validation passed with {warnings} warnings")
        return 0
    else:
        print("✅ Validation passed!")
        return 0


def cmd_audit(args):
    """Generate comprehensive audit report."""
    ensure_dirs()
    
    print(f"📊 Parsing SSOT: {SSOT_PATH}")
    parser = SSOTParser(SSOT_PATH)
    registry = parser.parse()
    
    print(f"   Found {len(registry.abbreviations)} abbreviations")
    
    # Generate audit report
    audit_path = DOCS_DIR / "ABBREVIATION_AUDIT.md"
    print(f"📋 Generating audit report: {audit_path}")
    reporter = AuditReporter(registry)
    reporter.generate_audit_report(audit_path)
    
    # Also generate validation report
    validator = AbbreviationValidator(registry)
    validation_path = DOCS_DIR / "VALIDATION_REPORT.md"
    ValidationReporter(validator).generate_report(validation_path)
    
    print("✅ Audit complete!")
    return 0


def cmd_backup(args):
    """Create timestamped SSOT backup."""
    ensure_dirs()
    
    if not SSOT_PATH.exists():
        print(f"❌ SSOT not found: {SSOT_PATH}")
        return 1
    
    # Create backup with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"copilot-instructions_{timestamp}.md"
    backup_path = BACKUP_DIR / backup_name
    
    print(f"💾 Creating backup: {backup_path}")
    shutil.copy2(SSOT_PATH, backup_path)
    
    # Also compute hash
    import hashlib
    with open(SSOT_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    hash_value = hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
    
    # Write hash file
    hash_path = backup_path.with_suffix('.hash')
    hash_path.write_text(f"{hash_value}\n{timestamp}\n{len(content)} bytes\n")
    
    print(f"   Hash: {hash_value}")
    print("✅ Backup created!")
    return 0


def cmd_search(args):
    """Search abbreviations."""
    parser = SSOTParser(SSOT_PATH)
    registry = parser.parse()
    
    query = args.query.upper()
    matches = registry.search(query)
    
    if not matches:
        print(f"No matches found for '{args.query}'")
        return 1
    
    print(f"Found {len(matches)} matches for '{args.query}':\n")
    
    for abbr in matches:
        status = "✅" if abbr.status.value == "active" else "⚠️"
        print(f"  {status} `{abbr.short_form}` = {abbr.full_term}")
        if abbr.category:
            print(f"      Category: {abbr.category}")
        if abbr.section:
            print(f"      Section: {abbr.section}")
        print()
    
    return 0


def cmd_stats(args):
    """Show abbreviation statistics."""
    parser = SSOTParser(SSOT_PATH)
    registry = parser.parse()
    stats = registry.get_statistics()
    
    print("\n📊 SSOT Abbreviation Statistics\n")
    print(f"   Total: {stats['total']}")
    print("\n   By Status:")
    for status, count in stats['by_status'].items():
        print(f"      {status}: {count}")
    print("\n   By Category:")
    for cat, count in sorted(stats['by_category'].items(), key=lambda x: -x[1]):
        print(f"      {cat}: {count}")
    print()
    
    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="abbrev",
        description="ASC Abbreviation System Manager"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate master glossary")
    gen_parser.set_defaults(func=cmd_generate)
    
    # Validate command
    val_parser = subparsers.add_parser("validate", help="Run validation checks")
    val_parser.set_defaults(func=cmd_validate)
    
    # Audit command
    audit_parser = subparsers.add_parser("audit", help="Generate audit report")
    audit_parser.set_defaults(func=cmd_audit)
    
    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Create SSOT backup")
    backup_parser.set_defaults(func=cmd_backup)
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search abbreviations")
    search_parser.add_argument("query", help="Search term")
    search_parser.set_defaults(func=cmd_search)
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show statistics")
    stats_parser.set_defaults(func=cmd_stats)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
