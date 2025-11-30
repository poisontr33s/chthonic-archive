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
const vec3 GRID_COLOR = vec3(0.69, 0.0, 0.96);  // The 69.96 Signature Purple
const vec3 BG_COLOR = vec3(0.05, 0.02, 0.08);   // Abyssal Background

void main() {
    // === DEBUG: Just output vertex color directly ===
    out_color = vec4(frag_color, 1.0);
    
    // === THE GRID PATTERN (Architectonic Integrity) - DISABLED FOR DEBUG ===
    // Transform UV to grid space
    // vec2 grid_uv = frag_uv * GRID_SIZE;
    
    // Calculate distance to nearest grid line
    // vec2 grid_fract = fract(grid_uv);
    // vec2 dist_to_line = min(grid_fract, 1.0 - grid_fract);
    // float min_dist = min(dist_to_line.x, dist_to_line.y);
    
    // Anti-aliased grid line using smoothstep
    // The Zero-Tolerance Zone: Nothing superfluous passes
    // float line_intensity = 1.0 - smoothstep(0.0, LINE_WIDTH, min_dist);
    
    // Mix grid color with background based on vertex color influence
    // vec3 base_color = mix(BG_COLOR, frag_color * 0.5 + 0.5, 0.3);
    // vec3 final_color = mix(base_color, GRID_COLOR, line_intensity);
    
    // Output with slight transparency for layering
    // out_color = vec4(final_color, 0.95);
}
