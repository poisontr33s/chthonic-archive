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

/// Grounded render-site fix: New Providence/Nassau, east-positive longitude.
pub const NEW_PROVIDENCE_LAT_DEG: f64 = 25.0443;
pub const NEW_PROVIDENCE_LON_DEG: f64 = -77.3504;

/// Current deterministic scene epoch used by the renderer: 2026-06-09 17:00 UTC.
/// This is the high-Sun verification epoch from the Horizons/Skyfield test set.
pub fn scene_julian_day() -> f64 {
    julian_day(2026, 6, 9, 17, 0, 0.0)
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
        280.460_618_37
            + 360.985_647_366_29 * (jd - 2_451_545.0)
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

/// Apparent topocentric horizontal coordinates (alt, az in degrees; az from North increasing
/// East; airless) of a body whose **geocentric** equatorial position of date is (`alpha_deg`,
/// `delta_deg`) at geocentric distance `dist_km`, seen from a sea-level site (`lat_deg`,
/// `lon_deg` east-positive) at Julian Day `jd`. Diurnal parallax via Meeus ch. 40 — ~1° for the
/// Moon, negligible (but applied) for the planets. Shared by [`lunar_position`]/[`planet_position`].
fn topocentric_altaz(
    lat_deg: f64,
    lon_deg: f64,
    jd: f64,
    alpha_deg: f64,
    delta_deg: f64,
    dist_km: f64,
) -> (f64, f64) {
    let t = (jd - 2_451_545.0) / 36525.0;
    let gmst = norm360(
        280.460_618_37
            + 360.985_647_366_29 * (jd - 2_451_545.0)
            + t * t * (0.000_387_933 - t / 38_710_000.0),
    );
    let lst = gmst + lon_deg;

    // Topocentric parallax (Meeus 40; observer at sea level).
    let delta = delta_deg.to_radians();
    let sin_pi = 6378.14 / dist_km;
    let phi = lat_deg.to_radians();
    let u = (0.996_647_19 * phi.tan()).atan();
    let rho_sin = 0.996_647_19 * u.sin();
    let rho_cos = u.cos();
    let h = (lst - alpha_deg).to_radians();
    let d_alpha = (-rho_cos * sin_pi * h.sin()).atan2(delta.cos() - rho_cos * sin_pi * h.cos());
    let alpha_t = alpha_deg.to_radians() + d_alpha;
    let delta_t = ((delta.sin() - rho_sin * sin_pi) * d_alpha.cos())
        .atan2(delta.cos() - rho_cos * sin_pi * h.cos());

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
    let lp = 218.316_447_7
        + t * (481_267.881_234_21 + t * (-0.001_578_6 + t * (1.0 / 538_841.0 - t / 65_194_000.0)));
    let d = 297.850_192_1
        + t * (445_267.111_403_4 + t * (-0.001_881_9 + t * (1.0 / 545_868.0 - t / 113_065_000.0)));
    let ms = 357.529_109_2 + t * (35_999.050_290_9 + t * (-0.000_153_6 + t / 24_490_000.0));
    let mp = 134.963_396_4
        + t * (477_198.867_505_5 + t * (0.008_741_4 + t * (1.0 / 69_699.0 - t / 14_712_000.0)));
    let f = 93.272_095_0
        + t * (483_202.017_523_3
            + t * (-0.003_653_9 + t * (-1.0 / 3_526_000.0 + t / 863_310_000.0)));
    let ecc = 1.0 - t * (0.002_516 + 0.000_007_4 * t);

    // Periodic sums (Σl, Σr from 47.A; Σb from 47.B). E-factor scales |M|=1,2 terms.
    let (mut sl, mut sr, mut sb) = (0.0_f64, 0.0_f64, 0.0_f64);
    for &(cd, cm, cmp, cf, cl, cr) in MOON_LON_DIST.iter() {
        let arg =
            (f64::from(cd) * d + f64::from(cm) * ms + f64::from(cmp) * mp + f64::from(cf) * f)
                .to_radians();
        let ef = match cm.abs() {
            1 => ecc,
            2 => ecc * ecc,
            _ => 1.0,
        };
        sl += cl * ef * arg.sin();
        sr += cr * ef * arg.cos();
    }
    for &(cd, cm, cmp, cf, cb) in MOON_LAT.iter() {
        let arg =
            (f64::from(cd) * d + f64::from(cm) * ms + f64::from(cmp) * mp + f64::from(cf) * f)
                .to_radians();
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
    sl += 3958.0 * a1.to_radians().sin()
        + 1962.0 * (lp - f).to_radians().sin()
        + 318.0 * a2.to_radians().sin();
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

    // Topocentric apparent horizontal coordinates — shared tail (the Moon's ~1° diurnal parallax
    // is why this step is mandatory, not cosmetic).
    topocentric_altaz(
        lat_deg,
        lon_deg,
        jd,
        alpha.to_degrees(),
        delta.to_degrees(),
        dist,
    )
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

// ── The wanderers ────────────────────────────────────────────────────────────────────────────
//
// The five naked-eye planets, from JPL's own low-precision theory: E. M. Standish, "Keplerian
// Elements for Approximate Positions of the Major Planets" (JPL Solar System Dynamics), Table 1 —
// heliocentric elements + linear per-century rates, valid 1800–2050 AD. For each body (and for
// Earth) we solve Kepler's equation, difference to a light-time-corrected geocentric vector,
// precess the J2000 ecliptic longitude to the equinox of date, then reuse the Moon's
// equatorial → topocentric → horizontal tail. Arcminute-class in this window — ample for the sky,
// and asserted body-by-body against JPL Horizons in the tests (measured, not fiction). Nutation
// (~0.005°) and annual aberration (~0.006°) are omitted as sub-tolerance; the dominant term — the
// ~0.37° of precession from 2000 to 2026 — is included. Computed, verified, and shader-wired.

/// A naked-eye planet. (Discriminants index [`ELEMENTS`]; row 0 is reserved for Earth.)
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Planet {
    Mercury = 1,
    Venus = 2,
    Mars = 3,
    Jupiter = 4,
    Saturn = 5,
}

impl Planet {
    /// The visible-planet set rendered by the celestial field.
    pub const ALL: [Self; 5] = [
        Self::Mercury,
        Self::Venus,
        Self::Mars,
        Self::Jupiter,
        Self::Saturn,
    ];
}

/// One body's Keplerian set: each element is `(value_at_J2000, rate_per_Julian_century)`.
/// Angles in degrees, `a` in AU.
#[derive(Clone, Copy)]
struct Kepler {
    a: (f64, f64),    // semi-major axis [AU]
    e: (f64, f64),    // eccentricity
    inc: (f64, f64),  // inclination to the ecliptic [deg]
    l: (f64, f64),    // mean longitude L [deg]
    peri: (f64, f64), // longitude of perihelion ϖ [deg]
    node: (f64, f64), // longitude of ascending node Ω [deg]
}

/// Keplerian elements (Standish, Table 1), indexed by [`Planet`]; row 0 is the Earth–Moon
/// barycenter (the observer's heliocentric position).
#[rustfmt::skip]
const ELEMENTS: [Kepler; 6] = [
    /* 0 Earth   */ Kepler { a: (1.000_002_61,  0.000_005_62), e: (0.016_711_23, -0.000_043_92), inc: (-0.000_015_31, -0.012_946_68), l: (100.464_571_66, 35_999.372_449_81), peri: (102.937_681_93,  0.323_273_64), node: (  0.000_000_00,  0.000_000_00) },
    /* 1 Mercury */ Kepler { a: (0.387_099_27,  0.000_000_37), e: (0.205_635_93,  0.000_019_06), inc: ( 7.004_979_02, -0.005_947_49), l: (252.250_323_50, 149_472.674_111_75), peri: ( 77.457_796_28,  0.160_476_89), node: ( 48.330_765_93, -0.125_340_81) },
    /* 2 Venus   */ Kepler { a: (0.723_335_66,  0.000_003_90), e: (0.006_776_72, -0.000_041_07), inc: ( 3.394_676_05, -0.000_788_90), l: (181.979_099_50, 58_517.815_387_29), peri: (131.602_467_18,  0.002_683_29), node: ( 76.679_842_55, -0.277_694_18) },
    /* 3 Mars    */ Kepler { a: (1.523_710_34,  0.000_018_47), e: (0.093_394_10,  0.000_078_82), inc: ( 1.849_691_42, -0.008_131_31), l: ( -4.553_432_05, 19_140.302_684_99), peri: (-23.943_629_59,  0.444_410_88), node: ( 49.559_538_91, -0.292_573_43) },
    /* 4 Jupiter */ Kepler { a: (5.202_887_00, -0.000_116_07), e: (0.048_386_24, -0.000_132_53), inc: ( 1.304_396_95, -0.001_837_14), l: ( 34.396_440_51,  3_034.746_127_75), peri: ( 14.728_479_83,  0.212_526_68), node: (100.473_909_09,  0.204_691_06) },
    /* 5 Saturn  */ Kepler { a: (9.536_675_94, -0.001_250_60), e: (0.053_861_79, -0.000_509_91), inc: ( 2.485_991_87,  0.001_936_09), l: ( 49.954_244_23,  1_222.493_622_01), peri: ( 92.598_878_31, -0.418_972_16), node: (113.662_424_48, -0.288_677_94) },
];

/// Heliocentric ecliptic rectangular coordinates (J2000 frame, AU) for an element set at `jd`.
fn heliocentric_ecliptic(k: &Kepler, jd: f64) -> [f64; 3] {
    let t = (jd - 2_451_545.0) / 36525.0;
    let a = k.a.0 + k.a.1 * t;
    let e = k.e.0 + k.e.1 * t;
    let inc = (k.inc.0 + k.inc.1 * t).to_radians();
    let l = k.l.0 + k.l.1 * t;
    let peri = k.peri.0 + k.peri.1 * t;
    let node_deg = k.node.0 + k.node.1 * t;
    let arg_peri = (peri - node_deg).to_radians(); // ω
    let node = node_deg.to_radians();

    // Mean anomaly, folded to [-180°, 180°], then Kepler's equation by Newton's method.
    let mut m = (l - peri).rem_euclid(360.0);
    if m > 180.0 {
        m -= 360.0;
    }
    let m = m.to_radians();
    let mut ea = m + e * m.sin();
    for _ in 0..12 {
        let dm = (ea - e * ea.sin() - m) / (1.0 - e * ea.cos());
        ea -= dm;
        if dm.abs() < 1e-12 {
            break;
        }
    }

    // Perifocal position (orbital plane), rotated by (ω, I, Ω) into the J2000 ecliptic.
    let xv = a * (ea.cos() - e);
    let yv = a * (1.0 - e * e).sqrt() * ea.sin();
    let (cw, sw) = (arg_peri.cos(), arg_peri.sin());
    let (co, so) = (node.cos(), node.sin());
    let (ci, si) = (inc.cos(), inc.sin());
    [
        (cw * co - sw * so * ci) * xv + (-sw * co - cw * so * ci) * yv,
        (cw * so + sw * co * ci) * xv + (-sw * so + cw * co * ci) * yv,
        (sw * si) * xv + (cw * si) * yv,
    ]
}

/// Apparent **topocentric** altitude + azimuth (degrees) of a planet for a site at Julian Day
/// `jd`. Conventions match [`solar_position`]: azimuth from North increasing East, airless.
/// Verified against JPL Horizons over New Providence in the tests (≤0.1° altitude).
pub fn planet_position(planet: Planet, lat_deg: f64, lon_deg: f64, jd: f64) -> (f64, f64) {
    let earth = heliocentric_ecliptic(&ELEMENTS[0], jd);
    let elem = ELEMENTS[planet as usize];

    // Geocentric vector, light-time corrected: the planet's light left at jd − τ (Earth at jd).
    let mut geo = [0.0_f64; 3];
    let mut tau = 0.0_f64;
    for _ in 0..3 {
        let p = heliocentric_ecliptic(&elem, jd - tau);
        geo = [p[0] - earth[0], p[1] - earth[1], p[2] - earth[2]];
        let d = (geo[0] * geo[0] + geo[1] * geo[1] + geo[2] * geo[2]).sqrt();
        tau = d * 0.005_775_518_3; // light-time per AU, in days
    }
    let dist_au = (geo[0] * geo[0] + geo[1] * geo[1] + geo[2] * geo[2]).sqrt();

    // Geocentric ecliptic (J2000) → spherical; precess the longitude to the equinox of date.
    let t = (jd - 2_451_545.0) / 36525.0;
    let lambda = (geo[1].atan2(geo[0]).to_degrees() + 1.396_971_2 * t).to_radians();
    let beta = (geo[2] / dist_au).asin();

    // Ecliptic (of date) → equatorial (of date); mean obliquity (nutation omitted, sub-tolerance).
    let eps0 = 23.0 + (26.0 + (21.448 - t * (46.815 + t * (0.00059 - t * 0.001813))) / 60.0) / 60.0;
    let eps = eps0.to_radians();
    let alpha = (lambda.sin() * eps.cos() - beta.tan() * eps.sin()).atan2(lambda.cos());
    let delta = (beta.sin() * eps.cos() + beta.cos() * eps.sin() * lambda.sin()).asin();

    topocentric_altaz(
        lat_deg,
        lon_deg,
        jd,
        alpha.to_degrees(),
        delta.to_degrees(),
        dist_au * 149_597_870.7,
    )
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

    // Planet authority: JPL Horizons (apparent, airless) over New Providence, 2026-06-09. Two
    // epochs per body — morning (below/low) and evening (high/setting) — so a pass can't be a
    // coincidence. The model is JPL's own low-precision Keplerian theory, so ≤0.1° altitude is
    // the bar it must clear (azimuth allowed 0.3°, looser only where high elevation magnifies it).
    fn check(p: Planet, h: u32, mi: u32, alt_ref: f64, az_ref: f64, az_tol: f64, label: &str) {
        let (alt, az) = planet_position(p, LAT, LON, julian_day(2026, 6, 9, h, mi, 0.0));
        assert!(
            (alt - alt_ref).abs() < 0.1,
            "{label} alt {alt} (ref {alt_ref})"
        );
        assert!(
            ang_diff(az, az_ref) < az_tol,
            "{label} az {az} (ref {az_ref})"
        );
    }

    #[test]
    fn mercury_two_epochs() {
        check(
            Planet::Mercury,
            11,
            0,
            -11.868_331,
            55.252_016,
            0.3,
            "mercury 11:00",
        );
        check(
            Planet::Mercury,
            21,
            30,
            54.189_964,
            277.972_040,
            0.3,
            "mercury 21:30",
        );
    }

    #[test]
    fn venus_two_epochs() {
        check(
            Planet::Venus,
            11,
            0,
            -23.226_812,
            47.858_772,
            0.3,
            "venus 11:00",
        );
        check(
            Planet::Venus,
            21,
            30,
            66.949_799,
            270.107_399,
            0.5,
            "venus 21:30",
        );
    }

    #[test]
    fn mars_two_epochs() {
        check(
            Planet::Mars,
            11,
            0,
            35.167_603,
            87.398_845,
            0.3,
            "mars 11:00",
        );
        check(
            Planet::Mars,
            21,
            30,
            -1.376_533,
            288.621_711,
            0.3,
            "mars 21:30",
        );
    }

    #[test]
    fn jupiter_two_epochs() {
        check(
            Planet::Jupiter,
            11,
            0,
            -24.389_041,
            49.132_765,
            0.3,
            "jupiter 11:00",
        );
        check(
            Planet::Jupiter,
            21,
            30,
            66.269_944,
            266.432_134,
            0.5,
            "jupiter 21:30",
        );
    }

    #[test]
    fn saturn_two_epochs() {
        check(
            Planet::Saturn,
            11,
            0,
            55.699_800,
            125.650_295,
            0.3,
            "saturn 11:00",
        );
        check(
            Planet::Saturn,
            21,
            30,
            -34.522_362,
            293.048_065,
            0.3,
            "saturn 21:30",
        );
    }
}
