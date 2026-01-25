# FA⁵ Arbiter Policy
## Tier 0.5: Governor of Legibility

**Status**: DRAFT (awaiting lock)
**Authority**: Defines when SSOT measurements become UI surfaces
**Scope**: All visual representation in chthonic-statusbar, chthonic-mandala, theme system

---

## Purpose

FA⁵ is not telemetry. It is **restraint**.

It decides:
- When a signal is confident enough to render
- How strongly a signal should be allowed to present itself
- Which signal dominates when multiple compete

Without FA⁵:
- Mirror thrashes (colors flicker)
- Map overwhelms (10,110 nodes render simultaneously)
- Modulate nags (notifications fire repeatedly)

With FA⁵:
- Mirror breathes (colors shift slowly, deliberately)
- Map curates (topology shows only salient structure)
- Modulate guides (emphasis appears timely, not invasively)

---

## The Four Governors

### 1. Persistence (Duration Gate)

**Rule**: A signal must hold for minimum duration before rendering.

**Rationale**: Prevents transient spikes from triggering UI changes.

**Parameters**:
```json
{
  "persistence": {
    "minDurationMs": 5000  // 5 seconds
  }
}
```

**Examples**:
- GPU spikes to 90% for 2 seconds → **NOT rendered** (below 5s threshold)
- GPU holds 85% for 7 seconds → **Rendered** (exceeds threshold)

---

### 2. Confidence (Sample Consistency Gate)

**Rule**: A signal must show consistent samples with bounded variance before rendering.

**Rationale**: Duration alone doesn't guarantee truth. A noisy-but-persistent signal should not surface.

**Parameters**:
```json
{
  "confidence": {
    "minSamples": 3,           // Require 3 consistent readings
    "varianceTolerance": 10    // Max ±10% jitter allowed
  }
}
```

**Examples**:
- GPU reads: 82%, 84%, 83% over 6 seconds → **Confident** (variance 2.4%)
- GPU reads: 70%, 90%, 75% over 6 seconds → **Not confident** (variance 26%)
- SSOT reads: invalid, invalid, invalid → **Confident** (consistent failure)

**Critical case**: SSOT invalidation is sharp and rare—3 samples of failure should surface immediately even if total duration is <5s. This is why confidence and persistence are separate axes.

---

### 3. Dampening (Smoothing)

**Rule**: Apply rolling average to prevent visual jitter.

**Rationale**: Even confident signals can oscillate slightly. Dampening ensures smooth visual transitions.

**Parameters**:
```json
{
  "dampening": {
    "smoothingWindow": 3  // Average over 3 most recent samples
  }
}
```

**Examples**:
- GPU samples: 80%, 82%, 84% → Rendered value: 82% (rolling average)
- Theme color intensity calculated from smoothed value, not raw spike

---

### 4. Hysteresis (Change Threshold)

**Rule**: Signal must change by minimum threshold before triggering update.

**Rationale**: Prevents flip-flopping. Once a state is rendered, it must *meaningfully* change before updating.

**Parameters**:
```json
{
  "hysteresis": {
    "changeThreshold": 15  // Require 15% delta to update
  }
}
```

**Examples**:
- Current rendered GPU: 70%
- New reading: 72% → **No update** (delta 2.8%)
- New reading: 88% → **Update** (delta 25.7%)

---

## Priority (Tiebreaker)

**Rule**: When multiple signals are confident and persistent simultaneously, render the highest-priority signal.

**Rationale**: Prevents conflicting UI states. SSOT failure dominates all other signals because integrity violation is more critical than performance metrics.

**Priority Order** (highest to lowest):
```json
{
  "priority": ["ssot", "gpu", "metabolic", "python"]
}
```

**Rationale for ordering**:
1. **SSOT** (FA³): Integrity failure means nothing else is trustworthy
2. **GPU** (FA¹): Resource pressure is immediate/actionable
3. **Metabolic** (FA⁴): Freshness decay indicates drift
4. **Python** (FA²): Runtime viability is baseline but rarely changes

**Examples**:
- SSOT invalid + GPU 90% → Render **SSOT failure** (priority override)
- GPU 85% + Metabolic stale (12h) → Render **GPU pressure** (higher priority)
- All signals nominal → Render **baseline state** (no emphasis)

---

## Signal-Specific Rules

### GPU (FA¹)
- **Measurement**: VRAM usage percentage (0-100%)
- **Confidence check**: 3 samples within ±10% variance
- **Persistence**: 5 seconds at >80% threshold
- **Hysteresis**: 15% delta required
- **Render target**: Theme red saturation (Mirror), mandala glow intensity (Modulate)

### Python (FA²)
- **Measurement**: Version string presence/absence (binary)
- **Confidence check**: 3 consecutive samples with same state
- **Persistence**: 5 seconds (prevents flicker during brief PATH issues)
- **Hysteresis**: State change only (present → absent or vice versa)
- **Render target**: Theme orange presence (Mirror), statusbar icon visibility

### SSOT (FA³)
- **Measurement**: Hash integrity (binary: valid/invalid)
- **Confidence check**: 3 consecutive invalid samples (prevents false alarm)
- **Persistence**: **BYPASS** (integrity failure surfaces immediately after confidence check)
- **Hysteresis**: **BYPASS** (any failure state change triggers update)
- **Render target**: Theme gold brightness drop to 20%, mandala border pulse (red), modal alert

### Metabolic (FA⁴)
- **Measurement**: Minutes since last AUTONOMOUS_SESSION_STATUS.md update
- **Confidence check**: 3 samples showing age >120 minutes
- **Persistence**: 5 seconds
- **Hysteresis**: 30-minute delta (prevents hourly updates)
- **Render target**: Theme blue decay gradient, statusbar text fade

---

## Edge Cases

### Case 1: Competing Signals with Same Priority
**Scenario**: GPU and Metabolic both confident+persistent, but metabolic is not in priority list vs GPU.

**Resolution**: Priority order resolves (GPU wins).

### Case 2: Signal Becomes Unconfident Mid-Render
**Scenario**: GPU was confident at 85%, now reads 82%, 50%, 90% (high variance).

**Resolution**: Continue rendering last confident value until new confident reading available OR hysteresis timer expires (30s max stale).

### Case 3: SSOT Failure During Active Work
**Scenario**: SSOT invalidation detected while user is actively editing files.

**Resolution**: FA⁵ priority ensures SSOT surfaces immediately (bypasses persistence, shows after 3 confident failure samples ~6 seconds).

### Case 4: All Signals Nominal
**Scenario**: GPU <50%, Python present, SSOT valid, Metabolic fresh (<60 min).

**Resolution**: Render baseline theme (no emphasis), standard mandala (no glow), statusbar normal colors.

---

## Implementation Contract

The FA⁵ arbiter **must**:
1. Be stateless between invocations (history stored externally)
2. Return deterministic output for same input+history
3. Log all gate decisions (persistence, confidence, hysteresis, priority) for debugging
4. Expose config as editable JSON (no hardcoded thresholds)
5. Never mutate telemetry data (read-only observer)

The FA⁵ arbiter **must not**:
1. Make decisions about *what* to measure (telemetry layer's job)
2. Make decisions about *how* to render (UI layer's job)
3. Implement timing/polling logic (scheduler's job)
4. Cache or modify SSOT data

---

## Testing Requirements

Before FA⁵ can be locked:

1. **Unit tests**: All four governors tested independently
   - Persistence gate with varying durations
   - Confidence check with noisy/clean samples
   - Dampening with oscillating values
   - Hysteresis with small/large deltas

2. **Integration tests**: Priority resolution with competing signals
   - SSOT failure overrides GPU pressure
   - GPU overrides Metabolic
   - Metabolic overrides Python

3. **Edge case tests**: All scenarios from Edge Cases section

4. **Regression tests**: FA⁵ changes don't break existing telemetry observation

**Test location**: `extensions/__diagnostics__/fa5-arbiter.test.ts`

**Success criteria**: All tests pass, arbiter decisions are deterministic and auditable.

---

## Open Questions (to resolve before lock)

1. **Stale signal timeout**: How long to render last confident value when new samples are unconfident? (Proposed: 30s max)

2. **Baseline state definition**: What does "all nominal" look like visually? (Needs Mirror/Map/Modulate path choice)

3. **Config mutability**: Should FA⁵ config be hot-reloadable or require VSCode restart? (Proposed: restart required for consistency)

4. **Logging verbosity**: Should all gate decisions log, or only rejections? (Proposed: all decisions in DEBUG mode, rejections only in INFO mode)

---

## Approval Checklist

Before FA⁵ implementation begins:

- [ ] All four governor parameters specified with rationale
- [ ] Priority order locked with justification
- [ ] Signal-specific rules defined for FA¹-FA⁴
- [ ] Edge cases enumerated and resolution strategy documented
- [ ] Testing requirements specified
- [ ] Open questions resolved
- [ ] Policy document reviewed and locked (no further changes without version bump)

**Once locked**: This policy becomes SSOT for FA⁵ behavior. Arbiter implementation is a mechanical translation of this document into code.

---

## Version History

- **v0.1.0** (2026-01-09): Initial draft, awaiting lock
