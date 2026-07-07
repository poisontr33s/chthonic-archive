// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: verifier.rs
// ║ Axiomatic Integrity Layer - FA⁴ Protection
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Spectral Frequency: GOLD
// ║ Architectural Role: ⚖️ THE SCALE
// ║ Purpose: Lore-Canon Seal Verification - Phase 14
// ╚════════════════════════════════════════════════════════════════════════════

//! Lore-Canon Seal Verification - Phase 14
//!
//! Detects drift in a frozen lore-canon file (e.g. `.chthonic/SSOT.md`) against
//! its last-sealed hash. Does one thing: compare, warn on mismatch. It does not
//! govern Claude Code's operational instructions (that distinction lives in
//! this repo's `CLAUDE.md`) - `AxiomVerifier` only watches canon content drift
//! for `game/`'s consistency.
//!
//! The expected hash is NOT hardcoded in source. It lives in a sidecar seal
//! file (`<canon_path>.sha256`) next to the canon it watches, so resealing
//! after a legitimate edit is a data change, not a recompile.
//!
//! @SID:    DATA_VERIFIER_V1
//! @Shabti: Verifier

use std::fs;
use std::path::Path;
use sha2::{Sha256, Digest};
use anyhow::{Result, anyhow};

/// AxiomVerifier: watches one frozen lore-canon file for drift against its seal.
pub struct AxiomVerifier {
    pub canon_path: String,
    pub seal_path: String,
}

impl AxiomVerifier {
    /// `seal_path` defaults to `<canon_path>.sha256`.
    pub fn new(canon_path: &str) -> Self {
        Self {
            canon_path: canon_path.to_string(),
            seal_path: format!("{}.sha256", canon_path),
        }
    }

    fn hash_file(path: &Path) -> Result<String> {
        let content = fs::read(path)?;
        let mut hasher = Sha256::new();
        hasher.update(content);
        Ok(format!("{:x}", hasher.finalize()))
    }

    /// FA⁴: Check if the current canon file matches its sealed hash.
    pub fn verify_integrity(&self) -> Result<()> {
        let canon = Path::new(&self.canon_path);
        if !canon.exists() {
            return Err(anyhow!("Critical Axiom Missing: {}", self.canon_path));
        }
        let actual_hash = Self::hash_file(canon)?;

        let seal = Path::new(&self.seal_path);
        if !seal.exists() {
            log::warn!(
                "⚖️ No seal recorded for {} yet - baseline would be: {}",
                self.canon_path, actual_hash
            );
            return Ok(());
        }

        let expected_hash = fs::read_to_string(seal)?.trim().to_string();
        if actual_hash != expected_hash {
            log::warn!("⚠️ AXIOMATIC DRIFT DETECTED (canon has moved since last seal)");
            log::warn!("Sealed:  {}", expected_hash);
            log::warn!("Current: {}", actual_hash);
            return Err(anyhow!(
                "Canon Drift: {} has diverged from its last seal ({}).",
                self.canon_path, self.seal_path
            ));
        }

        log::info!("✅ Axiomatic Integrity Verified: {}", self.canon_path);
        Ok(())
    }
}
