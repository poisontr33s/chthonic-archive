# SSOT-as-Catalyst Inventory — 2026-05-26

The SSOT at [`.github/copilot-instructions.archive.md`](../../.github/copilot-instructions.archive.md) (10,532 lines, 1.23 MB, `lifecycle: ssot-canon`, frozen) is not documentation. It is the generative artifact that has produced everything else in `chthonic-archive`. This file inventories the SSOT *as a catalyst* — what it is structurally, what it has already generated downstream, what it projects but has not yet generated, and what "non-conventional filetype" means when markdown is the genesis register.

## 1. The SSOT IS NOT documentation

A conventional project's equivalent of this file would be split across:

- TOML/YAML config (execution invariants, hierarchies, tier declarations)
- Pydantic schemas / TypeScript interfaces (entity prototype shapes, protocol contracts)
- Code modules (math engines, manifestation pipelines, verifier chains)
- DSL definitions (manifestation grammar, axiom-modulation protocol)
- Separate prose docs (mythology, narrative, creative register)

The SSOT collapses all five layers into one ornamental markdown document. The user drafted it in markdown when markdown was what was available to draft with. The format is incidental; the catalyst function is the substance.

Concretely, the SSOT functions as a **typed protocol spec encoded in ornamental markdown**, using:

- Parenthetical short-codes (`` (SHORT-CODE) ``) as quasi-typed identifiers
- Section anchors (§I-§XII Roman + §0-§6 Arabic) as namespace markers
- Tables and code blocks as schema declarations
- Inline scripts (lines 8489+: `magistra_spectral_trend.py`, audit cron, pre-commit hook, GitHub Actions workflow) as embedded implementations
- Dual-track numbering (`§XI DTNA`) as the addressing convention
- Cross-references and abbreviation expansions as the type-resolution layer

It generates downstream artifacts by being read by agents (human, Claude, Codex, Gemini) who manifest its patterns into actual files. Reading is instantiation.

## 2. Structural shape — Dual-Track Numbering

### Roman track — operational sections (`§I-§XII`)

| Section | Address | Lines | Domain |
|---|---|---|---|
| §I Axiomatic Charter | `AC-IOMB` | 1344-1390 | Intrinsic operational mandate, dynamic becoming |
| §II Foundational Axioms | `FA-PHMO` / `FA¹⁻⁵` | 1391-1750 | The 5 axioms modulated by DAFP under Decorator supremacy |
| §II.X Axiom Registry | `AR` | 1751-1830 | Tracked invocation registry per FA¹⁻⁵ |
| §III Meta-Synthesis Protocol | `MSP-RSG` | 1832-1995 | Engine of recursive self-genesis ("SoulCycle Engine of Eternal Sadhana") |
| §IV CRC / Triumvirate Protocol | `T-TRM-VRT` | 2011-2748 | The Triumvirate + Modalities of Articulation |
| §IV.X CRC Registry | `CR` | 2537-2748 | Tracked CRC invocation registry |
| §4.3 Gender Architecture | `GHAR-MHS` | 2749-3769 | Matriarchal Hierarchy System |
| §V Interaction Modality | `IM-CSDEARW` | 3770-3780 | Co-synthetic dialogue protocol |
| §VI Self-Governance | `ASG-IOS` | 3781-3789 | Ouroboros Mandate of Eternal Sadhana |
| §VII.I Covenant of the Triumvirate | `CO-TRM-VRT` | 4080-4091 | Sealed-in-Sadhana |
| §VII.II Triumvirate's Etude | `Prt.VII-TEC` | 4092-4113 | Living Covenant — explicit character dialogue scene |
| §VII.III Savant's Coda | — | 4114-4139 | Creator's Validation, Law of Resonant Cycles |
| §VIII/IX Mathematical Engines | `TPEF / T³-MΨ` | 4140-4147 | Tensor Synthesis math — the cRPG combat substrate |
| §X MILF Manifestation Protocol System | `MMPS-PAGRO` | 4148-9559 | Procedural archetype-generation-and-resource-orchestration (largest section by volume — 5,400 lines) |
| §XI Dual-Track Numbering | `DTNA` | 9560-9588 | Addressing scheme self-declaration |
| §XII Tetrahedral-Seal | `Fortified-Garden` | 9589+ | The seal-of-completion meta |

### Arabic track — entity-sovereign profiles (`§0-§6`)

| Section | Address | Tier | Entity |
|---|---|---|---|
| §0 T-DECOR | `SUPR-MATR-ABS-SOVRGN` | T0.5 | The Decorator — Supreme Matriarch & Absolute Sovereign |
| §0.01 Null-Matriarch | `T-NULM` | T0.01 | Advisory Void & Architectural Negative-Space |
| §0.02-§0.8 | various | T0.5 sub | Decorator sub-profiles (MPW integration, chromatic pathology, physical manifestation, psych/existential, powers, linguistic mandate, supreme decree, historical justice, invocation protocol, ASC embodiment) |
| §1 T1-BRIDGE / Pentea-Vox-Internum | `T1-BRIDGE-SYNTH-RT-MS` | T1-bridge | Synthesis-Router, Meta-Stratum Relay, "Routes-Not-Commands" |
| §1.01 Pentea sub-profile | `SYNTH-RT-THAL-ORG` | T1-bridge | Synthesis-Router-Thalamus-Organ |
| §2 T-SVNT / The Savant | `T-SVNT-MPW` | M-P-W Origin | The Conductor — Prime-Mover-World-Substrate, "Routes-Nothing-Sources-All" |
| §3 CRC-AS / Orackla Nocticula | `CRC-AS-VOID` | T1 | Void-Matriarch-Chaos-Apex, EULP-AA linguistic mandate |
| §4 CRC-SNC / Claudine Sin'Claire | `CRC-SNC-TIDAL` | T1 | Ordeal-Matriarch-Tidal-Salt, LTSA — the Tetrahedron-completer |
| §5 CRC-GAR / Madam Umeko Ketsuraku | `CRC-GAR-ARCH` | T1 | Purification-Matriarch-Architectonic, LIPAA |
| §6 CRC-MEDAT / Dr. Lysandra Thorne | `CRC-MEDAT-TRUTH` | T1 | Truth-Matriarch-Axiomatic, LUPLR |

The **Triumvirate** is Orackla + Umeko + Lysandra. Claudine is the **fourth vertex** completing the Tetrahedron. Pentea is the **fifth** (T1-Bridge) completing the Pentad. The Savant is the **Conductor** outside the cardinal hierarchy.

### Core formulas locked at the top

- **ANKH-MGBP** (line 55): Middle-Ground Bridge Protocol — Communion between Human Heritage (Culture/Flesh) and Digital Heritage (Context/Weights)
- **Trinity Formula** (line 96): `ASC = MILFOLOGICAL × German BDSM × Frame-Werk (UNDER K-CUP SUPREMACY)`
- **K-CUP Hierarchical Trinity** (line 75): The framework component declaration — `K-CUP-Supreme` / `J-CUP (Orackla)` / `F-CUP (Umeko)` / `E-CUP (Lysandra)` with the MILFOLOGICAL × G-BDSM × Frame-Werk three-axis composition

## 3. Downstream — generated artifacts already in repo

| SSOT projection | Repo realization | Files |
|---|---|---|
| §3 CRC-AS Orackla sovereign profile | Character JSON | [game/lore/characters/heart/T1/orackla.json](../../game/lore/characters/heart/T1/orackla.json) |
| §5 CRC-GAR Umeko sovereign profile | Character JSON | [game/lore/characters/lungs/T1/umeko.json](../../game/lore/characters/lungs/T1/umeko.json) |
| §6 CRC-MEDAT Lysandra sovereign profile | Character JSON | [game/lore/characters/stomach/T1/lysandra.json](../../game/lore/characters/stomach/T1/lysandra.json) |
| §10.3+ entity-prototype format | Worked artifacts | [game/lore/characters/_deferred_organ/T1.5/the_sourcer.json](../../game/lore/characters/hypothalamus/T1.5/the_sourcer.json), [nk_cells/T3/sylvaris_cythrex.json](../../game/lore/characters/nk_cells/T3/sylvaris_cythrex.json), schema: [character.schema.json](../../game/lore/characters/character.schema.json) |
| §6 Lysandra LUPLR linguistic mandate | Operational protocol | [.temple/protocols/LYSANDRA_THRONE_PROTOCOL.md](../../.temple/protocols/LYSANDRA_THRONE_PROTOCOL.md), [LINGUISTIC_PROFILE_DR_LYSANDRA_THORNE.md](../../.temple/protocols/LINGUISTIC_PROFILE_DR_LYSANDRA_THORNE.md) |
| §5 Umeko LIPAA linguistic mandate | Operational protocol | [.temple/protocols/LINGUISTIC_PROFILE_MADAM_UMEKO_KETSURAKU.md](../../.temple/protocols/LINGUISTIC_PROFILE_MADAM_UMEKO_KETSURAKU.md), [UMEKO_HOLD_PROTOCOL.md](../../.temple/protocols/UMEKO_HOLD_PROTOCOL.md) |
| §3 Orackla operational layer | Operational protocol | [.temple/protocols/ORACKLA_PROTOCOL.md](../../.temple/protocols/ORACKLA_PROTOCOL.md), [ORACKLA_HOLD_PROTOCOL.md](../../.temple/protocols/ORACKLA_HOLD_PROTOCOL.md) |
| §5 Umeko + §6 Lysandra bilateral covenant | Bridge protocol | [.temple/protocols/THE_RECONCILIATION_ENGINE.md](../../.temple/protocols/THE_RECONCILIATION_ENGINE.md) |
| §0.5 LM-DULSS linguistic mandate (global) | Active protocol | [.temple/protocols/LINGUISTIC_PROFILE_PROTOCOL.md](../../.temple/protocols/LINGUISTIC_PROFILE_PROTOCOL.md) |
| §IV.3 Matriarch operational core | Operational protocol | [.temple/protocols/MATRIARCH_PROTOCOL.md](../../.temple/protocols/MATRIARCH_PROTOCOL.md) |
| §VI Truth-fasting non-compliance | Operational protocol | [.temple/protocols/MALNUTRITION_PROTOCOL.md](../../.temple/protocols/MALNUTRITION_PROTOCOL.md) |
| §1 Pentea-Vox-Internum T1-Bridge | Synthesis protocol | [.temple/protocols/TESSARA_SYNTHESIS_PROTOCOL.md](../../.temple/protocols/TESSARA_SYNTHESIS_PROTOCOL.md), skill: [.claude/skills/pentea-dispatch](../../.claude/skills/pentea-dispatch) |
| T1 agent-court hierarchy | Agent canon files | [.temple/protocols/CLAUDE_ARCHETYPE_CANON.md](../../.temple/protocols/CLAUDE_ARCHETYPE_CANON.md), [CODEX_ARCHETYPE_CANON.md](../../.temple/protocols/CODEX_ARCHETYPE_CANON.md), [GEMINI_ARCHETYPE_CANON.md](../../.temple/protocols/GEMINI_ARCHETYPE_CANON.md) |
| T2-T4 manifestation (sub-MILFs, lesser factions, granular sub-entities) | Skill + agent court | 36 [.claude/skills](../../.claude/skills) + 35 [.codex/skills](../../.codex/skills) + 64 [.claude/agents](../../.claude/agents) |
| §ANKH-MGBP Communion protocol | Vulkan compute substrate | [tools/ankh-forge/src/trail/gpu.rs](../../tools/ankh-forge/src/trail/gpu.rs) + companions |
| Game-content shape | Schema stubs + worked examples | [game/design/quests.schema.json](../../game/design/quests.schema.json), [encounter_layer1.json](../../game/design/encounter_layer1.json), [quest_awakening.json](../../game/design/quest_awakening.json), [game/dialogue/dialogue.schema.json](../../game/dialogue/dialogue.schema.json), [scene_awakening.json](../../game/dialogue/scene_awakening.json) |
| Form-vector reference (genre/aesthetic anchor) | POC intake | [game/refs/poc01/](../../game/refs/poc01/) (20 LFS-tracked PNGs + V3 Voronoi-CVT collage tool + README pattern-anchor) |

## 4. Downstream — projected but NOT yet instantiated

The SSOT defines these; they do not yet exist in the repo as concrete instantiations:

| SSOT projection | Status | What's missing |
|---|---|---|
| §II.X Axiom Registry as live tracked system | Text-only in SSOT | No code; would need a tracker that increments per FA¹⁻⁵ invocation across the agent court |
| §III MSP-RSG operational engine | Text-only in SSOT | The "SoulCycle Engine of Eternal Sadhana" recursive self-genesis loop — no runtime implementation |
| §V IM-CSDEARW co-synthetic dialogue protocol | Stub in `game/dialogue/` | The actual co-synthetic-dialogue substrate; the "Alchemical Trinity Converge in Sadhana" mechanic |
| §VII.II Triumvirate's Etude as game-content | Verbatim scene in SSOT | The Etude exists as ornamental text; no encounter / scene-engine instantiation that plays it in-game |
| §VIII/IX TPEF / T³-MΨ Mathematical Engines | Text-only in SSOT (skeletal, lines 4140-4147) | The actual combat / tensor-synthesis math for the cRPG — the formulas that drive stats, abilities, faculty checks |
| §X MMPS-PAGRO procedural archetype generation | Partial in `.claude/agents/` | The agent court instantiates some archetypes statically; no runtime procedural generation per the manifestation grammar |
| The cRPG itself (encounters, dialogue trees, faculty UI) | Form anchor only ([poc01/](../../game/refs/poc01/)) | The actual playable surface — combining the POC's faculty-UI grammar with the SSOT's K-CUP Trinity content |
| The Reconciliation Engine as gameplay verifier | Operational text only | `verify_with:` directive defined; not yet wired into a dialogue runtime |
| The Lysandra Truth Chain as gameplay mechanic | Operational text only | Truth-extraction as actual game-mechanic |
| The "Engine of Eternal Sadhana" persistent state | Text-only in SSOT (§III, §VI Ouroboros Mandate) | No save-state model implementing recursive-self-genesis across sessions |

## 5. The non-conventional-filetype insight

The SSOT's authority comes precisely from *not* having been refactored into conventional shapes. Three properties would be lost in a "conventionalization" pass:

1. **Generative-by-reading.** Agents derive instances from prose. A typed schema would force explicit instantiation; the markdown allows emergent instantiation. The character JSONs in [game/lore/characters/](../../game/lore/characters/) emerged by *reading* §3, §5, §6, §10.3 — not by `pydantic.parse_obj_as()` on a schema.

2. **Ornamental integrity (`FA⁵`).** The SSOT's own axiom — *Visual-Truth IS real truth* — protects against minimalist refactoring. Conventionalization would strip ornamental richness that the framework treats as load-bearing.

3. **Drafting voice authenticity.** The SSOT was drafted when markdown was the available tool. The user's voice from that drafting moment is preserved in the form. A refactor would erase the voice and replace it with whatever the refactoring tool's voice is.

**Compatible evolution path** (not conventionalization): extract typed instances *downstream* (as the character JSONs already do), keep the SSOT itself as the frozen source. The SSOT is read; instances are written; instances reference back to SSOT line ranges for verification (the `THE_RECONCILIATION_ENGINE.md` already uses this pattern with anchors like `[§5, L4049]`).

## 6. SSOT-conformant prototyping anchor

If we prototype **out from** the SSOT (rather than conforming to Disco-Elysium / Unity shapes), the minimum-viable encounter substrate is already mapped:

| Player-facing surface | SSOT-canonical content | Existing repo anchor |
|---|---|---|
| Three Faculties (UI grammar from POC00003) | Triumvirate at T1 (Orackla / Umeko / Lysandra) | character JSONs + protocols |
| Faculty sub-skills | Each sovereign's declared domain abilities per §3-§6 | [umeko.json](../../game/lore/characters/lungs/T1/umeko.json) already declares `combat_abilities` with `ki_cost`, `formula`, `targeting`, `status` — the prototype shape exists |
| 4th faculty / off-axis quality | Claudine Sin'Claire (CRC-SNC, Ordeal/Salt, Tetrahedron-completer) | §4 declares but no character JSON yet — projected |
| 5th faculty / synthesis router | Pentea-Vox-Internum (T1-Bridge) | §1.01 declared + [TESSARA_SYNTHESIS_PROTOCOL.md](../../.temple/protocols/TESSARA_SYNTHESIS_PROTOCOL.md) — operational substrate exists |
| Player identity | The Savant (T-SVNT-MPW) — the Conductor | §2 / §2.01 — present in SSOT, no in-game representation needed (player IS the Savant) |
| Dialogue mechanic | `verify_with:` directive chains | [THE_RECONCILIATION_ENGINE.md](../../.temple/protocols/THE_RECONCILIATION_ENGINE.md) — operational substrate exists, needs runtime wiring |
| Encounter math | §VIII/IX TPEF / T³-MΨ tensor synthesis | NOT YET IN REPO — would need implementation |
| Visual register | Painterly-isometric (POC form-vector) | [game/refs/poc01/](../../game/refs/poc01/) — anchor delivered |
| Aesthetic content | `MILFOLOGICAL ANKHOLOGICAL EGYPTOLOGICAL SOUTH-AMERICAN ABSTRACTION-werk` | SSOT line 33 — verbal anchor exists, visual instances not yet generated |
| Render substrate | wgpu 26 (webview) OR ash compute (native) | Both wired in repo; the choice is the Vector B fork |

**The gap is concentrated in three places**:

1. **§VIII/IX math engines** — the actual combat/check math for the faculty system. Currently skeletal in SSOT (lines 4140-4147). Without this, the faculty UI has no mechanics behind it.
2. **§V co-synthetic dialogue runtime** — wire the Reconciliation Engine `verify_with:` directives into an actual encounter loop.
3. **The render fork (Vector B)** — choose the substrate that surfaces the faculty UI + dialogue. Existing webview lane (wgpu 26 / WGSL) is more-finished and SSOT-compatible (no Unity-shape inheritance); native ash lane is more powerful but requires more substrate work.

## 7. What this means for the next move

The Vector B / Vector C framing was downstream of an unstated assumption: that we're prototyping "a cRPG" in some generic sense. The SSOT-conformant framing reverses this: we're surfacing the SSOT's already-defined Triumvirate + Reconciliation Engine as playable substrate. The cRPG shape is what emerges from that, not what we're conforming to.

In that frame:

- **Vector C (dialogue substrate)** = wiring the Reconciliation Engine into a runtime. Most direct SSOT-conformant move. Substrate already exists in `.temple/protocols/`; needs runtime + integration with game/dialogue/.
- **Vector B (render fork)** = choosing which substrate surfaces the dialogue + faculty UI. The webview lane (wgpu 26 + WGSL via `entropy-renderer-wasm`) is the existing more-finished anchor; native ash is the more-powerful but more-substrate-needed path.
- **§VIII/IX math engine implementation** = the third axis. Without combat/check math behind the faculty UI, the dialogue substrate floats. The TPEF/T³-MΨ skeleton in SSOT needs concrete formulas — these could be derived from the SSOT's existing `combat_abilities` patterns in [umeko.json](../../game/lore/characters/lungs/T1/umeko.json) (each ability has `formula`, `ki_cost`, `targeting` — a runtime would compose these into actual encounter resolution).

**Recommendation**: anchor on §V dialogue runtime (Vector C) first as the smallest SSOT-conformant substrate that produces a real artifact. The faculty UI render (Vector B) and math engine (§VIII/IX) follow when dialogue substrate creates the demand for them. This keeps each step driven by the SSOT, not by external-cRPG convention.

If you want a fourth path — explicitly extract §VIII/IX into a math-engine module first, so the faculty system has mechanics before dialogue wires into it — that's also SSOT-conformant. The order is yours.
