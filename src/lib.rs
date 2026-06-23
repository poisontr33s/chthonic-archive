#![allow(unsafe_op_in_unsafe_fn)]
// @SID: CRATE_LIB_V1
// Library target — exposes render and data modules to binaries in src/bin/.
// main.rs continues to have its own `mod render` for the renderer binary;
// this lib target lets zodiac-query and any future bins share the same modules.
pub mod data;
pub mod render;
