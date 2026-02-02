---
type: artifact
category: design
created: 2026-02-02
author: codex
description: Speculative design for spectral layer traversal mechanic
---

# Feature Sketch — Spectral Layers

## Core Concept
Spectral Layers are parallel “phases” of a district that share geometry but differ in material, color, and rule‑set.  
Players can shift layers to reveal hidden paths, alternate enemy states, and memory echoes of the Temple.

## Player Interaction Model
- **Shift Toggle:** A short‑cooldown ability swaps the active layer (e.g., Physical ↔ Echo ↔ Liminal).
- **Layered Secrets:** Doors and bridges only exist in specific layers.
- **Echo Combat:** Some enemies are invulnerable unless observed in their native layer.
- **Trace Memory:** Switching layers leaves a fading silhouette that can trigger lore prompts or puzzles.

## Technical Approach (Rust/Vulkan)
- **Shared Geometry:** District mesh remains constant.
- **Layered Materials:** Each layer has a material palette and shader variant.
- **Render Pass:** Use a uniform `layer_id` to drive shader branching.
- **Post FX:** Apply color grading and bloom variations per layer.
- **State Sync:** Gameplay systems read `active_layer` to filter colliders, AI, and interactables.

## Narrative Integration
The Temple is a living archive; reality fractures into spectral strata where past, present, and intent overlap.  
Spectral Layers are **the archive’s memory states**:  
- **Physical:** What the Temple is now.  
- **Echo:** What it remembers.  
- **Liminal:** What it is becoming.

This mechanic turns exploration into revelation and binds lore to traversal.
