#version 460

// Chthonic Trail — LZ4 Block Decompressor
// @SID: SHADER_TRAIL_DECOMPRESS_V1
// @Type: Compute
//
// Decompresses a single LZ4 block stored in the stone payload.
// Single-invocation (local_size_x=1): LZ4 block decoding is inherently serial
// within a single block. Parallelism lives above this in multi-block dispatch.
//
// Dispatch: vkCmdDispatch(1, 1, 1)
// Target:   Vulkan 1.3, RTX 4090 (SPIR-V 1.6)

layout(local_size_x = 1, local_size_y = 1, local_size_z = 1) in;

// Binding 0: LZ4-compressed input. uint[] packs 4 bytes per element (LE).
layout(set = 0, binding = 0, std430) readonly buffer CompressedData {
    uint data[];
} src;

// Binding 1: Decompressed output. Must be readwrite — match copies read back
// previously written bytes (overlapping copies are defined by LZ4 spec).
layout(set = 0, binding = 1, std430) buffer DecompressedData {
    uint data[];
} dst;

// Binding 2: Sizes passed from CPU.
layout(set = 0, binding = 2, std430) readonly buffer Metadata {
    uint compressed_size;
    uint uncompressed_size;
} meta;

// Read one byte from the src (compressed) buffer at byte offset `i`.
uint src_byte(uint i) {
    return (src.data[i >> 2u] >> ((i & 3u) << 3u)) & 0xFFu;
}

// Read one byte from the dst (decompressed) buffer at byte offset `i`.
// Used during match-copy sequences.
uint dst_byte(uint i) {
    return (dst.data[i >> 2u] >> ((i & 3u) << 3u)) & 0xFFu;
}

// Write one byte to the dst buffer at byte offset `i`.
void dst_write(uint i, uint val) {
    uint idx   = i >> 2u;
    uint shift = (i & 3u) << 3u;
    dst.data[idx] = (dst.data[idx] & ~(0xFFu << shift)) | ((val & 0xFFu) << shift);
}

void main() {
    uint sp        = 0u;                    // source position (bytes)
    uint dp        = 0u;                    // destination position (bytes)
    uint src_end   = meta.compressed_size;
    uint dst_limit = meta.uncompressed_size;

    while (sp < src_end && dp < dst_limit) {

        // ── Token ────────────────────────────────────────────────────────────
        uint token = src_byte(sp);
        sp += 1u;

        // ── Literal length ───────────────────────────────────────────────────
        uint lit_len = token >> 4u;
        if (lit_len == 15u) {
            uint extra;
            do {
                extra = src_byte(sp);
                sp   += 1u;
                lit_len += extra;
            } while (extra == 255u && sp < src_end);
        }

        // ── Copy literals ────────────────────────────────────────────────────
        for (uint i = 0u; i < lit_len && dp < dst_limit && sp < src_end; i++) {
            dst_write(dp, src_byte(sp));
            dp += 1u;
            sp += 1u;
        }

        // End-of-block: last sequence has no match section.
        if (sp >= src_end) break;

        // ── Match offset (little-endian u16) ─────────────────────────────────
        uint offset = src_byte(sp) | (src_byte(sp + 1u) << 8u);
        sp += 2u;

        if (offset == 0u) break; // corrupt block — defensive exit

        // ── Match length (minimum 4 bytes) ────────────────────────────────────
        uint match_len = (token & 15u) + 4u;
        if ((token & 15u) == 15u) {
            uint extra;
            do {
                extra = src_byte(sp);
                sp   += 1u;
                match_len += extra;
            } while (extra == 255u && sp < src_end);
        }

        // ── Copy match (byte-by-byte for overlap correctness) ─────────────────
        uint match_pos = dp - offset;
        for (uint i = 0u; i < match_len && dp < dst_limit; i++) {
            dst_write(dp, dst_byte(match_pos + i));
            dp += 1u;
        }
    }
}
