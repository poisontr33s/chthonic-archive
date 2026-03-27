#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""Regression tests for SSOT binding across MAS scan tools."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

TESTS_ROOT = Path(__file__).resolve().parent
MAS_ROOT = TESTS_ROOT.parent

if str(MAS_ROOT) not in sys.path:
    sys.path.insert(0, str(MAS_ROOT))

from logic.ssot_binding import (
    compute_ssot_hash, compute_ssot_vitals, compare_vitals,
    resolve_ssot, resolve_ssot_for_lexicon,
    stamp_journal, read_journal_tail,
)
from logic.ssot_manifest import (
    SSOT_HOLDER_RELPATH, SSOT_POINTER_RELPATH, SSOT_PROTO_RELPATH,
    SSOT_ROLES, SSOT_RELATIONS, JOURNAL_EVENTS,
    SSOTProvenance, CascadeEntry, CASCADE_REGISTER,
    resolve_cascade_entry, cascade_register_to_dict,
)
from server import SSOT_LEXICON_PATH, SSOT_PATH, PROJECT_ROOT, mcp


def test_resolve_ssot_uses_git_root_and_env_overrides(tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    nested = repo_root / "apps" / "mas"
    repo_root.mkdir()
    nested.mkdir(parents=True)
    (repo_root / ".git").mkdir()
    (repo_root / ".github").mkdir()

    pointer, archive = resolve_ssot(nested)
    assert pointer == repo_root / ".github" / "copilot-instructions.md"
    assert archive == repo_root / ".github" / "copilot-instructions.archive.md"

    monkeypatch.setenv("SSOT_PATH", "custom/ssot.md")
    monkeypatch.setenv("SSOT_ARCHIVE_PATH", "custom/archive.md")

    pointer, archive = resolve_ssot(nested)
    assert pointer == repo_root / "custom" / "ssot.md"
    assert archive == repo_root / "custom" / "archive.md"


def test_resolve_ssot_for_lexicon_prefers_archive(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".git").mkdir()
    (repo_root / ".github").mkdir()
    pointer = repo_root / ".github" / "copilot-instructions.md"
    archive = repo_root / ".github" / "copilot-instructions.archive.md"

    pointer.write_text("`PointerTerm`\n", encoding="utf-8")
    assert resolve_ssot_for_lexicon(repo_root) == pointer

    archive.write_text("`ArchiveTerm`\n", encoding="utf-8")
    assert resolve_ssot_for_lexicon(repo_root) == archive


def test_ssot_hash_is_stable_across_canonical_whitespace(tmp_path):
    ssot_path = tmp_path / "ssot.md"
    ssot_path.write_bytes(b"alpha  \r\nbeta\t \r\n")
    first_hash = compute_ssot_hash(ssot_path)

    ssot_path.write_bytes(b"alpha\nbeta\n")
    second_hash = compute_ssot_hash(ssot_path)

    assert first_hash == second_hash


def test_server_tools_surface_ssot_binding_metadata():
    # Verify all tools are registered
    tools = {t.name: t for t in asyncio.run(mcp.list_tools())}
    assert "mas_pulse" in tools
    assert "mas_narrative_scan" in tools
    assert "mas_scan" in tools

    # Call the actual server functions directly (FastMCP 3.x list_tools returns schema, not callables)
    from mas_mcp.server import mas_pulse, mas_narrative_scan, mas_scan

    pulse = mas_pulse()
    bookend = pulse["ssot_bookend"]
    expected_pointer_hash = compute_ssot_hash(SSOT_PATH)[:16] if SSOT_PATH.exists() else None
    expected_lexicon_hash = (
        compute_ssot_hash(SSOT_LEXICON_PATH)[:16] if SSOT_LEXICON_PATH.exists() else None
    )

    assert set(bookend) >= {"ssot_file", "hash_start", "hash_now", "drifted",
                             "fingerprint_start", "fingerprint_now",
                             "changed_dimensions", "drift_summary"}
    assert bookend["hash_now"] == expected_pointer_hash
    if expected_pointer_hash is not None:
        assert len(bookend["hash_start"]) == 16
        assert len(bookend["hash_now"]) == 16
        assert isinstance(bookend["drifted"], bool)
        assert bookend["fingerprint_start"] is not None
        assert bookend["fingerprint_now"] is not None
        assert bookend["fingerprint_start"][0] == "L"

    # Pulse now includes journal timeline
    assert "ssot_journal" in pulse
    assert isinstance(pulse["ssot_journal"], list)

    narrative = mas_narrative_scan("CLAUDE.md")
    assert narrative["ssot_hash"] == expected_lexicon_hash
    assert "ssot_fingerprint" in narrative
    assert narrative["ssot_source_kind"] == "archive"

    scan = mas_scan("CLAUDE.md")
    assert scan["ssot_hash"] == expected_pointer_hash
    assert "ssot_fingerprint" in scan
    assert scan["ssot_source_kind"] == "pointer"
    assert scan["scan_metadata"]["files_scanned"] == 1


# ─────────────────────────────────────────────────────────────────────────────
# Vitals Fingerprint Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_vitals_fingerprint_structure(tmp_path):
    """Vitals returns a structured dict with all V5 fields."""
    ssot = tmp_path / "ssot.md"
    ssot.write_text(
        "# Title\n\n## Section A\n\n`FooBar` `BazQux`\n\n"
        "## Section B\n\nOrackla appears here.\n",
        encoding="utf-8",
    )
    vitals = compute_ssot_vitals(ssot, source_kind="archive")

    expected_keys = {
        "sha256", "source_kind", "source_role", "source_identity",
        "source_path",
        "lexicon_cardinality", "entity_census", "entity_count",
        "section_count", "byte_size",
        "heading_digest", "metrics_digest", "fingerprint",
    }
    assert set(vitals) == expected_keys
    assert len(vitals["sha256"]) == 64
    assert vitals["source_kind"] == "archive"
    assert vitals["source_role"] == "holder"
    assert vitals["source_identity"] == "holder"
    assert vitals["source_path"] == str(ssot)
    assert vitals["lexicon_cardinality"] >= 2  # FooBar, BazQux
    assert "Orackla" in vitals["entity_census"]
    assert vitals["entity_count"] == len(vitals["entity_census"])
    assert vitals["section_count"] == 3  # Title, Section A, Section B
    assert len(vitals["heading_digest"]) == 12
    assert len(vitals["metrics_digest"]) == 12
    assert vitals["fingerprint"].startswith("L")
    assert "\u00b7" in vitals["fingerprint"]  # middle dot separator

    # Pointer kind maps to pointer role
    vitals_ptr = compute_ssot_vitals(ssot, source_kind="pointer")
    assert vitals_ptr["source_role"] == "pointer"
    assert vitals_ptr["source_identity"] == "pointer"


def test_compare_vitals_detects_drift(tmp_path):
    """Compare vitals produces changed_dimensions and a compact summary."""
    ssot_v1 = tmp_path / "v1.md"
    ssot_v1.write_text("# Title\n\n`Alpha` `Beta`\n", encoding="utf-8")
    before = compute_ssot_vitals(ssot_v1)

    ssot_v2 = tmp_path / "v2.md"
    ssot_v2.write_text(
        "# Title\n\n## New Section\n\n`Alpha` `Beta` `Gamma` `Delta`\n\n"
        "Orackla is here now.\n",
        encoding="utf-8",
    )
    after = compute_ssot_vitals(ssot_v2)

    diff = compare_vitals(before, after)
    assert diff["hash_changed"] is True
    assert diff["lexicon_delta"] > 0
    assert diff["section_delta"] > 0
    # V4: changed_dimensions tracks which axes moved
    assert "lexicon" in diff["changed_dimensions"]
    assert "sections" in diff["changed_dimensions"]
    assert "entities" in diff["changed_dimensions"]
    assert isinstance(diff["headings_changed"], bool)
    assert isinstance(diff["metrics_changed"], bool)
    # V4: compact summary format: "lexicon +N, ..."
    assert "lexicon +" in diff["summary"]


# ─────────────────────────────────────────────────────────────────────────────
# Hash Journal Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_journal_stamp_and_read(tmp_path):
    """Journal stamps persist with source_kind, source_role, and can be read back."""
    ssot = tmp_path / "ssot.md"
    ssot.write_text("# Test\n\n`TermOne` `TermTwo`\n", encoding="utf-8")
    vitals = compute_ssot_vitals(ssot, source_kind="pointer")

    # Stamp two events with V5 event taxonomy
    entry1 = stamp_journal(tmp_path, vitals, event="startup_stamp")
    assert entry1["event"] == "startup_stamp"
    assert entry1["source_kind"] == "pointer"
    assert entry1["source_role"] == "pointer"
    assert entry1["source_identity"] == "pointer"
    assert entry1["fingerprint"].startswith("L")

    entry2 = stamp_journal(tmp_path, vitals, event="drift_detected")
    assert entry2["event"] == "drift_detected"
    assert entry2["source_kind"] == "pointer"
    assert entry2["source_role"] == "pointer"

    # Read back
    tail = read_journal_tail(tmp_path, n=10)
    assert len(tail) == 2
    assert tail[0]["event"] == "startup_stamp"
    assert tail[0]["source_kind"] == "pointer"
    assert tail[0]["source_role"] == "pointer"
    assert tail[1]["event"] == "drift_detected"

    # Verify JSONL format
    journal_file = tmp_path / ".mas_mcp" / "ssot_hash_journal.jsonl"
    assert journal_file.exists()
    lines = journal_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    for line in lines:
        parsed = json.loads(line)
        assert "ts" in parsed
        assert "hash" in parsed
        assert "source_kind" in parsed
        assert "source_role" in parsed
        assert "source_identity" in parsed


# ─────────────────────────────────────────────────────────────────────────────
# Manifest Tests (V5: Canon Declaration Layer)
# ─────────────────────────────────────────────────────────────────────────────

def test_manifest_role_taxonomy():
    """SSOT roles are complete and ordered."""
    assert "holder" in SSOT_ROLES
    assert "pointer" in SSOT_ROLES
    assert "projection" in SSOT_ROLES
    assert "validator" in SSOT_ROLES
    assert "journal" in SSOT_ROLES
    assert "artifact" in SSOT_ROLES
    assert "bridge" in SSOT_ROLES
    assert "config" in SSOT_ROLES
    assert len(SSOT_ROLES) == 8


def test_manifest_relation_taxonomy():
    """Relation types are complete."""
    assert "authoritative" in SSOT_RELATIONS
    assert "summarizing" in SSOT_RELATIONS
    assert "indexing" in SSOT_RELATIONS
    assert "validating" in SSOT_RELATIONS
    assert "projecting" in SSOT_RELATIONS
    assert "caching" in SSOT_RELATIONS
    assert "historizing" in SSOT_RELATIONS
    assert "config_boundary" in SSOT_RELATIONS
    assert len(SSOT_RELATIONS) == 8


def test_manifest_journal_event_taxonomy():
    """Journal events are sparse, threshold-only."""
    assert "startup_stamp" in JOURNAL_EVENTS
    assert "drift_detected" in JOURNAL_EVENTS
    assert "manual_reseal" in JOURNAL_EVENTS
    assert "artifact_emitted" in JOURNAL_EVENTS
    assert "holder_pointer_divergence" in JOURNAL_EVENTS
    assert len(JOURNAL_EVENTS) == 5


def test_cascade_register_completeness():
    """Cascade register covers all declared SSOT-adjacent artifacts."""
    identities = [e.identity for e in CASCADE_REGISTER]
    # Core SSOT files
    assert "holder" in identities
    assert "pointer" in identities
    assert "proto" in identities
    assert "hash_journal" in identities
    # Phase 0.1 expansions
    assert "ssot_binding" in identities
    assert "ssot_binding_tests" in identities
    assert "readable_ssot_generator" in identities
    assert "structural_extractor" in identities
    assert "loremaster" in identities
    assert "ssot_paths_bridge" in identities
    assert "asc_injector" in identities
    assert "narrative_scan_runner" in identities
    assert "run_cycle" in identities
    assert "ssot_extractor" in identities
    assert "abbreviation_cli" in identities

    # Every entry has a valid role and relation
    for entry in CASCADE_REGISTER:
        assert entry.role in SSOT_ROLES, f"{entry.identity}: bad role {entry.role}"
        assert entry.relation in SSOT_RELATIONS, f"{entry.identity}: bad relation {entry.relation}"

    holder = resolve_cascade_entry("holder")
    assert holder is not None
    assert holder.role == "holder"
    assert holder.relation == "authoritative"
    assert holder.relpath == SSOT_HOLDER_RELPATH

    pointer = resolve_cascade_entry("pointer")
    assert pointer is not None
    assert pointer.role == "pointer"
    assert pointer.relation == "summarizing"
    assert pointer.relpath == SSOT_POINTER_RELPATH


def test_cascade_register_serialization():
    """Cascade register exports as JSON-serializable list."""
    data = cascade_register_to_dict()
    assert isinstance(data, list)
    assert len(data) >= 4
    for entry in data:
        assert set(entry.keys()) == {"role", "identity", "relpath", "relation", "description"}
        assert entry["role"] in SSOT_ROLES
        assert entry["relation"] in SSOT_RELATIONS


def test_provenance_contract_roundtrip():
    """Provenance stamps and deserializes faithfully."""
    prov = SSOTProvenance.stamp_now(
        role="holder",
        identity="holder",
        path=".github/copilot-instructions.archive.md",
        sha256="a" * 64,
        fingerprint="L1504·E7·S204·955K",
        derived_from="canonical holder at session start",
    )
    d = prov.to_dict()
    assert d["source_role"] == "holder"
    assert d["source_identity"] == "holder"
    assert d["source_hash"] == "a" * 64
    assert d["source_fingerprint"] == "L1504·E7·S204·955K"
    assert d["derived_from"] == "canonical holder at session start"
    assert "T" in d["last_verified_at"]  # ISO timestamp

    restored = SSOTProvenance.from_dict(d)
    assert restored.source_role == prov.source_role
    assert restored.source_hash == prov.source_hash
    assert restored.last_verified_at == prov.last_verified_at


def test_binding_constants_resolve_through_manifest():
    """ssot_binding.SSOT_POINTER and SSOT_ARCHIVE are aliases of manifest constants."""
    from logic.ssot_binding import SSOT_POINTER, SSOT_ARCHIVE
    assert SSOT_POINTER == SSOT_POINTER_RELPATH
    assert SSOT_ARCHIVE == SSOT_HOLDER_RELPATH


def test_ssot_paths_bridge_resolves_through_manifest():
    """scripts/lib/ssot_paths.py bridge re-exports manifest constants and resolves absolute paths."""
    from scripts.lib.ssot_paths import (
        SSOT_HOLDER, SSOT_POINTER, SSOT_PROTO, resolve_ssot_paths
    )
    # Bridge re-exports match manifest
    assert SSOT_HOLDER == SSOT_HOLDER_RELPATH
    assert SSOT_POINTER == SSOT_POINTER_RELPATH
    assert SSOT_PROTO == SSOT_PROTO_RELPATH

    # resolve_ssot_paths produces absolute paths
    paths = resolve_ssot_paths(PROJECT_ROOT)
    assert paths.holder == PROJECT_ROOT / SSOT_HOLDER_RELPATH
    assert paths.pointer == PROJECT_ROOT / SSOT_POINTER_RELPATH
    assert paths.proto == PROJECT_ROOT / SSOT_PROTO_RELPATH
    assert paths.holder.is_absolute()


def test_cascade_register_all_relpaths_exist():
    """Every cascade entry with a code file relpath points to a real file."""
    for entry in CASCADE_REGISTER:
        target = PROJECT_ROOT / entry.relpath
        # Journal and SSOT content files may not exist in test environments,
        # but code files (validators, projections, bridges, artifacts, configs) should.
        if entry.role in ("validator", "projection", "bridge", "artifact", "config"):
            assert target.exists(), f"CASCADE_REGISTER[{entry.identity}]: {entry.relpath} not found"


# ── Phase 0.8: Cascade Grep Validation Tests ────────────────────────────────

import re
import subprocess


def _grep_ts_files_for_ssot_literals() -> list[str]:
    """Find hardcoded copilot-instructions paths in TS files (excluding bridges and comments)."""
    hits = []
    bridge_files = {"ssot-paths.ts"}
    ts_dirs = [PROJECT_ROOT / "scripts", PROJECT_ROOT / "extensions"]
    for d in ts_dirs:
        if not d.exists():
            continue
        for f in d.rglob("*.ts"):
            if f.name in bridge_files:
                continue
            content = f.read_text(encoding="utf-8", errors="replace")
            for i, line in enumerate(content.splitlines(), 1):
                stripped = line.strip()
                # Skip comments
                if stripped.startswith("//") or stripped.startswith("*") or stripped.startswith("/*"):
                    continue
                if "copilot-instructions" in line:
                    hits.append(f"{f.relative_to(PROJECT_ROOT)}:{i}")
    return hits


def _grep_ps1_files_for_ssot_literals() -> list[str]:
    """Find hardcoded copilot-instructions path constructions in PS1 files."""
    hits = []
    bridge_files = {"ssot-paths.ps1"}
    scripts_dir = PROJECT_ROOT / "scripts"
    if not scripts_dir.exists():
        return hits
    for f in scripts_dir.rglob("*.ps1"):
        if f.name in bridge_files:
            continue
        content = f.read_text(encoding="utf-8", errors="replace")
        in_block_comment = False
        for i, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()
            # Track <# #> block comments
            if "<#" in stripped:
                in_block_comment = True
            if "#>" in stripped:
                in_block_comment = False
                continue
            if in_block_comment:
                continue
            # Skip single-line comments
            if stripped.startswith("#"):
                continue
            # Skip evidence citation data (line-numbered archive references)
            if re.search(r'copilot-instructions\.\w+\.md:\d+', line):
                continue
            # Skip regex pattern strings (e.g., pre-commit guardian)
            if re.search(r'\\\..*copilot-instructions', line):
                continue
            if "copilot-instructions" in line:
                hits.append(f"{f.relative_to(PROJECT_ROOT)}:{i}")
    return hits


def test_no_hardcoded_ssot_paths_in_typescript():
    """No TS consumer outside bridge files should hardcode copilot-instructions paths."""
    hits = _grep_ts_files_for_ssot_literals()
    assert hits == [], f"Hardcoded SSOT paths in TS: {hits}"


def test_no_hardcoded_ssot_paths_in_powershell():
    """No PS1 consumer outside bridge files should hardcode copilot-instructions paths."""
    hits = _grep_ps1_files_for_ssot_literals()
    assert hits == [], f"Hardcoded SSOT paths in PS1: {hits}"


def test_config_boundary_ssot_paths_documented():
    """Every config-boundary entry in CASCADE_REGISTER must have relation 'config_boundary'."""
    config_entries = [e for e in CASCADE_REGISTER if e.role == "config"]
    assert len(config_entries) >= 2, "Expected at least 2 config boundary entries"
    for entry in config_entries:
        assert entry.relation == "config_boundary", (
            f"Config entry {entry.identity} should have relation 'config_boundary', got '{entry.relation}'"
        )
        target = PROJECT_ROOT / entry.relpath
        assert target.exists(), f"Config boundary {entry.identity}: {entry.relpath} not found"


def test_ankhrc_resolves_all_paths():
    """Every path value in .ankhrc must resolve to an existing file."""
    ankhrc_path = PROJECT_ROOT / ".ankhrc"
    assert ankhrc_path.exists(), ".ankhrc not found at repo root"

    content = ankhrc_path.read_text(encoding="utf-8")
    # Parse simple TOML key = "value" lines
    path_pattern = re.compile(r'^[A-Z_]+\s*=\s*"([^"]+)"', re.MULTILINE)
    paths = path_pattern.findall(content)
    assert len(paths) > 0, ".ankhrc has no path entries"

    missing = []
    for relpath in paths:
        if not (PROJECT_ROOT / relpath).exists():
            missing.append(relpath)

    assert missing == [], f".ankhrc paths not found: {missing}"


def _grep_py_files_for_ssot_literals() -> list[str]:
    """Find hardcoded copilot-instructions PATH CONSTRUCTIONS in Python files.

    Only catches actual path-building patterns (/, join, resolve with the literal).
    Runtime detection (if "copilot" in name), output paths (.readable.md), and
    data/documentation strings are exempt — they don't violate the cascade contract.
    """
    hits = []
    bridge_files = {"ssot_paths.py", "ssot_manifest.py", "test_ssot_binding.py", "stamp_sid.py"}
    # Pattern: path construction ops with copilot-instructions as a segment
    path_construction = re.compile(
        r'(?:'
        r'(?:Path|join|resolve|os\.path)\s*\(.*copilot-instructions'  # join/resolve calls
        r'|/\s*["\']\.github/copilot-instructions'  # / operator path building
        r'|["\']\.github/copilot-instructions[^.]*\.md["\']'  # bare string that IS an SSOT relpath
        r')'
    )
    scripts_dir = PROJECT_ROOT / "scripts"
    if not scripts_dir.exists():
        return hits
    for f in scripts_dir.rglob("*.py"):
        if f.name in bridge_files:
            continue
        content = f.read_text(encoding="utf-8", errors="replace")
        in_docstring = False
        for i, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()
            triple_count = line.count('"""') + line.count("'''")
            if triple_count % 2 == 1:
                in_docstring = not in_docstring
            if in_docstring:
                continue
            if stripped.startswith("#"):
                continue
            if path_construction.search(line):
                hits.append(f"{f.relative_to(PROJECT_ROOT)}:{i}")
    return hits


def test_no_hardcoded_ssot_paths_in_python():
    """No Python consumer outside bridge/manifest should hardcode copilot-instructions path constructions."""
    hits = _grep_py_files_for_ssot_literals()
    assert hits == [], f"Hardcoded SSOT paths in Python: {hits}"
