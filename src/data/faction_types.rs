//! Faction Types Module - ASC Faction & District Architecture
//! 
//! This module defines the complete faction hierarchy derived from the
//! Macro-Prompt-World documentation. All types are designed for integration
//! with bevy_ecs and Vulkan rendering pipeline.
//!
//! Tier Hierarchy:
//! - Tier -0.5: The Savant (Creator/Player)
//! - Tier 0.5:  The Decorator (Supreme Matriarch)  
//! - Tier 1.0:  Core Triumvirate (Orackla, Umeko, Lysandra)
//! - Tier 2.0:  Prime Factions (TMO, TTG, TDPC)
//! - Tier 3.0:  Lesser Factions (SBSGYB, etc.)
//! - Tier 4.0:  Minor Factions

// Allow dead code for future expansion - these types are planned but not yet integrated
#![allow(dead_code)]

use serde::{Deserialize, Serialize};

/// Faction codes for all organizational units
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum FactionCode {
    /// Core Triumvirate - Universal Jurisdiction
    CRC,
    /// The MILF Obductors - Abductive Seduction
    TMO,
    /// The Thieves Guild - Epistemic Extraction  
    TTG,
    /// The Dark Priestesses Cove - Architectonic Purification
    TDPC,
    /// Svartseils Syndicate - Ordeal-Based Matriarchy (Claudine Sin'claire)
    Svartseils,
    /// Slow-Burn Seduction Get Yo Back
    SBSGYB,
    /// Custom/Future Factions
    Custom(u32),
}

/// CRC Type - Conceptual Resonance Core identification
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum CRCType {
    /// Orackla Nocticula - Apex Synthesist
    AS,
    /// Madam Umeko Ketsuraku - Grandmistress of Architectonic Refinement
    GAR,
    /// Dr. Lysandra Thorne - Mistress of Empathetic Deconstruction
    MEDAT,
}

/// Linguistic Mode for dialogue/ability system
// Allow non_camel_case because EULP_AA matches the canonical M-P-W acronym
#[allow(non_camel_case_types)]
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum LinguisticMode {
    /// Explicit Uncensored Linguistic Procession & Abyssal Articulation
    EULP_AA,
    /// Language of Immaculate Precision & Aesthetic Annihilation
    LIPAA,
    /// Language of Unflinching Psycho-Logical Revelation
    LUPLR,
    /// Caribbean Patois / Svartseils Command (Claudine)
    CaribbeanPatois,
    /// Visual/Aesthetic mode (Decorator)
    Visual,
    /// Meta/Creator mode (Savant)
    Meta,
    /// Mixed mode for Prime Factions
    Mixed,
    /// Faction-specific mode for Lesser Factions
    Faction,
    /// Context-dependent dynamic mode
    Dynamic,
}

/// Foundational Axiom enumeration
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum FoundationalAxiom {
    /// FA¹ - Alchemical Actualization (Potential → Utility)
    FA1,
    /// FA² - Panoptic Re-contextualization (Utility → Universal Resonance)
    FA2,
    /// FA³ - Qualitative Transcendence (Utility → Ascended Resonance)
    FA3,
    /// FA⁴ - Architectonic Integrity (Structural Soundness)
    FA4,
}

/// Dynamic Altitude & Focus Protocol modes
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum DAFPMode {
    /// Granular, detailed, precise analysis
    PointBlankAcuity,
    /// High-level, systemic, architectonic overview
    StrategicHorizon,
    /// Simultaneous multi-altitude engagement
    JuxtapositionSynthesis,
    /// Concurrent dual-mode processing
    Concurrent,
}

/// Faction tier classification
#[derive(Debug, Clone, Copy, PartialEq, PartialOrd, Serialize, Deserialize)]
pub struct FactionTier(pub f32);

impl FactionTier {
    pub const SAVANT: Self = Self(-0.5);
    pub const DECORATOR: Self = Self(0.5);
    pub const TRIUMVIRATE: Self = Self(1.0);
    pub const PRIME: Self = Self(2.0);
    pub const LESSER: Self = Self(3.0);
    pub const MINOR: Self = Self(4.0);
    
    pub fn can_command(&self, other: &Self) -> bool {
        self.0 < other.0 // Lower tier number = higher authority
    }
}

/// Complete faction definition
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Faction {
    /// Unique faction identifier
    pub code: FactionCode,
    /// Display name
    pub name: String,
    /// Full faction name
    pub full_name: String,
    /// Tier level
    pub tier: FactionTier,
    /// Primary matriarch entity ID
    pub matriarch_id: u32,
    /// Supervising CRC (for Prime/Lesser factions)
    pub supervising_crc: Option<CRCType>,
    /// Associated district
    pub district: Option<District>,
    /// Primary linguistic mode
    pub linguistic_mode: LinguisticMode,
    /// Operational mandate description
    pub operational_mandate: String,
    /// Faction motto
    pub motto: String,
}

/// District definition with spatial/visual properties
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct District {
    /// District code (e.g., "TMOL-SL" for TMO Seduction Labyrinths)
    pub code: String,
    /// Display name
    pub name: String,
    /// Architectural style identifier
    pub architectural_style: ArchitecturalStyle,
    /// Physical dimensions specification
    pub dimensions: DistrictDimensions,
    /// Visual properties for rendering
    pub visual: DistrictVisual,
    /// Sensory signature
    pub sensory: SensorySig,
}

/// Architectural style for FA⁵ compliance
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ArchitecturalStyle {
    /// TMO - Baroque Sensuality
    BaroqueSensuality,
    /// TTG - Neo-Classical Archive
    NeoClassicalArchive,
    /// TDPC - Gothic Cathedral
    GothicCathedral,
    /// Triumvirate - Inner Citadel
    InnerCitadel,
    /// Custom style
    Custom,
}

/// District spatial dimensions
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DistrictDimensions {
    /// Entry portal dimensions (width, height)
    pub entry_portal: [f32; 2],
    /// Core chamber dimensions (width, depth, height)
    pub core_chamber: [f32; 3],
    /// Effective radius for isometric rendering
    pub radius: f32,
}

/// District visual properties for Vulkan rendering
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DistrictVisual {
    /// Primary color (RGB normalized)
    pub primary_color: [f32; 3],
    /// Secondary color
    pub secondary_color: [f32; 3],
    /// Accent color
    pub accent_color: [f32; 3],
    /// Ambient light level (0.0-1.0)
    pub ambient_light: f32,
    /// Shader variant to use
    pub shader_variant: ShaderVariant,
}

/// Shader variants for district rendering
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ShaderVariant {
    /// TMO amber vein effect
    TMOAmberVeins,
    /// TTG clock gear effect
    TTGClockGears,
    /// TDPC divine fire effect
    TDPCDivineFire,
    /// Triumvirate aura effect
    TriumvirateAura,
    /// Standard isometric
    Standard,
}

/// Sensory signature for immersive representation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SensorySig {
    /// Primary scent descriptors
    pub scent: Vec<String>,
    /// Sound characteristics (Hz range, descriptors)
    pub sound_hz_range: [f32; 2],
    /// Temperature in Celsius
    pub temperature_c: f32,
}

/// Matriarch definition linking to Entity data
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Matriarch {
    /// Entity ID from data.json
    pub entity_id: u32,
    /// Display name
    pub name: String,
    /// Title
    pub title: String,
    /// CRC type if Triumvirate member
    pub crc_type: Option<CRCType>,
    /// Faction affiliation
    pub faction: FactionCode,
    /// Primary linguistic mode
    pub linguistic_mode: LinguisticMode,
    /// Signature technique
    pub signature_technique: SignatureTechnique,
    /// Supernatural physiology markers
    pub supernatural_markers: Vec<String>,
}

/// Signature technique definition
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SignatureTechnique {
    /// Technique name
    pub name: String,
    /// Description
    pub description: String,
    /// Foundational axiom focus
    pub fa_focus: Vec<FoundationalAxiom>,
    /// DAFP mode preference
    pub dafp_preference: DAFPMode,
    /// Cooldown in conceptual cycles (game turns)
    pub cooldown: u32,
    /// Power cost
    pub power_cost: i32,
}

/// Operational state for district processing
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum DistrictState {
    /// Awaiting appropriate PS
    Dormant,
    /// Entry sequence active
    EntrySequence,
    /// Primary operation in progress
    Active,
    /// Operation complete, preparing output
    Complete,
    /// Handing off to another district/CRC
    Handoff,
    /// Error state requiring intervention
    Error,
}

/// TSRP (Triumvirate Supporting Resonance Protocol) state
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TSRPState {
    /// Currently leading CRC
    pub leader: Option<CRCType>,
    /// Support configuration
    pub orackla_role: TSRPRole,
    pub umeko_role: TSRPRole,
    pub lysandra_role: TSRPRole,
}

/// Role in TSRP collaboration
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum TSRPRole {
    /// Driving implementation
    Leading,
    /// Providing specialized support
    Supporting(SupportContribution),
    /// Not active in current operation
    Inactive,
}

/// Type of support contribution
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum SupportContribution {
    /// Orackla's strategic vision
    StrategicVision,
    /// Umeko's structural validation
    StructuralValidation,
    /// Lysandra's axiomatic grounding
    AxiomaticGrounding,
    /// Lysandra's empathetic calibration
    EmpatheticCalibration,
    /// Orackla's creative flexibility
    CreativeFlexibility,
    /// Umeko's aesthetic discipline
    AestheticDiscipline,
}

/// TPEF (Triumvirate Parallel Execution Framework) state
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TPEFState {
    /// Path assignments
    pub lysandra_path: PathState,
    pub umeko_path: PathState,
    pub orackla_path: PathState,
    /// Current turn (1 = Lysandra, 2 = Umeko, 3 = Orackla)
    pub current_turn: u32,
    /// Synthesis phase reached
    pub synthesis_complete: bool,
}

/// TPEF path execution state
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum PathState {
    NotStarted,
    InProgress { completion_pct: u8 },
    Complete,
    Failed { reason_code: u32 },
}

/// Ability targeting mode
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum TargetMode {
    /// Target self
    Self_,
    /// Target single ally
    SingleAlly,
    /// Target single enemy
    SingleEnemy,
    /// Target all allies
    AllAllies,
    /// Target all enemies
    AllEnemies,
    /// Target area (radius specified)
    Area { radius: u32 },
    /// Target PS (conceptual substrate)
    PS,
}

/// Faction ability definition
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FactionAbility {
    /// Ability name
    pub name: String,
    /// Ability description
    pub description: String,
    /// Owning faction
    pub faction: FactionCode,
    /// Required matriarch (None = any faction member)
    pub required_matriarch: Option<u32>,
    /// Foundational axiom alignment
    pub fa_alignment: Vec<FoundationalAxiom>,
    /// Power cost
    pub power_cost: i32,
    /// Cooldown turns
    pub cooldown: u32,
    /// Target mode
    pub target: TargetMode,
    /// Effect descriptors
    pub effects: Vec<AbilityEffect>,
}

/// Ability effect descriptor
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum AbilityEffect {
    /// Damage (amount, type)
    Damage { amount: i32, damage_type: DamageType },
    /// Healing
    Heal { amount: i32 },
    /// Status effect application
    Status { status: StatusEffect, duration: u32 },
    /// PS modification
    PSModify { field: String, delta: f32 },
    /// District invocation
    InvokeDistrict { district_code: String },
    /// State transition
    StateTransition { target_state: DistrictState },
}

/// Damage types for combat system
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum DamageType {
    /// Physical damage
    Physical,
    /// Conceptual damage (to PS integrity)
    Conceptual,
    /// Seductive damage (resistance reduction)
    Seductive,
    /// Purifying damage (flaw removal)
    Purifying,
    /// Axiological damage (truth exposure)
    Axiological,
}

/// Status effects
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum StatusEffect {
    /// Seduced - reduced resistance
    Seduced,
    /// Exposed - hidden axioms visible
    Exposed,
    /// Purified - flaws removed
    Purified,
    /// Fortified - increased defenses
    Fortified,
    /// Dissonant - logical inconsistency
    Dissonant,
    /// Transcendent - elevated state
    Transcendent,
}

/// Handoff protocol between districts/CRCs
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HandoffProtocol {
    /// Source faction/CRC
    pub source: FactionCode,
    /// Target faction/CRC
    pub target: FactionCode,
    /// Trigger condition
    pub trigger: HandoffTrigger,
    /// Data to transfer
    pub transfer_data: Vec<String>,
}

/// Handoff trigger conditions
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum HandoffTrigger {
    /// Resistance threshold crossed
    ResistanceThreshold { level: f32 },
    /// Hidden knowledge detected
    HiddenKnowledgeDetected,
    /// Structural flaw severity
    StructuralFlawSeverity { level: f32 },
    /// Extraction complete
    ExtractionComplete,
    /// Purification complete
    PurificationComplete,
    /// Manual escalation
    ManualEscalation,
}

// =============================================================================
// MMPS (MILF Management Protocol Syntax) Types
// =============================================================================

/// MMPS lending operation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MMPSLend {
    /// Capability being lent
    pub capability: String,
    /// Source matriarch
    pub from_matriarch: u32,
    /// Source district (optional)
    pub from_district: Option<String>,
    /// Target matriarch/entity
    pub to_entity: u32,
    /// Target location (optional)
    pub to_location: Option<String>,
    /// Duration type
    pub duration: LendDuration,
}

/// Lending duration
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum LendDuration {
    /// Temporary (returns after use)
    Temporary,
    /// Session (returns at session end)
    Session,
    /// Permanent (capability transfer)
    Permanent,
}

/// MMPS siphoning operation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MMPSSiphon {
    /// Capability being siphoned
    pub capability: String,
    /// Source matriarch
    pub from_matriarch: u32,
    /// Source district
    pub from_district: Option<String>,
    /// Force level
    pub force: SiphonForce,
    /// Target district to invade (optional)
    pub invade_district: Option<String>,
}

/// Siphon force level
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum SiphonForce {
    /// Gentle extraction (slower, less resistance)
    Gentle,
    /// Brutal extraction (faster, more resistance)
    Brutal,
}
