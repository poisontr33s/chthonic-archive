use std::mem::size_of;
use std::sync::atomic::{fence, AtomicU64, Ordering};
use std::time::{SystemTime, UNIX_EPOCH};

use anyhow::{anyhow, Context, Result};
use shared_memory::{Shmem, ShmemConf};

use crate::types::{SedimentResult, SedimentVertex};

const SYNAPSE_MAGIC: [u8; 8] = *b"CHTSYN02";
const SLOT_MAGIC: u32 = 0x5359_4E43; // "SYNC"
const SLOT_VERSION: u16 = 1;

#[repr(C)]
struct SynapseHeader {
    magic: [u8; 8],
    version: u32,
    slot_capacity: u32,
    vertex_capacity: u32,
    slot_stride: u32,
    high_water_mark: u32,
    write_index: AtomicU64,
    read_index: AtomicU64,
    dropped_frames: AtomicU64,
    notify_counter: AtomicU64,
}

#[repr(C)]
#[derive(Clone, Copy)]
struct SlotHeader {
    magic: u32,
    version: u16,
    flags: u16,
    vertex_count: u32,
    layer_count: u32,
    file_count: u32,
    chunk_index: u32,
    total_chunks: u32,
    compute_time_ms: u64,
    backend_code: u32,
    reserved: u32,
}

#[repr(C)]
#[derive(Clone, Copy)]
struct PackedVertex {
    x: f32,
    y: f32,
    z: f32,
    radius: f32,
    r: f32,
    g: f32,
    b: f32,
    alpha: f32,
}

#[derive(Debug, Clone, serde::Serialize)]
pub struct SynapseDescriptor {
    pub status: &'static str,
    pub mode: &'static str,
    pub shm_id: String,
    pub event_name: Option<String>,
    pub slot_capacity: u32,
    pub vertex_capacity: u32,
    pub slot_stride: u32,
    pub high_water_mark: u32,
}

#[derive(Debug, Clone, serde::Serialize)]
pub struct SynapsePublishSummary {
    pub total_chunks: u32,
    pub chunks_written: u32,
    pub dropped_chunks: u32,
    pub queue_depth: u64,
}

pub struct SynapseWriter {
    shmem: Shmem,
    descriptor: SynapseDescriptor,
    #[cfg(windows)]
    event_handle: windows_sys::Win32::Foundation::HANDLE,
}

impl SynapseWriter {
    pub fn create() -> Result<Self> {
        let slot_capacity: u32 = 64;
        let vertex_capacity: u32 = 384;
        let slot_stride = (size_of::<SlotHeader>() + (vertex_capacity as usize * size_of::<PackedVertex>())) as u32;
        let total_size = size_of::<SynapseHeader>() + (slot_capacity as usize * slot_stride as usize);

        let tag = unique_tag();
        let shm_id = format!("chthonic.synapse.{tag}");

        let shmem = ShmemConf::new()
            .size(total_size)
            .os_id(shm_id.clone())
            .create()
            .context("failed to create shared memory segment")?;

        unsafe {
            std::ptr::write_bytes(shmem.as_ptr(), 0, total_size);
            let header = &mut *(shmem.as_ptr() as *mut SynapseHeader);
            header.magic = SYNAPSE_MAGIC;
            header.version = 1;
            header.slot_capacity = slot_capacity;
            header.vertex_capacity = vertex_capacity;
            header.slot_stride = slot_stride;
            header.high_water_mark = 24;
            header.write_index.store(0, Ordering::Release);
            header.read_index.store(0, Ordering::Release);
            header.dropped_frames.store(0, Ordering::Release);
            header.notify_counter.store(0, Ordering::Release);
        }

        #[cfg(windows)]
        let (event_name, event_handle) = create_signal_event(&tag)?;
        #[cfg(not(windows))]
        let event_name = None;

        let descriptor = SynapseDescriptor {
            status: "ready",
            mode: "shared_memory",
            shm_id,
            event_name,
            slot_capacity,
            vertex_capacity,
            slot_stride,
            high_water_mark: 24,
        };

        Ok(Self {
            shmem,
            descriptor,
            #[cfg(windows)]
            event_handle,
        })
    }

    pub fn descriptor(&self) -> &SynapseDescriptor {
        &self.descriptor
    }

    pub fn publish_result(&mut self, result: &SedimentResult, requested_chunk_size: u32) -> Result<SynapsePublishSummary> {
        let chunk_size = requested_chunk_size
            .max(1)
            .min(self.descriptor.vertex_capacity) as usize;
        let total_chunks = if result.vertices.is_empty() {
            0
        } else {
            ((result.vertices.len() + chunk_size - 1) / chunk_size) as u32
        };

        let mut chunks_written = 0u32;
        let mut dropped_chunks = 0u32;

        for (chunk_index, chunk) in result.vertices.chunks(chunk_size).enumerate() {
            if self.try_push_chunk(
                chunk_index as u32,
                total_chunks,
                result.layer_count,
                result.file_count,
                result.compute_time_ms,
                backend_code(result.backend),
                chunk,
            )? {
                chunks_written += 1;
            } else {
                dropped_chunks += 1;
            }
        }

        let header = self.header_ref();
        let write = header.write_index.load(Ordering::Acquire);
        let read = header.read_index.load(Ordering::Acquire);

        Ok(SynapsePublishSummary {
            total_chunks,
            chunks_written,
            dropped_chunks,
            queue_depth: write.saturating_sub(read),
        })
    }

    fn try_push_chunk(
        &mut self,
        chunk_index: u32,
        total_chunks: u32,
        layer_count: u32,
        file_count: u32,
        compute_time_ms: u64,
        backend_code: u32,
        vertices: &[SedimentVertex],
    ) -> Result<bool> {
        let write = self.header_ref().write_index.load(Ordering::Acquire);
        let read = self.header_ref().read_index.load(Ordering::Acquire);

        if write.saturating_sub(read) >= self.descriptor.slot_capacity as u64 {
            self.header_ref().dropped_frames.fetch_add(1, Ordering::AcqRel);
            return Ok(false);
        }

        let slot_index = (write % self.descriptor.slot_capacity as u64) as u32;
        unsafe {
            self.write_slot(
                slot_index,
                SlotHeader {
                    magic: SLOT_MAGIC,
                    version: SLOT_VERSION,
                    flags: if chunk_index + 1 == total_chunks { 1 } else { 0 },
                    vertex_count: vertices.len() as u32,
                    layer_count,
                    file_count,
                    chunk_index,
                    total_chunks,
                    compute_time_ms,
                    backend_code,
                    reserved: 0,
                },
                vertices,
            )?;
        }

        fence(Ordering::Release);
        self.header_ref().write_index.store(write + 1, Ordering::Release);
        self.header_ref().notify_counter.fetch_add(1, Ordering::AcqRel);

        let depth = (write + 1).saturating_sub(read);
        if depth >= self.descriptor.high_water_mark as u64 {
            self.signal();
        }

        Ok(true)
    }

    unsafe fn write_slot(
        &mut self,
        slot_index: u32,
        slot_header: SlotHeader,
        vertices: &[SedimentVertex],
    ) -> Result<()> {
        if vertices.len() > self.descriptor.vertex_capacity as usize {
            return Err(anyhow!(
                "chunk vertex count {} exceeds capacity {}",
                vertices.len(),
                self.descriptor.vertex_capacity
            ));
        }

        let slot_ptr = self.slot_ptr(slot_index);
        let header_ptr = slot_ptr as *mut SlotHeader;
        std::ptr::write(header_ptr, slot_header);

        let vertex_ptr = slot_ptr.add(size_of::<SlotHeader>()) as *mut PackedVertex;
        for (idx, vertex) in vertices.iter().enumerate() {
            std::ptr::write(
                vertex_ptr.add(idx),
                PackedVertex {
                    x: vertex.x,
                    y: vertex.y,
                    z: vertex.z,
                    radius: vertex.radius,
                    r: vertex.r,
                    g: vertex.g,
                    b: vertex.b,
                    alpha: vertex.alpha,
                },
            );
        }

        Ok(())
    }

    fn header_ref(&self) -> &SynapseHeader {
        unsafe { &*(self.shmem.as_ptr() as *const SynapseHeader) }
    }

    unsafe fn slot_ptr(&self, slot_index: u32) -> *mut u8 {
        let base = self.shmem.as_ptr();
        base.add(size_of::<SynapseHeader>() + slot_index as usize * self.descriptor.slot_stride as usize)
    }

    fn signal(&self) {
        #[cfg(windows)]
        unsafe {
            let _ = windows_sys::Win32::System::Threading::SetEvent(self.event_handle);
        }
    }
}

impl Drop for SynapseWriter {
    fn drop(&mut self) {
        #[cfg(windows)]
        unsafe {
            if !self.event_handle.is_null() {
                windows_sys::Win32::Foundation::CloseHandle(self.event_handle);
            }
        }
    }
}

fn backend_code(backend: &str) -> u32 {
    match backend {
        "vulkan" => 1,
        "cpu-fallback" => 2,
        "cpu-only" => 3,
        "empty" => 4,
        _ => 255,
    }
}

fn unique_tag() -> String {
    let nanos = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_nanos())
        .unwrap_or(0);
    format!("{}-{nanos}", std::process::id())
}

#[cfg(windows)]
fn create_signal_event(tag: &str) -> Result<(Option<String>, windows_sys::Win32::Foundation::HANDLE)> {
    use windows_sys::Win32::System::Threading::CreateEventW;

    let event_name = format!("Local\\chthonic.synapse.{tag}.signal");
    let mut wide: Vec<u16> = event_name.encode_utf16().collect();
    wide.push(0);

    let handle = unsafe {
        CreateEventW(
            std::ptr::null_mut(),
            0,
            0,
            wide.as_ptr(),
        )
    };

    if handle.is_null() {
        return Err(anyhow!("failed to create signal event"));
    }

    Ok((Some(event_name), handle))
}
