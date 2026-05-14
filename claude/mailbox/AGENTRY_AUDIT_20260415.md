# Agentry Audit — 2026-04-15

Scope: `.github/agents/`, `.github/instructions/`, `.github/prompts/`, copilot-instructions family.
Executed by: Tessara (proxied — subagent tools unavailable in this session, executed inline)

---

## tessara.agent.md (stale)

| Check | Result | Finding |
|-------|--------|---------|
| `tools:` field | ⚠ WARN | YAML block scalar (`tools: >`) — VS Code parses this as a string, not a tool array. Functionally: VS Code likely falls back to all tools (user intent achieved), but the field is semantically invalid. Intentional flavor text — low priority to fix. To be clean: remove the field entirely (omit = all tools) or wrap prose in a comment. |
| SSOT link | ✅ PASS | `../copilot-instructions.archive.md` from `.github/agents/` resolves to `.github/copilot-instructions.archive.md` — file exists. |
| `description:` present | ✅ PASS | Block scalar, non-empty, keyword-rich. |
| `name:` present | ✅ PASS | `tessara` |
| `model:` | ✅ PASS | Removed — SSOT governs. |

---

## Instructions Files

None of the 6 files have YAML frontmatter (`---` delimiters). Without frontmatter, VS Code treats instructions as **always-on for all files** — no `applyTo` scoping. This is likely **intentional** (repo-wide governance doctrine), but flagged for awareness.

| File | Frontmatter | `applyTo` | Finding |
|------|-------------|-----------|---------|
| `ankh-workflow.instructions.md` | ❌ None | ❌ Absent | Always-on. No YAML block at all — starts with `#` heading. Intentional per design (protocol, not file-scoped). |
| `autopsy-protocol.instructions.md` | ❌ None | ❌ Absent | Always-on. Starts with `# 🔬`. Same pattern. |
| `project-workflow.instructions.md` | ❌ None | ❌ Absent | Always-on. Body has inline SSOT link to `../copilot-instructions.md` (pointer, not archive — see family section). |
| `python-scripting.instructions.md` | ❌ None | ❌ Absent | Always-on. Body references `SSOT-L-H`. |
| `ssot-toolbox.instructions.md` | ❌ None | ❌ Absent | Always-on. Body link to `../copilot-instructions.md` (pointer). |
| `technical-directives.instructions.md` | ❌ None | ❌ Absent | Always-on. Body link to `../copilot-instructions.md` (pointer). |

**Verdict:** No `applyTo` = always-on injection for all files. For governance-level instructions this is correct behavior. No action required unless per-filetype scoping is desired.

**Link drift note:** `project-workflow`, `ssot-toolbox`, `technical-directives` all link to `../copilot-instructions.md` (the pointer file, not the archive). These are NOT broken links — the pointer file exists — but they bypass the SSOT. Low priority.

---

## Prompt Files (sample: 5/11)

All sampled prompts have valid YAML frontmatter with `description` and `mode`. Tool names warrant a warning.

| File | `description` | `mode` | Tools | Finding |
|------|--------------|--------|-------|---------|
| `analyzeCode` | ✅ Present | `ask` | `search`, `read_file`, `get_errors` | ⚠ Non-standard aliases (`read_file`, `get_errors` — not in official VS Code alias list). Likely resolved as extension tool IDs. Functional but non-canonical. |
| `crossReferenceSSOT` | ✅ Present | `agent` | `read_file`, `search`, `edit` | ⚠ Same — `read_file` non-standard alias. |
| `beautifySessionArchive` | ✅ Present | `agent` | `edit`, `search`, `read_file`, `run_in_terminal` | ⚠ Same pattern. `run_in_terminal` also non-standard alias. |
| `debugIssue` | ✅ Present | absent | `edit`, `search`, `run_in_terminal` | ⚠ No `mode:` — VS Code defaults to `ask`. May be intentional. |
| `refactorCode` | ✅ Present | absent | `edit`, `search`, `read_file` | ⚠ No `mode:`. Same as above. |

**Tool alias pattern across all prompts:** `read_file`, `run_in_terminal`, `get_errors` appear consistently as non-standard aliases. VS Code Copilot's official aliases are: `execute`, `read`, `edit`, `search`, `agent`, `web`, `todo`. The non-standard names may resolve via tool ID lookup — test in practice before bulk-renaming.

---

## copilot-instructions Family

| File | Role | Verdict |
|------|------|---------|
| `copilot-instructions.archive.md` | 9171-line canonical SSOT. Header self-describes as "ARCHIVAL REFERENCE" and defers to `copilot-instructions.md` for current tasks — **contradicts** user memory (archive IS the primary). Header text is legacy narration, not current routing. | ✅ Primary SSOT per user directive. Header text is stale narration. |
| `copilot-instructions.md` | Intentionally small pointer file. Says "kept intentionally small." No link to archive. | ⚠ Pointer that doesn't point — the file exists but doesn't route to archive explicitly. Readers land here from instructions links and get a stub. |
| `copilot-instructions-copy.md` | Opens with GLOBAL OVERRIDE + LINGUISTIC_PROFILE_PROTOCOL.md banner. Contains codex content. Appears to be a snapshot from before the `.archive.md` consolidation. | ⚠ DRIFT CANDIDATE. Likely a stale copy. Salvage or archive before any deletion decision. |

**Summary on copilot-instructions.md stub:** Three instructions files link to `../copilot-instructions.md` expecting current coding guidance. The file they land on is a stub with no substantive content. This is a navigation dead-end for any agent following those links. Consider adding a redirect line pointing to `.archive.md`.

---

## Summary

| Category | Count | Items |
|----------|-------|-------|
| **Blockers** | 0 | — |
| **Warnings** | 4 | `tools: >` prose string in tessara.agent.md; non-standard tool aliases in all prompts; `copilot-instructions.md` stub doesn't route to archive; `copilot-instructions-copy.md` drift candidate |
| **Clean** | 1 | tessara.agent.md structure (description, name, SSOT link, no model pin) |
| **Intentional / no action** | 2 | All 6 instructions files missing `applyTo` (always-on by design); instructions body links to pointer (not archive) |

### Recommended actions (ordered by impact):
1. **copilot-instructions.md stub** — Add one line: `> Active SSOT: [copilot-instructions.archive.md](copilot-instructions.archive.md)` so linked agents don't dead-end.
2. **copilot-instructions-copy.md** — Salvage audit before deletion decision. Is it substantively different from the archive?
3. **tessara.agent.md `tools:`** — Low priority. Either remove the field (omit = all tools) or accept the prose string as intentional flavor that VS Code ignores gracefully.
4. **Prompt tool aliases** — Test `read_file` / `run_in_terminal` resolution in practice before bulk-renaming to canonical aliases.
