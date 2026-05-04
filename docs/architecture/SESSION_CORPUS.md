---
- type: strategy
- category: architecture
- created: 2026-05-04
- origin: Claude + concept engineering session
- status: doctrine + corpus pipeline reference — second of a pair
- agents:
  - Claudine
  - Description: Iron foundation behind the nightly escapades — the DB that the vampire drains from, training scope corpus calls
- pair: docs/architecture/VAMPIRISM_SATELLITES.md
- References: scripts/session-corpus.ts, scripts/vampire-copilot-chat.ts, ci/checks/federation-contract-validate.ts, scripts/embed.py, scripts/embed_doctor.py, scripts/embed_model_registry.json

---

# Session Corpus: Pipeline Architecture

> **Doctrine:** The corpus is the federation hub. Satellites observe; the corpus retains. Drain artifacts are projections, not copies.  
> **Pair:** [`VAMPIRISM_SATELLITES.md`](VAMPIRISM_SATELLITES.md) — reads the same data from the other side.

---

## Quick Lookup: What Each File Does

| File | Role | Run |
|------|------|-----|
| `scripts/session-corpus.ts` | **INGEST** — transcript.jsonl → corpus.sqlite | `bun run session:corpus` |
| `scripts/vampire-copilot-chat.ts` | **DRAIN** — corpus.sqlite → drain.json + session_blood.json | `bun run vampire:drain` |
| `scripts/session-query.ts` | **QUERY** — corpus.sqlite → stdout reports | `bun run session:query` |
| `scripts/corpus-mcp.ts` | **SERVE** — corpus.sqlite → MCP tool surface | `bun run session:corpus:mcp` |
| `scripts/session-watcher.ts` | **MIRROR** — Copilot Chat dir → manifest/sessions/ | `bun run session:watch` |
| `scripts/embed.py` | **EMBED** — stdin JSON-lines → sentence-transformers → sqlite-vec | called by `session:corpus:embed` |
| `scripts/embed_doctor.py` | **PREFLIGHT** — validates HF cache + schema compatibility | auto-runs before `--embed` |
| `scripts/embed_model_registry.json` | **REGISTRY** — active model contract (dims, schema_version_required) | read by doctor + embed.py |
| `ci/checks/federation-contract-validate.ts` | **GATE** — satellite.json contract check | `bun run vampire:validate` |

**Data flow:**
```
GitHub.copilot-chat/transcripts/<sid>.jsonl
  → session-watcher.ts      (mirror to manifest/sessions/)
  → session-corpus.ts       (ingest to manifest/corpus.sqlite)
      └→ embed_doctor.py    (pre-flight: HF cache + schema compat)
      └→ embed.py           (sentence-transformers → vec_embeddings FLOAT[1024])
  → vampire-copilot-chat.ts (drain to manifest/sessions/*/drain.json + session_blood.json)
  → session-query.ts        (report)
  → corpus-mcp.ts           (MCP surface: FTS5 + semantic search)
```

---

## corpus.sqlite — Schema (PRAGMA user_version = 4)

### Core Tables

| Table | Primary Key | Purpose |
|-------|-------------|---------|
| `sessions` | `sessionId` | Session metadata — intent, topic, tags, turn count, workspace |
| `session_restarts` | `id` | VS Code / Copilot version change events within a session |
| `file_edits` | `id` | Every file edit tool call: path, tool name, turn |
| `terminal_cmds` | `id` | Terminal commands: command text, goal, explanation, turn |
| `code_blocks` | `id` | Code blocks emitted: lang, line count, 120-char preview |
| `tool_calls` | `id` | All tool invocations with args, result snippet, success flag |
| `commit_refs` | `(sha, sessionId)` | Git commits referenced in session |
| `memory_snapshots` | `id` | Memory file contents captured at ingest time |
| `messages` | `id` | Full message content (role=user/assistant, turn, ts) |
| `entities` | `id` | Named entities extracted cross-session: name, type, first/last seen |
| `entity_occurrences` | `id` | Per-session entity mention: turn, context snippet |
| `vec_embeddings` | `rowid` | sqlite-vec virtual table — FLOAT[1024] Matryoshka embeddings (G7, Qwen3-Embedding-0.6B) |

### Views

| View | Purpose | Key Columns |
|------|---------|-------------|
| `session_ranked` | Ranked session quality — edit + cmd density | `sessionId`, `editCount`, `cmdCount`, `codeBlockCount`, `score` |
| `hot_files` | Most-edited files (cross-session) | `filePath`, `editCount`, `sessionCount` |
| `memory_chain` | Memory file evolution across sessions | `filename`, `sessionId`, `capturedAt`, `content` |
| `session_timeline` | Full denormalized session row | All sessions columns + `userTurns`, `assistantTurns` |
| `entity_cooccurrence` | Entities appearing in same session | `entityA`, `entityB`, `coSessionCount` |

### Key Columns on `sessions`

```sql
sessionId       TEXT PRIMARY KEY,   -- UUID from transcript filename
startTime       TEXT,               -- ISO8601
workspaceHash   TEXT,               -- federation key ↔ vscode-surface satellite
workspaceName   TEXT,
copilotVersion  TEXT,
vscodeVersion   TEXT,
turns           INTEGER,
intent          TEXT,               -- inferred session intent (LLM-classified)
topic           TEXT,
tags            TEXT,               -- JSON array
note            TEXT,
ingestedAt      TEXT
```

---

## Gate Ladder (G0–G9)

**Type:** `infra` · `schema` · `pipeline` · `view` · `satellite` · `enrich` · `federation`  
**Sub:** variant suffix — `a/b/c` for parallel tracks, `.0` for pre-gate subtype  
**State:** ✅ done · ⬜ pending · ❌ impossible_currently  
**Level:** L4 admitted · L3 hardened · L2 functional · L1 scaffold · L0 blocked  

| Gate | Type | Sub | State | Level | Description | Unlocks | Commit |
|------|------|-----|-------|-------|-------------|---------|--------|
| G0 | infra | — | ✅ done | L4 | SQLite init, WAL mode, base DDL | G1a, G1b | f7f276a9 |
| G1a | schema | a | ✅ done | L4 | Session ingestion (transcripts → sessions) | G2 | f7f276a9 |
| G1b | schema | b | ✅ done | L4 | Turn ingestion (messages table) | G2 | f7f276a9 |
| G2 | pipeline | — | ✅ done | L4 | Artefact extraction (edits, cmds, code_blocks) | G5, G6 | f7f276a9 |
| G5 | view | — | ✅ done | L4 | FTS5 virtual table on messages.content | `--search` | f7f276a9 |
| G6 | view | — | ✅ done | L4 | session_ranked + hot_files + memory_chain views | G8b, G7.0 | d1509972 |
| G8b | enrich | b | ✅ done | L4 | Entity DDL + cross-session tracking | entity MCP | d1509972 |
| G7.0 | satellite | .0 | ✅ done | L4 | `vampire-copilot-chat.ts` — corpus-native drain | vampire:* | 82c60dd7 |
| G7 | satellite | — | ✅ done | L4 | sqlite-vec 0.1.9 + Qwen3-Embedding-0.6B 1024d Matryoshka (Apache-2.0, 32k ctx, CUDA, schema v4 — upgraded 2026-05-04 from all-MiniLM-L6-v2 384d, pipeline hardened `13089647`) | semantic search | 72954168 |
| G8a | enrich | a | ⬜ pending | L0 | LLM summaries → `sessions.intent` auto-populate | intent queries | after G7 |
| G8c | view | c | ⬜ pending | L0 | Cross-session derived views (trend, velocity) | G9 | after G8a |
| G9 | federation | — | ⬜ pending | L0 | ATTACH DATABASE multi-satellite merge | full federation | after G8c |

**Gate check:** `bun run ci/checks/inference-gate-smoke.ts --report`  
**Corpus state:** `bun run session:query --status` → reads `manifest/corpus-state.json`

---

## corpus-state.json — Live Status Artifact

Emitted to `manifest/corpus-state.json` on every ingest run. This is the fast-lookup sync signal between the corpus and any satellite.

```json
{
  "schema_version": 4,
  "ingest_ts": "2026-05-04T20:18:26.096Z",
  "sessions": 13,
  "entities": 1073,
  "entity_occurrences": 16637,
  "gate_ladder": {
    "G0": true,  "G1a": true, "G1b": true,
    "G2": true,  "G5": true,  "G6": true,
    "G8b": true, "G7": true,
    "G8a": false, "G8c": false
  },
  "vec_count": 13,
  "vec_model": "Qwen/Qwen3-Embedding-0.6B",
  "vec_dims": 1024,
  "satellites": []
}
```

**Satellite sync contract:** Any satellite reads `corpus-state.json` before attempting federation. If `schema_version < corpus_schema_min` in the satellite's `satellite.json` → abort and emit upgrade hint. This file is the handshake.

---

## MCP Tool Surface (corpus-mcp.ts)

Four tools available when `session:corpus:mcp` is running:

| Tool | Inputs | Returns |
|------|--------|---------|
| `corpus_search` | `query: string, limit?: number` | FTS5 ranked results from messages |
| `corpus_semantic_search` | `query: string, limit?: number` | sqlite-vec ANN search via Qwen3-Embedding-0.6B 1024d embeddings |
| `corpus_session` | `sessionId: string` | Full session row + edit/cmd counts |
| `corpus_entities` | `name?: string, type?: string` | Entity records + occurrence count |
| `corpus_timeline` | `limit?: number, minTurns?: number` | session_ranked view rows |

MCP transport: stdio (default) — add to `settings.json` `mcpServers` block.

---

## CLI Reference — All Corpus Commands

```powershell
# INGEST
bun run session:corpus                      # incremental ingest (new sessions only)
bun run session:corpus:rebuild              # drop + full reingest
bun run session:corpus:classify             # re-run intent classification on all sessions
bun run session:corpus:stats                # print DB stats to stdout
bun run session:corpus:watch                # continuous watch mode
# HF token required — inject before embedding:
. .\scripts\api_pool.ps1 -Quiet; bun run session:corpus -- --embed
bun run session:corpus -- --embed           # embed all non-embedded sessions (doctor pre-flight auto-runs)
bun run session:corpus -- --embed --dry-run # doctor pre-flight only — no embedding
bun run session:corpus:rebuild              # full rebuild (drop + ingest + no embed)
. .\scripts\api_pool.ps1 -Quiet; bun run scripts/session-corpus.ts --rebuild --embed  # full rebuild + embed in one pass

# EMBED PRE-FLIGHT
uv run scripts/embed_doctor.py --current-schema-version 4  # standalone doctor check
# Model registry: scripts/embed_model_registry.json (active_model_id, dims, schema_version_required)
# HF token source: scripts/api_pool.ps1 → sets HF_TOKEN + HUGGINGFACE_HUB_TOKEN for subprocess

# QUERY
bun run session:query                       # summary (session count, top files, top tools)
bun run session:query --status              # corpus-state.json pretty-print
bun run session:query --timeline            # session_ranked view
bun run session:query --hot-files           # hot_files view
bun run session:query --tool-frequency      # tool call frequency table
bun run session:query --search <term>       # FTS5 search
bun run session:query --messages            # recent messages log

# DRAIN (vampire)
bun run vampire:drain                       # drain all sessions → manifest/sessions/*/drain.json
bun run vampire:drain --session <id>        # single session
bun run vampire:blood                       # cross-session blood index (session_blood.json)
bun run vampire:nightly                     # last-24h digest → manifest/vampire_nightly_*.json
bun run vampire:extract:edits               # hot-file table from drain data
bun run vampire:extract:commands            # terminal commands across sessions
bun run vampire:extract:code                # code blocks across sessions
bun run vampire:extract:memories            # memory file inventory

# SATELLITE / FEDERATION
bun run vampire:validate                    # validate vampire-copilot-chat satellite.json
bun run ci/checks/federation-contract-validate.ts --report     # all satellites
bun run ci/checks/federation-contract-validate.ts --register <path>  # enroll new satellite
```

---

## Lossless Identity: drain.json ↔ corpus.sqlite

The vampire does not re-parse transcripts. Every `drain.json` is a SQL projection of the corpus, provable by the `_corpus_ref` frontmatter block embedded in every drain artifact:

```json
{
  "_corpus_ref": {
    "sessionId":      "2b2dfd13-5eee-...",
    "schema_version": 4,
    "corpus_path":    "manifest/corpus.sqlite",
    "workspaceHash":  "eccd2abd...",
    "startTime":      "2026-05-04T01:32:00Z",
    "drainedAt":      "2026-05-04T03:00:01Z"
  },
  "sessionId": "2b2dfd13-5eee-...",
  ...
}
```

**Cross-check query:**
```sql
SELECT s.sessionId, s.intent, s.turns
FROM sessions s
WHERE s.sessionId = '2b2dfd13-5eee-...';
-- Must match drain.json.sessionId + sessionIntent + turns exactly
```

`drain.json.sessionId` === `corpus.sessions.sessionId` — same object, two surfaces.

---

## Pair Handshake: How These Two Documents Sync

| Question | Answer location |
|----------|-----------------|
| What does the corpus store? | **This file** — schema tables, gate ladder, column reference |
| How does a satellite read the corpus? | **This file** — corpus-state.json contract, ATTACH mode |
| What does a satellite _look like_? | [VAMPIRISM_SATELLITES.md](VAMPIRISM_SATELLITES.md) — satellite class definition, `satellite.json` spec |
| Which satellites exist? | [VAMPIRISM_SATELLITES.md → Satellite Inventory](VAMPIRISM_SATELLITES.md#satellite-inventory) |
| What's the overnight mode? | [VAMPIRISM_SATELLITES.md → Nightly Escapades](VAMPIRISM_SATELLITES.md#nightly-escapades) + `bun run vampire:nightly` |
| What gate am I on? | `bun run session:query --status` → `corpus-state.json#gate_ladder` |
| How do I start a new satellite? | [VAMPIRISM_SATELLITES.md → Satellite Implementation Guide](VAMPIRISM_SATELLITES.md#satellite-implementation-guide) |

Fast pickup rule: if you are **building or observing** → start in `VAMPIRISM_SATELLITES.md`.  
If you are **ingesting or querying** → start here.
