#!/bin/sh
# Chthonic Archive — pre-commit hook (source)
# Installed to .git/hooks/pre-commit by: bun run hooks:install
# Blocks commits containing displaced shebangs in .ts files.

bun run "$(git rev-parse --show-toplevel)/scripts/shebang-guard.ts" --staged
exit $?
