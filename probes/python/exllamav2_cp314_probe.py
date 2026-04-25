#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SID: PROBE-P03-EXLLAMAV2-CP314-EXISTENCE
# Gate: exllamav2/cp314_wheel
# FAF artifact type: impossible_currently_boundary (existence check)
# Run: python probes/python/exllamav2_cp314_probe.py  (no uv extra — stdlib only)
# Output: stdout (JSON)
#
# Does NOT attempt installation. Interrogates GitHub release API only.
import json
import sys
import time
import urllib.error
import urllib.request

REPOS = [
    {
        "gate": "exllamav2/cp314_wheel",
        "owner": "turboderp-org",
        "repo": "exllamav2",
        "cp_tag": "cp314",
        "upstream_dependency": "turboderp-org/exllamav2 release with cp314-cp314-win_amd64 wheel",
    },
    {
        "gate": "exllamav3/cp314_wheel",
        "owner": "turboderp-org",
        "repo": "exllamav3",
        "cp_tag": "cp314",
        "upstream_dependency": "turboderp-org/exllamav3 release with cp314 wheel + loosened pydantic pin",
    },
    {
        "gate": "flash_attn/cp314_wheel",
        "owner": "kingbri1",
        "repo": "flash-attention",
        "cp_tag": "cp314",
        "upstream_dependency": "kingbri1/flash-attention release with cp314-cp314-win_amd64 wheel",
    },
]

results = []

for spec in REPOS:
    url = f"https://api.github.com/repos/{spec['owner']}/{spec['repo']}/releases/latest"
    record = {
        "gate": spec["gate"],
        "artifact_type": "impossible_currently_boundary",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "queried_repo": f"{spec['owner']}/{spec['repo']}",
    }
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            release = json.loads(r.read())
        record["release_tag"] = release.get("tag_name", "unknown")
        record["release_published"] = release.get("published_at", "unknown")
        assets = [a["name"] for a in release.get("assets", [])]
        cp_wheels = [a for a in assets if spec["cp_tag"] in a]
        record["all_asset_count"] = len(assets)
        record["cp314_wheels_found"] = cp_wheels
        if cp_wheels:
            record["status"] = "admitted"
            record["level"] = "L1_loadable_candidate"
            record["note"] = f"cp314 wheel found — existence gate OPEN, install not yet probed"
        else:
            # Report highest cpXXX tag found
            import re
            cp_tags = sorted({m.group() for a in assets for m in [re.search(r'cp3\d\d', a)] if m})
            record["highest_cp_tag"] = cp_tags[-1] if cp_tags else "none_found"
            record["status"] = "blocked_not_closed"
            record["level"] = "L0_known_absent"
            record["minimum_condition_to_reopen"] = (
                f"cp314 wheel appears in {spec['owner']}/{spec['repo']} release assets"
            )
            record["upstream_dependency"] = spec["upstream_dependency"]
    except urllib.error.HTTPError as exc:
        record["status"] = "probe_failed"
        record["error"] = f"HTTP {exc.code}: {exc.reason}"
    except Exception as exc:  # noqa: BLE001
        record["status"] = "probe_failed"
        record["error"] = str(exc)

    results.append(record)
    print(json.dumps(record, indent=2))
    print()

# Summary
print("--- SUMMARY ---", file=sys.stderr)
for r in results:
    icon = "✅" if r.get("status") == "admitted" else "❌"
    tag = r.get("release_tag", "?")
    highest = r.get("highest_cp_tag", r.get("cp314_wheels_found", "?"))
    print(f"  {icon}  {r['gate']:40s}  release={tag:12s}  highest={highest}", file=sys.stderr)
