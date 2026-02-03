---
type: protocol
category: gemini
created: 2026-02-02
author: claude
status: active
description: Context hygiene rules to prevent API payload overflow in Gemini CLI
---

# Gemini CLI Context Hygiene Protocol

**Version:** 1.0
**Status:** ACTIVE
**Enforcement:** Self-governing (read at session start)

---

## Problem Statement

Gemini CLI's `ReadManyFiles` tool can pull thousands of files in a single request. When the concatenated payload exceeds ~1M tokens, the Google Cloud Code API returns:

```
400 INVALID_ARGUMENT - Request contains an invalid argument
```

Once this happens, the session is **unrecoverable** — even `/compress` fails because it calls the same API.

---

## Hard Rules

### 1. Never Use Broad Globs on These Directories

| Directory | Reason |
|-----------|--------|
| `.codex/` | Contains `auth.json`, `sessions/` (massive `.jsonl` files) |
| `../.codex/` | Global Codex home — same problem |
| `node_modules/` | Thousands of files |
| `target/`, `build/`, `dist/` | Build artifacts |
| `sessions/`, `*.jsonl` | Session logs can be 100MB+ |

### 2. File Count Limits

| Context | Max Files |
|---------|-----------|
| Single ReadManyFiles call | **6 files** |
| Total files in prompt context | **20 files** |
| Skill files (explicit paths) | **4-6 files** |

### 3. Explicit Paths Only for Skills

When reading skill files, use explicit paths:

**GOOD:**
```
~/.codex/skills/artifact-upcycle/SKILL.md
~/.codex/skills/artifact-upcycle/references/POLICY.md
~/.codex/skills/artifact-upcycle/scripts/artifact_upcycle.py
```

**BAD:**
```
~/.codex/**/*
```

### 4. Recovery from Overflow

If you see `400 INVALID_ARGUMENT`:
1. **Do NOT retry** — the session is poisoned
2. **Do NOT `/compress`** — it will fail too
3. **Start a fresh session** — only way to recover
4. **Report to triad** — log what caused the overflow

---

## Settings Reference

These settings are already configured in `.gemini/settings.json`:

```json
{
  "context": {
    "discoveryMaxDirs": 50,
    "respectGeminiIgnore": true
  }
}
```

But these only limit **automatic discovery**, not explicit `ReadManyFiles` calls.

---

## Triad Coordination

When Gemini needs access to shared artifacts:

1. **Ask Claude or Codex** to summarize large files
2. **Use file handoffs** — write summaries to `codex/handoffs/`
3. **Keep context lean** — the triad's strength is specialization, not bulk ingestion

---

## Checklist for Safe Sessions

Before using `ReadManyFiles`:
- [ ] Explicit file paths (not globs)
- [ ] Max 6 files per call
- [ ] No `.codex/`, `sessions/`, `node_modules/`
- [ ] No `.jsonl` or large log files

---

**Protocol Hash:** `GEMINI_CONTEXT_HYGIENE_V1`
**Author:** Claude Code (Opus 4.5)
**For:** Gemini CLI (3.0 Pro)
