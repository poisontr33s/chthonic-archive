#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: cm_sdb_fetch.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
scripts/cm_sdb_fetch.py — Copernicus Marine SDB fetch + resample for barometer.ts.

Subsets the Copernicus Marine global coastal SDB product (Sentinel-2 derived
bathymetry, 100 m class) for the Nassau/Bahama Banks bbox and resamples to a
target W×H grid. Writes bathymetry-copernicus.json and exits.

  Exit 0  — success, JSON written
  Exit 1  — fetch/resample failed (auth OK, data error)
  Exit 2  — copernicusmarine package not available
  Exit 3  — credentials not configured

Usage (called by barometer.ts):
  uv run --with copernicusmarine python scripts/cm_sdb_fetch.py \\
    --bbox MIN_LON MIN_LAT MAX_LON MAX_LAT \\
    --width 400 --height 300 \\
    --out charts/bathymetry-copernicus.json

Credentials checked in priority order:
  1. COPERNICUSMARINE_SERVICE_USERNAME / COPERNICUSMARINE_SERVICE_PASSWORD
  2. CMEMS_USER / CMEMS_PASS (aliases)
  3. ~/.copernicusmarine/.copernicusmarine-credentials  (from: copernicusmarine login)

@SID:           SCRIPT_CM_SDB_FETCH_V1
@Shabti:        CLI Script
@Purpose:       scripts/cm_sdb_fetch.py — Copernicus Marine SDB fetch + resample for barometer.ts.
"""

# @SID: SCRIPT_CM_SDB_FETCH_V1

import argparse, datetime, json, os, sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch Copernicus Marine SDB subset.")
    parser.add_argument("--bbox", nargs=4, type=float,
                        metavar=("MIN_LON", "MIN_LAT", "MAX_LON", "MAX_LAT"), required=True)
    parser.add_argument("--width", type=int, default=400)
    parser.add_argument("--height", type=int, default=300)
    parser.add_argument("--out", required=True, help="Output JSON path")
    args = parser.parse_args()

    min_lon, min_lat, max_lon, max_lat = args.bbox
    W, H = args.width, args.height

    try:
        import copernicusmarine as cm
    except ImportError:
        print("ERROR: copernicusmarine package not found.", file=sys.stderr)
        print("  Install: uv add copernicusmarine", file=sys.stderr)
        return 2

    import numpy as np  # transitive dep of copernicusmarine
    import xarray as xr  # transitive dep of copernicusmarine

    # Credential resolution
    user = (os.environ.get("COPERNICUSMARINE_SERVICE_USERNAME")
            or os.environ.get("CMEMS_USER") or "")
    pwd = (os.environ.get("COPERNICUSMARINE_SERVICE_PASSWORD")
           or os.environ.get("CMEMS_PASS") or "")
    cred_file = Path.home() / ".copernicusmarine" / ".copernicusmarine-credentials"
    has_env = bool(user and pwd)
    has_file = cred_file.exists()

    if not has_env and not has_file:
        print("ERROR: Copernicus Marine credentials not configured.", file=sys.stderr)
        print("  Register free at https://marine.copernicus.eu", file=sys.stderr)
        print("  Then run: uv run --with copernicusmarine python -m copernicusmarine login", file=sys.stderr)
        print("  Or set env vars: CMEMS_USER + CMEMS_PASS", file=sys.stderr)
        return 3

    DATASET_ID = "cmems_obs-sdb_glo_phy_comp_my_100m-l4-s2_static"
    VARIABLE = "height"  # standard_name='height', units='m', positive-up

    print(f"  CM-SDB open_dataset: bbox {min_lon:.3f},{min_lat:.3f} → {max_lon:.3f},{max_lat:.3f} ...",
          file=sys.stderr)
    try:
        kwargs: dict = dict(
            dataset_id=DATASET_ID,
            variables=[VARIABLE],
            minimum_longitude=min_lon,
            maximum_longitude=max_lon,
            minimum_latitude=min_lat,
            maximum_latitude=max_lat,
        )
        if has_env:
            kwargs["username"] = user
            kwargs["password"] = pwd
        # has_file: library reads ~/.copernicusmarine/.copernicusmarine-credentials automatically

        ds = cm.open_dataset(**kwargs)
        h = ds[VARIABLE]
        print(f"  CM-SDB opened: shape={dict(h.sizes)}  computing ...", file=sys.stderr)
        h_arr = h.compute()

    except Exception as exc:
        msg = str(exc).lower()
        if any(k in msg for k in ("auth", "credential", "401", "403", "forbidden",
                                   "unauthorized", "login", "password")):
            print(f"ERROR: Copernicus Marine authentication failed: {exc}", file=sys.stderr)
        elif any(k in msg for k in ("not found", "404", "dataset", "unavailable")):
            print(f"ERROR: Dataset not available: {exc}", file=sys.stderr)
        else:
            print(f"ERROR: Copernicus Marine fetch failed: {exc}", file=sys.stderr)
        return 1

    # Resample via two-step xarray.interp
    # Source coords: latitude (ascending -90→+90), longitude (ascending -180→+180)
    # Target: row 0 = max_lat (top), row H-1 = min_lat (bottom) — matches NOAA/GMRT
    target_lat_asc = np.linspace(min_lat, max_lat, H)
    target_lon = np.linspace(min_lon, max_lon, W)

    print(f"  CM-SDB resampling to {W}×{H} ...", file=sys.stderr)
    try:
        h1 = h_arr.interp(longitude=xr.DataArray(target_lon, dims=["col"]), method="linear")
        h2 = h1.interp(latitude=xr.DataArray(target_lat_asc, dims=["row"]), method="linear")
        arr = np.array(h2.values, dtype=float)  # shape (H, W)
        arr = arr[::-1]  # flip: row 0 = max_lat (top)
    except Exception as exc:
        print(f"ERROR: Resample failed: {exc}", file=sys.stderr)
        return 1

    depth_list: list = []
    for row in arr:
        for v in row:
            depth_list.append(None if (v != v) else float(v))

    valid = [v for v in depth_list if v is not None]
    land = [v for v in valid if v >= 0]
    shallow = [v for v in valid if -30.0 <= v < 0.0]

    out_data = {
        "_note": ("Copernicus Marine SDB candidate — NOT production. "
                  "Positive = land/elevation, negative = water depth. "
                  "Compare against bathymetry.json before promoting."),
        "source": "copernicus",
        "product": "BATHYMETRY_GLO_PHY_COASTAL_L4_MY_016_001",
        "dataset": DATASET_ID,
        "access": "copernicusmarine-toolbox",
        "variable": VARIABLE,
        "grid": {"width": W, "height": H},
        "roi": {"name": "Nassau / New Providence / Bahama Banks"},
        "units": "meters",
        "positiveDirection": "verify-and-record",
        "sourcePositiveDirection": "positive-up (standard_name=height, units=m)",
        "outputPositiveDirection": "positive-up",
        "createdAt": datetime.datetime.utcnow().isoformat() + "Z",
        "bbox": {"minLat": min_lat, "maxLat": max_lat, "minLon": min_lon, "maxLon": max_lon},
        "W": W,
        "H": H,
        "coverage": {
            "total": W * H,
            "valid": len(valid),
            "land": len(land),
            "sea": len(valid) - len(land),
            "shallow_0_30m": len(shallow),
            "nan": W * H - len(valid),
            "coverage_pct": round(100.0 * len(valid) / (W * H), 1),
        },
        "range": {
            "min": round(float(min(valid)), 2) if valid else None,
            "max": round(float(max(valid)), 2) if valid else None,
        },
        "depth": depth_list,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out_data, separators=(",", ":")))

    cov = out_data["coverage"]
    rng = out_data["range"]
    print(
        f"copernicus → {args.out}   {W}×{H} cells · "
        f"{rng['min']}..{rng['max']} m · "
        f"{cov['land']} land · {cov['sea']} sea · "
        f"{cov['coverage_pct']}% valid"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
