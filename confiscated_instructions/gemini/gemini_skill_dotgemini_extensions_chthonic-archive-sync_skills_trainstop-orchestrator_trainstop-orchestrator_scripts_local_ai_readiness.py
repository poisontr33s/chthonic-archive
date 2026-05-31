#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: local_ai_readiness.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🔥 THE FOUNDRY
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Local AI Readiness Probe.

Purpose:
- Provide a deterministic "pivot gate" before wiring local LLM outputs into skill workflows.
- Check local runtime/module/model readiness and latest overnight artifact health.
- Emit compact mailbox artifacts for both Codex and Claude lanes.

Outputs:
- codex/mailbox/LOCAL_AI_READINESS_LATEST.json
- codex/mailbox/LOCAL_AI_READINESS_LATEST.md
- claude/mailbox/LOCAL_AI_READINESS_LATEST.json
- claude/mailbox/LOCAL_AI_READINESS_LATEST.md

@SID:           TOOL_LOCAL_AI_READINESS_V1
@Shabti:          Utility
@Purpose:       Local AI Readiness Probe.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for p in [cur, *cur.parents]:
        if (p / "AGENTS.md").exists() and (p / ".gitignore").exists():
            return p
    return start.resolve().parents[4]


REPO_ROOT = find_repo_root(Path(__file__))
DAEMON_ROOT = REPO_ROOT / "dumpster-dive" / "intake" / "overnight-daemon"
ARCH_ROOT = REPO_ROOT / "dumpster-dive" / "intake" / "overnight-intelligence"
CLAUDE_MAILBOX = REPO_ROOT / "claude" / "mailbox"
MODELS_ROOT = REPO_ROOT / "models"


@dataclass
class Check:
    name: str
    ok: bool
    detail: str
    notes: list[str] = field(default_factory=list)


@dataclass
class PathsState:
    latest_daemon_run: str | None
    latest_daemon_log: str | None
    latest_arch_run: str | None
    latest_digest: str | None


@dataclass
class Summary:
    runtime_ready: bool
    cpp_toolchain_ready: bool
    local_refiner_ready: bool
    hf_stack_ready: bool
    overnight_data_ready: bool
    scheduler_log_clean: bool
    ready_for_skill_integration: bool


@dataclass
class ModelResidence:
    name: str
    path: str
    format: str
    exists: bool
    file_count: int
    total_gb: float
    latest_mtime: str | None


@dataclass
class LaneStatus:
    lane: str
    language: str
    entrypoint: str
    model: str | None
    ready: bool
    required: list[str]
    missing_required: list[str]
    optional_missing: list[str]
    notes: list[str] = field(default_factory=list)


@dataclass
class Report:
    schema_version: int
    generated_on: str
    repo_root: str
    platform: dict[str, str]
    toolchain: dict[str, str | None]
    paths: PathsState
    summary: Summary
    models: list[ModelResidence]
    lanes: list[LaneStatus]
    checks: list[Check]
    recommendations: list[str]


def importable(module: str) -> bool:
    try:
        __import__(module)
        return True
    except Exception:
        return False


def run_output(cmd: list[str], *, allow_nonzero: bool = False) -> str | None:
    try:
        proc = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
        )
    except Exception:
        return None
    if proc.returncode != 0 and not allow_nonzero:
        return None
    text = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
    if not text:
        return None
    return text


def run_version(cmd: list[str], *, allow_nonzero: bool = False) -> str | None:
    text = run_output(cmd, allow_nonzero=allow_nonzero)
    if not text:
        return None
    return text.splitlines()[0].strip()


def detect_az_version(az_exe: str) -> str | None:
    try:
        proc = subprocess.run(
            [az_exe, "version", "--output", "json"],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
        )
    except Exception:
        return None
    if proc.returncode != 0:
        return None

    text = (proc.stdout or "").strip()
    if not text:
        return None
    try:
        data = json.loads(text)
    except Exception:
        # Some environments prepend informational lines; salvage the JSON object region.
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            return None
        try:
            data = json.loads(text[start : end + 1])
        except Exception:
            return None
    ver = data.get("azure-cli")
    return str(ver) if ver else None


def detect_vs_build_tools() -> str | None:
    program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    vswhere = Path(program_files_x86) / "Microsoft Visual Studio" / "Installer" / "vswhere.exe"
    if not vswhere.exists():
        return None

    # Prefer VC build-tools capable installation metadata.
    display = run_version(
        [
            str(vswhere),
            "-latest",
            "-products",
            "*",
            "-requires",
            "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
            "-property",
            "catalog_productDisplayVersion",
        ]
    )
    install = run_version(
        [
            str(vswhere),
            "-latest",
            "-products",
            "*",
            "-requires",
            "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
            "-property",
            "installationVersion",
        ]
    )
    if display and install:
        return f"display={display} install={install}"
    return display or install


def detect_vs_any_instance() -> str | None:
    program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    vswhere = Path(program_files_x86) / "Microsoft Visual Studio" / "Installer" / "vswhere.exe"
    if not vswhere.exists():
        return None

    display = run_version([str(vswhere), "-latest", "-products", "*", "-property", "displayName"])
    install = run_version([str(vswhere), "-latest", "-products", "*", "-property", "installationVersion"])
    if display and install:
        return f"{display} ({install})"
    return display or install


def detect_ssms_version() -> str | None:
    program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    vswhere = Path(program_files_x86) / "Microsoft Visual Studio" / "Installer" / "vswhere.exe"
    if not vswhere.exists():
        return None

    return run_version(
        [
            str(vswhere),
            "-latest",
            "-products",
            "Microsoft.VisualStudio.Product.Ssms",
            "-property",
            "installationVersion",
        ]
    )


def detect_vs_binary(patterns: list[str]) -> Path | None:
    roots = [
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Microsoft Visual Studio",
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Microsoft Visual Studio",
    ]

    candidates: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for pattern in patterns:
            candidates.extend(root.glob(pattern))

    if not candidates:
        return None

    # Choose the newest discovered tool path.
    return sorted(candidates, key=lambda p: p.as_posix(), reverse=True)[0]


def latest_dir(root: Path, pattern: str) -> Path | None:
    if not root.exists():
        return None
    matches = sorted((p for p in root.glob(pattern) if p.is_dir()), key=lambda p: p.name, reverse=True)
    return matches[0] if matches else None


def latest_file(root: Path, pattern: str) -> Path | None:
    if not root.exists():
        return None
    matches = sorted((p for p in root.glob(pattern) if p.is_file()), key=lambda p: p.stat().st_mtime, reverse=True)
    return matches[0] if matches else None


def model_dir_check(model_name: str, model_dir: Path, expected_format: str = "gguf") -> Check:
    if not model_dir.exists() or not model_dir.is_dir():
        return Check(name=f"model:{model_name}", ok=False, detail=f"missing: {model_dir.as_posix()}")
    if expected_format == "gguf":
        files = sorted(model_dir.glob("*.gguf"))
        ok = bool(files)
        detail = f"{len(files)} gguf file(s) in {model_dir.as_posix()}"
    else:
        files = sorted(model_dir.glob("*.safetensors"))
        ok = bool(files)
        detail = f"{len(files)} safetensors file(s) in {model_dir.as_posix()}"
    return Check(
        name=f"model:{model_name}",
        ok=ok,
        detail=detail,
    )


def model_residence(name: str, model_dir: Path) -> ModelResidence:
    if not model_dir.exists() or not model_dir.is_dir():
        return ModelResidence(
            name=name,
            path=model_dir.as_posix(),
            format="missing",
            exists=False,
            file_count=0,
            total_gb=0.0,
            latest_mtime=None,
        )

    files = [p for p in model_dir.rglob("*") if p.is_file()]
    gguf = [p for p in files if p.suffix.lower() == ".gguf"]
    safetensors = [p for p in files if p.suffix.lower() == ".safetensors"]
    if gguf:
        fmt = "gguf"
    elif safetensors:
        fmt = "safetensors/exl2"
    elif "exl2" in model_dir.name.lower():
        fmt = "exl2"
    else:
        fmt = "unknown"

    total_bytes = sum(p.stat().st_size for p in files)
    latest = max((p.stat().st_mtime for p in files), default=0)
    latest_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(latest)) if latest else None

    return ModelResidence(
        name=name,
        path=model_dir.as_posix(),
        format=fmt,
        exists=True,
        file_count=len(files),
        total_gb=round(total_bytes / (1024**3), 3),
        latest_mtime=latest_iso,
    )


def parse_scheduler_log_state(log_path: Path | None) -> tuple[bool, list[str]]:
    if log_path is None:
        return False, ["No scheduler log found."]

    text = log_path.read_text(encoding="utf-8", errors="replace")
    findings: list[str] = []
    bad = False

    if re.search(r"Traceback \(most recent call last\):", text):
        bad = True
        findings.append("Python traceback detected in scheduler log.")
    if "ModuleNotFoundError" in text:
        bad = True
        findings.append("ModuleNotFoundError detected in scheduler log.")
    if "FATAL ERROR:" in text or "UNHANDLED REJECTION:" in text:
        bad = True
        findings.append("Fatal/unhandled error marker detected in scheduler log.")

    if not bad:
        findings.append("No fatal markers in latest scheduler log.")
    return (not bad), findings


def lane_status(
    lane: str,
    language: str,
    entrypoint: str,
    model: str | None,
    required: list[str],
    optional: list[str],
    module_state: dict[str, bool],
    tool_state: dict[str, bool],
    tool_required: list[str] | None = None,
    notes: list[str] | None = None,
) -> LaneStatus:
    tool_required = tool_required or []
    missing_required = [x for x in required if not module_state.get(x, False)]
    missing_tools = [x for x in tool_required if not tool_state.get(x, False)]
    missing_required_all = missing_required + [f"tool:{x}" for x in missing_tools]
    optional_missing = [x for x in optional if not module_state.get(x, False)]
    ready = len(missing_required_all) == 0
    status_notes = list(notes or [])
    if missing_tools:
        status_notes.append(f"Missing required tool(s): {', '.join(missing_tools)}")

    return LaneStatus(
        lane=lane,
        language=language,
        entrypoint=entrypoint,
        model=model,
        ready=ready,
        required=required + [f"tool:{x}" for x in tool_required],
        missing_required=missing_required_all,
        optional_missing=optional_missing,
        notes=status_notes,
    )


def build_report() -> Report:
    checks: list[Check] = []

    uv_path = shutil.which("uv")
    bun_path = shutil.which("bun")
    pwsh_path = shutil.which("pwsh")
    rv_path = shutil.which("rv")
    ruby_path = shutil.which("ruby")
    az_path = shutil.which("az")
    rustc_path = shutil.which("rustc")
    cargo_path = shutil.which("cargo")
    cl_path = shutil.which("cl")
    cmake_path = shutil.which("cmake")
    ninja_path = shutil.which("ninja")
    msbuild_path = shutil.which("msbuild")
    glslc_path = shutil.which("glslc")
    vulkan_sdk = os.environ.get("VULKAN_SDK")
    cl_disk = detect_vs_binary(
        [
            "*/*/VC/Tools/MSVC/*/bin/Hostx64/x64/cl.exe",
            "*/Insiders/VC/Tools/MSVC/*/bin/Hostx64/x64/cl.exe",
            "*/BuildTools/VC/Tools/MSVC/*/bin/Hostx64/x64/cl.exe",
            "*/Community/VC/Tools/MSVC/*/bin/Hostx64/x64/cl.exe",
            "*/Professional/VC/Tools/MSVC/*/bin/Hostx64/x64/cl.exe",
            "*/Enterprise/VC/Tools/MSVC/*/bin/Hostx64/x64/cl.exe",
        ]
    )
    msbuild_disk = detect_vs_binary(
        [
            "*/*/MSBuild/Current/Bin/MSBuild.exe",
            "*/Insiders/MSBuild/Current/Bin/MSBuild.exe",
            "*/BuildTools/MSBuild/Current/Bin/MSBuild.exe",
            "*/Community/MSBuild/Current/Bin/MSBuild.exe",
            "*/Professional/MSBuild/Current/Bin/MSBuild.exe",
            "*/Enterprise/MSBuild/Current/Bin/MSBuild.exe",
        ]
    )
    vs_any_instance = detect_vs_any_instance()
    ssms_version = detect_ssms_version()
    vs_build_tools = detect_vs_build_tools()
    if not vs_build_tools and cl_disk:
        vs_build_tools = f"inferred_from_cl={cl_disk.parent.as_posix()}"
    az_version = detect_az_version(az_path) if az_path else None

    cl_effective = cl_path or (str(cl_disk) if cl_disk else None)
    msbuild_effective = msbuild_path or (str(msbuild_disk) if msbuild_disk else None)

    toolchain: dict[str, str | None] = {
        "uv": run_version(["uv", "--version"]) if uv_path else None,
        "python": sys.version.splitlines()[0],
        "rv": run_version(["rv", "--version"]) if rv_path else None,
        "ruby": run_version(["ruby", "--version"]) if ruby_path else None,
        "az": az_version,
        "bun": run_version(["bun", "--version"]) if bun_path else None,
        "pwsh": run_version(["pwsh", "-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"]) if pwsh_path else None,
        "rustc": run_version(["rustc", "--version"]) if rustc_path else None,
        "cargo": run_version(["cargo", "--version"]) if cargo_path else None,
        "msvc_cl": run_version(["cl", "/?"], allow_nonzero=True) if cl_path else cl_effective,
        "cmake": run_version(["cmake", "--version"]) if cmake_path else None,
        "ninja": run_version(["ninja", "--version"]) if ninja_path else None,
        "msbuild": run_version(["msbuild", "-version", "-nologo"]) if msbuild_path else msbuild_effective,
        "glslc": run_version(["glslc", "--version"]) if glslc_path else None,
        "vulkan_sdk": vulkan_sdk,
        "vs_build_tools": vs_build_tools,
        "vs_any_instance": vs_any_instance,
        "ssms": ssms_version,
    }
    tool_state = {
        "uv": bool(uv_path),
        "bun": bool(bun_path),
        "pwsh": bool(pwsh_path),
        "rv": bool(rv_path),
        "ruby": bool(ruby_path),
        "az": bool(az_path),
        "rustc": bool(rustc_path),
        "cargo": bool(cargo_path),
        "cl": bool(cl_effective),
        "cmake": bool(cmake_path),
        "ninja": bool(ninja_path),
        "msbuild": bool(msbuild_effective),
        "glslc": bool(glslc_path),
        "vulkan_sdk": bool(vulkan_sdk),
        "vs_build_tools": bool(vs_build_tools),
        "ssms": bool(ssms_version),
    }

    cl_detail = "cl not found on PATH"
    if cl_path:
        cl_detail = toolchain["msvc_cl"] or cl_path
    elif cl_disk:
        cl_detail = f"found on disk (not on PATH): {cl_disk.as_posix()}"

    msbuild_detail = "msbuild not found on PATH"
    if msbuild_path:
        msbuild_detail = toolchain["msbuild"] or msbuild_path
    elif msbuild_disk:
        msbuild_detail = f"found on disk (not on PATH): {msbuild_disk.as_posix()}"

    checks.append(
        Check(
            name="runtime:uv",
            ok=bool(uv_path),
            detail=toolchain["uv"] or "uv not found on PATH",
        )
    )
    checks.append(
        Check(
            name="runtime:python",
            ok=True,
            detail=toolchain["python"] or "python unknown",
        )
    )
    checks.append(
        Check(
            name="runtime:bun",
            ok=bool(bun_path),
            detail=toolchain["bun"] or "bun not found on PATH",
        )
    )
    checks.append(
        Check(
            name="runtime:pwsh",
            ok=bool(pwsh_path),
            detail=toolchain["pwsh"] or "pwsh not found on PATH",
        )
    )
    checks.append(
        Check(
            name="runtime:rustc",
            ok=bool(rustc_path),
            detail=toolchain["rustc"] or "rustc not found on PATH",
            notes=["Rust toolchain is optional for current local-AI paths but available for extension lanes."],
        )
    )
    checks.append(
        Check(
            name="runtime:rv",
            ok=bool(rv_path),
            detail=toolchain["rv"] or "rv not found on PATH",
            notes=["Ruby manager lane in your polyglot toolchain."],
        )
    )
    checks.append(
        Check(
            name="runtime:ruby",
            ok=bool(ruby_path),
            detail=toolchain["ruby"] or "ruby not found on PATH",
            notes=["Optional for local-AI flows; useful for broader polyglot automation."],
        )
    )
    checks.append(
        Check(
            name="runtime:az",
            ok=bool(az_path),
            detail=toolchain["az"] or ("az version query failed" if az_path else "az not found on PATH"),
            notes=["Azure CLI is optional but useful for model artifact storage and cloud deployment lanes."],
        )
    )
    checks.append(
        Check(
            name="runtime:msvc_cl",
            ok=bool(cl_effective),
            detail=cl_detail,
            notes=[
                "Core C++ compiler for native extension and tooling builds.",
                "If only found on disk, launch Developer PowerShell or run vcvarsall to activate PATH.",
            ],
        )
    )
    checks.append(
        Check(
            name="runtime:cmake",
            ok=bool(cmake_path),
            detail=toolchain["cmake"] or "cmake not found on PATH",
            notes=["Required by many C++/CUDA projects and local model runtimes."],
        )
    )
    checks.append(
        Check(
            name="runtime:ninja",
            ok=bool(ninja_path),
            detail=toolchain["ninja"] or "ninja not found on PATH",
            notes=["Recommended high-speed build backend for CMake projects."],
        )
    )
    checks.append(
        Check(
            name="runtime:msbuild",
            ok=bool(msbuild_effective),
            detail=msbuild_detail,
            notes=[
                "Needed for some Visual Studio and native extension workflows.",
                "If only found on disk, launch Developer PowerShell to expose msbuild on PATH.",
            ],
        )
    )
    checks.append(
        Check(
            name="runtime:glslc",
            ok=bool(glslc_path),
            detail=toolchain["glslc"] or "glslc not found on PATH",
            notes=["Shader compiler from Vulkan SDK."],
        )
    )
    checks.append(
        Check(
            name="runtime:vulkan_sdk",
            ok=bool(vulkan_sdk),
            detail=toolchain["vulkan_sdk"] or "VULKAN_SDK not set",
            notes=["Expected when targeting Vulkan-native shader/tooling lanes."],
        )
    )
    checks.append(
        Check(
            name="runtime:vs_build_tools",
            ok=bool(vs_build_tools),
            detail=toolchain["vs_build_tools"] or "Visual Studio Build Tools with VC workload not detected",
            notes=[
                "Uses vswhere for discovery.",
                f"Detected Visual Studio-family instance: {vs_any_instance}" if vs_any_instance else "No Visual Studio-family instance detected by vswhere.",
            ],
        )
    )
    checks.append(
        Check(
            name="runtime:ssms",
            ok=bool(ssms_version),
            detail=ssms_version or "SSMS instance not detected",
            notes=["SQL Server Management Studio detection via vswhere product Microsoft.VisualStudio.Product.Ssms."],
        )
    )

    module_names = [
        "llama_cpp",
        "pydantic",
        "numpy",
        "huggingface_hub",
        "requests",
        "mcp",
        "pydantic_settings",
        "transformers",
        "tokenizers",
        "safetensors",
        "datasets",
        "accelerate",
        "torch",
        "exllamav2",
    ]
    module_state = {name: importable(name) for name in module_names}
    for mod in module_names:
        notes: list[str] = []
        if mod == "llama_cpp" and not module_state[mod]:
            notes.append("Install hint: uv add --dev llama-cpp-python")
        if mod == "exllamav2" and not module_state[mod]:
            notes.append("Optional legacy lane for local_refiner.py (v1).")
        checks.append(
            Check(
                name=f"module:{mod}",
                ok=module_state[mod],
                detail="import ok" if module_state[mod] else f"missing module {mod}",
                notes=notes,
            )
        )

    qwen_dir = REPO_ROOT / "models" / "Qwen2.5-14B-Instruct-GGUF"
    gpt_oss_dir = REPO_ROOT / "models" / "GPT-OSS-20B-NEOPlus-Uncensored"
    llama_exl2_dir = REPO_ROOT / "models" / "Llama-3.1-8B-Instruct-exl2-6.0bpw"
    checks.append(model_dir_check("qwen_14b", qwen_dir, "gguf"))
    checks.append(model_dir_check("gpt_oss_20b", gpt_oss_dir, "gguf"))
    checks.append(model_dir_check("llama_8b_exl2", llama_exl2_dir, "safetensors"))

    latest_daemon_run = latest_dir(DAEMON_ROOT, "20*")
    latest_daemon_log = latest_file(DAEMON_ROOT, "nightly-scheduled-*.log")
    latest_arch_run = latest_dir(ARCH_ROOT, "arch-*")
    latest_digest = latest_file(CLAUDE_MAILBOX, "ARCHAEOLOGY_DIGEST_*.md")

    daemon_report_json = (latest_daemon_run / "report.json") if latest_daemon_run else None
    daemon_report_md = (latest_daemon_run / "report.md") if latest_daemon_run else None
    checks.append(
        Check(
            name="artifact:daemon_report_json",
            ok=bool(daemon_report_json and daemon_report_json.exists()),
            detail=daemon_report_json.as_posix() if daemon_report_json else "missing latest daemon run directory",
        )
    )
    checks.append(
        Check(
            name="artifact:daemon_report_md",
            ok=bool(daemon_report_md and daemon_report_md.exists()),
            detail=daemon_report_md.as_posix() if daemon_report_md else "missing latest daemon run directory",
        )
    )

    l1_ore = (latest_arch_run / "L1-ore.json") if latest_arch_run else None
    l1_summary = (latest_arch_run / "L1-summary.md") if latest_arch_run else None
    checks.append(
        Check(
            name="artifact:l1_ore",
            ok=bool(l1_ore and l1_ore.exists()),
            detail=l1_ore.as_posix() if l1_ore else "missing latest archaeology run directory",
        )
    )
    checks.append(
        Check(
            name="artifact:l1_summary",
            ok=bool(l1_summary and l1_summary.exists()),
            detail=l1_summary.as_posix() if l1_summary else "missing latest archaeology run directory",
        )
    )

    checks.append(
        Check(
            name="artifact:latest_digest",
            ok=bool(latest_digest),
            detail=latest_digest.as_posix() if latest_digest else "no ARCHAEOLOGY_DIGEST_*.md found",
            notes=["Digest absence is acceptable for L1-only runs."],
        )
    )

    scheduler_clean, scheduler_notes = parse_scheduler_log_state(latest_daemon_log)
    checks.append(
        Check(
            name="log:scheduler",
            ok=scheduler_clean,
            detail=latest_daemon_log.as_posix() if latest_daemon_log else "no scheduler log",
            notes=scheduler_notes,
        )
    )

    models = [
        model_residence("qwen_14b", qwen_dir),
        model_residence("gpt_oss_20b", gpt_oss_dir),
        model_residence("llama_8b_exl2", llama_exl2_dir),
    ]

    lanes: list[LaneStatus] = []
    lanes.append(
        lane_status(
            lane="local_refiner_v2",
            language="python",
            entrypoint="scripts/local_refiner_v2.py",
            model=qwen_dir.as_posix(),
            required=["llama_cpp", "pydantic", "numpy"],
            optional=["torch"],
            module_state=module_state,
            tool_state=tool_state,
            tool_required=["uv", "pwsh"],
            notes=["Primary local LLM lane (structured JSON)."],
        )
    )
    lanes.append(
        lane_status(
            lane="local_refiner_v1",
            language="python",
            entrypoint="scripts/local_refiner.py",
            model=llama_exl2_dir.as_posix(),
            required=["exllamav2", "torch"],
            optional=[],
            module_state=module_state,
            tool_state=tool_state,
            tool_required=["uv", "pwsh"],
            notes=["Legacy fallback lane (ExLlamaV2)."],
        )
    )
    lanes.append(
        lane_status(
            lane="hf_refiner",
            language="python",
            entrypoint="scripts/hf_refiner.py",
            model=None,
            required=["huggingface_hub", "requests", "mcp", "pydantic_settings"],
            optional=["transformers", "datasets", "accelerate", "tokenizers", "safetensors"],
            module_state=module_state,
            tool_state=tool_state,
            tool_required=["uv", "pwsh"],
            notes=["Uses HF token auth; can run without local GPU model files."],
        )
    )
    lanes.append(
        lane_status(
            lane="overnight_daemon",
            language="typescript+powershell",
            entrypoint="scripts/run_archaeology.ps1 + scripts/overnight_daemon.ts",
            model=None,
            required=[],
            optional=[],
            module_state=module_state,
            tool_state=tool_state,
            tool_required=["bun", "pwsh", "uv"],
            notes=["Scavenge/classification lane that feeds L1 ore and daemon reports."],
        )
    )
    lanes.append(
        lane_status(
            lane="cpp_vulkan_toolchain",
            language="msvc+cmake+ninja+vulkan",
            entrypoint="native toolchain baseline for local-ai extensions + shaders",
            model=None,
            required=[],
            optional=[],
            module_state=module_state,
            tool_state=tool_state,
            tool_required=["cl", "cmake", "ninja", "glslc", "vulkan_sdk"],
            notes=[
                "Tracks native/C++ readiness for local model backends and Vulkan shader pipelines.",
                "msbuild and vs_build_tools are reported as additional environment indicators.",
            ],
        )
    )

    runtime_ready = all(c.ok for c in checks if c.name in {"runtime:uv", "runtime:python", "runtime:bun", "runtime:pwsh"})
    cpp_toolchain_ready = all(
        lane.ready for lane in lanes if lane.lane == "cpp_vulkan_toolchain"
    )
    local_refiner_ready = all(
        lane.ready for lane in lanes if lane.lane == "local_refiner_v2"
    )
    hf_stack_ready = all(
        lane.ready for lane in lanes if lane.lane == "hf_refiner"
    )
    overnight_data_ready = all(
        c.ok
        for c in checks
        if c.name
        in {
            "artifact:daemon_report_json",
            "artifact:daemon_report_md",
            "artifact:l1_ore",
            "artifact:l1_summary",
        }
    )
    ready_for_skill_integration = runtime_ready and local_refiner_ready and overnight_data_ready and scheduler_clean

    recommendations: list[str] = []
    if not local_refiner_ready:
        recommendations.append("Install local refiner deps and verify Qwen GGUF model directory before skill-side automation.")
    if not cpp_toolchain_ready:
        recommendations.append("Complete C++/Vulkan toolchain readiness (cl/cmake/ninja/glslc/VULKAN_SDK) for native extension and shader lanes.")
    if not scheduler_clean:
        recommendations.append("Fix scheduler/runtime errors first; treat latest run as informational only.")
    if not overnight_data_ready:
        recommendations.append("Re-run overnight pipeline to refresh L1 artifacts before ingesting into skills.")
    if not hf_stack_ready:
        recommendations.append("HF stack has missing modules; run: uv run scripts/hf_prep.py --apply --with transformers,datasets,accelerate")
    legacy_lane = next((lane for lane in lanes if lane.lane == "local_refiner_v1"), None)
    if legacy_lane and not legacy_lane.ready:
        recommendations.append("Legacy ExLlamaV2 lane is not fully ready; keep v2 (llama-cpp) as primary.")
    if ready_for_skill_integration:
        recommendations.append("Safe to route nightly outputs into skill workflows (ingest/mailbox/orchestrator lanes).")

    return Report(
        schema_version=1,
        generated_on=utc_now(),
        repo_root=REPO_ROOT.as_posix(),
        platform={
            "system": platform.system(),
            "release": platform.release(),
            "python": sys.version.splitlines()[0],
        },
        toolchain=toolchain,
        paths=PathsState(
            latest_daemon_run=latest_daemon_run.as_posix() if latest_daemon_run else None,
            latest_daemon_log=latest_daemon_log.as_posix() if latest_daemon_log else None,
            latest_arch_run=latest_arch_run.as_posix() if latest_arch_run else None,
            latest_digest=latest_digest.as_posix() if latest_digest else None,
        ),
        summary=Summary(
            runtime_ready=runtime_ready,
            cpp_toolchain_ready=cpp_toolchain_ready,
            local_refiner_ready=local_refiner_ready,
            hf_stack_ready=hf_stack_ready,
            overnight_data_ready=overnight_data_ready,
            scheduler_log_clean=scheduler_clean,
            ready_for_skill_integration=ready_for_skill_integration,
        ),
        models=models,
        lanes=lanes,
        checks=checks,
        recommendations=recommendations,
    )


def write_mailbox_artifacts(report: Report, mailbox: str) -> None:
    mailbox_dir = REPO_ROOT / mailbox / "mailbox"
    mailbox_dir.mkdir(parents=True, exist_ok=True)

    json_path = mailbox_dir / "LOCAL_AI_READINESS_LATEST.json"
    md_path = mailbox_dir / "LOCAL_AI_READINESS_LATEST.md"

    json_path.write_text(
        json.dumps(asdict(report), indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    lines: list[str] = []
    lines.append("# Local AI Readiness (Latest)")
    lines.append("")
    lines.append(f"- Generated: `{report.generated_on}`")
    lines.append(f"- Runtime ready: `{report.summary.runtime_ready}`")
    lines.append(f"- C++/Vulkan toolchain ready: `{report.summary.cpp_toolchain_ready}`")
    lines.append(f"- Local refiner ready: `{report.summary.local_refiner_ready}`")
    lines.append(f"- HF stack ready: `{report.summary.hf_stack_ready}`")
    lines.append(f"- Overnight data ready: `{report.summary.overnight_data_ready}`")
    lines.append(f"- Scheduler log clean: `{report.summary.scheduler_log_clean}`")
    lines.append(f"- Ready for skill integration: `{report.summary.ready_for_skill_integration}`")
    lines.append("")
    lines.append("## Toolchain")
    for k, v in report.toolchain.items():
        lines.append(f"- `{k}`: `{v}`")
    lines.append("")
    lines.append("## Paths")
    lines.append(f"- Latest daemon run: `{report.paths.latest_daemon_run}`")
    lines.append(f"- Latest scheduler log: `{report.paths.latest_daemon_log}`")
    lines.append(f"- Latest archaeology run: `{report.paths.latest_arch_run}`")
    lines.append(f"- Latest digest: `{report.paths.latest_digest}`")
    lines.append("")
    lines.append("## Model Residences")
    for model in report.models:
        lines.append(
            f"- `{model.name}`: exists=`{model.exists}` format=`{model.format}` files=`{model.file_count}` size_gb=`{model.total_gb}` path=`{model.path}`"
        )
    lines.append("")
    lines.append("## Lane Baseline")
    for lane in report.lanes:
        lines.append(f"- `{lane.lane}` [{lane.language}] ready=`{lane.ready}` entry=`{lane.entrypoint}`")
        if lane.model:
            lines.append(f"  - model: `{lane.model}`")
        lines.append(f"  - required: `{', '.join(lane.required) if lane.required else '(none)'}`")
        lines.append(f"  - missing_required: `{', '.join(lane.missing_required) if lane.missing_required else '(none)'}`")
        lines.append(f"  - optional_missing: `{', '.join(lane.optional_missing) if lane.optional_missing else '(none)'}`")
        for note in lane.notes:
            lines.append(f"  - {note}")
    lines.append("")
    lines.append("## Checks")
    for c in report.checks:
        status = "OK" if c.ok else "FAIL"
        lines.append(f"- `{status}` `{c.name}`: {c.detail}")
        for note in c.notes:
            lines.append(f"  - {note}")
    lines.append("")
    lines.append("## Recommendations")
    if report.recommendations:
        for rec in report.recommendations:
            lines.append(f"- {rec}")
    else:
        lines.append("- No blocking readiness actions.")
    lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--mailboxes",
        default="codex,claude",
        help="Comma-separated mailbox roots to emit into (codex,claude).",
    )
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero if not ready_for_skill_integration.",
    )
    args = ap.parse_args()

    targets = [x.strip().lower() for x in args.mailboxes.split(",") if x.strip()]
    valid = {"codex", "claude"}
    unknown = [x for x in targets if x not in valid]
    if unknown:
        raise SystemExit(f"Unknown mailbox target(s): {', '.join(unknown)}")

    report = build_report()
    for mailbox in targets:
        write_mailbox_artifacts(report, mailbox)
        print(f"Wrote: {mailbox}/mailbox/LOCAL_AI_READINESS_LATEST.json")
        print(f"Wrote: {mailbox}/mailbox/LOCAL_AI_READINESS_LATEST.md")

    if args.strict and not report.summary.ready_for_skill_integration:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
