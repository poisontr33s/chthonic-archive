#!/bin/sh
# Chthonic Archive — pre-commit hook (source)
# Installed to .git/hooks/pre-commit by: bun run hooks:install
# Runs local CI checks (staged) via ci/run.ts in --heal mode: on a fixable failure it applies
# the registered narrow auto-fix, re-stages the originally-staged files, re-verifies, and lets
# the commit proceed — so the VS Code commit button self-heals without a terminal. Only
# genuinely-manual failures (no narrow auto-fix) still block. Bypass: git commit --no-verify.
# Absolute bun path ensures the VS Code git UI (stripped PATH) can find bun.

BUN="${HOME}/.bun/bin/bun"
if [ ! -x "$BUN" ]; then
  BUN="$(command -v bun 2>/dev/null || echo '')"
fi
if [ -z "$BUN" ]; then
  echo "[pre-commit] bun not found — skipping CI checks" >&2
  exit 0
fi

"$BUN" run "$(git rev-parse --show-toplevel)/ci/run.ts" --staged --heal
exit $?
