---
name: dumpster-upcycler
description: Convert raw session dumps into compact structured logs, readable markdown, and warm-start resume packets (no deletion, optional archiving). Absorbs session-resumer.
metadata:
  short-description: "Upcycle raw dumps into structured logs + resume packets"
  argument-hint: "uv run .codex/skills/dumpster-upcycler/scripts/dumpster_upcycler.py codex/codex-session-logs/codex-session-log-00001"
  tags:
    - log processing
    - session management
    - data transformation
---

# Dumpster Upcycler

This skill takes large, raw `.txt`/transcript dumps and produces:
- a compact structured `.txt` (commands/actions only)
- a structured `.json` (warm-start / machine-loadable session state)
- a readable `.md` ("pretty" event stream)

It does not delete history. It can optionally move the raw dump into an archive folder.

## Commands

Single file:
```powershell
uv run .codex/skills/dumpster-upcycler/scripts/dumpster_upcycler.py codex/codex-session-logs/codex-session-log-00001
```

Directory sweep (all matching files):
```powershell
uv run .codex/skills/dumpster-upcycler/scripts/dumpster_upcycler.py codex/codex-session-logs --glob "codex-session-log-*"
```

Move originals into an archive folder (no overwrite):
```powershell
uv run .codex/skills/dumpster-upcycler/scripts/dumpster_upcycler.py codex/codex-session-logs --glob "codex-session-log-*" --archive
```

## Resume Packets (absorbed from session-resumer)

Generate a warm-start resume from a raw or structured log:
```powershell
uv run .codex/skills/session-resumer/scripts/session_resumer.py codex/codex-session-logs/codex-session-log-00001.txt
```

From Google AI Studio export:
```powershell
uv run .codex/skills/session-resumer/scripts/session_resumer.py codex/codex-session-logs/default-session-code-gemini.py --extract-ai-studio
```

From JSON transcript with canonical emit:
```powershell
uv run .codex/skills/session-resumer/scripts/session_resumer.py <transcript>.json --emit-canonical
```

Append resume into a session trail:
```powershell
uv run .codex/skills/session-resumer/scripts/session_resumer.py codex/codex-session-logs/codex-session-log-00001.txt --trail codex/codex-session-logs/SESSION_TRAIL_00001.md
```

## Output Convention
For an input `foo.txt` or `foo` (no extension), outputs are written next to it:
- `foo_structured.txt`
- `foo_structured.json`
- `foo_pretty.md`
