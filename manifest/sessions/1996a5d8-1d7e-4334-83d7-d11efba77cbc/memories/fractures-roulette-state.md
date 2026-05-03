# Fractures Family — Eulian TODO-Roulette State
## Session: 2026-04-30

## Completed
- ✅ **Σ-0** (F-γ Boot Oath): `main.rs` — AxiomVerifier gated behind `#[cfg(debug_assertions)]`. Release binary no longer swears dev-governance oath.
- ✅ **Σ-1** (F-β Foreign Key): `factions.rs` — all 6 integer SSOT foreign key lookups replaced with name-based lookups. `entity_id` and `matriarchs.insert` keys now use `entity.id`. Claudine's `register_claudine()` already used name-based lookup — no change needed there. `cargo check` clean after both.

## ALL Σ CLOSED — cargo check clean (zero warnings)

Σ-2: Created `src/data/lore_types.rs` — `CombatAbility`, `LoreCharacterOverlay`, `ChainEntry`, `FactionBonuses`, `LoreTriumvirate`, `LorePrimeFactionEntry`, `LorePrimeFactionsFile`.
Σ-3: Created `src/data/lore_loader.rs` — `load_lore_characters()`, `load_lore_triumvirate()`, `load_lore_prime_factions()`. Registered in `mod.rs`.
Σ-3 wire: `FactionRegistry` now has `lore_characters: HashMap<String, LoreCharacterOverlay>`, `lore_triumvirate: Option<LoreTriumvirate>`, `lore_prime_factions: Vec<LorePrimeFactionEntry>`, `schema_docs: Vec<GameSchemaDocument>`. `initialize()` calls `merge_lore("game")` as Phase 13.6.
Σ-4: `game_schemas.rs` now scans `game/lore/characters/` + `game/lore/factions/` (not phantom stub paths). `main.rs` Phase 12.5 stores schema docs into `faction_registry.schema_docs` instead of log sink.

## Closure Condition
After Σ-4: `¬dev_oath_in_release ∧ ¬SSOT_integer_FK ∧ ∀m: m.combat_abilities≠∅ ∧ ∀f: f.spectral≠0 ∧ Phase12.5_loads_content > 0`

## Remaining Integer Literals in factions.rs (cosmetic, not lookup keys)
- `Faction::matriarch_id: 3` (in triumvirate faction def, before orackla entity block — can use `orackla_entity.map_or(3, |e| e.id)` if needed)
- `Faction::matriarch_id: 6/7/8` for TMO/TTG/TDPC — same pattern
- These are data fields, not HashMap lookup keys — lower priority than Σ-2

## Key file paths for Σ-2
- `src/data/types.rs` — `Entity` struct (no abilities/chains/bonuses fields — needs lore overlay)
- `src/data/loader.rs` — add `load_lore_characters()`
- `src/data/factions.rs` — add merge pass after `register_*()` calls in `initialize()`
- `game/lore/characters/orackla.json` has: `combat_abilities[{id, ki_cost, formula, targeting, status}]`
