---
type: waypoint
category: codex
created: 2026-02-01
updated: 2026-02-02
author: codex
description: Session waypoint and next steps for Codex workspace
---

# Codex Scope: Next Steps

## Purpose
Capture what’s next for Codex in this workspace without expanding the SSOT. This is a lightweight waypoint for future sessions.

## Current State (Stable)
- Auth: file-based (`C:/Users/erdno/.codex/auth.json`)
- Global config: auth-only (`C:/Users/erdno/.codex/config.toml`)
- Workspace config: behavior SSOT (`.codex/config.toml`) with sandbox locked to this repo
- Instructions: `AGENTS.md` (compact) and `.github/copilot-instructions.md` (SSOT)
- Gemini MCP: GitHub Server **Enabled** (PAT-based auth required; no OAuth flow)
- Chthonic-archive MCP: **Disabled/WIP** (intentionally removed from Gemini extension to avoid startup errors)
- PowerShell Profile: **Optimized** (OneDrive stub pattern, 65ms load time)
- UTF-8 Encoding: **Enabled** in profile (prevents Mojibake)

## Immediate Priority: Creative Priming (Execute Now)
**Objective:** Validate your GitHub MCP "superpowers" and align with Gemini's creative synthesis.
**Task:**
1.  **Connect:** Use GitHub MCP to inspect `poisontr33s/chthonic-archive`.
2.  **Synthesize:** Generate a "Creative Priming" report summarizing the repo's Identity ("Temple of Eternal Sadhana"), Core Stats (Languages), and Recent Evolution (Commits).
3.  **Constraint:** **DO NOT** offer options (1, 2, 3). **DO NOT** split into divergences. **JUST EXECUTE** the lookups and present the influx.

## Scope: What’s Next (When Ready)
1. **GitHub Tool Integration** (Completed)
   - `GITHUB_MCP_PAT` confirmed and MCP verified operational.
2. **Research ingestion** (Completed)
   - Deep Research outputs triaged to `dumpster-dive/archive/deep-research/`.
   - Windows/Bun encoding tips captured in `GEMINI.md`.
3. **Archive Pruning** (Completed)
   - Target met via `.geminiignore` configuration.
   - Excluded: `dumpster-dive/`, `build/`, `.venv/`.
   - Active documentation surface is now focused.
4. **Refinement pass**
   - Completed: structured artifact created.
   - See `codex/checkpoints/REFINEMENT_PASS_2026_02_01.md`.
5. **Creative Priming (GitHub MCP)**
   - Completed: `codex/reports/CREATIVE_PRIMING_2026_02_02.md`.
6. **Creative Batch (Artifacts)**
   - Completed: `codex/artifacts/` (5 files).
7. **Script-Envelope Canonicalization**
   - Use `codex/skills/script-envelope/` to normalize metadata envelopes (fixed field order + padded width).
8. **Skill Cleanup**
   - Removed `codex/skills/artifact-upcycle` (Repo redundancy eliminated).
   - Source of Truth: `~/.codex/skills/artifact-upcycle` (Verified Intelligent).


## Known Issues

### Gemini CLI Context Overflow (2026-02-02)
- **Symptom:** `400 INVALID_ARGUMENT` from Google Cloud Code API
- **Cause:** `ReadManyFiles` pulling 20,000+ files with broad globs
- **Recovery:** Start fresh session (no way to recover poisoned context)
- **Mitigation:** Protocol at `codex/protocols/GEMINI_CONTEXT_HYGIENE.md`
- **Rule:** Max 6 files per ReadManyFiles, explicit paths only

### Bun Segfault with Gemini CLI (2026-02-01)
- **Symptom:** Segfault at address `0x8` after ~39 min session, 1M+ page faults
- **Bun version:** 1.3.7 (crash), upgraded to 1.3.8
- **Mitigation applied:** `.gemini/settings.json` now has `discoveryMaxDirs: 50`
- **Status:** Monitoring post-upgrade
- **Bug report URL:** `https://bun.report/1.3.7/wa1ba42621ijGukogCq+uq9C_____0ixgjDirp5iD66p5iDw81zjD2xy5iDgulgjD6i9m9C01iilD0r/u/C42uzvC+oyzsCghzxrCg+22sCy6o03BA2AQ`

## Guardrails
- Do not alter working auth or sandbox configs without explicit instruction.
- Keep AGENTS.md compact; reference SSOT instead of copying it.
- Prefer PowerShell commands; avoid bash syntax on Windows.

## References
- `claude/SESSION_COMPRESSION_2026_02_01.md` (High-level summary)
- `claude/MCP_CONFIGURATION_LOG_2026_02_01.md` (Auth details)
- `AGENTS.md` (Updated with `gh-mcp-autonomy`)
- `.codex/config.toml`
- `.github/copilot-instructions.md`
- `claude-codex-gemini/triadic-session-context/OpenAI_Codex_Win11_Keyring_Auth_Resolution.md`
- `claude-codex-gemini/triadic-session-context/Session_20260131_Codex_Onboarding_Summary.md`
- `claude-codex-gemini/triadic-session-shared-0001.md`
- `claude-codex-gemini/triadic-session-shared-0002.md`
- `codex/reports/gemini_mcp_status_report.md`
- `codex/checkpoints/REFINEMENT_PASS_2026_02_01.md`
- `codex/reports/CREATIVE_PRIMING_2026_02_02.md`
- `codex/artifacts/`
- `codex/handoffs/SESSION_HANDOFF_2026_02_01_CLAUDE.md`
- `codex/checkpoints/SESSION_CHECKPOINT_2026_02_01.md`
- `claude/SESSION_HANDOFF_2026_02_01_TRIAD_GEMINI.md`
- `.gemini/TRIAD_SYNC_2026_02_01.md`
- `deep-research-documents/Gemini_CLI_Preview_Win11_Bun_vscode_insiders_deep_research_IMPLEMENTATION.md`
