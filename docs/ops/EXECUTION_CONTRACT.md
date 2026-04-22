# Execution Contract

<!--
@SID:           CONTRACT_EXECUTION_INVARIANTS
@Type:          Contract Document
@Context:       Governance / Environment Constraints
@SessionOrigin: SESSION_DOC_2026_01_05_SSOTIFICATION
@References:    CONTRACT_PROBE_ABI, DOC_PWSH_RULES
@ReferencedBy:  DOC_CLAUDE_MD_ROOT
-->

This repository uses explicit execution contracts.

**Invariants:**
- **Shell:** `pwsh` (PowerShell 7+)
- **Package manager:** `bun`
- **Environment probe:** `scripts/shell_capabilities.ps1` (ABI-stable)
- **Bash policy:** Git Bash only (`C:\Program Files\Git\bin\bash.exe`) - WSL is installed but NOT used
- **Bash invocation:** Explicit only via `bash -lc "..."` from pwsh or Git Bash terminal profile
- **No inference of tooling defaults**

All automation must follow these invariants.

---

## Rationale

These constraints prevent entropy from tooling assumptions.

- **Ground truth beats inference** - The probe reports reality
- **Contracts prevent drift** - Explicit > implicit
- **Shared across agents** - Claude Code, GH Copilot CLI, Gemini CLI

---

## Authority Hierarchy

1. **Runtime Reality** - OS + shell behavior
2. **Repository SSOT** - `.github/copilot-instructions.md`
3. **Session Bootstrap** - `docs/SESSION_BOOTSTRAP_SPEC.md`
4. **This Contract** - `docs/EXECUTION_CONTRACT.md`

---

**Version:** 1.0  
**Date:** 2026-01-05  
**Maintained by:** Repository governance framework
