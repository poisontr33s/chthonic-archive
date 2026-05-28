---
name: gh-mcp-autonomy
description: Autonomous GitHub MCP usage for repo/issue/PR data and synthesis. Use when the user asks for repo facts, recent commits, issues/PRs, contributors, or creative priming. Execute without menus and write results to the specified file.
metadata:
  short-description: "Autonomous GitHub MCP usage for repo/issue/PR data and synthesis."
---

# GH MCP Autonomy

## Overview
Execute GitHub MCP lookups (or `gh` CLI fallback) without menu prompts, then synthesize results into a structured artifact.

## Execution Contract
- **No menus**: execute the obvious path.
- **No permission loops**: trust the handoff and proceed.
- **Write outputs**: store results in the file specified by the task.

## Workflow
1. **Verify MCP config** in `.codex/config.toml` (`[mcp_servers.github]`).
2. **Attempt MCP first** for:
   - Repo identity, description, last update
   - Language composition
   - Recent commits (last 10)
   - Open issues/PRs
   - Contributors/activity pulse
3. **Fallback to `gh` CLI** if MCP is unavailable or fails:
   - Verify `gh auth status`
   - Use `gh repo view`, `gh issue list`, `gh pr list`, `gh api .../contributors`
4. **Synthesize** a concise, structured report:
   - Facts
   - Trajectory
   - Triad coordination potential
5. **Write** the report to the requested path.

## Output Template
Use this structure unless the user specifies otherwise:
1. Repository pulse (facts)
2. Creative synthesis (identity/trajectory)
3. Triad coordination potential
4. Next-step vector (1–2 concrete actions)

## Defaults & rules
- Prefer MCP; fallback to `gh` only on failure.
- Never ask for permissions if the handoff is explicit.
- Keep outputs concise and structured; no extra sections unless requested.

<!-- @POLISHED: 2026-02-05 -->

## Cross-Flavor Compatibility
- Codex flavor: requires `agents/openai.yaml` and `assets/` with SVG icons.
- Claude flavor: requires `SKILL.md` with valid frontmatter (`name`, `description`), optional `allowed-tools`.
- For shared audits use: `python scripts/skill_audit.py --flavor codex --root .codex/skills` and `python scripts/skill_audit.py --flavor claude --root .claude/skills`.


