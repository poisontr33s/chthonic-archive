#!/usr/bin/env python3
"""
MAS-MCP GPU Compatibility Probe
Validates Windows GPU environment against compatibility matrix.
Outputs probe_report.json with pass/fail per engine and active row selection.

SSOT: .github/copilot-instructions.md (MILFOLOGICAL Codex)

Usage:
  python probe_gpu_compatibility.py [--matrix PATH] [--output PATH]
"""

import argparse
import json
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict, field

# Default paths relative to mas_mcp
MAS_MCP_ROOT = Path(__file__).parent.parent
DEFAULT_MATRIX = MAS_MCP_ROOT / "artifacts" / "compatibility" / "matrix.json"
DEFAULT_OUTPUT = MAS_MCP_ROOT / "artifacts" / "compatibility" / "probe_report.json"

@dataclass
class ProbeResult:
    name: str
    passed: bool
    version: Optional[str] = None
    path: Optional[str] = None
    providers: Optional[list] = None
    error: Optional[str] = None
    details: dict = field(default_factory=dict)

@dataclass
class ProbeReport:
    timestamp: str
    ssot_ref: str
    matrix_version: str
    probes: list
    active_row_id: Optional[str]
    overall_status: str  # "pass", "partial", "fail"
    notes: list

def probe_nvidia_driver() -> ProbeResult:
    """Probe NVIDIA driver version via nvidia-smi."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            version = result.stdout.strip().split('\n')[0]
            return ProbeResult(
                name="nvidia_driver",
                passed=True,
                version=version,
                path="nvidia-smi"
            )
        else:
            return ProbeResult(
                name="nvidia_driver",
                passed=False,
                error=result.stderr.strip()
            )
    except FileNotFoundError:
        return ProbeResult(
            name="nvidia_driver",
            passed=False,
            error="nvidia-smi not found in PATH"
        )
    except Exception as e:
        return ProbeResult(
            name="nvidia_driver",
            passed=False,
            error=str(e)
        )

def probe_cuda_runtime() -> ProbeResult:
    """Probe CUDA runtime via environment and nvcc."""
    cuda_path = os.environ.get("CUDA_PATH") or os.environ.get("CUDA_HOME")
    
    # Try nvcc for version
    try:
        result = subprocess.run(
            ["nvcc", "--version"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            # Parse version from output
            import re
            match = re.search(r"release (\d+\.\d+)", result.stdout)
            version = match.group(1) if match else "unknown"
            return ProbeResult(
                name="cuda_runtime",
                passed=True,
                version=version,
                path=cuda_path,
                details={"nvcc_output": result.stdout.strip()[:200]}
            )
    except FileNotFoundError:
        pass
    except Exception as e:
        pass
    
    # Fallback: check CUDA_PATH exists
    if cuda_path and Path(cuda_path).exists():
        return ProbeResult(
            name="cuda_runtime",
            passed=True,
            version="unknown (nvcc not in PATH)",
            path=cuda_path
        )
    
    return ProbeResult(
        name="cuda_runtime",
        passed=False,
        error="CUDA_PATH not set or nvcc not found"
    )

def probe_cudnn() -> ProbeResult:
    """Probe cuDNN by checking for DLL in CUDA path or PATH."""
    cuda_path = os.environ.get("CUDA_PATH") or os.environ.get("CUDA_HOME")
    
    # Common cuDNN DLL names
    dll_names = ["cudnn64_9.dll", "cudnn64_8.dll", "cudnn.dll"]
    
    search_paths = []
    if cuda_path:
        search_paths.append(Path(cuda_path) / "bin")
    
    # Also check PATH
    for p in os.environ.get("PATH", "").split(os.pathsep):
        if "cuda" in p.lower() or "cudnn" in p.lower():
            search_paths.append(Path(p))
    
    for search_path in search_paths:
        for dll_name in dll_names:
            dll_path = search_path / dll_name
            if dll_path.exists():
                # Extract version from DLL name
                import re
                match = re.search(r"cudnn64_(\d+)", dll_name)
                version = match.group(1) + ".x" if match else "unknown"
                return ProbeResult(
                    name="cudnn",
                    passed=True,
                    version=version,
                    path=str(dll_path)
                )
    
    return ProbeResult(
        name="cudnn",
        passed=False,
        error="cuDNN DLL not found in CUDA_PATH/bin or PATH"
    )

def probe_tensorrt() -> ProbeResult:
    """Probe TensorRT by checking for nvinfer.dll."""
    # Check common TensorRT paths
    tensorrt_paths = [
        Path("C:/TensorRT-10.0.1/lib"),
        Path("C:/TensorRT-8.6.1/lib"),
        Path(os.environ.get("TENSORRT_PATH", "") or "").parent / "lib",
    ]
    
    # Also check PATH
    for p in os.environ.get("PATH", "").split(os.pathsep):
        if "tensorrt" in p.lower():
            tensorrt_paths.append(Path(p))
    
    for search_path in tensorrt_paths:
        nvinfer_dll = search_path / "nvinfer.dll"
        if nvinfer_dll.exists():
            # Try to get version from path
            import re
            match = re.search(r"TensorRT-(\d+\.\d+\.\d+)", str(search_path))
            version = match.group(1) if match else "unknown"
            return ProbeResult(
                name="tensorrt",
                passed=True,
                version=version,
                path=str(search_path)
            )
    
    return ProbeResult(
        name="tensorrt",
        passed=False,
        error="nvinfer.dll not found. Set TENSORRT_PATH or add TensorRT/lib to PATH."
    )

def probe_onnxruntime() -> ProbeResult:
    """Probe ONNX Runtime and its execution providers."""
    try:
        import onnxruntime as ort
        version = ort.__version__
        providers = ort.get_available_providers()
        
        has_cuda = "CUDAExecutionProvider" in providers
        has_trt = "TensorrtExecutionProvider" in providers
        
        return ProbeResult(
            name="onnxruntime",
            passed=has_cuda,  # Minimum requirement
            version=version,
            providers=providers,
            details={
                "cuda_ep": has_cuda,
                "tensorrt_ep": has_trt
            }
        )
    except ImportError:
        return ProbeResult(
            name="onnxruntime",
            passed=False,
            error="onnxruntime not installed"
        )
    except Exception as e:
        return ProbeResult(
            name="onnxruntime",
            passed=False,
            error=str(e)
        )

def probe_pytorch_cuda() -> ProbeResult:
    """Probe PyTorch CUDA availability."""
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        
        if cuda_available:
            return ProbeResult(
                name="pytorch_cuda",
                passed=True,
                version=torch.__version__,
                details={
                    "cuda_version": torch.version.cuda,
                    "cudnn_version": str(torch.backends.cudnn.version()),
                    "device_count": torch.cuda.device_count(),
                    "device_name": torch.cuda.get_device_name(0) if torch.cuda.device_count() > 0 else None
                }
            )
        else:
            return ProbeResult(
                name="pytorch_cuda",
                passed=False,
                version=torch.__version__,
                error="CUDA not available in PyTorch"
            )
    except ImportError:
        return ProbeResult(
            name="pytorch_cuda",
            passed=False,
            error="torch not installed"
        )
    except Exception as e:
        return ProbeResult(
            name="pytorch_cuda",
            passed=False,
            error=str(e)
        )

def probe_python_env() -> ProbeResult:
    """Probe Python environment (uv-managed check)."""
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    venv_path = os.environ.get("VIRTUAL_ENV")
    
    # Check if uv-managed
    is_uv = False
    if venv_path:
        uv_marker = Path(venv_path) / ".uv"
        pyproject = Path(venv_path).parent / "pyproject.toml"
        is_uv = uv_marker.exists() or (pyproject.exists() and "uv" in pyproject.read_text())
    
    return ProbeResult(
        name="python_env",
        passed=True,
        version=python_version,
        path=venv_path,
        details={
            "managed_by": "uv" if is_uv else "unknown",
            "executable": sys.executable
        }
    )

def select_active_row(matrix: dict, probes: list[ProbeResult]) -> tuple[Optional[str], list[str]]:
    """Select the best matching row from the matrix based on probe results."""
    notes = []
    
    # Build probe lookup
    probe_map = {p.name: p for p in probes}
    
    driver_probe = probe_map.get("nvidia_driver")
    if not driver_probe or not driver_probe.passed:
        notes.append("NVIDIA driver probe failed; no row can be selected.")
        return None, notes
    
    driver_version = float(driver_probe.version.split('.')[0])
    
    for row in matrix.get("rows", []):
        if row.get("status") not in ["approved", "testing"]:
            continue
        
        # Check driver version range
        driver_min = float(row["driver"]["version_min"])
        driver_max = float(row["driver"].get("version_max") or 9999)
        
        if not (driver_min <= driver_version <= driver_max):
            continue
        
        # Check CUDA version
        cuda_probe = probe_map.get("cuda_runtime")
        if not cuda_probe or not cuda_probe.passed:
            continue
        
        row_cuda = row["cuda"]["version"]
        if cuda_probe.version and not cuda_probe.version.startswith(row_cuda.split('.')[0]):
            # Major version mismatch
            continue
        
        # Check ONNX Runtime providers
        ort_probe = probe_map.get("onnxruntime")
        if not ort_probe or not ort_probe.passed:
            continue
        
        required_eps = set(row["onnxruntime"]["execution_providers"])
        available_eps = set(ort_probe.providers or [])
        
        if not required_eps.issubset(available_eps):
            missing = required_eps - available_eps
            notes.append(f"Row {row['row_id']}: missing EPs {missing}")
            continue
        
        # Row matches!
        notes.append(f"Selected row {row['row_id']} (status: {row['status']})")
        return row["row_id"], notes
    
    notes.append("No compatible row found in matrix.")
    return None, notes

def run_all_probes() -> list[ProbeResult]:
    """Run all GPU compatibility probes."""
    probes = [
        probe_nvidia_driver(),
        probe_cuda_runtime(),
        probe_cudnn(),
        probe_tensorrt(),
        probe_onnxruntime(),
        probe_pytorch_cuda(),
        probe_python_env(),
    ]
    return probes

def generate_report(matrix_path: Path) -> ProbeReport:
    """Generate full probe report."""
    # Load matrix
    with open(matrix_path) as f:
        matrix = json.load(f)
    
    # Run probes
    probes = run_all_probes()
    
    # Select active row
    active_row_id, notes = select_active_row(matrix, probes)
    
    # Determine overall status
    passed_count = sum(1 for p in probes if p.passed)
    total_count = len(probes)
    
    if active_row_id and passed_count == total_count:
        overall_status = "pass"
    elif active_row_id or passed_count >= total_count // 2:
        overall_status = "partial"
    else:
        overall_status = "fail"
    
    return ProbeReport(
        timestamp=datetime.now().isoformat() + "Z",
        ssot_ref=".github/copilot-instructions.md",
        matrix_version=matrix.get("matrix_version", "unknown"),
        probes=[asdict(p) for p in probes],
        active_row_id=active_row_id,
        overall_status=overall_status,
        notes=notes
    )

def main():
    parser = argparse.ArgumentParser(description="MAS-MCP GPU Compatibility Probe")
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX,
                        help="Path to compatibility matrix JSON")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help="Path to output probe report JSON")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print report without saving")
    args = parser.parse_args()
    
    print("🔍 MAS-MCP GPU Compatibility Probe")
    print(f"   SSOT: .github/copilot-instructions.md")
    print(f"   Matrix: {args.matrix}")
    print()
    
    if not args.matrix.exists():
        print(f"❌ Matrix file not found: {args.matrix}")
        sys.exit(1)
    
    report = generate_report(args.matrix)
    
    # Print summary
    print("📊 Probe Results:")
    for probe in report.probes:
        status = "✅" if probe["passed"] else "❌"
        version = probe.get("version") or "N/A"
        print(f"   {status} {probe['name']}: {version}")
        if probe.get("error"):
            print(f"      ⚠️  {probe['error']}")
    
    print()
    print(f"🏷️  Active Row: {report.active_row_id or 'None'}")
    print(f"📈 Overall Status: {report.overall_status.upper()}")
    
    for note in report.notes:
        print(f"   📝 {note}")
    
    if args.dry_run:
        print()
        print("--- DRY RUN: Report JSON ---")
        print(json.dumps(asdict(report), indent=2))
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, 'w') as f:
            json.dump(asdict(report), f, indent=2)
        print()
        print(f"💾 Report saved: {args.output}")
    
    # Exit code based on status
    if report.overall_status == "fail":
        sys.exit(2)
    elif report.overall_status == "partial":
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
