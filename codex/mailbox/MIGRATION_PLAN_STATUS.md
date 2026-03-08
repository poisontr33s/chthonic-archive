---
type: mailbox-report
created: 2026-03-08
subject: migration-plan-status
---

# Migration Plan Status

## Current Reading

[STAGE_1_MIGRATION_PLAN.md](/c:/Users/erdno/chthonic-archive/docs/STAGE_1_MIGRATION_PLAN.md) still describes Stage 1 as complete, but one of its assumed live surfaces is now gone:

- `.ankhrc` does **not** exist at repository root

That means the migration plan is historically useful, but its post-migration verification section is stale against the current tree.

## TODO Status

| Item | Status | Notes |
|---|---|---|
| `Create ankhrc_validator.py` | DONE | created as [ankhrc_validator.py](/c:/Users/erdno/chthonic-archive/scripts/ankhrc_validator.py) |
| Verify `.ankhrc` paths | BLOCKED BY CURRENT TREE | validator correctly reports `.ankhrc` missing |
| Investigate `github-copilot-chat-log` dependency | DONE | no such dependency exists in current repo |
| Build `session_extractor.py` | BLOCKED | no chat-log source material or format to target |

## `.ankhrc` Validator

Current behavior:

```powershell
uv run scripts/ankhrc_validator.py
```

Expected current output:

```text
status: missing
path: .ankhrc
message: No .ankhrc exists at repository root.
```

The script is therefore useful now as a guardrail if `.ankhrc` returns later, but it cannot validate a file that no longer exists.

## Session Extractor Feasibility

The Stage 1 plan proposed a `scripts/session_extractor.py` based on a root dependency named `github-copilot-chat-log`.

Current repo check:

- `github-copilot-chat-log` not present
- no equivalent `copilot chat log` source folder found at repo root
- only `.copilotignore` exists

Feasibility judgment:

- extractor architecture: feasible in principle
- implementation against this repo today: blocked by missing source artifact and unknown log schema

## Other Stale Assumptions

The migration plan also still assumes:

- `.ankhrc[migration_status]` is a live tracking surface
- root cleanup state is anchored to January 2026 counts

Those claims should now be treated as historical status, not live truth.
