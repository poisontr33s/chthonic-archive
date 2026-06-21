// Rung 5 + Rung 4 — shallow-water hero shader (vertex stage).
//   mode 0 (seabed):   pass-through of the bathymetry vertex.
//   mode 1 (surface):  displacement sampled from the compute image (ocean_displace.comp) +
//                      analytic wave normal from the same field. The compute body is currently
//                      Gerstner (4.2a); it becomes Tessendorf FFT (4.2b/c) without changing
//                      this vertex stage — the image contract (xyz disp, w height) is stable.
//   mode 2 (celestial): pass-through camera-facing discs generated from topocentric alt/az.
// The 4th/5th push-constant vec4s carry the solar vector and [time, mode, dt, motion-debug].
#version 450
#extension GL_ARB_separate_shader_objects : enable

layout(location = 0) in vec3 in_position;
layout(location = 1) in vec3 in_normal;
layout(location = 2) in vec3 in_color;

layout(push_constant) uniform PushConstants {
    mat4 model;
    mat4 view;
    mat4 projection;
    vec4 sun;      // xyz = direction TO the sun, w = intensity
    vec4 params;   // x = time, y = mode, z = frame dt, w = motion-debug toggle
} pc;

// Displacement image written each frame by ocean_displace.comp (set 0, binding 0).
// rgba16f: .xyz = world-space displacement (choppy x/z + height y), .w = height.
layout(set = 0, binding = 0) uniform sampler2D u_displacement;

// World half-extents of the surface grid (must match ocean.rs surface_grid and ocean_compute.rs).
const float X_HALF = 2.45;
const float Z_HALF = 0.92;

layout(location = 0) out vec3 v_world_pos;
layout(location = 1) out vec3 v_normal;
layout(location = 2) out vec3 v_floor_albedo;
layout(location = 3) out vec4 v_clip;       // current clip position
layout(location = 4) out vec4 v_prev_clip;  // previous-frame clip position (for motion vectors)

void main() {
    vec3 pos = in_position;
    vec3 nrm = in_normal;
    vec3 prev_pos = in_position;

    if (pc.params.y > 0.5 && pc.params.y < 1.5) {
        // Map vertex XZ → [0,1] UV over the surface grid domain.
        // Clamp 1.5 texels inward from each edge so the finite-difference normal never
        // samples across the displacement image border (prevents boundary spires).
        const float MARGIN = 1.5 / 256.0;
        vec2 uv = clamp(
            (in_position.xz / vec2(X_HALF, Z_HALF)) * 0.5 + 0.5,
            vec2(MARGIN), vec2(1.0 - MARGIN)
        );

        // Sample the compute-written displacement field.
        vec4 disp4 = texture(u_displacement, uv);
        vec3 disp  = disp4.xyz;

        pos = in_position + disp;

        // Finite-difference normal from neighbouring texels (one texel = 1/resolution of domain).
        float texel = 1.0 / 256.0;
        float dx = texture(u_displacement, uv + vec2(texel, 0.0)).y
                 - texture(u_displacement, uv - vec2(texel, 0.0)).y;
        float dz = texture(u_displacement, uv + vec2(0.0, texel)).y
                 - texture(u_displacement, uv - vec2(0.0, texel)).y;
        nrm = normalize(vec3(-dx, 2.0 * texel, -dz));

        // Previous-frame position: sample the same field with time-offset params.
        // The compute image is current-frame only; use the analytic dt-offset approximation
        // (sample at uv — good enough for DLAA jitter vectors, revisit for full TAA history).
        prev_pos = pos; // conservative: zero motion vector on ocean surface for now
    }

    vec4 world      = pc.model * vec4(pos, 1.0);
    vec4 prev_world = pc.model * vec4(prev_pos, 1.0);
    gl_Position = pc.projection * pc.view * world;

    v_world_pos    = world.xyz;
    v_normal       = normalize(mat3(pc.model) * nrm);
    v_floor_albedo = in_color;
    v_clip      = gl_Position;
    v_prev_clip = pc.projection * pc.view * prev_world;
}
