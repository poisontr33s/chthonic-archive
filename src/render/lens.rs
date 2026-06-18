//! The view-set — compounding lenses (§2.7), not one chosen camera.

//! @SID:    RENDER_LENS_V1
//! @Shabti: Lens

//! "As above, so below." A real view abstraction so further lenses slot in without rework, and
//! selection is **explicit** (env `CHTHONIC_LENS`), never an auto-cycle or hidden mode (the 03A
//! correction). The isometric camera ([`super::camera::IsometricCamera`]) stays first-class — the
//! *so-below* lens that reads the Banks' depth honestly. This adds the *perspective* lens — the
//! view from a plane, with the horizon and recession the ortho lens cannot show — and it is the
//! path the celestial *as-above* up-look will follow, slotting into the same abstraction.

use super::camera::IsometricCamera;
use glam::{Mat4, Vec3};

/// An active lens. Lenses compound; none is a debug afterthought, and the renderer never cycles
/// them on its own — the human (or a future control) selects.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Default)]
pub enum Lens {
    /// So-below: the c-RPG orthographic view — the clearest read of what the depth is doing.
    #[default]
    Isometric,
    /// The view from a plane: true FOV, horizon, recession — toward the as-above/so-below frame.
    Perspective,
}

impl Lens {
    /// Select the lens explicitly from the environment (default: isometric). Not an auto-cycle.
    pub fn from_env() -> Self {
        match std::env::var("CHTHONIC_LENS").ok().as_deref() {
            Some("perspective") | Some("as-above-so-below") => Lens::Perspective,
            _ => Lens::Isometric,
        }
    }

    pub fn label(self) -> &'static str {
        match self {
            Lens::Isometric => "isometric (so-below)",
            Lens::Perspective => "perspective (as-above/so-below)",
        }
    }
}

/// View + projection for the active lens. The isometric lens delegates to the existing camera,
/// unchanged. The perspective lens shares the camera's vantage (eye + target) but with a true-FOV
/// projection — same place to stand, a different way of seeing — so it compounds with the iso lens
/// rather than competing with it.
pub fn matrices(lens: Lens, camera: &IsometricCamera, aspect: f32) -> (Mat4, Mat4) {
    match lens {
        Lens::Isometric => (camera.view_matrix(), camera.projection_matrix()),
        Lens::Perspective => {
            let view = Mat4::look_at_rh(camera.position, camera.target, Vec3::Y);
            let proj = Mat4::perspective_rh(45.0_f32.to_radians(), aspect.max(0.01), 0.1, 1000.0);
            (view, proj)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn default_lens_is_isometric() {
        assert_eq!(Lens::default(), Lens::Isometric);
    }

    #[test]
    fn isometric_delegates_perspective_diverges() {
        let mut cam = IsometricCamera::new(Vec3::ZERO, 10.0, 5.0);
        cam.update_matrices(16.0 / 9.0);

        let (iso_view, iso_proj) = matrices(Lens::Isometric, &cam, 16.0 / 9.0);
        assert_eq!(iso_view, cam.view_matrix(), "iso lens must delegate to the camera");
        assert_eq!(iso_proj, cam.projection_matrix());

        let (_pv, persp_proj) = matrices(Lens::Perspective, &cam, 16.0 / 9.0);
        assert_ne!(persp_proj, iso_proj, "perspective projection must differ from orthographic");
    }
}
