// @SID: ASCII_DUNGEON_COMP_G6
// G6 — Urca de Lima synthesis: manifest as dungeon floor plan.
// Same todo_roulette.json → same EulerTask SSBO → different projection function.
// No VkImage needed. Reads task_buf + score_buf, writes cells[] directly.
//
// Grid: 60 cols × 5 rows = 300 cells (same as ascii_downsample output).
// Room layout: each room occupies 4 cols + 1 col corridor = 5 cols per room.
//   60 / 5 = 12 rooms max → shows top-12 active tasks as dungeon rooms.
//
// Cell encoding (matches Rust BLOCK_CHARS): u32 = (char_idx << 24) | (R << 16) | (G << 8) | B
//   0=" "  1="░"  2="▒"  3="▓"  4="█"
//   5="╔"  6="═"  7="╗"  8="║"  9="╚"  10="╝"  11="·"  12="╬"
//
// SpinState ≡ RoomState (G5 identity):
//   state_phase 0 = Idle / Locked   (dim borders, dark interior)
//   state_phase 1 = Spinning / Unlocked  (full brightness borders)
//   state_phase 2 = Decelerating / Visited  (bright interior)
//   state_phase 3 = Landed / Cleared   (faded walls, open interior)

#version 450
layout(local_size_x = 8, local_size_y = 8, local_size_z = 1) in;

struct EulerTask {
    float weight;
    float staleness_days;
    float phase_angle;
    float _pad;
};

layout(std430, binding = 0) readonly buffer TaskBuf  { EulerTask tasks[];  };
layout(std430, binding = 1) readonly buffer ScoreBuf { float     scores[]; };
layout(std430, binding = 2) readonly buffer CountBuf { uint      task_count; };
layout(std430, binding = 3)          buffer CellBuf  { uint      cells[];  };

layout(push_constant) uniform Push { uint state_phase; };

const float TWO_PI    = 6.28318530718;
const uint  CELL_COLS = 60u;
const uint  CELL_ROWS = 5u;
const uint  ROOM_W    = 4u;   // cols per room (including both walls)
const uint  ROOM_STRIDE = 5u; // room width + 1 corridor col

void main() {
    uint col = gl_GlobalInvocationID.x;
    uint row = gl_GlobalInvocationID.y;
    if (col >= CELL_COLS || row >= CELL_ROWS) return;

    uint cell_idx  = row * CELL_COLS + col;
    uint room_idx  = col / ROOM_STRIDE;   // which room (0..11)
    uint col_in_rm = col % ROOM_STRIDE;   // 0-3 = room interior/wall, 4 = corridor

    // ── Task-derived color (tag phase angle → HSL-like RGB) ──────────────
    float phase = (room_idx < task_count) ? tasks[room_idx].phase_angle : 0.0;
    float r_f = clamp(0.5 + 0.5 * cos(phase),                          0.0, 1.0);
    float g_f = clamp(0.5 + 0.5 * cos(phase + TWO_PI / 3.0),           0.0, 1.0);
    float b_f = clamp(0.5 + 0.5 * cos(phase + 2.0 * TWO_PI / 3.0),     0.0, 1.0);

    // ── Score intensity for interior fill ─────────────────────────────────
    float score_norm = 0.0;
    if (room_idx < task_count) {
        score_norm = clamp(scores[room_idx] / 500.0, 0.0, 1.0);
    }

    // ── Dim factor: walls dimmer than interior ─────────────────────────────
    bool is_border_col = (col_in_rm == 0u || col_in_rm == 3u);
    bool is_top        = (row == 0u);
    bool is_bottom     = (row == 4u);
    bool is_wall       = is_border_col || is_top || is_bottom;
    float dim = is_wall ? 0.55 : 1.0;
    if (room_idx >= task_count) dim *= 0.2;   // empty slot = very dim

    // ── Character selection ────────────────────────────────────────────────
    uint char_idx;

    if (col_in_rm == 4u) {
        // Corridor column
        bool has_next = (room_idx + 1u < task_count);
        if (row == 0u || row == 4u) {
            char_idx = 4u;   // '█' wall above/below corridor
            dim      = 0.12;
        } else if (has_next) {
            char_idx = 6u;   // '═' connected corridor
        } else {
            char_idx = 11u;  // '·' dead-end stub
        }
    } else {
        // Room column (col_in_rm 0-3)
        if (is_top) {
            if      (col_in_rm == 0u) char_idx = 5u;  // '╔'
            else if (col_in_rm == 3u) char_idx = 7u;  // '╗'
            else                      char_idx = 6u;  // '═' top wall
        } else if (is_bottom) {
            if      (col_in_rm == 0u) char_idx = 9u;  // '╚'
            else if (col_in_rm == 3u) char_idx = 10u; // '╝'
            else                      char_idx = 6u;  // '═' bottom wall
        } else if (is_border_col) {
            char_idx = 8u;   // '║' side wall
        } else {
            // Interior (col_in_rm 1-2, row 1-3): score density fill
            float intensity = score_norm;

            // state_phase modulates interior brightness:
            //   0 Idle/Locked:         dim fill
            //   1 Spinning/Unlocked:   normal fill
            //   2 Decelerating/Visited: bright fill
            //   3 Landed/Cleared:      near-empty (cleared room)
            if      (state_phase == 0u) intensity *= 0.35;
            else if (state_phase == 2u) intensity  = clamp(intensity * 1.6, 0.0, 1.0);
            else if (state_phase == 3u) intensity *= 0.15;

            if (room_idx < task_count) {
                uint block = uint(intensity * 4.0);
                char_idx   = clamp(block, 0u, 4u);   // 0=' ' 1='░' 2='▒' 3='▓' 4='█'
            } else {
                char_idx = 0u; // empty room = space
            }
        }
    }

    // ── Active room (room 0) gets boosted border based on state_phase ─────
    if (room_idx == 0u && is_wall && col_in_rm != 4u) {
        if      (state_phase == 0u) dim = 0.3;
        else if (state_phase == 1u) dim = 1.0;
        else if (state_phase == 2u) dim = 0.9;
        else                        dim = 0.45;
    }

    uint R = uint(clamp(r_f * dim * 255.0, 0.0, 255.0));
    uint G = uint(clamp(g_f * dim * 255.0, 0.0, 255.0));
    uint B = uint(clamp(b_f * dim * 255.0, 0.0, 255.0));

    cells[cell_idx] = (char_idx << 24u) | (R << 16u) | (G << 8u) | B;
}
