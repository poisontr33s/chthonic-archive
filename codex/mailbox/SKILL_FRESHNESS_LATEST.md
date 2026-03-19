# Skill Freshness Gate Report

- Generated: `2026-03-19T21:45:01.070321+00:00`
- Skills scanned: `28`
- Critical issues: `3`
- Warnings: `38`
- Status: `FAIL`

## Findings

- `api-manager` -> `PASS`
  - [WARN] missing_refresh_marker: No @REFURBISHED/@POLISHED/refreshed date marker found.

- `artifact-upcycle` -> `PASS`
  - [WARN] missing_safety_contract_section: Skill guidance does not define an explicit safety/guardrails contract.
  - [WARN] missing_refresh_marker: No @REFURBISHED/@POLISHED/refreshed date marker found.

- `claude-skill-bridge` -> `PASS`
  - [WARN] missing_safety_contract_section: Skill guidance does not define an explicit safety/guardrails contract.

- `codekiller-remediation-gate` -> `PASS`
  - no issues

- `codex-skill-bridge` -> `PASS`
  - [WARN] missing_safety_contract_section: Skill guidance does not define an explicit safety/guardrails contract.

- `conceptualize` -> `PASS`
  - no issues

- `corpse-reviver` -> `PASS`
  - [WARN] missing_safety_contract_section: Skill guidance does not define an explicit safety/guardrails contract.
  - [WARN] missing_refresh_marker: No @REFURBISHED/@POLISHED/refreshed date marker found.

- `decision-razor` -> `FAIL`
  - [WARN] missing_safety_contract_section: Skill guidance does not define an explicit safety/guardrails contract.
  - [CRITICAL] assume_permission: Detected stale unsafe pattern `assume_permission` in skill guidance.
  - [CRITICAL] zero_questions_absolute: Detected stale unsafe pattern `zero_questions_absolute` in skill guidance.
  - [CRITICAL] forgiveness_over_permission: Detected stale unsafe pattern `forgiveness_over_permission` in skill guidance.

- `dumpster-upcycler` -> `PASS`
  - [WARN] missing_safety_contract_section: Skill guidance does not define an explicit safety/guardrails contract.
  - [WARN] missing_refresh_marker: No @REFURBISHED/@POLISHED/refreshed date marker found.

- `gh-address-comments` -> `PASS`
  - [WARN] missing_safety_contract_section: Skill guidance does not define an explicit safety/guardrails contract.
  - [WARN] missing_refresh_marker: No @REFURBISHED/@POLISHED/refreshed date marker found.

- `gh-fix-ci` -> `PASS`
  - [WARN] missing_safety_contract_section: Skill guidance does not define an explicit safety/guardrails contract.

- `gh-mcp-autonomy` -> `PASS`
  - [WARN] missing_safety_contract_section: Skill guidance does not define an explicit safety/guardrails contract.

- `imagegen` -> `PASS`
  - [WARN] missing_safety_contract_section: Skill guidance does not define an explicit safety/guardrails contract.

- `ingest-research` -> `PASS`
  - [WARN] missing_safety_contract_section: Skill guidance does not define an explicit safety/guardrails contract.
  - [WARN] missing_refresh_marker: No @REFURBISHED/@POLISHED/refreshed date marker found.

- `iron-maiden-runtime` -> `PASS`
  - [WARN] missing_safety_contract_section: Skill guidance does not define an explicit safety/guardrails contract.
  - [WARN] missing_refresh_marker: No @REFURBISHED/@POLISHED/refreshed date marker found.

- `link-path-guard` -> `PASS`
  - [WARN] missing_safety_contract_section: Skill guidance does not define an explicit safety/guardrails contract.
  - [WARN] missing_refresh_marker: No @REFURBISHED/@POLISHED/refreshed date marker found.

- `mailbox-handoff` -> `PASS`
  - [WARN] missing_safety_contract_section: Skill guidance does not define an explicit safety/guardrails contract.

- `meta-polisher-validator` -> `PASS`
  - [WARN] missing_safety_contract_section: Skill guidance does not define an explicit safety/guardrails contract.

- `openai-docs` -> `PASS`
  - [WARN] missing_safety_contract_section: Skill guidance does not define an explicit safety/guardrails contract.

- `postman` -> `PASS`
  - [WARN] missing_safety_contract_section: Skill guidance does not define an explicit safety/guardrails contract.
  - [WARN] missing_refresh_marker: No @REFURBISHED/@POLISHED/refreshed date marker found.

- `python-header-canon` -> `PASS`
  - [WARN] missing_safety_contract_section: Skill guidance does not define an explicit safety/guardrails contract.
  - [WARN] missing_refresh_marker: No @REFURBISHED/@POLISHED/refreshed date marker found.

- `scm-triage` -> `PASS`
  - [WARN] missing_safety_contract_section: Skill guidance does not define an explicit safety/guardrails contract.

- `script-envelope` -> `PASS`
  - [WARN] missing_safety_contract_section: Skill guidance does not define an explicit safety/guardrails contract.
  - [WARN] missing_refresh_marker: No @REFURBISHED/@POLISHED/refreshed date marker found.

- `session-resumer` -> `PASS`
  - [WARN] missing_safety_contract_section: Skill guidance does not define an explicit safety/guardrails contract.
  - [WARN] missing_refresh_marker: No @REFURBISHED/@POLISHED/refreshed date marker found.

- `skill-polisher` -> `PASS`
  - [WARN] missing_safety_contract_section: Skill guidance does not define an explicit safety/guardrails contract.
  - [WARN] missing_refresh_marker: No @REFURBISHED/@POLISHED/refreshed date marker found.

- `sora` -> `PASS`
  - no issues

- `toolchain-doctor` -> `PASS`
  - [WARN] missing_refresh_marker: No @REFURBISHED/@POLISHED/refreshed date marker found.

- `trainstop-orchestrator` -> `PASS`
  - [WARN] missing_safety_contract_section: Skill guidance does not define an explicit safety/guardrails contract.
  - [WARN] missing_refresh_marker: No @REFURBISHED/@POLISHED/refreshed date marker found.
