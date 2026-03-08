---
type: mailbox-report
created: 2026-03-08
subject: skill-consolidation
---

# Skill Consolidation Proposal

## Executive Summary

- Non-system Codex skills audited: `27`
- Category split:
  - `ACTIVE`: `19`
  - `REDIRECT`: `5`
  - `STASHED`: `2`
  - `PROTOCOL`: `1`
- AGENTS cap: `<=15`
- Current delta: `+12`
- Proposed post-consolidation count: `15`

The immediate removals are the already-declared redirects and stashed shells. Hitting the cap requires a second pass that graduates a small set of generic wrappers out of the repo-local skill surface and folds a few narrow behaviors into broader existing lanes.

## Full Inventory

| Skill | Category | Scripts | Assets | Refs | Lines | Claude Mirror | Proposed Action |
|---|---:|---:|---:|---:|---:|---:|---|
| `api-manager` | ACTIVE | Y | Y | N | 54 | Y | Keep |
| `artifact-upcycle` | STASHED | Y | Y | Y | 13 | Y | Archive top-level skill; absorb note into `dumpster-upcycler` |
| `claude-skill-bridge` | REDIRECT | N | Y | N | 25 | Y | Archive; keep only redirect note in `skill-polisher` |
| `codekiller-remediation-gate` | ACTIVE | Y | Y | N | 89 | N | Keep |
| `codex-skill-bridge` | REDIRECT | N | Y | N | 25 | Y | Archive; keep only redirect note in `skill-polisher` |
| `conceptualize` | ACTIVE | N | Y | Y | 71 | Y | Keep |
| `corpse-reviver` | ACTIVE | Y | N | N | 228 | N | Keep |
| `decision-razor` | PROTOCOL | N | Y | N | 87 | Y | Remove as skill; fold into `AGENT_COMMON.md` / protocol docs |
| `dumpster-upcycler` | ACTIVE | Y | Y | N | 65 | N | Keep |
| `gh-address-comments` | REDIRECT | Y | Y | N | 15 | Y | Archive; `gh-fix-ci` is the surviving lane |
| `gh-fix-ci` | ACTIVE | Y | Y | N | 92 | Y | Keep |
| `gh-mcp-autonomy` | ACTIVE | N | Y | N | 54 | Y | Keep |
| `imagegen` | ACTIVE | Y | Y | Y | 185 | Y | Graduate to global skill + repo script direct use |
| `ingest-research` | ACTIVE | N | Y | N | 70 | Y | Merge into `mailbox-handoff` as ingest mode |
| `iron-maiden-runtime` | ACTIVE | Y | Y | Y | 52 | N | Keep |
| `mailbox-handoff` | ACTIVE | Y | Y | N | 246 | Y | Keep |
| `meta-polisher-validator` | REDIRECT | N | Y | N | 26 | Y | Archive; absorbed by `skill-polisher --mode verify` |
| `openai-docs` | ACTIVE | N | Y | N | 67 | Y | Keep |
| `postman` | REDIRECT | N | Y | N | 15 | Y | Archive; absorbed by `mailbox-handoff` |
| `python-header-canon` | ACTIVE | Y | Y | N | 53 | Y | Merge into `script-envelope` protocol + `skill-polisher` |
| `scm-triage` | ACTIVE | N | Y | N | 72 | Y | Keep |
| `script-envelope` | STASHED | Y | Y | Y | 11 | Y | Remove as skill; preserve rule in governance docs |
| `session-resumer` | REDIRECT | Y | Y | N | 15 | N | Archive; absorbed by `dumpster-upcycler` |
| `skill-polisher` | ACTIVE | Y | Y | Y | 65 | Y | Keep |
| `sora` | ACTIVE | Y | Y | Y | 164 | Y | Graduate to global skill + repo script direct use |
| `toolchain-doctor` | ACTIVE | Y | Y | Y | 46 | N | Keep |
| `trainstop-orchestrator` | ACTIVE | Y | Y | N | 98 | N | Keep |

## Merge Map

| Source | Action | Target | Signal To Preserve |
|---|---|---|---|
| `artifact-upcycle` | Archive top-level skill | `dumpster-upcycler` | Short “absorbed from artifact-upcycle” note and salvage provenance |
| `claude-skill-bridge` | Archive | `skill-polisher` | Cross-flavor bridge wording |
| `codex-skill-bridge` | Archive | `skill-polisher` | Codex bridge wording |
| `decision-razor` | De-skill to protocol | `AGENT_COMMON.md` / protocol docs | Anti-paralysis rule remains normative |
| `gh-address-comments` | Archive | `gh-fix-ci` | Review-comment triage examples |
| `imagegen` | Graduate to global skill | home skill + `scripts/image_gen.py` | Repo-local script path and env requirements |
| `ingest-research` | Merge | `mailbox-handoff` | Gemini / Deep Research ingest pathway and mailbox note output |
| `meta-polisher-validator` | Archive | `skill-polisher` | `--mode verify` wording |
| `postman` | Archive | `mailbox-handoff` | Mailbox command alias note |
| `python-header-canon` | Merge | `script-envelope` protocol + `skill-polisher` | Two-line Python header canon and remediation steps |
| `script-envelope` | De-skill to protocol | `AGENT_COMMON.md` / governance docs | SID / shebang / flags rule |
| `session-resumer` | Archive | `dumpster-upcycler` | Resume packet wording |
| `sora` | Graduate to global skill | home skill + `scripts/sora.py` | Repo-local script path and API key requirement |

## Post-Consolidation Count

Start: `27`

Remove or graduate:
- `artifact-upcycle`
- `claude-skill-bridge`
- `codex-skill-bridge`
- `decision-razor`
- `gh-address-comments`
- `imagegen`
- `ingest-research`
- `meta-polisher-validator`
- `postman`
- `python-header-canon`
- `script-envelope`
- `session-resumer`
- `sora`

Projected remaining top-level Codex skills: `14`

This lands below the repo cap while preserving all distinct execution lanes.

## Risks

1. `dumpster-upcycler` does not currently exist in `.claude/skills/`.
   - This affects the redirect targets for `artifact-upcycle` and `session-resumer`.
2. `imagegen` and `sora` already exist as global home skills.
   - Repo-local removal is safe only if the global home skills remain installed and continue to point at the bundled repo scripts.
3. `python-header-canon` is narrow but still operationally useful.
   - If merged, the exact two-line header rule must remain discoverable and not dissolve into vague policy text.
4. `ingest-research` is a true task shape, not just a prompt.
   - `mailbox-handoff` must absorb its output contract, not just its description.

## Claude-Side Redirect Verification

| Redirect Source | Target | Target In `.codex/skills/` | Target In `.claude/skills/` | Status |
|---|---|---:|---:|---|
| `artifact-upcycle` | `dumpster-upcycler` | Y | N | Missing Claude mirror |
| `claude-skill-bridge` | `skill-polisher` | Y | Y | OK |
| `codex-skill-bridge` | `skill-polisher` | Y | Y | OK |
| `gh-address-comments` | `gh-fix-ci` | Y | Y | OK |
| `meta-polisher-validator` | `skill-polisher` | Y | Y | OK |
| `postman` | `mailbox-handoff` | Y | Y | OK |
| `session-resumer` | `dumpster-upcycler` | Y | N | Missing Claude mirror |

## Tracked Skill Bytecode

Tracked `.pyc` under skills:

1. `.codex/skills/artifact-upcycle/scripts/__pycache__/resolve_directory_relationships.cpython-313.pyc`
2. `.codex/skills/codekiller-remediation-gate/scripts/__pycache__/codekiller_remediation_gate.cpython-313.pyc`
3. `.codex/skills/mailbox-handoff/scripts/__pycache__/mailbox_check.cpython-313.pyc`
4. `.codex/skills/script-envelope/scripts/__pycache__/script_envelope.cpython-313.pyc`
5. `.codex/skills/skill-polisher/scripts/__pycache__/polish_skill.cpython-313.pyc`

`.gitignore` currently lacks explicit `__pycache__/` and `*.pyc` coverage. Those additions are listed in [TRACKED_ARTIFACT_CLEANUP.md](/c:/Users/erdno/chthonic-archive/codex/mailbox/TRACKED_ARTIFACT_CLEANUP.md).
