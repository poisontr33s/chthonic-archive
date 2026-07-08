// TAA resolve — fragment stage (Gate 3).
//
// Reads:
//   set 0 binding 0 — u_current     : current frame, offscreen colour (swapchain format)
//   set 0 binding 1 — u_history     : previous stable frame, ping-pong (R16G16B16A16_SFLOAT)
//   set 0 binding 2 — u_motion      : per-pixel motion vectors (RG16F, xy = NDC delta)
//
// Algorithm (in order):
//   1. Sample current colour at v_uv.
//   2. Read motion vector, reproject to history UV.
//   3. Sample history at reprojected UV.
//   4. Neighbourhood-clamp history to the 3×3 AABB of the current frame's neighbours
//      (kills ghosting from disoccluded pixels).
//   5. Blend: out = mix(history_clamped, current, adaptive_blend), where adaptive_blend
//      biases toward the current frame as pc.camera_motion grows (Track A1, attempt 2).
//      pc.blend (typically 0.1) is the floor used when the camera is static.
//   6. CHTHONIC_TAA_DEBUG push constant word flips to motion-vector visualisation.
//
// Output:
//   layout 0 — final colour for the swapchain image.
#version 450
#extension GL_ARB_separate_shader_objects : enable

layout(location = 0) in  vec2 v_uv;
layout(location = 0) out vec4 out_color;

layout(set = 0, binding = 0) uniform sampler2D u_current;
layout(set = 0, binding = 1) uniform sampler2D u_history;
layout(set = 0, binding = 2) uniform sampler2D u_motion;

layout(push_constant) uniform TaaParams {
    vec2  texel_size;     // 1.0 / vec2(width, height) — baked in at record time
    float blend;          // typically 0.1  (new) / 0.9 (history) — static-camera floor
    float debug;          // 1.0 = show motion vectors as colour, 0.0 = normal resolve
    float camera_motion;  // NDC-space (UV-scaled) delta of the camera's own target point
                          // between this frame and last — see renderer.rs, computed
                          // CPU-side from temporal_frame's two view-projections applied to
                          // the same world point, so it cannot be tripped by Tessendorf
                          // wave-crest animation the way the per-pixel `motion` vector can.
} pc;

// Camera-motion magnitude (in pixel-equivalents) at which the blend fully favours the
// current frame. Distinct from the reverted attempt's MOTION_ADAPT_PIXELS: that threshold
// gated on the combined per-pixel `motion` vector (camera + wave, indistinguishable) and
// tripped on ordinary wave-crest motion. This one gates on pc.camera_motion, which is
// exactly zero for a static camera regardless of how fast the water is animating.
const float CAMERA_MOTION_ADAPT_PIXELS = 8.0;

// 3×3 neighbourhood AABB clamp — keeps history inside the plausible range of the current
// frame's local neighbourhood, preventing ghosting on moving/disoccluded edges.
vec3 neighbourhood_clamp(sampler2D tex, vec2 uv, vec2 texel, vec3 history) {
    vec3 lo = history;
    vec3 hi = history;
    for (int dy = -1; dy <= 1; dy++) {
        for (int dx = -1; dx <= 1; dx++) {
            vec3 s = texture(tex, uv + vec2(float(dx), float(dy)) * texel).rgb;
            lo = min(lo, s);
            hi = max(hi, s);
        }
    }
    return clamp(history, lo, hi);
}

void main() {
    vec2 motion   = texture(u_motion, v_uv).rg;

    // Debug: paint motion vectors as colour and skip resolve.
    if (pc.debug > 0.5) {
        out_color = vec4(abs(motion) * 10.0, 0.0, 1.0);
        return;
    }

    vec2 hist_uv  = v_uv - motion;                          // reproject into history UV
    vec3 current  = texture(u_current, v_uv).rgb;
    vec3 history  = texture(u_history, hist_uv).rgb;

    // Clamp history before blend to eliminate ghosts.
    history = neighbourhood_clamp(u_current, v_uv, pc.texel_size, history);

    // Motion-adaptive temporal blend: pc.blend (0.9 history / 0.1 current) is the static
    // floor; as the camera's own motion grows, bias toward trusting only the current frame,
    // since a long temporal memory window is exactly what turns real per-frame reprojection
    // error into an ever-growing streak under sustained pan (see
    // reference_taa_ghosting_investigation's sustained-motion harness findings).
    float camera_motion_px = pc.camera_motion / pc.texel_size.x;
    float adapt            = clamp(camera_motion_px / CAMERA_MOTION_ADAPT_PIXELS, 0.0, 1.0);
    float adaptive_blend   = mix(pc.blend, 1.0, adapt);

    vec3 resolved = mix(history, current, adaptive_blend);
    out_color     = vec4(resolved, 1.0);
}
