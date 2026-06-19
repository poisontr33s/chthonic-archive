//! The first astrology module — the zodiac on the **Ankhological Origin**.

//! @SID:    RENDER_ZODIAC_V1
//! @Shabti: Zodiac

//! The owner set the origin (research: `CLAUDEBASE/The-Savant-High-Bounties/andean-egyptic-BCE-
//! choice-triangulation-lucid-clarity.md`, Option C). 0° Aries is not the vernal equinox (tropical,
//! Northern-biased) nor a Vedic/Babylonian ayanamsa (sidereal but foreign to both cultures) — it is
//! the **geocentric ecliptic midpoint between two cultural anchor stars**, an exact 50/50 fusion:
//!
//! - **Sirius** (Sopdet) — the Egyptian anchor: the Sothic year, the decanal clocks, the singular
//!   brightest star. Luminous, vertical, Northern-meridian.
//! - **Alcyone / the Pleiades** (Qullqa) — the Andean anchor: the heliacal-rising harvest marker,
//!   the El-Niño meteorological forecaster, the dark-cloud river's neighbour. Diffuse, horizon,
//!   Southern.
//!
//! This is sidereal mechanics — the origin is locked to the stars and **precesses with them**, so
//! it never drifts against the real sky — but its ayanamsa is defined by balancing the two
//! traditions, not by inheriting a third. The two anchors sit an invariant 44.0893° apart along the
//! ecliptic (both precess together), so the midpoint holds Sirius forever at +22°03′ and Alcyone at
//! −22°03′ (7°57′ Pisces) in this frame — the structural proof the fusion is exactly even.
//!
//! **Accuracy-not-fiction.** This module reads the *true* ecliptic ([`super::cosmos`]) and shifts
//! the 0° line by the derived ayanamsa — nothing more. No coordinate is fabricated, and the
//! **meaning** of each sign stays deliberately empty: the slot reports "Sun in sign N at λ°", and
//! the owner later populates the Andean/Egyptian semantics from verifiable lore, never invention.

use super::correspondence::{SkyContext, Slot, SlotReading};
use super::cosmos;

/// The Egyptian anchor — Sirius (α Canis Majoris, Sopdet), J2000 equatorial (matches [`cosmos::STARS`]).
const SIRIUS_RA_J2000: f64 = 101.287;
const SIRIUS_DEC_J2000: f64 = -16.716;

/// The Andean anchor — Alcyone (η Tauri), the brightest Pleiad (Qullqa), J2000 equatorial.
const ALCYONE_RA_J2000: f64 = 56.871;
const ALCYONE_DEC_J2000: f64 = 24.105;

/// The twelve 30° sectors, by their conventional ordinal labels (the research's own usage — e.g.
/// "0° Aries", "7°57′ Pisces"). These are *labels for the sectors*, not asserted meanings; sign 0
/// (Aries) begins at the Ankhological origin.
pub const SIGN_NAMES: [&str; 12] = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
];

/// Shortest signed angular difference `a − b`, in degrees, folded to [−180, 180). Used to take a
/// wrap-safe midpoint of the two anchors.
fn signed_delta(a: f64, b: f64) -> f64 {
    (a - b + 540.0).rem_euclid(360.0) - 180.0
}

/// The **Ankhological ayanamsa** at Julian Day `jd`: the tropical ecliptic longitude (of date,
/// degrees) of the geocentric midpoint between Sirius and Alcyone. Subtracting this from a body's
/// tropical longitude yields its longitude in the Ankhological zodiac.
///
/// Computed wrap-safe as `alcyone + (sirius − alcyone)/2` so the midpoint is always the *near* one
/// (the anchors are ~44° apart). At J2000 this is ≈ 82.05°, and it grows at the precession rate
/// (~1.3969712°/century), exactly because both anchors precess together.
pub fn ankhological_ayanamsa(jd: f64) -> f64 {
    let sirius = cosmos::star_ecliptic_longitude(SIRIUS_RA_J2000, SIRIUS_DEC_J2000, jd);
    let alcyone = cosmos::star_ecliptic_longitude(ALCYONE_RA_J2000, ALCYONE_DEC_J2000, jd);
    (alcyone + signed_delta(sirius, alcyone) / 2.0).rem_euclid(360.0)
}

/// A tropical ecliptic longitude (degrees, of date) → its longitude in the **Ankhological zodiac**
/// (degrees, normalized). Pure shift by the ayanamsa — the body's true position is untouched.
pub fn to_ankhological(tropical_lon_deg: f64, jd: f64) -> f64 {
    (tropical_lon_deg - ankhological_ayanamsa(jd)).rem_euclid(360.0)
}

/// A longitude in the Ankhological zodiac → `(sign index 0..=11, sign label, degree within sign)`.
pub fn sign_of(ankh_lon_deg: f64) -> (usize, &'static str, f64) {
    let lon = ankh_lon_deg.rem_euclid(360.0);
    let index = ((lon / 30.0) as usize).min(11);
    (index, SIGN_NAMES[index], lon - index as f64 * 30.0)
}

/// The **tropical** ecliptic longitude (degrees, of date) of each of the twelve sign boundaries —
/// the spokes of the Ankhological wheel, ready to draw on the real ecliptic. Boundary 0 is the
/// origin itself (the Sirius/Alcyone midpoint); the rest step exactly 30°. The geometry is
/// math-forced — the verified midpoint and an exact division — so the wheel carries no free knob;
/// only how it is *rendered* is a choice.
pub fn sign_boundaries_tropical(jd: f64) -> [f64; 12] {
    let ayan = ankhological_ayanamsa(jd);
    let mut out = [0.0_f64; 12];
    for (k, slot) in out.iter_mut().enumerate() {
        *slot = (ayan + k as f64 * 30.0).rem_euclid(360.0);
    }
    out
}

/// The zodiac as a correspondence [`Slot`]: it reads the true Sun against the Ankhological origin
/// and reports its sign. The Sun is the canonical zodiacal luminary (it rides exactly on the
/// ecliptic); the Moon and the five planets compound onto this same machinery next, each just
/// another tropical longitude shifted by the one ayanamsa. Meaning stays the owner's.
pub struct ZodiacSlot;

impl Slot for ZodiacSlot {
    fn name(&self) -> &str {
        "zodiac-ankhological"
    }

    fn read(&self, ctx: &SkyContext) -> SlotReading {
        let ayan = ankhological_ayanamsa(ctx.jd);
        let sun_trop = cosmos::sun_apparent_longitude(ctx.jd);
        let sun_ankh = to_ankhological(sun_trop, ctx.jd);
        let (index, name, deg) = sign_of(sun_ankh);
        SlotReading {
            slot: self.name().to_string(),
            entries: vec![
                ("origin".to_string(), "sirius-alcyone-midpoint".to_string()),
                ("ayanamsa_deg".to_string(), format!("{ayan:.3}")),
                ("sun_sign_index".to_string(), index.to_string()),
                ("sun_sign".to_string(), name.to_string()),
                ("sun_degree".to_string(), format!("{deg:.2}")),
                ("sun_lon_ankh_deg".to_string(), format!("{sun_ankh:.3}")),
                // Meaning is owner-defined: the slot asserts position, never significance.
                ("semantics".to_string(), "owner-defined".to_string()),
            ],
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// The defining 50/50 invariant: in the Ankhological frame Sirius sits at +22.04° and Alcyone
    /// at the mirror −22.04° (337.96°), so their midpoint is the origin. Holds at every epoch
    /// because both anchors precess together — the test runs two epochs a century apart.
    #[test]
    fn origin_balances_the_two_anchors() {
        for jd in [cosmos::julian_day(2000, 1, 1, 12, 0, 0.0), cosmos::julian_day(2100, 1, 1, 12, 0, 0.0)] {
            let sirius = cosmos::star_ecliptic_longitude(SIRIUS_RA_J2000, SIRIUS_DEC_J2000, jd);
            let alcyone = cosmos::star_ecliptic_longitude(ALCYONE_RA_J2000, ALCYONE_DEC_J2000, jd);

            let sirius_ankh = signed_delta(to_ankhological(sirius, jd), 0.0);
            let alcyone_ankh = signed_delta(to_ankhological(alcyone, jd), 0.0);

            assert!((sirius_ankh - 22.045).abs() < 0.2, "Sirius at {sirius_ankh:.3}°, expected +22.04°");
            assert!((alcyone_ankh + 22.045).abs() < 0.2, "Alcyone at {alcyone_ankh:.3}°, expected -22.04°");
            // The two are mirror images about the origin → their midpoint is 0°.
            assert!((sirius_ankh + alcyone_ankh).abs() < 0.05, "midpoint not at the origin");
        }
    }

    /// The anchors' separation is the invariant 44.0893° (Table 2 of the research) — the property
    /// that makes the precessing midpoint a stable origin.
    #[test]
    fn anchor_separation_is_invariant() {
        let jd = cosmos::julian_day(2026, 6, 19, 0, 0, 0.0);
        let sirius = cosmos::star_ecliptic_longitude(SIRIUS_RA_J2000, SIRIUS_DEC_J2000, jd);
        let alcyone = cosmos::star_ecliptic_longitude(ALCYONE_RA_J2000, ALCYONE_DEC_J2000, jd);
        let sep = signed_delta(sirius, alcyone);
        assert!((sep - 44.0893).abs() < 0.3, "separation {sep:.4}°, expected 44.0893°");
    }

    /// The ayanamsa is sidereal — it precesses. A century apart it grows by the engine's general
    /// precession rate (1.3969712°/century), proving the origin tracks the stars, not the seasons.
    #[test]
    fn ayanamsa_precesses_with_the_stars() {
        let a = ankhological_ayanamsa(cosmos::julian_day(2000, 1, 1, 12, 0, 0.0));
        let b = ankhological_ayanamsa(cosmos::julian_day(2100, 1, 1, 12, 0, 0.0));
        assert!((signed_delta(b, a) - 1.396_971_2).abs() < 0.01, "ayanamsa drift {:.4}°/century", signed_delta(b, a));
        // And at J2000 it is the derived ≈ 82.05°.
        assert!((a - 82.05).abs() < 0.3, "J2000 ayanamsa {a:.3}°, expected ≈ 82.05°");
    }

    /// No fabrication: the Sun's reported Ankhological longitude is exactly its true tropical
    /// longitude minus the ayanamsa — a pure shift of the origin, nothing invented.
    #[test]
    fn sun_is_tropical_minus_ayanamsa() {
        let jd = cosmos::julian_day(2026, 3, 20, 12, 0, 0.0); // near the equinox
        let sun_trop = cosmos::sun_apparent_longitude(jd);
        let expected = (sun_trop - ankhological_ayanamsa(jd)).rem_euclid(360.0);
        assert!(signed_delta(to_ankhological(sun_trop, jd), expected).abs() < 1e-9);
    }

    /// The twelve boundaries are the wheel: boundary 0 is the origin, and each lands exactly on
    /// its sign's 0° in the Ankhological frame (the division is math-forced, no drift).
    #[test]
    fn the_twelve_boundaries_are_the_wheel() {
        let jd = cosmos::julian_day(2026, 6, 19, 0, 0, 0.0);
        let b = sign_boundaries_tropical(jd);
        assert!(signed_delta(b[0], ankhological_ayanamsa(jd)).abs() < 1e-9, "boundary 0 is the origin");
        for (k, &lon) in b.iter().enumerate() {
            let expected = (k as f64 * 30.0) % 360.0;
            assert!(
                signed_delta(to_ankhological(lon, jd), expected).abs() < 1e-6,
                "boundary {k} not on its sign edge"
            );
        }
    }

    /// The slot plugs into the correspondence socket and produces a structured reading.
    #[test]
    fn zodiac_plugs_into_the_socket() {
        use super::super::correspondence::Correspondence;
        let ctx = SkyContext::new_providence(cosmos::julian_day(2026, 6, 19, 0, 0, 0.0));
        let engine = Correspondence::new().with_slot(Box::new(ZodiacSlot));

        assert_eq!(engine.slot_names(), vec!["zodiac-ankhological"]);
        let readings = engine.read(&ctx);
        assert_eq!(readings.len(), 1);

        let r = &readings[0];
        let sign = r.entries.iter().find(|(k, _)| k == "sun_sign").map(|(_, v)| v.as_str());
        assert!(sign.is_some_and(|s| SIGN_NAMES.contains(&s)), "reading must name a real sign");
        // Semantics are never asserted by the engine.
        let sem = r.entries.iter().find(|(k, _)| k == "semantics").map(|(_, v)| v.as_str());
        assert_eq!(sem, Some("owner-defined"));
    }
}
