#!/usr/bin/env python3
#-*- coding: utf-8 -*-
# @SID: P-06
# P-06 — VS 2022 BuildTools (14.4x) install gate + flash_attn source build retry
#
# Phase 1: detect MSVC 14.4x under VS 2022 BuildTools; install via winget if absent
# Phase 2: verify 14.4x cl.exe resolves both P-05 blockers:
#   - host_config.h version ceiling (14.4x < CUDA 12.8 max 14.40)
#   - CUTLASS platform::is_unsigned_v (14.51 STL breaks CUTLASS polyfill; 14.4x does not)
# Phase 3: attempt flash-attn==2.8.3 build targeting 14.4x toolchain
# Output: manifest/vs2022_flash_attn_probe.json

import datetime
import glob
import json
import os
import pathlib
import subprocess
import sys
import tempfile

MANIFEST_DIR = pathlib.Path(__file__).parents[2] / "manifest"
MANIFEST_DIR.mkdir(exist_ok=True)
MANIFEST_PATH = MANIFEST_DIR / "vs2022_flash_attn_probe.json"

VENV_PYTHON = r"C:\Users\eldno\chthonic-archive\dev\tabbyAPI\.venv\Scripts\python.exe"
CUDA_HOME = r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8"
VS2022_MSVC_BASE = r"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC"


def find_msvc_14_4x() -> tuple[str | None, str | None]:
    """Return (version_str, cl_exe_path) for the newest 14.4x MSVC under VS 2022 BuildTools."""
    if not os.path.isdir(VS2022_MSVC_BASE):
        return None, None
    candidates = sorted(
        glob.glob(os.path.join(VS2022_MSVC_BASE, "14.4*")), reverse=True
    )
    for candidate in candidates:
        cl = os.path.join(candidate, "bin", "Hostx64", "x64", "cl.exe")
        if os.path.isfile(cl):
            return os.path.basename(candidate), cl
    return None, None


def install_vs2022_buildtools() -> tuple[int, str]:
    """Install VS 2022 BuildTools with VCTools workload via winget."""
    cmd = [
        "winget", "install",
        "--id", "Microsoft.VisualStudio.2022.BuildTools",
        "--source", "winget",
        "--accept-package-agreements",
        "--accept-source-agreements",
        "--override",
        "--quiet --wait --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended --norestart",
    ]
    print("[P-06] Running winget install VS 2022 BuildTools (this may take 5–15 min)...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, (result.stdout + result.stderr)


def capture_vcvars_env(vctools_version: str) -> dict[str, str]:
    """Run vcvarsall.bat amd64 from VS 2022 BuildTools and capture the resulting environment.

    Uses a temp batch file to avoid cmd.exe quote-nesting bugs that prevent
    vcvarsall.bat from being invoked when the path contains spaces and the
    whole command is wrapped in outer double-quotes.
    """
    vcvarsall = r"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat"
    print(f"[P-06] vcvarsall: {vcvarsall}")

    bat_fd, bat_path = tempfile.mkstemp(suffix=".bat", prefix="p06_vcvars_")
    try:
        with os.fdopen(bat_fd, "w") as f:
            f.write("@echo off\r\n")
            f.write(f"set VCToolsVersion={vctools_version}\r\n")
            f.write(f'call "{vcvarsall}" amd64 > NUL 2>&1\r\n')
            f.write("set\r\n")

        result = subprocess.run(
            ["cmd.exe", "/c", bat_path],
            capture_output=True, text=True,
        )
        env: dict[str, str] = {}
        for line in result.stdout.splitlines():
            if "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
        return env
    finally:
        try:
            os.unlink(bat_path)
        except OSError:
            pass


def attempt_flash_attn_build(vctools_version: str) -> tuple[int, str]:
    """Attempt flash-attn==2.8.3 source build with VS 2022 14.4x toolchain."""
    env = capture_vcvars_env(vctools_version)
    if not env:
        # Fallback: manual env construction
        vctools_dir = os.path.join(VS2022_MSVC_BASE, vctools_version) + "\\"
        cl_bin_dir = os.path.join(vctools_dir, "bin", "Hostx64", "x64")
        env = os.environ.copy()
        env["VCToolsVersion"] = vctools_version
        env["VCToolsInstallDir"] = vctools_dir
        env["PATH"] = cl_bin_dir + os.pathsep + env.get("PATH", "")
    else:
        # Ensure CUDA_HOME is set in the captured env
        pass

    env["CUDA_HOME"] = CUDA_HOME
    env["VCToolsVersion"] = vctools_version  # re-assert in case vcvarsall reset it
    env["DISTUTILS_USE_SDK"] = "1"  # required by torch cpp_extension when VC env is pre-activated

    cl_bin_dir = os.path.join(VS2022_MSVC_BASE, vctools_version, "bin", "Hostx64", "x64")
    print(f"[P-06] Building flash-attn==2.8.3 with MSVC {vctools_version}...")
    print(f"       cl.exe: {os.path.join(cl_bin_dir, 'cl.exe')}")
    # Verify the captured INCLUDE points to 14.4x, not 14.51
    inc = env.get("INCLUDE", "")
    print(f"       INCLUDE[:120]: {inc[:120]}")

    cmd = [
        "uv", "pip", "install",
        "--python", VENV_PYTHON,
        "flash-attn==2.8.3",
        "--no-build-isolation",
    ]
    build_log_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "manifest", "flash_attn_build_full.log"
    )
    print(f"[P-06] Build output → {build_log_path}")
    with open(build_log_path, "w", encoding="utf-8", errors="replace") as flog:
        result = subprocess.run(
            cmd, stdout=flog, stderr=subprocess.STDOUT,
            text=True, env=env, timeout=7200
        )
    with open(build_log_path, "r", encoding="utf-8", errors="replace") as flog:
        combined = flog.read()
    # Tail for manifest; full log on disk for diagnosis
    tail = combined[-6000:] if len(combined) > 6000 else combined
    return result.returncode, tail


# ── Main ──────────────────────────────────────────────────────────────────────

manifest: dict = {
    "gate": "flash_attn/vs2022_buildtools_retry",
    "artifact_type": "probe",
    "probe_id": "P-06",
    "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    "target_package": "flash-attn==2.8.3",
    "build_mode": "--no-build-isolation",
    "cuda_home": CUDA_HOME,
    "venv_python": VENV_PYTHON,
    "vs2022_msvc_base": VS2022_MSVC_BASE,
}

# ── Phase 1: detect or install 14.4x ─────────────────────────────────────────
version, cl_path = find_msvc_14_4x()

if version:
    print(f"[P-06] VS 2022 14.4x detected: {version} — skipping install")
    manifest["vs2022_14_4x_detected"] = True
    manifest["vs2022_version"] = version
    manifest["vs2022_cl_path"] = cl_path
    manifest["install_phase"] = "skipped — already present"
else:
    print("[P-06] VS 2022 14.4x NOT found — installing via winget...")
    manifest["vs2022_14_4x_detected"] = False
    manifest["install_phase"] = "winget install attempted"

    rc, out = install_vs2022_buildtools()
    manifest["winget_exit_code"] = rc
    manifest["winget_output_tail"] = out[-3000:]

    version, cl_path = find_msvc_14_4x()
    manifest["vs2022_version_post_install"] = version
    manifest["vs2022_cl_path_post_install"] = cl_path

    if version:
        print(f"[P-06] Install succeeded — MSVC {version}")
    else:
        print("[P-06] Install step completed but 14.4x cl.exe still not found")

# ── Phase 2: build attempt ───────────────────────────────────────────────────
if not version:
    manifest["build_result"] = "SKIPPED"
    manifest["status"] = "vs2022_14_4x_not_available"
    manifest["level"] = "L0_blocked"
    print("[P-06] Cannot proceed — no 14.4x toolchain available")
else:
    rc, tail = attempt_flash_attn_build(version)
    manifest["build_exit_code"] = rc
    manifest["build_output_tail"] = tail

    if rc == 0:
        manifest["build_result"] = "SUCCESS"
        manifest["status"] = "source_build_succeeded_vs2022_14_4x"
        manifest["level"] = "L1_install_admitted"
        print("[P-06] BUILD SUCCEEDED — Gate 6 cleared with MSVC " + version)
    else:
        manifest["build_result"] = "FAILED"
        # Classify remaining blocker
        if "unsupported Microsoft Visual Studio version" in tail:
            blocker = "host_config.h ceiling still hit — VCToolsVersion env var not honoured by nvcc; check PATH ordering"
            manifest["status"] = "source_build_blocked_env_routing"
        elif "is_unsigned_v" in tail and "cutlass" in tail:
            blocker = "CUTLASS platform::is_unsigned_v still missing — 14.4x does not resolve it; flash_attn 2.8.3 CUTLASS incompatible with all MSVC"
            manifest["status"] = "source_build_blocked_cutlass_msvc_all"
        elif "is_unsigned_v" in tail:
            blocker = "is_unsigned_v error — different location than CUTLASS; inspect build_output_tail"
            manifest["status"] = "source_build_blocked_unknown_is_unsigned_v"
        else:
            blocker = "unknown — see build_output_tail"
            manifest["status"] = "source_build_blocked_unknown"
        manifest["remaining_blocker"] = blocker
        manifest["level"] = "L0_blocked"
        print(f"[P-06] BUILD FAILED — {blocker}")

# ── Output ────────────────────────────────────────────────────────────────────
print(json.dumps(manifest, indent=2))
MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))
print(f"\nmanifest written: {MANIFEST_PATH}", file=sys.stderr)
