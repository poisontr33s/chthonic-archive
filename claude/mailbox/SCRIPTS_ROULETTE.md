# Scripts Assessment — TODO Roulette

> **Source:** Explore agent full scan of `scripts/` (recursive, all filetypes)
> **Method:** L/E × H/V scoring (1=low, 3=high). SCORE = VALUE / EFFORT.
> **Hierarchy:** T0 (auth/infra gates) → T1 (core CLI) → T2 (companion tools) → T3 (coherence/batch) → T4 (tests/docs) → T5 (noise/tombstone)
> **Sort:** Within each tier, SCORE descending. Highest-impact, lowest-effort items first.

---

## T0 — Infrastructure & Auth Gates (blocks other work)

| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/nightly-scheduled.ps1` | **3.0** | 1 | Fix typo `erdno`→`eldno` (functional bug!); add failure sentinel file on daemon crash |
| `scripts/api_pool.ps1` | **3.0** | 1 | Add JSON schema validation (require "env" hashtable key); add `-Verify` switch that re-reads and confirms each key non-empty |
| `scripts/desktop-warmup.ps1` | **3.0** | 1 | Wrap each step in try/catch → append to `$failures`; print step summary at end instead of raw exception abort |
| `scripts/mcp-filesystem.ts` | **3.0** | 1 | Add marker-string idempotency check before patching (`if (!src.includes("// chthonic-patch"))`); add package.json version assertion |
| `scripts/lib/poe_auth.py` | **3.0** | 1 | Return `valid: bool` on resolution; raise `ValueError` in `strict=True` mode (no silent `None`); add optional live token validation call |
| `scripts/lib/shared.py` | **3.0** | 1 | Add type annotations to all public functions; add `__all__`; cap `find_repo_root` traversal at 10 levels (no hitting filesystem root on CI) |
| `scripts/lib/ssot-paths.ts` | **3.0** | 1 | Add `as const` assertions; export `assertSsotExists(root)` that throws descriptively if SSOT path absent |
| `scripts/lib/ssot_paths.py` | **3.0** | 1 | Guard `sys.path.insert` with existence check; add `except ImportError` fallback with `DeprecationWarning` |
| `scripts/lib/ssot-paths.ps1` | **3.0** | 1 | Remove hardcoded line-count comment (maintenance liability); add `[switch]$AssertExists` to `Resolve-SsotPath` |

---

## T1 — Core CLI Surface

| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/claudine.ps1` | **2.0** | 1 | Rename param `$Args` → `$ChthonicArgs` (shadows PS builtin); add `-NoProfile` to inner chthonic.ps1 invocation |
| `scripts/gemini-cli-wrapper.ps1` | **2.0** | 1 | Add pre-flight binary check with `bun add @google/gemini-cli` hint; add `-Version` flag |
| `scripts/chthonic-xp.ps1` | **2.0** | 1 | Scope `ErrorActionPreference='SilentlyContinue'` to only the `Get-Content` loop; derive TrailDir from chthonic config first; add `-Debug` flag |
| `scripts/probe_toolchain_path.ps1` | **2.0** | 1 | Use `Get-Command <tool>` as primary probe; hardcoded paths as fallback only; emit probe-miss log |
| `scripts/polyglot_env.ps1` | **2.0** | 1 | Auto-invoke probe if output stale (>24h); print confirmation on `-Apply`; add `-Verify` that re-runs sfs.ps1 |
| `scripts/fortify_terminal.ps1` | **2.0** | 1 | Replace reflection hack with `[System.Console]::TreatControlCAsInput = $false`; also set `[Console]::InputEncoding` |
| `scripts/pause_agents.ps1` | **2.0** | 1 | Print backup path clearly; add `--restore` flag; validate `operationalMode` key exists before setting |
| `scripts/api_pool_persist_user_env.ps1` | **2.0** | 1 | Add drift detection in `-Status`: compare pool file keys vs User env keys; highlight "need -Apply" keys |
| `scripts/api_key_gap_report.ps1` | **2.0** | 1 | Compute repo root via PSScriptRoot-relative traversal; validate RegistryPath exists; add `-Json` flag |
| `scripts/claude_ide.ps1` | **1.5** | 2 | Validate .mcp.json with `ConvertFrom-Json` try/catch before write; backup existing `.mcp.json.bak`; add `verify-mcp` subcommand |
| `scripts/chthonic.ps1` | **1.5** | 2 | Add `$ErrorActionPreference = 'Stop'` after param block; propagate `$LASTEXITCODE`; add `--version` from package.json |
| `scripts/desktop-clone-state.ps1` | **1.0** | 2 | Add pre-export size estimate; check destination disk space; add `--exclude-git` (use git bundle instead) |

---

## T2 — Companion CLIs & Python Tooling

### Archaeology / Nightly Pipeline
| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/git_snapshot.py` | **3.0** | 1 | Add `--quiet/-q` (suppress stdout, file only); use `resolve_ssot_paths()` for mailbox dir; add `--since <ISO>` |
| `scripts/run_archaeology.ps1` | **3.0** | 1 | Print `$runFailures` at script end (currently accumulated but never shown); remove dead `-LocalV2` param; add `-What` switch |
| `scripts/run_overnight_daemon.ps1` | **2.0** | 1 | Use `Get-Command bun` first, fall back to hardcoded path; add `-Timeout N`; propagate exit code as `$LASTEXITCODE` |
| `scripts/overnight_daemon.ts` | **1.5** | 2 | Uncomment and configure Sentry (DSN via env); add `--emit-digest` flag writing `DAEMON_DIGEST_<date>.md` to `claude/mailbox/` |
| `scripts/local_refiner_v2.py` | **2.0** | 1 | Normalize output schema between `--mistralrs` and `--legacy-backend`; add `--validate`; add `--model-list` |
| `scripts/hf_refiner.py` | **2.0** | 1 | Add exponential backoff for HF 429/503; add `--model` flag; make `--ore-dir` configurable |

### HuggingFace Lane
| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/hf_auth_doctor.ps1` | **2.0** | 1 | Add `-Verify` flag calling `https://huggingface.co/api/whoami`; annotate user-scope vs process-scope in output |
| `scripts/hf_model_scout.py` | **2.0** | 1 | Add exponential backoff retry (3 attempts); add `--verify-timeout N` per model; handle `RateLimitError` |
| `scripts/hf_probe.py` | **2.0** | 1 | Wrap `huggingface_hub` import in try/except with install hint; use process env copy, don't mutate `os.environ` |
| `scripts/hf_discovery.py` | **2.0** | 1 | Add auth check at startup with clear error if unauthenticated; write `LATEST` alias JSON alongside timestamped output |
| `scripts/hf-model-ranker.ts` | **2.0** | 1 | Use `import.meta.dir`-relative DB path; add exponential backoff for HF 429; document Bun requirement in header |

### Poe Lane
| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/poe_lane.py` | **2.0** | 1 | Add `--timeout N`; add `--stream` flag for incremental output |
| `scripts/poe_sdk_lane.py` | **2.0** | 1 | Add graceful `ImportError` catch with `uv run --with fastapi-poe` hint; add `poe-sdk` extra to `pyproject.toml` |
| `scripts/poe_transport_audit.py` | **2.0** | 1 | Import `poe_lane`/`poe_sdk_lane` as Python modules (not subprocess); add `--cache` for unchanged model results |
| `scripts/poe_account.ps1` | **2.0** | 1 | Fall back to `scripts/api_pool.ps1 -Load` if skill path not found; validate resolved `POE_API_KEY` non-empty; add `-List` flag |

### Mistral.rs Lane
| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/mistralrs_model_manager.py` | **2.0** | 1 | Write PID to `~/.chthonic/mistralrs.pid` on start; check existing PID before start; add `stop` subcommand; clean PID on confirmed stop |

### MCP Servers
| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/mcp-chthonic-server.ts` | **1.5** | 2 | Add SENTRY_DSN presence check at startup; use JSON error objects with `code`+`message`+`context` in all catch handlers; add `tools/describe` introspection |
| `scripts/gemini-model-router.ts` | **1.5** | 2 | Backup `settings.json` → `.bak` before write; make registry version mismatch a warning with migration path; add `--dry-run` |
| `scripts/mcp-asc-injector.ts` | **2.0** | 1 | Add SSOT existence check at startup with clear error; add `ping` tool returning server version + SSOT file size |

### VS Code Tooling
| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/theme_contrast_audit.py` | **3.0** | 1 | Add `sys.path.insert` guard (same pattern as zombie_consumer.py); document exit codes; add `--emit-junit` for CI XML |
| `scripts/theme-sync.ps1` | **3.0** | 1 | After copy, verify key file hashes match source; add `-VerifyOnly` flag; use glob-based path-finding as primary strategy |
| `scripts/vscode_terminal_crash_doctor.ps1` | **2.0** | 1 | Convert `OutRoot` to PSScriptRoot-relative repo detection; document scoring formula in header comment; add `--score-only` |
| `scripts/vscode_insiders_matrix.ps1` | **2.0** | 1 | PSScriptRoot-relative `OutRoot`; add `-Skip @(...)` parameter; add `--json` for structured results |
| `scripts/vscode_settings_live_audit.py` | **2.0** | 1 | Auto-detect VS Code install path via registry query; add `--timeout` for `code-insiders --status` call |
| `scripts/vscode_electron_hardener.py` | **2.0** | 1 | Backup `argv.json` → `.bak` before write; use `code-insiders --status` to discover actual `user-data-dir` |
| `scripts/vscode_error_autopsy.py` | **2.0** | 1 | Add `--log-dir` flag to override discovery; add `--severity-min` filter |
| `scripts/insiders-sync.ps1` | **2.0** | 1 | PSScriptRoot-relative repo root; post-package validation that `.vsix` > 0 bytes; add `--dry-run` |
| `scripts/update-claude-code.ps1` | **2.0** | 1 | Remove retired `patch-claude-insiders.ps1` call; capture version before/after; print diff |

### Project Scaffolding / Workflow
| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/chthonic_new.py` | **2.0** | 1 | Capture stderr per command and report structured error; add `--verify` flag; expose as `new` subcommand in `chthonic.ps1` |
| `scripts/chthonic_workflow.py` | **2.0** | 1 | Add `--list` to enumerate workflow profiles; add `--dry-run`; expose as `workflow` subcommand |
| `scripts/apply_canonize_uv.sh` | **2.0** | 1 | Add pre-flight `git remote get-url origin` check; add `--dry-run`; add `set -e` or explicit exit-code checks in loop |
| `scripts/siphon_to_dumpster_dive.ps1` | **2.0** | 1 | Exclude the script itself from siphon list; write `siphon-manifest.json` to `DestRoot` after completion |

### Zombie Pipeline
| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/zombie_consumer.py` | **2.0** | 1 | Lazy-import `sentence-transformers` with install prompt; add `analysis` extra to `pyproject.toml` for sklearn |
| `scripts/zombie_forge_bridge.py` | **2.0** | 1 | Auto-create forge stage directories; emit batch-level receipt JSON; add `--undo <batch>` |

---

## T3 — Surface Coherence & Batch Fixes

### Batch: 9× skill_tensor probe import fix (high-value, ~5 min total)
All 9 files share the same broken import (`from skill_tensor_common import ...` → `from scripts.skill_tensor_common import ...`):

| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/skill_tensor_roulette.py` | **2.0** | 1 | **Batch fix:** Add `sys.path.insert(0, str(Path(__file__).resolve().parent))` OR change to `from scripts.skill_tensor_common import ...` |
| `scripts/skill_tensor_execute.py` | **2.0** | 1 | Same batch fix |
| `scripts/skill_tensor_feedback.py` | **2.0** | 1 | Same batch fix |
| `scripts/skill_tensor_inventory.py` | **2.0** | 1 | Same batch fix |
| `scripts/skill_tensor_ledger.py` | **2.0** | 1 | Same batch fix |
| `scripts/skill_tensor_plan.py` | **2.0** | 1 | Same batch fix |
| `scripts/skill_tensor_pool.py` | **2.0** | 1 | Same batch fix |
| `scripts/skill_tensor_render_spec.py` | **2.0** | 1 | Same batch fix |
| `scripts/skill_tensor_weights.py` | **2.0** | 1 | Same batch fix |
| `scripts/skill_tensor_cycle.py` | **2.0** | 1 | Replace inline `find_repo_root` with `from scripts.lib.shared import find_repo_root`; add `--stages`, `--resume` |
| `scripts/skill_tensor_common.py` | **2.0** | 1 | Add clear `FileNotFoundError` with "run skill_tensor_cycle.py first" hint; add `--latest-path` override |

### Consolidation / Deduplication
| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/sfs.ps1` | **3.0** | 1 | Make thin shim that dots-sources `shell_capabilities.ps1`; or add `gh`/`uv` keys to `shell_capabilities.ps1` and tombstone `sfs.ps1` with redirect comment |

### Path Fix Hotspot (hardcoded `erdno` bug)
| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/setup-gemini-claude.ts` | **2.0** | 1 | Fix `erdno`→`eldno`; use `import.meta.dir` to derive `CHTHONIC_ROOT`; add `CHTHONIC_ROOT` to `desktop-warmup.ps1` |
| `scripts/validate-triad-links.ps1` | **1.0** | 1 | Fix hardcoded path `erdno`→`eldno`; use PSScriptRoot-relative repo root; wrap `link_audit.py scan` instead of duplicating logic |
| `scripts/build_epistemograph.py` | **1.0** | 1 | Fix `erdno`→`eldno` in default `--root`; deprecate v1 in favor of v1.1 |

### Lint / Validation Infrastructure
| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/shebang-guard.ts` | **2.0** | 1 | Extend to scan `.py` files for `#!/usr/bin/env python3` on line 1 + `# -*- coding: utf-8 -*-` on line 2; add `.sh` check |
| `scripts/validate_script_headers.py` | **2.0** | 1 | Add `.ps1` and `.ts` header support via type-specific regex; add `--fix` to append missing metadata; emit per-file results |
| `scripts/install-hooks.ps1` | **2.0** | 1 | Add post-merge hook running `bun install --frozen-lockfile` if lockfile changed; add `-Force/-DryRun`; report existing hooks before overwrite |
| `scripts/bun-practices-audit.ts` | **2.0** | 1 | Read `skipDirs` from `bunfig.toml` or `.bun-practices.json`; add `--fix` to auto-replace npm/npx → bun/bunx |
| `scripts/bun_compliance_audit.py` | **2.0** | 1 | Verify `--fix` is implemented; add to pre-commit hook alongside `shebang-guard.ts`; add `--except` whitelist |
| `scripts/ankhrc_validator.py` | **2.0** | 1 | Use `find_repo_root()` from `lib/shared.py`; emit deprecation warning on tomllib fallback; add `--fix` |

### Mailbox / Handoff Pipeline
| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/handoff_loop.py` | **2.0** | 1 | Emit JSON receipt to `codex/mailbox/ROUTE_RECEIPT_<timestamp>.json`; make stale threshold configurable via `--stale-hours` |
| `scripts/mailbox_handoff.ps1` | **2.0** | 1 | Add JSON schema validation before routing; use PSScriptRoot-relative repo root detection |
| `scripts/mailbox_scribe.py` | **2.0** | 1 | Compute `POLICY_PATH` relative to `find_repo_root()`; warn explicitly if policy absent and document defaults |
| `scripts/mailbox_polisher.py` | **2.0** | 1 | Externalize patterns to `.meta/mailbox-polisher-patterns.json`; `--dry-run` should print table of files-to-archive + target path |
| `scripts/mailbox_compactor.py` | **2.0** | 1 | Use `find_repo_root()`; add `--since <ISO>` for incremental compaction; add `--max-files N` |

### SSOT Tools
| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/ssot_hash.py` | **2.0** | 1 | Import `SSOT_HOLDER` from `scripts.lib.ssot_paths`; add `--compare <hash_or_file>`; add `--write` to `.chthonic/ssot.sha256` |
| `scripts/ssot_structural_extractor.py` | **2.0** | 1 | Add `--output` flag; add `--quiet`/`--progress`; add `--verify-only` (hash comparison, no re-parse) |
| `scripts/ankh_theme_reference.py` | **2.0** | 1 | Use `SSOT_ARCHIVE_STRUCTURAL_INDEX.json` as parse source; add SSOT hash check to invalidate cached output |

### Theme Pipeline
| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/theme_parity.py` | **2.0** | 1 | Fix `MASTER_NAME` to actual comprehensive theme (not mandala); add `--master` flag; emit per-theme missing key count |
| `scripts/theme_promote_master.py` | **2.0** | 1 | Write `.bak` before any modification; add `--dry-run`; add `--distance-metric` flag |
| `scripts/theme_color_diversity.py` | **2.0** | 1 | Backup before modification; document threshold rationale in docstring; add `--variants N`; add `--report-only` |
| `scripts/theme_token_coverage.py` | **2.0** | 1 | Add `--theme` flag; add `--update-universe` fetching from vscode-textmate GitHub; add coverage % output |
| `scripts/theme_sfs_transmute.py` | **2.0** | 1 | Use absolute path via `Path(__file__).resolve().parents[1]`; add changeset hash for idempotency; add `--verify` |
| `scripts/theme_artcop.py` | **2.0** | 1 | Read and verify relationship with `vscode-art-cop.ts`; if duplicate, consolidate; add `--compare` for before/after |
| `scripts/milf_scanner.py` | **2.0** | 1 | Add `--dump-json` to emit full registry for TS/PS1 consumers; add sanity check for 14 required palette role keys |

### Icon / Font Pipeline
| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/generate-product-icon-font.mjs` | **2.0** | 1 | Add `#!/usr/bin/env bun` shebang; add `@SID` comment block; add pre-flight check validating all SVG paths exist |

### Skill Tooling
| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/build_skill_index.py` | **2.0** | 1 | Fix Purpose string in header; add `--output` defaulting to `codex/mailbox/SKILL_INDEX_LATEST.json`; add `--diff` |
| `scripts/skill_health.py` | **2.0** | 1 | Externalize rubric to `.meta/skill-health-rubric.json`; add `--since <ISO>`; add `--emit-badge` |
| `scripts/skill_audit.py` | **2.0** | 1 | Validate `--root` exists; read `CLAUDE_TOOLS` from config not hardcoded set; align output format with `skill_health.py` |

### Audit / Scan Tooling
| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/scm_triage.py` | **2.0** | 1 | Add `sys.path` guard; add `--apply` that writes gitignore entries with confirmation; add `--preview-gitignore` |
| `scripts/link_audit.py` | **2.0** | 1 | Write `.bak` before in-place fix; add `--no-backup` to skip; wrap git calls in try/except |
| `scripts/icon_scaffold_contract_audit.py` | **2.0** | 1 | Add explicit mkdir with feedback; add `--diff` vs previous audit JSON |
| `scripts/extension_universe_scanner.py` | **2.0** | 1 | Verify no circular import with `wptg_common`; add `--diff`; add `--output` flag |
| `scripts/rootdir_health_audit.py` | **2.0** | 1 | Use `find_repo_root()` + absolute output path; add `--severity-min`; add `--json` |
| `scripts/health_report.py` | **2.0** | 1 | Verify aggregated tool list is current; add `--tools` to specify sub-reports; add schema version to JSON |
| `scripts/map_codebase.py` | **2.0** | 1 | Verify still invoked; add `--output` if missing; add to `chthonic.py` dispatch table |
| `scripts/compact_md.py` | **2.0** | 1 | Verify `--backup` flag before in-place modification; register in `chthonic.ps1` command surface |
| `scripts/upcycle_audit.py` | **1.0** | 1 | Add `--dir` for recursive scan; externalize score thresholds; write JSON output for zombie pipeline integration |

### Cross-Agent Integration
| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/cross-critique.ts` | **2.0** | 1 | Validate `ANTHROPIC_API_KEY` at startup; add `--cache-dir` for round-1 output reuse; add `--merge-only <f1> <f2>` |
| `scripts/run_mcp_validation.ts` | **2.0** | 1 | Add `SIGINT` handler to kill spawned MCP server; add `--json` output; add `--check <tool_name>` |
| `scripts/milfographic-calculator.ts` | **2.0** | 1 | Read entity data from SSOT via structural index rather than inline constants; add `--compare <entity1> <entity2>` |

### Observability
| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/sentry_init.ts` | **2.0** | 1 | Emit `console.warn` when `SENTRY_DSN` absent; add `SENTRY_ENABLED=false` escape hatch for CI |
| `scripts/mcp-browser.ts` | **2.0** | 1 | Replace `__dirname` with `import.meta.dir`; add `// TODO(upstream): when @playwright/mcp ≥ X.Y stable, swap` comment |
| `scripts/mcp-sentry-proxy.ts` | **1.0** | 1 | Replace `!` non-null assertion on `SSOT_PATH` with runtime guard + `process.exit(1)` |

### Misc Surface
| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/embed_ore.py` | **1.0** | 1 | Lazy-import `sentence-transformers`; write embeddings cache to `.embedding_cache.json` keyed by file hash; add `--recompute` |
| `scripts/chthonic.py` | **1.0** | 1 | Import and call lib/ modules directly (remove subprocess.run shell dependency); add `--list-commands` from shared registry |

---

## T4 — Tests & Documentation Validation

| Script | Score | Effort | Action |
|--------|-------|--------|--------|
| `scripts/sfs_slabstone_baseline.py` | **2.0** | 1 | Normalize line endings in hash computation (CRLF→LF, same pattern as ssot_hash.py); add `--emit-json`; document exit codes in VS Code task |
| `scripts/gemini-model-router.test.ts` | **2.0** | 1 | Add `bun:test` to CI via `package.json test` script; parameterize registry with fixture file; add edge-case test for missing `fallbackModel` |

---

## T5 — Noise & Tombstone Queue

### Thin-shim conversions (retired scripts → delegates)
| Script | Action |
|--------|--------|
| `scripts/patch-claude-insiders.ps1` | Move to `scripts/.deprecated/`; remove call from `update-claude-code.ps1`; update SCRIPTS_README |
| `scripts/claude_healthcheck.ps1` | Thin shim → `& "$PSScriptRoot/claude_ide.ps1" health @args` |
| `scripts/claude_insiders_selfheal.ps1` | Thin shim → `& "$PSScriptRoot/claude_ide.ps1" heal @args` |
| `scripts/mcp_write_local.ps1` | Thin shim → `& "$PSScriptRoot/claude_ide.ps1" write-mcp @args`; remove from SCRIPTS_README active list |
| `scripts/validate-triad-links.ps1` | Fix `erdno`→`eldno`; thin-wrap around `link_audit.py scan`; or move to `.deprecated/` |

### Assess-before-act (read, then decide)
| Script | Status | Action |
|--------|--------|--------|
| `scripts/hf_gemma_probe.py` | Probable stale | Read; if one-off Gemma probe, merge useful logic into `hf_model_scout.py --family gemma`; move to `.deprecated/` |
| `scripts/hf_prep.py` | Probable stale | Read; if setup wrapper superseded by `desktop-warmup.ps1`, consolidate and tombstone |
| `scripts/mistralrs_client.py` | Probable dup | Read; if duplicates `mistralrs_model_manager.py ask`, consolidate as `lib/mistralrs_client.py` |
| `scripts/local_refiner.py` | Superseded v1 | Confirm `run_archaeology.ps1` calls v2; move v1 to `.deprecated/` |
| `scripts/vector_db.py` | Probable orphan | Read; determine if used by any active pipeline; tombstone if orphaned |
| `scripts/setup_db.py` | Probable dup | Read; consolidate with `build_epistemograph.py --init-db` if schema setup |
| `scripts/mandala_topology.py` | Ambiguous | Read; if theme-related → `theme_parity.py` pipeline; if dependency topology → `build_epistemograph.py` |
| `scripts/unified_topology.py` | Probable stale | Read; determine relationship with `build_epistemograph.py`; consolidate or tombstone |
| `scripts/extract_session_value.py` | Probable stale | Read; if superseded by dumpster-upcycler skill, tombstone |
| `scripts/chthonic.sh` | Probable stale | Read; if thin alias, document relationship with `chthonic.py`; otherwise `.deprecated/` |
| `scripts/build_epistemograph_v1.1.py` | Canonical v1.1 | Rename to `build_epistemograph.py` after v1 is tombstoned; add `--schema-path` flag |

### Prototypes (integrate or tombstone)
| Script | Action |
|--------|--------|
| `scripts/ide-polling-prototype.ts` | Integrate polling logic into `mcp-chthonic-server.ts` as health-check event; or move to `.deprecated/` |
| `scripts/claude-chthonic-bridge.ts` | Tombstone — `mcp-chthonic-server.ts` already provides MCP integration making this redundant |
| `scripts/background_services.py` | Add graceful shutdown via `asyncio.Event()` + SIGINT handler; write service PIDs; otherwise scope is too large for T5 |
| `scripts/autonomous_coordinator.py` | Decouple from `pleasure_protocol.py` (lazy import); add `--dry-run`; document "metabolize" concretely |
| `scripts/novia_cadaveris_embalmer.ps1` | Fix `Join-Path` for ssot-paths include; add source file existence validation in `-DryRun` |

### Partial / WIP (not worth active maintenance)
| Script | Action |
|--------|--------|
| `scripts/vscode-art-cop.ts` | Add LLM endpoint health check before screenshot submission; handle non-JSON responses |

---

## Quick-Win Cluster Summary

> Highest-ROI sprint: run all **Score 3.0** items first. All are Effort=1 (minutes each).

1. Fix `erdno`→`eldno` typo in `nightly-scheduled.ps1` + add failure sentinel — **2 min**
2. `api_pool.ps1` schema validation + `-Verify` switch — **10 min**
3. `desktop-warmup.ps1` try/catch accumulation — **15 min**
4. `mcp-filesystem.ts` marker-string idempotency — **10 min**
5. `lib/shared.py` type annotations + `__all__` + `find_repo_root` depth cap — **20 min**
6. `lib/ssot-paths.ts` as-const + `assertSsotExists` — **5 min**
7. `lib/ssot_paths.py` sys.path guard + ImportError fallback — **5 min**
8. `lib/ssot-paths.ps1` remove line-count comment + `AssertExists` param — **5 min**
9. `lib/poe_auth.py` strict mode + valid field — **10 min**
10. `sfs.ps1` → shim to `shell_capabilities.ps1` consolidation — **5 min**
11. `git_snapshot.py` `--quiet` + ssot_paths + `--since` — **15 min**
12. `run_archaeology.ps1` print failures + remove dead `-LocalV2` — **5 min**
13. `theme_contrast_audit.py` sys.path guard + `--emit-junit` — **10 min**
14. `theme-sync.ps1` post-copy hash verification — **15 min**

**Batch fix** the 9× `skill_tensor_*.py` import issue in one `sed`/grep-replace pass — **5 min total**.

---

*Generated: scripts/ full recursive scan → Explore agent (thorough mode) → L/E × H/V ranking*
