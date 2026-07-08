// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: camera.rs
// ║ Rust module: IsometricCamera, new, update_matrices
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Spectral Frequency: RED
// ║ Architectural Role: 🏰 THE FORTRESS
// ║ Purpose: Isometric Camera System
// ║ Exports: IsometricCamera, new, update_matrices, view_matrix, projection_matrix
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Cross-References (Bidirectional):
// ║  (Standalone file - no detected dependencies)
// ╚════════════════════════════════════════════════════════════════════════════

//! Isometric Camera System

//! @SID:    RENDER_CAMERA_V1
//! @Shabti: Camera

//! "The Ultimate pleasure found in the relentless transformation of perspective"
//! — Orackla Nocticula

//! Implements the Gemini-specified isometric camera:
//! - Orthographic projection
//! - Y-axis rotation: 45°
//! - X-axis rotation: ~35.264° (arctan(1/√2))
//!
//! Trajectory marker, not active code: `north-star-constellations.md` §2.7 calls for
//! perspective and celestial lenses to compound with this camera later. Keep those
//! lenses out of this module until a real view abstraction exists; do not add an
//! automatic loop or a competing camera mode here. The current compiled contract is
//! one isometric camera that the renderer can enrich with additional visible layers.

//! The isometric projection creates the classic "2.5D" view where:
//! - Vertical lines remain vertical
//! - Horizontal lines are at 30° angles
//! - Equal foreshortening on all three axes

use glam::{DVec3, Mat4, Vec3};
use log::info;

use crate::render::geodesy::GeoAnchor;

/// Isometric camera configuration.
pub struct IsometricCamera {
    /// Camera position in world space.
    pub position: Vec3,
    /// Target point the camera looks at.
    pub target: Vec3,
    /// Camera distance from the target.
    pub distance: f32,
    /// Orthographic view bounds (half-width, half-height).
    pub ortho_size: f32,
    /// Near clipping plane.
    pub near: f32,
    /// Far clipping plane.
    pub far: f32,
    /// View matrix (world → camera).
    view: Mat4,
    /// Projection matrix (camera → NDC).
    projection: Mat4,
    /// Absolute WGS84 anchor. `None` = flat Cartesian (Lagoon mode).
    /// When set, `position`/`target` are ENU-local metres relative to this anchor.
    pub anchor: Option<GeoAnchor>,
}

impl IsometricCamera {
    /// Create a new isometric camera.
    ///
    /// # Arguments
    /// * `target` - Point in world space the camera looks at.
    /// * `distance` - Distance from target along the isometric view ray.
    /// * `ortho_size` - Half-size of the orthographic frustum.
    pub fn new(target: Vec3, distance: f32, ortho_size: f32) -> Self {
        let mut camera = Self {
            position: target,
            target,
            distance,
            ortho_size,
            near: -100.0, // Allow objects behind camera plane in ortho.
            far: 100.0,
            view: Mat4::IDENTITY,
            projection: Mat4::IDENTITY,
            anchor: None,
        };

        camera.update_matrices(1.0);
        camera.log_initial_state();
        camera
    }

    /// Update view and projection matrices.
    ///
    /// # Arguments
    /// * `aspect_ratio` - Window width / height.
    pub fn update_matrices(&mut self, aspect_ratio: f32) {
        self.position = self.target + Self::isometric_offset(self.distance);
        self.view = Mat4::look_at_rh(self.position, self.target, Vec3::Y);

        let half_width = self.ortho_size * aspect_ratio;
        let half_height = self.ortho_size;
        self.projection = Mat4::orthographic_rh(
            -half_width,
            half_width,
            -half_height,
            half_height,
            self.near,
            self.far,
        );
    }

    fn isometric_offset(distance: f32) -> Vec3 {
        const ISO_X_ANGLE: f32 = 0.615_479_7; // arctan(1/sqrt(2)).
        const ISO_Y_ANGLE: f32 = std::f32::consts::FRAC_PI_4;

        let cos_x = ISO_X_ANGLE.cos();
        let sin_x = ISO_X_ANGLE.sin();
        let cos_y = ISO_Y_ANGLE.cos();
        let sin_y = ISO_Y_ANGLE.sin();

        Vec3::new(
            distance * cos_x * sin_y,
            distance * sin_x,
            distance * cos_x * cos_y,
        )
    }

    fn log_initial_state(&self) {
        info!("╔══════════════════════════════════════════════════════════════╗");
        info!("║   ISOMETRIC CAMERA INITIALIZED                              ║");
        info!("╠══════════════════════════════════════════════════════════════╣");
        info!(
            "║   Position: ({x:.2}, {y:.2}, {z:.2})",
            x = self.position.x,
            y = self.position.y,
            z = self.position.z
        );
        info!(
            "║   Target:   ({tx:.2}, {ty:.2}, {tz:.2})",
            tx = self.target.x,
            ty = self.target.y,
            tz = self.target.z
        );
        info!("║   Distance: {distance:.2}", distance = self.distance);
        info!(
            "║   Ortho Size: {ortho_size:.2}",
            ortho_size = self.ortho_size
        );
        info!("╚══════════════════════════════════════════════════════════════╝");
    }

    /// Get the view matrix.
    #[inline]
    #[allow(dead_code)]
    pub fn view_matrix(&self) -> Mat4 {
        self.view
    }

    /// Get the projection matrix.
    #[inline]
    #[allow(dead_code)]
    pub fn projection_matrix(&self) -> Mat4 {
        self.projection
    }

    /// Get combined view-projection matrix.
    #[inline]
    #[allow(dead_code)]
    pub fn view_projection(&self) -> Mat4 {
        self.projection * self.view
    }

    /// Convert view matrix to array format for push constants.
    #[allow(dead_code)]
    pub fn view_as_array(&self) -> [[f32; 4]; 4] {
        self.view.to_cols_array_2d()
    }

    /// Convert projection matrix to array format for push constants.
    #[allow(dead_code)]
    pub fn projection_as_array(&self) -> [[f32; 4]; 4] {
        self.projection.to_cols_array_2d()
    }

    /// Set camera distance from target (zoom).
    #[allow(dead_code)]
    pub fn set_distance(&mut self, distance: f32, aspect_ratio: f32) {
        self.distance = distance;
        self.update_matrices(aspect_ratio);
    }

    /// Move camera target (pan).
    pub fn set_target(&mut self, target: Vec3, aspect_ratio: f32) {
        let offset = self.position - self.target;
        self.target = target;
        self.position = target + offset;
        self.update_matrices(aspect_ratio);
    }

    /// Ground-plane forward/right axes for this camera's current view direction — the horizontal
    /// projection of (target - position) and its 90° rotation, both unit length. Used for input
    /// panning so movement stays screen-relative (W moves toward what's "up" on screen) rather
    /// than sliding along raw world axes, which would feel wrong under the fixed isometric angle.
    /// Derived from the live position/target rather than re-deriving the isometric angle
    /// constants, so this stays correct even if the offset formula ever changes.
    pub fn ground_axes(&self) -> (Vec3, Vec3) {
        let mut forward = self.target - self.position;
        forward.y = 0.0;
        let forward = forward.normalize_or_zero();
        let right = forward.cross(Vec3::Y).normalize_or_zero();
        (forward, right)
    }

    /// Scale-based zoom. `distance` alone is a near-no-op for what actually renders under
    /// orthographic projection — moving the eye along the view ray without changing the frustum
    /// extent doesn't change the image at all. `ortho_size` is the real zoom control; this keeps
    /// `distance` at the same 2x ratio the renderer's own construction established, so near/far
    /// clipping headroom doesn't drift out of proportion as the zoom level changes.
    pub fn zoom(&mut self, scale: f32, aspect_ratio: f32) {
        const MIN_ORTHO_SIZE: f32 = 50.0;
        self.ortho_size = (self.ortho_size * scale).max(MIN_ORTHO_SIZE);
        self.distance = self.ortho_size * 2.0;
        self.update_matrices(aspect_ratio);
    }

    /// Build a camera anchored to a WGS84 geodetic position.
    ///
    /// The render-space origin is placed at the anchor; `position` and `target`
    /// are ENU-local metres (typically small near-zero values). Flat-Cartesian
    /// behaviour is unchanged when `anchor` stays `None`.
    pub fn with_geodetic_anchor(
        lat_deg: f64,
        lon_deg: f64,
        alt_m: f64,
        distance: f32,
        ortho_size: f32,
    ) -> Self {
        let mut cam = Self::new(Vec3::ZERO, distance, ortho_size);
        cam.anchor = Some(GeoAnchor::from_lla(lat_deg, lon_deg, alt_m));
        cam
    }

    /// Project an absolute ECEF coordinate into the current f32 render space.
    ///
    /// With an anchor set: returns the ENU displacement from the anchor, cast
    /// to f32. This is the floating-origin transform — the GPU sees values in
    /// the ±tens-of-kilometres range where f32 precision is adequate.
    ///
    /// Without an anchor (Lagoon mode): casts the raw ECEF components to f32.
    #[allow(dead_code)]
    pub fn project_ecef_to_render(&self, ecef: DVec3) -> Vec3 {
        match &self.anchor {
            Some(anchor) => {
                let enu = anchor.ecef_to_local_enu(ecef);
                // East→X, Up/elevation→Y, North→Z (render space convention).
                Vec3::new(enu.x as f32, enu.z as f32, enu.y as f32)
            }
            None => Vec3::new(ecef.x as f32, ecef.y as f32, ecef.z as f32),
        }
    }
}

impl Default for IsometricCamera {
    fn default() -> Self {
        Self::new(Vec3::ZERO, 10.0, 5.0)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn ground_axes_are_unit_and_perpendicular() {
        let camera = IsometricCamera::new(Vec3::ZERO, 10.0, 5.0);
        let (forward, right) = camera.ground_axes();
        assert!((forward.length() - 1.0).abs() < 1e-5, "forward not unit length: {forward:?}");
        assert!((right.length() - 1.0).abs() < 1e-5, "right not unit length: {right:?}");
        assert!(forward.dot(right).abs() < 1e-5, "forward/right not perpendicular");
        assert_eq!(forward.y, 0.0, "forward must stay in the ground plane");
        assert_eq!(right.y, 0.0, "right must stay in the ground plane");
    }

    #[test]
    fn ground_axes_forward_points_from_eye_to_target() {
        let camera = IsometricCamera::new(Vec3::ZERO, 10.0, 5.0);
        let (forward, _right) = camera.ground_axes();
        let to_target = (camera.target - camera.position).with_y(0.0);
        assert!(
            forward.dot(to_target.normalize_or_zero()) > 0.99,
            "forward should point toward the target, got {forward:?} vs {to_target:?}"
        );
    }

    #[test]
    fn zoom_scales_ortho_size_and_keeps_distance_ratio() {
        let mut camera = IsometricCamera::new(Vec3::ZERO, 800_000.0, 400_000.0);
        camera.zoom(0.5, 16.0 / 9.0);
        assert!((camera.ortho_size - 200_000.0).abs() < 1.0, "ortho_size {}", camera.ortho_size);
        assert!((camera.distance - 400_000.0).abs() < 1.0, "distance {}", camera.distance);
    }

    #[test]
    fn zoom_floor_prevents_degenerate_frustum() {
        let mut camera = IsometricCamera::new(Vec3::ZERO, 800_000.0, 400_000.0);
        for _ in 0..40 {
            camera.zoom(0.5, 16.0 / 9.0); // repeated deep zoom-in
        }
        assert!(camera.ortho_size >= 50.0, "ortho_size fell below the floor: {}", camera.ortho_size);
        assert!(camera.ortho_size > 0.0, "ortho_size must stay strictly positive");
    }

    #[test]
    fn test_camera_creation() {
        let camera = IsometricCamera::new(Vec3::ZERO, 10.0, 5.0);

        // Camera should be positioned above and to the side.
        assert!(camera.position.y > 0.0, "Camera should be above target");
        assert!(camera.position.x > 0.0, "Camera should be offset in X");
        assert!(camera.position.z > 0.0, "Camera should be offset in Z");
    }

    #[test]
    fn test_matrices_update() {
        let mut camera = IsometricCamera::new(Vec3::ZERO, 10.0, 5.0);
        camera.update_matrices(16.0 / 9.0);

        // Matrices should not be identity after update.
        assert_ne!(camera.view_matrix(), Mat4::IDENTITY);
        assert_ne!(camera.projection_matrix(), Mat4::IDENTITY);
    }

    #[test]
    fn lagoon_mode_has_no_anchor() {
        let cam = IsometricCamera::new(Vec3::ZERO, 10.0, 5.0);
        assert!(cam.anchor.is_none(), "flat Cartesian camera must have no anchor");
    }

    #[test]
    fn geodetic_anchor_constructor() {
        use crate::render::geodesy::{NEW_PROVIDENCE_LAT_DEG, NEW_PROVIDENCE_LON_DEG, NEW_PROVIDENCE_ALT_M};
        let cam = IsometricCamera::with_geodetic_anchor(
            NEW_PROVIDENCE_LAT_DEG, NEW_PROVIDENCE_LON_DEG, NEW_PROVIDENCE_ALT_M,
            10.0, 5.0,
        );
        assert!(cam.anchor.is_some(), "geodetic camera must carry an anchor");
        let a = cam.anchor.unwrap();
        assert!((a.lat_deg - NEW_PROVIDENCE_LAT_DEG).abs() < 1e-9);
        assert!((a.lon_deg - NEW_PROVIDENCE_LON_DEG).abs() < 1e-9);
    }

    #[test]
    fn project_ecef_anchor_origin_is_zero() {
        use crate::render::geodesy::{NEW_PROVIDENCE_LAT_DEG, NEW_PROVIDENCE_LON_DEG, NEW_PROVIDENCE_ALT_M, lla_to_ecef};
        let cam = IsometricCamera::with_geodetic_anchor(
            NEW_PROVIDENCE_LAT_DEG, NEW_PROVIDENCE_LON_DEG, NEW_PROVIDENCE_ALT_M,
            10.0, 5.0,
        );
        // Projecting the anchor's own ECEF position must yield render-space (0,0,0).
        let origin_ecef = lla_to_ecef(NEW_PROVIDENCE_LAT_DEG, NEW_PROVIDENCE_LON_DEG, NEW_PROVIDENCE_ALT_M);
        let render = cam.project_ecef_to_render(origin_ecef);
        assert!(render.length() < 1e-3, "anchor ECEF → render must be zero: {render:?}");
    }

    #[test]
    fn project_ecef_lagoon_passthrough() {
        let cam = IsometricCamera::new(Vec3::ZERO, 10.0, 5.0);
        use glam::DVec3;
        let ecef = DVec3::new(1000.0, 2000.0, 3000.0);
        let render = cam.project_ecef_to_render(ecef);
        assert_eq!(render, Vec3::new(1000.0, 2000.0, 3000.0));
    }
}
