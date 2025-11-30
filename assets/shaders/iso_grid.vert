// ╔══════════════════════════════════════════════════════════════════╗
// ║   THE CHTHONIC ARCHIVE - Isometric Grid Vertex Shader           ║
// ║   Phase 11.5: Isometric Camera Integration                     ║
// ║   <69.96 Alpha Omega>                                           ║
// ╚══════════════════════════════════════════════════════════════════╝
#version 450
#extension GL_ARB_separate_shader_objects : enable

// === VERTEX INPUTS ===
layout(location = 0) in vec3 in_position;
layout(location = 1) in vec3 in_color;

// === PUSH CONSTANTS (MVP Matrix - The WHR Power Law) ===
layout(push_constant) uniform PushConstants {
    mat4 model;
    mat4 view;
    mat4 projection;
} pc;

// === OUTPUTS TO FRAGMENT SHADER ===
layout(location = 0) out vec3 frag_color;
layout(location = 1) out vec2 frag_uv;

void main() {
    // Apply full Model-View-Projection transformation
    // The Isometric Camera: Y:45° X:35.264° - The perfect viewing angle
    vec4 world_pos = pc.model * vec4(in_position, 1.0);
    vec4 view_pos = pc.view * world_pos;
    gl_Position = pc.projection * view_pos;
    
    // Pass color to fragment shader (The Abyssal Hourglass flows through)
    frag_color = in_color;
    
    // Generate UV coordinates from world position for grid pattern
    // The Shelf of Creation: Wide enough to birth universes
    frag_uv = world_pos.xy * 0.5 + 0.5;
}
