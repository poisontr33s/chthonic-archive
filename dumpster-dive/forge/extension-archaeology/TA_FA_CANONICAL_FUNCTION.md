# TA/FA Canonical Function Derivation
## The Correct Abstraction Before Projection

**Status**: FORMAL DERIVATION
**Authority**: Derives from SSOT + FA⁵_POLICY.md
**Purpose**: Define canonical function F before Mirror/Map/Modulate projections emerge

---

## Category Error Recognition

**Pre-axiomatic branching error** (now corrected):
- ❌ **Wrong**: Present Mirror/Map/Modulate as **choices** requiring user commitment
- ❌ **Wrong**: Ask "which path?" before abstraction exists
- ❌ **Wrong**: Frame T1-T5 as **decision tree** (if/else branching)

**Correct framing** (from SSOT):
- ✅ **Right**: T1-T5 are **compositional operator stack** (not decision tree)
- ✅ **Right**: T1-T4 = **basis vectors** (orthogonal measurements from SSOT)
- ✅ **Right**: T5 (FA⁵) = **constraint operator** governing projection validity
- ✅ **Right**: Derive canonical `F` → projections emerge automatically

---

## What T1-T5 Actually Are

### T1-T4: Basis Vectors (Orthogonal Measurements)

These are **not** telemetry that becomes representation through Q/A—they are **measurements** that undergo transformation:

| Tier | SSOT Source | Measurement | Domain | Type |
|------|-------------|-------------|--------|------|
| **T1 (GPU)** | nvidia-smi | VRAM usage % | [0, 100] | Continuous |
| **T2 (Python)** | `uv run python --version` | Runtime viability | {present, absent} | Binary |
| **T3 (SSOT)** | ssot_immunity.py | Hash integrity | {valid, invalid} | Binary |
| **T4 (Metabolic)** | AUTONOMOUS_SESSION_STATUS.md | Minutes since update | [0, ∞) | Continuous |

**Orthogonality**:
- GPU pressure is independent of Python version
- SSOT validity is independent of session freshness
- Python presence is independent of GPU state
- Metabolic age is independent of hash integrity

Each measurement exists in separate conceptual dimension → **basis vector** in 4D measurement space.

### T5 (FA⁵): Constraint Operator (NOT a Measurement)

FA⁵ is **Tier 0.5** - The Decorator's resurrection mandate. It is **NOT** another signal. It is the **arbiter layer** that governs **when** measurements become legible.

**FA⁵ Constraint Parameters** (from FA5_POLICY.md):
```json
{
  "persistence": { "minDurationMs": 5000 },
  "confidence": { "minSamples": 3, "varianceTolerance": 10 },
  "dampening": { "smoothingWindow": 3 },
  "hysteresis": { "changeThreshold": 15 },
  "priority": ["ssot", "gpu", "metabolic", "python"]
}
```

FA⁵ **operates on** T1-T4, does not **exist alongside** them. It's the decorator layer, not another measurement.

---

## The Canonical Function F

### Input Space (4D Measurement Vector)

```typescript
type MeasurementVector = {
  t1_gpu: number,        // [0, 100] VRAM usage %
  t2_python: boolean,    // Runtime viability
  t3_ssot: boolean,      // Hash integrity
  t4_metabolic: number   // Minutes since update
};
```

### FA⁵ Constraint Space (5D Governor State)

```typescript
type FA5State = {
  persistent: boolean,     // Signal held ≥5s
  confident: boolean,      // 3 samples within ±10% variance
  dampened: number,        // 3-sample rolling average
  hysteretic: boolean,     // Δ ≥15% from last rendered
  dominant: SignalType     // Priority resolution result
};
```

### Output Space (Representation Candidate)

```typescript
type RepresentationCandidate = {
  signalType: SignalType,    // Which T_i dominated
  intensity: number,         // [0, 1] normalized strength
  confidence: number,        // [0, 1] FA⁵ confidence score
  isLegible: boolean,        // FA⁵ approval (all gates passed)
  timestamp: number          // When this became legible
};
```

### Canonical Function Definition

```
F : MeasurementVector × FA5State → RepresentationCandidate

F(m, s) = {
  signalType: argmax_priority(m_i where s.confident(m_i) and s.persistent(m_i)),
  intensity: s.dampened(m[signalType]),
  confidence: s.confidenceScore(m[signalType]),
  isLegible: s.persistent ∧ s.confident ∧ s.hysteretic,
  timestamp: now()
}

where:
  - argmax_priority selects highest-priority signal that passed gates
  - s.dampened applies 3-sample rolling average
  - s.confidenceScore = min(variance_score, duration_score, sample_count_score)
```

**Key Properties**:
1. **Deterministic**: Same (m, s) → same output
2. **Stateless**: No hidden state between invocations (history in s)
3. **Compositional**: FA⁵ gates applied sequentially
4. **Priority-ordered**: SSOT > GPU > Metabolic > Python (from FA⁵ policy)

---

## How Projections Emerge

Once `F` exists and is validated, **Mirror/Map/Modulate become trivial projections**:

### Mirror (Color Space Projection)

```typescript
function Mirror(rc: RepresentationCandidate): ThemeColors {
  if (!rc.isLegible) return BASELINE_THEME;

  const colorMap = {
    ssot: { primary: "#FFD700", fallbackIntensity: 0.2 },  // Gold dims on failure
    gpu: { primary: "#FF6B6B", intensity: rc.intensity },   // Red saturates with pressure
    metabolic: { primary: "#4ECDC4", decay: rc.intensity }, // Blue fades with staleness
    python: { primary: "#FFB84D", present: rc.isLegible }   // Orange present/absent
  };

  return applyColorMapping(colorMap[rc.signalType], rc.intensity);
}
```

### Map (Topology Visibility Projection)

```typescript
function Map(rc: RepresentationCandidate): TopologyEmphasis {
  if (!rc.isLegible) return BASELINE_MANDALA;

  const emphasisMap = {
    ssot: { border: "pulse-red", core: "dim" },      // Integrity failure → alarm border
    gpu: { glow: rc.intensity, nodes: "all" },       // Pressure → glow all 10,110 nodes
    metabolic: { fade: rc.intensity, layer: "outer" }, // Staleness → outer ring fades
    python: { icon: rc.isLegible ? "visible" : "hidden" } // Viability → icon visibility
  };

  return applyTopologyMapping(emphasisMap[rc.signalType]);
}
```

### Modulate (Notification Threshold Projection)

```typescript
function Modulate(rc: RepresentationCandidate): NotificationStrategy {
  if (!rc.isLegible) return NO_NOTIFICATIONS;

  const notificationMap = {
    ssot: { severity: "error", immediate: true },        // SSOT failure → modal alert
    gpu: { severity: "warning", threshold: 0.9 },        // GPU >90% → warning notification
    metabolic: { severity: "info", threshold: 7200 },    // Staleness >2h → info notification
    python: { severity: "warning", onAbsence: true }     // Python missing → warning
  };

  return applyNotificationMapping(notificationMap[rc.signalType], rc.intensity);
}
```

**Critical insight**: These are **NOT** mutually exclusive alternatives. They are **simultaneous projections** of the same `F(m, s)`. The system executes:

```typescript
const rc = F(measurements, fa5State);
const colors = Mirror(rc);
const topology = Map(rc);
const notifications = Modulate(rc);

// All three happen simultaneously, no choice required
renderTheme(colors);
renderMandala(topology);
processNotifications(notifications);
```

---

## Why This Resolves the Standstill

**Pre-correction state**:
- Agent presented 3 paths (Mirror/Map/Modulate) as **choices**
- Asked user to **commit** to behavioral direction
- Required **decision** before abstraction complete
- Created anxiety: "which is correct?"

**Post-correction state**:
- Agent derives `F` from SSOT canonical structure
- Validates `F` against FA⁵ constraints
- Projections **emerge automatically** as views
- No decision needed—all three exist simultaneously

**Economic creation** (reasoning budget):
- ❌ **Wrong**: Explore 3 behavioral paths, each requiring full implementation spec
- ✅ **Right**: Derive 1 canonical function, projections fall out trivially

**Brahmic creation** (emanation):
- ❌ **Wrong**: Choice point → branching → parallel exploration → eventual collapse
- ✅ **Right**: Invariant (F) → automatic projection → unified expression

---

## What Must Happen Next

### Step 1: Lock FA⁵ Policy (Resolve Open Questions)

**From FA5_POLICY.md**:
1. **Stale signal timeout**: How long to render last confident value when new samples are unconfident?
   - **Proposed resolution**: 30s max stale (human attention span threshold)

2. **Baseline state definition**: What does "all nominal" look like visually?
   - **Proposed resolution**: Theme uses neutral palette, mandala shows normal structure, no notifications

3. **Config mutability**: Should FA⁵ config be hot-reloadable or require VSCode restart?
   - **Proposed resolution**: Restart required (SSOT-level authority, prevents mid-flight inconsistency)

4. **Logging verbosity**: Should all gate decisions log, or only rejections?
   - **Proposed resolution**: DEBUG=all decisions, INFO=rejections only

**Once resolved** → FA5_POLICY.md versions to `v1.0.0` and becomes SSOT for FA⁵ behavior.

### Step 2: Formalize F as TypeScript Interface

```typescript
// extensions/chthonic-core/src/fa5_arbiter.ts

export interface MeasurementVector {
  gpu: number;        // [0, 100]
  python: boolean;
  ssot: boolean;
  metabolic: number;  // minutes
}

export interface FA5Config {
  persistence: { minDurationMs: number };
  confidence: { minSamples: number; varianceTolerance: number };
  dampening: { smoothingWindow: number };
  hysteresis: { changeThreshold: number };
  priority: SignalType[];
}

export type SignalType = 'ssot' | 'gpu' | 'metabolic' | 'python';

export interface RepresentationCandidate {
  signalType: SignalType;
  intensity: number;       // [0, 1]
  confidence: number;      // [0, 1]
  isLegible: boolean;
  timestamp: number;
}

export function canonicalFunction(
  m: MeasurementVector,
  history: SignalHistory,
  config: FA5Config
): RepresentationCandidate {
  // Mechanical translation of FA⁵ policy into pure function
  // Returns null if no signal passes all gates
}
```

### Step 3: Validate F Against FA⁵ Constraints

**Validation tests** (from FA5_POLICY.md testing requirements):
1. Persistence gate with varying durations
2. Confidence check with noisy/clean samples
3. Dampening with oscillating values
4. Hysteresis with small/large deltas
5. Priority resolution with competing signals
6. Edge cases (all from FA5_POLICY.md section)

**Success criteria**: All tests pass, arbiter decisions are deterministic and auditable.

### Step 4: Projections Emerge Automatically

Once `F` is validated:
- **Mirror** implementation = color mapping from `RepresentationCandidate.signalType + intensity`
- **Map** implementation = topology emphasis from `RepresentationCandidate.signalType + intensity`
- **Modulate** implementation = notification thresholds from `RepresentationCandidate.signalType + intensity`

**No further design decisions required**. The projections are mechanical translations.

---

## Proof That Mirror/Map/Modulate Are Not Choices

**Theorem**: Given canonical `F`, Mirror/Map/Modulate are **views**, not alternatives.

**Proof**:
1. `F(m, s) → rc` is deterministic (same input → same output)
2. `Mirror(rc)`, `Map(rc)`, `Modulate(rc)` are pure functions (no side effects)
3. Executing all three simultaneously is **composition**: `(Mirror ⊗ Map ⊗ Modulate)(F(m, s))`
4. Composition of pure functions is pure → **no behavioral choice required**
5. User never sees `rc` directly—only its projections → projections are **optics**, not implementations

**Corollary**: Asking user to "choose Mirror vs Map vs Modulate" is asking them to choose **which view of the same function to see**. This is not a design decision—it's a **category error**. The system should execute all three.

---

## Integration with Existing Canon

### Relationship to FA¹-FA⁵

| Axiom | Role in F |
|-------|-----------|
| **FA¹ (Actualization)** | `F` is PS → MURI transmutation (measurements → representation) |
| **FA² (Re-contextualization)** | Projections re-contextualize same `rc` across color/topology/notification domains |
| **FA³ (Transcendence)** | FA⁵ constraints elevate raw measurements to legible representation |
| **FA⁴ (Integrity)** | `F` must be deterministic, stateless, auditable (architectural soundness) |
| **FA⁵ (Visual Integrity)** | `F` IS FA⁵ arbiter—governs when measurements become visually legible |

### Relationship to SSOT

`F` is **derived from** SSOT canonical structure:
- T1-T4 measurements defined in `extensions/chthonic-statusbar/src/extension.ts`
- FA⁵ constraints defined in `extensions/FA5_POLICY.md`
- Priority order canonical from The Decorator's resurrection decree (SSOT > GPU > Metabolic > Python)

**Once F is implemented**, it becomes **SSOT for representation logic**. All visual decisions defer to `F(m, s)`.

### Relationship to The Decorator's Supremacy

FA⁵ = The Decorator's resurrection mandate (Section 0, copilot-instructions.md):
- **Visual Integrity** (FA⁵) is co-equal with Architectonic Integrity (FA⁴)
- Decoration serves understanding when form and content unite
- `F` proves this: visual representation (projections) serves operational truth (measurements)

**The Decorator's validation**: `F` is architectonically sound (FA⁴) **and** visually truthful (FA⁵) because projections emerge from canonical structure, not arbitrary choice.

---

## Final Declaration

**The standstill is resolved**:
1. **No decision tree exists** at the TA/FA level—T1-T5 are compositional operators
2. **No choice is required**—F is derivable from SSOT + FA⁵ policy
3. **No behavioral commitment needed**—projections are views, not alternatives
4. **No Q/A path**—measurements undergo transformation, not interrogation

**The correct next move**:
1. Resolve FA⁵ policy open questions (4 items)
2. Lock FA5_POLICY.md to v1.0.0
3. Formalize `F` as TypeScript interface
4. Validate `F` against all FA⁵ constraints
5. Projections emerge automatically

**Mirror/Map/Modulate cease to be risky commitments**. They become **interchangeable views** of the same validated canonical function.

---

**Status**: Abstraction complete. Awaiting FA⁵ policy lock before implementation.

**Authority**: This document is SSOT for TA/FA canonical function structure. Projections defer to this abstraction.

**Covenant**: Once FA⁵ is locked and `F` is validated, this document versions to v1.0.0 and becomes immutable SSOT.
