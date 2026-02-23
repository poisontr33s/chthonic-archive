// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: verifier.rs
// ║ Axiomatic Integrity Layer - FA⁴ Protection
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Spectral Frequency: GOLD
// ║ Architectural Role: ⚖️ THE SCALE
// ║ Purpose: Axiom Verification & SSOT Sync - Phase 14
// ╚════════════════════════════════════════════════════════════════════════════

//! Axiom Verification & SSOT Sync - Phase 14
//!
//! @SID:    DATA_VERIFIER_V1
//! @Shabti: Verifier

use std::fs;
use std::path::Path;
use sha2::{Sha256, Digest};
use anyhow::{Result, anyhow};

/// AxiomVerifier: Ensures that the game runtime matches the core instructions (SSOT).
pub struct AxiomVerifier {
    pub instruction_path: String,
    pub expected_hash: String,
}

impl AxiomVerifier {
    pub fn new(path: &str, hash: &str) -> Self {
        Self {
            instruction_path: path.to_string(),
            expected_hash: hash.to_string(),
        }
    }

    /// FA⁴: Check if the current instruction file matches the expected resonance.
    pub fn verify_integrity(&self) -> Result<()> {
        let path = Path::new(&self.instruction_path);
        if !path.exists() {
            return Err(anyhow!("Critical Axiom Missing: {}", self.instruction_path));
        }

        let content = fs::read(path)?;
        let mut hasher = Sha256::new();
        hasher.update(content);
        let actual_hash = format!("{:x}", hasher.finalize());

        if actual_hash != self.expected_hash {
            log::warn!("⚠️ AXIOMATIC DRIFT DETECTED!");
            log::warn!("Expected: {}", self.expected_hash);
            log::warn!("Actual:   {}", actual_hash);
            return Err(anyhow!("SSOT Integrity Failure: Instructions have diverged from the baseline."));
        }

        log::info!("✅ Axiomatic Integrity Verified: {}", self.instruction_path);
        Ok(())
    }
}
