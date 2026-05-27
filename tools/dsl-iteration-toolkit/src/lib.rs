// dsl-iteration-toolkit — generalized methodology layer for PEG-based DSL development.
//
// Provides:
//   - Catalog: typed pattern catalog with JSON Schema validation (patterns.json)
//   - Ledger: time-series iteration history with regression detection (NDJSON)
//   - Coverage: exhaustive per-occurrence grammar match logging across a corpus
//   - Checker: orchestrator that runs all of the above and persists state
//   - Config: dsl-iter.toml schema for per-project configuration
//
// First reference instance: chthonic-archive (.chthonic/dsl-iter.toml).
//
// Design principle (user-named 2026-05-27): the tool ENCODES the project's
// accumulated decisions so the methodology is portable across DSL projects.
// Tools serve methodology; methodology compounds across iterations.

pub mod catalog;
pub mod ledger;
pub mod coverage;
pub mod checker;
pub mod config;
pub mod grammar;

pub use catalog::{Catalog, Pattern, PatternResult};
pub use ledger::{Ledger, LedgerRow, Regression};
pub use coverage::{CoverageReport, Occurrence, OccurrenceClassification};
pub use checker::IterationChecker;
pub use config::Config;
pub use grammar::Grammar;
