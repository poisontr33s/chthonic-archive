// Grammar loading + runtime parsing via pest_vm (no compile-time pest_derive).
// This is what makes the toolkit generic across DSL projects — any .pest file
// can be loaded at runtime, no Rust recompile needed.

use anyhow::{anyhow, Context, Result};
use sha2::{Digest, Sha256};
use std::fs;
use std::path::Path;

/// A loaded grammar that can be queried for parsing.
pub struct Grammar {
    /// The original grammar source text (used for hashing).
    pub source: String,
    /// The pest_vm interpreter, ready to parse inputs.
    pub vm: pest_vm::Vm,
}

impl Grammar {
    /// Load a .pest grammar file and prepare it for runtime parsing.
    pub fn load(path: impl AsRef<Path>) -> Result<Self> {
        let path = path.as_ref();
        let source = fs::read_to_string(path)
            .with_context(|| format!("read grammar at {}", path.display()))?;
        Self::from_source(&source)
    }

    /// Build a Grammar from inline source.
    pub fn from_source(source: &str) -> Result<Self> {
        let pairs = pest_meta::parser::parse(pest_meta::parser::Rule::grammar_rules, source)
            .map_err(|e| anyhow!("pest_meta parse error: {}", e))?;
        let ast = pest_meta::parser::consume_rules(pairs)
            .map_err(|errs| anyhow!("pest_meta consume_rules errors: {:?}", errs))?;
        let optimized = pest_meta::optimizer::optimize(ast);
        let vm = pest_vm::Vm::new(optimized);
        Ok(Self { source: source.to_string(), vm })
    }

    /// SHA-256 hash of the grammar source — used as the iteration ledger key.
    pub fn hash(&self) -> String {
        let mut h = Sha256::new();
        h.update(self.source.as_bytes());
        format!("{:x}", h.finalize())
            .chars()
            .take(16)
            .collect()
    }

    /// Try to parse `input` against the named rule. Returns the top-level
    /// matched rule string (descending past trivial wrappers) and inner rule
    /// names collected from the parse tree, or an error.
    pub fn parse_at(&self, rule: &str, input: &str) -> Result<ParseSummary> {
        match self.vm.parse(rule, input) {
            Ok(pairs) => {
                let mut top_rule = None;
                let mut inner = Vec::new();
                for p in pairs {
                    if top_rule.is_none() {
                        top_rule = Some(p.as_rule().to_string());
                    }
                    collect_rules(&p, &mut inner);
                }
                Ok(ParseSummary { ok: true, top_rule, inner_rules: inner, error: None })
            }
            Err(e) => Ok(ParseSummary {
                ok: false,
                top_rule: None,
                inner_rules: vec![],
                error: Some(format!("{}", e)),
            }),
        }
    }
}

fn collect_rules<'i>(pair: &pest::iterators::Pair<'i, &str>, into: &mut Vec<String>) {
    into.push(pair.as_rule().to_string());
    for inner in pair.clone().into_inner() {
        collect_rules(&inner, into);
    }
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct ParseSummary {
    pub ok: bool,
    pub top_rule: Option<String>,
    pub inner_rules: Vec<String>,
    pub error: Option<String>,
}
