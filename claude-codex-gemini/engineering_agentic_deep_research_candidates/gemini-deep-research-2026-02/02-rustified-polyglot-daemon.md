---
type: deep-research-output
source: claude-codex-gemini/sessionANDresearch.md (lines 875-1084)
researcher: gemini-pro-3
created: 2026-02-11
topic: rustified-polyglot-daemon-architecture
---

# Research 2: Rustified Polyglot Daemon Architecture

## Executive Summary

Gemini independently designed a comprehensive daemon architecture that validates and extends our existing overnight tooling. Key additions: Elixir/BEAM for fault-tolerant orchestration, mistral.rs for pure-Rust inference, Qdrant for vector baselines, and MCP Bundle packaging for secure agent exposure.

## Architecture Layers

| Layer | Technology | Role |
|-------|-----------|------|
| Orchestration | Elixir/BEAM | Fault-tolerant file crawling, concurrent subprocess management |
| Inference | mistral.rs (Rust) | Local LLM serving, GPT-OSS 20B with MXFP4 |
| Vector Storage | Qdrant (Rust) | Historical baselines, sub-ms retrieval |
| Agent Bridge | Mailbox Pattern (files) | Air-gapped daemon↔agent communication |
| Security | Windows ODR + MCP Bundles | Proxy-mediated auth, capability gating |

## Mailbox Pattern (Validated)

Gemini independently validated our exact mailbox architecture:
- Local daemon writes structured Markdown digests
- Digests deposited in isolated mailbox directory (`claude/mailbox/`)
- External agents read/write ONLY to mailbox, never to source
- Pre-computed context: daemon does heavy lifting at zero cost, agents do reasoning
- **This is exactly what we already built.** ✅

## MCP Integration on Windows 11

### On-Device Agent Registry (odr.exe)
- Central registry for MCP server discovery and management
- Proxy-mediated communication blocks unauthorized tool execution
- Prevents token passthrough (least privilege)

### MCP Bundles (.mcpb)
- Standardized ZIP with `manifest.json` (v0.3 spec)
- `server.type: "uv"` for Python servers (uses pyproject.toml)
- No hardcoded credentials — auth prompted during install
- Register: `odr mcp add <path-to-manifest>`

### Future: Package Our Daemon as .mcpb
- Expose Qdrant queries, formatting tools, analysis triggers
- Any MCP client (Claude Desktop, Copilot CLI) can discover it
- Strict capability boundaries — no shell access leakage

## Dola.ai Alternative: Local Voice Assistant

Full pipeline for voice-controlled daemon interaction:

| Stage | Tool | Resource |
|-------|------|----------|
| STT | Parakeet V3 / Whisper | GPU (shared) |
| Intent Processing | Qwen3 Omni / Llama 3 | GPU via mistral.rs |
| TTS | Pocket-TTS / Kokoro | CPU (minimal) |
| Transport | LiveKit / Pipecat | WebRTC, VAD, barge-in |

**Status:** Aspirational. Not immediate priority, but architecturally sound.

## Claude Opus 4.6 Integration Notes

- **Adaptive Thinking:** `thinking: {type: "adaptive"}` replaces legacy `budget_tokens`
- **Effort levels:** Low → Max, adjustable per digest severity
- **1M token context (beta)** + Context Compaction API for infinite sessions
- **128K output limit** — can rewrite massive files in single pass

## Rustified Formatting Tools

| Tool | Target | Replaces | Speed |
|------|--------|----------|-------|
| ruff | Python | flake8/black | 10-100x faster |
| rumdl | Markdown | markdownlint | 5x faster, 57 rules |
| rfmt | Ruby | RuboCop | 100ms constant, 1500 files/sec |
| rustfmt | Rust | — | Native toolchain |

## What We Already Have vs What's New

| Capability | We Have | Gemini Proposes | Gap |
|-----------|---------|----------------|-----|
| File archaeology | overnight-archaeology.ts | Elixir crawler | Ours works, Elixir is aspirational |
| Debt scoring | overnight_daemon.ts | Same concept | ✅ Validated |
| LLM refinement | hf_refiner.py (HF API) | mistral.rs local | Replace HF with local |
| Mailbox pattern | claude/mailbox/ | Same | ✅ Identical |
| Vector baselines | Not yet | Qdrant | New capability |
| MCP packaging | Not yet | .mcpb bundles | Future |
| Voice assistant | Not yet | Full STT→LLM→TTS | Aspirational |
