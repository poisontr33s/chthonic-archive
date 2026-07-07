// Rung 2.5 (RT reflections) Phase 5 — composite stage. Blends the ray-traced reflection
// output onto the scene color, gated by hit/miss (see water_reflection.rgen/.rmiss: the
// payload's alpha is 1.0 on a real geometry hit, 0.0 on a sky miss or a non-water pixel).
// Reuses taa_resolve.vert's fullscreen-triangle trick for the vertex stage — no vertex buffer.
// Same SRC_ALPHA/ONE_MINUS_SRC_ALPHA blend as the main pipeline's color attachment 0
// (pipeline.rs), so alpha=0 (miss/non-water) leaves the destination bit-for-bit untouched
// and alpha=1 (hit) fully replaces it — this is what makes the Phase 5 pixel-diff meaningful.
#version 450

layout(location = 0) in vec2 v_uv;
layout(location = 0) out vec4 out_color;

layout(set = 0, binding = 0) uniform sampler2D u_rt_output;

void main() {
    out_color = texture(u_rt_output, v_uv);
}
