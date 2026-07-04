//! game-core -- the turn-contract kernel of the chthonic roguelite.
//!
//! Face-agnostic: pure turn logic plus an observe/act contract. The HUMAN face (cli-renderer
//! iso/ascii) and the AGENT face (MCP observe/act) both sit on this; the runestone stores it.
//! `observe()` returns the *same* picture whether a human renders it or an agent reads it as
//! JSON -- that symmetry is what lets both play the same game from opposite ends.
//!
//! Deterministic from `seed`: a run is reproducible, which is what makes it a roguelite the
//! agent can replay and the stone can re-forge.
//!
//! The world is the ankh_seeds canon (`.chthonic/ankh_seeds.yaml`), balanced 50/50 across the
//! heritage axis, and each principle resolves by its **verb** (Trade/Invoke/Weigh/Overturn/Strike).
//! The PLAYER is a CRC Tier-1 matriarch -- a `Class` whose stats are derived from the SSOT organ
//! canon (the heritage-root, NOT the derived JSONs) and which bends the verbs: Orackla plays
//! through force, Umeko through the wall, Lysandra through sight.

use serde::{Deserialize, Serialize};

pub const W: i32 = 8;
pub const H: i32 = 8;

#[derive(Clone, Copy, Serialize, Deserialize, PartialEq, Eq, Debug)]
pub enum Dir {
    North,
    South,
    East,
    West,
}

#[derive(Clone, Copy, Serialize, Deserialize, PartialEq, Eq, Debug)]
#[serde(tag = "kind")]
pub enum Action {
    Move { dir: Dir },
    Wait,
}

#[derive(Clone, Copy, Serialize, Deserialize, PartialEq, Eq, Debug)]
pub struct Pos {
    pub x: i32,
    pub y: i32,
}

/// Which half of the Ankhological heritage axis a seed anchors. The canon asks for a 50/50 balance
/// between the two (its `fusion_constraint`); `GameState::new` honors that when it spawns a world.
#[derive(Clone, Copy, Serialize, Deserialize, PartialEq, Eq, Debug)]
pub enum Heritage {
    Andean,
    Egyptologic,
}

/// A playable matriarch -- a CRC Tier-1 sovereign, verified against the SSOT organ canon (the
/// heritage-root table), NOT the derived JSONs. Each is an alchemical phase and a verb-philosophy.
/// Stats are derived from the SSOT *nature* (organ function + Magnum Opus phase), small scale, tunable.
#[derive(Clone, Copy, Serialize, Deserialize, PartialEq, Eq, Debug)]
pub enum Class {
    Orackla,  // Heart / Chaos (Nigredo) -- transgressive flow, primary pump: force + momentum
    Umeko,    // Lungs / Purification (Albedo) -- structural exhalation: the wall, the refusal
    Lysandra, // Stomach / Truth -- axiom absorption, deconstruction: sight, the reader
}

impl Class {
    /// (health, power, defense, insight) -- read from the SSOT nature, not the schema's numbers.
    pub fn stats(self) -> (i32, i32, i32, i32) {
        match self {
            Class::Orackla => (8, 5, 2, 3),  // glass cannon: hits hardest, falls fastest
            Class::Umeko => (10, 3, 5, 2),   // the wall: endures, shrugs, rejects
            Class::Lysandra => (7, 3, 3, 5), // the seer: invokes hardest, reads true
        }
    }
    pub fn name(self) -> &'static str {
        match self {
            Class::Orackla => "Orackla Nocticula",
            Class::Umeko => "Madam Umeko Ketsuraku",
            Class::Lysandra => "Dr. Lysandra Thorne",
        }
    }
    pub fn chain(self) -> &'static str {
        match self {
            Class::Orackla => "Chaos (Nigredo)",
            Class::Umeko => "Purification (Albedo)",
            Class::Lysandra => "Truth",
        }
    }
    /// Parse a class name (or its chain) from the CLI; `None` if unrecognized.
    pub fn parse(s: &str) -> Option<Class> {
        match s.to_lowercase().as_str() {
            "orackla" | "chaos" => Some(Class::Orackla),
            "umeko" | "purification" => Some(Class::Umeko),
            "lysandra" | "truth" => Some(Class::Lysandra),
            _ => None,
        }
    }
}

impl Default for Class {
    /// The seer -- a game about reading what a thing means, read by the class built to read.
    fn default() -> Self {
        Class::Lysandra
    }
}

/// One ankh_seed principle, borrowed from `.chthonic/ankh_seeds.yaml` -- the canon is the single
/// source, this is just the slice the game needs. An entity is a *principle*, not a monster.
#[derive(Clone, Serialize, Deserialize, Debug)]
pub struct Seed {
    pub label: String,
    pub principle: String,
    pub resonance_terms: Vec<String>,
    pub weight: f32,
    pub heritage: Heritage,
}

// --- canon loading: the yaml IS the world's source, compiled in so a run is the archive's own ---

#[derive(Deserialize)]
struct RawSeed {
    label: String,
    principle: String,
    resonance_terms: Vec<String>,
    weight: f32,
}

#[derive(Deserialize)]
struct AnkhCanon {
    andean_bce: Vec<RawSeed>,
    egyptologic_bce: Vec<RawSeed>,
}

/// The ten principles, parsed from the repo's own `ankh_seeds.yaml`. Borrowed, not re-authored:
/// edit the yaml and rebuild, and the world changes. Andean block first, then Egyptologic; the
/// fixed order keeps runs deterministic.
pub fn canon_seeds() -> Vec<Seed> {
    const RAW: &str = include_str!("../../../.chthonic/ankh_seeds.yaml");
    let canon: AnkhCanon = serde_yaml_ng::from_str(RAW)
        .expect("ankh_seeds.yaml must parse -- it is the canon the game is built on");
    let mut out = Vec::with_capacity(canon.andean_bce.len() + canon.egyptologic_bce.len());
    for s in canon.andean_bce {
        out.push(Seed {
            label: s.label,
            principle: s.principle,
            resonance_terms: s.resonance_terms,
            weight: s.weight,
            heritage: Heritage::Andean,
        });
    }
    for s in canon.egyptologic_bce {
        out.push(Seed {
            label: s.label,
            principle: s.principle,
            resonance_terms: s.resonance_terms,
            weight: s.weight,
            heritage: Heritage::Egyptologic,
        });
    }
    out
}

/// The verb a principle answers to, read from its meaning. Engaging it (moving into it) resolves
/// by this, not by uniform damage. Principles without a bespoke verb fall to "Strike" -- force.
fn verb_for(label: &str) -> &'static str {
    match label {
        "Ayni" => "Trade",
        "Heka" => "Invoke",
        "Ma'at" => "Weigh",
        "Pachakuti" => "Overturn",
        _ => "Strike",
    }
}

/// Pick `count` seeds from a heritage pool, chosen deterministically from the run seed.
fn pick<'a>(pool: &[&'a Seed], seed: u64, salt: u64, count: usize) -> Vec<&'a Seed> {
    if pool.is_empty() {
        return Vec::new();
    }
    let base = ((seed ^ salt) % pool.len() as u64) as usize;
    (0..count).map(|i| pool[(base + i * 2) % pool.len()]).collect()
}

/// The next free interior cell (x,y >= 1) in a deterministic probe order -- keeps the player's
/// origin and first step clear, and never lands two seeds on one tile.
fn free_interior_cell(seed: u64, salt: u64, used: &[Pos]) -> Pos {
    let span_x = (W - 2).max(1) as u64;
    let span_y = (H - 2).max(1) as u64;
    let mut k = seed ^ salt.wrapping_mul(0x9E37_79B9_7F4A_7C15);
    loop {
        let x = 1 + (k % span_x) as i32;
        let y = 1 + ((k / span_x) % span_y) as i32;
        let p = Pos { x, y };
        if !used.contains(&p) {
            return p;
        }
        k = k.wrapping_add(0x9E37_79B9_7F4A_7C15);
    }
}

#[derive(Clone, Serialize, Deserialize, Debug)]
pub struct Entity {
    pub id: u32,
    /// The seed's `label` -- the principle's name (e.g. "Ma'at", "Ayni"). Its first char is the glyph.
    pub seed: String,
    /// The principle itself, borrowed from canon -- what the agent actually faces, on its screen.
    pub principle: String,
    pub heritage: Heritage,
    /// How it resolves when engaged, read from its meaning: Trade / Invoke / Weigh / Overturn / Strike.
    pub verb: String,
    pub pos: Pos,
    /// Resistance -- seeded from the canon `weight`. A heavier principle is harder to overturn.
    pub hp: i32,
}

#[derive(Clone, Serialize, Deserialize, Debug)]
pub struct GameState {
    pub seed: u64, // the run's seed -- deterministic, replayable, stone-storable
    pub turn: u64,
    pub class: Class,
    pub player: Pos,
    pub hp: i32,       // current health -- starts at the class's health
    pub power: i32,    // force -- scales Strike (and feeds Orackla's momentum)
    pub defense: i32,  // the wall -- reduces damage taken
    pub insight: i32,  // meaning -- scales Invoke, sets the bar for Ma'at's alignment
    pub momentum: i32, // Orackla's transgressive flow -- builds on action, resets on Wait
    pub entities: Vec<Entity>,
    pub log: Vec<String>, // recent events, newest last
}

/// What a player -- human OR agent -- perceives this turn. The agent's entire screen.
#[derive(Serialize, Debug)]
pub struct Observation {
    pub turn: u64,
    pub class: String,
    pub chain: String,
    pub player: Pos,
    pub hp: i32,
    pub power: i32,
    pub defense: i32,
    pub insight: i32,
    pub momentum: i32,
    /// ASCII rows: '@' = player, a seed's initial = an entity, '.' = floor.
    pub grid: Vec<String>,
    pub entities: Vec<Entity>,
    pub legal_actions: Vec<String>,
    pub log_tail: Vec<String>,
}

impl GameState {
    /// Genesis with a chosen matriarch. Same seed + same class -> same run, always.
    pub fn new_as(seed: u64, class: Class) -> Self {
        let (health, power, defense, insight) = class.stats();
        let canon = canon_seeds();
        let andean: Vec<&Seed> = canon
            .iter()
            .filter(|s| s.heritage == Heritage::Andean)
            .collect();
        let egypt: Vec<&Seed> = canon
            .iter()
            .filter(|s| s.heritage == Heritage::Egyptologic)
            .collect();
        // Two from each heritage, interleaved, so the spawn set is 50/50 by construction.
        let a = pick(&andean, seed, 0xA5A5, 2);
        let e = pick(&egypt, seed, 0x5E5E, 2);
        let mut entities = Vec::new();
        let mut used: Vec<Pos> = Vec::new();
        let mut id = 1u32;
        for i in 0..a.len().max(e.len()) {
            for s in [a.get(i), e.get(i)].into_iter().flatten() {
                let pos = free_interior_cell(seed, id as u64, &used);
                used.push(pos);
                entities.push(Entity {
                    id,
                    seed: s.label.clone(),
                    principle: s.principle.clone(),
                    heritage: s.heritage,
                    verb: verb_for(&s.label).into(),
                    pos,
                    hp: (s.weight * 4.0).round() as i32,
                });
                id += 1;
            }
        }
        GameState {
            seed,
            turn: 0,
            class,
            player: Pos { x: 0, y: 0 },
            hp: health,
            power,
            defense,
            insight,
            momentum: 0,
            entities,
            log: vec![format!("{} enters -- {}", class.name(), class.chain())],
        }
    }

    /// Genesis with the default matriarch (the seer). Kept so existing callers still work.
    pub fn new(seed: u64) -> Self {
        Self::new_as(seed, Class::default())
    }

    /// Damage the player takes, softened by defense -- the wall is what `defense` buys.
    fn take_damage(&mut self, raw: i32) -> i32 {
        let actual = (raw - self.defense / 2).max(0);
        self.hp -= actual;
        actual
    }

    /// The turn contract: an action in, a resolved world out. Both faces call exactly this.
    pub fn step(&mut self, action: Action) {
        match action {
            Action::Move { dir } => {
                let (dx, dy) = match dir {
                    Dir::North => (0, -1),
                    Dir::South => (0, 1),
                    Dir::East => (1, 0),
                    Dir::West => (-1, 0),
                };
                let nx = (self.player.x + dx).clamp(0, W - 1);
                let ny = (self.player.y + dy).clamp(0, H - 1);
                if let Some(idx) = self.entities.iter().position(|e| e.pos.x == nx && e.pos.y == ny)
                {
                    // A principle holds that cell -- you don't walk over it, you engage it by its verb.
                    self.engage(idx);
                } else {
                    self.player = Pos { x: nx, y: ny };
                    self.log.push(format!("you move to {},{}", nx, ny));
                }
            }
            Action::Wait => self.log.push("you wait".into()),
        }
        // Orackla's transgressive flow -- momentum builds on any committed action, resets on rest.
        if self.class == Class::Orackla {
            self.momentum = match action {
                Action::Wait => 0,
                _ => (self.momentum + 1).min(3),
            };
        }
        self.entities.retain(|e| e.hp > 0);
        self.turn += 1;
        let n = self.log.len();
        if n > 16 {
            self.log.drain(0..n - 16);
        }
    }

    /// Resolve the entity at `idx` by its verb -- the principle's meaning made mechanic, bent by
    /// the player's class. This is the heart of the game: force is one verb among several, and the
    /// stat that drives it is the class you chose.
    fn engage(&mut self, idx: usize) {
        let verb = self.entities[idx].verb.clone();
        let label = self.entities[idx].seed.clone();
        match verb.as_str() {
            // Ayni -- reciprocity, flat: give of yourself, it yields faster than force.
            "Trade" => {
                if self.hp > 1 {
                    self.hp -= 1;
                    self.entities[idx].hp -= 3;
                    self.log
                        .push(format!("you trade with the {} -- gave 1, it yields", label));
                } else {
                    self.log
                        .push(format!("you have nothing to offer the {}", label));
                }
            }
            // Heka -- the utterance executes; insight sharpens it (Lysandra invokes hardest).
            "Invoke" => {
                let dmg = 2 + self.insight / 2;
                self.entities[idx].hp -= dmg;
                self.log.push(format!(
                    "you invoke the {} -- it answers ({} hp)",
                    label, self.entities[idx].hp
                ));
            }
            // Ma'at -- weighed against the order: alignment yields; deficiency is taken from you.
            // Insight is its own alignment -- the seer is found true even when weak.
            "Weigh" => {
                if self.hp >= 5 || self.insight >= 5 {
                    self.entities[idx].hp -= 3;
                    self.log.push(format!("the {} finds you aligned", label));
                } else {
                    let took = self.take_damage(2);
                    self.log
                        .push(format!("the {} finds you wanting (-{} hp)", label, took));
                }
            }
            // Pachakuti -- the board turns; the chaos costs you, unless you ARE chaos (Orackla).
            "Overturn" => {
                self.entities[idx].hp = 0;
                for (j, e) in self.entities.iter_mut().enumerate() {
                    if j != idx {
                        e.pos.x = W - 1 - e.pos.x;
                        e.pos.y = H - 1 - e.pos.y;
                    }
                }
                if self.class == Class::Orackla {
                    self.log
                        .push(format!("the {} overturns the age -- you ride it", label));
                } else {
                    let took = self.take_damage(2);
                    self.log
                        .push(format!("the {} overturns the age (-{} hp)", label, took));
                }
            }
            // Strike -- plain force: power drives it, Orackla's momentum compounds it.
            _ => {
                let dmg = (self.power / 2).max(1) + self.momentum;
                self.entities[idx].hp -= dmg;
                self.log.push(format!(
                    "you strike the {} ({} hp)",
                    label, self.entities[idx].hp
                ));
            }
        }
    }

    /// The observe contract -- identical information whether a human renders it or an agent reads it.
    pub fn observe(&self) -> Observation {
        let mut grid = vec![vec!['.'; W as usize]; H as usize];
        for e in &self.entities {
            if e.pos.x >= 0 && e.pos.x < W && e.pos.y >= 0 && e.pos.y < H {
                grid[e.pos.y as usize][e.pos.x as usize] = e.seed.chars().next().unwrap_or('?');
            }
        }
        grid[self.player.y as usize][self.player.x as usize] = '@';
        Observation {
            turn: self.turn,
            class: self.class.name().into(),
            chain: self.class.chain().into(),
            player: self.player,
            hp: self.hp,
            power: self.power,
            defense: self.defense,
            insight: self.insight,
            momentum: self.momentum,
            grid: grid
                .into_iter()
                .map(|row| row.into_iter().collect())
                .collect(),
            entities: self.entities.clone(),
            legal_actions: vec![
                "Move:North".into(),
                "Move:South".into(),
                "Move:East".into(),
                "Move:West".into(),
                "Wait".into(),
            ],
            log_tail: self.log.iter().rev().take(5).rev().cloned().collect(),
        }
    }

    /// The agent's screen as JSON -- this string IS how I read the board.
    pub fn observe_json(&self) -> String {
        serde_json::to_string_pretty(&self.observe()).unwrap_or_else(|_| "{}".into())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// A board with a player of explicit stats and no entities -- one verb at a time, precisely.
    fn rig(power: i32, defense: i32, insight: i32, hp: i32, class: Class) -> GameState {
        GameState {
            seed: 0,
            turn: 0,
            class,
            player: Pos { x: 0, y: 0 },
            hp,
            power,
            defense,
            insight,
            momentum: 0,
            entities: vec![],
            log: vec![],
        }
    }

    /// Place a principle by label at (x,y); its verb is read from its name, as in a real run.
    fn put(g: &mut GameState, label: &str, x: i32, y: i32, hp: i32) {
        let id = g.entities.len() as u32 + 1;
        g.entities.push(Entity {
            id,
            seed: label.into(),
            principle: "(test)".into(),
            heritage: Heritage::Andean,
            verb: verb_for(label).into(),
            pos: Pos { x, y },
            hp,
        });
    }

    #[test]
    fn observe_act_observe() {
        // The agent's loop, proven end to end: read state, act, read the changed world.
        let mut g = GameState::new(42);
        assert_eq!(g.player, Pos { x: 0, y: 0 });

        let obs = g.observe();
        assert_eq!(obs.turn, 0);
        assert_eq!(obs.grid.len(), H as usize);
        assert!(obs.grid[0].contains('@'));
        assert_eq!(obs.legal_actions.len(), 5);
        assert!(!obs.entities.is_empty());
        assert!(obs.entities.iter().all(|e| !e.principle.is_empty()));
        assert!(obs.entities.iter().all(|e| !e.verb.is_empty()));

        g.step(Action::Move { dir: Dir::East });
        assert_eq!(g.player, Pos { x: 1, y: 0 });
        assert_eq!(g.turn, 1);
        assert!(g.observe().log_tail.iter().any(|l| l.contains("move")));

        // The JSON screen carries the principle, the verb, and the player's class.
        let json = g.observe_json();
        assert!(json.contains("\"turn\""));
        assert!(json.contains("\"principle\""));
        assert!(json.contains("\"verb\""));
        assert!(json.contains("\"class\""));
    }

    #[test]
    fn deterministic_from_seed() {
        // Same seed + same class -> same world: replayable run, re-forgeable stone.
        let a = GameState::new(7);
        let b = GameState::new(7);
        assert_eq!(a.observe_json(), b.observe_json());
        assert!(!a.entities.is_empty());
    }

    #[test]
    fn canon_loads_and_balances() {
        let canon = canon_seeds();
        assert_eq!(canon.len(), 10);
        assert_eq!(
            canon.iter().filter(|s| s.heritage == Heritage::Andean).count(),
            5
        );
        assert_eq!(
            canon
                .iter()
                .filter(|s| s.heritage == Heritage::Egyptologic)
                .count(),
            5
        );
        let g = GameState::new(123);
        let a = g.entities.iter().filter(|e| e.heritage == Heritage::Andean).count();
        let e = g
            .entities
            .iter()
            .filter(|e| e.heritage == Heritage::Egyptologic)
            .count();
        assert_eq!(a, e);
    }

    #[test]
    fn verbs_scale_with_stats() {
        // Strike scales with power.
        let mut g = rig(4, 0, 0, 10, Class::Lysandra);
        put(&mut g, "Djed", 1, 0, 5);
        g.step(Action::Move { dir: Dir::East });
        assert_eq!(g.entities[0].hp, 3); // 5 - max(1, 4/2)

        // Invoke scales with insight.
        let mut g = rig(0, 0, 4, 10, Class::Lysandra);
        put(&mut g, "Heka", 1, 0, 6);
        g.step(Action::Move { dir: Dir::East });
        assert_eq!(g.entities[0].hp, 2); // 6 - (2 + 4/2)

        // Trade is flat reciprocity and costs your own hp.
        let mut g = rig(0, 0, 0, 10, Class::Lysandra);
        put(&mut g, "Ayni", 1, 0, 6);
        g.step(Action::Move { dir: Dir::East });
        assert_eq!((g.hp, g.entities[0].hp), (9, 3));
    }

    #[test]
    fn class_changes_play() {
        // Lysandra's insight is its own alignment -- Ma'at finds the seer true even at low hp.
        let mut g = rig(0, 0, 5, 3, Class::Lysandra);
        put(&mut g, "Ma'at", 1, 0, 6);
        g.step(Action::Move { dir: Dir::East });
        assert_eq!(g.entities[0].hp, 3); // aligned: 6 - 3
        assert_eq!(g.hp, 3); // unharmed

        // The wall shrugs Ma'at's judgment that would cost a frailer class.
        let mut g = rig(0, 4, 0, 3, Class::Umeko);
        put(&mut g, "Ma'at", 1, 0, 6);
        g.step(Action::Move { dir: Dir::East });
        assert_eq!(g.entities[0].hp, 6); // unmoved
        assert_eq!(g.hp, 3); // took max(0, 2 - 4/2) = 0

        // Orackla rides the Overturn for free; another class pays the chaos.
        let mut g = rig(0, 0, 0, 10, Class::Orackla);
        put(&mut g, "Pachakuti", 1, 0, 3);
        g.step(Action::Move { dir: Dir::East });
        assert_eq!(g.hp, 10); // chaos-native: no cost
        assert!(g.entities.is_empty());
        let mut g = rig(0, 0, 0, 10, Class::Lysandra);
        put(&mut g, "Pachakuti", 1, 0, 3);
        g.step(Action::Move { dir: Dir::East });
        assert_eq!(g.hp, 8); // paid 2

        // Orackla's momentum compounds her strike; resting resets it.
        let mut g = rig(2, 0, 0, 10, Class::Orackla);
        put(&mut g, "Djed", 2, 0, 9);
        g.step(Action::Move { dir: Dir::East }); // to (1,0); momentum -> 1
        assert_eq!(g.momentum, 1);
        g.step(Action::Move { dir: Dir::East }); // into Djed: strike = max(1,2/2) + 1 = 2
        assert_eq!(g.entities[0].hp, 7); // 9 - 2
        g.step(Action::Wait);
        assert_eq!(g.momentum, 0);
    }
}
