"""
Audit Report Generator Module

Generates comprehensive audit reports for SSOT abbreviation analysis.
Implements FA⁵ (Visual Integrity) - clear, structured presentation of findings.

Part of the ASC Abbreviation System for Codex Brahmanica Perfectus governance.
"""

from datetime import datetime
from pathlib import Path

from .models import (
    AbbreviationEntry,
    AuditReport,
    ConsistencyIssue,
    IssueCategory,
    IssueSeverity,
    SectionStats,
)
from .parser import SSOTParser
from .registry import AbbreviationRegistry
from .validator import ConsistencyValidator


class AuditReporter:
    """
    Generates comprehensive audit reports for SSOT abbreviations.

    Report types:
    - Full audit report (markdown)
    - Summary statistics (JSON)
    - Issue-specific reports
    - Pattern analysis
    - Recommendation document
    """

    def __init__(
        self,
        parser: SSOTParser,
        registry: AbbreviationRegistry,
        validator: ConsistencyValidator
    ):
        self.parser = parser
        self.registry = registry
        self.validator = validator

    @classmethod
    def from_ssot(cls, ssot_path: str) -> "AuditReporter":
        """
        Create an AuditReporter from an SSOT file path.

        Args:
            ssot_path: Path to the SSOT markdown file

        Returns:
            Configured AuditReporter instance
        """
        parser = SSOTParser()
        entries = parser.parse_file(ssot_path)  # This also sets parser.ssot_path
        registry = AbbreviationRegistry()
        registry.add_entries(entries)
        validator = ConsistencyValidator(registry)

        return cls(parser, registry, validator)

    def generate_full_report(self) -> AuditReport:
        """
        Generate a complete audit report.

        Returns:
            AuditReport model with all findings
        """
        abbreviations = self.registry.all_abbreviations()

        # Read SSOT content for validation
        ssot_content = ""
        ssot_hash = ""
        total_lines = 0
        if self.parser.ssot_path:
            ssot_content = Path(self.parser.ssot_path).read_text(encoding="utf-8")
            total_lines = len(ssot_content.splitlines())
            import hashlib
            ssot_hash = hashlib.sha256(ssot_content.encode()).hexdigest()[:16]

        issues = self.validator.validate_all(ssot_content)

        # Calculate pattern distribution
        pattern_counts = self._count_patterns()

        # Calculate section distribution (as SectionStats list)
        section_stats = self._build_section_stats()

        return AuditReport(
            ssot_path=str(self.parser.ssot_path or ""),
            ssot_hash=ssot_hash,
            total_lines=total_lines,
            total_abbreviations=len(abbreviations),
            unique_abbreviations=len(abbreviations),
            pattern_counts=pattern_counts,
            section_stats=section_stats,
            issues=issues,
            health_metrics=self._calculate_health_metrics(issues, len(abbreviations))
        )

    def _count_patterns(self) -> dict[str, int]:
        """Count abbreviations by notation pattern."""
        counts: dict[str, int] = {}
        for abbrev in self.registry.all_entries():
            pattern_name = abbrev.pattern_type.value
            counts[pattern_name] = counts.get(pattern_name, 0) + 1
        return counts

    def _count_sections(self) -> dict[str, int]:
        """Count abbreviations by SSOT section."""
        counts: dict[str, int] = {}
        for abbrev in self.registry.all_entries():
            section = abbrev.section or "Unknown"
            counts[section] = counts.get(section, 0) + 1
        return counts

    def _build_section_stats(self) -> list[SectionStats]:
        """Build section statistics list."""
        section_counts = self._count_sections()
        return [
            SectionStats(
                section_name=name,
                section_number=str(idx),
                line_start=0,  # Not tracked in current parser
                line_end=0,    # Not tracked in current parser
                abbreviation_count=count,
            )
            for idx, (name, count) in enumerate(section_counts.items())
        ]

    def _calculate_health_metrics(
        self, issues: list[ConsistencyIssue], total_abbrevs: int
    ) -> dict[str, float]:
        """Calculate health metrics for the SSOT."""
        critical = sum(1 for i in issues if i.severity == IssueSeverity.CRITICAL)
        warnings = sum(1 for i in issues if i.severity == IssueSeverity.WARNING)

        # Health score: 100 - (critical * 10) - (warnings * 2), clamped to 0-100
        health_score = max(0.0, min(100.0, 100.0 - (critical * 10) - (warnings * 2)))

        return {
            "health_score": health_score,
            "critical_issues": float(critical),
            "warning_issues": float(warnings),
            "total_issues": float(len(issues)),
            "abbreviations_per_issue": (
                total_abbrevs / len(issues) if issues else float(total_abbrevs)
            ),
        }

    def _generate_recommendations(self, issues: list[ConsistencyIssue]) -> list[str]:
        """Generate actionable recommendations based on issues found."""
        recommendations = []

        # Count issue categories
        category_counts: dict[IssueCategory, int] = {}
        for issue in issues:
            category_counts[issue.category] = category_counts.get(issue.category, 0) + 1

        # Generate recommendations based on issue patterns
        if category_counts.get(IssueCategory.DUPLICATE, 0) > 0:
            recommendations.append(
                f"🔴 CRITICAL: {category_counts[IssueCategory.DUPLICATE]} duplicate abbreviations found. "
                "Standardize on single definition for each abbreviation."
            )

        if category_counts.get(IssueCategory.SPELLING_VARIANT, 0) > 3:
            recommendations.append(
                f"⚠️ WARNING: {category_counts[IssueCategory.SPELLING_VARIANT]} spelling variants found. "
                "Consider consolidating to reduce cognitive load."
            )

        if category_counts.get(IssueCategory.EXCESSIVE_LENGTH, 0) > 5:
            recommendations.append(
                f"📏 STYLE: {category_counts[IssueCategory.EXCESSIVE_LENGTH]} abbreviations exceed 8 characters. "
                "Consider shortening Lesser Faction abbreviations to 4-char max."
            )

        if category_counts.get(IssueCategory.SEMANTIC_OVERLOAD, 0) > 0:
            recommendations.append(
                "📐 NOTATION: Slash `/` semantics are overloaded (OR vs AND). "
                "Standardize: `/` for OR alternatives, `+` for AND combinations."
            )

        if category_counts.get(IssueCategory.MISSING_DEFINITION, 0) > 0:
            recommendations.append(
                "📚 DOCUMENTATION: Some abbreviations used but never defined. "
                "Add definitions or notation guides retrospectively."
            )

        if not recommendations:
            recommendations.append("✅ No critical issues found. SSOT abbreviation system is healthy.")

        return recommendations

    def render_markdown(self, report: AuditReport | None = None) -> str:
        """
        Render the audit report as markdown.

        Args:
            report: Optional pre-generated report; generates new if None

        Returns:
            Formatted markdown string
        """
        if report is None:
            report = self.generate_full_report()

        lines = [
            "# SSOT Abbreviation Audit Report",
            "",
            f"**Generated:** {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**SSOT File:** `{report.ssot_path}`",
            f"**SSOT Hash:** `{report.ssot_hash[:12]}...`" if report.ssot_hash else "",
            "",
            "---",
            "",
            "## Executive Summary",
            "",
            f"- **Total Abbreviations:** {report.total_abbreviations}",
            f"- **Unique Abbreviations:** {report.unique_abbreviations}",
            f"- **Issues Found:** {len(report.issues)}",
            "",
        ]

        # Pattern distribution
        lines.extend([
            "## Pattern Distribution",
            "",
            "| Pattern | Count |",
            "|---------|-------|",
        ])
        for pattern, count in sorted(report.pattern_counts.items(), key=lambda x: -x[1]):
            lines.append(f"| {pattern} | {count} |")
        lines.append("")

        # Section distribution
        lines.extend([
            "## Section Distribution",
            "",
            "| Section | Count |",
            "|---------|-------|",
        ])
        for stat in report.section_stats:
            lines.append(f"| {stat.section_name} | {stat.abbreviation_count} |")
        lines.append("")

        # Issues by severity
        lines.extend([
            "## Issues Found",
            "",
        ])

        critical = [i for i in report.issues if i.severity == IssueSeverity.CRITICAL]
        warnings = [i for i in report.issues if i.severity == IssueSeverity.WARNING]
        info = [i for i in report.issues if i.severity == IssueSeverity.INFO]

        if critical:
            lines.extend([
                "### 🔴 Critical",
                "",
            ])
            for issue in critical[:10]:  # Cap at 10
                lines.append(f"- **{issue.category.value}**: {issue.description}")
                if issue.affected_entries:
                    affected_abbrevs = [e.abbreviation for e in issue.affected_entries]
                    lines.append(f"  - Affected: `{', '.join(affected_abbrevs)}`")
            if len(critical) > 10:
                lines.append(f"- ... and {len(critical) - 10} more critical issues")
            lines.append("")

        if warnings:
            lines.extend([
                "### ⚠️ Warnings",
                "",
            ])
            for issue in warnings[:10]:
                lines.append(f"- **{issue.category.value}**: {issue.description}")
            if len(warnings) > 10:
                lines.append(f"- ... and {len(warnings) - 10} more warnings")
            lines.append("")

        if info:
            lines.extend([
                "### ℹ️ Info",
                "",
            ])
            for issue in info[:5]:
                lines.append(f"- {issue.description}")
            if len(info) > 5:
                lines.append(f"- ... and {len(info) - 5} more info items")
            lines.append("")

        # Recommendations
        lines.extend([
            "## Recommendations",
            "",
        ])
        for i, rec in enumerate(report.recommendations, 1):
            lines.append(f"{i}. {rec}")
        lines.append("")

        # Footer
        lines.extend([
            "---",
            "",
            "*Report generated by ASC Abbreviation System (MMPS-PAGRO)*",
            "*Codex Brahmanica Perfectus - FA⁴ Validation Protocol*",
        ])

        return '\n'.join(lines)

    def render_json(self, report: AuditReport | None = None) -> str:
        """
        Render the audit report as JSON.

        Args:
            report: Optional pre-generated report; generates new if None

        Returns:
            JSON string
        """
        if report is None:
            report = self.generate_full_report()

        return report.model_dump_json(indent=2)

    def save_report(
        self,
        output_path: str,
        format: str = "markdown",
        report: AuditReport | None = None
    ) -> Path:
        """
        Save the audit report to a file.

        Args:
            output_path: Path to save the report
            format: "markdown" or "json"
            report: Optional pre-generated report

        Returns:
            Path to the saved file
        """
        if report is None:
            report = self.generate_full_report()

        path = Path(output_path)

        if format == "json":
            content = self.render_json(report)
        else:
            content = self.render_markdown(report)

        path.write_text(content, encoding='utf-8')
        return path

    def generate_glossary(self) -> str:
        """
        Generate a master glossary of all abbreviations.

        Returns:
            Formatted markdown glossary
        """
        lines = [
            "# SSOT Master Glossary",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total Entries:** {len(self.registry.all_entries())}",
            "",
            "---",
            "",
        ]

        # Group by pattern
        by_pattern: dict[str, list[AbbreviationEntry]] = {}
        for abbrev in self.registry.all_entries():
            pattern_name = abbrev.pattern_type.value
            if pattern_name not in by_pattern:
                by_pattern[pattern_name] = []
            by_pattern[pattern_name].append(abbrev)

        for pattern_name in sorted(by_pattern.keys()):
            abbrevs = sorted(by_pattern[pattern_name], key=lambda x: x.abbreviation)

            lines.extend([
                f"## {pattern_name}",
                "",
                "| Abbreviation | Full Term | Section |",
                "|--------------|-----------|---------|",
            ])

            for a in abbrevs:
                section = a.section or "—"
                lines.append(f"| `{a.abbreviation}` | {a.full_term} | {section} |")

            lines.append("")

        return '\n'.join(lines)

    def generate_diff_report(
        self,
        old_registry: AbbreviationRegistry
    ) -> str:
        """
        Generate a diff report comparing current registry to a previous version.

        Args:
            old_registry: Previous version of the registry

        Returns:
            Markdown diff report
        """
        current_abbrevs = set(self.registry.all_abbreviations())
        old_abbrevs = set(old_registry.all_abbreviations())

        added = current_abbrevs - old_abbrevs
        removed = old_abbrevs - current_abbrevs

        # Check for changed definitions
        changed = []
        for abbrev in current_abbrevs & old_abbrevs:
            current_entry = self.registry.lookup(abbrev)
            old_entry = old_registry.lookup(abbrev)
            current_term = current_entry.full_term if current_entry else None
            old_term = old_entry.full_term if old_entry else None
            if current_term != old_term:
                changed.append((abbrev, old_term, current_term))

        lines = [
            "# SSOT Abbreviation Diff Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"- **Added:** {len(added)}",
            f"- **Removed:** {len(removed)}",
            f"- **Changed:** {len(changed)}",
            "",
            "---",
            "",
        ]

        if added:
            lines.extend([
                "## ➕ Added",
                "",
            ])
            for abbrev in sorted(added):
                entry = self.registry.lookup(abbrev)
                term = entry.full_term if entry else "?"
                lines.append(f"- `{abbrev}` = {term}")
            lines.append("")

        if removed:
            lines.extend([
                "## ➖ Removed",
                "",
            ])
            for abbrev in sorted(removed):
                entry = old_registry.lookup(abbrev)
                term = entry.full_term if entry else "?"
                lines.append(f"- `{abbrev}` = {term}")
            lines.append("")

        if changed:
            lines.extend([
                "## 🔄 Changed",
                "",
            ])
            for abbrev, old_term, new_term in changed:
                lines.append(f"- `{abbrev}`: {old_term} → {new_term}")
            lines.append("")

        return '\n'.join(lines)
