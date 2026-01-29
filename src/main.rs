// ╔════════════════════════════════════════════════════════════════════════════╗
// ║  THE DECORATOR'S BLESSING: main.rs                                       ║
// ║  Vulkan rendering pipeline - visual truth incarnate                         ║
// ╠════════════════════════════════════════════════════════════════════════════╣
// ║  Spectral Frequency: RED                                                    ║
// ║  Architectural Role: 🏰 THE FORTRESS                                         ║
// ║  Purpose: The Chthonic Archive: Triumvirate Ascension                       ║
// ╠════════════════════════════════════════════════════════════════════════════╣
// ║  Cross-References (Bidirectional):                                      ║
// ║    (Standalone file - no detected dependencies)                          ║
// ╚════════════════════════════════════════════════════════════════════════════╝

//! The Chthonic Archive: Triumvirate Ascension
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
    event::{Event, WindowEvent},
    event_loop::EventLoop,
    window::WindowBuilder,
    dpi::LogicalSize,
};

// use data::loader::load_game_data;
use data::persistence::{load_game_state, save_game_state};
use data::factions::FactionRegistry;
use data::verifier::AxiomVerifier;
use render::{VulkanContext, Renderer};

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

    // === PHASE 14: AXIOMATIC VERIFICATION ===
    info!("⚖️ Verifying Axiomatic Integrity (SSOT)...");
    let verifier = AxiomVerifier::new(
        ".github/copilot-instructions.md", 
        "23658c449f09f3b2ad4d5cb7b94f2ecdcc4c64ae4a5de2d852872eef7f153b22"
    );
    if let Err(e) = verifier.verify_integrity() {
        error!("❌ AXIOMATIC FAILURE: {}", e);
        // In a production build, we might terminate here.
        // For development, we log and proceed with caution.
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
    
    // === PHASE 2: CREATE WINDOW ===
    info!("🖼️  Initializing windowing system...");
    let event_loop = EventLoop::new()?;
    
    let window = WindowBuilder::new()
        .with_title("The Chthonic Archive: Triumvirate Ascension 🔺")
        .with_inner_size(LogicalSize::new(1280.0, 720.0))
        .with_resizable(true)
        .build(&event_loop)?;
    
    info!("✅ Window created: {}x{}", 1280, 720);
    
    // === PHASE 3: INITIALIZE VULKAN (Dynamic Rendering) ===
    info!("🔥 Initializing Vulkan 1.3 with Dynamic Rendering...");
    let vulkan_context = unsafe { VulkanContext::new(&window)? };
    
    // === PHASE 11: CREATE RENDERER ===
    info!("🎨 Creating rendering pipeline...");
    let window_size = window.inner_size();
    let mut renderer = unsafe { 
        Renderer::new(&vulkan_context, (window_size.width, window_size.height))?
    };

    info!("═══════════════════════════════════════════════════════════════════");
    info!("   🔥 PHASE 11 COMPLETE: DYNAMIC RENDERING PIPELINE ACTIVE 🔥");
    info!("   Mode: Dynamic Rendering (cmd_begin_rendering/cmd_end_rendering)");
    info!("   Shader: iso_grid.vert + iso_grid.frag → SPIR-V");
    info!("   Ready to render: Hello Triangle 🔺");
    info!("═══════════════════════════════════════════════════════════════════");
    
    // === PHASE 4: RUN EVENT LOOP ===
    let mut frame_count: u64 = 0;

    event_loop.run(move |event, elwt| {
        match event {
            Event::WindowEvent { event, .. } => match event {
                WindowEvent::CloseRequested => {
                    info!("👋 Window close requested. Terminating Archive.");
                    
                    // === PHASE 12: PERSISTENCE (Save on Exit) ===
                    if let Err(e) = save_game_state(save_path, &game_data) {
                        error!("❌ Failed to save game state: {}", e);
                    }

                    // Clean up renderer before exit
                    unsafe {
                        renderer.cleanup(&vulkan_context.device);
                    }
                    
                    elwt.exit();
                }
                WindowEvent::Resized(size) => {
                    // Only log meaningful resizes (not the initial DPI-scaled resize spam)
                    if size.width > 0 && size.height > 0 {
                        // Check if size actually changed from current swapchain
                        let current = renderer.swapchain.extent;
                        if size.width != current.width || size.height != current.height {
                            info!("📐 Window resized: {}x{} (was {}x{})", 
                                  size.width, size.height, current.width, current.height);
                            renderer.needs_resize = true;
                        }
                    }
                }
                WindowEvent::RedrawRequested => {
                    // Handle pending resize BEFORE rendering
                    if renderer.needs_resize {
                        let size = window.inner_size();
                        if size.width > 0 && size.height > 0 {
                            match unsafe {
                                renderer.handle_resize(&vulkan_context, (size.width, size.height))
                            } {
                                Ok(()) => {
                                    // Skip rendering this frame - wait for next redraw
                                    // This prevents immediate re-acquire after recreate
                                    return;
                                }
                                Err(e) => {
                                    error!("❌ Resize failed: {e:?}");
                                    return;
                                }
                            }
                        }
                        // Window minimized, skip rendering
                        return;
                    }

                    // PHASE 15: SPATIAL ACTUALIZATION
                    // Cycle through world layers colors every 120 frames
                    frame_count += 1;
                    let layer_num = ((frame_count / 120) % 6) + 1;
                    let layer_code = format!("LAYER-{}", layer_num);
                    
                    let layer_color = faction_registry.districts.get(&layer_code)
                        .map(|d| d.visual.primary_color)
                        .unwrap_or([0.69, 0.0, 0.96]); // Fallback Purple

                    let final_color = [layer_color[0], layer_color[1], layer_color[2], 1.0];

                    if frame_count % 120 == 0 {
                        info!("🎨 Manifesting Spectral Frequency for {}: [{}, {}, {}]", 
                              layer_code, layer_color[0], layer_color[1], layer_color[2]);
                    }

                    // RENDER THE FRAME! 🔺
                    match unsafe { renderer.render_frame(&vulkan_context, final_color) } {
                        Ok(needs_resize) => {
                            if needs_resize {
                                renderer.needs_resize = true;
                                // Request immediate redraw to handle resize
                                window.request_redraw();
                            }
                        }
                        Err(e) => {
                            error!("❌ Render failed: {e:?}");
                        }
                    }
                }
                _ => {}
            }
            Event::AboutToWait => {
                window.request_redraw();
            }
            _ => {}
        }
    })?;
    
    Ok(())
}
