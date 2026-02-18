#![allow(clippy::missing_const_for_fn)]

pub const SYNAPSE_MAGIC: [u8; 8] = *b"CHTSYN02";
pub const SLOT_MAGIC: u32 = 0x5359_4E43; // "SYNC"
pub const SLOT_VERSION: u16 = 1;

pub const GEO_BG_RGB: [f32; 3] = [0.019_607_844, 0.019_607_844, 0.019_607_844]; // #050505
pub const GEO_SAFFRON_RGB: [f32; 3] = [0.956_862_75, 0.768_627_46, 0.188_235_3]; // #F4C430

#[repr(C)]
#[derive(Clone, Copy, Debug, Default)]
pub struct SedimentSlotHeader {
    pub magic: u32,
    pub version: u16,
    pub flags: u16,
    pub vertex_count: u32,
    pub layer_count: u32,
    pub file_count: u32,
    pub chunk_index: u32,
    pub total_chunks: u32,
    pub compute_time_ms: u64,
    pub backend_code: u32,
    pub reserved: u32,
}

#[repr(C)]
#[derive(Clone, Copy, Debug, Default)]
pub struct PackedSedimentVertex {
    pub x: f32,
    pub y: f32,
    pub z: f32,
    pub radius: f32,
    pub r: f32,
    pub g: f32,
    pub b: f32,
    pub alpha: f32,
}

pub const fn slot_header_bytes() -> usize {
    std::mem::size_of::<SedimentSlotHeader>()
}

pub const fn vertex_stride_bytes() -> usize {
    std::mem::size_of::<PackedSedimentVertex>()
}
