---
name: scm-triage
description: "Audit git status, classify changes as signal/noise/transient, generate gitignore/exclude fixes, identify files needing relocation to canonical paths, and produce structured migration plans. Use when source control is noisy, before bulk commits, or when the codebase needs structural housekeeping."
allowed-tools: "Bash, Read, Write, Glob, Grep"
user-invocable: true
---

# SCM Triage — Source Control Noise Reduction & Codebase Structurization

Deterministic skill for silencing source control noise, classifying changes, and planning ANKH-aligned file relocations.

Arguments: `$ARGUMENTS` (optional: "audit" for read-only analysis, "fix" to apply gitignore/exclude changes, "plan" to generate migration manifest, "full" for audit+fix+plan)

## When to invoke

- Source control panel shows >20 items and you need to separate signal from noise
- After a daemon run produces hundreds of transient outputs
- Before a bulk commit to understand what's actually changed
- When the codebase has accumulated orphans or misplaced files
- User asks to "structurize," "clean up changes," or "silence the noise"

## Workflow

### Phase 1: SCM Audit (always runs)

1. Capture `git status --porcelain` and count by status code:
   - `??` = untracked, ` M` = unstaged modified, `M ` = staged modified
   - ` D` = unstaged deleted, `D ` = staged deleted, `A ` = staged added
2. Group changes by top-level directory
3. Classify each group into:
   - **SIGNAL**: Intentional changes (scripts, themes, skills, source code)
   - **NOISE**: Transient outputs (daemon reports, classifications, temp fixtures, cache)
   - **GHOST**: Tracked files that were physically deleted (need `git rm --cached`)
   - **MAILBOX**: Agent-produced deliverables awaiting integration

### Phase 2: Noise Suppression (runs with "fix" or "full")

4. For NOISE files: propose `.gitignore` or `.git/info/exclude` additions
   - Repo-wide transients → `.gitignore` (after the appropriate `!dir/**` negation)
   - Local-only noise → `.git/info/exclude`
5. For GHOST files: run `git rm --cached` to clear from index
6. Apply changes and verify with `git status --porcelain | Measure-Object -Line`

### Phase 3: Migration Plan (runs with "plan" or "full")

7. Scan for files outside canonical locations per ANKH structure:
   - `scripts/` — tools and automation
   - `extensions/` — VS Code extension code
   - `game/` — cRPG content
   - `.temple/` — protocols, methodology, handoffs
   - `claude/`, `codex/`, `gemini/` — agent lanes
   - `dumpster-dive/` — intake, siphon, archive
   - `assets/` — static resources
   - `src/` — Rust/Vulkan source
   - `mas_mcp/` — Python MCP backend
8. Identify files with `@SID` headers that don't match their filesystem location
9. Produce `claude/mailbox/SCM_TRIAGE_PLAN.json` with migration actions:
   ```json
   {
     "generated": "<ISO timestamp>",
     "audit": {
       "total_changes": 0,
       "signal": [],
       "noise": [],
       "ghost": [],
       "mailbox": []
     },
     "noise_fixes": {
       "gitignore_additions": [],
       "exclude_additions": [],
       "ghost_removals": []
     },
     "migrations": [
       {
         "file": "<current path>",
         "target": "<canonical path>",
         "reason": "<why it should move>",
         "sid": "<@SID if found>"
       }
     ]
   }
   ```

## Invariants

- NEVER delete files. Relocations use `git mv` (preserves history).
- GHOST cleanup only removes from index, not from disk.
- Noise suppression rules respect the `.gitignore` negate-all pattern (`*` → `!dir/**` → `dir/subexclude/`).
- Exclusion rules placed AFTER their parent `!dir/**` allow-all negation (last-match-wins).
- Local-only exclusions go in `.git/info/exclude`, never committed.
- Migration plan is written to mailbox for review before execution.
- One top-level directory per audit pass. Full codebase = multiple passes.

## Integration

| Companion Skill | Relationship |
|----------------|-------------|
| `artifact-upcycle` | Upcycle individual files identified by triage |
| `overnight-archaeology` | Read daemon reports that feed triage classification |
| `git-snapshot` | Snapshot state before/after triage operations |
| `script-envelope` | Standardize headers on scripts identified by triage |

## Backing Script

`scripts/scm_triage.py` — Automated audit and plan generation. Run via:

```powershell
uv run scripts/scm_triage.py              # Audit only (read-only)
uv run scripts/scm_triage.py --fix        # Audit + apply noise fixes
uv run scripts/scm_triage.py --plan       # Audit + generate migration plan
uv run scripts/scm_triage.py --full       # All phases
uv run scripts/scm_triage.py --dry-run    # Preview all changes without applying
```

## Cross-Flavor Compatibility
- Codex flavor: requires `agents/openai.yaml` and `assets/` with SVG icons.
- Claude flavor: requires `SKILL.md` with valid frontmatter (`name`, `description`), optional `allowed-tools`.
