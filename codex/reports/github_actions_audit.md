# GitHub Actions Audit (MCP/GH)

Date: 2026-02-04
Repo: poisontr33s/chthonic-archive
Source: GitHub API via gh (MCP fallback)

## Current Workflow Inventory (11 total)

### Repo-managed (YAML in .github/workflows)
- Claude Code (.github/workflows/claude.yml) — **active**
- Claude Code Review (.github/workflows/claude-code-review.yml) — **disabled_manually**
- 🔀 Gemini Dispatch (.github/workflows/gemini-dispatch.yml) — **active**
- ▶️ Gemini Invoke (.github/workflows/gemini-invoke.yml) — **disabled_manually**
- 🔎 Gemini Review (.github/workflows/gemini-review.yml) — **disabled_manually**
- 📋 Gemini Scheduled Issue Triage (.github/workflows/gemini-scheduled-triage.yml) — **disabled_manually**
- 🔀 Gemini Triage (.github/workflows/gemini-triage.yml) — **disabled_manually**
- Validate Shell Probe (.github/workflows/validate-probe.yml) — **disabled_manually**

### Dynamic/Managed by GitHub Apps (not in repo)
- Copilot code review (dynamic/copilot-pull-request-reviewer/...) — **active**
- Copilot coding agent (dynamic/copilot-swe-agent/...) — **active**
- Dependabot Updates (dynamic/dependabot/...) — **active**

## Noise Sources (from recent runs)
- Gemini Scheduled Issue Triage was firing hourly (historical runs); now disabled.
- Validate Shell Probe failures were triggered on push; now disabled.
- Copilot coding agent & Copilot code review continue to run via GitHub App.

## Why you see “nested” runners
- Each workflow can spawn multiple jobs per run (for PR/comment events).
- Dynamic workflows create extra runs that are not controlled by repo YAML.

## Target State (explicit-only)
- Keep only:
  - Claude Code (runs on explicit @claude by trusted user)
  - Gemini Dispatch (runs on explicit @gemini-cli by trusted user)
- Disable all other YAML workflows (already done).
- Disable GitHub App workflows (Copilot + Dependabot) via GitHub UI.

## Actions Required in GitHub UI
These **cannot** be disabled from repo YAML or API.

1) Disable Copilot code review + Copilot coding agent
   - Repo → Settings → Copilot (or Code review / Copilot)
   - Turn off “Copilot code review” and “Copilot coding agent”

2) Disable Dependabot Updates
   - Repo → Settings → Code security and analysis
   - Turn off Dependabot alerts/updates as desired

## Verification Checklist
- Actions list shows only:
  - Claude Code (active)
  - Gemini Dispatch (active)
  - Dynamic workflows disabled (Copilot/Dependabot)
- No new scheduled triage runs appear.

---
If you want, I can also:
- disable Claude/Gemini on PR triggers entirely (only issue comments), or
- re-enable any workflow on demand.
