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
