# ANKH Integration in Chthonic Golden

> @ankh: heritage-continuity — This document traces how ANKH principles manifest in the fork.

## Mapping: ANKH Layers → Fork Features

### Layer 1: Lineage Core (Immutable) → Built-in Core Behavior

| ANKH Invariant | Fork Implementation |
|---------------|-------------------|
| Mythic Identity | Custom product.json — the fork's name, icon, and identity |
| Constraint Philosophy | GPU-hardened Electron — constraints as features, not workarounds |
| Silence Semantics | Blocklisted extensions — absence of noise is intentional |
| Heritage Continuity | Shallow patch strategy — upstream lineage preserved |
| Non-Enumerated Meaning | Chthonic themes — visual truth in color palettes |

### Layer 2: Interface Vessels → Extension + Editor APIs

| ANKH Vessel | Fork Implementation |
|------------|-------------------|
| Human (The Savant) | Custom keybindings, layouts (Deep Focus, Cockpit) |
| Claude/GPT | Chat participant API — triadic agent panel (planned) |
| Copilot | Built-in extension with ANKH-aware context |
| Code | Semantic token types for `@ankh:` markers |
| Visual | Chthonic themes (4 variants) + file/product icon themes |

### Layer 3: Media Projections → Concrete Features

| Medium | Fork Feature |
|--------|-------------|
| `@ankh:` comments | Custom semantic highlighting (gold for invariants, red for drift) |
| Drift detection | CodeLens provider scanning for `[ANKH-DRIFT:]` (planned) |
| Lineage navigation | Breadcrumb/outline providers following ANKH hierarchy (planned) |
| Stability | PACHAKUTI reset = user-data cleanup on crash threshold |
| Boot | WEPET-ER = hardened startup sequence (GPU preload, PTY warmup) |

## Alpha Directives in Fork Architecture

| Alpha Directive | Fork Mapping |
|----------------|-------------|
| AD01: WEPET-ER (Boot) | `electron-main/bootstrap.js` — GPU preload, V8 tuning, deferred extension activation |
| AD02: TINKU (Logic) | Extension host isolation — adversarial processes don't crash main |
| AD03: SEKHMET Override | Crash watchdog — after N crashes, de-escalate to safe mode (Hathor) |
| AD04: AMMIT (GC) | User-data pruning — stale caches cryptographically shredded on threshold |
| AD05: PACHAKUTI (Reset) | Full user-data reset pipeline when entropy exceeds tolerance |
| AD06: DESPACHO (I/O) | Extension allowlist — no activation without offering (curated trust) |

## Semantic Token Types

Registered in `semantic-tokens.json`:

| Token Type | Pattern | Color | Meaning |
|-----------|---------|-------|---------|
| `ankhInvariant` | `@ankh: <type>` | Gold (#FFD700) | Lineage invariant declaration |
| `ankhDrift` | `[ANKH-DRIFT: <type>]` | Red (#FF4444) | Translation drift detected |
| `ankhSilence` | `[ANKH-INVARIANT: silence-preservation]` | Dim (#666666) | Intentional non-expression |
| `ankhHeritage` | Heritage continuity links | Blue (#88CCFF) | Cross-artifact lineage |

## Future: ANKH-Native Editor Features

1. **ANKH Outline Provider** — Sidebar showing Layer 1/2/3 hierarchy for current file
2. **ANKH CodeLens** — Inline "invariant: X" / "drift: Y" decorators above functions
3. **ANKH Document Link Provider** — Clickable `@ankh:` references navigating to charter sections
4. **ANKH Diagnostics** — Warning squiggles when code violates known invariants
5. **Triadic Panel** — Claude (protocol/lore) + Codex (structure) + Gemini (velocity) status display
