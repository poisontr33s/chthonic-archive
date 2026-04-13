// Runestone Execution Model — Tier 2: Granite
//
// Phase 2 target. This module will contain the GPU-accelerated binary stone
// format (.runestone), compiled from cold NDJSON archives via `ash` (Vulkan)
// and `gpu-allocator`.
//
// Design notes for Phase 2 implementor:
//
// 1. Input:  `YYYY-MM-DD.cold.ndjson.gz` (verified, from cold::forge)
// 2. Output: `.chthonic/stones/YYYY-MM-DD.runestone` (binary, GPU-indexed)
//
// 3. The `.runestone` format should contain:
//    - A fixed-size header with magic bytes, version, event count, and
//      offset table pointer.
//    - A columnar event table (type, kind, at, p stored as fixed-width
//      columns for GPU-friendly access patterns).
//    - A variable-length string pool for msg/file/data payloads.
//    - An optional GPU-side index (sorted by timestamp) for O(log n)
//      range queries on the device.
//
// 4. Dependencies to add when implementing:
//    - ash = "0.38"         (Vulkan bindings)
//    - gpu-allocator = "0.27" (VMA-style memory management)
//
// 5. The `cold.rs` module already validates data before archiving, so the
//    granite path can trust cold input and focus on binary layout + GPU
//    upload.
//
// 6. Keep CPU fallback: if no Vulkan device is available, the granite
//    module should emit the binary format without GPU involvement (pure
//    CPU packing). Feature-gate GPU behind `#[cfg(feature = "gpu")]`.

use anyhow::Result;

/// Compile a cold archive into a `.runestone` binary stone.
///
/// Phase 2 stub — returns an error indicating the feature is not yet available.
pub fn compile(_trail_dir: &std::path::Path, _date: &str) -> Result<()> {
    anyhow::bail!("granite (Tier 2) is not yet implemented — Phase 2 target");
}

/// Query a `.runestone` binary stone.
///
/// Phase 2 stub.
pub fn query(_stone_path: &std::path::Path) -> Result<()> {
    anyhow::bail!("granite (Tier 2) is not yet implemented — Phase 2 target");
}
