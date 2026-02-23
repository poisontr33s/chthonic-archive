# ╔════════════════════════════════════════════════════════════════════════════
# ║ Artifact Name: RESEARCH_REGISTRY.md
# ║ Wedjat-Quipu Spectrum: 🏛️ Infrastructure — 📦 Registry
# ║ Temple-Ayllu Zone: 🏛️ THE HYPOSTYLE
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ claude-codex-gemini/ (all subdirectories)
# ║   └─◄ docs/design/SFS_WPTG_ITERATION_PLAN.md
# ║   └─◄ WET_PAPER_TO_GOLD_METHODOLOGY.md
# ╚════════════════════════════════════════════════════════════════════════════

<!--
@SID:           DOC_RESEARCH_REGISTRY_V1
@Shabti:        Registry / Manifest
@Purpose:       Structured index of all research documents, session logs, and
                engineering artifacts in claude-codex-gemini/. Designed for
                agent session continuity — read this FIRST to navigate the
                research corpus. Wet-Paper-to-Gold: no files destroyed, only
                indexed and classified.
-->

# Research Registry — claude-codex-gemini/

> **Purpose**: Navigable index of the entire research corpus. Classifies every
> file by domain, origin, date, size, and actionability. Flags duplication.
> Agents read this to avoid re-discovering the same material session after session.

**Total**: ~93 files | ~2.9 MB | 6 subdirectories + root

**Generated**: 2026-02-28 | **Method**: Full inventory + first-line classification

---

## 1. Root-Level Research Dumps

Deep research outputs, mostly from Gemini sessions. Each is a standalone
technical analysis report.

| # | File | Size | Domain | Origin | Actionability |
|---|------|------|--------|--------|---------------|
| 1 | `Embedding_model_landscape_DRESRCH_DUMP.md` | 31 KB | Embedding models (MiniLM, Nomic, Jina, Qwen) | Gemini | Reference — informs RAG stack decisions |
| 2 | `general_researchDUMP003.md` | 31 KB | LLM optimization (MoE, quantization, structured output) | Gemini | Reference — GPT-OSS 20B + Qwen 2.5 14B |
| 3 | `hotswapresearch.md` | 43 KB | Multi-model hot-swapping, chat template orchestration | Gemini | Reference — inference infrastructure |
| 4 | `research-dump002.md` | 40 KB | Local batch classification on Win11 | Gemini | Reference — polyglot pipeline design |
| 5 | `research_dump003.md` | 40 KB | "Wet Paper to Gold" Upcycler Daemon architecture | Gemini | **Active** — WPTG methodology source |
| 6 | `researchhags.md` | 31 KB | HAGS (HW Accelerated GPU Scheduling) on Win11/RTX 40 | Gemini | Reference — GPU scheduling for inference |
| 7 | `research_GPTOSS_HF.md` | 36 KB | GPT-OSS 20B structured JSON extraction | Gemini | Reference — reasoning model engineering |
| 8 | `sessionANDresearch.md` | 200 KB | Mixed session dump + research (Gemini conversation) | Gemini | **Triage** — large, unstructured, mixed content |
| 9 | `task_scheduler_researchDUMP.md` | 47 KB | GPU workloads, session isolation, power management | Gemini | Reference — unattended GPU compute |
| 10 | `vsTRAJECTORYDUMP.md` | 28 KB | ExLlamaV2/V3 vs llama.cpp trajectory analysis | Gemini | Reference — local inference stack |

### Root-Level Strategy & Handoff Docs

| # | File | Size | Domain | Origin | Actionability |
|---|------|------|--------|--------|---------------|
| 11 | `TRIAD_DOC_CONSOLIDATION_STRATEGY.md` | 5 KB | Triadic documentation consolidation plan | Claude | **Active** — strategy for this registry |
| 12 | `triadic-session-shared-0001.md` | 6 KB | Session continuity snapshot (cross-agent index) | Claude | Reference — historical handoff |
| 13 | `triadic-session-shared-0002.md` | 4 KB | Session continuity snapshot (GitHub MCP/PAT auth) | Claude | Reference — historical handoff |

---

## 2. ANKH_EGYPTOLOGY_SOUTH_AMERICAN/

Deep research on the aesthetic/cultural framework. Source material for the
50/50 Egyptological × Andean design vocabulary.

| # | File | Size | Domain | Actionability |
|---|------|------|--------|---------------|
| 1 | `ANKH_Ancient_Matriarcha_Systems_Researchl.md` | 41 KB | Ancient matriarchal systems analysis | Reference — lore corpus |
| 2 | `ANKH_ARCHETYPE_ANCIENT_RITUALS_NSFW.md` | 33 KB | Archetypal ritual systems | Reference — lore corpus |
| 3 | `ANKH_MILF_PROTOCOL_HIGH_INTENSITY_ARCHETYPAL_SYSTEMS_ARCHITECTURE.md` | 9 KB | MILF protocol architecture spec | **Active** — theme hierarchy source |
| 4 | `ANKH_UNIFYING_REPOSITORY_METADATA_STANDARDS.md` | 54 KB | KCP source: metadata unification research | **Active** — KCP protocol source |
| 5 | `VS_CODE_INSIDERS_MAXIMALIST_MILF_THE_DECORATOR_CHALLANGE.md` | 54 KB | Decorator challenge spec | **Active** — theme challenge brief |
| 6 | `BODY_SYSTEMS/ABSTRACTING_GESTALT_WHR_MAX_ARCHITECTURE.md` | 39 KB | Gestalt architecture research | Reference — lore corpus |

---

## 3. context_packets/

Small structured context packets for session bootstrapping.

| # | File | Size | Purpose |
|---|------|------|---------|
| 1 | `packet_001_init.md` | 2 KB | Session initialization packet |
| 2 | `packet_003_src_scan_meta.md` | 13 KB | Source code scan metadata |
| 3 | `packet_004_infrastructure_spec.md` | 2 KB | Infrastructure specification |

---

## 4. engineering_agentic_deep_research_candidates/

Well-organized engineering research. The `gemini-deep-research-2026-02/`
subfolder is particularly structured with numbered sections.

### Top-Level Candidates

| # | File | Size | Domain | Date | Actionability |
|---|------|------|--------|------|---------------|
| 1 | `codex52_medium_reasoning_candidate_persona.md` | 30 KB | Codex 5.2 persona research | — | Reference |
| 2 | `GEMINI_RESEARCH_DIGEST_2026_02_12.md` | 9 KB | Gemini research digest | 2026-02-12 | Reference |
| 3 | `LOCAL_LLM_STACK_RESEARCH_BRIEF_2026_02_11.md` | 6 KB | Local LLM stack brief | 2026-02-11 | Reference |
| 4 | `UNIFIED_METADATA_ABSTRACTION_RESEARCH_BRIEF_2026_02_27.md` | 22 KB | KCP metadata abstraction (Gemini output) | 2026-02-27 | **Active** — KCP source |

### gemini-deep-research-2026-02/ (Numbered Series)

| # | File | Size | Topic |
|---|------|------|-------|
| 00 | `00-unified-verdicts.md` | 7 KB | Unified research verdicts |
| 01 | `01-local-llm-inference-stack.md` | 4 KB | Local LLM inference stack |
| 02 | `02-rustified-polyglot-daemon.md` | 4 KB | Rustification of polyglot daemon |
| 03 | `03-api-gateways-and-vector-dbs.md` | 4 KB | API gateways + vector databases |
| 04 | `04-ruby-4-and-oxidized-toolchains.md` | 4 KB | Ruby 4 + oxidized toolchains |
| 05 | `05-batch-classification-infrastructure.md` | 40 KB | Batch classification infrastructure |
| 06 | `06-field-tested-corrections-and-frontier.md` | 15 KB | Field-tested corrections |
| 07 | `07-phase-learning-research-questions.md` | 7 KB | Phase learning research questions |
| 08 | `08-phase-learning-verdicts.md` | 7 KB | Phase learning verdicts |
| 09 | `09-session-trail-and-learnings.md` | 9 KB | Session trail + learnings |
| 10 | `10-anno-live-unanswered-questions-v2.md` | 5 KB | Live unanswered questions (v2) |
| — | `ANNO_RUSTIFICATION_ENDO_DOT_LIFE.md` | 37 KB | Rustification deep dive |
| — | `hf.html` | 165 KB | HuggingFace HTML snapshot (raw scrape) |

---

## 5. session_resumption_pickup/

Session state snapshots and runtime artifacts. **Heavy duplication** — timestamped
copies with `_LATEST` duplicates.

### Duplication Analysis

| Series | Timestamps | Files Per | Total Files | Dedup Savings |
|--------|-----------|-----------|-------------|---------------|
| `SESSION_RESUMPTION_HIGH_COVERAGE` | 8 | json + md | 17 (8×2 + LATEST) | ~86 KB (7 redundant copies) |
| `LOCAL_UNCENSORED_BENCHMARK` | 4 | json + md | 9 (4×2 + LATEST) | ~33 KB (3 redundant copies) |
| `UNCENSORED_LANE_STEWARD` | 5 | json + md | 11 (5×2 + LATEST) | ~75 KB (4 redundant copies) |
| `UNCENSORED_LANE_RUNTIME` | 1 | env + json + md | 6 (1×3 + LATEST×3) | ~4 KB (1 redundant copy) |

### Unique / Non-Duplicate Files

| # | File | Size | Purpose |
|---|------|------|---------|
| 1 | `GEMINI_DEEP_RESEARCH_TRIAGE_2026_02_19.md` | 2 KB | Research triage snapshot |
| 2 | `GEMINI_UNANSWERED_QUESTIONS_*.md` | 2 KB | Unanswered questions log |
| 3 | `SESSION_CONTINUATION_DAEMON_GENRE_LATEST.md` | 3 KB | Daemon genre continuation |
| 4 | `session_resumption_pickup_codex.md` | 401 KB | **Massive** Codex session dump |
| 5 | `session_resumption_pickup_codex.md_pretty.md` | 10 KB | Prettified version |
| 6 | `session_resumption_pickup_codex.md_resume.md` | 2 KB | Resume summary |
| 7 | `session_resumption_pickup_codex.md_structured.json` | 528 KB | Structured JSON extraction |
| 8 | `session_resumption_pickup_codex.md_structured.txt` | 5 KB | Structured text extraction |

### Dedup Recommendation

The `_LATEST` files are exact copies of the most recent timestamp. The timestamped
copies form a delta series (mostly near-identical). **Candidate for consolidation**:
keep only the latest timestamp + `_LATEST`, archive the rest.

> **Wet-Paper-to-Gold**: No files should be deleted. If consolidating, move old
> timestamps to a `session_resumption_pickup/archive/` subfolder.

---

## 6. triadic-session-context/

Session infrastructure, structured indices, and historical problem resolutions.

| # | File | Size | Domain | Actionability |
|---|------|------|--------|---------------|
| 1 | `Accurate_PEP_Standards_Win11_Uv_Python.md` | 24 KB | PEP standards on Win11 + uv | Reference |
| 2 | `BUN_SEGFAULT_2026_02_01.md` | 2 KB | Bun segfault resolution | Reference |
| 3 | `Claude_Code_Session_Dump_0001` | 211 KB | Raw Claude Code session dump | Reference |
| 4 | `claude-session-help.md` | 86 KB | Claude session help/troubleshooting | Reference |
| 5 | `gemini-cli-session-fix-too-large.md` | 66 KB | Gemini CLI session fix | Reference |
| 6 | `OpenAI_Codex_Win11_Keyring_Auth_Resolution.md` | 7 KB | Codex keyring auth fix | Reference |
| 7 | `PHASE4_LINK_VALIDATION_2026_02_01.filtered.json` | 67 KB | Link validation (filtered) | Reference |
| 8 | `PHASE4_LINK_VALIDATION_2026_02_01.filtered.summary.json` | 2 KB | Link validation summary | Reference |
| 9 | `PHASE4_LINK_VALIDATION_2026_02_01.json` | 209 KB | Link validation (full) | Reference |
| 10 | `PHASE4_LINK_VALIDATION_2026_02_01.triad_only.json` | 5 KB | Link validation (triad only) | Reference |
| 11 | `Python_Metabolic_Standard_v3_Transition.md` | 4 KB | PMS-v3 transition notes | Reference |
| 12 | `Session_20260131_Codex_Onboarding_Summary.md` | 3 KB | Codex onboarding summary | Reference |
| 13 | `SESSION_CACHE_STRUCTURED.md` | 7 KB | GHAR-MHS Tier 1 cache | **Active** — session continuity |
| 14 | `SESSION_PROTOCOL.md` | 9 KB | Session protocol definition | **Active** — session continuity |
| 15 | `SSOT_NAVIGATION_INDEX.md` | 8 KB | SSOT navigation pointers | **Active** — session continuity |
| 16 | `SSOT_STRUCTURAL_INDEX.json` | 24 KB | SSOT structural index (JSON) | **Active** — session continuity |
| 17 | `SSOTI_FIED_SESSION_LOG.md` | 725 KB | **Massive** SSOT-ified session log | Reference — historical |
| 18 | `STRATEGIC_PLAN.md` | 5 KB | Strategic plan | **Active** — roadmap |
| 19 | `Zone_1_REDUX_implementation_ripe_for_SSOT_canon.md` | 47 KB | SSOT canon candidates | **Active** — upcycle candidates |

---

## 7. TRIUVIRATE_ARCHITECTING_THREADS/

| # | File | Size | Domain | Actionability |
|---|------|------|--------|---------------|
| 1 | `CHTHONIC_NEURAL_BUS_ARCHITECTURE.md` | 5 KB | Neural bus architecture spec | Reference |

---

## Cross-Reference to Active Work

| Active Work Item | Relevant Files |
|------------------|----------------|
| **KCP Protocol** | `ANKH_UNIFYING_REPOSITORY_METADATA_STANDARDS.md`, `UNIFIED_METADATA_ABSTRACTION_RESEARCH_BRIEF_2026_02_27.md` |
| **WPTG Pipeline** | `research_dump003.md` (Upcycler Daemon arch), `WET_PAPER_TO_GOLD_METHODOLOGY.md` (root) |
| **SFS Theme** | `VS_CODE_INSIDERS_MAXIMALIST_MILF_THE_DECORATOR_CHALLANGE.md`, `ANKH_MILF_PROTOCOL_*.md` |
| **Local LLM Stack** | `01-local-llm-inference-stack.md`, `vsTRAJECTORYDUMP.md`, `hotswapresearch.md`, `05-batch-classification-infrastructure.md` |
| **Session Continuity** | `SESSION_PROTOCOL.md`, `SESSION_CACHE_STRUCTURED.md`, `SSOT_NAVIGATION_INDEX.md` |
| **Daemon/Forge** | `CHTHONIC_NEURAL_BUS_ARCHITECTURE.md`, `task_scheduler_researchDUMP.md` |

---

## Health Summary

| Metric | Value | Status |
|--------|-------|--------|
| Total files | ~93 | — |
| Total size | ~2.9 MB | ⚠️ Large |
| Well-structured dirs | `engineering_agentic_deep_research_candidates/`, `context_packets/` | ✅ |
| High-entropy dirs | `session_resumption_pickup/` (heavy duplication) | ⚠️ Consolidation candidate |
| Largest files | `SSOTI_FIED_SESSION_LOG.md` (725 KB), `session_resumption_pickup_codex.md_structured.json` (528 KB), `session_resumption_pickup_codex.md` (401 KB) | ⚠️ Archive candidates |
| Active cross-refs | 6 active work streams mapped | ✅ |
| Naming consistency | Root-level chaotic, subdirs structured | ⚠️ |
