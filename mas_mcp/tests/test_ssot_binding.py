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
    tools = asyncio.run(mcp._tool_manager.get_tools())

    pulse = tools["mas_pulse"].fn()
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

    narrative = tools["mas_narrative_scan"].fn("CLAUDE.md")
    assert narrative["ssot_hash"] == expected_lexicon_hash
    assert "ssot_fingerprint" in narrative
    assert narrative["ssot_source_kind"] == "archive"

    scan = tools["mas_scan"].fn("CLAUDE.md")
    assert scan["ssot_hash"] == expected_pointer_hash
    assert "ssot_fingerprint" in scan
    assert scan["ssot_source_kind"] == "pointer"
    assert scan["scan_metadata"]["files_scanned"] == 1


# ─────────────────────────────────────────────────────────────────────────────
# Vitals Fingerprint Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_vitals_fingerprint_structure(tmp_path):
    """Vitals returns a structured dict with all V4 fields."""
    ssot = tmp_path / "ssot.md"
    ssot.write_text(
        "# Title\n\n## Section A\n\n`FooBar` `BazQux`\n\n"
        "## Section B\n\nOrackla appears here.\n",
        encoding="utf-8",
    )
    vitals = compute_ssot_vitals(ssot, source_kind="archive")

    expected_keys = {
        "sha256", "source_kind", "source_path",
        "lexicon_cardinality", "entity_census", "entity_count",
        "section_count", "byte_size",
        "heading_digest", "metrics_digest", "fingerprint",
    }
    assert set(vitals) == expected_keys
    assert len(vitals["sha256"]) == 64
    assert vitals["source_kind"] == "archive"
    assert vitals["source_path"] == str(ssot)
    assert vitals["lexicon_cardinality"] >= 2  # FooBar, BazQux
    assert "Orackla" in vitals["entity_census"]
    assert vitals["entity_count"] == len(vitals["entity_census"])
    assert vitals["section_count"] == 3  # Title, Section A, Section B
    assert len(vitals["heading_digest"]) == 12
    assert len(vitals["metrics_digest"]) == 12
    assert vitals["fingerprint"].startswith("L")
    assert "\u00b7" in vitals["fingerprint"]  # middle dot separator


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
    """Journal stamps persist with source_kind and can be read back."""
    ssot = tmp_path / "ssot.md"
    ssot.write_text("# Test\n\n`TermOne` `TermTwo`\n", encoding="utf-8")
    vitals = compute_ssot_vitals(ssot, source_kind="pointer")

    # Stamp two events
    entry1 = stamp_journal(tmp_path, vitals, event="startup")
    assert entry1["event"] == "startup"
    assert entry1["source_kind"] == "pointer"
    assert entry1["fingerprint"].startswith("L")

    entry2 = stamp_journal(tmp_path, vitals, event="drift_detected")
    assert entry2["event"] == "drift_detected"
    assert entry2["source_kind"] == "pointer"

    # Read back
    tail = read_journal_tail(tmp_path, n=10)
    assert len(tail) == 2
    assert tail[0]["event"] == "startup"
    assert tail[0]["source_kind"] == "pointer"
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
