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

| Chamb