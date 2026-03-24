#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: wptg_common.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Shared helpers for WPTG census, forge, and validator scripts.

@SID:           WPTG_COMMON_V1
@Shabti:        Library Module
@Purpose:       Shared WPTG helpers for lane exclusions, toolchains, and file classification.
"""

from __future__ import annotations

import fnmatch
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.lib.shared import configure_utf8_output, find_repo_root


LANE_EXCLUSION_GLOBS: tuple[str, ...] = (
    "extensions/chthonic-archive/themes/icons/product/*.svg",
    "extensions/chthonic-archive/themes/icons/product-outlined/**",
    "extensions/chthonic-archive/themes/fonts/**",
    "scripts/generate-product-icon-font.mjs",
    "scripts/theme_*.py",
    "scripts/icon_*.py",
    "scripts/product_icon_census.py",
    "scripts/theme-sync.ps1",
    "extensions/chthonic-archive/themes/*.json",
    "gemini/to_gemini_DR/**",
)


EXTENSION_CATEGORIES: dict[str, set[str]] = {
    "source_code": {
        ".bat",
        ".cjs",
        ".css",
        ".html",
        ".js",
        ".mjs",
        ".ps1",
        ".py",
        ".rb",
        ".rs",
        ".sh",
        ".ts",
        ".tsx",
    },
    "data_config": {
        ".env",
        ".json",
        ".jsonl",
        ".lock",
        ".toml",
        ".yaml",
        ".yml",
    },
    "build_output": {
        ".db",
        ".png",
        ".pyc",
        ".tsbuildinfo",
        ".woff",
    },
    "documentation": {
        ".md",
        '.md"',
        ".txt",
    },
    "vcs_meta": {
        ".copilotignore",
        ".geminiignore",
        ".gitattributes",
        ".gitignore",
        ".gitkeep",
        ".keep",
        ".vscodeignore",
    },
    "graphics_gpu": {
        ".comp",
        ".frag",
        ".svg",
        ".vert",
    },
    "governance": {
        ".bak",
        ".off",
        ".vsconfig",
    },
    "domain_specific": {
        ".chthonic",
        ".python-version",
    },
    "damaged": {
        '.md"',
    },
}


TOOLCHAIN_MATRIX: dict[str, dict[str, Any]] = {
    "rust": {
        "display_name": "Rust",
        "runtime_cmd": ["rustc", "--version"],
        "manager_cmd": ["rustup", "--version"],
        "manager": "rustup",
        "oxidized": "self_oxidizing",
        "eol_slug": "rust",
        "represented_extensions": {".rs"},
    },
    "python": {
        "display_name": "Python",
        "runtime_cmd": [sys.executable, "--version"],
        "manager_cmd": ["uv", "--version"],
        "manager": "uv",
        "oxidized": True,
        "eol_slug": "python",
        "represented_extensions": {".py", ".pyc", ".python-version"},
    },
    "ruby": {
        "display_name": "Ruby",
        "runtime_cmd": ["ruby", "--version"],
        "manager_cmd": ["rv", "--version"],
        "manager": "rv",
        "oxidized": True,
        "eol_slug": "ruby",
        "represented_extensions": {".rb"},
    },
    "go": {
        "display_name": "Go",
        "runtime_cmd": ["go", "version"],
        "manager_cmd": ["goup", "--version"],
        "manager": "goup",
        "oxidized": True,
        "eol_slug": "go",
        "represented_extensions": {".go"},
    },
    "typescript": {
        "display_name": "TypeScript/JS",
        "runtime_cmd": ["bun", "--version"],
        "manager_cmd": ["bun", "--version"],
        "manager": "bun",
        "oxidized": "honorary",
        "eol_slug": "bun",
        "represented_extensions": {".cjs", ".js", ".mjs", ".ts", ".tsx", ".tsbuildinfo"},
    },
    "dotnet": {
        "display_name": ".NET / C# / F#",
        "runtime_cmd": ["dotnet", "--version"],
        "manager_cmd": None,
        "manager": None,
        "oxidized": False,
        "eol_slug": "dotnet",
        "represented_extensions": {".cs", ".fsx"},
    },
    "c_cpp": {
        "display_name": "C/C++",
        "runtime_cmd": ["gcc", "--version"],
        "manager_cmd": None,
        "manager": None,
        "oxidized": False,
        "eol_slug": None,
        "represented_extensions": {".c", ".cpp", ".h"},
    },
    "perl": {
        "display_name": "Perl",
        "runtime_cmd": ["perl", "-v"],
        "manager_cmd": None,
        "manager": None,
        "oxidized": False,
        "eol_slug": "perl",
        "represented_extensions": {".pl"},
    },
    "php": {
        "display_name": "PHP",
        "runtime_cmd": ["php", "--version"],
        "manager_cmd": None,
        "manager": None,
        "oxidized": False,
        "eol_slug": "php",
        "represented_extensions": {".php"},
    },
    "julia": {
        "display_name": "Julia",
        "runtime_cmd": ["julia", "--version"],
        "manager_cmd": ["juliaup", "--version"],
        "manager": "juliaup",
        "oxidized": True,
        "eol_slug": "julia",
        "represented_extensions": {".jl"},
    },
    "elixir": {
        "display_name": "Elixir",
        "runtime_cmd": ["elixir", "--version"],
        "manager_cmd": None,
        "manager": None,
        "oxidized": False,
        "eol_slug": "elixir",
        "represented_extensions": {".ex", ".exs"},
    },
    "lua": {
        "display_name": "Lua",
        "runtime_cmd": ["lua", "-v"],
        "manager_cmd": None,
        "manager": None,
        "oxidized": False,
        "eol_slug": "lua",
        "represented_extensions": {".lua"},
    },
    "java": {
        "display_name": "Java",
        "runtime_cmd": ["java", "--version"],
        "manager_cmd": None,
        "manager": None,
        "oxidized": False,
        "eol_slug": "java",
        "represented_extensions": {".java"},
    },
    "haskell": {
        "display_name": "Haskell",
        "runtime_cmd": ["ghc", "--version"],
        "manager_cmd": ["ghcup", "--version"],
        "manager": "ghcup",
        "oxidized": False,
        "eol_slug": None,
        "represented_extensions": {".hs"},
    },
    "cobol": {
        "display_name": "COBOL",
        "runtime_cmd": ["cobc", "--version"],
        "manager_cmd": None,
        "manager": None,
        "oxidized": False,
        "eol_slug": None,
        "represented_extensions": {".cob", ".cbl"},
    },
    "zig": {
        "display_name": "Zig",
        "runtime_cmd": ["zig", "version"],
        "manager_cmd": ["zigup", "--version"],
        "manager": "zigup",
        "oxidized": "honorary",
        "eol_slug": "zig",
        "represented_extensions": {".zig"},
    },
    "nodejs": {
        "display_name": "Node.js",
        "runtime_cmd": ["node", "--version"],
        "manager_cmd": ["fnm", "--version"],
        "manager": "fnm/volta",
        "alternate_manager_cmds": [["volta", "--version"]],
        "oxidized": True,
        "eol_slug": "nodejs",
        "represented_extensions": {".node"},
    },
    "powershell": {
        "display_name": "PowerShell",
        "runtime_cmd": ["pwsh", "--version"],
        "manager_cmd": None,
        "manager": None,
        "oxidized": False,
        "eol_slug": None,
        "represented_extensions": {".ps1"},
    },
    "shell": {
        "display_name": "POSIX Shell",
        "runtime_cmd": ["bash", "--version"],
        "manager_cmd": None,
        "manager": None,
        "oxidized": False,
        "eol_slug": None,
        "represented_extensions": {".sh"},
    },
    "batch": {
        "display_name": "Windows Batch",
        "runtime_cmd": [os.environ.get("ComSpec", "cmd.exe"), "/c", "ver"],
        "manager_cmd": None,
        "manager": None,
        "oxidized": False,
        "eol_slug": None,
        "represented_extensions": {".bat"},
    },
    "glsl": {
        "display_name": "GLSL / Shader Tooling",
        "runtime_cmd": ["glslangValidator", "--version"],
        "manager_cmd": None,
        "manager": None,
        "oxidized": False,
        "eol_slug": None,
        "represented_extensions": {".comp", ".frag", ".vert"},
    },
}


EXTENSION_TOOLCHAINS: dict[str, tuple[str, ...]] = {
    ".bat": ("batch",),
    ".cjs": ("typescript",),
    ".comp": ("glsl",),
    ".css": (),
    ".db": (),
    ".env": ("python", "typescript"),
    ".frag": ("glsl",),
    ".html": (),
    ".js": ("typescript",),
    ".json": ("python", "typescript"),
    ".jsonl": ("python", "typescript"),
    ".lock": (),
    ".log": ("python", "typescript"),
    ".md": (),
    '.md"': (),
    ".mjs": ("typescript",),
    ".off": (),
    ".png": (),
    ".ps1": ("powershell",),
    ".py": ("python",),
    ".pyc": ("python",),
    ".python-version": ("python",),
    ".rb": ("ruby",),
    ".rs": ("rust",),
    ".sh": ("shell",),
    ".svg": (),
    ".toml": ("python", "rust"),
    ".ts": ("typescript",),
    ".tsbuildinfo": ("typescript",),
    ".tsx": ("typescript",),
    ".txt": (),
    ".vert": ("glsl",),
    ".vsconfig": ("dotnet",),
    ".woff": (),
    ".yaml": ("python", "typescript"),
    ".yml": ("python", "typescript"),
}


ALCHEMY_RATIONALES: dict[str, str] = {
    ".go": "Go is installed; shell automation patterns can be recast as fast single-binary CLI tools.",
    ".cs": ".NET is installed; TypeScript interfaces can be mirrored as C# class contracts.",
    ".fsx": ".NET is installed; configuration and analysis flows can become F# scripts for typed automation.",
    ".c": "GCC is installed; Rust data layouts can be surfaced as C-compatible headers and shims.",
    ".cpp": "G++ is installed; performance-sensitive utility patterns can be ported into native helpers.",
    ".h": "C headers are viable because Rust struct layouts can be exported for FFI bridges.",
    ".pl": "Perl is installed; text-heavy archaeology and extraction flows can be expressed as Perl utilities.",
}


TEXTLIKE_SUFFIXES: set[str] = {
    ".bat",
    ".cjs",
    ".comp",
    ".copilotignore",
    ".css",
    ".chthonic",
    ".env",
    ".frag",
    ".geminiignore",
    ".gitattributes",
    ".gitignore",
    ".gitkeep",
    ".html",
    ".js",
    ".json",
    ".jsonl",
    ".keep",
    ".lock",
    ".log",
    ".md",
    '.md"',
    ".mjs",
    ".off",
    ".ps1",
    ".py",
    ".pyc",
    ".python-version",
    ".rb",
    ".rs",
    ".sh",
    ".svg",
    ".toml",
    ".ts",
    ".tsbuildinfo",
    ".tsx",
    ".txt",
    ".vert",
    ".vscodeignore",
    ".vsconfig",
    ".yaml",
    ".yml",
}

SHORTCUT_REFERENCE_RE = re.compile(r"(?<!\\)\[([^\[\]\n]+?)\](?!\(|\[|:)")


RUNTIME_VERSION_RE = re.compile(r"(?P<version>\d+(?:\.\d+){0,3})")


@dataclass(slots=True)
class ToolchainProbe:
    key: str
    display_name: str
    installed: bool
    runtime_version: str | None
    runtime_output: str | None
    manager: str | None
    manager_installed: bool
    manager_version: str | None
    oxidized: bool | str
    eol_slug: str | None


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def repo_root() -> Path:
    return find_repo_root()


def run_command(command: list[str], cwd: Path | None = None) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=cwd,
            check=False,
        )
    except OSError:
        return False, ""

    output = (result.stdout or result.stderr or "").strip()
    return result.returncode == 0, output


def extract_version(output: str) -> str | None:
    matches = [match.group("version") for match in RUNTIME_VERSION_RE.finditer(output)]
    if not matches:
        return None
    highest_dot_count = max(value.count(".") for value in matches)
    for value in matches:
        if value.count(".") == highest_dot_count:
            return value
    return matches[0]


def git_lines(*args: str, cwd: Path | None = None) -> list[str]:
    ok, output = run_command(["git", *args], cwd=cwd)
    if not ok:
        return []
    return [line for line in output.splitlines() if line.strip()]


def tracked_files(root: Path | None = None) -> list[str]:
    return git_lines("ls-files", cwd=root or repo_root())


def path_is_excluded(path: str) -> bool:
    normalized = path.replace("\\", "/")
    for pattern in LANE_EXCLUSION_GLOBS:
        glob = pattern.replace("\\", "/")
        if "**" in glob:
            prefix = glob.split("**", 1)[0]
            if normalized.startswith(prefix):
                return True
        if fnmatch.fnmatch(normalized, glob):
            return True
    return False


def normalize_repo_path(path: str | Path) -> str:
    normalized = str(path).strip().replace("\\", "/")
    if normalized.startswith("./"):
        normalized = normalized[2:]
    while normalized.startswith("/"):
        normalized = normalized[1:]
    return normalized


def markdown_path_link(path: str | Path, markdown_output_path: str | Path, label: str | None = None) -> str:
    root = repo_root()
    report_path = Path(markdown_output_path)
    if not report_path.is_absolute():
        report_path = root / report_path

    target_input = Path(path)
    if target_input.is_absolute():
        target_path = target_input
        try:
            normalized = target_input.relative_to(root).as_posix()
        except ValueError:
            normalized = target_input.as_posix()
    else:
        normalized = normalize_repo_path(path)
        target_path = root / normalized

    href = os.path.relpath(target_path, start=report_path.parent).replace("\\", "/")
    href = urllib.parse.quote(href, safe="/._-~")
    display = (label or normalized).replace("`", "\\`")
    return f"[`{display}`]({href})"


def compound_extension(path: str) -> str:
    name = Path(path).name
    if name.startswith(".") and name.count(".") == 1:
        return name
    suffixes = Path(name).suffixes
    if suffixes:
        if len(suffixes) >= 2:
            candidate = "".join(suffixes[-2:])
            if candidate in {".d.ts", ".spec.js", ".spec.ts", ".test.js", ".test.ts", ".test.tsx"}:
                return candidate
            if suffixes[-1] == ".pyc" and suffixes[-2].startswith(".cpython-"):
                return f"{suffixes[-2]}{suffixes[-1]}"
        return suffixes[-1]
    if "." not in name:
        return ""
    dot = name.find(".")
    return name[dot:]


def primary_extension(path: str) -> str:
    compound = compound_extension(path)
    if not compound:
        return ""
    suffixes = Path(path).suffixes
    if suffixes:
        return suffixes[-1]
    return compound


def extension_category(extension: str) -> str:
    for category, extensions in EXTENSION_CATEGORIES.items():
        if extension in extensions:
            return category
    return "unclassified"


def baseline_gold_tier(extension: str) -> str:
    category = extension_category(extension)
    if category == "source_code":
        return "tier_1_direct"
    if category in {"data_config", "vcs_meta", "domain_specific"}:
        return "tier_2_structural"
    if category == "documentation":
        return "tier_3_conceptual"
    return "raw_unrefined"


def is_textlike(path: str) -> bool:
    extension = compound_extension(path)
    if extension in TEXTLIKE_SUFFIXES:
        return True
    if extension_category(extension) in {"source_code", "data_config", "documentation", "vcs_meta", "governance", "domain_specific"}:
        return True
    return False


def safe_read_text(path: Path, limit_bytes: int | None = None) -> str | None:
    try:
        if limit_bytes is not None and path.stat().st_size > limit_bytes:
            return None
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def json_load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def escape_markdown_shortcut_references(text: str) -> str:
    if not text:
        return text
    segments = re.split(r"(`[^`]*`)", text)
    escaped: list[str] = []
    for index, segment in enumerate(segments):
        if index % 2 == 1:
            escaped.append(segment)
            continue
        def _escape_match(match: re.Match[str]) -> str:
            label = match.group(1)
            stripped = label.strip()
            if not stripped or stripped in {"x", "X"}:
                return match.group(0)
            return f"\\[{label}\\]"

        escaped.append(SHORTCUT_REFERENCE_RE.sub(_escape_match, segment))
    return "".join(escaped)


def discover_toolchains() -> dict[str, ToolchainProbe]:
    probes: dict[str, ToolchainProbe] = {}
    for key, meta in TOOLCHAIN_MATRIX.items():
        runtime_ok, runtime_output = run_command(meta["runtime_cmd"])
        manager_installed = False
        manager_version = None
        manager_output = None
        manager_cmd = meta.get("manager_cmd")
        alternate_manager_cmds = meta.get("alternate_manager_cmds", [])

        if manager_cmd:
            manager_installed, manager_output = run_command(manager_cmd)
            if not manager_installed:
                for alternate in alternate_manager_cmds:
                    manager_installed, manager_output = run_command(alternate)
                    if manager_installed:
                        break
            manager_version = extract_version(manager_output or "")

        probes[key] = ToolchainProbe(
            key=key,
            display_name=meta["display_name"],
            installed=runtime_ok,
            runtime_version=extract_version(runtime_output or ""),
            runtime_output=runtime_output or None,
            manager=meta.get("manager"),
            manager_installed=manager_installed,
            manager_version=manager_version,
            oxidized=meta["oxidized"],
            eol_slug=meta.get("eol_slug"),
        )
    return probes


def fetch_eol_cycle(slug: str, version: str) -> dict[str, Any] | None:
    major_minor = ".".join(version.split(".")[:2]) if "." in version else version.split(".", 1)[0]
    candidates = [major_minor, version.split(".", 1)[0]]
    try:
        with urllib.request.urlopen(f"https://endoflife.date/api/{slug}.json", timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None

    for cycle in candidates:
        for entry in payload:
            if str(entry.get("cycle")) == cycle:
                return entry
    return None


def toolchains_to_report(probes: dict[str, ToolchainProbe]) -> dict[str, Any]:
    installed = [key for key, probe in probes.items() if probe.installed]
    oxidized = [
        key
        for key, probe in probes.items()
        if probe.installed and probe.oxidized in {True, "self_oxidizing", "honorary"}
    ]
    unoxidized_installed = [
        key
        for key, probe in probes.items()
        if probe.installed and probe.oxidized is False
    ]
    oxidized_available_not_installed: list[str] = []
    no_oxidized_tooling_exists: list[str] = []

    for key, probe in probes.items():
        if probe.installed:
            continue
        if probe.manager_installed or probe.oxidized in {True, "honorary"}:
            label = key if not probe.manager else f"{key} ({probe.manager})"
            oxidized_available_not_installed.append(label)
        elif probe.oxidized is False:
            no_oxidized_tooling_exists.append(key)

    return {
        "installed": installed,
        "oxidized": oxidized,
        "unoxidized_installed": unoxidized_installed,
        "oxidized_available_not_installed": oxidized_available_not_installed,
        "no_oxidized_tooling_exists": no_oxidized_tooling_exists,
    }


def runtime_support_for_extension(extension: str, probes: dict[str, ToolchainProbe]) -> dict[str, Any]:
    supported_by = [
        key
        for key in EXTENSION_TOOLCHAINS.get(extension, ())
        if probes.get(key) and probes[key].installed
    ]
    required = list(EXTENSION_TOOLCHAINS.get(extension, ()))
    return {
        "supported": bool(supported_by) or not required,
        "supported_by": supported_by,
        "required_toolchains": required,
    }


def represented_extensions(tracked: list[str]) -> set[str]:
    return {compound_extension(path) for path in tracked}


def viable_but_unrepresented_extensions(tracked: list[str], probes: dict[str, ToolchainProbe]) -> list[str]:
    present = represented_extensions(tracked)
    primary_present = {primary_extension(path) for path in tracked}
    viable: list[str] = []
    for key, meta in TOOLCHAIN_MATRIX.items():
        probe = probes[key]
        if not probe.installed:
            continue
        for extension in meta["represented_extensions"]:
            if extension not in present and extension not in primary_present:
                viable.append(extension)
    return sorted(set(viable))


def dead_extensions(tracked: list[str], probes: dict[str, ToolchainProbe]) -> list[str]:
    dead: list[str] = []
    for extension in sorted(represented_extensions(tracked)):
        if not extension:
            continue
        support = runtime_support_for_extension(extension, probes)
        if support["required_toolchains"] and not support["supported"]:
            dead.append(extension)
    return dead


def alchemy_opportunities(extensions: list[str]) -> list[dict[str, str]]:
    return [
        {
            "target_ext": extension,
            "rationale": ALCHEMY_RATIONALES[extension],
        }
        for extension in extensions
        if extension in ALCHEMY_RATIONALES
    ]


def build_eol_report(probes: dict[str, ToolchainProbe]) -> dict[str, Any]:
    report: dict[str, Any] = {}
    for key, probe in probes.items():
        if not probe.installed or not probe.runtime_version or not probe.eol_slug:
            continue
        cycle = fetch_eol_cycle(probe.eol_slug, probe.runtime_version)
        if not cycle:
            report[key] = {
                "version": probe.runtime_version,
                "status": "unknown",
                "source": "https://endoflife.date",
            }
            continue
        report[key] = {
            "version": probe.runtime_version,
            "cycle": cycle.get("cycle"),
            "eol": cycle.get("eol"),
            "latest": cycle.get("latest"),
            "latest_release_date": cycle.get("latestReleaseDate"),
            "support": cycle.get("support"),
            "extended_support": cycle.get("extendedSupport"),
            "link": cycle.get("link"),
            "source": "https://endoflife.date",
        }
    return report


def ensure_utf8() -> None:
    configure_utf8_output()
