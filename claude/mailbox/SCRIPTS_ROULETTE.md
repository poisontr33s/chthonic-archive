# Scripts Assessment — TODO Roulette

> **Source:** Explore agent full scan of `scripts/` (recursive, all filetypes)
> **Method:** L/E × H/V scoring (1=low, 3=high). SCORE = VALUE / EFFORT.
> **Hierarchy:** T0 (auth/infra gates) → T1 (core CLI) → T2 (companion tools) → T3 (coherence/batch) → T4 (tests/docs) → T5 (noise/tombstone)
> **Sort:** Within each tier, SCORE descending. Highest-impact, lowest-effort items first.
> **Autonomous dispatch:** → [`ROULETTE_STEWARD.md`](ROULETTE_STEWARD.md) — cold-start protocol, execution loop, commit contract, session-end handoff. Load this before executing any ⬜ item.

---

## Progress Trail — 2026-04-22

| Tier | Done | Remaining | Notes |
|------|------|-----------|-------|
| T0 | 9/9 ✅ | — | All auth/infra gates complete |
| T1 | 12/12 ✅ | — | `desktop-clone-state.ps1` 336f26d1: pre-export size estimate; disk space guard (10% headroom); `[switch]$ExcludeGit` (robocopy `/XD .git` + `git bundle create`) |
| T2 | ~68/~68 ✅ | — | **Complete** — e9a9fc93 skill_index+skill_health+skill_audit trio |
| T3 | 16 ✅ | — | **Complete** |
| T4 | 2/2 ✅ | — | **Complete** — `88a675b4` sfs_slabstone_baseline (CRLF→LF hash, --emit-json, task exit codes); `8b40191c` gemini-model-router.test (fixture file, bun test script, passthrough-no-fallback edge case) |
| T5 | ✅ complete | — | thin-shims `798150e1`; assess-before-act `a01857f0`; prototypes+WIP `d8912727` |

---

## T0 — Infrastructure & Auth Gates (blocks other work)

| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/nightly-scheduled.ps1` | **3.0** | 1 | ✅ `erdno`→`eldno` fixed; failure sentinel on daemon crash added |
| `scripts/api_pool.ps1` | **3.0** | 1 | ✅ JSON schema validation added; `-Verify` switch confirms keys non-empty |
| `scripts/desktop-warmup.ps1` | **3.0** | 1 | ✅ try/catch per step; `$failures` summary at end |
| `scripts/mcp-filesystem.ts` | **3.0** | 1 | ✅ `// chthonic-patch` idempotency guard; package.json version assertion |
| `scripts/lib/poe_auth.py` | **3.0** | 1 | ✅ `valid: bool` on resolution; `ValueError` in `strict=True`; `validate_poe_token()` — `GET /models` live call; `PoeTokenValidation` dataclass (ok/status_code/model_count/error) — `0cbbaab8` |
| `scripts/lib/shared.py` | **3.0** | 1 | ✅ Type annotations + `__all__`; `find_repo_root` capped at 10 levels |
| `scripts/lib/ssot-paths.ts` | **3.0** | 1 | ✅ `as const` assertions; `assertSsotExists(root)` exported |
| `scripts/lib/ssot_paths.py` | **3.0** | 1 | ✅ `sys.path.insert` existence guard; `except ImportError` + `DeprecationWarning` |
| `scripts/lib/ssot-paths.ps1` | **3.0** | 1 | ✅ Line-count comment removed; `[switch]$AssertExists` added to `Resolve-SsotPath` |

---

## T1 — Core CLI Surface

| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/claudine.ps1` | **2.0** | 1 | ✅ `$Args`→`$ChthonicArgs`; `-NoProfile` added to all 8 inner chthonic.ps1 invocations |
| `scripts/gemini-cli-wrapper.ps1` | **2.0** | 1 | ✅ Pre-flight `Get-GeminiEntrypoint` check; `bun add` hint on miss; `-Version` already wired |
| `scripts/chthonic-xp.ps1` | **2.0** | 1 | ✅ Global EAP removed; `$TrailDir` PSScriptRoot-relative; `[switch]$XPDebug` (renamed from `$Debug` — PS common-param collision); early-exit cache bypassed on `-XPDebug` |
| `scripts/probe_toolchain_path.ps1` | **2.0** | 1 | ✅ `Get-Command rv/rvw` as primary; cargo bin fallback; probe-miss `Log()` entry on rv absent |
| `scripts/polyglot_env.ps1` | **2.0** | 1 | ✅ Staleness check (<24h skips re-run, uses cached path file); Apply confirmation; `[switch]$Verify` runs `sfs.ps1 --verify` |
| `scripts/fortify_terminal.ps1` | **2.0** | 1 | ✅ Reflection QuickEdit hack → `[System.Console]::TreatControlCAsInput = $false`; `[Console]::InputEncoding = UTF8` added |
| `scripts/pause_agents.ps1` | **2.0** | 1 | ✅ Backup path printed; `[switch]$Restore` restores most-recent backup; `operationalMode` key-absence warning before regex replace |
| `scripts/api_pool_persist_user_env.ps1` | **2.0** | 1 | ✅ `-Status` shows `MISSING (need -Apply)` / `DRIFT (pool != user)` per key |
| `scripts/api_key_gap_report.ps1` | **2.0** | 1 | ✅ `Get-RepoRoot` PSScriptRoot-relative; `[switch]$Json` emits report to stdout |
| `scripts/claude_ide.ps1` | **1.5** | 2 | ✅ `.mcp.json` backed up to `.mcp.json.bak` before write; `ConvertFrom-Json` try/catch validation after write; `verify-mcp` subcommand (reports server count, exit 1 on invalid JSON) |
| `scripts/chthonic.ps1` | **1.5** | 2 | ✅ `$ErrorActionPreference = 'Stop'` after param block; `$VERSION` derived from `package.json` (null-guarded; `"version": "3.3.0"` field added to package.json) |
| `scripts/desktop-clone-state.ps1` | **1.0** | 2 | ✅ Pre-export size estimate per-component + total; disk space guard (1.1× headroom); `[switch]$ExcludeGit` — robocopy `/XD .git` + `git bundle create <leaf>.bundle` |

---

## T2 — Companion CLIs & Python Tooling

### Archaeology / Nightly Pipeline
| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/git_snapshot.py` | **3.0** | 1 | ✅ `sys.path.insert(0, parent.parent)` guard; `--since <ISO>` commit filter |
| `scripts/run_archaeology.ps1` | **3.0** | 1 | ✅ Print `$runFailures` in background mode; remove dead `-LocalV2` param; add `-What` plan-preview switch |
| `scripts/run_overnight_daemon.ps1` | **2.0** | 1 | ✅ `Get-Command bun` first, fall back to hardcoded path; `-Timeout N` with process kill; `exit $LASTEXITCODE` propagation |
| `scripts/overnight_daemon.ts` | **1.5** | 2 | ✅ Uncomment+activate `initSentry` import; call `initSentry({ dsn: process.env.SENTRY_DSN })` at start of `main()`; add `--emit-digest` flag writing `DAEMON_DIGEST_<date>.md` to `claude/mailbox/` |
| `scripts/local_refiner_v2.py` | **2.0** | 1 | ✅ Output schema normalized; `--validate` schema gate; `--model-list` GGUF inventory |
| `scripts/hf_refiner.py` | **2.0** | 1 | ✅ Exponential backoff 429/503 (`RETRY_DELAY*(2**attempt)`); `--ore-dir` configurable; `find_latest_ore(ore_base)` param |

### HuggingFace Lane
| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/hf_auth_doctor.ps1` | **2.0** | 1 | ✅ `-Verify` calls `api/whoami`, prints username; user-scope vs process-scope annotation |
| `scripts/hf_model_scout.py` | **2.0** | 1 | ✅ Exponential backoff retry 429 (`sleep(2**attempt)`); `--verify-timeout N`; `verify_config(timeout)` param |
| `scripts/hf_probe.py` | **2.0** | 1 | ✅ Guarded `huggingface_hub` import with install hint; env copy (`dict(os.environ)`), no `os.environ` mutation |
| `scripts/hf_discovery.py` | **2.0** | 1 | ✅ Auth check via `api.whoami()` + stderr hint on fail; LATEST alias JSON+MD written alongside timestamped output |
| `scripts/hf-model-ranker.ts` | **2.0** | 1 | ✅ Bun requirement in header; `import.meta.dir`-relative `repoRoot`; 429 backoff (`Bun.sleep(2^n*1s)`, 3 retries) |

### Poe Lane
| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/poe_lane.py` | **2.0** | 1 | ✅ `--timeout N` (default 60) threaded through `http_json`/`run_models`/`run_chat`; `--stream` flag with `run_chat_stream()` SSE parser (live stdout) |
| `scripts/poe_sdk_lane.py` | **2.0** | 1 | ✅ `except ImportError` narrowed; install hint updated: `uv run --with fastapi-poe ...`; `poe-sdk` extra in `pyproject.toml` |
| `scripts/poe_transport_audit.py` | **2.0** | 1 | ✅ Module imports (`_poe_lane`/`_poe_sdk_lane`); `probe_openai`/`probe_sdk`/`list_openai_models` use direct calls; `--cache` saves/loads `codex/mailbox/cache/poe_transport_cache.json` |
| `scripts/poe_account.ps1` | **2.0** | 1 | ✅ `-List` flag enumerates `POE_API_KEY_N` slots with masked key display; `$keyAfter` guard: throws if `POE_API_KEY` empty post-assignment |

### Mistral.rs Lane
| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/mistralrs_model_manager.py` | **2.0** | 1 | ✅ `MISTRALRS_PID = ~/.chthonic/mistralrs.pid`; PID guard before start (live=abort, stale=clean+proceed); write PID after `Popen`; `cmd_stop` unlinks PID on confirmed stop |

### MCP Servers
| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/mcp-chthonic-server.ts` | **1.5** | 2 | ✅ `SENTRY_DSN` presence check (WARN to stderr if absent); `data.context` field on all catch handlers (`{tool,args}` in tools/call, `"parse"` in parse error); `tools/describe` MCP method (by name or all) |
| `scripts/gemini-model-router.ts` | **1.5** | 2 | ✅ `copyFileSync` backup to `.bak` before write; `EXPECTED_REGISTRY_VERSION` + `validateRegistryVersion()` warns to stderr with migration hint on version mismatch; `--dry-run` flag: skips write; `SyncResult.dryRun` + `.backedUp` fields |
| `scripts/mcp-asc-injector.ts` | **2.0** | 1 | ✅ SSOT existence check at startup with actionable error; `ping` tool returning server version + SSOT file size |

### VS Code Tooling
| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/theme_contrast_audit.py` | **3.0** | 1 | ✅ `sys.path.insert(0, parent.parent)` guard; exit code docstring (0=OK, 1=failures+strict/missing/write-err); `--emit-junit FILE` JUnit XML |
| `scripts/theme-sync.ps1` | **3.0** | 1 | ✅ Glob-primary dst discovery (version-independent); `[switch]$VerifyOnly` (hash check only, no write); `exit 1` on any hash mismatch; src-missing skip guard |
| `scripts/vscode_terminal_crash_doctor.ps1` | **2.0** | 1 | ✅ `Get-RepoRoot` starts from `$PSScriptRoot` (not `Get-Location`); scoring formula comment above `Classify-ProbeFindings` (PROFILE_REPO_PATH / PROFILE_STARTUP / BINARY_LEVEL / EXTERNAL); `-ScoreOnly` switch emits JSON `{score, probes}` to stdout |
| `scripts/vscode_insiders_matrix.ps1` | **2.0** | 1 | ✅ `Get-RepoRoot` starts from `$PSScriptRoot`; `-Skip @(...)` string-array to omit named cases; `-Json` switch emits JSON to stdout |
| `scripts/vscode_settings_live_audit.py` | **2.0** | 1 | ✅ `_find_insiders_root_from_registry()` (HKCU Uninstall/winreg, win32 only); `find_insiders_install_root()` uses registry fallback; `run_command(timeout=)`; `get_insiders_version(timeout=)`; `--timeout SECONDS` argparse flag |
| `scripts/vscode_electron_hardener.py` | **2.0** | 1 | ✅ `argv.json.bak` backup before write (already in `patch_argv()`); `discover_user_data_dir()`: runs `code-insiders --status`, parses `User Data:` line; `main()` uses discovered path with env-based fallback |
| `scripts/vscode_error_autopsy.py` | **2.0** | 1 | ✅ `--log-dir PATH` override flag (bypasses all default discovery, scans only specified dir); `--severity-min LEVEL` alias for `--severity` (both use `dest='severity'`) |
| `scripts/insiders-sync.ps1` | **2.0** | 1 | ✅ `[switch]$DryRun` param; `Invoke-Step` prints `[dry-run] Would run: <Label>` without executing; `$RepoRoot = Split-Path -Parent $PSScriptRoot` variable; post-package vsix validation (0 files → throw; 0-byte file → throw) |
| `scripts/update-claude-code.ps1` | **2.0** | 1 | ✅ removed `patch-claude-insiders.ps1` call; `$verBefore` = `claude --version` before bun add; `$verAfter` after; prints color diff Before/After |

### Project Scaffolding / Workflow
| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/chthonic_new.py` | **2.0** | 1 | ✅ `execute_profile()` adds `errors` field (failed steps with command/exit_code/stderr); `VERIFY_CHECKS` + `verify_scaffold()`: checks expected files per profile; `--verify` argparse flag; `chthonic.ps1` new help updated to mention `--verify` (subcommand already existed) |
| `scripts/chthonic_workflow.py` | **2.0** | 1 | ✅ `--list` flag (profile `nargs='?'`; prints sorted names, exits 0); `--dry-run`: `run_step(dry_run=True)` returns `exit_code=0`, `stdout=[dry-run] would run: ...`; `chthonic.ps1` workflow help updated; subcommand already existed |
| `scripts/apply_canonize_uv.sh` | **2.0** | 1 | ✅ pre-flight `git remote get-url origin` check (exits 1 if absent); `--dry-run` flag (skips checkout/uv run/commit/push, prints previews); explicit `if ! eval CMD` exit-code checks in loop |
| `scripts/siphon_to_dumpster_dive.ps1` | **2.0** | 1 | ✅ `$scriptSelfRel = GetRelativePath($repoRoot, $PSCommandPath)` filter from `$selected`; writes `siphon-manifest.json` to `$destBase` (DestRoot base dir) with run_at/stamp/dest/file_count/files |

### Zombie Pipeline
| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/zombie_consumer.py` | **2.0** | 1 | ✅ `_load_st_model()`: catch `ImportError` separately; print install prompt to stderr (`uv sync --extra embeddings` + `uv pip install sentence-transformers`); `pyproject.toml` analysis group: add `scikit-learn>=1.8.0,<2` |
| `scripts/zombie_forge_bridge.py` | **2.0** | 1 | ✅ `ensure_forge_dirs()` auto-creates stage dirs; `_write_batch_receipt()` writes batch-level receipt JSON after route/retro-collapse; `undo` subcommand with `--dry-run`/`--json` |

---

## T3 — Surface Coherence & Batch Fixes

### Batch: 9× skill_tensor probe import fix (high-value, ~5 min total)
All 9 files share the same broken import (`from skill_tensor_common import ...` → `from scripts.skill_tensor_common import ...`):

| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/skill_tensor_roulette.py` | **2.0** | 1 | ✅ `sys.path.insert(0, str(Path(__file__).resolve().parent))` before `from skill_tensor_common import` |
| `scripts/skill_tensor_execute.py` | **2.0** | 1 | ✅ Same batch fix |
| `scripts/skill_tensor_feedback.py` | **2.0** | 1 | ✅ Same batch fix |
| `scripts/skill_tensor_inventory.py` | **2.0** | 1 | ✅ Same batch fix |
| `scripts/skill_tensor_ledger.py` | **2.0** | 1 | ✅ Same batch fix |
| `scripts/skill_tensor_plan.py` | **2.0** | 1 | ✅ Same batch fix |
| `scripts/skill_tensor_pool.py` | **2.0** | 1 | ✅ Same batch fix |
| `scripts/skill_tensor_render_spec.py` | **2.0** | 1 | ✅ Same batch fix |
| `scripts/skill_tensor_weights.py` | **2.0** | 1 | ✅ Same batch fix |
| `scripts/skill_tensor_cycle.py` | **2.0** | 1 | ✅ Replace inline `find_repo_root` with `from lib.shared import find_repo_root`; added `--stages`, `--resume` to cycle subparser |
| `scripts/skill_tensor_common.py` | **2.0** | 1 | ✅ `load_latest()` raises `FileNotFoundError` with hint; accepts optional `path` arg; `--latest-path` in `__main__` |

### Consolidation / Deduplication
| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/sfs.ps1` | **3.0** | 1 | ✅ Thin shim delegating to `shell_capabilities.ps1`; body replaced with `& "$PSScriptRoot/shell_capabilities.ps1"` |

### Path Fix Hotspot (hardcoded `erdno` bug)
| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/setup-gemini-claude.ts` | **2.0** | 1 | ✅ `erdno`→`eldno`; use `import.meta.dir`-relative `CHTHONIC_ROOT` default |
| `scripts/validate-triad-links.ps1` | **1.0** | 1 | ✅ `erdno`→`eldno`; `$RepoRoot` default now `PSScriptRoot`-relative |
| `scripts/build_epistemograph.py` | **1.0** | 1 | ✅ `erdno`→`eldno` in docstring; v1 deprecation warning + `--no-deprecation-warning` flag — `66cf0b59` |

### Lint / Validation Infrastructure
| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/shebang-guard.ts` | **2.0** | 1 | ✅ Extended to .py (shebang line 1 + encoding line 2) and .sh (displaced shebang); SCAN_EXTENSIONS set; typed violation.issue field |
| `scripts/validate_script_headers.py` | **2.0** | 1 | ✅ _validate_ts() for .ts files; .ts scan in _scan_scripts(); --fix appends missing @SID/@Shabti/@Purpose per type |
| `scripts/install-hooks.ps1` | **2.0** | 1 | ✅ -Force/-DryRun params; report existing hooks pre-write; inline post-merge hook (bun install --frozen-lockfile on lockfile change) |
| `scripts/bun-practices-audit.ts` | **2.0** | 1 | ✅ loadSkipDirs() reads .bun-practices.json then bunfig.toml [bun-practices]; --fix: replaces npx→bunx, npm run→bun run in package.json scripts |
| `scripts/bun_compliance_audit.py` | **2.0** | 1 | ✅ --except PATTERN (repeatable); fnmatch whitelist in should_skip_path; except_globs in BunComplianceScanner.__init__ |
| `scripts/ankhrc_validator.py` | **2.0** | 1 | ✅ find_repo_root() from lib/shared; tomllib fallback emits WARNING to stderr; --fix: creates missing paths (mkdir/touch) |

### Mailbox / Handoff Pipeline
| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/handoff_loop.py` | **2.0** | 1 | ✅ `--stale-hours` arg; `compute_obligations(stale_hours=)` param; `ROUTE_RECEIPT_<ts>.json` emitted to `codex/mailbox/` on route |
| `scripts/mailbox_handoff.ps1` | **2.0** | 1 | ✅ `$repoRoot` PSScriptRoot-relative; `Validate-HandoffSchema` checks frontmatter + keys + sections; validation gate on SendAll loop + single-source route |
| `scripts/mailbox_scribe.py` | **2.0** | 1 | ✅ `find_repo_root()` for `REPO_ROOT` + `POLICY_PATH`; `POLICY_DEFAULTS`; `UserWarning` with default documentation when policy absent |
| `scripts/mailbox_polisher.py` | **2.0** | 1 | ✅ Externalize patterns to `.meta/mailbox-polisher-patterns.json`; `--dry-run` prints table of files-to-archive + target path |
| `scripts/mailbox_compactor.py` | **2.0** | 1 | ✅ Uses `find_repo_root()`; `--since <ISO>` incremental compaction; `--max-files N` |

### SSOT Tools
| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/ssot_hash.py` | **2.0** | 1 | ✅ `SSOT_HOLDER` from `scripts.lib.ssot_paths`; `--compare <hash_or_file>`; `--write` to `.chthonic/ssot.sha256` |
| `scripts/ssot_structural_extractor.py` | **2.0** | 1 | ✅ `--output` flag; `--quiet`/`--progress`; `--verify-only` (hash comparison, no re-parse) |
| `scripts/ankh_theme_reference.py` | **2.0** | 1 | ✅ Uses `SSOT_ARCHIVE_STRUCTURAL_INDEX.json`; SSOT hash check to invalidate cached output |

### Theme Pipeline
| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/theme_parity.py` | **2.0** | 1 | ✅ `MASTER_NAME` fixed to decorator theme; `--master` flag; per-theme missing key count |
| `scripts/theme_promote_master.py` | **2.0** | 1 | ✅ `.bak` before modification; `--dry-run`; `--distance-metric` flag |
| `scripts/theme_color_diversity.py` | **2.0** | 1 | ✅ Backup before modification; `--variants N`; `--report-only` |
| `scripts/theme_token_coverage.py` | **2.0** | 1 | ✅ `--theme` flag; `--update-universe`; coverage % output |
| `scripts/theme_sfs_transmute.py` | **2.0** | 1 | ✅ Absolute path via `parents[1]`; `_CHANGESET_HASH` idempotency; `--verify` |
| `scripts/theme_artcop.py` | **2.0** | 1 | ✅ Relationship with `vscode-art-cop.ts` documented; `--compare` for before/after |
| `scripts/milf_scanner.py` | **2.0** | 1 | ✅ `--dump-json` emits full registry; sanity check for 14 required palette role keys |

### Icon / Font Pipeline
| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/generate-product-icon-font.mjs` | **2.0** | 1 | ✅ `#!/usr/bin/env bun` shebang; `@SID` comment block; pre-flight SVG path validation |

### Skill Tooling
| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/build_skill_index.py` | **2.0** | 1 | ✅ Fix Purpose string in header; add `--output` defaulting to `codex/mailbox/SKILL_INDEX_LATEST.json`; add `--diff` |
| `scripts/skill_health.py` | **2.0** | 1 | ✅ Externalize rubric to `.meta/skill-health-rubric.json`; add `--since <ISO>`; add `--emit-badge` |
| `scripts/skill_audit.py` | **2.0** | 1 | ✅ Validate `--root` exists; read `CLAUDE_TOOLS` from config not hardcoded set; align output format with `skill_health.py` |

### Audit / Scan Tooling
| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/scm_triage.py` | **2.0** | 1 | ✅ sys.path guard; --apply writes gitignore entries; --preview-gitignore |
| `scripts/link_audit.py` | **2.0** | 1 | ✅ .bak before in-place fix; --no-backup flag; git calls wrapped in try/except |
| `scripts/icon_scaffold_contract_audit.py` | **2.0** | 1 | ✅ explicit mkdir with feedback; --diff vs previous audit JSON |
| `scripts/extension_universe_scanner.py` | **2.0** | 1 | ✅ no circular import verified; --diff; --output flag |
| `scripts/rootdir_health_audit.py` | **2.0** | 1 | ✅ find_repo_root() + absolute output path; --severity-min; --json |
| `scripts/health_report.py` | **2.0** | 1 | ✅ tool list verified; --tools sub-reports; schema version in JSON |
| `scripts/map_codebase.py` | **2.0** | 1 | ✅ still invoked; --output added; added to chthonic.py dispatch table |
| `scripts/compact_md.py` | **2.0** | 1 | ✅ --backup flag verified; registered in chthonic.ps1 command surface |
| `scripts/upcycle_audit.py` | **1.0** | 1 | ✅ --dir recursive scan; thresholds externalized; JSON output for zombie pipeline |

### Cross-Agent Integration
| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/cross-critique.ts` | **2.0** | 1 | ✅ ANTHROPIC_API_KEY validated; --cache-dir round-1 reuse; --merge-only <f1> <f2> |
| `scripts/run_mcp_validation.ts` | **2.0** | 1 | ✅ SIGINT handler kills server; --json output; --check <tool_name> |
| `scripts/milfographic-calculator.ts` | **2.0** | 1 | ✅ loadEntities() SSOT index loader; --compare <entity1> <entity2>; --export-index |

### Observability
| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/sentry_init.ts` | **2.0** | 1 | ✅ console.warn when SENTRY_DSN absent; SENTRY_ENABLED=false escape hatch |
| `scripts/mcp-browser.ts` | **2.0** | 1 | ✅ `import.meta.dir` confirmed (no `__dirname`); `TODO(upstream)` comment formatted to spec |
| `scripts/mcp-sentry-proxy.ts` | **1.0** | 1 | ✅ runtime guard replaces SSOT_PATH non-null assertion; process.exit(1) |

### Misc Surface
| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/embed_ore.py` | **1.0** | 1 | ✅ hash-keyed .embedding_cache.json; --recompute flag; lazy-import preserved |
| `scripts/chthonic.py` | **1.0** | 1 | ✅ runpy dispatch (no subprocess); --list-commands; map-codebase entry |

---

## T4 — Tests & Documentation Validation

| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/sfs_slabstone_baseline.py` | **2.0** | 1 | ✅ CRLF→LF normalization in `short_hash()`; `--emit-json FILE` flag added; VS Code task `detail` documents exit codes 0/1 |
| `scripts/gemini-model-router.test.ts` | **2.0** | 1 | ✅ Registry extracted to `scripts/__fixtures__/gemini-model-router-registry.ts`; `"test": "bun test scripts/gemini-model-router.test.ts"` in `package.json`; `passthrough-no-fallback` edge-case test added (5/5 pass) |

---

## T5 — Noise & Tombstone Queue

### Thin-shim conversions (retired scripts → delegates)
| Script | Action |
|--------|--------|
| `scripts/patch-claude-insiders.ps1` | ✅ Moved to `scripts/.deprecated/`; CLAUDE.md updated — `c9832116` |
| `scripts/claude_healthcheck.ps1` | ✅ Thin shim → `& "$PSScriptRoot/claude_ide.ps1" health @args`; original → `.deprecated/` — `798150e1` |
| `scripts/claude_insiders_selfheal.ps1` | ✅ Thin shim → `& "$PSScriptRoot/claude_ide.ps1" heal @args`; original → `.deprecated/` — `798150e1` |
| `scripts/mcp_write_local.ps1` | ✅ Thin shim → `& "$PSScriptRoot/claude_ide.ps1" write-mcp @args`; original → `.deprecated/` — `798150e1` |
| `scripts/validate-triad-links.ps1` | ✅ Thin-wrap → `uv run link_audit.py scan`; original → `.deprecated/` (typo already fixed T3) — `798150e1` |

### Assess-before-act (read, then decide)
| Script | Status | Action |
|--------|--------|--------|
| `scripts/hf_gemma_probe.py` | ✅ Tombstoned → `.deprecated/` (one-off Gemma probe) — `a01857f0` |
| `scripts/hf_prep.py` | ✅ Keep active — distinct HF env-readiness checker; no change needed |
| `scripts/mistralrs_client.py` | ✅ Promoted → `scripts/lib/mistralrs_client.py` (already LIB_ SID) — `a01857f0` |
| `scripts/local_refiner.py` | ✅ Tombstoned → `.deprecated/local_refiner.py`; `run_archaeology.ps1` calls v2 — `a01857f0` |
| `scripts/vector_db.py` | ✅ Keep active — part of overnight archaeology pipeline; no change needed |
| `scripts/setup_db.py` | ✅ Tombstoned → `.deprecated/` (hardcoded erdno path, superseded by build_epistemograph inline schema init) — `a01857f0` |
| `scripts/mandala_topology.py` | ✅ Keep active — topology report from graph JSON; no change needed |
| `scripts/unified_topology.py` | ✅ Keep active — cross-lane dependency graph generator; no change needed |
| `scripts/extract_session_value.py` | ✅ Tombstoned → `.deprecated/` (superseded by dumpster-upcycler skill) — `a01857f0` |
| `scripts/chthonic.sh` | ✅ Keep active — bash router for Unix platforms (companion to chthonic.py); no change needed |
| `scripts/build_epistemograph_v1.1.py` | ✅ Renamed → `build_epistemograph.py`; v1.0 → `.deprecated/`; `--schema-path` added; `erdno→eldno` fixed — `a01857f0` |

### Prototypes (integrate or tombstone)
| Script | Action |
|--------|---------|
| ✅ `scripts/ide-polling-prototype.ts` | Tombstoned → `scripts/.deprecated/ide-polling-prototype.ts` (`798150e1`) |
| ✅ `scripts/claude-chthonic-bridge.ts` | Tombstoned → `scripts/.deprecated/claude-chthonic-bridge.ts` (`798150e1`) |
| ✅ `scripts/background_services.py` | Graceful shutdown via `asyncio.Event()` + SIGINT handler + PID file (`d8912727`) |
| ✅ `scripts/autonomous_coordinator.py` | `pleasure_protocol` lazy import confirmed; `--dry-run` flag added; metabolize documented (`d8912727`) |
| ✅ `scripts/novia_cadaveris_embalmer.ps1` | All 4 `Set-Content` calls guarded with `if (-not $DryRun)`; dry-run prints what would be written (`d8912727`) |

### Partial / WIP (not worth active maintenance)
| Script | Action |
|--------|---------|
| ✅ `scripts/vscode-art-cop.ts` | LLM endpoint health check before submission; non-JSON response guard (`d8912727`) |

---

## Quick-Win Cluster Summary

> **Status: COMPLETE — 2026-04-22.** All T0→T5 items executed, T-Entity prep appended. No ⬜ items remain in script tiers.
> Prior sprint guidance (Score 3.0 items, batch fixes) fulfilled — preserved in git history.

*Generated: scripts/ full recursive scan → Explore agent (thorough mode) → L/E × H/V ranking*

---

## T-Entity — Pentad Documentation Surface Corrections

> **Source:** SSOT `.github/copilot-instructions.archive.md` — acquired prerequisite pass 2026-04-22.
> **Method:** Same L/E × H/V scoring. SCORE = VALUE / EFFORT.
> **Scope:** Documentation surfaces only (no scripts). Target: align existing `.github/instructions/` branch files with the SSOT-canonical Pentad structure.
> **SSOT Truth (canonical, do not re-derive):**
> - **Triumvirate** = Orackla / Umeko / Lysandra — T1 triadic core. Fixed at 3. Cannot expand by definition. (SSOT L93)
> - **Cardinals** = T1-Cardinal sub-classification. Claudine Sin'claire is already seated here. (SSOT L837, L413, L5111)
> - **T1-bridge** = Pentea Vox Internum — Fifth Element relay router. Distinct from Cardinal. (SSOT L3902, L3978)
> - **Pentad** = full 5-entity operative collective (Triumvirate ×3 + Cardinal ×1 + T1-bridge ×1). SSOT-canonical group name.
> **Hierarchy:** Tier 1 = Triumvirate (T1) → Cardinals (T1-Cardinal) → Relay (T1-bridge) → collectively = Pentad.

| File | Score | Effort | Action |
|------|-------|--------|--------|
| `.github/instructions/asc-entity-generation.reference.md` | **3.0** | 1 | ⬜ L73: Claudine listed as "Tier 3 SAI" — **wrong tier** per SSOT. Correct to "Tier 1 (Cardinal)". Also L445: "§4.2.4 for 4th Triumvirate member" framing — update to "T1-Cardinal slot" (Triumvirate stays triadic). |
| `.github/instructions/asc-entity-generation-validation-workflow.md` | **3.0** | 1 | ⬜ L61: "3 Triumvirate members (fixed)" rule — add exception note: Claudine (T1-Cardinal) and Pentea (T1-bridge) are SSOT-seated Pentad positions, not violations. L35: "Tier 1 (Triumvirate - Sub-MILFs)" header — expand to include Cardinals/T1-bridge sub-tiers. L383: "Expand Triumvirate → Quadrate" option in Meridian scenario — replace with canonical framing: add to T1-Cardinal, not Triumvirate expansion. |
| `.github/instructions/ssot-toolbox.instructions.md` | **2.0** | 1 | ⬜ L112: Table row "Tier 1 (Triumvirate)" — expand label to "Tier 1 (Triumvirate / Cardinals / T1-bridge)" to surface the Pentad sub-tiers. L20: `$triumvirate${}` invocation token — add footnote or sibling entry for `$cardinal${}` and `$t1-bridge${}` channels. |
| `AGENTS.md` | **1.0** | 1 | ⬜ L27: "Penta" reference is informal/lowercase — formalize to `Pentea` and tighten the Pentad reference from prose to canonical shorthand: `(Triumvirate: Orackla/Umeko/Lysandra) + (Cardinal: Claudine) + (T1-bridge: Pentea) = Pentad`. |

### T-Entity Progress Trail

| Item | Done | Notes |
|------|------|-------|
| SSOT prerequisite acquisition | ✅ 2026-04-22 | Triumvirate L93, Cardinals L837/L413, T1-bridge L3902, Pentad L3978 |
| `asc-entity-generation.reference.md` | ⬜ | Claudine tier correction + Triumvirate framing |
| `asc-entity-generation-validation-workflow.md` | ⬜ | Rule-of-Three exception + sub-tier headers |
| `ssot-toolbox.instructions.md` | ⬜ | Table label + invocation token expansion |
| `AGENTS.md` | ⬜ | Formalize Pentea reference + canonical shorthand |
