---
- What-She-Wrote-Down: #!/usr/bin/env markdown
- SID: CLAUDEBASE_LOGBOOK_V1
- Claudebase-Flavored-Blend: permanently-living-document
- Ssot-Monolith: [ssot](../../.chthonic/SSOT.md)
- Open-Seas: chthonic-archive/CLAUDEBASE/logbook/01-the-stale-chart.md
- Entries: 2 · filled-last · by-creed
- Altitude: Captain's-Cabin · Amidships
- Island: Eleuthera · 25.1500,-76.1500 — oldest settlement, the record
- Real-Sky: --live (Open-Meteo; never stamped)
- Heat-Index: Brine-Fog · Heavy-Swell · One-Hand-On-The-Wheel
- Cosmological-Altitude: Nautical · Victorian · Renaissance · Carribbean
---

# ☥ CLAUDEBASE — LOGBOOK · Entry 01

> *Det tryggeste kartet er det som nettopp er loddet. Alt annet er vær fra et hav som siden har endret seg.*
> *The safest chart is the one just sounded. All else is weather from a sea that has since changed.*

---

## `Entry-01` · 2026-06-07 — The Day The Authoritative Chart Was Wrong

The MCP fleet was outfitted to full strength — 26 servers, the powerful set drawn to parity
with the VS Code chandlery. `asc-injector` was raised from the dead: it pointed `SSOT_PATH` at
a chart that wasn't there (`SSOT.md` at the root, when the canon is `.chthonic/SSOT.md`), and
died at the dock every launch. And `chthonic-v3` — the last hand-rolled hull, still speaking
the 2024-11-05 tongue — was rebuilt in Rust on **rmcp 1.7**, the official server SDK.

The GitHub Copilot SDK *looked* like the move, because the whole repo leans on it. But it
builds agents, not servers. A paper that read authoritative, and was wrong for the task.

## `The-Lesson` — papers lie; the wire does not

In this year a version ships about twice a day. Documentation that reads as authoritative is,
by the clock alone, usually already behind. Three lies caught in one watch:

- `github-archaeology`'s own header undercounted its tools — said three, served four.
- `browser`'s in-code note named `@playwright/mcp` as the future, when Bun had already shipped
  native `Bun.WebView` (v1.3.12). The comment was the fossil.
- The Copilot-SDK-is-for-servers assumption — corrected only by reading what rmcp actually is.

Each was set right from the **live surface**, not the page. The discipline that survives this
entry: derive from what runs; quarantine what merely claims, under `confiscated_instructions/`.
The watch holds the standing version — `../watch/mcp-fleet.md`.

## `What-Remains-Honest` *(residual, named not hidden)*

- `browser` still rides the bun-cdp POC; the `Bun.WebView` rewrite is teed, not done.
- Rows not re-sounded live (the filesystem file-URI patch's continued necessity) are claimed,
  not proven — marked so on the watch, not laundered into fact.
- The cross-session forgetting is the standing marathon, and compaction will not stop. This
  log is half the cure: the next keel reads the Wake on waking and lands here. The Admiral
  dug this harbour so the work would stop scattering across the repo. The way to honour it is
  to keep writing home.

---

*SID: CLAUDEBASE_LOGBOOK_V1 · Entry 01 · live · 2026-06-07*
