//! Bathymetry heightfield — real GEBCO depth turned into a renderable mesh.

//! @SID:    RENDER_BATHYMETRY_V1
//! @Shabti: Bathymetry

//! Rung 3 of `CLAUDEBASE/charts/north-star-constellations.md`: load the grounded
//! `CLAUDEBASE/charts/bathymetry.json` (real GEBCO 2020 seafloor depth, verified data
//! plane) and emit a triangle-list heightfield. Reuses the existing `iso_grid` pipeline
//! (position + color); the shallow-water shader is rung 5.
//!
//! Site 2 — Ellipsoid Fork I: vertices are now in WGS84 ENU space (East→X, Up→Y,
//! North→Z) relative to the Nassau anchor. Y_SCALE is 1.0; render.y IS metres.

use anyhow::{ensure, Context, Result};
use serde::Deserialize;
use std::path::Path;

use super::geodesy::{
    GeoAnchor, WGS84_A, NEW_PROVIDENCE_ALT_M, NEW_PROVIDENCE_LAT_DEG, NEW_PROVIDENCE_LON_DEG,
};
use super::pipeline::Vertex;

/// Where the grounded data plane lives, relative to the repo root (the cargo run CWD).
pub const DEFAULT_PATH: &str = "CLAUDEBASE/charts/bathymetry.json";

/// Geographic bounding box from GEBCO JSON.
#[derive(Deserialize)]
struct Bbox {
    #[serde(rename = "minLat")]
    min_lat: f64,
    #[serde(rename = "maxLat")]
    max_lat: f64,
    #[serde(rename = "minLon")]
    min_lon: f64,
    #[serde(rename = "maxLon")]
    max_lon: f64,
}

/// Parsed `bathymetry.json` — only the fields the mesh needs.
#[derive(Deserialize)]
pub struct Bathymetry {
    #[serde(rename = "W")]
    pub w: usize,
    #[serde(rename = "H")]
    pub h: usize,
    /// Row-major `w * h` elevations in metres: `+` = land above sea, `-` = below sea.
    pub depth: Vec<f32>,
    /// Geographic bounding box of the GEBCO extract.
    bbox: Bbox,
}

impl Bathymetry {
    /// Load and validate the depth grid.
    pub fn load(path: impl AsRef<Path>) -> Result<Self> {
        let path = path.as_ref();
        let raw = std::fs::read_to_string(path)
            .with_context(|| format!("read bathymetry {}", path.display()))?;
        let b: Self = serde_json::from_str(&raw).context("parse bathymetry.json")?;
        ensure!(
            b.depth.len() == b.w * b.h,
            "bathymetry depth len {} != {}x{}",
            b.depth.len(),
            b.w,
            b.h
        );
        Ok(b)
    }

    fn depth_at(&self, i: usize, j: usize) -> f32 {
        self.depth[j * self.w + i]
    }

    /// Triangle-list heightfield in WGS84 ENU space.
    ///
    /// Vertex positions are geodetic: LLA → ECEF → ENU relative to the Nassau anchor.
    /// Render-space layout: East→X, elevation→Y (metres), North→Z.
    /// The Nassau anchor matches the camera anchor; both share the same ENU origin
    /// until camera panning is live.
    pub fn mesh(&self) -> Vec<Vertex> {
        let anchor = GeoAnchor::from_lla(
            NEW_PROVIDENCE_LAT_DEG,
            NEW_PROVIDENCE_LON_DEG,
            NEW_PROVIDENCE_ALT_M,
        );

        let lat_step = (self.bbox.max_lat - self.bbox.min_lat) / (self.h as f64 - 1.0);
        let lon_step = (self.bbox.max_lon - self.bbox.min_lon) / (self.w as f64 - 1.0);

        // Metric cell sizes for normal computation (approximation: <2% error over this grid).
        let lat_center = (self.bbox.min_lat + self.bbox.max_lat) * 0.5;
        let east_cell_m =
            (lon_step.to_radians() * WGS84_A * lat_center.to_radians().cos()) as f32;
        let north_cell_m = (lat_step.to_radians() * WGS84_A) as f32;

        // Clamped raw-depth sampler (metres), for central-difference normals at edges.
        let sample = |i: i64, j: i64| -> f32 {
            let ic = i.clamp(0, self.w as i64 - 1) as usize;
            let jc = j.clamp(0, self.h as i64 - 1) as usize;
            self.depth_at(ic, jc)
        };

        let vert = |i: usize, j: usize| -> Vertex {
            let (ii, jj) = (i as i64, j as i64);
            let d = sample(ii, jj);

            // Row j=0 is the northernmost row (maxLat); rows increase southward.
            let lat = self.bbox.max_lat - j as f64 * lat_step;
            let lon = self.bbox.min_lon + i as f64 * lon_step;

            // ENU from Nassau anchor → render space: East→X, Up/elevation→Y, North→Z.
            let enu = anchor.lla_to_local_enu(lat, lon, d as f64);
            let position = [enu.x as f32, enu.z as f32, enu.y as f32];

            // Normal via central differences (elevation in m, cell sizes in m → dimensionless slope).
            let dydx = (sample(ii + 1, jj) - sample(ii - 1, jj)) / (2.0 * east_cell_m);
            let dydz = (sample(ii, jj + 1) - sample(ii, jj - 1)) / (2.0 * north_cell_m);
            let inv = 1.0 / (dydx * dydx + 1.0 + dydz * dydz).sqrt();

            Vertex {
                position,
                normal: [-dydx * inv, inv, -dydz * inv],
                color: depth_color(d),
            }
        };

        let mut verts = Vec::with_capacity((self.w - 1) * (self.h - 1) * 6);
        for j in 0..self.h - 1 {
            for i in 0..self.w - 1 {
                verts.push(vert(i, j));
                verts.push(vert(i + 1, j));
                verts.push(vert(i, j + 1));
                verts.push(vert(i + 1, j));
                verts.push(vert(i + 1, j + 1));
                verts.push(vert(i, j + 1));
            }
        }
        verts
    }
}

/// Depth → banded colour. Placeholder for the Beer–Lambert shader's depth-attenuated
/// turquoise; makes the Banks legible without shader output.
fn depth_color(d: f32) -> [f32; 3] {
    if d >= 0.0 {
        [0.82, 0.74, 0.52] // land / carbonate sand
    } else if d > -10.0 {
        [0.30, 0.85, 0.80] // the Banks — bright turquoise shallows
    } else if d > -60.0 {
        [0.10, 0.65, 0.70] // shallow shelf
    } else if d > -200.0 {
        [0.06, 0.35, 0.62] // shelf edge
    } else if d > -1500.0 {
        [0.03, 0.15, 0.45] // slope
    } else {
        [0.01, 0.04, 0.20] // deep navy
    }
}
