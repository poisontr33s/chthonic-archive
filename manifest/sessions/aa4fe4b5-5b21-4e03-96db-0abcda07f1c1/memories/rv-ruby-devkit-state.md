# rv ruby DevKit install state — 2026-04-22

## Current state
- `ruby-4.0.2` DELETED (rv ruby uninstall, terminal 52d21ea9)
- `ruby-4.0.3` ACTIVE (sole installed, `*` default)
- `rv r ridk install 1 2 3` RUNNING — correct invocation
  - MSYS2 base installed into `ruby-4.0.3/msys64` ✅
  - Keyring signed, trustdb built ✅
  - pacman phase 1 (Syu core) RUNNING as of last poll

## Lesson burned in
- NEVER use bare `ridk` — it resolves via PATH, may hit a different version's msys64
- ALWAYS use `rv r ridk <cmd>` — routes through rv's runtime, targets active version's own msys64
- Repo toolchain rule: `rv r ridk` not `ridk`

## DONE — 2026-04-22
`rv r ridk version` output confirmed:
  ruby 4.0.3 @ ruby-4.0.3 ✅
  msys2 @ ruby-4.0.3\msys64 ✅ (correct, rv-owned path)
  cc: gcc 15.2.0 ✅
  sh: GNU bash 5.3.9 ✅
