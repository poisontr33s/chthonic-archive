# Handoff: Trail Relocation + REM Genesis — 2026-04-13

**Session:** 2026-04-13 | Copilot CLI (Claude Sonnet 4.6)
**Status:** Complete — no blockers

## What Changed

### 1. Chthonic Trail relocated (BREAKING for stale memory)
- **Old path:** ~/.chthonic/trail/ (home dir, removed)
- **New canonical:** chthonic-archive/.chthonic/trail/
- **Gitignore:** covered by *.chthonic pattern (line 2, root .gitignore)
- **Verified:** SHA-256 match, 16 events, hot=4618b, cold=1943b

### 2. REM_BLUEPRINT.md relocated
- **Old path:** ~/.chthonic/REM_BLUEPRINT.md (home dir, removed)
- **New canonical:** chthonic-archive/.chthonic/REM_BLUEPRINT.md
- **Patched:** 9 stale ~/.chthonic/ path refs updated to repo-relative .chthonic/

### 3. Runestone Execution Model (REM) conceived
- .runestone = deferred computation, not a file to read
- Bundle: [HEADER][SCHEMA][SPIRV][PAYLOAD] — embedded SPIR-V IS the decoder
- SHA-256 covers SCHEMA+SPIRV+PAYLOAD — hard abort on mismatch
- Phase 1 (CPU path): now unblocked — zstd + incode added to 	ools/ankh-forge/Cargo.toml
- Phase 2 (GPU path): sh, gpu-allocator, sha2, shaderc already in root Cargo.toml

### 4. .chthonic/ tree (current)
```
.chthonic/
  REM_BLUEPRINT.md    ← genesis doc, Step 1 complete
  trail/              ← hot (16 events) + cold (gzip)
  stones/             ← Tier 2 GRANITE dir, created, empty (Step 2 pending)
  cache/              ← bun probes, toolpool (existing)
  ledger/             ← entropy-settlements.jsonl (existing)
  packets/            ← empty
  specs/              ← empty
```

## Memory Status
- store_memory carved: trail canonical path (updated), REM concept, tool strata, Export-VsCodeSession
- Stale memory (~/.chthonic/trail/) was overwritten with corrected path

## Next Session Entry Point
- Step 2 (REM Phase 1 CPU implementation) is scope-ready
  - Add 	rail/ module to 	ools/ankh-forge/src/
  - Implement vent.rs, hot.rs, cold.rs, granite.rs
  - Subcommands: nkh-forge trail append|list|forge|verify|dump
- scripts/chthonic.ps1:1233 help string Configuration (~/.chthonic/) — review if user-facing or internal

## No Action Needed
- ~/.chthonic/api_pool.json refs in api-manager skills — intentionally home-dir, correct
- .temple/, claude-codex-gemini/ historical refs to ~/.chthonic/ — frozen docs, leave

---
*Written by: Copilot CLI session-scout + orchestrator, 2026-04-13*