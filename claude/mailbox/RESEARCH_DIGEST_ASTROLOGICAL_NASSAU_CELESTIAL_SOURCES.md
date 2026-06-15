---
type: research-digest
created: 2026-06-15T22:47:11Z
source: CLAUDEBASE/G-DR-3-1-Pro-Celestial-Computing-Sources-Research.md
topic: Astrological-Nassau-Celestial-Sources
---

# Research Digest: Astrological-Nassau-Celestial-Sources

- Classification: **research-results**
- Source: `CLAUDEBASE/G-DR-3-1-Pro-Celestial-Computing-Sources-Research.md`

## Findings
- 40. isawnyu/pleiades.datasets: Platform-independent versions of Pleiades gazetteer data - GitHub, brukt juni 15, 2026, [https://github.com/isawnyu/pleiades.datasets](https://github.com/isawnyu/pleiades.datasets)
- ### Matrix A: MCP Servers Evaluation | Server Repository | Domain | Transport | Auth / License | Self-Hostable | Data Grade | Fit / Recommendation | | :---- | :---- | :---- | :---- | :---- | :---- | :---- | | Spirit-River/openephemeris-MCP | Astronomy / Advanced Astrological Math | stdio, HTTP (SSE) | API Key / MIT | Yes | Primary (JPL DE440/441 backend) 13 | High.
- It provides high-precision planetary and lunar positions, calendar-to-Julian date conversions, and solar system dynamics based on the ![][image1] and ICRF 3.0 reference frames.1 It is designed explicitly for scientific correctness, orbital mechanics, and astronomical trajectory planning, acting as a legally clean, highly optimized compute core for positional astronomy.
- ### Matrix B: Open Sources Evaluation | Source / Project | Type | Domain | Access / License | Machine-Readable | Computable / Attested | Recommendation | | :---- | :---- | :---- | :---- | :---- | :---- | :---- | | rust-jpl crate | Compute Library | Astronomy | Open / Dual MIT/Apache | Yes (Rust code) | Computable 1 | High.
- 325-394).6 Scanned PDFs of this collection are currently open-access.7 A secondary collection of fragments, particularly concerning the numerological divination technique known as the "Petosiris Circle," has been translated into English and is available online.66 Stephan Heilen provided modern updates and metrical analysis of the fragments in 2011.65 2.
- * Swiss Ephemeris (swisseph): This C library is dual-licensed under the GNU Affero General Public License version 3 (AGPL-3.0) and a commercial license.17 The AGPL is a highly viral, copyleft license specifically designed to close the "Application Service Provider loophole" for network services.
- Recommended Minimal Stack and Action Plan To fulfill the rigorous requirements of the Astrological Nassau renderer—achieving sub-arcsecond astronomical precision while maintaining a deep, machine-readable repository of the 50/50 Andean/Egyptological heritage—the following minimal architecture stack is recommended: * 1.
- isawnyu/pleiades.datasets: Platform-independent versions of Pleiades gazetteer data - GitHub, brukt juni 15, 2026, [https://github.com/isawnyu/pleiades.datasets](https://github.com/isawnyu/pleiades.datasets) * 46.
- Source links observed:
  - https://github.com/CHINMAYVIVEK/rust-jpl
  - https://pypi.org/project/libephemeris/0.7.0/
  - https://en.wikipedia.org/wiki/Decan
  - https://www.wilfredhazelwood.com/nechepso-and-petosiris-the-lost-founders-of-western-astrology
  - https://ehrafarchaeology.yale.edu/document?id=se80-014
  - https://referenceworks.brill.com/display/entries/NPOE/e818880.xml
  - http://ancientworldonline.blogspot.com/2010/12/open-access-hellenistic-astrological.html
  - https://arxiv.org/pdf/physics/0408037
  - https://www.scribd.com/document/602356228/Bauer-2016-The-ceque-system
  - https://github.com/punkpeye/awesome-mcp-servers

## Decisions
| Decision | Options | Recommendation |
|---|---|---|
| ### Matrix B: Open Sources Evaluation \| Source / Project \| Type \| Domain \| Access / License \| Machine-Readable \| Computable / Attested \| Recommendation \| \| :---- \| :---- \| :---- \| :---- \| :---- \| :---- \| :---- \| \| rust-jpl crate \| Compute Library \| Astronomy \| Open / Dual MIT/Apache \| Yes (Rust code) \| Computable 1 \| High. | Yes / No | Recommendation \| \| :---- \| :---- \| :---- \| :---- \| :---- \| :---- \| :---- \| \| rust-jpl crate \| Compute Library \| Astronomy \| Open / Dual MIT/Apache \| Yes (Rust code) \| Computable 1 \| High. |
| Recommended Minimal Stack and Action Plan To fulfill the rigorous requirements of the Astrological Nassau renderer—achieving sub-arcsecond astronomical precision while maintaining a deep, machine-readable repository of the 50/50 Andean/Egyptological heritage—the following minimal architecture stack is recommended: * 1. | Yes / No | Recommended Minimal Stack and Action Plan To fulfill the rigorous requirements of the Astrological Nassau renderer—achieving sub-arcsecond astronomical precision while maintaining a deep, machine-readable repository of the 50/50 Andean/Egyptological heritage—the following minimal architecture stack is recommended: * 1. |

## Actionable Items
- [ ] [gemini] # Deep Research Brief: Astrological Nassau and the Computable Celestial Dimension --- ## **0. (manual-review)
- [ ] [manual] | | shinpr/mcp-local-rag | Document Retrieval (RAG) | stdio, CLI | None / MIT | Yes | N/A (Ingests user data) 22 | High. (manual-review)
- [ ] [manual] This 50/50 split forms the "Ankhology," requiring equivalent research weight and architectural support. (manual-review)

## Dependencies
| Dependency | Install Vector | Evidence |
|---|---|---|
| None detected | manual | n/a |

## Contradictions
- None detected.

---

## Verification Addendum (Claude, 2026-06-10) — load-bearing claims checked against source

The Pro lane is well-cited, and the **computable-vs-attested boundary (its §5) is the keystone deliverable — sound and usable as-is.** Two stack-critical, provenance-risky claims were checked against source (the open corpora — CDLI, Papyri.info, Pleiades, Perseus, McMaster AEA — are established digital-humanities infrastructure, accepted as described):

1. **`rust-jpl` (CHINMAYVIVEK/rust-jpl) — REAL but OVERSOLD.** Confirmed: MIT-licensed; reads NASA JPL **DE441** SPK kernels natively in Rust; outputs 11-body 3D positions (ICRF). BUT it is **v0.0.1-alpha, 36 commits, 12★ — a prototype "with professional structure," explicitly pre-production** — and the README carries **no precision/accuracy spec**. The DR called it a "highly optimized compute core"; in truth it is a **seed / reference implementation.** Verdict: *directionally correct* (pure-Rust, permissive, DE-backed → sidesteps AGPL) but treat it as a **floor to build up from or crib**, never a finished dependency. This fits the project's in-house-from-the-floor ethic.

2. **`openephemeris-MCP` (Spirit-River) — REAL but a VENDOR PIPE; demote.** Confirmed: MIT; JPL **DE440** backend; **79 tools** (DR undercounted at 52); stdio + HTTP + SSE. BUT it **requires an API key with tier-gated usage quotas and a hosted endpoint (mcp.openephemeris.com)** — a SaaS/free-tier model, not the clean local isolate the DR implied. This collides with the brief's own rule (*self-hosting over vendor pipes*). Verdict: **do not adopt as the astrology-compute node**; the astrology math (houses/aspects/ascendant) is pure spherical trig, built in-house.

3. **Swiss Ephemeris AGPL hazard — CONFIRMED** (Astrodienst dual-licenses AGPL-3.0 / commercial ≈700 CHF). The DR's warning holds. The in-house path (own DE-reader + spherical trig) sidesteps it entirely — no copyleft, no fee.

**Reframe given what we already have** (the DR is an external model; it didn't know our repo): we already have `src/render/cosmos.rs` (real solar position, Horizons-verified) and a corpus + embeddings + semantic-search stack. So the *honest* minimal stack is mostly **in-house**, not adopted:
- **Astronomy compute:** extend `cosmos.rs` from sun → planets + moon (crib `rust-jpl`'s DE441 reader as a *reference*, or wrap a DE-kernel reader). In-engine, no AGPL, no network.
- **Astrology math:** houses / ascendant / aspects = spherical trig, in-house (computable; no MCP needed).
- **Attested corpus:** feed the open corpora — **CDLI** (`cdli-gh/data`, git-lfs bulk), **Papyri.info** (`idp.data` EpiDoc), **Pleiades** (CC-BY coords), **Perseus** (Ptolemy/Manilius via CTS), **McMaster AEA** (decans) — into **our existing embeddings stack**, not a new RAG server (`mcp-local-rag` only if ours falls short).
- **Fragmentary sources to ingest first:** Riess 1891 (Nechepso–Petosiris fragments, public domain), Pingree 1976 Teubner (Dorotheus), **Riley's open machine-readable Valens**, CDLI dumps (MUL.APIN / Diaries / *Enūma Anu Enlil*).

**Triangulation status:** this is the **3.1 Pro lane only**. The 3.5 Flash lane (if run) is still pending; the corrections above already adjust two Pro-lane overstatements — fold Flash in when it lands.
