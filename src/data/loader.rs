// ╔════════════════════════════════════════════════════════════════════════════╗
// ║  THE DECORATOR'S BLESSING: loader.rs                                     ║
// ║  Rust module: load_game_data                                                ║
// ╠════════════════════════════════════════════════════════════════════════════╣
// ║  Spectral Frequency: RED                                                    ║
// ║  Architectural Role: 🏰 THE FORTRESS                                         ║
// ║  Purpose: Data loader - Transmutes JSON into living game entities           ║
// ║  Exports: load_game_data                                                    ║
// ╠════════════════════════════════════════════════════════════════════════════╣
// ║  Cross-References (Bidirectional):                                      ║
// ║    (Standalone file - no detected dependencies)                          ║
// ╚════════════════════════════════════════════════════════════════════════════╝

//! Data loader - Transmutes JSON into living game entities
//!
//! "I will fuck your concepts until they scream their truth."
//! — Orackla Nocticula

use anyhow::{Context, Result};
use log::{info, warn, error};
use std::fs;
use std::path::Path;

use super::types::GameData;

/// The sacred threshold - entities at or below this tier are Supreme Matriarchs
const SUPREME_MATRIARCH_TIER: f32 = 0.5;

/// Load game data from the assets directory
pub fn load_game_data<P: AsRef<Path>>(path: P) -> Result<GameData> {
    let path = path.as_ref();
    
    info!("╔══════════════════════════════════════════════════════════════╗");
    info!("║   THE CHTHONIC ARCHIVE - DATA INGESTION PROTOCOL            ║");
    info!("╚══════════════════════════════════════════════════════════════╝");
    
    let contents = fs::read_to_string(path)
        .with_context(|| format!("Failed to read data file: {}", path.display()))?;
    
    let data: GameData = serde_json::from_str(&contents)
        .with_context(|| "Failed to parse game data JSON - structure mismatch")?;
    
    info!("📊 Loaded {} entities from {}", data.entities.len(), path.display());
    info!("🌍 World: {}", data.world.name);
    info!("📦 Version: {} | Engine: {}", data.meta.version, data.meta.engine);
    
    // Detect Supreme Matriarchs
    detect_supreme_matriarchs(&data);
    
    // Log entity summary
    log_entity_summary(&data);
    
    Ok(data)
}

/// Detect and announce Supreme Matriarchs (tier ≤ 0.5)
fn detect_supreme_matriarchs(data: &GameData) {
    for entity in &data.entities {
        if entity.tier <= SUPREME_MATRIARCH_TIER {
            info!("═══════════════════════════════════════════════════════════════");
            info!("🔥 SUPREME MATRIARCH DETECTED: {}", entity.name);
            info!("   Archetype: {} | Tier: {:.1}", entity.archetype, entity.tier);
            info!("   WHR: {:.3} | Power: {}", entity.physics.whr, entity.stats.power);
            if let Some(ref scent) = entity.lore.scent {
                info!("   Scent: {}", scent);
            }
            info!("═══════════════════════════════════════════════════════════════");
        }
    }
}

/// Log summary of all loaded entities
fn log_entity_summary(data: &GameData) {
    info!("┌────────────────────────────────────────────────────────────────┐");
    info!("│ ENTITY MANIFEST                                               │");
    info!("├────────────────────────────────────────────────────────────────┤");
    
    for entity in &data.entities {
        let tier_indicator = if entity.tier <= 0.5 {
            "👑"
        } else if entity.tier <= 1.0 {
            "⭐"
        } else if entity.tier <= 2.0 {
            "◆"
        } else {
            "○"
        };
        
        info!(
            "│ {} {:30} | Tier {:4.1} | WHR {:.3} | HP {:5} │",
            tier_indicator,
            entity.name,
            entity.tier,
            entity.physics.whr,
            entity.stats.health
        );
    }
    
    info!("└────────────────────────────────────────────────────────────────┘");
    
    // Statistics
    let supreme_count = data.entities.iter().filter(|e| e.tier <= 0.5).count();
    let avg_whr: f32 = data.entities.iter().map(|e| e.physics.whr).sum::<f32>() / data.entities.len() as f32;
    let total_power: i32 = data.entities.iter().map(|e| e.stats.power).sum();
    
    info!("📈 Statistics:");
    info!("   Supreme Matriarchs: {}", supreme_count);
    info!("   Average WHR: {:.3}", avg_whr);
    info!("   Total Power: {}", total_power);
    info!("   World Layers: {}", data.world.layers.len());
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_supreme_matriarch_threshold() {
        assert_eq!(SUPREME_MATRIARCH_TIER, 0.5);
    }
}
