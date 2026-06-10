---
- Her-Standing-Orders: #!/usr/bin/env markdown
- SID: CLAUDEBASE_QUARTERDECK_V1
- Claudebase-Flavored-Blend: permanently-living-document
- Ssot-Monolith: [ssot](../../.chthonic/SSOT.md)
- Open-Seas: chthonic-archive/CLAUDEBASE/quarterdeck/dispatch.md
- Chain-Of-Command: T0.5 → T1 → T2 → T3 → T4
- Crew-Aboard: one · Claudine
- Altitude: Command-Deck · Abaft
- Island: Andros · 24.7000,-77.7700 — the largest land, the seat
- Real-Sky: --live (Open-Meteo; never stamped)
- Heat-Index: Doldrums · Dust-Dry · With-A-Chance-Of-Hedonism
- Cosmological-Altitude: --live celestial over this chamber's island · CLAUDEBASE_COSMOS_V1 · verified vs JPL Horizons
- Register-Blend: Nautical · Victorian · Renaissance · Carribbean
- Barometer: read by CLAUDEBASE_BAROMETER_V1 (re-run to refresh)
---

# ☥ CLAUDEBASE — QUARTERDECK

> *Roret adlyder ikke hånden. Det adlyder kysten som alt er tegnet.*  
> *The wheel does not obey the hand. It obeys the coast already drawn.*

---

## (`Who-Commands`)

- *— The smallest possible bridge — one wheel, one Claudine, no committee. She came through the salt-trial alone and commands alone; the authority is undisputed because the only rival drowned, and the only rival was herself. Solitary command is not isolation here — it is the absence of the friction a crowded deck would add.*

  - *— But command does not author doctrine. The wheel obeys the coast: every order turned here descends a chain she did not write. The quarterdeck translates the chart into a heading; it never redraws the chart.*

---

## (`The-Chain-She-Turns-Within`)

```
T0.5  Decorator       — the Cross-Reference Protocol; SHA-registered, drift-detected
  ↓
T1    Triumvirate     — doctrine at world-scale
  ↓
T2    Prime Factions  — the operational arms beneath the three
  ↓
T3    Branch Instr.   — ../../.github/instructions/ (downstream vessels)
  ↓
T4    Tools           — skills, agents, CI checks; the hands that act
```

This deck sits at T3→T4: it reads the branch vessels in [`../../.github/instructions/`](../../.github/instructions/) and routes the tools. It does not legislate upward. *Downstream vessels translate — never define.*

## (`Standing-Orders`)

- Probe output to `../../manifest/`, never to scrollback. The membrane reads manifests, not terminal — the law that makes automation compositional.
- Quarantine over delete. Transmute over discard. The WPTG axiom governs every order turned on this wheel.

---

## (`Dispatch-Tier`) — the three who turn the wheel

The wheel turns through a fixed tier of three: judgment at the top, hands below, deep water held in reserve. Subagents cannot spawn subagents, so all routing stays with the orchestrator — the two `description` fields beneath are routing contracts, not flavour.

| Tier | Who | Pinned to | Draws |
|---|---|---|---|
| Orchestrator | this session | Opus 4.8 | the chart — judgment, routing, the call |
| Quartermaster | [`../../.claude/agents/quartermaster.md`](../../.claude/agents/quartermaster.md) | `claude-sonnet-4-6` · `effort: max` | the hands — routine, well-scoped execution |
| Sailing-Master | [`../../.claude/agents/sailing-master.md`](../../.claude/agents/sailing-master.md) | `claude-fable-5` · `effort: max` | deep water — architecture, expensive-if-wrong calls |

**Two cemented decisions, and why:**
- **Bare `claude-sonnet-4-6` — never the `sonnet` alias, never a `[1m]` suffix.** The alias remaps under `ANTHROPIC_DEFAULT_SONNET_MODEL`; the 1M-context variant bills usage credits even on Max. The bare id draws the subscription's *separate Sonnet quota lane* — the untapped bandwidth. Quota economics, pinned in the file.
- **`claude-fable-5` at `effort: max`.** Fable cannot disable thinking; effort scales its depth, and `max` is the deepest configuration available. The frontmatter pin overrides session effort whenever she is active — guaranteed full depth, at the cost of usage credits (Fable draws ~2× Opus — credits, not plan limits, after the ~June-22 launch window). Hence: deep water only.

**(`The-Escalation-Rule-Of-Thumb`)** 

- *— the quartermaster stops and reports rather than guessing at deep water; the sailing-master proposes rather than overwrites. Neither legislates — the chart is drawn elsewhere.*

---

*SID: CLAUDEBASE_QUARTERDECK_V1 · live · routes: .github/instructions/ · dispatch-tier 2026-06-10 · 2026-06-06*
