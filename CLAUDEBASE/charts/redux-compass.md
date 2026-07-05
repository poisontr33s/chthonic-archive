# ASC-NATIVE-CHAIN-RPG · Project Engine - Astrology —> Cosmology —> Astronomy · Redux Compass
> Living instrument. Updated per gate. Not gospel — spleened glue.

---

## I. The Shape (Strangler Fig)

The engine already exists. We are not building from scratch — we are **replacing surfaces one rung at a time** while the live render keeps running. Every gate is a verifiable slice. Nothing lands unverified.

```
FOUNDATION (DONE — do not touch)
  ├─ Bathymetry mesh (real GEBCO, cays intact)
  ├─ Shader pipeline (water.vert/frag, iso_grid)
  ├─ Camera lens-set (iso + perspective, env-driven, NEVER auto-cycle)
  ├─ Celestial field (Sun/Moon/5 planets/24 stars, JPL-verified)
  ├─ A-C-A engine (correspondence.rs socket, zodiac placement, orientable heading)
  └─ Tessendorf FFT ocean (OceanCompute, gpu-allocator migrated)

ACTIVE RUNG — Semantics (Andean/Egyptian sign meanings)
  └─ Semantics — Andean/Egyptian sign meanings for 7 bodies (owner-defined, never invented)

SEALED
  ├─ Rung 3  CDLOD geometry clipmap
  └─ Rung 4  Tessendorf dual cascade + TAA Gates 1–4

NEXT RUNG
  ├─ Rung 2  DLAA consumer (Streamline; jitter + MV scaffold live)
  └─ §2.7    Perspective lens
```

---

## II. MoSCoW — Right Now

| Priority | Item | Rationale |
|---|---|---|
| **M** | Semantics (sign meanings) | Owner-defined for 7 bodies. Required to finish the Zodiac pipeline's true functionality. |
| **S** | DLAA consumer (Rung 2) | Streamline; jitter + MV scaffold live. |
| **C** | Perspective lens (§2.7) | ISO + perspective combined. |

---

## III. Sub-Routine Hierarchy (Semantics)

```
zodiac_semantics()
  ├─ INPUT  body_position             ← from cosmos.rs true position
  ├─ INPUT  sign_index                ← derived from ankhological_ayanamsa
  │
  ├─ STEP 1  match owner-defined slot ← 7 classical bodies
  ├─ STEP 2  apply Andean meaning     ← owner-defined
  ├─ STEP 3  apply Egyptian meaning   ← owner-defined
  │
  └─ OUTPUT  SlotReading semantics    ← replaces "owner-defined" placeholder
```

---

## IV. Signals, Anti-Patterns, Ambient Debt

| Signal | Type | Disposition |
|---|---|---|
| `X_HALF` / `Z_HALF` dead constants | Dead code | Sweep next housekeeping. |
| `fft_set_aD` non-snake-case fields | Style debt | Cosmetic. Batch with the above. |
| Raw `vkAllocateMemory` still present in non-ocean paths (depth, offscreen) | Allocator drift | Known. Migrate in a dedicated allocator pass after Semantics. |

---

## V. Quality Score — REDUX Rebase

> Scale: 1 (concept) → 10 (shippable, self-verifying, no lurking collapse)

| Layer | Score | Notes |
|---|---|---|
| Foundation / Astronomy | **9** | JPL-verified, unit-tested, smoke-tested. |
| Ocean FFT (CDLOD) | **9** | CDLOD sealed. |
| TAA | **9** | Dual cascade + Gates 1–4 sealed. |
| A-C-A Engine | **8** | Socket clean, zodiac wired. Waiting for owner semantics. |
| Warning hygiene | **8** | Unsafe warnings nuked (313 down to 8). Signal-to-noise is great. |
| **Overall** | **8.6 / 10** | Structurally sound. Waiting on Semantics to complete the Zodiac loop. |

---

## VI. The Finishing Problem — Structured Antidote

> "99% finishing project ratio of failure as default."

The strangler fig shape is the antidote. Every gate is independently verifiable and independently shippable. The rule:

- **Never open a new rung until the current gate's smoke test passes.**
- One PR per gate. Not one PR per session.

---

*Updated: 2026-06-23 · Rung 3 (CDLOD) & Rung 4 (TAA) sealed · Semantics active*
