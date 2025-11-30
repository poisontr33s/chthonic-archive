// Auto-generated from ProjectMPW Export Service
// Date: 2025-11-30T17:35:02.099203
// Classification: ASC-NATIVE-CHAIN-RPG

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GameData {
    pub meta: MetaData,
    pub entities: Vec<Entity>,
    pub world: WorldData,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MetaData {
    pub version: String,
    pub engine: String,
    pub classification: String,
    pub exported_at: String,
    pub entity_count: usize,
    pub source: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Entity {
    pub id: u32,
    pub name: String,
    pub archetype: String,
    pub tier: f32,
    pub linguistic_mode: String,
    pub physics: PhysicsData,
    pub stats: GameStats,
    pub lore: LoreData,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PhysicsData {
    pub height_cm: f32,
    pub weight_kg: f32,
    pub whr: f32,
    pub bust_cm: f32,
    pub waist_cm: f32,
    pub hips_cm: f32,
    pub cup_size: String,
    pub bmi: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GameStats {
    pub health: i32,
    pub power: i32,
    pub defense: i32,
    pub conceptual_capacity: i32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LoreData {
    pub scent: Option<String>,
    pub word_count: Option<i32>,
    pub edfa_excerpt: Option<String>,
    pub edfa_full: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorldData {
    pub name: String,
    pub layers: Vec<WorldLayer>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorldLayer {
    pub id: u32,
    pub name: String,
    pub zone_type: String,
    pub dimensions_meters: [f32; 2],
    pub tier_requirement: Option<f32>,
    pub boss: Option<String>,
    pub description: String,
}

// Linguistic Mode Enum (for dialogue system)
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum LinguisticMode {
    EULP_AA,   // Orackla - Explicit/Transgressive
    LIPAA,     // Umeko - Precise/Commanding
    LUPLR,     // Lysandra - Analytical/Revelatory
    VISUAL,    // Decorator - Aesthetic/Overwhelming
    META,      // Savant - Player/God
    MIXED,     // Prime Factions
    FACTION,   // Lesser Factions
    DYNAMIC,   // Context-dependent
}

impl From<&str> for LinguisticMode {
    fn from(s: &str) -> Self {
        match s {
            "EULP_AA" => LinguisticMode::EULP_AA,
            "LIPAA" => LinguisticMode::LIPAA,
            "LUPLR" => LinguisticMode::LUPLR,
            "VISUAL" => LinguisticMode::VISUAL,
            "META" => LinguisticMode::META,
            "MIXED" => LinguisticMode::MIXED,
            "FACTION" => LinguisticMode::FACTION,
            _ => LinguisticMode::DYNAMIC,
        }
    }
}
