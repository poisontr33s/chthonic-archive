// @SID: TOOL_CHTHONIC_MCP_CANON_V1
// ============================================================
// canon — the absorbed logic of three former bun MCP servers.
//
// `ssot` (scripts/mcp-ssot.ts), `sourcer` (scripts/mcp-sourcer.ts) and
// `asc-injector` (scripts/mcp-asc-injector.ts) ran as three standalone
// bun processes serving ten tools between them. Measured 2026-08-09,
// single-instance: 110 + 110 + 113 MB = 333 MB, of which essentially all
// is three copies of the bun runtime — the servers themselves are thin
// wrappers that shell out to `uv`/`cargo`/`bun` and pass JSON through.
// They also read the same 1.27MB catalyst, so running them as strangers
// meant holding that context three times.
//
// Absorbed here because they are one family: every tool below answers a
// question about .chthonic/SSOT.md or the canon derived from it.
//
// Deliberately NOT reimplemented: the Python/Rust engines they wrap
// (catalyst_lint.py, ssot_loremaster.py, dsl-full-smoke, sourcer-sdk.ts)
// remain the source of truth. This module only spawns and shapes.
// ============================================================

use std::path::{Path, PathBuf};
use std::process::Stdio;

use tokio::process::Command;

/// Resolve the catalyst path: SSOT_PATH env wins, else the canon under the repo.
pub fn ssot_path(repo_root: &Path) -> PathBuf {
    if let Ok(p) = std::env::var("SSOT_PATH") {
        let p = PathBuf::from(&p);
        return if p.is_absolute() { p } else { repo_root.join(p) };
    }
    repo_root.join(".chthonic").join("SSOT.md")
}

/// Spawn a command in the repo root and capture stdout.
///
/// Non-zero exit is NOT an error by itself: `catalyst_lint.py` exits 1 when it
/// finds violations while still writing valid JSON to stdout, and the bun
/// original relied on that. Only an empty stdout is treated as failure, and the
/// stderr tail is carried into the message so the cause is visible.
pub async fn run_capture(
    repo_root: &Path,
    program: &str,
    args: &[&str],
) -> Result<String, String> {
    let mut cmd = Command::new(program);
    for a in args {
        cmd.arg(a);
    }
    let output = cmd
        .current_dir(repo_root)
        .env("NO_COLOR", "1")
        .env("PYTHONUTF8", "1")
        .stdin(Stdio::null())
        .output()
        .await
        .map_err(|e| format!("failed to spawn {program}: {e}"))?;

    let stdout = String::from_utf8_lossy(&output.stdout).trim().to_string();
    if !stdout.is_empty() {
        return Ok(stdout);
    }
    let stderr = String::from_utf8_lossy(&output.stderr);
    let tail: String = stderr.lines().rev().take(6).collect::<Vec<_>>().join("\n");
    Err(format!(
        "{program} produced no stdout (exit {}). stderr tail:\n{}",
        output.status.code().unwrap_or(-1),
        tail.trim()
    ))
}

// ── ssot_outline ────────────────────────────────────────────────────────────

#[derive(serde::Serialize)]
pub struct Heading {
    pub line: usize,
    pub level: usize,
    pub title: String,
}

/// Markdown header map, fenced code blocks excluded so ``` blocks containing
/// `#` comments do not register as sections.
pub fn outline(text: &str, max_level: usize) -> Vec<Heading> {
    let mut out = Vec::new();
    let mut in_fence = false;
    for (i, line) in text.lines().enumerate() {
        if line.trim_start().starts_with("```") {
            in_fence = !in_fence;
            continue;
        }
        if in_fence {
            continue;
        }
        let trimmed = line.trim_end();
        let hashes = trimmed.chars().take_while(|c| *c == '#').count();
        if hashes == 0 || hashes > 6 || hashes > max_level {
            continue;
        }
        let rest = &trimmed[hashes..];
        if !rest.starts_with(' ') {
            continue; // "#hashtag" is not a header
        }
        let title = rest.trim();
        if title.is_empty() {
            continue;
        }
        out.push(Heading {
            line: i + 1,
            level: hashes,
            title: title.chars().take(160).collect(),
        });
    }
    out
}

// ── ssot_parse_frontier ─────────────────────────────────────────────────────

/// Pull `key`'s value out of a line shaped `--> 12:34` / `= expected foo`.
fn after_marker<'a>(hay: &'a str, marker: &str) -> Option<&'a str> {
    hay.lines()
        .find(|l| l.contains(marker))
        .and_then(|l| l.split_once(marker))
        .map(|(_, rest)| rest.trim())
}

/// Shape dsl-full-smoke output into the frontier verdict, carrying the same
/// diagnosis/next-action classification the bun server compounded onto it:
/// an odd count of `**` outside code spans means an orphan bold ran across a
/// newline, which is a content defect; anything else is a grammar gap.
pub fn parse_frontier(tool_output: &str, file_text: Option<&str>) -> serde_json::Value {
    if tool_output.contains("PARSE: OK") {
        return serde_json::json!({ "status": "OK" });
    }
    let mut v = serde_json::json!({ "status": "FAIL" });
    let m = v.as_object_mut().expect("json object");

    if let Some(pos) = after_marker(tool_output, "-->") {
        let mut it = pos.split(':');
        if let (Some(l), Some(c)) = (it.next(), it.next()) {
            if let Ok(n) = l.trim().parse::<usize>() {
                m.insert("fail_line".into(), n.into());
            }
            let col: String = c.trim().chars().take_while(|ch| ch.is_ascii_digit()).collect();
            if let Ok(n) = col.parse::<usize>() {
                m.insert("fail_col".into(), n.into());
            }
        }
    }
    if let Some(exp) = after_marker(tool_output, "expected ") {
        m.insert("expected".into(), exp.to_string().into());
    }
    if let Some(pre) = after_marker(tool_output, "First failing prefix: lines 1..") {
        let n: String = pre.chars().take_while(|c| c.is_ascii_digit()).collect();
        if let Ok(n) = n.parse::<usize>() {
            m.insert("first_failing_prefix".into(), n.into());
        }
    }

    let probe = m
        .get("first_failing_prefix")
        .or_else(|| m.get("fail_line"))
        .and_then(|x| x.as_u64())
        .map(|x| x as usize);

    if let (Some(probe), Some(text)) = (probe, file_text) {
        if let Some(raw) = text.lines().nth(probe.saturating_sub(1)) {
            let line_text: String = raw.trim().chars().take(300).collect();
            m.insert("line_text".into(), line_text.clone().into());

            // Strip inline code spans so a literal `**` (e.g. an applyTo: "**"
            // glob) is not counted as structural emphasis.
            let mut structural = String::new();
            let mut in_code = false;
            for ch in line_text.chars() {
                if ch == '`' {
                    in_code = !in_code;
                    continue;
                }
                if !in_code {
                    structural.push(ch);
                }
            }
            let bold_markers = structural.matches("**").count();
            if bold_markers % 2 == 1 {
                m.insert("diagnosis".into(), "content-defect: unbalanced bold — an orphan ** opens a bold that runs across newlines and derails the parse downstream".into());
                m.insert("next_action".into(), format!("fix bold on L{probe} (drop the stray ** if a header; restore the **(...)** pair if list/prose), then re-run. ssot_lint has the full set.").into());
            } else {
                let expected = m.get("expected").and_then(|e| e.as_str()).unwrap_or("?").to_string();
                m.insert("diagnosis".into(), format!("structural: parser reached '{expected}' and stopped — a construct the grammar lacks, or a non-bold malformation").into());
                m.insert("next_action".into(), format!("read L{probe}: if it is a real catalyst construct, extend .chthonic/grammar/chthonic.peg (rewindable via dsl_iteration_check); if a typo/malformation, repair the line.").into());
            }
        }
    }
    v
}

// ── inject_asc_context ──────────────────────────────────────────────────────

/// Extract `### <section>. …` up to the next `###`.
///
/// Returns None when the section is absent. The bun original returned the
/// string "Section X not found. Injecting full SSOT." and then did NOT inject
/// the full SSOT — a message that described an action it never took. The caller
/// here reports the miss honestly instead.
pub fn extract_section(text: &str, section: &str) -> Option<String> {
    let needle = format!("### {section}.");
    let start = text.find(&needle)?;
    let rest = &text[start + needle.len()..];
    let end = rest.find("###").map(|e| start + needle.len() + e).unwrap_or(text.len());
    Some(text[start..end].trim_end().to_string())
}

/// Section headings present in the catalyst, for an honest "not found" reply.
pub fn available_sections(text: &str) -> Vec<String> {
    let mut out = Vec::new();
    for line in text.lines() {
        if let Some(rest) = line.strip_prefix("### ") {
            if let Some((head, _)) = rest.split_once('.') {
                let head = head.trim();
                if !head.is_empty() && head.len() <= 12 && !out.iter().any(|x| x == head) {
                    out.push(head.to_string());
                }
            }
        }
    }
    out
}
