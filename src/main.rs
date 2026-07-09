// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: main.rs
// ║ Vulkan rendering pipeline - visual truth incarnate
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Spectral Frequency: RED
// ║ Architectural Role: 🏰 THE FORTRESS
// ║ Purpose: The Chthonic Archive: Triumvirate Ascension
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Cross-References (Bidirectional):
// ║   (Standalone file - no detected dependencies)
// ╚════════════════════════════════════════════════════════════════════════════

//! The Chthonic Archive: Triumvirate Ascension

#![allow(unsafe_op_in_unsafe_fn)]
//! @SID:    GAME_MAIN_ENTRY_V1
//! @Shabti: Entry Point

//! ASC-NATIVE-CHAIN-RPG - The World's First Rust/Vulkan/Solana Isometric RPG

//! "We do not accept the CRCs as they are. We demand they be stretched,
//!  filled, and broken until they evolve."

//! <69.96 Alpha Omega>

mod data;
mod render;

use anyhow::Result;
use glam::Vec3;
use log::{error, info};
use std::collections::HashSet;
use winit::{
    application::ApplicationHandler,
    dpi::{LogicalSize, PhysicalPosition},
    event::{ElementState, MouseScrollDelta, WindowEvent},
    event_loop::{ActiveEventLoop, EventLoop},
    keyboard::{KeyCode, PhysicalKey},
    window::{Window, WindowId},
};

// use data::loader::load_game_data;
use data::factions::FactionRegistry;
use data::game_schemas::load_game_schema_documents;
use data::game_tree::{inspect_game_tree, log_game_tree_report};
use data::persistence::{load_game_state, save_game_state};
use data::types::GameData;
use data::verifier::AxiomVerifier;
use render::{Renderer, VulkanContext};

struct ArchiveApp {
    save_path: &'static str,
    game_data: GameData,
    faction_registry: FactionRegistry,
    window: Option<Window>,
    vulkan_context: Option<VulkanContext>,
    renderer: Option<Renderer>,
    frame_count: u64,
    /// Rung 6.3 (camera input): held movement keys, applied continuously each RedrawRequested
    /// tick rather than as one-shot per-keydown steps, so panning is smooth while a key is held.
    keys_held: HashSet<KeyCode>,
}

impl ArchiveApp {
    fn new(
        save_path: &'static str,
        game_data: GameData,
        faction_registry: FactionRegistry,
    ) -> Self {
        // TAA sustained-motion diagnostic (linear-mapping-rain.md Track A1): seeds the exact
        // continuous-pan path a held key drives, instead of a separate one-shot hook, so
        // render-smoke -Profile at a few different CHTHONIC_MAX_FRAMES values can capture
        // ghosting/streaking across a real frame sequence rather than one post-jump screenshot.
        let mut keys_held = HashSet::new();
        if std::env::var("CHTHONIC_TEST_SUSTAINED_PAN").is_ok() {
            keys_held.insert(KeyCode::KeyD);
        }

        Self {
            save_path,
            game_data,
            faction_registry,
            window: None,
            vulkan_context: None,
            renderer: None,
            frame_count: 0,
            keys_held,
        }
    }

    fn cleanup_renderer(&mut self) {
        if let (Some(renderer), Some(vulkan_context)) =
            (self.renderer.as_mut(), self.vulkan_context.as_ref())
        {
            unsafe {
                renderer.cleanup(&vulkan_context.device, &vulkan_context.allocator);
            }
        }
        self.renderer = None;
        self.vulkan_context = None;
    }
}

impl ApplicationHandler for ArchiveApp {
    fn resumed(&mut self, event_loop: &ActiveEventLoop) {
        if self.window.is_some() {
            return;
        }

        info!("🖼️  Initializing windowing system...");
        // CHTHONIC_HEADLESS=1: park the window off-screen instead of showing it. Tried
        // `.with_visible(false)` first -- verified (render-smoke, empirical, not assumed) that
        // it silently stops winit from ever delivering RedrawRequested on Windows, stalling the
        // whole render loop at frame 0. Off-screen positioning keeps the window "visible" from
        // winit/the OS's perspective (so the redraw loop behaves exactly as normal) while never
        // appearing on any actual monitor, so render-smoke-style verification runs don't steal
        // focus or visually interrupt other work.
        let headless = std::env::var("CHTHONIC_HEADLESS").is_ok();
        let mut window_attributes = Window::default_attributes()
            .with_title("The Chthonic Archive: Triumvirate Ascension 🔺")
            .with_inner_size(LogicalSize::new(1280.0, 720.0))
            .with_resizable(true);
        if headless {
            window_attributes = window_attributes.with_position(PhysicalPosition::new(-32000, -32000));
        }

        let window = match event_loop.create_window(window_attributes) {
            Ok(window) => window,
            Err(error) => {
                error!("❌ Failed to create window: {error}");
                event_loop.exit();
                return;
            }
        };

        info!("✅ Window created: {}x{}", 1280, 720);

        info!("🔥 Initializing Vulkan 1.3 with Dynamic Rendering...");
        let vulkan_context = match unsafe { VulkanContext::new(&window) } {
            Ok(context) => context,
            Err(error) => {
                error!("❌ Failed to initialize Vulkan context: {error}");
                event_loop.exit();
                return;
            }
        };

        info!("🎨 Creating rendering pipeline...");
        // Rung 3 (IO off render thread): load bathymetry on a worker thread before any GPU init.
        let bathy_handle = std::thread::spawn(|| {
            // CHTHONIC_BATHYMETRY_PATH lets a candidate dataset (e.g. a Copernicus SDB
            // fused composite) be smoke-tested without touching the production file.
            let bathy_path = std::env::var("CHTHONIC_BATHYMETRY_PATH")
                .unwrap_or_else(|_| render::bathymetry::DEFAULT_PATH.to_string());
            match render::bathymetry::Bathymetry::load(&bathy_path) {
                Ok(b) => {
                    let mesh = b.mesh();
                    info!("🌊 Bathymetry pre-load: {}x{} → {} vertices", b.w, b.h, mesh.len());
                    mesh
                }
                Err(e) => {
                    log::warn!("⚠️ bathymetry load failed ({e:#}); falling back to triangle");
                    render::pipeline::triangle_vertices()
                }
            }
        });
        let bathy_vertices = bathy_handle.join().unwrap_or_else(|_| render::pipeline::triangle_vertices());

        let window_size = window.inner_size();
        let renderer = match unsafe {
            Renderer::new(&vulkan_context, (window_size.width, window_size.height), bathy_vertices)
        } {
            Ok(renderer) => renderer,
            Err(error) => {
                error!("❌ Failed to create renderer: {error}");
                event_loop.exit();
                return;
            }
        };

        info!("═══════════════════════════════════════════════════════════════════");
        info!("   🔥 PHASE 11 COMPLETE: DYNAMIC RENDERING PIPELINE ACTIVE 🔥");
        info!("   Mode: Dynamic Rendering (cmd_begin_rendering/cmd_end_rendering)");
        info!("   Shader: water.vert + water.frag → SPIR-V");
        info!("   Ready to render: bathymetry, ocean, and celestial field");
        info!("═══════════════════════════════════════════════════════════════════");

        self.renderer = Some(renderer);
        self.vulkan_context = Some(vulkan_context);
        self.window = Some(window);

        // TEMPORARY diagnostic, not product code: exercises the exact set_target/zoom calls the
        // real WASD/wheel handlers use, so a render-smoke screenshot can prove the camera math
        // actually moves pixels -- decoupled from whether winit's own event delivery works (a
        // mature library, not new code). Remove once hands-on input testing supersedes this.
        // CHTHONIC_TEST_CAMERA=pan|zoom|both
        if let Ok(mode) = std::env::var("CHTHONIC_TEST_CAMERA") {
            if let Some(renderer) = self.renderer.as_mut() {
                let extent = renderer.swapchain.extent;
                let aspect = extent.width as f32 / extent.height.max(1) as f32;
                if mode == "pan" || mode == "both" {
                    let (forward, _right) = renderer.camera.ground_axes();
                    let offset = forward * renderer.camera.ortho_size * 0.5;
                    let new_target = renderer.camera.target + offset;
                    info!("🧪 CHTHONIC_TEST_CAMERA=pan: target {:?} -> {:?}", renderer.camera.target, new_target);
                    renderer.camera.set_target(new_target, aspect);
                }
                if mode == "zoom" || mode == "both" {
                    info!("🧪 CHTHONIC_TEST_CAMERA=zoom: ortho_size {} -> scaling by 0.5", renderer.camera.ortho_size);
                    renderer.camera.zoom(0.5, aspect);
                }
            }
        }
    }

    fn window_event(
        &mut self,
        event_loop: &ActiveEventLoop,
        window_id: WindowId,
        event: WindowEvent,
    ) {
        let Some(window) = self.window.as_ref() else {
            return;
        };

        if window.id() != window_id {
            return;
        }

        match event {
            WindowEvent::CloseRequested => {
                info!("👋 Window close requested. Terminating Archive.");

                if let Err(error) = save_game_state(self.save_path, &self.game_data) {
                    error!("❌ Failed to save game state: {}", error);
                }

                self.cleanup_renderer();
                self.window = None;
                event_loop.exit();
            }
            WindowEvent::KeyboardInput { event: key_event, .. } => {
                if let PhysicalKey::Code(code) = key_event.physical_key {
                    match key_event.state {
                        ElementState::Pressed => {
                            self.keys_held.insert(code);
                        }
                        ElementState::Released => {
                            self.keys_held.remove(&code);
                        }
                    }
                }
            }
            WindowEvent::MouseWheel { delta, .. } => {
                if let Some(renderer) = self.renderer.as_mut() {
                    let scroll_y = match delta {
                        MouseScrollDelta::LineDelta(_, y) => y,
                        MouseScrollDelta::PixelDelta(pos) => (pos.y / 100.0) as f32,
                    };
                    if scroll_y != 0.0 {
                        let extent = renderer.swapchain.extent;
                        let aspect = extent.width as f32 / extent.height.max(1) as f32;
                        // Scroll up (positive) zooms in — shrinks ortho_size.
                        let scale = (1.0 - scroll_y * 0.1).clamp(0.5, 1.5);
                        renderer.camera.zoom(scale, aspect);
                    }
                }
            }
            WindowEvent::Resized(size) => {
                if let Some(renderer) = self.renderer.as_mut() {
                    if size.width > 0 && size.height > 0 {
                        let current = renderer.swapchain.extent;
                        if size.width != current.width || size.height != current.height {
                            info!(
                                "📐 Window resized: {}x{} (was {}x{})",
                                size.width, size.height, current.width, current.height
                            );
                            renderer.needs_resize = true;
                        }
                    }
                }
            }
            WindowEvent::RedrawRequested => {
                let Some(vulkan_context) = self.vulkan_context.as_ref() else {
                    return;
                };
                let Some(renderer) = self.renderer.as_mut() else {
                    return;
                };

                if renderer.needs_resize {
                    let size = window.inner_size();
                    if size.width > 0 && size.height > 0 {
                        match unsafe {
                            renderer.handle_resize(vulkan_context, (size.width, size.height))
                        } {
                            Ok(()) => return,
                            Err(error) => {
                                error!("❌ Resize failed: {error:?}");
                                return;
                            }
                        }
                    }
                    return;
                }

                self.frame_count += 1;

                // Profile-mode exit: render-smoke.ps1 -Profile sets CHTHONIC_MAX_FRAMES=300
                if let Ok(s) = std::env::var("CHTHONIC_MAX_FRAMES") {
                    if let Ok(max) = s.parse::<u64>() {
                        // Heartbeat every 60 frames so smoke -Profile can confirm loop is alive
                        if self.frame_count % 60 == 0 {
                            eprintln!("PROFILE HEARTBEAT frame={}", self.frame_count);
                        }
                        if self.frame_count >= max {
                            eprintln!("PROFILE EXIT at frame {}", self.frame_count);
                            event_loop.exit();
                            return;
                        }
                    }
                }

                // Rung 5/6: real solar vector over New Providence — grounded by the in-house
                // Rust cosmos (CLAUDEBASE_COSMOS_V1 port; verified vs Skyfield/JPL Horizons in
                // its tests). Fixed at 2026-06-09 17:00 UTC (Nassau solar noon) so the bank is
                // daylit for verification; swap to SystemTime::now()→JD for the live sky.
                let jd = render::cosmos::scene_julian_day();
                let sun = render::cosmos::sun_push_constant(
                    render::cosmos::NEW_PROVIDENCE_LAT_DEG,
                    render::cosmos::NEW_PROVIDENCE_LON_DEG,
                    jd,
                );

                if self.frame_count % 240 == 0 {
                    info!(
                        "☀️ Shallow-water + celestial shader live · sun = [{}, {}, {}]",
                        sun[0], sun[1], sun[2]
                    );
                }

                // Rung 6.3 (camera input): continuous pan while a WASD key is held. Speed scales
                // with the current zoom level (ortho_size) so it feels consistent whether zoomed
                // in close or viewing the whole Banks — a fixed step would be imperceptible at
                // the full 400km extent and wildly too fast zoomed all the way in.
                if !self.keys_held.is_empty() {
                    let (forward, right) = renderer.camera.ground_axes();
                    let mut delta = Vec3::ZERO;
                    if self.keys_held.contains(&KeyCode::KeyW) {
                        delta += forward;
                    }
                    if self.keys_held.contains(&KeyCode::KeyS) {
                        delta -= forward;
                    }
                    if self.keys_held.contains(&KeyCode::KeyD) {
                        delta += right;
                    }
                    if self.keys_held.contains(&KeyCode::KeyA) {
                        delta -= right;
                    }
                    if delta != Vec3::ZERO {
                        let pan_speed = renderer.camera.ortho_size * 0.02;
                        let new_target = renderer.camera.target + delta.normalize() * pan_speed;
                        let extent = renderer.swapchain.extent;
                        let aspect = extent.width as f32 / extent.height.max(1) as f32;
                        renderer.camera.set_target(new_target, aspect);
                    }
                }

                match unsafe { renderer.render_frame(vulkan_context, sun) } {
                    Ok(needs_resize) => {
                        if needs_resize {
                            renderer.needs_resize = true;
                            window.request_redraw();
                        }
                    }
                    Err(error) => {
                        error!("❌ Render failed: {error:?}");
                    }
                }
            }
            _ => {}
        }
    }

    fn about_to_wait(&mut self, _event_loop: &ActiveEventLoop) {
        if let Some(window) = self.window.as_ref() {
            window.request_redraw();
        }
    }
}

#[cfg(windows)]
#[link(name = "kernel32")]
unsafe extern "system" {
    fn FreeConsole() -> i32;
}

/// Entry point - The Gate to the Chthonic Archive
fn main() -> Result<()> {
    // CHTHONIC_HEADLESS=1: detach from the console window Windows auto-allocates for a
    // console-subsystem binary, regardless of stdout/stderr redirection. This is the other
    // half of "no visible window" alongside the off-screen graphics window in resumed() --
    // that one only parks the render surface; without this, an empty terminal still shows
    // up behind it every run. A launcher-side `-WindowStyle Hidden` fix doesn't work here:
    // PowerShell/.NET silently ignores WindowStyle whenever Start-Process redirection is
    // also used, which render-smoke.ps1 needs for its log capture -- so this has to be
    // fixed from inside the process itself. Already-redirected stdout/stderr are plain file
    // handles, unaffected by detaching from the console object.
    #[cfg(windows)]
    if std::env::var("CHTHONIC_HEADLESS").is_ok() {
        unsafe {
            FreeConsole();
        }
    }

    // Initialize logging
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info")).init();

    info!("╔══════════════════════════════════════════════════════════════════╗");
    info!("║   THE CHTHONIC ARCHIVE: TRIUMVIRATE ASCENSION                   ║");
    info!("║   Classification: ASC-NATIVE-CHAIN-RPG                          ║");
    info!("║   Engine: Rust/Vulkan 1.3 Native | Blockchain: Solana (Pending) ║");
    info!("╚══════════════════════════════════════════════════════════════════╝");

    // === PHASE 14: AXIOMATIC VERIFICATION (debug builds only) ===
    #[cfg(debug_assertions)]
    {
        info!("⚖️ Verifying Axiomatic Integrity (SSOT)...");
        let verifier = AxiomVerifier::new(".chthonic/SSOT.md");
        if let Err(e) = verifier.verify_integrity() {
            error!("❌ AXIOMATIC FAILURE: {}", e);
        }
    }

    // === PHASE 1: LOAD GAME DATA (Level 1.5 Entity Persistence) ===
    info!("📥 Loading game data and persistent state...");
    let save_path = "assets/save_state.json";
    let default_path = "assets/data.json";

    let game_data = load_game_state(save_path, default_path)?;

    // === PHASE 12: WORLD MANIFESTATION ===
    info!("🌍 Manifesting world into Faction Registry...");
    let mut faction_registry = FactionRegistry::new();
    faction_registry.initialize(&game_data);

    faction_registry.log_invocation("AIP-FA1: World Manifestation Initialized");

    info!(
        "✅ World manifestation complete. {} matriarchs active. {} world layers manifested.",
        faction_registry.matriarchs.len(),
        faction_registry.districts.len()
    );

    info!(
        "✅ Data ingestion complete. {} entities ready for manifestation.",
        game_data.entities.len()
    );

    // === PHASE 12.5: REPO-LOCAL cRPG CONTENT BRIDGE ===
    match inspect_game_tree("game") {
        Ok(game_tree) => log_game_tree_report(&game_tree),
        Err(e) => error!("⚠️ Game tree inspection failed: {}", e),
    }
    match load_game_schema_documents("game") {
        Ok(schema_docs) => {
            info!(
                "📚 Loaded {} game schema documents into registry",
                schema_docs.len()
            );
            faction_registry.schema_docs = schema_docs;
        }
        Err(e) => error!("⚠️ Schema document loading failed: {}", e),
    }

    let event_loop = EventLoop::new()?;
    let mut app = ArchiveApp::new(save_path, game_data, faction_registry);
    event_loop.run_app(&mut app)?;

    Ok(())
}
