// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: procedural.rs
// ║ Vulkan rendering pipeline - visual truth incarnate
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Spectral Frequency: VIOLET
// ║ Architectural Role: 🌀 THE VORTEX
// ║ Purpose: Procedural Generation Engine - Phase 13
// ╠════════════════════════════════════════════════════════════════════════════
// ║ FA¹: Procedural Manifestation of World Layers & Tier 3/4 Entities
// ╚════════════════════════════════════════════════════════════════════════════

//! Procedural Generation Engine - Phase 13
//!
//! @SID:    DATA_PROCEDURAL_V1
//! @Shabti: Engine
//!
//! Implementing Section X (MMPS) and the 6-Layer World Architecture.
//! This module handles the dynamic expansion of the Chthonic Archive.

use rand::Rng;
use std::fmt;
use super::faction_types::*;
use super::factions::FactionRegistry;

/// Procedural generation toolset
pub struct ProceduralEngine {
    /// Random seed
    pub seed: u64,
}

impl ProceduralEngine {
    pub fn new(seed: u64) -> Self {
        Self { seed }
    }

    /// MMPS-PAGRO: Generate a Manifested Sub-MILF (Tier 3)
    /// $matriarch${base}+$type${specialization}
    #[allow(dead_code)] // TODO: Hook into the runtime Tier 3 manifestation flow.
    pub fn generate_sub_milf(
        &self,
        base_id: u32,
        specialization: &str,
        registry: &FactionRegistry,
    ) -> Option<Matriarch> {
        let base = registry.matriarchs.get(&base_id)?;

        let mut rng = rand::thread_rng();
        let suffix_id = rng.gen_range(1000..9999);
        let new_id = base_id * 10000 + suffix_id;

        log::info!("🌀 MMPS: Manifesting Sub-MILF from base {} with spec: {}", base.name, specialization);

        Some(Matriarch {
            entity_id: new_id,
            name: format!("{}: {}", base.name, specialization),
            title: format!("{} of {}", base.title, specialization),
            crc_type: None, // Sub-MILFs are Tier 3, not Tier 1
            faction: base.faction,
            linguistic_mode: base.linguistic_mode,
            signature_technique: SignatureTechnique {
                name: format!("{} ({})", base.signature_technique.name, specialization),
                description: format!("Specialized version of {}: {}", base.signature_technique.description, specialization),
                fa_focus: base.signature_technique.fa_focus.clone(),
                dafp_preference: base.signature_technique.dafp_preference,
                cooldown: base.signature_technique.cooldown + 1,
                power_cost: base.signature_technique.power_cost + 20,
            },
            supernatural_markers: base.supernatural_markers.clone(),
        })
    }

    /// Generate a Tier 4 Interloper Agent
    #[allow(dead_code)] // TODO: Hook into dynamic faction encounter generation.
    pub fn generate_agent(&self, faction_code: FactionCode) -> AgentTemplate {
        let mut rng = rand::thread_rng();
        let agent_id = rng.gen_range(50000..99999);

        let names = ["Calyx", "Rift", "Vane", "Kore", "Axis", "Null", "Echo", "Void"];
        let name = names[rng.gen_range(0..names.len())];

        AgentTemplate {
            id: agent_id,
            name: format!("{faction_code} Agent {name}"),
            faction: faction_code,
            chaos_utility: rng.gen_range(0.5..1.5),
            governance_cost: rng.gen_range(0.2..0.8),
        }
    }

    /// Manifest the 6 Layers of the Chthonic Archive
    pub fn manifest_world_layers(&self, registry: &mut FactionRegistry) {
        log::info!("🌍 Commencing Tetrahedral Resonance: Manifesting 6 World Layers...");

        self.manifest_layer1(registry);
        self.manifest_layer2(registry);
        self.manifest_layer3(registry);
        self.manifest_layer4(registry);
        self.manifest_layer5(registry);
        self.manifest_layer6(registry);

        registry.log_invocation("FA1-WORLD-MANIFEST: 6-Layer Architecture fully actualized.");
    }

    fn manifest_layer1(&self, registry: &mut FactionRegistry) {
        let d = District {
            code: "LAYER-1".to_string(),
            name: "The Resonance Gate".to_string(),
            architectural_style: ArchitecturalStyle::Custom,
            dimensions: DistrictDimensions {
                entry_portal: [12.0, 4.0],
                core_chamber: [12.0, 12.0, 4.0],
                radius: 12.0,
            },
            visual: DistrictVisual {
                primary_color: [0.1, 0.1, 0.1], // Obsidian
                secondary_color: [1.0, 1.0, 1.0], // Hinoki (White)
                accent_color: [0.5, 0.5, 0.5],
                ambient_light: 0.5,
                shader_variant: ShaderVariant::Standard,
            },
            sensory: SensorySig {
                scent: vec!["Hinoki".to_string(), "Cold Obsidian".to_string()],
                sound_hz_range: [432.0, 528.0],
                temperature_c: 18.0,
            },
        };
        registry.districts.insert("LAYER-1".to_string(), d);
    }

    fn manifest_layer2(&self, registry: &mut FactionRegistry) {
        let d = District {
            code: "LAYER-2".to_string(),
            name: "The Temporal Nexus".to_string(),
            architectural_style: ArchitecturalStyle::NeoClassicalArchive,
            dimensions: DistrictDimensions {
                entry_portal: [0.8, 0.8],
                core_chamber: [12.0, 12.0, 4.0],
                radius: 12.0,
            },
            visual: DistrictVisual {
                primary_color: [0.0, 0.0, 0.5], // Past (Blue)
                secondary_color: [1.0, 1.0, 1.0], // Present (White)
                accent_color: [0.8, 0.7, 0.2], // Future (Gold)
                ambient_light: 0.8,
                shader_variant: ShaderVariant::Standard,
            },
            sensory: SensorySig {
                scent: vec!["Old Paper".to_string(), "Ozone".to_string()],
                sound_hz_range: [20.0, 20000.0],
                temperature_c: 20.0,
            },
        };
        registry.districts.insert("LAYER-2".to_string(), d);
    }

    fn manifest_layer3(&self, registry: &mut FactionRegistry) {
        let d = District {
            code: "LAYER-3".to_string(),
            name: "The Conceptual Atrium".to_string(),
            architectural_style: ArchitecturalStyle::NeoClassicalArchive,
            dimensions: DistrictDimensions {
                entry_portal: [3.0, 3.0],
                core_chamber: [12.0, 12.0, 4.0],
                radius: 12.0,
            },
            visual: DistrictVisual {
                primary_color: [0.6, 0.4, 0.2], // Hinoki floor
                secondary_color: [0.1, 0.1, 0.1], // Obsidian walls
                accent_color: [0.3, 0.7, 1.0], // Glyph glow
                ambient_light: 0.6,
                shader_variant: ShaderVariant::TTGClockGears,
            },
            sensory: SensorySig {
                scent: vec!["Incense".to_string(), "Fresh Parchment".to_string()],
                sound_hz_range: [100.0, 300.0],
                temperature_c: 22.0,
            },
        };
        registry.districts.insert("LAYER-3".to_string(), d);
    }

    fn manifest_layer4(&self, registry: &mut FactionRegistry) {
        let d = District {
            code: "LAYER-4".to_string(),
            name: "The Synthesis Forge".to_string(),
            architectural_style: ArchitecturalStyle::Custom,
            dimensions: DistrictDimensions {
                entry_portal: [3.0, 3.0],
                core_chamber: [10.0, 10.0, 10.0],
                radius: 10.0,
            },
            visual: DistrictVisual {
                primary_color: [0.8, 0.2, 0.1], // Furnace Orange
                secondary_color: [0.05, 0.05, 0.05], // Deep Black
                accent_color: [1.0, 1.0, 0.0], // Molten Gold
                ambient_light: 0.9,
                shader_variant: ShaderVariant::TDPCDivineFire,
            },
            sensory: SensorySig {
                scent: vec!["Hot Metal".to_string(), "Coal Smoke".to_string()],
                sound_hz_range: [50.0, 500.0],
                temperature_c: 850.0, // High conceptual heat
            },
        };
        registry.districts.insert("LAYER-4".to_string(), d);
    }

    fn manifest_layer5(&self, registry: &mut FactionRegistry) {
        let d = District {
            code: "LAYER-5".to_string(),
            name: "The Strategic Observatory".to_string(),
            architectural_style: ArchitecturalStyle::Custom,
            dimensions: DistrictDimensions {
                entry_portal: [1.0, 2.5],
                core_chamber: [12.0, 12.0, 6.0],
                radius: 12.0,
            },
            visual: DistrictVisual {
                primary_color: [0.9, 1.0, 1.0], // Glass/Crystal
                secondary_color: [0.0, 0.0, 0.1], // Starfield
                accent_color: [1.0, 1.0, 1.0], // High clarity
                ambient_light: 0.9,
                shader_variant: ShaderVariant::Standard,
            },
            sensory: SensorySig {
                scent: vec!["Clear Air".to_string(), "Cold Glass".to_string()],
                sound_hz_range: [10.0, 50.0], // Subsonic vibrations
                temperature_c: 15.0,
            },
        };
        registry.districts.insert("LAYER-5".to_string(), d);
    }

    fn manifest_layer6(&self, registry: &mut FactionRegistry) {
        let d = District {
            code: "LAYER-6".to_string(),
            name: "The Abyssal Archive".to_string(),
            architectural_style: ArchitecturalStyle::Custom,
            dimensions: DistrictDimensions {
                entry_portal: [2.0, 2.0],
                core_chamber: [18.0, 18.0, 8.0],
                radius: 18.0,
            },
            visual: DistrictVisual {
                primary_color: [0.0, 0.0, 0.0], // Void Black
                secondary_color: [0.0, 0.2, 0.0], // Bioluminescent Green
                accent_color: [0.1, 0.1, 0.15], // Dark Water
                ambient_light: 0.1,
                shader_variant: ShaderVariant::Standard,
            },
            sensory: SensorySig {
                scent: vec!["Damp Stone".to_string(), "Fungi".to_string()],
                sound_hz_range: [1.0, 10.0], // Infrasound
                temperature_c: 12.0,
            },
        };
        registry.districts.insert("LAYER-6".to_string(), d);
    }
}

impl fmt::Display for FactionCode {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            FactionCode::CRC => f.write_str("CRC"),
            FactionCode::TMO => f.write_str("TMO"),
            FactionCode::TTG => f.write_str("TTG"),
            FactionCode::TDPC => f.write_str("TDPC"),
            FactionCode::Svartseils => f.write_str("SVS"),
            FactionCode::SBSGYB => f.write_str("SBS"),
            FactionCode::Custom(v) => write!(f, "CST{}", v),
        }
    }
}
