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
//!
//! @SID:    GAME_MAIN_ENTRY_V1
//! @Shabti: Entry Point
//!
//! ASC-NATIVE-CHAIN-RPG - The World's First Rust/Vulkan/Solana Isometric RPG
//!
//! "We do not accept the CRCs as they are. We demand they be stretched,
//!  filled, and broken until they evolve."
//!
//! <69.96 Alpha Omega>

mod data;
mod render;

use anyhow::Result;
use log::{info, error};
use winit::{
    application::ApplicationHandler,
    dpi::LogicalSize,
    event::WindowEvent,
    event_loop::{ActiveEventLoop, EventLoop},
    window::{Window, WindowId},
};

// use data::loader::load_game_data;
use data::persistence::{load_game_state, save_game_state};
use data::factions::FactionRegistry;
use data::game_tree::{inspect_game_tree, log_game_tree_report};
use data::game_schemas::load_game_schema_documents;
use data::types::GameData;
use data::verifier::AxiomVerifier;
use render::{VulkanContext, Renderer};

struct ArchiveApp {
    save_path: &'static str,
    game_data: GameData,
    faction_registry: FactionRegistry,
    window: Option<Window>,
    vulkan_context: Option<VulkanContext>,
    renderer: Option<Renderer>,
    frame_count: u64,
}

impl ArchiveApp {
    fn new(save_path: &'static str, game_data: GameData, faction_registry: FactionRegistry) -> Self {
        Self {
            save_path,
            game_data,
            faction_registry,
            window: None,
            vulkan_context: None,
            renderer: None,
            frame_count: 0,
        }
    }

    fn cleanup_renderer(&mut self) {
        if let (Some(renderer), Some(vulkan_context)) =
            (self.renderer.as_mut(), self.vulkan_context.as_ref())
        {
            unsafe {
                renderer.cleanup(&vulkan_context.device);
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
        let window_attributes = Window::default_attributes()
            .with_title("The Chthonic Archive: Triumvirate Ascension 🔺")
            .with_inner_size(LogicalSize::new(1280.0, 720.0))
            .with_resizable(true);

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
        let window_size = window.inner_size();
        let renderer = match unsafe {
            Renderer::new(&vulkan_context, (window_size.width, window_size.height))
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
        info!("   Shader: iso_grid.vert + iso_grid.frag → SPIR-V");
        info!("   Ready to render: Hello Triangle 🔺");
        info!("═══════════════════════════════════════════════════════════════════");

        self.renderer = Some(renderer);
        self.vulkan_context = Some(vulkan_context);
        self.window = Some(window);
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

                // Rung 5/6: real solar vector over New Providence — grounded by the in-house
                // Rust cosmos (CLAUDEBASE_COSMOS_V1 port; verified vs Skyfield/JPL Horizons in
                // its tests). Fixed at 2026-06-09 17:00 UTC (Nassau solar noon) so the bank is
                // daylit for verification; swap to SystemTime::now()→JD for the live sky.
                let jd = render::cosmos::julian_day(2026, 6, 9, 17, 0, 0.0);
                let sun = render::cosmos::sun_push_constant(25.0443, -77.3504, jd);

                if self.frame_count % 240 == 0 {
                    info!("☀️ Shallow-water shader live · sun = [{}, {}, {}]", sun[0], sun[1], sun[2]);
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

/// Entry point - The Gate to the Chthonic Archive
fn main() -> Result<()> {
    // Initialize logging
    env_logger::Builder::from_env(
        env_logger::Env::default().default_filter_or("info")
    ).init();

    info!("╔══════════════════════════════════════════════════════════════════╗");
    info!("║   THE CHTHONIC ARCHIVE: TRIUMVIRATE ASCENSION                   ║");
    info!("║   Classification: ASC-NATIVE-CHAIN-RPG                          ║");
    info!("║   Engine: Rust/Vulkan 1.3 Native | Blockchain: Solana (Pending) ║");
    info!("╚══════════════════════════════════════════════════════════════════╝");

    // === PHASE 14: AXIOMATIC VERIFICATION (debug builds only) ===
    #[cfg(debug_assertions)]
    {
        info!("⚖️ Verifying Axiomatic Integrity (SSOT)...");
        let verifier = AxiomVerifier::new(
            ".github/copilot-instructions.md",
            "cc1d0f63b564f90861bea13995aaa445055fb8ac1d7b6965bc6700eb0e41ad1b"
        );
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

    info!("✅ World manifestation complete. {} matriarchs active. {} world layers manifested.",
          faction_registry.matriarchs.len(),
          faction_registry.districts.len());

    info!("✅ Data ingestion complete. {} entities ready for manifestation.",
          game_data.entities.len());

    // === PHASE 12.5: REPO-LOCAL cRPG CONTENT BRIDGE ===
    match inspect_game_tree("game") {
        Ok(game_tree) => log_game_tree_report(&game_tree),
        Err(e) => error!("⚠️ Game tree inspection failed: {}", e),
    }
    match load_game_schema_documents("game") {
        Ok(schema_docs) => {
            info!("📚 Loaded {} game schema documents into registry", schema_docs.len());
            faction_registry.schema_docs = schema_docs;
        }
        Err(e) => error!("⚠️ Schema document loading failed: {}", e),
    }

    let event_loop = EventLoop::new()?;
    let mut app = ArchiveApp::new(save_path, game_data, faction_registry);
    event_loop.run_app(&mut app)?;

    Ok(())
}
