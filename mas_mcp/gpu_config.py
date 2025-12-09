"""
🔥 GPU Configuration and Capability Detection

Detects available GPU backends (CUDA/CuPy, Numba, Vulkan) and provides
unified configuration for MAS-MCP performance modules.

Hardware Target: NVIDIA RTX 4090 Laptop GPU (Ada Lovelace, 7424 CUDA cores, 16GB VRAM)
System: Predator Helios 18 (Windows 11, CUDA 13.0)
Forward Compatible: RTX 5090, TensorRT integration
"""

import os
import sys
import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Callable, Any
from pathlib import Path

logger = logging.getLogger("mas.gpu")


class GPUBackend(Enum):
    """Available GPU compute backends."""
    NONE = auto()       # CPU-only fallback
    CUPY = auto()       # CuPy (preferred for RTX 4090 Laptop GPU)
    NUMBA = auto()      # Numba CUDA JIT
    VULKAN = auto()     # PyVulkan (cross-vendor)


@dataclass
class GPUCapabilities:
    """Detected GPU capabilities and limits."""
    backend: GPUBackend = GPUBackend.NONE
    device_name: str = "CPU Fallback"
    compute_capability: tuple[int, int] = (0, 0)
    total_memory_gb: float = 0.0
    multiprocessors: int = 0
    max_threads_per_block: int = 1024
    warp_size: int = 32
    
    # Runtime limits
    max_batch_size: int = 100_000  # Conservative default
    recommended_tile_size: int = 256
    
    # Feature flags
    has_tensor_cores: bool = False
    has_fp16: bool = False
    has_async_copy: bool = False
    
    def __post_init__(self):
        # Adjust limits based on detected hardware
        if self.backend == GPUBackend.CUPY and self.total_memory_gb >= 14:
            # RTX 4090 Laptop GPU with 16GB - moderate-aggressive batching
            self.max_batch_size = 500_000
            self.recommended_tile_size = 512
        elif self.backend == GPUBackend.CUPY and self.total_memory_gb >= 8:
            # Mid-range GPU
            self.max_batch_size = 250_000
            self.recommended_tile_size = 256


@dataclass
class GPUConfig:
    """Runtime GPU configuration with safety toggles."""
    
    # Master toggles
    gpu_enabled: bool = True
    ml_enabled: bool = False  # Gated - requires explicit opt-in
    
    # Performance tuning
    max_power_percent: int = 85  # Conservative for laptop thermal
    target_fps: int = 30
    batch_timeout_ms: float = 50.0
    
    # Determinism
    seed: int = 42
    float_tolerance: float = 1e-5
    position_bucket_size: float = 0.001
    
    # Safety
    governance_priority: bool = True  # Governance gates always CPU-authoritative
    auto_fallback: bool = True  # Fall back to CPU on GPU errors
    max_gpu_errors_before_disable: int = 3
    
    # Paths
    cache_dir: Path = field(default_factory=lambda: Path("mas_cache"))
    
    # Runtime state
    _gpu_error_count: int = field(default=0, repr=False)
    _capabilities: Optional[GPUCapabilities] = field(default=None, repr=False)
    
    def increment_error(self) -> bool:
        """Track GPU errors; returns True if GPU should be disabled."""
        self._gpu_error_count += 1
        if self._gpu_error_count >= self.max_gpu_errors_before_disable:
            logger.warning(f"GPU error threshold reached ({self._gpu_error_count}), disabling GPU")
            self.gpu_enabled = False
            return True
        return False
    
    def reset_errors(self):
        """Reset error count after successful GPU operation."""
        self._gpu_error_count = 0


# Global singleton
_config: Optional[GPUConfig] = None
_capabilities: Optional[GPUCapabilities] = None


def detect_gpu_capabilities() -> GPUCapabilities:
    """Detect available GPU backends and capabilities."""
    global _capabilities
    
    if _capabilities is not None:
        return _capabilities
    
    caps = GPUCapabilities()
    
    # Try CuPy first (preferred for NVIDIA)
    try:
        import cupy as cp
        device = cp.cuda.Device(0)
        props = cp.cuda.runtime.getDeviceProperties(0)
        
        caps.backend = GPUBackend.CUPY
        caps.device_name = props["name"].decode() if isinstance(props["name"], bytes) else props["name"]
        caps.compute_capability = (props["major"], props["minor"])
        caps.total_memory_gb = props["totalGlobalMem"] / (1024**3)
        caps.multiprocessors = props["multiProcessorCount"]
        caps.max_threads_per_block = props["maxThreadsPerBlock"]
        caps.warp_size = props["warpSize"]
        
        # Feature detection
        caps.has_tensor_cores = caps.compute_capability >= (7, 0)
        caps.has_fp16 = caps.compute_capability >= (5, 3)
        caps.has_async_copy = caps.compute_capability >= (8, 0)
        
        logger.info(f"CuPy backend: {caps.device_name} ({caps.total_memory_gb:.1f}GB, SM {caps.compute_capability})")
        _capabilities = caps
        return caps
        
    except ImportError:
        logger.debug("CuPy not available")
    except Exception as e:
        logger.warning(f"CuPy detection failed: {e}")
    
    # Try Numba CUDA
    try:
        from numba import cuda
        if cuda.is_available():
            device = cuda.get_current_device()
            caps.backend = GPUBackend.NUMBA
            caps.device_name = device.name.decode() if isinstance(device.name, bytes) else device.name
            caps.compute_capability = device.compute_capability
            caps.max_threads_per_block = device.MAX_THREADS_PER_BLOCK
            
            # Numba doesn't expose all properties easily
            caps.total_memory_gb = 8.0  # Conservative estimate
            
            logger.info(f"Numba CUDA backend: {caps.device_name}")
            _capabilities = caps
            return caps
            
    except ImportError:
        logger.debug("Numba not available")
    except Exception as e:
        logger.warning(f"Numba detection failed: {e}")
    
    # CPU fallback
    logger.info("No GPU backend detected, using CPU fallback")
    _capabilities = caps
    return caps


def get_config() -> GPUConfig:
    """Get or create the global GPU configuration."""
    global _config
    if _config is None:
        _config = GPUConfig()
        _config._capabilities = detect_gpu_capabilities()
    return _config


def get_capabilities() -> GPUCapabilities:
    """Get detected GPU capabilities."""
    config = get_config()
    return config._capabilities or detect_gpu_capabilities()


def gpu_available() -> bool:
    """Check if GPU compute is available and enabled."""
    config = get_config()
    caps = get_capabilities()
    return config.gpu_enabled and caps.backend != GPUBackend.NONE


def with_gpu_fallback(cpu_func: Callable, gpu_func: Callable) -> Callable:
    """
    Decorator/wrapper that uses GPU if available, falls back to CPU.
    
    Usage:
        result = with_gpu_fallback(cpu_score, gpu_score)(vectors)
    """
    def wrapper(*args, **kwargs) -> Any:
        config = get_config()
        
        if not gpu_available():
            return cpu_func(*args, **kwargs)
        
        try:
            result = gpu_func(*args, **kwargs)
            config.reset_errors()
            return result
        except Exception as e:
            logger.warning(f"GPU execution failed, falling back to CPU: {e}")
            if config.auto_fallback:
                config.increment_error()
                return cpu_func(*args, **kwargs)
            raise
    
    return wrapper


# Hardware-specific presets
PRESETS = {
    "rtx_4090_laptop": GPUConfig(
        max_power_percent=85,  # Thermal headroom for Predator Helios 18
        target_fps=30,
        batch_timeout_ms=50.0,
        seed=42,
    ),
    "rtx_4090_desktop": GPUConfig(
        max_power_percent=100,
        target_fps=60,
        batch_timeout_ms=25.0,
        seed=42,
    ),
    "safe_mode": GPUConfig(
        gpu_enabled=False,
        ml_enabled=False,
    ),
}

# Current mode tracking
_current_mode: str = "rtx_4090_laptop"  # Default to laptop for Predator Helios 18


def get_current_mode() -> str:
    """Get the currently active hardware profile mode."""
    return _current_mode


def set_mode(mode: str) -> GPUConfig:
    """
    Switch between laptop and desktop hardware profiles.
    
    Args:
        mode: One of 'laptop', 'desktop', 'safe', or full preset name
        
    Returns:
        The applied GPUConfig
        
    Example:
        >>> set_mode('desktop')  # Switch to desktop profile
        >>> set_mode('laptop')   # Switch back to laptop profile
    """
    global _current_mode
    
    # Shorthand aliases
    mode_aliases = {
        "laptop": "rtx_4090_laptop",
        "desktop": "rtx_4090_desktop",
        "safe": "safe_mode",
    }
    
    preset_name = mode_aliases.get(mode, mode)
    config = apply_preset(preset_name)
    _current_mode = preset_name
    
    logger.info(f"🔄 Mode switched to: {preset_name}")
    return config


def list_modes() -> dict:
    """List all available hardware profile modes with descriptions."""
    return {
        "laptop": {
            "preset": "rtx_4090_laptop",
            "description": "RTX 4090 Laptop GPU (Predator Helios 18) - 85% power, 30 FPS target",
            "power_percent": 85,
            "target_fps": 30,
        },
        "desktop": {
            "preset": "rtx_4090_desktop", 
            "description": "RTX 4090 Desktop - Full power, 60 FPS target",
            "power_percent": 100,
            "target_fps": 60,
        },
        "safe": {
            "preset": "safe_mode",
            "description": "CPU-only fallback - No GPU/ML",
            "power_percent": 0,
            "target_fps": 0,
        },
    }


def apply_preset(name: str) -> GPUConfig:
    """Apply a hardware preset configuration."""
    global _config
    if name not in PRESETS:
        raise ValueError(f"Unknown preset: {name}. Available: {list(PRESETS.keys())}")
    _config = PRESETS[name]
    _config._capabilities = detect_gpu_capabilities()
    logger.info(f"Applied GPU preset: {name}")
    return _config


# Alias for backward compatibility with orchestrator
ComputeBackend = GPUBackend
