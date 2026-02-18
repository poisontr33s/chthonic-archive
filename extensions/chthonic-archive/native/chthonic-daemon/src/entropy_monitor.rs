use std::cmp::Ordering;
use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicBool, Ordering as AtomicOrdering};
use std::sync::{Arc, RwLock};
use std::thread::{self, JoinHandle};
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use anyhow::{anyhow, Context, Result};
use reqwest::blocking::Client;
use serde::Deserialize;
use serde::Serialize;

const DEFAULT_API_BASE: &str = "https://endoflife.date/api/v1";
const DEFAULT_INTERVAL_MS: u64 = 6 * 60 * 60 * 1_000;
const TRACKED_TOOLS: [&str; 4] = ["python", "go", "rust", "solana"];

#[derive(Debug, Clone, Serialize)]
pub struct EntropyState {
    pub status: String,
    pub decay_score: f32,
    pub stale: bool,
    pub critical: bool,
    pub validator_active: bool,
    pub validator_source_mise: bool,
    pub validator_process: Option<String>,
    pub firedancer_surge: bool,
    pub simulated_tps: u32,
    pub checked_at_epoch_ms: u64,
    pub source_mise: Option<String>,
    pub auto_update: String,
    pub auto_update_enabled: bool,
    pub critical_tools: Vec<String>,
    pub tracked_tools: Vec<EntropyToolState>,
    pub warning: Option<String>,
}

#[derive(Debug, Clone, Serialize)]
pub struct EntropyToolState {
    pub tool: String,
    pub manager: String,
    pub requested: String,
    pub cycle: Option<String>,
    pub latest_cycle: Option<String>,
    pub latest_stable: bool,
    pub eol: bool,
    pub near_eol: bool,
    pub days_until_eol: Option<i64>,
    pub status: String,
    pub note: Option<String>,
}

#[derive(Debug, Clone)]
pub struct EntropyMonitorOptions {
    pub workspace: String,
    pub api_base: String,
    pub interval: Duration,
}

impl EntropyMonitorOptions {
    pub fn from_env(workspace: String) -> Self {
        let api_base = std::env::var("CHTHONIC_EOL_API_BASE")
            .ok()
            .filter(|raw| !raw.trim().is_empty())
            .map(|raw| normalize_api_base(&raw))
            .unwrap_or_else(|| DEFAULT_API_BASE.to_string());

        let interval_ms = std::env::var("CHTHONIC_ENTROPY_MONITOR_INTERVAL_MS")
            .ok()
            .and_then(|raw| raw.trim().parse::<u64>().ok())
            .map(|value| value.max(60_000))
            .unwrap_or(DEFAULT_INTERVAL_MS);

        Self {
            workspace,
            api_base,
            interval: Duration::from_millis(interval_ms),
        }
    }
}

pub struct EntropyMonitor {
    state: Arc<RwLock<EntropyState>>,
    stop: Arc<AtomicBool>,
    thread: Option<JoinHandle<()>>,
}

impl EntropyMonitor {
    pub fn start<F>(options: EntropyMonitorOptions, notify: F) -> Self
    where
        F: Fn(EntropyState) + Send + Sync + 'static,
    {
        let state = Arc::new(RwLock::new(EntropyState::stale(
            "entropy monitor booting",
            None,
            "manual",
            false,
        )));
        let stop = Arc::new(AtomicBool::new(false));

        let worker_state = Arc::clone(&state);
        let worker_stop = Arc::clone(&stop);
        let notify = Arc::new(notify);

        let thread = thread::spawn(move || {
            let client = Client::builder()
                .timeout(Duration::from_secs(8))
                .user_agent("chthonic-daemon/entropy-monitor")
                .build();

            loop {
                if worker_stop.load(AtomicOrdering::Acquire) {
                    break;
                }

                let snapshot = match &client {
                    Ok(client) => compute_entropy_state(&options, client)
                        .unwrap_or_else(|error| {
                            EntropyState::stale(
                                format!("entropy monitor failed: {error}"),
                                None,
                                "manual",
                                false,
                            )
                        }),
                    Err(error) => EntropyState::stale(
                        format!("reqwest client init failed: {error}"),
                        None,
                        "manual",
                        false,
                    ),
                };

                if let Ok(mut guard) = worker_state.write() {
                    *guard = snapshot.clone();
                }
                (notify)(snapshot);

                wait_interval(options.interval, &worker_stop);
            }
        });

        Self {
            state,
            stop,
            thread: Some(thread),
        }
    }

    pub fn snapshot(&self) -> EntropyState {
        self.state
            .read()
            .map(|state| state.clone())
            .unwrap_or_else(|_| {
                EntropyState::stale(
                    "entropy snapshot unavailable (lock poisoned)",
                    None,
                    "manual",
                    false,
                )
            })
    }
}

impl Drop for EntropyMonitor {
    fn drop(&mut self) {
        self.stop.store(true, AtomicOrdering::Release);
        if let Some(handle) = self.thread.take() {
            let _ = handle.join();
        }
    }
}

impl EntropyState {
    fn stale(
        warning: impl Into<String>,
        source_mise: Option<String>,
        auto_update: impl Into<String>,
        auto_update_enabled: bool,
    ) -> Self {
        Self {
            status: "stale".to_string(),
            decay_score: 0.5,
            stale: true,
            critical: false,
            validator_active: false,
            validator_source_mise: false,
            validator_process: None,
            firedancer_surge: false,
            simulated_tps: 0,
            checked_at_epoch_ms: now_epoch_ms(),
            source_mise,
            auto_update: auto_update.into(),
            auto_update_enabled,
            critical_tools: Vec::new(),
            tracked_tools: Vec::new(),
            warning: Some(warning.into()),
        }
    }
}

#[derive(Debug, Clone)]
struct MiseConfig {
    source: Option<PathBuf>,
    auto_update: String,
    auto_update_enabled: bool,
    tools: HashMap<String, String>,
}

#[derive(Debug, Clone)]
struct ToolPin {
    manager: String,
    requested: String,
}

#[derive(Debug, Clone, Deserialize)]
struct ApiCycle {
    #[serde(default)]
    cycle: String,
    #[serde(default)]
    eol: Option<EolField>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(untagged)]
enum EolField {
    Bool(bool),
    Date(String),
}

fn compute_entropy_state(options: &EntropyMonitorOptions, client: &Client) -> Result<EntropyState> {
    let mise = parse_mise_config(Path::new(&options.workspace))?;
    let source_mise = mise.source.as_ref().map(|path| path.display().to_string());
    let validator_source_mise = has_solana_mise_pin(&mise.tools);
    let validator_process = detect_validator_process();
    let validator_active = validator_source_mise && validator_process.is_some();
    let simulated_tps = simulated_tps_snapshot(validator_active);
    let firedancer_surge = validator_active && simulated_tps >= 220_000;

    let mut tracked_tools = Vec::new();
    let mut warning: Option<String> = None;

    for tool in TRACKED_TOOLS {
        let pin = resolve_tool_pin(tool, &mise.tools);
        match pin {
            Some(pin) => {
                let evaluated = evaluate_tool_state(
                    client,
                    &options.api_base,
                    tool,
                    &pin,
                );
                match evaluated {
                    Ok(state) => tracked_tools.push(state),
                    Err(error) => {
                        warning.get_or_insert_with(|| error.to_string());
                        tracked_tools.push(EntropyToolState {
                            tool: tool.to_string(),
                            manager: pin.manager,
                            requested: pin.requested,
                            cycle: None,
                            latest_cycle: None,
                            latest_stable: false,
                            eol: false,
                            near_eol: false,
                            days_until_eol: None,
                            status: "unknown".to_string(),
                            note: Some(error.to_string()),
                        });
                    }
                }
            }
            None => tracked_tools.push(EntropyToolState {
                tool: tool.to_string(),
                manager: "unmanaged".to_string(),
                requested: "unmanaged".to_string(),
                cycle: None,
                latest_cycle: None,
                latest_stable: false,
                eol: false,
                near_eol: false,
                days_until_eol: None,
                status: "unmanaged".to_string(),
                note: Some("no pinned tool in mise.toml".to_string()),
            }),
        }
    }

    let managed: Vec<&EntropyToolState> = tracked_tools
        .iter()
        .filter(|tool| tool.status != "unmanaged")
        .collect();

    let managed_count = managed.len() as f32;
    let eol_count = managed.iter().filter(|tool| tool.eol).count() as f32;
    let near_eol_count = managed.iter().filter(|tool| tool.near_eol).count() as f32;
    let outdated_count = managed
        .iter()
        .filter(|tool| tool.status == "outdated")
        .count() as f32;
    let unknown_count = managed
        .iter()
        .filter(|tool| tool.status == "unknown")
        .count() as f32;

    let critical_tools = managed
        .iter()
        .filter(|tool| tool.eol || tool.near_eol)
        .map(|tool| tool.tool.clone())
        .collect::<Vec<_>>();

    let (decay_score, status) = if eol_count > 0.0 {
        (1.0, "critical".to_string())
    } else if near_eol_count > 0.0 {
        (0.86, "critical".to_string())
    } else if managed_count == 0.0 {
        (0.35, "stale".to_string())
    } else if outdated_count == 0.0 && unknown_count == 0.0 {
        (0.0, "pristine".to_string())
    } else {
        let outdated_ratio = if managed_count > 0.0 {
            outdated_count / managed_count
        } else {
            0.0
        };
        let unknown_ratio = if managed_count > 0.0 {
            unknown_count / managed_count
        } else {
            0.0
        };
        let score = (0.2 + (outdated_ratio * 0.55) + (unknown_ratio * 0.15)).min(0.79);
        if unknown_count > 0.0 {
            (score.max(0.45), "stale".to_string())
        } else {
            (score, "degraded".to_string())
        }
    };

    let stale = status == "stale";
    let critical = decay_score > 0.8;

    Ok(EntropyState {
        status,
        decay_score,
        stale,
        critical,
        validator_active,
        validator_source_mise,
        validator_process,
        firedancer_surge,
        simulated_tps,
        checked_at_epoch_ms: now_epoch_ms(),
        source_mise,
        auto_update: mise.auto_update,
        auto_update_enabled: mise.auto_update_enabled,
        critical_tools,
        tracked_tools,
        warning,
    })
}

fn evaluate_tool_state(
    client: &Client,
    api_base: &str,
    tool: &str,
    pin: &ToolPin,
) -> Result<EntropyToolState> {
    let requested = pin.requested.trim();
    let (cycle, dynamic_latest) = parse_requested_cycle(tool, requested);
    if dynamic_latest {
        return Ok(EntropyToolState {
            tool: tool.to_string(),
            manager: pin.manager.clone(),
            requested: requested.to_string(),
            cycle: None,
            latest_cycle: None,
            latest_stable: true,
            eol: false,
            near_eol: false,
            days_until_eol: None,
            status: "latest".to_string(),
            note: Some("dynamic latest lane".to_string()),
        });
    }

    let products = products_for_tool(tool);
    let (product, cycles) = fetch_cycles(client, api_base, products)?;
    if cycles.is_empty() {
        return Err(anyhow!("empty endoflife payload for {product}"));
    }

    let latest_cycle = latest_supported_cycle(&cycles);
    let matched = cycle
        .as_ref()
        .and_then(|target| find_cycle(tool, target, &cycles));

    let Some(matched_cycle) = matched else {
        return Ok(EntropyToolState {
            tool: tool.to_string(),
            manager: pin.manager.clone(),
            requested: requested.to_string(),
            cycle,
            latest_cycle,
            latest_stable: false,
            eol: false,
            near_eol: false,
            days_until_eol: None,
            status: "unknown".to_string(),
            note: Some(format!("cycle not found in {product} feed")),
        });
    };

    let days_until_eol = days_until_eol(&matched_cycle.eol);
    let eol = is_eol(&matched_cycle.eol);
    let near_eol = !eol && days_until_eol.map(|days| days <= 90).unwrap_or(false);
    let latest_stable = latest_cycle
        .as_deref()
        .map(|latest| cycle_matches(tool, latest, &matched_cycle.cycle))
        .unwrap_or(false);

    let status = if eol {
        "eol"
    } else if near_eol {
        "near_eol"
    } else if latest_stable {
        "latest"
    } else {
        "outdated"
    };

    Ok(EntropyToolState {
        tool: tool.to_string(),
        manager: pin.manager.clone(),
        requested: requested.to_string(),
        cycle,
        latest_cycle,
        latest_stable,
        eol,
        near_eol,
        days_until_eol,
        status: status.to_string(),
        note: Some(format!("source={product}")),
    })
}

fn parse_mise_config(workspace: &Path) -> Result<MiseConfig> {
    let candidates = [
        workspace.join("mise.toml"),
        workspace.join(".mise.toml"),
        workspace.join(".chthonic").join("mise.toml"),
    ];

    let source = candidates.iter().find(|candidate| candidate.exists()).cloned();
    let Some(source) = source else {
        return Ok(MiseConfig {
            source: None,
            auto_update: "manual".to_string(),
            auto_update_enabled: false,
            tools: HashMap::new(),
        });
    };

    let content = fs::read_to_string(&source)
        .with_context(|| format!("failed to read {}", source.display()))?;
    let parsed: toml::Value = toml::from_str(&content)
        .with_context(|| format!("failed to parse {}", source.display()))?;

    let auto_update = parse_auto_update_mode(&parsed);
    let auto_update_enabled = auto_update == "auto";
    let tools = parse_tool_versions(&parsed);

    Ok(MiseConfig {
        source: Some(source),
        auto_update,
        auto_update_enabled,
        tools,
    })
}

fn parse_tool_versions(root: &toml::Value) -> HashMap<String, String> {
    let mut versions = HashMap::new();
    let Some(tools) = root.get("tools").and_then(|value| value.as_table()) else {
        return versions;
    };

    for (name, value) in tools {
        if let Some(version) = extract_version(value) {
            versions.insert(name.to_ascii_lowercase(), version);
        }
    }

    versions
}

fn extract_version(value: &toml::Value) -> Option<String> {
    match value {
        toml::Value::String(raw) => Some(raw.trim().to_string()),
        toml::Value::Integer(raw) => Some(raw.to_string()),
        toml::Value::Table(table) => table
            .get("version")
            .and_then(extract_version),
        _ => None,
    }
}

fn parse_auto_update_mode(root: &toml::Value) -> String {
    if let Some(mode) = root
        .get("settings")
        .and_then(|value| value.as_table())
        .and_then(|settings| settings.get("system_update"))
        .and_then(extract_auto_mode)
    {
        return mode;
    }

    if let Some(mode) = root.get("system_update").and_then(extract_auto_mode) {
        return mode;
    }

    "manual".to_string()
}

fn extract_auto_mode(value: &toml::Value) -> Option<String> {
    match value {
        toml::Value::String(raw) => {
            let normalized = raw.trim().to_ascii_lowercase();
            if normalized.is_empty() {
                None
            } else if normalized == "auto" {
                Some("auto".to_string())
            } else if normalized == "manual" {
                Some("manual".to_string())
            } else {
                Some("unknown".to_string())
            }
        }
        toml::Value::Boolean(value) => {
            if *value {
                Some("auto".to_string())
            } else {
                Some("manual".to_string())
            }
        }
        _ => None,
    }
}

fn resolve_tool_pin(tool: &str, versions: &HashMap<String, String>) -> Option<ToolPin> {
    let direct = match tool {
        "solana" => versions
            .get("solana-cli")
            .or_else(|| versions.get("solana"))
            .or_else(|| versions.get("agave"))
            .or_else(|| versions.get("firedancer")),
        _ => versions.get(tool),
    };

    if let Some(version) = direct {
        return Some(ToolPin {
            manager: tool.to_string(),
            requested: version.clone(),
        });
    }

    let alias = match tool {
        "python" => versions.get("uv").map(|version| ("uv", version)),
        "go" => versions.get("goup").map(|version| ("goup", version)),
        _ => None,
    }?;

    Some(ToolPin {
        manager: alias.0.to_string(),
        requested: alias.1.clone(),
    })
}

fn products_for_tool(tool: &str) -> &'static [&'static str] {
    match tool {
        "python" => &["python"],
        "go" => &["go"],
        "rust" => &["rust"],
        "solana" => &["solana", "agave", "solana-cli"],
        _ => &[],
    }
}

fn fetch_cycles(client: &Client, api_base: &str, products: &[&str]) -> Result<(String, Vec<ApiCycle>)> {
    let mut last_error: Option<anyhow::Error> = None;
    let base = normalize_api_base(api_base);

    for product in products {
        let url = format!("{base}/{product}.json");
        let response = match client
            .get(&url)
            .header("accept", "application/json")
            .send()
        {
            Ok(response) => response,
            Err(error) => {
                last_error = Some(anyhow!("GET {url} failed: {error}"));
                continue;
            }
        };

        if !response.status().is_success() {
            last_error = Some(anyhow!(
                "GET {url} returned {}",
                response.status(),
            ));
            continue;
        }

        let payload = response
            .json::<Vec<ApiCycle>>()
            .with_context(|| format!("failed to decode {url} JSON"))?;
        return Ok(((*product).to_string(), payload));
    }

    Err(last_error.unwrap_or_else(|| anyhow!("no products available")))
}

fn latest_supported_cycle(cycles: &[ApiCycle]) -> Option<String> {
    cycles
        .iter()
        .filter(|cycle| !is_eol(&cycle.eol))
        .filter_map(|cycle| {
            if cycle.cycle.trim().is_empty() {
                None
            } else {
                Some(cycle.cycle.clone())
            }
        })
        .max_by(|left, right| compare_cycles(left, right))
}

fn find_cycle<'a>(tool: &str, target_cycle: &str, cycles: &'a [ApiCycle]) -> Option<&'a ApiCycle> {
    cycles.iter().find(|candidate| {
        !candidate.cycle.trim().is_empty() && cycle_matches(tool, target_cycle, &candidate.cycle)
    })
}

fn cycle_matches(tool: &str, expected: &str, candidate: &str) -> bool {
    if tool == "node" || tool == "solana" {
        let expected_major = parse_major(expected);
        let candidate_major = parse_major(candidate);
        return expected_major.is_some() && expected_major == candidate_major;
    }

    normalize_cycle(candidate) == normalize_cycle(expected)
}

fn parse_requested_cycle(tool: &str, requested: &str) -> (Option<String>, bool) {
    if is_latest_alias(requested) {
        return (None, true);
    }

    let numbers = numeric_segments(requested);
    if numbers.is_empty() {
        return (None, false);
    }

    let cycle = if tool == "node" || tool == "solana" {
        numbers.first().cloned()
    } else if numbers.len() >= 2 {
        Some(format!("{}.{}", numbers[0], numbers[1]))
    } else {
        numbers.first().cloned()
    };

    (cycle, false)
}

fn normalize_cycle(raw: &str) -> String {
    let numbers = numeric_segments(raw);
    if numbers.is_empty() {
        raw.trim().to_ascii_lowercase()
    } else if numbers.len() >= 2 {
        format!("{}.{}", numbers[0], numbers[1])
    } else {
        numbers[0].clone()
    }
}

fn parse_major(raw: &str) -> Option<String> {
    numeric_segments(raw).first().cloned()
}

fn compare_cycles(left: &str, right: &str) -> Ordering {
    let left_parts = numeric_segments(left)
        .into_iter()
        .filter_map(|value| value.parse::<i32>().ok())
        .collect::<Vec<_>>();
    let right_parts = numeric_segments(right)
        .into_iter()
        .filter_map(|value| value.parse::<i32>().ok())
        .collect::<Vec<_>>();

    let width = left_parts.len().max(right_parts.len());
    for idx in 0..width {
        let left_value = *left_parts.get(idx).unwrap_or(&0);
        let right_value = *right_parts.get(idx).unwrap_or(&0);
        match left_value.cmp(&right_value) {
            Ordering::Equal => continue,
            ordering => return ordering,
        }
    }
    Ordering::Equal
}

fn numeric_segments(raw: &str) -> Vec<String> {
    let mut values = Vec::new();
    let mut current = String::new();

    for ch in raw.chars() {
        if ch.is_ascii_digit() {
            current.push(ch);
        } else if !current.is_empty() {
            values.push(std::mem::take(&mut current));
        }
    }
    if !current.is_empty() {
        values.push(current);
    }

    values
}

fn is_latest_alias(raw: &str) -> bool {
    let normalized = raw.trim().to_ascii_lowercase();
    normalized == "latest"
        || normalized == "stable"
        || normalized == "current"
        || normalized == "*"
        || normalized.contains("lts")
}

fn is_eol(value: &Option<EolField>) -> bool {
    match value {
        Some(EolField::Bool(flag)) => *flag,
        Some(EolField::Date(date)) => days_until(date).map(|days| days <= 0).unwrap_or(false),
        None => false,
    }
}

fn days_until_eol(value: &Option<EolField>) -> Option<i64> {
    match value {
        Some(EolField::Bool(flag)) => {
            if *flag {
                Some(-1)
            } else {
                None
            }
        }
        Some(EolField::Date(date)) => days_until(date),
        None => None,
    }
}

fn days_until(raw_date: &str) -> Option<i64> {
    let target_day = parse_date_epoch_day(raw_date)?;
    Some(target_day - current_epoch_day())
}

fn parse_date_epoch_day(raw: &str) -> Option<i64> {
    let date = raw.trim();
    let pieces = date.split('-').collect::<Vec<_>>();
    if pieces.len() < 3 {
        return None;
    }
    let year = pieces[0].parse::<i32>().ok()?;
    let month = pieces[1].parse::<u32>().ok()?;
    let day = pieces[2]
        .chars()
        .take_while(|ch| ch.is_ascii_digit())
        .collect::<String>()
        .parse::<u32>()
        .ok()?;
    Some(days_from_civil(year, month, day))
}

fn current_epoch_day() -> i64 {
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs() as i64;
    now / 86_400
}

fn days_from_civil(year: i32, month: u32, day: u32) -> i64 {
    let adjusted_year = year - i32::from(month <= 2);
    let era = if adjusted_year >= 0 {
        adjusted_year
    } else {
        adjusted_year - 399
    } / 400;
    let year_of_era = adjusted_year - (era * 400);
    let month_prime = month as i32 + if month > 2 { -3 } else { 9 };
    let day_of_year = ((153 * month_prime + 2) / 5) + day as i32 - 1;
    let day_of_era = year_of_era * 365 + year_of_era / 4 - year_of_era / 100 + day_of_year;
    era as i64 * 146_097 + day_of_era as i64 - 719_468
}

fn now_epoch_ms() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as u64
}

fn has_solana_mise_pin(versions: &HashMap<String, String>) -> bool {
    versions.contains_key("solana-cli")
        || versions.contains_key("solana")
        || versions.contains_key("agave")
        || versions.contains_key("firedancer")
}

fn simulated_tps_snapshot(validator_active: bool) -> u32 {
    if !validator_active {
        return 0;
    }
    let tick = (now_epoch_ms() / 1_000) as u32;
    let lane_wave = (tick % 17) * 3_700;
    165_000u32.saturating_add(lane_wave)
}

fn detect_validator_process() -> Option<String> {
    #[cfg(windows)]
    {
        use std::process::Command;
        let output = Command::new("tasklist")
            .args(["/fo", "csv", "/nh"])
            .output()
            .ok()?;
        if !output.status.success() {
            return None;
        }

        let lines = String::from_utf8_lossy(&output.stdout);
        for line in lines.lines() {
            let normalized = line.to_ascii_lowercase();
            if normalized.contains("solana-test-validator.exe") {
                return Some("solana-test-validator".to_string());
            }
            if normalized.contains("agave-validator.exe") {
                return Some("agave-validator".to_string());
            }
            if normalized.contains("fdctl.exe") {
                return Some("fdctl".to_string());
            }
        }
        None
    }

    #[cfg(not(windows))]
    {
        use std::process::Command;
        let candidates = ["solana-test-validator", "agave-validator", "fdctl"];
        for candidate in candidates {
            let status = Command::new("pgrep")
                .args(["-f", candidate])
                .status()
                .ok()?;
            if status.success() {
                return Some(candidate.to_string());
            }
        }
        None
    }
}

fn wait_interval(interval: Duration, stop: &AtomicBool) {
    let mut waited = Duration::ZERO;
    while waited < interval {
        if stop.load(AtomicOrdering::Acquire) {
            return;
        }
        let remaining = interval.saturating_sub(waited);
        let step = remaining.min(Duration::from_millis(250));
        thread::sleep(step);
        waited += step;
    }
}

fn normalize_api_base(raw: &str) -> String {
    let trimmed = raw.trim().trim_end_matches('/');
    if trimmed.ends_with("/api") {
        format!("{trimmed}/v1")
    } else {
        trimmed.to_string()
    }
}
