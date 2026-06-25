//! WGS84 geodetic foundation for the Ellipsoid retrofit.
//!
//! All math is `f64`. Render paths downcast to `f32` at the ENU→GPU boundary only.
//! Three coordinate systems live here:
//!   LLA   — geodetic (lat °, lon °, alt m above ellipsoid)
//!   ECEF  — Earth-Centred Earth-Fixed Cartesian (metres)
//!   ENU   — local East-North-Up tangent plane relative to an origin in ECEF

//! @SID:    RENDER_GEODESY_V1
//! @Shabti: Geodetic Foundation

use glam::{DMat3, DVec3};

// ── WGS84 constants ──────────────────────────────────────────────────────────

/// Semi-major axis (equatorial radius), metres.
pub const WGS84_A: f64 = 6_378_137.0;
/// Inverse flattening.
const WGS84_INV_F: f64 = 298.257_223_563;
/// Flattening.
pub const WGS84_F: f64 = 1.0 / WGS84_INV_F;
/// First eccentricity squared  e² = 2f − f².
pub const WGS84_E2: f64 = WGS84_F * (2.0 - WGS84_F);
/// Semi-minor axis b = a(1 − f).
pub const WGS84_B: f64 = WGS84_A * (1.0 - WGS84_F);

// ── Prime-vertical radius of curvature ───────────────────────────────────────

/// N(φ) — prime-vertical radius of curvature at geodetic latitude φ (radians).
#[inline]
pub fn prime_vertical_radius(lat_rad: f64) -> f64 {
    let sin_lat = lat_rad.sin();
    WGS84_A / (1.0 - WGS84_E2 * sin_lat * sin_lat).sqrt()
}

// ── LLA ↔ ECEF ───────────────────────────────────────────────────────────────

/// Geodetic latitude/longitude/altitude → ECEF Cartesian (metres).
///
/// `lat_deg`, `lon_deg` in decimal degrees; `alt_m` above the ellipsoid.
pub fn lla_to_ecef(lat_deg: f64, lon_deg: f64, alt_m: f64) -> DVec3 {
    let lat = lat_deg.to_radians();
    let lon = lon_deg.to_radians();
    let n = prime_vertical_radius(lat);
    let cos_lat = lat.cos();
    let sin_lat = lat.sin();
    DVec3::new(
        (n + alt_m) * cos_lat * lon.cos(),
        (n + alt_m) * cos_lat * lon.sin(),
        (n * (1.0 - WGS84_E2) + alt_m) * sin_lat,
    )
}

/// ECEF Cartesian (metres) → geodetic LLA (degrees, degrees, metres).
///
/// Uses Bowring's iterative method. Accurate to sub-millimetre for terrestrial
/// altitudes. Returns `(lat_deg, lon_deg, alt_m)`.
pub fn ecef_to_lla(ecef: DVec3) -> (f64, f64, f64) {
    let x = ecef.x;
    let y = ecef.y;
    let z = ecef.z;

    let lon = y.atan2(x);
    let p = (x * x + y * y).sqrt();

    // Bowring iteration — converges in 2–3 steps for terrestrial points.
    let mut lat = z.atan2(p * (1.0 - WGS84_E2));
    for _ in 0..5 {
        let n = prime_vertical_radius(lat);
        lat = (z + WGS84_E2 * n * lat.sin()).atan2(p);
    }

    let n = prime_vertical_radius(lat);
    let alt = if lat.cos().abs() > 1e-10 {
        p / lat.cos() - n
    } else {
        z.abs() / lat.sin() - n * (1.0 - WGS84_E2)
    };

    (lat.to_degrees(), lon.to_degrees(), alt)
}

// ── ENU basis ────────────────────────────────────────────────────────────────

/// 3×3 rotation matrix that maps ECEF vectors to local ENU axes at `origin_ecef`.
///
/// Columns are [East, North, Up] expressed in ECEF frame.
/// Apply as: `enu_vec = enu_basis_matrix(origin).transpose() * (ecef_point - origin)`.
pub fn enu_basis_matrix(lat_deg: f64, lon_deg: f64) -> DMat3 {
    let lat = lat_deg.to_radians();
    let lon = lon_deg.to_radians();

    let sin_lat = lat.sin();
    let cos_lat = lat.cos();
    let sin_lon = lon.sin();
    let cos_lon = lon.cos();

    // East:  (-sin_lon, cos_lon, 0)
    // North: (-sin_lat·cos_lon, -sin_lat·sin_lon, cos_lat)
    // Up:    ( cos_lat·cos_lon,  cos_lat·sin_lon, sin_lat)
    DMat3::from_cols(
        DVec3::new(-sin_lon, cos_lon, 0.0),
        DVec3::new(-sin_lat * cos_lon, -sin_lat * sin_lon, cos_lat),
        DVec3::new(cos_lat * cos_lon, cos_lat * sin_lon, sin_lat),
    )
}

// ── ECEF ↔ ENU ───────────────────────────────────────────────────────────────

/// Convert an ECEF point to ENU coordinates relative to `origin_ecef`.
///
/// `origin_lat_deg`, `origin_lon_deg`: geodetic coordinates of the ENU origin.
pub fn ecef_to_enu(
    point_ecef: DVec3,
    origin_ecef: DVec3,
    origin_lat_deg: f64,
    origin_lon_deg: f64,
) -> DVec3 {
    let delta = point_ecef - origin_ecef;
    let rot = enu_basis_matrix(origin_lat_deg, origin_lon_deg);
    // rot columns are E, N, U in ECEF space; transpose rotates ECEF→ENU.
    rot.transpose() * delta
}

/// Convert an ENU vector (relative to origin) back to ECEF.
pub fn enu_to_ecef(
    enu: DVec3,
    origin_ecef: DVec3,
    origin_lat_deg: f64,
    origin_lon_deg: f64,
) -> DVec3 {
    let rot = enu_basis_matrix(origin_lat_deg, origin_lon_deg);
    origin_ecef + rot * enu
}

// ── Camera-relative helpers ───────────────────────────────────────────────────

/// Anchor: a world position expressed in both ECEF and its geodetic LLA.
///
/// The render pipeline chooses a per-frame anchor (typically the camera eye
/// position). All geometry is expressed in ENU relative to this anchor and
/// downcast to `f32` for the GPU. This keeps vertex positions in the
/// ±tens-of-kilometres range where `f32` precision is adequate.
#[derive(Clone, Copy, Debug)]
pub struct GeoAnchor {
    pub ecef: DVec3,
    pub lat_deg: f64,
    pub lon_deg: f64,
    pub alt_m: f64,
}

impl GeoAnchor {
    /// Build from geodetic coordinates.
    pub fn from_lla(lat_deg: f64, lon_deg: f64, alt_m: f64) -> Self {
        Self {
            ecef: lla_to_ecef(lat_deg, lon_deg, alt_m),
            lat_deg,
            lon_deg,
            alt_m,
        }
    }

    /// Build from ECEF (derives LLA via Bowring).
    pub fn from_ecef(ecef: DVec3) -> Self {
        let (lat_deg, lon_deg, alt_m) = ecef_to_lla(ecef);
        Self { ecef, lat_deg, lon_deg, alt_m }
    }

    /// Express an ECEF point as ENU metres relative to this anchor.
    #[inline]
    pub fn ecef_to_local_enu(&self, point_ecef: DVec3) -> DVec3 {
        ecef_to_enu(point_ecef, self.ecef, self.lat_deg, self.lon_deg)
    }

    /// Express a geodetic point as ENU metres relative to this anchor.
    #[inline]
    pub fn lla_to_local_enu(&self, lat_deg: f64, lon_deg: f64, alt_m: f64) -> DVec3 {
        let p = lla_to_ecef(lat_deg, lon_deg, alt_m);
        self.ecef_to_local_enu(p)
    }
}

// ── New Providence constants (project reference datum) ───────────────────────

/// Nassau, New Providence, Bahamas — the fixed scene datum for the Chthonic Archive.
pub const NEW_PROVIDENCE_LAT_DEG: f64 = 25.048_9;
pub const NEW_PROVIDENCE_LON_DEG: f64 = -77.355_5;
pub const NEW_PROVIDENCE_ALT_M: f64 = 0.0;

#[cfg(test)]
mod tests {
    use super::*;

    const TOL: f64 = 1e-6; // 1 µm or 1 µ-degree tolerance

    #[test]
    fn round_trip_lla_ecef_nassau() {
        let (lat, lon, alt) = (25.04, -77.35, 0.0);
        let ecef = lla_to_ecef(lat, lon, alt);
        let (rlat, rlon, ralt) = ecef_to_lla(ecef);
        assert!((rlat - lat).abs() < TOL, "lat round-trip: {rlat} vs {lat}");
        assert!((rlon - lon).abs() < TOL, "lon round-trip: {rlon} vs {lon}");
        assert!(ralt.abs() < 1e-3, "alt round-trip: {ralt}m");
    }

    #[test]
    fn round_trip_lla_ecef_equator() {
        let (lat, lon, alt) = (0.0, 0.0, 0.0);
        let ecef = lla_to_ecef(lat, lon, alt);
        assert!((ecef.x - WGS84_A).abs() < 1e-3, "equator x = a");
        assert!(ecef.y.abs() < 1e-3);
        assert!(ecef.z.abs() < 1e-3);
    }

    #[test]
    fn round_trip_lla_ecef_pole() {
        let (lat, lon, alt) = (90.0, 0.0, 0.0);
        let ecef = lla_to_ecef(lat, lon, alt);
        assert!(ecef.x.abs() < 1e-3, "pole x ≈ 0");
        assert!(ecef.y.abs() < 1e-3, "pole y ≈ 0");
        assert!((ecef.z - WGS84_B).abs() < 1e-3, "pole z = b");
    }

    #[test]
    fn enu_zero_at_origin() {
        let (lat, lon, alt) = (25.04, -77.35, 0.0);
        let ecef = lla_to_ecef(lat, lon, alt);
        let anchor = GeoAnchor::from_lla(lat, lon, alt);
        let enu = anchor.ecef_to_local_enu(ecef);
        assert!(enu.length() < 1e-6, "origin → ENU zero vector: {enu:?}");
    }

    #[test]
    fn enu_east_is_east() {
        let (lat, lon) = (0.0f64, 0.0f64);
        let anchor = GeoAnchor::from_lla(lat, lon, 0.0);
        // 1 km east along the equator.
        let east_ecef = lla_to_ecef(lat, lon + 0.009, 0.0); // ~1 km east
        let enu = anchor.ecef_to_local_enu(east_ecef);
        assert!(enu.x > 0.0, "East displacement has positive ENU.x: {enu:?}");
        assert!(enu.y.abs() < enu.x * 0.1, "ENU.y (North) small relative to East");
    }

    #[test]
    fn enu_up_is_up() {
        let (lat, lon) = (25.04f64, -77.35f64);
        let anchor = GeoAnchor::from_lla(lat, lon, 0.0);
        let above = lla_to_ecef(lat, lon, 1000.0); // 1 km straight up
        let enu = anchor.ecef_to_local_enu(above);
        assert!((enu.z - 1000.0).abs() < 1.0, "1 km up = ENU.z ≈ 1000m: {enu:?}");
        assert!(enu.x.abs() < 1.0, "no East drift going straight up");
        assert!(enu.y.abs() < 1.0, "no North drift going straight up");
    }

    #[test]
    fn ecef_enu_round_trip() {
        let anchor = GeoAnchor::from_lla(25.04, -77.35, 0.0);
        let test_enu = DVec3::new(500.0, -300.0, 100.0);
        let ecef = enu_to_ecef(test_enu, anchor.ecef, anchor.lat_deg, anchor.lon_deg);
        let back = anchor.ecef_to_local_enu(ecef);
        assert!(
            (back - test_enu).length() < 1e-6,
            "ENU→ECEF→ENU round-trip failed: {back:?} vs {test_enu:?}"
        );
    }
}
