//! The correspondence kernel — the core of the astrology × astronomy engine.

//! @SID:    RENDER_CORRESPONDENCE_V1
//! @Shabti: Correspondence

//! "As above, so below." One true celestial position bound to one structured meaning-slot, so the
//! meaning always rides a true position. The astronomy shell ([`super::cosmos`]) feeds verified
//! positions; each astrology tradition is a swappable [`Slot`] module that reads them. This module
//! is the *socket* — small, fixed, the only thing every spiritual module plugs into. It renders
//! nothing yet (the lens is the next rung); the [`Slot`] trait stays minimal until the first real
//! module (the zodiac) proves its shape. The socket ships EMPTY — no tradition is hard-wired, and
//! none is invented here (accuracy-not-fiction: meaning rides true positions or it is nothing).

// Stage-0 socket: built + tested, not yet consumed by the renderer (the lens wires it in next).
#![allow(dead_code)]

use super::cosmos;

/// When + where the sky is read — the astronomy shell consumes this to produce true positions.
#[derive(Clone, Copy, Debug)]
pub struct SkyContext {
    pub lat_deg: f64,
    pub lon_deg: f64,
    pub jd: f64,
}

impl SkyContext {
    /// The default chamber: New Providence, the site every position in [`super::cosmos`] is over.
    pub fn new_providence(jd: f64) -> Self {
        Self {
            lat_deg: cosmos::NEW_PROVIDENCE_LAT_DEG,
            lon_deg: cosmos::NEW_PROVIDENCE_LON_DEG,
            jd,
        }
    }
}

/// What a [`Slot`] produces from the true sky — the structure/meaning that rides the positions.
/// Free-form `(key, value)` entries so a tradition is never forced into a fixed schema before it
/// exists; a module shapes its own reading and the owner sets what the values mean.
#[derive(Clone, Debug, Default)]
pub struct SlotReading {
    pub slot: String,
    pub entries: Vec<(String, String)>,
}

/// A swappable astrology module — the spirit half, owner-defined. It reads the true sky (through
/// [`super::cosmos`]) and returns a structured [`SlotReading`]; it must never assert a position the
/// astronomy half cannot verify. Rendering (its marks in the lens) is added at the next rung.
pub trait Slot {
    fn name(&self) -> &str;
    fn read(&self, ctx: &SkyContext) -> SlotReading;
}

/// The binding — "as above, so below". Holds the active [`Slot`] modules and reads them against one
/// true sky. Modules are swappable at runtime (the "modularly swappable from core" contract); none
/// is hard-wired, and the socket ships empty — real traditions enter only when a `/goal` selects
/// them and the owner sets their mechanics.
#[derive(Default)]
pub struct Correspondence {
    slots: Vec<Box<dyn Slot>>,
}

impl Correspondence {
    pub fn new() -> Self {
        Self { slots: Vec::new() }
    }

    /// Plug a module into the socket.
    pub fn with_slot(mut self, slot: Box<dyn Slot>) -> Self {
        self.slots.push(slot);
        self
    }

    pub fn slot_count(&self) -> usize {
        self.slots.len()
    }

    pub fn slot_names(&self) -> Vec<&str> {
        self.slots.iter().map(|s| s.name()).collect()
    }

    /// Read every active module against the true sky at `ctx`.
    pub fn read(&self, ctx: &SkyContext) -> Vec<SlotReading> {
        self.slots.iter().map(|s| s.read(ctx)).collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// A trivial module proving the socket binds a true position to a structured reading. (Not a
    /// real tradition — the astrology modules await a `/goal` + the owner's mechanics.)
    struct SunUpSlot;
    impl Slot for SunUpSlot {
        fn name(&self) -> &str {
            "sun-up"
        }
        fn read(&self, ctx: &SkyContext) -> SlotReading {
            let (alt, _az) = cosmos::solar_position(ctx.lat_deg, ctx.lon_deg, ctx.jd);
            SlotReading {
                slot: self.name().to_string(),
                entries: vec![("sun_up".to_string(), (alt > 0.0).to_string())],
            }
        }
    }

    #[test]
    fn socket_binds_a_slot_to_the_true_sky() {
        // 17:00 UTC over New Providence is local midday — the Sun is well up.
        let ctx = SkyContext::new_providence(cosmos::julian_day(2026, 6, 9, 17, 0, 0.0));
        let engine = Correspondence::new().with_slot(Box::new(SunUpSlot));

        assert_eq!(engine.slot_count(), 1);
        assert_eq!(engine.slot_names(), vec!["sun-up"]);

        let readings = engine.read(&ctx);
        assert_eq!(readings.len(), 1);
        assert_eq!(readings[0].slot, "sun-up");
        assert_eq!(readings[0].entries[0].1, "true");
    }

    #[test]
    fn empty_socket_reads_nothing() {
        let ctx = SkyContext::new_providence(cosmos::julian_day(2026, 6, 9, 17, 0, 0.0));
        let engine = Correspondence::new();
        assert_eq!(engine.slot_count(), 0);
        assert!(engine.read(&ctx).is_empty());
    }
}
