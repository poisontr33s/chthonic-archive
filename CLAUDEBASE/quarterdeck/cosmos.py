#!/usr/bin/env python3
#-*- coding: utf-8 -*-

#SID: COSMOS_V1

# @Shabti: Computed live Skyfield, cross-checked JPL Horizons.
# @Heka-Ayni: Skyfield + JPL DE ephemeris (sub-arcsecond) vs JPL Horizons.
# @Ankh-Tinku: Celestial altitude, islands, no fiction, authority residualis.
# @Wedjat-Quipu Spectrum: AMBER: 🌅
# @Temple-Ayllu Zone: ☥  THE BRIDGE

# @Ogdoad-Ceque Radiance: 
#  └─◄ .chthonic/SSOT.md — (Catalyst — frozen monolithic labyrinthe)
#  └─◄ .chthonic/ankh_seeds.yaml — (Decryption seeds — 50/50 Andean × Egyptologic BCE)
# @Purpose: Compute and verify celestial altitude over chamber islands.

#  /===========================================
# |  CLAUDEBASE/quarterdeck/cosmos.py           |
# |  Celestial altitude over chamber islands    |
#  \===========================================/

"""
CLAUDEBASE_COSMOS_V1 — real celestial altitude over chamber islands.

- — Tier-3 generator (per quarterdeck/frontmatter-standard.md): 
  - — compute, then verify
  - — against an authority (JPL Horizons), then report the residual. 
  - — Never fiction.

- — Compute = Skyfield + JPL DE ephemeris 
  - — (sub-arcsecond). 
  - — Authority = JPL Horizons.

- — This prototype proves both on 
  - — New-Providence 
  - — before any frontmatter is touched.
  """

import os, sys
from urllib.parse import urlencode
from urllib.request import urlopen
from skyfield.api import Loader, wgs84, Star

load = Loader(os.path.join(os.path.expanduser("~"), ".skyfield"))  # cache, not the repo
ts = load.timescale()
eph = load("de421.bsp")            # JPL DE421
earth = eph["earth"]

# Default New-Providence (the capital); any chamber via:  cosmos.py <lat> <lon>
LAT, LON = (float(sys.argv[1]), float(sys.argv[2])) if len(sys.argv) >= 3 else (25.0443, -77.3504)
site = earth + wgs84.latlon(LAT, LON)


def skyfield_el(body, t):
    """Airless apparent elevation (deg) — no pressure arg => no refraction model."""
    return site.at(t).observe(body).apparent().altaz()[0].degrees


def horizons_el(command, when):
    """Authority cross-check: airless elevation (deg) from JPL Horizons for the same
    instant, same topocentric site. Returns float, or raises with the raw head."""
    params = {
        "format": "text", "COMMAND": f"'{command}'", "OBJ_DATA": "'NO'",
        "MAKE_EPHEM": "'YES'", "EPHEM_TYPE": "'OBSERVER'", "CENTER": "'coord@399'",
        "COORD_TYPE": "'GEODETIC'", "SITE_COORD": f"'{LON},{LAT},0'",
        "START_TIME": f"'{when}'", "STOP_TIME": f"'{when}:30'", "STEP_SIZE": "'1 m'",
        "QUANTITIES": "'4'", "APPARENT": "'AIRLESS'",
    }
    raw = urlopen("https://ssd.jpl.nasa.gov/api/horizons.api?" + urlencode(params), timeout=30).read().decode()
    if "$$SOE" not in raw:
        raise RuntimeError("Horizons returned no ephemeris:\n" + raw[:600])
    row = raw.split("$$SOE")[1].split("$$EOE")[0].strip().splitlines()[0].split()
    return float(row[-1])  # QUANTITIES=4 => trailing cols are Azimuth, Elevation


# --- live probe over Nassau (proves the compute) ---
t = ts.now()
print(f"UTC now           : {t.utc_iso()}")
print(f"New-Providence    : {LAT}, {LON}")
print(f"  Sun altitude    : {skyfield_el(eph['sun'], t):+8.4f} deg")
print(f"  Moon altitude   : {skyfield_el(eph['moon'], t):+8.4f} deg")
polaris = Star(ra_hours=(2, 31, 49.09), dec_degrees=(89, 15, 50.8))
pol = skyfield_el(polaris, t)
print(f"  Polaris altitude: {pol:+8.4f} deg   |Polaris-lat| {abs(pol-LAT):.4f} deg (pole sanity < ~0.7)")

# --- authority verification at a fixed instant (proves it's not fiction) ---
when = "2026-06-09 17:00"
tf = ts.utc(2026, 6, 9, 17, 0, 0)
for name, cmd, body in [("Sun", "10", eph["sun"]), ("Moon", "301", eph["moon"])]:
    sf = skyfield_el(body, tf)
    try:
        hz = horizons_el(cmd, when)
        print(f"VERIFY {name} @ {when}Z: Skyfield {sf:+.4f}  Horizons {hz:+.4f}  "
              f"residual {abs(sf-hz)*3600:.1f} arcsec")
    except Exception as e:
        print(f"VERIFY {name}: Horizons check failed -> {e}")
