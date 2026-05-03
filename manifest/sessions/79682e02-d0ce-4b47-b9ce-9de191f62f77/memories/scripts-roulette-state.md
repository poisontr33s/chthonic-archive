# SCRIPTS_ROULETTE session state — 2026-04-21

## Completed
**T0 (9/9):** nightly-scheduled.ps1, api_pool.ps1, desktop-warmup.ps1, mcp-filesystem.ts, lib/poe_auth.py, lib/shared.py, lib/ssot-paths.ts, lib/ssot_paths.py, lib/ssot-paths.ps1

**T1 (10/12):** claudine.ps1, gemini-cli-wrapper.ps1, chthonic-xp.ps1 (bug: $Debug→$XPDebug + early-exit cache bypass), probe_toolchain_path.ps1, polyglot_env.ps1, fortify_terminal.ps1, pause_agents.ps1, api_pool_persist_user_env.ps1, api_key_gap_report.ps1, chthonic.ps1 (package.json version field added)

## Remaining T1
- claude_ide.ps1 (score 1.5)
- desktop-clone-state.ps1 (score 1.0)

## T2 Completed (10/~40)
- theme_contrast_audit.py (05ac3081)
- theme-sync.ps1 (7772a9c0)
- git_snapshot.py (1d9ab8f2)
- run_archaeology.ps1 (42f86a9f)
- run_overnight_daemon.ps1 (c7cb9602)
- mcp-asc-injector.ts (46a4ab63)
- local_refiner_v2.py + hf_refiner.py (1ef1f453)
- hf_auth_doctor.ps1 + hf_model_scout.py (75489cca)

## T2 Next Batch (score 2.0)
- hf_probe.py: wrap huggingface_hub import in try/except with install hint; use process env copy
- hf_discovery.py: auth check at startup with clear error if unauthenticated; write LATEST alias JSON alongside timestamped output
- hf-model-ranker.ts: use import.meta.dir-relative DB path; exponential backoff for HF 429; document Bun requirement in header

## T2 After That (score 2.0)
See roulette: Poe Lane, mistral.rs lane, VS Code lane, etc.
