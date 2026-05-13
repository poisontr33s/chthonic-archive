#!/bin/sh
# Chthonic Archive — pre-commit hook (source)
# Installed to .git/hooks/pre-commit by: bun run hooks:install
# Runs local CI checks in staged mode via ci/run.ts, including shebang and pathfinder.
# Absolute bun path ensures VS Code git UI (stripped PATH) can find it.

BUN="${HOME}/.bun/bin/bun"
if [ ! -x "$BUN" ]; then
  BUN="$(command -v bun 2>/dev/null || echo '')"
fi
if [ -z "$BUN" ]; then
  echo "[pre-commit] bun not found — skipping CI checks" >&2
  exit 0
fi

"$BUN" run "$(git rev-parse --show-toplevel)/ci/run.ts" --staged
exit $?
