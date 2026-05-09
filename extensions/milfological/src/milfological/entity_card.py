#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
entity_card.py — MILFOLOGICAL EntityCard (CharCard V2 superset)

Derives from CharCard V2 specification:
    https://github.com/malfoyslastname/character-card-spec-v2/blob/main/spec_v2.md

EntityCard is the MILFOLOGICAL canonical entity metadata format.
It is a strict superset of TavernCardV2: every EntityCard is a valid CharCard V2.
MILFOLOGICAL-specific fields live inside the `extensions["milfological"]` namespace.

Cross-refs:
    SD_CANDIDATE_REGISTRY.md §C18 [O8]
    MILFOLOGICAL_OPPORTUNITY_REPORT.md §XIV (entity identity surface)
    protocols.py — SDBackend / SegmentationBackend / PixelArtBackend
    entity_cutout.py — RGBA cutout source (feeds entity card avatar_path)

Schema hierarchy:
    EntityCard
    └── data: EntityCardData          ← TavernCardV2.data superset
        └── character_book: CharacterBook  ← lorebook (CharCard V2 canonical)
            └── entries: list[LoreEntry]

CharCard V2 field inventory (from spec):
    V1 fields (nested in data):
        name, description, personality, scenario, first_mes, mes_example
    V2 additions:
        creator_notes, system_prompt, post_history_instructions,
        alternate_greetings, character_book, tags, creator,
        character_version, extensions

MILFOLOGICAL extensions namespace ("milfological"):
    tier            — Triumvirate/Cardinal/Penarch/Sub-MILF designation
    organ           — Thalamus/Heart/etc. (Pentad organ assignment)
    prism           — PRISM colour + symbol (e.g. "GOLD 🏰 Fortress")
    whr_score       — WHR:MAX abstraction score (0.0–1.0)
    ssot_ref        — Canonical SSOT anchor (§section / line range)
    entity_class    — MILF / Sub-MILF / Pentad / Triumvirate / etc.
    avatar_path     — Local path to entity cutout PNG (entity_cutout.py output)
    sprite_path     — Local path to pixel-art sprite (entity_pixelart.py output)
    linguistic_profile — LUPLR / LIPAA / EULP-AA / etc.
    district        — Skyskraperen / Rustbeltet / Future
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ─── CharCard V2 Lorebook ────────────────────────────────────────────────────


@dataclass
class LoreEntry:
    """Single entry in a CharacterBook lorebook (CharCard V2 spec)."""

    keys: list[str]
    content: str
    enabled: bool
    insertion_order: int
    extensions: dict[str, Any] = field(default_factory=dict)

    # Optional CharCard V2 fields
    case_sensitive: bool | None = None
    name: str | None = None
    priority: int | None = None
    id: int | None = None
    comment: str | None = None
    selective: bool | None = None
    secondary_keys: list[str] | None = None
    constant: bool | None = None
    position: str | None = None  # 'before_char' | 'after_char'

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "keys": self.keys,
            "content": self.content,
            "enabled": self.enabled,
            "insertion_order": self.insertion_order,
            "extensions": self.extensions,
        }
        optionals = (
            "case_sensitive", "name", "priority", "id",
            "comment", "selective", "secondary_keys", "constant", "position",
        )
        for attr in optionals:
            val = getattr(self, attr)
            if val is not None:
                d[attr] = val
        return d


@dataclass
class CharacterBook:
    """Character-specific lorebook (CharCard V2 spec)."""

    entries: list[LoreEntry] = field(default_factory=list)
    extensions: dict[str, Any] = field(default_factory=dict)

    # Optional CharCard V2 fields
    name: str | None = None
    description: str | None = None
    scan_depth: int | None = None
    token_budget: int | None = None
    recursive_scanning: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "entries": [e.to_dict() for e in self.entries],
            "extensions": self.extensions,
        }
        optionals = ("name", "description", "scan_depth", "token_budget", "recursive_scanning")
        for attr in optionals:
            val = getattr(self, attr)
            if val is not None:
                d[attr] = val
        return d


# ─── MILFOLOGICAL extension payload ──────────────────────────────────────────


@dataclass
class MilfologicalMeta:
    """
    MILFOLOGICAL-specific metadata stored in extensions["milfological"].

    All fields are optional — EntityCard is still a valid CharCard V2 if
    MilfologicalMeta is absent or partially populated.
    """

    tier: str | None = None            # "T1 Triumvirate" / "T1-bridge" / "T2" / etc.
    organ: str | None = None           # "Thalamus" / "Heart" / etc.
    prism: str | None = None           # "GOLD 🏰 Fortress"
    whr_score: float | None = None     # WHR:MAX abstraction score 0.0–1.0
    ssot_ref: str | None = None        # "§10.3.1 / line 4450+"
    entity_class: str | None = None    # "MILF" / "Sub-MILF" / "Pentad" / etc.
    avatar_path: str | None = None     # path to entity_cutout.py RGBA output
    sprite_path: str | None = None     # path to entity_pixelart.py sprite sheet
    linguistic_profile: str | None = None  # "LUPLR" / "LIPAA" / "EULP-AA"
    district: str | None = None        # "Skyskraperen" / "Rustbeltet" / "Future"

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in {
            "tier": self.tier,
            "organ": self.organ,
            "prism": self.prism,
            "whr_score": self.whr_score,
            "ssot_ref": self.ssot_ref,
            "entity_class": self.entity_class,
            "avatar_path": self.avatar_path,
            "sprite_path": self.sprite_path,
            "linguistic_profile": self.linguistic_profile,
            "district": self.district,
        }.items() if v is not None}


# ─── EntityCard (CharCard V2 superset) ───────────────────────────────────────


@dataclass
class EntityCardData:
    """
    TavernCardV2.data superset.

    V1 fields (required by CharCard V1/V2):
        name, description, personality, scenario, first_mes, mes_example
    V2 additions:
        creator_notes, system_prompt, post_history_instructions,
        alternate_greetings, character_book, tags, creator,
        character_version, extensions
    MILFOLOGICAL:
        milfological field in extensions["milfological"] via MilfologicalMeta
    """

    # ── V1 required ──────────────────────────────────────────────────────────
    name: str = ""
    description: str = ""
    personality: str = ""
    scenario: str = ""
    first_mes: str = ""
    mes_example: str = ""

    # ── V2 additions ─────────────────────────────────────────────────────────
    creator_notes: str = ""
    system_prompt: str = ""
    post_history_instructions: str = ""
    alternate_greetings: list[str] = field(default_factory=list)
    character_book: CharacterBook | None = None
    tags: list[str] = field(default_factory=list)
    creator: str = ""
    character_version: str = ""
    extensions: dict[str, Any] = field(default_factory=dict)

    # ── MILFOLOGICAL convenience accessor ────────────────────────────────────
    milfological: MilfologicalMeta | None = None

    def to_dict(self) -> dict[str, Any]:
        ext = dict(self.extensions)
        if self.milfological is not None:
            ext["milfological"] = self.milfological.to_dict()

        d: dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "personality": self.personality,
            "scenario": self.scenario,
            "first_mes": self.first_mes,
            "mes_example": self.mes_example,
            "creator_notes": self.creator_notes,
            "system_prompt": self.system_prompt,
            "post_history_instructions": self.post_history_instructions,
            "alternate_greetings": self.alternate_greetings,
            "tags": self.tags,
            "creator": self.creator,
            "character_version": self.character_version,
            "extensions": ext,
        }
        if self.character_book is not None:
            d["character_book"] = self.character_book.to_dict()
        return d


@dataclass
class EntityCard:
    """
    MILFOLOGICAL EntityCard — CharCard V2 compliant envelope.

    Every EntityCard serialises to a valid TavernCardV2 JSON object:
        { "spec": "chara_card_v2", "spec_version": "2.0", "data": { ... } }

    Usage:
        card = EntityCard(data=EntityCardData(
            name="Claudine Sin'claire 3.7 'Inch' — Blunderbust",
            description="Supreme Meta-MILF Matriarch ...",
            milfological=MilfologicalMeta(
                tier="T1 Triumvirate",
                organ="Thalamus",
                prism="GOLD 🏰 Fortress",
                whr_score=1.0,
                ssot_ref="§10.3.1 / line 4450+",
                entity_class="MILF",
                linguistic_profile="LUPLR",
                district="Skyskraperen",
            ),
        ))
        card.save(Path("claudine.json"))
    """

    spec: str = "chara_card_v2"
    spec_version: str = "2.0"
    data: EntityCardData = field(default_factory=EntityCardData)

    # ── Serialisation ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        return {
            "spec": self.spec,
            "spec_version": self.spec_version,
            "data": self.data.to_dict(),
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def save(self, path: Path, indent: int = 2) -> None:
        path.write_text(self.to_json(indent=indent), encoding="utf-8")

    # ── Deserialisation ───────────────────────────────────────────────────────

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "EntityCard":
        """
        Load from a raw CharCard V2 dict.
        Accepts both V1 (flat) and V2 (data-nested) shapes.
        Preserves unknown extensions keys per spec ("MUST NOT destroy").
        """
        if "data" in d:
            # V2 shape
            raw = dict(d["data"])
            spec = d.get("spec", "chara_card_v2")
            spec_version = d.get("spec_version", "2.0")
        else:
            # V1 flat shape — wrap into V2
            raw = dict(d)
            spec = "chara_card_v2"
            spec_version = "2.0"

        extensions = dict(raw.pop("extensions", {}))
        milf_raw = extensions.pop("milfological", None)
        milfological = MilfologicalMeta(**{
            k: v for k, v in milf_raw.items()
            if k in MilfologicalMeta.__dataclass_fields__
        }) if milf_raw else None

        # character_book
        cb_raw = raw.pop("character_book", None)
        character_book: CharacterBook | None = None
        if cb_raw:
            entries = [
                LoreEntry(**{k: v for k, v in e.items() if k in LoreEntry.__dataclass_fields__})
                for e in cb_raw.get("entries", [])
            ]
            character_book = CharacterBook(
                entries=entries,
                extensions=cb_raw.get("extensions", {}),
                name=cb_raw.get("name"),
                description=cb_raw.get("description"),
                scan_depth=cb_raw.get("scan_depth"),
                token_budget=cb_raw.get("token_budget"),
                recursive_scanning=cb_raw.get("recursive_scanning"),
            )

        data = EntityCardData(
            name=raw.get("name", ""),
            description=raw.get("description", ""),
            personality=raw.get("personality", ""),
            scenario=raw.get("scenario", ""),
            first_mes=raw.get("first_mes", ""),
            mes_example=raw.get("mes_example", ""),
            creator_notes=raw.get("creator_notes", ""),
            system_prompt=raw.get("system_prompt", ""),
            post_history_instructions=raw.get("post_history_instructions", ""),
            alternate_greetings=raw.get("alternate_greetings", []),
            character_book=character_book,
            tags=raw.get("tags", []),
            creator=raw.get("creator", ""),
            character_version=raw.get("character_version", ""),
            extensions=extensions,
            milfological=milfological,
        )
        return cls(spec=spec, spec_version=spec_version, data=data)

    @classmethod
    def load(cls, path: Path) -> "EntityCard":
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))
