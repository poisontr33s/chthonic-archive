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
    vec4 params;   // x = time, y = mode, zw = current-to-previous motion vector
} pc;

layout(location = 0) out vec4 out_color;
layout(location = 1) out vec2 out_motion;

const float Y_SCALE = 0.0004;                   // must match bathymetry.rs
const vec3  SIGMA   = vec3(0.16, 0.035, 0.016); // per-metre extinction R,G,B (clear tropical water)
const vec3  SAND    = vec3(0.90, 0.82, 0.62);   // bright carbonate sand floor
const vec3  WATER   = vec3(0.015, 0.10, 0.17);  // deep-water in-scatter colour

void main() {
    out_motion = pc.params.zw;

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
        vec3  tint  = vec3(0.08, 0.34, 0.42);
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
