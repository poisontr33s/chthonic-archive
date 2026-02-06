---
type: handoff
from: codex
to: codex
created: 2026-02-05
priority: high
---

# Mailbox Consolidated: Skill Envelope + Policy + Cross-Flavor State

## Scope
This single report replaces prior fragmented mailbox markdown logs and reflects the latest repository state.

## Script-Envelope State
- `script-envelope` now enforces open-sided box conventions (no right-edge `╗`, `╣`, `╝`, trailing `║`).
- Python canonical header is standardized and idempotent:
  - `#!/usr/bin/env python3`
  - `# -*- coding: utf-8 -*-`
- `script_envelope.py` supports:
  - `--normalize-python-header`
  - `--validate-python-prologue`
  - `--normalize-open-sided`
- Universal metadata sidecars are active via `scripts/envelope_sync.py`.

## Policy Contract Applied
- Python dependency SSOT is `pyproject.toml`.
- No inline Python script dependency blocks (`# /// script`) in repo scripts.
- Execution default: `uv run <script.py>`.
- Escape hatch: `uv run python <script.py>` only when explicitly required.
- No `cmd /c` wrappers.

## Audit Lane
- `scripts/run_cross_audit.ps1` now runs:
  1. Codex skill audit
  2. Claude skill audit
  3. Python policy check (`scripts/check_python_policy.py`)

## Inline JSON: Codex Skill Audit
```json
{
  "flavor": "codex",
  "root": ".codex\\skills",
  "results": [
    {
      "name": "artifact-upcycle",
      "score": 100,
      "issues": []
    },
    {
      "name": "claude-skill-bridge",
      "score": 100,
      "issues": []
    },
    {
      "name": "codex-skill-bridge",
      "score": 100,
      "issues": []
    },
    {
      "name": "conceptualize",
      "score": 100,
      "issues": []
    },
    {
      "name": "decision-razor",
      "score": 100,
      "issues": []
    },
    {
      "name": "gh-address-comments",
      "score": 100,
      "issues": []
    },
    {
      "name": "gh-fix-ci",
      "score": 100,
      "issues": []
    },
    {
      "name": "gh-mcp-autonomy",
      "score": 100,
      "issues": []
    },
    {
      "name": "imagegen",
      "score": 100,
      "issues": []
    },
    {
      "name": "mailbox-handoff",
      "score": 100,
      "issues": []
    },
    {
      "name": "meta-polisher-validator",
      "score": 100,
      "issues": []
    },
    {
      "name": "openai-docs",
      "score": 100,
      "issues": []
    },
    {
      "name": "python-header-canon",
      "score": 100,
      "issues": []
    },
    {
      "name": "script-envelope",
      "score": 100,
      "issues": []
    },
    {
      "name": "skill-polisher",
      "score": 100,
      "issues": []
    },
    {
      "name": "sora",
      "score": 100,
      "issues": []
    }
  ]
}
```

## Inline JSON: Claude Skill Audit
```json
{
  "flavor": "claude",
  "root": ".claude\\skills",
  "results": [
    {
      "name": "artifact-upcycle",
      "score": 100,
      "issues": []
    },
    {
      "name": "claude-skill-bridge",
      "score": 100,
      "issues": []
    },
    {
      "name": "codex-skill-bridge",
      "score": 100,
      "issues": []
    },
    {
      "name": "conceptualize",
      "score": 100,
      "issues": []
    },
    {
      "name": "decision-razor",
      "score": 100,
      "issues": []
    },
    {
      "name": "gh-address-comments",
      "score": 100,
      "issues": []
    },
    {
      "name": "gh-fix-ci",
      "score": 100,
      "issues": []
    },
    {
      "name": "gh-mcp-autonomy",
      "score": 100,
      "issues": []
    },
    {
      "name": "imagegen",
      "score": 100,
      "issues": []
    },
    {
      "name": "mailbox-handoff",
      "score": 100,
      "issues": []
    },
    {
      "name": "meta-polisher-validator",
      "score": 100,
      "issues": []
    },
    {
      "name": "openai-docs",
      "score": 100,
      "issues": []
    },
    {
      "name": "script-envelope",
      "score": 100,
      "issues": []
    },
    {
      "name": "skill-polisher",
      "score": 100,
      "issues": []
    },
    {
      "name": "sora",
      "score": 100,
      "issues": []
    }
  ]
}
```

## Inline JSON: Meta Polisher Validation
```json
{
  "ok": true,
  "checks": [
    {
      "name": "codex_skill_polisher",
      "ok": true,
      "detail": ".codex\\skills\\skill-polisher\\SKILL.md"
    },
    {
      "name": "claude_skill_polisher",
      "ok": true,
      "detail": ".claude\\skills\\skill-polisher\\SKILL.md"
    },
    {
      "name": "shared_audit",
      "ok": true,
      "detail": "scripts\\skill_audit.py"
    },
    {
      "name": "run_codex_hook",
      "ok": true,
      "detail": "scripts\\run_codex_polisher.ps1"
    },
    {
      "name": "run_claude_hook",
      "ok": true,
      "detail": "scripts\\run_claude_skill_polisher.ps1"
    },
    {
      "name": "run_cross_hook",
      "ok": true,
      "detail": "scripts\\run_claude_cross_polish.ps1"
    },
    {
      "name": "codex_cross_flavor_section",
      "ok": true,
      "detail": "Cross-Flavor Audit section"
    },
    {
      "name": "claude_cross_flavor_section",
      "ok": true,
      "detail": "Cross-Flavor Audit section"
    },
    {
      "name": "codex_references_shared_audit",
      "ok": true,
      "detail": "scripts/skill_audit.py referenced"
    },
    {
      "name": "claude_references_shared_audit",
      "ok": true,
      "detail": "scripts/skill_audit.py referenced"
    }
  ]
}
```

## Status
- Codex skills: 100% clean
- Claude skills: 100% clean
- Meta-polisher validation: pass
- Python policy check: pass

---

Report Hash: `MAILBOX_CONSOLIDATED_V2_2026_02_05`
