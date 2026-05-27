#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: models.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🏰 THE FORTRESS
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
models.py — Script logic for models.py.

@SID:           TOOL_MODELS_V1
@Shabti:        CLI Script
@Purpose:       Script logic for models.py.
"""

from dataclasses import dataclass, field
from typing import Optional, Annotated, List, Dict, Any, Tuple
from pydantic import BaseModel, Field, field_validator
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════════
# LORE EXTRACTION MODELS
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


# ═══════════════════════════════════════════════════════════════════════════════
# PYDANTIC MODELS (Mirror of Rust types)
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
    dimensions_meters: List[float]
    tier_requirement: Optional[float] = None
    boss: Optional[str] = None
    description: str


class WorldData(BaseModel):
    """World structure - mirrors WorldData in types.rs"""
    name: str
    layers: List[WorldLayer]


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
    entities: List[Entity]
    world: WorldData


# ═══════════════════════════════════════════════════════════════════════════════
# MILF-CORE WORLD MODELS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class AxiomDiscipline:
    """Foundational Axiom as learnable discipline"""
    id: str
    name: str
    axiom_source: str
    description: str
    governing_principle: str
    dialectical_pair: Optional[str] = None
    operational_modes: List[str] = field(default_factory=list)
    matriarchal_patron: Optional[str] = None
    resonance_axis: Optional[str] = None


@dataclass
class LensOperator:
    """Φ-Operator as perceptual modality"""
    id: str
    name: str
    operator_source: str
    description: str
    primary_discipline: str
    signature_technique: str
    operational_role: str
    secondary_discipline: Optional[str] = None
    gestalt_manifestation: Optional[str] = None


@dataclass
class TetrahedralResonance:
    """4-axis cosmological position"""
    void_steel: float = 0.0
    truth_mystery: float = 0.0
    ordeal_comfort: float = 0.0
    raw_ornate: float = 0.0
    
    def vertex_affinities(self) -> Dict[str, float]:
        return {
            "Void (Orackla)": max(0, -self.void_steel) * max(0, -self.truth_mystery),
            "Steel (Umeko)": max(0, self.void_steel) * 0.75,
            "Truth (Lysandra)": max(0, self.truth_mystery) * 0.75,
            "Salt (Claudine)": max(0, -self.ordeal_comfort) * 0.75,
            "Ornate (Decorator)": max(0, self.raw_ornate) * max(0, self.ordeal_comfort),
        }
    
    def dominant_vertex(self) -> str:
        affinities = self.vertex_affinities()
        return max(affinities, key=affinities.get)


@dataclass
class MatriarchalFaction:
    """Faction with ideology"""
    id: str
    name: str
    tier: float
    ideology: str
    headquarters: Optional[str] = None
    matriarch: Optional[str] = None
    resonance_tendency: Optional[TetrahedralResonance] = None
    joinable: bool = True
    discipline_requirements: Dict[str, int] = field(default_factory=dict)
    resonance_requirements: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    faction_techniques: List[str] = field(default_factory=list)
    hierarchy_effects: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ArchiveLocation:
    """World location"""
    id: str
    name: str
    layer_type: str
    tier_requirement: float
    dimensions: Tuple[float, float]
    description: str
    ambient_resonance: str
    guardian: Optional[str] = None
    entity_density: str = "medium"
    encounter_types: List[str] = field(default_factory=list)
    associated_faction: Optional[str] = None
    key_artifacts: List[str] = field(default_factory=list)
    available_ordeals: List[str] = field(default_factory=list)
    hazards: List[str] = field(default_factory=list)
    hidden_chambers: int = 0


@dataclass
class LinguisticArsenal:
    """Linguistic Mode as reality-manipulation weapon"""
    id: str
    name: str
    mode_source: str
    matriarchal_origin: str
    governing_vertex: str
    description: str
    speaking_pattern: str
    passive_activation: int = 10
    signature_interventions: List[str] = field(default_factory=list)
    resonance_cost: float = 0.0
    synergy_modes: List[str] = field(default_factory=list)


@dataclass
class MILFCoreWorldData:
    """Complete MILF-core world database"""
    meta: Dict[str, Any]
    disciplines: List[AxiomDiscipline]
    operators: List[LensOperator]
    factions: List[MatriarchalFaction]
    locations: List[ArchiveLocation]
    arsenals: List[LinguisticArsenal]
    entities: List[Dict[str, Any]]
    cosmology: Dict[str, Any]
    resonances: List[Any] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════════
# MAS SIGNAL MODELS
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
    signal_type: str = ""
    confidence: float = 0.0
    raw_match: str = ""
