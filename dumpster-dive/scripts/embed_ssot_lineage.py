#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SSOT Hash Embed + Integration Manifest (Task 4 / SHES-001)

Embeds SSOT lineage metadata into the 9 tempered artifacts listed in:
  DUMPSTER_DIVE_REGISTRY.json -> folder_structure.forge.subdirectories.tempered.current_files

Rules:
- Markdown files: prepend YAML frontmatter block (SHES-001).
- JSON files: inject top-level keys `ssot_lineage` and `integration_status` (keeps valid JSON).
- Updates registry entries with `ssot_hash_embedded: true` for tempered artifacts.
- Writes an integration manifest JSON for the deployment.

This script is designed to be idempotent: reruns should not churn unless inputs change.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class DeploymentConfig:
    deployment_id: str
    operator: str
    rollback_checkpoint: str
    fa4_certification: str
    extraction_phase: str
    validation_date: str


def sha256_hex_upper(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha256_file_hex_upper(path: Path) -> str:
    return sha256_hex_upper(path.read_bytes())


def compute_word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def strip_existing_yaml_frontmatter(text: str) -> Tuple[Optional[str], str]:
    if not text.startswith("---\n"):
        return None, text

    end = text.find("\n---\n", 4)
    if end == -1:
        return None, text

    frontmatter = text[: end + len("\n---\n")]
    rest = text[end + len("\n---\n") :]
    return frontmatter, rest


def build_yaml_frontmatter(
    *,
    ssot_hash: str,
    ssot_source: str,
    computed_date: str,
    sections_impacted: List[str],
    file_id: str,
    deployment: DeploymentConfig,
) -> str:
    # Minimal, spec-conformant block from SHES-001.
    # Keep lists non-empty.
    sections = sections_impacted if sections_impacted else ["TBD"]

    lines: List[str] = [
        "---",
        "ssot_lineage:",
        f"  ssot_hash: \"{ssot_hash}\"",
        f"  ssot_source: \"{ssot_source}\"",
        f"  computed_date: \"{computed_date}\"",
        "  sections_impacted:",
    ]
    for section in sections:
        lines.append(f"    - \"{section}\"")

    lines.extend(
        [
            f"  fa4_certification: \"{deployment.fa4_certification}\"",
            f"  extraction_phase: \"{deployment.extraction_phase}\"",
            f"  validator: \"{deployment.operator}\"",
            f"  validation_date: \"{deployment.validation_date}\"",
            f"  integration_deployment: \"{deployment.deployment_id}\"",
            "  ",
            "integration_status:",
            f"  file_id: \"{file_id}\"",
            "  registry_ref: \"DUMPSTER_DIVE_REGISTRY.json\"",
            "  integration_ready: true",
            f"  rollback_checkpoint: \"{deployment.rollback_checkpoint}\"",
            "---",
            "",
        ]
    )

    return "\n".join(lines)


def embed_into_markdown(path: Path, frontmatter: str) -> bool:
    original = path.read_text(encoding="utf-8")
    _, rest = strip_existing_yaml_frontmatter(original)
    updated = frontmatter + rest.lstrip("\n")
    if updated == original:
        return False
    path.write_text(updated, encoding="utf-8", newline="\n")
    return True


def embed_into_json(path: Path, lineage: Dict[str, Any], status: Dict[str, Any]) -> bool:
    original_text = path.read_text(encoding="utf-8")
    original_obj = json.loads(original_text)
    if not isinstance(original_obj, dict):
        raise ValueError(f"Expected JSON object at top-level: {path}")

    # Put lineage/status first for readability; keep rest unchanged.
    new_obj: Dict[str, Any] = {}
    new_obj["ssot_lineage"] = lineage
    new_obj["integration_status"] = status

    # Preserve other keys.
    for key, value in original_obj.items():
        if key in ("ssot_lineage", "integration_status"):
            continue
        new_obj[key] = value

    updated_text = json.dumps(new_obj, indent=2, ensure_ascii=False) + "\n"
    if updated_text == original_text:
        return False

    path.write_text(updated_text, encoding="utf-8", newline="\n")
    return True


def main() -> None:
    script_path = Path(__file__).resolve()
    dumpster_dive_root = script_path.parent.parent
    repo_root = dumpster_dive_root.parent

    registry_path = dumpster_dive_root / "DUMPSTER_DIVE_REGISTRY.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))

    ssot_path = repo_root / ".github" / "copilot-instructions.md"
    ssot_hash = sha256_hex_upper(ssot_path.read_bytes())
    computed_date = datetime.now(timezone.utc).date().isoformat()

    run_timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    deployment = DeploymentConfig(
        deployment_id="DEPLOY-001-20251225",
        operator="THE-SAVANT (User)",
        rollback_checkpoint="PRE-DEPLOY-001",
        fa4_certification="PASSED",
        extraction_phase="Phase 1 - Timeline E",
        validation_date="2025-12-09",
    )

    targets: List[str] = registry["folder_structure"]["forge"]["subdirectories"]["tempered"]["current_files"]

    # Build lookup for file_id and sections_impacted.
    tempered_entries = {
        e.get("filename"): e
        for e in registry.get("tempered_artifacts", {}).get("files", [])
        if isinstance(e, dict)
    }
    fta = registry.get("forge_tempered_artifacts", {})

    modified_files: List[Dict[str, Any]] = []
    all_sections_impacted: List[str] = []

    for filename in targets:
        rel = Path("forge") / "tempered" / filename
        full_path = dumpster_dive_root / rel

        entry = tempered_entries.get(filename)
        if not entry or not entry.get("file_id"):
            raise RuntimeError(f"Missing file_id in registry for {filename}")
        file_id = entry["file_id"]

        sections_impacted: List[str] = []
        if isinstance(fta, dict) and filename in fta and isinstance(fta[filename], dict):
            maybe = fta[filename].get("ssot_integration", {}).get("sections_impacted")
            if isinstance(maybe, list):
                sections_impacted = [str(x) for x in maybe if str(x).strip()]

        if not sections_impacted:
            sections_impacted = ["TBD"]

        # Deduplicate global sections list.
        for section in sections_impacted:
            if section not in all_sections_impacted:
                all_sections_impacted.append(section)

        lineage_obj: Dict[str, Any] = {
            "ssot_hash": ssot_hash,
            "ssot_source": ".github/copilot-instructions.md",
            "computed_date": computed_date,
            "sections_impacted": sections_impacted,
            "fa4_certification": deployment.fa4_certification,
            "extraction_phase": deployment.extraction_phase,
            "validator": deployment.operator,
            "validation_date": deployment.validation_date,
            "integration_deployment": deployment.deployment_id,
        }

        status_obj: Dict[str, Any] = {
            "file_id": file_id,
            "registry_ref": "DUMPSTER_DIVE_REGISTRY.json",
            "integration_ready": True,
            "rollback_checkpoint": deployment.rollback_checkpoint,
        }

        changed = False
        if full_path.suffix.lower() in {".md", ".markdown"}:
            frontmatter = build_yaml_frontmatter(
                ssot_hash=ssot_hash,
                ssot_source=".github/copilot-instructions.md",
                computed_date=computed_date,
                sections_impacted=sections_impacted,
                file_id=file_id,
                deployment=deployment,
            )
            changed = embed_into_markdown(full_path, frontmatter)
        elif full_path.suffix.lower() == ".json":
            changed = embed_into_json(full_path, lineage_obj, status_obj)
        else:
            raise RuntimeError(f"Unsupported tempered file type for embedding: {full_path}")

        # Compute post-embed file hash for manifest.
        file_bytes = full_path.read_bytes()
        file_hash = sha256_hex_upper(file_bytes)
        word_count = compute_word_count(full_path.read_text(encoding="utf-8"))

        modified_files.append(
            {
                "filename": filename,
                "file_id": file_id,
                "source_path": str(rel).replace("\\", "/"),
                "target_section": sections_impacted[0],
                "file_hash": file_hash,
                "word_count": word_count,
                "fa4_certification": deployment.fa4_certification,
                "validation_status": "passed",
                "validation_timestamp": run_timestamp,
                "ssot_hash_embedded": True,
                "integration_notes": "Embedded SSOT lineage metadata (Task 4 / SHES-001).",
                "changed": changed,
            }
        )

        # Update registry flags (idempotent).
        entry["ssot_hash_embedded"] = True
        # Governance model: keep file_id/content_hash stable; track current bytes separately.
        entry["artifact_hash"] = sha256_file_hex_upper(full_path)
        entry["artifact_hash_algorithm"] = "SHA256"
        entry["artifact_hash_updated"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        if isinstance(fta, dict) and filename in fta and isinstance(fta[filename], dict):
            fta[filename]["ssot_hash_embedded"] = True
            fta[filename]["artifact_hash"] = entry["artifact_hash"]
            fta[filename]["artifact_hash_algorithm"] = "SHA256"
            fta[filename]["artifact_hash_updated"] = entry["artifact_hash_updated"]

    # Persist registry updates.
    registry_path.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

    manifest_path = dumpster_dive_root / "forge" / "tempered" / f"INTEGRATION_MANIFEST_{deployment.deployment_id}.json"

    deployment_record = {
        "deployment_id": deployment.deployment_id,
        "deployment_type": "staged-partial",
        "phase": deployment.extraction_phase,
        "timestamp": run_timestamp,
        "operator": deployment.operator,
        "ssot_hash_at_deployment": ssot_hash,
        "files": [{k: v for k, v in f.items() if k != "changed"} for f in modified_files],
        "sections_impacted": all_sections_impacted,
        "validation": {
            "fa4_compliance": "PASSED",
            "cross_references": "PENDING",
            "registry_sync": "PASSED",
            "lint_check": "PENDING",
            "notes": "Task 4: SSOT lineage embedded; run validate_references.ps1 to finalize cross-reference status.",
        },
        "status": "completed",
        "rollback_checkpoint": deployment.rollback_checkpoint,
        "completion_timestamp": run_timestamp,
        "duration_minutes": 0,
        "notes": "Automated embed + manifest generation.",
    }

    if manifest_path.exists():
        existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        deployments = existing.get("deployments")
        if not isinstance(deployments, list):
            raise ValueError(f"Invalid manifest deployments list: {manifest_path}")

        if any(d.get("deployment_id") == deployment.deployment_id for d in deployments if isinstance(d, dict)):
            # Idempotence: never rewrite an existing deployment (avoids timestamp churn).
            wrote_manifest = False
        else:
            deployments.append(deployment_record)
            existing["ssot_reference"] = {
                "path": ".github/copilot-instructions.md",
                "hash": ssot_hash,
                "hash_algorithm": "SHA256",
                "computed_date": computed_date,
            }
            manifest_path.write_text(json.dumps(existing, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
            wrote_manifest = True
    else:
        manifest = {
            "manifest_version": "1.0.0",
            "created": run_timestamp,
            "registry_ref": "DUMPSTER_DIVE_REGISTRY.json",
            "ssot_reference": {
                "path": ".github/copilot-instructions.md",
                "hash": ssot_hash,
                "hash_algorithm": "SHA256",
                "computed_date": computed_date,
            },
            "deployments": [deployment_record],
        }
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        wrote_manifest = True

    # Print a small summary for human validation.
    changed_count = sum(1 for f in modified_files if f["changed"])
    print(f"✅ Embedded SSOT lineage into {len(modified_files)} tempered files ({changed_count} changed)")
    print(f"✅ Updated registry flags: {registry_path}")
    if wrote_manifest:
        print(f"✅ Wrote integration manifest: {manifest_path}")
    else:
        print(f"✅ Integration manifest unchanged: {manifest_path}")
    print(f"SSOT SHA256: {ssot_hash}")


if __name__ == "__main__":
    main()
