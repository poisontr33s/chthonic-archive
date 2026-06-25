// TAA resolve — vertex stage (fullscreen triangle, no vertex buffer needed).
// Emits a clip-space triangle that covers the entire viewport. The rasterizer
// clips it to the screen; no input attributes, no push constants.
#version 450

// UV passed to the fragment stage for sampling the input images.
layout(location = 0) out vec2 v_uv;

void main() {
    // Fullscreen triangle trick: three hard-coded vertices in NDC.
    // gl_VertexIndex: 0→(-1,-1), 1→(3,-1), 2→(-1,3).
    // The triangle covers [0,1]² in UV space after the transform below.
    vec2 pos = vec2(
        float((gl_VertexIndex & 1) << 2) - 1.0,
        float((gl_VertexIndex & 2) << 1) - 1.0
    );
    v_uv        = pos * 0.5 + 0.5;
    gl_Position = vec4(pos, 0.0, 1.0);
}
