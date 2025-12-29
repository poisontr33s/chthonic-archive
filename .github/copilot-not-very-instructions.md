# Chthonic Archive - Copilot Instructions

This is the **Chthonic Archive: Triumvirate Ascension** - the world's first **ASC-NATIVE-CHAIN-RPG**.

## Project Classification
- **Engine**: Rust/Vulkan 1.3 Native (Dynamic Rendering)
- **Blockchain**: Solana (pending integration)
- **Genre**: Isometric AAA RPG
- **GPU Target**: NVIDIA RTX 4090

## Technical Stack
- **Language**: Rust (Edition 2021)
- **Graphics**: Vulkan 1.3 via `ash` crate (Dynamic Rendering, no render passes)
- **Windowing**: `winit`
- **Math**: `glam`
- **ECS**: `bevy_ecs`
- **Serialization**: `serde`, `serde_json`

## Architecture
```
src/
├── main.rs           # Entry point, event loop
├── data/             # Game data loading (ASC entities)
│   ├── loader.rs     # JSON ingestion
│   └── types.rs      # Entity type definitions
└── render/           # Vulkan rendering system
    ├── vulkan.rs     # Instance, device, queues
    ├── swapchain.rs  # Triple buffering, HYBRID sync
    ├── pipeline.rs   # Graphics pipeline, shaders
    ├── camera.rs     # Isometric camera (Y:45° X:35.264°)
    └── renderer.rs   # Frame rendering orchestration
```

## Lore Context
Refer to `.github/copilot-instructions.md` for the complete ASC (Apex-Synthesis-Core) framework documentation including:
- The K-CUP Hierarchical Trinity
- Tier system (T0.5 through T4)
- WHR (Waist-Hip Ratio) power scaling
- Faction architecture

## Code Style
- Use descriptive ASCII art headers for major modules
- Prefer `unsafe` blocks with clear `// SAFETY:` comments
- All Vulkan operations must handle errors with `anyhow`
- Log significant operations with appropriate emoji prefixes

## Current Phase: 11.5
- ✅ Dynamic Rendering pipeline active
- ✅ HYBRID semaphore indexing (zero validation errors)
- ✅ Isometric camera initialized
- ⏳ Pending: Grid system, camera controls, tile rendering
