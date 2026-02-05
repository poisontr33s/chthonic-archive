#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Zero-mutation audit: deployment manifest ↔ registry ↔ filesystem integrity.

Checks, for a given deployment_id:
- Finds the corresponding integration manifest under dumpster-dive/forge/tempered/.
- For each deployed file entry:
  - Computes SHA256 of the source artifact bytes and compares to manifest file_hash.
  - Looks up the corresponding registry entry (forge_tempered_artifacts preferred).
  - Compares registry file_id + integration references.
  - Compares registry artifact_hash to the computed bytes hash.
  - If the deploy map indicates a copy target, also verifies the target bytes hash.

This script intentionally does not write or mutate anything.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY_PATH = REPO_ROOT / "dumpster-dive" / "DUMPSTER_DIVE_REGISTRY.json"
DEFAULT_TEMPERED_DIR = REPO_ROOT / "dumpster-dive" / "forge" / "tempered"
DEFAULT_DEPLOY_MAP_PATH = REPO_ROOT / "dumpster-dive" / "protocols" / "TIMELINE_A_DEPLOY_MAP.json"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _norm_hash(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    return value.strip().upper()


def _resolve_manifest_source(repo_root: Path, manifest_source_path: str) -> Path:
    # Historical convention in manifests: "forge/tempered/<file>" (relative to dumpster-dive/)
    # Deploy-map convention: "dumpster-dive/forge/tempered/<file>" (repo-relative)
    # This resolver supports both.
    p = Path(manifest_source_path)
    as_posix = p.as_posix()

    if as_posix.startswith("dumpster-dive/"):
        return (repo_root / as_posix).resolve()

    if as_posix.startswith("forge/"):
        return (repo_root / "dumpster-dive" / as_posix).resolve()

    # Fallback: treat as repo-relative
    return (repo_root / as_posix).resolve()


@dataclass(frozen=True)
class DeployMapEntry:
    file_basename: str
    action: str
    source_path: str
    target_path: str
    enabled: bool


def _load_deploy_map(path: Path) -> Dict[str, DeployMapEntry]:
    raw = _load_json(path)
    out: Dict[str, DeployMapEntry] = {}
    for a in raw.get("artifacts", []):
        target = a.get("target") or {}
        entry = DeployMapEntry(
            file_basename=str(a.get("file_basename") or Path(str(a.get("source_path"))).name),
            action=str(a.get("action") or "noop"),
            source_path=str(a.get("source_path") or ""),
            target_path=str(target.get("path") or ""),
            enabled=bool(a.get("enabled", False)),
        )
        out[entry.file_basename] = entry
    return out


def _find_manifest_for_deployment(tempered_dir: Path, deployment_id: str) -> Tuple[Path, Dict[str, Any]]:
    if not tempered_dir.exists():
        raise SystemExit(f"Tempered directory not found: {tempered_dir}")

    manifests = sorted(tempered_dir.glob("INTEGRATION_MANIFEST_DEPLOY-*.json"))
    for mp in manifests:
        try:
            m = _load_json(mp)
        except Exception:
            continue
        for dep in m.get("deployments", []):
            if dep.get("deployment_id") == deployment_id:
                return mp, dep

    raise SystemExit(
        f"Deployment not found: {deployment_id}. Searched {len(manifests)} manifest(s) under {tempered_dir}"
    )


def _get_tempered_section(registry: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    for key in ("forge_tempered_artifacts", "tempered_artifacts"):
        section = registry.get(key)
        if isinstance(section, dict):
            return section
    raise SystemExit("Registry missing forge_tempered_artifacts/tempered_artifacts section")


def _index_registry_by_file_id(tempered: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for v in tempered.values():
        if not isinstance(v, dict):
            continue
        file_id = v.get("file_id")
        if isinstance(file_id, str) and file_id:
            out[file_id] = v
    return out


def _index_registry_by_filename(tempered: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for v in tempered.values():
        if not isinstance(v, dict):
            continue
        fn = v.get("filename")
        if isinstance(fn, str) and fn:
            out[fn] = v
    return out


def _format_path(repo_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root).as_posix()
    except Exception:
        return str(path)


def audit_deployment(
    *,
    deployment_id: str,
    registry_path: Path,
    deploy_map_path: Path,
    tempered_dir: Path,
) -> int:
    manifest_path, deployment = _find_manifest_for_deployment(tempered_dir, deployment_id)

    registry = _load_json(registry_path)
    tempered_section = _get_tempered_section(registry)

    by_file_id = _index_registry_by_file_id(tempered_section)
    by_filename = _index_registry_by_filename(tempered_section)

    deploy_map = _load_deploy_map(deploy_map_path) if deploy_map_path.exists() else {}

    files = deployment.get("files")
    if not isinstance(files, list) or not files:
        print(f"FAIL: deployment has no files: {deployment_id}")
        return 2

    manifest_ref_expected = _format_path(REPO_ROOT, manifest_path)

    errors: List[str] = []
    warnings: List[str] = []

    for f in files:
        if not isinstance(f, dict):
            errors.append("Invalid manifest file entry (not an object)")
            continue

        filename = f.get("filename")
        file_id = f.get("file_id")
        manifest_source = f.get("source_path")
        manifest_hash = _norm_hash(f.get("file_hash"))

        if not isinstance(filename, str) or not filename:
            errors.append("Manifest entry missing filename")
            continue
        if not isinstance(file_id, str) or not file_id:
            errors.append(f"{filename}: manifest entry missing file_id")
            continue
        if not isinstance(manifest_source, str) or not manifest_source:
            errors.append(f"{filename}: manifest entry missing source_path")
            continue
        if manifest_hash is None:
            errors.append(f"{filename}: manifest entry missing/invalid file_hash")
            continue

        src_path = _resolve_manifest_source(REPO_ROOT, manifest_source)
        if not src_path.exists():
            errors.append(f"{filename}: source missing: {_format_path(REPO_ROOT, src_path)}")
            continue

        computed_src_hash = _sha256_file(src_path)
        if computed_src_hash != manifest_hash:
            errors.append(
                f"{filename}: source hash != manifest file_hash ({computed_src_hash} != {manifest_hash})"
            )

        reg_entry = by_file_id.get(file_id) or by_filename.get(filename)
        if reg_entry is None:
            errors.append(f"{filename}: registry entry not found (file_id={file_id})")
            continue

        reg_file_id = reg_entry.get("file_id")
        if reg_file_id != file_id:
            errors.append(f"{filename}: registry file_id mismatch ({reg_file_id} != {file_id})")

        reg_manifest_ref = reg_entry.get("integration_manifest_ref")
        if isinstance(reg_manifest_ref, str) and reg_manifest_ref:
            if reg_manifest_ref.replace("\\", "/") != manifest_ref_expected:
                errors.append(
                    f"{filename}: registry integration_manifest_ref mismatch ({reg_manifest_ref} != {manifest_ref_expected})"
                )
        else:
            warnings.append(f"{filename}: registry missing integration_manifest_ref")

        reg_dep_id = reg_entry.get("integration_deployment_id")
        if reg_dep_id != deployment_id:
            errors.append(f"{filename}: registry integration_deployment_id mismatch ({reg_dep_id} != {deployment_id})")

        reg_art_hash = _norm_hash(reg_entry.get("artifact_hash"))
        if reg_art_hash is None:
            warnings.append(f"{filename}: registry missing artifact_hash")
        elif reg_art_hash != computed_src_hash:
            errors.append(
                f"{filename}: registry artifact_hash != source hash ({reg_art_hash} != {computed_src_hash})"
            )

        # Informational: content_hash is stable identity seed and may differ from current bytes.
        reg_content_hash = _norm_hash(reg_entry.get("content_hash"))
        if reg_content_hash is not None and reg_content_hash != computed_src_hash:
            warnings.append(
                f"{filename}: content_hash differs from current bytes (expected under Option B)"
            )

        # Target verification (if deploy map provides a copy target)
        dm = deploy_map.get(filename)
        if dm and dm.action == "copy" and dm.target_path:
            tgt_path = (REPO_ROOT / dm.target_path).resolve()
            if not tgt_path.exists():
                errors.append(f"{filename}: target missing: {_format_path(REPO_ROOT, tgt_path)}")
            else:
                computed_tgt_hash = _sha256_file(tgt_path)
                if computed_tgt_hash != manifest_hash:
                    errors.append(
                        f"{filename}: target hash != manifest file_hash ({computed_tgt_hash} != {manifest_hash})"
                    )
        else:
            warnings.append(f"{filename}: no copy target verification (no deploy map entry / not copy)")

    if warnings:
        print(f"WARN: {len(warnings)} issue(s)")
        for w in warnings:
            print(f"  - {w}")

    if errors:
        print(f"FAIL: {len(errors)} mismatch(es) for {deployment_id}")
        print(f"Manifest: {_format_path(REPO_ROOT, manifest_path)}")
        print(f"Registry: {_format_path(REPO_ROOT, registry_path)}")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"PASS: {deployment_id} integrity OK")
    print(f"Manifest: {_format_path(REPO_ROOT, manifest_path)}")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Audit integration deployment integrity (no mutation)")
    parser.add_argument("--deployment-id", required=True, help="Deployment id like DEPLOY-002-20251226")
    parser.add_argument(
        "--registry",
        default=str(DEFAULT_REGISTRY_PATH),
        help="Path to DUMPSTER_DIVE_REGISTRY.json (default: repo standard)",
    )
    parser.add_argument(
        "--deploy-map",
        default=str(DEFAULT_DEPLOY_MAP_PATH),
        help="Path to TIMELINE_A_DEPLOY_MAP.json (default: repo standard)",
    )
    parser.add_argument(
        "--tempered-dir",
        default=str(DEFAULT_TEMPERED_DIR),
        help="Path to forge/tempered directory (default: repo standard)",
    )

    args = parser.parse_args(argv)
    return audit_deployment(
        deployment_id=args.deployment_id,
        registry_path=Path(args.registry),
        deploy_map_path=Path(args.deploy_map),
        tempered_dir=Path(args.tempered_dir),
    )


if __name__ == "__main__":
    raise SystemExit(main())
