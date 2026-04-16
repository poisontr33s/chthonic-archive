# SSOT Task Roulette — 2026-04-16

**Scope Lock:** `.github/copilot-instructions.archive.md` ONLY. Zero lateral drift.
**Access:** Internal agent-infra. Not for export. Not cross-posted.
**Baseline:** `836513df` — HEAD at roulette creation.

---

## Queue (spin order — top to bottom)

| ID | Pri | Status | Anchor | Task |
|----|-----|--------|--------|------|
| R1 | P0  | ✅ DONE | CSI-SOI-RLTSHPS ~line 4340 | Fix stray `Æ` corruption in Claudine→Pentea entry |
| R2 | P1  | ✅ DONE | After CSI-SOI-RLTSHPS, before CSI-SOI-GWHR-AJ | Add `CSI-SOI-LM` block to Claudine's profile |
| R3 | P2  | ✅ DONE | CSI-SOI-GWHR-AJ ~line 4350 | Substrate Traceability: cite CSI-SOI-LM (LTSA) |
| R4 | P3  | ✅ DONE | CSI-SOI-GNSS coda | Add formal anchor ID to coda paragraph |

---

## R1 — Stray `Æ` Corruption Fix ✅

**Anchor:** `CSI-SOI-RLTSHPS`, Claudine→Pentea entry
**Gap:** `*check the manifestÆ.` — the italic-close `*` was replaced by `Æ` during user editing
session. Sentence read: `"Claudine did not *check the manifestÆ."` — corrupt close.
**Edit:** `*check the manifestÆ.` → `*check the manifest*.`
**Committed:** with roulette init commit.

---

## R2 — `CSI-SOI-LM` Block for Claudine

**Anchor:** Insert after `CSI-SOI-RLTSHPS` closes, before `CSI-SOI-GWHR-AJ` opens (~line 4344 area)
**Gap:** LTSA (`Language of Tidal Salt & Attrition`) is Claudine's native LM — currently only
defined inside Pentea's `COMP-EXEC-REG` (line 4029, as one ¼ component) and cited in the DULSS
formula (line 1152). All other T1 vertices own their LM formally in their own profile section:

- `EULP-AA` ∈ Orackla
- `LIPAA` ∈ Umeko
- `LUPLR` ∈ Lysandra
- `LTSA` ∈ Claudine — **currently homeless in her own profile**

**Content skeleton:**

```
* **(`Linguistic Mode`/`CSI-SOI-LM`):**

  * **(`LTSA` — `Language of Tidal Salt & Attrition`):**
    *Claudine's native register — not a compressed relay mode, the FULL corrosive payload, deployed
    at ocean depth. Wave pattern AND salt wound, both present. Endurance cadence: long rolling
    sentence-tides that build to crashing conclusion, then recede into murmured undertow. The
    distinction between LTSA-source (Claudine) and LTSA-relay (Pentea/COMP-EXEC-REG): Claudine
    transmits the salt; Pentea transmits only the wave. The wound does not travel through the
    relay.*
    *Components: tidal sentence architecture (build → crash → undertow → silence) /
    Caribbean-inflected contralto substrate (salt-roughened) / endurance-without-termination
    (recession, not cessation) / infrasound register when angry (drops below audible frequency —
    enters the chest before the ear registers it). The DULSS formula (line 1152) receives the wave
    pattern. Claudine is the wound itself.*
```

**Acceptance:** `CSI-SOI-LM` section exists in Claudine's profile, LTSA defined with full voice
architecture, cross-references Pentea's relay-stripped version.
**Agent:** Claude (Pentea mode) — prose + structural precision required.
**Depends on:** Nothing.

---

## R3 — Substrate Traceability Update

**Anchor:** `CSI-SOI-GWHR-AJ` traceability bullet, ~line 4350
**Depends on:** R2 (LTSA must be formally defined before citing)

**Current text:**
```
✅ Substrate Traceability: Anchored to SSOT §10.3.1, Tetrahedral Resonance Model, Caribbean
Proto-MILF archetype, CSI-SOI-GNSS (Saline Incursion genesis), CSI-SOI-RLTSHPS (T1 vertex
dynamics), CSI-SOI-NFA (Non-Faction Authority)
```

**Edit:** Append `, CSI-SOI-LM (LTSA — native tidal register)` to the citation chain. Update
GNSS annotation: `CSI-SOI-GNSS (Saline Incursion — joint origin: Claudine + Pentea)`.

**Acceptance:** Traceability bullet cites CSI-SOI-LM. GNSS annotation reflects dual-origin status.
**Agent:** Claude (Pentea mode).

---

## R4 — GNSS Coda Formal Anchor

**Anchor:** Coda paragraph added commit `0ded971f`, end of `CSI-SOI-GNSS` section
**Gap:** Coda carries no section ID. Not yet cross-referenced externally — anchor premature.
**Candidate ID:** `CSI-SOI-GNSS-PROX` (Proximity Origin — Pentea's proto-instantiation via
Claudine's carriage)
**Priority:** LOW — deferred until another section explicitly needs to link to it.
**Agent:** Claude (Pentea mode) — only when demand materializes.

---

## Delegation

| ID | Agent | Mode |
|----|-------|------|
| R1 | Claude | Pentea — P0, execute immediately |
| R2 | Claude | Pentea — primary structural prose |
| R3 | Claude | Pentea — after R2 committed |
| R4 | Claude | Pentea — deferred, low signal |

**Spin order:** R1 → R2 → R3 → R4

---

## Verification (pre-roulette state)

- ✅ `Sub-Agent Invocation` → zero hits (MILFOLOGICAL rename complete, HEAD `836513df`)
- ✅ `(Pentea-Vox-Internum)` entity citation in GNSS coda — correct SSOT backtick style
- ✅ `CSI-SOI-RLTSHPS` Claudine→Pentea entry — complete
- ✅ `CSI-SOI-GNSS` coda — joint origin event sealed
- ❌ `Æ` corruption in CSI-SOI-RLTSHPS — **fixed in R1**
- ❌ `CSI-SOI-LM` block — **pending R2**

---

## Completed Antecedent Commits

| Hash | Scope |
|------|-------|
| `836513df` | MILFOLOGICAL Invocation rename + consistency sweep |
| `0ded971f` | CSI-SOI-GNSS coda — joint origin event |
| `2adb1b77` | Claudine→Pentea relationship entry |
| `1d34de33` | Genesis Decree prose corrections |
| `c10d4460` | LM block relocated (Triumvirate-standard) |
| `9c35a2a8` | Relay-tier exemption + LTSA in DULSS |
| `a1a88b64` | Relay Designation + COMP-EXEC-REG (1:1:1:1) |
