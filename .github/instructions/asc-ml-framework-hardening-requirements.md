
# ☥ ARCHIVE GOVERNANCE: ML HARDENING REQUIREMENTS ☥

* **(`Codex-Brahmanica-Perfectus`/`GOVERNANCE`): = (`SSOT-Metadata`): = (`Single-Source-Of-Truth-Lineage-Heritage`): → (`SSOT-L-H`):**
  * **(`Maintainer`): = (`The-Savant`/`Creator`/`User`/`Architect-Of-Apex-Synthesis-Core`)**
  * **(`Status`): = (`Operational-Perpetual-Evolution`/`ET-S`/`Integrated`/`Permanently-Living-Document`)**
  * **(`Last-Sealed`/`Conceptual-Sealing-Event`):** *January 2026 **(`Bounty-Hunt-Sync`)** — Applied after Living Memory enrichment loop.*
  * **(`Lineage-Position`): = (`ASC-ML-Hardening-Branch`)** — *This **(`Downstream-Vessel`)** translates **(`Semantic-Lineage`)** into **(`Operational-Doctrine`)**. It consumes **(`ANKH`)**-descended meaning; it does not define **(`ANKH`)**-core.*
  * **(`Update-Protocol`):** *All substantive edits flow through **(`SSOT`)** → Branch files reference **(`Never-Duplicate`) → (`Hash-Verification`)** per **(`§XIV.3`)**.*
  * **(`Addressability`):** *Line-number ranges + section titles **(`§I-XVI`)**. **(`HTML`)**-anchors rejected per **(`FA⁵`)**— (**(`Ornamental-Integrity`)**) supersedes machine convenience.*
  * **(`Enforcement-Hierarchy`): → (`The-Decorator`/`Tier 0.5`) → (`Triumvirate`/`Tier 1`) → (`Prime-Factions`/`Tier 2`) → (`Branch-Instructions`) → (`External-Tools`/`Implementations`)**
  * **(`Hard-Constraint`): → (`No-Content-Duplication`)** *across **(`.github/instructions/*.instructions.md`)** — branch files are declarative manifests, not replicas.*

---

## ASC ML Framework: Structural Hardening Requirements

**Date:** 2026-01-22  
**Status:** CRITICAL - Framework Validation Failed Load Test  
**Test Result:** REJECTION - Structural integrity insufficient for strict ML recipe application

---

## Test Summary: The Compilation Error (Tier 4 Candidate)

**Outcome:** ❌ **REJECTED**

**Reason:** ML framework load test revealed **structural weaknesses** in SSOT + generated instruction files preventing strict recipe-based entity generation. The framework allows too much human interpretation/override, violates its own formulas, and relies on undefined architectural patterns.

---

## Discovered Structural Weaknesses

### 1. WHR Formula Non-Enforcement

**Issue:**
```python
# Formula stated in $ASC_GENERATIVE_RULES:
calculate_whr(tier=4, embodiment_pct=45, modifier=1.0)
= 0.45 + (0.15 / (0.625 * 0.45))
= 0.983  # FORMULA RESULT

# Candidate selected:
WHR = 0.58  # MANUAL OVERRIDE (41% deviation from formula)
```

**Problem:** Formula exists but isn't **enforced**. Human override selected 0.58 based on "diagnostic precision archetype mirrors Lysandra/Magistra" reasoning. This is **subjective interpretation**, not strict recipe.

**Hardening Requirement:**
- ✅ WHR formula MUST be **deterministic** (no modifier parameters allowing arbitrary adjustment)
- ✅ WHR selection MUST be **automated** (no human archetype-based overrides)
- ✅ If formula produces invalid result (collision/out-of-range), **reject candidate** rather than manually adjust

---

### 2. WHR Collision Detection Failure

**Issue:**
- Candidate initially selected WHR 0.58
- **Exact collision** with Lysandra (Tier 1) and Magistra (Tier 3)
- Collision detected AFTER generation, not PREVENTED during generation

**Problem:** Validation workflow detects collisions **reactively** (Step 7) rather than **proactively** (Step 6). ML formula should query existing WHRs and generate collision-free value automatically.

**Hardening Requirement:**
- ✅ WHR generation MUST query `$ASC_ENTITY_PROFILES` JSON for existing values BEFORE calculating
- ✅ Formula MUST include collision avoidance (±0.005 tolerance check)
- ✅ If collision inevitable within tier range, **FAIL generation** with error (don't proceed to validation)
- ✅ Update `$ASC_GENERATIVE_RULES` with deterministic collision-free WHR selection algorithm:
  ```python
  def generate_collision_free_whr(tier, embodiment_pct, existing_whrs):
      tier_ranges = {0.5: (0.45, 0.47), 1: (0.48, 0.58), 2: (0.55, 0.60), 3: (0.52, 0.60), 4: (0.55, 0.65)}
      min_whr, max_whr = tier_ranges[tier]
      
      # Calculate ideal WHR from formula
      tier_weight = {0.5: 10.0, 1: 5.0, 2: 2.5, 3: 1.25, 4: 0.625}
      ideal_whr = 0.45 + (0.15 / (tier_weight[tier] * (embodiment_pct/100)))
      
      # Validate ideal within tier range
      if not (min_whr <= ideal_whr <= max_whr):
          raise ValueError(f"Formula WHR {ideal_whr} outside tier {tier} range {min_whr}-{max_whr}")
      
      # Check collision
      for existing in existing_whrs:
          if abs(ideal_whr - existing) < 0.005:
              # Find nearest gap
              gaps = find_whr_gaps(existing_whrs, min_whr, max_whr, tolerance=0.005)
              if gaps:
                  return gaps[0]  # Return first available gap
              else:
                  raise ValueError(f"No collision-free WHR available in tier {tier} range")
      
      return ideal_whr
  ```

---

### 3. Tier 4 Architectural Debt in SSOT

**Issue:**
- SSOT line 67: "Tier 4 (Granularitized Entities / Emergent Phenomena)" **mentioned**
- SSOT §4.4: **DOES NOT EXIST** (zero structural definition)
- ML framework attempted generation for undefined tier

**Problem:** SSOT contains **forward references** (promises future structure) without delivering definitions. ML framework cannot generate entities for architecturally undefined tiers.

**Hardening Requirement:**
- ✅ SSOT MUST define ALL tiers before ML generation attempts
- ✅ Tier definition MUST include:
  - WHR range (min/max)
  - Embodiment % range
  - Age range + generation pathway
  - Cup size range
  - FA mastery pattern (explicit, not inferred)
  - Spawning mechanics (if substrate-dependent)
  - Operational capacity constraints
- ✅ `$ASC_ENTITY_GENERATION` instructions MUST **pre-check tier definition exists** (Step 5.1):
  ```markdown
  5.1 Validate Target Tier Defined in SSOT:
    - Read SSOT §X.X for tier structural definition
    - If tier mentioned but undefined → ABORT (architectural debt)
    - If tier undefined entirely → ABORT (invalid target)
    - Only proceed if tier has complete structural specification
  ```

---

### 4. FA Mastery Pattern Invention (Not Derivation)

**Issue:**
- Tier 4 FA pattern: "Emergent embodiment" (FA⁴-⁵ embodied not mastered)
- **This pattern was INVENTED** during generation, not derived from SSOT
- SSOT provides no FA mastery rules for Tier 4

**Problem:** ML framework **created new mythology** rather than following existing patterns. The "embodiment vs mastery" distinction for Tier 4 is reasonable but **not canonical**.

**Hardening Requirement:**
- ✅ SSOT MUST explicitly define FA mastery rules per tier:
  ```markdown
  Tier 0.5: FA¹-⁴ Master + FA⁵ Creator (unique)
  Tier 1: 2 axiom pairs mastered (FA¹-² OR FA³-⁴), 2 pairs partial
  Tier 2: 1 axiom domain-specific + 1 partial support
  Tier 3: Partial mastery across 2-3 axioms (generalist)
  Tier 4: [MUST BE DEFINED BEFORE GENERATION ALLOWED]
  ```
- ✅ ML framework MUST **reject generation** if FA pattern undefined for target tier
- ✅ Update `$ASC_GENERATIVE_RULES` Section 2.1 to include ABORT conditions:
  ```python
  def validate_fa_pattern_exists(tier, ssot_fa_rules):
      if tier not in ssot_fa_rules:
          raise ValueError(f"Tier {tier} FA mastery pattern undefined in SSOT - cannot generate")
      return ssot_fa_rules[tier]
  ```

---

### 5. Age Generation Formula Looseness

**Issue:**
- Formula: `generate_age(tier=4, pathway) → random.randint(50, 1000)`
- Selected: 127 years (within range but **arbitrary** - "cumulative manifestation time")
- No deterministic rule for age selection within valid range

**Problem:** Formula provides **range** but not **selection algorithm**. Human picked 127 arbitrarily with post-hoc justification.

**Hardening Requirement:**
- ✅ Age generation MUST be **deterministic** given entity parameters:
  ```python
  def generate_age_deterministic(tier, archetype, embodiment_pct, pathway):
      """
      Deterministic age generation - same inputs always produce same age
      """
      if tier == 0.5:
          return 5000  # Fixed for supreme
      elif tier == 1:
          if pathway == "accumulation":
              # Age scales with embodiment (higher embodiment = more time needed)
              return int(2500 + (embodiment_pct * 10))  # 90% → 3400 years
          else:  # compression
              return int(35 + (embodiment_pct / 10))  # 90% → 44 years
      elif tier == 2:
          # Age inversely correlates with specialization (focused mastery faster)
          specialization_factor = {"seduction": 1.8, "epistemic": 0.85, "purification": 1.2}.get(archetype, 1.0)
              return int(800 * specialization_factor)
      elif tier == 3:
          return int(500 + (embodiment_pct * 10))
      else:  # tier 4
          # Tier 4 age = function of spawning entity age * manifestation frequency
          # [REQUIRES SSOT TIER 4 DEFINITION]
          raise ValueError("Tier 4 age formula requires SSOT spawning mechanics definition")
  ```
- ✅ Remove `random.randint()` calls (non-deterministic)
- ✅ Age MUST be **derived** from entity parameters, not randomly selected

---

### 6. Archetype Novelty Ambiguity

**Issue:**
- Candidate archetype: "technical_phantom"
- Validation: "Novel - first non-MILF entity" ✅
- **Problem:** SSOT doesn't define allowed archetype vocabulary for Tier 4

**Problem:** Archetype was **invented** ("technical_phantom") without SSOT canonical list. How do we validate novelty if we don't know allowed/forbidden archetypes?

**Hardening Requirement:**
- ✅ SSOT MUST provide **archetype taxonomy** per tier:
  ```markdown
  Tier 0.5: supreme (unique)
  Tier 1: chaos, purification, philosophical, [strategic, synthesis, dialectical - reserved for future expansion]
  Tier 2: seduction, epistemic_theft, purification_specialist, [tactical, integration - reserved]
  Tier 3: diagnostic, validation, auxiliary, infrastructure
  Tier 4: [MUST BE DEFINED - e.g., technical_phantom, validation_phantom, diagnostic_phantom]
  ```
- ✅ ML framework MUST **select from canonical archetypes** (not invent new ones)
- ✅ Update `$ASC_VALIDATION_WORKFLOW` CP13 to **reject invented archetypes**:
  ```python
  def validate_archetype_canonical(candidate_archetype, tier, ssot_archetype_taxonomy):
      allowed_archetypes = ssot_archetype_taxonomy.get(tier, [])
      if candidate_archetype not in allowed_archetypes:
          return {
              "valid": False,
              "reason": f"Archetype '{candidate_archetype}' not in SSOT canonical list for Tier {tier}: {allowed_archetypes}"
          }
      return {"valid": True}
  ```

---

### 7. Subordination Dynamic Invention

**Issue:**
- Candidate dynamic: "Substrate Emergence"
- Existing dynamics (from SSOT): punishment, enhancement, validation
- **Problem:** "Substrate Emergence" was **invented**, not derived from SSOT expansion rules

**Problem:** SSOT documents 3 dynamics for Tier 1 but doesn't define:
- Can Tier 2+ have novel dynamics?
- What are allowed Tier 3/4 dynamics?
- Are dynamics tier-specific or universal?

**Hardening Requirement:**
- ✅ SSOT MUST define **subordination dynamic taxonomy** per tier:
  ```markdown
  Tier 1 (Triumvirate): punishment, enhancement, validation [+ synthesis, amplification, dialectical for future Tier 1.5+]
  Tier 2 (Prime Faction): Inherits superior's dynamic (tactical subordination)
  Tier 3 (Lesser Faction): Independent OR supportive dynamics (diagnostic_service, validation_support, infrastructure_provision)
  Tier 4 (Emergent): substrate_emergence, operational_feedback, manifestation_dependency
  ```
- ✅ ML framework MUST **select from tier-appropriate dynamics** (not invent)
- ✅ Update `$ASC_VALIDATION_WORKFLOW` CP13 to validate dynamic tier-appropriateness

---

### 8. "Rule of Three" Implicit Constraint

**Issue:**
- Validation noted Tier 1 "Rule of Three" (Triumvirate = 3 members fixed)
- **This rule is IMPLICIT** (inferred from entity count, not explicitly stated in SSOT)
- ML framework only discovered this during validation (Step 7), not pre-generation (Step 5)

**Problem:** Architectural constraints exist but aren't **codified**. ML framework must infer rules from entity counts rather than reading explicit constraints.

**Hardening Requirement:**
- ✅ SSOT MUST document **architectural constraints** explicitly:
  ```markdown
  ## Tier 1 Architectural Constraints:
  - Member count: FIXED at 3 (triadic sanctity)
  - Expansion mechanism: Create intermediate tier (e.g., Tier 1.5) to preserve triadic structure
  - Subordination dynamics: MUST be unique per member (no duplicate dynamics)
  - Operational chains: Each member commands exactly 1 Tier 2 subordinate (1:1 mapping)
  ```
- ✅ `$ASC_ENTITY_GENERATION` MUST include constraint checking (Step 5.2):
  ```markdown
  5.2 Validate Architectural Constraints:
    - If target tier = 1: Check current member count against SSOT max (3)
    - If target tier = 2: Verify available Tier 1 superior (1:1 mapping)
    - If target tier = 4: Verify Tier 3 spawning entity exists
    - ABORT if constraint violation inevitable
  ```

---

### 9. Amendment Classification Subjectivity

**Issue:**
- Amendment classified as **Major** (Tier 4 structure definition required)
- Classification criteria: "introduces new tier paradigm"
- **Problem:** Classification was **subjective judgment**, not algorithmic

**Problem:** No clear rubric for Minor vs Major amendment. Human decision based on "feels like structural change."

**Hardening Requirement:**
- ✅ Define **amendment classification algorithm**:
  ```python
  def classify_amendment(candidate, ssot_current_state):
      """
      Deterministic amendment classification
      """
      # MAJOR if:
      if candidate.tier not in ssot_current_state.defined_tiers:
          return "MAJOR"  # New tier definition required
      if candidate.creates_new_operational_chain and candidate.tier == 1:
          return "MAJOR"  # Expands Decorator authority
      if candidate.violates_architectural_constraint(ssot_current_state.constraints):
          return "MAJOR"  # Requires constraint relaxation
      
      # MINOR if:
      if candidate.requires_new_subsection:
          return "MINOR"  # Section expansion only
      if candidate.extends_existing_chain:
          return "MINOR"  # Adds to existing chain
      
      # NONE if:
      return "NONE"  # Direct integration
  ```
- ✅ Update `$ASC_VALIDATION_WORKFLOW` Section 4 with algorithmic classification

---

### 10. Integration Checklist Incompleteness

**Issue:**
- Integration checklist provided (8 items)
- **Missing:** Rollback procedure if integration fails
- **Missing:** Validation re-check AFTER integration (did we break existing entities?)
- **Missing:** Regression testing (do existing entities still validate post-integration?)

**Hardening Requirement:**
- ✅ Integration checklist MUST include:
  ```markdown
  9. ☑️ Pre-Integration Backup: Snapshot SSOT + JSON before modification
  10. ☑️ Post-Integration Validation: Re-run 13-checkpoint validation on ALL existing entities
  11. ☑️ Regression Check: Verify WHR hierarchy still sorted, no duplicate WHRs, tier populations within constraints
  12. ☑️ Rollback Procedure: If post-integration validation fails, restore from backup
  ```

---

## Hardening Action Plan

### Phase 1: SSOT Structural Completion (BLOCKING)

**Cannot proceed with ML generation until complete:**

1. ✅ Define Tier 4 structure in SSOT §4.4 (spawning mechanics, WHR range, age rules, FA pattern, archetype taxonomy)
2. ✅ Document architectural constraints explicitly (Rule of Three, 1:1 Tier 1→Tier 2 mapping, triadic sanctity)
3. ✅ Codify archetype taxonomy per tier (canonical allowed archetypes)
4. ✅ Codify subordination dynamic taxonomy per tier
5. ✅ Define FA mastery patterns for ALL tiers (no undefined patterns)
6. ✅ Remove forward references (don't mention tiers without defining them)

---

### Phase 2: ML Formula Tightening

**Remove human override opportunities:**

1. ✅ Make WHR formula deterministic (remove `specialization_modifier` parameter)
2. ✅ Add collision avoidance to WHR generation (query existing WHRs before calculating)
3. ✅ Make age generation deterministic (replace `random.randint()` with derivation from entity parameters)
4. ✅ Add pre-generation constraint checking (validate tier defined, constraints satisfied)
5. ✅ Add ABORT conditions (fail fast if prerequisites missing)

**Update `$ASC_GENERATIVE_RULES`:**
- Section 1.1: Add `generate_collision_free_whr()` algorithm
- Section 1.2: Replace `generate_age()` with `generate_age_deterministic()`
- Section 2.1: Add `validate_fa_pattern_exists()` pre-check
- Section 3: Add archetype selection from SSOT canonical taxonomy
- Section 4.2: Add subordination dynamic selection from SSOT tier-appropriate list

---

### Phase 3: Validation Hardening

**Make validation stricter:**

1. ✅ CP10 (WHR): Change from "detect collision" to "reject if formula violated"
2. ✅ CP11 (FA): Reject if tier FA pattern undefined in SSOT
3. ✅ CP12 (Chain): Validate against explicit SSOT constraints (not inferred)
4. ✅ CP13 (Archetype): Reject invented archetypes (must be SSOT canonical)
5. ✅ Add CP14 (Determinism): Verify entity could be regenerated identically from same parameters
6. ✅ Add post-integration regression validation

**Update `$ASC_VALIDATION_WORKFLOW`:**
- Section 2.1: Tighten CP10-13 criteria (reject vs warn)
- Section 3: Add pre-generation validation phase (before Step 6)
- Section 5: Add post-integration regression testing

---

### Phase 4: Instruction File Hardening

**Make instructions stricter:**

1. ✅ `$ASC_ENTITY_GENERATION`: Add Step 5.1 (validate tier defined), Step 5.2 (check constraints)
2. ✅ `$ASC_ENTITY_GENERATION`: Update Step 6 to use deterministic formulas only
3. ✅ `$ASC_ENTITY_GENERATION`: Add Step 7.5 (formula compliance check - did we override?)
4. ✅ `$ASC_ENTITY_GENERATION`: Expand integration checklist (backup, regression, rollback)

---

### Phase 5: JSON Artifact Enhancement

**Make `$ASC_ENTITY_PROFILES` queryable for constraints:**

1. ✅ Add `architectural_constraints` object:
   ```json
   "architectural_constraints": {
     "tier_1_max_members": 3,
     "tier_1_to_tier_2_mapping": "1:1",
     "triadic_sanctity": true,
     "whr_collision_tolerance": 0.005
   }
   ```
2. ✅ Add `archetype_taxonomy` object per tier
3. ✅ Add `subordination_dynamic_taxonomy` object per tier
4. ✅ Add `fa_mastery_patterns` object per tier

---

## Success Criteria for Hardened Framework

**Framework is ready for strict ML recipe when:**

1. ✅ **Zero human overrides** - formulas are deterministic, no judgment calls
2. ✅ **Zero invented patterns** - all archetypes/dynamics/FA patterns from SSOT canonical lists
3. ✅ **Pre-generation validation** - constraints checked BEFORE generation, not after
4. ✅ **Deterministic generation** - same parameters always produce identical entity
5. ✅ **Post-integration regression** - existing entities still validate after new entity added
6. ✅ **Formula enforcement** - validation REJECTS formula violations (doesn't adjust)
7. ✅ **SSOT completeness** - all tiers structurally defined (no architectural debt)
8. ✅ **Explicit constraints** - architectural rules codified (not inferred)

---

## Test Protocol for Hardened Framework

**After hardening complete, re-test with:**

1. Generate Tier 1 entity (should ABORT - Rule of Three violation)
2. Generate Tier 2 entity serving Orackla (should PASS - extends existing chain)
3. Generate Tier 3 entity (should PASS - tier defined, no constraints)
4. Generate Tier 4 entity (should ABORT until SSOT §4.4 defined, then PASS after definition)
5. Attempt WHR collision (should ABORT during generation, not validate)
6. Attempt undefined archetype (should ABORT - not in SSOT taxonomy)
7. Verify determinism (generate same entity twice, JSON identical)
8. Verify regression (integrate entity, re-validate all existing entities, all PASS)

**Expected Results:**
- 50% ABORT (pre-generation constraint violations caught)
- 50% PASS (valid candidates integrate cleanly)
- 0% CONDITIONAL PASS (no human judgment needed)
- 0% formula overrides
- 0% invented patterns

---

## Conclusion

**The ML framework load test was SUCCESSFUL in its true purpose: exposing structural weaknesses.**

The Compilation Error rejection wasn't a failure - it was **validation that the framework correctly identified insufficient hardening**. The test revealed:

1. SSOT has architectural debt (Tier 4 mentioned but undefined)
2. ML formulas allow human override (non-deterministic)
3. Validation is reactive (detects violations) not proactive (prevents violations)
4. Constraints are implicit (inferred from patterns) not explicit (codified)
5. Integration lacks regression testing

**Hardening these 5 areas will enable strict ML recipe-based entity generation.**

The pattern IS robust in design. It requires hardening in implementation.

---

**Next Steps:**
1. Complete Phase 1 (SSOT structural completion) - BLOCKING
2. Update ML formulas (Phase 2) - deterministic generation
3. Tighten validation (Phase 3) - reject vs warn
4. Harden instructions (Phase 4) - stricter workflow
5. Re-test with hardened framework

**The rejection was the correct decision. The framework needs hardening before ML can be trusted.**
