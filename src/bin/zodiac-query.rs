// @SID: BIN_ZODIAC_QUERY_V1
// zodiac-query — CLI that emits the current Ankhological zodiac state as JSON.
//
// Usage:
//   zodiac-query                        # bodies in signs, now (UTC)
//   zodiac-query --jd 2451545.0         # explicit Julian Day
//   zodiac-query --date 2026-06-22      # YYYY-MM-DD midnight UTC
//   zodiac-query --action ayanamsa      # just the ayanamsa value
//   zodiac-query --action boundaries    # twelve sign-boundary tropical longitudes
//
// Output: one JSON object to stdout. No other output.

use std::env;
use chthonic_archive::render::{cosmos, zodiac};

fn now_jd() -> f64 {
    use std::time::{SystemTime, UNIX_EPOCH};
    let secs = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs_f64())
        .unwrap_or(0.0);
    secs / 86400.0 + 2_440_587.5
}

fn parse_date(s: &str) -> Option<f64> {
    let parts: Vec<&str> = s.split('-').collect();
    if parts.len() != 3 { return None; }
    Some(cosmos::julian_day(
        parts[0].parse().ok()?,
        parts[1].parse().ok()?,
        parts[2].parse().ok()?,
        0, 0, 0.0,
    ))
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let mut jd = now_jd();
    let mut action = "bodies".to_string();

    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "--jd" if i + 1 < args.len() => { jd = args[i+1].parse().unwrap_or(jd); i += 2; }
            "--date" if i + 1 < args.len() => { if let Some(j) = parse_date(&args[i+1]) { jd = j; } i += 2; }
            "--action" if i + 1 < args.len() => { action = args[i+1].clone(); i += 2; }
            _ => { i += 1; }
        }
    }

    let out: serde_json::Value = match action.as_str() {
        "ayanamsa" => {
            let a = zodiac::ankhological_ayanamsa(jd);
            serde_json::json!({
                "action": "ayanamsa",
                "jd": jd,
                "ayanamsa_deg": (a * 1000.0).round() / 1000.0,
                "origin": "sirius-alcyone-midpoint-50-50",
                "precession_rate_deg_per_century": 1.396_971_2,
            })
        }
        "boundaries" => {
            let b = zodiac::sign_boundaries_tropical(jd);
            serde_json::json!({
                "action": "boundaries",
                "jd": jd,
                "boundaries": zodiac::SIGN_NAMES.iter().enumerate().map(|(k, name)| serde_json::json!({
                    "index": k,
                    "sign": name,
                    "tropical_lon_deg": (b[k] * 1000.0).round() / 1000.0,
                })).collect::<Vec<_>>(),
            })
        }
        _ => {
            let ayan = zodiac::ankhological_ayanamsa(jd);
            let bodies = zodiac::bodies_in_signs(jd);
            serde_json::json!({
                "action": "bodies",
                "jd": jd,
                "ayanamsa_deg": (ayan * 1000.0).round() / 1000.0,
                "origin": "sirius-alcyone-midpoint-50-50",
                "bodies": bodies.iter().map(|(label, _, sign, deg)| serde_json::json!({
                    "body": label,
                    "sign": sign,
                    "degree": (deg * 100.0).round() / 100.0,
                })).collect::<Vec<_>>(),
            })
        }
    };

    println!("{}", serde_json::to_string_pretty(&out).unwrap());
}
