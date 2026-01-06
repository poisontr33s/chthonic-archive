# Probe Contract — shell_capabilities.ps1

This document defines the **ABI contract** for the canonical environment probe:

```
scripts/shell_capabilities.ps1
```

---

## Purpose

The probe provides **ground-truth environment facts** to automation agents
(Claude Code, GitHub Copilot CLI, CI) without inference.

It exists to **collapse ambiguity**, not to add diagnostics.

---

## Canonical Artifact

- **Path:** `scripts/shell_capabilities.ps1`
- **Hash (SHA256):**
  ```
  6D6782ED8FFC4BF434D2A7108A0F3BACF13C3B40CC5C8F00F53CB789A96D9DF8
  ```
- **Validator (authoritative):**
  ```
  scripts/validate_shell_probe.ps1
  ```

---

## Hard Invariants (ABI)

The probe **MUST**:

- Emit **JSON only**
- Be **read-only**
- Have **no branching or logic** in executable lines
- Produce deterministic output for the same environment

The probe **MAY**:

- Contain comments
- Contain documentation
- Be reformatted *only if the hash is intentionally updated*

---

## Forbidden Changes

Do **NOT**:

- Add conditionals (`if`, `for`, `while`, `try`, etc.)
- Add prompts, logging, or side effects
- Add "just one more field"
- Repurpose the probe for diagnostics

If additional diagnostics are needed, create a **separate script**.

---

## Enforcement Model

- **Hard gate:** `validate_shell_probe.ps1`
- **CI:** Fails if the hard gate fails
- **Style / heuristics:** Advisory only
- **Upcycle audit:** Probe is explicitly exempt

---

## Design Principle

> *Give agents a rock, not a map.*

The probe is intentionally boring.
