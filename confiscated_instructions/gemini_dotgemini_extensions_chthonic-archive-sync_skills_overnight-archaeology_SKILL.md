---
name: overnight-archaeology
description: "Read the latest nightly daemon reports (debt scores + archaeology ore) from dumpster-dive/ and claude/mailbox/. Show status, findings, and launch commands. Does NOT run the daemons — zero API overhead. Use when asked about overnight findings, nightly status, debt scores, or archaeology digest."
---

# Overnight Nightly Status

Read-only. Reports on the latest nightly daemon outputs — zero API cost.

## Quick Read

```powershell
# Latest daemon report
Get-ChildItem "dumpster-dive/intake/overnight-daemon" -Directory | Sort-Object Name -Descending | Select-Object -First 1

# Latest archaeology ore
Get-ChildItem "dumpster-dive/intake/overnight-intelligence" -Directory -Filter "arch-*" | Sort-Object Name -Descending | Select-Object -First 1

# Latest LLM digest
Get-ChildItem "claude/mailbox" -Filter "ARCHAEOLOGY_DIGEST_*.md" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
```

## Launch Commands

```powershell
.\scripts\run_archaeology.ps1 -Background         # local-only, zero API
.\scripts\run_archaeology.ps1 -Background -WithHF  # with HF open-source LLM (free)
.\scripts\run_archaeology.ps1 -Background -WithLLM # with Gemini LLM quota
```

## Rules

- Does NOT run any daemon or LLM.
- Does NOT consume Gemini API quota.
- Does NOT modify any files.

## References

- Full spec: `.codex/skills/overnight-archaeology/SKILL.md`
- Launcher: `scripts/run_archaeology.ps1`
- Daemon: `scripts/overnight_daemon.ts`
- Archaeology: `meta-ide/copilot-sdk/overnight-archaeology.ts`
- `AGENT_COMMON.md`
