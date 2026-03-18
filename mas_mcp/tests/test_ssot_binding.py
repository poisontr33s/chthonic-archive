#!/usr/bin/env python3
#-*- coding: utf-8 -*-
"""Regression tests for SSOT binding across MAS scan tools."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

TESTS_ROOT = Path(__file__).resolve().parent
MAS_ROOT = TESTS_ROOT.parent

if str(MAS_ROOT) not in sys.path:
    sys.path.insert(0, str(MAS_ROOT))

from logic.ssot_binding import compute_ssot_hash, resolve_ssot, resolve_ssot_for_lexicon
from server import SSOT_LEXICON_PATH, SSOT_PATH, mcp


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

    assert set(bookend) == {"ssot_file", "hash_start", "hash_now", "drifted"}
    assert bookend["hash_now"] == expected_pointer_hash
    if expected_pointer_hash is not None:
        assert len(bookend["hash_start"]) == 16
        assert len(bookend["hash_now"]) == 16
        assert isinstance(bookend["drifted"], bool)

    narrative = tools["mas_narrative_scan"].fn("CLAUDE.md")
    assert narrative["ssot_hash"] == expected_lexicon_hash

    scan = tools["mas_scan"].fn("CLAUDE.md")
    assert scan["ssot_hash"] == expected_pointer_hash
    assert scan["scan_metadata"]["files_scanned"] == 1
