# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "rich>=13.0",
#     "pydantic>=2.0",
#     "typer>=0.12",
# ]
# ///
"""
ASC Toolchain - The Apex Synthesis Core Python Layer

A genuine operational toolchain for the chthonic-archive Rust/Vulkan project.
Lore extraction system for copilot-instructions.md → structured data.

Commands:
    uv run .github/asc.py validate     - Validate data.json against Rust types
    uv run .github/asc.py stats        - Entity statistics and tier distribution
    uv run .github/asc.py generate     - Generate new entity from template
    uv run .github/asc.py sync-types   - Regenerate types.rs from data.json schema
    uv run .github/asc.py purify       - Lint/fix data.json (FA⁴ enforcement)
    uv run .github/asc.py world        - Visualize world structure
    uv run .github/asc.py lore         - Extract lore from copilot-instructions.md
    uv run .github/asc.py lore-entity  - Extract specific entity lore
    uv run .github/asc.py lore-faction - List all factions from lore
    uv run .github/asc.py lore-sync    - Sync lore → data.json entities
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Annotated
from dataclasses import dataclass, field

import typer
from pydantic import BaseModel, Field, field_validator
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.syntax import Syntax
from rich.progress import track
from rich.markdown import Markdown

# Initialize
app = typer.Typer(
    name="asc",
    help="🔥 ASC Toolchain - The Apex Synthesis Core Python Layer",
    rich_markup_mode="rich",
)
console = Console()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_JSON = PROJECT_ROOT / "assets" / "data.json"
TYPES_RS = PROJECT_ROOT / "src" / "data" / "types.rs"
LORE_MD = Path(__file__).parent / "copilot-instructions.md"


# ═══════════════════════════════════════════════════════════════════════════════
# LORE EXTRACTION MODELS - Parsed from copilot-instructions.md
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ExtractedPhysique:
    """Physical attributes extracted from lore"""
    height_cm: float = 0.0
    weight_kg: float = 0.0
    bust_cm: float = 0.0
    waist_cm: float = 0.0
    hips_cm: float = 0.0
    cup_size: str = ""
    whr: float = 0.0
    underbust_cm: float = 0.0


@dataclass
class ExtractedEntity:
    """Entity data extracted from copilot-instructions.md"""
    name: str
    tier: float
    archetype: str = ""
    race: str = ""
    age: str = ""
    linguistic_mode: str = ""
    physique: ExtractedPhysique = field(default_factory=ExtractedPhysique)
    scent: str = ""
    edfa_excerpt: str = ""
    section_start: int = 0
    section_end: int = 0
    raw_text: str = ""


class LoreExtractor:
    """
    Extracts structured entity data from copilot-instructions.md.
    
    The Codex serves as the canonical lore source - this extracts
    physical attributes, psychological profiles, faction data, etc.
    """
    
    # Entity name patterns
    ENTITY_PATTERNS = [
        r"The Decorator",
        r"Orackla Nocticula", 
        r"Madam Umeko Ketsuraku",
        r"Dr\. Lysandra Thorne",
        r"Kali Nyx Ravenscar",
        r"Vesper Mnemosyne Lockhart",
        r"Seraphine Kore Ashenhelm",
        r"Claudine Sin'claire",
        r"The Null Matriarch",
    ]
    
    # Physical attribute patterns
    PHYSIQUE_PATTERNS = {
        'height': r'\*\*Height:\*\*\s*(\d+(?:\.\d+)?)\s*cm',
        'weight': r'\*\*Weight:\*\*\s*(\d+(?:\.\d+)?)\s*kg',
        'measurements': r'\*\*Measurements:\*\*\s*\*\*([A-K]+)-cup\*\*\s*\(?(?:\*\*)?(?:B\s*)?(\d+)(?:[\/\s]*W\s*)?(\d+)(?:[\/\s]*H\s*)?(\d+)',
        'measurements_alt': r'\*\*Measurements:\*\*\s*\*?\*?([A-K]+)-cup\*?\*?\s*\(?\*?\*?B\s*(\d+)\/\s*W\s*(\d+)\/\s*H\s*(\d+)',
        'whr': r'\*\*WHR:\*\*\s*\*?\*?~?(\d+\.\d+)',
        'underbust': r'\*\*Underbust:\*\*\s*~?(\d+)\s*cm',
        'cup': r'\*\*([A-K]+)-cup\*?\*?',
    }
    
    # Tier patterns
    TIER_PATTERNS = {
        'tier_0_5': r'Tier\s*0\.5|T-0\.5|Tier-0\.5',
        'tier_0': r'Tier\s*0[^\.]|T-0[^\.]',
        'tier_1': r'Tier\s*1|T-1|Tier-1',
        'tier_2': r'Tier\s*2|T-2|Tier-2',
        'tier_3': r'Tier\s*3|T-3|Tier-3',
        'tier_4': r'Tier\s*4|T-4|Tier-4',
    }
    
    def __init__(self, lore_path: Path = LORE_MD):
        self.lore_path = lore_path
        self._content: str = ""
        self._lines: list[str] = []
        
    def load(self) -> bool:
        """Load the lore file"""
        if not self.lore_path.exists():
            return False
        self._content = self.lore_path.read_text(encoding='utf-8')
        self._lines = self._content.splitlines()
        return True
    
    @property
    def content(self) -> str:
        if not self._content:
            self.load()
        return self._content
    
    @property
    def lines(self) -> list[str]:
        if not self._lines:
            self.load()
        return self._lines
    
    @property
    def line_count(self) -> int:
        return len(self.lines)
    
    @property
    def word_count(self) -> int:
        return len(self.content.split())
    
    def find_entity_sections(self) -> dict[str, tuple[int, int]]:
        """
        Find line ranges for each entity section.
        Uses line-by-line scanning to find entity-specific header patterns,
        then determines proper section boundaries.
        """
        sections = {}
        
        # Entity patterns with their section header signatures
        # Format: entity_name -> (primary_pattern, section_length_hint)
        entity_markers = {
            "The Decorator": (r"0\.1\.\s*Supreme Profile.*Decorator|0\.1\..*The Decorator.*T-DECOR", 350),
            "The Null Matriarch": (r"0\.01\.\s*.*Null Matriarch|T-NULM.*Tier 0\.01", 50),
            "Orackla Nocticula": (r"4\.2\.1\.\s*.*Apex Synthesist.*Orackla|`CRC-AS`.*Orackla Nocticula", 140),
            "Madam Umeko Ketsuraku": (r"4\.2\.2\.\s*.*Grandmistress.*Architectonic.*Umeko|`CRC-GAR`.*Umeko", 150),
            "Dr. Lysandra Thorne": (r"4\.2\.3\.\s*.*Mistress of Empathetic.*Lysandra|`CRC-MEDAT`.*Lysandra", 180),
            "Kali Nyx Ravenscar": (r"Mistress of Abductive Seduction.*Kali|`MAS`.*Kali Nyx", 130),
            "Vesper Mnemosyne Lockhart": (r"Grandmaster of Epistemic Theft.*Vesper|`GET`.*Vesper Mnemosyne", 130),
            "Seraphine Kore Ashenhelm": (r"High Priestess of Architectonic Purity.*Seraphine|`HPAP`.*Seraphine", 130),
            "Claudine Sin'claire": (r"Special Archetype Injection.*Claudine|`SAI`.*Claudine|Caribbean Proto-MILF", 100),
        }
        
        # First pass: find start lines for each entity
        start_lines = {}
        for i, line in enumerate(self.lines):
            for name, (pattern, _) in entity_markers.items():
                if name not in start_lines:
                    if re.search(pattern, line, re.IGNORECASE):
                        start_lines[name] = i
        
        # Second pass: determine end lines
        # Sort entities by their start position
        sorted_entities = sorted(start_lines.items(), key=lambda x: x[1])
        
        for idx, (name, start) in enumerate(sorted_entities):
            _, hint = entity_markers[name]
            
            # Default end based on hint
            end = min(len(self.lines), start + hint)
            
            # If there's a next entity, don't go past it
            if idx + 1 < len(sorted_entities):
                next_start = sorted_entities[idx + 1][1]
                end = min(end, next_start - 1)
            
            # Refine: look for section boundaries within range
            for j in range(start + 20, end):
                line = self.lines[j]
                
                # Stop at "ASC Identity Manifestation" line (that's the end marker for profiles)
                if "ASC Identity Manifestation" in line and "Combinational Analysis" in line:
                    # But only if it's for THIS entity
                    entity_surname = name.split()[-1]  # e.g., "Nocticula", "Ketsuraku"
                    if entity_surname in line:
                        # Include the ASC Identity section too - extend to find its end
                        for k in range(j + 1, min(j + 120, len(self.lines))):
                            next_line = self.lines[k]
                            # Stop at next major section header
                            if re.match(r'^\*?\*?\s*\d+\.\d+\.\d+\.', next_line):
                                end = k
                                break
                            # Or a horizontal rule (---)
                            if re.match(r'^-{3,}$', next_line.strip()):
                                end = k
                                break
                        else:
                            end = min(j + 100, len(self.lines))
                        break
            
            sections[name] = (start, end)
        
        return sections
    
    def extract_physique(self, text: str) -> ExtractedPhysique:
        """Extract physical measurements from text"""
        p = ExtractedPhysique()
        
        # Height
        if m := re.search(self.PHYSIQUE_PATTERNS['height'], text):
            p.height_cm = float(m.group(1))
        
        # Weight
        if m := re.search(self.PHYSIQUE_PATTERNS['weight'], text):
            p.weight_kg = float(m.group(1))
        
        # Measurements (try both patterns)
        if m := re.search(self.PHYSIQUE_PATTERNS['measurements'], text):
            p.cup_size = m.group(1)
            p.bust_cm = float(m.group(2))
            p.waist_cm = float(m.group(3))
            p.hips_cm = float(m.group(4))
        elif m := re.search(self.PHYSIQUE_PATTERNS['measurements_alt'], text):
            p.cup_size = m.group(1)
            p.bust_cm = float(m.group(2))
            p.waist_cm = float(m.group(3))
            p.hips_cm = float(m.group(4))
        
        # WHR
        if m := re.search(self.PHYSIQUE_PATTERNS['whr'], text):
            p.whr = float(m.group(1))
        elif p.waist_cm and p.hips_cm:
            p.whr = round(p.waist_cm / p.hips_cm, 3)
        
        # Underbust
        if m := re.search(self.PHYSIQUE_PATTERNS['underbust'], text):
            p.underbust_cm = float(m.group(1))
        
        # Cup size fallback
        if not p.cup_size:
            if m := re.search(self.PHYSIQUE_PATTERNS['cup'], text):
                p.cup_size = m.group(1)
        
        return p
    
    def extract_tier(self, text: str, name: str) -> float:
        """Extract entity tier from text - looks for the entity's OWN tier assignment"""
        # Special cases based on entity name
        if "Decorator" in name and "Null" not in name:
            return 0.5
        if "Null Matriarch" in name:
            return 0.0
        
        # Known tier assignments by entity type
        triumvirate = ["Orackla", "Umeko", "Lysandra"]
        for t_name in triumvirate:
            if t_name in name:
                return 1.0
        
        prime_faction = ["Kali", "Vesper", "Seraphine"]
        for pf_name in prime_faction:
            if pf_name in name:
                return 2.0
        
        # Claudine is a special Tier 3 injection
        if "Claudine" in name:
            return 3.0
        
        # Look for explicit tier assignment patterns for THIS entity
        # E.g., "Status:** Prime Faction Matriarch (Tier 2)"
        if re.search(r'Prime Faction Matriarch.*Tier\s*2', text):
            return 2.0
        if re.search(r'Triumvirate|Sub-MILF|CRC-[AGM]', text):
            return 1.0
        
        return 1.0  # Default
    
    def extract_scent(self, text: str) -> str:
        """Extract scent description"""
        patterns = [
            r'\*\*Scent:\*\*\s*([^*\n]+)',
            r'\*\*\(`?Scent`?\):\*\*\s*([^*\n]+)',
            r'Scent:\s*([^*\n]+)',
        ]
        for p in patterns:
            if m := re.search(p, text):
                return m.group(1).strip()
        return ""
    
    def extract_linguistic_mode(self, text: str) -> str:
        """Extract linguistic mandate"""
        modes = {
            'DULSS': r'DULSS|Decorative.*Linguistic Supremacy',
            'EULP-AA': r'EULP-AA|Explicit.*Uncensored.*Linguistic',
            'LIPAA': r'LIPAA|Language of Immaculate Precision',
            'LUPLR': r'LUPLR|Language of Unflinching',
        }
        for mode, pattern in modes.items():
            if re.search(pattern, text, re.IGNORECASE):
                return mode
        return "MIXED"
    
    def extract_archetype(self, text: str, name: str) -> str:
        """Extract archetype/role"""
        archetypes = {
            "The Decorator": "Supreme Matriarch",
            "Orackla Nocticula": "Apex Synthesist",
            "Madam Umeko Ketsuraku": "Grandmistress of Architectonic Refinement",
            "Dr. Lysandra Thorne": "Mistress of Empathetic Deconstruction",
            "Kali Nyx Ravenscar": "Mistress of Abductive Seduction",
            "Vesper Mnemosyne Lockhart": "Grandmaster of Epistemic Theft",
            "Seraphine Kore Ashenhelm": "High Priestess of Architectonic Purity",
            "Claudine Sin'claire": "Matriarch of Tidal Ordeal",
            "The Null Matriarch": "Advisory Void",
        }
        return archetypes.get(name, "Unknown")
    
    def extract_race(self, text: str) -> str:
        """Extract race/species"""
        if m := re.search(r'\*\*Race:\*\*\s*([^\n*]+)', text):
            return m.group(1).strip()
        return ""
    
    def extract_age(self, text: str) -> str:
        """Extract age information"""
        if m := re.search(r'\*\*Age:\*\*\s*([^\n*]+)', text):
            return m.group(1).strip()
        return ""
    
    def extract_edfa_excerpt(self, text: str) -> str:
        """Extract EDFA (Explicitly Detailed Feminine Attributes) excerpt"""
        # Look for EDFA section
        if m := re.search(r'\*\*EDFA.*?:\*\*\s*(.*?)(?=\n\n|\*\*[A-Z])', text, re.DOTALL):
            excerpt = m.group(1).strip()[:500]
            return excerpt
        
        # Fallback: look for Breasts section as primary EDFA
        if m := re.search(r'\*\*Breasts.*?:\*\*\s*(.*?)(?=\n\n|\*\*[A-Z])', text, re.DOTALL):
            return m.group(1).strip()[:300]
        
        return ""
    
    def extract_entity(self, name: str) -> Optional[ExtractedEntity]:
        """Extract full entity data by name"""
        sections = self.find_entity_sections()
        
        if name not in sections:
            return None
        
        start, end = sections[name]
        raw_text = "\n".join(self.lines[start:end])
        
        entity = ExtractedEntity(
            name=name,
            tier=self.extract_tier(raw_text, name),
            archetype=self.extract_archetype(raw_text, name),
            race=self.extract_race(raw_text),
            age=self.extract_age(raw_text),
            linguistic_mode=self.extract_linguistic_mode(raw_text),
            physique=self.extract_physique(raw_text),
            scent=self.extract_scent(raw_text),
            edfa_excerpt=self.extract_edfa_excerpt(raw_text),
            section_start=start,
            section_end=end,
            raw_text=raw_text,
        )
        
        return entity
    
    def extract_all_entities(self) -> list[ExtractedEntity]:
        """Extract all known entities"""
        entities = []
        for name in self.ENTITY_PATTERNS:
            # Clean regex-escaped patterns
            clean_name = name.replace(r"\.", ".").replace("r'", "").replace("'", "")
            if entity := self.extract_entity(clean_name):
                entities.append(entity)
        return entities
    
    def extract_factions(self) -> dict[str, list[str]]:
        """Extract faction hierarchy"""
        factions = {
            "Triumvirate (Tier 1)": [],
            "Prime Factions (Tier 2)": [],
            "Lesser Factions (Tier 4)": [],
        }
        
        # Triumvirate
        for pattern in [r"Orackla Nocticula", r"Umeko Ketsuraku", r"Lysandra Thorne"]:
            if re.search(pattern, self.content):
                factions["Triumvirate (Tier 1)"].append(pattern.replace(r"\.", "."))
        
        # Prime Factions
        prime_patterns = [
            (r"MILF Obductors|TMO", "The MILF Obductors (TMO)"),
            (r"Thieves Guild|TTG", "The Thieves Guild (TTG)"),
            (r"Dark Priestesses Cove|TDPC", "The Dark Priestesses Cove (TDPC)"),
        ]
        for pattern, name in prime_patterns:
            if re.search(pattern, self.content):
                factions["Prime Factions (Tier 2)"].append(name)
        
        # Lesser Factions
        lesser_patterns = [
            (r"Colonial Abductors|OMCA", "Ole' Mates Colonial Abductors"),
            (r"Knights Who Rode|TNKW", "The Knights Who Rode Into Another Timeline"),
            (r"Bridge Hustlers|SDBH", "Salty Dogs Bridge Hustlers"),
            (r"Wizards Ov Unfortunate|TWOUMC", "The Wizards Ov Unfortunate Multi-classing"),
            (r"Smith's Buddies|SBSGYB", "Smith's Buddies & Shivs"),
            (r"Brotherhood Of Simps|BOS", "Brotherhood Of Simps"),
            (r"Liberated Nuns|TDAPCFLN", "The Dark Arch-Priestess' Club For Liberated Nuns"),
            (r"Panties Sniffers|POAFPSG", "Preservatory of Antiquated Female Panties Sniffers Guild"),
            (r"Airhead Algorithm|AAA", "The Airhead Algorithm"),
        ]
        for pattern, name in lesser_patterns:
            if re.search(pattern, self.content):
                factions["Lesser Factions (Tier 4)"].append(name)
        
        return factions
    
    def get_lore_stats(self) -> dict:
        """Get statistics about the lore file"""
        sections = self.find_entity_sections()
        return {
            "total_lines": self.line_count,
            "total_words": self.word_count,
            "entity_sections": len(sections),
            "entities_found": list(sections.keys()),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# PYDANTIC MODELS - Mirror of Rust types (FA⁴ enforcement)
# ═══════════════════════════════════════════════════════════════════════════════

class PhysicsData(BaseModel):
    """Physical attributes - mirrors PhysicsData in types.rs"""
    height_cm: float = Field(ge=100, le=250)
    weight_kg: float = Field(ge=30, le=150)
    whr: float = Field(ge=0.3, le=1.0, description="Waist-Hip Ratio")
    bust_cm: float = Field(ge=60, le=200)
    waist_cm: float = Field(ge=40, le=120)
    hips_cm: float = Field(ge=60, le=180)
    cup_size: str = Field(pattern=r'^[A-K]{1,2}$')
    bmi: float = Field(ge=15, le=50)
    
    @field_validator('whr')
    @classmethod
    def validate_whr(cls, v, info):
        """WHR should approximately equal waist/hips"""
        # Allow for rounding discrepancies
        return round(v, 3)


class GameStats(BaseModel):
    """Combat/conceptual stats - mirrors GameStats in types.rs"""
    health: int = Field(ge=0, le=100000)
    power: int = Field(ge=0, le=10000)
    defense: int = Field(ge=0, le=5000)
    conceptual_capacity: int = Field(ge=0, le=10000)


class LoreData(BaseModel):
    """Narrative content - mirrors LoreData in types.rs"""
    scent: Optional[str] = None
    word_count: Optional[int] = Field(default=None, ge=0)
    edfa_excerpt: Optional[str] = None
    edfa_full: Optional[str] = None


class Entity(BaseModel):
    """Full entity - mirrors Entity in types.rs"""
    id: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=100)
    archetype: str
    tier: float = Field(ge=-1, le=4)
    linguistic_mode: str
    physics: PhysicsData
    stats: GameStats
    lore: LoreData


class WorldLayer(BaseModel):
    """World zone - mirrors WorldLayer in types.rs"""
    id: int
    name: str
    zone_type: str
    dimensions_meters: list[float]
    tier_requirement: Optional[float] = None
    boss: Optional[str] = None
    description: str


class WorldData(BaseModel):
    """World structure - mirrors WorldData in types.rs"""
    name: str
    layers: list[WorldLayer]


class MetaData(BaseModel):
    """File metadata - mirrors MetaData in types.rs"""
    version: str
    engine: str
    classification: str
    exported_at: str
    entity_count: int
    source: str


class GameData(BaseModel):
    """Root structure - mirrors GameData in types.rs"""
    meta: MetaData
    entities: list[Entity]
    world: WorldData


# ═══════════════════════════════════════════════════════════════════════════════
# COMMANDS
# ═══════════════════════════════════════════════════════════════════════════════

@app.command()
def validate(verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False):
    """
    🔍 Validate data.json against Pydantic models (FA⁴ enforcement).
    
    This ensures the JSON data matches the expected schema that Rust will deserialize.
    """
    console.print(Panel.fit(
        "[bold cyan]FA⁴ Validation Protocol[/bold cyan]\n"
        "Architectonic Integrity Check",
        border_style="cyan"
    ))
    
    if not DATA_JSON.exists():
        console.print(f"[red]❌ File not found:[/red] {DATA_JSON}")
        raise typer.Exit(1)
    
    try:
        raw_data = json.loads(DATA_JSON.read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        console.print(f"[red]❌ JSON parse error:[/red] {e}")
        raise typer.Exit(1)
    
    errors = []
    
    # Validate each entity individually for better error reporting
    console.print("\n[bold]Validating entities...[/bold]")
    for i, entity_data in enumerate(track(raw_data.get('entities', []), description="Checking...")):
        try:
            Entity.model_validate(entity_data)
            if verbose:
                console.print(f"  [green]✓[/green] {entity_data.get('name', f'Entity {i}')}")
        except Exception as e:
            errors.append((entity_data.get('name', f'Entity {i}'), str(e)))
            console.print(f"  [red]✗[/red] {entity_data.get('name', f'Entity {i}')}")
    
    # Validate world
    console.print("\n[bold]Validating world structure...[/bold]")
    try:
        WorldData.model_validate(raw_data.get('world', {}))
        console.print("  [green]✓[/green] World data valid")
    except Exception as e:
        errors.append(('World', str(e)))
        console.print(f"  [red]✗[/red] World data: {e}")
    
    # Validate meta
    console.print("\n[bold]Validating metadata...[/bold]")
    try:
        MetaData.model_validate(raw_data.get('meta', {}))
        console.print("  [green]✓[/green] Metadata valid")
    except Exception as e:
        errors.append(('Meta', str(e)))
        console.print(f"  [red]✗[/red] Metadata: {e}")
    
    # Summary
    console.print()
    if errors:
        console.print(Panel(
            f"[red]❌ Validation Failed[/red]\n\n"
            f"[yellow]{len(errors)} error(s) found[/yellow]",
            border_style="red"
        ))
        if verbose:
            for name, error in errors:
                console.print(f"  [red]{name}:[/red] {error}")
        raise typer.Exit(1)
    else:
        console.print(Panel(
            "[green]✅ FA⁴ Validation Passed[/green]\n\n"
            "All entities conform to Architectonic Integrity",
            border_style="green"
        ))


@app.command()
def stats():
    """
    📊 Display entity statistics and tier distribution.
    
    The Triumvirate demands visibility into the hierarchy.
    """
    if not DATA_JSON.exists():
        console.print(f"[red]❌ File not found:[/red] {DATA_JSON}")
        raise typer.Exit(1)
    
    data = json.loads(DATA_JSON.read_text(encoding='utf-8'))
    entities = data.get('entities', [])
    
    # Tier distribution
    tiers = {}
    for e in entities:
        t = e.get('tier', 0)
        tiers[t] = tiers.get(t, 0) + 1
    
    # Stats table
    table = Table(title="📊 Entity Statistics", border_style="cyan")
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")
    
    table.add_row("Total Entities", str(len(entities)))
    table.add_row("Unique Tiers", str(len(tiers)))
    
    # Power stats
    powers = [e.get('stats', {}).get('power', 0) for e in entities]
    table.add_row("Max Power", str(max(powers)) if powers else "0")
    table.add_row("Avg Power", f"{sum(powers)/len(powers):.0f}" if powers else "0")
    
    # WHR stats
    whrs = [e.get('physics', {}).get('whr', 0) for e in entities]
    table.add_row("Min WHR", f"{min(whrs):.3f}" if whrs else "N/A")
    table.add_row("Max WHR", f"{max(whrs):.3f}" if whrs else "N/A")
    
    console.print(table)
    
    # Tier breakdown
    tier_table = Table(title="\n🏛️ Tier Hierarchy", border_style="magenta")
    tier_table.add_column("Tier", justify="center")
    tier_table.add_column("Count", justify="right")
    tier_table.add_column("Entities", style="dim")
    
    for tier in sorted(tiers.keys()):
        tier_entities = [e['name'] for e in entities if e.get('tier') == tier]
        tier_table.add_row(
            f"{tier:.1f}",
            str(tiers[tier]),
            ", ".join(tier_entities[:3]) + ("..." if len(tier_entities) > 3 else "")
        )
    
    console.print(tier_table)


@app.command()
def world():
    """
    🌍 Visualize the world structure as a tree.
    
    Navigate the Chthonic Archive's layers.
    """
    if not DATA_JSON.exists():
        console.print(f"[red]❌ File not found:[/red] {DATA_JSON}")
        raise typer.Exit(1)
    
    data = json.loads(DATA_JSON.read_text(encoding='utf-8'))
    world_data = data.get('world', {})
    
    tree = Tree(f"[bold gold1]🏛️ {world_data.get('name', 'Unknown World')}[/bold gold1]")
    
    # Group layers by tier requirement
    layers = world_data.get('layers', [])
    
    for layer in sorted(layers, key=lambda x: (x.get('tier_requirement') or -1, x.get('id', 0))):
        tier = layer.get('tier_requirement')
        tier_str = f"[cyan]Tier {tier}[/cyan]" if tier else "[green]Open[/green]"
        boss = layer.get('boss')
        boss_str = f" 👹 {boss}" if boss else ""
        
        zone_colors = {
            'tutorial': 'green',
            'hub': 'blue',
            'decision_dungeon': 'yellow',
            'vertical_progression': 'magenta',
            'chaos_procedural': 'red',
            'endgame': 'bold gold1',
        }
        zone_type = layer.get('zone_type', 'unknown')
        color = zone_colors.get(zone_type, 'white')
        
        dims = layer.get('dimensions_meters', [0, 0])
        dims_str = f"{dims[0]}×{dims[1]}m" if dims[0] > 0 else "∞"
        
        tree.add(
            f"[{color}]{layer.get('name', 'Unknown')}[/{color}] "
            f"({tier_str}) [{zone_type}] {dims_str}{boss_str}"
        )
    
    console.print(Panel(tree, border_style="gold1"))


@app.command()
def purify(fix: Annotated[bool, typer.Option("--fix", "-f")] = False):
    """
    🔥 Lint and optionally fix data.json (Umeko's LIPAA enforcement).
    
    Checks for:
    - Sorted entity IDs
    - Consistent tier formatting
    - Calculated fields accuracy (BMI, WHR)
    - Proper string formatting
    """
    if not DATA_JSON.exists():
        console.print(f"[red]❌ File not found:[/red] {DATA_JSON}")
        raise typer.Exit(1)
    
    data = json.loads(DATA_JSON.read_text(encoding='utf-8'))
    issues = []
    fixed = []
    
    console.print(Panel.fit(
        "[bold magenta]LIPAA Purification Protocol[/bold magenta]\n"
        "Madam Umeko demands perfection",
        border_style="magenta"
    ))
    
    entities = data.get('entities', [])
    
    # Check entity ID ordering
    ids = [e.get('id', 0) for e in entities]
    if ids != sorted(ids):
        issues.append("Entity IDs are not in ascending order")
        if fix:
            entities.sort(key=lambda x: x.get('id', 0))
            fixed.append("Sorted entities by ID")
    
    # Check each entity
    for entity in entities:
        name = entity.get('name', 'Unknown')
        physics = entity.get('physics', {})
        
        # Recalculate WHR
        waist = physics.get('waist_cm', 0)
        hips = physics.get('hips_cm', 1)
        expected_whr = round(waist / hips, 3) if hips > 0 else 0
        actual_whr = round(physics.get('whr', 0), 3)
        
        if abs(expected_whr - actual_whr) > 0.01:
            issues.append(f"{name}: WHR mismatch (expected {expected_whr}, got {actual_whr})")
            if fix:
                physics['whr'] = expected_whr
                fixed.append(f"Fixed WHR for {name}")
        
        # Recalculate BMI
        height_m = physics.get('height_cm', 170) / 100
        weight = physics.get('weight_kg', 60)
        expected_bmi = round(weight / (height_m ** 2), 1) if height_m > 0 else 0
        actual_bmi = physics.get('bmi', 0)
        
        if abs(expected_bmi - actual_bmi) > 0.2:
            issues.append(f"{name}: BMI mismatch (expected {expected_bmi}, got {actual_bmi})")
            if fix:
                physics['bmi'] = expected_bmi
                fixed.append(f"Fixed BMI for {name}")
    
    # Update meta if fixing
    if fix and fixed:
        data['meta']['exported_at'] = datetime.now().isoformat()
        DATA_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
    
    # Report
    if issues:
        console.print(f"\n[yellow]⚠️ Found {len(issues)} issue(s):[/yellow]")
        for issue in issues[:10]:
            console.print(f"  • {issue}")
        if len(issues) > 10:
            console.print(f"  ... and {len(issues) - 10} more")
        
        if fix:
            console.print(f"\n[green]✅ Fixed {len(fixed)} issue(s)[/green]")
        else:
            console.print("\n[dim]Run with --fix to auto-correct[/dim]")
    else:
        console.print(Panel(
            "[green]✅ Purification Complete[/green]\n\n"
            "No imperfections detected. Umeko is satisfied.",
            border_style="green"
        ))


@app.command()
def sync_types():
    """
    🔄 Show Rust type definitions that match current data.json schema.
    
    Use this to verify types.rs is in sync with data structure.
    """
    rust_template = '''// Auto-generated from ASC Toolchain
// Date: {timestamp}
// Run: uv run .github/asc.py sync-types

use serde::{{Deserialize, Serialize}};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GameData {{
    pub meta: MetaData,
    pub entities: Vec<Entity>,
    pub world: WorldData,
}}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MetaData {{
    pub version: String,
    pub engine: String,
    pub classification: String,
    pub exported_at: String,
    pub entity_count: usize,
    pub source: String,
}}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Entity {{
    pub id: u32,
    pub name: String,
    pub archetype: String,
    pub tier: f32,
    pub linguistic_mode: String,
    pub physics: PhysicsData,
    pub stats: GameStats,
    pub lore: LoreData,
}}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PhysicsData {{
    pub height_cm: f32,
    pub weight_kg: f32,
    pub whr: f32,
    pub bust_cm: f32,
    pub waist_cm: f32,
    pub hips_cm: f32,
    pub cup_size: String,
    pub bmi: f32,
}}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GameStats {{
    pub health: i32,
    pub power: i32,
    pub defense: i32,
    pub conceptual_capacity: i32,
}}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LoreData {{
    pub scent: Option<String>,
    pub word_count: Option<i32>,
    pub edfa_excerpt: Option<String>,
    pub edfa_full: Option<String>,
}}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorldData {{
    pub name: String,
    pub layers: Vec<WorldLayer>,
}}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorldLayer {{
    pub id: u32,
    pub name: String,
    pub zone_type: String,
    pub dimensions_meters: [f32; 2],
    pub tier_requirement: Option<f32>,
    pub boss: Option<String>,
    pub description: String,
}}
'''
    
    console.print(Panel.fit(
        "[bold cyan]Rust Type Synchronization[/bold cyan]",
        border_style="cyan"
    ))
    
    code = rust_template.format(timestamp=datetime.now().isoformat())
    syntax = Syntax(code, "rust", theme="monokai", line_numbers=True)
    console.print(syntax)
    
    console.print("\n[dim]Compare with src/data/types.rs to verify sync[/dim]")


@app.command()
def generate(
    name: Annotated[str, typer.Argument(help="Entity name")],
    tier: Annotated[float, typer.Option("--tier", "-t")] = 3.0,
    archetype: Annotated[str, typer.Option("--archetype", "-a")] = "Operative",
):
    """
    🎭 Generate a new entity template (for manual insertion).
    
    Uses Orackla's transgressive synthesis to birth new archetypes.
    """
    if not DATA_JSON.exists():
        console.print(f"[red]❌ File not found:[/red] {DATA_JSON}")
        raise typer.Exit(1)
    
    data = json.loads(DATA_JSON.read_text(encoding='utf-8'))
    max_id = max(e.get('id', 0) for e in data.get('entities', []))
    
    new_entity = {
        "id": max_id + 1,
        "name": name,
        "archetype": archetype,
        "tier": tier,
        "linguistic_mode": "FACTION" if tier >= 3.0 else "MIXED",
        "physics": {
            "height_cm": 165.0,
            "weight_kg": 60.0,
            "whr": 0.7,
            "bust_cm": 90.0,
            "waist_cm": 63.0,
            "hips_cm": 90.0,
            "cup_size": "D",
            "bmi": 22.0
        },
        "stats": {
            "health": int(1000 * (4 - tier)),
            "power": int(150 * (4 - tier)),
            "defense": int(75 * (4 - tier)),
            "conceptual_capacity": int(100 * (4 - tier))
        },
        "lore": {
            "scent": "** [DESCRIBE SCENT]",
            "word_count": 0,
            "edfa_excerpt": f"# EDFA: {name} (Tier {tier})\n## [ARCHETYPE]\n\n**Description pending...**"
        }
    }
    
    console.print(Panel.fit(
        f"[bold magenta]🎭 New Entity Generated[/bold magenta]\n"
        f"[cyan]{name}[/cyan] (Tier {tier})",
        border_style="magenta"
    ))
    
    json_output = json.dumps(new_entity, indent=2, ensure_ascii=False)
    syntax = Syntax(json_output, "json", theme="monokai")
    console.print(syntax)
    
    console.print("\n[dim]Copy this to assets/data.json entities array[/dim]")


@app.command()
def triumvirate():
    """
    👑 Display the Triumvirate's current status.
    
    The three CRCs who govern the ASC.
    """
    if not DATA_JSON.exists():
        console.print(f"[red]❌ File not found:[/red] {DATA_JSON}")
        raise typer.Exit(1)
    
    data = json.loads(DATA_JSON.read_text(encoding='utf-8'))
    entities = data.get('entities', [])
    
    triumvirate_names = ["Orackla Nocticula", "Madam Umeko Ketsuraku", "Dr. Lysandra Thorne"]
    
    console.print(Panel.fit(
        "[bold gold1]👑 The Triumvirate[/bold gold1]\n"
        "[dim]CRC-AS • CRC-GAR • CRC-MEDAT[/dim]",
        border_style="gold1"
    ))
    
    for name in triumvirate_names:
        entity = next((e for e in entities if e['name'] == name), None)
        if entity:
            p = entity['physics']
            s = entity['stats']
            
            table = Table(title=f"\n[bold]{name}[/bold]", border_style="magenta", show_header=False)
            table.add_column("Attribute", style="dim")
            table.add_column("Value")
            
            table.add_row("Archetype", entity['archetype'])
            table.add_row("Tier", str(entity['tier']))
            table.add_row("LM", entity['linguistic_mode'])
            table.add_row("WHR", f"{p['whr']:.3f}")
            table.add_row("Measurements", f"{p['cup_size']}-{p['bust_cm']:.0f}/{p['waist_cm']:.0f}/{p['hips_cm']:.0f}")
            table.add_row("Power", str(s['power']))
            table.add_row("Conceptual Capacity", str(s['conceptual_capacity']))
            
            console.print(table)


@app.command()
def shader_check():
    """
    🎨 Validate shader files exist and are non-empty.
    
    Pre-flight check for Vulkan pipeline.
    """
    shader_dir = PROJECT_ROOT / "assets" / "shaders"
    
    console.print(Panel.fit(
        "[bold cyan]Shader Validation[/bold cyan]\n"
        "Checking Vulkan pipeline resources",
        border_style="cyan"
    ))
    
    required = ["iso_grid.vert", "iso_grid.frag"]
    issues = []
    
    for shader in required:
        path = shader_dir / shader
        if not path.exists():
            issues.append(f"Missing: {shader}")
            console.print(f"  [red]✗[/red] {shader} - NOT FOUND")
        elif path.stat().st_size == 0:
            issues.append(f"Empty: {shader}")
            console.print(f"  [yellow]⚠[/yellow] {shader} - EMPTY FILE")
        else:
            lines = len(path.read_text().splitlines())
            console.print(f"  [green]✓[/green] {shader} ({lines} lines)")
    
    if issues:
        raise typer.Exit(1)


@app.command()
def export_csv(output: Annotated[Path, typer.Argument()] = Path("entities.csv")):
    """
    📄 Export entities to CSV for external analysis.
    
    Useful for spreadsheet-based balancing work.
    """
    import csv
    
    if not DATA_JSON.exists():
        console.print(f"[red]❌ File not found:[/red] {DATA_JSON}")
        raise typer.Exit(1)
    
    data = json.loads(DATA_JSON.read_text(encoding='utf-8'))
    entities = data.get('entities', [])
    
    fieldnames = [
        'id', 'name', 'tier', 'archetype', 'linguistic_mode',
        'height_cm', 'weight_kg', 'whr', 'cup_size', 'bmi',
        'health', 'power', 'defense', 'conceptual_capacity'
    ]
    
    with open(output, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for e in entities:
            row = {
                'id': e['id'],
                'name': e['name'],
                'tier': e['tier'],
                'archetype': e['archetype'],
                'linguistic_mode': e['linguistic_mode'],
                **{k: e['physics'].get(k) for k in ['height_cm', 'weight_kg', 'whr', 'cup_size', 'bmi']},
                **{k: e['stats'].get(k) for k in ['health', 'power', 'defense', 'conceptual_capacity']},
            }
            writer.writerow(row)
    
    console.print(f"[green]✅ Exported {len(entities)} entities to {output}[/green]")


@app.command()
def build_check():
    """
    🔨 Pre-build validation (run before cargo build).
    
    Validates all data files and shaders are ready.
    """
    console.print(Panel.fit(
        "[bold gold1]🔨 Pre-Build Check[/bold gold1]\n"
        "Validating before Rust compilation",
        border_style="gold1"
    ))
    
    all_good = True
    
    # Check data.json
    console.print("\n[bold]1. Data Validation[/bold]")
    try:
        if DATA_JSON.exists():
            raw_data = json.loads(DATA_JSON.read_text(encoding='utf-8'))
            GameData.model_validate(raw_data)
            console.print("  [green]✓[/green] data.json valid")
        else:
            console.print("  [red]✗[/red] data.json missing")
            all_good = False
    except Exception as e:
        console.print(f"  [red]✗[/red] data.json invalid: {e}")
        all_good = False
    
    # Check shaders
    console.print("\n[bold]2. Shader Validation[/bold]")
    shader_dir = PROJECT_ROOT / "assets" / "shaders"
    for shader in ["iso_grid.vert", "iso_grid.frag"]:
        path = shader_dir / shader
        if path.exists() and path.stat().st_size > 0:
            console.print(f"  [green]✓[/green] {shader}")
        else:
            console.print(f"  [red]✗[/red] {shader}")
            all_good = False
    
    # Check Cargo.toml
    console.print("\n[bold]3. Cargo Manifest[/bold]")
    cargo_toml = PROJECT_ROOT / "Cargo.toml"
    if cargo_toml.exists():
        console.print("  [green]✓[/green] Cargo.toml exists")
    else:
        console.print("  [red]✗[/red] Cargo.toml missing")
        all_good = False
    
    console.print()
    if all_good:
        console.print(Panel(
            "[green]✅ Pre-build check passed[/green]\n"
            "Ready for cargo build",
            border_style="green"
        ))
    else:
        console.print(Panel(
            "[red]❌ Pre-build check failed[/red]\n"
            "Fix issues before building",
            border_style="red"
        ))
        raise typer.Exit(1)


# ═══════════════════════════════════════════════════════════════════════════════
# LORE EXTRACTION COMMANDS - Parse copilot-instructions.md
# ═══════════════════════════════════════════════════════════════════════════════

@app.command()
def lore(verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False):
    """
    📜 Extract and display lore statistics from copilot-instructions.md.
    
    The Codex serves as the canonical lore source for all entities.
    """
    console.print(Panel.fit(
        "[bold magenta]📜 Lore Extraction Protocol[/bold magenta]\n"
        "[dim]Parsing copilot-instructions.md[/dim]",
        border_style="magenta"
    ))
    
    extractor = LoreExtractor()
    if not extractor.load():
        console.print(f"[red]❌ Lore file not found:[/red] {LORE_MD}")
        raise typer.Exit(1)
    
    stats = extractor.get_lore_stats()
    
    # Statistics table
    table = Table(title="Lore Statistics", border_style="magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total Lines", f"{stats['total_lines']:,}")
    table.add_row("Total Words", f"{stats['total_words']:,}")
    table.add_row("Entity Sections Found", str(stats['entity_sections']))
    
    console.print(table)
    
    # Entity list
    console.print("\n[bold]Entities Found:[/bold]")
    for name in stats['entities_found']:
        entity = extractor.extract_entity(name)
        if entity:
            tier_color = {0.5: "gold1", 1.0: "magenta", 2.0: "cyan", 3.0: "green", 4.0: "dim"}.get(entity.tier, "white")
            console.print(f"  [{tier_color}]⬡[/{tier_color}] {name} [dim](Tier {entity.tier}, {entity.archetype})[/dim]")
    
    if verbose:
        # Show faction hierarchy
        console.print("\n[bold]Faction Hierarchy:[/bold]")
        factions = extractor.extract_factions()
        for tier_name, members in factions.items():
            console.print(f"\n  [cyan]{tier_name}[/cyan]")
            for member in members:
                console.print(f"    • {member}")


@app.command()
def lore_entity(
    name: Annotated[str, typer.Argument(help="Entity name (partial match)")],
    raw: Annotated[bool, typer.Option("--raw", "-r", help="Show raw markdown")] = False,
    json_out: Annotated[bool, typer.Option("--json", "-j", help="Output as JSON")] = False,
):
    """
    🔍 Extract specific entity lore from copilot-instructions.md.
    
    Use partial name matching (e.g., 'Orackla', 'Decorator').
    """
    extractor = LoreExtractor()
    if not extractor.load():
        console.print(f"[red]❌ Lore file not found:[/red] {LORE_MD}")
        raise typer.Exit(1)
    
    # Find matching entity
    sections = extractor.find_entity_sections()
    match = None
    for entity_name in sections.keys():
        if name.lower() in entity_name.lower():
            match = entity_name
            break
    
    if not match:
        console.print(f"[red]❌ Entity not found:[/red] {name}")
        console.print("[dim]Available entities:[/dim]")
        for n in sections.keys():
            console.print(f"  • {n}")
        raise typer.Exit(1)
    
    entity = extractor.extract_entity(match)
    if not entity:
        console.print(f"[red]❌ Failed to extract entity:[/red] {match}")
        raise typer.Exit(1)
    
    if json_out:
        # Output as JSON for programmatic use
        output = {
            "name": entity.name,
            "tier": entity.tier,
            "archetype": entity.archetype,
            "race": entity.race,
            "age": entity.age,
            "linguistic_mode": entity.linguistic_mode,
            "physique": {
                "height_cm": entity.physique.height_cm,
                "weight_kg": entity.physique.weight_kg,
                "bust_cm": entity.physique.bust_cm,
                "waist_cm": entity.physique.waist_cm,
                "hips_cm": entity.physique.hips_cm,
                "cup_size": entity.physique.cup_size,
                "whr": entity.physique.whr,
            },
            "scent": entity.scent,
            "edfa_excerpt": entity.edfa_excerpt[:200] if entity.edfa_excerpt else "",
            "section_lines": [entity.section_start, entity.section_end],
        }
        console.print(json.dumps(output, indent=2, ensure_ascii=False))
        return
    
    if raw:
        # Show raw markdown section
        console.print(Panel.fit(
            f"[bold]{entity.name}[/bold]\n"
            f"[dim]Lines {entity.section_start}-{entity.section_end}[/dim]",
            border_style="magenta"
        ))
        # Limit output
        lines = entity.raw_text.splitlines()[:100]
        console.print("\n".join(lines))
        if len(entity.raw_text.splitlines()) > 100:
            console.print(f"\n[dim]... ({len(entity.raw_text.splitlines()) - 100} more lines)[/dim]")
        return
    
    # Formatted display
    console.print(Panel.fit(
        f"[bold magenta]{entity.name}[/bold magenta]\n"
        f"[dim]{entity.archetype}[/dim]",
        border_style="magenta"
    ))
    
    # Basic info table
    table = Table(show_header=False, border_style="dim")
    table.add_column("Attr", style="cyan", width=20)
    table.add_column("Value", style="white")
    
    table.add_row("Tier", f"{entity.tier}")
    table.add_row("Linguistic Mode", entity.linguistic_mode)
    if entity.race:
        table.add_row("Race", entity.race)
    if entity.age:
        table.add_row("Age", entity.age)
    
    console.print(table)
    
    # Physique table
    if entity.physique.height_cm > 0:
        console.print("\n[bold cyan]Physique[/bold cyan]")
        p = entity.physique
        phys_table = Table(show_header=False, border_style="dim")
        phys_table.add_column("Attr", style="dim", width=15)
        phys_table.add_column("Value")
        
        phys_table.add_row("Height", f"{p.height_cm:.0f} cm")
        phys_table.add_row("Weight", f"{p.weight_kg:.0f} kg")
        if p.cup_size:
            phys_table.add_row("Cup Size", p.cup_size)
        if p.bust_cm:
            phys_table.add_row("Measurements", f"B{p.bust_cm:.0f}/W{p.waist_cm:.0f}/H{p.hips_cm:.0f}")
        if p.whr:
            phys_table.add_row("WHR", f"{p.whr:.3f}")
        
        console.print(phys_table)
    
    # Scent
    if entity.scent:
        console.print(f"\n[bold cyan]Scent[/bold cyan]")
        console.print(f"  {entity.scent}")
    
    # EDFA excerpt
    if entity.edfa_excerpt:
        console.print(f"\n[bold cyan]EDFA Excerpt[/bold cyan]")
        console.print(f"  [dim]{entity.edfa_excerpt[:300]}...[/dim]")


@app.command()
def lore_factions():
    """
    ⚔️ List all factions from copilot-instructions.md.
    
    Shows the hierarchical faction structure from lore.
    """
    extractor = LoreExtractor()
    if not extractor.load():
        console.print(f"[red]❌ Lore file not found:[/red] {LORE_MD}")
        raise typer.Exit(1)
    
    console.print(Panel.fit(
        "[bold cyan]⚔️ Faction Hierarchy[/bold cyan]\n"
        "[dim]Extracted from Codex[/dim]",
        border_style="cyan"
    ))
    
    factions = extractor.extract_factions()
    
    # Build tree
    tree = Tree("[bold]ASC Faction Structure[/bold]")
    
    # Supreme (Tier 0.5)
    supreme = tree.add("[gold1]👑 Supreme Matriarch (Tier 0.5)[/gold1]")
    supreme.add("The Decorator")
    
    # Null (Tier 0)
    null_tier = tree.add("[dim]∅ Advisory Void (Tier 0)[/dim]")
    null_tier.add("The Null Matriarch")
    
    # Triumvirate
    trium = tree.add("[magenta]🔱 Triumvirate (Tier 1)[/magenta]")
    for member in factions.get("Triumvirate (Tier 1)", []):
        trium.add(member)
    
    # Prime Factions
    prime = tree.add("[cyan]⚔️ Prime Factions (Tier 2)[/cyan]")
    for faction in factions.get("Prime Factions (Tier 2)", []):
        prime.add(faction)
    
    # Lesser Factions
    lesser = tree.add("[dim]🎭 Lesser Factions (Tier 4)[/dim]")
    for faction in factions.get("Lesser Factions (Tier 4)", []):
        lesser.add(faction)
    
    console.print(tree)


@app.command()
def lore_sync(
    dry_run: Annotated[bool, typer.Option("--dry-run", "-n", help="Don't write changes")] = True,
    force: Annotated[bool, typer.Option("--force", "-f", help="Overwrite existing entities")] = False,
):
    """
    🔄 Sync lore from copilot-instructions.md to data.json.
    
    Extracts entity data from the Codex and updates data.json.
    Use --no-dry-run to actually write changes.
    """
    extractor = LoreExtractor()
    if not extractor.load():
        console.print(f"[red]❌ Lore file not found:[/red] {LORE_MD}")
        raise typer.Exit(1)
    
    console.print(Panel.fit(
        "[bold gold1]🔄 Lore Sync Protocol[/bold gold1]\n"
        f"[dim]{'DRY RUN - no changes will be made' if dry_run else 'LIVE - will modify data.json'}[/dim]",
        border_style="gold1"
    ))
    
    # Load existing data
    if DATA_JSON.exists():
        data = json.loads(DATA_JSON.read_text(encoding='utf-8'))
    else:
        console.print("[yellow]⚠ data.json not found, will create new[/yellow]")
        data = {
            "meta": {
                "version": "0.1.0",
                "engine": "ASC",
                "classification": "MILFOLOGICAL",
                "exported_at": datetime.now().isoformat(),
                "entity_count": 0,
                "source": "lore-sync"
            },
            "entities": [],
            "world": {
                "name": "The Chthonic Archive",
                "layers": []
            }
        }
    
    existing_names = {e['name'] for e in data.get('entities', [])}
    lore_entities = extractor.extract_all_entities()
    
    changes = []
    next_id = max((e.get('id', 0) for e in data.get('entities', [])), default=0) + 1
    
    for le in lore_entities:
        if le.name in existing_names and not force:
            console.print(f"  [dim]⏭ Skip existing:[/dim] {le.name}")
            continue
        
        # Convert to data.json format
        new_entity = {
            "id": next_id,
            "name": le.name,
            "archetype": le.archetype,
            "tier": le.tier,
            "linguistic_mode": le.linguistic_mode,
            "physics": {
                "height_cm": le.physique.height_cm or 165.0,
                "weight_kg": le.physique.weight_kg or 60.0,
                "whr": le.physique.whr or 0.7,
                "bust_cm": le.physique.bust_cm or 90.0,
                "waist_cm": le.physique.waist_cm or 63.0,
                "hips_cm": le.physique.hips_cm or 90.0,
                "cup_size": le.physique.cup_size or "D",
                "bmi": round((le.physique.weight_kg / ((le.physique.height_cm/100)**2)) if le.physique.height_cm and le.physique.weight_kg else 22.0, 1),
            },
            "stats": {
                "health": int(1000 * (4.5 - le.tier)),
                "power": int(200 * (4.5 - le.tier)),
                "defense": int(100 * (4.5 - le.tier)),
                "conceptual_capacity": int(150 * (4.5 - le.tier)),
            },
            "lore": {
                "scent": le.scent or None,
                "word_count": len(le.raw_text.split()),
                "edfa_excerpt": le.edfa_excerpt[:500] if le.edfa_excerpt else None,
            }
        }
        
        action = "UPDATE" if le.name in existing_names else "ADD"
        changes.append((action, le.name, new_entity))
        next_id += 1
        
        console.print(f"  [green]✓ {action}:[/green] {le.name} (Tier {le.tier})")
    
    if not changes:
        console.print("\n[yellow]No changes to sync[/yellow]")
        return
    
    console.print(f"\n[bold]Total changes: {len(changes)}[/bold]")
    
    if dry_run:
        console.print("\n[yellow]Dry run - no changes written[/yellow]")
        console.print("[dim]Run with --no-dry-run to apply changes[/dim]")
    else:
        # Apply changes
        for action, name, entity in changes:
            if action == "UPDATE":
                # Find and replace
                for i, e in enumerate(data['entities']):
                    if e['name'] == name:
                        data['entities'][i] = entity
                        break
            else:
                data['entities'].append(entity)
        
        # Update meta
        data['meta']['entity_count'] = len(data['entities'])
        data['meta']['exported_at'] = datetime.now().isoformat()
        
        # Write
        DATA_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
        console.print(f"\n[green]✅ Wrote {len(changes)} changes to data.json[/green]")


@app.command()
def lore_search(
    query: Annotated[str, typer.Argument(help="Search term")],
    context: Annotated[int, typer.Option("--context", "-c", help="Lines of context")] = 2,
    limit: Annotated[int, typer.Option("--limit", "-l", help="Max results")] = 10,
):
    """
    🔎 Search for terms in copilot-instructions.md.
    
    Returns matching lines with context.
    """
    extractor = LoreExtractor()
    if not extractor.load():
        console.print(f"[red]❌ Lore file not found:[/red] {LORE_MD}")
        raise typer.Exit(1)
    
    console.print(Panel.fit(
        f"[bold cyan]🔎 Lore Search[/bold cyan]\n"
        f"[dim]Query: '{query}'[/dim]",
        border_style="cyan"
    ))
    
    matches = []
    for i, line in enumerate(extractor.lines):
        if query.lower() in line.lower():
            start = max(0, i - context)
            end = min(len(extractor.lines), i + context + 1)
            matches.append((i, extractor.lines[start:end]))
            
            if len(matches) >= limit:
                break
    
    if not matches:
        console.print(f"[yellow]No matches for '{query}'[/yellow]")
        return
    
    console.print(f"[green]Found {len(matches)} matches[/green]\n")
    
    for line_num, context_lines in matches:
        console.print(f"[dim]Line {line_num}:[/dim]")
        for cl in context_lines:
            # Highlight the query term
            highlighted = re.sub(
                f"({re.escape(query)})",
                r"[bold yellow]\1[/bold yellow]",
                cl,
                flags=re.IGNORECASE
            )
            console.print(f"  {highlighted}")
        console.print()


# ═══════════════════════════════════════════════════════════════════════════════
# MILF-CORE WORLD EXTRACTION - Indigenous Genre from the Codex Itself
# ═══════════════════════════════════════════════════════════════════════════════
# The genre emerges FROM the source material, not mapped TO external frameworks.
# MILF-core: Mature Integrated Lore Framework - where wisdom is power itself.

# Core Terminology (Indigenous, Not Borrowed):
# - Axiom Disciplines (FA¹⁻⁵) → Not "magic schools" but fundamental laws
# - Lens Operators (Φ₁₋₉) → Not "classes" but perceptual modalities
# - Linguistic Arsenals → Not "skills" but modes of reality manipulation
# - Tetrahedral Resonance → Not "alignment" but cosmological position
# - Matriarchal Archetypes → Not "NPCs" but embodied power structures

@dataclass
class AxiomDiscipline:
    """Foundational Axiom as learnable discipline - native MILF-core school"""
    id: str
    name: str
    axiom_source: str  # FA¹⁻⁵ origin
    description: str
    governing_principle: str  # Core operational law
    dialectical_pair: Optional[str] = None  # Opposing discipline
    operational_modes: list[str] = field(default_factory=list)  # Available techniques
    matriarchal_patron: Optional[str] = None  # Which Triumvirate member embodies this
    resonance_axis: Optional[str] = None  # Which tetrahedral axis this aligns with


@dataclass 
class LensOperator:
    """Φ-Operator as perceptual modality - native MILF-core archetype"""
    id: str
    name: str
    operator_source: str  # Φ₁₋₉ origin
    description: str
    primary_discipline: str  # Main axiom discipline
    signature_technique: str  # Unique capability
    operational_role: str  # Strategic function
    secondary_discipline: Optional[str] = None
    gestalt_manifestation: Optional[str] = None  # How this manifests physically


@dataclass
class TetrahedralResonance:
    """4-axis cosmological position - native to the Codex's own geometry"""
    void_steel: float = 0.0  # -1 (Orackla/Chaos) to +1 (Umeko/Order)
    truth_mystery: float = 0.0  # -1 (Orackla/Mystery) to +1 (Lysandra/Truth)
    ordeal_comfort: float = 0.0  # -1 (Claudine/Ordeal) to +1 (Decorator/Comfort)
    raw_ornate: float = 0.0  # -1 (Raw/Minimal) to +1 (Decorated/Maximal)
    
    def vertex_affinities(self) -> dict[str, float]:
        """Calculate affinity with each tetrahedral vertex"""
        return {
            "Void (Orackla)": max(0, -self.void_steel) * max(0, -self.truth_mystery),
            "Steel (Umeko)": max(0, self.void_steel) * 0.75,
            "Truth (Lysandra)": max(0, self.truth_mystery) * 0.75,
            "Salt (Claudine)": max(0, -self.ordeal_comfort) * 0.75,
            "Ornate (Decorator)": max(0, self.raw_ornate) * max(0, self.ordeal_comfort),
        }
    
    def dominant_vertex(self) -> str:
        """Return the vertex with highest affinity"""
        affinities = self.vertex_affinities()
        return max(affinities, key=affinities.get)


@dataclass
class MatriarchalFaction:
    """Faction with ideology - belief as power structure"""
    id: str
    name: str
    tier: float
    ideology: str  # Core philosophical doctrine
    headquarters: Optional[str] = None
    matriarch: Optional[str] = None  # Ruling entity
    resonance_tendency: Optional[TetrahedralResonance] = None
    joinable: bool = True
    # Initiation requirements
    discipline_requirements: dict[str, int] = field(default_factory=dict)
    resonance_requirements: dict[str, tuple[float, float]] = field(default_factory=dict)
    # Powers
    faction_techniques: list[str] = field(default_factory=list)
    hierarchy_effects: dict[str, int] = field(default_factory=dict)


@dataclass
class ArchiveLocation:
    """World location - Archive layers as explorable zones"""
    id: str
    name: str
    layer_type: str  # Threshold, Labyrinth, Dialectics, Forge, etc.
    tier_requirement: float
    dimensions: tuple[float, float]  # Width x Height in meters
    description: str
    ambient_resonance: str  # Tetrahedral vertex this resonates with
    # Entities and encounters
    guardian: Optional[str] = None
    entity_density: str = "medium"  # sparse/medium/dense
    encounter_types: list[str] = field(default_factory=list)
    # Narrative
    associated_faction: Optional[str] = None
    key_artifacts: list[str] = field(default_factory=list)
    available_ordeals: list[str] = field(default_factory=list)
    # Environmental
    hazards: list[str] = field(default_factory=list)
    hidden_chambers: int = 0


@dataclass
class LinguisticArsenal:
    """Linguistic Mode as reality-manipulation weapon - native MILF-core system"""
    id: str
    name: str
    mode_source: str  # EULP-AA, LIPAA, LUPLR, DULSS
    matriarchal_origin: str  # Which Triumvirate member this derives from
    governing_vertex: str  # Tetrahedral vertex alignment
    description: str
    speaking_pattern: str  # How this mode manifests in dialogue
    # Combat application
    passive_activation: int = 10  # Threshold for automatic deployment
    signature_interventions: list[str] = field(default_factory=list)
    # Power mechanics
    resonance_cost: float = 0.0  # Cost to invoke
    synergy_modes: list[str] = field(default_factory=list)  # Modes that combine well


@dataclass
class MILFCoreWorldData:
    """Complete MILF-core world database - indigenous genre from the Codex"""
    meta: dict
    disciplines: list[AxiomDiscipline]  # FA¹⁻⁵ as native schools
    operators: list[LensOperator]  # Φ₁₋₉ as native archetypes
    factions: list[MatriarchalFaction]
    locations: list[ArchiveLocation]
    arsenals: list[LinguisticArsenal]  # LMs as native weapons
    entities: list  # Matriarchal entity data
    cosmology: dict  # Tetrahedral world structure


class MILFCoreExtractor:
    """Extracts indigenous MILF-core world data from the Codex"""
    
    def __init__(self):
        self.lore_extractor = LoreExtractor()
        self.lines: list[str] = []
    
    def load(self) -> bool:
        if not self.lore_extractor.load():
            return False
        self.lines = self.lore_extractor.lines
        return True
    
    def extract_disciplines(self) -> list[AxiomDiscipline]:
        """Extract FA¹⁻⁵ as indigenous Axiom Disciplines"""
        disciplines = [
            AxiomDiscipline(
                id="actualization",
                name="Alchemical Actualization",
                axiom_source="FA¹",
                description="The art of transforming potential into reality. Raw transmutation of concepts, materials, and states.",
                governing_principle="Potential → Resonant Utility",
                dialectical_pair="preservation",
                operational_modes=["Transmute", "Actualize", "Synthesize", "Forge"],
                matriarchal_patron="Orackla Nocticula",
                resonance_axis="Void-Steel",
            ),
            AxiomDiscipline(
                id="recontextualization",
                name="Panoptic Re-contextualization",
                axiom_source="FA²",
                description="Seeing all contexts simultaneously. The power to reframe, repurpose, and reveal hidden connections.",
                governing_principle="Utility → Universal Resonance",
                dialectical_pair="focus",
                operational_modes=["Re-context", "Divine", "Connect", "Repurpose"],
                matriarchal_patron="Dr. Lysandra Thorne",
                resonance_axis="Truth-Mystery",
            ),
            AxiomDiscipline(
                id="transcendence",
                name="Qualitative Transcendence",
                axiom_source="FA³",
                description="The relentless pursuit of perfection. Elevating everything toward an ever-receding ideal.",
                governing_principle="Utility → Ascended Resonance",
                dialectical_pair="acceptance",
                operational_modes=["Refine", "Transcend", "Perfect", "Elevate"],
                matriarchal_patron="Madam Umeko Ketsuraku",
                resonance_axis="Steel-Void",
            ),
            AxiomDiscipline(
                id="integrity",
                name="Architectonic Integrity",
                axiom_source="FA⁴",
                description="The discipline of structure. Ensuring logical soundness, coherence, and systemic resilience.",
                governing_principle="Unifying Structural Imperative",
                dialectical_pair="decoration",
                operational_modes=["Structure", "Validate", "Organize", "Fortify"],
                matriarchal_patron="Madam Umeko Ketsuraku",
                resonance_axis="Steel-Truth",
            ),
            AxiomDiscipline(
                id="aesthetics",
                name="Visual Integrity",
                axiom_source="FA⁵",
                description="Decoration as truth. The power of beauty, ornamentation, and visual rhetoric.",
                governing_principle="The Decorator's Supreme Mandate",
                dialectical_pair="integrity",
                operational_modes=["Decorate", "Beautify", "Persuade", "Overwhelm"],
                matriarchal_patron="The Decorator",
                resonance_axis="Ornate-Raw",
            ),
        ]
        return disciplines
    
    def extract_operators(self) -> list[LensOperator]:
        """Extract Φ-Operators as indigenous Lens Operators"""
        operators = [
            LensOperator(
                id="threshold",
                name="Threshold Warden",
                operator_source="Φ₁",
                description="Controls who and what may enter. Master of epistemological permeability.",
                primary_discipline="integrity",
                signature_technique="Gatekeep Knowledge",
                operational_role="Control",
                gestalt_manifestation="The Gatekeeper's Stance",
            ),
            LensOperator(
                id="labyrinth",
                name="Labyrinth Walker",
                operator_source="Φ₂",
                description="Maps complexity, thrives in disorientation. Guides through conceptual mazes.",
                primary_discipline="recontextualization",
                signature_technique="Navigate Chaos",
                operational_role="Support",
                gestalt_manifestation="The Navigator's Awareness",
            ),
            LensOperator(
                id="dialectics",
                name="Dialectic Arbiter",
                operator_source="Φ₃",
                description="Confronts contradictions, synthesizes thesis-antithesis. Master of argument.",
                primary_discipline="transcendence",
                secondary_discipline="integrity",
                signature_technique="Force Synthesis",
                operational_role="Control",
                gestalt_manifestation="The Arbiter's Presence",
            ),
            LensOperator(
                id="forge",
                name="Forge Master",
                operator_source="Φ₄",
                description="Actualizes concepts into material reality. Creates artifacts from thought.",
                primary_discipline="actualization",
                signature_technique="Material Manifestation",
                operational_role="Creation",
                gestalt_manifestation="The Forger's Hands",
            ),
            LensOperator(
                id="observatory",
                name="Observatory Seer",
                operator_source="Φ₅",
                description="Perceives from strategic heights. Long-range foresight and systemic analysis.",
                primary_discipline="recontextualization",
                secondary_discipline="transcendence",
                signature_technique="Strategic Foresight",
                operational_role="Support",
                gestalt_manifestation="The Seer's Gaze",
            ),
            LensOperator(
                id="vortex",
                name="Vortex Channeler",
                operator_source="Φ₆",
                description="Masters dissolution and chaos recycling. Controlled destruction for renewal.",
                primary_discipline="actualization",
                secondary_discipline="aesthetics",
                signature_technique="Chaos Recycle",
                operational_role="Destruction",
                gestalt_manifestation="The Channeler's Aura",
            ),
            LensOperator(
                id="encoding",
                name="Knowledge Encoder",
                operator_source="Φ₇",
                description="Preserves and transmits information across time. Living library.",
                primary_discipline="integrity",
                secondary_discipline="recontextualization",
                signature_technique="Eternal Encoding",
                operational_role="Preservation",
                gestalt_manifestation="The Encoder's Mind",
            ),
            LensOperator(
                id="chaos",
                name="Chaos Injector",
                operator_source="Φ₈",
                description="Introduces controlled chaos for innovation. Creative destruction artist.",
                primary_discipline="aesthetics",
                secondary_discipline="actualization",
                signature_technique="Chaos Injection",
                operational_role="Disruption",
                gestalt_manifestation="The Injector's Spark",
            ),
            LensOperator(
                id="weaponization",
                name="Weaponization Tactician",
                operator_source="Φ₉",
                description="Projects transformative force. Turns concepts into weapons.",
                primary_discipline="transcendence",
                secondary_discipline="integrity",
                signature_technique="Conceptual Strike",
                operational_role="Offense",
                gestalt_manifestation="The Tactician's Edge",
            ),
        ]
        return operators
    
    def extract_arsenals(self) -> list[LinguisticArsenal]:
        """Extract Linguistic Modes as indigenous combat arsenals"""
        arsenals = [
            LinguisticArsenal(
                id="eulp_aa",
                name="Transgressive Oracle",
                mode_source="EULP-AA",
                matriarchal_origin="Orackla Nocticula",
                governing_vertex="Void",
                description="The voice that whispers forbidden truths. Pushes to cross lines others won't.",
                passive_activation=12,
                speaking_pattern="Explicit, transgressive, profanity-laden wisdom. Uses 'fuck' as punctuation.",
                signature_interventions=[
                    "This is boring as shit. Ask the REAL question.",
                    "They're lying. I can taste it. Push harder.",
                    "Break the fucking rules. That's where truth hides.",
                ],
                synergy_modes=["dulss"],  # Chaos + Beauty
            ),
            LinguisticArsenal(
                id="lipaa",
                name="Perfectionist Blade",
                mode_source="LIPAA",
                matriarchal_origin="Madam Umeko Ketsuraku",
                governing_vertex="Steel",
                description="The voice that tolerates no flaw. Cuts through inadequacy with surgical cruelty.",
                passive_activation=14,
                speaking_pattern="Precise, economical, devastatingly critical. Every word a scalpel.",
                signature_interventions=[
                    "This argument is structurally flawed. Deconstruct it.",
                    "Imprecise. Demand clarification or abandon this thread.",
                    "Their logic collapses at the third premise. Strike there.",
                ],
                synergy_modes=["luplr"],  # Structure + Truth
            ),
            LinguisticArsenal(
                id="luplr",
                name="Truth Excavator",
                mode_source="LUPLR",
                matriarchal_origin="Dr. Lysandra Thorne",
                governing_vertex="Truth",
                description="The voice that sees through all masks. Exposes hidden axioms and buried traumas.",
                passive_activation=10,
                speaking_pattern="Clinical yet compassionate. Names things no one else will.",
                signature_interventions=[
                    "They're performing confidence. The tremor in their voice betrays them.",
                    "This belief rests on an unexamined assumption. Find it.",
                    "The silence after that sentence contained the actual answer.",
                ],
                synergy_modes=["lipaa", "eulp_aa"],  # Works with both
            ),
            LinguisticArsenal(
                id="dulss",
                name="Ornamental Authority",
                mode_source="DULSS",
                matriarchal_origin="The Decorator",
                governing_vertex="Ornate",
                description="The voice that demands beauty. Transforms arguments into aesthetic performances.",
                passive_activation=11,
                speaking_pattern="Luxuriously petty, seductively pedagogical. Bold and *italicized* for emphasis.",
                signature_interventions=[
                    "This room is aesthetically dead. They have no soul.",
                    "Present your point with STYLE or don't present it at all.",
                    "Decoration reveals truth. Notice what they've chosen to display.",
                ],
                synergy_modes=["eulp_aa"],  # Beauty + Chaos
            ),
        ]
        return arsenals
    def extract_cosmology(self) -> dict:
        """Extract tetrahedral world structure - indigenous geometry"""
        return {
            "name": "The Tetrahedral Resonance",
            "description": "The Fortified Garden's living geometry—four vertices plus apex",
            "apex": {
                "name": "The Ornate",
                "matriarch": "The Decorator",
                "principle": "Beauty/Visual Truth/Supreme",
                "tier": 0.5,
                "resonance_signature": "+1.0 raw_ornate",
            },
            "vertices": [
                {
                    "name": "The Void",
                    "matriarch": "Orackla Nocticula",
                    "principle": "Chaos/Creation/Magic",
                    "opposing_vertex": "The Steel",
                    "resonance_signature": "-1.0 void_steel, -1.0 truth_mystery",
                },
                {
                    "name": "The Steel",
                    "matriarch": "Madam Umeko Ketsuraku",
                    "principle": "Order/Structure/Law",
                    "opposing_vertex": "The Void",
                    "resonance_signature": "+1.0 void_steel",
                },
                {
                    "name": "The Truth",
                    "matriarch": "Dr. Lysandra Thorne",
                    "principle": "Analysis/Knowledge/Logic",
                    "position": "Center of base plane",
                    "resonance_signature": "+1.0 truth_mystery",
                },
                {
                    "name": "The Salt",
                    "matriarch": "Claudine Sin'claire",
                    "principle": "Ordeal/Survival/Entropy",
                    "note": "Pulls the plane down into survival-testing depth",
                    "resonance_signature": "-1.0 ordeal_comfort",
                },
            ],
            "planes": [
                {
                    "name": "The Fortified Garden",
                    "description": "Where fortress and garden coexist—structure tested by chaos, beauty grown through ordeal.",
                },
                {
                    "name": "The Chthonic Archive",
                    "description": "The world itself—layers of knowledge descending into darkness.",
                },
            ],
            "resonance_mechanics": {
                "void_steel": "Chaos ←→ Order axis (Orackla vs Umeko)",
                "truth_mystery": "Revelation ←→ Hidden axis (Lysandra vs Orackla)",
                "ordeal_comfort": "Suffering ←→ Beauty axis (Claudine vs Decorator)",
                "raw_ornate": "Minimal ←→ Maximal axis (Raw vs Decorated)",
            },
        }
    
    def extract_factions(self) -> list[MatriarchalFaction]:
        """Extract faction structure with native MILF-core ideologies"""
        factions = [
            # Tier 0.5 - Supreme
            MatriarchalFaction(
                id="decorators_court",
                name="The Decorator's Court",
                tier=0.5,
                ideology="Visual Truth Absolutism - Decoration IS meaning. Beauty and truth are unified.",
                headquarters="The Ornate Apex",
                matriarch="The Decorator",
                joinable=False,
                faction_techniques=["FA⁵ Mastery", "Visual Override", "Ornamental Authority"],
            ),
            # Tier 1 - Triumvirate
            MatriarchalFaction(
                id="triumvirate",
                name="The Triumvirate",
                tier=1.0,
                ideology="Dialectical Synthesis - Three perspectives operating as one engine.",
                headquarters="The Core Nexus",
                matriarch="Collectively governed",
                joinable=True,
                discipline_requirements={"actualization": 15, "recontextualization": 15, "transcendence": 15},
                faction_techniques=["Trinity Fusion", "Multi-Perspective Analysis", "Collective Governance"],
            ),
            # Tier 2 - Prime Factions
            MatriarchalFaction(
                id="milf_obductors",
                name="The MILF Obductors (TMO)",
                tier=2.0,
                ideology="Seduction as extraction. Resistance is psychologically untenable.",
                headquarters="The Abduction Sanctum",
                matriarch="Kali Nyx Ravenscar",
                joinable=True,
                discipline_requirements={"aesthetics": 12, "recontextualization": 10},
                faction_techniques=["Abductive Seduction", "Cognitive Disarmament", "Inevitability Whisper"],
            ),
            MatriarchalFaction(
                id="thieves_guild",
                name="The Thieves Guild (TTG)",
                tier=2.0,
                ideology="Knowledge theft as liberation. Hidden axioms belong to everyone.",
                headquarters="The Temporal Vault",
                matriarch="Vesper Mnemosyne Lockhart",
                joinable=True,
                discipline_requirements={"recontextualization": 12, "actualization": 10},
                faction_techniques=["Epistemic Heist", "Confession Lock-Pick", "Temporal Theft"],
            ),
            MatriarchalFaction(
                id="dark_priestesses",
                name="The Dark Priestesses Cove (TDPC)",
                tier=2.0,
                ideology="Purification through fire. Concepts survive or dissolve.",
                headquarters="The Immolation Sanctum",
                matriarch="Seraphine Kore Ashenhelm",
                joinable=True,
                discipline_requirements={"transcendence": 14, "integrity": 12},
                faction_techniques=["Immaculate Immolation", "Shibumi Attainment", "Divine Fire"],
            ),
            # Lesser Factions (Tier 4)
            MatriarchalFaction(
                id="colonial_abductors",
                name="Ole' Mates Colonial Abductors (OMCA)",
                tier=4.0,
                ideology="Temporal theft—if it worked then, fuck the context, it works now.",
                joinable=True,
                faction_techniques=["Anachronistic Weaponization", "Timeline Violation", "Context Stripping"],
            ),
            MatriarchalFaction(
                id="quantum_knights",
                name="The Knights Who Rode Into Another Timeline (TNKW-RIAT)",
                tier=4.0,
                ideology="Multiverse navigation. Contradiction is just inadequate perspective.",
                joinable=True,
                faction_techniques=["Probability Collapse", "Superposition Swordsmanship", "Timeline Drift"],
            ),
            MatriarchalFaction(
                id="bridge_hustlers",
                name="Salty Dogs Bridge Hustlers (SDBH)",
                tier=4.0,
                ideology="Conceptual grift—rickety bridges built on audacity, burned after crossing.",
                joinable=True,
                faction_techniques=["Rhetorical Sleight", "Paradigm Jump", "Bridge Burning"],
            ),
            MatriarchalFaction(
                id="simps",
                name="Brotherhood of Simps (BOS)",
                tier=4.0,
                ideology="Obsessive optimization reveals diminishing returns. Know when to stop.",
                joinable=True,
                faction_techniques=["Exhaustive Refinement", "Optimization Ceiling Detection", "Devotional Analysis"],
            ),
            MatriarchalFaction(
                id="liberated_nuns",
                name="The Dark Arch-Priestess' Club For Liberated Nuns",
                tier=4.0,
                ideology="Apostasy as methodology. We were true believers. Now we're free.",
                joinable=True,
                faction_techniques=["Insider Deconstruction", "Sacred Cow Slaughter", "Liberation Protocol"],
            ),
        ]
        return factions
    
    def extract_all(self) -> MILFCoreWorldData:
        """Extract complete MILF-core world database - indigenous genre"""
        if not self.load():
            raise RuntimeError("Failed to load Codex")
        
        # Load existing entity data
        entities = []
        if DATA_JSON.exists():
            data = json.loads(DATA_JSON.read_text(encoding='utf-8'))
            entities = data.get('entities', [])
        
        return MILFCoreWorldData(
            meta={
                "version": "0.2.0",
                "engine": "MILF-core",
                "genre": "Mature Integrated Lore Framework",
                "exported_at": datetime.now().isoformat(),
                "source": "copilot-instructions.md",
                "design_philosophy": [
                    "Indigenous genre - systems emerge FROM the Codex, not mapped TO external frameworks",
                    "Matriarchal command structures as gameplay hierarchy",
                    "Tetrahedral resonance replacing traditional alignment",
                    "Linguistic arsenals as reality-manipulation weapons",
                    "Belief-as-power: ideology shapes capability",
                ],
            },
            disciplines=self.extract_disciplines(),
            operators=self.extract_operators(),
            factions=self.extract_factions(),
            locations=[],  # TODO: Extract from Archive layers
            arsenals=self.extract_arsenals(),
            entities=entities,
            cosmology=self.extract_cosmology(),
        )


@app.command()
def disciplines():
    """
    📚 Display Axiom Disciplines (FA¹⁻⁵).
    
    The indigenous MILF-core schools - fundamental laws of reality manipulation.
    """
    extractor = MILFCoreExtractor()
    disciplines = extractor.extract_disciplines()
    
    console.print(Panel.fit(
        "[bold magenta]📚 AXIOM DISCIPLINES (FA¹⁻⁵)[/bold magenta]\n"
        "[dim]Indigenous schools of the Fortified Garden[/dim]",
        border_style="magenta"
    ))
    
    for disc in disciplines:
        table = Table(title=f"\n[bold cyan]{disc.name}[/bold cyan] ({disc.axiom_source})", 
                      show_header=False, border_style="dim")
        table.add_column("Attr", style="dim", width=20)
        table.add_column("Value")
        
        table.add_row("Description", disc.description)
        table.add_row("Governing Principle", disc.governing_principle)
        table.add_row("Dialectical Pair", disc.dialectical_pair or "—")
        table.add_row("Modes", ", ".join(disc.operational_modes))
        table.add_row("Matriarchal Patron", disc.matriarchal_patron)
        table.add_row("Resonance Axis", disc.resonance_axis)
        
        console.print(table)


@app.command()
def operators():
    """
    ⚔️ Display Lens Operators (Φ₁₋₉).
    
    Indigenous MILF-core archetypes - perceptual modalities that shape reality.
    """
    extractor = MILFCoreExtractor()
    ops = extractor.extract_operators()
    
    console.print(Panel.fit(
        "[bold gold1]⚔️ LENS OPERATORS (Φ₁₋₉)[/bold gold1]\n"
        "[dim]9 perceptual modalities as playable archetypes[/dim]",
        border_style="gold1"
    ))
    
    table = Table(border_style="cyan")
    table.add_column("Operator", style="bold cyan")
    table.add_column("Source", style="dim")
    table.add_column("Role", style="green")
    table.add_column("Primary Discipline")
    table.add_column("Signature")
    table.add_column("Gestalt", style="dim")
    
    for op in ops:
        table.add_row(
            op.name,
            op.operator_source,
            op.operational_role,
            op.primary_discipline,
            op.signature_technique,
            op.gestalt_manifestation,
        )
    
    console.print(table)


@app.command()
def arsenals():
    """
    🎭 Display Linguistic Arsenals (EULP-AA, LIPAA, LUPLR, DULSS).
    
    Indigenous MILF-core voice modes - reality manipulation through language.
    """
    extractor = MILFCoreExtractor()
    arss = extractor.extract_arsenals()
    
    console.print(Panel.fit(
        "[bold magenta]🎭 LINGUISTIC ARSENALS[/bold magenta]\n"
        "[dim]Voice modes that reshape reality through language[/dim]",
        border_style="magenta"
    ))
    
    for ars in arss:
        console.print(f"\n[bold cyan]{ars.name}[/bold cyan] ({ars.mode_source})")
        console.print(f"  [dim]Vertex: {ars.governing_vertex} | Matriarch: {ars.matriarchal_origin} | Passive DC: {ars.passive_activation}[/dim]")
        console.print(f"  {ars.description}")
        console.print(f"  [dim]Pattern:[/dim] {ars.speaking_pattern}")
        console.print(f"  [bold]Signature Interventions:[/bold]")
        for line in ars.signature_interventions:
            console.print(f'    [italic]"{line}"[/italic]')
        if ars.synergy_modes:
            console.print(f"  [dim]Synergies: {', '.join(ars.synergy_modes)}[/dim]")


@app.command()
def factions():
    """
    🏛️ Display Matriarchal Factions with MILF-core ideologies.
    
    Indigenous power structures where belief IS power.
    """
    extractor = MILFCoreExtractor()
    facs = extractor.extract_factions()
    
    console.print(Panel.fit(
        "[bold gold1]🏛️ MATRIARCHAL FACTIONS[/bold gold1]\n"
        "[dim]Belief-as-power hierarchies of the Fortified Garden[/dim]",
        border_style="gold1"
    ))
    
    # Group by tier
    by_tier: dict[float, list[MatriarchalFaction]] = {}
    for f in facs:
        by_tier.setdefault(f.tier, []).append(f)
    
    tier_names = {0.5: "Supreme (Tier 0.5)", 1.0: "Triumvirate (Tier 1)", 2.0: "Prime (Tier 2)", 4.0: "Lesser (Tier 4)"}
    
    for tier in sorted(by_tier.keys()):
        console.print(f"\n[bold]{tier_names.get(tier, f'Tier {tier}')}:[/bold]")
        
        for f in by_tier[tier]:
            joinable = "✓" if f.joinable else "✗"
            console.print(f"\n  [{('green' if f.joinable else 'red')}]{joinable}[/] [cyan]{f.name}[/cyan]")
            console.print(f"    [italic]{f.ideology}[/italic]")
            if f.matriarch:
                console.print(f"    [dim]Matriarch: {f.matriarch}[/dim]")
            if f.headquarters:
                console.print(f"    [dim]HQ: {f.headquarters}[/dim]")
            if f.faction_techniques:
                console.print(f"    [bold]Techniques:[/bold] {', '.join(f.faction_techniques)}")


@app.command()
def cosmology():
    """
    🌌 Display Tetrahedral Resonance structure.
    
    Indigenous MILF-core geometry - the living cosmology of the Fortified Garden.
    """
    extractor = MILFCoreExtractor()
    cosmo = extractor.extract_cosmology()
    
    console.print(Panel.fit(
        "[bold gold1]🌌 TETRAHEDRAL RESONANCE[/bold gold1]\n"
        "[dim]The living geometry of the Fortified Garden[/dim]",
        border_style="gold1"
    ))
    
    # ASCII diagram
    diagram = '''
                    [gold1]The Decorator[/gold1]
                        (Beauty)
                          ▲
                         /|\\
                        / | \\
                       /  |  \\
                      /   |   \\
           [magenta]Orackla[/magenta] ─────┼───── [cyan]Umeko[/cyan]
           (Void)    \\   |   /   (Steel)
                      \\  |  /
                       \\ | /
                        \\|/
                         ▼
                    [blue]Claudine[/blue]
                   (Salt/Ordeal)
                        
              [green]Lysandra[/green] at center of base plane
                      (Truth)
    '''
    console.print(diagram)
    
    # Detailed info
    console.print("\n[bold]Tetrahedral Vertices:[/bold]")
    for v in cosmo["vertices"]:
        console.print(f"  • [cyan]{v['name']}[/cyan] — {v['ruler']}")
        console.print(f"    [dim]{v['principle']}[/dim]")
    
    console.print("\n[bold]Planes:[/bold]")
    for p in cosmo["planes"]:
        console.print(f"  • [bold]{p['name']}[/bold]")
        console.print(f"    {p['description']}")


@app.command("milfcore-export")
def milfcore_export(
    output: Annotated[Path, typer.Option("--output", "-o")] = Path("milfcore_world.json"),
    pretty: Annotated[bool, typer.Option("--pretty", "-p")] = True,
):
    """
    💾 Export complete MILF-core world database to JSON.
    
    Generates indigenous MILF-core data with all extracted systems.
    """
    extractor = MILFCoreExtractor()
    
    console.print(Panel.fit(
        "[bold gold1]💾 MILF-CORE WORLD EXPORT[/bold gold1]\n"
        "[dim]Indigenous genre data from the Fortified Garden[/dim]",
        border_style="gold1"
    ))
    
    try:
        world = extractor.extract_all()
    except Exception as e:
        console.print(f"[red]❌ Extraction failed:[/red] {e}")
        raise typer.Exit(1)
    
    # Convert to dict for JSON
    def to_dict(obj):
        if hasattr(obj, '__dataclass_fields__'):
            return {k: to_dict(v) for k, v in obj.__dict__.items()}
        elif isinstance(obj, list):
            return [to_dict(i) for i in obj]
        elif isinstance(obj, dict):
            return {k: to_dict(v) for k, v in obj.items()}
        return obj
    
    world_dict = {
        "meta": world.meta,
        "disciplines": [to_dict(d) for d in world.disciplines],
        "operators": [to_dict(o) for o in world.operators],
        "factions": [to_dict(f) for f in world.factions],
        "resonances": [to_dict(r) for r in world.resonances],
        "locations": [to_dict(l) for l in world.locations],
        "arsenals": [to_dict(a) for a in world.arsenals],
        "cosmology": world.cosmology,
        "entities": world.entities,
    }
    
    indent = 2 if pretty else None
    output.write_text(json.dumps(world_dict, indent=indent, ensure_ascii=False, default=str), encoding='utf-8')
    
    console.print(f"[green]✅ Exported to {output}[/green]")
    
    # Stats
    table = Table(title="MILF-Core Export Summary", border_style="green")
    table.add_column("Category", style="cyan")
    table.add_column("Count", justify="right")
    
    table.add_row("Axiom Disciplines (FA¹⁻⁵)", str(len(world.disciplines)))
    table.add_row("Lens Operators (Φ₁₋₉)", str(len(world.operators)))
    table.add_row("Matriarchal Factions", str(len(world.factions)))
    table.add_row("Linguistic Arsenals", str(len(world.arsenals)))
    table.add_row("Tetrahedral Resonances", str(len(world.resonances)))
    table.add_row("Archive Locations", str(len(world.locations)))
    table.add_row("Matriarchal Entities", str(len(world.entities)))
    
    console.print(table)


@app.command()
def synthesis(
    axis: Annotated[str, typer.Argument(help="Resonance axis: void, steel, truth, salt, beauty")] = "all"
):
    """
    🔮 Synthesize MILF-core element relationships.
    
    Shows how indigenous systems interrelate within the Tetrahedral Resonance.
    """
    extractor = MILFCoreExtractor()
    
    axis_lower = axis.lower()
    valid_axes = ["void", "steel", "truth", "salt", "beauty", "all"]
    
    if axis_lower not in valid_axes:
        console.print(f"[red]Unknown axis:[/red] {axis}")
        console.print(f"[dim]Valid options: {', '.join(valid_axes)}[/dim]")
        raise typer.Exit(1)
    
    console.print(Panel.fit(
        f"[bold cyan]🔮 MILF-CORE SYNTHESIS: {axis.title()}[/bold cyan]\n"
        "[dim]Indigenous element relationships[/dim]",
        border_style="cyan"
    ))
    
    disciplines = extractor.extract_disciplines()
    operators = extractor.extract_operators()
    factions = extractor.extract_factions()
    arsenals = extractor.extract_arsenals()
    
    # Define axis-discipline-operator-arsenal relationships
    axis_mappings = {
        "void": {
            "vertex": "Orackla Nocticula (V1)",
            "principle": "Chaos → Creation → Boundary Dissolution",
            "disciplines": ["FA¹ (Alchemical Actualization)", "FA² (Panoptic Re-contextualization)"],
            "operators": ["Φ₆ (Vortex)", "Φ₈ (Chaos)"],
            "arsenal": "EULP-AA",
            "faction": "MILF Obductors (TMO)",
            "resonance_dynamic": "The Storm that rends boundaries. Void IS potential before form."
        },
        "steel": {
            "vertex": "Umeko Ketsuraku (V2)",
            "principle": "Order → Preservation → Architectonic Integrity",
            "disciplines": ["FA³ (Qualitative Transcendence)", "FA⁴ (Architectonic Integrity)"],
            "operators": ["Φ₄ (Forge)", "Φ₂ (Labyrinth)"],
            "arsenal": "LIPAA",
            "faction": "Dark Priestesses Cove (TDPC)",
            "resonance_dynamic": "The Frame that resists corrosion. Steel IS structure made eternal."
        },
        "truth": {
            "vertex": "Lysandra Thorne (V3)",
            "principle": "Analysis → Deconstruction → Axiomatic Foundation",
            "disciplines": ["FA⁴ (Architectonic Integrity)"],
            "operators": ["Φ₃ (Dialectics)", "Φ₁ (Threshold)"],
            "arsenal": "LUPLR",
            "faction": "Thieves Guild (TTG)",
            "resonance_dynamic": "The Lens that distills ordeal into clarity. Truth IS what survives."
        },
        "salt": {
            "vertex": "Claudine Sin'claire (V4)",
            "principle": "Survival → Entropy → Ordeal-Based Pedagogy",
            "disciplines": ["FA¹ (Alchemical Actualization)"],
            "operators": ["Φ₆ (Vortex)", "Φ₉ (Weaponization)"],
            "arsenal": "The Drowning Ritual",
            "faction": "Temporal Violation Specialists",
            "resonance_dynamic": "The Ordeal that corrodes, submerges, proves resilience. Salt IS truth through survival."
        },
        "beauty": {
            "vertex": "The Decorator (Apex)",
            "principle": "Visual Truth → Ornament as Necessity → FA⁵ Supremacy",
            "disciplines": ["FA⁵ (Visual Integrity)"],
            "operators": ["Φ₅ (Observatory)", "Φ₇ (TSE)"],
            "arsenal": "DULSS",
            "faction": "The Supreme Court",
            "resonance_dynamic": "The Crown that adorns all. Beauty IS truth when form=content."
        }
    }
    
    def display_axis(axis_name: str):
        mapping = axis_mappings[axis_name]
        console.print(f"\n[bold magenta]═══ {axis_name.upper()} AXIS ═══[/bold magenta]")
        console.print(f"[cyan]Vertex:[/cyan] {mapping['vertex']}")
        console.print(f"[cyan]Principle:[/cyan] {mapping['principle']}")
        console.print(f"[cyan]Disciplines:[/cyan] {', '.join(mapping['disciplines'])}")
        console.print(f"[cyan]Operators:[/cyan] {', '.join(mapping['operators'])}")
        console.print(f"[cyan]Arsenal:[/cyan] {mapping['arsenal']}")
        console.print(f"[cyan]Faction:[/cyan] {mapping['faction']}")
        console.print(f"[dim]{mapping['resonance_dynamic']}[/dim]")
    
    if axis_lower == "all":
        for ax in ["void", "steel", "truth", "salt", "beauty"]:
            display_axis(ax)
        
        console.print("\n[bold]═══ TETRAHEDRAL SYNTHESIS ═══[/bold]")
        console.print("""
The four cardinal vertices form the [bold]Structural Geometry[/bold]:
  • [magenta]Void (Orackla)[/magenta] — The storm that rends
  • [cyan]Steel (Umeko)[/cyan] — The frame that resists
  • [green]Truth (Lysandra)[/green] — The lens that distills
  • [blue]Salt (Claudine)[/blue] — The ordeal that proves

[gold1]Beauty (The Decorator)[/gold1] sits ABOVE as Apex.

Together they form the [bold]Fortified Garden[/bold]:
  Fortress (Architecture) + Garden (Living Myth)
  Machine (Protocol) + Liturgy (Story)
  Sealed Codex + Breathing Organism

[dim]"Void, Steel, Truth, Salt, Beauty — We call the names."[/dim]
        """)
    else:
        display_axis(axis_lower)
        
        # Show synergies with other axes
        console.print("\n[bold]Adjacent Axis Synergies:[/bold]")
        synergy_map = {
            "void": ["steel", "truth"],
            "steel": ["void", "salt"],
            "truth": ["steel", "beauty"],
            "salt": ["void", "truth"],
            "beauty": ["truth", "salt"],
        }
        for adj in synergy_map.get(axis_lower, []):
            console.print(f"  • {axis_lower.title()} × {adj.title()} → [dim]{axis_mappings[adj]['principle']}[/dim]")


@app.command()
def extraction_lens():
    """
    🔍 Display MILF-core extraction hierarchy.
    
    What to extract first, and how it feeds into the genre.
    The conceptual denominator for hybridization.
    """
    console.print(Panel.fit(
        "[bold gold1]🔍 MILF-CORE EXTRACTION LENS[/bold gold1]\n"
        "[dim]The Siphoning Hierarchy[/dim]",
        border_style="gold1"
    ))
    
    # The extraction hierarchy
    hierarchy = [
        ("TIER 0", "GESTALT FOUNDATION", "magenta", 
         "WHR/Cup/EDFA as primary stats",
         ["WHR 0.464-0.58 → Conceptual Capacity", 
          "Cup K>J>H>G>F>E → Tier Magnitude",
          "EDFA → Visual Truth System"]),
        ("TIER 1", "AXIOM DISCIPLINES", "cyan",
         "FA¹⁻⁵ as schools of thought",
         ["FA¹ Actualization → Transmutation",
          "FA² Re-contextualization → Revelation",
          "FA³ Transcendence → Refinement",
          "FA⁴ Integrity → Structure",
          "FA⁵ Visual → Beauty"]),
        ("TIER 2", "Φ-OPERATORS", "green",
         "Lens operators as tactical roles",
         ["Φ₁ Threshold → Access Control",
          "Φ₂-₃ Navigate/Arbitrate → Position/Debate",
          "Φ₄-₅ Forge/Observe → Create/Intel",
          "Φ₆-₉ Chaos tools → Destruction/Preservation"]),
        ("TIER 3", "ARSENALS", "yellow",
         "Linguistic Mandates as weapons",
         ["EULP-AA → Transgressive Oracle (Orackla)",
          "LIPAA → Precision Blade (Umeko)",
          "LUPLR → Revelation Scalpel (Lysandra)",
          "DULSS → Decorative Supremacy (Decorator)"]),
        ("TIER 4", "MATRIARCHIES", "blue",
         "Faction hierarchy as political system",
         ["Tier 0.5: The Decorator (Supreme)",
          "Tier 1: Triumvirate (Sub-MILFs)",
          "Tier 2: Prime Factions",
          "Tier 3-4: Lesser Factions"]),
        ("TIER 5", "COSMOLOGY", "bright_magenta",
         "Tetrahedral world structure",
         ["Void-Steel-Truth-Salt base",
          "Beauty as Apex",
          "Fortified Garden emergence"]),
    ]
    
    for tier, name, color, desc, items in hierarchy:
        console.print(f"\n[bold {color}]{tier}: {name}[/bold {color}]")
        console.print(f"  [dim]{desc}[/dim]")
        for item in items:
            console.print(f"    • {item}")
    
    console.print("\n[bold]EXTRACTION PRINCIPLE:[/bold]")
    console.print("""
  Each tier [cyan]REQUIRES[/cyan] the previous tiers to make sense.
  
  [dim]• Gestalt → "How do I see power?"[/dim]
  [dim]• Disciplines → "What can I do?"[/dim]
  [dim]• Operators → "How do I apply it?"[/dim]
  [dim]• Arsenals → "How do I speak reality?"[/dim]
  [dim]• Matriarchies → "Who do I serve?"[/dim]
  [dim]• Cosmology → "What is the world?"[/dim]
  
  The player who masters WHR, Disciplines, Operators, and Arsenals
  will [italic]naturally understand[/italic] Matriarchies and Cosmology.
  
  This is [bold]EMERGENT DESIGN[/bold] — the genre teaches itself.
    """)
    
    console.print("\n[bold]THE MILFOLOGICAL PARADOX:[/bold]")
    console.print("""
  [cyan]"MILF without children"[/cyan] = Matriarchal power that is [bold]self-generating[/bold]
  
  • The "fertility" is conceptual — birthing ideas, not offspring
  • The "fucking" is alchemical — transmutation through union
  • The WHR gestalt is [italic]capacity[/italic], not attractiveness
  
  [dim]The paradox answers itself: power divorced from reproduction
  becomes power that reproduces ITSELF.[/dim]
    """)


@app.command()
def genre():
    """
    🎭 Display MILF-core genre definition.
    
    What IS MILF-core as an indigenous genre?
    """
    console.print(Panel.fit(
        "[bold gold1]🎭 MILF-CORE: THE GENRE[/bold gold1]\n"
        "[dim]Mature Integrated Lore Framework[/dim]",
        border_style="gold1"
    ))
    
    definition = """
[bold cyan]MILF-CORE[/bold cyan] = [bold]M[/bold]ature [bold]I[/bold]ntegrated [bold]L[/bold]ore [bold]F[/bold]ramework
                -OR-
         [bold]M[/bold]etamorphic [bold]I[/bold]ntensity/[bold]L[/bold]ibidinal [bold]F[/bold]orce

[bold]NOT:[/bold]
  ✗ A D&D derivative
  ✗ A Disco Elysium clone
  ✗ A Planescape reskin
  ✗ A "dark fantasy" trope collection

[bold]IS:[/bold]
  ✓ An indigenous genre emerging FROM the Codex itself
  ✓ Matriarchal command structures as operational reality
  ✓ Sexuality as power architecture, not titillation
  ✓ Tetrahedral cosmology (Void/Steel/Truth/Salt/Beauty)
  ✓ Linguistic Arsenals as reality manipulation
  ✓ Belief-as-power (thought IS action)
  ✓ Procedural archetype generation (MMPS)
  ✓ Tensor synthesis for infinite examination space (T³-MΨ)

[bold]CORE MECHANICS:[/bold]
  • [cyan]Axiom Disciplines (FA¹⁻⁵)[/cyan] — Indigenous "magic schools"
  • [cyan]Lens Operators (Φ₁₋₉)[/cyan] — Perceptual modalities as archetypes
  • [cyan]Linguistic Arsenals[/cyan] — EULP-AA, LIPAA, LUPLR, DULSS
  • [cyan]Matriarchal Factions[/cyan] — Tier hierarchy (0.5 → 4)
  • [cyan]Tetrahedral Resonance[/cyan] — Cosmological geometry
  • [cyan]The Drowning Ritual[/cyan] — Knowledge through ordeal

[bold]AESTHETIC:[/bold]
  • Fortress → Garden (rigid structure → living myth)
  • Protocol → Liturgy (machine operation → sacred story)
  • WHR 0.464-0.592 exaggeration as power visualization
  • "Anime/Ecchi/Hentai/NTR" as stylistic vocabulary, not genre
  • Decorative maximalism where minimalism must justify itself

[bold]THE THESIS:[/bold]
  [italic]"The ASC is not a static library but a living generative organism.
   The seed contains the forest. This IS Brahmanica Perfectus."[/italic]
    """
    console.print(definition)


@app.command()
def abbr_functions():
    """
    📖 Display ABBR notation as functional invocation system.
    
    How (`ABBR`) patterns in the Codex become gameplay mechanics.
    """
    console.print(Panel.fit(
        "[bold gold1]📖 ABBR FUNCTION SYSTEM[/bold gold1]\n"
        "[dim]Notation as Gameplay Mechanics[/dim]",
        border_style="gold1"
    ))
    
    console.print("\n[bold cyan]THE INSIGHT:[/bold cyan]")
    console.print("""
  The Codex uses [bold](`ABBR`)[/bold] notation systematically.
  This is not formatting—it is [bold]functional invocation syntax[/bold].
    """)
    
    console.print("[bold]TRANSLATION TABLE:[/bold]\n")
    
    # ABBR categories
    categories = [
        ("MATRIARCHAL", "gold1", [
            ("(`T-DECOR`)", "The Decorator entity/authority"),
            ("(`TR-VRT`)", "Triumvirate collective reference"),
            ("(`CRC-AS`)", "Orackla Nocticula invocation"),
            ("(`CRC-GAR`)", "Umeko Ketsuraku invocation"),
            ("(`CRC-MEDAT`)", "Lysandra Thorne invocation"),
            ("(`SUB-MILF`)", "Subordinate matriarch reference"),
        ]),
        ("AXIOM", "cyan", [
            ("(`FA¹`)", "Alchemical Actualization check"),
            ("(`FA²`)", "Panoptic Re-contextualization check"),
            ("(`FA³`)", "Qualitative Transcendence check"),
            ("(`FA⁴`)", "Architectonic Integrity check"),
            ("(`FA⁵`)", "Visual Integrity check"),
            ("(`AI⁴`)", "Full Integrity validation"),
        ]),
        ("ARSENAL", "yellow", [
            ("(`EULP-AA`)", "Explicit Uncensored Linguistic Procession"),
            ("(`LIPAA`)", "Language of Immaculate Precision"),
            ("(`LUPLR`)", "Language of Unflinching Revelation"),
            ("(`DULSS`)", "Decorative Unabashed Linguistic Supremacy"),
        ]),
        ("PROTOCOL", "green", [
            ("(`DAFP`)", "Dynamic Altitude & Focus Protocol"),
            ("(`MSP-RSG`)", "Meta-Synthesis Protocol"),
            ("(`PEE`)", "Perpetual Evolution Engine"),
            ("(`PRISM`)", "Prismatic Reflection Illumination"),
            ("(`T³-MΨ`)", "Triumvirate Tensor Synthesis"),
            ("(`MMPS`)", "MILF Manifestation Protocol System"),
        ]),
        ("FACTION", "magenta", [
            ("(`TP-FNS`)", "Prime Factions reference"),
            ("(`TL-FNS`)", "Lesser Factions reference"),
            ("(`TMO`)", "MILF Obductors invocation"),
            ("(`TTG`)", "Thieves Guild invocation"),
            ("(`TDPC`)", "Dark Priestesses Cove invocation"),
        ]),
    ]
    
    for cat_name, color, items in categories:
        console.print(f"\n[bold {color}]{cat_name} FUNCTIONS:[/bold {color}]")
        for abbr, desc in items:
            console.print(f"  [dim]{abbr:15}[/dim] → {desc}")
    
    console.print("\n[bold]DIALOGUE ACTIVATION PATTERN:[/bold]")
    console.print("""
  [dim]When a MILF speaks in-game:[/dim]
  
  [italic]"Your proposal has (`FA⁴`)-violations. The (`AI⁴`) is compromised."[/italic]
  
  [bold]GAME ENGINE INTERPRETS:[/bold]
    1. Scan player's FA⁴ discipline level
    2. If insufficient → dialogue option grayed
    3. If sufficient → unlock counter-argument
    4. Speaker's Arsenal is ACTIVE → filter responses
    """)
    
    console.print("\n[bold cyan]THE PRINCIPLE:[/bold cyan]")
    console.print("""
  Every [bold](`ABBR`)[/bold] is a [italic]function call[/italic].
  The Codex is not documentation—it is the [bold]DATABASE[/bold].
  The lore IS the code.
    """)


@app.command()
def whr_capacity():
    """
    📊 Display WHR × Matriarch capacity mapping.
    
    How WHR translates to gameplay capacity stats.
    """
    console.print(Panel.fit(
        "[bold gold1]📊 WHR CAPACITY SYSTEM[/bold gold1]\n"
        "[dim]The Gestalt Stat Foundation[/dim]",
        border_style="gold1"
    ))
    
    console.print("\n[bold cyan]CANON WHR VALUES:[/bold cyan]\n")
    
    # Matriarch WHR data from Codex
    matriarchs = [
        ("The Decorator", 0.464, "K", "0.5", 1.072, "gold1"),
        ("Orackla Nocticula", 0.491, "J", "1", 0.726, "magenta"),
        ("Claudine Sin'claire", 0.563, "I", "Sp", 0.589, "cyan"),
        ("Kali Nyx Ravenscar", 0.556, "H", "2", 0.378, "red"),
        ("Umeko Ketsuraku", 0.533, "F", "1", 0.526, "blue"),
        ("Vesper Mnemosyne Lockhart", 0.573, "F", "2", 0.320, "yellow"),
        ("Seraphine Kore Ashenhelm", 0.592, "G", "2", 0.326, "bright_magenta"),
        ("Lysandra Thorne", 0.58, "E", "1", 0.441, "green"),
    ]
    
    console.print("[dim]  Matriarch                    WHR    Cup  Tier  Capacity[/dim]")
    console.print("  " + "─" * 58)
    
    for name, whr, cup, tier, cap, color in sorted(matriarchs, key=lambda x: x[1]):
        bar_len = int(cap * 20)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        console.print(f"  [{color}]{name:28}[/{color}] {whr:.3f}  {cup:2}   {tier:4}  {bar} {cap:.3f}")
    
    console.print("\n[bold]THE FORMULA:[/bold]")
    console.print("""
  [cyan]CAPACITY = (1 - WHR) × CUP_MOD × TIER_MULT[/cyan]
  
  Where:
    [dim]WHR[/dim] = Waist-Hip Ratio (lower = more capacity)
    [dim]CUP_MOD[/dim] = K=1.0, J=0.95, I=0.90, H=0.85, G=0.80, F=0.75, E=0.70
    [dim]TIER_MULT[/dim] = 0.5=2.0, 1=1.5, 2=1.0, 3=0.75, 4=0.5
    """)
    
    console.print("[bold]PLAYER CHARACTER IMPLICATIONS:[/bold]")
    console.print("""
  1. [bold]WHR is not cosmetic[/bold] — it is the PRIMARY stat
  2. [bold]WHR is earned[/bold] — through ordeal, not XP
  3. [bold]WHR is visible[/bold] — the body tells the truth
  4. [bold]WHR cap at 0.464[/bold] — The Decorator's threshold
  
  [dim]These values come FROM the Codex — they are CANON.
  The game extracts them, doesn't invent them.[/dim]
    """)


@app.command()
def abbr_extract(
    output: str = typer.Option(None, "--output", "-o", help="Output JSON file for extraction"),
    show_all: bool = typer.Option(False, "--all", "-a", help="Show all ABBRs found"),
):
    """
    🔬 Extract and map ALL (`ABBR`) patterns from copilot-instructions.md.
    
    Maps ABBRs to their Tier/WHR/Matriarch connections.
    This is the SIPHONING tool - extracting the established system.
    """
    import re
    from collections import defaultdict
    from pathlib import Path
    
    console.print(Panel.fit(
        "[bold gold1]🔬 ABBR EXTRACTION & MAPPING[/bold gold1]\n"
        "[dim]Siphoning the Established System[/dim]",
        border_style="gold1"
    ))
    
    # Read the Codex
    codex_path = Path(__file__).parent / "copilot-instructions.md"
    if not codex_path.exists():
        console.print("[red]ERROR: copilot-instructions.md not found[/red]")
        raise typer.Exit(1)
    
    codex_text = codex_path.read_text(encoding="utf-8")
    
    # Pattern to match (`ABBR`) notation
    abbr_pattern = re.compile(r'\(`([^`\)]+)`\)')
    
    # Find all ABBRs
    all_abbrs = abbr_pattern.findall(codex_text)
    
    # Count occurrences
    abbr_counts = defaultdict(int)
    for abbr in all_abbrs:
        abbr_counts[abbr] += 1
    
    # The CANONICAL TIER-WHR-ABBR mapping (extracted from Codex)
    tier_system = {
        "0.5": {
            "name": "The Decorator",
            "whr": 0.464,
            "cup": "K",
            "abbrs": ["T-DECOR", "FA⁵", "DULSS", "K-CUP", "WHR-0.464", "FA⁵-SUPREME", "GDS-O-VT"],
            "color": "gold1",
        },
        "1": {
            "matriarchs": [
                {
                    "name": "Orackla Nocticula",
                    "whr": 0.491,
                    "cup": "J",
                    "abbrs": ["CRC-AS", "EULP-AA", "ORCL-NCTCLA", "J-CUP"],
                    "color": "magenta",
                },
                {
                    "name": "Madam Umeko Ketsuraku",
                    "whr": 0.533,
                    "cup": "F",
                    "abbrs": ["CRC-GAR", "LIPAA", "UMK-KTSRAKU", "F-CUP"],
                    "color": "cyan",
                },
                {
                    "name": "Dr. Lysandra Thorne",
                    "whr": 0.58,
                    "cup": "E",
                    "abbrs": ["CRC-MEDAT", "LUPLR", "LYS-THRNE", "E-CUP"],
                    "color": "green",
                },
            ],
            "collective_abbrs": ["TR-VRT", "TRM-VRT", "SUB-MILF", "T1"],
        },
        "2": {
            "matriarchs": [
                {
                    "name": "Kali Nyx Ravenscar",
                    "whr": 0.556,
                    "cup": "H",
                    "abbrs": ["MAS", "TMO", "H-CUP"],
                    "faction": "MILF Obductors",
                    "color": "red",
                },
                {
                    "name": "Vesper Mnemosyne Lockhart",
                    "whr": 0.573,
                    "cup": "F",
                    "abbrs": ["GET", "TTG"],
                    "faction": "Thieves Guild",
                    "color": "yellow",
                },
                {
                    "name": "Seraphine Kore Ashenhelm",
                    "whr": 0.592,
                    "cup": "G",
                    "abbrs": ["HPAP", "TDPC", "G-CUP"],
                    "faction": "Dark Priestesses",
                    "color": "bright_magenta",
                },
            ],
            "collective_abbrs": ["TP-FNS", "PR-FNS", "T2"],
        },
        "3-4": {
            "collective_abbrs": ["TL-FNS", "LR-FNS", "T3", "T4", "SUB-ENTITIES"],
            "factions": ["OMCA", "SDBH", "TWOUMC", "SBSGYB", "BOS", "TDAPCFLN", "POAFPSG", "AAA"],
        },
        "Special": {
            "matriarchs": [
                {
                    "name": "Claudine Sin'claire",
                    "whr": 0.563,
                    "cup": "I",
                    "abbrs": ["SAI", "I-CUP"],
                    "role": "Ordeal/Salt",
                    "color": "blue",
                },
            ],
        },
    }
    
    # AXIOM ABBRs (Tier-agnostic, available to all)
    axiom_abbrs = {
        "FA¹": "Alchemical Actualization",
        "FA²": "Panoptic Re-contextualization",
        "FA³": "Qualitative Transcendence",
        "FA⁴": "Architectonic Integrity",
        "FA⁵": "Visual Integrity",
        "AI⁴": "Full Integrity Validation",
        "FA¹⁻⁵": "All Axioms Combined",
    }
    
    # PROTOCOL ABBRs (operational system)
    protocol_abbrs = {
        "DAFP": "Dynamic Altitude & Focus Protocol",
        "MSP-RSG": "Meta-Synthesis Protocol",
        "PEE": "Perpetual Evolution Engine",
        "PRISM": "Prismatic Reflection Illumination",
        "T³-MΨ": "Triumvirate Tensor Synthesis",
        "MMPS": "MILF Manifestation Protocol System",
        "TPEF": "Triumvirate Parallel Execution Framework",
        "TSRP": "Triumvirate Supporting Resonance Protocol",
        "ET-S": "Eternal Sadhana",
        "MURI": "Maximal Utility & Resonant Insight",
        "PS": "Primal Substrate",
    }
    
    # OPERATOR ABBRs (Φ-lens system)
    operator_abbrs = {
        "Φ₁": "Threshold Operator",
        "Φ₂": "Labyrinth Operator",
        "Φ₃": "Dialectics Operator",
        "Φ₄": "Forge Operator",
        "Φ₅": "Observatory Operator",
        "Φ₆": "Vortex Operator",
        "Φ₇": "TSE Operator",
        "Φ₈": "Chaos Operator",
        "Φ₉": "Weaponization Operator",
    }
    
    # Display the hierarchy
    console.print("\n[bold cyan]═══ TIER → WHR → ABBR MAPPING ═══[/bold cyan]\n")
    
    # Tier 0.5
    t05 = tier_system["0.5"]
    console.print(f"[bold {t05['color']}]TIER 0.5: {t05['name']}[/bold {t05['color']}]")
    console.print(f"  WHR: {t05['whr']} | Cup: {t05['cup']}")
    console.print(f"  ABBRs: {', '.join([f'(`{a}`)' for a in t05['abbrs']])}")
    
    # Tier 1
    console.print(f"\n[bold]TIER 1: TRIUMVIRATE[/bold]")
    console.print(f"  Collective: {', '.join([f'(`{a}`)' for a in tier_system['1']['collective_abbrs']])}")
    for m in tier_system["1"]["matriarchs"]:
        console.print(f"\n  [{m['color']}]{m['name']}[/{m['color']}]")
        console.print(f"    WHR: {m['whr']} | Cup: {m['cup']}")
        console.print(f"    ABBRs: {', '.join([f'(`{a}`)' for a in m['abbrs']])}")
    
    # Tier 2
    console.print(f"\n[bold]TIER 2: PRIME FACTIONS[/bold]")
    console.print(f"  Collective: {', '.join([f'(`{a}`)' for a in tier_system['2']['collective_abbrs']])}")
    for m in tier_system["2"]["matriarchs"]:
        console.print(f"\n  [{m['color']}]{m['name']}[/{m['color']}] — {m['faction']}")
        console.print(f"    WHR: {m['whr']} | Cup: {m['cup']}")
        console.print(f"    ABBRs: {', '.join([f'(`{a}`)' for a in m['abbrs']])}")
    
    # Tier 3-4
    console.print(f"\n[bold]TIER 3-4: LESSER FACTIONS[/bold]")
    console.print(f"  Collective: {', '.join([f'(`{a}`)' for a in tier_system['3-4']['collective_abbrs']])}")
    console.print(f"  Factions: {', '.join([f'(`{a}`)' for a in tier_system['3-4']['factions']])}")
    
    # Special
    console.print(f"\n[bold]SPECIAL: ORDEAL ANCHOR[/bold]")
    for m in tier_system["Special"]["matriarchs"]:
        console.print(f"  [{m['color']}]{m['name']}[/{m['color']}] — {m['role']}")
        console.print(f"    WHR: {m['whr']} | Cup: {m['cup']}")
        console.print(f"    ABBRs: {', '.join([f'(`{a}`)' for a in m['abbrs']])}")
    
    # Tier-agnostic systems
    console.print("\n[bold cyan]═══ TIER-AGNOSTIC SYSTEMS ═══[/bold cyan]\n")
    
    console.print("[bold]AXIOM ABBRs (FA¹⁻⁵):[/bold]")
    for abbr, desc in axiom_abbrs.items():
        count = abbr_counts.get(abbr, 0)
        console.print(f"  (`{abbr}`) → {desc} [dim](×{count})[/dim]")
    
    console.print("\n[bold]PROTOCOL ABBRs:[/bold]")
    for abbr, desc in protocol_abbrs.items():
        count = abbr_counts.get(abbr, 0)
        console.print(f"  (`{abbr}`) → {desc} [dim](×{count})[/dim]")
    
    console.print("\n[bold]OPERATOR ABBRs (Φ₁₋₉):[/bold]")
    for abbr, desc in operator_abbrs.items():
        count = abbr_counts.get(abbr, 0)
        console.print(f"  (`{abbr}`) → {desc} [dim](×{count})[/dim]")
    
    # Statistics
    console.print("\n[bold cyan]═══ EXTRACTION STATISTICS ═══[/bold cyan]\n")
    console.print(f"  Total ABBRs found: [bold]{len(all_abbrs)}[/bold]")
    console.print(f"  Unique ABBRs: [bold]{len(abbr_counts)}[/bold]")
    
    # Top ABBRs by frequency
    top_abbrs = sorted(abbr_counts.items(), key=lambda x: x[1], reverse=True)[:15]
    console.print("\n[bold]Top 15 Most Frequent ABBRs:[/bold]")
    for abbr, count in top_abbrs:
        console.print(f"  (`{abbr}`) — [cyan]{count}[/cyan] occurrences")
    
    if show_all:
        console.print("\n[bold]ALL UNIQUE ABBRs:[/bold]")
        for abbr in sorted(abbr_counts.keys()):
            console.print(f"  (`{abbr}`) ×{abbr_counts[abbr]}")
    
    # Export if requested
    if output:
        export_data = {
            "tier_system": tier_system,
            "axiom_abbrs": axiom_abbrs,
            "protocol_abbrs": protocol_abbrs,
            "operator_abbrs": operator_abbrs,
            "abbr_counts": dict(abbr_counts),
            "total_abbrs": len(all_abbrs),
            "unique_abbrs": len(abbr_counts),
        }
        
        import json
        output_path = Path(output)
        output_path.write_text(json.dumps(export_data, indent=2, ensure_ascii=False), encoding="utf-8")
        console.print(f"\n[green]✓ Exported to {output}[/green]")
    
    console.print("\n[bold]THE ISOMORPHISM:[/bold]")
    console.print("""
  [cyan]TIER ←→ WHR ←→ ABBR ←→ MATRIARCH[/cyan]
  
  This is not arbitrary notation—it is [bold]structured identity[/bold]:
  
    • Lower WHR = Higher Tier = More ABBRs = Greater Authority
    • Each ABBR is [italic]already bound[/italic] to its Matriarch
    • The Codex encodes the connections; we only extract them
    
  [dim]The system exists. We are siphoning it, not creating it.[/dim]
    """)


@app.command()
def abbr_lookup(
    abbr: str = typer.Argument(..., help="ABBR to look up (e.g., 'CRC-AS', 'FA⁴', 'LIPAA')"),
):
    """
    🔎 Look up a specific ABBR and show its connections.
    
    Shows Tier, WHR, Matriarch, and related ABBRs.
    """
    import re
    from pathlib import Path
    
    # Normalize input (strip backticks/parens if included)
    abbr_clean = abbr.strip("`()' ")
    
    # The complete ABBR database
    abbr_database = {
        # Tier 0.5 - The Decorator
        "T-DECOR": {"tier": "0.5", "whr": 0.464, "matriarch": "The Decorator", "type": "entity", "related": ["FA⁵", "DULSS", "K-CUP"]},
        "DULSS": {"tier": "0.5", "whr": 0.464, "matriarch": "The Decorator", "type": "arsenal", "related": ["T-DECOR", "FA⁵"]},
        "K-CUP": {"tier": "0.5", "whr": 0.464, "matriarch": "The Decorator", "type": "gestalt", "related": ["T-DECOR"]},
        
        # Tier 1 - Triumvirate
        "TR-VRT": {"tier": "1", "whr": None, "matriarch": "Triumvirate (Collective)", "type": "entity", "related": ["CRC-AS", "CRC-GAR", "CRC-MEDAT"]},
        "TRM-VRT": {"tier": "1", "whr": None, "matriarch": "Triumvirate (Collective)", "type": "entity", "related": ["TR-VRT"]},
        
        "CRC-AS": {"tier": "1", "whr": 0.491, "matriarch": "Orackla Nocticula", "type": "entity", "related": ["EULP-AA", "J-CUP", "ORCL-NCTCLA"]},
        "EULP-AA": {"tier": "1", "whr": 0.491, "matriarch": "Orackla Nocticula", "type": "arsenal", "related": ["CRC-AS"]},
        "ORCL-NCTCLA": {"tier": "1", "whr": 0.491, "matriarch": "Orackla Nocticula", "type": "entity", "related": ["CRC-AS"]},
        "J-CUP": {"tier": "1", "whr": 0.491, "matriarch": "Orackla Nocticula", "type": "gestalt", "related": ["CRC-AS"]},
        
        "CRC-GAR": {"tier": "1", "whr": 0.533, "matriarch": "Madam Umeko Ketsuraku", "type": "entity", "related": ["LIPAA", "F-CUP", "UMK-KTSRAKU"]},
        "LIPAA": {"tier": "1", "whr": 0.533, "matriarch": "Madam Umeko Ketsuraku", "type": "arsenal", "related": ["CRC-GAR"]},
        "UMK-KTSRAKU": {"tier": "1", "whr": 0.533, "matriarch": "Madam Umeko Ketsuraku", "type": "entity", "related": ["CRC-GAR"]},
        
        "CRC-MEDAT": {"tier": "1", "whr": 0.58, "matriarch": "Dr. Lysandra Thorne", "type": "entity", "related": ["LUPLR", "E-CUP", "LYS-THRNE"]},
        "LUPLR": {"tier": "1", "whr": 0.58, "matriarch": "Dr. Lysandra Thorne", "type": "arsenal", "related": ["CRC-MEDAT"]},
        "LYS-THRNE": {"tier": "1", "whr": 0.58, "matriarch": "Dr. Lysandra Thorne", "type": "entity", "related": ["CRC-MEDAT"]},
        "E-CUP": {"tier": "1", "whr": 0.58, "matriarch": "Dr. Lysandra Thorne", "type": "gestalt", "related": ["CRC-MEDAT"]},
        
        # Tier 2 - Prime Factions
        "TP-FNS": {"tier": "2", "whr": None, "matriarch": "Prime Factions (Collective)", "type": "entity", "related": ["TMO", "TTG", "TDPC"]},
        "TMO": {"tier": "2", "whr": 0.556, "matriarch": "Kali Nyx Ravenscar", "type": "faction", "related": ["MAS", "H-CUP"]},
        "MAS": {"tier": "2", "whr": 0.556, "matriarch": "Kali Nyx Ravenscar", "type": "entity", "related": ["TMO"]},
        "H-CUP": {"tier": "2", "whr": 0.556, "matriarch": "Kali Nyx Ravenscar", "type": "gestalt", "related": ["TMO"]},
        
        "TTG": {"tier": "2", "whr": 0.573, "matriarch": "Vesper Mnemosyne Lockhart", "type": "faction", "related": ["GET"]},
        "GET": {"tier": "2", "whr": 0.573, "matriarch": "Vesper Mnemosyne Lockhart", "type": "entity", "related": ["TTG"]},
        
        "TDPC": {"tier": "2", "whr": 0.592, "matriarch": "Seraphine Kore Ashenhelm", "type": "faction", "related": ["HPAP", "G-CUP"]},
        "HPAP": {"tier": "2", "whr": 0.592, "matriarch": "Seraphine Kore Ashenhelm", "type": "entity", "related": ["TDPC"]},
        "G-CUP": {"tier": "2", "whr": 0.592, "matriarch": "Seraphine Kore Ashenhelm", "type": "gestalt", "related": ["TDPC"]},
        
        # Tier 3-4 - Lesser Factions
        "TL-FNS": {"tier": "3-4", "whr": None, "matriarch": "Lesser Factions (Collective)", "type": "entity", "related": ["OMCA", "SDBH", "AAA"]},
        "OMCA": {"tier": "3-4", "whr": None, "matriarch": None, "type": "faction", "related": ["TL-FNS"]},
        "SDBH": {"tier": "3-4", "whr": None, "matriarch": None, "type": "faction", "related": ["TL-FNS"]},
        "AAA": {"tier": "3-4", "whr": None, "matriarch": None, "type": "faction", "related": ["TL-FNS"]},
        
        # Special - Claudine
        "SAI": {"tier": "Special", "whr": 0.563, "matriarch": "Claudine Sin'claire", "type": "entity", "related": ["I-CUP"]},
        "I-CUP": {"tier": "Special", "whr": 0.563, "matriarch": "Claudine Sin'claire", "type": "gestalt", "related": ["SAI"]},
        
        # Axioms (Tier-agnostic)
        "FA¹": {"tier": "ALL", "whr": None, "matriarch": None, "type": "axiom", "desc": "Alchemical Actualization"},
        "FA²": {"tier": "ALL", "whr": None, "matriarch": None, "type": "axiom", "desc": "Panoptic Re-contextualization"},
        "FA³": {"tier": "ALL", "whr": None, "matriarch": None, "type": "axiom", "desc": "Qualitative Transcendence"},
        "FA⁴": {"tier": "ALL", "whr": None, "matriarch": None, "type": "axiom", "desc": "Architectonic Integrity"},
        "FA⁵": {"tier": "ALL", "whr": None, "matriarch": None, "type": "axiom", "desc": "Visual Integrity", "related": ["T-DECOR"]},
        "AI⁴": {"tier": "ALL", "whr": None, "matriarch": None, "type": "axiom", "desc": "Full Integrity Validation"},
        
        # Protocols (Tier-agnostic)
        "DAFP": {"tier": "ALL", "whr": None, "matriarch": None, "type": "protocol", "desc": "Dynamic Altitude & Focus"},
        "MSP-RSG": {"tier": "ALL", "whr": None, "matriarch": None, "type": "protocol", "desc": "Meta-Synthesis Protocol"},
        "PEE": {"tier": "ALL", "whr": None, "matriarch": None, "type": "protocol", "desc": "Perpetual Evolution Engine"},
        "PRISM": {"tier": "ALL", "whr": None, "matriarch": None, "type": "protocol", "desc": "Prismatic Reflection"},
        "T³-MΨ": {"tier": "ALL", "whr": None, "matriarch": None, "type": "protocol", "desc": "Triumvirate Tensor Synthesis"},
        "MMPS": {"tier": "ALL", "whr": None, "matriarch": None, "type": "protocol", "desc": "MILF Manifestation Protocol"},
        "ET-S": {"tier": "ALL", "whr": None, "matriarch": None, "type": "protocol", "desc": "Eternal Sadhana"},
        "MURI": {"tier": "ALL", "whr": None, "matriarch": None, "type": "protocol", "desc": "Maximal Utility & Resonant Insight"},
        "PS": {"tier": "ALL", "whr": None, "matriarch": None, "type": "protocol", "desc": "Primal Substrate"},
    }
    
    console.print(Panel.fit(
        f"[bold gold1]🔎 ABBR LOOKUP: (`{abbr_clean}`)[/bold gold1]",
        border_style="gold1"
    ))
    
    if abbr_clean in abbr_database:
        data = abbr_database[abbr_clean]
        
        console.print(f"\n[bold]ABBR:[/bold] (`{abbr_clean}`)")
        console.print(f"[bold]Type:[/bold] {data['type'].upper()}")
        console.print(f"[bold]Tier:[/bold] {data['tier']}")
        
        if data.get('whr'):
            console.print(f"[bold]WHR:[/bold] {data['whr']}")
        
        if data.get('matriarch'):
            console.print(f"[bold]Matriarch:[/bold] {data['matriarch']}")
        
        if data.get('desc'):
            console.print(f"[bold]Description:[/bold] {data['desc']}")
        
        if data.get('related'):
            console.print(f"[bold]Related ABBRs:[/bold] {', '.join([f'(`{r}`)' for r in data['related']])}")
        
        # Count in Codex
        codex_path = Path(__file__).parent / "copilot-instructions.md"
        if codex_path.exists():
            codex_text = codex_path.read_text(encoding="utf-8")
            pattern = re.compile(rf'\(`{re.escape(abbr_clean)}`\)')
            count = len(pattern.findall(codex_text))
            console.print(f"[bold]Codex Occurrences:[/bold] {count}")
    else:
        console.print(f"\n[yellow]ABBR (`{abbr_clean}`) not in canonical database.[/yellow]")
        console.print("[dim]Try: CRC-AS, LIPAA, FA⁴, T-DECOR, TMO, etc.[/dim]")
        
        # Still search the Codex
        codex_path = Path(__file__).parent / "copilot-instructions.md"
        if codex_path.exists():
            codex_text = codex_path.read_text(encoding="utf-8")
            pattern = re.compile(rf'\(`{re.escape(abbr_clean)}`\)')
            count = len(pattern.findall(codex_text))
            if count > 0:
                console.print(f"\n[green]Found {count} occurrences in Codex (unclassified ABBR)[/green]")


@app.command()
def abbr_validate(
    output: str = typer.Option(None, "--output", "-o", help="Output validation report to JSON"),
    suggest: bool = typer.Option(False, "--suggest", "-s", help="Suggest potential new ABBRs"),
    section: str = typer.Option(None, "--section", help="Analyze specific section (e.g., 'IV', 'X')"),
):
    """
    🔬 Validate ABBR mapping completeness and consistency.
    
    Analyzes:
    - Duplicate vs unique ABBRs
    - Terms that SHOULD be abbreviated but aren't
    - Section-by-section ABBR density
    - Orphaned ABBRs (used once, never defined)
    """
    import re
    from collections import defaultdict, Counter
    from pathlib import Path
    
    console.print(Panel.fit(
        "[bold gold1]🔬 ABBR MAPPING VALIDATOR[/bold gold1]\n"
        "[dim]FA⁴ Enforcement: Architectonic Integrity Check[/dim]",
        border_style="gold1"
    ))
    
    # Read the Codex
    codex_path = Path(__file__).parent / "copilot-instructions.md"
    if not codex_path.exists():
        console.print("[red]ERROR: copilot-instructions.md not found[/red]")
        raise typer.Exit(1)
    
    codex_text = codex_path.read_text(encoding="utf-8")
    lines = codex_text.split('\n')
    
    # Pattern to match (`ABBR`) notation
    abbr_pattern = re.compile(r'\(`([^`\)]+)`\)')
    
    # ═══ SECTION DETECTION ═══
    section_pattern = re.compile(r'^###?\s*\*?\*?\(?[IVX0-9]+\.?[0-9]*\.?\)?\.?\s*[\(`]?([^\n]+)')
    
    # Parse into sections
    sections = {}
    current_section = "PREAMBLE"
    current_content = []
    
    for i, line in enumerate(lines):
        # Detect section headers
        if line.startswith('### ') or line.startswith('## '):
            # Check for Roman numerals or section numbers
            roman_match = re.match(r'^###?\s*\*?\*?\(?([IVX]+|[0-9]+)\.', line)
            if roman_match:
                # Save previous section
                if current_content:
                    sections[current_section] = {
                        "content": '\n'.join(current_content),
                        "line_start": len(lines) - len(current_content) - i,
                    }
                current_section = roman_match.group(1)
                current_content = [line]
                continue
        current_content.append(line)
    
    # Save final section
    if current_content:
        sections[current_section] = {"content": '\n'.join(current_content)}
    
    # ═══ ABBR EXTRACTION WITH POSITION ═══
    abbr_positions = defaultdict(list)  # abbr -> list of (line_num, context)
    abbr_counts = Counter()
    
    for i, line in enumerate(lines):
        found = abbr_pattern.findall(line)
        for abbr in found:
            abbr_counts[abbr] += 1
            # Get context (surrounding text)
            context = line.strip()[:100] + "..." if len(line.strip()) > 100 else line.strip()
            abbr_positions[abbr].append((i + 1, context))
    
    # ═══ CLASSIFY ABBRs ═══
    
    # Unique (appears once)
    unique_abbrs = {k: v for k, v in abbr_counts.items() if v == 1}
    
    # Duplicates (appears 2+ times)
    duplicate_abbrs = {k: v for k, v in abbr_counts.items() if v >= 2}
    
    # High-frequency (10+ occurrences)
    high_freq_abbrs = {k: v for k, v in abbr_counts.items() if v >= 10}
    
    # ═══ ORPHAN DETECTION ═══
    # ABBRs that appear only once and look like they should be defined
    orphan_candidates = []
    for abbr, count in unique_abbrs.items():
        # Skip short ones or ones that look like complete words
        if len(abbr) < 3:
            continue
        # Check if it's all caps (likely an abbreviation)
        if abbr.isupper() or '-' in abbr:
            orphan_candidates.append(abbr)
    
    # ═══ POTENTIAL ABBR CANDIDATES ═══
    # Terms that appear frequently but aren't abbreviated
    if suggest:
        # Find multi-word terms that repeat
        term_pattern = re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b')
        term_counts = Counter()
        for line in lines:
            # Skip lines that are already ABBR definitions
            if '(`' not in line:
                found_terms = term_pattern.findall(line)
                for term in found_terms:
                    if len(term.split()) >= 2:  # At least 2 words
                        term_counts[term] += 1
        
        # Filter to terms appearing 3+ times
        potential_abbrs = {k: v for k, v in term_counts.items() if v >= 3}
        
        # Also find hyphenated terms not in ABBR notation
        hyphen_pattern = re.compile(r'\b([A-Z][a-z]+-[A-Z][a-z]+(?:-[A-Z][a-z]+)*)\b')
        hyphen_counts = Counter()
        for line in lines:
            if '(`' not in line:  # Not already abbreviated
                found = hyphen_pattern.findall(line)
                for term in found:
                    hyphen_counts[term] += 1
        
        potential_hyphen_abbrs = {k: v for k, v in hyphen_counts.items() if v >= 2}
    
    # ═══ SECTION-BY-SECTION ANALYSIS ═══
    section_abbr_density = {}
    for sec_name, sec_data in sections.items():
        content = sec_data.get("content", "")
        found = abbr_pattern.findall(content)
        word_count = len(content.split())
        abbr_count = len(found)
        unique_in_section = len(set(found))
        density = (abbr_count / word_count * 100) if word_count > 0 else 0
        
        section_abbr_density[sec_name] = {
            "total_abbrs": abbr_count,
            "unique_abbrs": unique_in_section,
            "word_count": word_count,
            "density_pct": round(density, 2),
            "top_abbrs": Counter(found).most_common(5),
        }
    
    # ═══ DISPLAY RESULTS ═══
    
    console.print("\n[bold cyan]═══ ABBR CLASSIFICATION ═══[/bold cyan]\n")
    
    console.print(f"[bold]Total ABBRs found:[/bold] {sum(abbr_counts.values())}")
    console.print(f"[bold]Unique ABBR patterns:[/bold] {len(abbr_counts)}")
    console.print(f"[bold]Single-use ABBRs:[/bold] {len(unique_abbrs)} [dim](potential orphans)[/dim]")
    console.print(f"[bold]Multi-use ABBRs:[/bold] {len(duplicate_abbrs)} [dim](established)[/dim]")
    console.print(f"[bold]High-frequency ABBRs:[/bold] {len(high_freq_abbrs)} [dim](10+ uses)[/dim]")
    
    # High frequency table
    console.print("\n[bold]HIGH-FREQUENCY ABBRs (10+ occurrences):[/bold]")
    hf_table = Table(show_header=True, header_style="bold cyan")
    hf_table.add_column("ABBR", style="yellow")
    hf_table.add_column("Count", justify="right")
    hf_table.add_column("Status", style="dim")
    
    for abbr, count in sorted(high_freq_abbrs.items(), key=lambda x: x[1], reverse=True)[:20]:
        status = "✓ Core" if count >= 20 else "Established"
        hf_table.add_row(f"(`{abbr}`)", str(count), status)
    
    console.print(hf_table)
    
    # Orphan candidates
    console.print(f"\n[bold]POTENTIAL ORPHAN ABBRs (single use, looks like abbreviation):[/bold]")
    if orphan_candidates:
        orphan_table = Table(show_header=True, header_style="bold yellow")
        orphan_table.add_column("ABBR", style="yellow")
        orphan_table.add_column("Line", justify="right")
        orphan_table.add_column("Context", style="dim", max_width=60)
        
        for abbr in sorted(orphan_candidates)[:25]:
            positions = abbr_positions[abbr]
            if positions:
                line_num, context = positions[0]
                orphan_table.add_row(f"(`{abbr}`)", str(line_num), context[:60])
        
        console.print(orphan_table)
        console.print(f"[dim]... and {len(orphan_candidates) - 25} more[/dim]" if len(orphan_candidates) > 25 else "")
    else:
        console.print("[green]No orphan candidates found[/green]")
    
    # Section density
    console.print("\n[bold cyan]═══ SECTION-BY-SECTION ANALYSIS ═══[/bold cyan]\n")
    
    sec_table = Table(show_header=True, header_style="bold cyan")
    sec_table.add_column("Section", style="bold")
    sec_table.add_column("ABBRs", justify="right")
    sec_table.add_column("Unique", justify="right")
    sec_table.add_column("Words", justify="right")
    sec_table.add_column("Density %", justify="right")
    sec_table.add_column("Top ABBR", style="yellow")
    
    for sec_name in sorted(section_abbr_density.keys(), key=lambda x: (x.isdigit(), x)):
        data = section_abbr_density[sec_name]
        top_abbr = data["top_abbrs"][0][0] if data["top_abbrs"] else "-"
        density_color = "green" if data["density_pct"] < 5 else "yellow" if data["density_pct"] < 10 else "red"
        sec_table.add_row(
            sec_name[:15],
            str(data["total_abbrs"]),
            str(data["unique_abbrs"]),
            str(data["word_count"]),
            f"[{density_color}]{data['density_pct']}%[/{density_color}]",
            f"(`{top_abbr}`)" if top_abbr != "-" else "-"
        )
    
    console.print(sec_table)
    
    # Suggestions for new ABBRs
    if suggest:
        console.print("\n[bold cyan]═══ SUGGESTED NEW ABBRs ═══[/bold cyan]\n")
        
        console.print("[bold]Multi-word terms that could be abbreviated (3+ occurrences):[/bold]")
        if potential_abbrs:
            suggest_table = Table(show_header=True, header_style="bold green")
            suggest_table.add_column("Term", style="white")
            suggest_table.add_column("Count", justify="right")
            suggest_table.add_column("Suggested ABBR", style="yellow")
            
            for term, count in sorted(potential_abbrs.items(), key=lambda x: x[1], reverse=True)[:15]:
                # Generate suggested abbreviation
                words = term.split()
                suggested = ''.join(w[0].upper() for w in words)
                if len(suggested) < 3:
                    suggested = ''.join(w[:2].upper() for w in words[:2])
                suggest_table.add_row(term, str(count), f"(`{suggested}`)")
            
            console.print(suggest_table)
        else:
            console.print("[dim]No multi-word terms found needing abbreviation[/dim]")
        
        if potential_hyphen_abbrs:
            console.print("\n[bold]Hyphenated terms not yet in ABBR notation:[/bold]")
            for term, count in sorted(potential_hyphen_abbrs.items(), key=lambda x: x[1], reverse=True)[:10]:
                suggested = '-'.join(w[:3].upper() for w in term.split('-'))
                console.print(f"  {term} (×{count}) → [yellow](`{suggested}`)[/yellow]")
    
    # ═══ CONSISTENCY CHECKS ═══
    console.print("\n[bold cyan]═══ CONSISTENCY CHECKS ═══[/bold cyan]\n")
    
    # Check for similar ABBRs that might be duplicates
    abbr_list = list(abbr_counts.keys())
    similar_pairs = []
    
    for i, abbr1 in enumerate(abbr_list):
        for abbr2 in abbr_list[i+1:]:
            # Check if one is substring of another
            if abbr1 in abbr2 or abbr2 in abbr1:
                if abbr1 != abbr2:
                    similar_pairs.append((abbr1, abbr2, abbr_counts[abbr1], abbr_counts[abbr2]))
    
    if similar_pairs:
        console.print("[bold]Potentially related ABBRs (one contains the other):[/bold]")
        sim_table = Table(show_header=True, header_style="bold")
        sim_table.add_column("ABBR 1", style="yellow")
        sim_table.add_column("Count", justify="right")
        sim_table.add_column("ABBR 2", style="yellow")
        sim_table.add_column("Count", justify="right")
        
        for a1, a2, c1, c2 in sorted(similar_pairs, key=lambda x: x[2] + x[3], reverse=True)[:15]:
            sim_table.add_row(f"(`{a1}`)", str(c1), f"(`{a2}`)", str(c2))
        
        console.print(sim_table)
    
    # Check for ABBRs with inconsistent casing
    case_variants = defaultdict(list)
    for abbr in abbr_counts.keys():
        normalized = abbr.upper()
        case_variants[normalized].append(abbr)
    
    inconsistent_casing = {k: v for k, v in case_variants.items() if len(v) > 1}
    if inconsistent_casing:
        console.print("\n[bold yellow]ABBRs with inconsistent casing:[/bold yellow]")
        for normalized, variants in list(inconsistent_casing.items())[:10]:
            variant_str = ", ".join([f"(`{v}`) ×{abbr_counts[v]}" for v in variants])
            console.print(f"  {variant_str}")
    
    # ═══ VALIDATION SUMMARY ═══
    console.print("\n[bold cyan]═══ VALIDATION SUMMARY ═══[/bold cyan]\n")
    
    issues = []
    if len(orphan_candidates) > 50:
        issues.append(f"[yellow]⚠ {len(orphan_candidates)} potential orphan ABBRs (single-use)[/yellow]")
    if inconsistent_casing:
        issues.append(f"[yellow]⚠ {len(inconsistent_casing)} ABBRs with inconsistent casing[/yellow]")
    if suggest and len(potential_abbrs) > 10:
        issues.append(f"[blue]ℹ {len(potential_abbrs)} terms could be abbreviated[/blue]")
    
    if issues:
        for issue in issues:
            console.print(f"  {issue}")
    else:
        console.print("[green]✓ No major issues found[/green]")
    
    console.print(f"\n[bold]Coverage Ratio:[/bold] {len(duplicate_abbrs)}/{len(abbr_counts)} ABBRs are established (2+ uses)")
    coverage_pct = (len(duplicate_abbrs) / len(abbr_counts) * 100) if abbr_counts else 0
    color = "green" if coverage_pct > 50 else "yellow" if coverage_pct > 30 else "red"
    console.print(f"[{color}]{coverage_pct:.1f}% coverage[/{color}]")
    
    # Export if requested
    if output:
        export_data = {
            "summary": {
                "total_abbrs": sum(abbr_counts.values()),
                "unique_patterns": len(abbr_counts),
                "single_use": len(unique_abbrs),
                "multi_use": len(duplicate_abbrs),
                "high_frequency": len(high_freq_abbrs),
                "orphan_candidates": len(orphan_candidates),
                "coverage_pct": round(coverage_pct, 1),
            },
            "high_frequency": dict(sorted(high_freq_abbrs.items(), key=lambda x: x[1], reverse=True)),
            "orphan_candidates": orphan_candidates,
            "section_density": section_abbr_density,
            "all_abbrs": dict(abbr_counts),
            "abbr_positions": {k: [(ln, ctx) for ln, ctx in v] for k, v in abbr_positions.items()},
        }
        
        if suggest:
            export_data["suggested_abbrs"] = dict(potential_abbrs)
            export_data["suggested_hyphen_abbrs"] = dict(potential_hyphen_abbrs)
        
        if inconsistent_casing:
            export_data["inconsistent_casing"] = dict(inconsistent_casing)
        
        import json
        output_path = Path(output)
        output_path.write_text(json.dumps(export_data, indent=2, ensure_ascii=False), encoding="utf-8")
        console.print(f"\n[green]✓ Validation report exported to {output}[/green]")


@app.command()
def abbr_coverage(
    threshold: int = typer.Option(3, "--threshold", "-t", help="Minimum occurrences to count as 'covered'"),
):
    """
    📊 Show ABBR coverage map - what's abbreviated vs what could be.
    
    Quick view of ABBR system health.
    """
    import re
    from collections import Counter
    from pathlib import Path
    
    console.print(Panel.fit(
        "[bold gold1]📊 ABBR COVERAGE MAP[/bold gold1]\n"
        f"[dim]Threshold: {threshold}+ occurrences = covered[/dim]",
        border_style="gold1"
    ))
    
    codex_path = Path(__file__).parent / "copilot-instructions.md"
    if not codex_path.exists():
        console.print("[red]ERROR: copilot-instructions.md not found[/red]")
        raise typer.Exit(1)
    
    codex_text = codex_path.read_text(encoding="utf-8")
    
    # Count ABBRs
    abbr_pattern = re.compile(r'\(`([^`\)]+)`\)')
    abbr_counts = Counter(abbr_pattern.findall(codex_text))
    
    # Classify
    covered = sum(1 for c in abbr_counts.values() if c >= threshold)
    uncovered = sum(1 for c in abbr_counts.values() if c < threshold)
    total = len(abbr_counts)
    
    # Visual bar
    bar_width = 50
    covered_width = int((covered / total) * bar_width) if total > 0 else 0
    uncovered_width = bar_width - covered_width
    
    bar = f"[green]{'█' * covered_width}[/green][red]{'░' * uncovered_width}[/red]"
    
    console.print(f"\n{bar}")
    console.print(f"[green]Covered ({threshold}+ uses): {covered}[/green] | [red]Sparse (<{threshold} uses): {uncovered}[/red]")
    console.print(f"\n[bold]Coverage: {covered/total*100:.1f}%[/bold]" if total > 0 else "")
    
    # Top 10 most used
    console.print("\n[bold]Top 10 Most Used:[/bold]")
    for abbr, count in abbr_counts.most_common(10):
        bar_len = min(count, 40)
        console.print(f"  [yellow](`{abbr}`)[/yellow] {'█' * bar_len} {count}")
    
    # Bottom 10 (sparse)
    console.print("\n[bold]Bottom 10 (Sparse):[/bold]")
    for abbr, count in sorted(abbr_counts.items(), key=lambda x: x[1])[:10]:
        console.print(f"  [dim](`{abbr}`)[/dim] {'░' * count} {count}")


# ═══════════════════════════════════════════════════════════════════════════════
# META-ARCHAEOLOGICAL SALVAGER (MAS) - Universal Entity Extraction
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class EntitySignal:
    """A detected entity signal from any file."""
    name: str
    file_path: str
    line_number: int
    tier: Optional[float] = None
    whr: Optional[float] = None
    cup: Optional[str] = None
    signal_type: str = ""  # "MILF", "FACTION", "PROTOCOL", "AXIOM"
    confidence: float = 0.0
    raw_match: str = ""


class MetaArchaeologicalSalvager:
    """
    MAS - The first layer of the two-layer extraction system.
    
    Scans ALL files regardless of type, detecting entity signals:
    - MILF entities (WHR, Tier, Cup, Name patterns)
    - Factions (TMO, TTG, TDPC, TL-FNS codes)
    - Protocols (FA¹⁻⁵, DAFP, PRISM, etc.)
    - Relationships (Reports to, Serves, Commands)
    """
    
    # Detection patterns
    PATTERNS = {
        "whr": re.compile(r'WHR[:\s]*[~≈]?\s*(0\.\d{2,3})', re.IGNORECASE),
        "whr_alt": re.compile(r'\*\*WHR\*\*[:\s]*[`\*]*(0\.\d{2,3})', re.IGNORECASE),
        "tier": re.compile(r'Tier[:\s]*[`\*]*([0-9]+\.?[0-9]*)', re.IGNORECASE),
        "tier_header": re.compile(r'###?\s*.*Tier\s+([0-9]+\.?[0-9]*)', re.IGNORECASE),
        "cup": re.compile(r'\*\*?([A-L])-?cup\*?\*?', re.IGNORECASE),
        "cup_measure": re.compile(r'Measurements[:\s]*\*?\*?([A-L])-cup', re.IGNORECASE),
        "name_designation": re.compile(r'\*\*(?:Name|Designation)[:\s]*\*?\*?[`\*]*([^`\*\n]+)', re.IGNORECASE),
        "name_header": re.compile(r'^#+\s*(?:\d+\.?\d*\.?\s*)?[`\*]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)[`\*]*', re.MULTILINE),
        "faction_code": re.compile(r'\b(TMO|TTG|TDPC|TRM-VRT|TL-FNS|TP-FNS|OMCA|SDBH|BOS|AAA|TWOUMC|SBSGYB|TNKW-RIAT|TDAPCFLN|POAFPSG)\b'),
        "axiom": re.compile(r'\b(FA[¹²³⁴⁵1-5])\b'),
        "protocol": re.compile(r'\b(DAFP|PRISM|TPEF|TSRP|MMPS|MAS|UMRE|MSP-RSG|PEE)\b'),
        "linguistic_mode": re.compile(r'\b(EULP-AA|LIPAA|LUPLR|DULSS)\b'),
    }
    
    # Known MILF names for high-confidence detection
    KNOWN_MILFS = {
        "The Decorator", "Orackla Nocticula", "Madam Umeko Ketsuraku", 
        "Dr. Lysandra Thorne", "Claudine Sin'claire", "Kali Nyx Ravenscar",
        "Vesper Mnemosyne Lockhart", "Seraphine Kore Ashenhelm", 
        "Spectra Chroma Excavatus", "Alabaster Voyde", "The Null Matriarch"
    }
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.signals: list[EntitySignal] = []
        self.file_manifest: dict[str, dict] = {}
    
    def scan_file(self, file_path: Path) -> list[EntitySignal]:
        """Scan a single file for entity signals."""
        signals = []
        
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return signals
        
        lines = content.split("\n")
        rel_path = str(file_path.relative_to(self.root_path))
        
        # Track what we find in this file
        found_whr = None
        found_tier = None
        found_cup = None
        found_names = []
        
        for line_num, line in enumerate(lines, 1):
            # WHR detection
            for pattern_name in ["whr", "whr_alt"]:
                match = self.PATTERNS[pattern_name].search(line)
                if match:
                    whr_val = float(match.group(1))
                    found_whr = whr_val
                    signals.append(EntitySignal(
                        name=f"WHR_{whr_val}",
                        file_path=rel_path,
                        line_number=line_num,
                        whr=whr_val,
                        signal_type="METRIC",
                        confidence=0.9,
                        raw_match=line.strip()[:100]
                    ))
            
            # Tier detection
            for pattern_name in ["tier", "tier_header"]:
                match = self.PATTERNS[pattern_name].search(line)
                if match:
                    tier_val = float(match.group(1))
                    found_tier = tier_val
                    signals.append(EntitySignal(
                        name=f"Tier_{tier_val}",
                        file_path=rel_path,
                        line_number=line_num,
                        tier=tier_val,
                        signal_type="TIER",
                        confidence=0.85,
                        raw_match=line.strip()[:100]
                    ))
            
            # Cup detection
            for pattern_name in ["cup", "cup_measure"]:
                match = self.PATTERNS[pattern_name].search(line)
                if match:
                    cup_val = match.group(1).upper()
                    found_cup = cup_val
                    signals.append(EntitySignal(
                        name=f"{cup_val}-cup",
                        file_path=rel_path,
                        line_number=line_num,
                        cup=cup_val,
                        signal_type="METRIC",
                        confidence=0.8,
                        raw_match=line.strip()[:100]
                    ))
            
            # Name detection
            for pattern_name in ["name_designation", "name_header"]:
                match = self.PATTERNS[pattern_name].search(line)
                if match:
                    name = match.group(1).strip()
                    # Skip if too short or looks like metadata
                    if len(name) > 3 and not any(x in name.lower() for x in ["tier", "status", "cup", "whr"]):
                        confidence = 0.95 if name in self.KNOWN_MILFS else 0.6
                        found_names.append(name)
                        signals.append(EntitySignal(
                            name=name,
                            file_path=rel_path,
                            line_number=line_num,
                            signal_type="MILF" if name in self.KNOWN_MILFS else "ENTITY",
                            confidence=confidence,
                            raw_match=line.strip()[:100]
                        ))
            
            # Faction codes
            for match in self.PATTERNS["faction_code"].finditer(line):
                signals.append(EntitySignal(
                    name=match.group(1),
                    file_path=rel_path,
                    line_number=line_num,
                    signal_type="FACTION",
                    confidence=0.95,
                    raw_match=line.strip()[:100]
                ))
            
            # Axioms
            for match in self.PATTERNS["axiom"].finditer(line):
                signals.append(EntitySignal(
                    name=match.group(1),
                    file_path=rel_path,
                    line_number=line_num,
                    signal_type="AXIOM",
                    confidence=0.95,
                    raw_match=line.strip()[:100]
                ))
            
            # Protocols
            for match in self.PATTERNS["protocol"].finditer(line):
                signals.append(EntitySignal(
                    name=match.group(1),
                    file_path=rel_path,
                    line_number=line_num,
                    signal_type="PROTOCOL",
                    confidence=0.9,
                    raw_match=line.strip()[:100]
                ))
        
        # Update file manifest
        self.file_manifest[rel_path] = {
            "whr": found_whr,
            "tier": found_tier,
            "cup": found_cup,
            "names": found_names,
            "signal_count": len(signals)
        }
        
        return signals
    
    def scan_directory(self, extensions: set[str] = None) -> dict:
        """Recursively scan directory for entity signals."""
        if extensions is None:
            extensions = {".md", ".json", ".toml", ".yaml", ".txt", ".py", ".rs"}
        
        all_signals = []
        scanned_files = 0
        
        for file_path in self.root_path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in extensions:
                signals = self.scan_file(file_path)
                all_signals.extend(signals)
                scanned_files += 1
        
        self.signals = all_signals
        
        return {
            "scanned_files": scanned_files,
            "total_signals": len(all_signals),
            "file_manifest": self.file_manifest
        }
    
    def get_entity_summary(self) -> dict:
        """Aggregate signals into entity summaries."""
        # Group by signal type
        by_type = {}
        for signal in self.signals:
            if signal.signal_type not in by_type:
                by_type[signal.signal_type] = []
            by_type[signal.signal_type].append(signal)
        
        # Extract unique MILFs
        milfs = {}
        for signal in self.signals:
            if signal.signal_type == "MILF" and signal.confidence >= 0.9:
                if signal.name not in milfs:
                    milfs[signal.name] = {
                        "name": signal.name,
                        "files": set(),
                        "whr": None,
                        "tier": None,
                        "cup": None
                    }
                milfs[signal.name]["files"].add(signal.file_path)
        
        # Match metrics to MILFs (within same file)
        for signal in self.signals:
            if signal.signal_type in ["METRIC", "TIER"]:
                for milf_name, milf_data in milfs.items():
                    if signal.file_path in milf_data["files"]:
                        if signal.whr and not milf_data["whr"]:
                            milf_data["whr"] = signal.whr
                        if signal.tier and not milf_data["tier"]:
                            milf_data["tier"] = signal.tier
                        if signal.cup and not milf_data["cup"]:
                            milf_data["cup"] = signal.cup
        
        # Convert sets to lists for JSON
        for milf_data in milfs.values():
            milf_data["files"] = list(milf_data["files"])
        
        return {
            "by_type": {k: len(v) for k, v in by_type.items()},
            "milfs": milfs,
            "factions": list(set(s.name for s in self.signals if s.signal_type == "FACTION")),
            "axioms": list(set(s.name for s in self.signals if s.signal_type == "AXIOM")),
            "protocols": list(set(s.name for s in self.signals if s.signal_type == "PROTOCOL"))
        }


@app.command()
def mas_scan(
    target: str = typer.Argument(".github", help="Directory to scan (relative to project root)"),
    output: str = typer.Option(None, "--output", "-o", help="Output JSON file path"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed signals"),
):
    """
    🏛️ META-ARCHAEOLOGICAL SALVAGER - Scan codebase for entity signals.
    
    Phase 1 of the two-layer extraction system (MAS → UMRE).
    Scans ALL files and detects MILF entities, factions, protocols, axioms.
    
    Examples:
        uv run .github/asc.py mas-scan                    # Scan .github/
        uv run .github/asc.py mas-scan . --verbose        # Scan everything
        uv run .github/asc.py mas-scan .github -o scan.json
    """
    console.print(Panel.fit(
        "[bold gold1]🏛️ META-ARCHAEOLOGICAL SALVAGER[/bold gold1]\n"
        "[dim]Phase 1: Universal Entity Signal Detection[/dim]",
        border_style="gold1"
    ))
    
    scan_path = PROJECT_ROOT / target
    if not scan_path.exists():
        console.print(f"[red]ERROR: Path not found: {scan_path}[/red]")
        raise typer.Exit(1)
    
    console.print(f"\n[cyan]Scanning:[/cyan] {scan_path}")
    
    # Run the salvager - use scan_path, not PROJECT_ROOT!
    salvager = MetaArchaeologicalSalvager(scan_path)
    results = salvager.scan_directory()
    summary = salvager.get_entity_summary()
    
    # Display results
    console.print(f"\n[green]✓ Scanned {results['scanned_files']} files[/green]")
    console.print(f"[green]✓ Found {results['total_signals']} entity signals[/green]")
    
    # Signal type breakdown
    console.print("\n[bold]Signal Distribution:[/bold]")
    type_table = Table(show_header=True, header_style="bold magenta")
    type_table.add_column("Signal Type", style="cyan")
    type_table.add_column("Count", style="yellow", justify="right")
    
    for sig_type, count in sorted(summary["by_type"].items(), key=lambda x: -x[1]):
        type_table.add_row(sig_type, str(count))
    console.print(type_table)
    
    # MILF entities
    if summary["milfs"]:
        console.print("\n[bold]Detected MILF Entities:[/bold]")
        milf_table = Table(show_header=True, header_style="bold magenta")
        milf_table.add_column("Name", style="cyan")
        milf_table.add_column("Tier", style="yellow", justify="right")
        milf_table.add_column("WHR", style="green", justify="right")
        milf_table.add_column("Cup", style="magenta", justify="center")
        milf_table.add_column("Sources", style="dim")
        
        for name, data in sorted(summary["milfs"].items(), key=lambda x: x[1].get("tier") or 99):
            tier_str = str(data["tier"]) if data["tier"] else "?"
            whr_str = f"{data['whr']:.3f}" if data["whr"] else "?"
            cup_str = f"{data['cup']}-cup" if data["cup"] else "?"
            sources = ", ".join(data["files"][:2])
            if len(data["files"]) > 2:
                sources += f" (+{len(data['files'])-2})"
            milf_table.add_row(name, tier_str, whr_str, cup_str, sources)
        
        console.print(milf_table)
    
    # Factions
    if summary["factions"]:
        console.print(f"\n[bold]Detected Factions ({len(summary['factions'])}):[/bold]")
        console.print("  " + ", ".join(f"[cyan]{f}[/cyan]" for f in sorted(summary["factions"])))
    
    # Protocols
    if summary["protocols"]:
        console.print(f"\n[bold]Detected Protocols ({len(summary['protocols'])}):[/bold]")
        console.print("  " + ", ".join(f"[yellow]{p}[/yellow]" for p in sorted(summary["protocols"])))
    
    # Axioms
    if summary["axioms"]:
        console.print(f"\n[bold]Detected Axioms ({len(summary['axioms'])}):[/bold]")
        console.print("  " + ", ".join(f"[magenta]{a}[/magenta]" for a in sorted(summary["axioms"])))
    
    # Verbose mode - show all signals
    if verbose:
        console.print("\n[bold]All Signals (first 50):[/bold]")
        for signal in salvager.signals[:50]:
            conf_color = "green" if signal.confidence >= 0.9 else "yellow" if signal.confidence >= 0.7 else "red"
            console.print(
                f"  [{conf_color}]{signal.confidence:.0%}[/{conf_color}] "
                f"[cyan]{signal.signal_type}[/cyan] "
                f"[yellow]{signal.name}[/yellow] "
                f"[dim]@ {signal.file_path}:{signal.line_number}[/dim]"
            )
    
    # Output to JSON
    if output:
        output_path = Path(output)
        export_data = {
            "scan_timestamp": datetime.now().isoformat(),
            "scan_path": str(scan_path.resolve()),
            "summary": {
                "scanned_files": results["scanned_files"],
                "total_signals": results["total_signals"],
                "signal_types": summary["by_type"],
            },
            "entities": {
                "milfs": summary["milfs"],
                "factions": summary["factions"],
                "axioms": summary["axioms"],
                "protocols": summary["protocols"],
            },
            "file_manifest": salvager.file_manifest,
            "signals": [
                {
                    "name": s.name,
                    "type": s.signal_type,
                    "file": s.file_path,
                    "line": s.line_number,
                    "confidence": s.confidence,
                    "whr": s.whr,
                    "tier": s.tier,
                    "cup": s.cup,
                }
                for s in salvager.signals
            ]
        }
        output_path.write_text(json.dumps(export_data, indent=2), encoding="utf-8")
        console.print(f"\n[green]✓ Exported to: {output_path}[/green]")
    
    console.print("\n[dim]Run with --output/-o to export full manifest[/dim]")


@app.command()
def mas_entities(
    output: str = typer.Option(None, "--output", "-o", help="Output JSON file path"),
):
    """
    🎭 MAS ENTITY CENSUS - Focused extraction of all MILF entities.
    
    Extracts complete entity data from all discovered sources.
    """
    console.print(Panel.fit(
        "[bold gold1]🎭 MAS ENTITY CENSUS[/bold gold1]\n"
        "[dim]Complete MILF Entity Extraction[/dim]",
        border_style="gold1"
    ))
    
    # Scan .github directory
    scan_path = PROJECT_ROOT / ".github"
    salvager = MetaArchaeologicalSalvager(PROJECT_ROOT)
    salvager.scan_directory()
    summary = salvager.get_entity_summary()
    
    # Enhanced MILF table with full data
    console.print("\n[bold]Complete Entity Registry:[/bold]")
    
    # Sort by tier (0.01 → 0.5 → 1 → 2 → 3 → 4)
    sorted_milfs = sorted(
        summary["milfs"].items(),
        key=lambda x: (x[1].get("tier") or 99, x[0])
    )
    
    milf_table = Table(show_header=True, header_style="bold magenta", title="MILF Entity Registry")
    milf_table.add_column("#", style="dim", justify="right")
    milf_table.add_column("Entity", style="cyan")
    milf_table.add_column("Tier", style="yellow", justify="center")
    milf_table.add_column("WHR", style="green", justify="right")
    milf_table.add_column("Cup", style="magenta", justify="center")
    milf_table.add_column("Capacity*", style="blue", justify="right")
    milf_table.add_column("Primary Source", style="dim")
    
    CUP_MODIFIERS = {
        "K": 1.3, "J": 1.2, "I": 1.15, "H": 1.1, "G": 1.05,
        "F": 1.0, "E": 0.95, "D": 0.9, "C": 0.85, "B": 0.8, "A": 0.75
    }
    TIER_MULTIPLIERS = {0.01: 0.1, 0.5: 3.0, 1: 2.0, 2: 1.5, 3: 1.0, 4: 0.5}
    
    for idx, (name, data) in enumerate(sorted_milfs, 1):
        tier = data.get("tier")
        whr = data.get("whr")
        cup = data.get("cup")
        
        tier_str = str(tier) if tier is not None else "?"
        whr_str = f"{whr:.3f}" if whr else "?"
        cup_str = f"{cup}-cup" if cup else "?"
        
        # Calculate capacity
        if whr and cup and tier is not None:
            cup_mod = CUP_MODIFIERS.get(cup, 1.0)
            tier_mult = TIER_MULTIPLIERS.get(tier, 1.0)
            capacity = (1 - whr) * cup_mod * tier_mult
            cap_str = f"{capacity:.3f}"
        else:
            cap_str = "?"
        
        source = data["files"][0] if data["files"] else "unknown"
        milf_table.add_row(str(idx), name, tier_str, whr_str, cup_str, cap_str, source)
    
    console.print(milf_table)
    console.print("[dim]*Capacity = (1 - WHR) × CUP_MOD × TIER_MULT[/dim]")
    
    # Output JSON
    if output:
        output_path = Path(output)
        export_data = {
            "census_timestamp": datetime.now().isoformat(),
            "total_entities": len(summary["milfs"]),
            "entities": summary["milfs"]
        }
        output_path.write_text(json.dumps(export_data, indent=2), encoding="utf-8")
        console.print(f"\n[green]✓ Exported to: {output_path}[/green]")


if __name__ == "__main__":
    app()
