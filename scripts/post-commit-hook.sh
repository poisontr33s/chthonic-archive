#!/usr/bin/env bash
# @SID: POST_COMMIT_PUSH_HOOK_V3
# Chthonic Archive — post-commit hook (source)
# Installed to .git/hooks/post-commit by: bun run hooks:install
#
# Two concerns, in order: record the commit on the trail, then auto-push the
# current branch to its upstream.
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

# --- trail: record the commit as a work event ---
# `git_commit` was already a scored kind (chthonic-xp.ps1: +5 on the artifact
# base = 15, and one achievement gates on three of them) with twelve examples in
# the whole history — all hand-written. Nothing emitted it, so a night of seven
# commits earned nothing, and the trail stayed 99.8% session_start/session_end.
# This is the one gate both lanes pass through: engine work and prose both
# terminate in a commit.
#
# Local-only append. No network, no dispatch, no external consequence — the
# no-commit-cloud-coupling rule from 2026-05-14 stands untouched.
#
# Placed before the branch/upstream checks on purpose: the work happened whether
# or not it can be pushed. Fail-open throughout; a broken emitter must never
# cost a commit.
emit_trail_event() {
    local root day dir ts secs ms at subj sha first files ins dels
    root=$(git rev-parse --show-toplevel 2>/dev/null) || return 0
    dir="$root/.chthonic/trail"
    mkdir -p "$dir" 2>/dev/null || return 0

    # One clock read, both stamps — ts is epoch-ms, at is UTC to the millisecond,
    # matching the pwsh emitter's contract exactly. The day file is named in
    # LOCAL time, also matching it; the two disagree near midnight, and that is
    # the existing convention rather than a bug to fix here.
    ts=$(date +%s%3N 2>/dev/null) || return 0
    secs=$(( ts / 1000 )); ms=$(( ts % 1000 ))
    at=$(date -u -d "@$secs" +%Y-%m-%dT%H:%M:%S 2>/dev/null) || return 0
    at=$(printf '%s.%03dZ' "$at" "$ms")
    day=$(date +%F)

    subj=$(git log -1 --pretty=%s 2>/dev/null | sed 's/\\/\\\\/g; s/"/\\"/g')
    sha=$(git log -1 --pretty=%h 2>/dev/null)
    first=$(git show --numstat --format= HEAD 2>/dev/null | head -1 | cut -f3 | sed 's/\\/\\\\/g; s/"/\\"/g')
    files=$(git show --numstat --format= HEAD 2>/dev/null | grep -c .)
    ins=$(git show --numstat --format= HEAD 2>/dev/null | awk '{a+=$1} END {printf "%d", a+0}')
    dels=$(git show --numstat --format= HEAD 2>/dev/null | awk '{d+=$2} END {printf "%d", d+0}')
    [ -n "$sha" ] || return 0

    printf '{"ts":%s,"at":"%s","type":"artifact","kind":"git_commit","p":2,"msg":"%s","file":"%s","data":{"commit":"%s","files":%s,"insertions":%s,"deletions":%s}}\n' \
        "$ts" "$at" "$subj" "$first" "$sha" "${files:-0}" "${ins:-0}" "${dels:-0}" \
        >> "$dir/$day.hot.ndjson" 2>/dev/null || return 0
    echo "[post-commit:trail] git_commit $sha recorded (${files:-0} file(s), +${ins:-0}/-${dels:-0})" >&2
}
emit_trail_event
# --- end trail ---

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
