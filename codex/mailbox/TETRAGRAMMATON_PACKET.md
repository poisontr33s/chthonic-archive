---
type: packet
created: 2026-02-06T20:13:06.593150+00:00
updated: 2026-02-07T20:19:58.518180+00:00
mailbox: codex/mailbox
codename: TETRAGRAMMATON
sources_hash: 8eb2680db7416ef1d9bfe974726c1b4dcfed17f94887f4faac91ba715189be58
sources_count: 14
---

# TETRAGRAMMATON Packet

<!-- @SCRIBED: 2026-02-07T20:19:58.518185+00:00 -->

## Packet Rules
- Paths are repo-relative (portable; no local usernames).
- Large JSON files may be embedded as a valid JSON stub with `_truncated: true`.
- Stub fields: `relative_path`, `bytes`, `sha256`.

## Index
- `SESSION_CONTEXT_CHRONICLE_2026_02_06.md`
- `SESSION_CONTEXT_APPENDIX_2026_02_06.md`
- `SKILLS_PARITY_DISCREPANCY_2026_02_06.md`
- `KISS_PARITY_BRIEF_2026_02_06.md`
- `HF_GEMMA_PROBE.md`
- `hf_gemma_probe.json`
- `CLAUDE_RUNBOOK_MATRIX.md`
- `QUEUE_2026_02_07.md`
- `MAILBOX_CURRENT_STATE.md`
- `tatragrammatron_matrix_2026_02_07.json`
- `TATRAGRAMMATRON_SUMMARY_LATEST_CODEX.md`
- `tatragrammatron_stamps_latest_codex.json`
- `tatragrammatron_trend.json`
- `mailbox_manifest.json`

## Snapshot
- Generated: `2026-02-07T20:19:58.518180+00:00`
- Sources hash: `8eb2680db7416ef1d9bfe974726c1b4dcfed17f94887f4faac91ba715189be58`

## Content

### SESSION_CONTEXT_CHRONICLE_2026_02_06.md
Path: `codex/mailbox/SESSION_CONTEXT_CHRONICLE_2026_02_06.md`

```md
---
type: consolidated-session-report
created: 2026-02-06
scope: train-stop_to_parity_gate
status: active
---

# Session Chronicle: Train Stop -> Cross-Compatibility Stabilization

## Intent
Preserve full historical value of the session while converting scattered mailbox notes into a stable, high-signal operational narrative.

## Executive Outcome
- Cross-compatibility lane established for Codex-side and Claude-side skills.
- Canonical path policy enforced: skills under hidden roots, handoffs under visible mailboxes.
- Mailbox sprawl reduced without deletion of historical context (archived, not discarded).
- Parity and E2E matrix artifacts produced and retained for reproducible checks.

## Hierarchical Timeline
1. Train Stop baseline established.
- Session initiated around integrity sweep, polisher recursion, and cross-IDE skill parity goals.
- Handoff loop established between Codex and Claude mailboxes.

2. Skill architecture hardened.
- Meta-skill and bridge concepts operationalized (`skill-polisher`, bridge skills, validator lane).
- Standardization pass applied around command policy and uv execution model.

3. Cross-flavor standards clarified.
- Codex/OpenAI and Claude/Anthropic skill semantics mapped as equivalent by contract, not identical file layout.
- Audit scripts used to validate both skill trees independently.

4. Canonical storage model fixed.
- Skills canonicalized to hidden roots (`.codex/skills`, `.claude/skills`).
- Mailboxes canonicalized to visible roots (`codex/mailbox`, `claude/mailbox`).
- Hidden mailbox roots retained as sentinel-only (`.gitkeep`).

5. Parity gap documented and measured.
- Structural discrepancy report generated.
- Skill parity map JSON generated and mirrored.
- E2E matrix comparison artifacts retained.

6. Mailbox hygiene completed.
- Active-cycle artifacts kept in mailbox root.
- Historical notes moved to mailbox `archive/` on both sides.
- Mailbox manifests and current-state docs generated.

7. Upstream model baseline refreshed.
- Claude release-notes baseline folded into parity documentation.
- Settings adjusted to Opus-focused defaults with high effort + thinking enabled where supported in Claude Code settings.

## Current Stable State
- Routing discipline: deterministic.
- Historical trace: preserved in archives.
- Operational root artifacts: compact and current.
- Audit posture: green on current mailbox layout checks.

## What Is Preserved (No Loss)
- All superseded reports remain available under:
- `codex/mailbox/archive/`
- `claude/mailbox/archive/`

## Operating Rule Going Forward
- New cycle outputs land in mailbox root.
- Superseded cycle outputs move to archive at cycle close.
- Root remains concise; archive remains complete.

## Immediate Next Use
- Send this chronicle + appendix as the canonical context packet via mailbox skill when handing off.
```

### SESSION_CONTEXT_APPENDIX_2026_02_06.md
Path: `codex/mailbox/SESSION_CONTEXT_APPENDIX_2026_02_06.md`

```md
---
type: consolidated-session-appendix
created: 2026-02-06
scope: train-stop_to_parity_gate
status: active
---

# Technical Appendix: Evidence and Traceability

## Core Active Artifacts (Codex Mailbox)
- `codex/mailbox/SKILLS_PARITY_DISCREPANCY_2026_02_06.md`
- `codex/mailbox/skills_parity_map_2026_02_06.json`
- `codex/mailbox/KISS_PARITY_BRIEF_2026_02_06.md`
- `codex/mailbox/e2e_matrix_codex_on_codex.json`
- `codex/mailbox/e2e_matrix_codex_on_claude.json`
- `codex/mailbox/e2e_matrix_claude_on_codex.json`
- `codex/mailbox/e2e_matrix_claude_on_claude.json`
- `codex/mailbox/e2e_matrix_compare_summary.json`
- `codex/mailbox/META_POLISHER_VALIDATION_SUMMARY.json`
- `codex/mailbox/mailbox_manifest.json`
- `codex/mailbox/MAILBOX_CURRENT_STATE_2026_02_06.md`

## Core Active Artifacts (Claude Mailbox)
- `claude/mailbox/SKILLS_PARITY_DISCREPANCY_2026_02_06.md`
- `claude/mailbox/skills_parity_map_2026_02_06.json`
- `claude/mailbox/KISS_PARITY_BRIEF_2026_02_06.md`
- `claude/mailbox/e2e_matrix_codex_on_codex.json`
- `claude/mailbox/e2e_matrix_codex_on_claude.json`
- `claude/mailbox/e2e_matrix_claude_on_codex.json`
- `claude/mailbox/e2e_matrix_claude_on_claude.json`
- `claude/mailbox/CLAUDE_META_VALIDATION_SUMMARY.json`
- `claude/mailbox/mailbox_manifest.json`
- `claude/mailbox/MAILBOX_CURRENT_STATE_2026_02_06.md`

## Archived Historical Reports (Preserved)
### Codex archive
- `codex/mailbox/archive/TRAIN_STOP_HANDOFF_CONSOLIDATED_2026_02_05.md`
- `codex/mailbox/archive/TRAIN_STOP_AUDIT_PRE_SEND_2026_02_05.md`
- `codex/mailbox/archive/MAILBOX_CONSOLIDATED_2026_02_05.md`
- `codex/mailbox/archive/CLAUDE_RESPONSE_TRAIN_STOP_2026_02_05.md`
- `codex/mailbox/archive/CLAUDE_SKILLS_SPEC_VALIDATION_2026_02_05.md`
- `codex/mailbox/archive/SESSION_HANDOFF_2026_02_05_PARITY_DELTA.md`
- `codex/mailbox/archive/EXECUTION_ORDER_RECAP_2026_02_05.md`
- `codex/mailbox/archive/MAILBOX_CMD_POLICY_2026_02_05.md`
- `codex/mailbox/archive/skill_audit_codex_2026_02_05.json`
- `codex/mailbox/archive/skill_audit_claude_2026_02_05.json`

### Claude archive
- `claude/mailbox/archive/SESSION_HANDOFF_2026_02_05_OPERATION_TRAIN_STOP.md`
- `claude/mailbox/archive/SESSION_HANDOFF_2026_02_05_MAILBOX_SKILL_UPDATE.md`
- `claude/mailbox/archive/SESSION_HANDOFF_2026_02_05_PARITY_DELTA.md`

## Verification Commands Used in This Lane
- `uv run scripts/skill_audit.py --flavor codex --root .codex/skills`
- `uv run scripts/skill_audit.py --flavor claude --root .claude/skills`
- `uv run scripts/check_mailbox_layout.py`
- `./scripts/run_e2e_parity_gate.ps1`

## Canonical Path Model
- Codex skills: `.codex/skills`
- Claude skills: `.claude/skills`
- Codex mailbox: `codex/mailbox`
- Claude mailbox: `claude/mailbox`
- Hidden mailbox roots are sentinel-only: `.codex/mailbox/.gitkeep`, `.claude/mailbox/.gitkeep`

## Decision Record
- Historical context is archived, not deleted.
- Operational context stays concise in mailbox root.
- Hand-off packet should include this appendix plus chronicle for complete continuity.
```

### SKILLS_PARITY_DISCREPANCY_2026_02_06.md
Path: `codex/mailbox/SKILLS_PARITY_DISCREPANCY_2026_02_06.md`

```md
---
type: parity-report
created: 2026-02-06
scope: codex-vs-claude-skills
---

# Skills Parity Discrepancy Report

## Summary
- Compared `.codex/skills` vs `.claude/skills` by file inventory and per-skill structure.
- Structural parity is partial: skill names align, implementation payload does not.
- Audit status is clean on both sides (`skill_audit.py` passes), but content parity is not equivalent.

## High-Signal Findings
- File count mismatch:
  - `.codex/skills`: 115 files
  - `.claude/skills`: 36 files
- For all 16 shared skill names:
  - `SKILL.md` content differs (`skillmd_equal=False` for all)
  - Codex has `agents/` for all 16
  - Claude has `agents/` for 0
  - Codex has scripts in 8 skills; Claude has scripts in 0
  - Codex has references in 5 skills; Claude has references in 0

## Per-Skill Structural Gap (Codex -> Claude)
- `artifact-upcycle`: missing `agents/`, `scripts/`, `references/`
- `claude-skill-bridge`: missing `agents/`
- `codex-skill-bridge`: missing `agents/`
- `conceptualize`: missing `agents/`, `references/`
- `decision-razor`: missing `agents/`
- `gh-address-comments`: missing `agents/`, `scripts/`
- `gh-fix-ci`: missing `agents/`, `scripts/`
- `gh-mcp-autonomy`: missing `agents/`
- `imagegen`: missing `agents/`, `scripts/`, `references/`
- `mailbox-handoff`: missing `agents/`
- `meta-polisher-validator`: missing `agents/`
- `openai-docs`: missing `agents/`
- `python-header-canon`: missing `agents/`, `scripts/`
- `script-envelope`: missing `agents/`, `scripts/`, `references/`
- `skill-polisher`: missing `agents/`, `scripts/`
- `sora`: missing `agents/`, `scripts/`, `references/`

## Interpretation
- This is expected if Claude-side is kept Claude-native and intentionally minimal.
- This is a discrepancy if your goal is operational equivalence across all cross-run paths.

## Surgical Equalization Paths
1. Metadata parity only (recommended baseline):
- Keep Claude `SKILL.md` Claude-native.
- Add parity manifest per skill describing equivalent command contract.
- Keep scripts centralized in repo `scripts/` and referenced by both sides.

2. Full payload parity (strict equivalence):
- Mirror `scripts/` + `references/` into `.claude/skills/*`.
- Keep Claude frontmatter semantics in `SKILL.md` while sharing script bodies.
- Add CI parity check to fail on drift.

3. Hybrid proxy parity:
- Keep `.claude/skills` lightweight.
- Add bridge hooks from Claude skills to run canonical scripts under `.codex/skills/*/scripts` or root `scripts/`.
- Preserve one implementation source while exposing both IDE flavors.

## Current Recommendation
- Use Path 3 now (least churn, best KISS).
- Add one machine-readable parity map JSON and enforce it via `run_e2e_parity_gate.ps1`.

## Fresh Upstream Baseline (Confirmed)
- Source: Claude Developer Platform release notes overview:
  - https://platform.claude.com/docs/en/release-notes/overview
- Relevant update date: February 5, 2026.
- Confirmed platform changes affecting cross-equivalence design:
  - Claude Opus 4.6 launched.
  - Adaptive thinking is recommended; manual `budget_tokens` path is deprecated on Opus 4.6.
  - `effort` is GA and replaces older thinking-depth controls on new models.
  - Compaction API is available (beta) for long-context workflows.
  - 1M context window is available in beta on Opus 4.6.

## Symmetric Equivalence Implication (Codex/OpenAI <-> Claude/Anthropic)
- Keep skill contracts equivalent at the workflow level, not by forcing identical model knobs.
- Store provider-specific knobs in flavor overlays:
  - OpenAI/Codex overlay: model + reasoning/effort controls per OpenAI surface.
  - Claude overlay: `thinking.type=adaptive`, `effort`, compaction-aware settings.
- Keep a shared parity core (commands, artifacts, mailbox routes, check/audit hooks).
```

### KISS_PARITY_BRIEF_2026_02_06.md
Path: `codex/mailbox/KISS_PARITY_BRIEF_2026_02_06.md`

```md
---
type: handoff
from: codex
to: codex
created: 2026-02-06
priority: high
---

# KISS Parity Brief: Codex vs Claude Skills

## Purpose
Truncate session noise into a minimal, operational map of differences and current parity status.

## Canonical Paths
- Codex skills: `.codex/skills`
- Claude skills: `.claude/skills`
- Codex mailbox: `codex/mailbox`
- Claude mailbox: `claude/mailbox`
- Non-canonical hidden mailboxes: `.codex/mailbox`, `.claude/mailbox` (sentinel only)

## Standards Delta (KISS)
1. Codex/OpenAI skill model
- Required: `SKILL.md` with `name`, `description`
- Codex-specific ecosystem artifacts expected by local audit policy: `agents/openai.yaml`, `assets/*.svg`

2. Claude skill model
- Required: `SKILL.md` with Claude frontmatter (`name`, `description`)
- Optional operational keys used here: `allowed-tools`, `argument-hint`, `user-invocable`, `disable-model-invocation`
- No native requirement for `agents/openai.yaml`

3. Cross-compat bridge policy
- Claude skills carry:
  - `metadata.codex-compat: true`
  - `metadata.openai-agent: false`
- This allows codex-flavor audits to pass on Claude skills without forcing OpenAI agent files.

## Current State (Now)
1. Skill parity
- `python-header-canon` now exists on both sides.
- `script-envelope` upgraded with:
  - open-sided box normalization
  - python prologue validation
  - dependency policy (pyproject SSOT)

2. Metadata system
- Universal sidecar schema: `.meta/script-envelope.schema.json`
- Extract/sync/inject tool: `scripts/envelope_sync.py`
  - `--check`
  - `--inject`
  - `--force`
  - `--prefer-source`

3. Policy guardrails
- `scripts/check_python_policy.py`
  - default lane: python/dependency execution policy
  - `--proto-ssot-style` lane: symbolic/backtick style checks for markdown targets
- `scripts/check_mailbox_layout.py`
  - enforces canonical mailbox topology

4. Audit lane
- `scripts/run_cross_audit.ps1` now runs:
  1) Codex skill audit
  2) Claude skill audit
  3) Python policy check
  4) Mailbox layout check

## Operator Commands
```powershell
./scripts/run_cross_audit.ps1
uv run scripts/envelope_sync.py scripts/ --check
uv run scripts/envelope_sync.py scripts/ --inject
uv run scripts/check_python_policy.py
uv run scripts/check_python_policy.py --proto-ssot-style
uv run scripts/check_mailbox_layout.py
```

## Bottom Line
- Differences are now explicit, bounded, and audited.
- Parity is achieved where it matters operationally, without forcing unnatural format equivalence between OpenAI and Claude skill ecosystems.

---

Report Hash: `KISS_PARITY_BRIEF_2026_02_06`
```

### HF_GEMMA_PROBE.md
Path: `codex/mailbox/HF_GEMMA_PROBE.md`

```md
# HF Gemma Probe

- Generated: `2026-02-06T20:21:36.149910+00:00`
- Search: `gemma-3`
- Total fetched: `200`
- Top emitted: `25`

## Top Candidates

| Repo | Score | Downloads | Likes | Gated | Private | Last Modified | Tags |
|---|---:|---:|---:|---:|---:|---|---|
| `google/gemma-3-27b-it` | `65.0` | `1622506` | `1856` | `manual` | `False` | `2025-03-21 20:29:02+00:00` | `transformers, safetensors, gemma3, image-to-text, image-text-to-text, conversational, arxiv:1905.07830, arxiv:1905.10044` |
| `google/gemma-3-4b-it` | `62.007` | `996075` | `1157` | `manual` | `False` | `2025-03-21 20:20:53+00:00` | `transformers, safetensors, gemma3, image-to-text, image-text-to-text, conversational, arxiv:1905.07830, arxiv:1905.10044` |
| `google/gemma-3-1b-it` | `59.414` | `1573932` | `831` | `manual` | `False` | `2025-04-04 13:12:40+00:00` | `transformers, safetensors, gemma3_text, text-generation, conversational, arxiv:1905.07830, arxiv:1905.10044, arxiv:1911.11641` |
| `google/gemma-3-12b-it` | `57.708` | `1411902` | `646` | `manual` | `False` | `2025-03-21 20:28:56+00:00` | `transformers, safetensors, gemma3, image-to-text, image-text-to-text, conversational, arxiv:1905.07830, arxiv:1905.10044` |
| `unsloth/gemma-3-4b-it-GGUF` | `57.405` | `193103` | `167` | `False` | `False` | `2025-08-14 19:57:28+00:00` | `transformers, gguf, gemma3, image-to-text, unsloth, gemma, google, en` |
| `unsloth/gemma-3-4b-it` | `57.345` | `254643` | `22` | `False` | `False` | `2025-05-12 07:54:39+00:00` | `transformers, safetensors, gemma3, image-to-text, unsloth, image-text-to-text, conversational, arxiv:1905.07830` |
| `MaziyarPanahi/gemma-3-4b-it-GGUF` | `54.544` | `206322` | `18` | `False` | `False` | `2025-03-12 20:16:35+00:00` | `gguf, mistral, quantized, 2-bit, 3-bit, 4-bit, 5-bit, 6-bit` |
| `google/gemma-3n-E2B-it` | `53.17` | `305510` | `267` | `manual` | `False` | `2025-07-14 13:55:52+00:00` | `transformers, safetensors, gemma3n, image-to-text, automatic-speech-recognition, automatic-speech-translation, audio-text-to-text, video-text-to-text` |
| `MaziyarPanahi/gemma-3-12b-it-GGUF` | `51.017` | `177075` | `15` | `False` | `False` | `2025-03-12 20:43:42+00:00` | `gguf, mistral, quantized, 2-bit, 3-bit, 4-bit, 5-bit, 6-bit` |
| `MaziyarPanahi/gemma-3-1b-it-GGUF` | `50.633` | `176185` | `11` | `False` | `False` | `2025-03-12 20:06:29+00:00` | `gguf, mistral, quantized, 2-bit, 3-bit, 4-bit, 5-bit, 6-bit` |
| `google/gemma-3n-E4B-it` | `50.25` | `164386` | `865` | `manual` | `False` | `2025-07-14 13:56:17+00:00` | `transformers, safetensors, gemma3n, image-to-text, automatic-speech-recognition, automatic-speech-translation, audio-text-to-text, video-text-to-text` |
| `MaziyarPanahi/gemma-3-27b-it-GGUF` | `50.158` | `174252` | `8` | `False` | `False` | `2025-03-16 21:49:31+00:00` | `gguf, quantized, 2-bit, 3-bit, 4-bit, 5-bit, 6-bit, 8-bit` |
| `mlabonne/gemma-3-27b-it-abliterated` | `49.714` | `132111` | `280` | `False` | `False` | `2025-03-21 16:10:45+00:00` | `transformers, safetensors, gemma3, image-to-text, image-text-to-text, conversational, base_model:google/gemma-3-27b-it, base_model:finetune:google/gemma-3-27b-it` |
| `abhishekchohan/gemma-3-12b-it-quantized-W4A16` | `49.175` | `183634` | `7` | `False` | `False` | `2025-03-17 20:13:37+00:00` | `transformers, safetensors, gemma3, image-to-text, image-text-to-text, conversational, base_model:google/gemma-3-12b-it, base_model:quantized:google/gemma-3-12b-it` |
| `unsloth/gemma-3-12b-it-GGUF` | `48.519` | `125862` | `146` | `False` | `False` | `2025-08-14 19:58:38+00:00` | `transformers, gguf, gemma3, image-to-text, unsloth, gemma, google, en` |
| `unsloth/gemma-3-27b-it-bnb-4bit` | `47.824` | `165671` | `18` | `False` | `False` | `2025-05-12 08:08:43+00:00` | `transformers, safetensors, gemma3, image-to-text, unsloth, gemma, google, en` |
| `unsloth/gemma-3-27b-it-GGUF` | `46.991` | `110401` | `183` | `False` | `False` | `2025-08-14 19:58:58+00:00` | `transformers, gguf, gemma3, image-to-text, unsloth, gemma, google, en` |
| `leon-se/gemma-3-27b-it-qat-W4A16-G128` | `46.249` | `153564` | `17` | `False` | `False` | `2025-04-27 20:09:06+00:00` | `safetensors, gemma3, image-text-to-text, conversational, base_model:google/gemma-3-27b-it-qat-q4_0-unquantized, base_model:quantized:google/gemma-3-27b-it-qat-q4_0-unquantized, license:gemma, compressed-tensors` |
| `google/gemma-3-4b-pt` | `46.021` | `300728` | `145` | `manual` | `False` | `2025-03-21 16:13:41+00:00` | `transformers, safetensors, gemma3, image-to-text, image-text-to-text, arxiv:1905.07830, arxiv:1905.10044, arxiv:1911.11641` |
| `mlx-community/gemma-3-4b-it-qat-4bit` | `43.715` | `181448` | `5` | `False` | `False` | `2025-04-21 20:31:00+00:00` | `transformers, safetensors, gemma3, image-to-text, internvl, custom_code, mlx, image-text-to-text` |
| `google/gemma-3-270m-it` | `42.644` | `129166` | `548` | `manual` | `False` | `2025-08-14 07:35:07+00:00` | `transformers, safetensors, gemma3_text, text-generation, gemma3, gemma, google, conversational` |
| `pytorch/gemma-3-27b-it-AWQ-INT4` | `41.511` | `128192` | `2` | `False` | `False` | `2025-10-11 01:51:54+00:00` | `transformers, pytorch, gemma3, image-to-text, torchao, en, arxiv:2507.16099, base_model:google/gemma-3-27b-it` |
| `lmstudio-community/gemma-3-4b-it-GGUF` | `40.88` | `97853` | `27` | `False` | `False` | `2025-03-12 18:32:41+00:00` | `gguf, image-text-to-text, base_model:google/gemma-3-4b-it, base_model:quantized:google/gemma-3-4b-it, license:gemma, endpoints_compatible, region:us, conversational` |
| `google/gemma-3-270m` | `38.433` | `107667` | `976` | `manual` | `False` | `2025-08-14 07:35:01+00:00` | `transformers, safetensors, gemma3_text, text-generation, gemma3, gemma, google, arxiv:2503.19786` |
| `lmstudio-community/gemma-3n-E4B-it-MLX-4bit` | `36.49` | `96040` | `1` | `False` | `False` | `2025-07-21 15:52:20+00:00` | `transformers, safetensors, gemma3n, image-to-text, automatic-speech-recognition, automatic-speech-translation, audio-text-to-text, video-text-to-text` |

## Notes

- This is Hub metadata only (not a benchmark).
- If `gated=true`, you may need to accept model terms on the Hub UI before downloads/inference.
- `inference_provider_mapping` presence indicates the model may be routable via Inference Providers; absence does not mean unusable.
```

### hf_gemma_probe.json
Path: `codex/mailbox/hf_gemma_probe.json`

```json
{
  "_truncated": true,
  "note": "Full JSON omitted from packet; see relative_path in the repo.",
  "name": "hf_gemma_probe.json",
  "relative_path": "codex/mailbox/hf_gemma_probe.json",
  "bytes": 33153,
  "sha256": "71836b7ae75ab8e6dacbfc4be7d9c5831ebee52a0e751df07ad843ec1ca1489a"
}
```

### CLAUDE_RUNBOOK_MATRIX.md
Path: `codex/mailbox/CLAUDE_RUNBOOK_MATRIX.md`

```md
# Claude Runbook: Polisher Matrix (Codex-generated)

Goal: reproduce the same matrix runs from Claude Code.

All commands are PowerShell and follow repo policy: `uv run <script.py>`.

## 1. Codex contract on Codex skills
```powershell
uv run .codex/skills/skill-polisher/scripts/polish_skill.py .codex/skills --all --mode verify --subprocess-fix --target-flavor codex --emit-stamps-json codex/mailbox/tatragrammatron_stamps_2026_02_07_codex_on_codex.json --emit-summary-md codex/mailbox/TATRAGRAMMATRON_SUMMARY_2026_02_07_CODEX_ON_CODEX.md
```

## 2. Claude contract on Claude skills
```powershell
uv run .codex/skills/skill-polisher/scripts/polish_skill.py .claude/skills --all --mode verify --subprocess-fix --target-flavor claude --emit-stamps-json codex/mailbox/tatragrammatron_stamps_2026_02_07_codex_on_claude.json --emit-summary-md codex/mailbox/TATRAGRAMMATRON_SUMMARY_2026_02_07_CODEX_ON_CLAUDE.md
```

## 3. Auto detection on Claude skills
```powershell
uv run .codex/skills/skill-polisher/scripts/polish_skill.py .claude/skills --all --mode verify --subprocess-fix --target-flavor auto --emit-stamps-json codex/mailbox/tatragrammatron_stamps_2026_02_07_auto_on_claude.json --emit-summary-md codex/mailbox/TATRAGRAMMATRON_SUMMARY_2026_02_07_AUTO_ON_CLAUDE.md
```

## 4. Cross-flavor auditor (independent check)
```powershell
uv run scripts/skill_audit.py --flavor codex --root .codex/skills --json --json-path codex/mailbox/codex_skill_audit_2026_02_07.json
uv run scripts/skill_audit.py --flavor claude --root .claude/skills --json --json-path codex/mailbox/claude_skill_audit_2026_02_07.json
```

## Expected artifacts
- `codex/mailbox/tatragrammatron_matrix_2026_02_07.json`
- stamps JSONs + summaries as above

## Notes
- If a run creates new icons/yaml scaffolds, that is expected under `--subprocess-fix`.
- Re-run `scripts/mailbox_scribe.py` after matrix runs to refresh the packet.
```

### QUEUE_2026_02_07.md
Path: `codex/mailbox/QUEUE_2026_02_07.md`

```md
# Tatragrammatron Queue (2026-02-07)

This queue captures the next iteration tranche for cross-flavor, poly-directional meta-skill capability.

## 1. Polisher Matrix Runner
- Goal: single command runs Codex-side matrix and emits one matrix JSON plus standard artifacts.
- Deliverables:
  - `scripts/run_polisher_matrix.py`
  - `codex/mailbox/tatragrammatron_matrix_YYYY_MM_DD.json`

## 2. Claude Toolchain Parity Hook (Proxy)
- Goal: provide Claude Code runbook to reproduce matrix from Claude side.
- Deliverables:
  - `codex/mailbox/CLAUDE_RUNBOOK_MATRIX.md`

## 3. FIXTURE_EVAL_V1 Expansion
- Add fixtures:
  - `claude_missing_description`
  - `codex_missing_assets_dir`
  - `codex_missing_agents_yaml`

## 4. Remediation Safety Gate
- Add flags:
  - `--dry-run-apply`
  - Ensure `--subprocess-fix` respects `--max-fix-per-skill` default

## 5. Skill Identity Normalization
- Add WARN checks:
  - Claude: frontmatter `name:` matches folder name
  - Codex: `agents/openai.yaml` name matches folder name

## 6. E2E Verification Sweep
- Run codex->codex, codex->claude, auto.
- Emit artifacts and refresh packet.

## 7. Trainstop Rewind Proxy (Orchestrator)
- Goal: a single proxy runner that chains the non-official skills/tools in the correct order and refreshes artifacts deterministically.
- Non-goal: modifying "official" OpenAI skills (`sora`, `imagegen`, etc.).
- Deliverables:
  - `.codex/skills/trainstop-orchestrator/`
  - `uv run .codex/skills/trainstop-orchestrator/scripts/orchestrate.py --target both --apply`
```

### MAILBOX_CURRENT_STATE.md
Path: `codex/mailbox/MAILBOX_CURRENT_STATE.md`

```md
---
type: mailbox-state
updated: 2026-02-07T20:19:58.512074+00:00
mailbox: codex/mailbox
---

# Mailbox Current State

## Active Files
- `CLAUDE_RUNBOOK_MATRIX.md`
- `HF_GEMMA_PROBE.md`
- `KISS_PARITY_BRIEF_2026_02_06.md`
- `MAILBOX_CURRENT_STATE.md`
- `META_POLISHER_VALIDATION_SUMMARY.json`
- `QUEUE_2026_02_07.md`
- `SESSION_CHRONICLE_2026_02_07.md`
- `SESSION_CONTEXT_APPENDIX_2026_02_06.md`
- `SESSION_CONTEXT_CHRONICLE_2026_02_06.md`
- `SKILLS_PARITY_DISCREPANCY_2026_02_06.md`
- `TATRAGRAMMATRON_SUMMARY_LATEST_CODEX.md`
- `TETRAGRAMMATON_PACKET.md`
- `TETRAGRAMMATON_PROGRESS_2026_02_06.md`
- `TOOLCHAIN_DOCTOR_LATEST.md`
- `TOOLCHAIN_DOCTOR_REPORT_2026_02_07_174714.md`
- `TOOLCHAIN_DOCTOR_REPORT_2026_02_07_180524.md`
- `TOOLCHAIN_DOCTOR_REPORT_2026_02_07_180604.md`
- `TOOLCHAIN_DOCTOR_REPORT_2026_02_07_194657.md`
- `claude_skill_audit_2026_02_07.json`
- `hf_gemma_probe.json`
- `mailbox_manifest.json`
- `skills_parity_map_2026_02_06.json`
- `tatragrammatron_matrix_2026_02_07.json`
- `tatragrammatron_stamps_latest_codex.json`
- `tatragrammatron_trend.json`

## Archive
- Path: `codex/mailbox/archive`
- Count: 40

## Policy
- Root mailbox keeps only current-cycle files.
- Historical files may remain in `archive/`.
- Hidden dot mailboxes stay sentinel-only (`.gitkeep`).
```

### tatragrammatron_matrix_2026_02_07.json
Path: `codex/mailbox/tatragrammatron_matrix_2026_02_07.json`

```json
{
  "generated_at": "2026-02-07T04:15:19.398641+00:00",
  "runner": "codex",
  "cases": [
    {
      "case": {
        "name": "codex_on_codex",
        "root": ".codex/skills",
        "target_flavor": "codex",
        "require_assets": true
      },
      "exit_code": 0,
      "stamps_json": "codex/mailbox/tatragrammatron_stamps_2026_02_07_codex_on_codex.json",
      "summary_md": "codex/mailbox/TATRAGRAMMATRON_SUMMARY_2026_02_07_CODEX_ON_CODEX.md"
    },
    {
      "case": {
        "name": "codex_on_claude",
        "root": ".claude/skills",
        "target_flavor": "claude",
        "require_assets": true
      },
      "exit_code": 0,
      "stamps_json": "codex/mailbox/tatragrammatron_stamps_2026_02_07_codex_on_claude.json",
      "summary_md": "codex/mailbox/TATRAGRAMMATRON_SUMMARY_2026_02_07_CODEX_ON_CLAUDE.md"
    },
    {
      "case": {
        "name": "auto_on_claude",
        "root": ".claude/skills",
        "target_flavor": "auto",
        "require_assets": true
      },
      "exit_code": 0,
      "stamps_json": "codex/mailbox/tatragrammatron_stamps_2026_02_07_auto_on_claude.json",
      "summary_md": "codex/mailbox/TATRAGRAMMATRON_SUMMARY_2026_02_07_AUTO_ON_CLAUDE.md"
    },
    {
      "case": {
        "name": "claude_contract_on_codex",
        "root": ".codex/skills",
        "target_flavor": "claude",
        "require_assets": true
      },
      "exit_code": 0,
      "stamps_json": "codex/mailbox/tatragrammatron_stamps_2026_02_07_claude_contract_on_codex.json",
      "summary_md": "codex/mailbox/TATRAGRAMMATRON_SUMMARY_2026_02_07_CLAUDE_CONTRACT_ON_CODEX.md"
    }
  ]
}
```

### TATRAGRAMMATRON_SUMMARY_LATEST_CODEX.md
Path: `codex/mailbox/TATRAGRAMMATRON_SUMMARY_LATEST_CODEX.md`

```md
# Skill Polisher Summary

- Generated: `2026-02-07T19:46:58.353422+00:00`
- Mode: `verify`
- Total skills: `18`
- Passed: `18`
- Failed: `0`
- Pure: `18`

## Scores

| Skill | Exit | Total | Structure | Policy | Semantics | Maintainability | Issues | Fixes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `artifact-upcycle` | `0` | `100` | `100` | `100` | `100` | `100` | `1` | `0` |
| `claude-skill-bridge` | `0` | `100` | `100` | `100` | `100` | `100` | `0` | `0` |
| `codex-skill-bridge` | `0` | `100` | `100` | `100` | `100` | `100` | `0` | `0` |
| `conceptualize` | `0` | `100` | `100` | `100` | `100` | `100` | `0` | `0` |
| `decision-razor` | `0` | `100` | `100` | `100` | `100` | `100` | `0` | `0` |
| `gh-address-comments` | `0` | `100` | `100` | `100` | `100` | `100` | `0` | `0` |
| `gh-fix-ci` | `0` | `100` | `100` | `100` | `100` | `100` | `0` | `0` |
| `gh-mcp-autonomy` | `0` | `100` | `100` | `100` | `100` | `100` | `0` | `0` |
| `imagegen` | `0` | `100` | `100` | `100` | `100` | `100` | `0` | `0` |
| `mailbox-handoff` | `0` | `100` | `100` | `100` | `100` | `100` | `0` | `0` |
| `meta-polisher-validator` | `0` | `100` | `100` | `100` | `100` | `100` | `0` | `0` |
| `openai-docs` | `0` | `100` | `100` | `100` | `100` | `100` | `0` | `0` |
| `python-header-canon` | `0` | `100` | `100` | `100` | `100` | `100` | `0` | `0` |
| `script-envelope` | `0` | `100` | `100` | `100` | `100` | `100` | `0` | `0` |
| `skill-polisher` | `0` | `100` | `100` | `100` | `100` | `100` | `1` | `0` |
| `sora` | `0` | `100` | `100` | `100` | `100` | `100` | `0` | `0` |
| `toolchain-doctor` | `0` | `100` | `100` | `100` | `100` | `100` | `0` | `0` |
| `trainstop-orchestrator` | `0` | `100` | `100` | `100` | `100` | `100` | `0` | `0` |
```

### tatragrammatron_stamps_latest_codex.json
Path: `codex/mailbox/tatragrammatron_stamps_latest_codex.json`

```json
{
  "_truncated": true,
  "note": "Full JSON omitted from packet; see relative_path in the repo.",
  "name": "tatragrammatron_stamps_latest_codex.json",
  "relative_path": "codex/mailbox/tatragrammatron_stamps_latest_codex.json",
  "bytes": 9172,
  "sha256": "9b57c6d50e227d6b25954d91418f66fb3aade3af14f5713f263db6e5570c6717"
}
```

### tatragrammatron_trend.json
Path: `codex/mailbox/tatragrammatron_trend.json`

```json
{
  "history": [
    {
      "generated_at": "2026-02-06T19:14:35.739901Z",
      "mode": "verify",
      "skills": 16,
      "avg_score": 100.0,
      "failed": 0
    },
    {
      "generated_at": "2026-02-06T19:14:53.993963+00:00",
      "mode": "verify",
      "skills": 16,
      "avg_score": 100.0,
      "failed": 0
    },
    {
      "generated_at": "2026-02-06T19:29:54.657999+00:00",
      "mode": "verify",
      "skills": 16,
      "avg_score": 100.0,
      "failed": 0
    },
    {
      "generated_at": "2026-02-06T20:21:36.594165+00:00",
      "mode": "verify",
      "skills": 16,
      "avg_score": 100.0,
      "failed": 0
    },
    {
      "generated_at": "2026-02-07T03:22:08.972354+00:00",
      "mode": "verify",
      "skills": 16,
      "avg_score": 100.0,
      "failed": 0
    },
    {
      "generated_at": "2026-02-07T03:23:07.043124+00:00",
      "mode": "verify",
      "skills": 16,
      "avg_score": 100.0,
      "failed": 0
    },
    {
      "generated_at": "2026-02-07T03:40:21.192011+00:00",
      "mode": "verify",
      "skills": 16,
      "avg_score": 100.0,
      "failed": 0
    },
    {
      "generated_at": "2026-02-07T03:51:10.352829+00:00",
      "mode": "verify",
      "skills": 16,
      "avg_score": 100.0,
      "failed": 0
    },
    {
      "generated_at": "2026-02-07T04:04:06.413250+00:00",
      "mode": "verify",
      "skills": 16,
      "avg_score": 100.0,
      "failed": 0
    },
    {
      "generated_at": "2026-02-07T17:49:12.920005+00:00",
      "mode": "verify",
      "skills": 17,
      "avg_score": 100.0,
      "failed": 0
    }
  ]
}
```

### mailbox_manifest.json
Path: `codex/mailbox/mailbox_manifest.json`

```json
{
  "schema_version": 2,
  "mailbox": "codex/mailbox",
  "generated_on": "2026-02-07T20:19:58.510423+00:00",
  "manifest_file": "mailbox_manifest.json",
  "active": {
    "md": [
      "CLAUDE_RUNBOOK_MATRIX.md",
      "HF_GEMMA_PROBE.md",
      "KISS_PARITY_BRIEF_2026_02_06.md",
      "MAILBOX_CURRENT_STATE.md",
      "QUEUE_2026_02_07.md",
      "SESSION_CHRONICLE_2026_02_07.md",
      "SESSION_CONTEXT_APPENDIX_2026_02_06.md",
      "SESSION_CONTEXT_CHRONICLE_2026_02_06.md",
      "SKILLS_PARITY_DISCREPANCY_2026_02_06.md",
      "TATRAGRAMMATRON_SUMMARY_LATEST_CODEX.md",
      "TETRAGRAMMATON_PACKET.md",
      "TETRAGRAMMATON_PROGRESS_2026_02_06.md",
      "TOOLCHAIN_DOCTOR_LATEST.md",
      "TOOLCHAIN_DOCTOR_REPORT_2026_02_07_174714.md",
      "TOOLCHAIN_DOCTOR_REPORT_2026_02_07_180524.md",
      "TOOLCHAIN_DOCTOR_REPORT_2026_02_07_180604.md",
      "TOOLCHAIN_DOCTOR_REPORT_2026_02_07_194657.md"
    ],
    "json": [
      "META_POLISHER_VALIDATION_SUMMARY.json",
      "claude_skill_audit_2026_02_07.json",
      "hf_gemma_probe.json",
      "skills_parity_map_2026_02_06.json",
      "tatragrammatron_matrix_2026_02_07.json",
      "tatragrammatron_stamps_latest_codex.json",
      "tatragrammatron_trend.json"
    ]
  },
  "archive_count": 40,
  "archive_files": [
    "2026_02_07/e2e_matrix_claude_on_claude.json",
    "2026_02_07/e2e_matrix_claude_on_codex.json",
    "2026_02_07/e2e_matrix_codex_on_claude.json",
    "2026_02_07/e2e_matrix_codex_on_codex.json",
    "2026_02_07/e2e_matrix_compare_summary.json",
    "2026_02_07/MAILBOX_CURRENT_STATE_2026_02_06.md",
    "2026_02_07/tatragrammatron_stamps_2026_02_06.json",
    "2026_02_07/tatragrammatron_stamps_2026_02_07.json",
    "2026_02_07/tatragrammatron_stamps_2026_02_07_auto_on_claude.json",
    "2026_02_07/tatragrammatron_stamps_2026_02_07_claude.json",
    "2026_02_07/tatragrammatron_stamps_2026_02_07_claude_contract_on_codex.json",
    "2026_02_07/tatragrammatron_stamps_2026_02_07_claude_v2.json",
    "2026_02_07/tatragrammatron_stamps_2026_02_07_codex.json",
    "2026_02_07/tatragrammatron_stamps_2026_02_07_codex_on_claude.json",
    "2026_02_07/tatragrammatron_stamps_2026_02_07_codex_on_codex.json",
    "2026_02_07/tatragrammatron_stamps_2026_02_07_codex_v3.json",
    "2026_02_07/tatragrammatron_stamps_2026_02_07_full_codex.json",
    "2026_02_07/tatragrammatron_stamps_2026_02_07_v2.json",
    "2026_02_07/TATRAGRAMMATRON_SUMMARY_2026_02_06.md",
    "2026_02_07/TATRAGRAMMATRON_SUMMARY_2026_02_07.md",
    "2026_02_07/TATRAGRAMMATRON_SUMMARY_2026_02_07_AUTO_ON_CLAUDE.md",
    "2026_02_07/TATRAGRAMMATRON_SUMMARY_2026_02_07_CLAUDE.md",
    "2026_02_07/TATRAGRAMMATRON_SUMMARY_2026_02_07_CLAUDE_CONTRACT_ON_CODEX.md",
    "2026_02_07/TATRAGRAMMATRON_SUMMARY_2026_02_07_CLAUDE_V2.md",
    "2026_02_07/TATRAGRAMMATRON_SUMMARY_2026_02_07_CODEX.md",
    "2026_02_07/TATRAGRAMMATRON_SUMMARY_2026_02_07_CODEX_ON_CLAUDE.md",
    "2026_02_07/TATRAGRAMMATRON_SUMMARY_2026_02_07_CODEX_ON_CODEX.md",
    "2026_02_07/TATRAGRAMMATRON_SUMMARY_2026_02_07_CODEX_V3.md",
    "2026_02_07/TATRAGRAMMATRON_SUMMARY_2026_02_07_FULL_CODEX.md",
    "2026_02_07/TATRAGRAMMATRON_SUMMARY_2026_02_07_V2.md",
    "CLAUDE_RESPONSE_TRAIN_STOP_2026_02_05.md",
    "CLAUDE_SKILLS_SPEC_VALIDATION_2026_02_05.md",
    "EXECUTION_ORDER_RECAP_2026_02_05.md",
    "MAILBOX_CMD_POLICY_2026_02_05.md",
    "MAILBOX_CONSOLIDATED_2026_02_05.md",
    "SESSION_HANDOFF_2026_02_05_PARITY_DELTA.md",
    "skill_audit_claude_2026_02_05.json",
    "skill_audit_codex_2026_02_05.json",
    "TRAIN_STOP_AUDIT_PRE_SEND_2026_02_05.md",
    "TRAIN_STOP_HANDOFF_CONSOLIDATED_2026_02_05.md"
  ]
}
```

## Scribe Log

- 2026-02-06T20:19:32.082083+00:00: sources changed
- 2026-02-06T20:21:36.307795+00:00: sources changed
- 2026-02-07T03:23:20.820138+00:00: sources changed
- 2026-02-07T03:40:27.038476+00:00: sources changed
- 2026-02-07T03:51:34.782705+00:00: sources changed
- 2026-02-07T04:04:20.101320+00:00: sources changed
- 2026-02-07T17:49:20.147955+00:00: sources changed
- 2026-02-07T17:56:02.140779+00:00: sources changed
- 2026-02-07T17:56:28.049419+00:00: sources changed
- 2026-02-07T18:07:03.583010+00:00: sources changed
- 2026-02-07T18:39:35.471327+00:00: sources changed
- 2026-02-07T18:48:48.548357+00:00: sources changed
- 2026-02-07T18:57:47.867973+00:00: sources changed
- 2026-02-07T19:04:47.955130+00:00: sources changed
- 2026-02-07T19:08:12.903738+00:00: sources changed
- 2026-02-07T19:37:14.838263+00:00: sources changed
- 2026-02-07T19:46:58.875749+00:00: sources changed
- 2026-02-07T20:19:58.518180+00:00: sources changed
