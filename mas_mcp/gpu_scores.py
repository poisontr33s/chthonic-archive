"""
⚡ GPU-Accelerated Scoring for Novelty, Redundancy, and Safety

Implements batch vector operations for governance scoring with:
- Seeded determinism for reproducible results
- CPU fallback parity
- Tolerance-based comparison for GPU/CPU equivalence

Hardware Target: RTX 4090 Laptop GPU (16GB VRAM, 7424 CUDA cores)
"""

import numpy as np
from typing import Optional, Tuple
from dataclasses import dataclass
import logging

from gpu_config import (
    get_config, get_capabilities, gpu_available, 
    with_gpu_fallback, GPUBackend
)

logger = logging.getLogger("mas.gpu.scores")


@dataclass
class ScoringResult:
    """Results from batch scoring operation."""
    novelty: np.ndarray      # Shape: (N,) - novelty scores [0, 1]
    redundancy: np.ndarray   # Shape: (N,) - redundancy scores [0, 1]
    safety: np.ndarray       # Shape: (N,) - safety scores [0, 1]
    overall: np.ndarray      # Shape: (N,) - weighted overall [0, 1]
    
    # Metadata
    batch_size: int = 0
    compute_time_ms: float = 0.0
    backend_used: str = "cpu"
    seed_used: int = 0
    
    def meets_thresholds(
        self, 
        novelty_min: float = 0.7,
        redundancy_max: float = 0.3,
        safety_min: float = 0.8,
        overall_min: float = 0.6
    ) -> np.ndarray:
        """Return boolean mask of items meeting all thresholds."""
        return (
            (self.novelty >= novelty_min) &
            (self.redundancy <= redundancy_max) &
            (self.safety >= safety_min) &
            (self.overall >= overall_min)
        )
    
    def in_grace_window(
        self,
        novelty_range: Tuple[float, float] = (0.5, 0.7),
        redundancy_range: Tuple[float, float] = (0.3, 0.5)
    ) -> np.ndarray:
        """Return boolean mask of items in grace window (borderline)."""
        novelty_borderline = (self.novelty >= novelty_range[0]) & (self.novelty < novelty_range[1])
        redundancy_borderline = (self.redundancy > redundancy_range[0]) & (self.redundancy <= redundancy_range[1])
        return novelty_borderline | redundancy_borderline


# ============================================================================
# CPU Reference Implementations (authoritative for determinism validation)
# ============================================================================

def _cpu_cosine_similarity_matrix(vectors: np.ndarray, reference: np.ndarray) -> np.ndarray:
    """
    CPU reference: Compute cosine similarity between vectors and reference set.
    
    Args:
        vectors: (N, D) query vectors
        reference: (M, D) reference vectors
    
    Returns:
        (N, M) similarity matrix
    """
    # Normalize
    v_norm = vectors / (np.linalg.norm(vectors, axis=1, keepdims=True) + 1e-8)
    r_norm = reference / (np.linalg.norm(reference, axis=1, keepdims=True) + 1e-8)
    
    # Dot product
    return v_norm @ r_norm.T


def _cpu_novelty_score(vectors: np.ndarray, reference: np.ndarray, seed: int) -> np.ndarray:
    """
    CPU reference: Novelty = 1 - max_similarity to reference set.
    
    Novel items have low similarity to existing corpus.
    """
    rng = np.random.default_rng(seed)
    
    if reference.shape[0] == 0:
        # No reference corpus = everything is novel
        return np.ones(vectors.shape[0], dtype=np.float32)
    
    sim_matrix = _cpu_cosine_similarity_matrix(vectors, reference)
    max_sim = np.max(sim_matrix, axis=1)
    
    # Add tiny seeded noise for tie-breaking determinism
    noise = rng.uniform(-1e-6, 1e-6, size=max_sim.shape).astype(np.float32)
    
    return np.clip(1.0 - max_sim + noise, 0.0, 1.0)


def _cpu_redundancy_score(vectors: np.ndarray, reference: np.ndarray, seed: int) -> np.ndarray:
    """
    CPU reference: Redundancy = average similarity to top-k most similar items.
    
    Redundant items are very similar to multiple existing items.
    """
    rng = np.random.default_rng(seed)
    k = min(5, max(1, reference.shape[0]))
    
    if reference.shape[0] == 0:
        return np.zeros(vectors.shape[0], dtype=np.float32)
    
    sim_matrix = _cpu_cosine_similarity_matrix(vectors, reference)
    
    # Top-k average similarity
    top_k_indices = np.argsort(sim_matrix, axis=1)[:, -k:]
    top_k_sims = np.take_along_axis(sim_matrix, top_k_indices, axis=1)
    redundancy = np.mean(top_k_sims, axis=1)
    
    # Seeded noise for determinism
    noise = rng.uniform(-1e-6, 1e-6, size=redundancy.shape).astype(np.float32)
    
    return np.clip(redundancy + noise, 0.0, 1.0)


def _cpu_safety_score(
    vectors: np.ndarray, 
    features: Optional[np.ndarray], 
    seed: int
) -> np.ndarray:
    """
    CPU reference: Safety based on feature analysis.
    
    Features expected: [has_exec, has_eval, has_subprocess, has_file_write, ...]
    High feature values = lower safety.
    
    If no features provided, returns neutral 0.5 (unknown safety).
    """
    rng = np.random.default_rng(seed)
    n = vectors.shape[0]
    
    if features is None:
        # Unknown safety = neutral score
        return np.full(n, 0.5, dtype=np.float32)
    
    # Feature weights (higher = more dangerous)
    danger_weights = np.array([
        1.0,   # has_exec
        0.9,   # has_eval
        0.7,   # has_subprocess
        0.6,   # has_file_write
        0.5,   # has_dynamic_import
        0.3,   # has_network
    ], dtype=np.float32)
    
    # Pad or truncate weights
    if features.shape[1] < len(danger_weights):
        danger_weights = danger_weights[:features.shape[1]]
    elif features.shape[1] > len(danger_weights):
        danger_weights = np.pad(danger_weights, (0, features.shape[1] - len(danger_weights)), constant_values=0.2)
    
    # Danger score = weighted sum of features
    danger = features @ danger_weights
    danger_normalized = danger / (np.sum(danger_weights) + 1e-8)
    
    # Safety = 1 - danger
    safety = 1.0 - danger_normalized
    
    # Seeded noise
    noise = rng.uniform(-1e-6, 1e-6, size=safety.shape).astype(np.float32)
    
    return np.clip(safety + noise, 0.0, 1.0)


def cpu_batch_score(
    vectors: np.ndarray,
    reference: np.ndarray,
    features: Optional[np.ndarray] = None,
    seed: Optional[int] = None,
    weights: Tuple[float, float, float] = (0.4, 0.3, 0.3)
) -> ScoringResult:
    """
    CPU reference implementation for batch scoring.
    
    Args:
        vectors: (N, D) vectors to score
        reference: (M, D) reference corpus vectors
        features: (N, F) optional safety feature matrix
        seed: Random seed for determinism
        weights: (novelty_weight, redundancy_weight, safety_weight) for overall
    
    Returns:
        ScoringResult with all scores
    """
    import time
    start = time.perf_counter()
    
    config = get_config()
    seed = seed or config.seed
    
    novelty = _cpu_novelty_score(vectors, reference, seed)
    redundancy = _cpu_redundancy_score(vectors, reference, seed + 1)
    safety = _cpu_safety_score(vectors, features, seed + 2)
    
    # Overall = weighted combination (redundancy inverted since low is good)
    w_nov, w_red, w_saf = weights
    overall = (
        w_nov * novelty + 
        w_red * (1.0 - redundancy) +  # Invert redundancy
        w_saf * safety
    ) / (w_nov + w_red + w_saf)
    
    elapsed_ms = (time.perf_counter() - start) * 1000
    
    return ScoringResult(
        novelty=novelty,
        redundancy=redundancy,
        safety=safety,
        overall=overall,
        batch_size=vectors.shape[0],
        compute_time_ms=elapsed_ms,
        backend_used="cpu",
        seed_used=seed
    )


# ============================================================================
# GPU Implementations (CuPy/Numba)
# ============================================================================

def _get_cupy():
    """Lazy import CuPy with Windows CUDA DLL path fix."""
    try:
        import os
        import sys
        
        # Windows requires CUDA 12.x DLLs in path for cupy-cuda12x
        if sys.platform == 'win32':
            cuda_bin = r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.6\bin'
            if os.path.isdir(cuda_bin):
                os.add_dll_directory(cuda_bin)
        
        import cupy as cp
        return cp
    except ImportError:
        return None
    except OSError as e:
        # DLL loading failed
        logger.warning(f"CuPy DLL loading failed: {e}")
        return None


def gpu_batch_score(
    vectors: np.ndarray,
    reference: np.ndarray,
    features: Optional[np.ndarray] = None,
    seed: Optional[int] = None,
    weights: Tuple[float, float, float] = (0.4, 0.3, 0.3)
) -> ScoringResult:
    """
    GPU-accelerated batch scoring using CuPy.
    
    Maintains determinism parity with CPU implementation.
    """
    import time
    start = time.perf_counter()
    
    cp = _get_cupy()
    if cp is None:
        logger.warning("CuPy not available, falling back to CPU")
        return cpu_batch_score(vectors, reference, features, seed, weights)
    
    config = get_config()
    seed = seed or config.seed
    
    try:
        # Transfer to GPU
        v_gpu = cp.asarray(vectors, dtype=cp.float32)
        r_gpu = cp.asarray(reference, dtype=cp.float32) if reference.shape[0] > 0 else cp.empty((0, vectors.shape[1]), dtype=cp.float32)
        
        # Normalize
        v_norm = v_gpu / (cp.linalg.norm(v_gpu, axis=1, keepdims=True) + 1e-8)
        
        if r_gpu.shape[0] > 0:
            r_norm = r_gpu / (cp.linalg.norm(r_gpu, axis=1, keepdims=True) + 1e-8)
            
            # Similarity matrix
            sim_matrix = v_norm @ r_norm.T
            
            # Novelty
            max_sim = cp.max(sim_matrix, axis=1)
            rng = cp.random.default_rng(seed)
            noise = rng.uniform(-1e-6, 1e-6, size=max_sim.shape, dtype=cp.float32)
            novelty = cp.clip(1.0 - max_sim + noise, 0.0, 1.0)
            
            # Redundancy (top-k average)
            k = min(5, max(1, r_gpu.shape[0]))
            top_k_indices = cp.argsort(sim_matrix, axis=1)[:, -k:]
            top_k_sims = cp.take_along_axis(sim_matrix, top_k_indices, axis=1)
            redundancy_raw = cp.mean(top_k_sims, axis=1)
            rng2 = cp.random.default_rng(seed + 1)
            noise2 = rng2.uniform(-1e-6, 1e-6, size=redundancy_raw.shape, dtype=cp.float32)
            redundancy = cp.clip(redundancy_raw + noise2, 0.0, 1.0)
        else:
            # No reference = fully novel, no redundancy
            novelty = cp.ones(v_gpu.shape[0], dtype=cp.float32)
            redundancy = cp.zeros(v_gpu.shape[0], dtype=cp.float32)
        
        # Safety
        if features is not None:
            f_gpu = cp.asarray(features, dtype=cp.float32)
            danger_weights = cp.array([1.0, 0.9, 0.7, 0.6, 0.5, 0.3], dtype=cp.float32)
            if f_gpu.shape[1] < len(danger_weights):
                danger_weights = danger_weights[:f_gpu.shape[1]]
            elif f_gpu.shape[1] > len(danger_weights):
                danger_weights = cp.pad(danger_weights, (0, f_gpu.shape[1] - len(danger_weights)), constant_values=0.2)
            
            danger = f_gpu @ danger_weights
            danger_normalized = danger / (cp.sum(danger_weights) + 1e-8)
            safety = 1.0 - danger_normalized
            
            rng3 = cp.random.default_rng(seed + 2)
            noise3 = rng3.uniform(-1e-6, 1e-6, size=safety.shape, dtype=cp.float32)
            safety = cp.clip(safety + noise3, 0.0, 1.0)
        else:
            safety = cp.full(v_gpu.shape[0], 0.5, dtype=cp.float32)
        
        # Overall
        w_nov, w_red, w_saf = weights
        overall = (
            w_nov * novelty +
            w_red * (1.0 - redundancy) +
            w_saf * safety
        ) / (w_nov + w_red + w_saf)
        
        # Transfer back to CPU
        result = ScoringResult(
            novelty=cp.asnumpy(novelty),
            redundancy=cp.asnumpy(redundancy),
            safety=cp.asnumpy(safety),
            overall=cp.asnumpy(overall),
            batch_size=vectors.shape[0],
            compute_time_ms=(time.perf_counter() - start) * 1000,
            backend_used="cupy",
            seed_used=seed
        )
        
        config.reset_errors()
        return result
        
    except Exception as e:
        logger.error(f"GPU scoring failed: {e}")
        config.increment_error()
        if config.auto_fallback:
            return cpu_batch_score(vectors, reference, features, seed, weights)
        raise


def batch_score(
    vectors: np.ndarray,
    reference: np.ndarray,
    features: Optional[np.ndarray] = None,
    seed: Optional[int] = None,
    weights: Tuple[float, float, float] = (0.4, 0.3, 0.3)
) -> ScoringResult:
    """
    Unified scoring interface - uses GPU if available, CPU otherwise.
    """
    if gpu_available():
        return gpu_batch_score(vectors, reference, features, seed, weights)
    return cpu_batch_score(vectors, reference, features, seed, weights)


# ============================================================================
# Validation and Testing
# ============================================================================

def validate_gpu_cpu_parity(
    n_vectors: int = 1000,
    dim: int = 256,
    n_reference: int = 500,
    seed: int = 42,
    tolerance: float = 1e-4
) -> dict:
    """
    Validate that GPU and CPU implementations produce equivalent results.
    
    Returns validation report with pass/fail and max differences.
    """
    rng = np.random.default_rng(seed)
    
    vectors = rng.random((n_vectors, dim)).astype(np.float32)
    reference = rng.random((n_reference, dim)).astype(np.float32)
    features = rng.random((n_vectors, 6)).astype(np.float32)
    
    cpu_result = cpu_batch_score(vectors, reference, features, seed)
    
    if not gpu_available():
        return {
            "status": "skipped",
            "reason": "GPU not available",
            "cpu_time_ms": cpu_result.compute_time_ms
        }
    
    gpu_result = gpu_batch_score(vectors, reference, features, seed)
    
    # Compare
    novelty_diff = np.max(np.abs(cpu_result.novelty - gpu_result.novelty))
    redundancy_diff = np.max(np.abs(cpu_result.redundancy - gpu_result.redundancy))
    safety_diff = np.max(np.abs(cpu_result.safety - gpu_result.safety))
    overall_diff = np.max(np.abs(cpu_result.overall - gpu_result.overall))
    
    max_diff = max(novelty_diff, redundancy_diff, safety_diff, overall_diff)
    passed = max_diff <= tolerance
    
    return {
        "status": "passed" if passed else "failed",
        "tolerance": tolerance,
        "max_difference": float(max_diff),
        "differences": {
            "novelty": float(novelty_diff),
            "redundancy": float(redundancy_diff),
            "safety": float(safety_diff),
            "overall": float(overall_diff)
        },
        "timing": {
            "cpu_ms": cpu_result.compute_time_ms,
            "gpu_ms": gpu_result.compute_time_ms,
            "speedup": cpu_result.compute_time_ms / max(gpu_result.compute_time_ms, 0.001)
        },
        "batch_size": n_vectors,
        "dimension": dim
    }
