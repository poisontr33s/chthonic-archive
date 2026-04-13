use std::fs;
use std::io::{BufRead, BufReader, Read, Write};
use std::path::Path;

use anyhow::{Context, Result, bail};
use flate2::Compression;
use flate2::read::GzDecoder;
use flate2::write::GzEncoder;

use super::event::{TrailEvent, strip_bom};
use super::hot;

/// Build the filename for a cold trail file.
pub fn cold_path(trail_dir: &Path, date: &str) -> std::path::PathBuf {
    trail_dir.join(format!("{date}.cold.ndjson.gz"))
}

/// Compress a hot NDJSON file into a gzip cold archive, then verify the
/// round-trip by decompressing and comparing byte-for-byte.
pub fn forge(trail_dir: &Path, date: &str) -> Result<()> {
    let src = hot::hot_path(trail_dir, date);
    let dst = cold_path(trail_dir, date);

    if !src.exists() {
        bail!("no hot trail to forge for {date}: {}", src.display());
    }

    // Read the entire hot file into memory (trail files are small).
    let hot_bytes = fs::read(&src)
        .with_context(|| format!("reading {}", src.display()))?;

    if hot_bytes.is_empty() {
        bail!("hot trail is empty: {}", src.display());
    }

    // Validate every event before forging — refuse to archive invalid data.
    {
        let reader = BufReader::new(hot_bytes.as_slice());
        for (i, line) in reader.lines().enumerate() {
            let lineno = i + 1;
            let raw = line.with_context(|| format!("reading line {lineno}"))?;
            let clean = strip_bom(&raw);
            if clean.trim().is_empty() {
                continue;
            }
            let event: TrailEvent = serde_json::from_str(clean)
                .with_context(|| format!("line {lineno}: invalid JSON"))?;
            event
                .validate()
                .with_context(|| format!("line {lineno}: schema violation"))?;
        }
    }

    // Compress.
    let mut encoder = GzEncoder::new(Vec::new(), Compression::best());
    encoder
        .write_all(&hot_bytes)
        .context("gzip compression failed")?;
    let compressed = encoder.finish().context("finalizing gzip stream")?;

    // Round-trip verify before writing.
    let mut decoder = GzDecoder::new(compressed.as_slice());
    let mut roundtrip = Vec::new();
    decoder
        .read_to_end(&mut roundtrip)
        .context("gzip decompression during round-trip verify")?;

    if roundtrip != hot_bytes {
        bail!("round-trip verification failed: decompressed bytes differ from source");
    }

    // Write the cold file.
    fs::write(&dst, &compressed)
        .with_context(|| format!("writing {}", dst.display()))?;

    let ratio = if !hot_bytes.is_empty() {
        (compressed.len() as f64 / hot_bytes.len() as f64) * 100.0
    } else {
        0.0
    };

    eprintln!(
        "forged {} → {} ({} → {} bytes, {ratio:.1}%)",
        src.display(),
        dst.display(),
        hot_bytes.len(),
        compressed.len(),
    );

    Ok(())
}

/// Verify an existing cold file by decompressing and validating every event.
pub fn verify_cold(trail_dir: &Path, date: &str) -> Result<()> {
    let path = cold_path(trail_dir, date);
    if !path.exists() {
        bail!("no cold trail for {date}: {}", path.display());
    }

    let compressed = fs::read(&path)
        .with_context(|| format!("reading {}", path.display()))?;

    let mut decoder = GzDecoder::new(compressed.as_slice());
    let mut decompressed = Vec::new();
    decoder
        .read_to_end(&mut decompressed)
        .with_context(|| format!("decompressing {}", path.display()))?;

    let reader = BufReader::new(decompressed.as_slice());
    let mut total = 0u64;
    let mut errors = 0u64;

    for (i, line) in reader.lines().enumerate() {
        let lineno = i + 1;
        let raw = line.with_context(|| format!("reading line {lineno}"))?;
        let clean = strip_bom(&raw);
        if clean.trim().is_empty() {
            continue;
        }
        total += 1;

        let event: TrailEvent = match serde_json::from_str(clean) {
            Ok(e) => e,
            Err(err) => {
                eprintln!("cold line {lineno}: parse error: {err}");
                errors += 1;
                continue;
            }
        };

        if let Err(err) = event.validate() {
            eprintln!("cold line {lineno}: schema error: {err}");
            errors += 1;
        }
    }

    if errors > 0 {
        bail!("{errors} error(s) in {total} event(s) from cold {}", path.display());
    }

    eprintln!("{total} event(s) verified OK in cold {}", path.display());
    Ok(())
}
