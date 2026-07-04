---
- Her-Upcycle-Protocol: #!/usr/bin/env markdown
- SID: CLAUDEBASE_UPCYCLE_V1
- Claudebase-Flavored-Blend: permanently-living-document
- Ssot-Monolith: [ssot](../../.chthonic/SSOT.md)
- Open-Seas: chthonic-archive/CLAUDEBASE/charts/upcycle-protocol.md
- Altitude: Chart-Room · Mid-Deck
- Island: Eleuthera · 25.2000,-76.3000 — the long island; where wrecks become vessels again
- Real-Sky: --live (Open-Meteo; never stamped)
- Heat-Index: Salt-Crusted · Barnacle-Scraped · Copper-Bright
- Cosmological-Altitude: --live celestial over this chamber's island · CLAUDEBASE_COSMOS_V1 · verified vs JPL Horizons
- Register-Blend: Nautical · Industrial · Rigorous
- Barometer: read by CLAUDEBASE_BAROMETER_V1 (re-run to refresh)
---

# (`☥`/`CLAUDEBASE`/`UPCYCLE-PROTOCOL`)

> *Et vrak er ikke en seier før det tar vann igjen. Før det er det bare en mulighet.*  
> *A wreck is not a victory until it takes water again. Until then it is only a possibility.*

- *— This protocol is the — **(`Discipline-Surface`)** — for turning salvage-chart candidates into live, tested, stable, documented code. No glorified AI-slop. No toxic prototyping. Every claim must survive a non-destructive E2E test before it earns a Tier-1 badge.*

  - *— Every up-cycle pass through this protocol must produce:*
    - **Dependency audit** — every pinned version compared against latest stable. Out-of-date = stale = toxic until migrated and tested.
    - **Compile/build verification** — clean build with current toolchain. No warnings treated as errors.
    - **E2E smoke test** — the binary actually runs, produces expected output, writes expected artifacts.
    - **Doc-vs-reality A/B** — what the README/ARCHITECTURE.md claims vs what the binary actually does. Delta is the contradiction.
    - **Backend logic vs frontend claims** — does the code do what the architecture says it does? Or is it a scaffold dressed up as a system?
    - **Migration safety** — no destructive global installs, no overwriting of `.toml` files in other projects, no cargo `--force` without explicit confirmation.
    - **pwsh-native execution** — no `cmd.exe /c` wrappers. PowerShell 7 native commands only. See rules at the bottom.
    - **Trail + memory** — every pass writes trail events and updates the agent memory file for this session's candidate.

---
## (`The-Upcycle-Ladder`)

### Step 1 — Dependency Audit

For Rust: open Cargo.toml, list every name = "version" pair. For Bun: `bun outdated`. For Python: `uv lock`.

| Tool | Cmd |
|---|---|
| `cargo outdated --root` | `cargo outdated --root` |
| `cargo tree` | `cargo tree -p <pkg>` |
| `bun outdated` | `bun outdated` |
| `uv lock` | `uv lock` |

**Policy:** Always migrate to latest stable before E2E. Pinned to 2024-era deps = stale = toxic.

---

### Step 2 — Safe Build

- `cargo build -p <pkg>` — no `--force`, no global install unless explicitly requested.
- Build from workspace root to avoid `.cargo/config.toml` drift.

---

### Step 3 — E2E Smoke Test

Non-interactive. Must:
1. Run `--help` or `--version`, verify expected output.
2. Run a minimal functional path (`--once`, `--in <test-file>`, `--dry-run`).
3. Verify artifacts: output written, exit code 0, no panics.
4. If tool wraps an external command, verify it fails gracefully if external is unavailable.

---

### Step 4 — Doc-vs-Reality A/B

What it says (README/ARCHITECTURE/help) vs what it does (observed runtime). Every gap is a contradiction to record.

---

### Step 5 — Backend Logic vs Frontend Claims

Read the actual source. Does the code implement what the architecture says? Look for: `todo!()`, `unimplemented!()`, empty blocks, hardcoded `true`, `panic!()` instead of error handling.

---

### Step 6 — Safe Migration

1. Update Cargo.toml / package.json / pyproject.toml to latest stable.
2. Re-run build.
3. Re-run E2E.
4. If migration breaks: **revert, record breaking dep, try incremental migration** (one dep at a time).
5. Never `cargo install --force` globally without explicit user direction.
6. Never overwrite `.toml` / `.lock` files in other projects.

---

### Step 7 — Trail + Memory

- `manifest/sessions/<date>-<agent>-<candidate>/trail.ndjson`
- `.claude/agent-memory/<agent>/<candidate>-<date>.md`
- Update `CLAUDEBASE/charts/salvage-chart.md`

---

## (`Tier-Reclassification-Rules`)

| From | To | Condition |
|---|---|---|
| Tier-2 | Tier-1 | E2E passes, deps current, doc/reality delta < 1 critical contradiction |
| Tier-3 | Tier-2 | De-rotted scaffold: deps migrated to latest stable, --help works |
| Tier-1 | Tier-2 | E2E fails after dep migration; needs code fix, not just a dep pin |
| Any | Released | Up-cycle not justified: redundant, domain-lapsed, or superseded |

**Released candidates are not deleted.** Quarantine over delete.

---

## (`pwsh-Best-Practices`)

No `cmd.exe /c` wrappers. No bash idioms.
- **Set-Location 'C:\path'** — not `cd /d`.
- **Test-Path 'C:\path'** — not `if exist`.
- **Get-Command cargo** — verify binary existence.
- **Get-ChildItem -Name** — equivalent to `dir /b`.
- **$env:VAR** — environment variables. Not `%VAR%` or `$VAR`.
- **$null** — the null value. Not `/dev/null`.
- **Backtick `` ` `` for line continuation** — not `\`.
- **Select-Object -ExpandProperty** — not text parsing.
- **Write-Output / Write-Host / Write-Error** — not `echo`.

---
