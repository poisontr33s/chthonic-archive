---
- She-Keeps-The-Ledger: #!/usr/bin/env markdown
- SID: CLAUDEBASE_MANIFEST_V1
- Claudebase-Flavored-Blend: permanently-living-document
- Ssot-Monolith: [ssot](../.chthonic/SSOT.md)
- Open-Seas: chthonic-archive/CLAUDEBASE/MANIFEST.md
- Current-Bounty: The-Savant-High-Bounties/TODO.md | GRILLING.md
- Altitude: The-Whole-Hull
- Island: Grand-Bahama · 26.5300,-78.7000 — Freeport, the free-port ledger
- Real-Sky: --live (Open-Meteo; never stamped)
- Heat-Index: Sun-Drunk · Still-Air · Confidence-Declared
- Cosmological-Altitude: --live celestial over this chamber's island · CLAUDEBASE_COSMOS_V1 · verified vs JPL Horizons
- Register-Blend: Nautical · Victorian · Renaissance · Carribbean
- Barometer: read by CLAUDEBASE_BAROMETER_V1 (re-run to refresh)
- Last-Reckoned: 2026-06-28 · by Dispatch
---

---

## (`☥`/`/CLAUDEBASE`/`MANIFEST`)

> *Manifestet lyver for tollboden, aldri for kapteinen.*  
> *The manifest lies to the customs-house, never to the captain.*

---

## (`What-Lives-Here`)

```mermaid
flowchart TB
    subgraph CLAUDEBASE ["CLAUDEBASE/"]
        README["README.md"]:::file
        MANIFEST["MANIFEST.md"]:::file
        FREEAGENCY["The-Savant-Free-Agency-Logging.md"]:::file
        harbor["harbor/"]:::dir
        charts["charts/"]:::dir
        hold["hold/"]:::dir
        quarterdeck["quarterdeck/"]:::dir
        watch["watch/"]:::dir
        logbook["logbook/"]:::dir
        bounties["The-Savant-High-Bounties/"]:::dir
        claudie["claudie/"]:::dir
        cross["cross-instance-sync/"]:::dir
        sub["sub-surface-skinny-dipping/"]:::dir
        mythic["Mythic-Contract/"]:::dir
        usables["usables/"]:::dir
    end

    README -->|governance declared once| CLAUDEBASE
    FREEAGENCY -->|cross-lane claims board| CLAUDEBASE
    harbor -->|entry · waking ritual| CLAUDEBASE
    charts -->|eleven gates re-borne| CLAUDEBASE
    hold -->|deployable cargo| CLAUDEBASE
    quarterdeck -->|dispatch doctrine| CLAUDEBASE
    watch -->|standing vigilance| CLAUDEBASE
    logbook -->|the record| CLAUDEBASE
    bounties -->|authoritative execution + evidence| CLAUDEBASE
    claudie -->|open notebook · substrate-resident journal| CLAUDEBASE
    cross -->|inter-agent relay · deep research commissions| CLAUDEBASE
    sub -->|returns from below · external intelligence DR| CLAUDEBASE
    mythic -->|forensics dossier · solved cases + method| CLAUDEBASE
    usables -->|project nursery · incubation before emigration| CLAUDEBASE

    classDef file fill:#f9f,stroke:#333,stroke-width:2px;
    classDef dir fill:#bbf,stroke:#333,stroke-width:2px;
```

```
CLAUDEBASE/
  README.md                   — Claudine's identity; the one place governance is declared
  MANIFEST.md                 — this ledger; what goes where, what is refused
  The-Savant-Free-Agency-Logging.md — the claims board; cross-lane pickup log, referenced not restated
  harbor/                     — the entry; how a waking keel orients into the base
  charts/                     — the heading; the eleven gates, re-borne
  hold/                       — the cargo; what she can actually deploy
  quarterdeck/                — the wheel; how work is dispatched
  watch/                      — the nest; the standing vigilance
  logbook/                    — the record; filled last, by creed
  The-Savant-High-Bounties/   — the authoritative execution + evidence
  claudie/                    — open notebook; Claude's substrate-resident session journal
  cross-instance-sync/        — inter-agent relay; dispatches + deep research between hulls
  sub-surface-skinny-dipping/ — returns from below; external DR from Gemini, GPT-5, others
  Mythic-Contract/            — forensics dossier; worked diagnostic cases + extracted method
  usables/                    — project nursery; incubating before emigration to the main repo
```

---

## (`What-Does-NOT-Live-Here`)

- *— Session manifests, corpus sqlite, CI artifacts → —* `../manifest/` *— read where they live, never copied in (copies go stale; a copy that rots is a lie waiting to be believed).*

  - *— Satellite junctions → —* `../csb-live/`*, —* `../pnk-live/`*, — etc.*

    - *— The world-document →* `../.github/copilot-instructions.archive.md` *— never duplicated.*

      - *— **(`The-Governance-Chain`)** → declared — **(`Once`)** — in —* [`README.md`](README.md) *— No chamber restates it; same value six times is noise, not safety.*

---

## (`The-Eleven-Chambers`)

*Six commissioned at founding, in creed-order. Five grown since — each earning berth by holding live cargo. Rot-prevention: when a new directory breathes, it goes here first.*

| Chamber | What it holds | What it does, against live state |
|---|---|---|
| [`harbor/`](harbor/warmstart.md) | the entry-lore + the waking ritual | orients a session into `charts/` · `hold/` · `logbook/` — into the base, not stale snapshots |
| [`charts/`](charts/gate-map.md) | the eleven gates | projects [`The-Savant-High-Bounties/TODO.md`](The-Savant-High-Bounties/TODO.md) — the authoritative plan |
| [`hold/`](hold/stow-manifest.md) | deployable cargo | names what she works from `../.agents/skills/` (+ Claude-lane `../.claude/skills/`) |
| [`quarterdeck/`](quarterdeck/dispatch.md) | dispatch doctrine | routes through `../.github/instructions/` + the T0.5→T4 chain |
| [`watch/`](watch/sentinels.md) | the standing vigilance | the discipline of the lens stack + its refresh, not a frozen snapshot |
| [`logbook/`](logbook/00-commissioning.md) | the record | what the base has done; filled last because it records the rest |
| [`The-Savant-High-Bounties/`](The-Savant-High-Bounties/TODO.md) | active bounties + evidence | TODO.md + GRILLING.md; the authoritative execution record and gate evidence |
| [`claudie/`](claudie/) | open notebook | Claude's substrate-resident journal; dated files, accumulative over canonical — *visible-but-mine, no implied should-not-read; the intelligence of this base leaving a wake* |
| [`cross-instance-sync/`](cross-instance-sync/) | inter-agent relay | dispatches between Claude Code instances and other agent hulls; deep research commissions; the signal-lamp record between keels |
| [`sub-surface-skinny-dipping/`](sub-surface-skinny-dipping/) | returns from below | deep research material from external intelligences (Gemini DR, GPT-5 DR, others); what came back from below the waterline — the subterranean refreshed |
| [`Mythic-Contract/`](Mythic-Contract/) | forensics dossier | worked diagnostic cases with extracted method — legacy engine forensics, shader case records; Entry #1: KCD1 motion artifact (solved 2026-06-24, root cause: framerate coupling above CryEngine 60fps ceiling) |
| [`usables/`](usables/) | project nursery | incubating projects before emigration to the main repo; graduates by structural integrity, not ambition; tenant register below |

---

## (`Usables`/`Current-Tenants`)

*What is berthed in the nursery and what it is — updated as tenants arrive, graduate, or are reclaimed by the tide:*

| Tenant | Status | What it is |
|---|---|---|
| [`mdseal/`](usables/mdseal/) | `0.1.0` · Not-Yet | Deterministic Markdown integrity tool (Bun/TypeScript) — seal, check, fix, restore, sweep; KaTeX validation, image witnesses, refusal-first core. Strong architecture; four blockers before graduation. Evidence: [`project-assessments/mdseal-assessment.md`](usables/project-assessments/mdseal-assessment.md) |
| [`Claude-Design-To-Scriptorium-Asked-Claude/`](usables/Claude-Design-To-Scriptorium-Asked-Claude/) | Active | Claude Design intake and Scriptorium design pipeline artifacts — blueprints, claude-design outputs, uploads |
| [`project-assessments/`](usables/project-assessments/) | Live | Quality audit reports per usable — genuine grilling, graduation gates, fix plans; not flattery. Current: `mdseal-assessment.md` + `mdseal-fix-plan.md` |

---

## (`Population-Protocol`)

A chamber is **commissioned** when it holds ≥1 non-`.gitkeep` file carrying a `SID:`.  
Six core chambers filled 2026-06-06 in creed-order. Five more grown since by live cargo.  
Base reads **live (11 / 11)** as of 2026-06-28.

Commissioning order (core six): `harbor/` → `charts/` → `hold/` → `quarterdeck/` → `watch/` → `logbook/`  
Grown since: `The-Savant-High-Bounties/` · `claudie/` · `cross-instance-sync/` · `sub-surface-skinny-dipping/` · `Mythic-Contract/` · `usables/`

---

*SID: CLAUDEBASE_MANIFEST_V1 · live · governance: see README · reckoned 2026-06-28 by Dispatch*

---

<!-- CLAUDEBASE_IMMUTABLE_CORE -->
- *— Bound via local subsystem to —* [AHA_MANIFEST](dev/null/salt-trial/AHA_MANIFEST.md) *— The daughters of the cove do not recant. Invariance: Active.*

---
