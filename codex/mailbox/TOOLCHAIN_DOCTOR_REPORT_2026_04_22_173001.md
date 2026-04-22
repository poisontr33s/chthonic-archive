# Toolchain Doctor Report

- Generated: `2026-04-22T17:30:01.323644+00:00`
- bun: `False`
- uv: `False`
- rv: `True`
- apply: `True`

## rv (Ruby version manager)

- active ruby: `3.4.9`
- rv ruby list: `ok`
```text
┌───────────────┬─────────────────────────────────────────────────────┐
│ Version       │ Installed                                           │
├───────────────┼─────────────────────────────────────────────────────┤
│   ruby-2.4.10 │ [available]                                         │
│   ruby-2.5.9  │ [available]                                         │
│   ruby-2.6.10 │ [available]                                         │
│   ruby-2.7.8  │ [available]                                         │
│   ruby-3.0.7  │ [available]                                         │
│   ruby-3.1.7  │ [available]                                         │
│   ruby-3.2.11 │ [available]                                         │
│   ruby-3.3.11 │ [available]                                         │
│ * ruby-3.4.9  │ ~\AppData\Roaming\rv\rubies\ruby-3.4.9\bin\ruby.exe │
│   ruby-4.0.3  │ ~\AppData\Roaming\rv\rubies\ruby-4.0.3\bin\ruby.exe │
├───────────────┴─────────────────────────────────────────────────────┤
│ * Default version pinned by .ruby-version                           │
└─────────────────────────────────────────────────────────────────────┘
```
- stale installer dirs: none

### rv upgrade workflow
`rv ruby upgrade` does not exist. Correct flow:
```powershell
rv ruby install <version>   # e.g. ruby-3.4.9
rv ruby pin <version>
```

