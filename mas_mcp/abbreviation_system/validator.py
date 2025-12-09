"""
Consistency Validator — Issue Detection Engine
==============================================

Analyzes the abbreviation registry and SSOT content to detect:
- Duplicate abbreviations with different meanings
- Orphaned abbreviations (defined but unused)
- Spelling variants (TRM-VRT vs TR-VRT)
- Semantic overloading (/ used for both OR and AND)
- Excessive length abbreviations (>6 chars)
- Missing definitions
- Pattern mismatches

Produces ConsistencyIssue objects that can be reported or auto-fixed.

Usage:
    validator = ConsistencyValidator(registry)
    issues = validator.validate_all(ssot_content)
"""

import re
from collections import defaultdict
from difflib import SequenceMatcher

from .models import (
    AbbreviationEntry,
    ConsistencyIssue,
    IssueCategory,
    IssueSeverity,
)
from .registry import AbbreviationRegistry


class ConsistencyValidator:
    """
    Detects consistency issues in the SSOT abbreviation system.

    Implements all 8 issue categories identified in the audit:
    1. Duplicate abbreviations
    2. Orphaned abbreviations
    3. Spelling variants
    4. Semantic overloading (/)
    5. Excessive length
    6. Missing definitions
    7. Missing notation guides
    8. Tier notation inconsistency
    """

    # Maximum recommended abbreviation length
    MAX_ABBREV_LENGTH = 6

    # Known spelling variants that should be unified
    KNOWN_VARIANTS = {
        ("TRM-VRT", "TR-VRT"): "TRM-VRT",  # Prefer longer, more readable
        ("SFS", "SIS-FRM-SCRAE"): "SFS",   # Prefer shorter
    }

    # Tier notation patterns
    TIER_PATTERNS = [
        (r"\bTier\s+(\d+(?:\.\d+)?)\b", "Tier X"),
        (r"\bT-(\d+(?:\.\d+)?)\b", "T-X"),
        (r"\bTier-(\d+(?:\.\d+)?)\b", "Tier-X"),
    ]

    def __init__(self, registry: AbbreviationRegistry):
        self.registry = registry
        self._issues: list[ConsistencyIssue] = []
        self._issue_counter = 0

    def validate_all(self, content: str) -> list[ConsistencyIssue]:
        """
        Run all validation checks on the SSOT content.

        Args:
            content: Full text of the SSOT markdown file

        Returns:
            List of detected ConsistencyIssue objects
        """
        self._issues = []
        self._issue_counter = 0

        # Run each validation check
        self._check_duplicates()
        self._check_spelling_variants()
        self._check_excessive_length()
        self._check_orphans(content)
        self._check_undefined_usages(content)
        self._check_semantic_overloading(content)
        self._check_tier_notation(content)
        self._check_notation_guides(content)
        self._check_redundant_compounds()

        return self._issues

    def _add_issue(
        self,
        severity: IssueSeverity,
        category: IssueCategory,
        description: str,
        affected: list[AbbreviationEntry] | None = None,
        lines: list[int] | None = None,
        recommendation: str = "",
        auto_fixable: bool = False,
    ) -> None:
        """Helper to create and store an issue."""
        self._issue_counter += 1
        issue = ConsistencyIssue(
            issue_id=f"ISSUE-{self._issue_counter:03d}",
            severity=severity,
            category=category,
            description=description,
            affected_entries=affected or [],
            line_numbers=lines or [],
            recommendation=recommendation,
            auto_fixable=auto_fixable,
        )
        self._issues.append(issue)

    def _check_duplicates(self) -> None:
        """Check for abbreviations with multiple different meanings."""
        duplicates = self.registry.find_duplicates()

        for abbrev, entries in duplicates.items():
            terms = [e.full_term for e in entries if e.full_term]
            self._add_issue(
                severity=IssueSeverity.CRITICAL,
                category=IssueCategory.DUPLICATE,
                description=f"Abbreviation '{abbrev}' has multiple meanings: {terms}",
                affected=entries,
                lines=[e.line_number for e in entries if e.line_number],
                recommendation="Disambiguate by using different abbreviations for each meaning",
            )

    def _check_spelling_variants(self) -> None:
        """Check for spelling variants of the same term."""
        all_abbrevs = self.registry.all_abbreviations()

        for (variant1, variant2), canonical in self.KNOWN_VARIANTS.items():
            if variant1 in all_abbrevs and variant2 in all_abbrevs:
                entry1 = self.registry.lookup(variant1)
                entry2 = self.registry.lookup(variant2)
                affected = [e for e in [entry1, entry2] if e]

                self._add_issue(
                    severity=IssueSeverity.WARNING,
                    category=IssueCategory.SPELLING_VARIANT,
                    description=f"Spelling variants detected: '{variant1}' vs '{variant2}'",
                    affected=affected,
                    recommendation=f"Standardize on '{canonical}'",
                    auto_fixable=True,
                )

        # Also check for similar abbreviations that might be variants
        self._check_fuzzy_variants(all_abbrevs)

    def _check_fuzzy_variants(self, abbrevs: list[str]) -> None:
        """Find potentially related abbreviations via fuzzy matching."""
        checked = set()

        for a1 in abbrevs:
            for a2 in abbrevs:
                if a1 >= a2:  # Avoid duplicate comparisons
                    continue
                pair = (a1, a2)
                if pair in checked:
                    continue
                checked.add(pair)

                # Calculate similarity
                similarity = SequenceMatcher(None, a1.lower(), a2.lower()).ratio()

                # Flag if very similar (>80%) but not identical
                if 0.8 < similarity < 1.0:
                    entry1 = self.registry.lookup(a1)
                    entry2 = self.registry.lookup(a2)

                    # Check if they might mean the same thing
                    if entry1 and entry2 and entry1.full_term and entry2.full_term:
                        term_similarity = SequenceMatcher(
                            None,
                            entry1.full_term.lower(),
                            entry2.full_term.lower()
                        ).ratio()

                        if term_similarity > 0.7:
                            self._add_issue(
                                severity=IssueSeverity.INFO,
                                category=IssueCategory.SPELLING_VARIANT,
                                description=f"Potentially related abbreviations: '{a1}' and '{a2}'",
                                affected=[e for e in [entry1, entry2] if e],
                                recommendation="Review if these should be unified",
                            )

    def _check_excessive_length(self) -> None:
        """Flag abbreviations that are too long."""
        for entry in self.registry.all_entries():
            abbrev = entry.abbreviation
            # Strip pattern artifacts
            clean_abbrev = abbrev.replace("`", "").replace("(", "").replace(")", "")

            if len(clean_abbrev) > self.MAX_ABBREV_LENGTH:
                self._add_issue(
                    severity=IssueSeverity.WARNING,
                    category=IssueCategory.EXCESSIVE_LENGTH,
                    description=f"Abbreviation '{abbrev}' is {len(clean_abbrev)} chars (max {self.MAX_ABBREV_LENGTH})",
                    affected=[entry],
                    lines=[entry.line_number] if entry.line_number else [],
                    recommendation=f"Shorten to ≤{self.MAX_ABBREV_LENGTH} chars or create alias",
                )

    def _check_orphans(self, content: str) -> None:
        """Find abbreviations that are defined but rarely/never used."""
        # Count all occurrences of each abbreviation
        usage_counts: dict[str, int] = defaultdict(int)

        for abbrev in self.registry.all_abbreviations():
            # Escape for regex
            escaped = re.escape(abbrev)
            # Count occurrences (whole word only)
            pattern = rf'\b{escaped}\b|`{escaped}`|\(\`{escaped}\`\)'
            matches = re.findall(pattern, content)
            usage_counts[abbrev] = len(matches)

        # Flag those with very low usage
        for abbrev, count in usage_counts.items():
            if count <= 1:
                entry = self.registry.lookup(abbrev)
                self._add_issue(
                    severity=IssueSeverity.INFO,
                    category=IssueCategory.ORPHAN,
                    description=f"Abbreviation '{abbrev}' appears only {count} time(s)",
                    affected=[entry] if entry else [],
                    recommendation="Consider removing if truly unused, or add more references",
                )

    def _check_undefined_usages(self, content: str) -> None:
        """Find abbreviations used but not formally defined."""
        # Look for backtick abbreviations in content
        pattern = r'`([A-Z][A-Z0-9-]{1,10})`'
        matches = re.findall(pattern, content)

        undefined = set()
        for match in matches:
            if not self.registry.lookup(match):
                undefined.add(match)

        for abbrev in undefined:
            # Find line numbers where it appears
            lines = []
            for i, line in enumerate(content.split("\n"), 1):
                if f"`{abbrev}`" in line:
                    lines.append(i)
                    if len(lines) >= 3:  # Cap at 3 examples
                        break

            self._add_issue(
                severity=IssueSeverity.WARNING,
                category=IssueCategory.MISSING_DEFINITION,
                description=f"Abbreviation '{abbrev}' is used but not defined in registry",
                lines=lines,
                recommendation="Add formal definition or register in known definitions",
            )

    def _check_semantic_overloading(self, content: str) -> None:
        """
        Check for slash (/) being used for both OR and AND semantics.

        OR usage: (`A`/`B`) meaning "A or B, they're alternatives"
        AND usage: (`A`/`B`) meaning "A combined with B"
        """
        # Find all slash-separated patterns
        pattern = r'\(\`([^`]+)\`/\`([^`]+)\`(?:/\`([^`]+)\`)?\)'
        matches = list(re.finditer(pattern, content))

        if len(matches) > 5:  # Arbitrary threshold for "overuse"
            self._add_issue(
                severity=IssueSeverity.WARNING,
                category=IssueCategory.SEMANTIC_OVERLOAD,
                description=f"Slash (/) operator used {len(matches)} times with potentially mixed semantics",
                recommendation="Use / for alternatives only; use + or × for compounds",
            )

    def _check_tier_notation(self, content: str) -> None:
        """Check for inconsistent tier notation (Tier X vs T-X vs Tier-X)."""
        tier_usages: dict[str, list[int]] = defaultdict(list)

        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            for pattern, pattern_name in self.TIER_PATTERNS:
                if re.search(pattern, line):
                    tier_usages[pattern_name].append(i)

        # If multiple patterns used, flag inconsistency
        used_patterns = [p for p, lines in tier_usages.items() if lines]
        if len(used_patterns) > 1:
            self._add_issue(
                severity=IssueSeverity.WARNING,
                category=IssueCategory.PATTERN_MISMATCH,
                description=f"Mixed tier notation styles: {used_patterns}",
                recommendation="Standardize on 'Tier X' (readable) or 'T-X' (compact), not both",
            )

    def _check_notation_guides(self, content: str) -> None:
        """Check which sections have notation guides."""
        # Find section headers
        section_pattern = r'^###?\s+\*\*([IVXLC]+(?:\.[0-9.]+)?)\.'
        guide_pattern = r'NOTATION GUIDE'

        lines = content.split("\n")
        sections_found = []
        sections_with_guides = []

        current_section = None
        for _i, line in enumerate(lines, 1):
            # Check for section header
            match = re.search(section_pattern, line)
            if match:
                current_section = match.group(1)
                sections_found.append(current_section)

            # Check for notation guide
            if guide_pattern in line.upper() and current_section:
                sections_with_guides.append(current_section)

        # Find sections missing guides
        missing = set(sections_found) - set(sections_with_guides)

        # Only care about major sections (I, II, III, etc., not subsections)
        major_missing = [s for s in missing if "." not in s]

        if major_missing:
            self._add_issue(
                severity=IssueSeverity.INFO,
                category=IssueCategory.MISSING_DEFINITION,
                description=f"Sections missing NOTATION GUIDE: {major_missing}",
                recommendation="Add NOTATION GUIDE subsection to each major section",
            )

    def _check_redundant_compounds(self) -> None:
        """Check for redundant compound abbreviations (TPEF-APT when TPEF exists)."""
        all_abbrevs = self.registry.all_abbreviations()

        for abbrev in all_abbrevs:
            if "-" in abbrev:
                # Check if base form exists
                parts = abbrev.split("-")
                if len(parts) >= 2:
                    base = parts[0]
                    if base in all_abbrevs and len(abbrev) > len(base) + 4:
                        entry = self.registry.lookup(abbrev)
                        base_entry = self.registry.lookup(base)

                        # Check if they're related
                        if entry and base_entry:
                            if entry.full_term and base_entry.full_term:
                                if base_entry.full_term in entry.full_term:
                                    self._add_issue(
                                        severity=IssueSeverity.INFO,
                                        category=IssueCategory.DUPLICATE,
                                        description=f"Redundant compound: '{abbrev}' extends '{base}'",
                                        affected=[entry, base_entry],
                                        recommendation=f"Use '{base}' alone; compound is documentation",
                                    )

    def get_issues_by_severity(self, severity: IssueSeverity) -> list[ConsistencyIssue]:
        """Get all issues of a specific severity."""
        return [i for i in self._issues if i.severity == severity]

    def get_issues_by_category(self, category: IssueCategory) -> list[ConsistencyIssue]:
        """Get all issues of a specific category."""
        return [i for i in self._issues if i.category == category]

    def summary(self) -> dict:
        """Get a summary of validation results."""
        return {
            "total_issues": len(self._issues),
            "critical": len(self.get_issues_by_severity(IssueSeverity.CRITICAL)),
            "warnings": len(self.get_issues_by_severity(IssueSeverity.WARNING)),
            "info": len(self.get_issues_by_severity(IssueSeverity.INFO)),
            "auto_fixable": sum(1 for i in self._issues if i.auto_fixable),
            "by_category": {
                cat.value: len(self.get_issues_by_category(cat))
                for cat in IssueCategory
            },
        }
