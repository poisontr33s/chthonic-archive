// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: persistence.rs
// ║ Rust module: save_game_state, load_game_state
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Spectral Frequency: RED
// ║ Architectural Role: 🏰 THE FORTRESS
// ║ Purpose: Entity Persistence - Level 1.5 Living Organism state management
// ║ Exports: save_game_state, load_game_state
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Cross-References (Bidirectional):
// ║  (Standalone file - no detected dependencies)
// ╚════════════════════════════════════════════════════════════════════════════

//! Entity Persistence - Level 1.5 Living Organism state management
//!
//! @SID:    DATA_PERSISTENCE_V1
//! @Shabti: Persistence
//! "What is written in the Archive remains manifest across the void."
//! — Dr. Lysandra Thorne

use anyhow::{Context, Result};
use log::info;
use std::fs;
use std::path::Path;

use super::types::GameData;

/// Save the current game state to a file
pub fn save_game_state<P: AsRef<Path>>(path: P, data: &GameData) -> Result<()> {
    let path = path.as_ref();
    info!("💾 Persisting world state to {path:?}...");

    let json = serde_json::to_string_pretty(data)
        .with_context(|| "Failed to serialize game state")?;

    fs::write(path, json)
        .with_context(|| format!("Failed to write save file: {0}", path.display()))?;

    info!("✅ Persistence complete. {} entities preserved.", data.entities.len());
    Ok(())
}

/// Load the game state from a file (or fall back to default)
pub fn load_game_state<P: AsRef<Path>>(path: P, default_path: P) -> Result<GameData> {
    let path = path.as_ref();
    let default_path = default_path.as_ref();

    if path.exists() {
        info!("📥 Loading persistent state from {path:?}...");
        let contents = fs::read_to_string(path)
            .with_context(|| format!("Failed to read save file: {0}", path.display()))?;

        let data: GameData = serde_json::from_str(&contents)
            .with_context(|| "Failed to parse persistent state JSON")?;

        Ok(data)
    } else {
        info!("⚠️ No persistent state found at {path:?}. Falling back to default: {default_path:?}");
        super::loader::load_game_data(default_path)
    }
}
