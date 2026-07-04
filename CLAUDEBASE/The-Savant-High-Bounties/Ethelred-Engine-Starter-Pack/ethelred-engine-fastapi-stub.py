#!/usr/bin/env python3
#-*- coding: utf-8 -*-

#SID: ETHELRED_ENGINE_FASTAPI_STUB_V1

from __future__ import annotations

from typing import Any, Literal
from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel, Field


app = FastAPI(
    title="Ethelred Gunnarsson Skill-Ideology Engine Actions",
    version="0.1.0",
)


class InputObject(BaseModel):
    type: str = "other"
    content: str
    surface_facts: list[str] = Field(default_factory=list)
    missing_facts: list[str] = Field(default_factory=list)
    visible_objects: list[str] = Field(default_factory=list)
    absent_agents: list[str] = Field(default_factory=list)
    material_context: list[str] = Field(default_factory=list)
    emotional_charge: list[str] = Field(default_factory=list)
    absurdity_seed: str | None = None
    escalation_paths: list[str] = Field(default_factory=list)


class VoiceLine(BaseModel):
    skill: str
    ideology: str
    ability: str | None = None
    pressure_score: float = 0.75
    utterance: str
    keep: bool = True


class CabinetRunRequest(BaseModel):
    input_object: InputObject
    mode: Literal["diagnose", "voices", "mutate", "bridge", "kill_report", "full_24", "canon_edit"] = "voices"
    persona: str = "ethelred_gunnarsson"
    active_ideologies: list[str] = Field(default_factory=lambda: [
        "forensic_criminal",
        "animist_object_agency",
        "labor_materialist",
    ])
    preferred_skills: list[str] = Field(default_factory=list)
    max_voices: int = Field(default=7, ge=1, le=24)
    output_density: Literal["minimal", "medium", "dense", "full"] = "medium"
    forbid_cleanup: bool = True
    allow_mutation: bool = True


class HumourRequest(BaseModel):
    input_object: InputObject
    persona: str = "ethelred_gunnarsson"
    active_ideologies: list[str] = Field(default_factory=lambda: [
        "forensic_criminal",
        "animist_object_agency",
        "labor_materialist",
    ])
    max_voices: int = Field(default=7, ge=1, le=24)
    forbid_cleanup: bool = True


class KillReportRequest(BaseModel):
    original_object: InputObject
    prior_response: str
    persona: str = "ethelred_gunnarsson"


class UtteranceRequest(BaseModel):
    input_object: InputObject
    persona: Literal["ethelred_gunnarsson"] = "ethelred_gunnarsson"
    stance: Literal[
        "dry_forensic",
        "broken_tribunal",
        "machine_inland",
        "bureaucratic_animist",
        "trade_haunted",
    ] = "broken_tribunal"
    selected_voices: list[VoiceLine] = Field(default_factory=list)
    max_length: int = Field(default=600, ge=50, le=2000)


class CanonPatchRequest(BaseModel):
    patch_goal: str
    operation: str | None = None
    target: str | None = None
    constraints: list[str] = Field(default_factory=list)
    dry_run: bool = True


def _facts(obj: InputObject) -> str:
    parts = []
    parts.extend(obj.surface_facts)
    parts.extend(obj.missing_facts)
    parts.extend(obj.visible_objects)
    parts.extend(obj.absent_agents)
    parts.extend(obj.material_context)
    return "; ".join(parts) if parts else obj.content


def _select_voice_lines(obj: InputObject, active_ideologies: list[str], max_voices: int) -> list[VoiceLine]:
    text = _facts(obj).lower()
    visible = ", ".join(obj.visible_objects) or "the visible scene"
    missing = ", ".join(obj.absent_agents or obj.missing_facts) or "the missing agent"

    candidates: list[VoiceLine] = [
        VoiceLine(
            skill="perception",
            ideology="forensic_criminal",
            ability="see_what_is_missing",
            pressure_score=0.92,
            utterance=f"{visible}. {missing} is absent. The scene is not empty; it is withholding names.",
        ),
        VoiceLine(
            skill="visual_calculus",
            ideology="forensic_criminal",
            ability="reconstruct_scene",
            pressure_score=0.88,
            utterance="The result is visible. The labour is not. The diagram has been cleaned before testimony.",
        ),
        VoiceLine(
            skill="inland_empire",
            ideology="animist_object_agency",
            ability="grant_agency_without_apology",
            pressure_score=0.86,
            utterance="The object knows what touched it. It has chosen the face of an innocent surface.",
        ),
        VoiceLine(
            skill="physical_instrument",
            ideology="trade_guild",
            ability="make_labor_heavy_again",
            pressure_score=0.84,
            utterance="Tools do not gather for decoration. Somewhere outside the frame, a body paid for the straight line.",
        ),
        VoiceLine(
            skill="rhetoric",
            ideology="moralist_bureaucratic",
            ability="invoice_language",
            pressure_score=0.80,
            utterance="Self-correcting material event: a phrase waiting to become paperwork once blame finds a desk.",
        ),
        VoiceLine(
            skill="savoir_faire",
            ideology="ultraliberal_hustle",
            ability="make_absence_profitable",
            pressure_score=0.78,
            utterance="A finished product with no visible production chain. Ugly ethics. Excellent margin shape.",
        ),
        VoiceLine(
            skill="composure",
            ideology="summary_sickness",
            ability="refuse_overexplaining",
            pressure_score=0.76,
            utterance="Do not make this cute. The object is funny because it nearly gets away with being normal.",
        ),
    ]

    if "scaffold" in text:
        candidates.insert(
            0,
            VoiceLine(
                skill="scaffold_sight",
                ideology="labor_materialist",
                ability="make_equipment_testify",
                pressure_score=0.95,
                utterance="The scaffold stayed behind as witness protection for the vanished workers.",
            ),
        )

    # Prefer explicitly requested skills when present.
    if obj.visible_objects or obj.absent_agents:
        pass

    return candidates[:max_voices]


@app.get("/v1/engine/manifest")
def read_engine_manifest() -> dict[str, Any]:
    return {
        "engine_name": "skill_ideology_humour_engine",
        "version": "0.1.0",
        "style": "cognitive_scaffold_noir",
        "canon_overlay": "disco_compatible_v0",
        "supported_modes": [
            "diagnose",
            "voices",
            "mutate",
            "bridge",
            "kill_report",
            "full_24",
            "canon_edit",
        ],
        "non_negotiables": [
            "no cleanup unless asked",
            "no punchline-first explanation",
            "preserve object-specific evidence",
            "preserve ideological distortion",
            "let voices disagree",
        ],
    }


@app.post("/v1/cabinet/run")
def run_cabinet_engine(req: CabinetRunRequest) -> dict[str, Any]:
    voices = _select_voice_lines(req.input_object, req.active_ideologies, req.max_voices)
    engine = (
        "Visible result plus missing labour turns the object into the only remaining suspect."
    )
    return {
        "engine": engine,
        "voices": [v.model_dump() for v in voices],
        "lock": "Do not polish the deformation into a normal joke; keep the absence active.",
        "optional_mutations": [
            "The object declined to name contractors pending structural counsel."
        ] if req.allow_mutation and req.mode == "mutate" else [],
        "debug": {
            "selected_skills": [v.skill for v in voices],
            "selected_ideologies": sorted({v.ideology for v in voices}),
            "pressure_tests": [
                "makes absence active",
                "preserves object specificity",
                "introduces biased worldview",
            ],
            "rejected_lines": [],
        },
    }


@app.post("/v1/utterance/ethelred")
def emit_ethelred_utterance(req: UtteranceRequest) -> dict[str, Any]:
    voices = req.selected_voices or _select_voice_lines(
        req.input_object,
        ["forensic_criminal", "animist_object_agency", "labor_materialist"],
        5,
    )
    utterance = "\n\n".join(
        f"[{v.skill.upper()} / {v.ideology.upper()}] — {v.utterance}" for v in voices
    )
    if len(utterance) > req.max_length:
        utterance = utterance[: req.max_length].rstrip() + "..."
    return {
        "persona": req.persona,
        "utterance": utterance,
        "voice_trace": [v.model_dump() for v in voices],
        "lock": "Selected voices remain separate. No polite synthesis.",
    }


@app.post("/v1/humour/diagnose")
def diagnose_humour_object(req: HumourRequest) -> dict[str, Any]:
    voices = _select_voice_lines(req.input_object, req.active_ideologies, req.max_voices)
    return {
        "engine": "An ordinary scene becomes funny because the evidence removes the actor and leaves the object to explain itself.",
        "load_bearing_damage": [
            "absence is treated as active evidence",
            "the object is allowed to behave like a suspect",
            "the scale escalates past the sane stopping point",
        ],
        "do_not_fix": [
            "do not normalize the syntax too early",
            "do not replace the object-agency with a cute mascot",
            "do not turn it into setup-punchline comedy",
        ],
        "active_skills": [v.skill for v in voices],
        "active_ideologies": sorted({v.ideology for v in voices}),
    }


@app.post("/v1/humour/mutate")
def mutate_in_world(req: HumourRequest) -> dict[str, Any]:
    return {
        "mutations": [
            "The scaffold remained on site to deny everything at height.",
            "The wall accepted no questions without a licensed witness present.",
        ],
        "mutation_rule": "Only add lines that feel latent in the source object; do not clean the original.",
    }


@app.post("/v1/humour/bridge")
def bridge_for_outsider(req: HumourRequest) -> dict[str, Any]:
    return {
        "bridge": (
            "The joke works because the visible result erases the people who did the work. "
            "The object then becomes the only thing left to blame, praise, invoice, or interrogate."
        ),
        "preserved_deformation": [
            "missing worker evidence",
            "object agency",
            "wrong-scale seriousness",
            "bureaucratic/financial aftershock",
        ],
    }


@app.post("/v1/humour/kill-report")
def generate_kill_report(req: KillReportRequest) -> dict[str, Any]:
    return {
        "kill_mechanism": "The response likely converted unstable deformation into normal explanatory joke architecture.",
        "specific_damage": [
            "explained before inhabiting the object",
            "replaced faculty collision with a single narrator",
            "over-cleaned the malformed pressure",
        ],
        "lost_material": [
            "object-specific evidence",
            "absence as suspect",
            "material labour",
            "ideological contamination",
        ],
        "repair_law": "Return to the object as scene evidence. Let selected skills speak separately.",
    }


@app.post("/v1/canon/patch")
def propose_canon_patch(req: CanonPatchRequest) -> dict[str, Any]:
    return {
        "patch_id": f"patch_{uuid4().hex[:8]}",
        "summary": f"Proposed canon patch for: {req.patch_goal}",
        "proposed_changes": [
            {
                "operation": req.operation or "canon_edit",
                "target": req.target or "engine",
                "constraints": req.constraints,
                "dry_run": req.dry_run,
            }
        ],
        "mutation_ledger_entry": {
            "version": "0.1.0",
            "change": req.patch_goal,
            "status": "proposed" if req.dry_run else "apply_requested",
        },
        "apply_warning": "Review before applying. Canon mutation should alter function, not only names.",
    }
