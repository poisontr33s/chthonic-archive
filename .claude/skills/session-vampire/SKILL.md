---
name: session-vampire
description: >
  Drain ALL structured artifacts from mirrored Copilot Chat sessions.
  The vampire reads transcript.jsonl + memories/*.md (mirrored by session-watcher),
  extracts file edits / terminal commands / code blocks / commit refs / memory files,
  and writes per-session drain.json + cross-session session_blood.json.
triggers:
  - "drain sessions"
  - "session vampire"
  - "session blood"
  - "what did copilot write"
  - "extract session artifacts"
  - "memory files"
  - "hottest files across sessions"
  - "what files did we edit"
  - "what commands did we run"
---

# session-vampire

## Artifact Taxonomy (native Copilot Chat storage, per session)

| Zone | Mirrored? | Path | Content |
|------|-----------|------|---------|
| Transcripts | ✅ watcher | `manifest/sessions/<id>/transcript.jsonl` | All events: user/assistant turns, tool calls |
| Debug telemetry | ✅ watcher | `manifest/sessions/<id>/debug.jsonl` | session_start spans, copilot+vscode versions |
| Model catalog | ✅ watcher | `manifest/sessions/<id>/models.json` | Available models at session time |
| Memory files | ✅ watcher | `manifest/sessions/<id>/memories/*.md` | In-session agent memory writes (highest signal) |
| Call resources | ❌ too large | `AppData/.../chat-session-resources/<id>/<call-id>/content.txt\|json` | Raw tool response payloads (up to 741KB each, 31+ dirs) |
| Codebase index | ❌ session-agnostic | `AppData/.../codebase-external.sqlite` | Workspace embedding index |

**base64 session ID key** (memory-tool dir names): `Buffer.from(sessionId).toString("base64")`.

**Three workspace hashes** with chthonic-archive data:
- `710554437afe84ae817dd8a105e496f6` — primary (10 sessions, 28+ memory mds)
- `eccd2abdbb1acd0697631505bd88f668` — current active workspace
- `ef54bace47120bf8bda2a555aef41825` — typo path `erdno` (1 session, 40 memory mds)

`session-watcher` discovers all hashes via `allTranscripts()` — no manual config needed.

---

## Commands

```powershell
# Mirror: pull transcripts + debug-logs + memory files from AppData → manifest/sessions/
bun run session:watch --once                      # one-shot pass, all workspace hashes
bun run session:watch --once --push               # mirror + auto-commit + push

# Drain: extract structured artifacts from mirrored sessions
bun run session:vampire                           # drain all sessions → drain.json per session
bun run session:vampire --session <id>            # drain one session
bun run session:vampire --blood                   # cross-session aggregate report
bun run session:vampire --extract edits           # hottest files across sessions
bun run session:vampire --extract commands        # all terminal commands with goals
bun run session:vampire --extract code            # all code blocks (lang, line count, preview)
bun run session:vampire --extract memories        # all memory files by session with byte sizes

# Continuous watch
bun run session:watch                             # poll every 10s
bun run session:watch --interval 30               # poll every 30s
bun run session:watch --push                      # poll + push debounced 30s after changes
```

---

## Drain Output Shape

### Per-session: `manifest/sessions/<id>/drain.json`
```typescript
{
  sessionId: string;
  drainedAt: string;          // ISO timestamp
  sourcePath: string;         // original AppData transcript path
  sessionIntent: string;      // first user message (session north star)
  turns: number;              // total user+assistant turns
  userMessages: number;
  assistantMessages: number;
  fileEdits: Array<{
    tool: string;             // create_file | replace_string_in_file | multi_replace_string_in_file
    filePath: string;
    turn: number;             // turn index in session
  }>;
  terminalCommands: Array<{
    command: string;
    explanation?: string;
    goal?: string;
    turn: number;
  }>;
  codeBlocks: Array<{
    lang: string;
    lines: number;
    preview: string;          // first 80 chars of content
    turn: number;
  }>;
  toolCallSummary: Record<string, number>; // tool name → call count
  commitRefs: string[];        // git commit SHAs (7-char) found in assistant messages
  memoryFiles: string[];       // filenames under manifest/sessions/<id>/memories/
}
```

### Cross-session index: `manifest/session_blood.json`
Array of `BloodEntry`: sessionId, drainedAt, sessionIntent, turns, fileEditCount, commandCount, codeBlockCount, memoryFileCount, topFiles[5], topTools[5].

---

## Watcher Architecture

- `allTranscripts()` — iterates ALL workspace hashes in AppData dynamically (sorted newest-first)
- `mirrorSession()` — size-change gated; copies transcript.jsonl + calls `mirrorAuxiliaries()`
- `mirrorAuxiliaries()` — copies debug-logs/main.jsonl, debug-logs/models.json, memory-tool/memories/<b64-id>/*.md
- Poll default: 10s. Push debounce: 30s after last change.
- Guard env: `--once` exits after one pass (size-change gating bypassed by fresh start each run — all new files are "changed")

## Vampire Architecture

- `drainSession(id)` — reads transcript.jsonl line by line, collects all artifacts; also checks `memories/` dir for mirrored memory files
- `allSessionIds()` — sessions in `manifest/sessions/` with a `transcript.jsonl`
- `buildBlood(drains)` — reads ALL existing `drain.json` on disk (incremental — old sessions preserved)
- `showBlood()` — formatted cross-session report with memory file count per session

---

## Anti-Patterns

- Do NOT scrape terminal buffers for session content. Write to `manifest/` and read from manifests.
- Do NOT mirror `chat-session-resources/` wholesale — some dirs are 741KB+ and there are 31+ per session.
- Do NOT call `--extract memories` as a substitute for actually reading the memory files — use it as an index, then `read_file manifest/sessions/<id>/memories/<filename>.md` to see content.
- The SQLite `codebase-external.sqlite` is session-agnostic (global workspace index, not per-session state). Drain scope is session-scoped artifacts only.
