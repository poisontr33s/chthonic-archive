# Vulkan CLI Renderer — Gate Walk (V6 Arc)

> **Urca de Lima Identity:** `todo_roulette.ts` and the dungeon renderer are ONE data source viewed through two projection functions. `manifest/todo_roulette.json` is read by both. `--mode=polar` renders the arc-wheel; `--mode=dungeon` renders the cRPG room map. The two projections are isomorphic — `SpinState ≡ RoomState`, `task ≡ room`, `weight ≡ encounter level`, `tags ≡ biome`, `status:completed ≡ room:cleared`.

---

## Gate Table (G0 → G7)

| Gate | Status | Commit | What Was Built |
|------|--------|--------|----------------|
| **G0** | ✅ open | `1c073231` | Headless Vulkan device (RTX 4090, QF=2 COMPUTE-only). Scaffold + target cleanup (`b4bbf0f6`). |
| **G1** | ✅ open | `1c073231` | `VkInstance` no-surface, physical device enum, ash 0.38 + serde_json. `cargo check` clean. |
| **G2** | ✅ open | `d135e3a1` | Euler scoring SSBO compute: `EulerTask[]` → `euler_score.comp.spv` → sorted output. GPU-scored, HOST_COHERENT buffers. KAPPA=0.07 mirrors `todo_roulette.ts`. |
| **G3** | ✅ open | `34a7a947` | `VkImage 480×80` RGBA8 → `ascii_downsample.comp.spv` → packed-u32 cell buffer (300 cells, 60×5). `fn transition_image_layout()` written once, load-bearing for G3–G6. BLOCK_CHARS density indices 0–4. |
| **G4** | ✅ open | `34a7a947` | Differential frame streaming: `dirty_diff.comp.spv` GPU diff pass (curr vs prev VkImage) → dirty-cell cursor positioning. Eliminates clear-screen flicker at 30fps. `--loop` flag enables render loop. |
| **G5** | ✅ open | *(this arc)* | `StatePhase` FSM: `Idle=0 → Spinning=1 → Decelerating=2 → Landed=3`. **SpinState ≡ RoomState** — same 4-phase graph drives polar animation phase and dungeon room visual state. `tick_state()` + `state_label()`. |
| **G6** | ✅ open | *(this arc)* | Dungeon render mode: `ascii_dungeon.comp.spv`, 4×STORAGE_BUFFER + `push_constant uint state_phase`. `--dungeon` flag. Box-drawing BLOCK_CHARS indices 5–12. Urca de Lima synthesis: roulette IS dungeon, one manifest, two projection functions. |
| **G7** | ✅ open | *(this arc)* | Meta-gate: this document. Session docs + gate walk seed next epoch. `todo_roulette.ts --live --dungeon` pass-through live. |

---

## Blocker Chain (Architectural Can-Openers)

Each blocker forced the architectural decision that the next gate required:

```
G1 blocker: none (headless device proven by G0 coop_matrix probe)
  └─→ G2 entry: data ingestion (manifest → SSBO)

G2 blocker: schema-sync (JSON ↔ GPU buffer layout)
  └─→ #[repr(C)] EulerTask struct serves both roles
  └─→ G3 entry: pixel rendering

G3 blocker: Vulkan barrier boilerplate (~80 lines per transition)
  └─→ fn transition_image_layout() written once → load-bearing for G3–G6
  └─→ G4 entry: animation / differential streaming

G4 blocker: full clear-screen flicker at 30fps
  └─→ GPU diff pass (curr vs prev VkImage) → dirty-cell cursor positioning
  └─→ also: room-state change detector for G6
  └─→ G5 entry: simulation state machine

G5 blocker: state machine design
  └─→ SpinState == RoomState (same transition graph) — written once, serves both
  └─→ G6 entry: render modes

G6 blocker: dungeon layout algorithm
  └─→ Urca de Lima: roulette IS dungeon (one manifest, two projection functions → --mode flag)
  └─→ score_buf re-write in ranked order before dungeon dispatch
  └─→ V7 entry: force-directed GPU world-generation compute vector

G7 (this gate): self-documenting arc — session docs = next epoch's G0
```

---

## Urca de Lima Synthesis

**The Urca de Lima pattern:** two apparent products are the same data through two projection functions. The treasure was aboard the whole time.

**Canonical instance — roulette × dungeon:**

| Field in `todo_roulette.json` | Polar (roulette) projection | Dungeon projection |
|-------------------------------|-----------------------------|--------------------|
| `weight` | arc span (Euler score contribution) | room area + encounter level |
| `phase_angle` | compass bearing on arc wheel | room adjacency (shared-tag graph) |
| `status: completed` | landed/cleared slot | cleared room (room collapse) |
| `verify_condition: file-exists` | weight multiplier | locked door unlock trigger |
| `TAG_COLOR` | arc segment color | room biome color |
| task → | arc slot | room |

**The FSM identity (G5):**
```
SpinState { Idle, Spinning, Decelerating, Landed }
    ≡
RoomState { Locked, Unlocked, Visited, Cleared }
```
Same 4-state transition graph. Written once (`StatePhase` enum), serves both render modes.

---

## V7: Next Epoch Vector

| Surface | Next work |
|---------|-----------|
| **Render** | Force-directed GPU room layout: room positions computed as spring-force simulation (SSBO positions, compute dispatch per frame). Dungeon becomes spatially coherent across sessions. |
| **World-gen** | `--mode=dungeon` → full cRPG: room collapse animation on task completion, locked-door event on `verify_condition` fail, biome palette from tag color registry. |
| **Polar** | Particle decay mode: completed tasks leave ghost arcs fading over N frames (history layer). |
| **Data** | Hot-reload: watch `manifest/todo_roulette.json` via `inotify`/`ReadDirectoryChanges`, push updates to GPU task buffer without full restart. |

---

*Last sealed: vulkan-lab V6 arc — G5+G6+G7 committed.*
