=== MAILBOX HANDOFF CMD POLICY ===
Do NOT use cmd.exe wrappers like `cmd /c ...` for mailbox operations.
Use PowerShell-native commands (`Rename-Item`, `Copy-Item`, `Remove-Item`) and `uv run` for Python scripts.

=== WORKAROUND ===
Preferred (PowerShell):
  Rename-Item -Path .claude/skills/gem-polisher -NewName .deprecated-gem-polisher
  Remove-Item -Recurse -Force .claude/skills/.deprecated-gem-polisher

If locked (PowerShell-only fallback):
  python -c "import os; os.remove('path/to/file')"
