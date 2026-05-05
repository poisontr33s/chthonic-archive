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
| `scripts/embed_model_registry.json` | **REGISTRY** — active model contract (dims, schema_version_required, gated status) | read by doctor + embed.py + embed_gate_accept.py |
| `scripts/embed_gate_accept.py` | **GATE** — HF gated model acceptance (Tier 0 registry guard → Tier 1 REST API → Tier 3 Bun.WebView form; G7-REDUX) | `uv run scripts/embed_gate_accept.py` |
| `scripts/hf_gate_playwright.ts` | **WEBVIEW** — Tier 3 Bun.WebView headless form-gate acceptor (Bun v1.3.12+ native, no npm/playwright dep; `efdce1e4`) | called by `embed_gate_accept.py --allow-playwright` |
| `ci/checks/federation-contract-validate.ts` | **GATE** — satellite.json contract check | `bun run vampire:validate` |

**Data flow:**
```
GitHub.copilot-chat/transcripts/<sid>.jsonl
  → session-watcher.ts      (mirror to manifest/sessions/)
  → session-corpus.ts       (ingest to manifest/corpus.sqlite)
      └→ embed_gate_accept.py  (HF gating: Tier 0 registry guard → Tier 1 REST API → Tier 3 Bun.WebView; skips if gated:false)
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
| G7 | satellite | — | ✅ done | L4 | sqlite-vec 0.1.9 + Qwen3-Embedding-0.6B 1024d Matryoshka (Apache-2.0, 32k ctx, CUDA, schema v4 — upgraded 2026-05-04 from all-MiniLM-L6-v2 384d; pipeline hardened `13089647`; gated automation `ca14e308`; Bun.WebView Tier 3 `efdce1e4`) | semantic search | 72954168 |
| G8a | enrich | a | ✅ done | L2 | Heuristic topic classification (`classifyAll` — TOPIC_SIGS keyword scoring → `sessions.topic`); LLM summarization (MCP sampling G8a-next) | intent queries | `12581b3c` |
| G8c | view | c | ✅ done | L2 | Cross-session entity co-occurrence (`entity_cooccurrence` view — entities appearing in ≥2 sessions) | `--entity-graph` | `12581b3c` |
| G9 | federation | — | ⬜ pending | L0 | ATTACH DATABASE multi-satellite merge | full federation | after G8c |

**Gate check:** `bun run ci/checks/inference-gate-smoke.ts --report`  
**Corpus state:** `bun run session:query --status` → reads `manifest/corpus-state.json`

---

## G7-REDUX: HF Gated Model Acceptance Pipeline

> **Context:** Introduced at `ca14e308`–`efdce1e4` (2026-05-04/05). Solves the problem of programmatically accepting HF model gates so a future switch to a gated embedding model (e.g. `google/embeddinggemma-300m`) requires zero manual HF Hub UI interaction.

The ladder is tried in order, stops at first success:

| Tier | Name | Mechanism | Fires when | Key commit |
|------|------|-----------|------------|-----------|
| 0 | **Registry guard** | Read `embed_model_registry.json#models[id].gated` — if `false`, exit 0 immediately | Always first; `Qwen3-Embedding-0.6B` takes this path | `ca14e308` |
| 1 | **HF REST API** | `POST /api/models/{id}/agree-terms` via stdlib `urllib` (zero deps) — HTTP 200 = accepted, 400 = already accepted | `gated: "auto"` (Gemma, Mistral, nomic, etc.) | `ca14e308` |
| 2 | *(none)* | No HF CLI binary provides gate acceptance; agree-terms IS the CLI path | — | — |
| 3 | **Bun.WebView** | `bun run scripts/hf_gate_playwright.ts` — Bun.WebView native (v1.3.12+), Chrome backend via DevTools Protocol, `isTrusted: true` OS-level events, no npm/playwright dep, no Named Pipes IPC | `gated: "form"` (Meta Llama, some Mistral) or Tier 1 403; only when `--allow-playwright` passed | `efdce1e4` |

**Active model shortcut:** `Qwen/Qwen3-Embedding-0.6B` has `gated: false` → Tier 0 fast-exit; Tier 3 is dormant until a form-gated model is set as `active_model_id`.

**Extra wins from Bun.WebView (vs old playwright):**
- No `@playwright/test` npm dep — transitive playwright install eliminated
- No `child_process.spawn` Named Pipes IPC layer — zero `\\.\pipe\wrapper-*` ENOENT risk
- No zombie `chrome.exe` on timeout — `Symbol.asyncDispose` / `await using` guarantees cleanup
- OS-level `isTrusted: true` events pass bot-detection heuristics that synthetic playwright events fail

**Output contract (JSON to stdout):**
```json
{
  "model_id": "some/model",
  "gated": "auto",
  "status": "accepted_now",
  "method": "hf_api",
  "detail": "Accepted (HTTP 200)",
  "pass": true
}
```
`method` values: `"none"` · `"hf_api"` · `"bun_webview"` · `"bun_webview_unavailable"` · `"check_only"`

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
    "G8a": true, "G8c": true
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

# HF GATE ACCEPTANCE (G7-REDUX — run before --embed when switching to a gated model)
# Tier 0: registry guard  — gated:false → exit 0, zero network (Qwen3-Embedding-0.6B is gated:false; fast-exit)
# Tier 1: HF REST API     — POST /api/models/{id}/agree-terms (gated="auto": Gemma, nomic, etc.)
# Tier 3: Bun.WebView     — headless Chromium form submission (gated="form": Meta Llama, some Mistral)
uv run scripts/embed_gate_accept.py                       # accept for active_model_id (Tier 0 fast-exit if not gated)
uv run scripts/embed_gate_accept.py --check-only          # status only, no acceptance
uv run scripts/embed_gate_accept.py --model-id some/model # target a specific model
uv run scripts/embed_gate_accept.py --allow-playwright    # enable Tier 3 Bun.WebView for form-gated models

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

---

## GHC Integration Vectors (v1.99–v1.102)

> **Context:** How the VS Code Insiders + Copilot Chat release cycle (v1.99–v1.102) aligns with or extends the corpus pipeline architecture. Research date: 2026-05-04 (anno).

### MCP Layer Alignment

`corpus-mcp.ts` is a first-class MCP surface (four tools: `corpus_search`, `corpus_semantic_search`, `corpus_session`, `corpus_entities`, `corpus_timeline`). The v1.99–v1.102 cycle advances MCP from experimental to GA and materially widens the protocol surface:

| MCP Evolution | Version | corpus-mcp.ts Impact |
|--------------|---------|----------------------|
| MCP server support lands in stable | v1.99 | `corpus-mcp.ts` is a first-class VS Code server from this release |
| MCP Streamable HTTP transport | v1.100 | Future: streaming `corpus_search` result pages |
| MCP prompts (`/mcp.server.prompt` slash cmds) | v1.101 | `/mcp.corpus.gate_status` as a slash command exposed from `corpus-mcp.ts` |
| MCP resources (attach as context) | v1.101 | `manifest/corpus-state.json` as an MCP resource — gate ladder always in context |
| MCP sampling — servers request back to model | v1.101 | G8a (LLM session summaries) can be triggered from within corpus-mcp via sampling |
| **MCP GA** — stable protocol, org policy, curated list | v1.102 | Breaking-change risk removed; server management view replaces manual `settings.json` |
| MCP in profile-scoped `mcp.json` (not `settings.json`) | v1.102 | New high-signal sovereignty surface (see below) |
| MCP elicitations — server requests input | v1.102 | `corpus-mcp.ts` can elicit query parameters (session date range, tag filter) interactively |

**Action:** `corpus-mcp.ts` registration moves from `settings.json#mcpServers` to profile-scoped `mcp.json` when user upgrades to v1.102. Registration block:
```json
{
  "corpus": {
    "command": "bun",
    "args": ["run", "scripts/corpus-mcp.ts"],
    "cwd": "${workspaceFolder}"
  }
}
```

### Satellite New Surface: `User/mcp.json`

With MCP GA in v1.102, `%APPDATA%\Code - Insiders\User\mcp.json` becomes a profile-scoped sovereignty surface: it records which MCP servers run, their auth config, and tool exposure. The `vampire-vscode-surface` satellite source contract (defined in `VAMPIRISM_SATELLITES.md`) must include this path alongside the existing `sync/` surface.

**Schema extension for `vscode_sync_queue`:**
```sql
-- surface: 'mcp_profile' — new surface type for mcp.json capture
-- item_id: '<profile_name>_mcp' — one row per profile
-- payload: full mcp.json content (BLOB) — what servers run, what tools they expose
-- captured_ts: epoch when captured; upload_ts NULL = captured before upload
INSERT INTO vscode_sync_queue (item_id, surface, payload, captured_ts)
VALUES ('default_mcp', 'mcp_profile', readfile('User/mcp.json'), unixepoch());
```

**Why this matters:** The `sync/` surface already captures settings sync payloads. `mcp.json` is a new parallel sovereignty surface — a user's MCP server list is a high-signal artifact (reveals what AI tools run, what data they can access). Observing it locally before Settings Sync uploads it is consistent with the Vampirism doctrine.

### CLI Dispatch (`code chat` — v1.102)

`code chat` CLI opens a direct automation path for corpus-aware scripts without opening the VS Code UI:

```powershell
# Pipe gate status to agent for autonomous analysis
bun run session:query --status | code chat -m agent -a manifest/corpus-state.json "analyze gate ladder and recommend next action"

# Run gate walk step non-interactively
code chat -m agent "execute G3 gate: write transition_image_layout() in vulkan-lab/cli-renderer/src/main.rs"

# Stdin injection: session timeline → agent
bun run session:query --timeline | code chat -m agent - "summarize corpus quality delta since last embed pass"

# Run with custom gate-walk mode (v1.101+)
code chat -m gate-walk "advance to G3, commit with --no-verify and Pentea co-author trailer"
```

**Automation chain:** `scripts/chthonic.ps1` can wrap `code chat` for scheduled autonomous gate ticks. Combined with terminal auto-approval, full gate cycles run without UI interaction.

### Terminal Auto-Approval — Chthonic Toolchain Config (v1.102)

`github.copilot.chat.agent.terminal.allowList` + `denyList` enable unattended terminal dispatch. Recommended `.vscode/settings.json` additions for chthonic-archive gate-walk automation:

```jsonc
"github.copilot.chat.agent.terminal.allowList": [
  "bun run",         // corpus ingest, vampire drain, gate checks, embed
  "uv run",          // embed.py, embed_doctor.py, embed_gate_accept.py, probes
  "cargo build",     // vulkan-lab cli-renderer
  "cargo check",
  "cargo clippy",
  "cargo test",
  "git add -f",      // vulkan-lab/ and tools/ are .gitignored — -f required
  "git commit",      // --no-verify standard in chthonic-archive
  "git status",
  "git log",
  "rv",              // Ruby toolchain
  "pwsh"             // PowerShell scripts (chthonic.ps1, api_pool.ps1)
],
"github.copilot.chat.agent.terminal.denyList": [
  "rm -rf",
  "Remove-Item -Recurse -Force",
  "git push --force",
  "git reset --hard"
]
```

**Corpus integrity note:** `chthonic-shell-hook.ps1` logs all terminal commands to `manifest/terminal_session.jsonl`. With auto-approval, agent-dispatched terminal commands land in the JSONL alongside manual commands. The `source` field does not currently distinguish them — this is a future schema consideration for `terminal_cmds` in `corpus.sqlite` (add `source TEXT CHECK(source IN ('manual', 'agent', 'script'))`).

### Gate-Walk Custom Chat Mode (v1.101/v1.102)

Custom chat modes (`*.chatprompt.md`) with `model:` frontmatter (v1.102) encode the gate-walk context at mode entry:

```markdown
---
description: Chthonic Archive gate-walk mode — corpus tools + gate status always in context
tools:
  - corpus_search
  - corpus_semantic_search
  - corpus_session
  - corpus_timeline
  - fetch
  - usages
model: claude-sonnet-4-5
---

You are operating in chthonic-archive gate-walk mode.
Active gate ladder: `bun run session:query --status` → `manifest/corpus-state.json`.
Commit standard: `--no-verify`. Co-author: `Pentea <223556219+Penteaa@users.noreply.github.com>`.
Never delete; upcycle per WET_PAPER_TO_GOLD_METHODOLOGY.md.
```

**File:** `.vscode/gate-walk.chatprompt.md` (pending — add to Next Build Actions Priority 6).

### `#copilotCodingAgent` as Pentea Background Session Vector (v1.102)

`#copilotCodingAgent` tool (v1.102) enables background coding agent sessions with session log view. This is architecturally adjacent to the `agentStop` hook queue in `scripts/pentea_autoloop.ts`:

| Mechanism | Surface | Status | Corpus relevance |
|-----------|---------|--------|-----------------|
| `agentStop` hook (SDK) | `meta-ide/copilot-sdk/sdk/index.d.ts` | Implemented (`scripts/pentea_autoloop.ts`) | Agent sessions → transcript → corpus ingest |
| `#copilotCodingAgent` (v1.102) | VS Code Chat panel + PR/issue view | Available in v1.102 | Background sessions = new transcript stream → new corpus drain path |

Both produce session transcripts. `vampire-copilot-chat` captures both streams (`GitHub.copilot-chat/transcripts/`). No corpus schema change required — `copilotVersion` column on `sessions` already captures agent context. `workspaceHash` on `sessions` may differ for coding agent sessions — verify before assuming they land in the standard drain path.

### Prompt Files as Gate Encoders (v1.100)

Each gate in the G7-REDUX walk can be encoded as a `.prompt.md` file, making the gate runnable via `/` slash command without full context re-establishment:

| Gate | Prompt file | Key tools in frontmatter |
|------|-------------|--------------------------|
| G3 ASCII framebuffer | `.vscode/prompts/g3-ascii-framebuffer.prompt.md` | `codebase`, `editFiles`, `runCommands` |
| G7 embed pass | `.vscode/prompts/g7-embed-pass.prompt.md` | `runCommands` (`bun run session:corpus -- --embed`) |
| G8a LLM summaries | `.vscode/prompts/g8a-intent-classify.prompt.md` | `runCommands`, `fetch` |
| G9 federation | `.vscode/prompts/g9-federation-attach.prompt.md` | `codebase`, `editFiles` |

G3 is the highest-priority prompt file — it is the next open gate in the vulkan-lab gate walk and unblocks G4–G6.

### Open Source Inspection Targets (v1.102)

`microsoft/vscode-copilot-chat` (MIT). Files of direct corpus/satellite interest:

| File | Signal |
|------|--------|
| `src/extension/chat/mcpToolCallingLoop.tsx` | Tool dispatch loop — how tools are called, retried, results merged — align `corpus-mcp.ts` tool response shapes |
| `src/extension/chat/agentPrompt.tsx` | Agent prompt construction — system prompt shape, tool injection order |
| `src/extension/chat/chatParticipants.tsx` | Chat participant registration — how agent mode participants are registered |

**Action:** Read `mcpToolCallingLoop.tsx` before next `corpus-mcp.ts` schema revision to ensure response shapes match VS Code's expected MCP tool output contract.

---

## Bun 1.3.13 Runtime Updates

**Confirmed runtime:** `bun 1.3.13` (`package.json` `engines.bun >=1.3.13`).

### Test runner — new flags (2026-04-20)

| Flag | Semantics | Corpus use-case |
|------|-----------|----------------|
| `bun test --parallel[=N]` | Run spec files concurrently | `npm run test:parallel` — faster CI on session-corpus test suite |
| `bun test --isolate` | Each file in its own worker | Prevents DB handle leaks in sqlite-vec tests |
| `bun test --shard=M/N` | Distribute across N runners | Future multi-runner gate checks |
| `bun test --changed` | Only files changed since last git commit | `npm run test:changed` — zero-cost re-run guard |

Scripts wired in `package.json`: `test:changed`, `test:parallel`.

### Performance wins relevant to corpus pipeline

| Feature | Improvement | Impact |
|---------|-------------|--------|
| `bun install` tarball streaming | 17× less peak memory | HF model wheel install during G7 embed pass |
| zlib-ng 2.3.3 | 5.5× faster gzip | Session transcript JSONL compression; `bun:gzip` in corpus ingest |
| mimalloc v3 + libpas | ~5% less runtime memory | Sustained corpus build (13 sessions × embedding batch) |
| SHA3 + X25519 WebCrypto | Standard in `crypto` module | Available for future session auth/signing layer |

### WebView status (for HF gating pipeline)
`Bun.WebView` shipped in **v1.3.12** — Bun 1.3.13 contains no new WebView features. `scripts/hf_gate_playwright.ts` (Tier 3 browser automation) remains current.

---

## Hardware-Optimized Embedding Strategy — RTX 4090 / TensorRT Trainstop

> **Strategic vantage** — the stable GOLD model target for this hardware platform. Documented once, referenced from `embed_model_registry.json#hardware_optimized`.

### GOLD Model: `NVIDIA/NV-Embed-v2`

| Property | Value |
|----------|-------|
| Architecture | Llama-3 7566M decoder, latent attention pooling, bidirectional |
| Native dims | 4096d (schema v6) |
| Schema v4 path | **TEI truncation → 1024d** — DDL_VEC `FLOAT[1024]` preserved, zero schema migration |
| MTEB score | **69.32** — highest in registry |
| VRAM (FP16) | ~15GB — fits RTX 4090 24GB comfortably at `bs=8` |
| VRAM (TRT INT8) | ~8GB — with TEI TensorRT quantization backend |
| Hardware advantage | Flash Attn 2 path · cuBLAS GEMM · TRT INT8 · designed for NVIDIA silicon |
| Context | 32 768 tokens — captures multi-session composite texts |
| License | NVIDIA NV-Community (non-commercial; commercial requires NVIDIA agreement) |
| Gated | `false` (HF API confirmed 2026-05-04) — no agree-terms call needed |
| Registry pointer | `scripts/embed_model_registry.json` → `hardware_optimized` field |

### Activation Sequence (schema v4 path — zero rebuild cost)

```powershell
# 1. Load HF token
. .\scripts\api_pool.ps1 -Quiet

# 2. Switch active model (updates embed_model_registry.json + embed.py)
bun run embed:switch NVIDIA/NV-Embed-v2

# 3. Remove TRANSFORMERS_OFFLINE=1 from scripts/embed.py (first-time download)
#    (only needed before initial model cache population)

# 4. Run embed doctor pre-flight (validates model cache + schema compat)
uv run scripts/embed_doctor.py --current-schema-version 4

# 5. Embed all sessions
bun run scripts/session-corpus.ts --embed

# 6. Verify G7 admitted
bun run session:query --status
# → gate_ladder.G7 = true, vec_count > 0, vec_model = NVIDIA/NV-Embed-v2
```

**dim_truncation note:** When using NV-Embed-v2 with schema v4 (1024d), embed.py must slice the 4096d output to 1024d before writing to vec_embeddings. embed_doctor.py validates this. If `doctorResult.dims` reports 4096 against a schema v4 target, add explicit truncation:

```python
# scripts/embed.py — add after model.encode():
if len(vec) > ACTIVE_VEC_DIMS:
    vec = vec[:ACTIVE_VEC_DIMS]
    # L2-renormalize after truncation
    norm = sum(x*x for x in vec) ** 0.5
    vec = [x / norm for x in vec] if norm > 0 else vec
```

### Why Not Qwen3-Embedding-8B?

Qwen3-8B is the `recommended_next` in the registry and the clean Apache-2.0 alternative (same VRAM envelope, Matryoshka-native 1024d, no license review). If NV-Community terms are a blocker (commercial use), switch to `Qwen/Qwen3-Embedding-8B` — same activation sequence, no truncation needed at 1024d (Matryoshka native).

| | NV-Embed-v2 | Qwen3-Embedding-8B |
|--|-------------|---------------------|
| License | NV-Community (non-commercial default) | Apache-2.0 |
| MTEB | 69.32 | SOTA 2025-06 (competitive) |
| Matryoshka | No (truncation only) | Yes (native 1024d) |
| HW optimization | NVIDIA-native | General CUDA |
| Task profile | `high_accuracy` | `max_accuracy` |

---

## corpus.sqlite Corruption Prevention

> Root cause: Bun/VS Code abrupt process exit leaves WAL journal uncommitted → `SQLITE_CORRUPT` errno 11 on next open.

### What is now hardened (as of 2026-05-05)

All protections are implemented in `scripts/session-corpus.ts`:

| Protection | Mechanism | Location in code |
|-----------|-----------|-----------------|
| WAL auto-checkpoint | `PRAGMA wal_autocheckpoint = 1000` — WAL self-truncates every 1000 pages | After `new Database()` |
| Integrity check on open | `PRAGMA integrity_check` run before any operation (skipped in `--rebuild`) | After PRAGMAs |
| Graceful exit handler | `process.on("exit/SIGINT/SIGTERM")` → `PRAGMA wal_checkpoint(TRUNCATE)` + `db.close()` | After `new Database()` |
| Pre-rebuild backup | `PRAGMA wal_checkpoint(FULL)` + `Bun.write(corpusPath + ".bak")` before table drops | Start of `--rebuild` block |

### Recovery procedure (if corruption still occurs)

```powershell
# Emergency: delete corrupt DB + WAL/SHM artifacts, full rebuild
Remove-Item manifest\corpus.sqlite -Force
Remove-Item manifest\corpus.sqlite-wal -Force -ErrorAction SilentlyContinue
Remove-Item manifest\corpus.sqlite-shm -Force -ErrorAction SilentlyContinue
bun run session:corpus:rebuild

# Then re-embed with GOLD model
. .\scripts\api_pool.ps1 -Quiet
bun run scripts/session-corpus.ts --embed

# Check backup is present (auto-created before each rebuild)
Get-Item manifest\corpus.sqlite.bak
```

### WAL mode semantics (reference)

```
PRAGMA journal_mode = WAL       → writers do not block readers; parallel reads safe
PRAGMA synchronous = NORMAL     → WAL header fsynced; no full fsync per commit; crash-safe
PRAGMA wal_autocheckpoint = 1000 → after 1000 WAL pages, background checkpoint runs automatically
PRAGMA wal_checkpoint(TRUNCATE) → at clean exit: truncates WAL to zero, main DB is sole source
```

`synchronous = NORMAL` is crash-safe under WAL mode (main DB file is never written mid-transaction). The only corruption vector is an abrupt kill where the WAL has uncommitted data — the graceful exit handler eliminates this for normal operation.
