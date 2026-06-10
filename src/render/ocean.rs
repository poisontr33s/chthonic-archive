//! Rung 4 — the ocean surface grid. A flat triangle-list grid at y=0 over the bank's
//! extent; the Gerstner displacement + wave normals run in `water.vert` (surface mode),
//! so this mesh stays static and the GPU animates it from the `time` push constant.
//! The cascaded-FFT spectral surface (Tessendorf, §2.2) replaces the in-shader Gerstner
//! in the next increment (4.2) — this is the prototype it hardens from.
//!
//! @SID:    RENDER_OCEAN_V1
//! @Shabti: Ocean

use super::pipeline::Vertex;

/// Flat surface grid at y=0, `divisions × divisions` cells, fit just inside the 56×22
/// bathymetry extent (WIDTH=5 world units). Triangle list; colour is the base water tint
/// (the surface fragment path overrides it). Cull is disabled, so winding is free.
pub fn surface_grid(divisions: usize) -> Vec<Vertex> {
    const X_HALF: f32 = 2.45; // ≈ (56-1)/2 * (5/56) — just inside the bank in X
    const Z_HALF: f32 = 0.92; // ≈ (22-1)/2 * (5/56) — just inside the bank in Z

    let (nx, nz) = (divisions, divisions);
    let dx = (2.0 * X_HALF) / nx as f32;
    let dz = (2.0 * Z_HALF) / nz as f32;

    let vert = |i: usize, j: usize| -> Vertex {
        Vertex {
            position: [i as f32 * dx - X_HALF, 0.0, j as f32 * dz - Z_HALF],
            normal: [0.0, 1.0, 0.0],
            color: [0.08, 0.34, 0.42],
        }
    };

    let mut verts = Vec::with_capacity(nx * nz * 6);
    for j in 0..nz {
        for i in 0..nx {
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
