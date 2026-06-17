// Rung 5 + Rung 4 — shallow-water hero shader (vertex stage).
//   mode 0 (seabed):  pass-through of the bathymetry vertex.
//   mode 1 (surface): Gerstner-wave displacement + analytic wave normal (the Rung-4 ocean).
//   mode 2 (celestial): pass-through camera-facing discs generated from topocentric alt/az.
// The 4th/5th push-constant vec4s carry the solar vector and [time, mode, motion.xy].
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

layout(location = 0) out vec3 v_world_pos;
layout(location = 1) out vec3 v_normal;
layout(location = 2) out vec3 v_floor_albedo;
layout(location = 3) out vec4 v_clip;       // current clip position
layout(location = 4) out vec4 v_prev_clip;  // previous-frame clip position (for motion vectors)

// Accumulate one directional Gerstner wave into position P and normal-basis (Nacc, ny).
void gerstner(vec2 dir, float amp, float wavelen, float steep, float speed,
              vec2 p0, float t, inout vec3 P, inout vec3 Nacc, inout float ny) {
    vec2  D = normalize(dir);
    float k = 6.2831853 / wavelen;   // spatial frequency
    float wa = k * amp;
    float ph = k * dot(D, p0) + speed * t;
    float c = cos(ph);
    float s = sin(ph);
    P.x += steep * amp * D.x * c;
    P.z += steep * amp * D.y * c;
    P.y += amp * s;
    Nacc.x -= D.x * wa * c;
    Nacc.z -= D.y * wa * c;
    ny    -= steep * wa * s;
}

void main() {
    vec3 pos = in_position;
    vec3 nrm = in_normal;
    vec3 prev_pos = in_position;

    // mode 1 (ocean surface): Gerstner displacement at the current time, plus the previous-frame
    // position at (t - dt) so the fragment stage can form a true per-pixel motion vector. Seabed
    // (mode 0) and celestial (mode 2) are static, so prev_pos stays == pos → zero motion.
    if (pc.params.y > 0.5 && pc.params.y < 1.5) {
        float t  = pc.params.x;
        float dt = pc.params.z;
        vec2  p0 = in_position.xz;
        vec3  P  = in_position;
        vec3  Nacc = vec3(0.0);
        float ny = 1.0;
        gerstner(vec2( 1.0,  0.3), 0.045, 1.60, 0.55, 1.1, p0, t, P, Nacc, ny); // swell
        gerstner(vec2(-0.6,  1.0), 0.018, 0.90, 0.50, 1.7, p0, t, P, Nacc, ny); // chop
        gerstner(vec2( 0.8, -0.5), 0.009, 0.45, 0.40, 2.6, p0, t, P, Nacc, ny); // ripple
        Nacc.y = ny;
        pos = P;
        nrm = normalize(Nacc);

        // Previous-frame wave position (displacement only; normals are discarded).
        float tp = t - dt;
        vec3  Pp = in_position;
        vec3  Np = vec3(0.0);
        float nyp = 1.0;
        gerstner(vec2( 1.0,  0.3), 0.045, 1.60, 0.55, 1.1, p0, tp, Pp, Np, nyp);
        gerstner(vec2(-0.6,  1.0), 0.018, 0.90, 0.50, 1.7, p0, tp, Pp, Np, nyp);
        gerstner(vec2( 0.8, -0.5), 0.009, 0.45, 0.40, 2.6, p0, tp, Pp, Np, nyp);
        prev_pos = Pp;
    }

    vec4 world      = pc.model * vec4(pos, 1.0);
    vec4 prev_world = pc.model * vec4(prev_pos, 1.0);
    gl_Position = pc.projection * pc.view * world;

    v_world_pos    = world.xyz;
    v_normal       = normalize(mat3(pc.model) * nrm);
    v_floor_albedo = in_color;
    // Both clip positions go through the SAME (current) view-projection. The camera is static,
    // so reusing one VP makes the motion vector jitter-free (identical jitter cancels) and exactly
    // zero for the static seabed/celestial geometry. (A moving camera will need a previous VP.)
    v_clip      = gl_Position;
    v_prev_clip = pc.projection * pc.view * prev_world;
}
