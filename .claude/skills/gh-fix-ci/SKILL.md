---
name: gh-fix-ci
description: Debug and fix failing GitHub PR checks via GitHub Actions. Inspect checks and logs with `gh`, summarize failure context, draft a fix plan, implement after explicit approval. External providers (e.g. Buildkite) are out of scope—report the details URL only.
allowed-tools: "Read, Write, Glob, Grep, Bash"
user-invocable: true
---
# Gh Pr Checks Plan Fix

## Overview

Locate failing PR checks via `gh`, fetch GitHub Actions logs, summarize the failure snippet, propose a fix plan, implement after explicit approval.
- Use the `create-plan` skill if available; otherwise draft a concise plan inline and request approval before implementing.

Prereq: authenticate via `gh auth login`, confirm with `gh auth status` (repo + workflow scopes required).

## Inputs

- `repo`: path inside the repo (default `.`)
- `pr`: PR number or URL (optional; defaults to current branch PR)
- `gh` authentication for the repo host

## Quick start

- `python "<path-to-skill>/scripts/inspect_pr_checks.py" --repo "." --pr "<number-or-url>"`
- Add `--json` for machine-friendly output.

## Workflow

1. Verify gh authentication.
   - Run `gh auth status` in the repo.
   - If unauthenticated, instruct the user to run `gh auth login` (repo + workflow scopes) before proceeding.
2. Resolve the PR.
   - Prefer the current branch PR: `gh pr view --json number,url`.
   - If the user specifies a PR number or URL, use it directly.
3. Inspect failing checks (GitHub Actions only).
   - Run the bundled script (handles gh field drift and job-log fallbacks):
     - `python "<path-to-skill>/scripts/inspect_pr_checks.py" --repo "." --pr "<number-or-url>"`
     - Add `--json` for machine-friendly output.
   - Manual fallback:
     - `gh pr checks <pr> --json name,state,bucket,link,startedAt,completedAt,workflow`
       - If a field is rejected, rerun with the available fields reported by `gh`.
     - For each failing check, extract the run id from `detailsUrl` and run:
       - `gh run view <run_id> --json name,workflowName,conclusion,status,url,event,headBranch,headSha`
       - `gh run view <run_id> --log`
     - If the run is still in progress, fetch job logs directly:
       - `gh api "/repos/<owner>/<repo>/actions/jobs/<job_id>/logs" > "<path>"`
4. Scope non-GitHub Actions checks.
   - If `detailsUrl` is not a GitHub Actions run, label it as external and only report the URL.
   - Do not attempt Buildkite or other providers; keep the workflow lean.
5. Summarize failures for the user.
   - Provide the failing check name, run URL, and a concise log snippet.
   - Call out missing logs explicitly.
6. Create a plan.
   - Use the `create-plan` skill to draft a concise plan and request approval.
7. Implement after approval.
   - Apply the approved plan, summarize diffs/tests, open a PR or report completion.
8. Recheck status.
   - After changes, re-run the relevant tests and `gh pr checks` to confirm.

## Address PR Review Comments (absorbed from gh-address-comments)

When the goal is to address review/issue comments rather than CI failures:

1. **Fetch comments**: Run `python "<path-to-skill>/scripts/fetch_comments.py"` (or the gh-address-comments version if bundled separately) to list all review threads.
2. **Triage**: Number each thread, summarize the required fix, present to the user.
3. **User selects**: User picks which numbered comments to address.
4. **Apply fixes**: Implement changes for the selected comments, same approval flow as CI fixes.
5. **Recheck**: `gh pr checks` + confirm the review threads are resolved.

Auth and PR resolution use the same prereqs as the CI workflow above.

## Bundled Resources

### scripts/inspect_pr_checks.py

Fetch failing PR checks, pull GitHub Actions logs, and extract a failure snippet. Exits non-zero when failures remain so it can be used in automation.

Usage examples:
- `python "<path-to-skill>/scripts/inspect_pr_checks.py" --repo "." --pr "123"`
- `python "<path-to-skill>/scripts/inspect_pr_checks.py" --repo "." --pr "https://github.com/org/repo/pull/123" --json`
- `python "<path-to-skill>/scripts/inspect_pr_checks.py" --repo "." --max-lines 200 --context 40`

<!-- @POLISHED: 2026-02-05 -->


## Cross-Flavor Compatibility
- Codex flavor: requires `agents/openai.yaml` and `assets/` with SVG icons.
- Claude flavor: requires `SKILL.md` with valid frontmatter (`name`, `description`), optional `allowed-tools`.
- For shared audits use: `python scripts/skill_audit.py --flavor codex --root .codex/skills` and `python scripts/skill_audit.py --flavor claude --root .claude/skills`.



