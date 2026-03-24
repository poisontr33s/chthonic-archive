#!/usr/bin/env bash
set -euo pipefail

BRANCH="fix/canonize-blessing-$(date +%F)"

git checkout -b "${BRANCH}"

targets=( "scripts" "mas_mcp" "ankh_atlas" ".codex" ".temple" )

for t in "${targets[@]}"; do
  if [ -d "${t}" ] || [ -f "${t}" ]; then
    echo "Applying canonize to ${t}"
    if [ "${t}" = "scripts" ]; then
      uv run scripts/canonize_blessing.py --apply --target "${t}"
    else
      uv run scripts/canonize_blessing.py --apply --recursive --target "${t}"
    fi
  else
    echo "Skipping ${t} (not found)"
  fi
done

# Show changes, commit if any
if git status --porcelain | grep -q .; then
  git add -A
  git commit -m "chore: apply canonize_blessing fixes (CI; uv runtime)"
  git push --set-upstream origin "${BRANCH}"
  echo "Pushed branch ${BRANCH}"
else
  echo "No changes detected; aborting branch creation"
  git checkout -
  git branch -D "${BRANCH}" || true
fi
