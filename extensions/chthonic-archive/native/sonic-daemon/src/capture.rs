// @SID: SONIC_DAEMON_CAPTURE_V1
//! WASAPI loopback capture → rolling RMS + spectral window → atomic JSON snapshot.
//!
//! Two capture modes (SONIC_CAPTURE_MODE), both feeding one snapshot loop:
//!
//!   device (default) — shared loopback on a render endpoint. Tries the default endpoint first,
//!     then any other active render endpoint. Render device + `Direction::Capture` +
//!     `PollingShared` → AUDCLNT_STREAMFLAGS_LOOPBACK. Captures all system audio.
//!   process — per-process loopback via AUDCLNT_ACTIVATION_TYPE_PROCESS_LOOPBACK
//!     (`new_application_loopback_client`, `EventsShared`). Captures one process tree's render
//!     stream in isolation. Target via SONIC_PID (+ SONIC_INCLUDE_TREE).
//!
//! cpal's loopback is disabled upstream (cpal #476); event-driven device loopback is rejected,
//! so device mode polls. Process loopback follows Microsoft's ApplicationLoopback sample (events).
//!
//! Exclusive mode: an endpoint held in WASAPI exclusive mode (bit-perfect/lossless, e.g. Spotify
//! "exclusive mode") is uncapturable by ANY loopback — exclusive bypasses the shared engine by
//! design. open fails with AUDCLNT_E_DEVICE_IN_USE → we write a `blocked` window and retry.
//!
//! SONIC_DIAG=1 → one-shot: list render endpoints + their audio sessions (pid+state), then exit.

use std::collections::VecDeque;
use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};

use anyhow::{anyhow, Context, Result};
use rustfft::{num_complex::Complex, FftPlanner};
use serde::{Deserialize, Serialize};
use wasapi::{
    initialize_mta, AudioCaptureClient, AudioClient, Device, DeviceEnumerator, Direction, Handle,
    SampleType, StreamMode, WaveFormat,
};

const SCHEMA: &str = "sonic_window/v1";
/// FFT size for spectral features (centroid/flatness). ~85ms at 48kHz.
const FFT_SIZE: usize = 4096;
/// Below this RMS the window is reported silent.
const SILENCE_RMS: f32 = 1.0e-5;
/// dBFS floor for the energy mapping; quieter than this maps to 0.
const DB_FLOOR: f32 = -60.0;
/// Process-loopback capture format (no mixformat available for the virtual device).
const PROC_SAMPLE_RATE: u32 = 48_000;
const PROC_CHANNELS: usize = 2;

pub struct CaptureConfig {
    pub enabled: bool,
    pub window_secs: f32,
    pub snapshot: Duration,
    pub out_path: PathBuf,
}

impl CaptureConfig {
    pub fn from_env(workspace: PathBuf) -> Self {
        let enabled = std::env::var("SONIC_CAPTURE")
            .map(|v| {
                !matches!(
                    v.trim().to_ascii_lowercase().as_str(),
                    "off" | "0" | "false" | "no"
                )
            })
            .unwrap_or(true);
        let window_secs = env_f32("SONIC_WINDOW_SECS", 5.0).max(0.5);
        let snapshot_ms = env_u64("SONIC_SNAPSHOT_MS", 1000).max(100);
        let out_path = workspace.join("manifest").join("sonic_window.json");
        Self {
            enabled,
            window_secs,
            snapshot: Duration::from_millis(snapshot_ms),
            out_path,
        }
    }

    pub fn write_disabled(&self) -> Result<()> {
        write_atomic(
            &self.out_path,
            &SonicWindow {
                schema: SCHEMA,
                source: "disabled",
                energy: 0.0,
                silent: true,
                captured_at_epoch_ms: now_ms(),
                window_secs: self.window_secs,
                sample_rate: 0,
                brightness: None,
                tonality: None,
                valence_proxy: None,
                voiceness: None,
                temporal: None,
            },
        )
    }
}

#[derive(Serialize, Clone)]
struct SonicWindow {
    schema: &'static str,
    /// "loopback" | "blocked" | "disabled". Spotify fusion happens MCP-side, not here.
    source: &'static str,
    /// 0..1 perceptual loudness over the rolling window.
    energy: f32,
    silent: bool,
    captured_at_epoch_ms: u64,
    window_secs: f32,
    sample_rate: u32,
    /// 0..1 spectral centroid (log-mapped 200..8000 Hz). Present only when not silent.
    #[serde(skip_serializing_if = "Option::is_none")]
    brightness: Option<f32>,
    /// 0..1 tonality (1 - spectral flatness). Low = percussive/noisy.
    #[serde(skip_serializing_if = "Option::is_none")]
    tonality: Option<f32>,
    /// 0..1 valence proxy (brightness × tonality blend). Heuristic — labelled proxy.
    #[serde(skip_serializing_if = "Option::is_none")]
    valence_proxy: Option<f32>,
    /// 0..1 voice/words-presence proxy (2–8 Hz syllable-rate amplitude modulation). High =
    /// likely vocals/speech/podcast; low = wordless/instrumental. Rough proxy, low confidence —
    /// the real version is a small VAD model on the GPU.
    #[serde(skip_serializing_if = "Option::is_none")]
    voiceness: Option<f32>,
    /// The temporal sense: trends, phase, events, narrative — the ARC, not the frame.
    #[serde(skip_serializing_if = "Option::is_none")]
    temporal: Option<Temporal>,
}

/// Fixed-capacity mono ring of the most recent samples.
struct Ring {
    buf: Vec<f32>,
    pos: usize,
    filled: usize,
    capacity: usize,
}

impl Ring {
    fn new(capacity: usize) -> Self {
        let capacity = capacity.max(1);
        Self {
            buf: vec![0.0; capacity],
            pos: 0,
            filled: 0,
            capacity,
        }
    }

    fn push(&mut self, sample: f32) {
        self.buf[self.pos] = sample;
        self.pos = (self.pos + 1) % self.capacity;
        if self.filled < self.capacity {
            self.filled += 1;
        }
    }

    fn rms(&self) -> f32 {
        if self.filled == 0 {
            return 0.0;
        }
        let sum_sq: f32 = self.buf.iter().take(self.filled).map(|x| x * x).sum();
        (sum_sq / self.filled as f32).sqrt()
    }

    /// The most recent `n` samples in time order (oldest → newest).
    fn latest(&self, n: usize) -> Vec<f32> {
        let n = n.min(self.filled);
        let start = (self.pos + self.capacity - n) % self.capacity;
        (0..n).map(|i| self.buf[(start + i) % self.capacity]).collect()
    }
}

/// A live loopback capture: the audio client (kept alive), its capture client, and format.
struct OpenLoopback {
    audio_client: AudioClient,
    capture_client: AudioCaptureClient,
    sample_rate: u32,
    channels: usize,
    blockalign: usize,
    poll: Duration,
    source_label: String,
    /// Event-driven capture (process loopback) carries a wait handle; polling (device) is None.
    event: Option<Handle>,
}

pub fn run_capture(cfg: CaptureConfig, stop: Arc<AtomicBool>) -> Result<()> {
    let _ = initialize_mta(); // COM (MTA) for this thread

    let process_mode = std::env::var("SONIC_CAPTURE_MODE")
        .map(|m| m.trim().eq_ignore_ascii_case("process"))
        .unwrap_or(false);
    if process_mode && process_pid().is_none() {
        return Err(anyhow!(
            "SONIC_CAPTURE_MODE=process requires SONIC_PID (numeric target process id)"
        ));
    }

    // Singleton lifecycle (SONIC_SINGLETON=1): one daemon serves all MCP sessions. Claim the
    // lock first — stand down if a live peer already serves — then start the heartbeat +
    // reader-idle watcher. `_singleton_guard` releases the lock and joins the watcher on every
    // exit path. With the flag off this is skipped entirely (stdin-reap / Ctrl+C as before).
    let singleton = env_bool("SONIC_SINGLETON", false);
    let my_pid = std::process::id();
    let _singleton_guard = if singleton {
        if !singleton_claim(&cfg, &stop, my_pid) {
            return Ok(());
        }
        Some(SingletonGuard {
            stop: stop.clone(),
            lifecycle: Some(spawn_singleton_lifecycle(&cfg, stop.clone(), my_pid)),
            lock: lock_path(&cfg),
            pid: my_pid,
        })
    } else {
        None
    };

    // Open with retry: an endpoint can be transiently exclusive-locked (bit-perfect playback).
    // Write a `blocked` window and wait it out rather than dying.
    let OpenLoopback {
        audio_client,
        capture_client,
        sample_rate,
        channels,
        blockalign,
        poll,
        source_label,
        event,
    } = loop {
        if stop.load(Ordering::Acquire) {
            return Ok(());
        }
        let attempt = if process_mode {
            open_process()
        } else {
            open_device()
        };
        match attempt {
            Ok(o) => break o,
            Err(e) => {
                eprintln!("[sonic] capture unavailable: {e} — retrying in 3s");
                let _ = write_atomic(&cfg.out_path, &blocked_window(cfg.window_secs));
                sleep_with_stop(Duration::from_secs(3), &stop);
            }
        }
    };

    eprintln!(
        "[sonic] capturing {source_label}: {sample_rate} Hz · {channels} ch · f32 · window {}s · poll {}ms → {}",
        cfg.window_secs,
        poll.as_millis(),
        cfg.out_path.display()
    );

    let capacity = (cfg.window_secs * sample_rate as f32) as usize;
    let mut ring = Ring::new(capacity);
    let mut byte_queue: VecDeque<u8> = VecDeque::new();

    // Initial snapshot so the window file exists immediately.
    let _ = write_atomic(&cfg.out_path, &window(SCHEMA, 0.0, true, cfg.window_secs, sample_rate));

    let mut last_snapshot = Instant::now();
    let mut frames_since_snapshot: u64 = 0;
    // Calibration persists across restarts: load the running baseline so "your norm" keeps
    // deepening with accumulated intake instead of resetting each daemon start.
    let mut temporal = TemporalModel::with_baseline(manifest_dir(&cfg).join("sonic_baseline.json"));
    let mut history = HistoryLake::from_env(&cfg);

    while !stop.load(Ordering::Acquire) {
        // Pace the loop: event-driven (process loopback) waits for the capture event;
        // polling (device loopback) sleeps near the device period.
        match &event {
            Some(ev) => {
                let _ = ev.wait_for_event(200); // Err = timeout (silence); harmless
            }
            None => std::thread::sleep(poll),
        }

        // Drain whatever loopback packets are queued into the byte buffer.
        if let Err(e) = capture_client.read_from_device_to_deque(&mut byte_queue) {
            eprintln!("[sonic] read error: {e:?}");
        }

        // Convert whole interleaved f32 frames → mono → ring.
        while byte_queue.len() >= blockalign {
            let mut acc = 0.0f32;
            for _ in 0..channels {
                let b = [
                    byte_queue.pop_front().unwrap(),
                    byte_queue.pop_front().unwrap(),
                    byte_queue.pop_front().unwrap(),
                    byte_queue.pop_front().unwrap(),
                ];
                acc += f32::from_le_bytes(b);
            }
            ring.push(acc / channels as f32);
            frames_since_snapshot += 1;
        }

        if last_snapshot.elapsed() >= cfg.snapshot {
            let now = now_ms();
            // No new frames this interval → genuine silence (no loopback packets), not loud-stale.
            let (energy, silent) = if frames_since_snapshot == 0 {
                (0.0, true)
            } else {
                energy_from_rms(ring.rms())
            };
            let (spec, voice) = if silent {
                (None, None)
            } else {
                // ~2s of samples: spectral uses the tail FFT_SIZE; voiceness needs the longer
                // span for syllable-rate (2–8 Hz) envelope modulation.
                let recent = ring.latest((sample_rate as usize) * 2);
                (spectral(&recent, sample_rate), voiceness(&recent, sample_rate))
            };
            let brightness = spec.map(|s| s.0).unwrap_or(0.0);
            // Feed the temporal sense: it accumulates the arc across turn-gaps the agent can't see.
            let temporal_block = temporal.observe(now, energy, brightness, silent);
            let phase = temporal_block.phase.character.clone();
            let snap = SonicWindow {
                schema: SCHEMA,
                source: "loopback",
                energy,
                silent,
                captured_at_epoch_ms: now,
                window_secs: cfg.window_secs,
                sample_rate,
                brightness: spec.map(|s| s.0),
                tonality: spec.map(|s| s.1),
                valence_proxy: spec.map(|s| s.2),
                voiceness: voice,
                temporal: Some(temporal_block),
            };
            if let Err(e) = write_atomic(&cfg.out_path, &snap) {
                eprintln!("[sonic] snapshot write failed: {e}");
            }
            // The history lake — persist the per-second stream we'd otherwise overwrite. Scalars
            // only (privacy), silence-coalesced, size-capped. This is the substrate a future
            // encoder/embedder learns from; without it the dense intake is lost every tick.
            history.append(now, energy, silent, spec, voice, &phase);
            frames_since_snapshot = 0;
            last_snapshot = Instant::now();
        }
    }

    let _ = audio_client.stop_stream();
    temporal.save_baseline(); // persist the final baseline on clean shutdown
    eprintln!("[sonic] capture stopped");
    Ok(())
}

// ── Singleton lifecycle (SONIC_SINGLETON=1) ────────────────────────────────────
// One daemon serves N MCP sessions. The first to claim `sonic_daemon.lock` runs; a later
// daemon that sees a fresh lock beat stands down. MCP readers touch `sonic_daemon.readers`
// while alive; when that goes stale past the idle window, the singleton self-exits. Each file
// has a single writer domain (daemon owns .lock, readers own .readers) → no write contention.
// With SONIC_SINGLETON unset, none of this engages.

/// How fresh a lock beat must be for a peer daemon to count as alive.
const PEER_FRESH_MS: u64 = 4_000;
/// Lock-beat cadence (also the reader-idle poll cadence).
const SINGLETON_BEAT_MS: u64 = 1_000;

#[derive(Serialize, Deserialize)]
struct LockFile {
    pid: u32,
    beat_ms: u64,
}

fn manifest_dir(cfg: &CaptureConfig) -> PathBuf {
    cfg.out_path
        .parent()
        .map(Path::to_path_buf)
        .unwrap_or_else(|| PathBuf::from("manifest"))
}
fn lock_path(cfg: &CaptureConfig) -> PathBuf {
    manifest_dir(cfg).join("sonic_daemon.lock")
}
fn readers_path(cfg: &CaptureConfig) -> PathBuf {
    manifest_dir(cfg).join("sonic_daemon.readers")
}

fn read_lock(path: &Path) -> Option<LockFile> {
    serde_json::from_str(&fs::read_to_string(path).ok()?).ok()
}

fn write_lock(path: &Path, pid: u32, beat_ms: u64) {
    if let Some(dir) = path.parent() {
        let _ = fs::create_dir_all(dir);
    }
    let Ok(body) = serde_json::to_string(&LockFile { pid, beat_ms }) else {
        return;
    };
    let tmp = path.with_extension("lock.tmp");
    if fs::write(&tmp, body).is_ok() {
        let _ = fs::rename(&tmp, path);
    }
}

fn clear_lock_if_ours(path: &Path, my_pid: u32) {
    if matches!(read_lock(path), Some(l) if l.pid == my_pid) {
        let _ = fs::remove_file(path);
    }
}

/// Milliseconds since the readers file was last touched; `u64::MAX` if it's absent.
fn readers_idle_ms(path: &Path) -> u64 {
    match fs::metadata(path).and_then(|m| m.modified()) {
        Ok(mtime) => SystemTime::now()
            .duration_since(mtime)
            .map(|d| d.as_millis() as u64)
            .unwrap_or(0),
        Err(_) => u64::MAX,
    }
}

/// Claim the singleton lock. `true` → we own it (capture). `false` → a live peer already
/// serves; the caller exits cleanly. The settle + re-read resolves a simultaneous-start race
/// down to one winner (last writer) with no OS-level mutex.
fn singleton_claim(cfg: &CaptureConfig, stop: &Arc<AtomicBool>, my_pid: u32) -> bool {
    let lock = lock_path(cfg);
    if let Some(existing) = read_lock(&lock) {
        if now_ms().saturating_sub(existing.beat_ms) < PEER_FRESH_MS {
            eprintln!(
                "[sonic] singleton: live daemon (pid {}) already serving — exiting",
                existing.pid
            );
            return false;
        }
    }
    write_lock(&lock, my_pid, now_ms());
    sleep_with_stop(Duration::from_millis(300), stop);
    if let Some(after) = read_lock(&lock) {
        if after.pid != my_pid && now_ms().saturating_sub(after.beat_ms) < PEER_FRESH_MS {
            eprintln!("[sonic] singleton: lost claim race to pid {} — exiting", after.pid);
            return false;
        }
    }
    write_lock(&lock, my_pid, now_ms());
    true
}

/// Heartbeat + reader-idle watcher. Keeps the lock beat fresh and flips `stop` once no MCP
/// reader has touched the readers file within the idle window. A startup grace covers the gap
/// before the first reader heartbeat and a slow device open.
fn spawn_singleton_lifecycle(
    cfg: &CaptureConfig,
    stop: Arc<AtomicBool>,
    my_pid: u32,
) -> std::thread::JoinHandle<()> {
    let lock = lock_path(cfg);
    let readers = readers_path(cfg);
    let idle_ms = env_u64("SONIC_SINGLETON_IDLE_MS", 45_000);
    let grace_ms = env_u64("SONIC_SINGLETON_GRACE_MS", 15_000);
    let start_ms = now_ms();
    std::thread::spawn(move || {
        while !stop.load(Ordering::Acquire) {
            write_lock(&lock, my_pid, now_ms());
            if now_ms().saturating_sub(start_ms) > grace_ms && readers_idle_ms(&readers) > idle_ms {
                eprintln!(
                    "[sonic] singleton: no live readers within {}ms idle window — self-exiting",
                    idle_ms
                );
                stop.store(true, Ordering::Release);
                break;
            }
            sleep_with_stop(Duration::from_millis(SINGLETON_BEAT_MS), &stop);
        }
    })
}

/// RAII: on every exit path, signal stop, join the watcher, and release the lock if it's ours.
struct SingletonGuard {
    stop: Arc<AtomicBool>,
    lifecycle: Option<std::thread::JoinHandle<()>>,
    lock: PathBuf,
    pid: u32,
}
impl Drop for SingletonGuard {
    fn drop(&mut self) {
        self.stop.store(true, Ordering::Release);
        if let Some(h) = self.lifecycle.take() {
            let _ = h.join();
        }
        clear_lock_if_ours(&self.lock, self.pid);
    }
}

// ── History lake (SONIC_HISTORY; default on) ───────────────────────────────────
// Persist the per-snapshot scalar stream that the window file otherwise overwrites each tick —
// the dense intake a future encoder/embedder learns from. Privacy: derived scalars only, never
// raw audio. Silence is coalesced to a single marker per run (no 1/s "silent" spam), and the
// file is byte-capped with a single roll so it can't grow without bound.

/// One compact line of the lake. Short keys: ts(ms) · e=energy · br=brightness · to=tonality ·
/// va=valence_proxy · vo=voiceness · ph=phase character · si=silent.
#[derive(Serialize)]
struct HistoryRecord<'a> {
    ts: u64,
    e: f32,
    #[serde(skip_serializing_if = "Option::is_none")]
    br: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    to: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    va: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    vo: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    ph: Option<&'a str>,
    si: bool,
}

struct HistoryLake {
    path: PathBuf,
    enabled: bool,
    last_silent_logged: bool,
    bytes: u64,
    max_bytes: u64,
}

impl HistoryLake {
    fn from_env(cfg: &CaptureConfig) -> Self {
        let enabled = env_bool("SONIC_HISTORY", true);
        let path = manifest_dir(cfg).join("sonic_window_history.ndjson");
        // SONIC_HISTORY_MAX_BYTES wins if set (lets a test force a tiny cap); else MB.
        let max_bytes = match std::env::var("SONIC_HISTORY_MAX_BYTES").ok().and_then(|v| v.trim().parse().ok()) {
            Some(b) => b,
            None => env_u64("SONIC_HISTORY_MAX_MB", 64).max(1) * 1024 * 1024,
        };
        let bytes = fs::metadata(&path).map(|m| m.len()).unwrap_or(0);
        Self {
            path,
            enabled,
            last_silent_logged: false,
            bytes,
            max_bytes,
        }
    }

    fn append(
        &mut self,
        ts: u64,
        energy: f32,
        silent: bool,
        spec: Option<(f32, f32, f32)>,
        voice: Option<f32>,
        phase: &str,
    ) {
        if !self.enabled {
            return;
        }
        // Coalesce silence: one marker per silent run, not 1/s of "silent".
        if silent {
            if self.last_silent_logged {
                return;
            }
            self.last_silent_logged = true;
        } else {
            self.last_silent_logged = false;
        }
        let rec = HistoryRecord {
            ts,
            e: energy,
            br: spec.map(|s| s.0),
            to: spec.map(|s| s.1),
            va: spec.map(|s| s.2),
            vo: voice,
            ph: if silent { None } else { Some(phase) },
            si: silent,
        };
        let Ok(mut line) = serde_json::to_string(&rec) else {
            return;
        };
        line.push('\n');
        if let Some(dir) = self.path.parent() {
            let _ = fs::create_dir_all(dir);
        }
        if let Ok(mut f) = fs::OpenOptions::new().create(true).append(true).open(&self.path) {
            if f.write_all(line.as_bytes()).is_ok() {
                self.bytes += line.len() as u64;
            }
        }
        if self.bytes > self.max_bytes {
            self.rotate();
        }
    }

    /// Roll the lake over when it hits the cap: current → `.ndjson.1` (one previous kept), fresh start.
    fn rotate(&mut self) {
        let rolled = self.path.with_extension("ndjson.1");
        if fs::rename(&self.path, &rolled).is_ok() {
            self.bytes = 0;
        }
    }
}

// ── Process loopback (SONIC_CAPTURE_MODE=process) ──────────────────────────────

fn open_process() -> Result<OpenLoopback> {
    let pid = process_pid().ok_or_else(|| {
        anyhow!(
            "process loopback requires SONIC_PID (numeric target process id); \
             set it, or use the default device mode"
        )
    })?;
    let include_tree = env_bool("SONIC_INCLUDE_TREE", true);

    let mut audio_client =
        AudioClient::new_application_loopback_client(pid, include_tree).map_err(we)?;
    let desired = WaveFormat::new(
        32,
        32,
        &SampleType::Float,
        PROC_SAMPLE_RATE as usize,
        PROC_CHANNELS,
        None,
    );
    let blockalign = desired.get_blockalign() as usize;
    // Event-driven (like Microsoft's ApplicationLoopback sample): the process-loopback virtual
    // device only fills buffers when driven by its event. get_device_period() is non-functional
    // in process mode; the period is irrelevant.
    let mode = StreamMode::EventsShared {
        autoconvert: true,
        buffer_duration_hns: 200_000, // 20ms
    };
    audio_client
        .initialize_client(&desired, &Direction::Capture, &mode)
        .map_err(we)?;

    let event = audio_client.set_get_eventhandle().map_err(we)?;
    let capture_client = audio_client.get_audiocaptureclient().map_err(we)?;
    audio_client.start_stream().map_err(we)?;

    Ok(OpenLoopback {
        audio_client,
        capture_client,
        sample_rate: PROC_SAMPLE_RATE,
        channels: PROC_CHANNELS,
        blockalign,
        poll: Duration::from_millis(10),
        source_label: format!("process pid {pid} (tree:{include_tree})"),
        event: Some(event),
    })
}

// ── Device loopback (default) ──────────────────────────────────────────────────

fn open_device() -> Result<OpenLoopback> {
    let enumerator = DeviceEnumerator::new().map_err(we)?;
    let candidates = collect_render_devices(&enumerator);
    if candidates.is_empty() {
        return Err(anyhow!("no active render devices found"));
    }

    for device in candidates {
        let name = device
            .get_friendlyname()
            .unwrap_or_else(|_| "<unknown>".to_string());
        match try_open_device_loopback(device) {
            Ok(o) => {
                eprintln!("[sonic] loopback OK on '{}'", o.source_label);
                return Ok(o);
            }
            Err(e) => eprintln!("[sonic] loopback unavailable on '{name}': {e}"),
        }
    }
    Err(anyhow!(
        "no render device accepted shared-mode loopback — likely all held in exclusive mode"
    ))
}

fn try_open_device_loopback(device: Device) -> Result<OpenLoopback> {
    let name = device
        .get_friendlyname()
        .unwrap_or_else(|_| "<unknown>".to_string());
    let mut audio_client = device.get_iaudioclient().map_err(we)?;

    let mix = audio_client.get_mixformat().map_err(we)?;
    let sample_rate = mix.get_samplespersec();
    let channels = mix.get_nchannels() as usize;
    let desired = WaveFormat::new(32, 32, &SampleType::Float, sample_rate as usize, channels, None);
    let blockalign = desired.get_blockalign() as usize;

    let (def_period_hns, _min_period_hns) = audio_client.get_device_period().map_err(we)?;
    let mode = StreamMode::PollingShared {
        autoconvert: true,
        buffer_duration_hns: def_period_hns,
    };
    audio_client
        .initialize_client(&desired, &Direction::Capture, &mode)
        .map_err(we)?;

    let capture_client = audio_client.get_audiocaptureclient().map_err(we)?;
    audio_client.start_stream().map_err(we)?;

    let poll = Duration::from_millis((def_period_hns / 10_000).clamp(2, 20) as u64);
    Ok(OpenLoopback {
        audio_client,
        capture_client,
        sample_rate,
        channels,
        blockalign,
        poll,
        source_label: format!("device '{name}'"),
        event: None,
    })
}

/// Candidate render devices: default first, then every active render endpoint.
fn collect_render_devices(en: &DeviceEnumerator) -> Vec<Device> {
    let mut out = Vec::new();
    if let Ok(d) = en.get_default_device(&Direction::Render) {
        out.push(d);
    }
    if let Ok(coll) = en.get_device_collection(&Direction::Render) {
        if let Ok(n) = coll.get_nbr_devices() {
            for i in 0..n {
                if let Ok(d) = coll.get_device_at_index(i) {
                    out.push(d);
                }
            }
        }
    }
    out
}

// ── Spectral features ─────────────────────────────────────────────────────────

/// Spectral features over the most recent FFT_SIZE samples → (brightness, tonality, valence_proxy),
/// each 0..1. None if not enough samples or the frame is effectively silent.
fn spectral(samples: &[f32], sample_rate: u32) -> Option<(f32, f32, f32)> {
    if samples.len() < FFT_SIZE {
        return None;
    }
    let frame = &samples[samples.len() - FFT_SIZE..];
    // Hann window → complex buffer.
    let mut buf: Vec<Complex<f32>> = (0..FFT_SIZE)
        .map(|i| {
            let w = 0.5
                - 0.5 * (2.0 * std::f32::consts::PI * i as f32 / (FFT_SIZE as f32 - 1.0)).cos();
            Complex::new(frame[i] * w, 0.0)
        })
        .collect();

    let mut planner = FftPlanner::<f32>::new();
    planner.plan_fft_forward(FFT_SIZE).process(&mut buf);

    // Magnitude spectrum, bins 1..N/2 (skip DC).
    let half = FFT_SIZE / 2;
    let mags: Vec<f32> = (1..half).map(|k| buf[k].norm()).collect();
    let sum_mag: f32 = mags.iter().sum();
    if sum_mag < 1.0e-6 {
        return None;
    }

    // Spectral centroid (Hz) → brightness (log-mapped 200..8000 Hz → 0..1).
    let bin_hz = sample_rate as f32 / FFT_SIZE as f32;
    let centroid: f32 = mags
        .iter()
        .enumerate()
        .map(|(i, m)| (i as f32 + 1.0) * bin_hz * m)
        .sum::<f32>()
        / sum_mag;
    let lo = 200.0_f32.log2();
    let hi = 8000.0_f32.log2();
    let brightness = ((centroid.max(1.0).log2() - lo) / (hi - lo)).clamp(0.0, 1.0);

    // Spectral flatness = geomean/arithmean → tonality = 1 - flatness.
    let n = mags.len() as f32;
    let arith = sum_mag / n;
    let eps = 1.0e-9_f32;
    let log_mean: f32 = mags.iter().map(|m| (m + eps).ln()).sum::<f32>() / n;
    let geo = log_mean.exp();
    let flatness = (geo / (arith + eps)).clamp(0.0, 1.0);
    let tonality = 1.0 - flatness;

    // Heuristic valence proxy: bright + tonal → higher. Labelled proxy on the wire.
    let valence_proxy = (0.5 * brightness + 0.5 * tonality).clamp(0.0, 1.0);

    let r3 = |x: f32| (x * 1000.0).round() / 1000.0;
    Some((r3(brightness), r3(tonality), r3(valence_proxy)))
}

/// Voice/words-presence proxy: fraction of amplitude-envelope modulation energy in the 2–8 Hz
/// syllable-rate band. Speech and vocals modulate loudness at syllable rate; steady instrumental
/// textures modulate less there. Rough proxy (singing / rhythmic instruments blur it) — labelled
/// low-confidence. The honest version is a small VAD model on the GPU.
fn voiceness(samples: &[f32], sample_rate: u32) -> Option<f32> {
    let hop = (sample_rate as f32 * 0.02) as usize; // 20ms → ~50 Hz envelope
    if hop == 0 || samples.len() < hop * 16 {
        return None;
    }
    // Short-time energy envelope.
    let mut env: Vec<f32> = Vec::with_capacity(samples.len() / hop);
    let mut i = 0;
    while i + hop <= samples.len() {
        let frame = &samples[i..i + hop];
        let e = (frame.iter().map(|x| x * x).sum::<f32>() / hop as f32).sqrt();
        env.push(e);
        i += hop;
    }
    let n = env.len();
    if n < 16 {
        return None;
    }
    // Remove DC; bail if effectively silent.
    let mean = env.iter().sum::<f32>() / n as f32;
    if mean < 1.0e-6 {
        return None;
    }
    for e in env.iter_mut() {
        *e -= mean;
    }

    let mut buf: Vec<Complex<f32>> = env.iter().map(|&e| Complex::new(e, 0.0)).collect();
    FftPlanner::<f32>::new().plan_fft_forward(n).process(&mut buf);

    let env_rate = sample_rate as f32 / hop as f32;
    let bin_hz = env_rate / n as f32;
    let half = n / 2;
    let mut band = 0.0f32; // 2–8 Hz
    let mut total = 0.0f32; // all modulation (skip DC)
    for k in 1..half {
        let f = k as f32 * bin_hz;
        let mag = buf[k].norm();
        total += mag;
        if (2.0..=8.0).contains(&f) {
            band += mag;
        }
    }
    if total < 1.0e-9 {
        return None;
    }
    let v = (band / total).clamp(0.0, 1.0);
    Some((v * 1000.0).round() / 1000.0)
}

// ── Temporal sense (the arc, not the frame) ───────────────────────────────────
//
// The daemon runs continuously — it is what's awake during the gaps when the agent isn't.
// So the temporal model lives here: it ingests the per-snapshot feature stream and maintains
// multi-timescale trends, a debounced "phase" (a stable stretch of character), and an event log,
// then emits a narrative the agent reads as a *sense of time*, not a frozen reading.

#[derive(Clone, Copy)]
struct Sample {
    t_ms: u64,
    energy: f32,
    brightness: f32,
    silent: bool,
}

#[derive(Serialize, Clone)]
struct PhaseOut {
    /// e.g. "silent" | "quiet-mellow" | "moderate-bright" | "loud-bright".
    character: String,
    /// How long the current phase has held.
    secs: u64,
}

#[derive(Serialize, Clone)]
struct Trend {
    /// "rising" | "falling" | "steady" over each horizon.
    energy_30s: &'static str,
    energy_5m: &'static str,
    brightness_30s: &'static str,
}

#[derive(Serialize, Clone)]
struct TemporalEvent {
    kind: &'static str, // "shift" | "silence" | "resume"
    detail: String,
    secs_ago: u64,
}

#[derive(Serialize, Clone)]
struct Temporal {
    phase: PhaseOut,
    trend: Trend,
    events: Vec<TemporalEvent>,
    /// "settled" (deep in one mode) | "settling" | "transitional" (shifting). How much the
    /// sonic ground is holding vs moving — changes whether to go deep or stay light.
    stability: &'static str,
    /// The instant read RELATIVE to this user's own running baseline — "above/around/below
    /// your norm", not an absolute threshold. Calibration: the sense becomes about THEM.
    relative: Relative,
    /// One-line, agent-readable: "Quiet-mellow for 11m; energy easing; quiet-bright → quiet-mellow 2m ago".
    narrative: String,
}

/// The current read placed against the user's own listening baseline.
#[derive(Serialize, Clone)]
struct Relative {
    /// "above" | "around" | "below" | "calibrating" (not enough history yet).
    energy: &'static str,
    brightness: &'static str,
    /// True once the baseline has enough samples to be trusted.
    calibrated: bool,
}

/// Running mean/variance (Welford) — the user's habitual listening level for one feature.
#[derive(Clone, Serialize, Deserialize)]
struct Baseline {
    n: u64,
    mean: f64,
    m2: f64,
}

impl Baseline {
    fn new() -> Self {
        Self {
            n: 0,
            mean: 0.0,
            m2: 0.0,
        }
    }

    fn push(&mut self, x: f64) {
        self.n += 1;
        let d = x - self.mean;
        self.mean += d / self.n as f64;
        self.m2 += d * (x - self.mean);
    }

    fn std(&self) -> f64 {
        if self.n < 2 {
            0.0
        } else {
            (self.m2 / (self.n - 1) as f64).sqrt()
        }
    }

    /// z-score of x against the running baseline (0 if std not yet meaningful).
    fn z(&self, x: f64) -> f64 {
        let s = self.std();
        if s < 1.0e-6 {
            0.0
        } else {
            (x - self.mean) / s
        }
    }
}

/// Persisted calibration: the energy + brightness baselines, so "your norm" survives a daemon
/// restart and keeps deepening with accumulated intake instead of resetting from zero.
#[derive(Serialize, Deserialize)]
struct BaselineSnapshot {
    energy: Baseline,
    bright: Baseline,
}

/// Classify a z-score against the user's norm.
fn relative_label(z: f64) -> &'static str {
    if z > 0.7 {
        "above"
    } else if z < -0.7 {
        "below"
    } else {
        "around"
    }
}

struct TemporalModel {
    samples: VecDeque<Sample>,
    cap: usize,
    phase_char: String,
    phase_started_ms: u64,
    cand_char: Option<String>,
    cand_since_ms: u64,
    events: VecDeque<(u64, &'static str, String)>,
    last_silent: Option<bool>,
    /// Session-long baselines (non-silent samples) — the user's own normal.
    energy_base: Baseline,
    bright_base: Baseline,
    /// Where the baseline is persisted (None = ephemeral). Loaded on start, saved periodically.
    baseline_path: Option<PathBuf>,
    /// Non-silent observes since the last baseline save (throttles disk writes).
    since_save: u32,
}

impl TemporalModel {
    fn new() -> Self {
        Self {
            samples: VecDeque::with_capacity(600),
            cap: 600, // ~10 min at 1 Hz
            phase_char: String::new(),
            phase_started_ms: 0,
            cand_char: None,
            cand_since_ms: 0,
            events: VecDeque::new(),
            last_silent: None,
            energy_base: Baseline::new(),
            bright_base: Baseline::new(),
            baseline_path: None,
            since_save: 0,
        }
    }

    /// Like `new`, but load any persisted baseline so calibration continues across restarts.
    fn with_baseline(path: PathBuf) -> Self {
        let mut m = Self::new();
        if let Ok(raw) = fs::read_to_string(&path) {
            if let Ok(snap) = serde_json::from_str::<BaselineSnapshot>(&raw) {
                eprintln!(
                    "[sonic] calibration: resumed baseline (n={}) from {}",
                    snap.energy.n,
                    path.display()
                );
                m.energy_base = snap.energy;
                m.bright_base = snap.bright;
            }
        }
        m.baseline_path = Some(path);
        m
    }

    /// Atomically persist the running baseline (energy + brightness).
    fn save_baseline(&self) {
        let Some(path) = &self.baseline_path else {
            return;
        };
        let snap = BaselineSnapshot {
            energy: self.energy_base.clone(),
            bright: self.bright_base.clone(),
        };
        let Ok(body) = serde_json::to_string(&snap) else {
            return;
        };
        if let Some(dir) = path.parent() {
            let _ = fs::create_dir_all(dir);
        }
        let tmp = path.with_extension("json.tmp");
        if fs::write(&tmp, body).is_ok() {
            let _ = fs::rename(&tmp, path);
        }
    }

    fn observe(&mut self, t_ms: u64, energy: f32, brightness: f32, silent: bool) -> Temporal {
        self.samples.push_back(Sample {
            t_ms,
            energy,
            brightness,
            silent,
        });
        while self.samples.len() > self.cap {
            self.samples.pop_front();
        }

        // Baseline accrues only on non-silent samples — the user's listening norm, not silence.
        if !silent {
            self.energy_base.push(energy as f64);
            self.bright_base.push(brightness as f64);
            self.since_save += 1;
            if self.since_save >= 30 {
                self.save_baseline();
                self.since_save = 0;
            }
        }

        // Silence / resume transitions.
        if let Some(prev) = self.last_silent {
            if !prev && silent {
                self.push_event(t_ms, "silence", "audio stopped".to_string());
            } else if prev && !silent {
                self.push_event(t_ms, "resume", "audio resumed".to_string());
            }
        }
        self.last_silent = Some(silent);

        let ch = classify_character(energy, brightness, silent);

        // Initialize the phase on the first sample (no spurious shift event).
        if self.phase_started_ms == 0 {
            self.phase_char = ch.clone();
            self.phase_started_ms = t_ms;
        }

        // Debounced phase change: a new character must hold ≥3s before it commits.
        if ch != self.phase_char {
            if self.cand_char.as_deref() == Some(ch.as_str()) {
                if t_ms.saturating_sub(self.cand_since_ms) >= 3000 {
                    let detail = format!("{} → {}", self.phase_char, ch);
                    let started = self.cand_since_ms;
                    self.push_event(t_ms, "shift", detail);
                    self.phase_char = ch;
                    self.phase_started_ms = started;
                    self.cand_char = None;
                }
            } else {
                self.cand_char = Some(ch);
                self.cand_since_ms = t_ms;
            }
        } else {
            self.cand_char = None;
        }

        let trend = Trend {
            energy_30s: trend_label(&self.samples, t_ms, 30_000, |s| s.energy),
            energy_5m: trend_label(&self.samples, t_ms, 300_000, |s| s.energy),
            brightness_30s: trend_label(&self.samples, t_ms, 30_000, |s| {
                if s.silent {
                    0.0
                } else {
                    s.brightness
                }
            }),
        };

        let events: Vec<TemporalEvent> = self
            .events
            .iter()
            .rev()
            .take(4)
            .map(|(et, kind, detail)| TemporalEvent {
                kind: *kind,
                detail: detail.clone(),
                secs_ago: t_ms.saturating_sub(*et) / 1000,
            })
            .collect();

        let phase_char = self.phase_char.clone();
        let phase_secs = t_ms.saturating_sub(self.phase_started_ms) / 1000;
        let last_shift_secs = events.iter().find(|e| e.kind == "shift").map(|e| e.secs_ago);
        let stability = if phase_secs >= 90 && last_shift_secs.map_or(true, |s| s > 30) {
            "settled"
        } else if last_shift_secs.map_or(false, |s| s < 15) || phase_secs < 20 {
            "transitional"
        } else {
            "settling"
        };
        let calibrated = self.energy_base.n >= 30;
        let relative = Relative {
            energy: if calibrated {
                relative_label(self.energy_base.z(energy as f64))
            } else {
                "calibrating"
            },
            brightness: if calibrated {
                relative_label(self.bright_base.z(brightness as f64))
            } else {
                "calibrating"
            },
            calibrated,
        };

        let narrative = narrate(&phase_char, phase_secs, &trend, &events, stability, &relative);

        Temporal {
            phase: PhaseOut {
                character: phase_char,
                secs: phase_secs,
            },
            trend,
            events,
            stability,
            relative,
            narrative,
        }
    }

    fn push_event(&mut self, t_ms: u64, kind: &'static str, detail: String) {
        self.events.push_back((t_ms, kind, detail));
        while self.events.len() > 16 {
            self.events.pop_front();
        }
    }
}

/// Energy × brightness bucket → a coarse character label.
fn classify_character(energy: f32, brightness: f32, silent: bool) -> String {
    if silent {
        return "silent".to_string();
    }
    let e = if energy < 0.33 {
        "quiet"
    } else if energy > 0.66 {
        "loud"
    } else {
        "moderate"
    };
    let b = if brightness >= 0.5 { "bright" } else { "mellow" };
    format!("{e}-{b}")
}

/// Least-squares slope of `f` over the samples within `horizon_ms` → rising/falling/steady.
fn trend_label(
    samples: &VecDeque<Sample>,
    now_ms: u64,
    horizon_ms: u64,
    f: impl Fn(&Sample) -> f32,
) -> &'static str {
    let cutoff = now_ms.saturating_sub(horizon_ms);
    let pts: Vec<(f32, f32)> = samples
        .iter()
        .filter(|s| s.t_ms >= cutoff)
        .map(|s| (s.t_ms as f32 / 1000.0, f(s)))
        .collect();
    if pts.len() < 4 {
        return "steady";
    }
    let n = pts.len() as f32;
    let sx: f32 = pts.iter().map(|p| p.0).sum();
    let sy: f32 = pts.iter().map(|p| p.1).sum();
    let sxx: f32 = pts.iter().map(|p| p.0 * p.0).sum();
    let sxy: f32 = pts.iter().map(|p| p.0 * p.1).sum();
    let denom = n * sxx - sx * sx;
    if denom.abs() < 1.0e-6 {
        return "steady";
    }
    let slope = (n * sxy - sx * sy) / denom; // units per second
    let per_horizon = slope * (horizon_ms as f32 / 1000.0);
    if per_horizon > 0.12 {
        "rising"
    } else if per_horizon < -0.12 {
        "falling"
    } else {
        "steady"
    }
}

fn narrate(
    phase: &str,
    phase_secs: u64,
    trend: &Trend,
    events: &[TemporalEvent],
    stability: &str,
    relative: &Relative,
) -> String {
    let dur = human_dur(phase_secs);
    let mut s = if phase == "silent" {
        format!("Silence for {dur}")
    } else {
        let mut c = phase.to_string();
        if let Some(first) = c.get_mut(0..1) {
            first.make_ascii_uppercase();
        }
        format!("{c} for {dur}")
    };
    match trend.energy_30s {
        "rising" => s.push_str("; energy building"),
        "falling" => s.push_str("; energy easing"),
        _ => {}
    }
    if let Some(ev) = events.iter().find(|e| e.kind == "shift") {
        s.push_str(&format!("; {} {}", ev.detail, ago(ev.secs_ago)));
    } else if let Some(ev) = events.first() {
        s.push_str(&format!("; {} {}", ev.detail, ago(ev.secs_ago)));
    }
    if relative.calibrated && phase != "silent" {
        match relative.energy {
            "above" => s.push_str("; louder than your norm"),
            "below" => s.push_str("; quieter than your norm"),
            _ => {}
        }
    }
    match stability {
        "settled" => s.push_str("; settled"),
        "transitional" => s.push_str("; in flux"),
        _ => {}
    }
    s
}

fn human_dur(secs: u64) -> String {
    if secs < 60 {
        format!("{secs}s")
    } else if secs < 3600 {
        format!("{}m", secs / 60)
    } else {
        format!("{}h{}m", secs / 3600, (secs % 3600) / 60)
    }
}

fn ago(secs: u64) -> String {
    if secs < 5 {
        "just now".to_string()
    } else {
        format!("{} ago", human_dur(secs))
    }
}

// ── Diagnostics (SONIC_DIAG=1) ────────────────────────────────────────────────

/// One-shot: list render endpoints and their audio sessions (pid + state). Answers
/// "which process is actually rendering, and on which endpoint."
pub fn run_diagnostics() -> Result<()> {
    let _ = initialize_mta();
    let en = DeviceEnumerator::new().map_err(we)?;

    if let Ok(def) = en.get_default_device(&Direction::Render) {
        eprintln!(
            "[sonic-diag] default render: '{}'",
            def.get_friendlyname().unwrap_or_else(|_| "<unknown>".into())
        );
    }

    let coll = en.get_device_collection(&Direction::Render).map_err(we)?;
    let n = coll.get_nbr_devices().map_err(we)?;
    eprintln!("[sonic-diag] {n} active render endpoint(s):");
    for i in 0..n {
        let device = match coll.get_device_at_index(i) {
            Ok(d) => d,
            Err(e) => {
                eprintln!("[sonic-diag]   device #{i}: error {e:?}");
                continue;
            }
        };
        let name = device
            .get_friendlyname()
            .unwrap_or_else(|_| "<unknown>".into());
        let mgr = match device.get_iaudiosessionmanager() {
            Ok(m) => m,
            Err(e) => {
                eprintln!("[sonic-diag] '{name}': session manager error {e:?}");
                continue;
            }
        };
        let sessions = match mgr.get_audiosessionenumerator() {
            Ok(s) => s,
            Err(e) => {
                eprintln!("[sonic-diag] '{name}': session enumerator error {e:?}");
                continue;
            }
        };
        let count = sessions.get_count().unwrap_or(0);
        eprintln!("[sonic-diag] '{name}': {count} session(s)");
        for s in 0..count {
            if let Ok(sc) = sessions.get_session(s) {
                let pid = sc.get_process_id().unwrap_or(0);
                let state = sc
                    .get_state()
                    .map(|st| format!("{st:?}"))
                    .unwrap_or_else(|_| "?".into());
                eprintln!("[sonic-diag]     pid={pid} state={state}");
            }
        }
    }
    Ok(())
}

// ── Helpers ───────────────────────────────────────────────────────────────────

fn window(
    schema: &'static str,
    energy: f32,
    silent: bool,
    window_secs: f32,
    sample_rate: u32,
) -> SonicWindow {
    SonicWindow {
        schema,
        source: "loopback",
        energy,
        silent,
        captured_at_epoch_ms: now_ms(),
        window_secs,
        sample_rate,
        brightness: None,
        tonality: None,
        valence_proxy: None,
        voiceness: None,
        temporal: None,
    }
}

/// A `blocked` window: no endpoint accepted loopback (all exclusive-locked). sonic_read reads
/// this and falls back to Spotify identity only.
fn blocked_window(window_secs: f32) -> SonicWindow {
    SonicWindow {
        schema: SCHEMA,
        source: "blocked",
        energy: 0.0,
        silent: true,
        captured_at_epoch_ms: now_ms(),
        window_secs,
        sample_rate: 0,
        brightness: None,
        tonality: None,
        valence_proxy: None,
        voiceness: None,
        temporal: None,
    }
}

/// Read SONIC_PID as a numeric target process id.
fn process_pid() -> Option<u32> {
    std::env::var("SONIC_PID")
        .ok()
        .and_then(|v| v.trim().parse::<u32>().ok())
}

/// Sleep up to `total`, in short slices, returning early if stop is requested.
fn sleep_with_stop(total: Duration, stop: &Arc<AtomicBool>) {
    let slice = Duration::from_millis(100);
    let mut remaining = total;
    while remaining > Duration::ZERO {
        if stop.load(Ordering::Acquire) {
            return;
        }
        let nap = remaining.min(slice);
        std::thread::sleep(nap);
        remaining = remaining.saturating_sub(nap);
    }
}

/// Map RMS (~0..1) to a perceptual 0..1 energy via dBFS, floored at DB_FLOOR.
fn energy_from_rms(rms: f32) -> (f32, bool) {
    if rms < SILENCE_RMS {
        return (0.0, true);
    }
    let db = 20.0 * rms.log10();
    let energy = ((db - DB_FLOOR) / -DB_FLOOR).clamp(0.0, 1.0);
    (energy, false)
}

/// Atomic write: serialize to `<path>.tmp`, then rename over the target.
/// On Windows std::fs::rename uses MOVEFILE_REPLACE_EXISTING, so this overwrites atomically.
fn write_atomic(path: &Path, window: &SonicWindow) -> Result<()> {
    if let Some(dir) = path.parent() {
        let _ = fs::create_dir_all(dir);
    }
    let tmp = path.with_extension("json.tmp");
    let json = serde_json::to_string_pretty(window).context("serialize window")?;
    {
        let mut f = fs::File::create(&tmp).context("create temp window file")?;
        f.write_all(json.as_bytes()).context("write temp window file")?;
        let _ = f.flush();
    }
    fs::rename(&tmp, path).context("atomic rename window file")?;
    Ok(())
}

/// Wrap wasapi errors (whose concrete type varies) into anyhow via Debug.
fn we<E: std::fmt::Debug>(e: E) -> anyhow::Error {
    anyhow!("wasapi error: {e:?}")
}

fn now_ms() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_millis() as u64)
        .unwrap_or(0)
}

fn env_f32(key: &str, default: f32) -> f32 {
    std::env::var(key)
        .ok()
        .and_then(|v| v.trim().parse().ok())
        .unwrap_or(default)
}

fn env_u64(key: &str, default: u64) -> u64 {
    std::env::var(key)
        .ok()
        .and_then(|v| v.trim().parse().ok())
        .unwrap_or(default)
}

fn env_bool(key: &str, default: bool) -> bool {
    std::env::var(key)
        .ok()
        .map(|v| {
            matches!(
                v.trim().to_ascii_lowercase().as_str(),
                "1" | "true" | "yes" | "on"
            )
        })
        .unwrap_or(default)
}
