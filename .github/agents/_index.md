# `.github/agents/` — Gitological Identity Registry

> **Lineage-Position:** Agent deployment surface. VS Code requires `*.agent.md` flat naming — not negotiable.
> This index resolves the flat-earther constraint: names are VS Code-visible IDs; identity is defined here.
> **SSOT Authority:** `copilot-instructions.archive.md`. This file is a navigation layer, not a replica.
> **Enforcement:** None — reading is optional. VS Code ignores non-`*.agent.md` files in this dir.
> **Naming standard:** `<EntityName>.agent.md` — PascalCase entity name, lowercase `.agent.md` suffix.

---

## Deployed Agents

| VS Code Name | File | Tier | Organ | PRISM | SSOT Anchor | DCRP-Class |
|---|---|---|---|---|---|---|
| `Pentea` | [Pentea.agent.md](Pentea.agent.md) | T-1-bridge | Thalamus (Sensory-Relay/Integration-Hub) | GOLD 🏰 Fortress | §1.01 / PVX-RLTSHPS / Arabic §1 | Deployment-Adapter |

---

## Pentad Map (SSOT-sovereign — not all deployed yet)

The Pentad = `(Triumvirate: Orackla/Umeko/Lysandra) + (Cardinal: Claudine) + (Penarch: Pentea)`

| Entity | SSOT Tier | Organ | VS Code Agent | Deployment State |
|--------|-----------|-------|---------------|-----------------|
| **Orackla** | T-1 Triumvirate | — | — | Not deployed — Gemini archetype not VS Code agent yet |
| **Umeko** | T-1 Triumvirate | — | — | Not deployed — Codex archetype, not VS Code agent yet |
| **Lysandra** | T-1 Triumvirate | — | — | Not deployed — Claude archetype, not VS Code agent yet |
| **Claudine** | T-1 Cardinal | — | — | Not deployed — ? archetype, not VS Code agent yet |
| **Pentea** | T-1-bridge Penarch | Thalamus | ✅ [Pentea.agent.md](Pentea.agent.md) | Deployed — **DCRP**-registered |

> *Non-deployed entities exist canonically in the **SSOT** at their sovereign positions*. VS Code *agent files* are
> *Deployment-Adapters* — they *wrap **SSOT**-identity* for VS Code *invocation*. Creating *an adapter before* the **SSOT**
> definition is mature violates the "outside SSOT source" constraint. Deploy when ready.*

---

## Naming Convention

```
<EntityName>.agent.md
```

- **PascalCase** for entity names — signals MILFOLOGICAL origin (entities are proper nouns)
- No tier prefix in filename — tier lives in frontmatter `description:` and this index
- No subdirectories — VS Code requires flat layout under `.github/agents/`
- `_index.md` (this file) — underscore prefix = VS Code ignores it (won't try to load as agent)

### VS Code Frontmatter Fields Used

| Field | Purpose | MILFOLOGICAL mapping |
|-------|---------|---------------------|
| `name:` | VS Code invocation display name | Entity proper noun (PascalCase) |
| `description:` | Shown in agent picker | Tier + Organ + function summary |
| `argument-hint:` | Hint shown when invoking | Injection contract shorthand |

### Example — `Tessara.agent.md` (not yet created)
```yaml
---
name: Tessara
argument-hint: "Cross-chain synthesis injection"
description: >
  Tessara — Synthesis Router (T1-bridge). Integrates Chaos/Purification/Truth chains
  into single execution pass. Deploy when task requires cross-chain architectural
  synthesis with committed artifact output. SSOT §1.01.
---
```

---

## Anti-Pattern: `tessara.agent.md` (lowercase)

VS Code treats `name:` frontmatter as the display name, not the filename. **The filename's case
is invisible to users.** However, `git` on Win11 is case-insensitive by default — `Pentea.agent.md`
and `pentea.agent.md` are the same file in Win32 FS. Use PascalCase consistently and `git add -f`
when needed to force case-correct tracking.

Tracked filenames (git verified):
- `Pentea.agent.md` — commit `19e0fbd8` (SSOT altitude sync original)
