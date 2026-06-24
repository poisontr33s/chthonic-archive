// Rung 5 + Rung 4 — shallow-water hero shader (fragment stage). Two modes via params.y:
//   mode 1 (surface): the Rung-4 ocean surface — Fresnel sky-tint + sun glint on the
//                     Gerstner wave normal, translucent so it blends over the seabed.
//   mode 0 (seabed):  the Volumetric Optical Pipeline — depth reconstruction + per-channel
//                     Beer–Lambert (turquoise from white sand) + in-scatter (deep → navy).
//   mode 2 (celestial): unlit Sun/Moon/planet discs in the real topocentric sky.
#version 450
#extension GL_ARB_separate_shader_objects : enable

layout(location = 0) in vec3 v_world_pos;
layout(location = 1) in vec3 v_normal;
layout(location = 2) in vec3 v_floor_albedo;

layout(push_constant) uniform PushConstants {
    mat4 model;
    mat4 view;
    mat4 projection;
    vec4 sun;      // xyz = direction TO the sun, w = intensity
    vec4 params;   // x = time, y = mode, z = frame dt, w = motion-debug toggle
} pc;

// set=0 is the ocean displacement sampler (water.vert, bindings 0+1).
// SST UBO lives at set=1 to avoid collision.
// vec4 layout: xyz = sst_tint, w = sst_blend — avoids vec3 std140 padding ambiguity.
layout(set = 1, binding = 0) uniform WaterSST {
    vec4 sst_data;  // xyz = SST-adjusted warm tint, w = blend scalar [0..1]
} u_sst;

layout(location = 3) in vec4 v_clip;       // current clip position
layout(location = 4) in vec4 v_prev_clip;  // previous-frame clip position

layout(location = 0) out vec4 out_color;
layout(location = 1) out vec2 out_motion;

const float Y_SCALE = 0.0004;                   // must match bathymetry.rs
const vec3  SIGMA   = vec3(0.16, 0.035, 0.016); // per-metre extinction R,G,B (clear tropical water)
const vec3  SAND    = vec3(0.90, 0.82, 0.62);   // bright carbonate sand floor
const vec3  WATER   = vec3(0.015, 0.10, 0.17);  // deep-water in-scatter colour

void main() {
    // True per-pixel motion vector: current → previous in UV space. Both clip positions came
    // through the same (current) view-projection, so the sub-pixel jitter cancels in the
    // difference and the static seabed/celestial geometry resolves to exactly zero.
    vec2 curr_uv = (v_clip.xy / v_clip.w) * 0.5 + 0.5;
    vec2 prev_uv = (v_prev_clip.xy / v_prev_clip.w) * 0.5 + 0.5;
    vec2 motion  = prev_uv - curr_uv;
    out_motion = motion;

    // Motion-buffer debug view (CHTHONIC_SHOW_MOTION): mid-grey = still, R/G encode motion
    // direction. The gain is large because per-frame wave motion is sub-pixel at this zoom.
    if (pc.params.w > 0.5) {
        const float gain = 12000.0;
        out_color = vec4(0.5 + motion.x * gain, 0.5 + motion.y * gain, 0.5, 1.0);
        return;
    }

    vec3  N = normalize(v_normal);
    vec3  L = normalize(pc.sun.xyz);
    float I = pc.sun.w;
    vec3  V = normalize(vec3(1.0, 1.0, 1.0)); // iso camera approx (toward viewer)
    vec3  H = normalize(L + V);

    // === Rung 6.2: celestial field ===
    if (pc.params.y > 1.5) {
        out_color = vec4(v_floor_albedo, 1.0);
        return;
    }

    // === Rung 4: ocean surface ===
    if (pc.params.y > 0.5) {
        float fres  = 0.02 + 0.98 * pow(1.0 - max(dot(N, V), 0.0), 5.0);
        vec3  sky   = vec3(0.35, 0.55, 0.72);
        float glint = pow(max(dot(N, H), 0.0), 200.0) * I;
        vec3  tint  = mix(vec3(0.08, 0.34, 0.42), u_sst.sst_data.xyz, u_sst.sst_data.w);
        vec3  col   = mix(tint, sky, fres) + vec3(glint);
        out_color   = vec4(col, 0.30); // translucent — lets the seabed turquoise read through
        return;
    }

    // === Rung 5: seabed volumetric optics ===
    float depth_m = max(0.0, -v_world_pos.y / Y_SCALE);
    float lambert = 0.30 + 0.70 * max(dot(N, L), 0.0);

    if (depth_m <= 0.0) {
        out_color = vec4(v_floor_albedo * lambert * I, 1.0); // exposed cay
        return;
    }

    vec3  trans      = exp(-SIGMA * depth_m * 2.0);
    vec3  floor_light = SAND * lambert * I * trans;
    float floor_vis  = dot(trans, vec3(0.299, 0.587, 0.114));
    vec3  water_glow = WATER * I * (1.0 - floor_vis);
    vec3  body       = floor_light + water_glow;

    float fres  = 0.02 + 0.30 * pow(1.0 - max(dot(N, V), 0.0), 5.0);
    vec3  sky   = vec3(0.30, 0.50, 0.68);
    float glint = pow(max(dot(N, H), 0.0), 80.0) * I;

    out_color = vec4(mix(body, sky, fres) + vec3(glint), 1.0);
}
