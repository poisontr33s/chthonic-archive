#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: ssot_manifest.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 📜 THE SCRIPTORIUM
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ mas_mcp/logic/ssot_binding.py
# ║   └─◄ mas_mcp/server.py
# ╚════════════════════════════════════════════════════════════════════════════

"""
ssot_manifest.py — Canon Declaration Layer for SSOT Identity.

@SID:           LOGIC_SSOT_MANIFEST_V1
@Shabti:        Domain Logic (Governance)
@Lineage:       Born from LOGIC_SSOT_BINDING_V4 cascade analysis
@Purpose:       Single source of truth for SSOT identity, roles, and
                provenance contracts. Filenames are mutable aliases;
                role identity is not. Everything in the archive becomes
                legibly accountable to the SSOT through this manifest.

Canon Contract:
  - copilot-instructions.archive.md is the canonical HOLDER.
  - copilot-instructions.md is the operational POINTER (minified surface).
  - All supporting files must declare which one they bind to and why.
  - If a filename changes, THIS FILE changes first. Everything else
    resolves through it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional


# ─────────────────────────────────────────────────────────────────────────────
# Canonical SSOT Paths — THE single source for filenames
# ─────────────────────────────────────────────────────────────────────────────
# If filenames change, change ONLY HERE. Everything else resolves through this.

SSOT_HOLDER_RELPATH = ".github/copilot-instructions.archive.md"
SSOT_POINTER_RELPATH = ".github/copilot-instructions.md"
SSOT_PROTO_RELPATH = ".github/copilot-instructions-copy.md"


# ─────────────────────────────────────────────────────────────────────────────
# SSOT Role Taxonomy
# ─────────────────────────────────────────────────────────────────────────────
# Every SSOT-adjacent artifact must declare exactly one role.
# If a file cannot be assigned one, it is likely ornamental drift.

SSOTRole = Literal[
    "holder",       # Canonical body (the archive itself)
    "pointer",      # Minified operational surface
    "projection",   # Derived readable form (e.g., generated readable SSOT)
    "validator",    # Checks SSOT integrity (tests, audit scripts)
    "journal",      # Records SSOT state transitions
    "artifact",     # Generated against a specific SSOT state
    "bridge",       # Translates SSOT into another runtime/language/domain
]

SSOT_ROLES: List[str] = list(SSOTRole.__args__)


# ─────────────────────────────────────────────────────────────────────────────
# Relation Taxonomy — classifies every SSOT-derived artifact
# ─────────────────────────────────────────────────────────────────────────────
# Before creating or repurposing any file, classify it.

SSOTRelation = Literal[
    "authoritative",  # Canon — the source itself
    "summarizing",    # Condensed view of canon
    "indexing",       # Navigation/lookup into canon
    "validating",     # Integrity checks against canon
    "projecting",     # Derived form for consumption
    "caching",        # Memoized/precomputed from canon
    "historizing",    # Records canon evolution over time
]

SSOT_RELATIONS: List[str] = list(SSOTRelation.__args__)


# ─────────────────────────────────────────────────────────────────────────────
# Provenance Contract — minimal metadata every SSOT-derived artifact carries
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SSOTProvenance:
    """
    Every SSOT-derived artifact should conceptually carry this contract.
    Three layers that coexist:
      1. Exact anchor:      sha256
      2. Readable vitals:   semantic fingerprint
      3. Relationship note: which source, in what role, for what purpose
    """
    source_role: SSOTRole
    source_identity: str          # Stable semantic identity, e.g. "holder" or "pointer"
    source_path: str              # Current filesystem path (mutable alias)
    source_hash: str              # SHA-256 (exact anchor)
    source_fingerprint: str       # Semantic vitals label, e.g. "L1504·E7·S204·955K"
    derived_from: str             # What the artifact was produced from
    last_verified_at: str         # ISO 8601 timestamp of last verification

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_role": self.source_role,
            "source_identity": self.source_identity,
            "source_path": self.source_path,
            "source_hash": self.source_hash,
            "source_fingerprint": self.source_fingerprint,
            "derived_from": self.derived_from,
            "last_verified_at": self.last_verified_at,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SSOTProvenance":
        return cls(
            source_role=d["source_role"],
            source_identity=d["source_identity"],
            source_path=d["source_path"],
            source_hash=d["source_hash"],
            source_fingerprint=d["source_fingerprint"],
            derived_from=d["derived_from"],
            last_verified_at=d["last_verified_at"],
        )

    @classmethod
    def stamp_now(
        cls,
        role: SSOTRole,
        identity: str,
        path: str,
        sha256: str,
        fingerprint: str,
        derived_from: str,
    ) -> "SSOTProvenance":
        return cls(
            source_role=role,
            source_identity=identity,
            source_path=path,
            source_hash=sha256,
            source_fingerprint=fingerprint,
            derived_from=derived_from,
            last_verified_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )


# ─────────────────────────────────────────────────────────────────────────────
# Cascade Register — declared map of all SSOT-adjacent targets
# ─────────────────────────────────────────────────────────────────────────────
# When a filename changes, the cascade register is the only thing
# that must change first. Everything else resolves through it.

@dataclass
class CascadeEntry:
    """One entry in the cascade register."""
    role: SSOTRole
    identity: str          # Stable semantic name: "holder", "pointer", "proto"
    relpath: str           # Current relative path from repo root
    relation: SSOTRelation
    description: str

CASCADE_REGISTER: List[CascadeEntry] = [
    # ── Canonical Sources ────────────────────────────────────────────────────
    CascadeEntry(
        role="holder",
        identity="holder",
        relpath=SSOT_HOLDER_RELPATH,
        relation="authoritative",
        description="Canonical SSOT archive — months of creative work, full entity data",
    ),
    CascadeEntry(
        role="pointer",
        identity="pointer",
        relpath=SSOT_POINTER_RELPATH,
        relation="summarizing",
        description="Operational pointer — minified surface for context-budget compliance",
    ),
    CascadeEntry(
        role="pointer",
        identity="proto",
        relpath=SSOT_PROTO_RELPATH,
        relation="historizing",
        description="Proto-SSOT safe fork — reference only, not auto-loaded",
    ),
    # ── Journals ─────────────────────────────────────────────────────────────
    CascadeEntry(
        role="journal",
        identity="hash_journal",
        relpath=".mas_mcp/ssot_hash_journal.jsonl",
        relation="historizing",
        description="Persistent SSOT state timeline — stamped at threshold events",
    ),
    # ── Validators ───────────────────────────────────────────────────────────
    CascadeEntry(
        role="validator",
        identity="ssot_binding",
        relpath="mas_mcp/logic/ssot_binding.py",
        relation="validating",
        description="Cryptographic + semantic binding: SHA-256, vitals fingerprint, drift detection",
    ),
    CascadeEntry(
        role="validator",
        identity="ssot_binding_tests",
        relpath="mas_mcp/tests/test_ssot_binding.py",
        relation="validating",
        description="14-test suite verifying manifest, binding, provenance, and cascade integrity",
    ),
    # ── Projections (readable/navigable derived forms) ───────────────────────
    CascadeEntry(
        role="projection",
        identity="readable_ssot_generator",
        relpath="scripts/generate_readable_ssot.py",
        relation="projecting",
        description="Generates readable SSOT from pointer — derived human form",
    ),
    CascadeEntry(
        role="projection",
        identity="structural_extractor",
        relpath="scripts/ssot_structural_extractor.py",
        relation="indexing",
        description="Extracts heading tree + section structure from holder archive",
    ),
    CascadeEntry(
        role="projection",
        identity="loremaster",
        relpath="scripts/ssot_loremaster.py",
        relation="indexing",
        description="Holder mirror management, section queue, and archive navigation",
    ),
    # ── Bridges (cross-domain translators) ──────────────────────────────────
    CascadeEntry(
        role="bridge",
        identity="ssot_paths_bridge",
        relpath="scripts/lib/ssot_paths.py",
        relation="indexing",
        description="Thin re-export bridge for scripts/ — resolves SSOT paths from manifest",
    ),
    CascadeEntry(
        role="bridge",
        identity="asc_injector",
        relpath="scripts/mcp-asc-injector.ts",
        relation="projecting",
        description="TypeScript MCP server — injects SSOT into Copilot context via stdio",
    ),
    # ── Artifacts (generated against specific SSOT state) ────────────────────
    CascadeEntry(
        role="artifact",
        identity="narrative_scan_runner",
        relpath="scripts/run_narrative_scan.py",
        relation="validating",
        description="CLI runner for cultural drift scanning against SSOT lexicon",
    ),
    CascadeEntry(
        role="artifact",
        identity="run_cycle",
        relpath="scripts/run_cycle.py",
        relation="validating",
        description="Full audit cycle runner — hashes SSOT + orchestrates scan/audit pipeline",
    ),
    CascadeEntry(
        role="artifact",
        identity="ssot_extractor",
        relpath="mas_mcp/ssot_extractor.py",
        relation="indexing",
        description="Structured entity/section extraction from SSOT content",
    ),
    CascadeEntry(
        role="artifact",
        identity="abbreviation_cli",
        relpath="mas_mcp/abbreviation_system/cli.py",
        relation="indexing",
        description="Abbreviation system CLI — reads SSOT for canonical abbreviation registry",
    ),
]


# ─────────────────────────────────────────────────────────────────────────────
# Journal Event Taxonomy — sparse, threshold-only
# ─────────────────────────────────────────────────────────────────────────────
# Journal state transitions, not every breath.

JournalEvent = Literal[
    "startup_stamp",              # Server/session initialization
    "drift_detected",             # SSOT content changed since last stamp
    "manual_reseal",              # Operator explicitly re-sealed SSOT state
    "artifact_emitted",           # An artifact was generated against current SSOT state
    "holder_pointer_divergence",  # Holder and pointer disagree (structural split)
]

JOURNAL_EVENTS: List[str] = list(JournalEvent.__args__)


def resolve_cascade_entry(identity: str) -> Optional[CascadeEntry]:
    """Look up a cascade entry by stable semantic identity."""
    for entry in CASCADE_REGISTER:
        if entry.identity == identity:
            return entry
    return None


def cascade_register_to_dict() -> List[Dict[str, str]]:
    """Export the cascade register as a serializable list."""
    return [
        {
            "role": e.role,
            "identity": e.identity,
            "relpath": e.relpath,
            "relation": e.relation,
            "description": e.description,
        }
        for e in CASCADE_REGISTER
    ]
