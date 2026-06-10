// Rung 5 + Rung 4 — shallow-water hero shader (vertex stage).
//   mode 0 (seabed):  pass-through of the bathymetry vertex.
//   mode 1 (surface): Gerstner-wave displacement + analytic wave normal (the Rung-4 ocean).
// The 4th/5th push-constant vec4s carry the solar vector and [time, mode].
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
    vec4 params;   // x = time (s), y = mode (0 seabed / 1 surface)
} pc;

layout(location = 0) out vec3 v_world_pos;
layout(location = 1) out vec3 v_normal;
layout(location = 2) out vec3 v_floor_albedo;

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

    if (pc.params.y > 0.5) {
        float t  = pc.params.x;
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
    }

    vec4 world = pc.model * vec4(pos, 1.0);
    gl_Position = pc.projection * pc.view * world;

    v_world_pos    = world.xyz;
    v_normal       = normalize(mat3(pc.model) * nrm);
    v_floor_albedo = in_color;
}
