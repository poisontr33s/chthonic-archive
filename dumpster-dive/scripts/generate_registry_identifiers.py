#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Registry Universal Identifier Generator (RUIG)
==============================================

Purpose: Assign stable UUID or content-hash based identifiers to all 115 files 
         in dumpster-dive/ for chaos-resilient cross-reference navigation.

Strategy: Use content-addressable UUIDs (UUIDv5) based on file path + content hash
          to ensure identifiers remain stable across renames/moves while tracking
          content changes.

Author: Sister Ferrum Scoriae (SFS) - Tier 3 Matriarch
Domain: dumpster-dive/ Ore Processing & Registry Management
"""

import json
import hashlib
import uuid
from pathlib import Path
from typing import Dict, Any, Iterable, List, Optional, Set, Tuple
from datetime import datetime

class RegistryIdentifierGenerator:
    """Generates and embeds stable file identifiers into DUMPSTER_DIVE_REGISTRY.json"""
    
    # UUID namespace for chthonic-archive project
    NAMESPACE_CHTHONIC = uuid.UUID('a1b2c3d4-e5f6-7890-abcd-ef1234567890')
    
    def __init__(self, registry_path: Path):
        self.registry_path = registry_path
        self.registry_data: Dict[str, Any] = {}
        self.dumpster_dive_root = registry_path.parent
        
    def load_registry(self) -> None:
        """Load existing registry JSON"""
        with open(self.registry_path, 'r', encoding='utf-8') as f:
            self.registry_data = json.load(f)
            
    def compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of file content"""
        if not file_path.exists():
            return "FILE_NOT_FOUND"
        
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        return hasher.hexdigest()

    def compute_artifact_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of the current on-disk bytes.

        Governance note:
        - `content_hash` is treated as an identity seed (stable once assigned).
        - `artifact_hash` tracks the mutable, current bytes (used for deploy/manifests).
        """
        return self.compute_file_hash(file_path)
    
    def generate_file_id(self, relative_path: str, content_hash: str) -> str:
        """
        Generate stable UUIDv5 based on file path + content hash
        
        Format: FILE-{uuid}
        Example: FILE-9f8e7d6c-5b4a-3210-fedc-ba9876543210
        
        Stability: Same path + same content = same UUID
                   Path change = new UUID (intentional - tracks moves)
                   Content change = new UUID (intentional - tracks versions)
        """
        # Combine path + hash as seed for UUID generation
        seed_string = f"{relative_path}::{content_hash}"
        
        # Generate UUIDv5 using chthonic-archive namespace
        file_uuid = uuid.uuid5(self.NAMESPACE_CHTHONIC, seed_string)
        
        return f"FILE-{file_uuid}"

    def _normalize_relative_path(self, relative_path: str) -> str:
        # Registry uses POSIX-style paths.
        return relative_path.replace('\\', '/').lstrip('/')

    def _ensure_files_section(self, key: str) -> Dict[str, Any]:
        section = self.registry_data.get(key)
        if not isinstance(section, dict):
            section = {}
            self.registry_data[key] = section
        files = section.get("files")
        if not isinstance(files, list):
            section["files"] = []
        return section

    def _upsert_file_entry(
        self,
        section_key: str,
        relative_path: str,
        filename: Optional[str] = None,
        forge_stage: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], bool]:
        section = self._ensure_files_section(section_key)
        rel = self._normalize_relative_path(relative_path)
        entries: List[Dict[str, Any]] = section["files"]

        for entry in entries:
            if entry.get("relative_path") == rel:
                return entry, False

        entry: Dict[str, Any] = {
            "relative_path": rel,
            "filename": filename or Path(rel).name,
        }
        if forge_stage is not None:
            entry["forge_stage"] = forge_stage
        entries.append(entry)
        return entry, True

    def update_file_entry(self, file_entry: Dict[str, Any], section_key: str) -> Tuple[bool, bool]:
        """Add/update file identifier fields.

        Returns:
          (identity_changed, artifact_hash_changed)

        Identity policy (Option B):
        - Never rewrite an existing `file_id`/`content_hash` just because the file bytes changed.
        - Track current bytes in `artifact_hash`.
        """

        explicit_rel = file_entry.get("relative_path")
        if isinstance(explicit_rel, str) and explicit_rel.strip():
            relative_path = self._normalize_relative_path(explicit_rel)
        else:
            # Determine file path based on section
            if section_key == "tempered_artifacts":
                base_path = "forge/tempered"
            elif section_key == "from_github":
                base_path = "from-github"
            elif section_key == "protocols":
                base_path = "protocols"
            elif section_key == "root_documentation":
                base_path = ""
            elif section_key.startswith("forge_"):
                base_path = f"forge/{section_key.replace('forge_', '')}"
            else:
                base_path = ""

            filename = file_entry.get("filename", "")
            if not filename:
                return False, False

            relative_path = self._normalize_relative_path(f"{base_path}/{filename}" if base_path else filename)

        full_path = self.dumpster_dive_root / relative_path

        # Compute current bytes hash (mutable).
        artifact_hash = self.compute_artifact_hash(full_path)

        prior_file_id = file_entry.get("file_id")
        prior_content_hash = file_entry.get("content_hash")
        prior_artifact_hash = file_entry.get("artifact_hash")

        file_entry["relative_path"] = relative_path
        file_entry["hash_algorithm"] = "SHA256"

        # Identity assignment (only if missing).
        identity_changed = False
        if not isinstance(prior_file_id, str) or not prior_file_id.strip() or not isinstance(prior_content_hash, str) or not prior_content_hash.strip():
            # First-time identity seed: use current bytes hash.
            content_hash = artifact_hash
            file_id = self.generate_file_id(relative_path, content_hash)
            file_entry["file_id"] = file_id
            file_entry["content_hash"] = content_hash
            file_entry["identifier_generated"] = datetime.now().isoformat()
            identity_changed = True

        # Mutable bytes hash tracking (always refreshed).
        file_entry["artifact_hash"] = artifact_hash
        file_entry["artifact_hash_algorithm"] = "SHA256"
        artifact_hash_changed = prior_artifact_hash != artifact_hash
        if artifact_hash_changed:
            file_entry["artifact_hash_updated"] = datetime.now().isoformat()

        # Add integration tracking fields (initialize only if missing)
        file_entry.setdefault("integrated", False)
        file_entry.setdefault("integration_deployment_id", None)
        file_entry.setdefault("integration_timestamp", None)
        file_entry.setdefault("integration_manifest_ref", None)
        file_entry.setdefault("ssot_hash_at_integration", None)

        return identity_changed, artifact_hash_changed

    def _collect_tracked_relative_paths(self) -> List[Tuple[str, str, Optional[str]]]:
        """Return list of (section_key, relative_path, forge_stage) that should receive identifiers."""

        tracked: List[Tuple[str, str, Optional[str]]] = []

        folder_structure = self.registry_data.get("folder_structure", {})
        if isinstance(folder_structure, dict):
            root = folder_structure.get("root", {})
            if isinstance(root, dict):
                for key_file in root.get("key_files", []) or []:
                    if not isinstance(key_file, str):
                        continue
                    # Avoid self-referential hashing for the registry itself.
                    if key_file == "DUMPSTER_DIVE_REGISTRY.json":
                        continue
                    tracked.append(("root_documentation", key_file, "root"))

            protocols = folder_structure.get("protocols", {})
            if isinstance(protocols, dict):
                for key_file in protocols.get("key_files", []) or []:
                    if not isinstance(key_file, str):
                        continue
                    tracked.append(("protocols", f"protocols/{key_file}", "protocols"))

            forge = folder_structure.get("forge", {})
            if isinstance(forge, dict):
                subdirs = forge.get("subdirectories", {})
                if isinstance(subdirs, dict):
                    for stage_key, stage_info in subdirs.items():
                        if not isinstance(stage_info, dict):
                            continue
                        current_files = stage_info.get("current_files")
                        if not isinstance(current_files, list):
                            continue
                        for filename in current_files:
                            if not isinstance(filename, str):
                                continue
                            tracked.append(("tempered_artifacts" if stage_key == "tempered" else f"forge_{stage_key}", f"forge/{stage_key}/{filename}", stage_key))

        # from-github: enumerate actual files on disk for full coverage
        from_github_dir = self.dumpster_dive_root / "from-github"
        if from_github_dir.exists():
            for path in sorted(from_github_dir.rglob("*")):
                if not path.is_file():
                    continue
                rel = self._normalize_relative_path(str(path.relative_to(self.dumpster_dive_root)))
                tracked.append(("from_github", rel, None))

        return tracked
    
    def update_registry(self) -> None:
        """Update all file entries in registry with identifiers"""

        updated_paths: Set[str] = set()
        sections_processed: Set[str] = set()
        skipped_paths: List[Dict[str, str]] = []
        any_identity_changes = False
        any_artifact_hash_changes = False

        # Build/ensure per-file sections from the current registry schema.
        for section_key, relative_path, forge_stage in self._collect_tracked_relative_paths():
            entry, created = self._upsert_file_entry(
                section_key=section_key,
                relative_path=relative_path,
                forge_stage=forge_stage,
            )
            if created:
                any_identity_changes = True

            identity_changed, artifact_hash_changed = self.update_file_entry(entry, section_key)
            if identity_changed:
                any_identity_changes = True
            if artifact_hash_changed:
                any_artifact_hash_changes = True
            resolved_rel = entry.get("relative_path", relative_path)
            if entry.get("content_hash") == "FILE_NOT_FOUND":
                skipped_paths.append({"relative_path": resolved_rel, "reason": "FILE_NOT_FOUND"})
                continue
            updated_paths.add(resolved_rel)
            sections_processed.add(section_key)

            # Also mirror identifiers into forge_tempered_artifacts mapping when present.
            if section_key == "tempered_artifacts":
                filename = entry.get("filename") or Path(entry.get("relative_path", "")).name
                fta = self.registry_data.get("forge_tempered_artifacts")
                if isinstance(fta, dict) and isinstance(filename, str) and filename in fta and isinstance(fta[filename], dict):
                    forged_entry = fta[filename]
                    # Only flag change if we actually add new fields or modify identifier values.
                    before = (
                        forged_entry.get("file_id"),
                        forged_entry.get("content_hash"),
                        forged_entry.get("artifact_hash"),
                        forged_entry.get("hash_algorithm"),
                        forged_entry.get("identifier_generated"),
                        forged_entry.get("relative_path"),
                    )
                    forged_entry["filename"] = filename
                    forged_entry["relative_path"] = entry.get("relative_path")
                    forged_entry["file_id"] = entry.get("file_id")
                    forged_entry["content_hash"] = entry.get("content_hash")
                    forged_entry["artifact_hash"] = entry.get("artifact_hash")
                    forged_entry["artifact_hash_algorithm"] = entry.get("artifact_hash_algorithm")
                    forged_entry["artifact_hash_updated"] = entry.get("artifact_hash_updated")
                    forged_entry["hash_algorithm"] = entry.get("hash_algorithm")
                    # Mirror identifier timestamps, but don't clobber existing integration state.
                    forged_entry["identifier_generated"] = entry.get("identifier_generated")
                    forged_entry.setdefault("integrated", entry.get("integrated", False))
                    forged_entry.setdefault("integration_deployment_id", entry.get("integration_deployment_id"))
                    forged_entry.setdefault("integration_timestamp", entry.get("integration_timestamp"))
                    forged_entry.setdefault("integration_manifest_ref", entry.get("integration_manifest_ref"))
                    forged_entry.setdefault("ssot_hash_at_integration", entry.get("ssot_hash_at_integration"))
                    after = (
                        forged_entry.get("file_id"),
                        forged_entry.get("content_hash"),
                        forged_entry.get("artifact_hash"),
                        forged_entry.get("hash_algorithm"),
                        forged_entry.get("identifier_generated"),
                        forged_entry.get("relative_path"),
                    )
                    if before != after:
                        any_artifact_hash_changes = True
        
        # Update metadata
        if any_identity_changes:
            self.registry_data["metadata"]["last_identifier_update"] = datetime.now().isoformat()
        if any_artifact_hash_changes:
            self.registry_data["metadata"]["last_artifact_hash_update"] = datetime.now().isoformat()
        self.registry_data["metadata"]["files_with_identifiers"] = len(updated_paths)
        self.registry_data["metadata"]["sections_processed"] = sorted(sections_processed)
        # Explain why 114/115 can be expected (registry file is intentionally excluded).
        skipped_paths.append({"relative_path": "DUMPSTER_DIVE_REGISTRY.json", "reason": "SELF_REFERENCE_EXCLUDED"})
        self.registry_data["metadata"]["identifier_skipped"] = skipped_paths
        
        # Add identifier schema reference
        self.registry_data["identifier_schema"] = {
            "format": "FILE-{uuidv5}",
            "namespace": str(self.NAMESPACE_CHTHONIC),
            "algorithm": "UUIDv5(path::content_hash)",
            "stability": "Same path + same content = same UUID",
            "purpose": "Chaos-resilient cross-reference navigation"
        }
        
        changed_note = "(no identity changes)" if not any_identity_changes else ""
        print(f"✅ Updated {len(updated_paths)} file entries across {len(sections_processed)} sections {changed_note}")
        
    def save_registry(self) -> None:
        """Save updated registry back to JSON file"""
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump(self.registry_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Registry saved to {self.registry_path}")
        
    def generate_identifier_report(self) -> str:
        """Generate markdown report of all assigned identifiers"""
        generated_at = self.registry_data.get("metadata", {}).get("last_identifier_update") or datetime.now().isoformat()
        report_lines = [
            "# Registry Universal Identifier Report",
            "",
            f"**Generated**: {generated_at}",
            f"**Registry**: {self.registry_path.name}",
            f"**Total Files**: {self.registry_data['metadata'].get('files_with_identifiers', 0)}",
            "",
            "## Identifier Schema",
            "",
            f"- **Format**: FILE-{{uuidv5}}",
            f"- **Namespace**: {self.NAMESPACE_CHTHONIC}",
            f"- **Algorithm**: UUIDv5(relative_path::content_hash)",
            f"- **Stability**: Same path + same content = same UUID",
            "",
            "## Sample Identifiers",
            ""
        ]
        
        # Sample 5 identifiers from tempered artifacts
        if "tempered_artifacts" in self.registry_data:
            files = self.registry_data["tempered_artifacts"].get("files", [])[:5]
            report_lines.append("### Tempered Artifacts (Sample)")
            report_lines.append("")
            for f in files:
                report_lines.append(f"- **{f['filename']}**")
                report_lines.append(f"  - ID: `{f.get('file_id', 'N/A')}`")
                report_lines.append(f"  - Hash: `{f.get('content_hash', 'N/A')[:16]}...`")
                report_lines.append("")
        
        return "\n".join(report_lines)


def main():
    """Execute registry identifier generation"""
    
    # Path to registry
    registry_path = Path(__file__).parent.parent / "DUMPSTER_DIVE_REGISTRY.json"
    
    print("🔧 Registry Universal Identifier Generator (RUIG)")
    print("=" * 60)
    print()
    
    # Initialize generator
    generator = RegistryIdentifierGenerator(registry_path)
    
    # Load registry
    print("📖 Loading registry...")
    generator.load_registry()
    print(f"✅ Loaded {generator.registry_data['metadata']['total_files']} file entries")
    print()
    
    # Generate identifiers
    print("🔨 Generating stable file identifiers...")
    generator.update_registry()
    print()
    
    # Save updated registry
    print("💾 Saving updated registry...")
    generator.save_registry()
    print()
    
    # Generate report
    print("📊 Generating identifier report...")
    report = generator.generate_identifier_report()
    report_path = registry_path.parent / "IDENTIFIER_GENERATION_REPORT.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"✅ Report saved to {report_path}")
    print()
    
    print("🎉 Registry universal identifier generation COMPLETE")
    print()
    print("Next Steps:")
    print("  1. Review IDENTIFIER_GENERATION_REPORT.md")
    print("  2. Verify file_id assignments in DUMPSTER_DIVE_REGISTRY.json")
    print("  3. Proceed to Task 4: Embed SSOT hashes into tempered files")


if __name__ == "__main__":
    main()
