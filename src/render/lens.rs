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

/// The as-above/so-below eye: stand on the Banks, just above the water. The eye sits well inside
/// the sky-dome (radius ~4.15), which is correct — from the ground you never see the whole
/// hemisphere at once. The eye does **not** move; only the heading (where you look) is free. Tuned
/// against the render-smoke PNG.
const HORIZON_EYE: Vec3 = Vec3::new(0.0, 0.45, 2.6);
/// How far ahead the look-at target sits along the heading. Only the *direction* matters to
/// `look_at_rh`; any positive distance yields the same view.
const LOOK_DISTANCE: f32 = 4.0;
/// Vertical field of view (degrees) for the perspective lens.
const PERSPECTIVE_FOV_DEG: f32 = 55.0;

/// Where the orientable (perspective) lens points: a compass **azimuth** and an **up-tilt**
/// (altitude), in degrees, in the *same* alt/az frame the celestial bodies use — so "look toward
/// az/alt" points the eye exactly at whatever body sits there. This is the rung's freedom: the sky
/// is forced (verified positions) and the eye is fixed, but *where you look* is yours. Turn the
/// head; never move the heavens.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Heading {
    pub az_deg: f32,
    pub alt_deg: f32,
}

impl Default for Heading {
    /// Reproduces the original horizon look: due south (az 180°), tilted ~11.7° up.
    fn default() -> Self {
        Self { az_deg: 180.0, alt_deg: 11.7 }
    }
}

impl Heading {
    /// Read the heading explicitly from the environment (degrees), falling back to the default
    /// horizon look. Not an auto-pan — the human (or a future control) chooses where to look.
    pub fn from_env() -> Self {
        let d = Heading::default();
        Heading {
            az_deg: env_deg("CHTHONIC_LOOK_AZ", d.az_deg),
            alt_deg: env_deg("CHTHONIC_LOOK_ALT", d.alt_deg),
        }
    }

    /// The unit world direction the eye looks along — via the **one** alt/az→world map the whole
    /// engine shares ([`super::cosmos::altaz_to_world_direction`]), so the lens and the bodies agree
    /// on what "az/alt" means and aiming at a sign actually points at that sign.
    pub fn direction(self) -> Vec3 {
        let d = super::cosmos::altaz_to_world_direction(self.alt_deg as f64, self.az_deg as f64);
        Vec3::new(d[0], d[1], d[2])
    }
}

fn env_deg(key: &str, fallback: f32) -> f32 {
    std::env::var(key).ok().and_then(|v| v.parse().ok()).unwrap_or(fallback)
}

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

    /// Where the lens stands and what it looks at — `(eye, target)`. The isometric lens reproduces
    /// the camera's own vantage exactly (so its render is byte-identical to before the lens-set
    /// existed). The perspective lens leaves the iso vantage behind: it stands low on the Banks and
    /// looks toward the horizon, the true *as-above/so-below* frame. This is the single source of
    /// the vantage — both [`matrices`] and the celestial-field disc-facing read it, so the sky is
    /// built facing whichever eye is actually looking.
    /// The perspective eye is fixed at [`HORIZON_EYE`]; the `heading` only turns where it looks
    /// (the sky never moves).
    pub fn vantage(self, camera: &IsometricCamera, heading: Heading) -> (Vec3, Vec3) {
        match self {
            Lens::Isometric => (camera.position, camera.target),
            Lens::Perspective => {
                let dir = heading.direction().normalize_or_zero();
                (HORIZON_EYE, HORIZON_EYE + dir * LOOK_DISTANCE)
            }
        }
    }
}

/// View + projection for the active lens. The isometric lens delegates to the existing camera,
/// unchanged. The perspective lens stands at its own [`Lens::vantage`] — low on the Banks looking
/// at the horizon — with a true-FOV projection, so it compounds with the iso lens rather than
/// competing with it.
pub fn matrices(lens: Lens, camera: &IsometricCamera, heading: Heading, aspect: f32) -> (Mat4, Mat4) {
    match lens {
        Lens::Isometric => (camera.view_matrix(), camera.projection_matrix()),
        Lens::Perspective => {
            let (eye, target) = lens.vantage(camera, heading);
            let view = Mat4::look_at_rh(eye, target, Vec3::Y);
            let mut proj = Mat4::perspective_rh(
                PERSPECTIVE_FOV_DEG.to_radians(),
                aspect.max(0.01),
                0.1,
                1000.0,
            );
            // Vulkan clip-space has Y pointing down; the viewport is positive-height and the
            // pipeline already expects the flipped convention (front-face = clockwise). glam's
            // `perspective_rh` is Y-up, so without this the horizon view renders upside-down
            // (sky below, Banks above). The iso ortho path is left untouched — verified and
            // byte-identical — so this correction lives only on the perspective lens.
            proj.y_axis.y *= -1.0;
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

        let (iso_view, iso_proj) = matrices(Lens::Isometric, &cam, Heading::default(), 16.0 / 9.0);
        assert_eq!(iso_view, cam.view_matrix(), "iso lens must delegate to the camera");
        assert_eq!(iso_proj, cam.projection_matrix());

        let (_pv, persp_proj) = matrices(Lens::Perspective, &cam, Heading::default(), 16.0 / 9.0);
        assert_ne!(persp_proj, iso_proj, "perspective projection must differ from orthographic");
    }

    #[test]
    fn iso_vantage_is_the_camera_perspective_stands_apart() {
        let cam = IsometricCamera::new(Vec3::ZERO, 10.0, 5.0);

        let (iso_eye, iso_target) = Lens::Isometric.vantage(&cam, Heading::default());
        assert_eq!(iso_eye, cam.position, "iso vantage must be the camera's own eye");
        assert_eq!(iso_target, cam.target);

        let (persp_eye, persp_target) = Lens::Perspective.vantage(&cam, Heading::default());
        assert_ne!(persp_eye, iso_eye, "perspective must leave the iso eye");
        // The horizon eye stands low and looks *up* toward the sky-dome.
        assert!(persp_target.y > persp_eye.y, "perspective look must tilt upward");
    }

    #[test]
    fn default_heading_looks_south_and_up() {
        // The default reproduces the original horizon look: southward, tilted up.
        let d = Heading::default().direction();
        assert!(d.z < 0.0, "default look is southward (-Z)");
        assert!(d.y > 0.0, "default look tilts up");
    }

    #[test]
    fn heading_aims_by_the_same_altaz_as_the_bodies() {
        // The lens and the celestial bodies must agree on what "az/alt" means, or "look at the
        // zodiac" would not point at the zodiac.
        let h = Heading { az_deg: 123.0, alt_deg: 34.0 };
        let d = super::super::cosmos::altaz_to_world_direction(34.0, 123.0);
        let v = h.direction();
        assert!((v.x - d[0]).abs() < 1e-6, "x must match the shared alt/az map");
        assert!((v.y - d[1]).abs() < 1e-6, "y must match the shared alt/az map");
        assert!((v.z - d[2]).abs() < 1e-6, "z must match the shared alt/az map");
    }

    #[test]
    fn heading_turns_the_look_without_moving_the_eye() {
        // The rung's contract: turning the head changes where you look, never where you stand —
        // the heavens do not move.
        let cam = IsometricCamera::new(Vec3::ZERO, 10.0, 5.0);
        let (eye_a, target_a) =
            Lens::Perspective.vantage(&cam, Heading { az_deg: 90.0, alt_deg: 10.0 });
        let (eye_b, target_b) =
            Lens::Perspective.vantage(&cam, Heading { az_deg: 270.0, alt_deg: 10.0 });
        assert_eq!(eye_a, eye_b, "turning the heading must not move the eye (the sky does not move)");
        assert_ne!(target_a, target_b, "a different heading must look somewhere else");
    }
}
