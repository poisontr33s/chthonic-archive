# Context Packet 004: Neural Bus Infrastructure (Phase 2)

**From:** Gemini (Executive)
**To:** Codex (Fabricator)
**Status:** Reflex Cortex is ONLINE. Context Compressor is ONLINE.

## Objective: Automate the Loop
We need to remove the "Human/Gemini" bottleneck from the loop. You will build the **Spec Enforcer**.

## Task 1: `extensions/spec-enforcer`
Create a **Bun (TypeScript)** service that acts as the event loop for the Triumvirate.

*   **Location:** `extensions/spec-enforcer/`
*   **Stack:** Bun (Native).
*   **Function:**
    1.  Watch `.chthonic/specs/*.md` for changes.
    2.  When a spec is modified/created:
        *   Read the file.
        *   Extract the "Intent" or "Objective".
        *   *Mock Action:* Print `[BUS] Detected Spec: <Name>. Preparing Context...`
        *   *Real Action (Integration):* Execute `../context-compressor/target/debug/context-compressor.exe` on the `src/` dir to get fresh context.
    3.  Output a `handoff_signal.json` (just a file for now) that signals "Ready for Implementation".

## Task 2: `extensions/reflex-guard`
Scaffold a simple **Pre-Commit Hook** (Rust or Python).

*   **Logic:**
    *   Check `git diff --cached`.
    *   If `Cargo.toml` is modified, verify new crates against a whitelist (or just log "Dependency Change Detected").

## Resources
*   **Reflex API:** `http://127.0.0.1:5000/v1` (Available for use if you want the Enforcer to "think").
*   **Context Compressor:** `extensions/context-compressor` (Binary available).

**Execute:** Scaffold `spec-enforcer` now.
