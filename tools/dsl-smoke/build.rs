// build.rs — copy the canonical grammar from .chthonic/grammar/chthonic.peg
// into src/chthonic.pest at compile time, so pest_derive can find it via its
// macro-attribute path discipline (relative to src/).
//
// This way the canonical grammar in .chthonic/ stays the single source of truth.
// Editing the canonical grammar triggers a recompile via cargo:rerun-if-changed.

use std::fs;
use std::path::PathBuf;

fn main() {
    let manifest_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let repo_root = manifest_dir.ancestors().nth(2).expect("workspace root").to_path_buf();
    let canonical_grammar = repo_root.join(".chthonic").join("grammar").join("chthonic.peg");
    let dest = manifest_dir.join("src").join("chthonic.pest");

    if !canonical_grammar.exists() {
        panic!(
            "canonical grammar not found at {} (expected from workspace root .chthonic/grammar/)",
            canonical_grammar.display()
        );
    }

    let content = fs::read_to_string(&canonical_grammar)
        .unwrap_or_else(|e| panic!("read canonical grammar {}: {}", canonical_grammar.display(), e));
    fs::write(&dest, &content)
        .unwrap_or_else(|e| panic!("write {}: {}", dest.display(), e));

    println!("cargo:rerun-if-changed={}", canonical_grammar.display());
}
