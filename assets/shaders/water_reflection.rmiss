// Rung 2.5 (RT reflections) — miss stage. A ray that escapes to sky must produce the same
// result as water.frag's existing analytic sky term, so the RT pass is a strict superset (not
// a regression) for the common no-occluder case. sampleSkyViewLut is hand-duplicated here —
// no #include mechanism exists in this shader tree (build.rs has no -I plumbing either).
#version 460
#extension GL_EXT_ray_tracing : require

layout(location = 0) rayPayloadInEXT vec3 hit_color;

layout(set = 1, binding = 0, std140) uniform FrameData {
    mat4 current_motion_view_projection;
    mat4 previous_motion_view_projection;
    vec4 sst_data;
    layout(offset = 144) vec3 sun_direction;
} u_frame;

layout(set = 1, binding = 1) uniform sampler2D u_sky_view_lut;

// Verbatim copy of water.frag's sampleSkyViewLut (see that file for derivation notes).
vec3 sampleSkyViewLut(vec3 view_dir) {
    float view_zenith_angle = acos(clamp(view_dir.y, -1.0, 1.0));

    vec3 sun_dir_flat = normalize(vec3(u_frame.sun_direction.x, 0.0, u_frame.sun_direction.z));
    vec3 view_dir_flat = normalize(vec3(view_dir.x, 0.0, view_dir.z));
    float view_sun_azimuth = acos(clamp(dot(sun_dir_flat, view_dir_flat), -1.0, 1.0));

    if (dot(cross(vec3(0.0, 1.0, 0.0), sun_dir_flat), view_dir_flat) < 0.0) {
        view_sun_azimuth = -view_sun_azimuth;
    }

    vec2 uv;
    uv.x = (view_sun_azimuth / 3.14159265) * 0.5 + 0.5;

    if (view_zenith_angle < 3.14159265 * 0.5) {
        float coord = sqrt(max(0.0, 1.0 - view_zenith_angle / (3.14159265 * 0.5)));
        uv.y = (1.0 - coord) * 0.5;
    } else {
        float coord = sqrt(max(0.0, (view_zenith_angle - 3.14159265 * 0.5) / (3.14159265 * 0.5)));
        uv.y = 0.5 + coord * 0.5;
    }

    return texture(u_sky_view_lut, uv).rgb;
}

void main() {
    hit_color = sampleSkyViewLut(normalize(gl_WorldRayDirectionEXT));
}
