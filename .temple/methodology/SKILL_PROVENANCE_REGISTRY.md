---
type: provenance-registry
created: 2026-02-26
scope: skill-system
implements: SKILL-HARDENING-3.0
---

# Skill Provenance Registry

Maps every non-active skill to where its value was deposited. Nothing deleted — only redirected, absorbed, or extracted.

## Redirect → Absorbed

| Skill | Absorbed Into | What Transferred | When |
|-------|---------------|------------------|------|
| claude-skill-bridge | skill-polisher | Claude audit CLI commands | SKILL-HARDENING-3.0 |
| codex-skill-bridge | skill-polisher | Codex audit CLI commands | SKILL-HARDENING-3.0 |
| meta-polisher-validator | skill-polisher `--mode verify` | 4-item validation checklist | SKILL-HARDENING-3.0 |
| gh-address-comments | gh-fix-ci | PR comment triage | SKILL-HARDENING-2.0 |
| postman | mailbox-handoff | Mailbox routing workflow | SKILL-HARDENING-2.0 |
| session-resumer (codex) | Codex session protocol | Session continuity | SKILL-HARDENING-2.0 |

## Stashed → Concept Extracted

| Skill | Concept Deposited To | What Extracted | When |
|-------|---------------------|----------------|------|
| decision-razor | AGENT_COMMON.md behavioral rule | Anti-paralysis heuristic: infer, execute, never ask | SKILL-HARDENING-2.0 |
| script-envelope | AGENT_COMMON.md envelope rule | SID/shebang/flags standard for all scripts | SKILL-HARDENING-2.0 |
| artifact-upcycle | dumpster-upcycler | Raw→structured conversion concept | SKILL-HARDENING-2.0 |
| sfa | docs/SFA_REFERENCE.md (if created) | Sister Ferrum Scoriae aesthetic reference | SKILL-HARDENING-2.0 |

## Formalized → Script Created

| Skill | Script | What Formalized | When |
|-------|--------|-----------------|------|
| git-snapshot | `scripts/git_snapshot.py` | Git state capture to mailbox | SKILL-HARDENING-3.0 |

## Verification

Run `uv run scripts/skill_health.py` to confirm all redirects/stashes are correctly classified.
Expected: 0 skills in the 5-6 band. All redirects score 1.0. All stashes score 2.0.
