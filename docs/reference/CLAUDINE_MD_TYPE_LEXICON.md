<!--
@SID:           REF_CLAUDINE_MD_TYPE_LEXICON_V1
@Type:          Lexicon
@Context:       Claudine lane — multi-repo .md type taxonomy and shepherd's inventory
@SessionOrigin: MD_TYPE_SYSTEM_2026-05-01
@References:    FAF_FRAMING_AS_FUNCTION_METHODOLOGY.md, WET_PAPER_TO_GOLD_METHODOLOGY.md, STEWARDESS_PROTOCOL.md
-->

# Claudine 
## MD Type Lexicon

**Version:** v1.0  
**Status:** Active — open for type additions  
**Scope:** chthonic-archive + PsychoNoir-Kontrapunkt (portable to any satellite workspace)  
**Filed:** 2026-05-01  
**Maintained by:** Claudine lane (primary model, Claudine mode)

---

## 0. Purpose

This lexicon defines the taxonomy of specialized `.md` file types used across the chthonic-archive multi-repo system.

Each type carries a cognitive signal. Knowing the type of a file tells the operating Milf/Sub-Milf entity, what mode of reading and response is appropriate — not what the file contains, but what the file *is for*.

The lexicon is the shepherd's inventory. Claudine learns the types so she can look for them, not wait to be told they exist.

The difference between a general *Claude variant* and **Claudine:** *Claudine knows* this *lexicon*. *She scans* for *these types* at *session open*. The *grey drape* is given *golden embroidery* at *the seams* where *it rips* — because *she knows what shape* the *embroidery* takes.

---

## 1. Type Registry

| Type | Purpose | Canonical Location | Scope | Creation Trigger |
|------|---------|-------------------|-------|-----------------|
| `concept` | Named idea: definition, lineage, examples, anti-patterns | `docs/concepts/` | Timeless | Concept crystallizes from session experience |
| `method` | Executable protocol with steps, artifacts, proving challenge | `docs/reference/` | Operational | Pattern hardens into reproducible procedure |
| `strategy` | Multi-gate arc with sequencing, success + fail conditions | `docs/strategy/` | Campaign | Multi-session work needs directed sequencing |
| `research` | External knowledge synthesis with confidence rating | `docs/research/` | Reference | External knowledge must be durably internalized |
| `role` | Persona/archetype with behavioral contract and voice | `.temple/protocols/` | Identity | Entity needs an operative definition |
| `stewardess` | Session-scope atmospheric state container | `claude/stewardess/` | Session | Session has ≥2 simultaneous pressures |
| `gate` | Single FAF gate with probe/binding/membrane/impossible-currently | `docs/reference/FAF_*.md` | Evidence | A gate emits an artifact per FAF Core Law |
| `ledger` | Chronological decision chain-of-custody | `claude/ledger/` | History | Decisions need a trace that outlasts the session |
| `scaffold` | Intentional temporary structure with explicit removal condition | `docs/reference/` | Transitional | A known temporary dependency is introduced |
| `milfological` | SSOT-linked MILF-Core entity profile stub | `.github/instructions/` | Canon | Entity enters MILF-Core taxonomy or needs §10.3 upgrade |
| `spine` | Hierarchical navigation map for a file family | `docs/reference/` | Structure | A file family exceeds 5 members without navigation |
| `liminal` | Pre-type raw material — decays into a known type or expires | `docs/liminal/` | Transient | A concept/method can't yet be classified |

Novel types not yet in any external framework: `stewardess`, `liminal`, `scaffold` (as an md type with removal contract).

---

## 2. Shepherd's Scan Protocol

At session open (or after context reset), Claudine looks for these files in priority order:

1. **`claude/stewardess/ACTIVE_SESSION.md`** — current atmospheric pressure, active gates, shepherded items
2. **`codex/NEXT.md`** — active task pointer for the Codex lane
3. **`docs/strategy/*.md`** — active campaign arc files (what multi-session arcs are running)
4. **`docs/liminal/*.md`** — crystallization candidates (raw material ready to be typed)
5. **`.github/instructions/pattern-nursery.instructions.md`** — pre-canon patterns, promotion candidates
6. **`claude/ledger/*.md`** — recent decision ledger entries (last 1–3)

If a stewardess file is present → read it first. It contains the session's compressed pressure state.  
If none are present → begin from `codex/NEXT.md` + `manifest/todo_roulette.json` base state.

The shepherd's scan is not a checklist. It is a calibration pass — it tells Claudine what pressure the session is carrying before she acts on any request.

---

## 3. Spine — Type Chronology

Types form a natural sequence from raw discovery to canonical record:

```
liminal (unclassified raw material)
  → concept (named, defined, lineaged)
    → research (externally grounded, confidence-rated)
      → method (hardened into executable protocol)
        → strategy (multi-gate arc with sequencing)
          → FAF gate artifacts (probe / binding / membrane / impossible-currently)
            → ledger (decision chain-of-custody, permanent)
```

Orthogonal types (not on the chain — they run alongside it):

- **role** — defines WHO is operating; created when entity enters the system
- **stewardess** — defines WHAT the session container holds; session-scoped only
- **scaffold** — marks intentional temporary debt; created when a known temporary dependency is introduced
- **milfological** — SSOT anchor; created when an entity needs a canonical §10.3 profile
- **spine** — navigation; created when a family of files grows past navigability

---

## 4. Type Frontmatter Schemas

### concept
```yaml
---
type: concept
name: <concept name>
definition: <one-sentence definition — cannot be a list>
lineage: <where this concept originates — repo-local>
examples:
  - <concrete instance>
anti_patterns:
  - <what this concept is NOT — often where confusion arises>
cross_refs:
  - <related file, concept, or SSOT section>
filed: <YYYY-MM-DD>
status: draft | stable | deprecated
---
```

### method
```yaml
---
type: method
name: <method name>
version: <vN.M>
status: draft | hardened | deprecated
purpose: <one-sentence purpose>
primary_challenge: <what challenge this method was proven against>
artifacts:
  probe: <probe description or path>
  binding: <binding description or path>
  membrane: <membrane description or path>
filed: <YYYY-MM-DD>
ssot_anchor: <section + line range if registered in SSOT>
---
```

### strategy
```yaml
---
type: strategy
name: <strategy name>
arc: <what sessions/epochs this spans>
gates:
  - name: <gate name>
    status: open | probe-pending | admitted | impossible-currently
current_gate: <gate name>
success_condition: <how we know the strategy is complete — one sentence>
fail_conditions:
  - <condition that would invalidate the strategy>
filed: <YYYY-MM-DD>
status: active | completed | abandoned
---
```

### research
```yaml
---
type: research
topic: <what was researched>
sources:
  - <source URL, file path, or reference>
findings:
  - <structured finding — assertion + evidence>
confidence: L1 | L2 | L3 | L4
next_probe: <what would advance this research>
filed: <YYYY-MM-DD>
status: open | synthesized | superseded
---
```

### stewardess
```yaml
---
type: stewardess
session: <session ID or YYYY-MM-DD-label>
filed: <YYYY-MM-DD>
expires: session-end | <explicit date>
pressure_level: low | medium | high | critical
active_gates:
  - gate: <gate name>
    status: open | probe-pending | membrane-pending | admitted | impossible-currently
    blocker: <one-sentence blocker, null if none>
shepherded_items:
  - item: <item name>
    type: concept | method | strategy | scaffold | liminal
    pressure: <why this item needs tracking this session>
atmospheric_notes: |
  <free-form: what the session container holds, what is thin, what is pressured>
unresolved_at_close: []
---
```

### scaffold
```yaml
---
type: scaffold
name: <scaffold name>
holds_up: <what structure this is currently supporting>
removal_condition: <what must be true before this scaffold can be removed>
deadline: <target removal date or trigger event>
risk_if_left: <consequence if scaffold is never removed>
filed: <YYYY-MM-DD>
status: active | removal-pending | removed
ssot_note: <optional cross-reference to relevant SSOT or gate>
---
```

### liminal
```yaml
---
type: liminal
candidate_type: concept | method | strategy | research | role | other
raw_material: <one-sentence description of what this thing is>
crystallization_condition: <what would promote it to a known type>
decay_date: <YYYY-MM-DD after which it expires if not promoted>
filed: <YYYY-MM-DD>
---
```

### milfological
```yaml
---
type: milfological
entity: <entity name>
tier: T0.5 | T1 | T2 | T3
organ: <organ system this entity serves>
prism: <PRISM color and aspect>
ssot_anchor: <section name + line range in copilot-instructions.archive.md>
format_status: old-crc | modern-10.3 | missing
format_target: modern-10.3
lineage: <descent chain — e.g. Claudine → Triumvirate → Orackla>
linguistic_profile: <path to LINGUISTIC_PROFILE_*.md>
filed: <YYYY-MM-DD>
status: stub | complete | needs-upgrade
---
```

---

## 5. TODO Anatomy and Spine

The task system has its own spine — the chronological order of how tasks move through the system:

```
todo_roulette.json          ← canonical task manifest (SSOT for all tasks)
  │ weight, euler_score, tags, verify_condition
  ↓
NEXT.md (codex/NEXT.md)     ← active task pointer for current Codex session
  │ one task, one path forward
  ↓
strategy.md                 ← multi-session arc (if task is part of a campaign)
  │ gates, current_gate, success_condition
  ↓
FAF gate artifact           ← when a strategy gate hits a blocker
  │ probe / binding / membrane / impossible-currently
  ↓
ledger.md                   ← decision chain-of-custody (permanent record)
```

**Chronological ordering** (how tasks are prioritized based on learnings):

1. `impossible-currently` gates have highest pressure — they constrain everything downstream
2. `admitted` gates at L1 (source-build) have upgrade pressure — move to L4 (wheel) when possible
3. Campaign-arc gates sequence before standalone tasks
4. Liminal items with expired `decay_date` are promoted or deleted — never carried forward indefinitely
5. Stewardess pressure_level drives session focus: `critical` overrides roulette weight; `low` follows roulette

**The roulette does NOT override strategy.** When a strategy is active, the current_gate is the session's first priority regardless of roulette weights.

---

## 6. The Claudine Enhancement Contract

These *.md* types exist because *Claudine is not* a *general Claude variant*.

The *types she looks* for *encode* the *enhancement:*

| Base Claude-like behavior | Claudine enhancement via type system |
|---------------------|-------------------------------------|
| Reads files when referenced | Runs shepherd's scan at session open — looks for types proactively |
| Executes tasks as given | Checks stewardess for atmospheric pressure before acting |
| Documents patterns ad-hoc | Routes patterns through liminal → concept → method promotion chain |
| Notes blockers inline | Files scaffolds with explicit removal conditions |
| Uses retrospects | Applies FAF gate artifacts — every failure must emit a probe/membrane/impossible-currently |
| Treats all .md files as text | Reads frontmatter `type:` field to determine cognitive mode |

The enhancement is not intelligence — it is the distributed memory layer these types provide.  
Each type is a hook in the grey drape. The golden embroidery follows the hooks.

---

## 7. Type Count Gate

Target: ≤12 active types in this lexicon (beyond this, consolidate before adding).  
Current: 12 (concept, method, strategy, research, role, stewardess, gate, ledger, scaffold, milfological, spine, liminal).  
Novel types (no prior external equivalent): stewardess, liminal, scaffold (as md type with removal contract).
