use std::mem::size_of;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Mutex;
use std::time::{Duration, Instant};

use napi::bindgen_prelude::{Buffer, Result};
use napi_derive::napi;
use shared_memory::{Shmem, ShmemConf};

const SYNAPSE_MAGIC: [u8; 8] = *b"CHTSYN02";
const SLOT_MAGIC: u32 = 0x5359_4E43; // "SYNC"

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

struct ReaderState {
    shmem: Shmem,
    last_notify_counter: u64,
    #[cfg(windows)]
    event_handle: windows_sys::Win32::Foundation::HANDLE,
}

impl ReaderState {
    fn header_ref(&self) -> anyhow::Result<&SynapseHeader> {
        let header = unsafe { &*(self.shmem.as_ptr() as *const SynapseHeader) };
        if header.magic != SYNAPSE_MAGIC {
            return Err(anyhow::anyhow!("invalid synapse header magic"));
        }
        Ok(header)
    }
}

impl Drop for ReaderState {
    fn drop(&mut self) {
        #[cfg(windows)]
        unsafe {
            if self.event_handle != 0 {
                windows_sys::Win32::Foundation::CloseHandle(self.event_handle);
            }
        }
    }
}

#[napi]
pub struct SynapseReader {
    inner: Mutex<ReaderState>,
}

#[napi]
impl SynapseReader {
    #[napi(constructor)]
    pub fn new(shm_id: String, event_name: Option<String>) -> Result<Self> {
        let shmem = ShmemConf::new()
            .os_id(shm_id)
            .open()
            .map_err(to_napi_error)?;

        let header = unsafe { &*(shmem.as_ptr() as *const SynapseHeader) };
        if header.magic != SYNAPSE_MAGIC {
            return Err(to_napi_error(anyhow::anyhow!("synapse magic mismatch")));
        }

        #[cfg(windows)]
        let event_handle = open_signal_event(event_name.as_deref())?;

        let state = ReaderState {
            shmem,
            last_notify_counter: header.notify_counter.load(Ordering::Acquire),
            #[cfg(windows)]
            event_handle,
        };

        Ok(Self {
            inner: Mutex::new(state),
        })
    }

    #[napi]
    pub fn wait_for_signal(&self, timeout_ms: u32) -> Result<bool> {
        let mut guard = self
            .inner
            .lock()
            .map_err(|_| napi::Error::from_reason("synapse reader lock poisoned"))?;

        #[cfg(windows)]
        {
            if guard.event_handle != 0 {
                let status = unsafe {
                    windows_sys::Win32::System::Threading::WaitForSingleObject(
                        guard.event_handle,
                        timeout_ms,
                    )
                };
                return Ok(status == windows_sys::Win32::Foundation::WAIT_OBJECT_0);
            }
        }

        let deadline = Instant::now() + Duration::from_millis(timeout_ms as u64);
        loop {
            let header = guard.header_ref().map_err(to_napi_error)?;
            let current = header.notify_counter.load(Ordering::Acquire);
            if current != guard.last_notify_counter {
                guard.last_notify_counter = current;
                return Ok(true);
            }
            if Instant::now() >= deadline {
                return Ok(false);
            }
            std::thread::sleep(Duration::from_millis(2));
        }
    }

    #[napi]
    pub fn read_chunk(&self) -> Result<Option<Buffer>> {
        let guard = self
            .inner
            .lock()
            .map_err(|_| napi::Error::from_reason("synapse reader lock poisoned"))?;
        let header = guard.header_ref().map_err(to_napi_error)?;

        let write = header.write_index.load(Ordering::Acquire);
        let read = header.read_index.load(Ordering::Acquire);
        if read >= write {
            return Ok(None);
        }

        let slot_index = (read % header.slot_capacity as u64) as usize;
        let slot_offset = size_of::<SynapseHeader>() + (slot_index * header.slot_stride as usize);
        let slot_ptr = unsafe { guard.shmem.as_ptr().add(slot_offset) };

        let slot_header = unsafe { &*(slot_ptr as *const SlotHeader) };
        if slot_header.magic != SLOT_MAGIC {
            return Ok(None);
        }

        let max_vertices = header.vertex_capacity as usize;
        let vertex_count = (slot_header.vertex_count as usize).min(max_vertices);
        let payload_bytes = size_of::<SlotHeader>() + (vertex_count * size_of::<PackedVertex>());

        let src = unsafe { std::slice::from_raw_parts(slot_ptr as *const u8, payload_bytes) };
        let out = src.to_vec();

        header.read_index.store(read + 1, Ordering::Release);
        Ok(Some(Buffer::from(out)))
    }
}

#[cfg(windows)]
fn open_signal_event(event_name: Option<&str>) -> Result<windows_sys::Win32::Foundation::HANDLE> {
    use windows_sys::Win32::System::Threading::{OpenEventW, SYNCHRONIZE};
    let Some(event_name) = event_name else {
        return Ok(0);
    };

    let mut wide: Vec<u16> = event_name.encode_utf16().collect();
    wide.push(0);

    let handle = unsafe { OpenEventW(SYNCHRONIZE, 0, wide.as_ptr()) };
    if handle == 0 {
        return Err(napi::Error::from_reason("failed to open synapse signal event"));
    }
    Ok(handle)
}

fn to_napi_error(error: impl std::fmt::Display) -> napi::Error {
    napi::Error::from_reason(error.to_string())
}
