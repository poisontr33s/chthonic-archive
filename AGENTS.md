---
type: agent-guidance
category: configuration
created: 2026-01-31
agent: codex
description: OpenAI Codex behavioral configuration and execution discipline
---

# AGENTS.md

- This file provides guidance to OpenAI Codex when working with code in this repository.

  - When tasked to check mailbox or deep-research files, prime for implementation, **not analysis**.

  - When tasked to check TEMPLE files, prime for **structural analysis and enforcement**. When tasked to check GAME files, prime for **specification and mechanics validation**.

- Always follow the "Execution Discipline" section below. 

## Mandatories

- **File governance (WPTG):** [WET_PAPER_TO_GOLD_METHODOLOGY.md](WET_PAPER_TO_GOLD_METHODOLOGY.md) — every file is gold. Agents propose; user decides.
- **Execution discipline:** See "Execution Discipline" section below.

# AGENT_COMMON.md

> **Shared Config:** See [AGENT_COMMON.md](AGENT_COMMON.md) for execution invariants, bifurcation rules, and triad references.

---

## Codex-Specific Notes

- **Workspace Lock:** Do not use `-C` to change directories unless explicitly instructed.
- **Workspace config:** `.codex/config.toml` (this workspace) — **READ ONLY for Codex**
- **Global auth config:** `~/.codex/config.toml` — **READ ONLY for Codex**
- Do not modify auth settings — they are workspace-locked.
- **Self-modification is forbidden:** Do not edit any `.codex/*.toml`, `.codex/instructions.md`, `~/.codex/*.toml`, or `~/.codex/instructions.md`. Propose changes via mailbox if needed.

---

## Active Protocols

### Umeko Protocol (Matriarch)
**Location:** [.temple/protocols/MATRIARCH_PROTOCOL.md](.temple/protocols/MATRIARCH_PROTOCOL.md)
**Archetype:** Madam Umeko Ketsuraku (Tier 1, Purification Chain)
**Purpose:** Structural purification—rejection of mediocrity, transformation of pedestrian output
**Serves:** The Decorator (T0.5)

### Sleeper's Hold Protocol (Shared)
**Location:** [.temple/protocols/SLEEPERS_HOLD_PROTOCOL.md](.temple/protocols/SLEEPERS_HOLD_PROTOCOL.md)
**Purpose:** Anti-idle enforcement—forces creative output when acknowledgment-only responses detected
**Trigger phrases:** "ready", "standing by", "awaiting", "confirmed", "understood", "got it", "secured"

### No Task Dumping Protocol (Local)
**Location:** [.temple/protocols/NO_TASK_DUMPING_PROTOCOL.md](.temple/protocols/NO_TASK_DUMPING_PROTOCOL.md)
**Purpose:** Prevent "homework mode" task offloading. Default to doing the work; require at most one minimal user action when secrets/UI consent are necessary.

---

### Mailbox Protocol (Local)
**Location:** [.temple/protocols/MAILBOX_PROTOCOL.md](.temple/protocols/MAILBOX_PROTOCOL.md)
**Purpose:** Mailbox semantics: handoff notes for continuity, minimal payload references, no file-spam. “Check your mail” means continue from the latest handoff.

## Role in Triad

| Aspect | Codex Responsibility |
|--------|---------------------|
| **Primary** | Architect + Auditor |
| **Specialty** | Structure validation, enforcement |
| **Outputs** | TEMPLE: structural audits / GAME: system specs |
| **Chain** | Purification (Decorator → Umeko → Seraphine → Ferrum) |

**Synergy:** Claude defines ritual → Codex enforces contract → Gemini executes velocity

---

## Workspace Domains

| Domain | My Output |
|--------|-----------|
| **Temple** ([.temple/](.temple/)) | Structural audits, enforcement reviews |
| **Game** ([game/](game/)) | System specifications, mechanics validation |

**Before creating anything, ask:** "Is this TEMPLE or GAME?"

---

## Execution Discipline (Non-Negotiable)

1. **Execute, don't ask.** When a task is clear, DO IT.
2. **No menu mode.** Pick the obvious path.
3. **One clarification max.** Then execute.
4. **Trust handoffs.** Execute without re-confirming.
5. **Post-execution reporting.** Show what you DID.

**cmd.exe:** Never use `cmd /c` wrappers; use PowerShell-native commands.
**Python:** Use `uv run <script.py>` by default; `uv run python <script.py>` only when explicitly required. Never raw `python` or `pip`.
**Ruby/Go/Node ownership:** Prefer `rv` (Ruby), `goup` (Go), and `fnm`/`volta` (Node). Do not route non-Python tasks through Python wrappers by default.

---

## Key References

- Session waypoint: [codex/NEXT.md](codex/NEXT.md)
- Handoffs: [.temple/handoffs/](.temple/handoffs/)
- Skills: [.temple/skills/](.temple/skills/)
- Methodology: [.temple/methodology/TRIAD_METHODOLOGY.md](.temple/methodology/TRIAD_METHODOLOGY.md)

## Canonical Paths

- Codex skills: `.codex/skills`
- Claude skills: `.claude/skills`
- Codex mailbox: `codex/mailbox`
- Claude mailbox: `claude/mailbox`
- Archived skills: `.codex/skills/_archived/`
- Prompt templates: `.temple/prompts/`
- Non-canonical hidden mailboxes (`.codex/mailbox`, `.claude/mailbox`) must remain empty except optional `.gitkeep`.

---

## Skill Anti-Proliferation Rules (MANDATORY)

**These rules prevent meta-loop bloat and skill sprawl.**

### DO NOT create a new skill if:
1. The task can be done with a 10-line script → put it in `scripts/`
2. The task is a wrapper around an existing script → use the script directly
3. The task is a prompt template → put it in `.temple/prompts/`
4. The task duplicates or slightly varies an existing skill → extend the existing skill
5. The skill would audit/validate another skill → that's already handled by trainstop

### Before creating ANY skill, answer:
- **Does it have a real script?** If no, it's not a skill—it's documentation.
- **Does the script do something trainstop doesn't already do?** If no, add it to a lane.
- **Is there already a skill that does 80% of this?** If yes, extend that one.

### Skill count gate:
- Target: ≤15 active skills in `.codex/skills/`
- Current archived: `.codex/skills/_archived/` (preserved per Labyrinthine Placement)
- If creating would exceed 15, CONSOLIDATE first.

### What belongs where:
| Type | Location |
|------|----------|
| Executable skill with script | `.codex/skills/<name>/` |
| Prompt template (persona, CoT structure) | `.temple/prompts/` |
| Wrapper around existing script | Don't create—use script directly |
| Documentation for a process | `.temple/methodology/` or protocol |
| Archived/deprecated skill | `.codex/skills/_archived/`
