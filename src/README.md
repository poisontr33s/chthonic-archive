# Source Code (`src/`)

> **Context:** Core Rust Infrastructure (Chthonic Archive Renderer & Faction Logic)
> **Type:** Source Code
> **Status:** Active / Pre-Alpha
> **Steward:** Core Engine Team

<!--
================================================================================
SEMANTIC IDENTITY (Anchor & Signal Protocol)
================================================================================
@SID:           DOC_SRC_README
@Type:          Documentation
@Context:       Readme
@SessionOrigin: SESSION_DOC_2026_01_17_CLEANUP
================================================================================
-->

## Purpose
This directory contains the primary executable logic for the Chthonic Archive, written in Rust. It houses the Vulkan rendering engine (`render/`) and the Faction data structures (`data/`).

## Contents
| Component | Description |
|-----------|-------------|
| `main.rs` | Entry point for the application. |
| `render/` | Vulkan graphics pipeline, swapchain, and shader management. |
| `data/`   | Data structures defining Factions, Matriarchs, and Protocols. |

## Ownership
- **Steward:** Core Engine Team
- **Update Policy:** Manual updates required when directory structure changes.

## Build Instructions
```bash
# Build the project
cargo build

# Run the project
cargo run
```
