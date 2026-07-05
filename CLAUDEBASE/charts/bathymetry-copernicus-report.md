# Copernicus Marine SDB — Comparison Report

Generated: 2026-07-05T09:42:40.250Z

## Copernicus Candidate
- Source: `cmems_obs-sdb_glo_phy_comp_my_100m-l4-s2_static`
- Grid: 400×300 = 120000 cells
- Valid: 26508 / 120000 (22.1%)
- NaN: 93492
- Range: -27.59 .. 0.02 m
- Shallow (0–30 m): 26504 cells
- Land (>0 m): 4
- Sign convention: positive-up (standard_name=height) — matches NOAA/GMRT

## Production Composite (NOAA+GMRT)
- Source: composite:noaa+gmrt
- Valid: 120000 / 120000
- Range: -5680 .. 834 m

## Fused Candidate (Copernicus > NOAA+GMRT)
- Valid: 120000 / 120000 (100.0%)
- Copernicus cells used: 26508 (22.1%)
- Copernicus overrides production: 26508 cells
- Production fallback cells: 93492

## Assessment
- Copernicus SDB coverage at Nassau/Bahamas bbox: **22.1%**
- Promote to production only after visual smoke confirmation.

## Files
- `charts/bathymetry-copernicus.json` — Copernicus-only grid
- `charts/bathymetry-copernicus-composite.json` — Fused candidate
- `charts/bathymetry.json` — Production (NOAA+GMRT composite, unchanged)