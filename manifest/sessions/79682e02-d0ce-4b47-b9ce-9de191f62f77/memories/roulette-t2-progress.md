# ROULETTE T2 Progress — current session

## Completed this session (commits)
- `2f66182b` — rootdir_health_audit.py: conflict resolved, sys.path guard, find_repo_root, --severity-min
- `351aea31` — health_report.py: fix __future__ placement, sys.path guard, --tools, --json, SCHEMA_VERSION
- `89cd4897` — map_codebase.py: sys.path guard, find_repo_root, --output flag
- `3deecb68` — compact_md.py: sys.path guard, --backup flag
- `be909709` — upcycle_audit.py: sys.path guard, --dir, externalize thresholds, --output

## Remaining T2 (in order)
10. cross-critique.ts — ANTHROPIC_API_KEY validation; --cache-dir; --merge-only
11. run_mcp_validation.ts — SIGINT handler; --json; --check <tool_name>
12. milfographic-calculator.ts — read from SSOT structural index; --compare
13. sentry_init.ts — console.warn when SENTRY_DSN absent; SENTRY_ENABLED=false escape
14. mcp-browser.ts — __dirname → import.meta.dir; TODO upstream comment
15. mcp-sentry-proxy.ts — lower priority (1.0)
16. embed_ore.py — lower priority (1.0)
17. chthonic.py — lower priority (1.0)

## Currently working on
#10 cross-critique.ts — read complete, implementing:
- ANTHROPIC_API_KEY validation already present; move to very first check
- --cache-dir: cache API responses by hash of (model, systemPrompt, userPrompt)  
- --merge-only: skip Round 1; use --version-a <file> --version-b <file>

## Key patterns
- sys.path guard: `_REPO_ROOT_CANDIDATE = Path(__file__).resolve().parent.parent; if str(_REPO_ROOT_CANDIDATE) not in sys.path: sys.path.insert(0, str(_REPO_ROOT_CANDIDATE))`
- Import: `from scripts.lib.shared import find_repo_root as _find_repo_root`
- No win32 stdout wrapping (causes ValueError with uv run)
- Commit trailer: `Co-authored-by: Pentea <223556219+Penteaa@users.noreply.github.com>`
- Commit format: `roulette(T2): <script-basename> — <1-line shorthand>`
- After all T2 done: update SCRIPTS_ROULETTE.md T2 row to ✅
