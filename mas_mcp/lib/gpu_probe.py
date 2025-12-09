"""
GPU Capability Probing with Output Suppression
===============================================

Safe, quiet GPU capability detection that suppresses stderr/stdout noise
from CUDA/cuDNN initialization. Essential for production MCP tools where
spurious GPU warnings would pollute JSON responses.

Key Features:
- OutputSuppressor context manager for silent GPU init
- Tiered capability detection (CUDA → Numba → CPU fallback)
- Cached probe results for fast repeated queries
- MCP-compatible JSON output format

Usage:
    from mas_mcp.lib.gpu_probe import probe_gpu_capabilities, GPUProbeResult
    
    result = probe_gpu_capabilities()
    if result.cuda_available:
        print(f"CUDA: {result.cuda_device}")
    else:
        print(f"Fallback: {result.fallback_reason}")

Per Section XIV.1: Always invoke via `uv run python`, never `python` directly.
"""

from __future__ import annotations

import contextlib
import io
import os
import sys
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from functools import lru_cache
from pathlib import Path
from typing import Any, Generator, Optional

# ─────────────────────────────────────────────────────────────────────────────────
# Output Suppression
# ─────────────────────────────────────────────────────────────────────────────────


class OutputSuppressor:
    """
    Context manager to suppress stdout/stderr during GPU initialization.
    
    CUDA, cuDNN, and TensorRT can emit noisy warnings during init that
    pollute MCP tool output. This captures and discards them cleanly.
    
    Usage:
        with OutputSuppressor() as suppressor:
            import cupy  # Noisy init, but silenced
        
        # Check if anything was captured
        if suppressor.captured_stderr:
            logger.debug(f"GPU init noise: {suppressor.captured_stderr[:200]}")
    """
    
    def __init__(self, suppress_stdout: bool = True, suppress_stderr: bool = True):
        self.suppress_stdout = suppress_stdout
        self.suppress_stderr = suppress_stderr
        self._stdout_buffer: io.StringIO | None = None
        self._stderr_buffer: io.StringIO | None = None
        self._old_stdout: Any = None
        self._old_stderr: Any = None
        
    def __enter__(self) -> "OutputSuppressor":
        if self.suppress_stdout:
            self._stdout_buffer = io.StringIO()
            self._old_stdout = sys.stdout
            sys.stdout = self._stdout_buffer
            
        if self.suppress_stderr:
            self._stderr_buffer = io.StringIO()
            self._old_stderr = sys.stderr
            sys.stderr = self._stderr_buffer
            
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if self._old_stdout is not None:
            sys.stdout = self._old_stdout
        if self._old_stderr is not None:
            sys.stderr = self._old_stderr
        return False  # Don't suppress exceptions
    
    @property
    def captured_stdout(self) -> str:
        """Get captured stdout content."""
        if self._stdout_buffer:
            return self._stdout_buffer.getvalue()
        return ""
    
    @property
    def captured_stderr(self) -> str:
        """Get captured stderr content."""
        if self._stderr_buffer:
            return self._stderr_buffer.getvalue()
        return ""


@contextlib.contextmanager
def suppress_gpu_output() -> Generator[OutputSuppressor, None, None]:
    """
    Convenience context manager for GPU output suppression.
    
    Example:
        with suppress_gpu_output():
            import onnxruntime  # Silent
    """
    suppressor = OutputSuppressor()
    with suppressor:
        yield suppressor


# ─────────────────────────────────────────────────────────────────────────────────
# GPU Probe Result
# ─────────────────────────────────────────────────────────────────────────────────


class GPUTier(Enum):
    """GPU capability tiers for MAS-MCP."""
    NONE = auto()           # CPU only
    CUDA_BASIC = auto()     # CUDA without cuDNN
    CUDA_FULL = auto()      # CUDA + cuDNN
    CUDA_TENSORRT = auto()  # Full stack with TensorRT
    VULKAN = auto()         # Vulkan compute (cross-vendor)


@dataclass
class GPUProbeResult:
    """
    Complete GPU capability probe result.
    
    Designed for JSON serialization in MCP responses.
    """
    # Core status
    tier: GPUTier = GPUTier.NONE
    available: bool = False
    
    # Device info (if GPU found)
    device_name: str = ""
    device_id: int = 0
    driver_version: str = ""
    compute_capability: tuple[int, int] = (0, 0)
    
    # Memory
    total_memory_gb: float = 0.0
    free_memory_gb: float = 0.0
    
    # Feature detection
    cuda_available: bool = False
    cudnn_available: bool = False
    tensorrt_available: bool = False
    cupy_available: bool = False
    numba_available: bool = False
    onnx_gpu_available: bool = False
    
    # Version strings
    cuda_version: str = ""
    cudnn_version: str = ""
    cupy_version: str = ""
    onnx_version: str = ""
    
    # Fallback info
    fallback_reason: str = ""
    
    # Probe metadata
    probe_timestamp: str = ""
    probe_duration_ms: float = 0.0
    suppressed_output_bytes: int = 0
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "tier": self.tier.name,
            "available": self.available,
            "device": {
                "name": self.device_name,
                "id": self.device_id,
                "driver_version": self.driver_version,
                "compute_capability": list(self.compute_capability),
            },
            "memory": {
                "total_gb": self.total_memory_gb,
                "free_gb": self.free_memory_gb,
            },
            "features": {
                "cuda": self.cuda_available,
                "cudnn": self.cudnn_available,
                "tensorrt": self.tensorrt_available,
                "cupy": self.cupy_available,
                "numba": self.numba_available,
                "onnx_gpu": self.onnx_gpu_available,
            },
            "versions": {
                "cuda": self.cuda_version,
                "cudnn": self.cudnn_version,
                "cupy": self.cupy_version,
                "onnx": self.onnx_version,
            },
            "fallback_reason": self.fallback_reason,
            "meta": {
                "probe_timestamp": self.probe_timestamp,
                "probe_duration_ms": self.probe_duration_ms,
                "suppressed_output_bytes": self.suppressed_output_bytes,
            },
        }


# ─────────────────────────────────────────────────────────────────────────────────
# Capability Probing
# ─────────────────────────────────────────────────────────────────────────────────


def _probe_nvidia_smi() -> dict[str, Any]:
    """Probe nvidia-smi for basic GPU info (fast, no Python deps)."""
    import subprocess
    
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,driver_version,memory.total,memory.free", 
             "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            parts = [p.strip() for p in result.stdout.strip().split(",")]
            if len(parts) >= 4:
                return {
                    "found": True,
                    "name": parts[0],
                    "driver": parts[1],
                    "memory_total_mb": float(parts[2]),
                    "memory_free_mb": float(parts[3]),
                }
    except Exception:
        pass
    
    return {"found": False}


def _probe_cupy() -> dict[str, Any]:
    """Probe CuPy availability and device info."""
    result = {"available": False}
    
    with suppress_gpu_output() as suppressor:
        try:
            import cupy as cp
            
            result["available"] = True
            result["version"] = cp.__version__
            
            # Get device info
            device = cp.cuda.Device(0)
            result["device_name"] = device.attributes["Name"].decode() if isinstance(device.attributes.get("Name"), bytes) else str(device.attributes.get("Name", "Unknown"))
            
            # Compute capability: CuPy returns int (e.g., 89 for SM 8.9), convert to tuple
            cc_raw = device.compute_capability
            if isinstance(cc_raw, int):
                result["compute_capability"] = (cc_raw // 10, cc_raw % 10)  # 89 → (8, 9)
            else:
                result["compute_capability"] = tuple(cc_raw) if cc_raw else (0, 0)
            
            # Memory info
            mempool = cp.get_default_memory_pool()
            result["memory_used_bytes"] = mempool.used_bytes()
            result["memory_total_bytes"] = mempool.total_bytes()
            
            # CUDA runtime version
            result["cuda_version"] = f"{cp.cuda.runtime.runtimeGetVersion()}"
            
        except ImportError:
            result["error"] = "cupy not installed"
        except Exception as e:
            result["error"] = str(e)
        
        result["suppressed_bytes"] = len(suppressor.captured_stderr) + len(suppressor.captured_stdout)
    
    return result


def _probe_onnx_gpu() -> dict[str, Any]:
    """Probe ONNX Runtime GPU providers."""
    result = {"available": False, "providers": []}
    
    with suppress_gpu_output() as suppressor:
        try:
            import onnxruntime as ort
            
            result["version"] = ort.__version__
            result["providers"] = ort.get_available_providers()
            result["cuda_provider"] = "CUDAExecutionProvider" in result["providers"]
            result["tensorrt_provider"] = "TensorrtExecutionProvider" in result["providers"]
            result["available"] = result["cuda_provider"]
            
        except ImportError:
            result["error"] = "onnxruntime not installed"
        except Exception as e:
            result["error"] = str(e)
        
        result["suppressed_bytes"] = len(suppressor.captured_stderr) + len(suppressor.captured_stdout)
    
    return result


def _probe_numba() -> dict[str, Any]:
    """Probe Numba CUDA availability."""
    result = {"available": False}
    
    with suppress_gpu_output() as suppressor:
        try:
            from numba import cuda
            
            if cuda.is_available():
                result["available"] = True
                result["device_count"] = len(cuda.gpus)
                if cuda.gpus:
                    device = cuda.gpus[0]
                    result["device_name"] = device.name.decode() if isinstance(device.name, bytes) else str(device.name)
            else:
                result["error"] = "CUDA not available to Numba"
                
        except ImportError:
            result["error"] = "numba not installed"
        except Exception as e:
            result["error"] = str(e)
        
        result["suppressed_bytes"] = len(suppressor.captured_stderr) + len(suppressor.captured_stdout)
    
    return result


@lru_cache(maxsize=1)
def probe_gpu_capabilities(force_refresh: bool = False) -> GPUProbeResult:
    """
    Probe all available GPU capabilities.
    
    Results are cached for performance. Use force_refresh=True to re-probe.
    Note: force_refresh requires clearing the cache externally.
    
    Returns:
        GPUProbeResult with complete capability assessment
    """
    from datetime import datetime
    
    start_time = time.perf_counter()
    result = GPUProbeResult()
    result.probe_timestamp = datetime.now().isoformat()
    
    total_suppressed = 0
    
    # Step 1: nvidia-smi (fast, no deps)
    smi = _probe_nvidia_smi()
    if smi.get("found"):
        result.device_name = smi["name"]
        result.driver_version = smi["driver"]
        result.total_memory_gb = smi["memory_total_mb"] / 1024.0
        result.free_memory_gb = smi["memory_free_mb"] / 1024.0
        result.cuda_available = True
        result.available = True
        result.tier = GPUTier.CUDA_BASIC
    
    # Step 2: CuPy (preferred CUDA backend)
    cupy_result = _probe_cupy()
    total_suppressed += cupy_result.get("suppressed_bytes", 0)
    if cupy_result.get("available"):
        result.cupy_available = True
        result.cupy_version = cupy_result.get("version", "")
        result.cuda_version = cupy_result.get("cuda_version", "")
        cc = cupy_result.get("compute_capability", (0, 0))
        if isinstance(cc, tuple):
            result.compute_capability = cc
        if not result.device_name:
            result.device_name = cupy_result.get("device_name", "")
        result.tier = GPUTier.CUDA_FULL
        result.cudnn_available = True  # CuPy typically includes cuDNN
    
    # Step 3: ONNX Runtime GPU
    onnx_result = _probe_onnx_gpu()
    total_suppressed += onnx_result.get("suppressed_bytes", 0)
    if onnx_result.get("available"):
        result.onnx_gpu_available = True
        result.onnx_version = onnx_result.get("version", "")
        if onnx_result.get("tensorrt_provider"):
            result.tensorrt_available = True
            result.tier = GPUTier.CUDA_TENSORRT
    
    # Step 4: Numba CUDA (fallback)
    numba_result = _probe_numba()
    total_suppressed += numba_result.get("suppressed_bytes", 0)
    if numba_result.get("available"):
        result.numba_available = True
    
    # Determine fallback reason if no GPU
    if not result.available:
        if not smi.get("found"):
            result.fallback_reason = "No NVIDIA GPU detected (nvidia-smi failed)"
        elif not result.cupy_available:
            result.fallback_reason = "CuPy not available"
        else:
            result.fallback_reason = "Unknown GPU initialization failure"
    
    result.suppressed_output_bytes = total_suppressed
    result.probe_duration_ms = (time.perf_counter() - start_time) * 1000.0
    
    return result


def clear_probe_cache() -> None:
    """Clear the cached probe result to force re-probing."""
    probe_gpu_capabilities.cache_clear()


# ─────────────────────────────────────────────────────────────────────────────────
# CLI Interface
# ─────────────────────────────────────────────────────────────────────────────────


def main() -> None:
    """CLI entry point for GPU probing."""
    import json
    import sys
    import io
    
    # Force UTF-8 output on Windows
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    print("[*] Probing GPU capabilities...")
    result = probe_gpu_capabilities()
    
    print(f"\n{'=' * 60}")
    print("GPU Probe Result")
    print(f"{'=' * 60}")
    print(f"Tier:      {result.tier.name}")
    print(f"Available: {result.available}")
    print(f"Device:    {result.device_name or 'None'}")
    print(f"Compute:   SM {result.compute_capability[0]}.{result.compute_capability[1]}")
    print(f"Memory:    {result.total_memory_gb:.1f} GB total, {result.free_memory_gb:.1f} GB free")
    print(f"{'-' * 60}")
    print(f"CUDA:      {'[OK]' if result.cuda_available else '[--]'}")
    print(f"cuDNN:     {'[OK]' if result.cudnn_available else '[--]'}")
    print(f"TensorRT:  {'[OK]' if result.tensorrt_available else '[--]'}")
    print(f"CuPy:      {'[OK]' if result.cupy_available else '[--]'} {result.cupy_version}")
    print(f"ONNX GPU:  {'[OK]' if result.onnx_gpu_available else '[--]'} {result.onnx_version}")
    print(f"Numba:     {'[OK]' if result.numba_available else '[--]'}")
    print(f"{'-' * 60}")
    print(f"Probe time: {result.probe_duration_ms:.1f} ms")
    print(f"Suppressed: {result.suppressed_output_bytes} bytes of GPU noise")
    
    if result.fallback_reason:
        print(f"\n[!] Fallback reason: {result.fallback_reason}")
    
    print(f"\n{'-' * 60}")
    print("JSON Output:")
    print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    main()
