//! Real solar position for the renderer's sun vector — the Rust port of CLAUDEBASE_COSMOS_V1.

//! @SID:    RENDER_COSMOS_V1
//! @Shabti: Cosmos

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

/// World-space unit direction from horizontal coordinates. Renderer frame: Y up, +X East,
/// +Z North (matches the bathymetry mesh: column i → East, row j → North).
pub fn altaz_to_world_direction(alt_deg: f64, az_deg: f64) -> [f32; 3] {
    let (alt, az) = (alt_deg.to_radians(), az_deg.to_radians());
    [
        (alt.cos() * az.sin()) as f32, // East  → +X
        alt.sin() as f32,              // Up    → +Y
        (alt.cos() * az.cos()) as f32, // North → +Z
    ]
}

/// World-space unit direction TO the sun (thin alias over [`altaz_to_world_direction`]).
pub fn sun_world_direction(alt_deg: f64, az_deg: f64) -> [f32; 3] {
    altaz_to_world_direction(alt_deg, az_deg)
}

/// Push-constant solar vector for the water shader: xyz = direction TO the sun,
/// w = intensity = max(sin(altitude), 0) — so the sun below the horizon goes dark.
pub fn sun_push_constant(lat_deg: f64, lon_deg: f64, jd: f64) -> [f32; 4] {
    let (alt, az) = solar_position(lat_deg, lon_deg, jd);
    let d = sun_world_direction(alt, az);
    let intensity = alt.to_radians().sin().max(0.0) as f32;
    [d[0], d[1], d[2], intensity]
}

/// Moon longitude/distance periodic terms (Meeus table 47.A): (D, M, M′, F, Σl·1e6 deg, Σr·1e3 km).
#[rustfmt::skip]
const MOON_LON_DIST: [(i8, i8, i8, i8, f64, f64); 35] = [
    (0,  0,  1,  0,  6_288_774.0, -20_905_355.0),
    (2,  0, -1,  0,  1_274_027.0,  -3_699_111.0),
    (2,  0,  0,  0,    658_314.0,  -2_955_968.0),
    (0,  0,  2,  0,    213_618.0,    -569_925.0),
    (0,  1,  0,  0,   -185_116.0,      48_888.0),
    (0,  0,  0,  2,   -114_332.0,      -3_149.0),
    (2,  0, -2,  0,     58_793.0,     246_158.0),
    (2, -1, -1,  0,     57_066.0,    -152_138.0),
    (2,  0,  1,  0,     53_322.0,    -170_733.0),
    (2, -1,  0,  0,     45_758.0,    -204_586.0),
    (0,  1, -1,  0,    -40_923.0,    -129_620.0),
    (1,  0,  0,  0,    -34_720.0,     108_743.0),
    (0,  1,  1,  0,    -30_383.0,     104_755.0),
    (2,  0,  0, -2,     15_327.0,      10_321.0),
    (0,  0,  1,  2,    -12_528.0,           0.0),
    (0,  0,  1, -2,     10_980.0,      79_661.0),
    (4,  0, -1,  0,     10_675.0,     -34_782.0),
    (0,  0,  3,  0,     10_034.0,     -23_210.0),
    (4,  0, -2,  0,      8_548.0,     -21_636.0),
    (2,  1, -1,  0,     -7_888.0,      24_208.0),
    (2,  1,  0,  0,     -6_766.0,      30_824.0),
    (1,  0, -1,  0,     -5_163.0,      -8_379.0),
    (1,  1,  0,  0,      4_987.0,     -16_675.0),
    (2, -1,  1,  0,      4_036.0,     -12_831.0),
    (2,  0,  2,  0,      3_994.0,     -10_445.0),
    (4,  0,  0,  0,      3_861.0,     -11_650.0),
    (2,  0, -3,  0,      3_665.0,      14_403.0),
    (0,  1, -2,  0,     -2_689.0,      -7_003.0),
    (2,  0, -1,  2,     -2_602.0,           0.0),
    (2, -1, -2,  0,      2_390.0,      10_056.0),
    (1,  0,  1,  0,     -2_348.0,       6_322.0),
    (2, -2,  0,  0,      2_236.0,      -9_884.0),
    (0,  1,  2,  0,     -2_120.0,       5_751.0),
    (0,  2,  0,  0,     -2_069.0,           0.0),
    (2, -2, -1,  0,      2_048.0,      -4_950.0),
];

/// Moon latitude periodic terms (Meeus table 47.B): (D, M, M′, F, Σb·1e6 deg).
#[rustfmt::skip]
const MOON_LAT: [(i8, i8, i8, i8, f64); 30] = [
    (0,  0,  0,  1, 5_128_122.0),
    (0,  0,  1,  1,   280_602.0),
    (0,  0,  1, -1,   277_693.0),
    (2,  0,  0, -1,   173_237.0),
    (2,  0, -1,  1,    55_413.0),
    (2,  0, -1, -1,    46_271.0),
    (2,  0,  0,  1,    32_573.0),
    (0,  0,  2,  1,    17_198.0),
    (2,  0,  1, -1,     9_266.0),
    (0,  0,  2, -1,     8_822.0),
    (2, -1,  0, -1,     8_216.0),
    (2,  0, -2, -1,     4_324.0),
    (2,  0,  1,  1,     4_200.0),
    (2,  1,  0, -1,    -3_359.0),
    (2, -1, -1,  1,     2_463.0),
    (2, -1,  0,  1,     2_211.0),
    (2, -1, -1, -1,     2_065.0),
    (0,  1, -1, -1,    -1_870.0),
    (4,  0, -1, -1,     1_828.0),
    (0,  1,  0,  1,    -1_794.0),
    (0,  0,  0,  3,    -1_749.0),
    (0,  1, -1,  1,    -1_565.0),
    (1,  0,  0,  1,    -1_491.0),
    (0,  1,  1,  1,    -1_475.0),
    (0,  1,  1, -1,    -1_410.0),
    (0,  1,  0, -1,    -1_344.0),
    (1,  0,  0, -1,    -1_335.0),
    (0,  0,  3,  1,     1_107.0),
    (4,  0,  0, -1,     1_021.0),
    (4,  0, -1,  1,       833.0),
];

/// Apparent **topocentric** lunar altitude + azimuth (degrees) for a site at Julian Day `jd`.
/// Same conventions as [`solar_position`]: azimuth from North increasing East, airless.
///
/// Truncated Meeus (*Astronomical Algorithms*, ch. 47) geocentric ecliptic position →
/// equatorial → topocentric parallax (ch. 40). The Moon's ~1° horizontal parallax makes the
/// topocentric step mandatory (geocentric is ~1° wrong at the horizon). Verified against JPL
/// Horizons over New Providence in the tests (≈arcminute) — measured, not asserted.
pub fn lunar_position(lat_deg: f64, lon_deg: f64, jd: f64) -> (f64, f64) {
    let t = (jd - 2_451_545.0) / 36525.0;

    // Mean arguments (Meeus 47.1–47.6), degrees.
    let lp = 218.316_447_7 + t * (481_267.881_234_21 + t * (-0.001_578_6 + t * (1.0 / 538_841.0 - t / 65_194_000.0)));
    let d = 297.850_192_1 + t * (445_267.111_403_4 + t * (-0.001_881_9 + t * (1.0 / 545_868.0 - t / 113_065_000.0)));
    let ms = 357.529_109_2 + t * (35_999.050_290_9 + t * (-0.000_153_6 + t / 24_490_000.0));
    let mp = 134.963_396_4 + t * (477_198.867_505_5 + t * (0.008_741_4 + t * (1.0 / 69_699.0 - t / 14_712_000.0)));
    let f = 93.272_095_0 + t * (483_202.017_523_3 + t * (-0.003_653_9 + t * (-1.0 / 3_526_000.0 + t / 863_310_000.0)));
    let ecc = 1.0 - t * (0.002_516 + 0.000_007_4 * t);

    // Periodic sums (Σl, Σr from 47.A; Σb from 47.B). E-factor scales |M|=1,2 terms.
    let (mut sl, mut sr, mut sb) = (0.0_f64, 0.0_f64, 0.0_f64);
    for &(cd, cm, cmp, cf, cl, cr) in MOON_LON_DIST.iter() {
        let arg = (f64::from(cd) * d + f64::from(cm) * ms + f64::from(cmp) * mp + f64::from(cf) * f).to_radians();
        let ef = match cm.abs() {
            1 => ecc,
            2 => ecc * ecc,
            _ => 1.0,
        };
        sl += cl * ef * arg.sin();
        sr += cr * ef * arg.cos();
    }
    for &(cd, cm, cmp, cf, cb) in MOON_LAT.iter() {
        let arg = (f64::from(cd) * d + f64::from(cm) * ms + f64::from(cmp) * mp + f64::from(cf) * f).to_radians();
        let ef = match cm.abs() {
            1 => ecc,
            2 => ecc * ecc,
            _ => 1.0,
        };
        sb += cb * ef * arg.sin();
    }

    // Additive (planetary/secular) terms.
    let a1 = 119.75 + 131.849 * t;
    let a2 = 53.09 + 479_264.290 * t;
    let a3 = 313.45 + 481_266.484 * t;
    sl += 3958.0 * a1.to_radians().sin() + 1962.0 * (lp - f).to_radians().sin() + 318.0 * a2.to_radians().sin();
    sb += -2235.0 * lp.to_radians().sin()
        + 382.0 * a3.to_radians().sin()
        + 175.0 * (a1 - f).to_radians().sin()
        + 175.0 * (a1 + f).to_radians().sin()
        + 127.0 * (lp - mp).to_radians().sin()
        - 115.0 * (lp + mp).to_radians().sin();

    // Geocentric ecliptic coordinates (mean equinox of date).
    let mut lambda = lp + sl / 1_000_000.0; // longitude, deg
    let beta = (sb / 1_000_000.0).to_radians(); // latitude, rad
    let dist = 385_000.56 + sr / 1000.0; // km

    // Nutation (main terms) → apparent longitude + true obliquity.
    let omega = 125.044_52 - 1934.136_261 * t;
    let ls = 280.4665 + 36_000.7698 * t;
    let dpsi = (-17.20 * omega.to_radians().sin()
        - 1.32 * (2.0 * ls).to_radians().sin()
        - 0.23 * (2.0 * lp).to_radians().sin()
        + 0.21 * (2.0 * omega).to_radians().sin())
        / 3600.0;
    let deps = (9.20 * omega.to_radians().cos()
        + 0.57 * (2.0 * ls).to_radians().cos()
        + 0.10 * (2.0 * lp).to_radians().cos()
        - 0.09 * (2.0 * omega).to_radians().cos())
        / 3600.0;
    lambda += dpsi;
    let eps0 = 23.0 + (26.0 + (21.448 - t * (46.815 + t * (0.00059 - t * 0.001813))) / 60.0) / 60.0;
    let eps = (eps0 + deps).to_radians();
    let lam = lambda.to_radians();

    // Ecliptic → equatorial (geocentric, with latitude β).
    let alpha = (lam.sin() * eps.cos() - beta.tan() * eps.sin()).atan2(lam.cos());
    let delta = (beta.sin() * eps.cos() + beta.cos() * eps.sin() * lam.sin()).asin();

    // Local sidereal time (same GMST series as the Sun path).
    let gmst = norm360(
        280.460_618_37 + 360.985_647_366_29 * (jd - 2_451_545.0) + t * t * (0.000_387_933 - t / 38_710_000.0),
    );
    let lst = gmst + lon_deg;

    // Topocentric parallax (Meeus 40; observer at sea level).
    let sin_pi = 6378.14 / dist;
    let phi = lat_deg.to_radians();
    let u = (0.996_647_19 * phi.tan()).atan();
    let rho_sin = 0.996_647_19 * u.sin();
    let rho_cos = u.cos();
    let h = (lst - alpha.to_degrees()).to_radians();
    let d_alpha = (-rho_cos * sin_pi * h.sin()).atan2(delta.cos() - rho_cos * sin_pi * h.cos());
    let alpha_t = alpha + d_alpha;
    let delta_t =
        ((delta.sin() - rho_sin * sin_pi) * d_alpha.cos()).atan2(delta.cos() - rho_cos * sin_pi * h.cos());

    // Topocentric horizontal coordinates (geodetic latitude).
    let h_t = (lst - alpha_t.to_degrees()).to_radians();
    let sin_alt = phi.sin() * delta_t.sin() + phi.cos() * delta_t.cos() * h_t.cos();
    let alt = sin_alt.asin();
    let cos_az = (delta_t.sin() - phi.sin() * sin_alt) / (phi.cos() * alt.cos());
    let mut az = cos_az.clamp(-1.0, 1.0).acos().to_degrees();
    if h_t.sin() > 0.0 {
        az = 360.0 - az;
    }
    (alt.to_degrees(), az)
}

/// Illuminated fraction of the Moon's disk (0 = new, 1 = full) at Julian Day `jd`.
/// Low-precision Meeus (ch. 48) — good to ~0.5° in phase angle, ample for moonlight scaling.
pub fn moon_phase(jd: f64) -> f64 {
    let t = (jd - 2_451_545.0) / 36525.0;
    let d = 297.850_192_1 + 445_267.111_403_4 * t;
    let ms = 357.529_109_2 + 35_999.050_290_9 * t;
    let mp = 134.963_396_4 + 477_198.867_505_5 * t;
    // Phase angle i (Meeus 48.4), degrees.
    let i = 180.0 - d - 6.289 * mp.to_radians().sin() + 2.100 * ms.to_radians().sin()
        - 1.274 * (2.0 * d - mp).to_radians().sin()
        - 0.658 * (2.0 * d).to_radians().sin()
        - 0.214 * (2.0 * mp).to_radians().sin()
        - 0.110 * d.to_radians().sin();
    (1.0 + i.to_radians().cos()) / 2.0
}

/// Push-constant lunar vector (parallel to [`sun_push_constant`]): xyz = direction TO the
/// Moon, w = geometric intensity = max(sin(altitude), 0). Scale by [`moon_phase`] in-shader
/// for phase-aware moonlight.
pub fn moon_push_constant(lat_deg: f64, lon_deg: f64, jd: f64) -> [f32; 4] {
    let (alt, az) = lunar_position(lat_deg, lon_deg, jd);
    let dir = altaz_to_world_direction(alt, az);
    let intensity = alt.to_radians().sin().max(0.0) as f32;
    [dir[0], dir[1], dir[2], intensity]
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

    // Moon authority: JPL Horizons (topocentric, airless apparent) over New Providence.
    #[test]
    fn moon_high_morning() {
        let (alt, az) = lunar_position(LAT, LON, julian_day(2026, 6, 9, 11, 0, 0.0));
        assert!((alt - 63.102_800).abs() < 0.1, "alt {alt}");
        assert!(ang_diff(az, 145.045_120) < 0.3, "az {az}");
    }

    #[test]
    fn moon_low_west() {
        let (alt, az) = lunar_position(LAT, LON, julian_day(2026, 6, 9, 17, 0, 0.0));
        assert!((alt - 16.794_648).abs() < 0.1, "alt {alt}");
        assert!(ang_diff(az, 266.456_159) < 0.3, "az {az}");
    }

    #[test]
    fn moon_below_horizon() {
        let (alt, az) = lunar_position(LAT, LON, julian_day(2026, 6, 9, 21, 30, 0.0));
        assert!((alt - (-39.659_022)).abs() < 0.1, "alt {alt}");
        assert!(ang_diff(az, 300.892_040) < 0.5, "az {az}");
    }

    #[test]
    fn moon_phase_in_range() {
        let k = moon_phase(julian_day(2026, 6, 9, 17, 0, 0.0));
        assert!((0.0..=1.0).contains(&k), "fraction {k}");
    }
}
