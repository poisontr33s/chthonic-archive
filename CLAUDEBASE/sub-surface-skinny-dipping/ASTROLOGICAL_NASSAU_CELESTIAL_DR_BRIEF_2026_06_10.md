# Deep Research Brief — Astrological Nassau: Accessible MCP Servers & Open Sources for the Celestial Dimension

> **Purpose:** Self-contained context packet for Gemini Deep Research.
> **Author:** Chthonic Archive — Claude Fable 5, for the human creator.
> **Date:** (ANNO).
> **Classification:** Research input — read fully before generating queries.
> **Scope:** BOTH, equally — (A) accessible **MCP servers** and (B) accessible **open sources** — for *computing* and *studying* the astronomy + astrology (50/50) celestial dimension of the Astrological Nassau renderer.

---

## 0. WHY THIS DOCUMENT EXISTS

Gemini Deep Research has no native context on:

1. The renderer **Astrological Nassau** and what its celestial dimension is.
2. That the dimension is **astronomy + astrology, 50/50 = the Andean + Egyptological "Ankhology"** — and what that demands of our sourcing.
3. The hard **epistemic reality** of the field (precise contemporary sources are largely lost; the corpus is reconstructed from literary mentions) and the project's non-negotiable rule: **accuracy, not fiction.**
4. What compute + study infrastructure **already exists**, so research targets *additions*, not greenfield.

The deliverable we need is a **sourced, evaluated map of BOTH the MCP servers AND the open sources we can actually access and use** — split cleanly into what is **precisely computable** versus what is **historically attested / reconstructed**.

---

## 1. PROJECT CONTEXT (concise — enough to target research)

### 1.1 The renderer
A from-scratch Rust/Vulkan real-time renderer of Nassau and the Bahama Banks. The sky over the real place is **not a backdrop** — it is a structured celestial field, and computing/structuring it correctly is *half the project's depth*. Goal is a North-Star engine, & open-ended study substrate, for the celestial dimension of the project — both the **precise, computable astronomy** and the **historical, attested astrology**. The research target is: **what MCP servers and open sources can we actually use to build this?**

### 1.2 The 50/50 — astronomy + astrology = Andean + Egyptological
The celestial dimension is held in equal halves:
- **Astronomy** = the positional-accuracy layer — exact, computable to arc-seconds (sun, moon, planets, fixed stars, houses, the celestial-sphere geometry).
- **Astrology** = the older, fuller field that *contains* astronomy — the structure and meaning, and historically the home of the advanced mathematics (Babylonian ephemerides; Ptolemy's *Almagest* **and** *Tetrabiblos* from one hand; the ascendant and houses as spherical-trig geometry).

This maps onto the project's existing **Ankhology** abstraction: a 50/50 fusion of **Andean** (Inca *ceque* system, solstice alignments, dark-cloud constellations) and **Egyptological** (decans, Sothic cycle, star-clocks) heritage — two lineages reading one sky, each in its own mathematics and its own meaning. **Both halves must be researched with equal weight.**

### 1.3 The epistemic reality (this shapes the entire sourcing problem)
Precise contemporary primary sources are largely **lost**; the field is reconstructed from literary mentions and indirect materials. Concretely:
- **Nechepso–Petosiris** — the foundational Hellenistic astrological text — survives only as *fragments and later citations*.
- **Dorotheus of Sidon** survives mainly through an *Arabic translation of a Pahlavi version*.
- **Manilius' *Astronomica*** is a Latin *poem*; Aratus' *Phaenomena* likewise.
- The **Babylonian astronomical diaries** (the longest continuous observational record in history) and the **Andean *ceque* system** reach us reconstructed — the latter from a people with *no phonetic writing*, via Spanish chroniclers (Cobo, Polo de Ondegardo, Guaman Poma) plus archaeoastronomy.

Therefore the project classifies **every** source as either **computable (exact)** or **attested (reconstructed — must be cited, never fabricated)**. This split is the single most important output of the research.

### 1.4 What already exists (so research targets additions, not greenfield)
- A Rust solar-position module (NOAA/Meeus algorithms), verified against JPL Horizons — the seed of the astronomy layer.
- A local corpus + embeddings + semantic-search stack — i.e. the **"study and grow learning" substrate already exists**; what it lacks is *content* pointed at this domain.
- This Gemini DR lane itself.

Research should therefore prioritise: **(a) authoritative compute engines we can wrap, and (b) machine-readable open corpora we can index** — plus any MCP server that delivers either at primary-source grade.

---

## 2. WHAT TO RESEARCH — BOTH clusters, equal priority

### CLUSTER A — MCP SERVERS (accessible)

**Q1 · Astronomy / ephemeris MCP servers.** Any MCP server wrapping JPL Horizons, Skyfield, Astropy, NASA SPICE, Stellarium, or equivalent. For each: what it computes, transport (stdio / HTTP / SSE), auth model, license, self-hostable?, precision, maintenance/health.

**Q2 · Astrology-computation MCP servers.** Any MCP wrapping Swiss Ephemeris / `pyswisseph`, or computing houses / aspects / natal charts / mundane positions. Existence, quality, license, and crucially whether the underlying ephemeris is **authoritative (JPL-DE-derived)** or merely approximate.

**Q3 · Historical-text / classics / cuneiform / digital-humanities MCP servers.** Any MCP exposing primary-source corpora (Perseus/Scaife, CDLI, papyri.info, TLG, etc.), *or* a general document/RAG MCP suitable for hosting **our own** curated corpus.

**Q4 · For every MCP returned:** is it **primary-source-grade or a convenience wrapper**? Self-hostable (we prefer self-hosting over vendor pipes)? License? Honest maintenance status (mark dead/abandoned servers as such)?

### CLUSTER B — OPEN SOURCES (accessible)

**Q5 · Compute libraries.** Swiss Ephemeris / `pyswisseph` (**flag the AGPL-vs-commercial licensing precisely**), Skyfield, Astropy, ERFA / IAU SOFA, SpiceyPy / SPICE. For each: precision, license, language bindings (especially **Rust**, or C-FFI reachable from Rust), data dependencies (which JPL DE kernels), and suitability as the project's compute core.

**Q6 · Ephemeris data + APIs.** JPL Horizons (the web API and the DE431/DE440/DE441 kernels), IMCCE Miriade, USNO. Access, rate limits, bulk-download, license.

**Q7 · Primary-text open corpora.** Digitised critical editions of the surviving astronomical/astrological corpus: Ptolemy (*Almagest*, *Tetrabiblos*), Vettius Valens (*Anthologies*), Dorotheus, Manilius, Firmicus Maternus, Hephaestio; the Babylonian texts (MUL.APIN, the Astronomical Diaries, *Enūma Anu Enlil*). **Where** each is open-access and **machine-readable** (Perseus/Scaife, the Greek/Latin digital libraries, CDLI/ETCSL for cuneiform), and which are **CC-licensed / bulk-downloadable** for indexing. For the **fragmentary** ones (Nechepso–Petosiris), where the fragment collections live.

**Q8 · Andean + Egyptological archaeoastronomy (equal weight).**
- *Andean:* the *ceque* system (Zuidema, Brian Bauer), the dark-cloud constellations, solstice / Pleiades alignments; the Spanish chronicles digitised (Cobo, Guaman Poma, Polo de Ondegardo). Open-access scholarship + any datasets.
- *Egyptological:* the decans, the Dendera zodiac, the Ramesside star-clocks, the Sothic cycle; the relevant Egyptological editions/corpora. Open-access scholarship + any datasets.

**Q9 · Digital-humanities databases / datasets.** CDLI (cuneiform), papyri.info, Pleiades (ancient-places gazetteer), any archaeoastronomy alignment databases, any structured zodiac/decan datasets. Access, license, machine-readability.

### CLUSTER C — INTEGRATION & FIT (secondary)

**Q10 · Indexability.** Of everything above, which expose **machine-readable / bulk-downloadable** corpora we could index into a local corpus + embeddings store? Licensing for that reuse.

**Q11 · The computable-vs-attested classification.** For every source and server, classify it **computable (exact)** or **attested (reconstruction — cite, do not derive)**. *This boundary is the core deliverable.*

**Q12 · Recommended minimal stack.** The smallest set — roughly one compute engine + one or two open corpora + optionally one MCP — that gives us a **precise celestial-compute layer** AND a **credible study substrate** for the attested layer, with licensing clean and self-hosting preferred.

---

## 3. COMPARISON MATRICES REQUESTED

**Matrix A — MCP servers**

| Server | Domain | Transport | Auth | License | Self-hostable | Data grade (primary / convenience) | Maintained? | Fit |
|---|---|---|---|---|---|---|---|---|

**Matrix B — Open sources**

| Source | Type (lib / API / corpus / dataset) | Domain (astronomy / astrology-math / Andean / Egyptian / general) | Access (open / CC / paywall) | Machine-readable | License | Computable or Attested | Fit |
|---|---|---|---|---|---|---|---|

---

## 4. CONSTRAINTS FOR OUTPUT

1. **Cite every claim** — link to documentation, repository, API page, or scholarly edition.
2. **Distinguish computable vs attested explicitly** for every item. Accuracy-not-fiction governs the cosmos; this classification is non-negotiable.
3. **Flag licensing precisely** — especially Swiss Ephemeris (AGPL/commercial) and any copyleft that would affect a Rust/Vulkan codebase, and corpus-reuse licensing (CC-BY vs all-rights-reserved).
4. **Provenance-skepticism** — evaluate *authority*, not popularity. Mark vendor-marketing and thin wrappers as such. Prefer self-hosted/authoritative over hosted convenience.
5. **Currency** — software must be 2025–2026 current (mark dead repos); primary-source scholarly editions are timeless — judge them by scholarly authority, not date.
6. **Actionable** — each finding ends with "what we would do."
7. **Equal weight to Andean and Egyptological** — the 50/50 is load-bearing; do not let the better-documented half crowd out the other.

---

## 5. EXPECTED DELIVERABLES

1. **Matrix A** (MCP servers) filled with verified data.
2. **Matrix B** (open sources) filled with verified data.
3. The **computable-vs-attested map** across all items.
4. A **licensing register** (especially anything copyleft / reuse-restricted).
5. The **recommended minimal stack** (compute engine + corpora + optional MCP), with rationale.
6. An explicit list of the **fragmentary / lost sources** and **where their fragments and citations are collected**, so the attested layer can be studied honestly.
7. A short **"what we'd do first"** action plan.

---

*Offered to Deep Research: complete context in exchange for actionable intelligence. The 50/50 is the gate — astronomy and astrology, Andean and Egyptological, computable and attested, in equal hands.*
