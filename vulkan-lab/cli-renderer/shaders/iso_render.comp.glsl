// @SID: ISO_RENDER_COMP_V8
// V8: Isometric cRPG terminal renderer.
// Projects 12×6 tile world into 80×24 diamond-angle ASCII grid.
// Each tile maps to a task from the manifest (task_idx field in IsoRoom).
// Room visual state mirrors SpinState FSM (Idle/Locked → Spinning/Unlocked → Decel/Visited → Landed/Cleared).
#version 450
layout(local_size_x=8, local_size_y=8, local_size_z=1) in;

struct EulerTask    { float weight; float staleness_days; float phase_angle; float _pad; };
struct IsoRoom      { int tile_x; int tile_y; uint room_state; uint task_idx;
                      float tag_color_r; float tag_color_g; float tag_color_b; float _pad; };
struct PlayerState  { int tile_x; int tile_y; uint facing; uint _pad; };

layout(set=0, binding=0, std430) readonly  buffer TaskBuf    { EulerTask tasks[]; };
layout(set=0, binding=1, std430) readonly  buffer ScoreBuf   { float scores[]; };
layout(set=0, binding=2, std430) readonly  buffer CountBuf   { uint task_count; };
layout(set=0, binding=3, std430) writeonly buffer IsoCellBuf { uint cells[]; };
layout(set=0, binding=4, std430) readonly  buffer PlayerBuf  { PlayerState player; };
layout(set=0, binding=5, std430) readonly  buffer IsoRoomBuf { IsoRoom rooms[12]; };

layout(push_constant) uniform PC {
    uint state_phase;
    int  player_tile_x;
    int  player_tile_y;
    uint _pad;
} pc;

// ── Constants ──────────────────────────────────────────────────────────────
// Diamond-angle isometric projection: screen_x = (tx-ty)*TW, screen_y = (tx+ty)*TH
const int TILE_W_HALF = 4;   // half tile width in screen cells
const int TILE_H_HALF = 2;   // half tile height in screen cells
const int ISO_COLS    = 80;
const int ISO_ROWS    = 24;
const int TILE_COLS   = 12;
const int TILE_ROWS   = 6;
// Origin: where tile (0,0) top vertex appears on screen
const int ORIGIN_X    = 40;
const int ORIGIN_Y    = 6;

void main() {
    uint gx = gl_GlobalInvocationID.x;
    uint gy = gl_GlobalInvocationID.y;
    if (gx >= uint(ISO_COLS) || gy >= uint(ISO_ROWS)) return;

    uint cell_idx = gy * uint(ISO_COLS) + gx;

    // Default: void (background)
    uint char_idx = 0u;
    uint r = 8u, g = 8u, b = 12u;

    // Inverse iso projection: screen → tile coords (float)
    int sx = int(gx) - ORIGIN_X;
    int sy = int(gy) - ORIGIN_Y;

    // Solve: sx = (tx - ty)*TW_HALF, sy = (tx + ty)*TH_HALF
    // tx = 0.5*(sx/TW_HALF + sy/TH_HALF), ty = 0.5*(sy/TH_HALF - sx/TW_HALF)
    float ftx = (float(sx) / float(TILE_W_HALF) + float(sy) / float(TILE_H_HALF)) * 0.5;
    float fty = (float(sy) / float(TILE_H_HALF) - float(sx) / float(TILE_W_HALF)) * 0.5;
    int tx = int(floor(ftx));
    int ty = int(floor(fty));

    float frac_x = ftx - floor(ftx);
    float frac_y = fty - floor(fty);
    bool in_grid = (tx >= 0 && tx < TILE_COLS && ty >= 0 && ty < TILE_ROWS);

    if (in_grid) {
        // Find room at (tx, ty)
        int room_idx = -1;
        for (int i = 0; i < 12; i++) {
            if (rooms[i].tile_x == tx && rooms[i].tile_y == ty) { room_idx = i; break; }
        }

        if (room_idx >= 0) {
            IsoRoom rm = rooms[room_idx];
            uint rs = rm.room_state;
            // char: 13=◆(cleared), 14=◇(locked), 15=╱(visited edge), 12=·(unlocked dot)
            if      (rs == 0u) { char_idx = 14u; }   // Locked  → hollow diamond
            else if (rs == 1u) { char_idx = 12u; }   // Unlocked → center dot
            else if (rs == 2u) { char_idx = 15u; }   // Visited  → slash
            else               { char_idx = 13u; }   // Cleared  → solid diamond

            // Brightness by state
            float brightness;
            if      (rs == 3u) { brightness = 1.3; }
            else if (rs == 2u) { brightness = 0.9; }
            else if (rs == 1u) { brightness = 0.6; }
            else                { brightness = 0.3; }

            r = uint(clamp(rm.tag_color_r * brightness * 255.0, 0.0, 255.0));
            g = uint(clamp(rm.tag_color_g * brightness * 255.0, 0.0, 255.0));
            b = uint(clamp(rm.tag_color_b * brightness * 255.0, 0.0, 255.0));
        } else {
            // Empty tile — dim floor
            char_idx = 1u;   // ░
            r = 22u; g = 18u; b = 30u;
        }

        // Diamond tile edges (NE: frac_x+frac_y≈1, NW: frac_x≈frac_y)
        bool on_ne_edge = (abs(frac_x + frac_y - 1.0) < 0.25);
        bool on_nw_edge = (abs(frac_x - frac_y) < 0.12);
        if (on_ne_edge && char_idx != 13u) {
            char_idx = 16u; r = 70u; g = 70u; b = 110u;  // ╱ NE edge
        } else if (on_nw_edge && char_idx != 13u) {
            char_idx = 17u; r = 70u; g = 70u; b = 110u;  // ╲ NW edge
        }
    }

    // Player glyph (@ = index 19, drawn on top)
    if (in_grid && tx == pc.player_tile_x && ty == pc.player_tile_y) {
        char_idx = 19u;  // @
        r = 255u; g = 85u; b = 85u;
    }

    cells[cell_idx] = (char_idx << 24u) | (r << 16u) | (g << 8u) | b;
}
