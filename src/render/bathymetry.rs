//! Bathymetry heightfield — real GEBCO depth turned into a renderable mesh.

//! @SID:    RENDER_BATHYMETRY_V1
//! @Shabti: Bathymetry

//! Rung 3 of `CLAUDEBASE/charts/north-star-constellations.md`: load the grounded
//! `CLAUDEBASE/charts/bathymetry.json` (real GEBCO 2020 seafloor depth, verified data
//! plane) and emit a triangle-list heightfield fit to the isometric camera box. Reuses
//! the existing `iso_grid` pipeline (position + color); the shallow-water shader is rung 5.

use anyhow::{ensure, Context, Result};
use serde::Deserialize;
use std::path::Path;

use super::pipeline::Vertex;

/// Where the grounded data plane lives, relative to the repo root (the cargo run CWD).
pub const DEFAULT_PATH: &str = "CLAUDEBASE/charts/bathymetry.json";

/// Parsed `bathymetry.json` — only the fields the mesh needs.
#[derive(Deserialize)]
pub struct Bathymetry {
    #[serde(rename = "W")]
    pub w: usize,
    #[serde(rename = "H")]
    pub h: usize,
    /// Row-major `w * h` elevations in metres: `+` = land above sea, `-` = below sea.
    pub depth: Vec<f32>,
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

    /// Triangle-list heightfield, centred on origin and fit to the iso camera box.
    /// Square cells across a ~5-unit width; Y = depth scaled; vertex colour banded by
    /// depth (placeholder for the rung-5 Beer–Lambert shader).
    pub fn mesh(&self) -> Vec<Vertex> {
        const WIDTH: f32 = 5.0; // matches ortho_size * 2 of the iso camera
        const Y_SCALE: f32 = 0.0004; // -5500 m -> -2.2, +1024 m -> +0.41 (fits the box)

        let cell = WIDTH / self.w as f32;
        let cx = (self.w as f32 - 1.0) * 0.5;
        let cz = (self.h as f32 - 1.0) * 0.5;

        // Clamped raw-depth sampler (metres), for central-difference normals at the edges.
        let sample = |i: i64, j: i64| -> f32 {
            let ic = i.clamp(0, self.w as i64 - 1) as usize;
            let jc = j.clamp(0, self.h as i64 - 1) as usize;
            self.depth_at(ic, jc)
        };

        let vert = |i: usize, j: usize| -> Vertex {
            let (ii, jj) = (i as i64, j as i64);
            let d = sample(ii, jj);
            // Heightfield normal from central differences (world units): n = (-dy/dx, 1, -dy/dz).
            let dydx = (sample(ii + 1, jj) - sample(ii - 1, jj)) * Y_SCALE / (2.0 * cell);
            let dydz = (sample(ii, jj + 1) - sample(ii, jj - 1)) * Y_SCALE / (2.0 * cell);
            let inv = 1.0 / (dydx * dydx + 1.0 + dydz * dydz).sqrt();
            Vertex {
                position: [
                    (i as f32 - cx) * cell,
                    d * Y_SCALE,
                    (j as f32 - cz) * cell,
                ],
                normal: [-dydx * inv, inv, -dydz * inv],
                color: depth_color(d),
            }
        };

        let mut verts = Vec::with_capacity((self.w - 1) * (self.h - 1) * 6);
        for j in 0..self.h - 1 {
            for i in 0..self.w - 1 {
                // two triangles per cell (cull is disabled, so winding is free)
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

/// Depth → banded colour. Placeholder for rung 5's depth-attenuated turquoise; for now it
/// just makes the Banks legible: sand land, turquoise shallows, navy deep.
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
