// @SID: DIRTY_DIFF_COMP_G4
// G4 — per-cell diff pass: compare curr_cells vs prev_cells, write dirty[i]=1 if changed.
// 300 cells (60×5 grid) — local_size_x=64 → 5 workgroups dispatch(ceil(300/64),1,1).

#version 450

layout(local_size_x = 64, local_size_y = 1, local_size_z = 1) in;

layout(std430, binding = 0) buffer CurrCells { uint curr[]; };
layout(std430, binding = 1) buffer PrevCells { uint prev[]; };
layout(std430, binding = 2) buffer DirtyFlags { uint dirty[]; };

layout(push_constant) uniform Push { uint cell_count; };

void main() {
    uint i = gl_GlobalInvocationID.x;
    if (i >= cell_count) return;
    dirty[i] = (curr[i] != prev[i]) ? 1u : 0u;
}
