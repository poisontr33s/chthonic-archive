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
    ONNX_GPU = auto()   # ONNX Runtime with CUDA/TensorRT providers


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
        if self.backend in (GPUBackend.CUPY, GPUBackend.ONNX_GPU) and self.total_memory_gb >= 14:
            # RTX 4090 Laptop GPU with 16GB - moderate-aggressive batching
            self.max_batch_size = 500_000
            self.recommended_tile_size = 512
        elif self.backend in (GPUBackend.CUPY, GPUBackend.ONNX_GPU) and self.total_memory_gb >= 8:
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
    
    # Try ONNX Runtime GPU (CUDA/TensorRT providers)
    try:
        import onnxruntime as ort
        providers = ort.get_available_providers()
        
        has_cuda = "CUDAExecutionProvider" in providers
        has_tensorrt = "TensorRTExecutionProvider" in providers
        
        if has_cuda or has_tensorrt:
            caps.backend = GPUBackend.ONNX_GPU
            
            # Get device info via ONNX Runtime
            try:
                # Create a minimal session to get device info
                import numpy as np
                # Check if CUDA is functional by getting device properties
                if has_cuda:
                    # Use nvidia-smi fallback for device name
                    import subprocess
                    result = subprocess.run(
                        ["nvidia-smi", "--query-gpu=name,memory.total,compute_cap", "--format=csv,noheader,nounits"],
                        capture_output=True, text=True, timeout=5
                    )
                    if result.returncode == 0:
                        parts = result.stdout.strip().split(", ")
                        if len(parts) >= 3:
                            caps.device_name = parts[0].strip()
                            caps.total_memory_gb = float(parts[1].strip()) / 1024  # MB to GB
                            cc_str = parts[2].strip()
                            if "." in cc_str:
                                major, minor = cc_str.split(".")
                                caps.compute_capability = (int(major), int(minor))
                            
                            # Feature detection based on compute capability
                            caps.has_tensor_cores = caps.compute_capability >= (7, 0)
                            caps.has_fp16 = caps.compute_capability >= (5, 3)
                            caps.has_async_copy = caps.compute_capability >= (8, 0)
            except Exception as e:
                logger.debug(f"ONNX GPU device query failed: {e}")
                caps.device_name = "ONNX CUDA/TensorRT Device"
                caps.total_memory_gb = 8.0  # Conservative estimate
            
            provider_str = "TensorRT+CUDA" if has_tensorrt else "CUDA"
            logger.info(f"ONNX Runtime GPU backend: {caps.device_name} ({caps.total_memory_gb:.1f}GB, {provider_str})")
            _capabilities = caps
            return caps
            
    except ImportError:
        logger.debug("ONNX Runtime not available")
    except Exception as e:
        logger.warning(f"ONNX Runtime GPU detection failed: {e}")
    
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
        max_power_percent=85,  # Thermal headroom
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


def apply_preset(name: str) -> GPUConfig:
    """Apply a hardware preset configuration."""
    global _config
    if name not in PRESETS:
        raise ValueError(f"Unknown preset: {name}. Available: {list(PRESETS.keys())}")
    _config = PRESETS[name]
    _config._capabilities = detect_gpu_capabilities()
    logger.info(f"Applied GPU preset: {name}")
    return _config


# ═══════════════════════════════════════════════════════════════════════════════
# TILING LAYER - Prevents GPU stalls and Windows TDR timeouts
# Windows TDR kills GPU kernels running >2 seconds. Tile workloads to stay safe.
# ═══════════════════════════════════════════════════════════════════════════════

import time
import numpy as np
from typing import Iterator, TypeVar, Generic

T = TypeVar('T')


@dataclass
class TileMetrics:
    """Metrics from a tiled GPU operation."""
    total_items: int = 0
    tile_count: int = 0
    tile_size: int = 0
    total_ms: float = 0.0
    tile_times_ms: list = field(default_factory=list)
    max_tile_ms: float = 0.0
    backend: str = "unknown"
    
    @property
    def avg_tile_ms(self) -> float:
        return self.total_ms / self.tile_count if self.tile_count > 0 else 0.0
    
    @property
    def items_per_second(self) -> float:
        return (self.total_items / self.total_ms * 1000) if self.total_ms > 0 else 0.0


class TiledBatchProcessor:
    """
    Automatic tiling for GPU workloads to prevent TDR timeouts.
    
    Windows TDR timeout is ~2 seconds. We target <500ms per tile for safety.
    Recommended tile sizes:
      - Batch scoring: 5,000-10,000 vectors
      - Hierarchy layout: 1,000-5,000 nodes per pass
    """
    
    # Safe defaults based on RTX 4090 Laptop GPU testing
    DEFAULT_TILE_SIZES = {
        'score': 5000,      # vectors per tile
        'hierarchy': 2000,  # nodes per pass  
        'edges': 50000,     # edges per tile
    }
    
    # Maximum ms per tile before we shrink tile size
    MAX_TILE_MS = 500.0
    
    # Minimum tile size (below this, just run CPU)
    MIN_TILE_SIZE = 100
    
    def __init__(
        self,
        tile_size: Optional[int] = None,
        mode: str = 'score',
        adaptive: bool = True
    ):
        """
        Args:
            tile_size: Items per tile (auto if None)
            mode: 'score', 'hierarchy', or 'edges' - affects defaults
            adaptive: If True, shrink tile size when tiles run slow
        """
        self.mode = mode
        self.adaptive = adaptive
        self._tile_size = tile_size or self.DEFAULT_TILE_SIZES.get(mode, 5000)
        self._last_metrics: Optional[TileMetrics] = None
        
    @property
    def tile_size(self) -> int:
        return max(self.MIN_TILE_SIZE, self._tile_size)
    
    def tiles(self, items: list) -> Iterator[tuple[int, list]]:
        """
        Yield (tile_index, tile_items) for each tile.
        
        Usage:
            for tile_idx, tile_items in processor.tiles(all_items):
                result = process_tile(tile_items)
                accumulate(result)
        """
        size = self.tile_size
        for i in range(0, len(items), size):
            yield i // size, items[i:i + size]
    
    def tiles_array(self, arr: np.ndarray) -> Iterator[tuple[int, np.ndarray]]:
        """Yield (tile_index, tile_array) for numpy arrays."""
        size = self.tile_size
        for i in range(0, len(arr), size):
            yield i // size, arr[i:i + size]
    
    def adapt_tile_size(self, tile_ms: float):
        """Shrink tile size if a tile ran too slow."""
        if not self.adaptive:
            return
        
        if tile_ms > self.MAX_TILE_MS:
            # Shrink by ratio of overage
            ratio = self.MAX_TILE_MS / tile_ms
            new_size = int(self._tile_size * ratio * 0.9)  # 10% safety margin
            self._tile_size = max(self.MIN_TILE_SIZE, new_size)
            logger.warning(
                f"Tile took {tile_ms:.0f}ms (>{self.MAX_TILE_MS}ms), "
                f"shrinking tile size to {self._tile_size}"
            )
    
    def record_metrics(
        self,
        total_items: int,
        tile_times: list[float],
        backend: str
    ) -> TileMetrics:
        """Record metrics from a tiled operation."""
        self._last_metrics = TileMetrics(
            total_items=total_items,
            tile_count=len(tile_times),
            tile_size=self.tile_size,
            total_ms=sum(tile_times),
            tile_times_ms=tile_times,
            max_tile_ms=max(tile_times) if tile_times else 0.0,
            backend=backend,
        )
        return self._last_metrics
    
    @property
    def last_metrics(self) -> Optional[TileMetrics]:
        return self._last_metrics


# Global tiler instances for reuse
_score_tiler = TiledBatchProcessor(mode='score')
_hierarchy_tiler = TiledBatchProcessor(mode='hierarchy')


def get_score_tiler() -> TiledBatchProcessor:
    """Get the global score tiling processor."""
    return _score_tiler


def get_hierarchy_tiler() -> TiledBatchProcessor:
    """Get the global hierarchy tiling processor."""
    return _hierarchy_tiler


# ═══════════════════════════════════════════════════════════════════════════════
# MAS-MCP TOOL API FUNCTIONS
# These are the entry points called by server.py
# ═══════════════════════════════════════════════════════════════════════════════

# Cup size to numeric mapping for feature vector
CUP_VALUES = {
    'A': 0.1, 'B': 0.2, 'C': 0.3, 'D': 0.4, 'DD': 0.5,
    'E': 0.5, 'F': 0.6, 'G': 0.7, 'H': 0.8, 'I': 0.9, 'J': 0.95, 'K': 1.0
}


def _parse_measurements(measurements: Optional[str]) -> tuple:
    """Parse 'B120/W55/H112' format to numeric tuple."""
    if not measurements:
        return (0.0, 0.0, 0.0)
    try:
        parts = measurements.replace('B', '').replace('W', '').replace('H', '').split('/')
        return tuple(float(p) for p in parts[:3])
    except:
        return (0.0, 0.0, 0.0)


def _entity_to_vector(
    entity_name: str,
    whr: Optional[float] = None,
    tier: Optional[float] = None,
    cup: Optional[str] = None,
    measurements: Optional[str] = None
) -> np.ndarray:
    """Convert entity attributes to feature vector for scoring."""
    # Parse measurements
    bust, waist, hips = _parse_measurements(measurements)
    
    # Compute WHR if not provided
    if whr is None and waist > 0 and hips > 0:
        whr = waist / hips
    
    # Build feature vector
    features = np.array([
        whr if whr is not None else 0.5,
        tier if tier is not None else 2.0,
        CUP_VALUES.get(cup.upper() if cup else '', 0.5),
        bust / 150.0 if bust > 0 else 0.5,  # Normalized
        waist / 80.0 if waist > 0 else 0.5,
        hips / 130.0 if hips > 0 else 0.5,
    ], dtype=np.float32)
    
    return features


def mas_gpu_score(
    entity_name: str,
    whr: Optional[float] = None,
    tier: Optional[float] = None,
    cup: Optional[str] = None,
    measurements: Optional[str] = None
) -> dict:
    """
    🚀 Score a single entity using GPU acceleration.
    
    Returns novelty, redundancy, safety, and overall scores with governance thresholds.
    """
    config = get_config()
    caps = get_capabilities()
    seed = config.seed
    
    t0 = time.perf_counter()
    
    # Convert entity to vector
    vector = _entity_to_vector(entity_name, whr, tier, cup, measurements)
    
    # Create small reference set for scoring context
    rng = np.random.default_rng(seed)
    reference = rng.random((100, 6)).astype(np.float32)  # Synthetic reference
    
    # Try to use GPU scoring
    try:
        from gpu_scores import batch_score
        result = batch_score(
            vectors=vector.reshape(1, -1),
            reference=reference,
            features=vector.reshape(1, -1),
            seed=seed
        )
        
        elapsed = (time.perf_counter() - t0) * 1000
        
        return {
            "entity": entity_name,
            "novelty": float(result.novelty[0]),
            "redundancy": float(result.redundancy[0]),
            "safety": float(result.safety[0]),
            "overall": float(result.overall[0]),
            "meets_thresholds": bool(result.meets_thresholds()[0]),
            "in_grace_window": bool(result.in_grace_window()[0]),
            "backend": result.backend_used,
            "elapsed_ms": round(elapsed, 2),
            "seed": seed,
            "thresholds": {
                "novelty_min": 0.7,
                "redundancy_max": 0.3,
                "safety_min": 0.8
            }
        }
        
    except ImportError as e:
        logger.warning(f"GPU scoring unavailable: {e}")
        # CPU fallback with synthetic scores
        rng = np.random.default_rng(seed + hash(entity_name) % 1000)
        elapsed = (time.perf_counter() - t0) * 1000
        
        return {
            "entity": entity_name,
            "novelty": float(rng.uniform(0.5, 1.0)),
            "redundancy": float(rng.uniform(0.0, 0.5)),
            "safety": float(rng.uniform(0.7, 1.0)),
            "overall": float(rng.uniform(0.5, 0.9)),
            "meets_thresholds": False,
            "in_grace_window": True,
            "backend": "cpu_fallback",
            "elapsed_ms": round(elapsed, 2),
            "seed": seed,
            "warning": "Using synthetic fallback scores"
        }


def mas_gpu_batch_score(
    entities: list,
    seed: Optional[int] = None,
    tile_size: Optional[int] = None
) -> dict:
    """
    🚀 Batch score multiple entities using GPU acceleration with automatic tiling.
    
    Tiling prevents GPU stalls by processing in safe chunks (<500ms per tile).
    
    Args:
        entities: List of dicts with keys: name, whr, tier, cup, measurements
                  OR list of dicts with keys: id, vec (raw vectors)
        seed: Optional random seed for reproducibility
        tile_size: Override tile size (default: 5000 vectors)
    
    Returns:
        Batch results with individual scores and aggregate statistics.
    """
    config = get_config()
    seed = seed or config.seed
    
    t0 = time.perf_counter()
    
    if not entities:
        return {"error": "No entities provided", "count": 0}
    
    # Check if raw vectors or entity dicts
    if 'vec' in entities[0]:
        # Raw vector mode (benchmark format)
        vectors = np.array([e['vec'] for e in entities], dtype=np.float32)
        entity_ids = [e.get('id', f'e{i}') for i, e in enumerate(entities)]
    else:
        # Entity attribute mode
        vectors = np.array([
            _entity_to_vector(
                e.get('name', ''),
                e.get('whr'),
                e.get('tier'),
                e.get('cup'),
                e.get('measurements')
            )
            for e in entities
        ], dtype=np.float32)
        entity_ids = [e.get('name', f'e{i}') for i, e in enumerate(entities)]
    
    # Generate reference set
    rng = np.random.default_rng(seed)
    reference = rng.random((min(500, len(entities)), vectors.shape[1])).astype(np.float32)
    
    try:
        from gpu_scores import batch_score
        
        # Use tiling for large batches
        tiler = TiledBatchProcessor(
            tile_size=tile_size,
            mode='score',
            adaptive=True
        )
        
        # Accumulate results across tiles
        all_novelty = []
        all_redundancy = []
        all_safety = []
        all_overall = []
        tile_times = []
        backend_used = "unknown"
        
        for tile_idx, tile_vectors in tiler.tiles_array(vectors):
            tile_t0 = time.perf_counter()
            
            result = batch_score(
                vectors=tile_vectors,
                reference=reference,
                features=tile_vectors if tile_vectors.shape[1] <= 10 else None,
                seed=seed + tile_idx  # Different seed per tile for diversity
            )
            
            tile_ms = (time.perf_counter() - tile_t0) * 1000
            tile_times.append(tile_ms)
            tiler.adapt_tile_size(tile_ms)
            
            all_novelty.extend(result.novelty.tolist())
            all_redundancy.extend(result.redundancy.tolist())
            all_safety.extend(result.safety.tolist())
            all_overall.extend(result.overall.tolist())
            backend_used = result.backend_used
        
        elapsed = (time.perf_counter() - t0) * 1000
        
        # Record metrics
        metrics = tiler.record_metrics(len(entities), tile_times, backend_used)
        
        # Convert to numpy for threshold checks
        novelty_arr = np.array(all_novelty)
        redundancy_arr = np.array(all_redundancy)
        safety_arr = np.array(all_safety)
        overall_arr = np.array(all_overall)
        
        # Threshold checks
        meets_threshold = (novelty_arr >= 0.7) & (redundancy_arr <= 0.3) & (safety_arr >= 0.8)
        in_grace = (novelty_arr >= 0.5) & (redundancy_arr <= 0.5) & (safety_arr >= 0.6)
        
        # Build individual scores
        scores = []
        for i, eid in enumerate(entity_ids):
            scores.append({
                "id": eid,
                "novelty": float(all_novelty[i]),
                "redundancy": float(all_redundancy[i]),
                "safety": float(all_safety[i]),
                "overall": float(all_overall[i]),
                "meets_thresholds": bool(meets_threshold[i]),
            })
        
        # Aggregate stats
        meets_count = int(np.sum(meets_threshold))
        grace_count = int(np.sum(in_grace))
        
        return {
            "count": len(entities),
            "scores": scores,
            "aggregate": {
                "mean_novelty": float(np.mean(novelty_arr)),
                "mean_redundancy": float(np.mean(redundancy_arr)),
                "mean_safety": float(np.mean(safety_arr)),
                "mean_overall": float(np.mean(overall_arr)),
                "meets_threshold_count": meets_count,
                "in_grace_window_count": grace_count,
                "pass_rate": meets_count / len(entities) if entities else 0,
            },
            "backend": backend_used,
            "elapsed_ms": round(elapsed, 2),
            "seed": seed,
            "tiling": {
                "tile_count": metrics.tile_count,
                "tile_size": metrics.tile_size,
                "max_tile_ms": round(metrics.max_tile_ms, 2),
                "avg_tile_ms": round(metrics.avg_tile_ms, 2),
                "items_per_second": round(metrics.items_per_second, 1),
            }
        }
        
    except ImportError as e:
        logger.warning(f"GPU batch scoring unavailable: {e}")
        elapsed = (time.perf_counter() - t0) * 1000
        
        # CPU fallback with synthetic scores
        rng = np.random.default_rng(seed)
        scores = []
        for eid in entity_ids:
            scores.append({
                "id": eid,
                "novelty": float(rng.uniform(0.5, 1.0)),
                "redundancy": float(rng.uniform(0.0, 0.5)),
                "safety": float(rng.uniform(0.7, 1.0)),
                "overall": float(rng.uniform(0.5, 0.9)),
                "meets_thresholds": bool(rng.random() > 0.5),
            })
        
        return {
            "count": len(entities),
            "scores": scores,
            "backend": "cpu_fallback",
            "elapsed_ms": round(elapsed, 2),
            "seed": seed,
            "warning": "Using synthetic fallback scores"
        }


def mas_gpu_status() -> dict:
    """
    📊 Return GPU infrastructure status.
    
    Includes backend detection, memory info, and capability flags.
    """
    config = get_config()
    caps = get_capabilities()
    
    status = {
        "gpu_available": caps.backend != GPUBackend.NONE,
        "backend": caps.backend.name,
        "device_name": caps.device_name,
        "compute_capability": list(caps.compute_capability) if caps.compute_capability else None,
        "total_memory_gb": round(caps.total_memory_gb, 2),
        "multiprocessors": caps.multiprocessors,
        "max_batch_size": caps.max_batch_size,
        "features": {
            "tensor_cores": caps.has_tensor_cores,
            "fp16": caps.has_fp16,
            "async_copy": caps.has_async_copy,
        },
        "config": {
            "gpu_enabled": config.gpu_enabled,
            "ml_enabled": config.ml_enabled,
            "max_power_percent": config.max_power_percent,
            "target_fps": config.target_fps,
            "seed": config.seed,
            "governance_priority": config.governance_priority,
        },
        "error_count": config._gpu_error_count,
    }
    
    # Add CUDA version if CuPy available
    if caps.backend == GPUBackend.CUPY:
        try:
            import cupy as cp
            status["cuda_version"] = cp.cuda.runtime.runtimeGetVersion()
        except:
            pass
    
    return status


def mas_gpu_hierarchy(
    positions: Optional[list] = None,
    nodes: Optional[list] = None,
    edges: Optional[list] = None,
    iterations: int = 100,
    cooling_rate: float = 0.95,
    seed: Optional[int] = None,
    max_nodes_per_pass: Optional[int] = None
) -> dict:
    """
    🏛️ GPU-accelerated force-directed hierarchy layout with automatic tiling.
    
    Uses progressive refinement for large graphs to prevent TDR timeouts.
    
    Args:
        positions: List of {entity, tier, x, y, z} initial positions
        nodes: Alternative: list of node IDs (positions auto-generated)
        edges: List of (source, target) or (source, target, weight) tuples
        iterations: Number of force iterations
        cooling_rate: Temperature decay rate
        seed: Random seed for reproducibility
        max_nodes_per_pass: Override max nodes per layout pass (default: 2000)
    
    Returns:
        Updated positions after force-directed layout.
    """
    config = get_config()
    seed = seed or config.seed
    
    t0 = time.perf_counter()
    
    # Parse input format
    if positions:
        # Explicit positions format
        node_ids = [p.get('entity', p.get('id', f'n{i}')) for i, p in enumerate(positions)]
        node_tiers = [p.get('tier', 2.0) for p in positions]
        initial_pos = np.array([
            [p.get('x', 0.0), p.get('y', 0.0), p.get('z', 0.0)]
            for p in positions
        ], dtype=np.float32)
    elif nodes:
        # Node list format - generate positions
        node_ids = nodes
        node_tiers = [2.0] * len(nodes)  # Default tier
        initial_pos = None  # Will be generated
    else:
        return {"error": "Either 'positions' or 'nodes' must be provided"}
    
    # Parse edges
    parsed_edges = []
    node_index = {nid: i for i, nid in enumerate(node_ids)}
    
    if edges:
        for edge in edges:
            if len(edge) == 2:
                src, tgt = edge
                weight = 1.0
            else:
                src, tgt, weight = edge[:3]
            
            src_idx = node_index.get(src)
            tgt_idx = node_index.get(tgt)
            
            if src_idx is not None and tgt_idx is not None:
                parsed_edges.append((src_idx, tgt_idx, float(weight)))
    
    # Determine if we need progressive layout
    tiler = TiledBatchProcessor(
        tile_size=max_nodes_per_pass,
        mode='hierarchy',
        adaptive=True
    )
    use_progressive = len(node_ids) > tiler.tile_size
    
    try:
        from gpu_forces import initialize_layout, run_layout, LayoutConfig, LayoutState
        
        pass_times = []
        total_iterations = 0
        converged = False
        total_movement = 0.0
        backend_used = "gpu" if gpu_available() else "cpu"
        
        if use_progressive:
            # Progressive layout: coarse-to-fine passes
            # Start with subset, then refine with full set
            logger.info(f"Using progressive layout for {len(node_ids)} nodes "
                       f"(passes of ~{tiler.tile_size} nodes)")
            
            # Generate initial positions using coarse pass
            rng = np.random.default_rng(seed)
            coarse_count = min(tiler.tile_size, len(node_ids))
            coarse_indices = rng.choice(len(node_ids), coarse_count, replace=False)
            coarse_indices.sort()
            
            # Coarse pass
            pass_t0 = time.perf_counter()
            coarse_node_ids = [node_ids[i] for i in coarse_indices]
            coarse_tiers = [node_tiers[i] for i in coarse_indices]
            
            # Filter edges to coarse nodes
            coarse_node_set = set(coarse_indices)
            coarse_edges = [
                (np.searchsorted(coarse_indices, e[0]),
                 np.searchsorted(coarse_indices, e[1]),
                 e[2])
                for e in parsed_edges
                if e[0] in coarse_node_set and e[1] in coarse_node_set
            ]
            
            state = initialize_layout(
                node_ids=coarse_node_ids,
                node_tiers=coarse_tiers,
                edges=coarse_edges,
                seed=seed
            )
            
            coarse_config = LayoutConfig(
                max_iterations=iterations // 2,
                damping=cooling_rate,
                seed=seed
            )
            
            state = run_layout(
                state=state,
                config=coarse_config,
                node_tiers=np.array(coarse_tiers, dtype=np.float32)
            )
            
            pass_ms = (time.perf_counter() - pass_t0) * 1000
            pass_times.append(pass_ms)
            tiler.adapt_tile_size(pass_ms)
            
            total_iterations += state.iteration
            
            # Interpolate positions for non-coarse nodes
            full_positions = np.zeros((len(node_ids), 3), dtype=np.float32)
            for i, ci in enumerate(coarse_indices):
                full_positions[ci] = state.positions[i]
            
            # Interpolate missing positions from nearest coarse neighbors
            for i in range(len(node_ids)):
                if i not in coarse_node_set:
                    # Find nearest coarse node by tier
                    tier = node_tiers[i]
                    closest_idx = coarse_indices[np.argmin(
                        [abs(node_tiers[ci] - tier) for ci in coarse_indices]
                    )]
                    # Jitter position near that node
                    base_pos = full_positions[closest_idx]
                    jitter = rng.uniform(-20, 20, size=3).astype(np.float32)
                    full_positions[i] = base_pos + jitter
            
            # Refinement pass with all nodes
            pass_t0 = time.perf_counter()
            
            state = initialize_layout(
                node_ids=node_ids,
                node_tiers=node_tiers,
                edges=parsed_edges,
                seed=seed + 1
            )
            state.positions = full_positions
            
            refine_config = LayoutConfig(
                max_iterations=iterations // 2,
                damping=cooling_rate * 0.9,  # Slower cooling for refinement
                seed=seed + 1
            )
            
            state = run_layout(
                state=state,
                config=refine_config,
                node_tiers=np.array(node_tiers, dtype=np.float32)
            )
            
            pass_ms = (time.perf_counter() - pass_t0) * 1000
            pass_times.append(pass_ms)
            
            total_iterations += state.iteration
            converged = state.converged
            total_movement = float(state.total_movement)
            
        else:
            # Single pass for small graphs
            pass_t0 = time.perf_counter()
            
            state = initialize_layout(
                node_ids=node_ids,
                node_tiers=node_tiers,
                edges=parsed_edges,
                seed=seed
            )
            
            if initial_pos is not None:
                state.positions = initial_pos.copy()
            
            layout_config = LayoutConfig(
                max_iterations=iterations,
                damping=cooling_rate,
                seed=seed
            )
            
            state = run_layout(
                state=state,
                config=layout_config,
                node_tiers=np.array(node_tiers, dtype=np.float32)
            )
            
            pass_ms = (time.perf_counter() - pass_t0) * 1000
            pass_times.append(pass_ms)
            
            total_iterations = int(state.iteration)
            converged = bool(state.converged)
            total_movement = float(state.total_movement)
        
        elapsed = (time.perf_counter() - t0) * 1000
        
        # Record tiling metrics
        metrics = tiler.record_metrics(len(node_ids), pass_times, backend_used)
        
        # Build result
        result_positions = {}
        for i, nid in enumerate(node_ids):
            result_positions[nid] = [
                float(state.positions[i, 0]),
                float(state.positions[i, 1]),
                float(state.positions[i, 2])
            ]
        
        return {
            "positions": result_positions,
            "iterations": total_iterations,
            "converged": converged,
            "total_movement": total_movement,
            "node_count": len(node_ids),
            "edge_count": len(parsed_edges),
            "elapsed_ms": round(elapsed, 2),
            "backend": backend_used,
            "seed": seed,
            "progressive": use_progressive,
            "tiling": {
                "pass_count": len(pass_times),
                "max_nodes_per_pass": tiler.tile_size,
                "max_pass_ms": round(max(pass_times), 2) if pass_times else 0.0,
                "avg_pass_ms": round(sum(pass_times) / len(pass_times), 2) if pass_times else 0.0,
            }
        }
        
    except ImportError as e:
        logger.warning(f"GPU forces unavailable: {e}")
        elapsed = (time.perf_counter() - t0) * 1000
        
        # CPU fallback - simple circular layout
        rng = np.random.default_rng(seed)
        result_positions = {}
        
        for i, nid in enumerate(node_ids):
            tier = node_tiers[i] if i < len(node_tiers) else 2.0
            radius = 50.0 * tier
            angle = 2.0 * np.pi * i / len(node_ids)
            result_positions[nid] = [
                float(radius * np.cos(angle)),
                float(radius * np.sin(angle)),
                0.0
            ]
        
        return {
            "positions": result_positions,
            "iterations": iterations,
            "converged": True,
            "node_count": len(node_ids),
            "edge_count": len(parsed_edges) if edges else 0,
            "elapsed_ms": round(elapsed, 2),
            "backend": "cpu_fallback",
            "seed": seed,
            "warning": "Using simple circular layout fallback"
        }
