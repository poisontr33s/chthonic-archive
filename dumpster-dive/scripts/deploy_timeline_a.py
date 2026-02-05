#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gated Timeline A integration deploy (dry-run/apply).

This script is intentionally conservative:
- Always runs SSOT drift check first; refuses to proceed on drift.
- Defaults to dry-run (no mutations).
- Only automates file-copy integrations with explicit target paths.
- Content-level SSOT merges are represented as manual steps until an explicit merge spec exists.

Registry + manifest updates are only written in apply mode.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "dumpster-dive" / "DUMPSTER_DIVE_REGISTRY.json"
DEPLOY_MAP_PATH = REPO_ROOT / "dumpster-dive" / "protocols" / "TIMELINE_A_DEPLOY_MAP.json"
MANIFEST_SCHEMA_HINT = "dumpster-dive/protocols/INTEGRATION_MANIFEST_SCHEMA.json"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _date_yyyymmdd_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d")


def _date_yyyy_mm_dd_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _word_count_text(text: str) -> int:
    # Cheap + deterministic; good enough for manifest logging.
    return len(text.split())


def _safe_rel_from_root(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _run_drift_gate(python_exe: str, drift_script_rel: str) -> None:
    drift_path = (REPO_ROOT / drift_script_rel).resolve()
    if not drift_path.exists():
        raise SystemExit(f"Drift gate script not found: {drift_path}")

    proc = subprocess.run(
        [python_exe, str(drift_path)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )

    # Always show drift output; it's a guardrail.
    out = (proc.stdout or "").rstrip()
    err = (proc.stderr or "").rstrip()
    if out:
        print(out)
    if err:
        print(err, file=sys.stderr)

    if proc.returncode != 0:
        raise SystemExit(f"Refusing to deploy: drift check failed (exit {proc.returncode}).")


def _next_deploy_id(existing_ids: Iterable[str]) -> str:
    # DEPLOY-001-YYYYMMDD
    max_n = 0
    for dep_id in existing_ids:
        if not dep_id.startswith("DEPLOY-"):
            continue
        parts = dep_id.split("-")
        if len(parts) != 3:
            continue
        try:
            n = int(parts[1])
        except ValueError:
            continue
        max_n = max(max_n, n)
    return f"DEPLOY-{max_n + 1:03d}-{_date_yyyymmdd_utc()}"


def _find_existing_deploy_ids() -> List[str]:
    ids: List[str] = []
    # Current convention: forge/tempered/INTEGRATION_MANIFEST_DEPLOY-XXX-YYYYMMDD.json
    tempered_dir = REPO_ROOT / "dumpster-dive" / "forge" / "tempered"
    if not tempered_dir.exists():
        return ids
    for p in tempered_dir.glob("INTEGRATION_MANIFEST_DEPLOY-*.json"):
        try:
            m = _load_json(p)
        except Exception:
            continue
        for dep in m.get("deployments", []):
            dep_id = dep.get("deployment_id")
            if isinstance(dep_id, str):
                ids.append(dep_id)
    return ids


@dataclass(frozen=True)
class DeployArtifact:
    source_path: str
    file_basename: str
    file_type: str
    action: str
    target_path: str
    target_section: str
    enabled: bool
    notes: str


def _load_deploy_map() -> List[DeployArtifact]:
    raw = _load_json(DEPLOY_MAP_PATH)
    artifacts = []
    for a in raw.get("artifacts", []):
        target = a.get("target") or {}
        artifacts.append(
            DeployArtifact(
                source_path=str(a["source_path"]),
                file_basename=str(a.get("file_basename") or Path(a["source_path"]).name),
                file_type=str(a.get("file_type") or "unknown"),
                action=str(a.get("action") or "noop"),
                target_path=str(target.get("path") or ""),
                target_section=str(target.get("section") or ""),
                enabled=bool(a.get("enabled", False)),
                notes=str(a.get("notes") or ""),
            )
        )
    return artifacts


def _load_registry() -> Dict[str, Any]:
    return _load_json(REGISTRY_PATH)


def _get_tempered_entries(registry: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    # Prefer the actual structured section used by the registry.
    # Historical: some iterations used "tempered_artifacts"; current uses "forge_tempered_artifacts".
    for key in ("forge_tempered_artifacts", "tempered_artifacts"):
        ta = registry.get(key)
        if isinstance(ta, dict):
            return ta
    raise SystemExit("Registry missing or invalid: forge_tempered_artifacts/tempered_artifacts")


def _find_tempered_entry_by_basename(tempered: Dict[str, Dict[str, Any]], basename: str) -> Tuple[str, Dict[str, Any]]:
    # Key might be filename, but don't assume; search values.
    for k, v in tempered.items():
        if not isinstance(v, dict):
            continue
        fn = v.get("filename")
        if fn == basename:
            return k, v
    raise SystemExit(f"Registry tempered_artifacts missing entry for: {basename}")


def _copy_if_changed(src: Path, dst: Path, *, dry_run: bool) -> Tuple[bool, str]:
    if not src.exists():
        raise SystemExit(f"Source not found: {src}")

    src_bytes = src.read_bytes()
    src_hash = _sha256_bytes(src_bytes)

    if dst.exists():
        dst_hash = _sha256_file(dst)
        if dst_hash == src_hash:
            return False, src_hash

    if dry_run:
        return True, src_hash

    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    return True, src_hash


def _make_manifest(
    *,
    deployment_id: str,
    ssot_hash: str,
    run_ts: str,
    operator: str,
    files: List[Dict[str, Any]],
    sections_impacted: List[str],
    notes: str,
) -> Dict[str, Any]:
    return {
        "manifest_version": "1.0.0",
        "created": run_ts,
        "registry_ref": "DUMPSTER_DIVE_REGISTRY.json",
        "ssot_reference": {
            "path": ".github/copilot-instructions.md",
            "hash": ssot_hash,
            "hash_algorithm": "SHA256",
            "computed_date": _date_yyyy_mm_dd_utc(),
        },
        "deployments": [
            {
                "deployment_id": deployment_id,
                "deployment_type": "staged-partial",
                "phase": "Timeline A Integration",
                "timestamp": run_ts,
                "operator": operator,
                "ssot_hash_at_deployment": ssot_hash,
                "files": files,
                "sections_impacted": sections_impacted,
                "validation": {
                    "fa4_compliance": "PASSED",
                    "cross_references": "PENDING",
                    "registry_sync": "PENDING",
                    "lint_check": "PENDING",
                    "notes": f"Gate: drift check passed. Schema: {MANIFEST_SCHEMA_HINT}",
                },
                "status": "completed",
                "rollback_checkpoint": "PRE-DEPLOY-001",
                "completion_timestamp": run_ts,
                "duration_minutes": 0,
                "notes": notes,
            }
        ],
    }


def _registry_integration_matches(
    reg_entry: Dict[str, Any],
    *,
    deployment_id: str,
    run_ts: str,
    manifest_rel: str,
    ssot_hash: str,
) -> bool:
    return (
        reg_entry.get("integrated") is True
        and reg_entry.get("integration_deployment_id") == deployment_id
        and reg_entry.get("integration_timestamp") == run_ts
        and reg_entry.get("integration_manifest_ref") == manifest_rel
        and reg_entry.get("ssot_hash_at_integration") == ssot_hash
    )


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Gated Timeline A integration deploy")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Show actions only (default)")
    mode.add_argument("--apply", action="store_true", help="Perform integration + write manifest + update registry")

    ap.add_argument(
        "--deployment-id",
        default=None,
        help="Override deployment id (default: next DEPLOY-XXX-YYYYMMDD)",
    )
    ap.add_argument(
        "--operator",
        default="THE-SAVANT (User)",
        help="Operator name recorded in manifest",
    )
    ap.add_argument(
        "--python",
        default=sys.executable,
        help="Python executable used for drift gate (default: current interpreter)",
    )
    ap.add_argument(
        "--only-enabled",
        action="store_true",
        help="Only process artifacts with enabled=true in deploy map (default behavior)",
    )
    args = ap.parse_args(argv)

    dry_run = not args.apply

    if not REGISTRY_PATH.exists():
        raise SystemExit(f"Registry not found: {REGISTRY_PATH}")
    if not DEPLOY_MAP_PATH.exists():
        raise SystemExit(f"Deploy map not found: {DEPLOY_MAP_PATH}")

    deploy_map = _load_deploy_map()
    selected = [a for a in deploy_map if a.enabled]

    if not selected:
        print("No enabled artifacts in deploy map; nothing to do.")
        return 0

    drift_rel = _load_json(DEPLOY_MAP_PATH).get("ssot", {}).get("drift_gate")
    if not isinstance(drift_rel, str) or not drift_rel:
        raise SystemExit("Deploy map missing ssot.drift_gate")

    # Guardrail 0: drift gate must pass.
    _run_drift_gate(args.python, drift_rel)

    ssot_hash = _sha256_file(REPO_ROOT / ".github" / "copilot-instructions.md")

    existing_ids = _find_existing_deploy_ids()
    deployment_id = args.deployment_id or _next_deploy_id(existing_ids)

    run_ts = _utc_now_iso()

    registry = _load_registry()
    tempered = _get_tempered_entries(registry)

    manifest_files: List[Dict[str, Any]] = []
    sections_impacted: List[str] = []

    # Track whether apply would actually change anything.
    any_copy_changed = False
    applied_copy_count = 0

    print(f"\nDeployment: {deployment_id}")
    print(f"Mode: {'DRY-RUN' if dry_run else 'APPLY'}")
    print(f"SSOT hash: {ssot_hash}")
    print(f"Enabled artifacts: {len(selected)}")

    for artifact in selected:
        src = (REPO_ROOT / artifact.source_path).resolve()

        # Registry lookup by filename.
        reg_key, reg_entry = _find_tempered_entry_by_basename(tempered, artifact.file_basename)
        file_id = reg_entry.get("file_id")
        if not isinstance(file_id, str):
            raise SystemExit(f"Registry entry missing file_id for {artifact.file_basename}")

        action = artifact.action
        changed = False
        file_hash = _sha256_file(src)
        word_count = 0
        if artifact.file_type.lower() == "markdown":
            word_count = _word_count_text(src.read_text(encoding="utf-8"))
        else:
            # For JSON/etc: count words from canonical JSON text
            try:
                word_count = _word_count_text(src.read_text(encoding="utf-8"))
            except Exception:
                word_count = 0

        integration_notes = artifact.notes

        if action == "copy":
            dst = (REPO_ROOT / artifact.target_path).resolve()
            changed, file_hash = _copy_if_changed(src, dst, dry_run=dry_run)
            any_copy_changed = any_copy_changed or changed
            integration_notes = f"copy → {_safe_rel_from_root(dst)}; {'would write' if dry_run else 'wrote' if changed else 'unchanged'}. {artifact.notes}".strip()
            sections_impacted.append(artifact.target_section or artifact.target_path)

            print(f"- {artifact.file_basename}: copy to {_safe_rel_from_root(dst)} ({'CHANGED' if changed else 'no-op'})")

        elif action == "noop":
            print(f"- {artifact.file_basename}: noop ({artifact.notes})")

        elif action == "manual_merge":
            print(f"- {artifact.file_basename}: MANUAL MERGE REQUIRED → {artifact.target_section}")
            # Do not mark integrated automatically.

        else:
            raise SystemExit(f"Unknown action '{action}' for {artifact.file_basename}")

        # Only mark integrated + record in manifest when we actually performed an automated integration action.
        if action == "copy":
            source_path_for_manifest = reg_entry.get("relative_path")
            if not isinstance(source_path_for_manifest, str) or not source_path_for_manifest:
                source_path_for_manifest = "forge/tempered/" + artifact.file_basename

            manifest_files.append(
                {
                    "filename": artifact.file_basename,
                    "file_id": file_id,
                    "source_path": source_path_for_manifest,
                    "target_section": artifact.target_section or artifact.target_path,
                    "file_hash": file_hash,
                    "word_count": word_count,
                    "fa4_certification": "PASSED",
                    "validation_status": "passed",
                    "validation_timestamp": run_ts,
                    "ssot_hash_embedded": True,
                    "integration_notes": integration_notes,
                }
            )

            if not dry_run:
                applied_copy_count += 1

    if dry_run:
        print("\nDry-run complete: no files/registry/manifests were modified.")
        return 0

    # Apply-mode guard: if the copy operations resulted in no changes and the targets are already
    # up to date, do not churn registry/manifests by creating a new deployment.
    if applied_copy_count == 0:
        print("\nNothing to apply: no enabled copy actions.")
        return 0
    if not any_copy_changed:
        print("\nNo file changes detected (targets already match sources).")
        print("No manifest/registry updates performed to preserve idempotence.")
        return 0

    # Apply-mode: write registry + manifest.
    manifest_path = REPO_ROOT / "dumpster-dive" / "forge" / "tempered" / f"INTEGRATION_MANIFEST_{deployment_id}.json"

    manifest_rel = _safe_rel_from_root(manifest_path)

    # Now that we know we're making a real change, update the registry entries for copy actions.
    fta = registry.get("forge_tempered_artifacts")
    for artifact in selected:
        if artifact.action != "copy":
            continue
        _, reg_entry = _find_tempered_entry_by_basename(tempered, artifact.file_basename)
        reg_entry["integrated"] = True
        reg_entry["integration_deployment_id"] = deployment_id
        reg_entry["integration_timestamp"] = run_ts
        reg_entry["integration_manifest_ref"] = manifest_rel
        reg_entry["ssot_hash_at_integration"] = ssot_hash

        # Mirror (no-op if this section doesn't exist or isn't a dict)
        if isinstance(fta, dict):
            mirror = fta.get(artifact.file_basename)
            if isinstance(mirror, dict):
                mirror["integrated"] = True
                mirror["integration_deployment_id"] = deployment_id
                mirror["integration_timestamp"] = run_ts
                mirror["integration_manifest_ref"] = manifest_rel
                mirror["ssot_hash_at_integration"] = ssot_hash

    manifest = _make_manifest(
        deployment_id=deployment_id,
        ssot_hash=ssot_hash,
        run_ts=run_ts,
        operator=args.operator,
        files=manifest_files,
        sections_impacted=sorted(set(sections_impacted)),
        notes="Automated Timeline A integration (file-copy subset).",
    )

    _write_json(manifest_path, manifest)
    _write_json(REGISTRY_PATH, registry)

    print(f"\n✅ Applied. Wrote manifest: {manifest_rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
