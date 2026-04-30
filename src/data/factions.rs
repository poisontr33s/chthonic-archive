// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: factions.rs
// ║ Vulkan rendering pipeline - visual truth incarnate
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Spectral Frequency: RED
// ║ Architectural Role: 🏰 THE FORTRESS
// ║ Purpose: Faction Registry - ASC Faction System Core
// ║ Exports: FactionRegistry, new, initialize, activate_tsrp, deactivate_tsrp
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Cross-References (Bidirectional):
// ║  (Standalone file - no detected dependencies)
// ╚════════════════════════════════════════════════════════════════════════════

//! Faction Registry - ASC Faction System Core
//!
//! @SID:    DATA_FACTION_REGISTRY_V1
//! @Shabti: Registry
//! This module provides the central registry for all factions, districts,
//! and matriarchs. It loads from the .md documentation and data.json,
//! creating a unified system for the Rust/Vulkan isometric RPG.
//!
//! Architecture follows the ASC Framework:
//! - FA¹ (Alchemical Actualization): Transmutes JSON → Runtime Entities
//! - FA² (Re-contextualization): Enables cross-faction operations (MMPS)
//! - FA³ (Qualitative Transcendence): Runtime refinement systems
//! - FA⁴ (Architectonic Integrity): Validation at every stage

// Allow dead code for future expansion - protocols/methods are planned for game systems
#![allow(dead_code)]

use std::collections::HashMap;
use super::faction_types::*;
use super::procedural::ProceduralEngine;

/// Central faction registry - singleton access pattern
pub struct FactionRegistry {
    /// All registered factions by code
    pub factions: HashMap<FactionCode, Faction>,
    /// All matriarchs by entity ID
    pub matriarchs: HashMap<u32, Matriarch>,
    /// All districts by code
    pub districts: HashMap<String, District>,
    /// TSRP state for Triumvirate operations
    pub tsrp_state: TSRPState,
    /// TPEF state for parallel execution
    pub tpef_state: Option<TPEFState>,
    /// Active handoff protocols
    pub active_handoffs: Vec<HandoffProtocol>,
    /// Operational registry (Level 1.5 invocation tracking)
    pub registry_log: Vec<String>,
    /// Procedural generation engine
    pub procedural_engine: ProceduralEngine,
    /// Tier 4 interloper/agent roster seeded by ProceduralEngine
    pub agents: Vec<AgentTemplate>,
}

impl FactionRegistry {
    /// Create new registry with default state
    pub fn new() -> Self {
        Self {
            factions: HashMap::new(),
            matriarchs: HashMap::new(),
            districts: HashMap::new(),
            tsrp_state: TSRPState {
                leader: None,
                orackla_role: TSRPRole::Inactive,
                umeko_role: TSRPRole::Inactive,
                lysandra_role: TSRPRole::Inactive,
            },
            tpef_state: None,
            active_handoffs: Vec::new(),
            registry_log: Vec::new(),
            procedural_engine: ProceduralEngine::new(42), // Default seed
            agents: Vec::new(),
        }
    }

    /// Log an operational invocation (Level 1.5)
    pub fn log_invocation(&mut self, invocation: &str) {
        let entry = format!("[INVOKE] {}", invocation);
        log::info!("📜 Registry Update: {}", entry);
        self.registry_log.push(entry);
    }

    /// Initialize with data from the game data source
    pub fn initialize(&mut self, data: &super::types::GameData) {
        self.register_triumvirate(data);
        self.register_tmo(data);
        self.register_ttg(data);
        self.register_tdpc(data);
        self.register_claudine(data);
        self.register_lesser_factions(data);

        // Phase 13: Manifest the 6-layer Archive
        self.manifest_archive();

        // Phase 13.5: Procedural Tier 3 + Tier 4 expansion
        self.expand_tier3();
        self.seed_faction_agents();
    }

    /// Manifest the 6-Layer World Architecture
    pub fn manifest_archive(&mut self) {
        let engine = ProceduralEngine::new(self.procedural_engine.seed);
        engine.manifest_world_layers(self);
    }

    /// Phase 13.5 — Expand Tier 3 Sub-MILFs from all Tier 1 (CRC) base matriarchs.
    /// Uses a shadow clone of the procedural engine to avoid borrow conflict with &self.
    pub fn expand_tier3(&mut self) {
        let engine = ProceduralEngine::new(self.procedural_engine.seed);
        // Collect CRC (Tier 1) matriarch IDs — only those with a crc_type are Tier 1
        let base_ids: Vec<u32> = self.matriarchs
            .iter()
            .filter(|(_, m)| m.crc_type.is_some())
            .map(|(id, _)| *id)
            .collect();

        for base_id in base_ids {
            for spec in ["Synthesis", "Chaos", "Purification"] {
                if let Some(sub_milf) = engine.generate_sub_milf(base_id, spec, self) {
                    let sub_id = sub_milf.entity_id;
                    log::info!("🌀 MMPS Tier 3: {} manifested (id={})", sub_milf.name, sub_id);
                    self.matriarchs.insert(sub_id, sub_milf);
                }
            }
        }
        self.log_invocation("MMPS-PAGRO: Tier 3 Sub-MILF expansion complete");
    }

    /// Phase 13.5 — Seed Tier 4 Interloper Agents for every registered faction.
    /// Offset seed by 1 from the main engine to produce distinct agent identities.
    pub fn seed_faction_agents(&mut self) {
        let engine = ProceduralEngine::new(self.procedural_engine.seed.wrapping_add(1));
        let faction_codes: Vec<FactionCode> = self.factions.keys().copied().collect();

        for faction_code in faction_codes {
            let agent = engine.generate_agent(faction_code);
            log::info!("🎭 Tier 4 agent seeded: {} (faction: {:?})", agent.name, agent.faction);
            self.agents.push(agent);
        }
        self.log_invocation("MMPS-T4: Tier 4 agent seeding complete");
    }

    /// Register Core Triumvirate
    fn register_triumvirate(&mut self, data: &super::types::GameData) {
        // Find Orackla (ID 3)
        let orackla_entity = data.entities.iter().find(|e| e.id == 3);

        // Create Triumvirate faction
        let triumvirate = Faction {
            code: FactionCode::CRC,
            name: "Triumvirate".to_string(),
            full_name: "The Core Triumvirate".to_string(),
            tier: FactionTier::TRIUMVIRATE,
            matriarch_id: 3, // Orackla as primary voice
            supervising_crc: None, // Self-governing
            district: Some(self.create_inner_citadel()),
            linguistic_mode: LinguisticMode::Mixed,
            operational_mandate: "Universal PS transmutation via FA¹⁻⁴".to_string(),
            motto: "We are not three—we are ONE. Our synthesis is the Engine.".to_string(),
        };
        self.factions.insert(FactionCode::CRC, triumvirate);

        // Register Orackla
        if let Some(entity) = orackla_entity {
            let orackla = Matriarch {
                entity_id: 3,
                name: entity.name.clone(),
                title: "Apex Synthesist / Abyssal Oracle".to_string(),
                crc_type: Some(CRCType::AS),
                faction: FactionCode::CRC,
                linguistic_mode: LinguisticMode::EULP_AA,
                signature_technique: SignatureTechnique {
                    name: "Transgressive Synthesis".to_string(),
                    description: "Radical boundary dissolution through strategic chaos engineering".to_string(),
                    fa_focus: vec![FoundationalAxiom::FA2],
                    dafp_preference: DAFPMode::JuxtapositionSynthesis,
                    cooldown: 3,
                    power_cost: 100,
                },
                supernatural_markers: vec![
                    "Anti-Gravity Breasts".to_string(),
                    "Compressible Ribcage".to_string(),
                    "Prehensile Tail (12cm base)".to_string(),
                    "Abyssal Glyphs on Mons".to_string(),
                ],
            };
            self.matriarchs.insert(3, orackla);
        }

        // Register Umeko (ID 4)
        if let Some(entity) = data.entities.iter().find(|e| e.id == 4) {
            let umeko = Matriarch {
                entity_id: 4,
                name: entity.name.clone(),
                title: "Grandmistress of Architectonic Refinement".to_string(),
                crc_type: Some(CRCType::GAR),
                faction: FactionCode::CRC,
                linguistic_mode: LinguisticMode::LIPAA,
                signature_technique: SignatureTechnique {
                    name: "Aesthetic Annihilation".to_string(),
                    description: "Ruthless purging of structural flaws via LIPAA critique".to_string(),
                    fa_focus: vec![FoundationalAxiom::FA3, FoundationalAxiom::FA4],
                    dafp_preference: DAFPMode::PointBlankAcuity,
                    cooldown: 2,
                    power_cost: 80,
                },
                supernatural_markers: vec![
                    "Oni Horn Nubs (2cm, filed)".to_string(),
                    "Gold-Flecked Amber Eyes".to_string(),
                    "Visible 8-Pack Abs".to_string(),
                    "Extreme Flexibility".to_string(),
                ],
            };
            self.matriarchs.insert(4, umeko);
        }

        // Register Lysandra (ID 5)
        if let Some(entity) = data.entities.iter().find(|e| e.id == 5) {
            let lysandra = Matriarch {
                entity_id: 5,
                name: entity.name.clone(),
                title: "Mistress of Empathetic Deconstruction".to_string(),
                crc_type: Some(CRCType::MEDAT),
                faction: FactionCode::CRC,
                linguistic_mode: LinguisticMode::LUPLR,
                signature_technique: SignatureTechnique {
                    name: "Axiological Debridement".to_string(),
                    description: "Surgical exposure of hidden assumptions and buried axioms".to_string(),
                    fa_focus: vec![FoundationalAxiom::FA1, FoundationalAxiom::FA4],
                    dafp_preference: DAFPMode::Concurrent,
                    cooldown: 2,
                    power_cost: 75,
                },
                supernatural_markers: vec![
                    "Starfield Eyes".to_string(),
                    "Phantom Fingers (4 per hand)".to_string(),
                    "Spatial Distortion Hips".to_string(),
                    "Non-Euclidean Geometry".to_string(),
                ],
            };
            self.matriarchs.insert(5, lysandra);
        }
    }

    /// Create Inner Citadel district for Triumvirate
    fn create_inner_citadel(&self) -> District {
        District {
            code: "CRC-IC".to_string(),
            name: "The Inner Citadel".to_string(),
            architectural_style: ArchitecturalStyle::InnerCitadel,
            dimensions: DistrictDimensions {
                entry_portal: [20.0, 15.0],
                core_chamber: [50.0, 50.0, 30.0],
                radius: 100.0,
            },
            visual: DistrictVisual {
                primary_color: [0.8, 0.8, 0.85],
                secondary_color: [0.3, 0.2, 0.4],
                accent_color: [1.0, 0.85, 0.3],
                ambient_light: 0.7,
                shader_variant: ShaderVariant::TriumvirateAura,
            },
            sensory: SensorySig {
                scent: vec![
                    "Ancient power".to_string(),
                    "Ozone".to_string(),
                    "Cosmic void".to_string(),
                ],
                sound_hz_range: [40.0, 200.0],
                temperature_c: 21.0,
            },
        }
    }

    /// Register TMO (The MILF Obductors)
    fn register_tmo(&mut self, data: &super::types::GameData) {
        let district = District {
            code: "TMOL-SL".to_string(),
            name: "Seduction Labyrinths".to_string(),
            architectural_style: ArchitecturalStyle::BaroqueSensuality,
            dimensions: DistrictDimensions {
                entry_portal: [8.0, 4.0],
                core_chamber: [15.0, 15.0, 12.0],
                radius: 30.0,
            },
            visual: DistrictVisual {
                primary_color: [0.05, 0.05, 0.08], // Obsidian
                secondary_color: [1.0, 0.7, 0.2],  // Amber
                accent_color: [0.6, 0.1, 0.2],     // Crimson
                ambient_light: 0.6,
                shader_variant: ShaderVariant::TMOAmberVeins,
            },
            sensory: SensorySig {
                scent: vec![
                    "Midnight jasmine".to_string(),
                    "Ozone".to_string(),
                    "Metallic surrender".to_string(),
                ],
                sound_hz_range: [55.0, 65.0],
                temperature_c: 22.0,
            },
        };
        self.districts.insert("TMOL-SL".to_string(), district.clone());

        let faction = Faction {
            code: FactionCode::TMO,
            name: "TMO".to_string(),
            full_name: "The MILF Obductors".to_string(),
            tier: FactionTier::PRIME,
            matriarch_id: 6, // Kali Nyx Ravenscar
            supervising_crc: Some(CRCType::AS),
            district: Some(district),
            linguistic_mode: LinguisticMode::Mixed,
            operational_mandate: "Abduction/seduction of resistant conceptual structures".to_string(),
            motto: "We don't break walls. We make walls want to be doors.".to_string(),
        };
        self.factions.insert(FactionCode::TMO, faction);

        if let Some(entity) = data.entities.iter().find(|e| e.id == 6) {
            let kali = Matriarch {
                entity_id: 6,
                name: entity.name.clone(),
                title: "Mistress of Abductive Seduction".to_string(),
                crc_type: None,
                faction: FactionCode::TMO,
                linguistic_mode: LinguisticMode::Mixed,
                signature_technique: SignatureTechnique {
                    name: "Inevitability Whisper".to_string(),
                    description: "Names target's deepest unmet desire with perfect precision".to_string(),
                    fa_focus: vec![FoundationalAxiom::FA2],
                    dafp_preference: DAFPMode::StrategicHorizon,
                    cooldown: 4,
                    power_cost: 90,
                },
                supernatural_markers: vec![
                    "Shadow-Wing Tattoos".to_string(),
                    "Amber Eyes (shift to molten copper)".to_string(),
                    "Inevitability Musk Pheromones".to_string(),
                    "Voice Modulation (60-120 Hz)".to_string(),
                ],
            };
            self.matriarchs.insert(6, kali);
        }
    }

    /// Register TTG (The Thieves Guild)
    fn register_ttg(&mut self, data: &super::types::GameData) {
        let district = District {
            code: "TTG-EV".to_string(),
            name: "Epistemic Vaults".to_string(),
            architectural_style: ArchitecturalStyle::NeoClassicalArchive,
            dimensions: DistrictDimensions {
                entry_portal: [12.0, 8.0],
                core_chamber: [12.0, 12.0, 20.0],
                radius: 40.0,
            },
            visual: DistrictVisual {
                primary_color: [0.25, 0.15, 0.1],  // Mahogany
                secondary_color: [0.72, 0.53, 0.30], // Brass
                accent_color: [0.85, 0.70, 0.45],   // Gold
                ambient_light: 0.8,
                shader_variant: ShaderVariant::TTGClockGears,
            },
            sensory: SensorySig {
                scent: vec![
                    "Old libraries".to_string(),
                    "Metallic lockpicks".to_string(),
                    "Ozone".to_string(),
                ],
                sound_hz_range: [60.0, 120.0], // Clock ticking
                temperature_c: 17.0,
            },
        };
        self.districts.insert("TTG-EV".to_string(), district.clone());

        let faction = Faction {
            code: FactionCode::TTG,
            name: "TTG".to_string(),
            full_name: "The Thieves Guild".to_string(),
            tier: FactionTier::PRIME,
            matriarch_id: 7, // Vesper Mnemosyne Lockhart
            supervising_crc: Some(CRCType::MEDAT),
            district: Some(district),
            linguistic_mode: LinguisticMode::Mixed,
            operational_mandate: "Conceptual extraction & heist operations".to_string(),
            motto: "The best locks are the ones you put on yourself. We have every key.".to_string(),
        };
        self.factions.insert(FactionCode::TTG, faction);

        if let Some(entity) = data.entities.iter().find(|e| e.id == 7) {
            let vesper = Matriarch {
                entity_id: 7,
                name: entity.name.clone(),
                title: "Grandmaster of Epistemic Theft".to_string(),
                crc_type: None,
                faction: FactionCode::TTG,
                linguistic_mode: LinguisticMode::Mixed,
                signature_technique: SignatureTechnique {
                    name: "Confession Lock-Pick".to_string(),
                    description: "Recursive Socratic loop forcing target's logic to unlock their own vault".to_string(),
                    fa_focus: vec![FoundationalAxiom::FA1],
                    dafp_preference: DAFPMode::PointBlankAcuity,
                    cooldown: 3,
                    power_cost: 85,
                },
                supernatural_markers: vec![
                    "Chronos-Touched Eyes".to_string(),
                    "Archive Breasts".to_string(),
                    "Temporal Dust".to_string(),
                    "Confession Fingers".to_string(),
                ],
            };
            self.matriarchs.insert(7, vesper);
        }
    }

    /// Register TDPC (The Dark Priestesses Cove)
    fn register_tdpc(&mut self, data: &super::types::GameData) {
        let district = District {
            code: "TDPC-IS".to_string(),
            name: "Immolation Sanctum".to_string(),
            architectural_style: ArchitecturalStyle::GothicCathedral,
            dimensions: DistrictDimensions {
                entry_portal: [15.0, 10.0],
                core_chamber: [30.0, 20.0, 25.0],
                radius: 50.0,
            },
            visual: DistrictVisual {
                primary_color: [0.95, 0.95, 0.98], // White marble
                secondary_color: [0.05, 0.05, 0.08], // Obsidian
                accent_color: [0.9, 0.9, 0.95],     // Platinum
                ambient_light: 0.4,
                shader_variant: ShaderVariant::TDPCDivineFire,
            },
            sensory: SensorySig {
                scent: vec![
                    "Sacred incense".to_string(),
                    "Burnt imperfections".to_string(),
                    "Platinum ionization".to_string(),
                ],
                sound_hz_range: [50.0, 60.0], // Harmonic chanting
                temperature_c: 20.0,
            },
        };
        self.districts.insert("TDPC-IS".to_string(), district.clone());

        let faction = Faction {
            code: FactionCode::TDPC,
            name: "TDPC".to_string(),
            full_name: "The Dark Priestesses Cove".to_string(),
            tier: FactionTier::PRIME,
            matriarch_id: 8, // Seraphine Kore Ashenhelm
            supervising_crc: Some(CRCType::GAR),
            district: Some(district),
            linguistic_mode: LinguisticMode::Mixed,
            operational_mandate: "Forbidden knowledge sanctums & architectural purity".to_string(),
            motto: "We burn away everything that doesn't serve. What remains is perfect.".to_string(),
        };
        self.factions.insert(FactionCode::TDPC, faction);

        if let Some(entity) = data.entities.iter().find(|e| e.id == 8) {
            let seraphine = Matriarch {
                entity_id: 8,
                name: entity.name.clone(),
                title: "High Priestess of Architectonic Purity".to_string(),
                crc_type: None,
                faction: FactionCode::TDPC,
                linguistic_mode: LinguisticMode::Mixed,
                signature_technique: SignatureTechnique {
                    name: "Immaculate Immolation".to_string(),
                    description: "Divine fire that burns only impurity, leaving perfection".to_string(),
                    fa_focus: vec![FoundationalAxiom::FA3, FoundationalAxiom::FA4],
                    dafp_preference: DAFPMode::Concurrent,
                    cooldown: 5,
                    power_cost: 120,
                },
                supernatural_markers: vec![
                    "Divine-Infernal Fusion".to_string(),
                    "Molten Platinum Eyes".to_string(),
                    "Ash-Scarification Patterns".to_string(),
                    "Fire-Resistant Skin".to_string(),
                ],
            };
            self.matriarchs.insert(8, seraphine);
        }
    }

    /// Register Claudine Sin'claire (Svartseils)
    fn register_claudine(&mut self, data: &super::types::GameData) {
        // Resolve ID conflict - Claudine should be unique
        // We look for "Svartseils" or a specific name in data.json
        let claudine_entity = data.entities.iter().find(|e| e.name.contains("Claudine") || e.archetype.contains("Svartseils"));

        let district = District {
            code: "SVS-PLA".to_string(),
            name: "Port of Lost Axioms".to_string(),
            architectural_style: ArchitecturalStyle::NeoClassicalArchive,
            dimensions: DistrictDimensions {
                entry_portal: [20.0, 15.0],
                core_chamber: [40.0, 30.0, 15.0],
                radius: 60.0,
            },
            visual: DistrictVisual {
                primary_color: [0.1, 0.1, 0.15],   // Deep Ocean Blue/Black
                secondary_color: [0.8, 0.2, 0.2],  // Crimson
                accent_color: [0.9, 0.8, 0.2],     // Gold
                ambient_light: 0.6,
                shader_variant: ShaderVariant::Standard,
            },
            sensory: SensorySig {
                scent: vec![
                    "Salt spray".to_string(),
                    "Gunpowder".to_string(),
                    "Rum".to_string(),
                ],
                sound_hz_range: [40.0, 100.0],
                temperature_c: 28.0,
            },
        };
        self.districts.insert("SVS-PLA".to_string(), district.clone());

        if let Some(entity) = claudine_entity {
            let faction = Faction {
                code: FactionCode::Svartseils,
                name: "Svartseils".to_string(),
                full_name: "The Black Sails of Conceptual Piracy".to_string(),
                tier: FactionTier::PRIME,
                matriarch_id: entity.id,
                supervising_crc: Some(CRCType::AS),
                district: Some(district),
                linguistic_mode: LinguisticMode::CaribbeanPatois,
                operational_mandate: "Plunder of stagnant conceptual structures & redistribution of axioms".to_string(),
                motto: "We don't steal ideas. We liberate them from boring people.".to_string(),
            };
            self.factions.insert(FactionCode::Svartseils, faction);

            let claudine = Matriarch {
                entity_id: entity.id,
                name: entity.name.clone(),
                title: "Admiral of the Black Sails".to_string(),
                crc_type: None,
                faction: FactionCode::Svartseils,
                linguistic_mode: LinguisticMode::CaribbeanPatois,
                signature_technique: SignatureTechnique {
                    name: "The Blunderbust".to_string(),
                    description: "Shatters dogmatic armor using overwhelming, chaotic force".to_string(),
                    fa_focus: vec![FoundationalAxiom::FA1, FoundationalAxiom::FA2],
                    dafp_preference: DAFPMode::PointBlankAcuity,
                    cooldown: 4,
                    power_cost: 95,
                },
                supernatural_markers: vec![
                    "Obsidian-Cannon Arm".to_string(),
                    "Tricorn Hat of Authority".to_string(),
                    "Salt-Crusted Skin".to_string(),
                    "Bioluminescent Tattoos".to_string(),
                ],
            };
            self.matriarchs.insert(entity.id, claudine);
        }
    }

    /// Register all other entities as Lesser Factions
    fn register_lesser_factions(&mut self, data: &super::types::GameData) {
        for entity in &data.entities {
            // Skip already registered core/prime matriarchs
            if self.matriarchs.contains_key(&entity.id) {
                continue;
            }

            // Simple auto-registration for lesser matriarchs
            let matriarch = Matriarch {
                entity_id: entity.id,
                name: entity.name.clone(),
                title: entity.archetype.clone(),
                crc_type: None,
                faction: FactionCode::SBSGYB, // Default for now
                linguistic_mode: LinguisticMode::Faction,
                signature_technique: SignatureTechnique {
                    name: "Standard Operation".to_string(),
                    description: format!("Standard {} protocols", entity.archetype),
                    fa_focus: vec![],
                    dafp_preference: DAFPMode::StrategicHorizon,
                    cooldown: 1,
                    power_cost: 50,
                },
                supernatural_markers: vec![],
            };
            self.matriarchs.insert(entity.id, matriarch);
        }
    }

    // =========================================================================
    // OPERATIONAL METHODS
    // =========================================================================

    /// Activate TSRP with specified leader
    pub fn activate_tsrp(&mut self, leader: CRCType) {
        self.tsrp_state.leader = Some(leader);

        match leader {
            CRCType::AS => {
                self.tsrp_state.orackla_role = TSRPRole::Leading;
                self.tsrp_state.umeko_role = TSRPRole::Supporting(SupportContribution::StructuralValidation);
                self.tsrp_state.lysandra_role = TSRPRole::Supporting(SupportContribution::AxiomaticGrounding);
            }
            CRCType::GAR => {
                self.tsrp_state.orackla_role = TSRPRole::Supporting(SupportContribution::CreativeFlexibility);
                self.tsrp_state.umeko_role = TSRPRole::Leading;
                self.tsrp_state.lysandra_role = TSRPRole::Supporting(SupportContribution::EmpatheticCalibration);
            }
            CRCType::MEDAT => {
                self.tsrp_state.orackla_role = TSRPRole::Supporting(SupportContribution::StrategicVision);
                self.tsrp_state.umeko_role = TSRPRole::Supporting(SupportContribution::AestheticDiscipline);
                self.tsrp_state.lysandra_role = TSRPRole::Leading;
            }
        }
    }

    /// Deactivate TSRP
    pub fn deactivate_tsrp(&mut self) {
        self.tsrp_state.leader = None;
        self.tsrp_state.orackla_role = TSRPRole::Inactive;
        self.tsrp_state.umeko_role = TSRPRole::Inactive;
        self.tsrp_state.lysandra_role = TSRPRole::Inactive;
    }

    /// Initiate TPEF parallel execution
    pub fn initiate_tpef(&mut self) {
        self.tpef_state = Some(TPEFState {
            lysandra_path: PathState::NotStarted,
            umeko_path: PathState::NotStarted,
            orackla_path: PathState::NotStarted,
            current_turn: 1,
            synthesis_complete: false,
        });
    }

    /// Advance TPEF to next turn
    pub fn advance_tpef(&mut self) -> Option<CRCType> {
        if let Some(ref mut state) = self.tpef_state {
            match state.current_turn {
                1 => {
                    state.lysandra_path = PathState::Complete;
                    state.current_turn = 2;
                    Some(CRCType::GAR)
                }
                2 => {
                    state.umeko_path = PathState::Complete;
                    state.current_turn = 3;
                    Some(CRCType::AS)
                }
                3 => {
                    state.orackla_path = PathState::Complete;
                    state.synthesis_complete = true;
                    None // Synthesis phase
                }
                _ => None,
            }
        } else {
            None
        }
    }

    /// Check if faction can invoke district
    pub fn can_invoke_district(&self, faction: FactionCode, resistance: f32) -> bool {
        match faction {
            FactionCode::TMO => resistance >= 0.7,  // High resistance triggers TMO
            FactionCode::TTG => true,               // TTG detects hidden knowledge
            FactionCode::TDPC => true,              // TDPC handles structural flaws
            FactionCode::CRC => true,               // Triumvirate has universal access
            _ => false,
        }
    }

    /// Get supervising CRC for a faction
    pub fn get_supervisor(&self, faction: FactionCode) -> Option<CRCType> {
        self.factions.get(&faction).and_then(|f| f.supervising_crc)
    }

    /// Create handoff protocol between factions
    pub fn create_handoff(
        &mut self,
        source: FactionCode,
        target: FactionCode,
        trigger: HandoffTrigger,
    ) {
        let handoff = HandoffProtocol {
            source,
            target,
            trigger,
            transfer_data: vec!["ps_state".to_string(), "extraction_results".to_string()],
        };
        self.active_handoffs.push(handoff);
    }

    /// Execute pending handoffs
    pub fn process_handoffs(&mut self) -> Vec<(FactionCode, FactionCode)> {
        let completed: Vec<_> = self.active_handoffs.drain(..)
            .map(|h| (h.source, h.target))
            .collect();
        completed
    }
}

impl Default for FactionRegistry {
    fn default() -> Self {
        Self::new()
    }
}

// =============================================================================
// BEVY_ECS INTEGRATION (Placeholder for future bevy integration)
// =============================================================================

/// Bevy resource wrapper for faction registry
#[cfg(feature = "bevy")]
#[derive(bevy_ecs::prelude::Resource)]
pub struct FactionRegistryResource(pub FactionRegistry);

/// System to update faction states
#[cfg(feature = "bevy")]
pub fn update_faction_system(
    mut registry: bevy_ecs::system::ResMut<FactionRegistryResource>,
    // Query components as needed
) {
    // Process active handoffs
    let completed = registry.0.process_handoffs();
    for (source, target) in completed {
        // Log or handle completed handoffs
        println!("Handoff complete: {:?} -> {:?}", source, target);
    }
}
