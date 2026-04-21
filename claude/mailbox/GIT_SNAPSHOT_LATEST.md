---
type: git-snapshot
from: git-snapshot-tool
to: claude
created: 2026-04-21T16:25:27.587361+00:00
priority: low
scope: session-resumption
---

# Git Snapshot — 2026-04-21

**Branch:** main
**HEAD:** 7772a9c0
**Remote:** https://github.com/poisontr33s/chthonic-archive.git
**Clean:** no

## Recent Commits (last 6)

- 7772a9c0 roulette(T2): theme-sync.ps1 — glob-primary dst discovery; -VerifyOnly flag; exit 1 on hash mismatch; src-missing skip guard
- 05ac3081 roulette(T2): theme_contrast_audit.py — sys.path.insert guard; exit code docstring; --emit-junit JUnit XML output
- 336f26d1 roulette(T1): desktop-clone-state.ps1 — pre-export size estimate + disk space guard; [switch]$ExcludeGit (robocopy /XD .git + git bundle create)
- df2d4e9b roulette(T1): claude_ide.ps1 — backup .mcp.json.bak before write; ConvertFrom-Json validation after write; verify-mcp subcommand
- db449631 Refactor code structure for improved readability and maintainability
- ac7366f2 chore(docs): update various instruction files for clarity and consistency; add new Pattern Nursery documentation

## Today's Velocity (last 24h)

6 commits

- 7772a9c0 roulette(T2): theme-sync.ps1 — glob-primary dst discovery; -VerifyOnly flag; exit 1 on hash mismatch; src-missing skip guard
- 05ac3081 roulette(T2): theme_contrast_audit.py — sys.path.insert guard; exit code docstring; --emit-junit JUnit XML output
- 336f26d1 roulette(T1): desktop-clone-state.ps1 — pre-export size estimate + disk space guard; [switch]$ExcludeGit (robocopy /XD .git + git bundle create)
- df2d4e9b roulette(T1): claude_ide.ps1 — backup .mcp.json.bak before write; ConvertFrom-Json validation after write; verify-mcp subcommand
- db449631 Refactor code structure for improved readability and maintainability
- ac7366f2 chore(docs): update various instruction files for clarity and consistency; add new Pattern Nursery documentation

## Working Tree

    M .github/agents/pentea.agent.md
     M claude/mailbox/SCRIPTS_ROULETTE.md
     M package.json
     M scripts/api_key_gap_report.ps1
     M scripts/api_pool.ps1
     M scripts/api_pool_persist_user_env.ps1
     M scripts/chthonic-xp.ps1
     M scripts/chthonic.ps1
     M scripts/claudine.ps1
     M scripts/fortify_terminal.ps1
     M scripts/gemini-cli-wrapper.ps1
     M scripts/git_snapshot.py
     M scripts/lib/poe_auth.py
     M scripts/lib/ssot_paths.py
     M scripts/mcp-filesystem.ts
     M scripts/nightly-scheduled.ps1
     M scripts/pause_agents.ps1
     M scripts/polyglot_env.ps1
     M scripts/probe_toolchain_path.ps1
     M scripts/run_archaeology.ps1
    ?? claude/mailbox/GIT_SNAPSHOT_LATEST.md
    ?? claude/mailbox/ROULETTE_STEWARD.md
    ?? codex/mailbox/API_KEY_ENV_TEMPLATE_20260421T154124Z.env
    ?? codex/mailbox/API_KEY_ENV_TEMPLATE_20260421T154126Z.env
    ?? codex/mailbox/API_KEY_GAP_REPORT_20260421T154124Z.json
    ?? codex/mailbox/API_KEY_GAP_REPORT_20260421T154124Z.md
    ?? codex/mailbox/API_KEY_GAP_REPORT_20260421T154126Z.json
    ?? codex/mailbox/API_KEY_GAP_REPORT_20260421T154126Z.md
    ?? dumpster-dive/intake/toolchain-probe/probe_path_20260421_174128.log
    ?? dumpster-dive/intake/toolchain-probe/probed_path_20260421_174128.txt

## Uncommitted Diff Stats

    .github/agents/pentea.agent.md        | 134 +++++-----------------------------
     claude/mailbox/SCRIPTS_ROULETTE.md    |  60 +++++++++------
     package.json                          |   1 +
     scripts/api_key_gap_report.ps1        |  20 +++--
     scripts/api_pool.ps1                  |  14 ++++
     scripts/api_pool_persist_user_env.ps1 |  13 +++-
     scripts/chthonic-xp.ps1               |  32 +++++++-
     scripts/chthonic.ps1                  |  12 ++-
     scripts/claudine.ps1                  |  34 ++++-----
     scripts/fortify_terminal.ps1          |  16 +---
     scripts/gemini-cli-wrapper.ps1        |   6 ++
     scripts/git_snapshot.py               |  30 +++++---
     scripts/lib/poe_auth.py               |  23 +++++-
     scripts/lib/ssot_paths.py             |  22 ++++--
     scripts/mcp-filesystem.ts             |  14 +++-
     scripts/nightly-scheduled.ps1         |   4 +-
     scripts/pause_agents.ps1              |  22 ++++++
     scripts/polyglot_env.ps1              |  38 ++++++++--
     scripts/probe_toolchain_path.ps1      |  10 +++
     scripts/run_archaeology.ps1           |  28 ++++++-
     20 files changed, 321 insertions(+), 212 deletions(-)
