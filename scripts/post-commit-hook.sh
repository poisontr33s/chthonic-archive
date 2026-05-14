#!/usr/bin/env bash
# @SID: POST_COMMIT_COMBINED_V1
# Chthonic Archive — combined post-commit hook (source)
# Installed to .git/hooks/post-commit by: bun run hooks:install
# (scripts/install-git-hooks.ps1 mirrors this content)
#
# Two concerns in priority order:
#
# 1. AUTO-PUSH (every commit, always fires)
#    Pushes current branch to its upstream. Replaces VS Code's unreliable
#    git.postCommitCommand:"sync" setting with a tool-agnostic git hook.
#    Works from VS Code, Copilot, terminal, any commit path.
#
# 2. PENTEA-NEXT DISPATCH (only when commit has 'Pentea-Next: <id>' trailer)
#    Preserves the existing T3 automation: dispatches the next queue task
#    to GitHub Copilot cloud agent via gh agent-task create. AFK-safe.
#
# Push failure does NOT block Pentea dispatch (it runs on the local commit
# regardless). Both behaviors are independent.

# ─── Part 1: Auto-push ──────────────────────────────────────────────────────

BRANCH=$(git symbolic-ref --quiet --short HEAD 2>/dev/null)
UPSTREAM=$(git rev-parse --abbrev-ref --symbolic-full-name "@{upstream}" 2>/dev/null)

if [ -z "$BRANCH" ]; then
    echo "[post-commit] detached HEAD — skipping push" >&2
elif [ -z "$UPSTREAM" ]; then
    echo "[post-commit] no upstream for $BRANCH — skipping push" >&2
else
    echo "[post-commit] pushing $BRANCH -> $UPSTREAM ..." >&2
    git push origin "$BRANCH" >&2
    if [ $? -eq 0 ]; then
        echo "[post-commit] push succeeded" >&2
    else
        echo "[post-commit] push failed — local commit still landed; run 'git push' after fixing the underlying issue" >&2
    fi
fi

# ─── Part 2: Pentea-Next dispatch (conditional) ─────────────────────────────

NEXT_TASK=$(git log --format="%B" -1 | grep -oP '(?<=^Pentea-Next: ).*$' | head -1)

if [ -z "$NEXT_TASK" ] || [ "$NEXT_TASK" = "none" ] || [ "$NEXT_TASK" = "DONE" ]; then
    exit 0
fi

# Verify gh CLI is available
if ! command -v gh >/dev/null 2>&1; then
    echo "[pentea-hook] gh CLI not found — skipping cloud dispatch for: $NEXT_TASK" >&2
    exit 0
fi

# Detect gh CLI version — agent-task requires v2.80.0+
GH_VERSION=$(gh --version 2>/dev/null | head -1 | grep -oP '\d+\.\d+\.\d+' | head -1)
GH_MAJOR=$(echo "$GH_VERSION" | cut -d. -f1)
GH_MINOR=$(echo "$GH_VERSION" | cut -d. -f2)

AGENT_TASK_AVAILABLE=0
if [ "$GH_MAJOR" -gt 2 ] || ([ "$GH_MAJOR" -eq 2 ] && [ "$GH_MINOR" -ge 80 ]); then
    AGENT_TASK_AVAILABLE=1
fi

# Auto-detect remote repo (owner/name)
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null)
if [ -z "$REPO" ]; then
    echo "[pentea-hook] gh repo view failed — not authenticated or not a GitHub remote. Skipping." >&2
    exit 0
fi

STEWARDESS_URL="https://github.com/${REPO}/blob/main/claude/mailbox/PENTEA_ROULETTE_STEWARDESS.md"

PROMPT="Execute Pentea queue task: ${NEXT_TASK}

Context: chthonic-archive autonomous queue system. Task spec in stewardess:
${STEWARDESS_URL}

Custom instructions: .github/copilot-instructions.md and AGENTS.md define all invariants.
Constraint: follow AGENT_COMMON.md. No file deletion without salvage (upcycle first).
Python: uv run <script>. JS/TS: bun. Rust: cargo (tools/ankh-forge/). Shell: pwsh.

Required git trailer on your commit:
  Pentea-Completed: ${NEXT_TASK}
  Pentea-Next: <next-id-or-none>
  Co-authored-by: Claudine Sin'claire <203248971+copilot-swe-agent@users.noreply.github.com>"

echo "[pentea-hook] Pentea-Next: ${NEXT_TASK} — dispatching to cloud agent..." >&2

if [ "$AGENT_TASK_AVAILABLE" -eq 1 ]; then
    gh agent-task create "$PROMPT" --repo "$REPO" &
    disown
    echo "[pentea-hook] gh agent-task create dispatched (gh v${GH_VERSION}). Check: gh copilot/agents" >&2
else
    echo "[pentea-hook] gh v${GH_VERSION} < 2.80.0 — creating issue fallback for: $NEXT_TASK" >&2
    ISSUE_TITLE="[Pentea-Queue] Execute task: ${NEXT_TASK}"
    gh issue create \
        --repo "$REPO" \
        --title "$ISSUE_TITLE" \
        --body "$PROMPT" \
        --label "pentea-queue" \
        --assignee "copilot-swe-agent[bot]" 2>/dev/null \
    || gh issue create \
        --repo "$REPO" \
        --title "$ISSUE_TITLE" \
        --body "$PROMPT" \
        --label "pentea-queue" 2>/dev/null \
    || echo "[pentea-hook] Issue creation also failed — check gh auth status" >&2
fi

exit 0
