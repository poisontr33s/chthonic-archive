#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P-09 — tabby-modern import gate probe.
FAF Gate: apps/tabby-modern/ package imports cleanly on Python 3.14 in container.
Manifest: /workspace/manifest/tabby_modern_import_gate.json
Exit codes: 0=pass, 1=fail.
"""

import importlib
import json
import pathlib
import sys
import traceback
from datetime import datetime, timezone

MANIFEST_DIR = pathlib.Path("/workspace/manifest")
MANIFEST_OUT = MANIFEST_DIR / "tabby_modern_import_gate.json"

MODULES_UNDER_TEST = [
    "tabby_modern",
    "tabby_modern.settings",
    "tabby_modern.state",
    "tabby_modern.sampler",
    "tabby_modern.app",
    "tabby_modern.api.health",
    "tabby_modern.api.models",
    "tabby_modern.api.completions",
    "tabby_modern.api.chat",
]


def run() -> dict:
    results = {}
    all_pass = True

    for mod in MODULES_UNDER_TEST:
        try:
            importlib.import_module(mod)
            results[mod] = "PASS"
        except Exception:
            results[mod] = f"FAIL: {traceback.format_exc(limit=3)}"
            all_pass = False

    # Verify Settings instantiation (does not require exllamav3)
    settings_ok = "SKIP"
    try:
        from tabby_modern.settings import Settings
        s = Settings()
        settings_ok = f"OK: host={s.network.host} port={s.network.port}"
    except Exception:
        settings_ok = f"FAIL: {traceback.format_exc(limit=3)}"
        all_pass = False

    # Verify FastAPI app creation (does not require exllamav3)
    app_ok = "SKIP"
    try:
        from tabby_modern.app import create_app
        app = create_app()
        routes = [r.path for r in app.routes]  # type: ignore[union-attr]
        app_ok = f"OK: {len(routes)} routes ({', '.join(routes[:4])}{'...' if len(routes) > 4 else ''})"
    except Exception:
        app_ok = f"FAIL: {traceback.format_exc(limit=3)}"
        all_pass = False

    return {
        "probe_id": "P-09",
        "gate": "tabby-modern/import_gate",
        "python_version": sys.version.split()[0],
        "substrate": sys.platform,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "module_imports": results,
        "settings_check": settings_ok,
        "app_factory_check": app_ok,
        "status": "admitted_import_gate" if all_pass else "failed_import_gate",
        "level": "L1" if all_pass else "L0_blocked",
    }


def main() -> None:
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    result = run()
    MANIFEST_OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(json.dumps(result, indent=2))

    if result["status"] != "admitted_import_gate":
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
