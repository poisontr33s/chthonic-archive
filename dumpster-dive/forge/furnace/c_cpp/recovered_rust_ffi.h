/* @SID: FORGE_RUST_FFI_HEADER_V1 */
/* Purpose: C header derived from recovered Rust struct signatures. */
#ifndef CHTHONIC_ARCHIVE_RECOVERED_RUST_FFI_H
#define CHTHONIC_ARCHIVE_RECOVERED_RUST_FFI_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

typedef struct SlotHeader {
    uint32_t magic;
    uint16_t version;
    uint16_t flags;
    uint32_t vertex_count;
    uint32_t layer_count;
    uint32_t file_count;
    uint32_t chunk_index;
    uint32_t total_chunks;
    uint64_t compute_time_ms;
    uint32_t backend_code;
    uint32_t reserved;
} SlotHeader;

typedef struct PackedVertex {
    float x;
    float y;
    float z;
    float radius;
    float r;
    float g;
    float b;
    float alpha;
} PackedVertex;

typedef struct DevKitReport {
    uint32_t msys2_home;
    uint32_t ucrt64_bin;
    uint32_t perl_path;
    uint32_t cc;
    uint32_t cxx;
    uint32_t env_vars;
    uint32_t path_prepend;
} DevKitReport;

#endif
