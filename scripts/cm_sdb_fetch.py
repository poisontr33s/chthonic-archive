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

# Static ARCO Zarr URI — from copernicusmarine.describe(dataset_id=DATASET_ID)
# Retrieved 2026-06-27. Update if the dataset version suffix changes.
_ZARR_URI = (
    "https://s3.waw3-1.cloudferro.com/mdl-arco-time-003/arco/"
    "BATHYMETRY_GLO_PHY_COASTAL_L4_MY_016_001/"
    "cmems_obs-sdb_glo_phy_comp_my_100m-l4-s2_static_202511/static.zarr"
)


def probe_zarr(bbox: tuple[float, float, float, float] | None) -> int:
    """Diagnostic probe: test anonymous direct Zarr access. Does not write any files."""
    import urllib.request, urllib.error

    results: dict = {
        "zarr_uri": _ZARR_URI,
        "direct_zarr_uri_reachable": "unknown",
        "anonymous_access_works": "unknown",
        "dataset_opens": "unknown",
        "height_variable_present": "unknown",
        "bbox_subset_readable": "unknown",
        "credentials_used": False,
    }

    # Step 1: reachability — fetch .zmetadata (lightweight catalogue file)
    meta_url = _ZARR_URI + "/.zmetadata"
    try:
        with urllib.request.urlopen(meta_url, timeout=15) as resp:
            code = resp.getcode()
            results["direct_zarr_uri_reachable"] = f"yes (HTTP {code})"
            results["anonymous_access_works"] = "yes"
    except urllib.error.HTTPError as e:
        results["direct_zarr_uri_reachable"] = f"no (HTTP {e.code})"
        results["anonymous_access_works"] = "no (auth required)" if e.code in (401, 403) else f"no (HTTP {e.code})"
    except Exception as e:
        results["direct_zarr_uri_reachable"] = f"no ({e})"
        results["anonymous_access_works"] = f"no ({e})"

    if "yes" not in results["anonymous_access_works"]:
        _print_probe(results)
        return 0

    # Step 2: read .zmetadata (Zarr v2 consolidated) directly via urllib.
    # Avoids zarr library trying zarr.json (v3) which returns 403 on this store.
    zmeta_url = _ZARR_URI + "/.zmetadata"
    try:
        with urllib.request.urlopen(zmeta_url, timeout=15) as r:
            zmeta = json.loads(r.read().decode("utf-8"))
        results["dataset_opens"] = "yes (via .zmetadata)"
        meta = zmeta.get("metadata", zmeta)
        vars_found = sorted({
            k.split("/")[0] for k in meta
            if "/" in k and not k.startswith(".") and not k.endswith(".zattrs")
        })
        results["height_variable_present"] = (
            "yes" if "height" in vars_found
            else f"no (top-level vars: {vars_found[:8]})"
        )
        lat_info = meta.get("latitude/.zattrs") or meta.get(".zattrs", {}).get("latitude")
        lon_info = meta.get("longitude/.zattrs") or meta.get(".zattrs", {}).get("longitude")
        if lat_info:
            results["coord_latitude"] = str(lat_info)[:120]
        if lon_info:
            results["coord_longitude"] = str(lon_info)[:120]
    except Exception as e:
        results["dataset_opens"] = f"no ({e})"
        _print_probe(results)
        return 0

    # Step 3: bbox chunk probe — attempt a raw data chunk to determine if data plane is public
    if "yes" in results.get("height_variable_present", ""):
        try:
            chunk_url = _ZARR_URI + "/height/0.0"
            with urllib.request.urlopen(chunk_url, timeout=15) as r:
                chunk_bytes = len(r.read())
            results["bbox_subset_readable"] = f"yes — data plane is public (chunk 0.0: {chunk_bytes} bytes)"
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                results["bbox_subset_readable"] = (
                    f"no — data plane is auth-gated (chunk 0.0: HTTP {e.code}); "
                    "metadata plane is public, data chunks require credentials"
                )
            else:
                results["bbox_subset_readable"] = f"no (chunk 0.0: HTTP {e.code})"
        except Exception as e:
            results["bbox_subset_readable"] = f"no (chunk 0.0: {e})"

    _print_probe(results)
    return 0


def _print_probe(results: dict) -> None:
    print("\n=== Copernicus Marine Direct Zarr Probe ===")
    for k, v in results.items():
        print(f"  {k}: {v}")
    print("===========================================\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch Copernicus Marine SDB subset.")
    parser.add_argument("--probe-direct-zarr", action="store_true",
                        help="Diagnostic-only: test anonymous direct Zarr access. No files written.")
    parser.add_argument("--bbox", nargs=4, type=float,
                        metavar=("MIN_LON", "MIN_LAT", "MAX_LON", "MAX_LAT"))
    parser.add_argument("--width", type=int, default=400)
    parser.add_argument("--height", type=int, default=300)
    parser.add_argument("--out", help="Output JSON path (required unless --probe-direct-zarr)")
    args = parser.parse_args()

    # Probe mode: diagnostic only, no files written, no credentials required
    if args.probe_direct_zarr:
        bbox = tuple(args.bbox) if args.bbox else None
        return probe_zarr(bbox)

    # Normal fetch mode: --bbox and --out are required
    if not args.bbox:
        parser.error("--bbox is required for fetch mode")
    if not args.out:
        parser.error("--out is required for fetch mode")

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
