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
///
/// When `skip_invalid` is true, lines that fail to parse as `TrailEvent`
/// are warned about and excluded from the cold archive rather than
/// aborting the whole forge run.
pub fn forge(trail_dir: &Path, date: &str, skip_invalid: bool) -> Result<()> {
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
    if hot_bytes.len() > 64 * 1024 * 1024 {
        bail!(
            "hot trail exceeds 64 MiB ({} bytes): {}. Stone it in segments if intentional.",
            hot_bytes.len(),
            src.display()
        );
    }

    // When skip_invalid is set, filter out unparseable lines and compress
    // only the valid TrailEvent lines. Otherwise validate all and abort on error.
    let forge_bytes: Vec<u8>;
    if skip_invalid {
        let reader = BufReader::new(hot_bytes.as_slice());
        let mut kept: Vec<u8> = Vec::with_capacity(hot_bytes.len());
        let mut skipped = 0u32;
        let mut bom_checked = false;
        for (i, line) in reader.lines().enumerate() {
            let lineno = i + 1;
            let raw = line.with_context(|| format!("reading line {lineno}"))?;
            let clean = if !bom_checked { bom_checked = true; strip_bom(&raw) } else { raw.as_str() };
            if clean.trim().is_empty() {
                continue;
            }
            match serde_json::from_str::<TrailEvent>(clean) {
                Ok(ev) => match ev.validate() {
                    Ok(()) => {
                        kept.extend_from_slice(clean.as_bytes());
                        kept.push(b'\n');
                    }
                    Err(err) => {
                        eprintln!("[forge] skip line {lineno} (schema violation): {err}");
                        skipped += 1;
                    }
                },
                Err(err) => {
                    eprintln!("[forge] skip line {lineno} (parse error): {err}");
                    skipped += 1;
                }
            }
        }
        if kept.is_empty() {
            bail!("no valid TrailEvents found in {}; skipped {skipped} lines", src.display());
        }
        if skipped > 0 {
            eprintln!("[forge] skipped {skipped} non-TrailEvent line(s); {kept_count} valid events kept",
                kept_count = kept.iter().filter(|&&b| b == b'\n').count());
        }
        forge_bytes = kept;
    } else {
        {
            let reader = BufReader::new(hot_bytes.as_slice());
            let mut bom_checked = false;
            for (i, line) in reader.lines().enumerate() {
                let lineno = i + 1;
                let raw = line.with_context(|| format!("reading line {lineno}"))?;
                let clean = if !bom_checked { bom_checked = true; strip_bom(&raw) } else { raw.as_str() };
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
        forge_bytes = hot_bytes.clone();
    }

    // Compress.
    let mut encoder = GzEncoder::new(Vec::new(), Compression::best());
    encoder
        .write_all(&forge_bytes)
        .context("gzip compression failed")?;
    let compressed = encoder.finish().context("finalizing gzip stream")?;

    // Round-trip verify before writing.
    let mut decoder = GzDecoder::new(compressed.as_slice());
    let mut roundtrip = Vec::new();
    decoder
        .read_to_end(&mut roundtrip)
        .context("gzip decompression during round-trip verify")?;

    if roundtrip != forge_bytes {
        bail!("round-trip verification failed: decompressed bytes differ from source");
    }

    // Write the cold file.
    fs::write(&dst, &compressed)
        .with_context(|| format!("writing {}", dst.display()))?;

    // Seal the hot file to prevent further appends after archiving.
    let sealed = super::hot::sealed_path(trail_dir, date);
    fs::rename(&src, &sealed)
        .with_context(|| format!("sealing {} → {}", src.display(), sealed.display()))?;
    eprintln!("sealed → {}", sealed.display());

    let ratio = if !forge_bytes.is_empty() {
        (compressed.len() as f64 / forge_bytes.len() as f64) * 100.0
    } else {
        0.0
    };

    eprintln!(
        "forged {} → {} ({} → {} bytes, {ratio:.1}%)",
        src.display(),
        dst.display(),
        forge_bytes.len(),
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
    let mut bom_checked = false;

    for (i, line) in reader.lines().enumerate() {
        let lineno = i + 1;
        let raw = line.with_context(|| format!("reading line {lineno}"))?;
        let clean = if !bom_checked { bom_checked = true; strip_bom(&raw) } else { raw.as_str() };
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
