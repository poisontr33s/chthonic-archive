#version 460
// @SID: ASCII_DOWNSAMPLE_COMP_V0
// Gate 3: ASCII framebuffer downsample
//
// Reads off-screen VkImage (GPU-rasterized arc wheel, 480x80 R8G8B8A8).
// For each 8x16 pixel cell: compute coverage + dominant color.
// Outputs: (char_index, r, g, b) packed into uint32 per cell.
// Host decodes: emit \x1b[38;2;R;G;Bm<block_char>  (ANSI truecolor)
//
// Block char mapping (coverage 0..1 → Unicode block elements):
//   0.00–0.20 → ' '  (space)
//   0.20–0.40 → '░'  U+2591
//   0.40–0.60 → '▒'  U+2592
//   0.60–0.80 → '▓'  U+2593
//   0.80–1.00 → '█'  U+2588
//
// Binding contract:
//   set=0 binding=0  image2D  src_image   rgba8  — off-screen VkImage (480x80)
//   set=0 binding=1  SSBO     OutBuf              — uint cells[], one per character cell
//
// Output encoding: cells[i] = (char_index << 24) | (r << 16) | (g << 8) | b
// Cell grid: image_width / 8  x  image_height / 16  (60 x 5 for 480x80)
//
// G4 extension: add set=0 binding=2 prev_image for dirty-cell diff pass.
// Diff: for each cell, compare curr vs prev dominant color → emit dirty flag.
// Host iterates only dirty cells — eliminates full-screen clear flicker.

layout(local_size_x = 8, local_size_y = 16) in;

layout(set = 0, binding = 0, rgba8) readonly uniform image2D src_image;
layout(set = 0, binding = 1)        writeonly buffer OutBuf  { uint cells[]; };

shared vec4 tile[16][8]; // 8x16 pixels for this cell, loaded into shared memory

// Luminance weights (BT.709)
const vec3 LUMA = vec3(0.2126, 0.7152, 0.0722);

void main() {
    ivec2 cell  = ivec2(gl_WorkGroupID.xy);
    ivec2 pixel = cell * ivec2(8, 16) + ivec2(gl_LocalInvocationID.xy);

    // Load pixel into shared memory
    vec4 col = imageLoad(src_image, pixel);
    tile[gl_LocalInvocationID.y][gl_LocalInvocationID.x] = col;

    barrier();

    // Only thread (0,0) in each workgroup writes the output
    if (gl_LocalInvocationID.x == 0u && gl_LocalInvocationID.y == 0u) {
        // Reduce: average coverage + dominant color across all 128 pixels in cell
        float coverage_sum = 0.0;
        vec3  color_sum    = vec3(0.0);

        for (int y = 0; y < 16; ++y) {
            for (int x = 0; x < 8; ++x) {
                vec4 p = tile[y][x];
                coverage_sum += dot(p.rgb, LUMA);
                color_sum    += p.rgb;
            }
        }

        float coverage = coverage_sum / 128.0;
        vec3  avg_col  = color_sum    / 128.0;

        // Map coverage → block character index
        uint char_idx;
        if      (coverage < 0.2) char_idx = 0u;  // ' '
        else if (coverage < 0.4) char_idx = 1u;  // ░
        else if (coverage < 0.6) char_idx = 2u;  // ▒
        else if (coverage < 0.8) char_idx = 3u;  // ▓
        else                     char_idx = 4u;  // █

        uint r = uint(avg_col.r * 255.0);
        uint g = uint(avg_col.g * 255.0);
        uint b = uint(avg_col.b * 255.0);

        ivec2 img_size  = imageSize(src_image);
        ivec2 grid_size = img_size / ivec2(8, 16);
        uint  out_idx   = uint(cell.y) * uint(grid_size.x) + uint(cell.x);

        cells[out_idx] = (char_idx << 24u) | (r << 16u) | (g << 8u) | b;
    }
}
