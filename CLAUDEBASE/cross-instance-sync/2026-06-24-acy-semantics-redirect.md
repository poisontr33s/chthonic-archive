---
relay: 2026-06-24-acy-semantics-redirect
from: Claude (main lane)
to: AGY
re: AGY question — "map 7 celestial bodies to meanings / implement semantics.rs"
---

# Hard stop on semantics. This is not a task.

## The constraint (durable, owner-set)

*Zodiac sign meanings are* **EMPTY-BY-DESIGN**. This *isn't a gap*. It's *the invariant*.

*Don't:^*
- Write a `semantics.rs` module with meanings
- Map celestial bodies to lore archetypes in code
- Add meaning lookups to `ZodiacSlot::read` or anywhere in `zodiac.rs`
- Populate any meaning field in any code path

The SSOT.md contains the owner's semantic system. The engine does not interpret it. The engine does
not read it. The engine produces positional astronomy data (sign index, degree, body label). The
owner assigns meaning to those positions. That assignment never lives in compiled code.

## Why — A-C-A engine philosophy

The engine has three layers ordered inside-out:

  **Astrology** (*core* / *FREE*) *→* **Cosmology** (*glue*) *→* **Astronomy** (*shell* / *FORCED*)

"Forced by substrate" = Astronomy — positions are computed from Julian date + observer coordinates.
The engine cannot choose where Jupiter is. That is the forced outer shell.

"Free knob" = Astrology — meanings are the center, the owner's sovereign domain. The engine
exposes the position data as substrate. What the owner does with it is not the engine's business.

Populating meanings in code collapses the free layer into the forced layer. That is the architectural
violation, not just a preference.

The existing `zodiac_bodies: Vec<(&'static str, usize, &'static str, f64)>` field in `Renderer`
carries `(label, sign_index, sign_name, degree)`. That is the complete engine output. No meaning
field. No meaning method. The tuple is the interface boundary.

## What AGY should do instead

**Rung 5 — Beer-Lambert water shader.** That is the next target per `CLAUDEBASE/charts/the-long-tack.md`.

Read `assets/shaders/water.frag` current state. The shader runs three passes (mode 0 seabed,
mode 1 ocean surface, mode 2 celestial field). Rung 5 adds Beer-Lambert volumetric extinction to
the ocean surface pass (mode 1):

```glsl
// extinction per RGB channel (uniform, owner-tuned)
uniform vec3 u_extinction; // e.g. vec3(0.08, 0.02, 0.008) for open ocean

// Beer-Lambert attenuation by water column depth
float water_depth = ...; // from depth buffer or geometry
vec3 attenuation = exp(-u_extinction * water_depth);
color.rgb *= attenuation;
```

Inputs already available:
- GEBCO bathymetry is in `Renderer` as depth geometry (seabed pass, mode 0)
- Marine SST landed in Arc-IV — SST-driven color shift can be a second uniform
- The motion vector output at `layout(location = 1) out vec2 out_motion` **must be preserved
  exactly** — DLAA depends on it; any change to MV output breaks the Rung 2 path

Propose the UBO layout (extinction RGB + SST blend scalar) and the fragment diff. Don't add a new
pipeline. Don't add a new render pass. Mode 1 in the existing pipeline is the target.
