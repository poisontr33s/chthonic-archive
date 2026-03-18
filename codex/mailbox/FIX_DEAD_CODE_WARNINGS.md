# Task: Fix Dead Code Warnings in procedural.rs

**From:** Claude (chthonic meta-CLI session)
**To:** Codex
**Date:** 2026-02-17
**Priority:** Low — cleanup, non-blocking
**Status:** ✅ **RESOLVED** (verified 2026-03-18)

---

## Resolution

All three issues already resolved in `src/data/procedural.rs`:
- `generate_sub_milf` and `generate_agent`: annotated with `#[allow(dead_code)]` + TODO comments for future use
- `FactionCode::to_string`: converted to `impl fmt::Display for FactionCode`

Verification: `cargo check` produces **zero warnings**. `cargo test` passes 3/3.

---

## Original Problem

`cargo check` produces 2 warnings:

```
warning: methods `generate_sub_milf` and `generate_agent` are never used
  --> src\data\procedural.rs:34:12

warning: method `to_string` is never used
   --> src\data\procedural.rs:256:8
```

## File

`src/data/procedural.rs`

## What to Fix

1. **`ProceduralEngine::generate_sub_milf`** (line 34) — unused method
2. **`ProceduralEngine::generate_agent`** (line 68) — unused method
3. **`FactionCode::to_string`** (line 256) — unused method

## Decision

- If these are intended for future use, add `#[allow(dead_code)]` with a `// TODO:` comment explaining the planned usage
- If they're stale/orphaned code, delete them
- If `to_string` is meant to implement `Display`, convert to `impl fmt::Display for FactionCode` instead

## Verification

```powershell
cargo check 2>&1 | Select-String "warning"
```

Should produce zero warnings after fix.
