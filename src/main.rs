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

use data::loader::load_game_data;
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
    
    // === PHASE 1: LOAD GAME DATA ===
    info!("📥 Loading game data from assets/data.json...");
    let game_data = load_game_data("assets/data.json")?;
    
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
    event_loop.run(move |event, elwt| {
        match event {
            Event::WindowEvent { event, .. } => match event {
                WindowEvent::CloseRequested => {
                    info!("👋 Window close requested. Terminating Archive.");
                    
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
                                    error!("❌ Resize failed: {:?}", e);
                                    return;
                                }
                            }
                        } else {
                            // Window minimized, skip rendering
                            return;
                        }
                    }

                    // RENDER THE FRAME! 🔺
                    match unsafe { renderer.render_frame(&vulkan_context) } {
                        Ok(needs_resize) => {
                            if needs_resize {
                                renderer.needs_resize = true;
                                // Request immediate redraw to handle resize
                                window.request_redraw();
                            }
                        }
                        Err(e) => {
                            error!("❌ Render failed: {:?}", e);
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
