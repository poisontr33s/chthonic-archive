# Stewardship Report — renderer.rs & gpu-allocator Migration

> **Time:** 2026-06-22T03:47 +02:00  
> **Source:** Antigravity CLI (Claude Opus 4.6 Thinking) taking the wheel from Claude Code (Sonnet 4.6) after 529 overload

---

## What Sonnet Was Doing When It Crashed

Sonnet was mid-flight on a **gpu-allocator migration** — replacing raw `vkAllocateMemory` / `vk::DeviceMemory` calls with the `gpu_allocator` crate's `Allocator` in the ocean compute subsystem. This is a memory-management improvement (shared allocator = fewer Vulkan allocation objects = better for the 4090's allocation limits).

### Changes Sonnet Had Already Applied (uncommitted, in working tree):

| File | What Changed | Status |
|---|---|---|
| [vulkan.rs](file:///C:/Users/eldno/chthonic-archive/src/render/vulkan.rs) | Added `pub allocator: Arc<Mutex<Allocator>>` field to `VulkanContext`; constructs it in `new()` | ✅ Complete |
| [ocean_compute.rs](file:///C:/Users/eldno/chthonic-archive/src/render/ocean_compute.rs) | Replaced 4× `vk::DeviceMemory` fields with `Option<Allocation>`; rewrote `alloc_storage_image()` to use `gpu-allocator`; removed local `find_memory_type()`; updated `cleanup()` signature to take `&mut Allocator` | ✅ Complete |
| [renderer.rs](file:///C:/Users/eldno/chthonic-archive/src/render/renderer.rs) | Added `use gpu_allocator::vulkan::Allocator` + `Arc<Mutex>`; changed `cleanup()` signature to pass allocator through to `ocean_compute.cleanup()` | ✅ Complete |
| [main.rs](file:///C:/Users/eldno/chthonic-archive/src/main.rs) | Call site for `renderer.cleanup()` — **NOT updated before 529 hit** | ❌ → ✅ Fixed by me |

### The Fix I Applied

One-line fix in [main.rs:79](file:///C:/Users/eldno/chthonic-archive/src/main.rs#L79):
```diff
-                renderer.cleanup(&vulkan_context.device);
+                renderer.cleanup(&vulkan_context.device, &vulkan_context.allocator);
```

**`cargo check` now passes** — zero errors, only existing warnings (dead code, snake_case naming).

---

## Quality State — Codebase Progression

### The Engine ("Astrological Nassau") — What's Built & Committed

| Rung/Stage | Feature | State |
|---|---|---|
| Rung 1-2 | Vulkan 1.4 dynamic rendering, depth buffer, swapchain | ✅ Committed |
| Rung 2.4 | Temporal anti-aliasing scaffolding (Halton jitter + true per-pixel motion vectors via water.vert reprojection) | ✅ Committed |
| Rung 3 | Real GEBCO bathymetry (loaded off render thread) + Beer–Lambert shallow-water shader | ✅ Committed |
| Rung 4.2a-c | **Tessendorf IFFT ocean** — h₀ spectrum → evolve → N×butterfly → displacement. Full compute pipeline. | ✅ Committed (HEAD: `7284b800`) |
| §2.6 | Celestial field — Sun/Moon/5 planets/24 stars + ecliptic/equator/galactic great circles (JPL-Horizons-verified) | ✅ Committed |
| A-C-A Stage 0 | Correspondence socket (`correspondence.rs`) | ✅ Committed |
| A-C-A Stage 1 | Lens set — iso + perspective (`lens.rs`) | ✅ Committed |
| A-C-A Stage 2a-d | Zodiac (Ankhological origin), orientable heading, Moon+5 planets in signs | ✅ Committed |
| TAA Gate 1 | Offscreen colour target + verbatim copy to swapchain | ✅ Committed |

### What's In-Flight (Uncommitted Working Tree)

**gpu-allocator migration** in `ocean_compute.rs` + `vulkan.rs` + `renderer.rs` + `main.rs` — now compiles, but **NOT yet tested** (needs `render-smoke.ps1` + `cargo test render::` before commit).

### What's Next (from Sonnet's own memory)

1. **TAA Gate 2**: History colour buffer (ping-pong pair) + sampler
2. **TAA Gate 3**: Fullscreen resolve pass (sample + reproject + clamp + blend → swapchain)
3. **TAA Gate 4**: Verify static-camera supersampling win
4. **Semantics**: Owner-defined Andean/Egyptian sign meanings (engine never invents)

---

## Memory & Project Sync Audit

### Claude Code Memory ([memory/](file:///C:/Users/eldno/.claude/projects/C--Users-eldno-chthonic-archive/memory))

| Memory File | Synced? | Notes |
|---|---|---|
| [project_north_star_renderer_checkpoint.md](file:///C:/Users/eldno/.claude/projects/C--Users-eldno-chthonic-archive/memory/project_north_star_renderer_checkpoint.md) | ⚠️ Stale | Dated `2026-06-19`. Does not mention the gpu-allocator migration or the current uncommitted work. Lists "Rung 4 Tessendorf" as NEXT, but Tessendorf is already committed (`7284b800`). The NEXT section needs updating. |
| [project_sonnet_parallel_lane.md](file:///C:/Users/eldno/.claude/projects/C--Users-eldno-chthonic-archive/memory/project_sonnet_parallel_lane.md) | ✅ OK | Describes the Sonnet lane architecture correctly. The current 529 crash is exactly the kind of mid-flight interruption this arrangement expects. |
| [MEMORY.md](file:///C:/Users/eldno/.claude/projects/C--Users-eldno-chthonic-archive/memory/MEMORY.md) | Not checked | 34KB — likely the main rolling memory. May need update re: gpu-allocator migration. |

### CLAUDEBASE State ([CLAUDEBASE/](file:///C:/Users/eldno/chthonic-archive/CLAUDEBASE))

All 6 chambers **LIVE** (commissioned 2026-06-06):
- `harbor/` → `warmstart.md` 
- `charts/` → `gate-map.md`
- `hold/` → `stow-manifest.md`
- `quarterdeck/` → `dispatch.md`
- `watch/` → `sentinels.md`
- `logbook/` → `00-commissioning.md`

The CLAUDEBASE is structurally sound and reflects the nautical governance. Its `CLAUDE.md` has the API pool contract correctly referencing the parent repo's `docs/API_POOL_MCP_CONTRACT.md`.

### Global Claude Code Config (`~/.claude/CLAUDE.md`)

**Effectively empty** (just `# CLAUDE.md` + blank line). All real memory lives in the project-scoped memory files (101 files in `memory/`).

---

## Verdict

| Aspect | Status |
|---|---|
| **Compile** | ✅ PASS (zero errors after my one-line fix) |
| **Working tree coherent** | ✅ Changes are a consistent gpu-allocator migration across 4 files |
| **Sonnet doing anything bad** | ❌ No — this was a legitimate and well-scoped refactor |
| **Memory synced** | ⚠️ `project_north_star_renderer_checkpoint.md` is ~3 days stale (doesn't reflect Tessendorf landing or gpu-allocator work) |
| **Ready to test + commit** | ✅ After `render-smoke.ps1` + `cargo test render::` |

> [!IMPORTANT]
> The uncommitted gpu-allocator migration compiles but has not been runtime-verified. Run `scripts/render-smoke.ps1` and `cargo test render::` before committing.
