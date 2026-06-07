#version 460
// @SID: ARCHIPELAGO_DIFFUSE_COMP_V0
// L−4 · ITERATE — one relaxation step of the archipelago field.
//
// The field stops being an analytic interpolation (L−5) and becomes a SIMULATION:
// islands are fixed sources (Dirichlet boundary), and every other cell relaxes toward
// the mean of its neighbours. Run N times, ping-ponging read/write buffers, and the
// field diffuses outward from the isles like heat — or pressure — over the sea.
//
// One invocation per grid cell. Pinned cells (islands) hold their seed; free cells
// take the 4-neighbour average of the READ buffer and write it to the WRITE buffer.
//
// Binding contract:
//   set=0 binding=0  SSBO  ReadBuf   readonly   — float in[W*H]   (previous step)
//   set=0 binding=1  SSBO  WriteBuf  writeonly  — float out[W*H]  (this step)
//   set=0 binding=2  SSBO  MaskBuf   readonly   — vec2 mask[W*H]: .x = state (1 source / 0 sea / −1 land), .y = source value
//   push_constant    { uint W, H }

layout(local_size_x = 8, local_size_y = 8) in;

layout(set = 0, binding = 0) readonly  buffer ReadBuf  { float fin[];  };
layout(set = 0, binding = 1) writeonly buffer WriteBuf { float fout[]; };
layout(set = 0, binding = 2) readonly  buffer MaskBuf  { vec2  mask[]; };

layout(push_constant) uniform Push { uint W; uint H; } pc;

uint at(uint x, uint y) { return y * pc.W + x; }

void main() {
    uint x = gl_GlobalInvocationID.x;
    uint y = gl_GlobalInvocationID.y;
    if (x >= pc.W || y >= pc.H) return;

    uint idx = at(x, y);

    // Island cells are fixed sources — they pin the field (Dirichlet boundary).
    if (mask[idx].x > 0.5) {
        fout[idx] = mask[idx].y;
        return;
    }
    // Land cells (mask.x = −1, set from real GEBCO bathymetry) are no-flux barriers — the field
    // never enters them, they hold. The standalone diffuse bin never sets land, so this branch
    // is inert there (backward-compatible).
    if (mask[idx].x < -0.5) {
        fout[idx] = fin[idx];
        return;
    }

    // Sea cells relax toward the mean of their SEA neighbours only. A land neighbour gives no
    // flux (a reflecting coast), so heat flows AROUND the islands and through the channels —
    // the field runs on the real Bahama Bank, not a flat grid.
    uint xl = (x > 0u)          ? x - 1u : x;
    uint xr = (x + 1u < pc.W)   ? x + 1u : x;
    uint yu = (y > 0u)          ? y - 1u : y;
    uint yd = (y + 1u < pc.H)   ? y + 1u : y;

    float sum = 0.0;
    float n = 0.0;
    if (mask[at(xl, y)].x > -0.5) { sum += fin[at(xl, y)]; n += 1.0; }
    if (mask[at(xr, y)].x > -0.5) { sum += fin[at(xr, y)]; n += 1.0; }
    if (mask[at(x, yu)].x > -0.5) { sum += fin[at(x, yu)]; n += 1.0; }
    if (mask[at(x, yd)].x > -0.5) { sum += fin[at(x, yd)]; n += 1.0; }
    fout[idx] = (n > 0.0) ? sum / n : fin[idx];
}
