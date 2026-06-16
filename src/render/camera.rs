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

use glam::{Mat4, Vec3};
use log::info;

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
    #[allow(dead_code)]
    pub fn set_target(&mut self, target: Vec3, aspect_ratio: f32) {
        let offset = self.position - self.target;
        self.target = target;
        self.position = target + offset;
        self.update_matrices(aspect_ratio);
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
}
