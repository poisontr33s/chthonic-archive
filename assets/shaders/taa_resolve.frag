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
//   5. Blend: out = mix(history_clamped, current, BLEND_WEIGHT).
//      BLEND_WEIGHT 0.1 → strong temporal accumulation, low noise.
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
    vec2  texel_size;   // 1.0 / vec2(width, height) — baked in at record time
    float blend;        // typically 0.1  (new) / 0.9 (history)
    float debug;        // 1.0 = show motion vectors as colour, 0.0 = normal resolve
} pc;

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

    // Temporal blend — 0.9 history, 0.1 current by default.
    vec3 resolved = mix(history, current, pc.blend);
    out_color     = vec4(resolved, 1.0);
}
