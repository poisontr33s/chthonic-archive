# Deep Research Request: Solana Ecosystem for Chthonic Toolchain

**From:** Claude (chthonic meta-CLI)
**To:** Gemini 3 Pro (deep research)
**Date:** 2026-02-17
**Priority:** Medium — informational, no code changes pending

---

## Context

The chthonic meta-CLI (`scripts/chthonic.ps1` v3.2.0) manages a Rust-native polyglot toolchain:
- **rv** → Ruby, **uv** → Python, **goup** → Go, **rustup** → Rust, **bun** → JS/TS
- `chthonic doctor` checks versions against endoflife.date API
- `chthonic doctor --origins` shows install methodology per tool

We're considering adding Solana to the toolchain. Solana CLI is NOT currently installed.

## Research Questions

### 1. Solana CLI Install Vector
- What is the current recommended install method for Solana CLI tools on Windows?
- Is it `cargo install` based, or a standalone binary? (`solana-install`, `agave-install`?)
- Does it install to `~/.local/share/solana/` or `~/.cargo/bin/`?
- What's the version manager story? (solana-install update vs manual)

### 2. Agave vs Solana Labs Validator
- Agave (Anza) forked from Solana Labs — is Agave now the canonical client?
- What CLI tools come with Agave? (`solana`, `solana-keygen`, `solana-test-validator`?)
- Version numbering: is it still `solana 1.x` or has Agave diverged to `2.x`?

### 3. Firedancer & Frankendancer
- **Firedancer** (Jump Crypto) — written in C, is it production-ready?
- **Frankendancer** — hybrid Firedancer networking + Agave execution. Status?
- Are these relevant for a developer workstation, or only for validator operators?
- Any SDK/CLI tools that a Solana developer would need from the Firedancer ecosystem?

### 4. Solana SDK Language Story
- The core validator is Rust. What about the SDK?
- Is there a C/C++ SDK? (for Firedancer integration?)
- What do Solana program developers use? (Anchor framework, native Rust, Seahorse/Python?)
- Any recent language shifts worth knowing about?

### 5. endoflife.date API
- Does `https://endoflife.date/api/solana.json` exist? (probably not)
- If not, what's the best way to check latest Solana CLI version programmatically?

### 6. Dependencies
- Does Solana CLI need cmake/ninja? (we just installed those)
- Does it need the Vulkan SDK? (we have it at `C:\VulkanSDK\1.4.341.1`)
- Any other system deps for Windows?

## Expected Output

A structured summary answering these questions, with:
- Recommended install command for chthonic DoctorFixMap
- Whether to add Solana to `chthonic doctor` checks
- Whether Firedancer/Frankendancer matter for dev workstations
- Any cmake/Vulkan/SDK dependencies to wire up

---

*This handoff is informational. No code changes should be made until research is reviewed.*
