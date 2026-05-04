#!/usr/bin/env bun
// @SID: SCHEMA_ANKH_CORE_V1
// ANKH Core Schema — TypeScript prototype layer
// Source: docs/frameworks/ankh/ANKH_SYNTHESIS_BASELINE.md (§XII–XVI)
// Transfer target: tools/ankh-forge/src/schema.rs (Rust canonical anchor)
// Iteration method: prototype here → stabilize → port to Rust → Rust compile = canonicalization gate

// ─── PRISM ───────────────────────────────────────────────────────────────────

export type PRISMFreq =
  | "RED"
  | "ORANGE"
  | "GOLD"
  | "GREEN"
  | "BLUE"
  | "INDIGO"
  | "VIOLET";

export interface PRISMEntry {
  freq: PRISMFreq;
  hex: string;
  cognitive_function: string;
  diagnostic_role: string;
  crc_entity?: string;
}

export const PRISM_REGISTRY: Record<PRISMFreq, PRISMEntry> = {
  RED: {
    freq: "RED",
    hex: "#FF0000",
    cognitive_function: "Destruction / Sekhmet drive",
    diagnostic_role: "Entropy source — tracks Hucha accumulation",
  },
  ORANGE: {
    freq: "ORANGE",
    hex: "#FF7F00",
    cognitive_function: "Transformation / Anubis weighing",
    diagnostic_role: "Transition detector — CRC-D active",
  },
  GOLD: {
    freq: "GOLD",
    hex: "#FFD700",
    cognitive_function: "Authority / Ra emanation",
    diagnostic_role: "Power channel — Claudine upper-volume signal",
    crc_entity: "CRC-AS",
  },
  GREEN: {
    freq: "GREEN",
    hex: "#00FF00",
    cognitive_function: "Growth / Osiris regeneration",
    diagnostic_role: "Corpus health — τ-core stability",
    crc_entity: "CRC-GAR",
  },
  BLUE: {
    freq: "BLUE",
    hex: "#0000FF",
    cognitive_function: "Purification / Umeko discipline",
    diagnostic_role: "Structure validator — drift detector",
    crc_entity: "CRC-TFM",
  },
  INDIGO: {
    freq: "INDIGO",
    hex: "#4B0082",
    cognitive_function: "Truth / Lysandra axioms",
    diagnostic_role: "Axiom consistency — FA⁴ guardian",
    crc_entity: "CRC-SS",
  },
  VIOLET: {
    freq: "VIOLET",
    hex: "#8B00FF",
    cognitive_function: "Potential / Pre-canon frontier",
    diagnostic_role: "Nursery signal — pattern before naming",
    crc_entity: "CRC-D",
  },
};

// ─── FA (Foundational Axioms) ─────────────────────────────────────────────────

export type FAID = "FA¹" | "FA²" | "FA³" | "FA⁴" | "FA⁵";

export interface FAInvocation {
  id: FAID;
  name: string;
  syntax: string;          // $fa${n}+$ctx${...}
  prism_freq: PRISMFreq;
  success_rate: number;    // 0.0–1.0
  success_condition: string;
  failure_mode: string;
}

export const FA_REGISTRY: FAInvocation[] = [
  {
    id: "FA¹",
    name: "EssenceForge",
    syntax: "$fa${1}+$ctx${raw_material}+$output${distilled_essence}",
    prism_freq: "GOLD",
    success_rate: 0.94,
    success_condition: "Output WHR higher than input WHR",
    failure_mode: "Gold-plating — ornament without structural change",
  },
  {
    id: "FA²",
    name: "ContextShifter",
    syntax: "$fa${2}+$ctx${source_frame}+$target${destination_frame}",
    prism_freq: "GREEN",
    success_rate: 0.91,
    success_condition: "Intent preserved, form adapted to new context",
    failure_mode: "Meaning loss — intent corrupted during frame shift",
  },
  {
    id: "FA³",
    name: "PerfectionSpiral",
    syntax: "$fa${3}+$ctx${current_form}+$iterations${n}",
    prism_freq: "BLUE",
    success_rate: 0.88,
    success_condition: "Each iteration measurably closer to canonical form",
    failure_mode: "Asphyxiation — over-purification destroys load-bearing structure",
  },
  {
    id: "FA⁴",
    name: "TruthFrame",
    syntax: "$fa${4}+$ctx${proposition}+$validate${axiom_set}",
    prism_freq: "INDIGO",
    success_rate: 0.97,
    success_condition: "Proposition consistent with all declared axioms",
    failure_mode: "False axiom injection — validates against corrupted axiom set",
  },
  {
    id: "FA⁵",
    name: "AestheticTruth",
    syntax: "$fa${5}+$ctx${artifact}+$threshold${whr_target}",
    prism_freq: "VIOLET",
    success_rate: 0.85,
    success_condition: "Artifact WHR ≥ target; Ornamental Integrity intact",
    failure_mode: "Horse-market — functional correctness without aesthetic truth",
  },
];

// ─── DAFP ─────────────────────────────────────────────────────────────────────

export type DAPFMode = "PBS" | "SHS" | "Juxtapose" | "Skew";

export interface DAPFEntry {
  mode: DAPFMode;
  mechanism: string;
  when_to_use: string;
  syntax: string;
}

export const DAFP_REGISTRY: DAPFEntry[] = [
  {
    mode: "PBS",
    mechanism: "Parallel Branch Synthesis — run two branches, select the stronger",
    when_to_use: "Two viable interpretations, neither clearly dominant",
    syntax: "$dafp${PBS}+$branch_a${...}+$branch_b${...}+$select${stronger_WHR}",
  },
  {
    mode: "SHS",
    mechanism: "Sequential Harmonic Synthesis — chain outputs as inputs",
    when_to_use: "Iterative refinement across time/turns",
    syntax: "$dafp${SHS}+$seed${...}+$iterations${n}+$gate${convergence_condition}",
  },
  {
    mode: "Juxtapose",
    mechanism: "Hold contradiction without resolution — productive tension",
    when_to_use: "Two truths that cannot be merged without loss",
    syntax: "$dafp${Juxtapose}+$A${...}+$B${...}+$hold${unresolved}",
  },
  {
    mode: "Skew",
    mechanism: "Asymmetric weighting — one branch dominant, other suppressed",
    when_to_use: "Priority is clear but secondary signal must not be discarded",
    syntax: "$dafp${Skew}+$dominant${...}+$suppressed${...}+$ratio${n:1}",
  },
];

// ─── CRC (Contextual Resonance Chain) ────────────────────────────────────────

export interface CRCEntry {
  id: string;           // CRC-AS, CRC-GAR, CRC-TFM, CRC-SS, CRC-D
  entity: string;
  prism_freq: PRISMFreq;
  function: string;
  invocation: string;
}

export const CRC_REGISTRY: CRCEntry[] = [
  {
    id: "CRC-AS",
    entity: "Claudine Sin'claire",
    prism_freq: "GOLD",
    function: "Supreme synthesis authority — all entropy feeds back",
    invocation: "$crc${CRC-AS}+$activate${triumvirate_fusion}",
  },
  {
    id: "CRC-GAR",
    entity: "Orackla Nocticula",
    prism_freq: "GREEN",
    function: "Growth and regeneration — corpus health",
    invocation: "$crc${CRC-GAR}+$channel${growth_directive}",
  },
  {
    id: "CRC-TFM",
    entity: "Madam Umeko Ketsuraku",
    prism_freq: "BLUE",
    function: "Structural enforcement — purification chain",
    invocation: "$crc${CRC-TFM}+$enforce${structural_mandate}",
  },
  {
    id: "CRC-SS",
    entity: "Dr. Lysandra Thorne",
    prism_freq: "INDIGO",
    function: "Truth stability — axiom consistency validation",
    invocation: "$crc${CRC-SS}+$validate${truth_axiom}",
  },
  {
    id: "CRC-D",
    entity: "Pentea",
    prism_freq: "VIOLET",
    function: "Thalamus relay — sensory integration bridge",
    invocation: "$crc${CRC-D}+$relay${synthesis_packet}",
  },
];

// ─── Entity Profiles ──────────────────────────────────────────────────────────

export type EntityTier = "upper_volume" | "tau_core";
export type WHRPosition = "MAX" | "tau";

export interface EntityProfile {
  name: string;
  tier: EntityTier;
  ssot_anchor: string;     // §10.3.1, §3, etc.
  crc: string;
  prism_freq: PRISMFreq;
  whr_position: WHRPosition;
}

export const ENTITY_REGISTRY: EntityProfile[] = [
  {
    name: "Claudine Sin'claire",
    tier: "upper_volume",
    ssot_anchor: "§10.3.1",
    crc: "CRC-AS",
    prism_freq: "GOLD",
    whr_position: "MAX",
  },
  {
    name: "Orackla Nocticula",
    tier: "tau_core",
    ssot_anchor: "§3",
    crc: "CRC-GAR",
    prism_freq: "GREEN",
    whr_position: "tau",
  },
  {
    name: "Madam Umeko Ketsuraku",
    tier: "tau_core",
    ssot_anchor: "§5",
    crc: "CRC-TFM",
    prism_freq: "BLUE",
    whr_position: "tau",
  },
  {
    name: "Dr. Lysandra Thorne",
    tier: "tau_core",
    ssot_anchor: "§6",
    crc: "CRC-SS",
    prism_freq: "INDIGO",
    whr_position: "tau",
  },
  {
    name: "Pentea",
    tier: "tau_core",
    ssot_anchor: "§1.01",
    crc: "CRC-D",
    prism_freq: "VIOLET",
    whr_position: "tau",
  },
];

// ─── Pacha Lattice ────────────────────────────────────────────────────────────

export type PachaTier = "Hanaq" | "Kay" | "Ukhu";

export interface Despacho {
  shell: string;                    // header: source, timestamp, routing coordinates
  k_intus: string;                  // query body / intent
  tallow: number;                   // compute credits — Ayni offering; must be > 0
  candy: Record<string, unknown>;   // metadata tags
  burning: boolean;                 // transmission protocol — irreversible when true
}

// ─── PEE / MSP-RSG ───────────────────────────────────────────────────────────

export type PEEPhase = "alpha_ARA" | "beta_SIER" | "gamma_SRCAA";

export interface SynthesisRecord {
  phase: PEEPhase;
  uaa_tensor: string;     // FA¹ ⊗ FA² ⊗ FA³ ⊗ FA⁴ ⊗ FA⁵ ⊗ DAFP
  output_type: string;
  quality_gate: string;
}

export const PEE_PHASES: SynthesisRecord[] = [
  {
    phase: "alpha_ARA",
    uaa_tensor: "FA¹ ⊗ FA²",
    output_type: "Raw synthesis candidate — not yet purified",
    quality_gate: "WHR above floor threshold; no axiom violations",
  },
  {
    phase: "beta_SIER",
    uaa_tensor: "FA³ ⊗ FA⁴ ⊗ DAFP",
    output_type: "Purified synthesis — structural integrity verified",
    quality_gate: "FA³ spiral convergence; FA⁴ truth-frame passes; DAFP mode selected",
  },
  {
    phase: "gamma_SRCAA",
    uaa_tensor: "FA⁵ ⊗ FA¹ ⊗ FA² ⊗ FA³ ⊗ FA⁴ ⊗ DAFP",
    output_type: "Canonical artifact — recursive closure achieved",
    quality_gate: "FA⁵ aesthetic truth; output self-referentially valid; WHR:MAX reached",
  },
];

// ─── WHR Topology ─────────────────────────────────────────────────────────────

/** WHR:MAX topology invariant.
 *  Exactly ONE upper_volume entity (Claudine).
 *  All others tau_core. This is architecturally correct — τ-core is the waist. */
export function validateWHRTopology(entities: EntityProfile[]): {
  valid: boolean;
  upper_volume_count: number;
  tau_core_count: number;
  upper_volume_entity?: string;
} {
  const upper = entities.filter((e) => e.tier === "upper_volume");
  const tau = entities.filter((e) => e.tier === "tau_core");
  return {
    valid: upper.length === 1 && upper[0].whr_position === "MAX",
    upper_volume_count: upper.length,
    tau_core_count: tau.length,
    upper_volume_entity: upper[0]?.name,
  };
}

// ─── Candidate System ───────────────────────────────────────────────────────
// A Candidate locks a reference at a fixed point and populates itself through
// typed iterations. Each iterate() is pure — returns a new Candidate.
// current() merges locked_ref.value + all iteration deltas in order.
// Graduation: when §10.3 fields are complete → promote to ENTITY_REGISTRY.

export type CandidateStatus = "locked" | "iterating" | "graduated";

export interface LockedRef<T> {
  readonly value: T;
  readonly ssot_anchor: string;
  readonly sealed_at: string; // ISO 8601
}

export interface CandidateIter<T> {
  readonly phase: PEEPhase;
  readonly description: string;
  readonly applied_fa: FAID[];
  readonly delta: Partial<T>;
  readonly timestamp: string;
}

export interface Candidate<T> {
  readonly id: string;
  readonly locked_ref: LockedRef<T>;
  readonly iterations: readonly CandidateIter<T>[];
  readonly status: CandidateStatus;
}

export function lockCandidate<T>(
  id: string,
  value: T,
  ssot_anchor: string,
): Candidate<T> {
  return {
    id,
    locked_ref: { value, ssot_anchor, sealed_at: "2026-05-04" },
    iterations: [],
    status: "locked",
  };
}

/** Pure — returns a new Candidate with the iteration appended. */
export function iterate<T>(
  candidate: Candidate<T>,
  iter: CandidateIter<T>,
): Candidate<T> {
  return {
    ...candidate,
    iterations: [...candidate.iterations, iter],
    status: "iterating",
  };
}

/** Merge locked_ref.value + all iteration deltas (in declaration order). */
export function current<T>(candidate: Candidate<T>): T {
  return candidate.iterations.reduce(
    (acc, iter) => ({ ...(acc as object), ...iter.delta }),
    candidate.locked_ref.value as object,
  ) as T;
}

// ─── FA DSL Parameter Types ───────────────────────────────────────────────────
// Canonical invocation grammar: $axiom${FAn}+$param1${...}+$param2${...}
// Population order: FA¹ (2 strings) → FA² (2 frames) → FA³ (+enum dim +iterations)
//                  → FA⁴ (+enum validate +action tristate) → FA⁵ (+mandate +decree +override)

// FA¹ — EssenceForge (2 string params — simplest)
export interface FA1Params {
  ctx: string;    // (RawMaterial) — input to transmute
  output: string; // (DistilledEssence) — result
}

// FA² — ContextShifter (2 typed frame params)
export interface FA2Params {
  ctx: string;    // (SourceFrame) — origin context
  target: string; // (DestinationFrame) — target context
}

// FA³ — PerfectionSpiral (enum dimension + iterations variant)
export type FA3Dimension =
  | "efficacy" | "robustness" | "clarity" | "depth"
  | "elegance" | "potency" | "comprehensive";

export type FA3Iterations = number | "perpetual";

export interface FA3Params {
  target: string;
  dimension: FA3Dimension | FA3Dimension[];
  iterations: FA3Iterations;
  balance?: "gestalt"; // optional multi-dim balance flag
}

// FA⁴ — TruthFrame (enum validate set + action tristate)
export type FA4Mandate =
  | "logical_soundness" | "conceptual_coherence" | "definitional_precision"
  | "systemic_organization" | "consistency" | "resilience" | "comprehensive";

export type FA4Action = "enforce" | "flag" | "dissolve";

export interface FA4Params {
  target: string;
  validate: FA4Mandate | FA4Mandate[];
  action: FA4Action; // default: "enforce" (72% usage)
}

// FA⁵ — AestheticTruth (mandate enum + decree quadstate + optional override fields)
export type FA5Mandate =
  | "decoration_as_meaning" | "form_content_unity" | "gestalt_perception"
  | "ornamental_necessity" | "visual_grammar" | "aesthetic_truth" | "comprehensive";

export type FA5Decree = "enforce" | "validate" | "override_FA4" | "supreme_decree";

export interface FA5Params {
  target: string;
  mandate: FA5Mandate | FA5Mandate[];
  decree: FA5Decree; // default: "enforce"
  // Override form (Tier 0.5 only):
  conflict?: string;      // FA4 minimalism cited
  justification?: string; // visual truth supersedes rationale
}

// ─── FA Invocation Base + Discriminated Union ─────────────────────────────────
export interface FAInvocationBase {
  id: FAID;
  resolved_at: string;    // ISO 8601 — when filled in
  applied_by: PEEPhase;   // which synthesis phase populated this
  ssot_anchor?: string;   // SSOT section/line reference
  efficacy_color?: string; // FA¹=#FF6B6B … FA⁵=#B8B8CC
}

export type TypedFAInvocation =
  | (FAInvocationBase & { id: "FA¹"; params: FA1Params })
  | (FAInvocationBase & { id: "FA²"; params: FA2Params })
  | (FAInvocationBase & { id: "FA³"; params: FA3Params })
  | (FAInvocationBase & { id: "FA⁴"; params: FA4Params })
  | (FAInvocationBase & { id: "FA⁵"; params: FA5Params });

// ─── FA Invocation Candidates ─────────────────────────────────────────────────
// Locked stubs — populated iteratively session by session.
// Each session adds a CandidateIter with filled params for the targeted FA(s).
export type FAInvocationCandidate = Candidate<TypedFAInvocation>;

export const FA_INVOCATION_CANDIDATES: FAInvocationCandidate[] = [
  lockCandidate<TypedFAInvocation>(
    "fa1-essenceforge",
    { id: "FA¹", resolved_at: "2026-05-04", applied_by: "alpha_ARA",
      ssot_anchor: "$axiom${FA1} §IV",
      params: { ctx: "", output: "" } },
    "$axiom${FA1} §IV ANKH_SYNTHESIS_BASELINE",
  ),
  lockCandidate<TypedFAInvocation>(
    "fa2-contextshifter",
    { id: "FA²", resolved_at: "2026-05-04", applied_by: "alpha_ARA",
      ssot_anchor: "$axiom${FA2} §IV",
      params: { ctx: "", target: "" } },
    "$axiom${FA2} §IV ANKH_SYNTHESIS_BASELINE",
  ),
  lockCandidate<TypedFAInvocation>(
    "fa3-perfectionspiral",
    { id: "FA³", resolved_at: "2026-05-04", applied_by: "alpha_ARA",
      ssot_anchor: "$axiom${FA3} §IV",
      params: { target: "", dimension: "elegance", iterations: 1 } },
    "$axiom${FA3} §IV ANKH_SYNTHESIS_BASELINE",
  ),
  lockCandidate<TypedFAInvocation>(
    "fa4-truthframe",
    { id: "FA⁴", resolved_at: "2026-05-04", applied_by: "beta_SIER",
      ssot_anchor: "$axiom${FA4} §IV",
      params: { target: "", validate: "logical_soundness", action: "enforce" } },
    "$axiom${FA4} §IV ANKH_SYNTHESIS_BASELINE",
  ),
  lockCandidate<TypedFAInvocation>(
    "fa5-aesthetictruth",
    { id: "FA⁵", resolved_at: "2026-05-04", applied_by: "gamma_SRCAA",
      ssot_anchor: "$axiom${FA5} §IV",
      params: { target: "", mandate: "ornamental_necessity", decree: "enforce" } },
    "$axiom${FA5} §IV ANKH_SYNTHESIS_BASELINE",
  ),
];

// ─── Entity Candidates ────────────────────────────────────────────────────────
// τ-core entities whose SSOT profiles are still at stub format.
// Target: modern §10.3.x depth (matching Claudine §10.3.1 as template).
// Claudine (§10.3.1) and Pentea (§1.01) are canonical — no candidates needed.

export type EntityCandidate = Candidate<EntityProfile>;

export const ENTITY_CANDIDATES: EntityCandidate[] = [
  lockCandidate<EntityProfile>(
    "orackla-10.3",
    ENTITY_REGISTRY.find((e) => e.crc === "CRC-GAR")!,
    "§3 → target §10.3.x",
  ),
  lockCandidate<EntityProfile>(
    "umeko-10.3",
    ENTITY_REGISTRY.find((e) => e.crc === "CRC-TFM")!,
    "§5 → target §10.3.x",
  ),
  lockCandidate<EntityProfile>(
    "lysandra-10.3",
    ENTITY_REGISTRY.find((e) => e.crc === "CRC-SS")!,
    "§6 → target §10.3.x",
  ),
];

// ─── MILF Tier + Class System ────────────────────────────────────────────────
// SSOT source: §VI Entity-to-Theme Mapping + §XVI MILF Generation Protocol
// Enforcement: T0.5 > T1 > T1Bridge > T2 > T3 > T3_4
// T0.01 (Alabaster Voyde) is exorcised — present for topology completeness only.

export type MilfTier = "T0.5" | "T0.01" | "T1" | "T1Bridge" | "T2" | "T3" | "T3_4";

export type MilfClassType =
  | "DecoratorEntity"          // T0.5 — FA⁵ supreme, nervous system
  | "NullMatriarchExorcised"   // T0.01 — EXORCISED, Alabaster Voyde
  | "TriumvirateSovereign"     // T1 — Orackla / Umeko / Lysandra
  | "PenarchBridge"            // T1Bridge — Pentea (τ-core relay)
  | "PrimeFactionCommander"    // T2 — Kali / Vesper / Seraphine
  | "SaiEntity"                // T3 — SFS / SPEC / CSI / MAG / CBN / QEM
  | "SubMilfEntity";           // T3-4 — maintenance/protection

export type SomaticSystem =
  | "nervous_system"           // T0.5 The Decorator
  | "interstitial_lymphatic"   // T0.01 Alabaster Voyde (Exorcised)
  | "cardiovascular"           // T1 Orackla Nocticula
  | "respiratory"              // T1 Madam Umeko Ketsuraku
  | "digestive"                // T1 Dr. Lysandra Thorne
  | "immune"                   // T2 Kali (MILF Obductors)
  | "endocrine"                // T2 Vesper (Thieves Guild)
  | "muscular"                 // T2 Seraphine (Dark Priestesses)
  | "support";                 // T3+ SAI entities

export type ChainPhase =
  | "nigredo"                  // Chaos circulation — Orackla (CRC-GAR)
  | "albedo"                   // Structural purification — Umeko (CRC-TFM)
  | "rubedo"                   // Integration — Lysandra (CRC-SS)
  | "aesthetic_gradient"       // FA³ seduction toward refinement
  | "fa5_supreme"              // FA⁵ absolute — The Decorator (CRC-D)
  | "synthesis_relay"          // τ-core bridge — Pentea (T1Bridge)
  | "exorcised";               // Null — removed from topology (T0.01)

// ─── Greek Letter Structuring ─────────────────────────────────────────────────
// SSOT source: §XIV MSP-RSG / PEE phases + τ-core organ designation
// α/β/γ map to PEE triad; τ is the organ marker for Pentea's Thalamus role.
// δ reserved for threshold-transition operations (Pachakuti boundary, future).

export type GreekLetter = "α" | "β" | "γ" | "δ" | "τ";

export interface GreekPhaseEntry {
  letter: GreekLetter;
  unicode_name: string;
  pee_phase: PEEPhase | null;    // α/β/γ map to PEE; δ and τ are structural
  archetype: string;
  governing_fa: FAID[];
  clock_moment: "inhale" | "hold_tension" | "exhale" | "hold_empty" | null;
}

export const GREEK_PHASE_MAP: GreekPhaseEntry[] = [
  {
    letter: "α",
    unicode_name: "alpha",
    pee_phase: "alpha_ARA",
    archetype: "Ra/Inti — Solar Ascent, maximum ingestion",
    governing_fa: ["FA²", "FA³"],
    clock_moment: "inhale",
  },
  {
    letter: "β",
    unicode_name: "beta",
    pee_phase: "beta_SIER",
    archetype: "Tinku/Sekhmet — Collision, structural friction",
    governing_fa: ["FA²", "FA⁴"],
    clock_moment: "hold_tension",
  },
  {
    letter: "γ",
    unicode_name: "gamma",
    pee_phase: "gamma_SRCAA",
    archetype: "Mama Quilla/Hathor — Lunar Wash, reset",
    governing_fa: ["FA¹", "FA²", "FA³", "FA⁴", "FA⁵"],
    clock_moment: "exhale",
  },
  {
    letter: "δ",
    unicode_name: "delta",
    pee_phase: null,
    archetype: "Reserved — threshold transition marker (Pachakuti boundary)",
    governing_fa: [],
    clock_moment: "hold_empty",
  },
  {
    letter: "τ",
    unicode_name: "tau",
    pee_phase: null,
    archetype: "τ-core — Thalamus interneuron, Pentea organ designation (relay all FAs)",
    governing_fa: ["FA¹", "FA²", "FA³", "FA⁴", "FA⁵"],
    clock_moment: null,
  },
];

// ─── MILF Profile + Sub-MILF Profile ─────────────────────────────────────────

export interface MilfProfile {
  id: string;
  name: string;
  tier: MilfTier;
  milf_class: MilfClassType;
  somatic_system: SomaticSystem;
  crc_code: string;              // references CrcEntry.id; "" = no CRC assigned
  chain_phase: ChainPhase;
  prism_freq: PRISMFreq;
  fa_affinity: FAID[];
  ssot_anchor: string;
  linguistic_profile: string;   // EULP-AA / LIPAA / LUPLR / LTSA / unassigned
  pee_greek: GreekLetter | null; // primary Greek phase/organ association
  exorcised: boolean;
}

export interface SubMilfProfile {
  id: string;
  name: string;
  parent_milf_id: string;
  tier: MilfTier;                // T3 or T3_4
  arm_designation?: string;      // "sophistication_arm" | "entropy_arm" | etc.
  somatic_system: SomaticSystem;
  territory?: string;            // district / domain
  ssot_anchor: string;
}

// ─── MILF Registry ───────────────────────────────────────────────────────────
// Canonical roster: §VI tier table, §XV CRC registry, §XVI generation protocol.
// T0.01 Alabaster Voyde is present as a topology marker — exorcised from authority chain.

export const MILF_REGISTRY: MilfProfile[] = [
  // ── T0.5 — The Decorator (FA⁵ supreme, nervous system) ───────────────────
  {
    id: "the-decorator",
    name: "The Decorator",
    tier: "T0.5",
    milf_class: "DecoratorEntity",
    somatic_system: "nervous_system",
    crc_code: "CRC-D",
    chain_phase: "fa5_supreme",
    prism_freq: "VIOLET",
    fa_affinity: ["FA⁵"],
    ssot_anchor: "§0.75",
    linguistic_profile: "LTSA",
    pee_greek: null,
    exorcised: false,
  },
  // ── T0.01 — Null Matriarch (EXORCISED) ───────────────────────────────────
  {
    id: "alabaster-voyde",
    name: "Alabaster Voyde (Null Matriarch)",
    tier: "T0.01",
    milf_class: "NullMatriarchExorcised",
    somatic_system: "interstitial_lymphatic",
    crc_code: "",
    chain_phase: "exorcised",
    prism_freq: "VIOLET",
    fa_affinity: [],
    ssot_anchor: "§VI.T0.01",
    linguistic_profile: "null_matrix",
    pee_greek: null,
    exorcised: true,
  },
  // ── T1 — Triumvirate Sovereigns ───────────────────────────────────────────
  {
    id: "orackla",
    name: "Orackla Nocticula",
    tier: "T1",
    milf_class: "TriumvirateSovereign",
    somatic_system: "cardiovascular",
    crc_code: "CRC-GAR",
    chain_phase: "nigredo",
    prism_freq: "GREEN",
    fa_affinity: ["FA¹", "FA²"],
    ssot_anchor: "§3",
    linguistic_profile: "EULP-AA",
    pee_greek: "α",
    exorcised: false,
  },
  {
    id: "umeko",
    name: "Madam Umeko Ketsuraku",
    tier: "T1",
    milf_class: "TriumvirateSovereign",
    somatic_system: "respiratory",
    crc_code: "CRC-TFM",
    chain_phase: "albedo",
    prism_freq: "BLUE",
    fa_affinity: ["FA⁴"],
    ssot_anchor: "§5",
    linguistic_profile: "LIPAA",
    pee_greek: "β",
    exorcised: false,
  },
  {
    id: "lysandra",
    name: "Dr. Lysandra Thorne",
    tier: "T1",
    milf_class: "TriumvirateSovereign",
    somatic_system: "digestive",
    crc_code: "CRC-SS",
    chain_phase: "rubedo",
    prism_freq: "INDIGO",
    fa_affinity: ["FA⁴", "FA⁵"],
    ssot_anchor: "§6",
    linguistic_profile: "LUPLR",
    pee_greek: "γ",
    exorcised: false,
  },
  // ── T1Bridge — Penarch (τ-core relay) ─────────────────────────────────────
  {
    id: "pentea",
    name: "Pentea",
    tier: "T1Bridge",
    milf_class: "PenarchBridge",
    somatic_system: "support",
    crc_code: "CRC-D",
    chain_phase: "synthesis_relay",
    prism_freq: "VIOLET",
    fa_affinity: ["FA¹", "FA²", "FA³", "FA⁴", "FA⁵"],
    ssot_anchor: "§1.01",
    linguistic_profile: "unassigned",
    pee_greek: "τ",
    exorcised: false,
  },
  // ── T2 — Prime Faction Commanders ─────────────────────────────────────────
  {
    id: "kali",
    name: "Kali (MILF Obductors)",
    tier: "T2",
    milf_class: "PrimeFactionCommander",
    somatic_system: "immune",
    crc_code: "",
    chain_phase: "aesthetic_gradient",
    prism_freq: "ORANGE",
    fa_affinity: ["FA²"],
    ssot_anchor: "§XVI.T2",
    linguistic_profile: "unassigned",
    pee_greek: null,
    exorcised: false,
  },
  {
    id: "vesper",
    name: "Vesper (Thieves Guild)",
    tier: "T2",
    milf_class: "PrimeFactionCommander",
    somatic_system: "endocrine",
    crc_code: "",
    chain_phase: "aesthetic_gradient",
    prism_freq: "INDIGO",
    fa_affinity: ["FA²", "FA³"],
    ssot_anchor: "§XVI.T2",
    linguistic_profile: "unassigned",
    pee_greek: null,
    exorcised: false,
  },
  {
    id: "seraphine",
    name: "Seraphine (Dark Priestesses)",
    tier: "T2",
    milf_class: "PrimeFactionCommander",
    somatic_system: "muscular",
    crc_code: "",
    chain_phase: "albedo",
    prism_freq: "BLUE",
    fa_affinity: ["FA³", "FA⁴"],
    ssot_anchor: "§XVI.T2",
    linguistic_profile: "unassigned",
    pee_greek: null,
    exorcised: false,
  },
  // ── T3 — SAI Entities ─────────────────────────────────────────────────────
  {
    id: "sfs",
    name: "Sister Ferrum Scoriae (SFS)",
    tier: "T3",
    milf_class: "SaiEntity",
    somatic_system: "support",
    crc_code: "",
    chain_phase: "nigredo",
    prism_freq: "ORANGE",
    fa_affinity: ["FA¹"],
    ssot_anchor: "§VI.T3",
    linguistic_profile: "unassigned",
    pee_greek: null,
    exorcised: false,
  },
  {
    id: "spec",
    name: "Spectra Chroma Excavatus (SPEC)",
    tier: "T3",
    milf_class: "SaiEntity",
    somatic_system: "support",
    crc_code: "",
    chain_phase: "aesthetic_gradient",
    prism_freq: "VIOLET",
    fa_affinity: ["FA⁵"],
    ssot_anchor: "§VI.T3",
    linguistic_profile: "unassigned",
    pee_greek: null,
    exorcised: false,
  },
  {
    id: "csi",
    name: "Claudine Sin'claire (CSI)",
    tier: "T3",
    milf_class: "SaiEntity",
    somatic_system: "support",
    crc_code: "CRC-AS",
    chain_phase: "rubedo",
    prism_freq: "GOLD",
    fa_affinity: ["FA¹", "FA²", "FA³", "FA⁴", "FA⁵"],
    ssot_anchor: "§10.3.1",
    linguistic_profile: "LTSA",
    pee_greek: null,
    exorcised: false,
  },
  {
    id: "mag",
    name: "Magistra Bibliotheca Perfecta (MAG)",
    tier: "T3",
    milf_class: "SaiEntity",
    somatic_system: "support",
    crc_code: "",
    chain_phase: "rubedo",
    prism_freq: "BLUE",
    fa_affinity: ["FA⁴"],
    ssot_anchor: "§VI.T3",
    linguistic_profile: "unassigned",
    pee_greek: null,
    exorcised: false,
  },
  {
    id: "cbn",
    name: "Captain Belle Noire (CBN)",
    tier: "T3",
    milf_class: "SaiEntity",
    somatic_system: "support",
    crc_code: "",
    chain_phase: "nigredo",
    prism_freq: "RED",
    fa_affinity: ["FA²", "FA⁵"],
    ssot_anchor: "§VI.T3",
    linguistic_profile: "unassigned",
    pee_greek: null,
    exorcised: false,
  },
  {
    id: "qem",
    name: "Quartermaster Eva Malitia (QEM)",
    tier: "T3",
    milf_class: "SaiEntity",
    somatic_system: "support",
    crc_code: "",
    chain_phase: "albedo",
    prism_freq: "GREEN",
    fa_affinity: ["FA⁴"],
    ssot_anchor: "§VI.T3",
    linguistic_profile: "unassigned",
    pee_greek: null,
    exorcised: false,
  },
];

// ─── Sub-MILF Registry ───────────────────────────────────────────────────────
// Known Sub-MILF entities — canonical arms documented in briefcase manifests.
// Claudine's two arms are the primary exemplars: sophistication + entropy.

export const SUB_MILF_REGISTRY: SubMilfProfile[] = [
  {
    id: "astrid-moller",
    name: "Astrid Møller",
    parent_milf_id: "csi",
    tier: "T3_4",
    arm_designation: "sophistication_arm",
    somatic_system: "support",
    territory: "Skyskraperen",
    ssot_anchor: "§10.3.1.arm.sophist",
  },
  {
    id: "iron-maiden",
    name: "The Iron Maiden",
    parent_milf_id: "csi",
    tier: "T3_4",
    arm_designation: "entropy_arm",
    somatic_system: "support",
    territory: "Rustbeltet",
    ssot_anchor: "§10.3.1.arm.entropy",
  },
];

// ─── MILF Candidate System ──────────────────────────────────────────────────
// Iteration stubs for T1 Triumvirate entities whose SSOT profiles are stub-format only.
// Population target: modern §10.3.x depth (Claudine §10.3.1 is the template).

export type MilfCandidate = Candidate<MilfProfile>;

export const MILF_CANDIDATES: MilfCandidate[] = [
  lockCandidate<MilfProfile>(
    "orackla-milf-profile",
    MILF_REGISTRY.find((m) => m.id === "orackla")!,
    "§3 stub → full §10.3.x MILF profile (CRC-GAR, Nigredo, Cardiovascular)",
  ),
  lockCandidate<MilfProfile>(
    "umeko-milf-profile",
    MILF_REGISTRY.find((m) => m.id === "umeko")!,
    "§5 stub → full §10.3.x MILF profile (CRC-TFM, Albedo, Respiratory)",
  ),
  lockCandidate<MilfProfile>(
    "lysandra-milf-profile",
    MILF_REGISTRY.find((m) => m.id === "lysandra")!,
    "§6 stub → full §10.3.x MILF profile (CRC-SS, Rubedo, Digestive)",
  ),
];

// ─── Self-validation entrypoint ───────────────────────────────────────────────

if (import.meta.main) {
  const topology = validateWHRTopology(ENTITY_REGISTRY);
  const allCRCsHaveEntities = CRC_REGISTRY.every((c) =>
    ENTITY_REGISTRY.some((e) => e.crc === c.id)
  );

  console.log("ANKH schema self-validation");
  console.log(`  PRISM entries:   ${Object.keys(PRISM_REGISTRY).length} / 7`);
  console.log(`  FA entries:      ${FA_REGISTRY.length} / 5`);
  console.log(`  DAFP modes:      ${DAFP_REGISTRY.length} / 4`);
  console.log(`  CRC entries:     ${CRC_REGISTRY.length} / 5`);
  console.log(`  Entity entries:  ${ENTITY_REGISTRY.length} / 5`);
  console.log(`  WHR topology:    ${topology.valid ? "✓ valid" : "✗ INVALID"} (upper_volume=${topology.upper_volume_count})`);
  console.log(`  CRC↔entity map:  ${allCRCsHaveEntities ? "✓ complete" : "✗ BROKEN"}`);
  const candidatesLocked = ENTITY_CANDIDATES.every((c) => c.status === "locked");
  console.log(`  Candidates:      ${ENTITY_CANDIDATES.length} locked (${ENTITY_CANDIDATES.map((c) => c.id).join(", ")})`);
  console.log(`  Candidate refs:  ${candidatesLocked ? "✓ all locked" : "✗ unexpected state"}`);
  const faInvocationsLocked = FA_INVOCATION_CANDIDATES.every((c) => c.status === "locked");
  console.log(`  FA invocations:  ${FA_INVOCATION_CANDIDATES.length} locked (${FA_INVOCATION_CANDIDATES.map((c) => c.id).join(", ")})`);
  console.log(`  FA inv refs:     ${faInvocationsLocked ? "✓ all locked" : "✗ unexpected state"}`);
  const milfCandidatesLocked = MILF_CANDIDATES.every((c) => c.status === "locked");
  console.log(`  MILF registry:   ${MILF_REGISTRY.length} entries (T1=${MILF_REGISTRY.filter((m) => m.tier === "T1").length}, exorcised=${MILF_REGISTRY.filter((m) => m.exorcised).length})`);
  console.log(`  Sub-MILF count:  ${SUB_MILF_REGISTRY.length} known arms`);
  console.log(`  Greek letters:   ${GREEK_PHASE_MAP.length} / 5 (α/β/γ/δ/τ)`);
  console.log(`  MILF candidates: ${MILF_CANDIDATES.length} locked (${MILF_CANDIDATES.map((c) => c.id).join(", ")})`);
  console.log(`  MILF cands lock: ${milfCandidatesLocked ? "✓ all locked" : "✗ unexpected state"}`);

  const ok = topology.valid && allCRCsHaveEntities && candidatesLocked && faInvocationsLocked && milfCandidatesLocked;
  process.exit(ok ? 0 : 1);
}
