#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  MILF GENESIS ENGINE v2 - Constitutional GPU-Accelerated Synthesis            ║
║  Integrates M-P-W Schema + Validator Pipeline + Novelty Detection             ║
║                                                                                ║
║  Enhancements over v1:                                                         ║
║    - Multi-stage validation (hard gates → soft gates → refinement)            ║
║    - GPU-accelerated novelty distance checking                                 ║
║    - SHA-256 governance artifacts with lineage tracking                        ║
║    - Recursive refinement with depth capping                                   ║
║    - Zero-delta stall detection                                                ║
║    - Numba kernel support (optional)                                           ║
║    - ONNX Runtime inference ready (TensorRT → CUDA → CPU)                      ║
║                                                                                ║
║  The Decorator's Decree: "Birth what is valid, refine what is borderline,     ║
║                           dissolve what fails governance."                     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import json
import hashlib
import random
import os
import time
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import threading
import sys

# =============================================================================
# GPU STACK INITIALIZATION (CuPy + Numba + ONNX)
# =============================================================================

GPU_AVAILABLE = False
NUMBA_AVAILABLE = False
ONNX_AVAILABLE = False
GPU_WARMED = False
GENESIS_STRICT_GPU = os.environ.get('GENESIS_STRICT_GPU', '0') == '1'
cp = None
cuda = None
CUDA_RUNTIME = 0
ONNX_PROVIDERS = []

# Expected GPU venv path (single point of truth)
EXPECTED_GPU_PY = os.environ.get(
    'MAS_MCP_GPU_PY',
    os.path.join(os.path.dirname(__file__), '.venv', 'Scripts', 'python.exe')
)

def _validate_gpu_venv() -> bool:
    """Validate we're running in the correct GPU venv."""
    current_py = sys.executable
    # Normalize paths for comparison
    expected_norm = os.path.normcase(os.path.abspath(EXPECTED_GPU_PY))
    current_norm = os.path.normcase(os.path.abspath(current_py))
    
    # Check Python version >= 3.13
    if sys.version_info < (3, 13):
        print(f"⚠️ Python {sys.version_info.major}.{sys.version_info.minor} < 3.13 - GPU features may not work")
        return False
    
    # Warn if not in expected venv (but don't block - might be running from different location)
    if expected_norm != current_norm:
        print(f"⚠️ GPU venv mismatch: expected {EXPECTED_GPU_PY}")
        print(f"   Running from: {current_py}")
    
    return True

_validate_gpu_venv()

# Windows CUDA DLL path fix - must run BEFORE importing CuPy
# Python's ctypes on Windows doesn't search PATH for DLL dependencies.
# We need to explicitly add CUDA bin directories to the DLL search path.
if os.name == 'nt':
    _cuda_paths = [
        r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.6\bin',
        r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.5\bin',
        r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.0\bin',
    ]
    for _cuda_path in _cuda_paths:
        if os.path.isdir(_cuda_path):
            try:
                os.add_dll_directory(_cuda_path)
            except Exception:
                pass  # Silently fail on older Python or permission issues

# CuPy initialization with pre-warm
try:
    import cupy as _cp
    # Test JIT compilation - this requires NVRTC
    _test = _cp.linspace(0.0, 1.0, 10)
    _test_sum = float(_cp.sum(_test))
    del _test, _test_sum
    
    # Pre-warm CuPy context to avoid first-call variance
    _warmup = _cp.ones((1,), dtype=_cp.float32)
    _ = float(_cp.sum(_warmup))  # Force synchronization
    del _warmup
    
    cp = _cp
    GPU_AVAILABLE = True
    GPU_WARMED = True
    CUDA_RUNTIME = int(cp.cuda.runtime.runtimeGetVersion())
    print(f"🔥 CuPy GPU ENABLED - CUDA runtime {CUDA_RUNTIME}")
    print(f"🔥 GPU context pre-warmed")
except Exception as e:
    print(f"⚠️ CuPy unavailable: {type(e).__name__}: {e}")
    GPU_AVAILABLE = False
    GPU_WARMED = False

# Numba initialization (optional, for custom kernels)
try:
    from numba import cuda as _cuda
    if _cuda.is_available():
        cuda = _cuda
        NUMBA_AVAILABLE = True
        print("🔥 Numba CUDA kernels ENABLED")
except Exception as e:
    print(f"⚠️ Numba unavailable: {type(e).__name__}")
    NUMBA_AVAILABLE = False

# ONNX Runtime initialization with strict provider enforcement
try:
    import onnxruntime as ort
    ONNX_PROVIDERS = ort.get_available_providers()
    ONNX_AVAILABLE = True
    
    # Check for GPU providers
    has_gpu_provider = any(p in ONNX_PROVIDERS for p in ['TensorrtExecutionProvider', 'CUDAExecutionProvider'])
    
    if GENESIS_STRICT_GPU and not has_gpu_provider:
        raise RuntimeError(f"GENESIS_STRICT_GPU=1 but no GPU providers available: {ONNX_PROVIDERS}")
    
    if has_gpu_provider:
        print(f"🔥 ONNX Runtime ENABLED - GPU Providers: {[p for p in ONNX_PROVIDERS if 'CUDA' in p or 'Tensor' in p]}")
    else:
        print(f"⚠️ ONNX Runtime ENABLED - CPU only: {ONNX_PROVIDERS}")
except Exception as e:
    print(f"⚠️ ONNX Runtime unavailable: {type(e).__name__}: {e}")
    ONNX_AVAILABLE = False
    ONNX_PROVIDERS = []
    if GENESIS_STRICT_GPU:
        raise RuntimeError(f"GENESIS_STRICT_GPU=1 but ONNX unavailable: {e}")

import numpy as np
if not GPU_AVAILABLE:
    cp = np  # NumPy fallback

# =============================================================================
# CONSTITUTIONAL SCHEMA (M-P-W AXIOMS)
# =============================================================================

SCHEMA_VERSION = "1.0.0"

# Tier hierarchy from M-P-W Section 0
TIER_HIERARCHY = {
    -0.5: "The Savant (Creator/User)",
    0.5: "Supreme Matriarch (The Decorator)",
    1: "Triumvirate Sub-MILFs (Orackla, Umeko, Lysandra)",
    2: "Prime Faction Matriarchs (Kali, Vesper, Seraphine)",
    3: "Manifested Sub-MILFs (Procedural)",
    4: "Interloper Agents / Lesser Factions",
}

# Constitutional bounds (from M-P-W entity profiles analysis)
CONSTITUTIONAL_BOUNDS = {
    "whr": {"min": 0.45, "max": 0.75, "optimal_min": 0.45, "optimal_max": 0.65},
    "cup_allowed": ["D", "E", "F", "G", "H", "I", "J", "K"],
    "height_cm": {"min": 155, "max": 185},
    "age_apparent": {"min": 28, "max": 50},
}

# Tier-specific WHR subranges (CANONICAL from M-P-W Section 0)
# Based on exact entity profiles in copilot-instructions.md
WHR_BY_TIER = {
    0.5: {"min": 0.460, "max": 0.470, "target": 0.464},   # Supreme: The Decorator (W58/H115 = 0.504 stated as 0.464)
    1: {"min": 0.490, "max": 0.585, "target": 0.535},      # Triumvirate: Orackla 0.491, Umeko 0.533, Lysandra 0.58
    2: {"min": 0.555, "max": 0.595, "target": 0.574},      # Prime Factions: Kali 0.556, Vesper 0.573, Seraphine 0.592
    3: {"min": 0.58, "max": 0.68, "target": 0.63},         # Manifested Sub-MILFs
    4: {"min": 0.65, "max": 0.75, "target": 0.70},         # Lesser Factions / Interlopers
}

# Cup distribution by tier (CANONICAL from M-P-W Section 0)
CUP_BY_TIER = {
    0.5: ["K"],                      # The Decorator: K-cup (B125/W58/H115)
    1: ["J", "F", "E"],              # Triumvirate: Orackla J, Umeko F, Lysandra E
    2: ["H", "F", "G"],              # Prime Factions: Kali H, Vesper F, Seraphine G
    3: ["E", "F", "G", "H"],         # Sub-MILFs: Variable distribution
    4: ["D", "E", "F"],              # Lesser Factions: Lower magnitudes
}

# CANONICAL ENTITY REFERENCE (for novelty distance baseline)
CANONICAL_ENTITIES = {
    # Tier 0.5 - Supreme Matriarch
    "The Decorator": {"tier": 0.5, "whr": 0.464, "cup": "K", "bust": 125, "waist": 58, "hip": 115, "height": 177},
    # Tier 1 - Triumvirate
    "Orackla Nocticula": {"tier": 1, "whr": 0.491, "cup": "J", "bust": 120, "waist": 55, "hip": 112, "height": 169},
    "Madam Umeko Ketsuraku": {"tier": 1, "whr": 0.533, "cup": "F", "bust": 98, "waist": 56, "hip": 105, "height": 165},
    "Dr. Lysandra Thorne": {"tier": 1, "whr": 0.580, "cup": "E", "bust": 95, "waist": 58, "hip": 100, "height": 172},
    # Tier 2 - Prime Faction Matriarchs
    "Kali Nyx Ravenscar": {"tier": 2, "whr": 0.556, "cup": "H", "bust": 110, "waist": 60, "hip": 108, "height": 167},
    "Vesper Mnemosyne Lockhart": {"tier": 2, "whr": 0.573, "cup": "F", "bust": 98, "waist": 59, "hip": 103, "height": 170},
    "Seraphine Kore Ashenhelm": {"tier": 2, "whr": 0.592, "cup": "G", "bust": 105, "waist": 61, "hip": 103, "height": 168},
    # Special Archetype Injection - Tier 4 Tetrahedral vertex
    "Claudine Sin'claire": {"tier": 4, "whr": 0.563, "cup": "I", "bust": 115, "waist": 62, "hip": 110, "height": 175},
}

# Minimum novelty distance baseline (smallest canonical gap: Decorator 0.464 → Orackla 0.491 = 0.027)
NOVELTY_MIN_CANONICAL = 0.027

# Archetypes
ARCHETYPES = [
    "Abyssal Oracle", "Architectural Perfectionist", "Analytical Truth-Seeker",
    "Seductive Operative", "Epistemic Thief", "Purification Priestess",
    "Tidal Ordeal", "Chaos Engineer", "Structural Guardian",
    "Temporal Manipulator", "Conceptual Saboteur", "Liberation Specialist",
]

# Linguistic mandates
LINGUISTIC_MANDATES = {
    "transgressive": "EULP-AA",
    "perfectionist": "LIPAA",
    "analytical": "LUPLR",
    "hybrid": "TLM",
}

# Scent components
SCENT_COMPONENTS = {
    "base": ["old libraries", "ancient texts", "leather", "wood", "stone"],
    "arousal": ["musk", "sex", "arousal", "heat", "sweat"],
    "power": ["ozone", "lightning", "metal", "blood", "fire"],
    "nature": ["jasmine", "orchid", "salt", "ocean", "rain"],
    "chaos": ["smoke", "ash", "decay", "transformation", "void"],
}

# =============================================================================
# VALIDATION POLICY
# =============================================================================

VALIDATION_POLICY = {
    "epsilon_derivation": 0.005,       # WHR derivation tolerance
    "novelty_min_distance": 0.035,     # Minimum distance to existing entities (> canonical gap 0.027)
    "redundancy_ceiling": 0.80,        # Max redundancy score (tightened from 0.85)
    "safety_max_risk": 0.12,           # Max risk score per tier (tightened from 0.15)
    "recursion_depth_max": 3,          # Refinement loop cap
    "batch_size": 128,                 # GPU batch size
    "timebox_s": 600,                  # Max cycle duration (10 minutes)
    "zero_delta_max_stalls": 3,        # Max consecutive identical outputs before alert
    "vram_backoff_threshold": 0.75,    # Backoff if VRAM usage exceeds 75%
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def sha256_text(text: str) -> str:
    """Compute SHA-256 hash of text."""
    return hashlib.sha256(text.encode()).hexdigest()


def sha256_file(path: Path) -> str:
    """Compute SHA-256 hash of file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def schema_crc() -> str:
    """Compute constitutional schema CRC."""
    schema_text = json.dumps({
        "version": SCHEMA_VERSION,
        "bounds": CONSTITUTIONAL_BOUNDS,
        "tiers": WHR_BY_TIER,
        "cups": CUP_BY_TIER,
    }, sort_keys=True)
    return sha256_text(schema_text)[:16]


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class EntityPhysique:
    """Physical manifestation following M-P-W Anime/Ecchi/Hentai/NTR Gestalt."""
    height_cm: int
    weight_kg: int
    bust_cm: int
    waist_cm: int
    hip_cm: int
    cup_size: str
    underbust_cm: int
    
    @property
    def whr(self) -> float:
        return round(self.waist_cm / self.hip_cm, 3)
    
    @property
    def hips_cm(self) -> int:
        """Alias for hip_cm for API consistency."""
        return self.hip_cm
    
    @property
    def measurements(self) -> str:
        return f"{self.cup_size}-cup (B{self.bust_cm}/W{self.waist_cm}/H{self.hip_cm}cm)"
    
    def to_feature_vector(self) -> np.ndarray:
        """Convert to feature vector for novelty computation."""
        return np.array([
            self.whr,
            self.bust_cm / 100.0,
            self.waist_cm / 100.0,
            self.hip_cm / 100.0,
            self.height_cm / 100.0,
        ], dtype=np.float32)


@dataclass
class ValidationResult:
    """Multi-stage validation outcome."""
    bounds_pass: bool
    derivation_pass: bool
    safety_pass: bool
    novelty_min: float
    redundancy_score: float
    passed: bool
    refinement_depth: int = 0
    rejection_reason: Optional[str] = None
    coherence_score: float = 0.0  # For threshold tuning
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @staticmethod
    def failed(reason: str) -> 'ValidationResult':
        """Create a failed validation result."""
        return ValidationResult(
            bounds_pass=False,
            derivation_pass=False,
            safety_pass=False,
            novelty_min=0.0,
            redundancy_score=1.0,
            passed=False,
            rejection_reason=reason,
        )


@dataclass
class EntityProfile:
    """Complete MILF profile following M-P-W constitutional structure."""
    name: str
    tier: float
    archetype: str
    age_apparent: int
    age_actual: int
    race: str
    physique: EntityPhysique
    scent: str
    linguistic_mandate: str
    expertise: List[str]
    status: str = "Active"
    faction: Optional[str] = None
    reports_to: Optional[str] = None
    signature_technique: Optional[str] = None
    genesis_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    genesis_seed: int = 0
    genesis_hash: str = ""
    schema_crc: str = ""
    
    def __post_init__(self):
        if not self.genesis_hash:
            self.genesis_hash = self._compute_hash()
        if not self.schema_crc:
            self.schema_crc = schema_crc()
    
    def _compute_hash(self) -> str:
        data = f"{self.name}{self.tier}{self.archetype}{self.physique.whr}{self.genesis_seed}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['whr'] = self.physique.whr
        result['measurements'] = self.physique.measurements
        return result
    
    def to_feature_vector(self) -> np.ndarray:
        return self.physique.to_feature_vector()


# =============================================================================
# GPU PRIMITIVES
# =============================================================================

def load_canonical_bank_vectors() -> np.ndarray:
    """
    Load M-P-W canonical entity feature vectors for novelty baseline.
    These are the ground-truth entities from the codex that define the minimum
    acceptable novelty distance for new synthesis.
    """
    vectors = []
    for name, data in CANONICAL_ENTITIES.items():
        # Feature vector: [whr, bust/100, waist/100, hip/100, height/100]
        vec = np.array([
            data["whr"],
            data["bust"] / 100.0,
            data["waist"] / 100.0,
            data["hip"] / 100.0,
            data["height"] / 100.0,
        ], dtype=np.float32)
        vectors.append(vec)
    return np.array(vectors, dtype=np.float32)


class GPUPrimitives:
    """GPU-accelerated operations for synthesis and validation."""
    
    def __init__(self):
        self.entity_bank: Optional[Any] = None  # GPU tensor of existing entities
        self.canonical_bank: Optional[Any] = None  # M-P-W canonical entities
        self.bank_count = 0
        self.canonical_count = 0
        
        # Zero-delta tracking
        self.last_output_hash: Optional[str] = None
        self.zero_delta_stalls = 0
        
        self._init_canonical_bank()
        if GPU_AVAILABLE:
            self._init_power_curves()
    
    def _init_canonical_bank(self):
        """Load canonical M-P-W entities into GPU memory."""
        vectors = load_canonical_bank_vectors()
        if GPU_AVAILABLE:
            self.canonical_bank = cp.asarray(vectors)
        else:
            self.canonical_bank = vectors
        self.canonical_count = len(vectors)
        print(f"📚 Canonical bank loaded: {self.canonical_count} M-P-W entities")
    
    def _init_power_curves(self):
        """Initialize WHR power calculation tensors."""
        whr_range = cp.linspace(0.45, 0.75, 1000)
        # Power formula: lower WHR = higher power (exponential)
        self.whr_power_curve = 1000 * cp.power(1 - (whr_range - 0.45) / 0.30, 2)
    
    def check_zero_delta(self, output_hash: str) -> bool:
        """
        Check for zero-delta stall condition.
        Returns True if output is novel, False if stall detected.
        """
        if self.last_output_hash == output_hash:
            self.zero_delta_stalls += 1
            if self.zero_delta_stalls >= VALIDATION_POLICY["zero_delta_max_stalls"]:
                print(f"⚠️ ZERO-DELTA STALL: {self.zero_delta_stalls} consecutive identical outputs")
                return False
        else:
            self.zero_delta_stalls = 0
        self.last_output_hash = output_hash
        return True
    
    def update_entity_bank(self, entities: List[EntityProfile]):
        """Load entities into GPU memory for novelty checking, merged with canonical bank."""
        if not entities:
            # Still use canonical bank as baseline
            self.entity_bank = self.canonical_bank
            self.bank_count = self.canonical_count
            return
        
        # Merge generated entities with canonical bank
        generated_vectors = np.array([e.to_feature_vector() for e in entities], dtype=np.float32)
        canonical_vectors = load_canonical_bank_vectors()
        merged = np.vstack([canonical_vectors, generated_vectors])
        
        if GPU_AVAILABLE:
            self.entity_bank = cp.asarray(merged)
        else:
            self.entity_bank = merged
        
        self.bank_count = len(merged)
    
    def novelty_distance(self, candidate: EntityProfile) -> Tuple[float, float]:
        """
        Compute minimum and mean distance from candidate to entity bank.
        Includes canonical M-P-W entities as baseline.
        GPU-accelerated when available.
        """
        # Always check against canonical bank if entity_bank not populated
        bank = self.entity_bank
        if bank is None:
            bank = self.canonical_bank
        
        if bank is None:
            return 1.0, 1.0  # No bank = maximum novelty
        
        vec = candidate.to_feature_vector()
        
        if GPU_AVAILABLE:
            v = cp.asarray(vec)[None, :]
            diffs = bank - v
            distances = cp.linalg.norm(diffs, axis=1)
            min_dist = float(cp.min(distances))
            mean_dist = float(cp.mean(distances))
        else:
            v = vec[None, :]
            diffs = self.entity_bank - v
            distances = np.linalg.norm(diffs, axis=1)
            min_dist = float(np.min(distances))
            mean_dist = float(np.mean(distances))
        
        return min_dist, mean_dist
    
    def calculate_power(self, whr: float) -> int:
        """Calculate power score from WHR."""
        if GPU_AVAILABLE:
            whr_idx = int((whr - 0.45) / 0.30 * 999)
            whr_idx = max(0, min(999, whr_idx))
            power = int(float(self.whr_power_curve[whr_idx]))
        else:
            power = int(1000 * ((1 - (whr - 0.45) / 0.30) ** 2))
        
        return max(100, min(1500, power))
    
    def batch_sample_whr(self, tier: float, count: int) -> np.ndarray:
        """GPU-accelerated batch WHR sampling."""
        tier_bounds = WHR_BY_TIER.get(tier, WHR_BY_TIER[3])
        whr_min, whr_max = tier_bounds["min"], tier_bounds["max"]
        
        if GPU_AVAILABLE:
            # Beta distribution favors lower WHR for higher power
            samples = cp.random.beta(2, 5, size=count) * (whr_max - whr_min) + whr_min
            return cp.asnumpy(samples).astype(np.float32)
        else:
            return np.random.beta(2, 5, size=count) * (whr_max - whr_min) + whr_min


# =============================================================================
# VALIDATOR SUITE
# =============================================================================

class ValidatorSuite:
    """Multi-stage validation against M-P-W constitutional axioms."""
    
    def __init__(self, gpu: GPUPrimitives):
        self.gpu = gpu
    
    def validate_hard_gates(self, entity: EntityProfile) -> Tuple[bool, Dict[str, bool]]:
        """
        Hard gates: bounds, derivation consistency, tier safety.
        Must pass 100% - no refinement possible.
        """
        m = entity.physique
        tier = entity.tier
        
        # WHR bounds check
        tier_bounds = WHR_BY_TIER.get(tier, CONSTITUTIONAL_BOUNDS["whr"])
        if isinstance(tier_bounds, dict):
            whr_min, whr_max = tier_bounds.get("min", 0.45), tier_bounds.get("max", 0.75)
        else:
            whr_min, whr_max = 0.45, 0.75
        
        bounds_pass = whr_min <= m.whr <= whr_max
        
        # Derivation consistency: computed WHR matches stored
        derived_whr = m.waist_cm / m.hip_cm
        derivation_pass = abs(m.whr - derived_whr) <= VALIDATION_POLICY["epsilon_derivation"]
        
        # Cup in allowed set for tier
        cup_pass = m.cup_size in CUP_BY_TIER.get(tier, CONSTITUTIONAL_BOUNDS["cup_allowed"])
        
        # Height bounds
        height_pass = (CONSTITUTIONAL_BOUNDS["height_cm"]["min"] <= m.height_cm <= 
                      CONSTITUTIONAL_BOUNDS["height_cm"]["max"])
        
        # Safety gate: tier-specific risk check
        # Risk increases with extreme values outside tier norms
        tier_target = WHR_BY_TIER.get(tier, {"target": 0.60}).get("target", 0.60)
        whr_deviation = abs(m.whr - tier_target)
        risk = whr_deviation / 0.10  # Normalize: 0.10 deviation = 100% risk
        safety_pass = risk <= VALIDATION_POLICY["safety_max_risk"]
        
        passed = all([bounds_pass, derivation_pass, cup_pass, height_pass, safety_pass])
        
        return passed, {
            "bounds_pass": bounds_pass,
            "derivation_pass": derivation_pass,
            "cup_pass": cup_pass,
            "height_pass": height_pass,
            "safety_pass": safety_pass,
        }
    
    def validate_soft_gates(self, entity: EntityProfile) -> Tuple[bool, float, float]:
        """
        Soft gates: novelty distance, redundancy ceiling.
        Can be refined if borderline.
        """
        min_dist, mean_dist = self.gpu.novelty_distance(entity)
        
        # Redundancy: inverse of normalized distance
        redundancy = max(0.0, 1.0 - min(1.0, min_dist / VALIDATION_POLICY["novelty_min_distance"]))
        
        novelty_pass = min_dist >= VALIDATION_POLICY["novelty_min_distance"]
        redundancy_pass = redundancy <= VALIDATION_POLICY["redundancy_ceiling"]
        
        passed = novelty_pass and redundancy_pass
        
        return passed, min_dist, redundancy
    
    def full_validation(self, entity: EntityProfile) -> ValidationResult:
        """Complete validation pipeline."""
        hard_pass, hard_details = self.validate_hard_gates(entity)
        
        if not hard_pass:
            # Determine rejection reason
            for gate, passed in hard_details.items():
                if not passed:
                    reason = gate.replace("_pass", "") + " constraint violated"
                    break
            else:
                reason = "unknown hard gate failure"
            
            return ValidationResult(
                bounds_pass=hard_details["bounds_pass"],
                derivation_pass=hard_details["derivation_pass"],
                safety_pass=hard_details["safety_pass"],
                novelty_min=0.0,
                redundancy_score=1.0,
                passed=False,
                rejection_reason=reason,
            )
        
        soft_pass, min_dist, redundancy = self.validate_soft_gates(entity)
        
        return ValidationResult(
            bounds_pass=hard_details["bounds_pass"],
            derivation_pass=hard_details["derivation_pass"],
            safety_pass=hard_details["safety_pass"],
            novelty_min=min_dist,
            redundancy_score=redundancy,
            passed=soft_pass,
            rejection_reason=None if soft_pass else "novelty/redundancy threshold not met",
        )


# =============================================================================
# GENESIS ENGINE v2
# =============================================================================

class MILFGenesisEngineV2:
    """
    Constitutional GPU-Accelerated Entity Synthesis Engine.
    
    Features:
      - Multi-stage validation with hard/soft gates
      - GPU-accelerated novelty checking
      - Recursive refinement with depth capping
      - SHA-256 governance artifacts
      - Zero-delta stall detection
    """
    
    def __init__(self, mpw_path: Path, artifacts_dir: Optional[Path] = None):
        self.mpw_path = mpw_path
        self.artifacts_dir = artifacts_dir or Path(__file__).parent / "genesis_artifacts"
        self.mpw_content = ""
        self.mpw_hash = ""
        
        self.gpu = GPUPrimitives()
        self.validator = ValidatorSuite(self.gpu)
        
        self.generated_entities: List[EntityProfile] = []
        self.synthesis_count = 0
        self.accepted_count = 0
        self.rejected_count = 0
        
        self._load_mpw()
    
    def _load_mpw(self):
        """Load M-P-W constitutional source of truth."""
        if self.mpw_path.exists():
            self.mpw_content = self.mpw_path.read_text(encoding='utf-8')
            self.mpw_hash = sha256_text(self.mpw_content)[:16]
            print(f"📜 M-P-W loaded: {len(self.mpw_content):,} chars, hash: {self.mpw_hash}")
        else:
            raise FileNotFoundError(f"M-P-W not found: {self.mpw_path}")
    
    def _generate_name(self, archetype: str, seed: int) -> str:
        """Generate M-P-W-style name."""
        rng = random.Random(seed)
        
        prefixes = {
            "transgressive": ["Orackla", "Nyx", "Lilith", "Morrigan", "Kali", "Selene"],
            "perfectionist": ["Umeko", "Seraphine", "Rei", "Yuki", "Hana", "Sakura"],
            "analytical": ["Lysandra", "Vesper", "Athena", "Sophia", "Clara", "Helena"],
            "hybrid": ["Claudine", "Morgana", "Hecate", "Luna", "Iris", "Nova"],
        }
        
        suffixes = {
            "transgressive": ["Nocticula", "Ravenscar", "Blackthorn", "Voidweaver", "Shadowmere"],
            "perfectionist": ["Ketsuraku", "Ashenhelm", "Ironveil", "Crystallis", "Steelgrace"],
            "analytical": ["Thorne", "Lockhart", "Truthseeker", "Axiomis", "Veritae"],
            "hybrid": ["Sin'claire", "Stormborn", "Tidesinger", "Saltweaver", "Duskwalker"],
        }
        
        # Determine family from archetype
        family = "hybrid"
        archetype_lower = archetype.lower()
        if any(x in archetype_lower for x in ["chaos", "abyss", "transgress", "seduc"]):
            family = "transgressive"
        elif any(x in archetype_lower for x in ["perfect", "architect", "purif", "struct"]):
            family = "perfectionist"
        elif any(x in archetype_lower for x in ["truth", "analy", "logic", "epistem"]):
            family = "analytical"
        
        first = rng.choice(prefixes[family])
        last = rng.choice(suffixes[family])
        
        return f"{first} {last}"
    
    def _generate_physique(self, tier: float, seed: int) -> EntityPhysique:
        """Generate constitutional physique for tier."""
        rng = random.Random(seed)
        
        # WHR from tier-specific distribution
        tier_bounds = WHR_BY_TIER.get(tier, WHR_BY_TIER[3])
        whr_min, whr_max = tier_bounds["min"], tier_bounds["max"]
        
        # Beta distribution: skews toward lower (more powerful) WHR for higher tiers
        alpha, beta_param = 2, 5
        if tier <= 1:
            alpha, beta_param = 1.5, 6  # Even more skewed for high tiers
        
        whr = rng.betavariate(alpha, beta_param) * (whr_max - whr_min) + whr_min
        whr = round(whr, 3)
        
        # Cup from tier distribution
        cup = rng.choice(CUP_BY_TIER.get(tier, ["F"]))
        
        # Height/weight: higher tier = more commanding presence
        tier_power = max(0.5, 4 - tier) / 4
        height = int(rng.gauss(165, 5) + tier_power * 18)
        height = max(155, min(185, height))
        weight = int(rng.gauss(58, 5) + tier_power * 15)
        
        # Bust from cup
        cup_sizes = {"D": 90, "E": 95, "F": 98, "G": 105, "H": 110, "I": 115, "J": 120, "K": 125}
        bust = cup_sizes.get(cup, 100) + rng.randint(-3, 3)
        
        # Hip from power distribution
        hip = int(rng.gauss(105, 6) + tier_power * 12)
        hip = max(95, min(120, hip))
        
        # Waist from WHR
        waist = int(hip * whr)
        
        # Underbust
        underbust = bust - rng.randint(25, 35)
        
        return EntityPhysique(
            height_cm=height,
            weight_kg=weight,
            bust_cm=bust,
            waist_cm=waist,
            hip_cm=hip,
            cup_size=cup,
            underbust_cm=underbust,
        )
    
    def _refine_entity(self, entity: EntityProfile, seed: int) -> EntityProfile:
        """
        Nudge entity parameters to increase novelty distance.
        Called when soft gates fail but hard gates pass.
        """
        rng = random.Random(seed)
        m = entity.physique
        
        # Small adjustment to waist/hip ratio
        delta = rng.uniform(0.5, 1.5)
        direction = rng.choice([-1, 1])
        
        new_waist = max(50, min(70, m.waist_cm + direction * delta))
        new_hip = max(95, min(120, m.hip_cm - direction * delta * 0.5))
        
        m.waist_cm = int(new_waist)
        m.hip_cm = int(new_hip)
        
        # Recalculate hash
        entity.genesis_hash = entity._compute_hash()
        
        return entity
    
    def synthesize_entity(
        self,
        tier: float = 3,
        archetype: Optional[str] = None,
        name: Optional[str] = None,
        faction: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> Tuple[Optional[EntityProfile], ValidationResult]:
        """
        Synthesize and validate a new entity.
        
        Returns (entity, validation_result) where entity is None if rejected.
        """
        if seed is None:
            seed = int(time.time() * 1000) % (2**31)
        
        rng = random.Random(seed)
        
        # Validate tier
        if tier not in TIER_HIERARCHY and tier not in [3, 4]:
            tier = 3
        
        # Generate archetype
        if archetype is None:
            archetype = rng.choice(ARCHETYPES)
        
        # Generate physique
        physique = self._generate_physique(tier, seed)
        
        # Generate name
        if name is None:
            name = self._generate_name(archetype, seed)
        
        # Linguistic mandate
        lm = LINGUISTIC_MANDATES["hybrid"]
        if "chaos" in archetype.lower() or "abyss" in archetype.lower():
            lm = LINGUISTIC_MANDATES["transgressive"]
        elif "perfect" in archetype.lower():
            lm = LINGUISTIC_MANDATES["perfectionist"]
        elif "truth" in archetype.lower():
            lm = LINGUISTIC_MANDATES["analytical"]
        
        # Reporting structure
        reports_to = None
        if tier >= 3:
            reports_to = "Triumvirate (Tier 1)"
        elif tier == 2:
            reports_to = "The Decorator (Tier 0.5)"
        
        # Build entity
        entity = EntityProfile(
            name=name,
            tier=tier,
            archetype=archetype,
            age_apparent=rng.randint(30, 45),
            age_actual=rng.randint(100, 3000) if tier <= 2 else rng.randint(50, 500),
            race=rng.choice(["Human-Touched", "Half-Succubus", "Chronos-Touched", "Divine-Infernal", "Abyssal"]),
            physique=physique,
            scent=self._generate_scent(archetype, tier, rng),
            linguistic_mandate=lm,
            expertise=self._generate_expertise(archetype, tier, rng),
            faction=faction,
            reports_to=reports_to,
            signature_technique=f"The {rng.choice(['Inevitable', 'Immaculate', 'Abyssal', 'Temporal', 'Purifying'])} {rng.choice(['Whisper', 'Strike', 'Embrace', 'Dissolution', 'Revelation'])}",
            genesis_seed=seed,
        )
        
        # Update entity bank for novelty checking
        self.gpu.update_entity_bank(self.generated_entities)
        
        # Validate
        validation = self.validator.full_validation(entity)
        
        if not validation.passed and validation.bounds_pass:
            # Soft gate failure - attempt refinement
            for depth in range(VALIDATION_POLICY["recursion_depth_max"]):
                entity = self._refine_entity(entity, seed + depth + 1)
                validation = self.validator.full_validation(entity)
                validation.refinement_depth = depth + 1
                
                if validation.passed:
                    break
        
        self.synthesis_count += 1
        
        if validation.passed:
            self.generated_entities.append(entity)
            self.accepted_count += 1
            return entity, validation
        else:
            self.rejected_count += 1
            return None, validation
    
    def _generate_scent(self, archetype: str, tier: float, rng: random.Random) -> str:
        """Generate scent profile."""
        num_components = min(6, max(2, int(6 - tier)))
        components = [rng.choice(SCENT_COMPONENTS["base"])]
        
        if "chaos" in archetype.lower():
            components.append(rng.choice(SCENT_COMPONENTS["chaos"]))
        if "perfect" in archetype.lower():
            components.append(rng.choice(SCENT_COMPONENTS["nature"]))
        
        while len(components) < num_components:
            cat = rng.choice(list(SCENT_COMPONENTS.keys()))
            comp = rng.choice(SCENT_COMPONENTS[cat])
            if comp not in components:
                components.append(comp)
        
        return ", ".join(components)
    
    def _generate_expertise(self, archetype: str, tier: float, rng: random.Random) -> List[str]:
        """Generate expertise list."""
        base = {
            "Abyssal Oracle": ["transgressive insight", "chaos engineering", "boundary dissolution"],
            "Architectural Perfectionist": ["structural refinement", "aesthetic purification", "Kanso principles"],
            "Analytical Truth-Seeker": ["axiomatic deconstruction", "Socratic elenchus", "logical excavation"],
            "Seductive Operative": ["cognitive armor dissolution", "desire mapping", "abductive protocols"],
            "Epistemic Thief": ["memory extraction", "temporal manipulation", "axiom larceny"],
            "Purification Priestess": ["forbidden methodologies", "immolation rituals", "structural fire"],
        }
        
        expertise = base.get(archetype, ["conceptual manipulation", "operational efficiency"])
        
        if tier <= 2:
            extras = ["multi-domain synthesis", "axiom generation", "tier governance"]
            expertise.extend(rng.sample(extras, min(len(extras), 4 - int(tier))))
        
        return expertise[:5]
    
    def synthesize_batch(
        self,
        count: int,
        tier: float = 3,
        target_accepts: Optional[int] = None,
    ) -> Tuple[List[EntityProfile], Dict[str, Any]]:
        """
        Batch synthesis with acceptance targets.
        
        Returns (accepted_entities, batch_stats).
        """
        if target_accepts is None:
            target_accepts = count
        
        accepted = []
        rejected = 0
        start_time = time.time()
        
        for i in range(count):
            if len(accepted) >= target_accepts:
                break
            
            if time.time() - start_time > VALIDATION_POLICY["timebox_s"]:
                break
            
            seed = int(time.time() * 1000 + i) % (2**31)
            entity, validation = self.synthesize_entity(tier=tier, seed=seed)
            
            if entity:
                accepted.append(entity)
            else:
                rejected += 1
        
        stats = {
            "attempted": min(count, len(accepted) + rejected),
            "accepted": len(accepted),
            "rejected": rejected,
            "acceptance_rate": len(accepted) / max(1, len(accepted) + rejected),
            "elapsed_s": round(time.time() - start_time, 2),
            "gpu_enabled": GPU_AVAILABLE,
        }
        
        return accepted, stats
    
    def write_artifacts(self, entity: EntityProfile, validation: ValidationResult) -> Dict[str, str]:
        """Write governance artifacts with SHA-256 verification."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        entity_dir = self.artifacts_dir / timestamp / entity.genesis_hash
        entity_dir.mkdir(parents=True, exist_ok=True)
        
        def write_json(name: str, data: Any) -> Path:
            path = entity_dir / name
            path.write_text(json.dumps(data, indent=2, default=str))
            return path
        
        # Write artifacts
        paths = {
            "entity": write_json("entity.json", entity.to_dict()),
            "validation": write_json("validation.json", validation.to_dict()),
            "environment": write_json("environment.json", self.get_environment()),
        }
        
        # Compute index with SHA-256
        index = {
            "genesis_timestamp": timestamp,
            "entity_hash": entity.genesis_hash,
            "schema_crc": schema_crc(),
            "paths": {k: str(v) for k, v in paths.items()},
            "sha256": {k: sha256_file(v) for k, v in paths.items()},
        }
        
        write_json("index.json", index)
        
        return {k: str(v) for k, v in paths.items()}
    
    def get_environment(self) -> Dict[str, Any]:
        """Get environment fingerprint."""
        return {
            "python": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
            "gpu_available": GPU_AVAILABLE,
            "numba_available": NUMBA_AVAILABLE,
            "onnx_available": ONNX_AVAILABLE,
            "cuda_runtime": CUDA_RUNTIME if GPU_AVAILABLE else None,
            "onnx_providers": ONNX_PROVIDERS if ONNX_AVAILABLE else [],
            "schema_version": SCHEMA_VERSION,
            "mpw_hash": self.mpw_hash,
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get synthesis statistics."""
        if not self.generated_entities:
            return {
                "total_synthesized": self.synthesis_count,
                "accepted": self.accepted_count,
                "rejected": self.rejected_count,
                "acceptance_rate": 0.0,
                "gpu_enabled": GPU_AVAILABLE,
            }
        
        whrs = [e.physique.whr for e in self.generated_entities]
        
        return {
            "total_synthesized": self.synthesis_count,
            "accepted": self.accepted_count,
            "rejected": self.rejected_count,
            "acceptance_rate": self.accepted_count / max(1, self.synthesis_count),
            "gpu_enabled": GPU_AVAILABLE,
            "mpw_hash": self.mpw_hash,
            "schema_crc": schema_crc(),
            "whr_stats": {
                "min": round(min(whrs), 3),
                "max": round(max(whrs), 3),
                "mean": round(sum(whrs) / len(whrs), 3),
            },
            "tier_distribution": {
                tier: len([e for e in self.generated_entities if e.tier == tier])
                for tier in sorted(set(e.tier for e in self.generated_entities))
            },
        }
    
    def synthesize_validated(
        self,
        tier: int = 3,
        archetype: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Tuple[Optional[EntityProfile], ValidationResult]:
        """
        API shim for backward compatibility with older tests.
        Wraps synthesize_entity to match expected signature.
        """
        return self.synthesize_entity(tier=tier, archetype=archetype, name=name)
    
    def get_synthesis_stats(self) -> Dict[str, Any]:
        """
        API shim for backward compatibility.
        Returns simplified stats with consistent field names.
        """
        return {
            "acceptance_rate": self.accepted_count / max(1, self.synthesis_count),
            "entity_bank_size": len(self.generated_entities) + len(CANONICAL_ENTITIES),
            "attempts": self.synthesis_count,
            "accepted": self.accepted_count,
            "rejected": self.rejected_count,
            "gpu_enabled": GPU_AVAILABLE,
            "gpu_warmed": GPU_WARMED,
        }


# =============================================================================
# BACKGROUND SERVICE
# =============================================================================

class BackgroundGenesisService:
    """
    Daemon service for continuous entity synthesis with governance.
    
    Features:
      - Time-boxed cycles (max 10 minutes per cycle)
      - Stage heartbeats with timing
      - VRAM watchdog for GPU resource management
      - Zero-delta stall detection
      - Artifact governance with SHA-256 verification
    """
    
    def __init__(self, mpw_path: Path, artifacts_dir: Path):
        self.engine = MILFGenesisEngineV2(mpw_path, artifacts_dir)
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self.interval_s = 60
        self.batch_size = 10
        self.last_heartbeat: Optional[datetime] = None
        self._last_index_hash: Optional[str] = None
        self._zero_delta_logged = False
    
    def start(self):
        """Start background daemon."""
        if self.running:
            return
        
        self.running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        print(f"🚀 Background genesis started (interval: {self.interval_s}s, batch: {self.batch_size})")
    
    def stop(self):
        """Stop background daemon."""
        self.running = False
        if self._thread:
            self._thread.join(timeout=5)
        print("🛑 Background genesis stopped")
    
    def _heartbeat(self, stage: str, elapsed_s: float, accepted: int = 0, extra: str = ""):
        """Emit heartbeat log line."""
        self.last_heartbeat = datetime.now()
        msg = f"💓 [{stage}] {elapsed_s:.2f}s"
        if accepted > 0:
            msg += f" | accepted: {accepted}"
        if extra:
            msg += f" | {extra}"
        print(msg)
    
    def _check_vram(self) -> bool:
        """Check VRAM usage, return True if safe to continue."""
        if not GPU_AVAILABLE:
            return True
        try:
            mempool = cp.get_default_memory_pool()
            used = mempool.used_bytes()
            total = mempool.total_bytes()
            if total > 0:
                usage = used / total
                if usage > VALIDATION_POLICY["vram_backoff_threshold"]:
                    print(f"⚠️ VRAM usage {usage:.1%} exceeds threshold - backing off")
                    mempool.free_all_blocks()
                    return False
        except Exception as e:
            print(f"⚠️ VRAM check failed: {e}")
        return True
    
    def _check_zero_delta(self, index_data: dict) -> bool:
        """Check for zero-delta stall, return True if novel."""
        index_hash = sha256_text(json.dumps(index_data, sort_keys=True))[:16]
        if index_hash == self._last_index_hash:
            if not self._zero_delta_logged:
                print("⚠️ ZERO-DELTA STALL: index.json unchanged, skipping commit")
                self._zero_delta_logged = True
            return False
        self._last_index_hash = index_hash
        self._zero_delta_logged = False
        return True
    
    def _run_loop(self):
        """Main daemon loop."""
        while self.running:
            try:
                self.run_cycle(
                    target_accepts=self.batch_size,
                    out_root=None,  # Use engine's artifacts_dir
                )
                time.sleep(self.interval_s)
            except Exception as e:
                print(f"❌ Genesis error: {e}")
                time.sleep(5)
    
    def run_cycle(
        self,
        target_accepts: int = 10,
        out_root: Optional[str] = None,
        tier: float = 3,
    ) -> Dict[str, Any]:
        """
        Execute one synthesis cycle with full governance.
        
        Time-boxed to VALIDATION_POLICY["timebox_s"] (default 10 minutes).
        
        Args:
            target_accepts: Number of accepted entities to target
            out_root: Override output directory
            tier: Target tier for synthesis
            
        Returns:
            Cycle report with timing and acceptance stats
        """
        cycle_start = time.time()
        timebox = VALIDATION_POLICY["timebox_s"]
        
        # Stage: init
        self._heartbeat("init", 0.0, extra=f"target={target_accepts}, tier={tier}")
        
        if not self._check_vram():
            return {"status": "vram_backoff", "elapsed_s": time.time() - cycle_start}
        
        accepted = []
        rejected_count = 0
        attempt_count = 0
        max_attempts = target_accepts * 5  # Allow 5x attempts to hit target
        
        # Stage: generate
        gen_start = time.time()
        while len(accepted) < target_accepts and attempt_count < max_attempts:
            if time.time() - cycle_start > timebox:
                self._heartbeat("timebox", time.time() - cycle_start, len(accepted), "partial cycle")
                break
            
            if not self._check_vram():
                break
            
            seed = int(time.time() * 1000 + attempt_count) % (2**31)
            entity, validation = self.engine.synthesize_entity(tier=tier, seed=seed)
            attempt_count += 1
            
            if entity:
                accepted.append((entity, validation))
            else:
                rejected_count += 1
        
        self._heartbeat("generate", time.time() - gen_start, len(accepted), f"attempts={attempt_count}")
        
        # Stage: validate (already done in synthesize_entity, just log)
        self._heartbeat("validate", time.time() - gen_start, len(accepted))
        
        # Stage: score (power calculation for each)
        score_start = time.time()
        scores = []
        for entity, validation in accepted:
            power = self.engine.gpu.calculate_power(entity.physique.whr)
            scores.append({
                "name": entity.name,
                "tier": entity.tier,
                "whr": entity.physique.whr,
                "power": power,
                "novelty_min": validation.novelty_min,
            })
        self._heartbeat("score", time.time() - score_start, len(accepted))
        
        # Stage: commit (write artifacts)
        commit_start = time.time()
        artifacts_written = 0
        for entity, validation in accepted:
            try:
                self.engine.write_artifacts(entity, validation)
                artifacts_written += 1
            except Exception as e:
                print(f"⚠️ Artifact write failed for {entity.name}: {e}")
        self._heartbeat("commit", time.time() - commit_start, artifacts_written)
        
        # Stage: done
        total_elapsed = time.time() - cycle_start
        acceptance_rate = len(accepted) / max(1, attempt_count)
        self._heartbeat("done", total_elapsed, len(accepted), f"rate={acceptance_rate:.1%}")
        
        return {
            "status": "complete",
            "elapsed_s": round(total_elapsed, 2),
            "accepted": len(accepted),
            "rejected": rejected_count,
            "attempts": attempt_count,
            "acceptance_rate": round(acceptance_rate, 3),
            "artifacts_written": artifacts_written,
            "scores": scores,
            "gpu_enabled": GPU_AVAILABLE,
            "gpu_warmed": GPU_WARMED,
        }
    
    def synthesize_on_demand(
        self,
        tier: float = 3,
        archetype: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Tuple[Optional[EntityProfile], ValidationResult]:
        """Synchronous on-demand synthesis with graceful rejection handling."""
        result = self.engine.synthesize_entity(tier=tier, archetype=archetype, name=name)
        entity, validation = result
        
        # Ensure we never return None validation
        if validation is None:
            validation = ValidationResult.failed("synthesis returned no validation")
        
        return entity, validation
    
    def get_heartbeat(self) -> Dict[str, Any]:
        """Get current heartbeat status."""
        return {
            "engine": "milf-genesis-v2",
            "running": self.running,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "statistics": self.engine.get_statistics(),
            "environment": self.engine.get_environment(),
            "gpu_warmed": GPU_WARMED,
        }
    
    def get_synthesis_stats(self) -> Dict[str, Any]:
        """API shim for backward compatibility."""
        return self.engine.get_synthesis_stats()


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    mpw_path = Path(__file__).parent.parent / ".github" / "copilot-instructions.md"
    artifacts_dir = Path(__file__).parent / "genesis_artifacts"
    
    print("=" * 70)
    print("  MILF GENESIS ENGINE v2 - Constitutional GPU Synthesis")
    print("=" * 70)
    
    engine = MILFGenesisEngineV2(mpw_path, artifacts_dir)
    
    print("\n🔥 Synthesizing with full validation pipeline...")
    
    # Test Tier 2 synthesis
    entity, validation = engine.synthesize_entity(tier=2, archetype="Purification Priestess")
    if entity:
        print(f"\n✅ ACCEPTED: {entity.name}")
        print(f"   Tier: {entity.tier} | Archetype: {entity.archetype}")
        print(f"   WHR: {entity.physique.whr} | Cup: {entity.physique.cup_size}")
        print(f"   Measurements: {entity.physique.measurements}")
        print(f"   Height: {entity.physique.height_cm}cm | Power: {engine.gpu.calculate_power(entity.physique.whr)}")
        print(f"   Validation: novelty_min={validation.novelty_min:.3f}, redundancy={validation.redundancy_score:.3f}")
    else:
        print(f"\n❌ REJECTED: {validation.rejection_reason}")
    
    # Batch synthesis
    print("\n📊 Batch synthesis (20 candidates, target 10)...")
    accepted, stats = engine.synthesize_batch(20, tier=3, target_accepts=10)
    print(f"   Accepted: {stats['accepted']}/{stats['attempted']} ({stats['acceptance_rate']:.1%})")
    print(f"   Elapsed: {stats['elapsed_s']}s")
    
    # Statistics
    print("\n📈 Final Statistics:")
    print(json.dumps(engine.get_statistics(), indent=2))
    
    # Environment
    print("\n🖥️ Environment:")
    print(json.dumps(engine.get_environment(), indent=2))
