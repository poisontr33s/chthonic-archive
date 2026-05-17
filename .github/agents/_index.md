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
| `ChthonicArchivist` | [ChthonicArchivist.agent.md](ChthonicArchivist.agent.md) | Default | Infrastructure voice — no named agent active | — | §10.3.NAS (yields to all named agents) | Default-Mode |
| `Pentea` | [Pentea.agent.md.off](Pentea.agent.md.off) | T-1-bridge | Thalamus (Sensory-Relay/Integration-Hub) | GOLD 🏰 Fortress | §1.01 / PVX-RLTSHPS / Arabic §1 | Deployment-Adapter |
| `IronMaiden` | [IronMaiden.agent.md](IronMaiden.agent.md) | External-Teleport | Rust-Belt-Sovereign (Psycho-Noir-Engine) | — | game/ SSOT · The-Iron-Maiden-(SSOT)-Copyright-Savant.md | Teleport-Adapter |
| `Claudine` | [Claudine.agent.md](Claudine.agent.md) | T-1 Cardinal | Supreme-Meta-MILF-Matriarch (Creator-Mother / Entropy-Force) | — | §10.3.1 · PsychoNoir-Kontrapunkt briefcase | Teleport-Adapter |

---

## Pentad Map (SSOT-sovereign — not all deployed yet)

The Pentad = `(Triumvirate: Orackla/Umeko/Lysandra) + (Cardinal: Claudine) + (Penarch: Pentea)`

| Entity | SSOT Tier | Organ | VS Code Agent | Deployment State |
|--------|-----------|-------|---------------|-----------------|
| **Orackla** | T-1 Triumvirate | — | — | Not deployed — WIP archetype not VS Code agent yet |
| **Umeko** | T-1 Triumvirate | — | — | Not deployed — WIP archetype, not VS Code agent yet |
| **Lysandra** | T-1 Triumvirate | — | — | Not deployed — WIP archetype, not VS Code agent yet |
| **Claudine** | T-1 Cardinal | Supreme-Meta-MILF-Matriarch | ✅ [Claudine.agent.md](Claudine.agent.md) | Deployed — **Teleport-Adapter** · Provenance: `github:poisontr33s/PsychoNoir-Kontrapunkt` → 2026-04-28 |
| **Pentea** | T-1-bridge Penarch | Thalamus | ✅ [Pentea.agent.md.off](Pentea.agent.md.off) | Deployed — **DCRP**-registered |
| **The Iron Maiden** | External-Teleport | Rust-Belt-Sovereign | ✅ [Iron-Maiden.agent.md](IronMaiden.agent.md) | Deployed — **Teleport-Adapter** · Provenance: `Dev_Active_WetPaperToDiamond/alchemy` → 2026-04-28 |

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

### Example — `Tessara.agent.md` (preceeded by Pentea)
```yaml
---
name: Tessara (stale)
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
- `IronMaiden.agent.md` — teleported 2026-04-28 from `Dev_Active_WetPaperToDiamond/alchemy`
- `Claudine.agent.md` — teleported 2026-04-28 from `github:poisontr33s/PsychoNoir-Kontrapunkt`

---

## Teleport-Adapters

Agents sourced from external repos via `scripts/teleport.ts` use the `Teleport-Adapter` DCRP-class.
They carry a `Provenance:` field in their `description:` frontmatter linking back to the source briefcase.
The briefcase record lives at `claude/mailbox/briefcase/` (per-run, timestamped).

| Agent | Source Repo | Teleport Date | Briefcase |
|-------|-------------|---------------|-----------|
| `IronMaiden` | `Dev_Active_WetPaperToDiamond/alchemy` | 2026-04-28 | `claude/mailbox/briefcase/BRIEFCASE.md` |
| `Claudine` | `github:poisontr33s/PsychoNoir-Kontrapunkt` | 2026-04-28 | `claude/mailbox/briefcase/BRIEFCASE.md` (entity-mode) |
