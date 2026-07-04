---
type: task-handoff
created: 2026-06-27
gate: credentials-required
commits: 739e54c8 (plumbing) · ed298dde (probe)
status: parked-until-credentials
---

# Copernicus Marine SDB E2E Activation Task

## Current State (do not re-derive)

```
production bathymetry.json = NOAA+GMRT composite (42.7% GMRT overlay, 400×300)
Copernicus plumbing         = 739e54c8 ✓ pushed
direct-Zarr probe           = ed298dde ✓ pushed
metadata plane              = public (.zmetadata HTTP 200, height var confirmed)
data plane                  = auth-gated (height/0.0 chunk → HTTP 403)
E2E fetch                   = blocked — no credentials on this machine
```

No env vars, no stored login, no API-pool Copernicus keys exist. This task activates once credentials are configured.

## Step 0: Credential setup (one path only)

**Preferred — stored login:**
```powershell
cd "C:\Users\eldno\chthonic-archive"
uv run --with copernicusmarine python -m copernicusmarine login
```

**Alternative — session env vars:**
```powershell
$env:CMEMS_USER="YOUR_USERNAME"
$env:CMEMS_PASS="YOUR_PASSWORD"
```

**Verify (no values printed):**
```powershell
@("CMEMS_USER","CMEMS_PASS","COPERNICUSMARINE_SERVICE_USERNAME","COPERNICUSMARINE_SERVICE_PASSWORD") |
  ForEach-Object { $v = [System.Environment]::GetEnvironmentVariable($_); "$_ = $(if ($v) { 'SET' } else { 'MISSING' })" }
Test-Path "$env:USERPROFILE\.copernicusmarine\.copernicusmarine-credentials"
```

## Step 1: E2E fetch

```powershell
cd "C:\Users\eldno\chthonic-archive"
bun run CLAUDEBASE/quarterdeck/barometer.ts --bathymetry --bathymetry-source=copernicus
```

Expected outputs (NOT production):
- `CLAUDEBASE/charts/bathymetry-copernicus.json`
- `CLAUDEBASE/charts/bathymetry-copernicus-composite.json`
- `CLAUDEBASE/charts/bathymetry-copernicus-report.md`

Production must be unchanged:
```powershell
git diff -- CLAUDEBASE/charts/bathymetry.json  # expected: no diff
```

## Step 2: Candidate inspection

Read `bathymetry-copernicus-report.md`. Verify:
- coverage.coverage_pct > meaningful threshold
- shallow_0_30m count > 0 (this is the turquoise-zone signal)
- range.min plausible (should be < −5000 for Tongue of the Ocean)
- range.max plausible (should be small positive for cay tops)
- sign convention: positive = land, negative = water (matches NOAA/GMRT)
- no land/sea inversion (large positive in known-deep areas = bad)

## Step 3: Candidate smoke

```powershell
Copy-Item CLAUDEBASE/charts/bathymetry.json CLAUDEBASE/charts/bathymetry.production.backup.json
Copy-Item CLAUDEBASE/charts/bathymetry-copernicus-composite.json CLAUDEBASE/charts/bathymetry.json
pwsh -NoProfile -File scripts/render-smoke.ps1
Copy-Item CLAUDEBASE/charts/bathymetry.production.backup.json CLAUDEBASE/charts/bathymetry.json
Remove-Item CLAUDEBASE/charts/bathymetry.production.backup.json
git diff -- CLAUDEBASE/charts/bathymetry.json  # expected: no diff
```

## Step 4: Commit candidate data only

Stage only:
```
CLAUDEBASE/charts/bathymetry-copernicus.json
CLAUDEBASE/charts/bathymetry-copernicus-composite.json
CLAUDEBASE/charts/bathymetry-copernicus-report.md
CLAUDEBASE/charts/north-star-constellations.md
```

Do NOT stage: credentials, `.copernicusmarine/*`, backups, production `bathymetry.json`.

Commit message: `feat(bathymetry): add Copernicus Marine SDB candidate grid`

## Step 5: Promotion (separate commit, only if all criteria met)

Promote only if ALL true:
- fetch succeeded with real data
- shallow-water coverage meaningful
- sign convention verified
- candidate composite smoke PASS
- no land/sea inversion
- production restorable cleanly

Promotion commit message: `feat(bathymetry): promote Copernicus composite bathymetry`

**Do not fold promotion into the candidate commit.**

## Context: barometer.ts source options

```typescript
// --bathymetry-source=noaa|gmrt|composite|copernicus|legacy
```

- `composite` (current production): NOAA NCEI base + GMRT topo-mask overlay
- `copernicus` (next): Sentinel-2 SDB 100 m coastal, dataset `cmems_obs-sdb_glo_phy_comp_my_100m-l4-s2_static`

## Tool reference

```
scripts/cm_sdb_fetch.py  — Python helper called by barometer.ts
  --probe-direct-zarr    — metadata-only diagnostic (no credentials needed)
  --bbox ...             — normal fetch mode (requires credentials)
```
