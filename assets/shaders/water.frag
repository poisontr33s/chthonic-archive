// Rung 5 + Rung 4 — shallow-water hero shader (fragment stage). Two modes via params.y:
//   mode 1 (surface): the Rung-4 ocean surface — Fresnel sky-tint + sun glint on the
//                     Gerstner wave normal, translucent so it blends over the seabed.
//   mode 0 (seabed):  the Volumetric Optical Pipeline — depth reconstruction + per-channel
//                     Beer–Lambert (turquoise from white sand) + in-scatter (deep → navy).
//   mode 2 (celestial): unlit Sun/Moon/planet discs in the real topocentric sky.
#version 450
#extension GL_ARB_separate_shader_objects : enable

layout(location = 0) in vec3 v_world_pos;
layout(location = 1) in vec3 v_normal;
layout(location = 2) in vec3 v_floor_albedo;

layout(push_constant) uniform PushConstants {
    mat4 model;
    mat4 view;
    mat4 projection;
    vec4 sun;      // xyz = direction TO the sun, w = intensity
    vec4 params;   // x = time, y = mode, z = frame dt, w = motion-debug toggle
} pc;

// set=0 is the ocean displacement sampler (water.vert, bindings 0+1).
// Frame UBO lives at set=1: vertex reads motion matrices, fragment reads SST tint.
layout(set = 1, binding = 0) uniform FrameData {
    mat4 current_motion_view_projection;
    mat4 previous_motion_view_projection;
    vec4 sst_data;  // xyz = SST-adjusted warm tint, w = blend scalar [0..1]
} u_frame;

layout(location = 3) in vec4 v_clip;       // current clip position
layout(location = 4) in vec4 v_prev_clip;  // previous-frame clip position

layout(location = 0) out vec4 out_color;
layout(location = 1) out vec2 out_motion;

layout(set = 1, binding = 1) uniform sampler2D u_sky_view_lut;
layout(set = 1, binding = 2) uniform sampler2D u_cloud_tex;

// Site 2 — bathymetry render.y is ENU.z (elevation in metres). Y_SCALE = 1.0.
// ELLIPSOID-RETROFIT: Site 5 — replace with ellipsoidal normal distance for precision passes.
const float Y_SCALE = 1.0;                      // render.y IS metres after Ellipsoid Site 2
// Williamson & Hollins 2022 (PMID 36606827) Table 7, Jerlov IB — Nassau/Bahama Banks.
// Round-trip path length factored by exp(-SIGMA * depth_m * 2.0) below; SIGMA = Kd one-way.
const vec3  SIGMA   = vec3(0.471, 0.076, 0.050); // Kd m⁻¹ at R(670nm) G(550nm) B(440nm)
// Nassau Banks bottom: 70% Thalassia testudinum canopy + 30% Bahamas carbonate sand.
// Canopy endmember (CoBOP/Voss 2003, Lee Stocking Island): R(670)=0.02, G(550)=0.09, B(440)=0.03.
// Sand endmember (Hill 2014, Voss 2003 Bahamas): R(670)=0.44, G(550)=0.40, B(440)=0.30.
// 70/30 linear mix per Mobley 2005 LUT. Cover fraction from Moritsch 2025 (PMC12084626). DR 2026-06-27.
const vec3  SAND    = vec3(0.150, 0.172, 0.097); // 70% T.testudinum canopy + 30% carbonate sand
// Jerlov IB deep-water asymptote: R_inf ∝ b_b/a (Morel & Maritorena 2001 Case 1 reflectance model).
// Williamson-Hollins 2022 IOPs → midpoint of simple/refined R_inf: G/B≈0.32, R/B≈0.032. DR 2026-06-27.
const vec3  WATER   = vec3(0.006, 0.060, 0.185); // Jerlov IB deep-water asymptote (blue-dominant)

vec3 sampleSkyViewLut(vec3 view_dir) {
    // view_dir must be normalized
    float view_zenith_angle = acos(clamp(view_dir.y, -1.0, 1.0));    
    
    // The sun azimuth is currently aligned with the X-axis in the LUT generation, 
    // so we measure azimuth relative to the sun direction from the UBO.
    vec3 sun_dir_flat = normalize(vec3(pc.sun.x, 0.0, pc.sun.z));
    vec3 view_dir_flat = normalize(vec3(view_dir.x, 0.0, view_dir.z));
    float view_sun_azimuth = acos(clamp(dot(sun_dir_flat, view_dir_flat), -1.0, 1.0));
    
    // Determine sign of azimuth
    if (dot(cross(vec3(0.0, 1.0, 0.0), sun_dir_flat), view_dir_flat) < 0.0) {
        view_sun_azimuth = -view_sun_azimuth;
    }
    
    vec2 uv;
    // Inverse Azimuth mapping
    uv.x = (view_sun_azimuth / 3.14159265) * 0.5 + 0.5;
    
    // Inverse Zenith mapping (Non-linear horizon emphasis)
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
    // Streamline/DLSS motion vector direction: current -> previous in UV space.
    // Both clip positions are generated from unjittered view-projection matrices; Streamline
    // receives jitter separately through sl::Constants::jitterOffset.
    vec2 curr_uv = (v_clip.xy / v_clip.w) * 0.5 + 0.5;
    vec2 prev_uv = (v_prev_clip.xy / v_prev_clip.w) * 0.5 + 0.5;
    vec2 motion  = prev_uv - curr_uv;
    out_motion = motion;

    // Motion-buffer debug view (CHTHONIC_SHOW_MOTION): mid-grey = still, R/G encode motion
    // direction. The gain is large because per-frame wave motion is sub-pixel at this zoom.
    if (pc.params.w > 0.5) {
        const float gain = 12000.0;
        out_color = vec4(0.5 + motion.x * gain, 0.5 + motion.y * gain, 0.5, 1.0);
        return;
    }

    vec3  N = normalize(v_normal);
    vec3  L = normalize(pc.sun.xyz);
    float I = pc.sun.w;
    vec3  V = normalize(vec3(1.0, 1.0, 1.0)); // iso camera approx (toward viewer)
    vec3  H = normalize(L + V);

    // Screen UV for cloud composite (same resolution as the render target)
    vec2 cloudUv = gl_FragCoord.xy / vec2(textureSize(u_cloud_tex, 0));
    vec4 cloudLayer = texture(u_cloud_tex, cloudUv);

    // === Rung 6.2: celestial field ===
    if (pc.params.y > 1.5) {
        // Cloud layer composited over sky background; celestial discs (v_floor_albedo) on top
        vec3 sky = sampleSkyViewLut(V);
        out_color = vec4(mix(sky, cloudLayer.rgb, cloudLayer.a) + v_floor_albedo, 1.0);
        return;
    }

    // === Rung 4: ocean surface ===
    if (pc.params.y > 0.5) {
        float fres  = 0.02 + 0.98 * pow(1.0 - max(dot(N, V), 0.0), 5.0);
        // Blend clouds into the reflected sky so they appear in the water surface Fresnel
        vec3  sky   = mix(sampleSkyViewLut(reflect(-V, N)), cloudLayer.rgb, cloudLayer.a * 0.7);
        float glint = pow(max(dot(N, H), 0.0), 200.0) * I;
        vec3  tint  = mix(vec3(0.08, 0.34, 0.42), u_frame.sst_data.xyz, u_frame.sst_data.w);
        vec3  col   = mix(tint, sky, fres) + vec3(glint);
        out_color   = vec4(col, 0.30); // translucent — lets the seabed turquoise read through
        return;
    }

    // === Rung 5: seabed volumetric optics ===
    // ELLIPSOID-RETROFIT: Site 5 — depth_m is ENU.z (positive = metres below sea surface).
    // At Site 6, replace with ellipsoidal normal distance for sub-metre geodetic precision.
    float depth_m = max(0.0, -v_world_pos.y / Y_SCALE);
    float lambert = 0.30 + 0.70 * max(dot(N, L), 0.0);

    if (depth_m <= 0.0) {
        out_color = vec4(v_floor_albedo * lambert * I, 1.0); // exposed cay
        return;
    }

    vec3  trans      = exp(-SIGMA * depth_m * 2.0);
    vec3  floor_light = SAND * lambert * I * trans;
    float floor_vis  = dot(trans, vec3(0.299, 0.587, 0.114));
    vec3  water_glow = WATER * I * (1.0 - floor_vis);
    vec3  body       = floor_light + water_glow;

    float fres  = 0.02 + 0.30 * pow(1.0 - max(dot(N, V), 0.0), 5.0);
    vec3  sky   = sampleSkyViewLut(reflect(-V, N));
    float glint = pow(max(dot(N, H), 0.0), 80.0) * I;

    out_color = vec4(mix(body, sky, fres) + vec3(glint), 1.0);
}
