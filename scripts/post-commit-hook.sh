#!/usr/bin/env bash
# @SID: POST_COMMIT_PUSH_HOOK_V2
# Chthonic Archive — post-commit hook (source)
# Installed to .git/hooks/post-commit by: bun run hooks:install
#
# Single concern: auto-push current branch to its upstream after every commit.
#
# Replaces VS Code's git.postCommitCommand:"sync" setting which was
# unreliable on VS Code Insiders. Tool-agnostic — works regardless of
# whether the commit came from VS Code, Copilot, terminal, or any other path.
#
# Explicitly does NOT do cloud-agent dispatch. The previous version of
# this hook (combined with Pentea-Next: trailer parsing) connected commits
# to GitHub Copilot cloud agent via gh agent-task create. That coupling
# was removed 2026-05-14 — see memory/feedback_no_commit_cloud_coupling.md.
# Commits stay local-scoped events: they push to the user's remote, and
# that is the end of automated consequence. No issue creation, no PR
# dispatch, no agent-task fire. The user owns when to invoke external
# agents, not the commit itself.

BRANCH=$(git symbolic-ref --quiet --short HEAD 2>/dev/null)
UPSTREAM=$(git rev-parse --abbrev-ref --symbolic-full-name "@{upstream}" 2>/dev/null)

if [ -z "$BRANCH" ]; then
    echo "[post-commit] detached HEAD — skipping push" >&2
    exit 0
fi

if [ -z "$UPSTREAM" ]; then
    echo "[post-commit] no upstream for $BRANCH — skipping push" >&2
    exit 0
fi

# --- CI gate: pathfinder link-audit ---
# Runs even when commit used --no-verify (which only bypasses pre-commit).
# post-commit always fires, so agent lane commits get link validation here.
REPO_ROOT="$(git rev-parse --show-toplevel)"
echo "[post-commit:ci] pathfinder — checking tracked markdown ..." >&2
( cd "$REPO_ROOT" && bun run ci/run.ts --check pathfinder )
CI_EXIT=$?
if [ $CI_EXIT -ne 0 ]; then
    echo "" >&2
    echo "[post-commit:ci] ✗ pathfinder FAILED — push blocked" >&2
    echo "[post-commit:ci]   repair broken links, then: git push" >&2
    exit 0
fi
echo "[post-commit:ci] ✓ pathfinder clean" >&2
# --- end CI gate ---

echo "[post-commit] pushing $BRANCH -> $UPSTREAM ..." >&2
git push origin "$BRANCH" >&2
if [ $? -eq 0 ]; then
    echo "[post-commit] push succeeded" >&2
else
    echo "[post-commit] push failed — local commit still landed; run 'git push' after fixing the underlying issue" >&2
fi

exit 0
