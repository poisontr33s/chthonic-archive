# The Chthonic Archive

A solo-developed Rust/Vulkan game engine, built from raw `ash` bindings rather than an existing engine, for an isometric cRPG (`game/`) set in the Bahamas. Windows-only. No engine abstraction layer between this code and the Vulkan API — every pipeline, descriptor set, and barrier is hand-written.

## What's actually running

- **Vulkan 1.3, dynamic rendering** — no render-pass/framebuffer objects; `cmd_begin_rendering`/`cmd_end_rendering` throughout.
- **Hardware ray-traced water reflections** — `VK_KHR_ray_tracing_pipeline`, BLAS/TLAS over the real bathymetry + ocean meshes, a closest-hit shader with a depth-driven Beer-Lambert seabed model (real per-vertex color for exposed land, fixed-reflectance + in-scatter glow underwater).
- **FFT ocean simulation** — Tessendorf wave model, GPU compute, double-buffered.
- **Real bathymetry** — GEBCO/Copernicus seabed elevation data drives the actual mesh, not a procedural approximation.
- **A working solar/celestial system** — real Julian-day astronomy (verified against Skyfield/JPL Horizons in-repo), a zodiac wheel anchored to a Sirius/Alcyone-midpoint ayanamsa, driving the actual sun direction and atmosphere scattering (Rayleigh/Mie/ozone).
- **TAA** — Halton-jittered dynamic rendering, per-pixel motion vectors, neighbourhood-clamp history rejection, and a camera-motion-adaptive blend that disambiguates real camera movement from ordinary wave-surface animation.
- **DLAA fallback path** — Streamline integration, engages automatically when available.
- **Isometric camera** — orthographic projection, WASD pan + mouse-wheel zoom, screen-relative axes.
- **21 shader files** (`assets/shaders/`) — GLSL, compiled to SPIR-V at build time via `shaderc`.

None of the above is a tech demo in isolation — they run together, every frame, in the same swapchain loop.

## Repo shape

- `src/` — the engine binary. `src/render/` is where almost everything above actually lives.
- `assets/shaders/` — GLSL source; SPIR-V output goes to `OUT_DIR`, not checked in.
- `tools/` — a Rust workspace of MCP servers and support tooling (`chthonic-mcp-server`, `vulkan-mcp-server`, `chthonic-hw-mcp-server`, `bevy-mcp-server`, and others) — these are Cargo workspace members; the engine itself is not.
- `extensions/` — a family of VS Code extensions (themes, status bar, sidebar tooling) built around this project.
- `apps/` — standalone apps (a Next.js site, an image-gen pipeline, a few others).
- `scripts/` + `ci/` — the automation layer (Bun/TypeScript, PowerShell, Python via `uv`).
- `game/` — the actual RPG content this engine renders: assets, lore, dialogue, systems.
- `CLAUDEBASE/` — a repo-in-repo used as working memory/logbook for AI-assisted development sessions on this project.

If you're an AI agent working in this repo: read `CLAUDE.md` first, not this file.

## Building

Requires the Vulkan SDK (for `shaderc`'s build-time GLSL→SPIR-V compilation) and a Rust stable toolchain (see `rust-toolchain.toml`).

```
cargo build          # builds the engine (repo root — it's not a workspace member)
cargo run
cargo test
```

`scripts/render-smoke.ps1` builds, runs the engine headless for a bounded window, captures a screenshot, and reports validation-layer/crash status — the fast way to self-check a rendering change without watching a window.

Repo-wide automation (linting, link auditing, CI checks) runs through `bun run <script>` — see `SCRIPTS_README.md`.

## License

WTFPL, per `Cargo.toml`.
