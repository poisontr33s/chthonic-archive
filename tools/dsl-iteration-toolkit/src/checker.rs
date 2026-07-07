// IterationChecker — orchestrates catalog test + coverage + ledger append.
// One-stop check per iteration.

use anyhow::{Context, Result};
use chrono::Utc;
use std::fs;
use std::path::PathBuf;

use crate::catalog::{Catalog, PatternResult};
use crate::checkpoint::{Checkpoint, DEFAULT_RETENTION};
use crate::config::Config;
use crate::coverage::{run_coverage, BacktickSurface, BoldSurface, CoverageReport, FencedSurface, ParenSurface, Surface};
use crate::grammar::Grammar;
use crate::ledger::{Ledger, LedgerRow};

pub struct IterationChecker {
    pub config: Config,
    pub config_dir: PathBuf,
}

impl IterationChecker {
    pub fn new(config: Config, config_dir: PathBuf) -> Self {
        Self { config, config_dir }
    }

    pub fn from_config_path(path: impl AsRef<std::path::Path>) -> Result<Self> {
        let path = path.as_ref();
        let config = Config::load(path)?;
        let config_dir = path.parent().unwrap_or_else(|| std::path::Path::new(".")).to_path_buf();
        Ok(Self::new(config, config_dir))
    }

    fn abs(&self, p: &std::path::Path) -> PathBuf {
        if p.is_absolute() { p.to_path_buf() } else { self.config_dir.join(p) }
    }

    /// Run a full iteration check: grammar load + catalog test + coverage
    /// (per configured surfaces) + ledger append. Checkpoints all state files
    /// BEFORE mutating them so `dsl-iter revert` can roll back this exact run.
    pub fn check(&self) -> Result<CheckReport> {
        let grammar = Grammar::load(self.abs(&self.config.grammar_path))?;
        let corpus_path = self.abs(&self.config.corpus_path);
        let corpus = fs::read_to_string(&corpus_path)
            .with_context(|| format!("read corpus {}", corpus_path.display()))?;

        // Checkpoint state files before any mutation. Loop C: step-level
        // rewindability complementing git (commit-level) + ledger (run-level).
        let manifest_dir = self.abs(&self.config.manifest_dir);
        let ledger_path_for_ckpt = manifest_dir.join(format!(
            "{}_iteration_history.ndjson", self.config.project_name));
        let mut files_to_snapshot = vec![ledger_path_for_ckpt.clone()];
        for surface_name in &self.config.coverage_surfaces {
            files_to_snapshot.push(manifest_dir.join(format!(
                "{}_coverage_{}_audit.json", self.config.project_name, surface_name)));
        }
        let checkpoint = Checkpoint::new(&manifest_dir);
        let checkpoint_manifest = checkpoint.create(
            &files_to_snapshot,
            "pre-check",
            git_head(&self.config_dir),
            Some(grammar.hash()),
            Some(&self.config.project_name),
        )?;
        // Prune to keep the checkpoint history bounded.
        checkpoint.prune(DEFAULT_RETENTION).ok();

        // Pattern catalog test — always parse against the grammar's entry rule
        // ("program"), then check the parse tree for expected_top_rule appearing
        // anywhere. Special "DEFERRED" expected_top_rule means we're not asserting
        // a specific rule (used for architectural-decision patterns).
        let catalog_path = self.abs(&self.config.catalog_path);
        let mut pattern_results = Vec::new();
        if catalog_path.exists() {
            let catalog = Catalog::load(&catalog_path)?;
            pattern_results = catalog.test_all(|p| {
                match grammar.parse_at("program", &p.example) {
                    Ok(sum) => (sum.ok, sum.inner_rules),
                    Err(_) => (false, vec![]),
                }
            });
        }

        // Coverage per surface
        let mut coverage_reports: Vec<CoverageReport> = Vec::new();
        for surface_name in &self.config.coverage_surfaces {
            let surface: Box<dyn Surface> = match surface_name.as_str() {
                "paren" => Box::new(ParenSurface::default()),
                "bold" => Box::new(BoldSurface::default()),
                "backtick" => Box::new(BacktickSurface::default()),
                "fenced" => Box::new(FencedSurface::default()),
                other => {
                    eprintln!("[checker] unknown surface '{}', skipping", other);
                    continue;
                }
            };
            let report = run_coverage(&*surface, &corpus, &corpus_path.display().to_string(), &grammar)?;
            // Write coverage manifest
            let manifest_path = self.abs(&self.config.manifest_dir)
                .join(format!("{}_coverage_{}_audit.json", self.config.project_name, surface.name()));
            if let Some(parent) = manifest_path.parent() { fs::create_dir_all(parent)?; }
            fs::write(&manifest_path, serde_json::to_string_pretty(&report)? + "\n")?;
            coverage_reports.push(report);
        }

        // Build ledger row
        let pattern_pass = pattern_results.iter().filter(|(_, r)| matches!(r, PatternResult::Pass)).count();
        let pattern_fail = pattern_results.iter().filter(|(_, r)| r.is_regression()).count();
        let mut row = LedgerRow {
            tool: format!("DSL_ITERATION_TOOLKIT_V1 ({})", self.config.project_name),
            timestamp: Utc::now(),
            git_head: git_head(&self.config_dir),
            grammar_hash: grammar.hash(),
            slice_count: pattern_results.len(),
            slice_pass_count: pattern_pass,
            slice_fail_count: pattern_fail,
            audit_shadow_total: pattern_results.iter().filter(|(_, r)| matches!(r, PatternResult::Shadow(_))).count(),
            full_corpus_status: None,
            full_corpus_first_failing_line: None,
            paren_coverage_pct: None,
            bold_coverage_pct: None,
            backtick_coverage_pct: None,
            fenced_coverage_pct: None,
            regression_warnings: vec![],
            extra: Default::default(),
        };
        for report in &coverage_reports {
            match report.surface.as_str() {
                "paren" => row.paren_coverage_pct = Some(report.coverage_pct),
                "bold" => row.bold_coverage_pct = Some(report.coverage_pct),
                "backtick" => row.backtick_coverage_pct = Some(report.coverage_pct),
                "fenced" => row.fenced_coverage_pct = Some(report.coverage_pct),
                _ => {}
            }
        }

        // Compare to last ledger row
        let ledger_path = self.abs(&self.config.manifest_dir)
            .join(format!("{}_iteration_history.ndjson", self.config.project_name));
        let mut ledger = Ledger::load(&ledger_path)?;
        let regressions = ledger.detect_regressions(&row);
        row.regression_warnings = regressions.iter().map(|r| r.describe()).collect();

        // Append (de-dup on grammar_hash + results)
        let is_dup = match ledger.last() {
            Some(prev) => prev.grammar_hash == row.grammar_hash
                && prev.slice_pass_count == row.slice_pass_count
                && prev.audit_shadow_total == row.audit_shadow_total
                && prev.paren_coverage_pct == row.paren_coverage_pct,
            None => false,
        };
        if !is_dup {
            ledger.append(row.clone())?;
        }

        Ok(CheckReport {
            grammar_hash: grammar.hash(),
            pattern_results,
            coverage_reports,
            ledger_row: row,
            is_duplicate_of_last: is_dup,
            regressions,
            checkpoint_id: checkpoint_manifest.id,
        })
    }
}

fn git_head(dir: &std::path::Path) -> Option<String> {
    let out = std::process::Command::new("git")
        .args(["rev-parse", "HEAD"])
        .current_dir(dir)
        .output()
        .ok()?;
    if !out.status.success() { return None; }
    Some(String::from_utf8_lossy(&out.stdout).trim().chars().take(12).collect())
}

pub struct CheckReport {
    pub grammar_hash: String,
    pub pattern_results: Vec<(String, PatternResult)>,
    pub coverage_reports: Vec<CoverageReport>,
    pub ledger_row: LedgerRow,
    pub is_duplicate_of_last: bool,
    pub regressions: Vec<crate::ledger::Regression>,
    pub checkpoint_id: String,
}
