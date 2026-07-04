# Toolchain Doctor Report

- Generated: `2026-06-29T20:50:39.860035+00:00`
- bun: `False`
- uv: `False`
- rv: `True`
- apply: `False`

## rv (Ruby version manager)

- rv executable: `C:\Users\eldno\.cargo\bin\rvw.EXE`
- active ruby: `4.0.5`
- note: root `rv.lock` is R language package state, not Ruby rv state
- rv ruby list: `ok`
```text
┌──────────┬─────────────────────────────────────────────────────┐
│ Version  │ Installed                                           │
├──────────┼─────────────────────────────────────────────────────┤
│   2.4.10 │ [available]                                         │
│   2.5.9  │ [available]                                         │
│   2.6.10 │ [available]                                         │
│   2.7.8  │ [available]                                         │
│   3.0.7  │ [available]                                         │
│   3.1.7  │ [available]                                         │
│   3.2.11 │ [available]                                         │
│   3.3.11 │ [available]                                         │
│   3.4.9  │ [available]                                         │
│ * 4.0.5  │ ~\AppData\Roaming\rv\rubies\ruby-4.0.5\bin\ruby.exe │
├──────────┴─────────────────────────────────────────────────────┤
│ * Default version pinned by .ruby-version                      │
└────────────────────────────────────────────────────────────────┘
```
- stale installer dirs: none

### rv upgrade workflow
`rv ruby upgrade` does not exist. Correct flow:
```powershell
rv ruby install <new-version>   # e.g. ruby-4.0.3
rv ruby pin <new-version>
```
> **Windows PowerShell note:** `rv` may resolve to the built-in `Remove-Variable` alias.
> Use `rvw` if `rv` commands fail, or set up shell integration: `rv shell powershell`.

