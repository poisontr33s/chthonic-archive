# Bun Segfault Bug Report

**Date:** 2026-02-01
**Reporter:** Triad (Claude Code + Codex + Gemini CLI)
**Status:** Mitigated, monitoring

---

## Crash Signature

```
panic(thread 17224): Segmentation fault at address 0x8
oh no: Bun has crashed. This indicates a bug in Bun, not your code.
```

**Bun Report URL:**
```
https://bun.report/1.3.7/wa1ba42621ijGukogCq+uq9C_____0ixgjDirp5iD66p5iDw81zjD2xy5iDgulgjD6i9m9C01iilD0r/u/C42uzvC+oyzsCghzxrCg+22sCy6o03BA2AQ
```

## Environment

| Component | Version |
|-----------|---------|
| Bun | 1.3.7 (crash) → 1.3.8 (upgraded) |
| Gemini CLI | 0.27.0-preview.3 |
| OS | Windows 11 |
| Platform | MSYS_NT-10.0-26200 |

## Crash Context

- **Session duration:** ~39 minutes (2350863ms)
- **RSS:** 0.72GB
- **Peak RSS:** 0.72GB
- **Page faults:** 1,083,347 (high)
- **User CPU:** 5406ms
- **Sys CPU:** 2796ms

## Analysis

- Segfault at `0x8` indicates null pointer dereference
- High page fault count suggests memory pressure during long session
- Crash occurred in Bun runtime, not Gemini CLI code
- Likely triggered by context discovery/file scanning over time

## Mitigation Applied

1. **Bun upgrade:** 1.3.7 → 1.3.8
2. **Gemini settings:** Added to `.gemini/settings.json`:
   ```json
   "context": {
     "discoveryMaxDirs": 50,
     "enableRecursiveFileSearch": true
   }
   ```

## Triage Steps (if recurrence)

1. `gemini -e none` — Test with extensions disabled
2. `gemini --ide=off` — Test without IDE integration
3. Reduce `discoveryMaxDirs` further if crash persists
4. File minimal repro with Bun team if reproducible

## References

- [codex/NEXT.md](../codex/NEXT.md) - Known Issues section
- [Bun Issue Tracker](https://github.com/oven-sh/bun/issues)
