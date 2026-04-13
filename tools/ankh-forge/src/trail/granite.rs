// Runestone Execution Model — Tier 2: Granite (CPU path)
//
// Phase 2 CPU-path implementation of the `.runestone` binary stone format.
// Compiles cold NDJSON archives into a compact, integrity-verified binary
// using zstd compression + bincode 2.0 serialization + SHA-256 digest.
//
// Wire format (70-byte fixed header + variable blocks):
//   [0..8]    Magic: b"CHTHONIC"
//   [8..10]   format_version: u16 le = 1
//   [10..14]  schema_version: u32 le = 1
//   [14..18]  event_count: u32 le
//   [18..22]  flags: u32 le (bit 1 = CPU_COMPRESSED/zstd)
//   [22..54]  SHA-256 of (schema ++ spirv ++ payload_compressed)
//   [54..58]  spirv_len: u32 le (0 in Phase 2 CPU path)
//   [58..62]  schema_len: u32 le
//   [62..66]  payload_compressed_len: u32 le
//   [66..70]  payload_uncompressed_len: u32 le
//   [70..]    SCHEMA block (JSON bytes)
//   [70+N..]  SPIRV block (empty in Phase 2)
//   [70+N..]  PAYLOAD (zstd-compressed bincode of Vec<TrailEvent>)

use std::fs;
use std::io::{BufRead, BufReader, Read};
use std::path::Path;

use anyhow::{Context, Result, bail};
use flate2::read::GzDecoder;
use sha2::{Sha256, Digest};

use super::event::{TrailEvent, strip_bom};

const MAGIC: &[u8; 8] = b"CHTHONIC";
const FORMAT_VERSION: u16 = 1;
const SCHEMA_VERSION: u32 = 1;
const HEADER_SIZE: usize = 70;

// Flag bits
const FLAG_CPU_COMPRESSED: u32 = 1 << 1;
const FLAG_GPU_COMPRESSED: u32 = 1 << 0;
const FLAGS_KNOWN: u32 = FLAG_CPU_COMPRESSED | FLAG_GPU_COMPRESSED;

/// Validate flags before any decode. Rejects unknown bits, conflicting modes,
/// and the unimplemented GPU path. Must be called before block extraction.
fn validate_flags(flags: u32) -> Result<()> {
    let unknown = flags & !FLAGS_KNOWN;
    if unknown != 0 {
        bail!("unknown flag bits: 0x{unknown:08x}");
    }
    let cpu = flags & FLAG_CPU_COMPRESSED != 0;
    let gpu = flags & FLAG_GPU_COMPRESSED != 0;
    if cpu && gpu {
        bail!("conflicting flags: both CPU and GPU compression set");
    }
    if gpu {
        bail!("GPU compression (flag bit 0) is not yet supported in CPU-path binary");
    }
    Ok(())
}

/// Bincode-native representation of a TrailEvent.
/// Avoids serde attribute conflicts (skip_serializing_if) that break bincode 2.0.
#[derive(bincode::Encode, bincode::Decode)]
struct StoneEvent {
    event_type: String,
    kind: String,
    at_rfc3339: String,
    p: u8,
    msg: String,
    file: Option<String>,
    data_json: Option<String>,
}

impl StoneEvent {
    fn from_trail(e: &TrailEvent) -> Self {
        StoneEvent {
            event_type: e.event_type.clone(),
            kind: e.kind.clone(),
            at_rfc3339: e.at.to_rfc3339(),
            p: e.p,
            msg: e.msg.clone(),
            file: e.file.clone(),
            data_json: e.data.as_ref().map(|v| serde_json::to_string(v).unwrap()),
        }
    }

    fn to_trail(self) -> Result<TrailEvent> {
        Ok(TrailEvent {
            event_type: self.event_type,
            kind: self.kind,
            at: self.at_rfc3339.parse().context("parsing stored timestamp")?,
            p: self.p,
            msg: self.msg,
            file: self.file,
            data: self.data_json
                .as_deref()
                .map(serde_json::from_str)
                .transpose()
                .context("parsing stored data JSON")?,
        })
    }
}

/// The Phase 1 schema JSON — describes trail stone structure.
fn schema_json() -> Vec<u8> {
    serde_json::to_vec(&serde_json::json!({
        "stone_type": "trail",
        "format_version": FORMAT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "event_schema": {
            "types": ["diagnostic", "decision", "artifact", "snapshot", "meta", "memory", "recovery"],
            "priority_range": [1, 3],
            "at_format": "rfc3339"
        }
    })).expect("schema serialization is infallible")
}

/// Read a cold .ndjson.gz file and parse all TrailEvents from it.
fn read_cold_events(trail_dir: &Path, date: &str) -> Result<Vec<TrailEvent>> {
    let cold_path = trail_dir.join(format!("{date}.cold.ndjson.gz"));
    if !cold_path.exists() {
        bail!("no cold trail for {date}: {}", cold_path.display());
    }

    let compressed = fs::read(&cold_path)
        .with_context(|| format!("reading {}", cold_path.display()))?;

    let mut decoder = GzDecoder::new(compressed.as_slice());
    let mut decompressed = Vec::new();
    decoder.read_to_end(&mut decompressed)
        .with_context(|| format!("decompressing {}", cold_path.display()))?;

    let reader = BufReader::new(decompressed.as_slice());
    let mut events = Vec::new();

    let mut bom_checked = false;
    for (i, line) in reader.lines().enumerate() {
        let raw = line.with_context(|| format!("reading line {}", i + 1))?;
        let clean = if !bom_checked { bom_checked = true; strip_bom(&raw) } else { raw.as_str() };
        if clean.trim().is_empty() {
            continue;
        }
        let event: TrailEvent = serde_json::from_str(clean)
            .with_context(|| format!("parsing cold line {}", i + 1))?;
        event.validate()
            .with_context(|| format!("cold line {} schema violation", i + 1))?;
        events.push(event);
    }

    if events.is_empty() {
        bail!("cold trail for {date} contains no events");
    }

    Ok(events)
}

/// Compile a cold archive into a `.runestone` binary stone.
pub fn compile(trail_dir: &Path, date: &str, force: bool) -> Result<()> {
    // Stone immutability: one immutable stone per day unless --force overrides.
    {
        let stones_dir = trail_dir.parent()
            .context("trail_dir has no parent")?
            .join("stones");
        let existing = stones_dir.join(format!("{date}.runestone"));
        if existing.exists() && !force {
            bail!(
                "stone already exists: {}\nStones are immutable by default. Use --force to overwrite.",
                existing.display()
            );
        }
    }

    let events = read_cold_events(trail_dir, date)?;
    let event_count = events.len() as u32;

    // Encode events via bincode 2.0 (native Encode, not serde — avoids skip_serializing_if)
    let stone_events: Vec<StoneEvent> = events.iter().map(StoneEvent::from_trail).collect();
    let payload_raw = bincode::encode_to_vec(&stone_events, bincode::config::standard())
        .context("bincode encoding failed")?;
    let payload_uncompressed_len = payload_raw.len() as u32;

    // Compress with zstd
    let payload_compressed = zstd::encode_all(payload_raw.as_slice(), 3)
        .context("zstd compression failed")?;
    if payload_compressed.len() > 256 * 1024 * 1024 {
        bail!(
            "compressed payload exceeds 256 MiB ({} bytes) for {date}. Split the trail first.",
            payload_compressed.len()
        );
    }
    let payload_compressed_len = payload_compressed.len() as u32;

    // Schema block
    let schema_bytes = schema_json();
    let schema_len = schema_bytes.len() as u32;

    // SPIRV block (empty in Phase 2 CPU path)
    let spirv_bytes: &[u8] = &[];
    let spirv_len: u32 = 0;

    // Build fixed header with zeroed hash digest slot — hash covers full file
    let flags: u32 = FLAG_CPU_COMPRESSED;
    let mut header = [0u8; HEADER_SIZE];
    header[0..8].copy_from_slice(MAGIC);
    header[8..10].copy_from_slice(&FORMAT_VERSION.to_le_bytes());
    header[10..14].copy_from_slice(&SCHEMA_VERSION.to_le_bytes());
    header[14..18].copy_from_slice(&event_count.to_le_bytes());
    header[18..22].copy_from_slice(&flags.to_le_bytes());
    // [22..54] = hash slot: zero during digest computation, filled after
    header[54..58].copy_from_slice(&spirv_len.to_le_bytes());
    header[58..62].copy_from_slice(&schema_len.to_le_bytes());
    header[62..66].copy_from_slice(&payload_compressed_len.to_le_bytes());
    header[66..70].copy_from_slice(&payload_uncompressed_len.to_le_bytes());

    // SHA-256 covers the full stone: zeroed header + schema + spirv + payload.
    // This authenticates event_count, flags, and all length fields.
    let mut hasher = Sha256::new();
    hasher.update(&header);
    hasher.update(&schema_bytes);
    hasher.update(spirv_bytes);
    hasher.update(&payload_compressed);
    let hash: [u8; 32] = hasher.finalize().into();
    header[22..54].copy_from_slice(&hash);

    // Assemble the full stone
    let mut out = Vec::with_capacity(HEADER_SIZE + schema_bytes.len() + payload_compressed.len());
    out.extend_from_slice(&header);
    out.extend_from_slice(&schema_bytes);
    out.extend_from_slice(spirv_bytes);
    out.extend_from_slice(&payload_compressed);

    // Atomic write: temp file → rename to avoid truncated stones on crash or kill
    let stones_dir = trail_dir.parent()
        .context("trail_dir has no parent")?
        .join("stones");
    fs::create_dir_all(&stones_dir)
        .with_context(|| format!("creating stones dir {}", stones_dir.display()))?;

    let stone_path = stones_dir.join(format!("{date}.runestone"));
    let tmp_path = stones_dir.join(format!("{date}.runestone.tmp.{}", std::process::id()));

    fs::write(&tmp_path, &out)
        .with_context(|| format!("writing temp stone {}", tmp_path.display()))?;
    fs::rename(&tmp_path, &stone_path)
        .with_context(|| format!("atomically installing stone {}", stone_path.display()))?;

    eprintln!(
        "stoned {} → {} ({} events, {} bytes)",
        date, stone_path.display(), event_count, out.len()
    );

    Ok(())
}

/// Query/inspect a `.runestone` binary stone — verify integrity, decode, print.
pub fn query(stone_path: &Path) -> Result<()> {
    if !stone_path.exists() {
        bail!("stone not found: {}", stone_path.display());
    }

    let data = fs::read(stone_path)
        .with_context(|| format!("reading {}", stone_path.display()))?;

    if data.len() < HEADER_SIZE {
        bail!("file too small for runestone header ({} < {HEADER_SIZE})", data.len());
    }

    // Verify magic
    if &data[0..8] != MAGIC {
        bail!(
            "invalid magic: expected {:?}, got {:?}",
            MAGIC, &data[0..8]
        );
    }

    // Parse fixed header
    let format_version = u16::from_le_bytes(data[8..10].try_into().unwrap());
    let schema_version = u32::from_le_bytes(data[10..14].try_into().unwrap());
    let event_count = u32::from_le_bytes(data[14..18].try_into().unwrap());
    let flags = u32::from_le_bytes(data[18..22].try_into().unwrap());
    let stored_hash: [u8; 32] = data[22..54].try_into().unwrap();
    let spirv_len = u32::from_le_bytes(data[54..58].try_into().unwrap()) as usize;
    let schema_len = u32::from_le_bytes(data[58..62].try_into().unwrap()) as usize;
    let payload_compressed_len = u32::from_le_bytes(data[62..66].try_into().unwrap()) as usize;
    let _payload_uncompressed_len = u32::from_le_bytes(data[66..70].try_into().unwrap()) as usize;

    // Validate flags before any block extraction or decode
    validate_flags(flags)?;

    // Bounds check
    let total_needed = HEADER_SIZE + schema_len + spirv_len + payload_compressed_len;
    if data.len() < total_needed {
        bail!(
            "truncated stone: need {total_needed} bytes, have {}",
            data.len()
        );
    }

    // Extract blocks
    let schema_start = HEADER_SIZE;
    let spirv_start = schema_start + schema_len;
    let payload_start = spirv_start + spirv_len;

    let schema_bytes = &data[schema_start..spirv_start];
    let spirv_bytes = &data[spirv_start..payload_start];
    let payload_compressed = &data[payload_start..payload_start + payload_compressed_len];

    // Verify SHA-256: reconstruct canonical hash (header with zeroed digest slot)
    let mut header_for_hash = data[0..HEADER_SIZE].to_vec();
    header_for_hash[22..54].fill(0);

    let mut hasher = Sha256::new();
    hasher.update(&header_for_hash);
    hasher.update(schema_bytes);
    hasher.update(spirv_bytes);
    hasher.update(payload_compressed);
    let computed_hash: [u8; 32] = hasher.finalize().into();

    if computed_hash != stored_hash {
        bail!("SHA-256 integrity check failed — stone is corrupted or tampered");
    }

    // Decompress payload
    let is_cpu_compressed = (flags & FLAG_CPU_COMPRESSED) != 0;
    let payload_raw = if is_cpu_compressed {
        zstd::decode_all(payload_compressed)
            .context("zstd decompression failed")?
    } else {
        payload_compressed.to_vec()
    };

    // Decode events via bincode 2.0 (native Decode)
    let (stone_events, _): (Vec<StoneEvent>, _) =
        bincode::decode_from_slice(&payload_raw, bincode::config::standard())
            .context("bincode decoding failed")?;

    let events: Vec<TrailEvent> = stone_events
        .into_iter()
        .map(|se| se.to_trail())
        .collect::<Result<Vec<_>>>()
        .context("converting stone events")?;

    if events.len() as u32 != event_count {
        bail!(
            "event count mismatch: header says {event_count}, decoded {}",
            events.len()
        );
    }

    // Validate every decoded event against the REM schema
    for (i, event) in events.iter().enumerate() {
        event.validate()
            .with_context(|| format!("granite event {i} schema violation"))?;
    }

    // Print header info
    eprintln!(
        "runestone v{format_version} schema={schema_version} events={event_count} \
         flags=0x{flags:04x} schema_len={schema_len} spirv_len={spirv_len} \
         payload={payload_compressed_len} bytes (compressed)"
    );

    // Print each event
    for event in &events {
        println!("{event}");
    }

    eprintln!("{event_count} event(s) decoded from {}", stone_path.display());
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;
    use flate2::Compression;
    use flate2::write::GzEncoder;

    /// Helper: create a temporary trail dir with a cold file containing test events.
    fn make_cold_file(trail_dir: &Path, date: &str, events: &[TrailEvent]) {
        fs::create_dir_all(trail_dir).unwrap();
        let cold_path = trail_dir.join(format!("{date}.cold.ndjson.gz"));

        let mut ndjson = Vec::new();
        for event in events {
            let line = serde_json::to_string(event).unwrap();
            writeln!(&mut ndjson, "{line}").unwrap();
        }

        let mut encoder = GzEncoder::new(Vec::new(), Compression::best());
        encoder.write_all(&ndjson).unwrap();
        let compressed = encoder.finish().unwrap();

        fs::write(&cold_path, &compressed).unwrap();
    }

    fn sample_events() -> Vec<TrailEvent> {
        vec![
            TrailEvent {
                event_type: "diagnostic".into(),
                kind: "test".into(),
                at: chrono::Utc::now(),
                p: 1,
                msg: "first event".into(),
                file: Some("foo.rs".into()),
                data: None,
            },
            TrailEvent {
                event_type: "decision".into(),
                kind: "arch".into(),
                at: chrono::Utc::now(),
                p: 2,
                msg: "second event".into(),
                file: None,
                data: Some(serde_json::json!({"key": "value"})),
            },
            TrailEvent {
                event_type: "artifact".into(),
                kind: "commit".into(),
                at: chrono::Utc::now(),
                p: 3,
                msg: "third event".into(),
                file: None,
                data: None,
            },
        ]
    }

    #[test]
    fn test_roundtrip() -> Result<()> {
        let tmp = tempfile::tempdir()?;
        // .chthonic/trail layout
        let chthonic = tmp.path().join(".chthonic");
        let trail_dir = chthonic.join("trail");
        let date = "2026-07-13";

        let events = sample_events();
        make_cold_file(&trail_dir, date, &events);

        // Compile
        compile(&trail_dir, date, false)?;

        // Verify stone exists
        let stone_path = chthonic.join("stones").join(format!("{date}.runestone"));
        assert!(stone_path.exists(), "stone file must exist");

        // Read stone and verify header
        let data = fs::read(&stone_path)?;
        assert!(data.len() >= HEADER_SIZE);
        assert_eq!(&data[0..8], MAGIC);
        let event_count = u32::from_le_bytes(data[14..18].try_into().unwrap());
        assert_eq!(event_count, 3);

        // Query — should not error (integrity check passes)
        query(&stone_path)?;

        Ok(())
    }

    #[test]
    fn test_sha256_tamper_detection() -> Result<()> {
        let tmp = tempfile::tempdir()?;
        let chthonic = tmp.path().join(".chthonic");
        let trail_dir = chthonic.join("trail");
        let date = "2026-07-14";

        make_cold_file(&trail_dir, date, &sample_events());
        compile(&trail_dir, date, false)?;

        let stone_path = chthonic.join("stones").join(format!("{date}.runestone"));
        let mut data = fs::read(&stone_path)?;

        // Flip a byte in the payload area (after the 70-byte header)
        assert!(data.len() > HEADER_SIZE + 10);
        let target = HEADER_SIZE + 5;
        data[target] ^= 0xFF;

        // Write tampered stone back
        fs::write(&stone_path, &data)?;

        // Query must fail with integrity error
        let result = query(&stone_path);
        assert!(result.is_err(), "tampered stone must fail query");
        let err_msg = format!("{}", result.unwrap_err());
        assert!(
            err_msg.contains("SHA-256") || err_msg.contains("integrity") || err_msg.contains("corrupted"),
            "error should mention integrity: {err_msg}"
        );

        Ok(())
    }

    #[test]
    fn test_header_tamper_detection() -> Result<()> {
        let tmp = tempfile::tempdir()?;
        let chthonic = tmp.path().join(".chthonic");
        let trail_dir = chthonic.join("trail");
        let date = "2026-07-15";

        make_cold_file(&trail_dir, date, &sample_events());
        compile(&trail_dir, date, false)?;

        let stone_path = chthonic.join("stones").join(format!("{date}.runestone"));
        let mut data = fs::read(&stone_path)?;

        // Flip a byte in event_count [14..18] — outside old partial-hash coverage
        data[15] ^= 0x01;
        fs::write(&stone_path, &data)?;

        let result = query(&stone_path);
        assert!(result.is_err(), "header tamper must fail integrity check");
        let err_msg = format!("{}", result.unwrap_err());
        assert!(
            err_msg.contains("SHA-256") || err_msg.contains("integrity") || err_msg.contains("corrupted"),
            "error should mention integrity: {err_msg}"
        );

        Ok(())
    }

    #[test]
    fn test_magic_mismatch() -> Result<()> {
        let tmp = tempfile::tempdir()?;
        let bad_stone = tmp.path().join("bad.runestone");

        // Write a file with wrong magic
        let mut data = vec![0u8; HEADER_SIZE + 32];
        data[0..8].copy_from_slice(b"WRONGMGC");

        fs::write(&bad_stone, &data)?;

        let result = query(&bad_stone);
        assert!(result.is_err(), "wrong magic must fail");
        let err_msg = format!("{}", result.unwrap_err());
        assert!(
            err_msg.contains("magic"),
            "error should mention magic: {err_msg}"
        );

        Ok(())
    }
}
