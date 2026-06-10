//! Real solar position for the renderer's sun vector — the Rust port of CLAUDEBASE_COSMOS_V1.
//!
//! @SID:    RENDER_COSMOS_V1
//! @Shabti: Cosmos
//!
//! The Python prototype (`CLAUDEBASE/quarterdeck/cosmos.py`: Skyfield + JPL DE421,
//! verified vs JPL Horizons to sub-arcsecond) remains the **authority of record**.
//! This module is the in-house Rust port the Rust/Vulkan renderer actually calls: a
//! standard NOAA/Meeus apparent-solar-position algorithm (~arcminute for the Sun —
//! lighting-grade; the renderer needs nothing near DE421's precision). Its tests assert
//! it against three Skyfield/DE421 fixes over New Providence, so it is verified, not fiction.

/// Julian Day (UTC) from a proleptic-Gregorian calendar instant.
pub fn julian_day(year: i32, month: u32, day: u32, hour: u32, minute: u32, second: f64) -> f64 {
    let (mut y, mut m) = (year, month as i32);
    if m <= 2 {
        y -= 1;
        m += 12;
    }
    let a = (f64::from(y) / 100.0).floor();
    let b = 2.0 - a + (a / 4.0).floor();
    let day_frac = (f64::from(hour) + f64::from(minute) / 60.0 + second / 3600.0) / 24.0;
    (365.25 * (f64::from(y) + 4716.0)).floor()
        + (30.6001 * (f64::from(m) + 1.0)).floor()
        + f64::from(day)
        + b
        - 1524.5
        + day_frac
}

fn norm360(x: f64) -> f64 {
    x.rem_euclid(360.0)
}

/// Apparent solar altitude + azimuth (degrees) for a site at Julian Day `jd`.
/// Azimuth is measured from North, increasing toward East. NOAA/Meeus apparent
/// position (aberration + nutation in longitude), airless (no refraction model) —
/// matching the Skyfield `altaz()` (no pressure) used as the test authority.
pub fn solar_position(lat_deg: f64, lon_deg: f64, jd: f64) -> (f64, f64) {
    let t = (jd - 2_451_545.0) / 36525.0;

    // Sun's apparent ecliptic longitude.
    let l0 = norm360(280.46646 + t * (36000.76983 + t * 0.0003032));
    let m = 357.52911 + t * (35999.05029 - 0.0001537 * t);
    let mrad = m.to_radians();
    let c = mrad.sin() * (1.914602 - t * (0.004817 + 0.000014 * t))
        + (2.0 * mrad).sin() * (0.019993 - 0.000101 * t)
        + (3.0 * mrad).sin() * 0.000289;
    let true_long = l0 + c;
    let omega = 125.04 - 1934.136 * t;
    let lambda = (true_long - 0.00569 - 0.00478 * omega.to_radians().sin()).to_radians();

    // Obliquity of the ecliptic (mean + nutation correction).
    let eps0 = 23.0 + (26.0 + (21.448 - t * (46.815 + t * (0.00059 - t * 0.001813))) / 60.0) / 60.0;
    let eps = (eps0 + 0.00256 * omega.to_radians().cos()).to_radians();

    // Equatorial coordinates.
    let alpha = (eps.cos() * lambda.sin()).atan2(lambda.cos()); // right ascension (rad)
    let delta = (eps.sin() * lambda.sin()).asin(); // declination (rad)

    // Local hour angle.
    let gmst = norm360(
        280.460_618_37 + 360.985_647_366_29 * (jd - 2_451_545.0)
            + t * t * (0.000_387_933 - t / 38_710_000.0),
    );
    let lst = gmst + lon_deg; // east-positive longitude
    let mut h = lst - alpha.to_degrees();
    h = (h + 180.0).rem_euclid(360.0) - 180.0; // → [-180, 180)
    let hrad = h.to_radians();
    let lat = lat_deg.to_radians();

    // Horizontal coordinates (Practical Astronomy form; acos + hour-angle sign for E/W).
    let sin_alt = lat.sin() * delta.sin() + lat.cos() * delta.cos() * hrad.cos();
    let alt = sin_alt.asin();
    let cos_az = (delta.sin() - lat.sin() * sin_alt) / (lat.cos() * alt.cos());
    let mut az = cos_az.clamp(-1.0, 1.0).acos().to_degrees();
    if hrad.sin() > 0.0 {
        az = 360.0 - az;
    }
    (alt.to_degrees(), az)
}

/// World-space unit direction TO the sun. Renderer frame: Y up, +X East, +Z North
/// (matches the bathymetry mesh: column i → East, row j → North).
pub fn sun_world_direction(alt_deg: f64, az_deg: f64) -> [f32; 3] {
    let (alt, az) = (alt_deg.to_radians(), az_deg.to_radians());
    [
        (alt.cos() * az.sin()) as f32, // East  → +X
        alt.sin() as f32,              // Up    → +Y
        (alt.cos() * az.cos()) as f32, // North → +Z
    ]
}

/// Push-constant solar vector for the water shader: xyz = direction TO the sun,
/// w = intensity = max(sin(altitude), 0) — so the sun below the horizon goes dark.
pub fn sun_push_constant(lat_deg: f64, lon_deg: f64, jd: f64) -> [f32; 4] {
    let (alt, az) = solar_position(lat_deg, lon_deg, jd);
    let d = sun_world_direction(alt, az);
    let intensity = alt.to_radians().sin().max(0.0) as f32;
    [d[0], d[1], d[2], intensity]
}

#[cfg(test)]
mod tests {
    use super::*;

    // Authority: Skyfield + JPL DE421 (apparent, airless) over New Providence.
    const LAT: f64 = 25.0443;
    const LON: f64 = -77.3504;

    fn ang_diff(a: f64, b: f64) -> f64 {
        let d = (a - b).abs();
        if d > 180.0 { 360.0 - d } else { d }
    }

    #[test]
    fn morning_ene() {
        let (alt, az) = solar_position(LAT, LON, julian_day(2026, 6, 9, 11, 0, 0.0));
        assert!((alt - 7.67563).abs() < 0.1, "alt {alt}");
        assert!(ang_diff(az, 68.20236) < 2.0, "az {az}");
    }

    #[test]
    fn afternoon_wnw() {
        let (alt, az) = solar_position(LAT, LON, julian_day(2026, 6, 9, 21, 30, 0.0));
        assert!((alt - 30.90301).abs() < 0.1, "alt {alt}");
        assert!(ang_diff(az, 282.86637) < 2.0, "az {az}");
    }

    #[test]
    fn noon_near_zenith() {
        // Azimuth is hypersensitive within ~3° of the zenith, so altitude alone is the assertion.
        let (alt, _az) = solar_position(LAT, LON, julian_day(2026, 6, 9, 17, 0, 0.0));
        assert!((alt - 87.12962).abs() < 0.1, "alt {alt}");
    }
}
