//! Ocean surface meshes.
//!
//! `surface_grid`  — legacy uniform 128×128 grid (kept for reference).
//! `clipmap_grid`  — LOD clipmap: finest cells at centre, coarsening toward the bank edges.
//!
//! ## Geometry clipmap layout
//!
//! Levels are indexed 0 (innermost / finest) → L-1 (outermost / coarsest).
//! Each level k contributes:
//!   • Level 0: a filled (2n × 2n) centre patch at cell size dx₀.
//!   • Level k>0: a hollow square frame of n/2 cells wide on each side, at cell size dx₀ × 2^k.
//!
//! Half-extent of level k: n × dx₀ × 2^k.
//! Cell size doubles per level so the outer boundary of level L-1 = X_HALF (bank edge).
//!
//! T-junctions between levels are accepted at this stage; displacement is smooth so
//! sub-pixel seams are imperceptible at the current static camera.

//! @SID:    RENDER_OCEAN_V1
//! @Shabti: Ocean

use super::pipeline::Vertex;

// ELLIPSOID-RETROFIT: X_HALF/Z_HALF are flat Cartesian half-extents (must also change in water.vert).
// Under WGS84 these become camera-relative ENU bounds derived from the geodetic tile extent.
const X_HALF: f32 = 2.45;
const Z_HALF: f32 = 0.92;
const BASE_COLOR: [f32; 3] = [0.08, 0.34, 0.42];
const FLAT_NORMAL: [f32; 3] = [0.0, 1.0, 0.0];

// ─────────────────────────────────────────────────────────────────────────────

/// LOD geometry clipmap for the ocean surface.
///
/// `levels` — number of LOD levels (4 is a good default).
/// `ring_n` — determines inner patch size (2*ring_n × 2*ring_n cells) and frame width (ring_n/2).
///
/// With `levels=4, ring_n=32`:
///   Level 0: 64×64 cells at dx₀ ≈ 0.0096 world units (≈ 256×256 uniform density at centre).
///   Level 3: cells at 8×dx₀ ≈ 0.077 world units at the bank edge.
///   Total ≈ 13 K cells (vs 16 K for the uniform 128×128).
pub fn clipmap_grid(levels: u32, ring_n: u32) -> Vec<Vertex> {
    // dx₀ chosen so the outer boundary of level (levels-1) = ±X_HALF / ±Z_HALF.
    // outer_k = ring_n × dx₀ × 2^k  →  ring_n × dx₀ × 2^(levels-1) = X_HALF
    let base_dx = X_HALF / (ring_n as f32 * (1u32 << (levels - 1)) as f32);
    let base_dz = Z_HALF / (ring_n as f32 * (1u32 << (levels - 1)) as f32);

    let n = ring_n as i32;
    // Upper-bound capacity estimate: centre (2n)² + (levels-1) frames × 3n² cells × 6 verts.
    let cap = (4 * n * n + 3 * n * n * (levels as i32 - 1)) as usize * 6;
    let mut verts: Vec<Vertex> = Vec::with_capacity(cap);

    for level in 0..levels {
        let scale = (1u32 << level) as f32;
        let dx = base_dx * scale;
        let dz = base_dz * scale;

        // Half-extent (world units) of this level's outer boundary.
        let outer_x = ring_n as f32 * base_dx * scale;
        let outer_z = ring_n as f32 * base_dz * scale;
        // Inner boundary (= outer of the previous level).
        let inner_x = if level == 0 { 0.0 } else { outer_x * 0.5 };
        let inner_z = if level == 0 { 0.0 } else { outer_z * 0.5 };

        if level == 0 {
            // Filled centre patch: cells in [-outer_x, outer_x] × [-outer_z, outer_z].
            // i, j iterate in cell-count space: 2n cells per axis.
            let half = n; // cells from origin to edge = n
            for j in -half..half {
                for i in -half..half {
                    push_quad(
                        &mut verts,
                        i as f32 * dx,
                        j as f32 * dz,
                        dx,
                        dz,
                    );
                }
            }
        } else {
            // Frame: 4 sub-regions.

            // Top strip: x ∈ [-outer_x, outer_x], z ∈ [inner_z, outer_z].
            emit_strip(
                &mut verts,
                -outer_x,  inner_z,
                dx, dz,
                (2 * n) as u32,
                (n / 2) as u32,
            );
            // Bottom strip: x ∈ [-outer_x, outer_x], z ∈ [-outer_z, -inner_z].
            emit_strip(
                &mut verts,
                -outer_x, -outer_z,
                dx, dz,
                (2 * n) as u32,
                (n / 2) as u32,
            );
            // Left column: x ∈ [-outer_x, -inner_x], z ∈ [-inner_z, inner_z].
            emit_strip(
                &mut verts,
                -outer_x, -inner_z,
                dx, dz,
                (n / 2) as u32,
                n as u32,
            );
            // Right column: x ∈ [inner_x, outer_x], z ∈ [-inner_z, inner_z].
            emit_strip(
                &mut verts,
                inner_x, -inner_z,
                dx, dz,
                (n / 2) as u32,
                n as u32,
            );
        }
    }

    verts
}

/// Emit `cols × rows` quads starting at world origin `(ox, oz)` with cell size `dx × dz`.
fn emit_strip(verts: &mut Vec<Vertex>, ox: f32, oz: f32, dx: f32, dz: f32, cols: u32, rows: u32) {
    for j in 0..rows {
        for i in 0..cols {
            push_quad(verts, ox + i as f32 * dx, oz + j as f32 * dz, dx, dz);
        }
    }
}

/// Emit one quad (two triangles, triangle-list) with lower-left corner at `(x0, z0)`.
#[inline]
fn push_quad(verts: &mut Vec<Vertex>, x0: f32, z0: f32, dx: f32, dz: f32) {
    let v = |x: f32, z: f32| Vertex {
        position: [x, 0.0, z],
        normal: FLAT_NORMAL,
        color: BASE_COLOR,
    };
    verts.push(v(x0,       z0      ));
    verts.push(v(x0 + dx,  z0      ));
    verts.push(v(x0,       z0 + dz ));
    verts.push(v(x0 + dx,  z0      ));
    verts.push(v(x0 + dx,  z0 + dz ));
    verts.push(v(x0,       z0 + dz ));
}

// ─────────────────────────────────────────────────────────────────────────────

/// Legacy uniform grid, kept for comparison.
pub fn surface_grid(divisions: usize) -> Vec<Vertex> {
    let (nx, nz) = (divisions, divisions);
    let dx = (2.0 * X_HALF) / nx as f32;
    let dz = (2.0 * Z_HALF) / nz as f32;

    let mut verts = Vec::with_capacity(nx * nz * 6);
    for j in 0..nz {
        for i in 0..nx {
            push_quad(
                &mut verts,
                i as f32 * dx - X_HALF,
                j as f32 * dz - Z_HALF,
                dx,
                dz,
            );
        }
    }
    verts
}
