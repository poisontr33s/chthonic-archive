#!/bin/sh
# Chthonic Archive — pre-commit hook (source)
# Installed to .git/hooks/pre-commit by: bun run hooks:install
# Runs local CI checks in staged mode: shebang, python-headers, sid-envelope.

bun run "$(git rev-parse --show-toplevel)/ci/run.ts" --staged
exit $?
