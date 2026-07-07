// Rung 2.5 (RT reflections) — closest-hit stage. Fork-V: the real depth-driven Beer-Lambert
// seabed model, ported from water.frag's hero shader (its "Rung 5: seabed volumetric optics"
// block) rather than the flat vertex-color x N.L placeholder Phase 5 shipped with. Same
// constants, same physics — minus water.frag's final surface Fresnel/sky-reflection blend,
// which is the water SURFACE's own appearance from above and doesn't belong here: this shader
// only answers "what does the ray see having hit the seabed," a single-bounce hit, not a second
// reflection layered on top of the first.
//
// Reads vertex data via buffer_reference into the BLAS-input copy buffers built in
// ray_tracing.rs Phase 2 — those buffers carry no index buffer (VK_INDEX_TYPE_NONE_KHR, plain
// triangle lists matching Vertex's 36-byte [pos:3][normal:3][color:3] f32 layout), so
// gl_PrimitiveID directly indexes triangle N's three consecutive vertices.
#version 460
#extension GL_EXT_ray_tracing : require
#extension GL_EXT_buffer_reference2 : require
#extension GL_EXT_scalar_block_layout : require
#extension GL_EXT_shader_explicit_arithmetic_types_int64 : require

struct Vertex {
    vec3 position;
    vec3 normal;
    vec3 color;
};

// scalar layout (not std430) so this exactly matches the Rust #[repr(C)] Vertex layout —
// std430 would pad each vec3 member to 16 bytes, doubling the stride and misaligning reads.
layout(buffer_reference, scalar, buffer_reference_align = 4) readonly buffer VertexBuffer {
    Vertex v[];
};

// Set by the RT pipeline's push-constant range (Phase 4) — device addresses of the two
// BLAS-input copy buffers from ray_tracing.rs. gl_InstanceCustomIndexEXT selects which one
// (0 = bathymetry, 1 = ocean — matches Packed24_8::new(0/1, ...) in ray_tracing.rs; only
// bathymetry is ever actually hit today since the ray-gen's cullMask excludes ocean, mask 0x02).
layout(push_constant) uniform PushConstants {
    uint64_t bathymetry_vertex_addr;
    uint64_t ocean_vertex_addr;
    float sun_intensity;
} pc;

layout(location = 0) rayPayloadInEXT vec4 hit_color;
hitAttributeEXT vec2 attribs;

layout(set = 1, binding = 0, std140) uniform FrameData {
    mat4 current_motion_view_projection;
    mat4 previous_motion_view_projection;
    vec4 sst_data;
    layout(offset = 144) vec3 sun_direction;
} u_frame;

// Duplicated from water.frag (no shader #include mechanism in this codebase) — same Y_SCALE/
// SIGMA/SAND/WATER constants, same citations. See water.frag for the full sourcing
// (Williamson & Hollins 2022 PMID 36606827 Table 7, Jerlov IB; CoBOP/Voss 2003; Hill 2014).
const float Y_SCALE = 1.0;
const vec3  SIGMA   = vec3(0.471, 0.076, 0.050);
const vec3  SAND    = vec3(0.150, 0.172, 0.097);
const vec3  WATER   = vec3(0.006, 0.060, 0.185);

void main() {
    uint64_t addr = (gl_InstanceCustomIndexEXT == 0)
        ? pc.bathymetry_vertex_addr
        : pc.ocean_vertex_addr;
    VertexBuffer vb = VertexBuffer(addr);

    uint i0 = gl_PrimitiveID * 3 + 0;
    uint i1 = gl_PrimitiveID * 3 + 1;
    uint i2 = gl_PrimitiveID * 3 + 2;

    vec3 bary = vec3(1.0 - attribs.x - attribs.y, attribs.x, attribs.y);

    vec3 position = vb.v[i0].position * bary.x + vb.v[i1].position * bary.y + vb.v[i2].position * bary.z;
    vec3 color    = vb.v[i0].color    * bary.x + vb.v[i1].color    * bary.y + vb.v[i2].color    * bary.z;
    vec3 normal   = normalize(
        vb.v[i0].normal * bary.x + vb.v[i1].normal * bary.y + vb.v[i2].normal * bary.z
    );

    float I = pc.sun_intensity;
    float lambert = 0.30 + 0.70 * max(dot(normal, normalize(u_frame.sun_direction)), 0.0);

    // water.frag's Rung 5 seabed block, verbatim physics: exposed cay uses the real per-vertex
    // bathymetry color (varies per vertex); underwater uses the fixed SAND reflectance (the
    // Jerlov/Williamson-Hollins model assumes a uniform sand/seagrass mix, not the bathymetry
    // mesh's own per-vertex coloring) attenuated by Beer-Lambert, plus the water column's own
    // in-scatter glow where the floor is no longer visible. water.frag keeps a final Fresnel/
    // sky-reflection blend after this — deliberately not ported, see the header comment.
    float depth_m = max(0.0, -position.y / Y_SCALE);

    vec3 body;
    if (depth_m <= 0.0) {
        body = color * lambert * I;
    } else {
        vec3  trans       = exp(-SIGMA * depth_m * 2.0);
        vec3  floor_light = SAND * lambert * I * trans;
        float floor_vis   = dot(trans, vec3(0.299, 0.587, 0.114));
        vec3  water_glow  = WATER * I * (1.0 - floor_vis);
        body = floor_light + water_glow;
    }

    hit_color = vec4(body, 1.0); // alpha=1: a real hit, composite pass replaces
}
