#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: polish_skill.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🔥 THE FOUNDRY
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
The Digestive Enzyme (Skill Polisher Implementation).
Audits skill directories for structural integrity, missing assets, and code gaps.
Implements the 'Addiction' protocol with recursive improvement loops.

@SID:           TOOL_POLISH_SKILL_V1
@Shabti:        CLI Script
@Purpose:       The Digestive Enzyme (Skill Polisher Implementation).
"""

import ast
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

DOMAIN_WEIGHTS = {
    "structure": 30,
    "policy": 25,
    "semantics": 25,
    "maintainability": 20,
}

SEVERITY_PENALTIES = {
    "CRITICAL": 30,
    "WARN": 15,
    "INFO": 0,
}


def die(msg: str) -> None:
    print(f"FAILED: {msg}")
    sys.exit(1)


def stdout_supports_unicode() -> bool:
    encoding = (sys.stdout.encoding or "").lower().replace("-", "")
    return encoding in {"utf8", "utf_8"}


@dataclass
class IssueRecord:
    stamp: str
    severity: str
    domain: str
    file: str
    line: int | None
    msg: str
    remedy: str
    confidence: float


@dataclass
class WPTGStageRecord:
    stage_id: str
    stage_name: str
    met: bool
    evidence: list[str]
    gaps: list[str]


@dataclass
class FixAction:
    stamp: str
    remedy: str
    fn: callable


class SkillDigest:
    def __init__(
        self,
        skill_path: Path,
        *,
        target_flavor: str = "codex",
        require_assets: bool = True,
        wptg_profile: str = "off",
    ):
        self.path = skill_path
        self.name = skill_path.name
        self.target_flavor = target_flavor
        self.require_assets = require_assets
        self.wptg_profile = wptg_profile
        self.issues: list[IssueRecord] = []
        self.wptg_stages: list[WPTGStageRecord] = []
        self.wptg_score = 0
        self.score = 100
        self.domain_scores: dict[str, int] = {k: 100 for k in DOMAIN_WEIGHTS}
        self.fixable_actions: list[FixAction] = []
        self.applied_fixes: list[str] = []

    def log_issue(
        self,
        severity: str,
        msg: str,
        stamp: str,
        remedy: str,
        fix_action=None,
        domain: str = "maintainability",
        file: str = "SKILL.md",
        line: int | None = None,
        confidence: float = 0.9,
    ) -> None:
        self.issues.append(
            IssueRecord(
                stamp=stamp,
                severity=severity,
                domain=domain,
                file=file,
                line=line,
                msg=msg,
                remedy=remedy,
                confidence=confidence,
            )
        )
        if fix_action:
            self.fixable_actions.append(FixAction(stamp=stamp, remedy=remedy, fn=fix_action))

    def finalize_scores(self) -> None:
        scores = {k: 100 for k in DOMAIN_WEIGHTS}
        for issue in self.issues:
            penalty = SEVERITY_PENALTIES.get(issue.severity, 0)
            scores[issue.domain] = max(0, scores[issue.domain] - penalty)
        self.domain_scores = scores
        weighted = 0.0
        for domain, weight in DOMAIN_WEIGHTS.items():
            weighted += (scores[domain] * weight) / 100.0
        self.score = int(round(weighted))

    def has_fixable_entropy(self) -> bool:
        if not self.fixable_actions:
            return False
        return any(i.severity in {"CRITICAL", "WARN"} for i in self.issues)

    def check_structure(self) -> None:
        if not (self.path / "SKILL.md").exists():
            self.log_issue(
                "CRITICAL",
                "Missing SKILL.md",
                "#FIXME",
                "Create SKILL.md with required frontmatter and deterministic workflow.",
            )

        # Flavor-aware structural checks.
        # - Codex: requires agents/openai.yaml.
        # - Claude: requires strict frontmatter fields (name, description).
        target = self._resolve_target_flavor()
        is_claude = target == "claude"
        is_gemini = target == "gemini"
        yaml_path = self.path / "agents/openai.yaml"
        if not is_claude and not is_gemini and not yaml_path.exists():
            self.log_issue(
                "CRITICAL",
                "Missing agents/openai.yaml",
                "#FIXME",
                "Add agents/openai.yaml with valid metadata and model routing.",
                self._scaffold_openai_yaml,
            )

        if is_claude:
            self._require_claude_frontmatter()
        if is_gemini:
            self._require_gemini_frontmatter()

        if not self.require_assets:
            return

        if not (self.path / "assets").exists():
            self.log_issue(
                "WARN",
                "Missing assets/ directory",
                "#TODO",
                "Create assets/ and add at least one canonical SVG icon.",
                lambda: (self.path / "assets").mkdir(exist_ok=True),
            )
        else:
            svgs = list((self.path / "assets").glob("*.svg"))
            if not svgs:
                self.log_issue(
                    "WARN",
                    "No SVG icon found in assets/",
                    "#TODO",
                    "Add canonical SVG icon files; placeholder can be temporary.",
                    self._ensure_canonical_icons,
                )
            else:
                self._check_canonical_icon_filenames()

    def _is_claude_skill(self) -> bool:
        skill_md = self.path / "SKILL.md"
        if not skill_md.exists():
            return False
        raw = skill_md.read_text(encoding="utf-8", errors="ignore").lower()
        # Claude Code skill frontmatter commonly includes these knobs.
        return ("allowed-tools" in raw) or ("disable-model-invocation" in raw) or ("user-invocable" in raw)

    def _resolve_target_flavor(self) -> str:
        if self.target_flavor in {"codex", "claude", "gemini"}:
            return self.target_flavor
        # auto
        return "claude" if self._is_claude_skill() else "codex"

    def _require_claude_frontmatter(self) -> None:
        skill_md = self.path / "SKILL.md"
        if not skill_md.exists():
            return
        raw = skill_md.read_text(encoding="utf-8", errors="ignore")
        stripped = raw.lstrip()
        if not stripped.startswith("---"):
            self.log_issue(
                "CRITICAL",
                "Claude skill missing frontmatter fence at top.",
                "#FIXME",
                "Add YAML frontmatter with at least `name` and `description`.",
            )
            return
        lower = raw.lower()
        if "name:" not in lower:
            self.log_issue(
                "CRITICAL",
                "Claude skill frontmatter missing `name:` field.",
                "#FIXME",
                "Add `name:` to SKILL.md frontmatter.",
            )
        # Require a non-empty description for Claude flavor.
        m = re.search(r"(?m)^description[ \t]*:[ \t]*(.*)$", raw)
        if m is None or not m.group(1).strip():
            self.log_issue(
                "CRITICAL",
                "Claude skill frontmatter missing `description:` field.",
                "#FIXME",
                "Add `description:` to SKILL.md frontmatter.",
            )

    def _require_gemini_frontmatter(self) -> None:
        skill_md = self.path / "SKILL.md"
        if not skill_md.exists():
            return
        raw = skill_md.read_text(encoding="utf-8", errors="ignore")
        stripped = raw.lstrip()
        if not stripped.startswith("---"):
            self.log_issue(
                "CRITICAL",
                "Gemini skill missing frontmatter fence at top.",
                "#FIXME",
                "Add YAML frontmatter with at least `name` and `description`.",
            )
            return
        lower = raw.lower()
        if "name:" not in lower:
            self.log_issue(
                "CRITICAL",
                "Gemini skill frontmatter missing `name:` field.",
                "#FIXME",
                "Add `name:` to SKILL.md frontmatter.",
            )
        m = re.search(r"(?m)^description[ \t]*:[ \t]*(.*)$", raw)
        if m is None or not m.group(1).strip():
            self.log_issue(
                "CRITICAL",
                "Gemini skill frontmatter missing `description:` field.",
                "#FIXME",
                "Add `description:` to SKILL.md frontmatter.",
            )

    def _extract_code_fence_lines(self, text: str) -> list[str]:
        lines = text.splitlines()
        in_fence = False
        extracted: list[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence and stripped:
                extracted.append(stripped)
        return extracted

    def _record_wptg_stage(
        self,
        *,
        stage_id: str,
        stage_name: str,
        met: bool,
        evidence: list[str],
        gaps: list[str],
        remedy: str,
    ) -> None:
        self.wptg_stages.append(
            WPTGStageRecord(
                stage_id=stage_id,
                stage_name=stage_name,
                met=met,
                evidence=evidence,
                gaps=gaps,
            )
        )
        if met or self.wptg_profile == "off":
            return
        severity = "INFO"
        if self.wptg_profile == "strict":
            if stage_id in {"03", "04", "05"}:
                severity = "CRITICAL"
            elif stage_id in {"00", "01", "02", "06"}:
                severity = "WARN"
        self.log_issue(
            severity,
            f"WPTG stage {stage_id} `{stage_name}` missing evidence.",
            "#WPTG",
            remedy,
            domain="maintainability",
            file="SKILL.md",
            confidence=0.8,
        )

    def audit_wptg_transition(self) -> None:
        if self.wptg_profile == "off":
            return
        skill_md = self.path / "SKILL.md"
        if not skill_md.exists():
            return
        raw = skill_md.read_text(encoding="utf-8", errors="ignore")
        lower = raw.lower()

        code_lines = [line.lower() for line in self._extract_code_fence_lines(raw)]
        command_markers = (
            "uv run ",
            "bun ",
            "pwsh ",
            "cargo ",
            "go test",
            "pytest",
            "npm ",
            "node ",
            "ruby ",
        )
        command_lines = [line for line in code_lines if any(marker in line for marker in command_markers)]
        links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", raw)

        references_dir = self.path / "references"
        fixtures_dir = self.path / "fixtures"
        scripts_dir = self.path / "scripts"
        script_files = []
        if scripts_dir.exists():
            script_files = [
                p
                for p in scripts_dir.glob("*")
                if p.is_file()
                and p.suffix.lower() in {".py", ".ps1", ".ts", ".js", ".mjs", ".cjs", ".rb", ".go", ".rs", ".sh"}
            ]

        has_frontmatter_keys = ("name:" in lower) and ("description:" in lower)
        has_use_contract = ("when to use" in lower) or ("triggers:" in lower) or ("use when" in lower)
        has_flavor_scope = ("target-flavor" in lower) or ("cross-flavor" in lower) or ("flavor" in lower)
        has_cross_reference = (len(links) >= 2) or references_dir.exists() or ("cross-reference" in lower)
        has_criteria = any(
            token in lower
            for token in ("verify", "validation", "gate", "criteria", "threshold", "acceptance")
        )
        has_execution = bool(script_files) and bool(command_lines)
        has_verification = fixtures_dir.exists() or any(
            token in lower for token in ("--mode verify", "fixture-eval", "selftest", "regression")
        )
        has_iteration = any(
            token in lower
            for token in ("@polished", "--emit-trend-json", "retrospective", "baseline promotion", "history")
        )

        stage_00_evidence = []
        if has_frontmatter_keys:
            stage_00_evidence.append("frontmatter keys present")
        if has_use_contract:
            stage_00_evidence.append("use contract present")
        stage_00_gaps = []
        if not has_frontmatter_keys:
            stage_00_gaps.append("missing frontmatter keys")
        if not has_use_contract:
            stage_00_gaps.append("missing use contract")

        self._record_wptg_stage(
            stage_id="00",
            stage_name="Blind Ingestion",
            met=has_frontmatter_keys and has_use_contract,
            evidence=stage_00_evidence,
            gaps=stage_00_gaps,
            remedy="Add explicit intake contract in SKILL.md (`name`, `description`, `When to Use`/`triggers`).",
        )
        self._record_wptg_stage(
            stage_id="01",
            stage_name="Emergent Taxonomy",
            met=has_flavor_scope,
            evidence=["flavor/scope contract"] if has_flavor_scope else [],
            gaps=[] if has_flavor_scope else ["no flavor/scope derivation language"],
            remedy="Declare target flavor/scope and classification logic used by the skill.",
        )
        stage_02_evidence = []
        if len(links) >= 2:
            stage_02_evidence.append("links to related artifacts")
        if references_dir.exists():
            stage_02_evidence.append("references/ directory")
        self._record_wptg_stage(
            stage_id="02",
            stage_name="Cartography",
            met=has_cross_reference,
            evidence=stage_02_evidence,
            gaps=[] if has_cross_reference else ["no relationship mapping to neighboring artifacts"],
            remedy="Add cross-reference mapping to protocols/scripts/references this skill depends on.",
        )
        self._record_wptg_stage(
            stage_id="03",
            stage_name="Criterion Genesis",
            met=has_criteria,
            evidence=["verification/gate criteria present"] if has_criteria else [],
            gaps=[] if has_criteria else ["missing measurable criteria/gates"],
            remedy="Define measurable verification criteria (gates, thresholds, acceptance checks).",
        )
        stage_04_evidence = []
        if script_files:
            stage_04_evidence.append("script implementation present")
        if command_lines:
            stage_04_evidence.append("executable command snippets present")
        stage_04_gaps = []
        if not script_files:
            stage_04_gaps.append("missing scripts/")
        if not command_lines:
            stage_04_gaps.append("missing executable command snippets")
        self._record_wptg_stage(
            stage_id="04",
            stage_name="Transmutation",
            met=has_execution,
            evidence=stage_04_evidence,
            gaps=stage_04_gaps,
            remedy="Provide concrete script-backed execution commands, not prose-only instructions.",
        )
        self._record_wptg_stage(
            stage_id="05",
            stage_name="Verification",
            met=has_verification,
            evidence=["fixture/selftest evidence present"] if has_verification else [],
            gaps=[] if has_verification else ["missing self-test/fixture/verify evidence"],
            remedy="Add a deterministic verification path (verify mode, fixture eval, or selftest).",
        )
        self._record_wptg_stage(
            stage_id="06",
            stage_name="Iteration",
            met=has_iteration,
            evidence=["iteration/trend evidence present"] if has_iteration else [],
            gaps=[] if has_iteration else ["missing iteration memory (trend/history/baseline promotion)"],
            remedy="Add iteration memory (trend log, retrospective note, or baseline promotion trail).",
        )
        met_count = sum(1 for stage in self.wptg_stages if stage.met)
        self.wptg_score = int(round((met_count / max(len(self.wptg_stages), 1)) * 100))

    def wptg_snapshot(self) -> dict:
        if not self.wptg_stages:
            return {
                "enabled": False,
                "profile": self.wptg_profile,
                "score": 0,
                "met": 0,
                "total": 0,
                "stages": [],
            }
        met_count = sum(1 for stage in self.wptg_stages if stage.met)
        return {
            "enabled": self.wptg_profile != "off",
            "profile": self.wptg_profile,
            "score": self.wptg_score,
            "met": met_count,
            "total": len(self.wptg_stages),
            "stages": [
                {
                    "stage_id": stage.stage_id,
                    "stage_name": stage.stage_name,
                    "met": stage.met,
                    "evidence": stage.evidence,
                    "gaps": stage.gaps,
                }
                for stage in self.wptg_stages
            ],
        }

    def _check_canonical_icon_filenames(self) -> None:
        assets = self.path / "assets"
        svgs = list(assets.glob("*.svg"))
        small_svgs = [p for p in svgs if p.name.endswith("-small.svg")]
        large_svgs = [p for p in svgs if p.name.endswith("-large.svg")]
        if not small_svgs or not large_svgs:
            self.log_issue(
                "WARN",
                "Missing canonical SVG icon(s)",
                "#TODO",
                "Ensure at least one *-small.svg and one *-large.svg exist in assets/; placeholders are acceptable.",
                self._ensure_canonical_icons,
            )

    def _ensure_canonical_icons(self) -> None:
        assets = self.path / "assets"
        assets.mkdir(exist_ok=True)
        svgs = list(assets.glob("*.svg"))
        small_svgs = [p for p in svgs if p.name.endswith("-small.svg")]
        large_svgs = [p for p in svgs if p.name.endswith("-large.svg")]

        if small_svgs and not large_svgs:
            base = small_svgs[0].name.removesuffix("-small.svg")
            self._generate_placeholder_icon(size="large", base=base)
            return
        if large_svgs and not small_svgs:
            base = large_svgs[0].name.removesuffix("-large.svg")
            self._generate_placeholder_icon(size="small", base=base)
            return
        if small_svgs and large_svgs:
            return
        # No canonical suffix files at all, create a pair from the skill name.
        self._generate_placeholder_icon(size="small", base=self.name)
        self._generate_placeholder_icon(size="large", base=self.name)

    def _generate_placeholder_icon(self, *, size: str, base: str) -> None:
        assets = self.path / "assets"
        assets.mkdir(exist_ok=True)
        if size not in {"small", "large"}:
            raise ValueError("size must be 'small' or 'large'")
        dim = 16 if size == "small" else 64
        icon_path = assets / f"{base}-{size}.svg"
        if icon_path.exists():
            return
        content = self._render_icon_svg(dim)
        icon_path.write_text(content, encoding="utf-8")
        print(f"  [FIX] Generated placeholder icon: {icon_path.name}")

    def _render_icon_svg(self, dim: int) -> str:
        """
        ICON_POOL_V1
        Deterministic icon "pool" that selects one of several simple motifs for placeholder icons.
        This keeps subprocess remediation visually distinct across skills without extra deps.
        """
        seed = f"{self.name}|{self.path.as_posix()}"
        digest = hashlib.sha256(seed.encode("utf-8")).digest()

        def hsl(h_byte: int, s: int, l: int) -> str:
            hue = int(round((h_byte / 255.0) * 360.0))
            return f"hsl({hue} {s}% {l}%)"

        def svg_header() -> str:
            return (
                f"<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"{dim}\" height=\"{dim}\" "
                f"viewBox=\"0 0 {dim} {dim}\">"
            )

        def monogram() -> str:
            return (
                f"  <text x=\"50%\" y=\"52%\" dominant-baseline=\"middle\" text-anchor=\"middle\" "
                f"fill=\"{ink}\" font-size=\"{font_size}\" font-family=\"ui-sans-serif,system-ui\">{initial}</text>"
            )

        def rect_monogram() -> str:
            return "\n".join(
                [
                    svg_header(),
                    f"  <rect width=\"{dim}\" height=\"{dim}\" rx=\"3\" fill=\"{bg}\"/>",
                    monogram(),
                    "</svg>",
                ]
            )

        def diagonal_split() -> str:
            return "\n".join(
                [
                    svg_header(),
                    f"  <rect width=\"{dim}\" height=\"{dim}\" rx=\"3\" fill=\"{bg}\"/>",
                    f"  <path d=\"M0 0 L{dim} 0 L0 {dim} Z\" fill=\"{accent}\" opacity=\"0.65\"/>",
                    monogram(),
                    "</svg>",
                ]
            )

        def rings() -> str:
            c = dim / 2
            r1 = dim * 0.45
            r2 = dim * 0.28
            sw1 = max(2, dim // 16)
            sw2 = max(2, dim // 20)
            return "\n".join(
                [
                    svg_header(),
                    f"  <rect width=\"{dim}\" height=\"{dim}\" rx=\"3\" fill=\"{bg}\"/>",
                    f"  <circle cx=\"{c}\" cy=\"{c}\" r=\"{r1}\" fill=\"none\" stroke=\"{accent}\" stroke-width=\"{sw1}\" opacity=\"0.7\"/>",
                    f"  <circle cx=\"{c}\" cy=\"{c}\" r=\"{r2}\" fill=\"none\" stroke=\"{accent}\" stroke-width=\"{sw2}\" opacity=\"0.5\"/>",
                    monogram(),
                    "</svg>",
                ]
            )

        def corner_badge() -> str:
            s = dim * 0.45
            return "\n".join(
                [
                    svg_header(),
                    f"  <rect width=\"{dim}\" height=\"{dim}\" rx=\"3\" fill=\"{bg}\"/>",
                    f"  <rect x=\"0\" y=\"0\" width=\"{s}\" height=\"{s}\" fill=\"{accent}\" opacity=\"0.75\"/>",
                    monogram(),
                    "</svg>",
                ]
            )

        def stripes_svg(stripes: int) -> str:
            step = dim / stripes
            parts = [svg_header(), f"  <rect width=\"{dim}\" height=\"{dim}\" rx=\"3\" fill=\"{bg}\"/>"]
            for i in range(stripes):
                x = i * step
                parts.append(
                    f"  <rect x=\"{x}\" y=\"0\" width=\"{step/2}\" height=\"{dim}\" fill=\"{accent}\" opacity=\"0.35\"/>"
                )
            parts.append(monogram())
            parts.append("</svg>")
            return "\n".join(parts)

        def notch() -> str:
            n = dim * 0.28
            return "\n".join(
                [
                    svg_header(),
                    f"  <rect width=\"{dim}\" height=\"{dim}\" rx=\"3\" fill=\"{bg}\"/>",
                    f"  <path d=\"M{dim-n} 0 L{dim} 0 L{dim} {n} Z\" fill=\"{accent}\" opacity=\"0.8\"/>",
                    monogram(),
                    "</svg>",
                ]
            )

        bg = hsl(digest[0], 55 + (digest[1] % 30), 30 + (digest[2] % 25))
        accent = hsl((digest[0] + 60 + (digest[3] % 120)) % 255, 60, 55)
        ink = "#ffffff"
        initial = (self.name[0] if self.name else "?").upper()
        font_size = 10 if dim <= 16 else 28

        variant = digest[4] % 6
        if variant == 0:
            return rect_monogram()
        if variant == 1:
            return diagonal_split()
        if variant == 2:
            return rings()
        if variant == 3:
            return corner_badge()
        if variant == 4:
            stripes = 2 + (digest[5] % 4)
            return stripes_svg(stripes)
        return notch()
    def _scaffold_openai_yaml(self) -> None:
        agents = self.path / "agents"
        agents.mkdir(exist_ok=True)
        yaml_path = agents / "openai.yaml"
        if yaml_path.exists():
            return
        payload = "\n".join(
            [
                f"# Auto-scaffolded by skill-polisher for `{self.name}`.",
                "# Review and adjust model/tool policy as needed.",
                "version: 1",
                f"name: {self.name}",
                "provider: openai",
                "models:",
                "  default: gpt-5",
                "policy:",
                "  allowed_tools: []",
                "",
            ]
        )
        yaml_path.write_text(payload, encoding="utf-8")
        print(f"  [FIX] Scaffolded agents/openai.yaml for {self.name}")

    def audit_python_code(self) -> None:
        script_dir = self.path / "scripts"
        if not script_dir.exists():
            return

        for py_file in script_dir.glob("*.py"):
            try:
                tree = ast.parse(py_file.read_text(encoding="utf-8"))
                defined_funcs = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
                called_funcs = {
                    n.func.id
                    for n in ast.walk(tree)
                    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                }

                builtins = {
                    "print",
                    "len",
                    "range",
                    "open",
                    "str",
                    "int",
                    "list",
                    "dict",
                    "set",
                    "max",
                    "min",
                    "isinstance",
                    "getattr",
                    "setattr",
                }

                for func in called_funcs:
                    if func not in defined_funcs and func not in builtins and "adapter_" in func:
                        self.log_issue(
                            "CRITICAL",
                            f"Code Rot in {py_file.name}: Calls undefined local function '{func}'",
                            "#XXX",
                            "Define the missing function or replace the call with an existing implementation.",
                        )

            except SyntaxError as e:
                self.log_issue(
                    "CRITICAL",
                    f"Syntax Error in {py_file.name}: {e}",
                    "#FIXME",
                    "Repair syntax so the file is parseable before running the skill.",
                )

    def audit_skill_contract(self) -> None:
        skill_md = self.path / "SKILL.md"
        if not skill_md.exists():
            return

        if self._resolve_target_flavor() == "claude":
            # Claude flavor uses stricter checks in check_structure; avoid duplicate WARN noise here.
            return

        raw = skill_md.read_text(encoding="utf-8")
        stripped = raw.strip()
        if not stripped.startswith("---"):
            self.log_issue(
                "WARN",
                "SKILL.md is missing YAML frontmatter fence at top.",
                "#TODO",
                "Add frontmatter with `name` and `description` for deterministic discovery.",
            )
            return

        lower = raw.lower()
        if "name:" not in lower:
            self.log_issue(
                "CRITICAL",
                "SKILL.md frontmatter missing `name`.",
                "#FIXME",
                "Add `name` in frontmatter.",
            )
        if "description:" not in lower:
            self.log_issue(
                "CRITICAL",
                "SKILL.md frontmatter missing `description`.",
                "#FIXME",
                "Add `description` in frontmatter.",
            )

    def audit_command_policy(self) -> None:
        skill_md = self.path / "SKILL.md"
        if not skill_md.exists():
            return
        lines = skill_md.read_text(encoding="utf-8").splitlines()
        in_fence = False
        code_lines: list[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence and stripped:
                code_lines.append(stripped.lower())

        for line in code_lines:
            if re.search(r"\bcmd\s*/c\b", line):
                self.log_issue(
                    "CRITICAL",
                    "Forbidden command wrapper `cmd /c` found in executable snippet.",
                    "#FIXME",
                    "Replace with PowerShell-native commands.",
                )
            if re.search(r"(^|\\s)pip(\\s|$)", line):
                self.log_issue(
                    "CRITICAL",
                    "Forbidden raw `pip` command found in executable snippet.",
                    "#FIXME",
                    "Route dependency operations through `uv` policy.",
                )
            if re.match(r"^(python|python3)\\b", line):
                self.log_issue(
                    "WARN",
                    "Potential raw `python` command found in executable snippet.",
                    "#TODO",
                    "Replace with `uv run <script.py>` unless explicit interpreter call is required.",
                )

    def audit_debt_markers(self) -> None:
        patterns = ("TODO", "FIXME", "XXX", "TBD")
        hits: dict[str, int] = {p: 0 for p in patterns}
        for p in self.path.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in {".md", ".py", ".yaml", ".yml", ".json", ".txt"}:
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            upper = text.upper()
            for marker in patterns:
                hits[marker] += upper.count(marker)

        nonzero = {k: v for k, v in hits.items() if v > 0}
        if not nonzero:
            return
        marker_report = ", ".join(f"{k}:{v}" for k, v in sorted(nonzero.items()))
        self.log_issue(
            "INFO",
            f"Debt markers detected ({marker_report}).",
            "#TBD",
            "Review markers and convert unresolved debt into tracked action items.",
        )

    def audit_linguistics(self) -> None:
        skill_md = self.path / "SKILL.md"
        if not skill_md.exists():
            return

        raw = skill_md.read_text(encoding="utf-8")
        if "style-exempt" in raw.lower():
            return

        lines = raw.splitlines()
        filtered: list[str] = []
        in_fence = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            if stripped.startswith(">"):
                continue
            filtered.append(line)

        content = "\n".join(filtered).lower()

        hedging = {"maybe", "perhaps", "try to", "hopefully", "if you want", "might", "possibly"}
        weakness = {"help with", "assist in", "can be used", "aims to"}
        power = {"execute", "enforce", "destroy", "kill", "override", "mandatory", "critical", "must"}

        hedge_count = sum(1 for w in hedging if w in content)
        weak_count = sum(1 for w in weakness if w in content)
        power_count = sum(1 for w in power if w in content)

        if hedge_count > 0:
            self.log_issue(
                "WARN",
                f"Linguistic Entropy: Found {hedge_count} hedging terms",
                "#TBD",
                "Decide whether to tighten language or add style exemption for intentional voice.",
            )

        if weak_count > 2:
            self.log_issue(
                "WARN",
                f"Passive Voice: Found {weak_count} weak phrases",
                "#TODO",
                "Rewrite weak phrases into direct execution language.",
            )

        # Power-language no longer adds hidden bonus. Scoring is domain-weight deterministic.

    def report(self) -> None:
        self.finalize_scores()
        if stdout_supports_unicode():
            top = "╔══════════════════════════════════════════════════════════════╗"
            mid = f"║                    FEEDING REPORT: {self.name:<18}           ║"
            bot = "╚══════════════════════════════════════════════════════════════╝"
        else:
            top = "+--------------------------------------------------------------+"
            mid = f"|                    FEEDING REPORT: {self.name:<18}           |"
            bot = "+--------------------------------------------------------------+"

        print(top)
        print(mid)
        print(bot)

        flavor = "PURE (Clean)"
        if self.score < 50:
            flavor = "BITTER (Broken)"
        elif self.score < 90:
            flavor = "BLAND (Dirty)"

        print(f"TASTE: {flavor}")
        print(f"NUTRITION LEVEL: {self.score}%\n")
        print("DOMAIN SCORES:")
        for domain in ("structure", "policy", "semantics", "maintainability"):
            print(f"  - {domain}: {self.domain_scores[domain]}%")
        print("")

        if self.wptg_stages:
            met_count = sum(1 for stage in self.wptg_stages if stage.met)
            print("WPTG STAGE ALIGNMENT:")
            print(f"  - profile: {self.wptg_profile}")
            print(f"  - coverage: {met_count}/{len(self.wptg_stages)} ({self.wptg_score}%)")
            for stage in self.wptg_stages:
                status = "OK" if stage.met else "GAP"
                print(f"    - [{status}] {stage.stage_id} {stage.stage_name}")
            print("")

        if self.issues:
            print("ENTROPY DETECTED:")
            for issue in self.issues:
                loc = f"{issue.file}:{issue.line}" if issue.line else issue.file
                print(f"  [{issue.severity}] {issue.stamp} ({issue.domain}) {issue.msg}")
                print(f"    -> location: {loc}, confidence: {issue.confidence:.2f}")
                print(f"    -> {issue.remedy}")
            self._print_stamp_summary()
        else:
            print("System Satisfied. No entropy found.")

    def _print_stamp_summary(self) -> None:
        counts: dict[str, int] = {}
        for issue in self.issues:
            counts[issue.stamp] = counts.get(issue.stamp, 0) + 1
        ordered = ", ".join(f"{stamp}:{counts[stamp]}" for stamp in sorted(counts.keys()))
        print(f"\nSTAMP INDEX: {ordered}")

    def run_all_audits(self) -> None:
        self.check_structure()
        self.audit_skill_contract()
        self.audit_command_policy()
        self.audit_python_code()
        self.audit_linguistics()
        self.audit_debt_markers()
        self.audit_wptg_transition()

    def has_blocking_issues(self) -> bool:
        return any(issue.severity in {"CRITICAL", "WARN"} for issue in self.issues)

    def print_plan(self) -> None:
        print("\nPLAN:")
        if not self.issues:
            print("  - No findings. No action required.")
            return
        for idx, issue in enumerate(self.issues, start=1):
            loc = f"{issue.file}:{issue.line}" if issue.line else issue.file
            print(f"  {idx}. {issue.stamp} [{issue.severity}] ({issue.domain}) {issue.msg}")
            print(f"     location: {loc}")
            print(f"     remedy: {issue.remedy}")
        if self.fixable_actions:
            print(f"  - Auto-fix actions available: {len(self.fixable_actions)}")
        else:
            print("  - Auto-fix actions available: 0")


class PolisherAddict:
    def __init__(self, skill_path: Path, max_binge: int = 3):
        self.path = skill_path
        self.max_binge = max_binge
        self.last_digest: SkillDigest | None = None
        self.max_fix_per_skill: int | None = None
        self.halt_after_fix: bool = False
        self.target_flavor: str = "codex"
        self.require_assets: bool = True
        self.wptg_profile: str = "off"

    def binge(self, *, max_fix_per_skill: int | None = None, halt_after_fix: bool = False) -> int:
        if max_fix_per_skill is None:
            max_fix_per_skill = self.max_fix_per_skill
        if halt_after_fix is False and self.halt_after_fix:
            halt_after_fix = True
        for i in range(self.max_binge):
            print(f"\n>>> BINGE CYCLE {i+1}/{self.max_binge} <<<")
            digest = SkillDigest(
                self.path,
                target_flavor=self.target_flavor,
                require_assets=self.require_assets,
                wptg_profile=self.wptg_profile,
            )
            digest.run_all_audits()
            digest.report()
            self.last_digest = digest

            if digest.score == 100:
                print("\n>>> HIGH ACHIEVED. DOPAMINE RELEASED. <<<")
                return 0

            if not digest.fixable_actions:
                print("\n>>> WITHDRAWAL: No fixable entropy found. Manual intervention required. <<<")
                return 1

            actions = digest.fixable_actions
            if max_fix_per_skill is not None:
                actions = actions[: max_fix_per_skill]

            print(f"\n>>> CRAVING: Consuming {len(actions)} issues... <<<")
            for action in actions:
                digest.applied_fixes.append(action.remedy)
                action.fn()

            if halt_after_fix:
                print("\n>>> HALT: Fixes applied. Stop requested (no further recursion). <<<")
                return 0

        print("\n>>> OVERDOSE: Max recursion depth reached. Entropy persists. <<<")
        return 2

    def detect(self) -> int:
        digest = SkillDigest(
            self.path,
            target_flavor=self.target_flavor,
            require_assets=self.require_assets,
            wptg_profile=self.wptg_profile,
        )
        digest.run_all_audits()
        digest.report()
        self.last_digest = digest
        return 0

    def plan(self) -> int:
        digest = SkillDigest(
            self.path,
            target_flavor=self.target_flavor,
            require_assets=self.require_assets,
            wptg_profile=self.wptg_profile,
        )
        digest.run_all_audits()
        digest.report()
        digest.print_plan()
        self.last_digest = digest
        return 0

    def verify(self) -> int:
        digest = SkillDigest(
            self.path,
            target_flavor=self.target_flavor,
            require_assets=self.require_assets,
            wptg_profile=self.wptg_profile,
        )
        digest.run_all_audits()
        digest.report()
        self.last_digest = digest
        if digest.has_blocking_issues():
            print("\n>>> VERIFY: FAILED (blocking findings present). <<<")
            return 1
        print("\n>>> VERIFY: PASSED (no blocking findings). <<<")
        return 0

    def run_mode(self, mode: str) -> int:
        if mode == "detect":
            return self.detect()
        if mode == "plan":
            return self.plan()
        if mode == "verify":
            return self.verify()
        return self.binge()


def issue_to_dict(skill_name: str, issue: IssueRecord) -> dict:
    return {
        "skill": skill_name,
        "stamp": issue.stamp,
        "severity": issue.severity,
        "domain": issue.domain,
        "file": issue.file,
        "line": issue.line,
        "message": issue.msg,
        "remedy": issue.remedy,
        "confidence": issue.confidence,
    }


def emit_stamps_json(path: Path, results: list[dict]) -> None:
    stamps: list[dict] = []
    for result in results:
        for issue in result["issues"]:
            stamps.append(issue_to_dict(result["skill"], issue))
        if result.get("pure", False):
            stamps.append(
                {
                    "skill": result["skill"],
                    "stamp": "#PURE",
                    "severity": "INFO",
                    "domain": "structure",
                    "file": "SKILL.md",
                    "line": None,
                    "message": "TASTE: PURE (Clean) and no blocking entropy detected.",
                    "remedy": "None (record only).",
                    "confidence": 1.0,
                }
            )
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(stamps),
        "records": stamps,
        "skills": [
            {
                "skill": r["skill"],
                "exit_code": r["exit_code"],
                "score": r["score"],
                "pure": r.get("pure", False),
                "applied_fixes": r.get("applied_fixes", []),
            }
            for r in results
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def emit_summary_md(path: Path, mode: str, results: list[dict]) -> None:
    total = len(results)
    passed = sum(1 for r in results if r["exit_code"] == 0)
    failed = total - passed
    pure = sum(1 for r in results if r.get("pure", False))
    wptg_rows = [r for r in results if r.get("wptg", {}).get("enabled")]
    wptg_avg = 0
    if wptg_rows:
        wptg_avg = round(sum(r["wptg"]["score"] for r in wptg_rows) / len(wptg_rows), 2)
    lines = [
        "# Skill Polisher Summary",
        "",
        f"- Generated: `{datetime.now(timezone.utc).isoformat()}`",
        f"- Mode: `{mode}`",
        f"- Total skills: `{total}`",
        f"- Passed: `{passed}`",
        f"- Failed: `{failed}`",
        f"- Pure: `{pure}`",
        f"- WPTG profile enabled skills: `{len(wptg_rows)}`",
        f"- WPTG average score: `{wptg_avg}`",
        "",
        "## Scores",
        "",
        "| Skill | Exit | Total | WPTG | Structure | Policy | Semantics | Maintainability | Issues | Fixes |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in results:
        d = r["domain_scores"]
        fixes = len(r.get("applied_fixes", []))
        wptg = r.get("wptg", {})
        wptg_cell = "-"
        if wptg.get("enabled"):
            wptg_cell = f"{wptg.get('met', 0)}/{wptg.get('total', 0)} ({wptg.get('score', 0)}%)"
        lines.append(
            f"| `{r['skill']}` | `{r['exit_code']}` | `{r['score']}` | `{wptg_cell}` | `{d['structure']}` | `{d['policy']}` | `{d['semantics']}` | `{d['maintainability']}` | `{len(r['issues'])}` | `{fixes}` |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def emit_wptg_json(path: Path, results: list[dict]) -> None:
    enabled = [r for r in results if r.get("wptg", {}).get("enabled")]
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "skills_total": len(results),
        "skills_wptg_enabled": len(enabled),
        "avg_wptg_score": round(sum(r["wptg"]["score"] for r in enabled) / max(len(enabled), 1), 2),
        "skills": [
            {
                "skill": r["skill"],
                "exit_code": r["exit_code"],
                "score": r["score"],
                "wptg": r.get("wptg", {}),
            }
            for r in results
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def emit_trend_json(path: Path, mode: str, results: list[dict]) -> None:
    snapshot = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "skills": len(results),
        "avg_score": round(sum(r["score"] for r in results) / max(len(results), 1), 2),
        "failed": sum(1 for r in results if r["exit_code"] != 0),
    }
    payload = {"history": []}
    if path.exists():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = {"history": []}
    history = payload.get("history", [])
    history.append(snapshot)
    payload["history"] = history[-100:]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def iter_skills(root: Path) -> list[Path]:
    return sorted([p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")])


def _copy_tree(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for p in src.rglob("*"):
        rel = p.relative_to(src)
        out = dst / rel
        if p.is_dir():
            out.mkdir(parents=True, exist_ok=True)
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(p.read_bytes())


def fixture_eval(fixtures_root: Path) -> int:
    """
    FIXTURE_EVAL_V1
    - Runs skill-polisher against fixture skill folders in an isolated tmp copy.
    - Compares stamp sets against expected JSON.
    """
    if not fixtures_root.exists():
        die(f"Fixtures root not found: {fixtures_root}")

    fixture_dirs = sorted([p for p in fixtures_root.iterdir() if p.is_dir() and not p.name.startswith(".")])
    if not fixture_dirs:
        die(f"No fixture directories found under: {fixtures_root}")

    tmp_root = Path("codex/mailbox/.tmp_fixture_eval")
    if tmp_root.exists():
        # Best-effort cleanup without shelling out to cmd.
        for p in sorted(tmp_root.rglob("*"), reverse=True):
            try:
                if p.is_file():
                    p.unlink()
                else:
                    p.rmdir()
            except OSError:
                pass
        try:
            tmp_root.rmdir()
        except OSError:
            pass
    tmp_root.mkdir(parents=True, exist_ok=True)

    failures: list[str] = []
    for fixture_dir in fixture_dirs:
        expected_path = fixture_dir / "expected.json"
        if not expected_path.exists():
            failures.append(f"{fixture_dir.name}: missing expected.json")
            continue

        expected = json.loads(expected_path.read_text(encoding="utf-8"))
        expected_stamps = set(expected.get("stamps", []))
        mode = expected.get("mode", "verify")
        target_flavor = expected.get("target_flavor", "codex")
        require_assets = bool(expected.get("require_assets", True))
        wptg_profile = expected.get("wptg_profile", "off")
        if mode not in {"detect", "plan", "verify", "apply"}:
            failures.append(f"{fixture_dir.name}: invalid mode in expected.json")
            continue
        if wptg_profile not in {"off", "baseline", "strict"}:
            failures.append(f"{fixture_dir.name}: invalid wptg_profile in expected.json")
            continue

        skill_copy = tmp_root / fixture_dir.name
        _copy_tree(fixture_dir, skill_copy)

        addict = PolisherAddict(skill_copy)
        addict.target_flavor = target_flavor
        addict.require_assets = require_assets
        addict.wptg_profile = wptg_profile
        code = addict.run_mode(mode)
        digest = addict.last_digest or SkillDigest(skill_copy, wptg_profile=wptg_profile)
        # Fixture evaluation compares only blocking stamp behavior by default.
        # INFO markers (for example debt-marker #TBD) are intentionally ignored to keep fixtures stable.
        got_stamps = {i.stamp for i in digest.issues if i.severity in {"CRITICAL", "WARN"}}
        if code == 0 and not digest.has_blocking_issues():
            got_stamps.add("#PURE")

        missing = sorted(expected_stamps - got_stamps)
        extra = sorted(got_stamps - expected_stamps)
        if missing or extra:
            failures.append(
                f"{fixture_dir.name}: stamp mismatch missing={missing} extra={extra}"
            )

    if failures:
        print("\n=== FIXTURE_EVAL_V1: FAILED ===")
        for f in failures:
            print(f"- {f}")
        return 1

    print("\n=== FIXTURE_EVAL_V1: PASSED ===")
    return 0


def run_envelope_canon(skills_root: Path) -> None:
    print("\n=== OPERATION TRAIN STOP: ENVELOPE CANON ===")
    print("Target skill: script-envelope")
    skill_dir = skills_root / "script-envelope"
    if not skill_dir.exists():
        die("script-envelope skill not found")
    addict = PolisherAddict(skill_dir)
    addict.binge()
    print("\nAction: Use script-envelope to canonicalize prioritized scripts.")
    print("Note: This operation is a prep stage; apply to concrete scripts when requested.")


def run_decision_razor_hardening(skills_root: Path) -> None:
    print("\n=== OPERATION TRAIN STOP: DECISION RAZOR HARDENING ===")
    print("Target skill: decision-razor")
    skill_dir = skills_root / "decision-razor"
    if not skill_dir.exists():
        die("decision-razor skill not found")
    addict = PolisherAddict(skill_dir)
    addict.binge()
    print("\nAction: Tighten output conventions in decision-razor when requested.")


def run_artifact_upcycle_pass(skills_root: Path) -> None:
    print("\n=== OPERATION TRAIN STOP: ARTIFACT UPCYCLE PASS ===")
    print("Target skill: artifact-upcycle")
    skill_dir = skills_root / "artifact-upcycle"
    if not skill_dir.exists():
        die("artifact-upcycle skill not found")
    addict = PolisherAddict(skill_dir)
    addict.binge()
    print("\nAction: Identify stale artifact targets and run artifact-upcycle when requested.")


def main() -> None:
    if len(sys.argv) < 2:
        die(
            "Usage: polish_skill.py <skill_path|skills_root> [--all] [--mode detect|plan|verify|apply] "
            "[--subprocess-fix] [--emit-stamps-json <path>] [--emit-summary-md <path>] [--emit-trend-json <path>] "
            "[--emit-wptg-json <path>] [--wptg-profile off|baseline|strict] "
            "[--target-flavor codex|claude|gemini|auto] [--require-assets|--no-require-assets] "
            "[--halt-after-fix] [--max-fix-per-skill N] [--fixture-eval <fixtures_root>] [--train-stop <op>]"
        )

    target = Path(sys.argv[1])
    if not target.exists():
        die(f"Target not found: {target}")

    args = sys.argv[2:]
    run_all = "--all" in args
    subprocess_fix = "--subprocess-fix" in args
    halt_after_fix = "--halt-after-fix" in args
    target_flavor = "codex"
    if "--target-flavor" in args:
        tidx = args.index("--target-flavor")
        if tidx + 1 >= len(args):
            die("--target-flavor requires one of: codex | claude | gemini | auto")
        target_flavor = args[tidx + 1]
        if target_flavor not in {"codex", "claude", "gemini", "auto"}:
            die("--target-flavor requires one of: codex | claude | gemini | auto")

    wptg_profile = "off"
    if "--wptg-profile" in args:
        widx = args.index("--wptg-profile")
        if widx + 1 >= len(args):
            die("--wptg-profile requires one of: off | baseline | strict")
        wptg_profile = args[widx + 1]
        if wptg_profile not in {"off", "baseline", "strict"}:
            die("--wptg-profile requires one of: off | baseline | strict")

    require_assets = True
    if "--no-require-assets" in args:
        require_assets = False
    if "--require-assets" in args:
        require_assets = True
    max_fix_per_skill = None
    if "--max-fix-per-skill" in args:
        midx = args.index("--max-fix-per-skill")
        if midx + 1 >= len(args):
            die("--max-fix-per-skill requires an integer")
        try:
            max_fix_per_skill = int(args[midx + 1])
        except ValueError:
            die("--max-fix-per-skill requires an integer")
        if max_fix_per_skill <= 0:
            die("--max-fix-per-skill must be > 0")
    mode = "apply"
    if "--mode" in args:
        midx = args.index("--mode")
        if midx + 1 >= len(args):
            die("--mode requires one of: detect | plan | verify | apply")
        mode = args[midx + 1]
        if mode not in {"detect", "plan", "verify", "apply"}:
            die("Unknown --mode. Use: detect | plan | verify | apply")

    emit_stamps_path = None
    emit_summary_path = None
    emit_trend_path = None
    emit_wptg_path = None
    fixture_eval_root = None
    if "--emit-stamps-json" in args:
        sidx = args.index("--emit-stamps-json")
        if sidx + 1 >= len(args):
            die("--emit-stamps-json requires a path")
        emit_stamps_path = Path(args[sidx + 1])
    if "--emit-summary-md" in args:
        sidx = args.index("--emit-summary-md")
        if sidx + 1 >= len(args):
            die("--emit-summary-md requires a path")
        emit_summary_path = Path(args[sidx + 1])
    if "--emit-trend-json" in args:
        sidx = args.index("--emit-trend-json")
        if sidx + 1 >= len(args):
            die("--emit-trend-json requires a path")
        emit_trend_path = Path(args[sidx + 1])
    if "--emit-wptg-json" in args:
        sidx = args.index("--emit-wptg-json")
        if sidx + 1 >= len(args):
            die("--emit-wptg-json requires a path")
        emit_wptg_path = Path(args[sidx + 1])
    if "--fixture-eval" in args:
        fidx = args.index("--fixture-eval")
        if fidx + 1 >= len(args):
            die("--fixture-eval requires a fixtures root directory")
        fixture_eval_root = Path(args[fidx + 1])
    if "--train-stop" in args:
        idx = args.index("--train-stop")
        if idx + 1 >= len(args):
            die("--train-stop requires an operation: envelope-canon | decision-razor-hardening | artifact-upcycle-pass")
        op = args[idx + 1]
        if not target.is_dir():
            die("When using --train-stop, target must be a skills root directory.")
        if op == "envelope-canon":
            run_envelope_canon(target)
            return
        if op == "decision-razor-hardening":
            run_decision_razor_hardening(target)
            return
        if op == "artifact-upcycle-pass":
            run_artifact_upcycle_pass(target)
            return
        die("Unknown --train-stop op. Use: envelope-canon | decision-razor-hardening | artifact-upcycle-pass")

    if fixture_eval_root is not None:
        sys.exit(fixture_eval(fixture_eval_root))

    if run_all:
        if not target.is_dir():
            die("When using --all, target must be a directory of skills.")
        exit_code = 0
        results: list[dict] = []
        script_path = Path(__file__).resolve()
        for skill_dir in iter_skills(target):
            print(f"\n=== POLISHING: {skill_dir.name} ===")
            addict = PolisherAddict(skill_dir)
            addict.halt_after_fix = halt_after_fix
            addict.max_fix_per_skill = max_fix_per_skill
            addict.target_flavor = target_flavor
            addict.require_assets = require_assets
            addict.wptg_profile = wptg_profile
            code = addict.run_mode(mode)
            digest = addict.last_digest or SkillDigest(skill_dir, wptg_profile=wptg_profile)

            # Optional isolation: remediate in a subprocess (uv run) before continuing.
            # This is useful when the sweep is in verify/detect/plan mode but we still want
            # to auto-apply safe standardizations (icons, yaml scaffolds, etc.).
            if subprocess_fix and mode != "apply" and digest.has_fixable_entropy():
                print("\n>>> SUBPROCESS FIX: Spawning uv run apply for this skill... <<<")
                apply_cmd = [
                    "uv",
                    "run",
                    str(script_path),
                    str(skill_dir),
                    "--mode",
                    "apply",
                    "--target-flavor",
                    target_flavor,
                    "--wptg-profile",
                    wptg_profile,
                ]
                if require_assets:
                    apply_cmd.append("--require-assets")
                else:
                    apply_cmd.append("--no-require-assets")
                proc = subprocess.run(
                    apply_cmd,
                    capture_output=False,
                    check=False,
                )
                if proc.returncode != 0:
                    print(f">>> SUBPROCESS FIX: Apply failed (exit {proc.returncode}). Continuing sweep. <<<")
                else:
                    # Refresh digest after remediation for accurate reporting/artifacts.
                    addict = PolisherAddict(skill_dir)
                    addict.target_flavor = target_flavor
                    addict.require_assets = require_assets
                    addict.wptg_profile = wptg_profile
                    code = addict.run_mode(mode)
                    digest = addict.last_digest or SkillDigest(skill_dir, wptg_profile=wptg_profile)

            if code != 0:
                exit_code = code

            results.append(
                {
                    "skill": skill_dir.name,
                    "exit_code": code,
                    "score": digest.score,
                    "domain_scores": digest.domain_scores,
                    "issues": digest.issues,
                    "pure": (code == 0 and not digest.has_blocking_issues()),
                    "applied_fixes": getattr(digest, "applied_fixes", []),
                    "target_flavor": target_flavor,
                    "require_assets": require_assets,
                    "wptg": digest.wptg_snapshot(),
                }
            )
        if emit_stamps_path:
            emit_stamps_json(emit_stamps_path, results)
        if emit_summary_path:
            emit_summary_md(emit_summary_path, mode, results)
        if emit_trend_path:
            emit_trend_json(emit_trend_path, mode, results)
        if emit_wptg_path:
            emit_wptg_json(emit_wptg_path, results)
        sys.exit(exit_code)

    if (target / "SKILL.md").exists():
        addict = PolisherAddict(target)
        addict.halt_after_fix = halt_after_fix
        addict.max_fix_per_skill = max_fix_per_skill
        addict.target_flavor = target_flavor
        addict.require_assets = require_assets
        addict.wptg_profile = wptg_profile
        code = addict.run_mode(mode)
        digest = addict.last_digest or SkillDigest(target, wptg_profile=wptg_profile)
        result = [
            {
                "skill": target.name,
                "exit_code": code,
                "score": digest.score,
                "domain_scores": digest.domain_scores,
                "issues": digest.issues,
                "pure": (code == 0 and not digest.has_blocking_issues()),
                "applied_fixes": getattr(digest, "applied_fixes", []),
                "target_flavor": target_flavor,
                "require_assets": require_assets,
                "wptg": digest.wptg_snapshot(),
            }
        ]
        if emit_stamps_path:
            emit_stamps_json(emit_stamps_path, result)
        if emit_summary_path:
            emit_summary_md(emit_summary_path, mode, result)
        if emit_trend_path:
            emit_trend_json(emit_trend_path, mode, result)
        if emit_wptg_path:
            emit_wptg_json(emit_wptg_path, result)
        sys.exit(code)

    die("Target is not a skill directory. Use --all for a skills root.")


if __name__ == "__main__":
    main()
