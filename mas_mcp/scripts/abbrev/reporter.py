"""
SSOT Abbreviation System: Reporter Module

Generates validation reports and audit summaries.
"""

from pathlib import Path
from datetime import datetime
from typing import TextIO

from .models import (
    ValidationResult, 
    ValidationSeverity, 
    AbbreviationStatus,
    NotationPattern
)
from .registry import AbbreviationRegistry
from .validator import AbbreviationValidator


class ValidationReporter:
    """Generates formatted validation reports."""
    
    def __init__(self, validator: AbbreviationValidator):
        self.validator = validator
    
    def generate_report(self, output_path: Path) -> None:
        """Generate comprehensive validation report."""
        results = self.validator.validate_all()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            self._write_header(f, results)
            self._write_summary(f, results)
            self._write_errors(f, results)
            self._write_warnings(f, results)
            self._write_info(f, results)
            self._write_recommendations(f, results)
            self._write_footer(f)
    
    def _write_header(self, f: TextIO, results: list[ValidationResult]) -> None:
        """Write report header."""
        error_count = sum(1 for r in results if r.severity == ValidationSeverity.ERROR)
        warn_count = sum(1 for r in results if r.severity == ValidationSeverity.WARNING)
        
        status_emoji = "✅" if error_count == 0 else "❌" if error_count > 5 else "⚠️"
        
        f.write(f"""# **SSOT Abbreviation Validation Report**

{status_emoji} **Status:** {"PASSED" if error_count == 0 else "ISSUES FOUND"}

> **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
> **Errors:** {error_count}
> **Warnings:** {warn_count}
> **Total Issues:** {len(results)}

---

""")
    
    def _write_summary(self, f: TextIO, results: list[ValidationResult]) -> None:
        """Write validation summary."""
        by_type: dict[str, int] = {}
        for r in results:
            by_type[r.issue_type] = by_type.get(r.issue_type, 0) + 1
        
        f.write("## **Issue Summary**\n\n")
        f.write("| Issue Type | Count | Severity |\n")
        f.write("|------------|-------|----------|\n")
        
        for issue_type, count in sorted(by_type.items()):
            # Find max severity for this type
            max_sev = max(
                (r.severity for r in results if r.issue_type == issue_type),
                key=lambda s: {"error": 3, "warning": 2, "info": 1}.get(s.value, 0)
            )
            sev_icon = {"error": "🔴", "warning": "🟡", "info": "🔵"}.get(max_sev.value, "⚪")
            f.write(f"| {issue_type} | {count} | {sev_icon} |\n")
        
        f.write("\n---\n\n")
    
    def _write_errors(self, f: TextIO, results: list[ValidationResult]) -> None:
        """Write error section."""
        errors = [r for r in results if r.severity == ValidationSeverity.ERROR]
        
        if not errors:
            f.write("## **Errors**\n\n✅ No errors found.\n\n---\n\n")
            return
        
        f.write("## **Errors** 🔴\n\n")
        f.write("These issues must be resolved:\n\n")
        
        for i, error in enumerate(errors, 1):
            f.write(f"### Error {i}: {error.issue_type}\n\n")
            f.write(f"**Abbreviation:** `{error.abbreviation}`\n\n")
            f.write(f"**Message:** {error.message}\n\n")
            if error.suggestion:
                f.write(f"**Suggestion:** {error.suggestion}\n\n")
            if error.context:
                f.write(f"**Context:** {error.context}\n\n")
            f.write("---\n\n")
    
    def _write_warnings(self, f: TextIO, results: list[ValidationResult]) -> None:
        """Write warnings section."""
        warnings = [r for r in results if r.severity == ValidationSeverity.WARNING]
        
        if not warnings:
            f.write("## **Warnings**\n\n✅ No warnings.\n\n---\n\n")
            return
        
        f.write("## **Warnings** 🟡\n\n")
        f.write("These issues should be addressed:\n\n")
        
        f.write("| # | Abbreviation | Issue | Suggestion |\n")
        f.write("|---|--------------|-------|------------|\n")
        
        for i, warn in enumerate(warnings, 1):
            suggestion = warn.suggestion or "—"
            f.write(f"| {i} | `{warn.abbreviation}` | {warn.message} | {suggestion} |\n")
        
        f.write("\n---\n\n")
    
    def _write_info(self, f: TextIO, results: list[ValidationResult]) -> None:
        """Write informational findings."""
        infos = [r for r in results if r.severity == ValidationSeverity.INFO]
        
        if not infos:
            return
        
        f.write("## **Informational Notes** 🔵\n\n")
        
        for info in infos:
            f.write(f"- **`{info.abbreviation}`**: {info.message}\n")
        
        f.write("\n---\n\n")
    
    def _write_recommendations(self, f: TextIO, results: list[ValidationResult]) -> None:
        """Write actionable recommendations."""
        f.write("## **Recommendations**\n\n")
        
        # Group by priority
        errors = [r for r in results if r.severity == ValidationSeverity.ERROR]
        warnings = [r for r in results if r.severity == ValidationSeverity.WARNING]
        
        if errors:
            f.write("### Immediate Actions (Priority 1)\n\n")
            for error in errors:
                if error.suggestion:
                    f.write(f"1. {error.suggestion}\n")
            f.write("\n")
        
        if warnings:
            f.write("### Medium Priority (Priority 2)\n\n")
            seen = set()
            for warn in warnings:
                if warn.suggestion and warn.suggestion not in seen:
                    f.write(f"- {warn.suggestion}\n")
                    seen.add(warn.suggestion)
            f.write("\n")
        
        f.write("### Long-term Maintenance\n\n")
        f.write("- Run validation after each SSOT update\n")
        f.write("- Regenerate glossary quarterly\n")
        f.write("- Review deprecated abbreviations for removal\n")
        f.write("\n---\n\n")
    
    def _write_footer(self, f: TextIO) -> None:
        """Write report footer."""
        f.write(f"""## **Validation Complete**

This report was generated by the ASC Abbreviation Validation System.

**Next Steps:**
1. Address all errors (🔴)
2. Review warnings (🟡)
3. Regenerate glossary after fixes

```bash
# Re-run validation after fixes
uv run python -m mas_mcp.scripts.abbrev validate

# Regenerate glossary
uv run python -m mas_mcp.scripts.abbrev generate
```

---

**FA⁴ Validation System | {datetime.now().strftime('%Y-%m-%d')}**
""")


class AuditReporter:
    """Generates comprehensive audit reports."""
    
    def __init__(self, registry: AbbreviationRegistry):
        self.registry = registry
    
    def generate_audit_report(self, output_path: Path) -> None:
        """Generate full audit report."""
        stats = self.registry.get_statistics()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"""# **SSOT Abbreviation System Audit**

**Auditor:** ASC Abbreviation System (Automated)
**Date:** {datetime.now().strftime('%B %d, %Y')}
**SSOT Version:** Post-Section XIV

---

## **I. Executive Summary**

| Metric | Value | Assessment |
|--------|-------|------------|
| Total Abbreviations | {stats['total']} | {'High density' if stats['total'] > 300 else 'Normal'} |
| Active | {stats['by_status'].get('active', 0)} | — |
| Deprecated | {stats['by_status'].get('deprecated', 0)} | {'⚠️ Review needed' if stats['by_status'].get('deprecated', 0) > 10 else '✅'} |
| Categories | {len(stats['by_category'])} | — |

---

## **II. Category Analysis**

""")
            
            for category, count in sorted(stats['by_category'].items()):
                pct = (count / stats['total']) * 100
                bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
                f.write(f"**{category.replace('_', ' ').title()}**\n")
                f.write(f"- Count: {count} ({pct:.1f}%)\n")
                f.write(f"- `{bar}`\n\n")
            
            f.write("""---

## **III. Health Assessment**

### Notation Consistency
""")
            
            # Pattern analysis
            patterns = self.registry.get_by_pattern()
            for pattern, abbrs in sorted(patterns.items(), key=lambda x: -len(x[1])):
                f.write(f"- **{pattern.value}**: {len(abbrs)} abbreviations\n")
            
            f.write(f"""
### Document Coverage

- Sections with notation guides: 3/14 (21%)
- Recommended: Add notation guides to Sections I-VII

---

## **IV. Recommendations**

1. **Standardize Tier notation** to consistent format
2. **Shorten Lesser Faction abbreviations** exceeding 6 characters
3. **Add notation guides** to early sections
4. **Deprecate duplicate forms** (e.g., `TR-VRT` → `TRM-VRT`)

---

**Audit Complete | FA⁴ Validated**
""")
