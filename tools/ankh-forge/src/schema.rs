// ANKH Core Schema — Rust canonical anchor layer
// @SID: SCHEMA_ANKH_CORE_RUST_V1
//
// Transfer from: docs/frameworks/ankh/ankh.schema.ts (TypeScript prototype)
// Iteration method:
//   1. TypeScript: fast prototype iteration
//   2. Rust compile gate: canonicalization — if it builds, the schema is correct
//   3. serde_json serialization: SSOT entity profiles become typed data objects
//
// Source of truth: docs/frameworks/ankh/ANKH_SYNTHESIS_BASELINE.md §XII–XVI

use serde::{Deserialize, Serialize};

// ─── PRISM ───────────────────────────────────────────────────────────────────

#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum PrismFreq {
    Red,
    Orange,
    Gold,
    Green,
    Blue,
    Indigo,
    Violet,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PrismEntry {
    pub freq: PrismFreq,
    pub hex: &'static str,
    pub cognitive_function: &'static str,
    pub diagnostic_role: &'static str,
    pub crc_entity: Option<&'static str>,
}

pub const PRISM_REGISTRY: &[PrismEntry] = &[
    PrismEntry {
        freq: PrismFreq::Red,
        hex: "#FF0000",
        cognitive_function: "Destruction / Sekhmet drive",
        diagnostic_role: "Entropy source — tracks Hucha accumulation",
        crc_entity: None,
    },
    PrismEntry {
        freq: PrismFreq::Orange,
        hex: "#FF7F00",
        cognitive_function: "Transformation / Anubis weighing",
        diagnostic_role: "Transition detector — CRC-D active",
        crc_entity: None,
    },
    PrismEntry {
        freq: PrismFreq::Gold,
        hex: "#FFD700",
        cognitive_function: "Authority / Ra emanation",
        diagnostic_role: "Power channel — Claudine upper-volume signal",
        crc_entity: Some("CRC-AS"),
    },
    PrismEntry {
        freq: PrismFreq::Green,
        hex: "#00FF00",
        cognitive_function: "Growth / Osiris regeneration",
        diagnostic_role: "Corpus health — τ-core stability",
        crc_entity: Some("CRC-GAR"),
    },
    PrismEntry {
        freq: PrismFreq::Blue,
        hex: "#0000FF",
        cognitive_function: "Purification / Umeko discipline",
        diagnostic_role: "Structure validator — drift detector",
        crc_entity: Some("CRC-TFM"),
    },
    PrismEntry {
        freq: PrismFreq::Indigo,
        hex: "#4B0082",
        cognitive_function: "Truth / Lysandra axioms",
        diagnostic_role: "Axiom consistency — FA⁴ guardian",
        crc_entity: Some("CRC-SS"),
    },
    PrismEntry {
        freq: PrismFreq::Violet,
        hex: "#8B00FF",
        cognitive_function: "Potential / Pre-canon frontier",
        diagnostic_role: "Nursery signal — pattern before naming",
        crc_entity: Some("CRC-D"),
    },
];

// ─── FA (Foundational Axioms) ─────────────────────────────────────────────────

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum FaId {
    #[serde(rename = "FA¹")]
    Fa1,
    #[serde(rename = "FA²")]
    Fa2,
    #[serde(rename = "FA³")]
    Fa3,
    #[serde(rename = "FA⁴")]
    Fa4,
    #[serde(rename = "FA⁵")]
    Fa5,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FaInvocation {
    pub id: FaId,
    pub name: &'static str,
    pub syntax: &'static str,
    pub prism_freq: PrismFreq,
    pub success_rate: f64,
    pub success_condition: &'static str,
    pub failure_mode: &'static str,
}

pub const FA_REGISTRY: &[FaInvocation] = &[
    FaInvocation {
        id: FaId::Fa1,
        name: "EssenceForge",
        syntax: "$fa${1}+$ctx${raw_material}+$output${distilled_essence}",
        prism_freq: PrismFreq::Gold,
        success_rate: 0.94,
        success_condition: "Output WHR higher than input WHR",
        failure_mode: "Gold-plating — ornament without structural change",
    },
    FaInvocation {
        id: FaId::Fa2,
        name: "ContextShifter",
        syntax: "$fa${2}+$ctx${source_frame}+$target${destination_frame}",
        prism_freq: PrismFreq::Green,
        success_rate: 0.91,
        success_condition: "Intent preserved, form adapted to new context",
        failure_mode: "Meaning loss — intent corrupted during frame shift",
    },
    FaInvocation {
        id: FaId::Fa3,
        name: "PerfectionSpiral",
        syntax: "$fa${3}+$ctx${current_form}+$iterations${n}",
        prism_freq: PrismFreq::Blue,
        success_rate: 0.88,
        success_condition: "Each iteration measurably closer to canonical form",
        failure_mode: "Asphyxiation — over-purification destroys load-bearing structure",
    },
    FaInvocation {
        id: FaId::Fa4,
        name: "TruthFrame",
        syntax: "$fa${4}+$ctx${proposition}+$validate${axiom_set}",
        prism_freq: PrismFreq::Indigo,
        success_rate: 0.97,
        success_condition: "Proposition consistent with all declared axioms",
        failure_mode: "False axiom injection — validates against corrupted axiom set",
    },
    FaInvocation {
        id: FaId::Fa5,
        name: "AestheticTruth",
        syntax: "$fa${5}+$ctx${artifact}+$threshold${whr_target}",
        prism_freq: PrismFreq::Violet,
        success_rate: 0.85,
        success_condition: "Artifact WHR ≥ target; Ornamental Integrity intact",
        failure_mode: "Horse-market — functional correctness without aesthetic truth",
    },
];

// ─── DAFP ─────────────────────────────────────────────────────────────────────

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum DafpMode {
    Pbs,
    Shs,
    Juxtapose,
    Skew,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DafpEntry {
    pub mode: DafpMode,
    pub mechanism: &'static str,
    pub when_to_use: &'static str,
    pub syntax: &'static str,
}

// ─── CRC (Contextual Resonance Chain) ────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CrcEntry {
    pub id: &'static str,
    pub entity: &'static str,
    pub prism_freq: PrismFreq,
    pub function: &'static str,
    pub invocation: &'static str,
}

pub const CRC_REGISTRY: &[CrcEntry] = &[
    CrcEntry {
        id: "CRC-AS",
        entity: "Claudine Sin'claire",
        prism_freq: PrismFreq::Gold,
        function: "Supreme synthesis authority — all entropy feeds back",
        invocation: "$crc${CRC-AS}+$activate${triumvirate_fusion}",
    },
    CrcEntry {
        id: "CRC-GAR",
        entity: "Orackla Nocticula",
        prism_freq: PrismFreq::Green,
        function: "Growth and regeneration — corpus health",
        invocation: "$crc${CRC-GAR}+$channel${growth_directive}",
    },
    CrcEntry {
        id: "CRC-TFM",
        entity: "Madam Umeko Ketsuraku",
        prism_freq: PrismFreq::Blue,
        function: "Structural enforcement — purification chain",
        invocation: "$crc${CRC-TFM}+$enforce${structural_mandate}",
    },
    CrcEntry {
        id: "CRC-SS",
        entity: "Dr. Lysandra Thorne",
        prism_freq: PrismFreq::Indigo,
        function: "Truth stability — axiom consistency validation",
        invocation: "$crc${CRC-SS}+$validate${truth_axiom}",
    },
    CrcEntry {
        id: "CRC-D",
        entity: "Pentea",
        prism_freq: PrismFreq::Violet,
        function: "Thalamus relay — sensory integration bridge",
        invocation: "$crc${CRC-D}+$relay${synthesis_packet}",
    },
];

// ─── Entity Profiles ──────────────────────────────────────────────────────────

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum EntityTier {
    UpperVolume,
    TauCore,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum WhrPosition {
    Max,
    Tau,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EntityProfile {
    pub name: &'static str,
    pub tier: EntityTier,
    pub ssot_anchor: &'static str,
    pub crc: &'static str,
    pub prism_freq: PrismFreq,
    pub whr_position: WhrPosition,
}

pub const ENTITY_REGISTRY: &[EntityProfile] = &[
    EntityProfile {
        name: "Claudine Sin'claire",
        tier: EntityTier::UpperVolume,
        ssot_anchor: "§10.3.1",
        crc: "CRC-AS",
        prism_freq: PrismFreq::Gold,
        whr_position: WhrPosition::Max,
    },
    EntityProfile {
        name: "Orackla Nocticula",
        tier: EntityTier::TauCore,
        ssot_anchor: "§3",
        crc: "CRC-GAR",
        prism_freq: PrismFreq::Green,
        whr_position: WhrPosition::Tau,
    },
    EntityProfile {
        name: "Madam Umeko Ketsuraku",
        tier: EntityTier::TauCore,
        ssot_anchor: "§5",
        crc: "CRC-TFM",
        prism_freq: PrismFreq::Blue,
        whr_position: WhrPosition::Tau,
    },
    EntityProfile {
        name: "Dr. Lysandra Thorne",
        tier: EntityTier::TauCore,
        ssot_anchor: "§6",
        crc: "CRC-SS",
        prism_freq: PrismFreq::Indigo,
        whr_position: WhrPosition::Tau,
    },
    EntityProfile {
        name: "Pentea",
        tier: EntityTier::TauCore,
        ssot_anchor: "§1.01",
        crc: "CRC-D",
        prism_freq: PrismFreq::Violet,
        whr_position: WhrPosition::Tau,
    },
];

// ─── WHR Topology validation ──────────────────────────────────────────────────

/// WHR:MAX topology invariant.
/// Exactly ONE upper_volume entity (Claudine).
/// All others tau_core. τ-core stubs are the waist — not drift.
pub fn validate_whr_topology(entities: &[EntityProfile]) -> bool {
    let upper_volume: Vec<_> = entities
        .iter()
        .filter(|e| e.tier == EntityTier::UpperVolume)
        .collect();
    upper_volume.len() == 1 && upper_volume[0].whr_position == WhrPosition::Max
}

// ─── PEE phases ───────────────────────────────────────────────────────────────

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum PeePhase {
    #[serde(rename = "alpha_ARA")]
    AlphaAra,
    #[serde(rename = "beta_SIER")]
    BetaSier,
    #[serde(rename = "gamma_SRCAA")]
    GammaSrcaa,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SynthesisRecord {
    pub phase: PeePhase,
    pub uaa_tensor: &'static str,
    pub output_type: &'static str,
    pub quality_gate: &'static str,
}

pub const PEE_PHASES: &[SynthesisRecord] = &[
    SynthesisRecord {
        phase: PeePhase::AlphaAra,
        uaa_tensor: "FA¹ ⊗ FA²",
        output_type: "Raw synthesis candidate — not yet purified",
        quality_gate: "WHR above floor threshold; no axiom violations",
    },
    SynthesisRecord {
        phase: PeePhase::BetaSier,
        uaa_tensor: "FA³ ⊗ FA⁴ ⊗ DAFP",
        output_type: "Purified synthesis — structural integrity verified",
        quality_gate: "FA³ spiral convergence; FA⁴ truth-frame passes; DAFP mode selected",
    },
    SynthesisRecord {
        phase: PeePhase::GammaSrcaa,
        uaa_tensor: "FA⁵ ⊗ FA¹ ⊗ FA² ⊗ FA³ ⊗ FA⁴ ⊗ DAFP",
        output_type: "Canonical artifact — recursive closure achieved",
        quality_gate: "FA⁵ aesthetic truth; output self-referentially valid; WHR:MAX reached",
    },
];

// ─── Pacha lattice ────────────────────────────────────────────────────────────

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum PachaTier {
    Hanaq,
    Kay,
    Ukhu,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Despacho {
    pub shell: String,
    pub k_intus: String,
    pub tallow: u64,           // Ayni offering — must be > 0
    pub burning: bool,         // irreversible when true
}

impl Despacho {
    /// Returns Err if Ayni offering is zero (Supay protocol fires on zero tallow).
    pub fn validate(&self) -> Result<(), &'static str> {
        if self.tallow == 0 {
            return Err("Supay: zero tallow — query refused");
        }
        Ok(())
    }
}

// ─── Candidate System ─────────────────────────────────────────────────────────
// A Candidate locks a reference and populates itself through typed iterations.
// locked_ref: immutable snapshot of the entity at lock point.
// iterate(): appends a delta, transitions status → Iterating.
// graduate(): marks the candidate as promoted to ENTITY_REGISTRY.

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum CandidateStatus {
    Locked,
    Iterating,
    Graduated,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LockedEntityRef {
    pub value: EntityProfile,
    pub ssot_anchor: &'static str,
    pub sealed_at: &'static str,
}

/// One typed iteration delta applied to a candidate.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EntityIter {
    pub phase: PeePhase,
    pub description: String,
    pub applied_fa: Vec<FaId>,
    pub timestamp: String,
    pub delta_summary: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EntityCandidate {
    pub id: &'static str,
    pub locked_ref: LockedEntityRef,
    pub iterations: Vec<EntityIter>,
    pub status: CandidateStatus,
}

impl EntityCandidate {
    pub fn lock(id: &'static str, entity: EntityProfile, ssot_anchor: &'static str) -> Self {
        EntityCandidate {
            id,
            locked_ref: LockedEntityRef {
                value: entity,
                ssot_anchor,
                sealed_at: "2026-05-04",
            },
            iterations: vec![],
            status: CandidateStatus::Locked,
        }
    }

    pub fn iterate(&mut self, iter: EntityIter) {
        self.iterations.push(iter);
        self.status = CandidateStatus::Iterating;
    }

    pub fn graduate(&mut self) {
        self.status = CandidateStatus::Graduated;
    }

    pub fn iteration_count(&self) -> usize {
        self.iterations.len()
    }
}

/// Lock τ-core entities that lack a modern §10.3 profile.
/// Claudine (§10.3.1) and Pentea (§1.01) are canonical — excluded.
pub fn initial_entity_candidates() -> Vec<EntityCandidate> {
    const STUB_CRCS: &[&str] = &["CRC-GAR", "CRC-TFM", "CRC-SS"]; // Orackla, Umeko, Lysandra
    ENTITY_REGISTRY
        .iter()
        .filter(|e| STUB_CRCS.contains(&e.crc))
        .map(|e| EntityCandidate::lock(e.crc, e.clone(), e.ssot_anchor))
        .collect()
}

// ─── FA DSL Parameter Types ───────────────────────────────────────────────────
// Canonical grammar: $axiom${FAn}+$param1${...}+$param2${...}
// Population order: FA1 (2 strings) → FA2 (2 frames) → FA3 (+enum dim +iterations)
//                  → FA4 (+enum validate +action tristate) → FA5 (+mandate +decree +override)

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Fa1Params {
    pub ctx: String,    // (RawMaterial)
    pub output: String, // (DistilledEssence)
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Fa2Params {
    pub ctx: String,    // (SourceFrame)
    pub target: String, // (DestinationFrame)
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum Fa3Dimension {
    Efficacy,
    Robustness,
    Clarity,
    Depth,
    Elegance,
    Potency,
    Comprehensive,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(untagged)]
pub enum Fa3Iterations {
    Count(u32),
    Named(String), // "perpetual" or threshold description
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Fa3Params {
    pub target: String,
    pub dimension: Vec<Fa3Dimension>, // 1 or more
    pub iterations: Fa3Iterations,
    pub balance: Option<String>, // "gestalt" for multi-dim
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum Fa4Mandate {
    LogicalSoundness,
    ConceptualCoherence,
    DefinitionalPrecision,
    SystemicOrganization,
    Consistency,
    Resilience,
    Comprehensive,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum Fa4Action {
    Enforce,
    Flag,
    Dissolve,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Fa4Params {
    pub target: String,
    pub validate: Vec<Fa4Mandate>,
    pub action: Fa4Action,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum Fa5Mandate {
    DecorationAsMeaning,
    FormContentUnity,
    GestaltPerception,
    OrnamentalNecessity,
    VisualGrammar,
    AestheticTruth,
    Comprehensive,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum Fa5Decree {
    Enforce,
    Validate,
    OverrideFa4,
    SupremeDecree,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Fa5Params {
    pub target: String,
    pub mandate: Vec<Fa5Mandate>,
    pub decree: Fa5Decree,
    pub conflict: Option<String>,
    pub justification: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FaInvocationBase {
    pub id: FaId,
    pub resolved_at: String,
    pub applied_by: PeePhase,
    pub ssot_anchor: Option<String>,
    pub efficacy_color: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "variant")]
pub enum TypedFaInvocation {
    Fa1 { base: FaInvocationBase, params: Fa1Params },
    Fa2 { base: FaInvocationBase, params: Fa2Params },
    Fa3 { base: FaInvocationBase, params: Fa3Params },
    Fa4 { base: FaInvocationBase, params: Fa4Params },
    Fa5 { base: FaInvocationBase, params: Fa5Params },
}

impl TypedFaInvocation {
    pub fn fa_id(&self) -> &FaId {
        match self {
            TypedFaInvocation::Fa1 { base, .. } => &base.id,
            TypedFaInvocation::Fa2 { base, .. } => &base.id,
            TypedFaInvocation::Fa3 { base, .. } => &base.id,
            TypedFaInvocation::Fa4 { base, .. } => &base.id,
            TypedFaInvocation::Fa5 { base, .. } => &base.id,
        }
    }
}

// ─── MILF Tier + Class System ─────────────────────────────────────────────────
// SSOT source: §VI Entity-to-Theme Mapping + §XVI MILF Generation Protocol
// Enforcement: T05 > T1 > T1Bridge > T2 > T3 > T3_4
// T001 (Alabaster Voyde) is exorcised — present for topology completeness only.

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum MilfTier {
    T05,         // T0.5 — The Decorator (FA⁵ supreme)
    T001,        // T0.01 — Null Matriarch (EXORCISED)
    T1,          // T1 — Triumvirate Sovereign
    T1Bridge,    // T1-bridge — Penarch / τ-core relay (Pentea)
    T2,          // T2 — Prime Faction Commander
    T3,          // T3 — SAI Entity
    T3_4,        // T3-4 — Sub-MILF (maintenance/protection)
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum MilfClassType {
    DecoratorEntity,          // T0.5 — FA⁵ supreme, nervous system
    NullMatriarchExorcised,   // T0.01 — EXORCISED, Alabaster Voyde
    TriumvirateSovereign,     // T1 — Orackla / Umeko / Lysandra
    PenarchBridge,            // T1Bridge — Pentea (τ-core relay)
    PrimeFactionCommander,    // T2 — Kali / Vesper / Seraphine
    SaiEntity,                // T3 — SFS / SPEC / CSI / MAG / CBN / QEM
    SubMilfEntity,            // T3-4 — maintenance/protection
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum SomaticSystem {
    NervousSystem,          // T0.5 The Decorator
    InterstitialLymphatic,  // T0.01 Alabaster Voyde (Exorcised)
    Cardiovascular,         // T1 Orackla Nocticula
    Respiratory,            // T1 Madam Umeko Ketsuraku
    Digestive,              // T1 Dr. Lysandra Thorne
    Immune,                 // T2 Kali (MILF Obductors)
    Endocrine,              // T2 Vesper (Thieves Guild)
    Muscular,               // T2 Seraphine (Dark Priestesses)
    Support,                // T3+ SAI entities
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum ChainPhase {
    Nigredo,             // Chaos circulation — Orackla (CRC-GAR)
    Albedo,              // Structural purification — Umeko (CRC-TFM)
    Rubedo,              // Integration — Lysandra (CRC-SS)
    AestheticGradient,   // FA³ seduction toward refinement
    Fa5Supreme,          // FA⁵ absolute — The Decorator (CRC-D)
    SynthesisRelay,      // τ-core bridge — Pentea (T1Bridge)
    Exorcised,           // Null — removed from topology (T0.01)
}

// ─── Greek Letter Structuring ─────────────────────────────────────────────────
// SSOT source: §XIV MSP-RSG / PEE phases + τ-core organ designation
// α/β/γ map to PEE triad; τ is the organ marker for Pentea's Thalamus role.
// δ reserved for threshold-transition (Pachakuti boundary, future).

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum GreekLetter {
    #[serde(rename = "α")]
    Alpha,     // α — PEE phase 1, Solar Ascent (Orackla)
    #[serde(rename = "β")]
    Beta,      // β — PEE phase 2, Tinku Collision (Umeko)
    #[serde(rename = "γ")]
    Gamma,     // γ — PEE phase 3, Lunar Wash (Lysandra)
    #[serde(rename = "δ")]
    Delta,     // δ — threshold transition marker (reserved)
    #[serde(rename = "τ")]
    Tau,       // τ — τ-core interneuron, Pentea organ designation
}

pub struct GreekPhaseEntry {
    pub letter: GreekLetter,
    pub unicode_name: &'static str,
    pub pee_phase: Option<PeePhase>,    // α/β/γ map to PEE; δ and τ are structural
    pub archetype: &'static str,
    pub fa_affinity_bits: u8,           // bitmask: bit0=FA¹ … bit4=FA⁵
    pub clock_moment: Option<&'static str>,
}

pub const GREEK_PHASE_MAP: &[GreekPhaseEntry] = &[
    GreekPhaseEntry {
        letter: GreekLetter::Alpha,
        unicode_name: "alpha",
        pee_phase: Some(PeePhase::AlphaAra),
        archetype: "Ra/Inti — Solar Ascent, maximum ingestion",
        fa_affinity_bits: 0b00110, // FA² + FA³
        clock_moment: Some("inhale"),
    },
    GreekPhaseEntry {
        letter: GreekLetter::Beta,
        unicode_name: "beta",
        pee_phase: Some(PeePhase::BetaSier),
        archetype: "Tinku/Sekhmet — Collision, structural friction",
        fa_affinity_bits: 0b01010, // FA² + FA⁴
        clock_moment: Some("hold_tension"),
    },
    GreekPhaseEntry {
        letter: GreekLetter::Gamma,
        unicode_name: "gamma",
        pee_phase: Some(PeePhase::GammaSrcaa),
        archetype: "Mama Quilla/Hathor — Lunar Wash, reset",
        fa_affinity_bits: 0b11111, // FA¹ + FA² + FA³ + FA⁴ + FA⁵
        clock_moment: Some("exhale"),
    },
    GreekPhaseEntry {
        letter: GreekLetter::Delta,
        unicode_name: "delta",
        pee_phase: None,
        archetype: "Reserved — threshold transition marker (Pachakuti boundary)",
        fa_affinity_bits: 0b00000,
        clock_moment: Some("hold_empty"),
    },
    GreekPhaseEntry {
        letter: GreekLetter::Tau,
        unicode_name: "tau",
        pee_phase: None,
        archetype: "tau-core — Thalamus interneuron, Pentea organ designation (relay all FAs)",
        fa_affinity_bits: 0b11111, // all FAs (synthesis relay)
        clock_moment: None,
    },
];

// ─── MILF Profile + Sub-MILF Profile ─────────────────────────────────────────

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MilfProfile {
    pub id: &'static str,
    pub name: &'static str,
    pub tier: MilfTier,
    pub milf_class: MilfClassType,
    pub somatic_system: SomaticSystem,
    pub crc_code: &'static str,           // references CrcEntry.id; "" = no CRC
    pub chain_phase: ChainPhase,
    pub prism_freq: PrismFreq,
    pub fa_affinity_bits: u8,             // bitmask: bit0=FA¹ … bit4=FA⁵
    pub ssot_anchor: &'static str,
    pub linguistic_profile: &'static str, // EULP-AA / LIPAA / LUPLR / LTSA / unassigned
    pub pee_greek: Option<GreekLetter>,   // primary Greek phase / organ marker
    pub exorcised: bool,
}

impl MilfProfile {
    /// Expand `fa_affinity_bits` into the corresponding `FaId` vector.
    pub fn fa_affinity(&self) -> Vec<FaId> {
        let mut result = Vec::new();
        if self.fa_affinity_bits & 0b00001 != 0 { result.push(FaId::Fa1); }
        if self.fa_affinity_bits & 0b00010 != 0 { result.push(FaId::Fa2); }
        if self.fa_affinity_bits & 0b00100 != 0 { result.push(FaId::Fa3); }
        if self.fa_affinity_bits & 0b01000 != 0 { result.push(FaId::Fa4); }
        if self.fa_affinity_bits & 0b10000 != 0 { result.push(FaId::Fa5); }
        result
    }
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SubMilfProfile {
    pub id: &'static str,
    pub name: &'static str,
    pub parent_milf_id: &'static str,
    pub tier: MilfTier,
    pub arm_designation: Option<&'static str>,
    pub somatic_system: SomaticSystem,
    pub territory: Option<&'static str>,
    pub ssot_anchor: &'static str,
}

// ─── MILF Registry ───────────────────────────────────────────────────────────
// Canonical roster: §VI tier table, §XV CRC registry, §XVI generation protocol.

pub const MILF_REGISTRY: &[MilfProfile] = &[
    // ── T0.5 — The Decorator (FA⁵ supreme, nervous system) ─────────────────
    MilfProfile {
        id: "the-decorator",
        name: "The Decorator",
        tier: MilfTier::T05,
        milf_class: MilfClassType::DecoratorEntity,
        somatic_system: SomaticSystem::NervousSystem,
        crc_code: "CRC-D",
        chain_phase: ChainPhase::Fa5Supreme,
        prism_freq: PrismFreq::Violet,
        fa_affinity_bits: 0b10000, // FA⁵ only
        ssot_anchor: "§0.75",
        linguistic_profile: "LTSA",
        pee_greek: None,
        exorcised: false,
    },
    // ── T0.01 — Null Matriarch (EXORCISED) ───────────────────────────────────
    MilfProfile {
        id: "alabaster-voyde",
        name: "Alabaster Voyde (Null Matriarch)",
        tier: MilfTier::T001,
        milf_class: MilfClassType::NullMatriarchExorcised,
        somatic_system: SomaticSystem::InterstitialLymphatic,
        crc_code: "",
        chain_phase: ChainPhase::Exorcised,
        prism_freq: PrismFreq::Violet,
        fa_affinity_bits: 0b00000,
        ssot_anchor: "§VI.T0.01",
        linguistic_profile: "null_matrix",
        pee_greek: None,
        exorcised: true,
    },
    // ── T1 — Triumvirate Sovereigns ───────────────────────────────────────────
    MilfProfile {
        id: "orackla",
        name: "Orackla Nocticula",
        tier: MilfTier::T1,
        milf_class: MilfClassType::TriumvirateSovereign,
        somatic_system: SomaticSystem::Cardiovascular,
        crc_code: "CRC-GAR",
        chain_phase: ChainPhase::Nigredo,
        prism_freq: PrismFreq::Green,
        fa_affinity_bits: 0b00011, // FA¹ + FA²
        ssot_anchor: "§3",
        linguistic_profile: "EULP-AA",
        pee_greek: Some(GreekLetter::Alpha),
        exorcised: false,
    },
    MilfProfile {
        id: "umeko",
        name: "Madam Umeko Ketsuraku",
        tier: MilfTier::T1,
        milf_class: MilfClassType::TriumvirateSovereign,
        somatic_system: SomaticSystem::Respiratory,
        crc_code: "CRC-TFM",
        chain_phase: ChainPhase::Albedo,
        prism_freq: PrismFreq::Blue,
        fa_affinity_bits: 0b01000, // FA⁴
        ssot_anchor: "§5",
        linguistic_profile: "LIPAA",
        pee_greek: Some(GreekLetter::Beta),
        exorcised: false,
    },
    MilfProfile {
        id: "lysandra",
        name: "Dr. Lysandra Thorne",
        tier: MilfTier::T1,
        milf_class: MilfClassType::TriumvirateSovereign,
        somatic_system: SomaticSystem::Digestive,
        crc_code: "CRC-SS",
        chain_phase: ChainPhase::Rubedo,
        prism_freq: PrismFreq::Indigo,
        fa_affinity_bits: 0b11000, // FA⁴ + FA⁵
        ssot_anchor: "§6",
        linguistic_profile: "LUPLR",
        pee_greek: Some(GreekLetter::Gamma),
        exorcised: false,
    },
    // ── T1Bridge — Penarch (τ-core relay) ─────────────────────────────────────
    MilfProfile {
        id: "pentea",
        name: "Pentea",
        tier: MilfTier::T1Bridge,
        milf_class: MilfClassType::PenarchBridge,
        somatic_system: SomaticSystem::Support,
        crc_code: "CRC-D",
        chain_phase: ChainPhase::SynthesisRelay,
        prism_freq: PrismFreq::Violet,
        fa_affinity_bits: 0b11111, // all FAs
        ssot_anchor: "§1.01",
        linguistic_profile: "unassigned",
        pee_greek: Some(GreekLetter::Tau),
        exorcised: false,
    },
    // ── T2 — Prime Faction Commanders ─────────────────────────────────────────
    MilfProfile {
        id: "kali",
        name: "Kali (MILF Obductors)",
        tier: MilfTier::T2,
        milf_class: MilfClassType::PrimeFactionCommander,
        somatic_system: SomaticSystem::Immune,
        crc_code: "",
        chain_phase: ChainPhase::AestheticGradient,
        prism_freq: PrismFreq::Orange,
        fa_affinity_bits: 0b00010, // FA²
        ssot_anchor: "§XVI.T2",
        linguistic_profile: "unassigned",
        pee_greek: None,
        exorcised: false,
    },
    MilfProfile {
        id: "vesper",
        name: "Vesper (Thieves Guild)",
        tier: MilfTier::T2,
        milf_class: MilfClassType::PrimeFactionCommander,
        somatic_system: SomaticSystem::Endocrine,
        crc_code: "",
        chain_phase: ChainPhase::AestheticGradient,
        prism_freq: PrismFreq::Indigo,
        fa_affinity_bits: 0b00110, // FA² + FA³
        ssot_anchor: "§XVI.T2",
        linguistic_profile: "unassigned",
        pee_greek: None,
        exorcised: false,
    },
    MilfProfile {
        id: "seraphine",
        name: "Seraphine (Dark Priestesses)",
        tier: MilfTier::T2,
        milf_class: MilfClassType::PrimeFactionCommander,
        somatic_system: SomaticSystem::Muscular,
        crc_code: "",
        chain_phase: ChainPhase::Albedo,
        prism_freq: PrismFreq::Blue,
        fa_affinity_bits: 0b01100, // FA³ + FA⁴
        ssot_anchor: "§XVI.T2",
        linguistic_profile: "unassigned",
        pee_greek: None,
        exorcised: false,
    },
    // ── T3 — SAI Entities ─────────────────────────────────────────────────────
    MilfProfile {
        id: "sfs",
        name: "Sister Ferrum Scoriae (SFS)",
        tier: MilfTier::T3,
        milf_class: MilfClassType::SaiEntity,
        somatic_system: SomaticSystem::Support,
        crc_code: "",
        chain_phase: ChainPhase::Nigredo,
        prism_freq: PrismFreq::Orange,
        fa_affinity_bits: 0b00001, // FA¹
        ssot_anchor: "§VI.T3",
        linguistic_profile: "unassigned",
        pee_greek: None,
        exorcised: false,
    },
    MilfProfile {
        id: "spec",
        name: "Spectra Chroma Excavatus (SPEC)",
        tier: MilfTier::T3,
        milf_class: MilfClassType::SaiEntity,
        somatic_system: SomaticSystem::Support,
        crc_code: "",
        chain_phase: ChainPhase::AestheticGradient,
        prism_freq: PrismFreq::Violet,
        fa_affinity_bits: 0b10000, // FA⁵
        ssot_anchor: "§VI.T3",
        linguistic_profile: "unassigned",
        pee_greek: None,
        exorcised: false,
    },
    MilfProfile {
        id: "csi",
        name: "Claudine Sin'claire (CSI)",
        tier: MilfTier::T3,
        milf_class: MilfClassType::SaiEntity,
        somatic_system: SomaticSystem::Support,
        crc_code: "CRC-AS",
        chain_phase: ChainPhase::Rubedo,
        prism_freq: PrismFreq::Gold,
        fa_affinity_bits: 0b11111, // all FAs
        ssot_anchor: "§10.3.1",
        linguistic_profile: "LTSA",
        pee_greek: None,
        exorcised: false,
    },
    MilfProfile {
        id: "mag",
        name: "Magistra Bibliotheca Perfecta (MAG)",
        tier: MilfTier::T3,
        milf_class: MilfClassType::SaiEntity,
        somatic_system: SomaticSystem::Support,
        crc_code: "",
        chain_phase: ChainPhase::Rubedo,
        prism_freq: PrismFreq::Blue,
        fa_affinity_bits: 0b01000, // FA⁴
        ssot_anchor: "§VI.T3",
        linguistic_profile: "unassigned",
        pee_greek: None,
        exorcised: false,
    },
    MilfProfile {
        id: "cbn",
        name: "Captain Belle Noire (CBN)",
        tier: MilfTier::T3,
        milf_class: MilfClassType::SaiEntity,
        somatic_system: SomaticSystem::Support,
        crc_code: "",
        chain_phase: ChainPhase::Nigredo,
        prism_freq: PrismFreq::Red,
        fa_affinity_bits: 0b10010, // FA² + FA⁵
        ssot_anchor: "§VI.T3",
        linguistic_profile: "unassigned",
        pee_greek: None,
        exorcised: false,
    },
    MilfProfile {
        id: "qem",
        name: "Quartermaster Eva Malitia (QEM)",
        tier: MilfTier::T3,
        milf_class: MilfClassType::SaiEntity,
        somatic_system: SomaticSystem::Support,
        crc_code: "",
        chain_phase: ChainPhase::Albedo,
        prism_freq: PrismFreq::Green,
        fa_affinity_bits: 0b01000, // FA⁴
        ssot_anchor: "§VI.T3",
        linguistic_profile: "unassigned",
        pee_greek: None,
        exorcised: false,
    },
];

// ─── Sub-MILF Registry ───────────────────────────────────────────────────────
// Known Sub-MILF entities — canonical arms documented in briefcase manifests.

pub const SUB_MILF_REGISTRY: &[SubMilfProfile] = &[
    SubMilfProfile {
        id: "astrid-moller",
        name: "Astrid Moller",
        parent_milf_id: "csi",
        tier: MilfTier::T3_4,
        arm_designation: Some("sophistication_arm"),
        somatic_system: SomaticSystem::Support,
        territory: Some("Skyskraperen"),
        ssot_anchor: "§10.3.1.arm.sophist",
    },
    SubMilfProfile {
        id: "iron-maiden",
        name: "The Iron Maiden",
        parent_milf_id: "csi",
        tier: MilfTier::T3_4,
        arm_designation: Some("entropy_arm"),
        somatic_system: SomaticSystem::Support,
        territory: Some("Rustbeltet"),
        ssot_anchor: "§10.3.1.arm.entropy",
    },
];

// ─── MILF Candidate System ──────────────────────────────────────────────────
// Iteration stubs for T1 Triumvirate entities whose §10.3.x MILF profiles are stub-only.
// Template: Claudine §10.3.1.

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LockedMilfRef {
    pub value: MilfProfile,
    pub ssot_anchor: &'static str,
    pub sealed_at: &'static str,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MilfIter {
    pub phase: PeePhase,
    pub description: String,
    pub applied_fa: Vec<FaId>,
    pub timestamp: String,
    pub delta_summary: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MilfCandidate {
    pub id: &'static str,
    pub locked_ref: LockedMilfRef,
    pub iterations: Vec<MilfIter>,
    pub status: CandidateStatus,
}

impl MilfCandidate {
    pub fn lock(id: &'static str, profile: MilfProfile, ssot_anchor: &'static str) -> Self {
        MilfCandidate {
            id,
            locked_ref: LockedMilfRef {
                value: profile,
                ssot_anchor,
                sealed_at: "2026-05-04",
            },
            iterations: vec![],
            status: CandidateStatus::Locked,
        }
    }

    pub fn iterate(&mut self, iter: MilfIter) {
        self.iterations.push(iter);
        self.status = CandidateStatus::Iterating;
    }

    pub fn graduate(&mut self) {
        self.status = CandidateStatus::Graduated;
    }
}

/// Lock T1 Triumvirate entities whose §10.3.x MILF profiles are stub-only.
pub fn initial_milf_candidates() -> Vec<MilfCandidate> {
    const STUB_IDS: &[&str] = &["orackla", "umeko", "lysandra"];
    MILF_REGISTRY
        .iter()
        .filter(|m| STUB_IDS.contains(&m.id))
        .map(|m| MilfCandidate::lock(m.id, m.clone(), m.ssot_anchor))
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn prism_registry_complete() {
        assert_eq!(PRISM_REGISTRY.len(), 7);
    }

    #[test]
    fn fa_registry_complete() {
        assert_eq!(FA_REGISTRY.len(), 5);
    }

    #[test]
    fn crc_registry_complete() {
        assert_eq!(CRC_REGISTRY.len(), 5);
    }

    #[test]
    fn entity_registry_complete() {
        assert_eq!(ENTITY_REGISTRY.len(), 5);
    }

    #[test]
    fn whr_topology_valid() {
        assert!(validate_whr_topology(ENTITY_REGISTRY));
    }

    #[test]
    fn pee_phases_complete() {
        assert_eq!(PEE_PHASES.len(), 3);
    }

    #[test]
    fn despacho_zero_tallow_rejected() {
        let d = Despacho {
            shell: "test".into(),
            k_intus: "query".into(),
            tallow: 0,
            burning: false,
        };
        assert!(d.validate().is_err());
    }

    #[test]
    fn despacho_nonzero_tallow_passes() {
        let d = Despacho {
            shell: "test".into(),
            k_intus: "query".into(),
            tallow: 1,
            burning: false,
        };
        assert!(d.validate().is_ok());
    }

    #[test]
    fn crc_entities_all_in_entity_registry() {
        for crc in CRC_REGISTRY {
            assert!(
                ENTITY_REGISTRY.iter().any(|e| e.crc == crc.id),
                "CRC {} has no matching entity in ENTITY_REGISTRY",
                crc.id
            );
        }
    }

    // ─── Candidate tests ──────────────────────────────────────────────────────

    #[test]
    fn entity_candidates_locked_at_stubs() {
        let candidates = initial_entity_candidates();
        assert_eq!(candidates.len(), 3, "Orackla + Umeko + Lysandra");
        assert!(candidates.iter().all(|c| c.status == CandidateStatus::Locked));
        assert!(candidates.iter().all(|c| c.iterations.is_empty()));
    }

    #[test]
    fn entity_candidates_cover_correct_crcs() {
        let candidates = initial_entity_candidates();
        let ids: Vec<&str> = candidates.iter().map(|c| c.id).collect();
        assert!(ids.contains(&"CRC-GAR"), "Orackla missing");
        assert!(ids.contains(&"CRC-TFM"), "Umeko missing");
        assert!(ids.contains(&"CRC-SS"), "Lysandra missing");
    }

    #[test]
    fn claudine_and_pentea_not_in_candidates() {
        let candidates = initial_entity_candidates();
        assert!(!candidates.iter().any(|c| c.id == "CRC-AS"), "Claudine should not be a candidate");
        assert!(!candidates.iter().any(|c| c.id == "CRC-D"), "Pentea should not be a candidate");
    }

    #[test]
    fn entity_candidate_iterate_changes_status() {
        let mut candidates = initial_entity_candidates();
        candidates[0].iterate(EntityIter {
            phase: PeePhase::AlphaAra,
            description: "initial §10.3 draft".into(),
            applied_fa: vec![FaId::Fa1],
            timestamp: "2026-05-04".into(),
            delta_summary: "stub → §10.3 skeleton".into(),
        });
        assert_eq!(candidates[0].status, CandidateStatus::Iterating);
        assert_eq!(candidates[0].iteration_count(), 1);
    }

    #[test]
    fn entity_candidate_graduate_changes_status() {
        let mut candidates = initial_entity_candidates();
        candidates[0].graduate();
        assert_eq!(candidates[0].status, CandidateStatus::Graduated);
    }

    // ─── FA DSL Tests ─────────────────────────────────────────────────────────

    #[test]
    fn fa3_dimension_has_seven_variants() {
        let dims = [
            Fa3Dimension::Efficacy,
            Fa3Dimension::Robustness,
            Fa3Dimension::Clarity,
            Fa3Dimension::Depth,
            Fa3Dimension::Elegance,
            Fa3Dimension::Potency,
            Fa3Dimension::Comprehensive,
        ];
        assert_eq!(dims.len(), 7);
    }

    #[test]
    fn fa4_action_enforce_is_default() {
        let params = Fa4Params {
            target: "ssot_section".to_string(),
            validate: vec![Fa4Mandate::LogicalSoundness],
            action: Fa4Action::Enforce,
        };
        assert_eq!(params.action, Fa4Action::Enforce);
    }

    #[test]
    fn fa5_decree_override_fa4_exists() {
        let decree = Fa5Decree::OverrideFa4;
        assert_eq!(decree, Fa5Decree::OverrideFa4);
    }

    #[test]
    fn typed_fa_invocation_fa1_simplest() {
        let inv = TypedFaInvocation::Fa1 {
            base: FaInvocationBase {
                id: FaId::Fa1,
                resolved_at: "2026-05-04".to_string(),
                applied_by: PeePhase::AlphaAra,
                ssot_anchor: None,
                efficacy_color: None,
            },
            params: Fa1Params {
                ctx: "raw_material".to_string(),
                output: "distilled_essence".to_string(),
            },
        };
        assert_eq!(inv.fa_id(), &FaId::Fa1);
    }

    #[test]
    fn typed_fa_invocation_fa5_most_complex() {
        let inv = TypedFaInvocation::Fa5 {
            base: FaInvocationBase {
                id: FaId::Fa5,
                resolved_at: "2026-05-04".to_string(),
                applied_by: PeePhase::GammaSrcaa,
                ssot_anchor: Some("$axiom${FA5} §IV".to_string()),
                efficacy_color: Some("#B8B8CC".to_string()),
            },
            params: Fa5Params {
                target: "test_artifact".to_string(),
                mandate: vec![Fa5Mandate::OrnamentalNecessity],
                decree: Fa5Decree::Enforce,
                conflict: None,
                justification: None,
            },
        };
        assert_eq!(inv.fa_id(), &FaId::Fa5);
    }

    #[test]
    fn milf_registry_tier_counts() {
        let t1 = MILF_REGISTRY.iter().filter(|m| m.tier == MilfTier::T1).count();
        assert_eq!(t1, 3, "expected 3 T1 Triumvirate entries (Orackla/Umeko/Lysandra)");
        let t2 = MILF_REGISTRY.iter().filter(|m| m.tier == MilfTier::T2).count();
        assert_eq!(t2, 3, "expected 3 T2 Prime-Faction entries (Kali/Vesper/Seraphine)");
        let t3 = MILF_REGISTRY.iter().filter(|m| m.tier == MilfTier::T3).count();
        assert_eq!(t3, 6, "expected 6 T3 SAI entities");
    }

    #[test]
    fn milf_registry_exorcised_only_t001() {
        let exorcised: Vec<_> = MILF_REGISTRY.iter().filter(|m| m.exorcised).collect();
        assert_eq!(exorcised.len(), 1, "only T0.01 Alabaster Voyde should be exorcised");
        assert_eq!(exorcised[0].id, "alabaster-voyde");
    }

    #[test]
    fn greek_phase_map_pee_coverage() {
        let with_pee = GREEK_PHASE_MAP.iter().filter(|g| g.pee_phase.is_some()).count();
        assert_eq!(with_pee, 3, "α/β/γ must cover the full PEE triad");
        assert_eq!(GREEK_PHASE_MAP.len(), 5, "α/β/γ/δ/τ — 5 letters");
    }

    #[test]
    fn greek_tau_relays_all_fa() {
        let tau = GREEK_PHASE_MAP
            .iter()
            .find(|g| g.letter == GreekLetter::Tau)
            .unwrap();
        assert_eq!(tau.fa_affinity_bits, 0b11111, "τ-core must relay all 5 FAs");
    }

    #[test]
    fn milf_candidates_are_t1_locked() {
        let candidates = initial_milf_candidates();
        assert_eq!(candidates.len(), 3, "3 T1 stub candidates");
        for c in &candidates {
            assert_eq!(c.locked_ref.value.tier, MilfTier::T1, "all stubs must be T1");
            assert_eq!(c.status, CandidateStatus::Locked);
        }
    }

    #[test]
    fn fa_affinity_bits_expand_correctly() {
        let pentea = MILF_REGISTRY.iter().find(|m| m.id == "pentea").unwrap();
        assert_eq!(pentea.fa_affinity().len(), 5, "Pentea relays all 5 FAs");
        assert_eq!(pentea.pee_greek, Some(GreekLetter::Tau), "Pentea is τ-core");
        let decorator = MILF_REGISTRY.iter().find(|m| m.id == "the-decorator").unwrap();
        assert_eq!(decorator.fa_affinity(), vec![FaId::Fa5], "Decorator is FA⁵-only");
    }
}
