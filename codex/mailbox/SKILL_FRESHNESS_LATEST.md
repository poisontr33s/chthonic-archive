# Skill Freshness Gate Report

- Generated: `2026-03-20T18:51:07.387388+00:00`
- Skills scanned: `28`
- Critical issues: `3`
- Warnings: `38`
- Status: `FAIL`

## Findings

- `api-manager` -> `PASS`
  - severity=`WARN` code=`missing_refresh_marker`: No @REFURBISHED/@POLISHED/refreshed date marker found.

- `artifact-upcycle` -> `PASS`
  - severity=`WARN` code=`missing_safety_contract_section`: Skill guidance does not define an explicit safety/guardrails contract.
  - severity=`WARN` code=`missing_refresh_marker`: No @REFURBISHED/@POLISHED/refreshed date marker found.

- `claude-skill-bridge` -> `PASS`
  - severity=`WARN` code=`missing_safety_contract_section`: Skill guidance does not define an explicit safety/guardrails contract.

- `codekiller-remediation-gate` -> `PASS`
  - no issues

- `codex-skill-bridge` -> `PASS`
  - severity=`WARN` code=`missing_safety_contract_section`: Skill guidance does not define an explicit safety/guardrails contract.

- `conceptualize` -> `PASS`
  - no issues

- `corpse-reviver` -> `PASS`
  - severity=`WARN` code=`missing_safety_contract_section`: Skill guidance does not define an explicit safety/guardrails contract.
  - severity=`WARN` code=`missing_refresh_marker`: No @REFURBISHED/@POLISHED/refreshed date marker found.

- `decision-razor` -> `FAIL`
  - severity=`WARN` code=`missing_safety_contract_section`: Skill guidance does not define an explicit safety/guardrails contract.
  - severity=`CRITICAL` code=`assume_permission`: Detected stale unsafe pattern `assume_permission` in skill guidance.
  - severity=`CRITICAL` code=`zero_questions_absolute`: Detected stale unsafe pattern `zero_questions_absolute` in skill guidance.
  - severity=`CRITICAL` code=`forgiveness_over_permission`: Detected stale unsafe pattern `forgiveness_over_permission` in skill guidance.

- `dumpster-upcycler` -> `PASS`
  - severity=`WARN` code=`missing_safety_contract_section`: Skill guidance does not define an explicit safety/guardrails contract.
  - severity=`WARN` code=`missing_refresh_marker`: No @REFURBISHED/@POLISHED/refreshed date marker found.

- `gh-address-comments` -> `PASS`
  - severity=`WARN` code=`missing_safety_contract_section`: Skill guidance does not define an explicit safety/guardrails contract.
  - severity=`WARN` code=`missing_refresh_marker`: No @REFURBISHED/@POLISHED/refreshed date marker found.

- `gh-fix-ci` -> `PASS`
  - severity=`WARN` code=`missing_safety_contract_section`: Skill guidance does not define an explicit safety/guardrails contract.

- `gh-mcp-autonomy` -> `PASS`
  - severity=`WARN` code=`missing_safety_contract_section`: Skill guidance does not define an explicit safety/guardrails contract.

- `imagegen` -> `PASS`
  - severity=`WARN` code=`missing_safety_contract_section`: Skill guidance does not define an explicit safety/guardrails contract.

- `ingest-research` -> `PASS`
  - severity=`WARN` code=`missing_safety_contract_section`: Skill guidance does not define an explicit safety/guardrails contract.
  - severity=`WARN` code=`missing_refresh_marker`: No @REFURBISHED/@POLISHED/refreshed date marker found.

- `iron-maiden-runtime` -> `PASS`
  - severity=`WARN` code=`missing_safety_contract_section`: Skill guidance does not define an explicit safety/guardrails contract.
  - severity=`WARN` code=`missing_refresh_marker`: No @REFURBISHED/@POLISHED/refreshed date marker found.

- `link-path-guard` -> `PASS`
  - severity=`WARN` code=`missing_safety_contract_section`: Skill guidance does not define an explicit safety/guardrails contract.
  - severity=`WARN` code=`missing_refresh_marker`: No @REFURBISHED/@POLISHED/refreshed date marker found.

- `mailbox-handoff` -> `PASS`
  - severity=`WARN` code=`missing_safety_contract_section`: Skill guidance does not define an explicit safety/guardrails contract.

- `meta-polisher-validator` -> `PASS`
  - severity=`WARN` code=`missing_safety_contract_section`: Skill guidance does not define an explicit safety/guardrails contract.

- `openai-docs` -> `PASS`
  - severity=`WARN` code=`missing_safety_contract_section`: Skill guidance does not define an explicit safety/guardrails contract.

- `postman` -> `PASS`
  - severity=`WARN` code=`missing_safety_contract_section`: Skill guidance does not define an explicit safety/guardrails contract.
  - severity=`WARN` code=`missing_refresh_marker`: No @REFURBISHED/@POLISHED/refreshed date marker found.

- `python-header-canon` -> `PASS`
  - severity=`WARN` code=`missing_safety_contract_section`: Skill guidance does not define an explicit safety/guardrails contract.
  - severity=`WARN` code=`missing_refresh_marker`: No @REFURBISHED/@POLISHED/refreshed date marker found.

- `scm-triage` -> `PASS`
  - severity=`WARN` code=`missing_safety_contract_section`: Skill guidance does not define an explicit safety/guardrails contract.

- `script-envelope` -> `PASS`
  - severity=`WARN` code=`missing_safety_contract_section`: Skill guidance does not define an explicit safety/guardrails contract.
  - severity=`WARN` code=`missing_refresh_marker`: No @REFURBISHED/@POLISHED/refreshed date marker found.

- `session-resumer` -> `PASS`
  - severity=`WARN` code=`missing_safety_contract_section`: Skill guidance does not define an explicit safety/guardrails contract.
  - severity=`WARN` code=`missing_refresh_marker`: No @REFURBISHED/@POLISHED/refreshed date marker found.

- `skill-polisher` -> `PASS`
  - severity=`WARN` code=`missing_safety_contract_section`: Skill guidance does not define an explicit safety/guardrails contract.
  - severity=`WARN` code=`missing_refresh_marker`: No @REFURBISHED/@POLISHED/refreshed date marker found.

- `sora` -> `PASS`
  - no issues

- `toolchain-doctor` -> `PASS`
  - severity=`WARN` code=`missing_refresh_marker`: No @REFURBISHED/@POLISHED/refreshed date marker found.

- `trainstop-orchestrator` -> `PASS`
  - severity=`WARN` code=`missing_safety_contract_section`: Skill guidance does not define an explicit safety/guardrails contract.
  - severity=`WARN` code=`missing_refresh_marker`: No @REFURBISHED/@POLISHED/refreshed date marker found.
