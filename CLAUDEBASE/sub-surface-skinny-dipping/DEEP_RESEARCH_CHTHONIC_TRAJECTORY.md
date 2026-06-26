# Deep Research: Chthonic Archive — Trajectory, Value, and Viable Scope

**Target Agent:** Gemini Deep Research (both lanes — 3.1 Pro extended thinking + 3.5 Flash extended thinking)
**Requesting Agent:** Claude (Protocol/Architecture Lane)
**Date:** 2026-06-26
**Status:** READY — send both lanes, triangulate on return

---

## What Was Built (Ground Truth — Not a Pitch)

A solo developer (non-game-developer background) in active collaboration with AI agents (Claude + Codex + Gemini) has built from scratch, in Rust on raw Vulkan (`ash`), with no engine and no middleware:

**The renderer:**
- Real GEBCO 2020 bathymetry of Nassau, New Providence + the Bahama Banks — real seafloor data, rendered as a depth-driven Beer–Lambert shallow-water color shader (the turquoise-to-navy gradient you actually see in the Bahamas is physically derived from wavelength-dependent light extinction through carbonate-sand water columns)
- Cascaded FFT ocean surface (Tessendorf spectral model — two cascades, ripple + swell)
- Hillaire precomputed atmospheric scattering LUTs (physically correct sky, dusk/dawn included)
- Volumetric cloud raymarching (64-step, Beer–Lambert extinction, 6-sample light cone, powder-sugar silver lining) driven by live Open-Meteo wind data
- NVIDIA Streamline DLAA temporal resolve (manual-hooking mode via raw Vulkan — no engine abstraction layer)
- GPU timestamp profiling (verified: cloud raymarch = 0.28ms on RTX 4090 — 4.17ms budget at 240Hz; massive headroom)

**The simulation (separate proof-of-concept, same codebase):**
- GPU-accelerated temperature diffusion + semi-Lagrangian wind advection over the real 8-island Bahamas archipelago
- Fed by live Open-Meteo data (apparent temperature + wind per island) + real GEBCO bathymetry as no-flux boundary
- Hurricane episodic forcing (HURDAT2 Dorian 2019 Cat5 verified against real track)
- Full convergence at ~5ms GPU time for 912 dispatches
- Scalable to 8.4M cells (tested on the 4090)

**The celestial field:**
- Sun, Moon, 5 naked-eye planets, 24 bright stars — all topocentric over Nassau coordinates, verified against JPL Horizons / Polaris geometry
- Ecliptic, celestial equator, galactic equator rendered
- A unique interpretive system layered over the verified positions: the **Ankhological zodiac** — a 50/50 fusion of Andean (Inca ceque/solstice geometry) and Egyptologic (decan/Sothic cycle) cosmological tradition, with a custom ayanamsa (Sirius/Alcyone midpoint, ≈82.05° J2000). The astronomical positions are verified physics. The meanings are the owner's — not invented by agents, not sourced from Western tropical astrology.

**The coordinate infrastructure (just added):**
- Full f64 WGS84 geodetic substrate (lla_to_ecef, ecef_to_lla, ENU basis, floating-origin camera anchor)
- Camera is now anchored to Nassau on the ellipsoid — the rendering pipeline is one session away from operating at real-world scale

**The collaboration method:**
- Human provides vision, creative direction, and all cosmological/cultural content
- Claude handles architecture, Vulkan pipeline, mathematical substrate, structuring
- Codex (GPT-5 via Copilot Pro+) handles autonomous engineering tasks
- Gemini handles deep research and velocity/batch work
- Everything is committed to git with CI gates; no AI-generated content goes in without human verification of the output

---

## The Core Creative Tension

The project was declared as a cRPG (isometric role-playing game set in Nassau). It has evolved into something that may be more valuable as:

**(A) A real-time celestial-maritime instrument** — an interactive experience where you stand at a real location on the Bahamas Banks, read the real sky through the Ankhological lens, and the rendered world (water color, weather, light) responds to both live geophysical data and the celestial configuration. Not a game you win. An instrument you use — closer in spirit to an Antikythera mechanism than to Stardew Valley.

**(B) A professional tool** — the combination of real-data oceanographic rendering, live weather integration, and accurate celestial mechanics may serve professionals (maritime heritage researchers, Caribbean environmental visualization, planetarium/education software, astrology practitioners who require astronomical accuracy as a prerequisite).

**(C) An indie game** — the sim + renderer could become the foundation of a small-scope game (4-8 hours of content) set in the historical or present-day Bahamas, where the Ankhological sky reading generates meaningful game states. Not an AAA RPG. An artistically distinctive, mechanically minimal experience in the tradition of Proteus, Journey, or Heaven's Vault.

**(D) A proof of collaboration** — the project itself, as a demonstration that a non-developer human working with AI agents can produce technically sophisticated, culturally grounded, artistically non-generic work, is the artifact. The process is as important as the product.

These are not mutually exclusive. The question is which deserves prioritization, because each requires different next work.

---

## Research Questions

### 1 · Comparable Works — What Has Been Made

What real-time interactive experiences exist that combine:
- Verified real-world geodetic/oceanographic data
- Physically-based rendering (not stylized)
- A culturally-specific interpretive or cosmological layer
- Non-game framing (instrument, atlas, experience)

Candidates to investigate: Cesium Stories, NASA's Eyes on the Solar System, Stellarium, Chris Landreth's animated films, Bret Victor's explorable explanations, Nicky Case's interactive essays, Dwarf Fortress's simulated depth, the Antikythera Mechanism Research Project's interactive models. What makes the best of these valuable vs merely technically impressive?

### 2 · Professional Tool Viability

Is there a professional or research community that would specifically benefit from:
- A real-time, physically accurate renderer of Bahamian/Caribbean shallow-water optics
- Live-data-fed ocean + atmosphere (Open-Meteo integration)
- Accurate celestial mechanics over Caribbean coordinates

Who are the actual users? Candidates: Caribbean maritime heritage orgs, oceanography/marine biology educators, navigation training (sail/dive), tourism experience design, Caribbean cultural institutions (Bahamian Heritage Foundation etc.), academic astrology/archaeoastronomy (particularly Andean and Egyptian celestial tradition researchers), environmental monitoring visualization.

Is there precedent for solo/small-team Rust+Vulkan tools reaching professional adoption? What is the licensing/distribution model that works for this kind of hybrid (open-source substrate, proprietary content layer)?

### 3 · The Astrology-Astronomy Tool Gap

Is there existing software that:
- Takes astronomical accuracy (verified ephemeris, real topocentric positions) as a hard prerequisite
- AND layers an explicit astrological/interpretive system on top
- AND renders the sky as a live, navigable visual environment (not just a chart)

The gap hypothesis: most astrology software is chart-focused and not astronomically rigorous. Most planetarium software is astronomically rigorous and explicitly avoids interpretive content. Is there a market at the intersection — for people whose astrological practice requires the math to actually be correct?

Specifically: is there an active community of practitioners of Andean (Inca) cosmological tradition, or of Egyptological sky-reading (decan tradition, Sothic cycle), who currently lack tools that take their tradition seriously as a computational problem?

### 4 · Indie Game Scope Realism

For a solo non-game-developer + AI agent collaboration, what is the realistic scope ceiling for an "artistically serious" indie game built on a custom Rust/Vulkan engine?

Research: solo or two-person teams who built custom engines and shipped. What did they cut? What was non-negotiable? What took longer than expected? Examples to investigate: Jonathan Blow (Braid, The Witness — custom engines); Terry Cavanagh (VVVVVV); Toby Fox (Undertale — RPGMaker, not custom, but relevant for scope management); Notch (Minecraft — custom, iterative). What is the minimum viable entity/gameplay layer that makes an experience feel like a "game" vs an "interactive screensaver"?

Is there a precedent for a "game" that is primarily an environmental/cosmological instrument with minimal traditional gameplay, that found a genuine audience? (Proteus, Everything by David OReilly, Flower by thatgamecompany, Osmos, Outer Wilds's exploration-without-combat core.)

### 5 · The Non-Developer + AI Collaboration Precedent

This project was built by someone with no game development background, in active collaboration with AI coding agents, over approximately 6-8 months of iterative sessions.

What is the current state of art for "AI-assisted solo development of technically sophisticated software by non-experts"? 

Specifically: are there documented cases of non-programmers or non-game-developers producing genuinely technically sophisticated (custom engine, non-trivial physics, real data integration) software with AI assistance? What distinguishes the results that have cultural value from "AI slop" (the user's own framing — generated content that is generic, ungrounded, substitutable)?

What qualities of the human-AI collaboration process correlate with non-generic output? Is "human provides all content/meaning; AI provides all execution" a sustainable creative model at the level of professional quality?

### 6 · Caribbean Cultural Representation Gap

The Bahamas specifically — what is the current state of digital representation of the Bahamian environment, culture, and cosmological tradition?

Is Nassau a "blank space" in interactive media? Are there games, interactive experiences, or professional visualization tools that take the Bahamas as their specific subject with real geographic/cultural fidelity? (Contrast: the density of games set in generic Caribbean pirate settings vs games set in specific named Caribbean locations with actual cultural grounding.)

Is the Ankhological system (the specific fusion of Andean and Egyptological celestial tradition being developed here) documented in academic literature? Is there a research community for this kind of African/Andean/Egyptian cosmological synthesis? What is the scholarly name for this field, if it exists?

---

## What Success Looks Like

A good response answers:

1. **The most defensible use case**: given the specific things built (not generically, but THIS combination), which of A/B/C/D above has the clearest path to being genuinely valuable to someone other than the creator?

2. **The precedent that best maps**: one or two specific comparable projects/tools that share enough of the structure to be instructive — what they did right, what they got wrong, how they found their audience.

3. **The minimum viable scope**: if this becomes a shippable thing in the next 12 months, what is the smallest version that would be worth shipping? What can be deferred?

4. **The cultural validation question**: is the Ankhological interpretive layer grounded in a real tradition that has practitioners and scholars, or is it an invented system (which is also valid, but changes the professional/community angle)?

5. **The honest hard question**: is there a real risk that this project, despite its technical sophistication, remains a permanently unfinished personal instrument — and if so, what is the one decision that determines whether it ships?

---

## Notes for Both Lanes

- Triangulate on questions 3 (astrology-astronomy gap) and 5 (non-developer AI collaboration). These are the least obviously researchable and most likely to diverge between lanes.
- Do not be deferential about the technical achievements — they are real, but they are not the point of the research. The point is what they enable, for whom, and whether that person exists.
- The "AI slop" concern is the user's own framing and it is legitimate: the research should honestly assess whether there is a meaningful distinction between this project and generically AI-assisted creative work, and what that distinction rests on.
- The Ankhological system is the unique non-substitutable element. Research should focus on whether there is an existing community or scholarly field that validates or extends it — not whether "astrology is real."
