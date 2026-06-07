#version 460
// @SID: ARCHIPELAGO_ADVECT_COMP_V0
// L−2 · ADVECT — semi-Lagrangian transport of the field by a wind velocity field.
//
// Diffusion (L−4) SPREADS; advection MOVES. For each cell we trace one step BACKWARD
// along the local wind (Stam's stable advection), bilinearly sample the field at that
// upstream point, and write it here. Unconditionally stable — no CFL limit — because we
// never push mass forward past a neighbour; we pull from where it came.
//
// Binding contract:
//   set=0 binding=0  SSBO  ReadBuf   readonly   — float in[W*H]   (previous step)
//   set=0 binding=1  SSBO  WriteBuf  writeonly  — float out[W*H]  (this step)
//   set=0 binding=2  SSBO  VelBuf    readonly   — vec2 vel[W*H]   (cells/step, grid axes: +x east, +y south)
//   push_constant    { uint W, H }

layout(local_size_x = 8, local_size_y = 8) in;

layout(set = 0, binding = 0) readonly  buffer ReadBuf  { float fin[];  };
layout(set = 0, binding = 1) writeonly buffer WriteBuf { float fout[]; };
layout(set = 0, binding = 2) readonly  buffer VelBuf   { vec2  vel[];  };

layout(push_constant) uniform Push { uint W; uint H; } pc;

// Bilinear sample of the READ buffer at a (possibly fractional) grid point.
float sample_bilinear(vec2 p) {
    // Clamp into the grid so an upstream trace off the edge reads the border, never OOB.
    p = clamp(p, vec2(0.0), vec2(float(pc.W - 1u), float(pc.H - 1u)));
    uint x0 = uint(floor(p.x));
    uint y0 = uint(floor(p.y));
    uint x1 = min(x0 + 1u, pc.W - 1u);
    uint y1 = min(y0 + 1u, pc.H - 1u);
    float fx = p.x - float(x0);
    float fy = p.y - float(y0);
    float a = fin[y0 * pc.W + x0];
    float b = fin[y0 * pc.W + x1];
    float c = fin[y1 * pc.W + x0];
    float d = fin[y1 * pc.W + x1];
    return mix(mix(a, b, fx), mix(c, d, fx), fy);
}

void main() {
    uint x = gl_GlobalInvocationID.x;
    uint y = gl_GlobalInvocationID.y;
    if (x >= pc.W || y >= pc.H) return;
    uint idx = y * pc.W + x;

    vec2 here = vec2(float(x), float(y));
    vec2 src  = here - vel[idx];   // trace one step UPSTREAM, then pull the field from there
    fout[idx] = sample_bilinear(src);
}
