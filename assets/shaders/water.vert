// Rung 5 + Rung 4.2d — shallow-water hero shader (vertex stage).
//   mode 0 (seabed):   pass-through of the bathymetry vertex.
//   mode 1 (surface):  displacement from TWO Tessendorf cascades summed here.
//                      binding 0 = C0 (ripple/chop, patch=5m)
//                      binding 1 = C1 (swell, patch=60m)
//                      Displacement fields are summed in world-space before normal derivation.
//   mode 2 (celestial): pass-through camera-facing discs generated from topocentric alt/az.
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

// Cascade 0 (ripple/chop, patch=5m) and Cascade 1 (swell, patch=60m).
// rgba16f per cascade: .xyz = world-space displacement (choppy x/z + height y).
layout(set = 0, binding = 0) uniform sampler2D u_displacement_c0;
layout(set = 0, binding = 1) uniform sampler2D u_displacement_c1;

// Rung 2.5 (RT reflections): camera_pos_and_lens_flag appended at the END of the Rust
// FrameUniform (renderer.rs) so shared byte offsets elsewhere (cloud/atmosphere shaders)
// stay untouched — its true offset (224) is given explicitly since this block skips the
// atmosphere/weather fields in between. Not yet read here — future RT ray-gen shader.
layout(set = 1, binding = 0, std140) uniform FrameData {
    mat4 current_motion_view_projection;
    mat4 previous_motion_view_projection;
    vec4 sst_data;
    layout(offset = 224) vec4 camera_pos_and_lens_flag;
} u_frame;

// ENU-local metres (must match ocean.rs X_HALF/Z_HALF). Site 2+3 — Ellipsoid retrofit.
// ELLIPSOID-RETROFIT: push via UBO when camera panning is live (Site 6).
const float X_HALF = 200000.0; // 200 km East half-extent
const float Z_HALF = 200000.0; // 200 km North half-extent

// Cascade patch sizes (must match ocean_compute.rs DEFAULT_CASCADES): the small
// FFT tile each cascade simulates should REPEAT every patch_size metres across
// the world, not stretch once across the full 200km domain (checkerboard
// artifact fix, 2026-07-06 — see uv_c0/uv_c1 below).
const float PATCH_C0 = 5.0;  // ripple/chop
const float PATCH_C1 = 60.0; // swell

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
        // Per-cascade tiling UV: the sampler is REPEAT-wrapped (ocean_compute.rs),
        // so dividing world position by each cascade's OWN patch_size (not the
        // 200km world half-extent) makes the small FFT tile repeat across the
        // world at its intended physical scale, instead of one texture stretched
        // once over the whole domain — that stretch was the checkerboard
        // artifact: with no tiling, the raw 256x256 texture's own low-frequency
        // structure was directly visible, magnified ~40,000x for C0 alone.
        // No border margin/clamp needed — REPEAT wrap handles the seam.
        vec2 uv_c0 = in_position.xz / PATCH_C0;
        vec2 uv_c1 = in_position.xz / PATCH_C1;

        // Sum displacement from both cascades.
        vec3 disp = texture(u_displacement_c0, uv_c0).xyz
                  + texture(u_displacement_c1, uv_c1).xyz;

        pos = in_position + disp;

        // Finite-difference normal — sum height gradients from both cascades.
        // texel is the same 1/256 step in EACH cascade's own uv space (uv_cN is
        // already scaled by 1/patch_size, so one texel there is patch_size/256
        // world metres regardless of which cascade).
        float texel = 1.0 / 256.0;
        float dx = (texture(u_displacement_c0, uv_c0 + vec2(texel, 0.0)).y
                  + texture(u_displacement_c1, uv_c1 + vec2(texel, 0.0)).y)
                 - (texture(u_displacement_c0, uv_c0 - vec2(texel, 0.0)).y
                  + texture(u_displacement_c1, uv_c1 - vec2(texel, 0.0)).y);
        float dz = (texture(u_displacement_c0, uv_c0 + vec2(0.0, texel)).y
                  + texture(u_displacement_c1, uv_c1 + vec2(0.0, texel)).y)
                 - (texture(u_displacement_c0, uv_c0 - vec2(0.0, texel)).y
                  + texture(u_displacement_c1, uv_c1 - vec2(0.0, texel)).y);
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
    v_clip      = u_frame.current_motion_view_projection * world;
    v_prev_clip = u_frame.previous_motion_view_projection * prev_world;
}
