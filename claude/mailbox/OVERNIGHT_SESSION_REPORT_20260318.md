# Overnight Session Report — 2026-03-18

**Session scope:** Autonomous 8-hour "YOLO" cycle — commit, dependency wiring, transport infrastructure, MCP config.
**Commits:** 5 (from `6a87c67c` to `c2df70f2`)

---

## Completed Work

### 1. `link_audit.py` — Empty-label reclassification + corpse-vault skip

**Commit:** `6a87c67c` — `feat: Empty-label reclassification + corpse-vault skip in link_audit`

**Changes:**
- `resolve_link()` classifies `[](path)` as `"empty_label"` instead of `"ambiguous"` or `"broken"`
- `audit_file()` counts `empty_label` separately
- Scan output: totals line, JSON payload, `[EMPTY]` tag map all propagated
- Check output: summary line and tag map both propagated
- `SKIP_DIRS` now includes `"corpse-vault"` (19,516 files, zero inbound links)

**Validated baseline:**

| Metric | Before | After |
|---|---|---|
| Ambiguous | 21 | 0 |
| Empty-label | — | 21 |
| Broken | 5 | 5 (all anchors) |
| Fixable | 0 | 0 |
| Collision index | ~23k | ~4k |

---

### 2. `pyproject.toml` — Optional dependency groups + git tracking

**Commit:** `b0a94353` — `feat: Track pyproject.toml + add [poe] [openai] optional dependency groups`

**Changes:**
- Whitelisted `!pyproject.toml` in `.gitignore` (was excluded by `*` ignore-all pattern)
- Added `[poe]` extra: `fastapi-poe>=0.0.83,<1`
- Added `[openai]` extra: `openai>=1.82,<2`
- Existing extras preserved: `[analysis]` (radon), `[hf]` (mcp, pydantic-settings, requests)

**Install command for full lane coverage:**
```powershell
uv sync --extra poe --extra openai --extra hf --extra analysis
```

**Verified:** `uv sync` succeeded with all 4 extras.

---

### 3. API Pool Gap Report — Tracked

**Commit:** `756485a4` — `docs: Track API key gap report in codex mailbox`

**Summary:**
- 6/30 keys available (all 6 required present)
- 0 missing required keys
- 24 missing optional keys (expected — alternative providers not yet onboarded)
- Live providers: GitHub, Poe (×3 accounts), Hugging Face (×2 aliases)
- Files: `codex/mailbox/API_KEY_GAP_REPORT_20260317T233340Z.{md,json}`

---

### 4. `desktop-warmup.ps1` — Post-pull environment warmup

**Commit:** `416d8e27` — `feat: Add desktop-warmup.ps1 — post-pull environment warmup`

**Purpose:** Single idempotent command to arm the desktop after `git pull`.

**Steps:**
1. `git pull` (unless `-SkipPull`)
2. `uv sync --extra poe --extra openai --extra hf --extra analysis`
3. Load API pool into process env
4. Persist API pool to Windows User env (registry-backed)
5. Regenerate `.mcp.json` from pool
6. Verify: Poe auth + HF auth (unless `-SkipVerify`)

**Flags:** `-SkipPull`, `-SkipVerify`, `-DryRun`

**Verified:** Full run (with `-SkipPull`) — all 6 steps passed:
```
[1] git pull            — SKIP (SkipPull)
[2] uv sync             — OK
[3] API pool load       — OK
[4] User env persist    — OK (0 new vars — already persisted)
[5] .mcp.json regen     — OK (copilot mode)
[6] Poe + HF auth       — OK
```

---

### 5. MCP Config — `mas-mcp` wired into `.vscode/mcp.json`

**Commit:** `c2df70f2` — `feat: Wire mas-mcp server into .vscode/mcp.json`

**Added server:** `mas-mcp` (FastMCP, stdio via `uv run --directory mas_mcp python -m server`)

**6 tools now accessible in Copilot Chat:**
| Tool | Purpose |
|---|---|
| `mas_ssot_hash` | Compute SSOT file hash |
| `mas_narrative_scan` | Cultural drift against SSOT lexicon |
| `mas_qualia_check` | Phase 3 canonical alignment gate |
| `mas_scan` | Full codebase entity signal scan |
| `mas_pulse` | Archive vault + MPW source pulse |
| `mas_gpu_probe` | GPU capabilities |

---

## Architecture Assessment — Transport & Transverse

### Desktop Advantage (4090 / 25GB VRAM / 64GB RAM)

The desktop is the natural home for:
- **Local LLM inference** (`llama-cpp-python`, `exllamav2`) — scripts exist (`hf_model_scout.py`, `hf_refiner.py`)
- **Vector DB lanes** (`qdrant-client` + `sentence-transformers`) — `embed_ore.py`, `vector_db.py`
- **Full `uv sync --all-extras`** — heavy deps install cleanly with GPU drivers present

### Laptop-to-Desktop Sync ("Transverse Algorithm")

**Current state:** `scripts/desktop-clone-state.ps1` handles full VS Code Insiders user state export/restore/verify. API pool is user-profile (`~/.chthonic/api_pool.json`).

**Implemented transport pattern:**
1. **Git as the spine** — all committed code syncs via `git pull`
2. **API pool is portable** — user-profile, not repo
3. **uv resolves locally** — each machine gets its own lockfile for GPU driver compat
4. **MCP configs regenerate** — `claude_ide.ps1 write-mcp` rebuilds `.mcp.json` from pool
5. **`desktop-warmup.ps1`** — NEW: single command automates post-pull arming

**Remaining gap:** `uv.lock` not tracked in git (deliberate — GPU driver differences between machines). If CI is ever added, consider tracking it.

### MCP Configuration State (post-session)

| Server | Type | Status |
|---|---|---|
| `github` | stdio | Active (via `start_github_mcp.ps1`) |
| `browser` | stdio | Active (bun-cdp) |
| `bun-docs` | http | Active |
| `microsoft-docs` | http | Active |
| `filesystem` | stdio | Active |
| `asc-injector` | stdio | Active |
| `chthonic-v3` | stdio | Active (19 tools) |
| `mas-mcp` | stdio | **NEW** (6 tools) |

**Dual GitHub MCP note:** `.mcp.json` (Claude Code) uses Copilot proxy. `.vscode/mcp.json` uses the official Go binary via `start_github_mcp.ps1`. Both work in their respective contexts — not redundant, different auth paths.

### Poe SDK Status

- `fastapi-poe>=0.0.83` now tracked in `pyproject.toml [poe]`
- `openai>=1.82` now tracked in `pyproject.toml [openai]`
- Poe OpenAI-compatible lane (`poe_lane.py`) — auth verified live
- All 3 Poe accounts present in pool (`POE_API_KEY`, `POE_API_KEY_1`, `POE_API_KEY_2`)
- Optional enhancement: `poe_lane.py` could use `openai` client instead of raw `urllib.request` for cleaner error handling

---

## Next Session Ideas

1. **link_audit afterglow** — parked, resume when ready
2. **Poe transport upgrade** — optionally use `openai` client in `poe_lane.py`
3. **`uv.lock` portability** — consider tracking for CI/desktop clone speed
4. **Vector lane warmup** — wire `qdrant-client` + `sentence-transformers` as `[vector]` extra when version conflicts resolve
5. **`mas-mcp` Copilot Chat test** — verify the 6 tools surface correctly in @mas-mcp
6. **GPU-heavy extras** — `[local-llm]` bundle for `llama-cpp-python` / `exllamav2` on desktop only

---

## Commit Log

```
c2df70f2 feat: Wire mas-mcp server into .vscode/mcp.json
416d8e27 feat: Add desktop-warmup.ps1 — post-pull environment warmup
756485a4 docs: Track API key gap report in codex mailbox
b0a94353 feat: Track pyproject.toml + add [poe] [openai] optional dependency groups
6a87c67c feat: Empty-label reclassification + corpse-vault skip in link_audit
```
