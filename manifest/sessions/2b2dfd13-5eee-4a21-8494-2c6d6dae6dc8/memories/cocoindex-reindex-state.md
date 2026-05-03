# CocoIndex Reindex Session State (2026-05-01)

## What was changed
1. `chthonic-archive/.cocoindex_code/settings.yml` — added exclusions:
   - `.github/**` (OOM source — SSOT 1.08 MB crashes daemon)
   - `dumpster-dive/**`, `manifest/**`, `models/**`, `data/**`, `logs/**`
   - `artifacts/**`, `debugging_data/**`, `audit-reports/**`, `out/**`, `build/**`
   - Lock files, `filesystem_root/**`, `mcp_fs_root/**`, `chthonic-golden/**`
   
2. `PsychoNoir-Kontrapunkt/.cocoindex_code/settings.yml` — added exclusions:
   - `logs/**`, `data/**`, `backups/**`, `temporal_backups/**`, `SESSION_SNAPSHOTS/**`
   - `necromancy_graveyard/**`, `archives/**`, `emigration/**`, `temp_build/**`
   - `static_mobile_chat/**`, `KNOWLEDGE_BASE/**`, lock files

3. `~/.cocoindex_code/global_settings.yml` — reduced `max_file_size: 524288` (512 KB) from 2MB

## Current state
- chthonic-archive DB: `target_sqlite.db` = 0 MB (corrupted/empty, needs clean rebuild)
- Expected scope after exclusions: ~620 files (down from 11,197)
- Expected chunk count: ~3-8K (down from 158,673 — 84% was JSON noise)
- "618 unchanged, error: 2" repeating — daemon caching state across kills

## CRITICAL FINDINGS (2026-05-01 session continuation)

### max_file_size and batch_size are NOT real settings
- `max_file_size` is NOT in `ProjectSettings` dataclass → silently ignored
- `batch_size` is NOT in `EmbeddingSettings` dataclass → silently ignored  
- `index.respect_gitignore` → also ignored (not in UserSettings)
- The real supported settings: `embedding.{provider,model,device,min_interval_ms,indexing_params,query_params}` and `{include_patterns,exclude_patterns,language_overrides,chunkers}`

### Real OOM source: meta-ide/ minified JS bundles (NOT SSOT)
- `meta-ide/copilot-cli-0.0.406/index.js` = 15 MB minified JS
- `meta-ide/copilot-sdk/sdk/index.js` = 11 MB minified JS
- Minified JS has NO split points → `RecursiveSplitter` returns whole file as ONE chunk
- One 15 MB minified JS = ~3.75M tokens → single chunk → padded to 8192 tokens? Actually might be attempted as-is
- Default batch_size (from Rust backend) = 32 (NOT our setting, which was ignored)
- 32 × 24 heads × 8192 × 8192 × 2 bytes = 96 GiB → matches the exact error
- `.github/**` exclusion IS working (confirmed by daemon log search)

### CRITICAL FIX: transformers 5.7.0 + NomicBertModel incompatibility
- **symptom**: `TypeError: NomicBertModel.__init__() got an unexpected keyword argument 'safe_serialization'`
- **root cause**: transformers 5.x added `safe_serialization` kwarg to model instantiation; built-in NomicBertModel at `~\AppData\Roaming\uv\tools\cocoindex-code\Lib\site-packages\transformers\models\nomic_bert\modeling_nomic_bert.py` line ~392 lacked `**kwargs`
- **fix applied**: added `**kwargs` to `NomicBertModel.__init__` signature in `modeling_nomic_bert.py`  
- **verification**: `SentenceTransformer('nomic-ai/CodeRankEmbed', device='cuda')` loaded in 9.4s, encoded shape `(1, 768)` OK  
- **note**: transformers 5.x has BUILT-IN NomicBertModel (NOT loaded from HuggingFace cache `modeling_hf_nomic_bert.py`). Also patched cache file but that was wrong target.
- **NOTE**: This patch will be LOST on `uv tool upgrade cocoindex-code`. Re-apply after upgrades.

### Fixed exclusions in settings.yml
- Added `meta-ide/**` — bundled JS: the CONFIRMED OOM source (15 MB + 11 MB minified)
- Added `claude/mailbox/**` — SSOT convenience copy at 1.1 MB (second OOM risk)
- Added `rv/**` — Ruby package library (jQuery etc.)
- Added `extensions/**/.vscode-test/**` — vscode test fixtures
- Added `codex/mailbox/**` — 38 MB tensor JSON
- Added binary formats: `*.dll`, `*.dmp`, `*.zip`, `*.db`, `*.pyd`, `*.exe`, `*.npz`

### Still potentially large (verify after reindex)
- `docs/protocols/CROSS_REFERENCE_TRIPTYCH_ORIGINAL_6637.md` — 933 KB (markdown, splittable)
- `extensions/*/vscode.d.ts` — 724 KB each (TypeScript defs, structured)
- `claude-codex-gemini/triadic-session-context/SSOTI_FIED_SESSION_LOG.md` — 717 KB

### cocoindex-code chunking
- CHUNK_SIZE=1000, MIN_CHUNK_SIZE=250, CHUNK_OVERLAP=150 (characters)
- For files WITH a registered chunker: language-specific first, then splitter
- For files WITHOUT a chunker (markdown, plain text): `RecursiveSplitter.split()` with above params
- Minified JS: NO newlines → splitter can't find split points → returns whole file as one chunk → OOM

## Fix procedure (next ccc index attempt)
1. `taskkill /FI "IMAGENAME eq ccc.exe" /F`
2. `Remove-Item "~/.cocoindex_code/daemon.pid"` + `daemon.log` 
3. `Remove-Item "chthonic-archive/.cocoindex_code/target_sqlite.db" -Force`
4. `& "C:\Users\eldno\.local\bin\ccc.exe" index 2>&1` from chthonic-archive dir
5. Expected: no OOM, ~620 files, clean completion

## PsychoNoir — not yet reindexed with new settings
- Need to kill daemon, delete `PsychoNoir-Kontrapunkt/.cocoindex_code/target_sqlite.db`, reindex
