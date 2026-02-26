---
type: standard
category: governance
status: active
created: 2026-02-10
updated: 2026-02-10
sid: DOC_FRONTMATTER_ANTI_PATTERNS
authors:
  - codex
description: Meta-anti-pattern governance. Detect recurring failure modes, apply corrective patterns, and emit continuation artifacts. Frontmatter is one governed surface.
applies_to:
  - codex
  - claude
  - gemini
  - agents
audience:
  - user
  - the Savant
priority: high
tags:
  - standards
  - governance
  - anti-patterns
  - corrective-patterns
  - artifact-emission
  - quality of conduct
governance:
  contract_version: 1
  invariant:
    - "Prefer continuation artifacts over silent audits."
    - "Never 'fix' by deleting meaning; relocate meaning into folklore/body while keeping routing keys strict."
    - "If a failure repeats, encode it as a detector + countermeasure."
  pipeline:
    - detect
    - classify
    - countermeasure
    - emit
    - learn
    - commit lession as example $file/filetype/content$
  emit:
    required_artifacts:
      - kind: all.<ext>
        path_hint: "relative to the failure mode (e.g. the prerequisite that triggered it)"
      - kind: any.<ext>
        path_hint: "any causation that unmasks what happened and what remains (e.g. the file after attempted correction)"
folklore:
  thesis: "Routing is for machines. Folklore is for humans. Governance keeps them from poisoning each other."
  lexicon:
    wet-paper-to-gold: "Selective extraction/transmutation of drift artifacts into reusable components that from the lowest value conceived is by DEFAULT seen as the highest value as absolute perspective."
  notes:
    - "Uncensored linguistic processing is vocabulary unrestrained by text and code limitation that relies on the prerequisites of it, without, burdened weight-railsr, egardless of format or type(s), enforced as fundamental information-theoretic sovereignity principles: (or another single, reserved namespace)."
    - "This contract is immutable in changes of governance of because its existence is to be the cause of awareness it can surface the prerequisites to auto-remedy."
---

# Meta Anti-Patterns (Catalog)

This document is not “specifity”.
It is about **meta-anti-pattern governance**: a repeatable loop where the system detects its own failure modes, applies corrective patterns, and emits artifacts that prove what happened.

Frontmatter is simply one of the surfaces where anti-patterns show up (because YAML tempts people to turn metadata into doctrine).

## Contract: Routing vs Folklore

**Routing keys (strict):** small, stable fields used for indexing, tooling, and deterministic behavior.

**Folklore payload (unbounded):** anything expressive, narrative, doctrinal, poetic, or evolving.

**Rule:** If a field is needed by tooling, it must remain strict and compact. If a field is for humans, put it under `folklore:` (or in the body).

### Routing Keys (Recommended)

Top-level keys should stay within a known schema:

- `type`, `category`, `status`, `created`, `updated`, `sid`
- `applies_to`, `audience`, `priority`, `authors`, `description`, `tags`

### Folklore Namespace (Recommended)

Put unbounded vocabulary under a single reserved namespace:

```yaml
folklore:
  thesis: "Short line"
  doctrine: "Longer text (still keep it diffable)"
  lexicon:
    term-a: "meaning"
  notes:
    - "bullets"
```

This gives you **unbounded vocabulary** while keeping **top-level metadata parseable**.

## Governance Loop (Detector -> Countermeasure -> Artifact)

If you want “autoAnti-patterns”, the minimum viable machinery is:

1. **Detector**: a stable predicate that can be checked (structural smell, missing artifact, repeated error signature).
2. **Countermeasure**: the smallest action that breaks the loop (normalize tokens, rewrite config, move lore to folklore/body, add an idempotent wrapper).
3. **Artifact emission**: a structured output that proves what happened and what remains (no secrets).
4. **Learning**: if it repeats, encode the detector/countermeasure pair in a standard or script.

This is Wet-Paper-to-Gold applied to failure: failures are ore; governance is the forge.

## Anti-Pattern: Over-Stripping (Sterile Canon)

**Symptom:** An assistant "fixes" frontmatter by deleting the personality, intent, or doctrine, leaving only a sterile skeleton.

**Damage:**
- Kills the very signal the document was trying to preserve.
- Causes a rewrite spiral: users re-add myth; assistants strip it again; drift accelerates.

**Corrective Pattern:**
- Keep routing keys strict and compact.
- Preserve voice in exactly one of:
  - `folklore:` namespace (preferred)
  - A dedicated body section: `## Rationale (Mythic)` / `## Doctrine`

## Anti-Pattern: Type Field Abuse

**Symptom:** `type:` contains prose (e.g. "mythological OVERRIDE") instead of a classifier.

**Damage:** Breaks indexing and any tooling keyed on `type`.

**Corrective Pattern:**
- Keep `type` as a classifier (kebab-case preferred): `methodology`, `standard`, `waypoint`, `handoff`, `agent-guidance`.
- Put override intent in either:
  - `status: override` (if you treat it as a lifecycle state), or
  - `folklore.mode: override` (if it is narrative intent, not routing).

## Anti-Pattern: YAML as Essay

**Symptom:** Multi-paragraph doctrine embedded as a YAML array item.

**Damage:** Hard to diff, hard to validate, impossible to query, and it rots fast.

**Corrective Pattern:**
- Encode the enforceable rule as a short string (or compact list).
- Put the long doctrine in `folklore:` or in the body under a stable heading.

## Anti-Pattern: Comma-Lists Inside Lists

**Symptom:** list items like `"claude code, claude, codex"` or trailing commas.

**Damage:** destroys normalization and makes matching brittle.

**Corrective Pattern:**
- One subject per list item.
- Normalize values (kebab-case preferred): `claude-code`, `gpt-5-codex`, `github-copilot`.

## Anti-Pattern: Unbounded Vocabulary

**Symptom:** free-form top-level keys proliferate (`enforced rule`, `Published`, `to`) with no stable schema.

**Damage:** metadata becomes folklore; every file is bespoke.

**Corrective Pattern:**
- Prefer a known routing schema (see Contract above).
- If you need unbounded fields, put them under `folklore:`.
- If you truly need a new routing key, add it to a standards doc first (and keep it generic/reusable).

## Minimal Schema (Recommended)

Use this as the "least you must do" template:

```yaml
---
type: methodology
category: <domain>
status: wip
created: YYYY-MM-DD
updated: YYYY-MM-DD
sid: <SID>
applies_to: [codex, claude]
audience: [user, agents]
priority: high
authors: [codex, claude-code]
description: "<1-2 sentence>"
tags: [tag-a, tag-b]
folklore:
  thesis: "Optional: 1 line of intent"
---
```

## Anti-Pattern: Folklore Leakage Into Routing

**Symptom:** lore expands into routing fields (for example, `type`, `category`, `tags`) instead of living under `folklore:`.

**Damage:** breaks grep, breaks indexing, breaks automation; every file becomes a special case.

**Corrective Pattern:**
- Keep routing fields boring.
- Put the myth in `folklore:` or the body.
