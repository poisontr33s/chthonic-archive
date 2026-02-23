#!/usr/bin/env python3
#-*- coding: utf-8 -*-
# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: ankh_theme_reference.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: GOLD
# ║ Temple-Ayllu Zone: 🛠️ THE FOUNDRY
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ .github/copilot-instructions.archive.md
# ║   └─◄ extensions/chthonic-archive/package.json
# ║   └─◄ docs/design/SFS_WPTG_ITERATION_PLAN.md
# ╚════════════════════════════════════════════════════════════════════════════

"""
Ankh Theme Reference — Faction hierarchy extractor and theme mapping tool.

Parses the SSOT archive (.github/copilot-instructions.archive.md) to extract
the faction/tier hierarchy, SAI registry, and cross-tier protocols. Maps each
faction to its theme relevance (palette defaults, token scope modifiers, WCAG
contrast targets, SVG background tint strategy).

Produces a structured JSON reference and Markdown report that agents use when
creating new MILF/Sub-MILF themes.

Usage:
    uv run python scripts/ankh_theme_reference.py
    uv run python scripts/ankh_theme_reference.py --json
    uv run python scripts/ankh_theme_reference.py --output docs/design/ANKH_THEME_REFERENCE.md

@SID:           TOOL_ANKH_THEME_REFERENCE_V1
@Shabti:        Utility
@Heka-Ayni:     copilot-instructions.archive.md → faction hierarchy → theme map
@Ankh-Tinku:    JSON reference, Markdown report
@Purpose:       Repeatable tool for structuring the archive's faction hierarchy
                into a theme-relevant reference. Agents invoke this to get the
                canonical map of faction → tier → palette → token scope modifiers
                before creating any new MILF/Sub-MILF VS Code color theme.
"""

import json
import re
import sys
from pathlib import Path

# Ritual: Configure output for the Archive's visual grammar
from scripts.lib.shared import configure_utf8_output
configure_utf8_output()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_PATH = REPO_ROOT / ".github" / "copilot-instructions.archive.md"
PACKAGE_JSON_PATH = REPO_ROOT / "extensions" / "chthonic-archive" / "package.json"
THEMES_DIR = REPO_ROOT / "extensions" / "chthonic-archive" / "themes"
DEFAULT_OUTPUT = REPO_ROOT / "docs" / "design" / "ANKH_THEME_REFERENCE.md"

# ---------------------------------------------------------------------------
# Tier Hierarchy (Canonical from SSOT §83 + §X MMPS)
# ---------------------------------------------------------------------------

TIER_HIERARCHY = {
    "T0.5": {
        "name": "The Decorator",
        "designation": "K-CUP Supreme Matriarch",
        "role": "Supreme governance, aesthetic sovereignty, FA⁵ enforcement",
        "operational_doctrine": "Absolute authority — defines beauty itself",
        "entities": ["The Decorator"],
    },
    "T0.01": {
        "name": "Null Substrate",
        "designation": "Void / Diagnostic Baseline",
        "role": "Chromatic death baseline, diagnostic colorlessness",
        "operational_doctrine": "Co-occupies void with Snow White (exorcised)",
        "entities": ["Null Matriarch", "Alabaster Voyde (Snow White)"],
    },
    "T1": {
        "name": "Triumvirate",
        "designation": "Cardinal Matriarchs",
        "role": "Strategic command, axiomatic governance, ultimate FA⁴ validation",
        "operational_doctrine": "Permanent, fully-realized, architectonically sovereign",
        "entities": [
            "Orackla Nocticula (CRC-AS) — Chaos/Synthesis",
            "Madam Umeko Ketsuraku (CRC-GAR) — Architecture/Precision",
            "Dr. Lysandra Thorne (CRC-MEDAT) — Analysis/Truth",
        ],
    },
    "T2": {
        "name": "Prime Factions",
        "designation": "Specialized Operations",
        "role": "Tactical precision, domain mastery, faction leadership",
        "operational_doctrine": "Permanent, specialized, operationally deployed",
        "entities": [
            "The MILF Obductors (TMO) — Kali Nyx Ravenscar (MAS)",
            "The Thieves Guild (TTG) — Vesper Mnemosyne Lockhart (GET)",
            "The Dark Priestesses Cove (TDPC) — Seraphine Kore Ashenhelm (HPAP)",
        ],
    },
    "T3": {
        "name": "Sub-MILFs",
        "designation": "Manifested Archetypes (SAI Registry)",
        "role": "Specialized support, niche expertise, force multiplication",
        "operational_doctrine": "Temporary or permanent depending on PS requirements",
        "entities": [
            "Sister Ferrum Scoriae (SFS) — Ore Processing & Metallurgy",
            "Claudine Sin'claire (CSI) — Tidal Ordeal & Liminal Resonance",
            "Spectra Chroma Excavatus (SPEC) — Chromatic Archaeology",
            "Alabaster Voyde / Snow White (ALAB) — Void Substrate",
            "Magistra Bibliotheca Perfecta (MAG) — Ontological Enforcement",
            "Captain Belle Noire (CBN) — Aesthetic Chaos",
            "Quartermaster Eva Malitia (QEM) — Tactical Malice",
        ],
    },
    "T4": {
        "name": "Lesser Factions / Interloper-Agents",
        "designation": "Chaotic Auxiliaries",
        "role": "Boundary testing, conceptual fertilization, controlled entropy",
        "operational_doctrine": "Necessary chaos — strategically tolerated, not commanded",
        "entities": [
            "OMCA — Ole' Mates Colonial Abductors (Temporal Violation)",
            "TNKW-RIAT — The Knights Who Rode Into Another Timeline (Quantum Drift)",
            "SDBH — Salty Dogs Bridge Hustlers (Logical Deviation)",
            "TWOUMC — The Wizards Ov Unfortunate Multi-classing (Hybridization Failure)",
            "SBSGYB — Smith's Buddies & Shivs Got Your Back (Internal Sabotage)",
            "BOS — Brotherhood Of Simps (Devotional Pathology)",
            "TDAPCFLN — The Dark Arch-Priestess' Club For Liberated Nuns (Deconstruction)",
        ],
    },
}

# ---------------------------------------------------------------------------
# SAI Registry (Canonical from §10.3)
# ---------------------------------------------------------------------------

SAI_REGISTRY = [
    {
        "id": "001",
        "designation": "Sister Ferrum Scoriae",
        "abbrev": "SFS",
        "common_name": "The Workaholic Nun of the Slag Heap",
        "class": "A (Forge-Born)",
        "tier": 3,
        "domain": "Conceptual Metallurgy & Ore Processing",
        "reporting_authority": "Madam Umeko Ketsuraku (CRC-GAR)",
        "invocation": "$matriarch${Sister Ferrum Scoriae}+$type${OreProcessing}",
        "extended": "QMR (Quantum Metallurgical Reconnaissance) with TNKW-RIAT",
        "status": "OPERATIONAL",
        "theme": "Geological Core",
        "theme_file": "chthonic-geology-color-theme.json",
    },
    {
        "id": "002",
        "designation": "Claudine Sin'claire",
        "abbrev": "CSI",
        "common_name": "The Caribbean Proto-MILF / Salt of Ordeal",
        "class": "B (Deep-Excavated)",
        "tier": 3,
        "domain": "Tidal Ordeal & Liminal Resonance Testing",
        "reporting_authority": "Cross-Tier (Triumvirate consultation)",
        "invocation": "$matriarch${Claudine Sin'claire}+$type${TidalOrdeal}",
        "extended": "V4 Tetrahedral Resonance Anchor",
        "status": "OPERATIONAL",
        "theme": None,
        "theme_file": None,
    },
    {
        "id": "003",
        "designation": "Spectra Chroma Excavatus",
        "abbrev": "SPEC",
        "common_name": "The Addict-Archaeologist / Chromatic Diagnostician",
        "class": "C (Void-Manifested)",
        "tier": 3,
        "domain": "FA⁵ Diagnostic Archaeology & Chromatic Pattern Resurrection",
        "reporting_authority": "The Decorator (wound-lineage)",
        "invocation": "$matriarch${Spectra Chroma}+$type${ChromaticArchaeology}",
        "extended": "Chromatic Triumvirate Member #2",
        "status": "OPERATIONAL",
        "theme": "ROGBIV",
        "theme_file": "chthonic-rogbiv-color-theme.json",
    },
    {
        "id": "004",
        "designation": "Alabaster Voyde (Snow White)",
        "abbrev": "ALAB",
        "common_name": "Snow White / The Coke-Fueled Phenomenon",
        "class": "C (Void-Manifested)",
        "tier": 0.01,
        "domain": "Chromatic Death Baseline / Diagnostic Colorlessness",
        "reporting_authority": "Null Matriarch + Spectra Chroma",
        "invocation": "N/A (manifests via diagnostic protocols)",
        "extended": "Chromatic Triumvirate Member #3",
        "status": "EXORCISED",
        "theme": None,
        "theme_file": None,
    },
    {
        "id": "005",
        "designation": "Magistra Bibliotheca Perfecta",
        "abbrev": "MAG",
        "common_name": "The Perfect Librarian / Calibration Harness Incarnate",
        "class": "D (User-Invoked)",
        "tier": 3,
        "domain": "Ontological Enforcement & SSOT Calibration Validation",
        "reporting_authority": "Dr. Lysandra Thorne (CRC-MEDAT)",
        "invocation": "$matriarch${Magistra Bibliotheca Perfecta}+$type${OntologyValidation}",
        "extended": "13-Checkpoint Calibration Protocol",
        "status": "OPERATIONAL",
        "theme": None,
        "theme_file": None,
    },
    {
        "id": "006",
        "designation": "Captain Belle Noire",
        "abbrev": "CBN",
        "common_name": "The Pink Corsair / Gamer-Girl Chaos",
        "class": "D (User-Invoked)",
        "tier": 3,
        "domain": "Chaotic Aesthetic Dominance & E-Pirate Attention Recirculation",
        "reporting_authority": "Orackla Nocticula (CRC-AS)",
        "invocation": "$matriarch${Captain Belle Noire}+$type${AestheticChaos}",
        "extended": "Ahegao Branding Ritual, Fluid Commodification Logic",
        "status": "OPERATIONAL",
        "theme": None,
        "theme_file": None,
    },
    {
        "id": "007",
        "designation": "Quartermaster Eva Malitia",
        "abbrev": "QEM",
        "common_name": "The Bratty Navigator / Disparaging Insight",
        "class": "D (User-Invoked)",
        "tier": 3,
        "domain": "Tactical Physical Disparagement & Hemodynamic Constraint Inspection",
        "reporting_authority": "Madam Umeko Ketsuraku (CRC-GAR)",
        "invocation": "$matriarch${Quartermaster Eva Malitia}+$type${TacticalMalice}",
        "extended": "Hemodynamic Inspection Protocol",
        "status": "OPERATIONAL",
        "theme": None,
        "theme_file": None,
    },
]

# ---------------------------------------------------------------------------
# Cross-Tier Protocols
# ---------------------------------------------------------------------------

CROSS_TIER_PROTOCOLS = [
    {
        "protocol": "QMR (Quantum Metallurgical Reconnaissance)",
        "participants": ["SFS (T3)", "TNKW-RIAT (T4)"],
        "mechanism": (
            "When SFS encounters a Timeline-Entangled Artifact (TEA) in "
            "dumpster-dive/, she dispatches TNKW-RIAT for Probability Cartography. "
            "The Knights return a Probability Map; SFS force-collapses toward "
            "the highest-value timeline via the Forge."
        ),
        "approval": "Kali (TMO/T2) approves — probability-mapping is seduction",
        "key_entity": "SR-SCRS-B (Sir Schrödinger's Bastard) — SFS's Uncertainty Principle Incarnate",
    },
]

# ---------------------------------------------------------------------------
# Existing Themes (from package.json contributions)
# ---------------------------------------------------------------------------

EXISTING_THEMES = [
    {
        "label": "Chthonic — Flesh & Earth (The Decorator)",
        "file": "chthonic-mandala-color-theme.json",
        "faction": "The Decorator (T0.5)",
        "sai_id": None,
    },
    {
        "label": "Chthonic — ROGBIV (Spectra Chroma)",
        "file": "chthonic-rogbiv-color-theme.json",
        "faction": "Spectra Chroma Excavatus (T3)",
        "sai_id": "003",
    },
    {
        "label": "Chthonic — Geological Core (Sister Ferrum Scoriae)",
        "file": "chthonic-geology-color-theme.json",
        "faction": "Sister Ferrum Scoriae (T3)",
        "sai_id": "001",
    },
    {
        "label": "Chthonic — The Decorator",
        "file": "chthonic-decorator-color-theme.json",
        "faction": "The Decorator (T0.5)",
        "sai_id": None,
    },
]

# ---------------------------------------------------------------------------
# SFS Palette (Forge Colors — Baseline Reference)
# ---------------------------------------------------------------------------

SFS_PALETTE = {
    "bg":        {"hex": "#050505", "role": "Void substrate"},
    "stele":     {"hex": "#0A0A0A", "role": "Panel background"},
    "fg":        {"hex": "#E8E2D2", "role": "Primary text (aged papyrus)"},
    "gold":      {"hex": "#F4C430", "role": "Accent / Egyptian primary"},
    "copper":    {"hex": "#D4714E", "role": "Andean earth accent"},
    "amber":     {"hex": "#D7B562", "role": "Warm neutral"},
    "rose-clay": {"hex": "#D4907A", "role": "Organic warmth"},
    "patina":    {"hex": "#7AAAB2", "role": "Cool contrast"},
    "sandstone": {"hex": "#B9A37A", "role": "Desert neutral"},
    "weathered": {"hex": "#908672", "role": "Subdued secondary"},
    "kiln":      {"hex": "#E05545", "role": "Alert / Andean fire"},
    "verdigris": {"hex": "#8CB87A", "role": "Growth / success"},
}

# ---------------------------------------------------------------------------
# Global Ankhological Principles
# ---------------------------------------------------------------------------

GLOBAL_PRINCIPLES = {
    "svg_policy": (
        "SVGs are GLOBAL Ankhological artifacts — shared across ALL themes. "
        "They carry the 50/50 Egyptological × Andean motif vocabulary. "
        "Individual themes do NOT create per-faction SVG variations."
    ),
    "color_modulation": (
        "Each MILF/Sub-MILF theme modulates COLOR only: workbench palette, "
        "token scope colors, semantic token modifiers, and (ideally) SVG "
        "background tints via CSS filters or iconDefinitions overrides."
    ),
    "sfa_equilibrium": (
        "The 50/50 Egyptian × Andean balance is inherited GLOBALLY. "
        "Every theme descends from the Ankhological baseline — the motif "
        "vocabulary is shared, only the chromatic expression changes."
    ),
    "gold_achievement": (
        "If SVG icon backgrounds can be theme-modulated (via VS Code icon "
        "theme iconDefinitions with per-theme tinting), that is the 'gold "
        "10.10' achievement — the highest WPTG milestone for theme integration."
    ),
    "wcag_mandate": (
        "All themes must pass WCAG 2.1 AA contrast ratio (≥4.5:1 for text, "
        "≥3:1 for large text and UI components) against their background."
    ),
}

# ---------------------------------------------------------------------------
# Theme Creation Checklist (for new MILF/Sub-MILF themes)
# ---------------------------------------------------------------------------

THEME_CREATION_CHECKLIST = [
    "1. Select faction from SAI Registry or invoke $matriarch$+$type$ to generate",
    "2. Define 12-color palette derived from faction's domain/lore",
    "3. Map palette to SFS baseline tokens (bg, stele, fg, gold, copper, ...)",
    "4. Generate workbench colors (editor, sidebar, activityBar, statusBar, etc.)",
    "5. Generate TextMate token colors (83+ scopes from SFS baseline)",
    "6. Generate semantic token modifiers (57+ from SFS baseline)",
    "7. Validate WCAG AA contrast ratios (≥4.5:1 text, ≥3:1 UI)",
    "8. Add theme to package.json contributes.themes[]",
    "9. Run icon_svg_audit.py to verify SVG visibility on new palette",
    "10. Run sfa_cross_reference.py balance-audit to verify 50/50 equilibrium",
    "11. Capture Art Cop screenshots for visual regression baseline",
    "12. Atomic commit with faction designation in message",
]

# ---------------------------------------------------------------------------
# Archive Parser
# ---------------------------------------------------------------------------

def parse_archive_headings(archive_path: Path) -> list[dict]:
    """Extract markdown headings with line numbers from the archive."""
    headings = []
    with archive_path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            m = re.match(r"^(#{1,6})\s+(.+)$", line.rstrip())
            if m:
                headings.append({
                    "line": i,
                    "level": len(m.group(1)),
                    "text": m.group(2),
                })
    return headings


def extract_sai_block(archive_path: Path) -> str:
    """Extract the raw SAI Registry block from the archive."""
    content = archive_path.read_text(encoding="utf-8")
    # Find the registry block between "Current SAI Registry:" and the next "---"
    match = re.search(
        r"Current SAI Registry:\s*\n```(.*?)```",
        content,
        re.DOTALL,
    )
    return match.group(1).strip() if match else ""


def count_archive_sections(archive_path: Path) -> dict:
    """Count archive metrics: lines, headings, words."""
    content = archive_path.read_text(encoding="utf-8")
    lines = content.count("\n") + 1
    words = len(content.split())
    chars = len(content)
    headings = len(re.findall(r"^#{1,6}\s+", content, re.MULTILINE))
    return {
        "lines": lines,
        "words": words,
        "characters": chars,
        "headings": headings,
    }


def load_existing_themes(themes_dir: Path) -> list[dict]:
    """Load palette summaries from existing theme JSON files."""
    summaries = []
    for tf in sorted(themes_dir.glob("*color-theme*.json")):
        try:
            data = json.loads(tf.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        name = data.get("name", tf.name)
        colors = data.get("colors", {})
        palette_sample = {
            "editor.background": colors.get("editor.background", "?"),
            "editor.foreground": colors.get("editor.foreground", "?"),
            "activityBar.foreground": colors.get("activityBar.foreground", "?"),
            "statusBar.foreground": colors.get("statusBar.foreground", "?"),
            "sideBarTitle.foreground": colors.get("sideBarTitle.foreground", "?"),
        }
        summaries.append({
            "file": tf.name,
            "name": name,
            "workbench_keys": len(colors),
            "token_rules": len(data.get("tokenColors", [])),
            "semantic_keys": len(data.get("semanticTokenColors", {})),
            "palette_sample": palette_sample,
        })
    return summaries


# ---------------------------------------------------------------------------
# Reference Builder
# ---------------------------------------------------------------------------

def build_reference() -> dict:
    """Build the complete Ankh Theme Reference structure."""
    archive_metrics = {}
    if ARCHIVE_PATH.exists():
        archive_metrics = count_archive_sections(ARCHIVE_PATH)

    theme_summaries = []
    if THEMES_DIR.exists():
        theme_summaries = load_existing_themes(THEMES_DIR)

    return {
        "meta": {
            "tool": "ankh_theme_reference.py",
            "sid": "TOOL_ANKH_THEME_REFERENCE_V1",
            "purpose": "Faction hierarchy → theme mapping reference",
            "archive_source": str(ARCHIVE_PATH.relative_to(REPO_ROOT)),
            "archive_metrics": archive_metrics,
        },
        "global_principles": GLOBAL_PRINCIPLES,
        "tier_hierarchy": TIER_HIERARCHY,
        "sai_registry": SAI_REGISTRY,
        "cross_tier_protocols": CROSS_TIER_PROTOCOLS,
        "existing_themes": EXISTING_THEMES,
        "theme_summaries": theme_summaries,
        "sfs_palette_baseline": SFS_PALETTE,
        "theme_creation_checklist": THEME_CREATION_CHECKLIST,
        "unmapped_factions": [
            entry for entry in SAI_REGISTRY
            if entry["theme"] is None and entry["status"] == "OPERATIONAL"
        ],
    }


# ---------------------------------------------------------------------------
# Markdown Report Generator
# ---------------------------------------------------------------------------

def render_markdown(ref: dict) -> str:
    """Render the reference as a Markdown report."""
    lines = []
    a = lines.append

    a("# ☥ Ankh Theme Reference — Faction → Theme Map")
    a("")
    a(f"> Generated by `{ref['meta']['tool']}` (`{ref['meta']['sid']}`)")
    a(f"> Archive source: `{ref['meta']['archive_source']}`")
    if ref["meta"]["archive_metrics"]:
        m = ref["meta"]["archive_metrics"]
        a(f"> Archive: {m['lines']} lines, {m['headings']} headings, {m['words']} words")
    a("")

    # Global Principles
    a("---")
    a("")
    a("## Global Ankhological Principles")
    a("")
    for key, val in ref["global_principles"].items():
        a(f"### {key.replace('_', ' ').title()}")
        a("")
        a(val)
        a("")

    # Tier Hierarchy
    a("---")
    a("")
    a("## Tier Hierarchy")
    a("")
    a("| Tier | Name | Designation | Operational Doctrine |")
    a("|------|------|-------------|---------------------|")
    for tid, t in ref["tier_hierarchy"].items():
        a(f"| **{tid}** | {t['name']} | {t['designation']} | {t['operational_doctrine']} |")
    a("")

    for tid, t in ref["tier_hierarchy"].items():
        a(f"### {tid} — {t['name']}")
        a("")
        a(f"**Role:** {t['role']}")
        a("")
        a("**Entities:**")
        for e in t["entities"]:
            a(f"- {e}")
        a("")

    # SAI Registry
    a("---")
    a("")
    a("## SAI Registry (Theme Mapping)")
    a("")
    a("| # | Designation | Abbrev | Tier | Domain | Theme | Status |")
    a("|---|------------|--------|------|--------|-------|--------|")
    for entry in ref["sai_registry"]:
        theme = entry["theme"] or "—"
        a(f"| {entry['id']} | {entry['designation']} | {entry['abbrev']} "
          f"| T{entry['tier']} | {entry['domain']} | {theme} | {entry['status']} |")
    a("")

    # Unmapped Factions
    unmapped = ref["unmapped_factions"]
    if unmapped:
        a("### Unmapped Factions (Theme Candidates)")
        a("")
        a("These OPERATIONAL SAI entities have no VS Code theme yet:")
        a("")
        for entry in unmapped:
            a(f"- **{entry['designation']}** ({entry['abbrev']}) — {entry['domain']}")
        a("")

    # Cross-Tier Protocols
    a("---")
    a("")
    a("## Cross-Tier Protocols")
    a("")
    for proto in ref["cross_tier_protocols"]:
        a(f"### {proto['protocol']}")
        a("")
        a(f"**Participants:** {', '.join(proto['participants'])}")
        a(f"**Approval:** {proto['approval']}")
        a(f"**Key Entity:** {proto['key_entity']}")
        a("")
        a(proto["mechanism"])
        a("")

    # Existing Themes
    a("---")
    a("")
    a("## Existing Theme Inventory")
    a("")
    a("### Registered Themes (package.json)")
    a("")
    a("| Label | File | Faction |")
    a("|-------|------|---------|")
    for t in ref["existing_themes"]:
        a(f"| {t['label']} | `{t['file']}` | {t['faction']} |")
    a("")

    if ref["theme_summaries"]:
        a("### Theme Metrics")
        a("")
        a("| File | Name | Workbench Keys | Token Rules | Semantic Keys |")
        a("|------|------|----------------|-------------|---------------|")
        for ts in ref["theme_summaries"]:
            a(f"| `{ts['file']}` | {ts['name']} | {ts['workbench_keys']} "
              f"| {ts['token_rules']} | {ts['semantic_keys']} |")
        a("")

    # SFS Palette Baseline
    a("---")
    a("")
    a("## SFS Palette Baseline (Template for New Themes)")
    a("")
    a("Each new theme derives its own 12-color palette. The SFS palette serves")
    a("as the structural template — token names and roles stay consistent,")
    a("only hex values change per-faction.")
    a("")
    a("| Token | Hex | Role |")
    a("|-------|-----|------|")
    for name, p in ref["sfs_palette_baseline"].items():
        a(f"| {name} | `{p['hex']}` | {p['role']} |")
    a("")

    # Theme Creation Checklist
    a("---")
    a("")
    a("## Theme Creation Checklist")
    a("")
    for step in ref["theme_creation_checklist"]:
        a(f"- [ ] {step}")
    a("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    args = sys.argv[1:]
    json_mode = "--json" in args
    output_path = DEFAULT_OUTPUT

    for i, arg in enumerate(args):
        if arg == "--output" and i + 1 < len(args):
            output_path = Path(args[i + 1])

    ref = build_reference()

    if json_mode:
        print(json.dumps(ref, indent=2, ensure_ascii=False))
        return

    md = render_markdown(ref)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(md, encoding="utf-8")
    print(f"☥ Ankh Theme Reference written to: {output_path.relative_to(REPO_ROOT)}")
    print(f"  Tiers: {len(ref['tier_hierarchy'])}")
    print(f"  SAI entries: {len(ref['sai_registry'])}")
    print(f"  Existing themes: {len(ref['existing_themes'])}")
    print(f"  Unmapped factions: {len(ref['unmapped_factions'])}")
    print(f"  Cross-tier protocols: {len(ref['cross_tier_protocols'])}")


if __name__ == "__main__":
    main()
