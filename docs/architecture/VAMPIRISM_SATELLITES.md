---
- type: strategy
- category: architecture
- created: 2026-05-04
- origin: Claude + concept engineering session
- status: doctrine + first satellite spec of a pair
- agents:
  - Claudine
  - Description: Hardcore fitness + nightly escapades in Vampiric form — for training scope nightly date-base calls
- pair: docs/architecture/SESSION_CORPUS.md
- References: docs/architecture/SESSION_CORPUS.md, scripts/satellite.json, ci/checks/federation-contract-validate.ts, scripts/embed.py, scripts/embed_doctor.py, scripts/embed_model_registry.json

---

# Vampirism: Satellite Class Architecture

> **Doctrine:** Vampirism is an observation discipline, not a script. 
> **Reframe origin:** The §10.2 deprecate-vs-rebase question on the vampire script is obsolete — it was the wrong question. Vampire was the seed. This document is the doctrine.
**Pair:** [`SESSION_CORPUS.md`](SESSION_CORPUS.md) — reads the same data from the other side.


---

## The Reframe: Vampire Is a Satellite Class, Not a Script

The corpus pipeline (G0–G9) is one stream — Copilot Chat → SQLite. But the desktop produces dozens of streams: editor history, workspace storage from every extension, settings sync payloads, telemetry packets queued for upload, language server traffic, terminal histories, browser sessions of Claude.ai, ChatGPT, etc. Each is a host that wants to either delete its trace (logs that rotate) or upstream it (telemetry, sync).

**Vampirism is the discipline of catching them locally before either happens.**

`vampire-the-script` doesn't get deprecated or rebased. It gets promoted to the first satellite of a class — `vampire-copilot-chat` — and a sibling architecture forms around it. The chthonic-archive corpus becomes the federation hub. Each satellite owns its drain; the corpus owns the merge.

This makes "polyrepo via local satellites" literal architecture, not metaphor.

---

## Satellite Class Definition

Each satellite is an independent local process with three contracts:

| Contract | Definition |
|----------|-----------|
| **Source contract** | What host it observes, what surface it reads, how often |
| **Drain format** | Normalized JSONL or SQLite, schema documented, no proprietary serialization |
| **Federation key** | An identifier the corpus can use to merge it: timestamp, sessionId, workspace hash, file path |

That's it.

Implementation constraints: a few hundred lines, single-purpose, separately versioned. No inter-satellite dependencies. The corpus pulls via scheduled merge or live `ATTACH DATABASE`. Failure of one satellite never breaks another — fault isolation by design.

---

## High-Signal First Satellite: VSCode Surface Observer (`vampire-vscode-surface`)

`vampire-copilot-chat` already drains `GitHub.copilot-chat/`. The same machine has unmined seams under `%APPDATA%\Code - Insiders\`:

| Surface | Path | Signal | Why It Matters |
|---------|------|--------|----------------|
| All extension state | `User\workspaceStorage\<hash>\<ext>\` | Per-extension working memory, tokens, caches | Continue, Tabnine, Codeium, Cody all live here — multi-AI archaeology |
| Global extension state | `User\globalStorage\<ext>\` | Cross-workspace state | Settings, auth tokens, model catalogs |
| File history | `User\History\<hash>\` | Every save creates a snapshot | Reconstruct deleted edits, rollback intent without git |
| Settings sync queue | `User\sync\` | What's about to be uploaded to MS | The exact "what is leaving my machine" frame — pure sovereignty value |
| Logs | `logs\<ts>\` | Extension host crashes, telemetry attempts | Forensic record of what extensions tried to do |
| Cached extension VSIXs | `CachedExtensionVSIXs\` | Extension binaries pre-update | Recovery if marketplace pulls something |

**Drain pattern:** FS poller (same shape as `session-watcher.ts`) → mirrors → normalizer parses → SQLite tables `vscode_workspace_state`, `vscode_history`, `vscode_sync_queue`, `vscode_logs`. All federated to corpus by `(workspaceHash, ts)`.

### Schema Sketches

| Table | Key columns | Notes |
|-------|-------------|-------|
| `vscode_workspace_state` | `workspace_hash TEXT`, `ext_id TEXT`, `key TEXT`, `value BLOB`, `ts INTEGER` | One row per extension state key per workspace |
| `vscode_history` | `workspace_hash TEXT`, `file_path TEXT`, `snapshot_ts INTEGER`, `content BLOB` | Every VS Code save snapshot — rollback surface |
| `vscode_sync_queue` | `item_id TEXT`, `surface TEXT`, `payload BLOB`, `captured_ts INTEGER`, `upload_ts INTEGER NULL` | `upload_ts NULL` = captured before upload; sovereignty window |
| `vscode_logs` | `session_ts INTEGER`, `ext_id TEXT`, `level TEXT`, `message TEXT`, `ts INTEGER` | Extension host events, crash traces, telemetry attempts |

Federation join: `SELECT * FROM vscode_history WHERE workspace_hash = corpus.workspace_hash AND snapshot_ts BETWEEN :t0 AND :t1`.

---

## Open-Source Resistance Pattern

Four invariants do most of the work against re-enclosure:

| Invariant | Mechanism | Anti-pattern it blocks |
|-----------|-----------|----------------------|
| **License: Apache 2.0 + federation clause** | Patent grant blocks corporate weaponization; federation clause requires any fork to keep the satellite contract open | Silent Microsoft absorption (MIT is too permissive for this) |
| **Zero call-home, by inspection** | Any binary shipped has zero outbound network unless explicitly invoked by the user — verifiable: ship strace/Wireshark transcript with each release as proof | Extension telemetry, undeclared upstreaming |
| **Federation protocol as document, not framework** | Satellite contract is a 200-line markdown spec, not a 50KB SDK — anyone in any language implements it | SDK leverage point → capture moat |
| **Distribution multi-rooted** | GitHub (necessary evil) + Codeberg mirror + own static site + IPFS + signed binaries via Sigstore — if GitHub deplatforms, binary still verifies and propagates | Single-point deplatform kill |

These four together make re-enclosure economically pointless: there is nothing to capture and the moat does not form.

### Enforceable Checklist (CI Gate)

| Check | Gate condition | CI command (sketch) |
|-------|---------------|---------------------|
| No outbound DNS | Binary has zero outbound network calls unless user-invoked | `strace -e trace=network ./satellite 2>&1 \| grep -E 'connect\|sendto' \| grep -v 127.0.0.1` |
| License header | Every source file carries Apache 2.0 + federation clause header | `grep -rL 'Apache-2.0' src/ \| grep -v test` → must be empty |
| Federation contract test | Satellite registration JSON validates against federation schema | `bun run ci/checks/federation-contract-validate.ts --satellite <id>` |

---

## Federation Protocol (Skeleton)

A satellite declares itself to the corpus via a registration document:

```jsonc
{
  "satellite_id": "vampire-vscode-surface",
  "version": "0.1.0",
  "source_contract": {
    "host": "VSCode Insiders",
    "surfaces": ["workspaceStorage", "globalStorage", "History", "sync", "logs"],
    "poll_interval_ms": 30000
  },
  "drain_format": {
    "type": "sqlite",
    "schema_doc": "docs/architecture/VAMPIRISM_SATELLITES.md#drain-schema",
    "tables": ["vscode_workspace_state", "vscode_history", "vscode_sync_queue", "vscode_logs"]
  },
  "federation_keys": ["workspaceHash", "ts"],
  "outbound_network": false
}
```

The corpus accepts `ATTACH DATABASE '<satellite.db>' AS <satellite_id>` for live merge, or scheduled import for batch mode. No satellite-to-satellite calls. No shared runtime. No central broker.

---

## Satellite Inventory

| Satellite ID | Status | Source Host | Drain Target |
|---|---|---|---|
| `vampire-copilot-chat` | Promoted (was: `vampire`) | `GitHub.copilot-chat/` transcripts | corpus SQLite |
| `vampire-vscode-surface` | Spec (this document) | `%APPDATA%\Code - Insiders\` | corpus SQLite |
| `vampire-browser-sessions` | Candidate | Browser local storage / IndexedDB | corpus SQLite |
| `vampire-terminal-history` | Candidate | `manifest/terminal_session.jsonl` + PSReadLine history | corpus SQLite |

---

## Gate Status (Drain View)

Drain-relevant slice of the full G0–G9 ladder. Columns — **Type:** `infra` · `schema` · `pipeline` · `view` · `satellite` · `enrich` · `federation`. **Sub:** variant suffix (a/b/c or .0 for pre-gate). **Level:** L4=admitted · L0=pending/impossible. Full ingest-side ladder with all columns: [`SESSION_CORPUS.md → Gate Ladder`](SESSION_CORPUS.md#gate-ladder-g0g9).

| Gate | Type | Sub | State | Level | What it enables on the drain side |
|------|------|-----|-------|-------|-----------------------------------|
| G6 | view | — | ✅ done | L4 | `session_ranked` view — blood score computable without re-parse |
| G8b | enrich | b | ✅ done | L4 | Entity tables — `--extract` entity mode available |
| G7.0 | satellite | .0 | ✅ done | L4 | `vampire-copilot-chat.ts` — corpus-native, `_corpus_ref` identity locked |
| G7 | satellite | — | ✅ done | L4 | sqlite-vec 0.1.9 + Qwen3-Embedding-0.6B 1024d Matryoshka (schema v4, upgraded 2026-05-04 from all-MiniLM-L6-v2 384d) — semantic drain (query by meaning) |
| G8a | enrich | a | ⬜ pending | L0 | LLM summaries → `drain.json.sessionIntent` auto-populated |
| G9 | federation | — | ⬜ pending | L0 | ATTACH DATABASE — sidecar satellite DBs federated into corpus |

**Fast state check:** `bun run session:query --status` → `manifest/corpus-state.json#gate_ladder`

---

## Satellite Specs

### `vampire-copilot-chat` (Promoted from `session-vampire.ts`)

**Source contract**
- Host: GitHub Copilot Chat (`%APPDATA%\Code - Insiders\User\workspaceStorage\<hash>\GitHub.copilot-chat\`)
- Surfaces: `transcripts/<sid>.jsonl`, `debug-logs/<sid>`, `memories/*.md`
- Poll interval: file-watcher (inotify/ReadDirectoryChanges) on transcripts dir + 60s fallback poll
- Mirror target: `manifest/sessions/<sid>/` (already wired via `session-watcher.ts`)

**Drain format**
- SQLite: `manifest/corpus.sqlite` (federation hub — satellite writes here directly, not to a sidecar)
- Tables: `sessions`, `turns`, `file_edits`, `terminal_cmds`, `code_blocks`, `entities`, `entity_occurrences`, `memory_snapshots`, `vec_embeddings` (1024d, sqlite-vec, G7, Qwen3-Embedding-0.6B)
- Schema owner: `scripts/session-corpus.ts` DDL constants
- Embed pipeline: `scripts/embed_model_registry.json` (active model) → `scripts/embed_doctor.py` (pre-flight) → `scripts/embed.py` (Python stdin/stdout bridge) → `vec_embeddings` virtual table

**Federation key**
- `sessionId` (UUID from transcript filename) + `ts` (turn timestamp ISO8601)

**Rebase decision (Option B — locked 2026-05-04)**  
`session-vampire.ts` internals rebase onto `corpus.sqlite` queries. The filesystem artifact contract (`drain.json`, `session_blood.json`) is preserved — outputs are generated from SQLite queries against the already-ingested corpus, not from re-parsing transcripts. Zero external consumers confirmed before decision.

**Status:** ✅ Implemented — commit `82c60dd7`. `scripts/session-vampire.ts` renamed to `scripts/vampire-copilot-chat.ts`. `_corpus_ref` frontmatter in every drain artifact. Semantic drain (G7) available via `bun run vampire:drain --embed` after corpus embed pass.

---

### `vampire-vscode-surface` (First new satellite)

**Source contract**
- Host: VS Code Insiders (`%APPDATA%\Code - Insiders\User\`)
- Surfaces:

| Surface | Glob | Poll | Priority |
|---------|------|------|----------|
| `workspaceStorage\<hash>\<ext>\` | `**/*.json`, `**/*.db` | 30s | HIGH — multi-AI memory archaeology |
| `globalStorage\<ext>\` | `**/*.json`, `**/*.db` | 60s | HIGH — auth tokens, model catalogs |
| `History\<hash>\` | `**` (binary safe) | on-write | HIGH — deleted edit recovery |
| `sync\` | `**` | on-write | CRITICAL — sovereignty window (pre-upload) |
| `logs\<ts>\` | `*.log` | on-rotate | MEDIUM — telemetry forensics |
| `CachedExtensionVSIXs\` | `*.vsix` | on-change | LOW — recovery only |

- Poller shape: identical to `session-watcher.ts` — `ReadDirectoryChangesW` (Win32) with 30s fallback scan. Mirror to `manifest/vscode-surface/<surface-type>/<hash>/`.

**Drain format**
- Sidecar SQLite: `manifest/vscode-surface.db` (separate from corpus — federated in, not written to corpus directly)
- DDL:

```sql
CREATE TABLE vscode_workspace_state (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  workspace_hash TEXT NOT NULL,
  ext_id       TEXT NOT NULL,
  key          TEXT NOT NULL,
  value        BLOB,
  captured_ts  INTEGER NOT NULL,
  UNIQUE(workspace_hash, ext_id, key)  -- upsert by recency
);

CREATE TABLE vscode_history (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  workspace_hash TEXT NOT NULL,
  file_path    TEXT NOT NULL,
  snapshot_ts  INTEGER NOT NULL,
  content_hash TEXT NOT NULL,
  content      BLOB,
  UNIQUE(workspace_hash, file_path, snapshot_ts)
);

CREATE TABLE vscode_sync_queue (
  item_id      TEXT PRIMARY KEY,   -- from sync payload header
  surface      TEXT NOT NULL,
  payload      BLOB NOT NULL,
  captured_ts  INTEGER NOT NULL,
  upload_ts    INTEGER             -- NULL = captured before upload; sovereignty window
);

CREATE TABLE vscode_logs (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  session_ts   INTEGER NOT NULL,
  ext_id       TEXT,
  level        TEXT NOT NULL,      -- 'info'|'warn'|'error'|'trace'
  message      TEXT NOT NULL,
  raw_line     TEXT,
  ts           INTEGER NOT NULL
);

-- Index for corpus federation join
CREATE INDEX vscode_history_whash_ts ON vscode_history(workspace_hash, snapshot_ts);
CREATE INDEX vscode_workspace_state_whash ON vscode_workspace_state(workspace_hash, captured_ts);
```

**Federation key**
- `(workspace_hash, captured_ts)` — corpus joins via `ATTACH DATABASE 'manifest/vscode-surface.db' AS vscode`

**Implementation file:** `scripts/vampire-vscode-surface.ts` (not yet written — G7.0+)

---

### Candidate Satellites (Future)

**`vampire-browser-sessions`**
- Source: Chrome/Edge `%LOCALAPPDATA%\Google\Chrome\User Data\Default\Local Storage\leveldb\` + IndexedDB
- Target surfaces: Claude.ai localStorage (conversation history before eviction), ChatGPT (same), GitHub (PR state)
- Blocker: LevelDB requires a native parser (`leveldown` or Rust `rusty-leveldb`) — not trivial on Win32

**`vampire-terminal-history`**
- Source: PSReadLine `%APPDATA%\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt` + `manifest/terminal_session.jsonl`
- Note: `terminal_session.jsonl` is already wired via `chthonic-shell-hook.ps1` — this satellite would federate it into `corpus.sqlite` cross-session
- Low-effort: PSReadLine history is plaintext, one command per line

---

## Federation Protocol v1

### Registration

Each satellite ships a `satellite.json` at its repo root:

```jsonc
{
  "satellite_id": "vampire-vscode-surface",  // kebab-case, globally unique
  "version": "0.1.0",
  "source_contract": {
    "host": "VSCode Insiders",
    "platform": "win32",                     // win32 | linux | darwin | cross
    "surfaces": ["workspaceStorage", "globalStorage", "History", "sync", "logs"],
    "poll_interval_ms": 30000,
    "trigger": "fs-watch+poll-fallback"       // fs-watch | poll | on-event
  },
  "drain_format": {
    "type": "sqlite",
    "path": "manifest/vscode-surface.db",    // relative to repo root
    "schema_version": 1,
    "tables": ["vscode_workspace_state", "vscode_history", "vscode_sync_queue", "vscode_logs"]
  },
  "federation_keys": ["workspace_hash", "captured_ts"],
  "outbound_network": false,                 // HARD CONSTRAINT — CI gate fails if true
  "license": "Apache-2.0",                   // CI gate: must match license header in src/
  "corpus_schema_min": 4                     // minimum corpus user_version (schema v4 = G7/Qwen3 baseline)
}
```

### Corpus Merge Modes

**Live (ATTACH DATABASE):**
```sql
ATTACH DATABASE 'manifest/vscode-surface.db' AS vscode;

-- Join example: file history co-occurring with corpus edits in session window
SELECT c.sessionId, v.file_path, v.snapshot_ts, v.content_hash
FROM sessions c
JOIN vscode.vscode_history v
  ON v.workspace_hash = c.workspaceHash
 AND v.snapshot_ts BETWEEN c.startTs AND c.endTs
ORDER BY v.snapshot_ts;
```

**Batch import (scheduled merge):**
```typescript
// corpus pulls satellite on a schedule
const sat = new Database("manifest/vscode-surface.db", { readonly: true });
const rows = sat.prepare("SELECT * FROM vscode_history WHERE captured_ts > ?").all(lastMergeTs);
// upsert into corpus federation tables
```

**Conflict resolution:** last-write-wins on `(federation_key)` — satellites are append-only, corpus is the authority for dedup.

### Federation Contract Test (CI)

```typescript
// ci/checks/federation-contract-validate.ts
// Validates satellite.json: satellite_id kebab-case, outbound_network:false,
// license:Apache-2.0, drain tables non-empty, corpus_schema_min ≤ actual user_version
bun run ci/checks/federation-contract-validate.ts --satellite vampire-vscode-surface
bun run ci/checks/federation-contract-validate.ts --register path/to/satellite.json   // validate + enroll
bun run ci/checks/federation-contract-validate.ts --report                             // JSON report
```

Exits 1 if: `outbound_network: true`, license mismatch, `satellite_id` not kebab-case,
`corpus_schema_min > corpus user_version` (run corpus gates first to advance schema).

---

## Satellite Implementation Guide

### Starting a new satellite (3 files minimum)

```
vampire-<host>/
  satellite.json         # registration contract (required)
  src/watcher.ts         # FS poller — mirrors source to manifest/
  src/normalizer.ts      # parses mirrored files → SQLite drain tables
  src/main.ts            # entry: starts watcher + normalizer
  ci/checks/             # federation-contract-validate.ts (copy from corpus)
```

### Watcher shape (mirrors session-watcher.ts)

```typescript
#!/usr/bin/env bun
// @SID: SATELLITE_WATCHER_<HOST>_V1
import { watch } from "fs";
import { join, resolve } from "path";

const SOURCE = resolve(process.env.APPDATA!, "Code - Insiders/User");
const MIRROR = resolve("manifest/vscode-surface");

// Mirror on change — no parsing here, no outbound network
watch(SOURCE, { recursive: true }, async (event, filename) => {
  if (!filename) return;
  const src = join(SOURCE, filename);
  const dst = join(MIRROR, filename);
  await Bun.write(dst, Bun.file(src));
});
```

### Normalizer contract

- Opens mirror path (read-only)
- Parses each surface type into its drain table schema
- Upserts to sidecar SQLite — never overwrites, never deletes
- Emits `manifest/<satellite-id>-status.json` on each pass (gate-smoke readable)

### What a satellite must NEVER do

| Prohibited | Reason |
|-----------|--------|
| Outbound network call (any) | Sovereignty violation — CI gate fails |
| Read source path with write access | Defense against accidental mutation of host state |
| Import from corpus or other satellites | No inter-satellite deps — fault isolation |
| Use proprietary serialization | Protocol lock-in; drain format must be inspectable |
| Auto-update | User must control when satellite code changes |

---

## Architecture Position

| Layer | Component | Role |
|-------|-----------|------|
| Federation hub | `chthonic-archive` corpus (G0–G9) | Merge, query, long-term storage — not a satellite |
| Satellite class | `vampire-*` repos | Independent drain processes, one per source host |
| Observation discipline | Vampirism doctrine (this document) | The invariants that govern what a satellite is and isn't |

G6–G9 corpus work continues unblocked — it is the federation hub, not a satellite. The satellite class does not require the corpus to change.

This document is a **parallel ladder** to the **FAF** plan, not part of *G6–G9*. It *runs alongside without modifying the corpus gate sequence*.

---

## Next Build Actions

### Completed

| Action | Commit |
|--------|--------|
| `vampire-copilot-chat` rebase (G7.0) — renamed from `session-vampire.ts`, corpus-native, `_corpus_ref` locked | `82c60dd7` |
| `ci/checks/federation-contract-validate.ts` — satellite contract CI gate | present |

### Pending

| Priority | Action | Prerequisite |
|----------|--------|--------------|
| 1 | `vampire-vscode-surface` watcher + normalizer scaffolding | after G7.0 |
| 2 | Corpus ATTACH DATABASE merge query set | after vampire-vscode-surface drain DB exists |
| 3 | `vampire-terminal-history` (PSReadLine ingest) | low-effort, any time |

The CI gate (`federation-contract-validate.ts`) is the only item that can ship before G7.0 — it validates the doctrine before any new satellite exists, which is the correct enforcement order.
