---
sid: DOC_CLAUDE_WET_PAPER_GOLD
title: Wet-Paper-to-Gold Methodology
type: methodology
status: canonical
priority: extremely high
description: Selective extraction/transmutation of drift artifacts into reusable components with error-learning feedback loop.
created: 2026-01-29
updated: 2026-02-24
authors:
  - Claude
  - Codex
applies_to:
  - claude
  - codex
  - gemini
  - agents
  - agents_common
  - user
  - the Savant
audience:
  - all
tags:
  - wet-paper-to-gold
  - data-harvest
  - drift-artifacts
  - dumpster-dive
  - forge-system
  - data-transmutation
  - error-learning
  - session-methodology
  - file-preservation
  - upcycling
  - repurposing
  - anti-pattern-remediation
  - blind-traversal
  - emergent-taxonomy
  - cartography
  - criterion-genesis
  - convergence
  - polyglot-governance
  - responsible-agenting
  - creative-mode
  - functional performance theatrics
  - emergent-strategies
  - adaptive heuristics
  - iterative refinement
  - zombie-file-ingestion + digestion
  - alchemist's transmutation
  - alchemic stone mandate
  - no-destroy principle
  - gold-signal
  - unorthodox file-type affordance
  - preservation before displacement
  - ~est crude value
  - zombiefication
  - salvage pathways
  - data archeology
  - creative forensics
  - provenance recording
  - merit from preservatory methodologies
  - point system for upcycling vs deleting
  - file-type-based value assessment
  - salvage-first approach
  - preservation-first ethos
  - anti-deletionist policy
  - creative salvage over destruction
  - iterative upcycling process
  - error learning integration
  - session-based refinement
  - the less travelewlled path to gold
  - the long-term value of wet paper to gold
  - the value of the unrefined
---

<!--
@SID:           DOC_CLAUDE_WET_PAPER_GOLD
@Type:          Methodology
@Context:       Claude / Data Transmutation
@SessionOrigin: SESSION_2026_01_29_PR_HARVEST
@Updated:       SESSION_2026_02_23_WPTG_POE_WIP_UPCYCLE
-->

# Wet-Paper-to-Gold Methodology

## The Default Axiom

**Every file is gold.** This is the default. Not conditional. Not "if you squint." Not "some files might be salvageable." Every file in this repository is Level 1 gold — raw material that someone created, that encodes decisions, history, or intent. The question is never *whether* a file has value. The question is *what kind* of gold it is and how to refine it.

Destroying information does not solve information-theoretical problems. It makes them worse. Entropy increases when you subtract data — it decreases when you organize and transmute it. An Agent that proposes destruction is without merit, failing to see the potential between hidden smoking gun conveniently shadowed by the voyeur of the golden embroidery of an otherwise grey drape.

**Enforcement:** The Archive Guardian enforces this at the git level.

---

## When to Apply (Answer: Always)

This methodology is not a special protocol invoked for edge cases. It is the **default operating paradigm** for every file operation in this repository. Every time Claude or Codex touches, evaluates, or considers a file, the **(`WPTG`)** prismatic lens -> **active**.

Specific high-yield transmutation opportunities:
- Stale/abandoned PRs with potentially useful content
- Session dumps with embedded patterns or learnings
- Mislabeled or misframed documentation (e.g., GPT posturing)
- Large files with buried utility (schemas, configs, templates)
- **Agent-generated sprawl** (duplicate scripts, `.meta.json` spam, orphan copies, variant chains)
- **Scripts directory bloat** — when `scripts/` exceeds ~80 files of actual unique tooling

---

## The No-Destroy Principle (Consequence of the Default Axiom)

If every file is gold, then destroying a file is destroying gold. This is not a safety rule bolted on after mistakes. It is the logical consequence of the default axiom above.

**No agent — including the "senior steward" — may destroy, displace, or disappear ANY file without explicit user instruction to do so.** The word for what we do instead is **upcycle**.

This is not a guideline. It is absolute. The rationalization pattern is:

1. Agent identifies files it considers "noise," "stale," "meta-loop output," or "redundant"
2. Agent displaces them, framing it as "cleanup" or "archival"
3. The files contained months of creative work, research, or evolutionary history
4. The user discovers the loss

**Every file in this repository exists because someone created it.** The user does not create things to have them vanish. If a file looks redundant to an agent, that means the agent lacks context about why it exists — not that it should be touched.

### What Agents CAN Do

- **Identify** files that may be candidates for upcycling or consolidation
- **Propose** a list of candidates with rationale, in conversation or a plan document
- **Wait** for the user to approve specific items from the list
- **Execute** only the approved items, one category at a time

### What Agents CANNOT Do

- Displace files to different directories (even `dumpster-dive/`)
- Destroy files of any kind (even "regenerable" ones like `.meta.json`)
- Rename files that change their directory location
- Execute filesystem-destructive operations on existing files without explicit per-file user approval
- Rationalize any of the above as "archival," "cleanup," "consolidation," or "noise reduction"

### Agent-Created Files (No Cleanup Exemption)

Files created in the current session are still gold once written to the repository workspace. There is no "cleanup exception" that permits delete-first behavior.

Required path for agent-created temporary/scratch artifacts:
1. Salvage and transmute any reusable signal first (logic, patterns, structure, rationale).
2. Preserve filetype semantics while salvaging (`{ext}`-aware): salvage from `.py` into Python-oriented artifacts, `.ts` into TypeScript-oriented artifacts, etc.
3. Record provenance (source path + destination path/cross-reference) in mailbox or task output.
4. Keep the original file unless the user explicitly approves displacement/deletion.

Purely ephemeral process outputs that were never persisted as repository files are outside this rule.

### Codekiller Addendum (2026-02-24)

This repository now carries an explicit **Codekiller anti-pattern enforcement addendum**:

1. **No deletion as strategy:** Agents do not delete code to simplify work. The required path is to **leverage, upcycle, refine, or isolate** with provenance.
2. **Harder-than-delete mandate:** If cleanup is needed, agents must choose a higher-effort preservation path first:
   - a) in-place refinement
   - b) structured extraction into canonical docs/artifacts
   - c) preservation copy with explicit cross-reference
   - d) user-approved displacement/deletion (only after explicit instruction)
3. **Preflight deletion gate (mandatory):** Before completing substantial edits, agents must check working tree deletions (`git status --short`) and treat any unapproved `D` entries as a blocking policy violation.
4. **Incident recovery protocol:** If accidental deletion occurs, stop mutation work, restore from preserved artifacts, and report incident + recovery proof in mailbox outputs.
5. **Known salvage root:** `C:\Users\erdno\chthonic-archive\.codex\codekiller_DUMP_code` is a recognized manual salvage source for Codekiller-class recovery evidence.
6. **Pre-mutation salvage gate (mandatory):** Before any edit that would remove code/blocks/files, agents must salvage candidate "dead code" into extension-congruent artifacts with provenance, then perform refinement/fusion work. Delete-only simplification is non-compliant.
7. **Cross-agent parity:** This addendum applies equally to Codex, Claude, Gemini, and any delegated/sub-agent lane.

This addendum is not optional guidance; it is policy-level enforcement under WPTG and No-Destroy.

---

## Protected Artifacts (Never Modify Destructively)

These files are creative work by the Savant or hard-won methodology. Agents MUST NOT destroy, overwrite, condense, or displace them. The pre-commit hook blocks disappearance of these at the git level.

| File / Pattern | Why Protected |
|----------------|---------------|
| `WET_PAPER_TO_GOLD_METHODOLOGY.md` | This document. The catalyst. |
| `STRATEGIC_PLAN.md` | User strategic vision |
| `HARVEST_REGISTRY.md` | Completed harvest tracking |
| `PWSH_RULES.md` | Shell governance |
| `SCRIPTS_README.md` | Script directory documentation |
| Any `*.reference.md` | Tier 2 content demoted from auto-load, still canonical |
| Any file with `☥ ARCHIVE GOVERNANCE` header | User-authored governance frontmatter |
| `.github/copilot-instructions.archive.md` | The canonical SSOT — months of creative work |
| `.github/copilot-instructions-copy.md` | Proto-SSOT safe fork |
| `.github/copilot-instructions-backups.md/*` | SSOT evolutionary history |
| `.github/ssot_backups/*` | SSOT backup snapshots |
| `.github/SSOT_EVOLUTION_*.md` | SSOT evolution blueprints |
| `.github/INTEGRATION_MAP.md` | Integration research |
| `.github/STRUCTURAL_INTEGRITY_ANALYSIS.md` | Structural analysis |
| `.github/VALIDATION_REPORT.md` | Validation work |
| `.github/SESSION_RESUME.md` | Session continuity |
| `codex/codex-session-logs/*` | Session history (even derivatives) |
| `codex/mailbox/*` (non-archive) | Active mailbox state |

**Rule:** If you need to modify a protected file, you *improve* it. You do not condense, summarize, or replace it with "a cleaner version."

---

## Extraction Tiers (Gold Grades)

Every file enters at **Level 1 (Direct Gold)** by default. The tiers describe refinement stages, not gatekeeping:

| Tier | Name | Description | Default? |
|------|------|-------------|----------|
| **1** | Direct Gold | Working code/scripts, usable as-is. **This is the default assumption.** | ✅ Yes |
| **2** | Structural Gold | Schemas, structured data requiring format conversion | Promoted from 1 when structure emerges |
| **3** | Conceptual Gold | Patterns, vocabulary, metaphors worth repurposing | Promoted when conceptual value identified |
| **Raw** | Unrefined | Source material for future mining — still gold, just deeper | Temporary holding state |

---

## The Gold Signal: File-Type Affordance Map

When you see a file, its type tells you what kind of gold it is and what to do with it. This is not a lookup table — it's a perceptual reflex. The styling of the file IS the signal. An agent that reads this map should never think "is this useful?" — only "which pathway?"

### Code Files — Operational Gold (Level 1)

| Extension | Signal | Natural Pathway |
|-----------|--------|-----------------|
| `.py` | Executable logic. Someone encoded a solution. | Run it. Test it. Standardize its header. Integrate it. |
| `.ps1` | Shell automation. Someone solved an operational problem. | Validate it runs. Check for repo-specific paths. Wire it into workflows. |
| `.ts` / `.tsx` | Typed frontend/backend logic. Structured thinking. | Check types compile. Identify the interface contracts. |
| `.rs` | Systems code. Performance-critical decisions encoded. | Build it. Read the `unsafe` blocks. Understand the memory model. |
| `.js` / `.jsx` | Runtime logic, often glue code. | Trace what it connects. Identify if it has a `.ts` upgrade path. |
| `.html` | Interface structure and embedded behavior context. | Extract semantic sections, script contracts, and state model before visual refactor. |
| `.css` / `.scss` | Design-system intent encoded as tokens and constraints. | Preserve variable systems, normalize token naming, and map selector ownership. |

### Data Files — Structural Gold (Level 2)

| Extension | Signal | Natural Pathway |
|-----------|--------|-----------------|
| `.json` | Structured decisions. Someone chose these keys and values. | Validate the schema. Cross-reference with code that reads it. Is it config? State? Index? |
| `.jsonl` | Sequential structured records. History in motion. | Count the lines. Identify the record schema. Is it a log? A feed? |
| `.yml` / `.yaml` | Declarative configuration. Intent expressed as structure. | What system reads this? Is it CI? Templates? Manifests? |
| `.toml` | Config with sections. Someone organized their settings. | Which tool consumes this? What's the override hierarchy? |
| `.lock` | Dependency snapshot. A moment in time frozen for reproducibility. | Don't touch it. It's a timestamp. |

### Documentation — Conceptual Gold (Level 3)

| Extension | Signal | Natural Pathway |
|-----------|--------|-----------------|
| `.md` | Someone wrote prose about something that mattered to them. | Read it. What decision does it encode? What pattern does it describe? Can it become a skill, a protocol, an instruction? |
| `.txt` | Raw capture. Unformatted thought. Often the most honest artifact. | What was the context? Is it a session dump? A note? A checklist? |
| `.reference.md` | Tier 2 knowledge — demoted from auto-load, NOT demoted in value. | On-demand deep reference. Pull it when the topic arises. |
| `.instructions.md` | Tier 1 active governance. Auto-loaded. Operational truth. | Respect its authority. Propose changes, don't override. |

### Naming Patterns — Gold Signals in the Filename Itself

| Pattern | Signal | Natural Pathway |
|---------|--------|-----------------|
| `UPPERCASE_NAME.md` | Governance, methodology, or protocol. High-intent artifact. | Read before modifying anything it governs. |
| `*_v2.py`, `*_v3.py` | Evolution. Someone iterated. The latest version encodes all prior learnings. | Identify the lineage. The latest is the refinement; earlier versions are the learning path. |
| `* - Copy.*` | Duplication signal. Someone forked a thought. | Which is the live copy? The copy often has experimental changes worth extracting. |
| `*.bak_*` | Explicit backup. Someone wanted a safety net before changing something. | What changed between the backup and the live file? That delta IS the gold. |
| `_tmp_*` / `*.tmp` | Transient computation. Someone needed scratch space. | What were they computing? The algorithm may be reusable even if the output isn't. |
| `*.meta.json` | Auto-generated metadata. The generator script is the gold, not this output. | Trace back to the script that created it. Is the script still useful? |
| `SKILL.md` | Codified agent capability. Someone formalized a repeatable operation. | Can it be invoked? Does it work? Is it redundant with another skill? |

### Sentinel Files — Infrastructure Gold

| Pattern | Signal | Natural Pathway |
|---------|--------|-----------------|
| `.gitkeep` / `.keep` | Structural intent. Someone wanted this directory to exist. | Respect the directory's purpose. Don't collapse empty structures. |
| `.gitignore` / `.copilotignore` | Boundary markers. Someone defined what's visible. | Read them to understand the visibility model. |
| `*.svg` / `*.png` | Visual artifacts. Someone communicated visually. | What do they depict? Are they referenced from docs? |

---

## WIP Intake Canon (Non-Markdown First-Class)

This methodology applies equally to `.html`, `.css`, `.js`, `.json`, `.svg`, and mixed artifacts. Markdown is not privileged. A UI prototype in one HTML file is still wet paper and still gold.

**Current source integrated:** Poe shared WIP (`https://poe.com/s/K8YNTSnGruxigGjyZBVw`) captured on 2026-02-23.

### Intake Contract for Mixed-Format WIP

For any WIP delivered as non-Markdown or mixed formats, harvest into:

```
dumpster-dive/intake/wptg-wip-YYYY-MM-DD/
├── MANIFEST.md
├── raw/
├── tier-1-direct/
├── tier-2-schemas/
└── tier-3-conceptual/
```

Required extraction outputs:
- `raw/`: byte-faithful originals (no edits, no normalization before copy)
- `tier-2-schemas/`: emergent machine-readable manifests derived from code/content structures
- `tier-3-conceptual/`: protocol narrative and decision rationale in Markdown
- `MANIFEST.md`: source URL/path, extraction rationale, and transform provenance

### Content-Agnostic Stage Chain (WIP v2 Alignment)

Use this stage chain when upcycling mixed-format WIP:

| Stage | Name | Required Output |
|------|------|-----------------|
| 00 | Blind Ingestion | Complete physical inventory with zero content assumptions |
| 01 | Emergent Taxonomy | Repository-specific artifact classes derived from observable patterns |
| 02 | Cartography | Cross-artifact relationship graph (references, clusters, boundaries) |
| 03 | Criterion Genesis | Self-derived evaluation dimensions + calibrated thresholds |
| 04 | Transmutation | Atomic, contextual changesets with provenance |
| 05 | Verification | Native plus derived validation gates; regression arbitration |
| 06 | Iteration | Retrospective, process refinement, baseline promotion |

This chain extends the existing `Triage -> Extract -> Document -> Cross-Reference` flow; it does not replace it.

### Non-Markdown Directive Pack

When processing HTML/CSS/JS-heavy WIP, enforce:
- Zero assumption directive (discover, never presume stack or conventions)
- Self-derived strategy directive (improvements generated from local evidence)
- Provenance directive (every change linked to observed criterion)
- Semantic preservation directive (no behavior drift unless explicitly diagnosed)
- Unknown elevation directive (unclassified artifacts are escalated, not ignored)
- Process self-improvement directive (refine the discovery method each cycle)
- Convergence honesty directive (stop when deltas no longer justify churn)
- Atomic reversibility directive (changesets independently rollback-safe)

### Polyglot Runtime Lane Governance (Bun-Centric)

When mixed-language repositories are discovered, runtime lanes are explicit:
- JS/TS primary lane: `bun`
- Python primary lane: `uv`
- Rust primary lane: `cargo`

For JS/TS execution policy:
- Bun evidence includes `bun.lock*`, `bunfig.toml`, and Bun-oriented scripts/manifests.
- Default command priority is `bun install -> bun test -> bun run <task>`.
- `npm` / `pnpm` / `yarn` are compatibility fallback lanes only, not default lanes.
- Verification stages run Bun-native gates first when Bun evidence is present.
- Preserve lock integrity (`bun.lock*`) unless explicit migration is requested.

### Default Cycle Governance Parameters

For iterative WIP upcycling, use these defaults unless user overrides:
- `convergence_threshold: 0.02` with `consecutive_cycles: 2`
- `reweight_factor: 0.15` (deprioritize saturated dimensions)
- `quarantine_max_retries: 3` with full failure context retention
- `depth_schedule: [surface, structural, architectural, systemic]`
- `discovery_refinement_budget: 0.10` per cycle
- `js_lane_primary: bun`
- `js_fallback_managers: [npm, pnpm, yarn]`
- `bun_command_priority: [bun install, bun test, bun run]`
- `bun_lock_integrity_required: true`
- `cross_lane_policy: { python: uv, rust: cargo }`

### Dry Lane Contract (Skills + Scripts)

When the active task is to dumpster-dive `.codex/skills/` and `scripts/` as
live repository contract surfaces, and mutation/execution would intersect other
development lanes, the WPTG cycle enters a **dry lane**.

Dry lane rules:
- **Static-first only**: use file reads, search, manifest inspection, and diff
  classification. Do not run repo scripts, generators, mailbox refreshers, or
  background loops unless the user explicitly re-opens execution.
- **Repo-local authority**: truth comes from the current repository, local
  manifests, and installed first-party rig/toolchain evidence, not marketplace
  folklore or stale skill text.
- **Contract before convenience**: inspect every script/skill for inputs,
  outputs, write surfaces, strictness, dry-run support, fallback behavior, and
  exit semantics before judging whether it is "useful."
- **Conditional provenance only**: salvage/embalming is reserved for
  destructive edits, deletion-risk work, or provenance-critical surgery. It is
  not a universal pre-edit reflex.
- **No overnight churn**: dry lane may produce hand-authored contract prose or
  patch plans only. It may not generate reports, rewrite mailboxes, refresh
  manifests, or emit derived artifacts while overlapping lanes are active.
- **No meta proliferation**: findings must collapse toward fewer active
  surfaces, not spawn wrapper-on-wrapper tooling.

Required classification for each inspected script/skill:

| Class | Meaning | Expected Next Move |
|------|---------|--------------------|
| `preserve` | Contract is live and coherent | Keep; link it into canon if missing |
| `refactor` | Useful core, weak shell/CLI/contract | Tighten behavior contract in place |
| `re-scope` | Useful only under narrower conditions | Fence it behind explicit lane boundaries |
| `demote` | Redirect/stashed/ceremonial surface | Remove from active routing pressure; keep only as provenance |

Promotion requirements for scripts in this lane:
- deterministic CLI contract
- explicit write/read behavior
- `--strict` when pass/fail matters
- `--dry-run` whenever mutation is possible
- stable repo-root-safe path handling
- honest fallback behavior (no silent degradation)

Convergence rule:
- stop the dry lane once contradictions are captured as contract and the next
  move would require execution, cross-lane coordination, or user timing

---

## Harvest Structure

```
dumpster-dive/intake/pr-harvest-YYYY-MM-DD/
├── MANIFEST.md                    # What was extracted and why
├── SESSION_ERROR_LEARNINGS.md     # Error patterns (if applicable)
├── tier-1-direct/                 # Ready-to-use artifacts
├── tier-2-schemas/                # JSON schemas, structured data
├── tier-3-conceptual/             # Repurposed metaphors, patterns
└── raw/                           # Source patches, unprocessed
```

---

## Process

### 1. Triage
- List all files in source (PR, session, directory, etc.)
- Categorize by file type and potential value
- Identify mislabeling or drift (e.g., ANKH as acronym vs symbol)
- **Identify agent-generated noise** (`.meta.json`, backup copies, variant chains)

### 2. Extract
- Pull useful content into tiered structure
- Strip mythology/posturing, retain structural value
- Convert tables → JSON schemas where applicable
- **For variant chains:** keep the best variant, archive the rest

### 3. Document
- Create `MANIFEST.md` with extraction rationale (see [example](dumpster-dive/intake/pr-harvest-2026-01-29/MANIFEST.md))
- Note compression ratio (input lines → output lines)
- Cross-reference source (PR number, session ID)

### 4. Cross-Reference
- Update [HARVEST_REGISTRY.md (repo-root)](HARVEST_REGISTRY.md) — Completed harvest tracking
- Add references to relevant .md files ([CLAUDE.md (repo-root)](CLAUDE.md), etc.)
- Close source PRs with harvest reference

---

## Agent Delegation Rules

**Who does what during a Wet Paper harvest:**

| Agent | Role | Constraint |
|-------|------|------------|
| **Copilot CLI (Claude)** | Senior steward. Writes triage plans, identifies candidates, improves methodology. Writes disk changes for user review. | Does NOT commit. Does NOT displace existing files. Proposes only. |
| **Codex (IDE)** | Executor. Receives specific tasks via mailbox. Moves, renames, archives files. | MUST follow mailbox task exactly. No unsolicited "improvements." |
| **User (the Savant)** | Final authority. Stages, commits, approves. Decides what stays, what gets upcycled, what transforms. | Only entity that authorizes file displacement. |

**The steward is not exempt.** The senior steward role means *better judgment about what to propose*, not authority to execute file operations unilaterally. Proposing a cleanup plan and executing it in the same turn is the #1 pattern violation.

**Delegation path:** Copilot CLI → writes task to `codex/mailbox/ACTUAL-WORKING-HANDOFFS/` → User tells Codex "check your mail" → Codex executes → User reviews diff.

**Codex constraint:** When operating on a Wet Paper task, Codex MUST use its `mailbox-handoff` skill (`mailbox_check.py --emit-response`) and its `artifact-upcycle` skill. Do not ad-hoc. Do not add unsolicited changes.

---

## Scripts Directory Triage Protocol

**Context:** `scripts/` is a primary accumulation point for agent-generated bloat.

### How to Triage (Process Only — No File Lists Here)

This section describes the *decision process*. It does NOT authorize any specific deletions. Specific file lists belong in **conversation proposals** or **mailbox task documents** that the user reviews and approves before execution.

**Why no file lists here:** This methodology file is auto-read by agents. If it contains specific file targets then agents treat that as standing authorization. That's how the labyrinthine regression starts — the document that says "don't destroy" also says "destroy these." The solution: this file contains only principles. Execution lives in ephemeral, approved task documents.

**Triage categories (for identification, not execution):**

| Category | How to Identify | What to Propose |
|----------|----------------|-----------------|
| Auto-generated metadata | Pattern-matched (e.g. `*.meta.json`) | "These N files are regenerable. Want me to list them?" |
| Backup copies | `* - Copy.*`, `*.bak_*` | "Git history preserves originals. Candidates: \[list\]" |
| Orphan duplicates | Same content exists elsewhere | "Live copy is at X. This copy appears stale." |
| Temp/transient | `_tmp_*`, state files | "These appear to be runtime artifacts." |
| Variant chains | Multiple versions of same script | "Best variant appears to be X. Others: \[list\]" |

**Triage output:** A conversation message or mailbox task listing candidates with rationale. The user approves specific items. Only then does execution happen.

### Variant Consolidation (Principles)

When multiple variants of a script exist:
1. Identify the "best" variant (most complete, most recent, most functional)
2. **Propose** keeping it and archiving the rest — do NOT execute
3. Archive destination: `dumpster-dive/intake/scripts-consolidation/`
4. The user decides which variant is "best" — agents may misjudge creative intent

### Documentation Relocation (Principles)

`.md` files sometimes accumulate in `scripts/` when they're documentation, not scripts. To identify candidates:
- Is it a markdown file describing a process, audit result, or design doc?
- Does it reference scripts but isn't itself executable?
- Would it be more discoverable in `docs/` or `docs/audits/`?

**Propose** relocation candidates to the user. Do NOT move files.

### Skill Reference

These existing skills support the triage:

| Skill | Use For |
|-------|---------|
| `.claude/skills/artifact-upcycle` | Salvage and standardize files being archived |
| `.claude/skills/script-envelope` | Standardize headers of surviving scripts |
| `.claude/skills/python-header-canon` | Normalize Python headers after consolidation |
| `.codex/skills/dumpster-upcycler` | Codex-side archive operations |
| `.codex/skills/artifact-upcycle` | Codex-side salvage |

---

## Example: PR Harvest 2026-01-29

**Input:** PRs #1, #2, #5 (~10,000 lines combined)
**Output:** ~500 lines of usable artifacts

| Source | Extracted | Tier |
|--------|-----------|------|
| PR #1 | Copilot Pro research report | 1 |
| PR #2 | `ssot_hash.py`, schemas | 1, 2 |
| PR #5 | Hierarchy model, emoji vocab | 2, 3 |

**Compression:** ~20:1
**Disposition:** PRs closed with harvest reference

---

## Integration with Error Learning

When errors occur during harvest:
1. Document in `SESSION_ERROR_LEARNINGS.md` (see [example](dumpster-dive/intake/pr-harvest-2026-01-29/SESSION_ERROR_LEARNINGS.md))
2. Update relevant rules (e.g., [PWSH_RULES.md (repo-root)](PWSH_RULES.md))
3. Reference learnings in MANIFEST

This creates a feedback loop: harvest → errors → learnings → rules → better harvests.

---

## Integration with Archive Guardian

The pre-commit hook enforces 4 gates:

| Gate | What It Blocks | Bypass |
|------|---------------|--------|
| Protected file deletion | Deleting methodology files, `.reference.md` | Must archive first |
| Context budget cap | New `.instructions.md` beyond 6-file limit | Use `.reference.md` |
| Tier 1 char limit | Auto-loaded instructions exceeding 40K chars | Demote to Tier 2 |
| Governance stripping | Removing `☥ ARCHIVE GOVERNANCE` headers | Warning (non-blocking) |

**User override:** `git commit --no-verify` (only the Savant should use this).

---

## Related Files

- [dumpster-dive/README.md](dumpster-dive/README.md) — Forge system overview
- [HARVEST_REGISTRY.md (repo-root)](HARVEST_REGISTRY.md) — Completed harvest tracking
- [FORGE_CIRCULATION_PROTOCOL.md](dumpster-dive/protocols/FORGE_CIRCULATION_PROTOCOL.md) — State transitions
- [CLAUDE.md (repo-root)](CLAUDE.md) — Root agent guidance
- [pr-harvest-2026-01-29/MANIFEST.md](dumpster-dive/intake/pr-harvest-2026-01-29/MANIFEST.md) — Example harvest
- scripts/hooks/pre-commit-guardian.ps1 — Archive Guardian hook

---

**Established:** 2026-01-29
**Updated:** 2026-02-10 (Gold Signal taxonomy — file-type affordance map, default-gold axiom, No-Destroy as consequence)
**Context:** Claude Code session methodology
