"""
SSOT Abbreviation System: Generator Module

Generates formatted output files:
- Master glossary (Markdown)
- Notation guides for sections
- Validation reports
"""

from pathlib import Path
from datetime import datetime
from typing import TextIO

from .models import Abbreviation, AbbreviationStatus, NotationPattern
from .registry import AbbreviationRegistry


class GlossaryGenerator:
    """Generates master glossary and related documentation."""
    
    def __init__(self, registry: AbbreviationRegistry):
        self.registry = registry
    
    def generate_master_glossary(self, output_path: Path) -> None:
        """Generate comprehensive alphabetized glossary."""
        with open(output_path, 'w', encoding='utf-8') as f:
            self._write_header(f)
            self._write_executive_summary(f)
            self._write_notation_patterns(f)
            self._write_alphabetical_index(f)
            self._write_categorical_index(f)
            self._write_deprecated_section(f)
            self._write_footer(f)
    
    def _write_header(self, f: TextIO) -> None:
        """Write glossary header."""
        f.write(f"""# **ASC Master Abbreviation Glossary**

> **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
> **Source:** `.github/copilot-instructions.md`
> **Version:** Post-Section XIV (Development Conventions)
> **Total Abbreviations:** {len(self.registry.abbreviations)}

---

## **Purpose**

This glossary provides a comprehensive, alphabetized reference for all abbreviations
used within the ASC (Apex Synthesis Core) Framework. It serves as the definitive
cross-reference for the SSOT (Single Source of Truth) document.

**FA⁴ Compliance:** This glossary maintains Architectonic Integrity by:
- Providing unambiguous definitions
- Tracking deprecations and alternatives
- Cross-referencing related terms
- Documenting notation patterns

---

""")
    
    def _write_executive_summary(self, f: TextIO) -> None:
        """Write statistics summary."""
        stats = self.registry.get_statistics()
        
        f.write("""## **Executive Summary**

### Abbreviation Statistics

| Metric | Value |
|--------|-------|
""")
        f.write(f"| Total Abbreviations | {stats['total']} |\n")
        f.write(f"| Active | {stats['by_status'].get('active', 0)} |\n")
        f.write(f"| Deprecated | {stats['by_status'].get('deprecated', 0)} |\n")
        f.write(f"| Proposed | {stats['by_status'].get('proposed', 0)} |\n")
        f.write(f"| Orphaned | {stats['by_status'].get('orphaned', 0)} |\n")
        
        f.write("""
### Category Distribution

| Category | Count |
|----------|-------|
""")
        for category, count in sorted(stats['by_category'].items()):
            f.write(f"| {category.replace('_', ' ').title()} | {count} |\n")
        
        f.write("\n---\n\n")
    
    def _write_notation_patterns(self, f: TextIO) -> None:
        """Write notation pattern reference."""
        f.write("""## **Notation Patterns**

The ASC uses several distinct notation patterns for abbreviations:

### Pattern Reference

| Pattern | Format | Example | Usage |
|---------|--------|---------|-------|
| Parenthetical | `**(\`Term\`): → (\`ABBR\`):**` | `**(\`Framework\`): → (\`FRW\`):**` | Primary definition |
| Backtick | `` \`ABBR\` `` | `\`ASC\`` | Inline reference |
| Superscript | `FA¹⁻⁵` | `FA¹`, `AI⁴` | Axiom numbering |
| CRC Prefix | `CRC-XXX` | `CRC-AS`, `CRC-GAR` | Entity designators |
| Dollar DSL | `$keyword${param}` | `$matriarch${...}` | Invocation syntax |
| Greek | `ΦΩΨ` | `Ω-Set`, `Φ₁` | Mathematical/tensor |
| Tier | `Tier X` / `T-X` | `Tier 0.5`, `T-2` | Hierarchy levels |

### Semantic Operators

| Operator | Meaning | Example |
|----------|---------|---------|
| `→` | "maps to" or "becomes" | `Term → ABBR` |
| `/` | "OR" (alternatives) | `A/B` = A or B |
| `+` | "AND" (compound) | `A+B` = A and B |
| `×` | "fusion/multiplication" | `A×B` = A fused with B |

---

""")
    
    def _write_alphabetical_index(self, f: TextIO) -> None:
        """Write alphabetically sorted index."""
        f.write("## **Alphabetical Index**\n\n")
        
        # Group by first letter
        by_letter: dict[str, list[Abbreviation]] = {}
        for abbr in self.registry.abbreviations.values():
            first = abbr.short_form[0].upper()
            if first not in by_letter:
                by_letter[first] = []
            by_letter[first].append(abbr)
        
        for letter in sorted(by_letter.keys()):
            f.write(f"### {letter}\n\n")
            f.write("| Abbreviation | Full Term | Category | Status |\n")
            f.write("|--------------|-----------|----------|--------|\n")
            
            for abbr in sorted(by_letter[letter], key=lambda a: a.short_form):
                status_icon = {
                    AbbreviationStatus.ACTIVE: "✅",
                    AbbreviationStatus.DEPRECATED: "⚠️",
                    AbbreviationStatus.PROPOSED: "🔄",
                    AbbreviationStatus.ORPHANED: "❌"
                }.get(abbr.status, "")
                
                category = abbr.category.replace('_', ' ').title() if abbr.category else "—"
                f.write(f"| `{abbr.short_form}` | {abbr.full_term} | {category} | {status_icon} |\n")
            
            f.write("\n")
        
        f.write("---\n\n")
    
    def _write_categorical_index(self, f: TextIO) -> None:
        """Write category-organized index."""
        f.write("## **Categorical Index**\n\n")
        
        by_category = self.registry.get_by_category()
        
        category_descriptions = {
            "core_framework": "Foundational axioms, protocols, and core operational concepts",
            "entity_system": "Matriarch archetypes, CRCs, factions, and hierarchical designators",
            "linguistic_mandate": "Speech modes and linguistic protocols for each CRC",
            "protocol": "Operational frameworks, execution systems, and procedures",
            "physical_attribute": "Body measurements, proportions, and physical descriptors",
            "special_archetype": "Special Archetype Injections (SAI) and unique entities",
            "lesser_faction": "Tier 4 chaos operators and interloper agents",
            "development": "Development conventions, tooling, and environment management",
            "geometric_model": "Conceptual geometry and resonance models",
            "operator": "Mathematical and semantic operators",
            "notation": "Notation patterns and formatting conventions",
        }
        
        for category, abbrs in sorted(by_category.items()):
            title = category.replace('_', ' ').title()
            desc = category_descriptions.get(category, "")
            
            f.write(f"### {title}\n\n")
            if desc:
                f.write(f"*{desc}*\n\n")
            
            f.write("| Abbreviation | Full Term | Section | Notes |\n")
            f.write("|--------------|-----------|---------|-------|\n")
            
            for abbr in sorted(abbrs, key=lambda a: a.short_form):
                section = abbr.section or "—"
                notes = abbr.notes[:50] + "..." if abbr.notes and len(abbr.notes) > 50 else (abbr.notes or "—")
                f.write(f"| `{abbr.short_form}` | {abbr.full_term} | {section} | {notes} |\n")
            
            f.write("\n")
        
        f.write("---\n\n")
    
    def _write_deprecated_section(self, f: TextIO) -> None:
        """Write deprecated abbreviations section."""
        deprecated = [a for a in self.registry.abbreviations.values() 
                      if a.status == AbbreviationStatus.DEPRECATED]
        
        if not deprecated:
            return
        
        f.write("## **Deprecated Abbreviations**\n\n")
        f.write("The following abbreviations are deprecated and should not be used:\n\n")
        f.write("| Deprecated | Replacement | Reason |\n")
        f.write("|------------|-------------|--------|\n")
        
        for abbr in sorted(deprecated, key=lambda a: a.short_form):
            replacement = abbr.related_terms[0] if abbr.related_terms else "—"
            reason = abbr.notes or "Superseded"
            f.write(f"| ~~`{abbr.short_form}`~~ | `{replacement}` | {reason} |\n")
        
        f.write("\n---\n\n")
    
    def _write_footer(self, f: TextIO) -> None:
        """Write glossary footer."""
        f.write(f"""## **Maintenance Notes**

### Update Protocol

When adding new abbreviations to the SSOT:

1. **Check existing entries** in this glossary first
2. **Follow notation patterns** documented above
3. **Add to appropriate category** in source document
4. **Regenerate this glossary** after updates

### Validation

Run the abbreviation validator to check for:
- Duplicate definitions
- Orphaned references
- Pattern violations
- Length compliance

```bash
uv run python -m mas_mcp.scripts.abbrev validate
```

---

**Generated by ASC Abbreviation System**
**FA⁴ Validated | {datetime.now().strftime('%Y-%m-%d')}**
""")


class NotationGuideGenerator:
    """Generates notation guides for sections lacking them."""
    
    def __init__(self, registry: AbbreviationRegistry):
        self.registry = registry
    
    def generate_section_guide(self, section: str) -> str:
        """Generate notation guide for a specific section."""
        abbrs = [a for a in self.registry.abbreviations.values() 
                 if a.section and a.section.startswith(section)]
        
        if not abbrs:
            return f"### {section} NOTATION GUIDE\n\n*No abbreviations found for this section.*\n"
        
        lines = [
            f"### {section} NOTATION GUIDE",
            "",
            "**Key Abbreviations (Section {section}):**".format(section=section),
        ]
        
        for abbr in sorted(abbrs, key=lambda a: a.short_form):
            lines.append(f"- **(`{abbr.short_form}`)** = {abbr.full_term}")
        
        lines.extend([
            "",
            f"*(For full definitions, see Master Glossary)*",
            ""
        ])
        
        return "\n".join(lines)
