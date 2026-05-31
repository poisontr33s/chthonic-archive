// @SID: TOOL_CHTHONIC_SCANNER_V1
// ============================================================
// chthonic-scanner — Rust port of scripts/spread-value.ts.
// Third sibling in the parallel-arsenal at extensions/.../native/,
// alongside chthonic-copilot-bridge and chthonic-acp-bridge.
//
// V2.2-parity scope (this iteration / R3.5):
//   - walkdir-based directory walk (single-threaded, matches Bun
//     baseline; parallel via ignore::WalkBuilder / jwalk / dirwalk
//     is the V2.2.5 follow-up per claude/research/ triangulation)
//   - SHA256 file fingerprinting via the `sha2` crate (SHA-NI when
//     supported at runtime; matches Bun's OpenSSL/BoringSSL parity)
//   - Magic-byte detection via `file-format` (~200 formats) plus
//     a custom overlay for ML/GPU artifacts (GGUF + safetensors)
//     not covered by the canonical library
//   - NDJSON cache at .spread/file_index.ndjson with
//     (path, size, mtime_ms) invalidation
//   - Workspace-wide SHA256 dedup map, sorted by bytes_wasted
//   - Path-dedup against nested-project double-visit (V2.2 bug-fix
//     ported from the Bun version)
//
// Reference: scripts/spread-value.ts (the proven Bun shape).
// Reference: claude/research/*.md (three-lane research triangulation
//   that informs library picks + sequencing decisions for V2.3+).
// ============================================================

use std::collections::{BTreeMap, HashMap, HashSet};
use std::fs::{self, File};
use std::io::{BufRead, BufReader, BufWriter, Read, Write};
use std::path::{Path, PathBuf};
use std::time::Instant;

use anyhow::{Context, Result};
use clap::Parser;
use file_format::FileFormat;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use tracing::{info, warn};
use walkdir::WalkDir;

// ─── Args ─────────────────────────────────────────────────────────────────

#[derive(Debug, Parser)]
#[command(
    name = "chthonic-scanner",
    about = "Polyglot spread scanner — V2.2 parity port from Bun",
)]
struct Args {
    /// Root directory to scan. Defaults to current working directory. Mutually
    /// exclusive with --workspace-file.
    #[arg(long)]
    root: Option<PathBuf>,

    /// VS Code .code-workspace file. When set, each `folders[].path` becomes
    /// a separate scan root (resolved relative to the workspace file's dir).
    /// Junction-following is implicitly disabled in this mode because the
    /// workspace file enumerates the canonical satellite set — walking junctions
    /// would double-count siblings already in the scan.
    #[arg(long)]
    workspace_file: Option<PathBuf>,

    /// Cache file path. Defaults to <root>/.spread/file_index.ndjson (single
    /// root) or to the first workspace folder's .spread dir (workspace-file mode).
    #[arg(long)]
    cache: Option<PathBuf>,

    /// Rebuild cache from scratch (ignore existing rows).
    #[arg(long)]
    rebuild_cache: bool,

    /// Minimum file size (bytes) for a duplicate cluster to be reported.
    #[arg(long, default_value_t = 1024)]
    min_dup_bytes: u64,

    /// Output path for the value manifest.
    #[arg(long)]
    output: Option<PathBuf>,

    /// Skip the full SHA256 pass (cache-load + summary only). Useful for
    /// quick re-summaries from an existing cache.
    #[arg(long)]
    summary_only: bool,

    /// Hard upper bound on file size to hash (bytes). Above this, the file
    /// is recorded but skipped from hashing.
    #[arg(long, default_value_t = 50 * 1024 * 1024)]
    max_hash_bytes: u64,
}

// ─── Workspace file parsing ───────────────────────────────────────────────

#[derive(Debug, Deserialize)]
struct WorkspaceFile {
    folders: Vec<WorkspaceFolder>,
}

#[derive(Debug, Deserialize)]
struct WorkspaceFolder {
    path: String,
    #[serde(default)]
    name: Option<String>,
}

#[derive(Debug, Clone)]
struct ScanRoot {
    name: String,         // display label (workspace folder name or basename)
    path: PathBuf,        // resolved absolute path
}

/// Parse a .code-workspace file, returning the canonical satellite scan-roots.
/// Each folders[].path is resolved relative to the workspace file's directory.
/// Skips folders that don't exist or aren't directories.
fn load_workspace_roots(workspace_file: &Path) -> Result<Vec<ScanRoot>> {
    // .code-workspace files allow // line comments — strip them before parsing.
    let raw = fs::read_to_string(workspace_file)
        .with_context(|| format!("read workspace file {}", workspace_file.display()))?;
    let stripped = strip_jsonc_comments(&raw);
    let parsed: WorkspaceFile = serde_json::from_str(&stripped)
        .with_context(|| format!("parse workspace file {}", workspace_file.display()))?;
    let workspace_dir = workspace_file.parent().unwrap_or(Path::new("."));

    let mut roots = Vec::new();
    for folder in parsed.folders {
        let resolved = workspace_dir.join(&folder.path);
        let canon = match resolved.canonicalize() {
            Ok(p) => p,
            Err(e) => {
                warn!(path = %resolved.display(), err = %e, "workspace folder skipped (canonicalize failed)");
                continue;
            }
        };
        if !canon.is_dir() {
            warn!(path = %canon.display(), "workspace folder skipped (not a directory)");
            continue;
        }
        let name = folder.name.unwrap_or_else(|| {
            canon.file_name()
                .map(|s| s.to_string_lossy().to_string())
                .unwrap_or_else(|| canon.to_string_lossy().to_string())
        });
        roots.push(ScanRoot { name, path: canon });
    }
    Ok(roots)
}

/// Minimal JSONC stripper. Handles `// line comments`, `/* block */`, and
/// trailing commas before `}` / `]` (all permitted by VS Code .code-workspace).
fn strip_jsonc_comments(s: &str) -> String {
    let bytes = s.as_bytes();
    let mut out = String::with_capacity(s.len());
    let mut i = 0;
    let mut in_string = false;
    let mut escape = false;
    while i < bytes.len() {
        let c = bytes[i];
        if in_string {
            out.push(c as char);
            if escape {
                escape = false;
            } else if c == b'\\' {
                escape = true;
            } else if c == b'"' {
                in_string = false;
            }
            i += 1;
            continue;
        }
        if c == b'"' {
            in_string = true;
            out.push(c as char);
            i += 1;
            continue;
        }
        // // line comment
        if c == b'/' && i + 1 < bytes.len() && bytes[i + 1] == b'/' {
            while i < bytes.len() && bytes[i] != b'\n' { i += 1; }
            continue;
        }
        // /* block comment */
        if c == b'/' && i + 1 < bytes.len() && bytes[i + 1] == b'*' {
            i += 2;
            while i + 1 < bytes.len() && !(bytes[i] == b'*' && bytes[i + 1] == b'/') {
                i += 1;
            }
            i += 2;
            continue;
        }
        out.push(c as char);
        i += 1;
    }
    // Second pass: drop trailing commas before } or ]
    // (only safe outside strings; we just produced a comment-free `out`, but
    // strings inside it are intact, so we re-track string state here too.)
    let mut final_out = String::with_capacity(out.len());
    let chars: Vec<char> = out.chars().collect();
    let mut j = 0;
    let mut in_str = false;
    let mut esc = false;
    while j < chars.len() {
        let ch = chars[j];
        if in_str {
            final_out.push(ch);
            if esc { esc = false; }
            else if ch == '\\' { esc = true; }
            else if ch == '"' { in_str = false; }
            j += 1;
            continue;
        }
        if ch == '"' {
            in_str = true;
            final_out.push(ch);
            j += 1;
            continue;
        }
        // Trailing comma: skip if followed by whitespace then } or ]
        if ch == ',' {
            let mut k = j + 1;
            while k < chars.len() && chars[k].is_whitespace() { k += 1; }
            if k < chars.len() && (chars[k] == '}' || chars[k] == ']') {
                j += 1; // skip the comma
                continue;
            }
        }
        final_out.push(ch);
        j += 1;
    }
    final_out
}

// ─── Skip sets (filesystem-direct, no git involvement) ────────────────────

const SKIP_DIRS: &[&str] = &[
    "node_modules", "target", "dist", "build", "out", ".git", ".next", ".nuxt",
    ".cache", ".turbo", ".vite", ".parcel-cache", "__pycache__", ".venv", "venv",
    "vendor", "coverage", ".gradle", ".idea", "tmp", ".tmp",
];

const VENDORED_PATH_PATTERNS: &[&str] = &[
    "vcpkg/buildtrees", "vcpkg/packages", "vcpkg/installed",
    ".cargo/registry", ".cargo/git/checkouts",
    "rv/library/", "rv-test-rubies", "/buildtrees/",
    "/.rustup/", "AppData/Local/Programs/", "AppData/Roaming/",
    "/site-packages/", "/.gem/", "/Library/Caches/",
];

fn is_vendored(path: &Path) -> bool {
    let s = path.to_string_lossy().replace('\\', "/");
    VENDORED_PATH_PATTERNS.iter().any(|p| s.contains(p))
}

fn is_skip_dir(name: &str) -> bool {
    if name.starts_with('.') && name != ".github" && name != ".cargo" {
        return true;
    }
    SKIP_DIRS.contains(&name)
}

// ─── Bucket classification ────────────────────────────────────────────────

fn bucket_of(ext: &str) -> &'static str {
    // Coarse bucketing for dedup/UI purposes; full classification lives in
    // spread-sweep. Source list is intentionally a superset of common
    // programming languages seen in the workspace census.
    let source = [
        "ts", "tsx", "mts", "cts", "js", "jsx", "mjs", "cjs",
        "rs", "c", "cc", "cpp", "cxx", "h", "hpp", "hh", "hxx", "inl",
        "cu", "cuh", "glsl", "vert", "frag", "comp", "hlsl", "wgsl", "metal",
        "py", "pyi", "pyx", "pxd", "go", "rb", "swift", "kt", "java", "cs",
        "zig", "lua", "dart", "sh", "ps1", "bat", "awk", "hbs",
    ];
    let doc = ["md", "mdx", "rst", "txt", "adoc"];
    let config = [
        "toml", "yaml", "yml", "json", "jsonc", "lock", "ini", "cfg",
        "meta", "asmdef", "uss",
    ];
    let asset = [
        "png", "jpg", "jpeg", "gif", "webp", "svg", "bmp",
        "ttf", "otf", "woff", "woff2", "mp3", "mp4", "wav", "ogg",
    ];
    let binary = [
        "exe", "dll", "so", "dylib", "lib", "a", "o", "bin", "dat",
        "spv", "hsaco", "pyd", "safetensors", "gguf", "pt", "pth", "onnx",
        "ckpt", "node", "sqlite", "db",
    ];
    let ext = ext.trim_start_matches('.').to_ascii_lowercase();
    if source.contains(&ext.as_str()) { return "source"; }
    if doc.contains(&ext.as_str())    { return "doc"; }
    if config.contains(&ext.as_str()) { return "config"; }
    if asset.contains(&ext.as_str())  { return "asset"; }
    if binary.contains(&ext.as_str()) { return "binary"; }
    "unknown"
}

// ─── Magic detection (file-format + ML overlay) ───────────────────────────

/// Detect ML/GPU artifact formats not covered by `file-format`. Returns
/// `Some(name)` when matched, `None` otherwise.
///
/// Coverage per research triangulation:
///   - GGUF: 4-byte magic 0x47 0x47 0x55 0x46 ("GGUF")
///   - safetensors: 8-byte little-endian u64 header-length prefix, then
///     UTF-8 JSON starting with '{' (0x7B) at byte 8
fn detect_ml_artifact(first_bytes: &[u8]) -> Option<&'static str> {
    if first_bytes.len() >= 4 && &first_bytes[..4] == b"GGUF" {
        return Some("GGUF model");
    }
    if first_bytes.len() >= 9 && first_bytes[8] == 0x7B {
        // Validate the header-length is plausible (< 1 GiB upper bound)
        let len_le = u64::from_le_bytes([
            first_bytes[0], first_bytes[1], first_bytes[2], first_bytes[3],
            first_bytes[4], first_bytes[5], first_bytes[6], first_bytes[7],
        ]);
        if len_le > 0 && len_le < (1 << 30) {
            return Some("safetensors");
        }
    }
    None
}

fn detect_magic(path: &Path, size: u64) -> Option<String> {
    if size == 0 {
        return Some("empty".to_string());
    }
    let mut buf = vec![0u8; std::cmp::min(512, size as usize)];
    let mut f = match File::open(path) {
        Ok(f) => f,
        Err(_) => return None,
    };
    if f.read_exact(&mut buf).is_err() {
        return None;
    }
    // ML/GPU overlay first — `file-format` doesn't know GGUF or safetensors
    if let Some(name) = detect_ml_artifact(&buf) {
        return Some(name.to_string());
    }
    // Canonical pass via file-format
    let detected = FileFormat::from_bytes(&buf);
    if detected != FileFormat::ArbitraryBinaryData {
        return Some(detected.name().to_string());
    }
    // Text vs binary heuristic — null byte in first 512 → binary
    if buf.iter().any(|&b| b == 0) {
        Some("unknown-binary".to_string())
    } else {
        Some("unknown-text".to_string())
    }
}

// ─── Hashing ──────────────────────────────────────────────────────────────

fn sha256_of_file(path: &Path, size: u64, max_bytes: u64) -> Option<String> {
    if size == 0 {
        return Some("EMPTY_FILE_SHA256".to_string());
    }
    if size > max_bytes {
        return None;
    }
    let mut f = match File::open(path) {
        Ok(f) => f,
        Err(_) => return None,
    };
    let mut hasher = Sha256::new();
    let mut buf = vec![0u8; 64 * 1024];
    loop {
        let n = match f.read(&mut buf) {
            Ok(0) => break,
            Ok(n) => n,
            Err(_) => return None,
        };
        hasher.update(&buf[..n]);
    }
    Some(format!("{:x}", hasher.finalize()))
}

// ─── Cache (NDJSON) ───────────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
struct CacheRow {
    path: String,
    size: u64,
    mtime_ms: i64,
    sha256: String,
    bucket: String,
    #[serde(skip_serializing_if = "Option::is_none", default)]
    magic: Option<String>,
}

fn load_cache(path: &Path) -> HashMap<String, CacheRow> {
    let mut map = HashMap::new();
    let f = match File::open(path) {
        Ok(f) => f,
        Err(_) => return map,
    };
    let reader = BufReader::new(f);
    for line in reader.lines().map_while(Result::ok) {
        if line.trim().is_empty() { continue; }
        if let Ok(row) = serde_json::from_str::<CacheRow>(&line) {
            map.insert(row.path.clone(), row);
        }
    }
    map
}

fn write_cache(path: &Path, rows: impl IntoIterator<Item = CacheRow>) -> Result<()> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).ok();
    }
    let f = File::create(path).with_context(|| format!("create cache {}", path.display()))?;
    let mut w = BufWriter::new(f);
    for row in rows {
        let line = serde_json::to_string(&row)?;
        writeln!(w, "{line}")?;
    }
    Ok(())
}

// ─── Walking + per-file scan ──────────────────────────────────────────────

#[derive(Debug, Clone)]
struct Visit {
    path: PathBuf,
    size: u64,
    mtime_ms: i64,
    sha256: Option<String>,
    bucket: String,
    magic: Option<String>,
    from_cache: bool,
}

fn mtime_ms_of(meta: &fs::Metadata) -> i64 {
    use std::time::UNIX_EPOCH;
    meta.modified()
        .ok()
        .and_then(|m| m.duration_since(UNIX_EPOCH).ok())
        .map(|d| d.as_millis() as i64)
        .unwrap_or(0)
}

fn scan_root(
    root: &Path,
    cache: &HashMap<String, CacheRow>,
    rebuild_cache: bool,
    max_hash_bytes: u64,
    follow_links: bool,
) -> (Vec<Visit>, u64, u64) {
    // Returns (visits, cache_hits, cache_misses)
    let mut visits = Vec::new();
    let mut hits = 0u64;
    let mut misses = 0u64;

    // follow_links semantic:
    //   - true:  single-root mode (V2.2 parity); follows `*-live` symlinks
    //            into sibling projects. Matches Bun's readdirSync behavior.
    //   - false: workspace-file mode; each satellite walked from its own
    //            root, so following junctions would double-count siblings
    //            already in the scan set.
    // walkdir's follow_links(true) internally detects loops and yields an
    // error which our filter_map(Result::ok) discards silently.
    let walker = WalkDir::new(root)
        .follow_links(follow_links)
        .into_iter()
        .filter_entry(|e| {
            let name = e.file_name().to_string_lossy().to_string();
            // Always allow the root itself
            if e.depth() == 0 { return true; }
            // Apply skip-dir + vendored-path filters
            if e.file_type().is_dir() {
                if is_skip_dir(&name) { return false; }
                if is_vendored(e.path()) { return false; }
            }
            true
        });

    for entry in walker.filter_map(Result::ok) {
        if !entry.file_type().is_file() { continue; }
        let path = entry.path().to_path_buf();
        let meta = match entry.metadata() {
            Ok(m) => m,
            Err(_) => continue,
        };
        let size = meta.len();
        let mtime_ms = mtime_ms_of(&meta);
        let path_key = path.to_string_lossy().to_string();

        let ext = path
            .extension()
            .map(|e| e.to_string_lossy().to_string())
            .unwrap_or_default();
        let bucket = bucket_of(&ext).to_string();

        // Cache lookup
        if !rebuild_cache {
            if let Some(cached) = cache.get(&path_key) {
                if cached.size == size && cached.mtime_ms == mtime_ms {
                    hits += 1;
                    visits.push(Visit {
                        path: path.clone(),
                        size,
                        mtime_ms,
                        sha256: Some(cached.sha256.clone()),
                        bucket: cached.bucket.clone(),
                        magic: cached.magic.clone(),
                        from_cache: true,
                    });
                    continue;
                }
            }
        }

        // Cache miss — do the work
        misses += 1;
        let sha = sha256_of_file(&path, size, max_hash_bytes);
        let magic = if bucket == "unknown" || bucket == "binary" {
            detect_magic(&path, size)
        } else {
            None
        };
        visits.push(Visit {
            path,
            size,
            mtime_ms,
            sha256: sha,
            bucket,
            magic,
            from_cache: false,
        });
    }

    (visits, hits, misses)
}

// ─── Dedup map ────────────────────────────────────────────────────────────

#[derive(Debug, Serialize)]
struct DupCluster {
    sha256: String,
    byte_size: u64,
    occurrences: usize,
    bytes_wasted: u64,
    paths: Vec<String>,
    bucket: String,
}

fn build_dup_map(visits: &[Visit]) -> Vec<DupCluster> {
    let mut by_hash: HashMap<String, (u64, String, Vec<String>)> = HashMap::new();
    for v in visits {
        let sha = match &v.sha256 {
            Some(s) if s != "EMPTY_FILE_SHA256" => s,
            _ => continue,
        };
        if v.size == 0 { continue; }
        let entry = by_hash.entry(sha.clone())
            .or_insert_with(|| (v.size, v.bucket.clone(), Vec::new()));
        entry.2.push(v.path.to_string_lossy().to_string());
    }
    let mut clusters: Vec<DupCluster> = by_hash
        .into_iter()
        .filter(|(_, (_, _, paths))| paths.len() >= 2)
        .map(|(sha, (size, bucket, paths))| DupCluster {
            sha256: sha,
            byte_size: size,
            occurrences: paths.len(),
            bytes_wasted: size * (paths.len() as u64 - 1),
            paths,
            bucket,
        })
        .collect();
    clusters.sort_by(|a, b| b.bytes_wasted.cmp(&a.bytes_wasted));
    clusters
}

// ─── Output ───────────────────────────────────────────────────────────────

#[derive(Debug, Serialize)]
struct OutputManifest<'a> {
    generated_at: String,
    mode: String,                          // "single-root" | "workspace-file"
    root: String,                          // primary/first root path
    roots: Vec<RootSummary>,               // all scanned roots with per-root file count
    total_files: usize,
    total_bytes: u64,
    cache: CacheStats,
    bucket_totals: &'a BTreeMap<String, u64>,
    bucket_bytes: &'a BTreeMap<String, u64>,
    duplicate_clusters: &'a [DupCluster],
    wasted_bytes_total: u64,
    elapsed_secs: f64,
}

#[derive(Debug, Serialize)]
struct RootSummary {
    name: String,
    path: String,
    file_count: usize,
}

#[derive(Debug, Serialize)]
struct CacheStats {
    initial_rows: usize,
    updated_rows: usize,
    cache_hits: u64,
    cache_misses: u64,
    hit_rate: f64,
}

fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env().unwrap_or_else(|_| {
                tracing_subscriber::EnvFilter::new("chthonic_scanner=info")
            }),
        )
        .with_writer(std::io::stderr)
        .init();

    let args = Args::parse();

    // Resolve scan roots. workspace-file mode wins over --root if both passed.
    let (roots, follow_links, mode): (Vec<ScanRoot>, bool, &'static str) =
        if let Some(workspace_file) = &args.workspace_file {
            let canon = workspace_file.canonicalize()
                .unwrap_or_else(|_| workspace_file.clone());
            let roots = load_workspace_roots(&canon)
                .with_context(|| format!("load workspace file {}", canon.display()))?;
            info!(
                workspace_file = %canon.display(),
                root_count = roots.len(),
                "workspace-file mode: junction-following disabled to avoid double-walking"
            );
            (roots, false, "workspace-file")
        } else {
            let root = match args.root.clone() {
                Some(r) => r,
                None => std::env::current_dir().context("Failed to read current_dir")?,
            };
            let canon = root.canonicalize().unwrap_or(root);
            let name = canon.file_name()
                .map(|s| s.to_string_lossy().to_string())
                .unwrap_or_else(|| canon.to_string_lossy().to_string());
            (vec![ScanRoot { name, path: canon }], true, "single-root")
        };

    if roots.is_empty() {
        anyhow::bail!("no scan roots resolved");
    }

    // Cache path: defaults to first root's .spread/file_index.ndjson
    let cache_path = args
        .cache
        .clone()
        .unwrap_or_else(|| roots[0].path.join(".spread").join("file_index.ndjson"));
    let output_path = args
        .output
        .clone()
        .unwrap_or_else(|| roots[0].path.join("manifest").join("spread_value.json"));

    info!(
        mode = mode,
        cache = %cache_path.display(),
        output = %output_path.display(),
        rebuild_cache = args.rebuild_cache,
        summary_only = args.summary_only,
        max_hash_mib = args.max_hash_bytes / 1024 / 1024,
        "chthonic-scanner R3.5 starting"
    );
    for root in &roots {
        info!(name = %root.name, path = %root.path.display(), "scan root");
    }

    if args.summary_only {
        warn!("--summary-only is recognized but not yet implemented in R3.5; running full scan");
    }

    let cache = if args.rebuild_cache {
        HashMap::new()
    } else {
        load_cache(&cache_path)
    };
    let initial_cache_size = cache.len();
    info!(rows = initial_cache_size, "cache loaded");

    let started = Instant::now();
    let mut visits: Vec<Visit> = Vec::new();
    let mut per_root_visits: Vec<(String, usize)> = Vec::new();
    let mut hits = 0u64;
    let mut misses = 0u64;
    for root in &roots {
        let (root_visits, h, m) = scan_root(&root.path, &cache, args.rebuild_cache, args.max_hash_bytes, follow_links);
        let count = root_visits.len();
        info!(name = %root.name, files = count, "root walked");
        visits.extend(root_visits);
        per_root_visits.push((root.name.clone(), count));
        hits += h;
        misses += m;
    }
    let elapsed = started.elapsed().as_secs_f64();

    // Path-dedup (port of the V2.2 bug-fix: nested-project walks can visit the
    // same file twice). With single-root scan + filter_entry walking, this is
    // mostly defensive — the same path shouldn't appear twice from one root —
    // but we keep the safety net.
    let mut seen_paths = HashSet::new();
    let unique_visits: Vec<&Visit> = visits
        .iter()
        .filter(|v| seen_paths.insert(v.path.clone()))
        .collect();

    // Update cache map with current state
    let mut updated_cache: HashMap<String, CacheRow> = cache.clone();
    for v in &visits {
        let Some(sha) = &v.sha256 else { continue };
        updated_cache.insert(
            v.path.to_string_lossy().to_string(),
            CacheRow {
                path: v.path.to_string_lossy().to_string(),
                size: v.size,
                mtime_ms: v.mtime_ms,
                sha256: sha.clone(),
                bucket: v.bucket.clone(),
                magic: v.magic.clone(),
            },
        );
    }
    let updated_rows = updated_cache.len();
    write_cache(&cache_path, updated_cache.values().cloned())
        .with_context(|| format!("write cache {}", cache_path.display()))?;

    // Aggregations on unique_visits
    let mut bucket_totals: BTreeMap<String, u64> = BTreeMap::new();
    let mut bucket_bytes: BTreeMap<String, u64> = BTreeMap::new();
    let mut total_bytes = 0u64;
    for v in &unique_visits {
        *bucket_totals.entry(v.bucket.clone()).or_insert(0) += 1;
        *bucket_bytes.entry(v.bucket.clone()).or_insert(0) += v.size;
        total_bytes += v.size;
    }

    let dup_clusters: Vec<DupCluster> = build_dup_map(
        &unique_visits.iter().map(|&v| v.clone()).collect::<Vec<_>>(),
    )
    .into_iter()
    .filter(|c| c.byte_size >= args.min_dup_bytes)
    .collect();
    let wasted_bytes_total: u64 = dup_clusters.iter().map(|c| c.bytes_wasted).sum();

    let cache_stats = CacheStats {
        initial_rows: initial_cache_size,
        updated_rows,
        cache_hits: hits,
        cache_misses: misses,
        hit_rate: if !unique_visits.is_empty() {
            hits as f64 / unique_visits.len() as f64
        } else {
            0.0
        },
    };

    // Build per-root summary
    let root_summaries: Vec<RootSummary> = roots.iter().zip(per_root_visits.iter())
        .map(|(r, (_, count))| RootSummary {
            name: r.name.clone(),
            path: r.path.to_string_lossy().to_string(),
            file_count: *count,
        })
        .collect();

    // Write output manifest
    let manifest = OutputManifest {
        generated_at: chrono::Utc::now().to_rfc3339(),
        mode: mode.to_string(),
        root: roots[0].path.to_string_lossy().to_string(),
        roots: root_summaries,
        total_files: unique_visits.len(),
        total_bytes,
        cache: cache_stats,
        bucket_totals: &bucket_totals,
        bucket_bytes: &bucket_bytes,
        duplicate_clusters: &dup_clusters,
        wasted_bytes_total,
        elapsed_secs: elapsed,
    };
    if let Some(parent) = output_path.parent() {
        fs::create_dir_all(parent).ok();
    }
    let f = File::create(&output_path)
        .with_context(|| format!("create output {}", output_path.display()))?;
    serde_json::to_writer_pretty(BufWriter::new(f), &manifest)?;

    // Stdout summary
    println!();
    println!("=== chthonic-scanner R3.5 summary ({}) ===", mode);
    println!(
        "Scanned: {} files  ({:.1} MiB)  in {:.2}s",
        unique_visits.len(),
        total_bytes as f64 / 1024.0 / 1024.0,
        elapsed
    );
    println!(
        "Cache:   {} hits / {} fresh  ({:.1}% hit rate)",
        hits, misses, manifest.cache.hit_rate * 100.0
    );
    if roots.len() > 1 {
        println!();
        println!("Per-satellite file counts:");
        for r in &manifest.roots {
            println!("  {:>7} files  {}", r.file_count, r.name);
        }
    }
    println!();
    println!("Bucket distribution (files / bytes):");
    for (b, n) in &bucket_totals {
        let bytes = bucket_bytes.get(b).copied().unwrap_or(0);
        println!(
            "  {:<8} {:>7} files  {:>8.1} MiB",
            b, n, bytes as f64 / 1024.0 / 1024.0
        );
    }

    if !dup_clusters.is_empty() {
        println!();
        println!(
            "Duplicate clusters ({}, >= {} bytes/file, sorted by waste):",
            dup_clusters.len(), args.min_dup_bytes
        );
        println!(
            "Total wasted bytes from duplicates: {:.2} MiB",
            wasted_bytes_total as f64 / 1024.0 / 1024.0
        );
        println!();
        for c in dup_clusters.iter().take(15) {
            println!(
                "  {}x {:.1}KiB -> {:.1}KiB wasted  [{}]",
                c.occurrences,
                c.byte_size as f64 / 1024.0,
                c.bytes_wasted as f64 / 1024.0,
                c.bucket
            );
            for p in c.paths.iter().take(3) {
                println!("    {p}");
            }
            if c.paths.len() > 3 {
                println!("    ... +{} more copies", c.paths.len() - 3);
            }
        }
        if dup_clusters.len() > 15 {
            println!(
                "  ... {} more clusters (full list in {})",
                dup_clusters.len() - 15,
                output_path.display()
            );
        }
    } else {
        println!();
        println!("No duplicate clusters above threshold.");
    }

    println!();
    println!("Wrote {}", output_path.display());
    println!("Cache: {} ({} rows)", cache_path.display(), updated_rows);

    Ok(())
}
