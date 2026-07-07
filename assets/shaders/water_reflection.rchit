// Rung 2.5 (RT reflections) — closest-hit stage. First cut: flat vertex-interpolated albedo
// x a basic N.L term — deliberately NOT the full Beer-Lambert shallow-water shader
// (water.frag's hero shader); duplicating that shader's constants/logic into a hit shader is a
// much bigger lift than this first pass warrants, and can be layered on once the pass's basic
// correctness (does the ray hit the right geometry, in the right place) is established.
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
} pc;

layout(location = 0) rayPayloadInEXT vec4 hit_color;
hitAttributeEXT vec2 attribs;

layout(set = 1, binding = 0, std140) uniform FrameData {
    mat4 current_motion_view_projection;
    mat4 previous_motion_view_projection;
    vec4 sst_data;
    layout(offset = 144) vec3 sun_direction;
} u_frame;

void main() {
    uint64_t addr = (gl_InstanceCustomIndexEXT == 0)
        ? pc.bathymetry_vertex_addr
        : pc.ocean_vertex_addr;
    VertexBuffer vb = VertexBuffer(addr);

    uint i0 = gl_PrimitiveID * 3 + 0;
    uint i1 = gl_PrimitiveID * 3 + 1;
    uint i2 = gl_PrimitiveID * 3 + 2;

    vec3 bary = vec3(1.0 - attribs.x - attribs.y, attribs.x, attribs.y);

    vec3 color = vb.v[i0].color  * bary.x + vb.v[i1].color  * bary.y + vb.v[i2].color  * bary.z;
    vec3 normal = normalize(
        vb.v[i0].normal * bary.x + vb.v[i1].normal * bary.y + vb.v[i2].normal * bary.z
    );

    float lambert = 0.30 + 0.70 * max(dot(normal, normalize(u_frame.sun_direction)), 0.0);
    hit_color = vec4(color * lambert, 1.0); // alpha=1: a real hit, composite pass replaces
}
