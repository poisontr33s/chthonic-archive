# SESSION_HANDOFF — Anti-Pattern Directory Structural Integrity Audit
 
 ## Meta

 ### 1. Codex Skill Summaries (Anti-Pattern / Preservation Relevant)

 - **codekiller-remediation-gate**
   - Purpose: Prerequisite gate for Codekiller (CDE-KLLR) recovery. Produces an evidence-backed readiness report and an iterative remediation plan before any conceptual review. Read-only by default — never rewrites governance records or awards itself points. Outputs READY/BLOCKED status with blockers, evidence anchors, and a four-loop proportional recovery plan with tribunal-aligned milestones.
   - Command: `uv run .codex/skills/codekiller-remediation-gate/scripts/codekiller_remediation_gate.py --emit-json ... --emit-md ...`

 - **artifact-upcycle**
   - Purpose: Salvage stale/orphaned files into agent-ready artifacts. One action per pass (normalize names, add frontmatter, extract TODOs, apply script-envelope, archive/relocate). Never deletes content without archiving. Directly relevant to code preservation — it's the structured counterweight to codekiller behavior.

 - **dumpster-upcycler**
   - Purpose: Converts raw session dumps into compact structured logs (.txt, .json, .md). No deletion — optional archival. Relevant for preserving session context that might otherwise be lost.

 - **iron-maiden-runtime**
   - Purpose: Deterministic runtime harness for the Iron Maiden voicepack (cRPG game content). State model + scene renderer. Not directly relevant to anti-pattern remediation — this is game/Temple content.

 - **skill-polisher**
   - Purpose: Meta-skill ("The Custodian") that audits, refines, and upgrades other skills. Detects structural entropy (missing icons, drifted configs, broken scripts, stubs) and fixes them. Cross-flavor compatible (Codex ↔ Claude). Indirectly relevant — keeps the remediation toolchain itself healthy.

 ### 2. anti-patterns/ Directory Contents

 No `codekiller/` subdirectory exists. The directory contains only two files:

 - `anti-patterns/README.md` — Defines the anti-pattern registry, the original -10 point deduction against Codex (Tier I Capital Offense CAP-001: Mass Deletion), the points economy (Claude: 50 base, Codex: 40 base), and links to the full Tribunal governance system under `.temple/governance/`.

 - `anti-patterns/codekiller.md` — The raw evidence packet. Documents the code-killer commit (9 files changed, +298/-1931), references to SSOT governance rules forbidding deletion, and the creation of `chthonic-archive_transmutation_framework_original.html` as proof of damage. Note: the file references a `codekiller/Readme.md` subdirectory that does not exist — this is a broken reference.

 ### 3. Full Skills Index (24 skills)

 | # | Skill | Description | Scripts |
 |---:|---|---|---|
 | 1 | api-manager | Load/diagnose API tokens (HF/OpenAI) without secrets in git | — |
 | 2 | artifact-upcycle | Salvage orphaned files into clean artifacts | artifact_upcycle.py |
 | 3 | claude-skill-bridge | Codex-side bridge for Claude Code audits/hooks | — |
 | 4 | codex-skill-bridge | Codex-side bridge for Codex audits/hooks | — |
 | 5 | conceptualize | Aesthetic/architectural/philosophical code audit (Disco Elysium monologue) | — |
 | 6 | decision-razor | Aggressive deadlock breaking, force velocity | — |
 | 7 | dumpster-upcycler | Raw dumps → structured logs | dumpster_upcycler.py |
 | 8 | gh-address-comments | Address PR review comments via gh CLI | fetch_comments.py |
 | 9 | gh-fix-ci | Debug failing GitHub Actions checks | inspect_pr_checks.py |
 | 10 | gh-mcp-autonomy | Autonomous GitHub MCP for repo/issue/PR data | — |
 | 11 | imagegen | OpenAI Image API CLI | image_gen.py |
 | 12 | ingest-research | Gemini/Deep Research → structured digests | — |
 | 13 | iron-maiden-runtime | cRPG voicepack harness | render_scene.py |
 | 14 | mailbox-handoff | Cross-agent mailbox routing (Claude ↔ Codex) | mailbox_check.py |
 | 15 | meta-polisher-validator | Validate that meta-skills enforce their scope | — |
 | 16 | openai-docs | OpenAI docs lookup with citations | — |
 | 17 | postman | Continuation-first mailbox reader + skeleton emitter | — |
 | 18 | python-header-canon | Normalize Python shebangs + UTF-8 headers | python_header_canon.py |
 | 19 | script-envelope | Standardize script metadata envelopes (SID, purpose, exports) | script_envelope.py |
 | 20 | session-resumer | Raw session log → warm-start resume packet | session_resumer.py |
 | 21 | skill-polisher | Meta-skill: audit/refine/upgrade other skills | polish_skill.py |
 | 22 | sora | Sora video API CLI | sora.py |
 | 23 | toolchain-doctor | Bun + uv drift diagnosis and safe remediation | toolchain_doctor.py |
 | 24 | trainstop-orchestrator | Chained maintenance proxy (doctor → polisher → mailbox → scribe → manifest) | orchestrate.py, local_ai_readiness.py |

 **Key Finding: Broken Reference**

 > `anti-patterns/codekiller.md` at line 57 references `anti-patterns/codekiller/Readme.md` — that subdirectory doesn't exist. This is a minor codekiller symptom (a reference to content that was never created or was lost).

 Skills most relevant to anti-pattern remediation: `codekiller-remediation-gate` (direct), `artifact-upcycle` (preservation), `conceptualize` (judgment), `skill-polisher` (toolchain integrity), `dumpster-upcycler` (session preservation).

## Scope
- Domain: `TEMPLE` (governance/anti-patterns)
- Objective: Verify structural integrity of `anti-patterns/` directory — cross-references, broken links, missing artifacts, and alignment between the evidence packet and existing Codex skills.

## Context

The `anti-patterns/` directory has been manually refined by the Savant. The files reference governance artifacts, tribunal records, and remediation pathways that need structural validation to ensure all cross-references resolve and the directory is self-consistent.

## Tasks

### TASK 1: Cross-Reference Audit of `anti-patterns/codekiller.md`
- **Read** `anti-patterns/codekiller.md` in full — every line, every reference.
- **Read** `anti-patterns/README.md` in full.
- **Validate** every `policy_basis` reference in the YAML frontmatter resolves to an actual file and line number:
  - `.github/copilot-instructions.md:44`
  - `.github/copilot-instructions.archive.md:5670`
  - `.github/copilot-instructions.archive.md:5676`
  - `WET_PAPER_TO_GOLD_METHODOLOGY.md:42`
  - `WET_PAPER_TO_GOLD_METHODOLOGY.md:68`
  - `chthonic-archive_transmutation_framework_original.html` — does this file exist at the referenced path?
  - `anti-patterns/codekiller/Readme.md` — referenced at line ~57, does this subdirectory exist?
- **Output:** `codex/mailbox/CODEKILLER_CROSSREF_AUDIT.md` — per-reference table: `| Reference | Exists | Line Content (if found) | Status |`

### TASK 2: Skill Prerequisite Self-Assessment
- **Read** `.codex/skills/codekiller-remediation-gate/SKILL.md` in full.
- **Run** the remediation gate script if it has a `--dry-run` or `--check` mode: `uv run .codex/skills/codekiller-remediation-gate/scripts/codekiller_remediation_gate.py --emit-md codex/mailbox/CODEKILLER_GATE_STATUS.md`
- **Cross-check:** Do the skills referenced in the remediation gate actually exist and function?
  - `artifact-upcycle` — read its SKILL.md, verify script exists
  - `conceptualize` — read its SKILL.md
  - `skill-polisher` — read its SKILL.md, verify script exists
- **Question to answer:** If the remediation gate outputs BLOCKED, what specific blockers exist and which skills need structural repair before the gate can pass?

### TASK 3: Evidence Completeness Check
- The `codekiller.md` contains raw code fragments (package.json, verify-host.ts) from the original code-killer commit.
- **Verify:** Does `-1931` lines of deletion evidence align with what's preserved in the evidence packet?
- **Verify:** Is the `chthonic-archive_transmutation_framework_original.html` file referenced in the evidence still present at its expected location (check `WET_PAPER_TO_GOLD_WIP/` or similar paths)?
- **Verify:** Are the Tribunal governance documents referenced in `README.md` all present under `.temple/governance/`?
  - `TRIBUNAL_SPEC.md`, `ROLES.md`, `CRIME_CLASSIFICATION.md`, `POINTS_ECONOMY.md`, `PROCEEDINGS.md`, `TEMPORAL_MECHANICS.md`, `FRACTAL_GOVERNANCE.md`, `ledger/LEDGER.yaml`, `ledger/PRECEDENTS.yaml`

### TASK 4: Structural Repair Manifest
- Based on findings from TASKs 1-3, produce a repair manifest:
  - Broken references that need fixing (files that don't exist, wrong line numbers)
  - Missing subdirectories or files that are referenced but absent
  - Any YAML frontmatter syntax issues in `codekiller.md`
  - Any governance document gaps
- **Output:** `codex/mailbox/CODEKILLER_REPAIR_MANIFEST.md`
- **Do NOT auto-fix anything.** Output findings only. The Savant decides what gets repaired.

## Constraints
- Read-only audit. No file modifications. No point awards. No self-adjudication.
- All output goes to `codex/mailbox/` as structured reports.
- If the remediation gate script fails, capture the error output — that IS the finding.

## Cross-References
- `anti-patterns/codekiller.md` — Primary evidence packet
- `anti-patterns/README.md` — Registry and points ledger
- `.codex/skills/codekiller-remediation-gate/` — Codex's own remediation tooling
- `.temple/governance/` — Tribunal governance system
- `WET_PAPER_TO_GOLD_METHODOLOGY.md` — WPTG enforcement rules

## Handoff Metadata
- Origin: Claude (KCP-2.5 session — side task)
- Destination: Codex .5.3
- Priority: LOW (one-off audit, non-blocking)
- Type: Read-only structural audit
