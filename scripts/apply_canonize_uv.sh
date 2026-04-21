#!/usr/bin/env bash
set -euo pipefail

# ---- flag parsing ----
DRY_RUN=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
  esac
done

# ---- pre-flight: require git remote origin ----
if ! git remote get-url origin >/dev/null 2>&1; then
  echo "ERROR: no git remote 'origin' configured -- cannot push" >&2
  exit 1
fi

BRANCH="fix/canonize-blessing-$(date +%F)"

if [ "$DRY_RUN" -eq 1 ]; then
  echo "[dry-run] would checkout branch: ${BRANCH}"
else
  git checkout -b "${BRANCH}"
fi

targets=( "scripts" "mas_mcp" "ankh_atlas" ".codex" ".temple" )

for t in "${targets[@]}"; do
  if [ -d "${t}" ] || [ -f "${t}" ]; then
    if [ "${t}" = "scripts" ]; then
      CMD="uv run scripts/canonize_blessing.py --apply --target ${t}"
    else
      CMD="uv run scripts/canonize_blessing.py --apply --recursive --target ${t}"
    fi
    if [ "$DRY_RUN" -eq 1 ]; then
      echo "[dry-run] would run: ${CMD}"
    else
      echo "Applying canonize to ${t}"
      if ! eval "${CMD}"; then
        echo "ERROR: canonize failed on ${t}" >&2
        exit 1
      fi
    fi
  else
    echo "Skipping ${t} (not found)"
  fi
done

# Show changes, commit if any
if [ "$DRY_RUN" -eq 1 ]; then
  echo "[dry-run] would commit and push branch: ${BRANCH}"
elif git status --porcelain | grep -q .; then
  git add -A
  git commit -m "chore: apply canonize_blessing fixes (CI; uv runtime)"
  git push --set-upstream origin "${BRANCH}"
  echo "Pushed branch ${BRANCH}"
else
  echo "No changes detected; aborting branch creation"
  git checkout -
  git branch -D "${BRANCH}" || true
fi
