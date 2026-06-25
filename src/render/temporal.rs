//! Rung 2.4 temporal authority: one Halton jitter source and one motion-vector
//! convention for every temporal pass that follows.

//! @SID:    RENDER_TEMPORAL_V1
//! @Shabti: Temporal

use ash::vk;
use glam::{Mat4, Vec2};

/// Per-frame temporal inputs consumed by the current graphics pass.
pub struct TemporalFrame {
    /// Projection with the current frame's sub-pixel jitter baked into clip space.
    pub projection: Mat4,
    /// Current unjittered view-projection, used only for motion-vector generation.
    pub current_view_projection: Mat4,
    /// Previous unjittered view-projection, used only for motion-vector generation.
    pub previous_view_projection: Mat4,
    /// Current-to-previous screen-space motion caused by the shared jitter source.
    pub motion_vector_ndc: Vec2,
    /// Sub-pixel jitter in pixel space, range [-0.5, 0.5] on each axis.
    /// Used by Streamline's sl::Constants::jitterOffset (pixel-space, not NDC).
    pub jitter_pixel: Vec2,
}

/// Single temporal clock for the renderer.
pub struct TemporalState {
    frame_index: u64,
    previous_jitter_ndc: Vec2,
    previous_view_projection: Mat4,
}

impl TemporalState {
    /// Start the temporal authority with the first unjittered view-projection.
    pub fn new(initial_view_projection: Mat4) -> Self {
        Self {
            frame_index: 0,
            previous_jitter_ndc: Vec2::ZERO,
            previous_view_projection: initial_view_projection,
        }
    }

    /// Advance the shared temporal clock for one rendered frame.
    pub fn begin_frame(
        &mut self,
        extent: vk::Extent2D,
        view: Mat4,
        projection: Mat4,
    ) -> TemporalFrame {
        let sample = self.frame_index + 1;
        let jitter_pixel = Vec2::new(halton(sample, 2) - 0.5, halton(sample, 3) - 0.5);
        let jitter_ndc = if extent.width > 0 && extent.height > 0 {
            Vec2::new(
                2.0 * jitter_pixel.x / extent.width as f32,
                2.0 * jitter_pixel.y / extent.height as f32,
            )
        } else {
            Vec2::ZERO
        };
        let current_view_projection = projection * view;
        let previous_view_projection = self.previous_view_projection;
        let jittered_projection = jitter_projection(projection, jitter_ndc);

        let motion_vector_ndc = self.previous_jitter_ndc - jitter_ndc;
        self.previous_jitter_ndc = jitter_ndc;
        self.previous_view_projection = current_view_projection;
        self.frame_index += 1;

        TemporalFrame {
            projection: jittered_projection,
            current_view_projection,
            previous_view_projection,
            motion_vector_ndc,
            jitter_pixel,
        }
    }

    /// Previous unjittered view-projection retained for motion-vector generation.
    #[inline]
    #[allow(dead_code)]
    pub fn previous_view_projection(&self) -> Mat4 {
        self.previous_view_projection
    }
}

fn halton(mut index: u64, base: u64) -> f32 {
    debug_assert!(base > 1);

    let mut fraction = 1.0_f32;
    let mut result = 0.0_f32;

    while index > 0 {
        fraction /= base as f32;
        result += fraction * (index % base) as f32;
        index /= base;
    }

    result
}

/// Apply clip-space jitter by adding `jitter * clip.w` to clip x/y.
pub fn jitter_projection(projection: Mat4, jitter_ndc: Vec2) -> Mat4 {
    let mut cols = projection.to_cols_array_2d();
    for col in &mut cols {
        col[0] += jitter_ndc.x * col[3];
        col[1] += jitter_ndc.y * col[3];
    }
    Mat4::from_cols_array_2d(&cols)
}

#[cfg(test)]
mod tests {
    use super::*;
    use glam::{Vec3, Vec4};

    fn near(a: f32, b: f32) -> bool {
        (a - b).abs() <= 1.0e-6
    }

    #[test]
    fn halton_starts_with_expected_bases() {
        assert!(near(halton(1, 2), 0.5));
        assert!(near(halton(2, 2), 0.25));
        assert!(near(halton(3, 2), 0.75));
        assert!(near(halton(1, 3), 1.0 / 3.0));
        assert!(near(halton(2, 3), 2.0 / 3.0));
    }

    #[test]
    fn jitter_projection_offsets_clip_by_clip_w() {
        let jitter = Vec2::new(0.25, -0.125);
        let projection = jitter_projection(Mat4::IDENTITY, jitter);
        let clip = projection * Vec4::new(0.10, 0.20, 0.30, 1.0);

        assert!(near(clip.x, 0.35));
        assert!(near(clip.y, 0.075));
        assert!(near(clip.z, 0.30));
        assert!(near(clip.w, 1.0));
    }

    #[test]
    fn begin_frame_advances_one_jitter_clock() {
        let mut temporal = TemporalState::new(Mat4::IDENTITY);
        let extent = vk::Extent2D {
            width: 100,
            height: 100,
        };

        let first_view = Mat4::from_translation(Vec3::new(1.0, 2.0, 3.0));
        let second_view = Mat4::from_translation(Vec3::new(2.0, 2.0, 3.0));
        let first = temporal.begin_frame(extent, first_view, Mat4::IDENTITY);
        let second = temporal.begin_frame(extent, second_view, Mat4::IDENTITY);

        assert_ne!(first.projection, second.projection);
        assert_ne!(first.motion_vector_ndc, second.motion_vector_ndc);
        assert_eq!(first.previous_view_projection, Mat4::IDENTITY);
        assert_eq!(first.current_view_projection, first_view);
        assert_eq!(
            second.previous_view_projection,
            first.current_view_projection
        );
        assert_eq!(
            temporal.previous_view_projection(),
            second.current_view_projection
        );
    }
}
