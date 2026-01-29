// ╔══════════════════════════════════════════════════════════════════╗
// ║   THE CHTHONIC ARCHIVE - Isometric Grid Fragment Shader         ║
// ║   Phase 11: Triumvirate Ascension                               ║
// ║   <69.96 Alpha Omega>                                           ║
// ╚══════════════════════════════════════════════════════════════════╝
#version 450
#extension GL_ARB_separate_shader_objects : enable

// === INPUTS FROM VERTEX SHADER ===
layout(location = 0) in vec3 frag_color;
layout(location = 1) in vec2 frag_uv;

// === OUTPUT COLOR ===
layout(location = 0) out vec4 out_color;

// === GRID CONFIGURATION ===
const float GRID_SIZE = 32.0;        // Grid cell size in world units
const float LINE_WIDTH = 0.02;       // Line width as fraction of cell
const vec3 BG_COLOR = vec3(0.05, 0.02, 0.08);   // Abyssal Background

// === PUSH CONSTANTS ===
layout(push_constant) uniform PushConstants {
    mat4 model;
    mat4 view;
    mat4 projection;
    vec4 layer_color;
} push;

void main() {
    // === LAYER MANIFESTATION: Visual Truth FA⁵ ===
    // We use the layer color passed from the engine to tint the render
    vec3 spectral_color = push.layer_color.rgb;
    
    // Mix vertex color with the layer's spectral frequency
    vec3 final_color = mix(frag_color, spectral_color, 0.7);
    
    out_color = vec4(final_color, 1.0);
    
    // === THE GRID PATTERN (Architectonic Integrity) ===
    // (Re-enabling basic grid overlay)
    vec2 grid_uv = frag_uv * GRID_SIZE;
    vec2 grid_fract = fract(grid_uv);
    vec2 dist_to_line = min(grid_fract, 1.0 - grid_fract);
    float min_dist = min(dist_to_line.x, dist_to_line.y);
    float line_intensity = 1.0 - smoothstep(0.0, LINE_WIDTH, min_dist);
    
    // Apply grid lines in variant color
    out_color.rgb = mix(out_color.rgb, vec3(1.0), line_intensity * 0.2);
}
