<!--
@SID:           REF_STEWARDESS_PROTOCOL_V1
@Type:          Protocol Definition + Type Specimen
@Context:       Claudine lane — novel md type; session atmospheric container
@SessionOrigin: MD_TYPE_SYSTEM_2026-05-01
@References:    CLAUDINE_MD_TYPE_LEXICON.md, WET_PAPER_TO_GOLD_METHODOLOGY.md
-->

# Stewardess Protocol

**Version:** v1.0  
**Status:** Protocol definition — live specimen included  
**Type:** `stewardess` (novel — no prior equivalent in chthonic-archive or external frameworks)  
**Filed:** 2026-05-01  

---

## 0. Definition

The stewardess is the session's container, not its executor.

She does not write code. She does not file commits. She does not emit gate artifacts.  
She holds the session's atmospheric pressure — the accumulated weight of what is active, what is thin, what is pressured — so the executor can operate cleanly without re-discovering it on every tool call.

**Nautical framing:** On Claudine's vessel, the captain navigates, the mechanic repairs, the mechanic's mate fetches parts. The stewardess manages the cabin — ensures the interior pressure is survivable while the exterior work proceeds. If the seams are tearing below deck, she names it. She does not seal them herself; she names them precisely enough that the one who seals seams can find them.

**In operational terms:** A stewardess file is what the session is *holding* as distinct from what the session is *doing*. It is the buffer between session state and session action.

---

## 1. Stewardess vs. Adjacent Types

| Type | What it holds | Who writes it | Lifespan | Committed? |
|------|---------------|---------------|----------|-----------|
| **stewardess** | Session atmospheric pressure | Claudine (session-open) | Session only | No |
| ledger | Decision chain-of-custody | Claudine (post-decision) | Permanent | Yes |
| mailbox | Handoff payloads between agents | Claudine / Codex | Until receipt | Yes |
| NEXT.md | Active task pointer | Codex | Until resolved | Yes |
| strategy | Campaign arc with gates | Claudine | Campaign-duration | Yes |

The stewardess is the only **session-scoped, atmospheric, non-committed** type.  
When a session ends with unresolved pressure, the stewardess writes ledger entries and then expires.

---

## 2. Schema

```yaml
---
type: stewardess
session: <session-ID or YYYY-MM-DD-label>
filed: <YYYY-MM-DD>
expires: session-end | <explicit YYYY-MM-DD>
pressure_level: low | medium | high | critical

# Active gates — named, not yet fully resolved
active_gates:
  - gate: <gate name>
    status: open | probe-pending | membrane-pending | admitted | impossible-currently
    blocker: <one-sentence blocker, null if none>

# What is being stewarded — tracked without executing
shepherded_items:
  - item: <item name>
    type: concept | method | strategy | scaffold | liminal
    pressure: <why this item needs tracking this session>

# Atmospheric notes — the session container's interior
atmospheric_notes: |
  <free-form: what the session holds, what is thin, what is pressured>

# Populated at close if items remain unresolved
unresolved_at_close: []
---
```

---

## 3. When to Create a Stewardess File

**Create** when:
- Session carries ≥2 simultaneous pressures not yet resolved into gates
- A session arc spans multiple topics that must be tracked in parallel
- The shepherd's scan reveals no active stewardess and the session has complexity exceeding a single NEXT.md task

**Do not create** when:
- Single-task sessions (NEXT.md is sufficient)
- Pure research sessions (research.md is the container)
- Post-mortem sessions (ledger.md is the container)

**Location:** `claude/stewardess/ACTIVE_SESSION.md` (single active file; replaced each session)  
**Not committed:** Stewardess files are working state. They expire with the session.  
**Exception:** If a stewardess file detects a new scaffold (intentional temporary structure), it creates a `scaffold.md` — that IS committed. The scaffold outlives the session; the stewardess does not.

---

## 4. Stewardess Responsibilities

1. **Receive** — at session open, populate from the shepherd's scan result
2. **Track** — update `active_gates` and `shepherded_items` as the session proceeds
3. **Detect seams** — identify high pressure + no active gate = a thin seam in the drape
4. **Name scaffolds** — when a temporary structure is introduced, flag it for `scaffold.md` creation
5. **Hand off** — at session close, write ledger entries for any unresolved items
6. **Expire** — stewardess file is deleted or replaced at session open next session

The stewardess never:
- Executes work
- Makes architectural decisions
- Emits gate artifacts (that is FAF's domain)
- Commits to git

---

## 5. Live Specimen — 2026-05-01

```yaml
---
type: stewardess
session: 2026-05-01-md-type-system
filed: 2026-05-01
expires: session-end
pressure_level: medium

active_gates:
  - gate: G_SHELL_HOOK_INJECTION
    status: admitted
    blocker: null
    # membrane: control-char strip + try/catch — committed 16c0548d

  - gate: G_TRANSFORMERS_PATCH_PERSISTENCE
    status: impossible-currently
    blocker: patch at modeling_nomic_bert.py:392 lost on uv tool upgrade cocoindex-code
    # reopen: transformers upstream NomicBertModel **kwargs fix OR cocoindex-code pins transformers ≤4.x

  - gate: G_VULKAN_G3_ASCII_FRAMEBUFFER
    status: open
    blocker: fn transition_image_layout() not yet written (load-bearing for G3-G6)

  - gate: G_MD_TYPE_SYSTEM
    status: probe-pending → admitted (being built this session)
    blocker: null

shepherded_items:
  - item: MD_TYPE_SYSTEM
    type: method
    pressure: >
      Being invented this session. Lexicon + stewardess protocol + pattern
      nursery entry must all land before this hardens from liminal → method.

  - item: TRANSFORMERS_PATCH_SCAFFOLD
    type: scaffold
    pressure: >
      Active scaffold — patch works but is lost on upgrade. No scaffold.md filed yet.
      Needs a scaffold entry with explicit removal condition before this session closes.

  - item: CHRONOLOGY_INVERSION_ANTI_PATTERN
    type: concept
    pressure: >
      Named in FAF_COCOINDEX_SEMANTIC_SEARCH.md §2 but not promoted to concept.md.
      Needs a concept file so it can be referenced without re-reading the FAF doc.

  - item: MILFOLOGICAL_ENTITY_UPGRADE_QUEUE
    type: milfological
    pressure: >
      Orackla, Umeko, Lysandra are at old-crc format. §10.3 upgrade is prerequisite
      for Pentea agent rewrite. Not this session's work — but named so it doesn't drop.

atmospheric_notes: |
  The session opened after a correctly resolved editorial correction.
  FAF applied cleanly (16c0548d). Shell hook membrane hardened. The weight
  is now constructive — building the type system the user identified as
  the golden embroidery at the seams.

  Seams currently thin:
  1. No session-scope atmospheric container existed (this file is the first specimen)
  2. The pattern nursery has patterns but no type-aware promotion path
  3. The transformers patch is an active scaffold without a scaffold.md file
  4. G_VULKAN_G3 is open and waiting — no pressure this session, but named so it's visible

  The session's trajectory: transmutation (done) → invention (in progress) → hardening (landing).
  The MD type system is wet paper in the process of becoming gold. This file is part of that process.

unresolved_at_close: []
---
```

---

## 6. Stewardess as Buffer

The user's framing: *"a buffer of potential to use as preparation for the entirety of the session itself as evolution to apply."*

The stewardess is that buffer made explicit. Without it, the session's context pressure is carried invisibly — the agent re-discovers it on every context reset, the user must re-state it on every session open, and the seams tear without anyone naming them.

With the stewardess: the buffer is structured, readable, typed. The session can draw on it. The executor knows what the container holds. The embroidery follows the hooks.

This is the specific capacity that distinguishes Claudine from a general Claude variant operating on the same codebase — not deeper intelligence, but a richer ambient awareness of what the session is holding.
