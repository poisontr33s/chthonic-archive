"""
🌀 GPU-Accelerated Force-Directed Graph Layout

Implements batched force calculations for entity relationship visualization with:
- Axis-locked positions for hierarchical actors (Triumvirate, Decorator)
- Inertia scaling based on WHR/Capacity metrics
- Progressive rendering for large graphs (100k+ edges)

Hardware Target: RTX 4090 Laptop GPU (16GB VRAM, batch 500k+ edges)
"""

import numpy as np
from typing import Optional, Dict, List, Tuple, Set
from dataclasses import dataclass, field
import logging
import math

from gpu_config import get_config, get_capabilities, gpu_available, GPUBackend

logger = logging.getLogger("mas.gpu.forces")


@dataclass
class NodeConstraints:
    """Constraints for individual nodes in layout."""
    # Axis locks (None = free, tuple = locked to direction)
    axis_lock: Optional[Tuple[float, float, float]] = None
    
    # Position bounds
    min_radius: float = 0.0
    max_radius: float = float('inf')
    
    # Fixed position (overrides forces)
    fixed_position: Optional[Tuple[float, float, float]] = None
    
    # Inertia multiplier (higher = harder to move)
    inertia: float = 1.0
    
    # Crown wedge for Decorator tier
    crown_wedge: Optional[Tuple[float, float]] = None  # (min_angle, max_angle) in radians


@dataclass
class LayoutConfig:
    """Configuration for force-directed layout."""
    # Force parameters
    repulsion_strength: float = 1000.0
    attraction_strength: float = 0.01
    damping: float = 0.9
    min_distance: float = 1.0
    
    # Hierarchical layout
    tier_spacing: float = 50.0
    tier_attraction: float = 0.5  # Pull towards tier ring
    
    # Performance
    max_iterations: int = 500
    convergence_threshold: float = 0.01
    tile_size: int = 256  # GPU tile size for batching
    
    # Rendering
    progressive_render: bool = True
    render_every_n: int = 10
    
    # Determinism
    seed: int = 42


@dataclass
class LayoutState:
    """Current state of layout computation."""
    positions: np.ndarray  # (N, 3) current positions
    velocities: np.ndarray  # (N, 3) current velocities
    forces: np.ndarray     # (N, 3) accumulated forces
    
    node_ids: List[str]    # Node identifiers
    constraints: Dict[str, NodeConstraints] = field(default_factory=dict)
    
    iteration: int = 0
    total_movement: float = float('inf')
    converged: bool = False
    
    # Edges
    edge_sources: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.int32))
    edge_targets: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.int32))
    edge_weights: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.float32))


# ============================================================================
# Tier and Hierarchy Definitions
# ============================================================================

TIER_RADII = {
    0.5: 10.0,   # Decorator - crown apex
    1.0: 50.0,   # Triumvirate
    2.0: 100.0,  # Prime Factions
    3.0: 150.0,  # Manifested Sub-MILFs
    4.0: 200.0,  # Interloper Agents (chaos ring)
}

TIER_AXIS_LOCKS = {
    # Triumvirate locked to unit vectors
    "Orackla Nocticula": (1.0, 0.0, 0.0),      # +X axis
    "Madam Umeko Ketsuraku": (-0.5, 0.866, 0.0),  # 120° from X
    "Dr. Lysandra Thorne": (-0.5, -0.866, 0.0),   # 240° from X
    "The Decorator": (0.0, 0.0, 1.0),            # +Z apex
}

# WHR-derived inertia (higher WHR ratio = higher inertia = more stable)
WHR_INERTIA_MAP = {
    "The Decorator": 0.464,
    "Orackla Nocticula": 0.491,
    "Madam Umeko Ketsuraku": 0.533,
    "Dr. Lysandra Thorne": 0.58,
    "Kali Nyx Ravenscar": 0.556,
    "Vesper Mnemosyne Lockhart": 0.573,
    "Seraphine Kore Ashenhelm": 0.592,
}


def whr_to_inertia(whr: float) -> float:
    """Convert WHR ratio to inertia multiplier (lower WHR = higher inertia)."""
    # WHR 0.464 (Decorator) → inertia 5.0 (very stable)
    # WHR 0.6 → inertia 1.0 (baseline)
    if whr <= 0:
        return 1.0
    return max(0.5, min(10.0, 0.6 / whr * 2.0))


# ============================================================================
# CPU Reference Implementation (with Barnes-Hut style optimization)
# ============================================================================

# Threshold for switching to fast approximation
FAST_REPULSION_THRESHOLD = 200  # Use spatial grid for N > 200 nodes


def _cpu_compute_repulsion(
    positions: np.ndarray,
    strength: float,
    min_distance: float
) -> np.ndarray:
    """
    CPU repulsion: Automatically switches between exact O(N²) for small graphs
    and spatial-grid approximation O(N × k) for large graphs.
    """
    n = positions.shape[0]
    
    if n <= FAST_REPULSION_THRESHOLD:
        return _cpu_compute_repulsion_exact(positions, strength, min_distance)
    else:
        return _cpu_compute_repulsion_fast(positions, strength, min_distance)


def _cpu_compute_repulsion_exact(
    positions: np.ndarray,
    strength: float,
    min_distance: float
) -> np.ndarray:
    """
    Exact O(N²) repulsion - use for small graphs (N < 200).
    """
    n = positions.shape[0]
    forces = np.zeros_like(positions)
    
    for i in range(n):
        for j in range(i + 1, n):
            delta = positions[i] - positions[j]
            distance = np.linalg.norm(delta)
            
            if distance < min_distance:
                distance = min_distance
            
            # Coulomb-like repulsion
            force_magnitude = strength / (distance ** 2)
            force_direction = delta / distance
            force = force_direction * force_magnitude
            
            forces[i] += force
            forces[j] -= force
    
    return forces


def _cpu_compute_repulsion_fast(
    positions: np.ndarray,
    strength: float,
    min_distance: float,
    cutoff_factor: float = 10.0
) -> np.ndarray:
    """
    Spatial grid approximation for repulsion - O(N × k) where k = avg neighbors.
    
    Barnes-Hut style optimization:
    1. Build spatial grid (cell size = cutoff distance)
    2. For each node, only compute exact forces with nearby cells
    3. Approximate distant cells as single point masses (center of mass)
    
    Args:
        positions: Node positions (N, 3)
        strength: Repulsion strength
        min_distance: Minimum separation
        cutoff_factor: Cells beyond this × cell_size use approximation
        
    Returns:
        Force vectors (N, 3)
    """
    n = positions.shape[0]
    forces = np.zeros_like(positions)
    
    if n == 0:
        return forces
    
    # Determine bounding box and cell size
    pos_min = positions.min(axis=0)
    pos_max = positions.max(axis=0)
    extent = pos_max - pos_min
    
    # Cell size based on average expected separation (sqrt(N) heuristic)
    avg_separation = max(extent.max() / max(np.sqrt(n), 1), min_distance * 2)
    cell_size = avg_separation
    
    # Grid dimensions (at least 1 cell per dimension)
    grid_dims = np.maximum(np.ceil(extent / cell_size).astype(int), 1)
    
    # Clamp to reasonable grid size (prevent memory explosion)
    max_cells_per_dim = 50
    grid_dims = np.minimum(grid_dims, max_cells_per_dim)
    cell_size_actual = extent / np.maximum(grid_dims, 1)
    cell_size_actual = np.where(cell_size_actual == 0, cell_size, cell_size_actual)
    
    # Assign nodes to cells
    cell_indices = np.floor((positions - pos_min) / cell_size_actual).astype(int)
    cell_indices = np.clip(cell_indices, 0, grid_dims - 1)
    
    # Build cell lookup: cell_key -> list of node indices
    cell_to_nodes: Dict[Tuple[int, int, int], List[int]] = {}
    for i in range(n):
        key = (cell_indices[i, 0], cell_indices[i, 1], cell_indices[i, 2])
        if key not in cell_to_nodes:
            cell_to_nodes[key] = []
        cell_to_nodes[key].append(i)
    
    # Precompute cell centers of mass for approximation
    cell_com: Dict[Tuple[int, int, int], Tuple[np.ndarray, int]] = {}
    for key, node_list in cell_to_nodes.items():
        com = positions[node_list].mean(axis=0)
        cell_com[key] = (com, len(node_list))
    
    # Cutoff for exact vs approximate calculation
    cutoff_cells = int(cutoff_factor)
    
    # For each node, compute forces
    for i in range(n):
        my_cell = (cell_indices[i, 0], cell_indices[i, 1], cell_indices[i, 2])
        my_pos = positions[i]
        
        # Iterate over all cells
        for cell_key, (com, count) in cell_com.items():
            # Manhattan distance in cell space
            cell_dist = max(
                abs(cell_key[0] - my_cell[0]),
                abs(cell_key[1] - my_cell[1]),
                abs(cell_key[2] - my_cell[2])
            )
            
            if cell_dist <= 1:
                # Nearby cell: compute exact forces with each node
                for j in cell_to_nodes[cell_key]:
                    if j <= i:
                        continue  # Avoid double-counting and self
                    
                    delta = my_pos - positions[j]
                    distance = np.linalg.norm(delta)
                    
                    if distance < min_distance:
                        distance = min_distance
                    
                    force_magnitude = strength / (distance ** 2)
                    force_direction = delta / distance
                    force = force_direction * force_magnitude
                    
                    forces[i] += force
                    forces[j] -= force
                    
            elif cell_dist <= cutoff_cells:
                # Medium distance: approximate cell as center of mass
                delta = my_pos - com
                distance = np.linalg.norm(delta)
                
                if distance < min_distance:
                    distance = min_distance
                
                # Treat cell as single mass with strength proportional to node count
                force_magnitude = (strength * count) / (distance ** 2)
                force_direction = delta / distance
                forces[i] += force_direction * force_magnitude
            
            # Far cells: negligible force (Coulomb drops off as 1/r²)
    
    return forces


def _cpu_compute_attraction(
    positions: np.ndarray,
    edge_sources: np.ndarray,
    edge_targets: np.ndarray,
    edge_weights: np.ndarray,
    strength: float
) -> np.ndarray:
    """
    CPU reference: Compute attraction forces along edges.
    
    O(E) - linear in edge count.
    """
    forces = np.zeros_like(positions)
    
    for src, tgt, weight in zip(edge_sources, edge_targets, edge_weights):
        delta = positions[tgt] - positions[src]
        distance = np.linalg.norm(delta)
        
        if distance < 1e-6:
            continue
        
        # Spring-like attraction
        force_magnitude = strength * distance * weight
        force_direction = delta / distance
        force = force_direction * force_magnitude
        
        forces[src] += force
        forces[tgt] -= force
    
    return forces


def _cpu_compute_tier_forces(
    positions: np.ndarray,
    node_tiers: np.ndarray,
    tier_attraction: float
) -> np.ndarray:
    """
    CPU reference: Pull nodes towards their tier radius.
    """
    forces = np.zeros_like(positions)
    
    for i, tier in enumerate(node_tiers):
        target_radius = TIER_RADII.get(tier, 200.0)
        
        # Project to XY plane for radius calculation
        xy_pos = positions[i, :2]
        current_radius = np.linalg.norm(xy_pos)
        
        if current_radius < 1e-6:
            continue
        
        # Force towards target radius
        radius_error = target_radius - current_radius
        force_direction = xy_pos / current_radius
        force = force_direction * radius_error * tier_attraction
        
        forces[i, :2] += force
    
    return forces


def _apply_constraints(
    positions: np.ndarray,
    velocities: np.ndarray,
    forces: np.ndarray,
    node_ids: List[str],
    constraints: Dict[str, NodeConstraints]
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Apply node constraints: axis locks, bounds, fixed positions.
    """
    for i, node_id in enumerate(node_ids):
        constraint = constraints.get(node_id)
        
        # Apply axis locks from tier hierarchy
        if node_id in TIER_AXIS_LOCKS:
            axis = np.array(TIER_AXIS_LOCKS[node_id])
            # Project position onto axis
            pos_on_axis = np.dot(positions[i], axis) * axis
            positions[i] = pos_on_axis
            # Project velocity onto axis
            vel_on_axis = np.dot(velocities[i], axis) * axis
            velocities[i] = vel_on_axis
        
        if constraint is None:
            continue
        
        # Fixed position
        if constraint.fixed_position is not None:
            positions[i] = np.array(constraint.fixed_position)
            velocities[i] = np.zeros(3)
            continue
        
        # Axis lock (general)
        if constraint.axis_lock is not None:
            axis = np.array(constraint.axis_lock)
            axis = axis / np.linalg.norm(axis)
            pos_on_axis = np.dot(positions[i], axis) * axis
            positions[i] = pos_on_axis
            vel_on_axis = np.dot(velocities[i], axis) * axis
            velocities[i] = vel_on_axis
        
        # Crown wedge (for Decorator)
        if constraint.crown_wedge is not None:
            min_angle, max_angle = constraint.crown_wedge
            xy_pos = positions[i, :2]
            current_angle = np.arctan2(xy_pos[1], xy_pos[0])
            
            # Clamp angle to wedge
            if current_angle < min_angle:
                current_angle = min_angle
            elif current_angle > max_angle:
                current_angle = max_angle
            
            radius = np.linalg.norm(xy_pos)
            positions[i, 0] = radius * np.cos(current_angle)
            positions[i, 1] = radius * np.sin(current_angle)
        
        # Radius bounds
        radius = np.linalg.norm(positions[i, :2])
        if radius < constraint.min_radius:
            scale = constraint.min_radius / max(radius, 1e-6)
            positions[i, :2] *= scale
        elif radius > constraint.max_radius:
            scale = constraint.max_radius / radius
            positions[i, :2] *= scale
    
    return positions, velocities


def cpu_layout_step(
    state: LayoutState,
    config: LayoutConfig,
    node_tiers: np.ndarray,
    dt: float = 1.0
) -> LayoutState:
    """
    CPU reference: Single layout iteration step.
    """
    # Reset forces
    state.forces.fill(0)
    
    # Repulsion (all pairs)
    repulsion = _cpu_compute_repulsion(
        state.positions, 
        config.repulsion_strength, 
        config.min_distance
    )
    state.forces += repulsion
    
    # Attraction (edges)
    if len(state.edge_sources) > 0:
        attraction = _cpu_compute_attraction(
            state.positions,
            state.edge_sources,
            state.edge_targets,
            state.edge_weights,
            config.attraction_strength
        )
        state.forces += attraction
    
    # Tier forces
    tier_forces = _cpu_compute_tier_forces(
        state.positions,
        node_tiers,
        config.tier_attraction
    )
    state.forces += tier_forces
    
    # Apply inertia from WHR
    for i, node_id in enumerate(state.node_ids):
        whr = WHR_INERTIA_MAP.get(node_id, 0.6)
        inertia = whr_to_inertia(whr)
        state.forces[i] /= inertia
    
    # Update velocities and positions
    state.velocities = (state.velocities + state.forces * dt) * config.damping
    state.positions += state.velocities * dt
    
    # Apply constraints
    state.positions, state.velocities = _apply_constraints(
        state.positions,
        state.velocities,
        state.forces,
        state.node_ids,
        state.constraints
    )
    
    # Track movement
    state.total_movement = np.sum(np.abs(state.velocities))
    state.converged = state.total_movement < config.convergence_threshold
    state.iteration += 1
    
    return state


# ============================================================================
# GPU Implementation
# ============================================================================

def _get_cupy():
    """Lazy import CuPy."""
    try:
        import cupy as cp
        return cp
    except ImportError:
        return None


def _gpu_compute_repulsion_tiled(
    positions_gpu,  # CuPy array
    strength: float,
    min_distance: float,
    tile_size: int = 256
):
    """
    GPU: Compute repulsion with tiled matrix multiplication.
    
    Uses O(N²) memory-efficient tiling for large graphs.
    """
    cp = _get_cupy()
    n = positions_gpu.shape[0]
    forces = cp.zeros_like(positions_gpu)
    
    # Process in tiles to avoid memory explosion
    for i_start in range(0, n, tile_size):
        i_end = min(i_start + tile_size, n)
        
        for j_start in range(0, n, tile_size):
            j_end = min(j_start + tile_size, n)
            
            # Tile positions
            pos_i = positions_gpu[i_start:i_end]  # (Ti, 3)
            pos_j = positions_gpu[j_start:j_end]  # (Tj, 3)
            
            # Compute pairwise distances
            delta = pos_i[:, None, :] - pos_j[None, :, :]  # (Ti, Tj, 3)
            distances = cp.linalg.norm(delta, axis=2)  # (Ti, Tj)
            distances = cp.maximum(distances, min_distance)
            
            # Repulsion forces
            force_magnitude = strength / (distances ** 2)  # (Ti, Tj)
            
            # Mask self-interactions
            if i_start == j_start:
                mask = cp.eye(i_end - i_start, j_end - j_start, dtype=cp.bool_)
                force_magnitude = cp.where(mask, 0.0, force_magnitude)
            
            # Normalize delta to get direction
            delta_norm = delta / (distances[:, :, None] + 1e-8)  # (Ti, Tj, 3)
            
            # Accumulate forces
            tile_forces = cp.sum(delta_norm * force_magnitude[:, :, None], axis=1)  # (Ti, 3)
            forces[i_start:i_end] += tile_forces
    
    return forces


def gpu_layout_step(
    state: LayoutState,
    config: LayoutConfig,
    node_tiers: np.ndarray,
    dt: float = 1.0
) -> LayoutState:
    """
    GPU-accelerated layout iteration step.
    """
    cp = _get_cupy()
    if cp is None:
        return cpu_layout_step(state, config, node_tiers, dt)
    
    try:
        # Transfer to GPU
        pos_gpu = cp.asarray(state.positions, dtype=cp.float32)
        vel_gpu = cp.asarray(state.velocities, dtype=cp.float32)
        forces_gpu = cp.zeros_like(pos_gpu)
        
        # GPU repulsion (tiled)
        repulsion = _gpu_compute_repulsion_tiled(
            pos_gpu,
            config.repulsion_strength,
            config.min_distance,
            config.tile_size
        )
        forces_gpu += repulsion
        
        # Edge attraction (GPU)
        if len(state.edge_sources) > 0:
            src_gpu = cp.asarray(state.edge_sources, dtype=cp.int32)
            tgt_gpu = cp.asarray(state.edge_targets, dtype=cp.int32)
            wgt_gpu = cp.asarray(state.edge_weights, dtype=cp.float32)
            
            # Vectorized edge forces
            delta = pos_gpu[tgt_gpu] - pos_gpu[src_gpu]  # (E, 3)
            distances = cp.linalg.norm(delta, axis=1, keepdims=True)  # (E, 1)
            distances = cp.maximum(distances, 1e-6)
            
            force_magnitude = config.attraction_strength * distances[:, 0] * wgt_gpu
            force_direction = delta / distances
            edge_forces = force_direction * force_magnitude[:, None]
            
            # Scatter-add (GPU atomics)
            cp.scatter_add(forces_gpu, src_gpu[:, None], edge_forces.repeat(3, axis=0).reshape(-1, 3))
            cp.scatter_add(forces_gpu, tgt_gpu[:, None], -edge_forces.repeat(3, axis=0).reshape(-1, 3))
        
        # Tier forces (GPU)
        tiers_gpu = cp.asarray(node_tiers, dtype=cp.float32)
        target_radii = cp.array([TIER_RADII.get(t, 200.0) for t in node_tiers], dtype=cp.float32)
        
        xy_pos = pos_gpu[:, :2]
        current_radii = cp.linalg.norm(xy_pos, axis=1)
        current_radii = cp.maximum(current_radii, 1e-6)
        
        radius_error = target_radii - current_radii
        force_direction = xy_pos / current_radii[:, None]
        tier_forces = force_direction * (radius_error * config.tier_attraction)[:, None]
        
        forces_gpu[:, :2] += tier_forces
        
        # Apply inertia
        inertias = cp.array([whr_to_inertia(WHR_INERTIA_MAP.get(nid, 0.6)) for nid in state.node_ids], dtype=cp.float32)
        forces_gpu /= inertias[:, None]
        
        # Update velocities and positions
        vel_gpu = (vel_gpu + forces_gpu * dt) * config.damping
        pos_gpu += vel_gpu * dt
        
        # Transfer back to CPU for constraint application
        state.positions = cp.asnumpy(pos_gpu)
        state.velocities = cp.asnumpy(vel_gpu)
        state.forces = cp.asnumpy(forces_gpu)
        
        # Apply constraints (CPU - simpler for complex logic)
        state.positions, state.velocities = _apply_constraints(
            state.positions,
            state.velocities,
            state.forces,
            state.node_ids,
            state.constraints
        )
        
        # Track movement
        state.total_movement = np.sum(np.abs(state.velocities))
        state.converged = state.total_movement < config.convergence_threshold
        state.iteration += 1
        
        return state
        
    except Exception as e:
        logger.error(f"GPU layout failed: {e}")
        return cpu_layout_step(state, config, node_tiers, dt)


def layout_step(
    state: LayoutState,
    config: LayoutConfig,
    node_tiers: np.ndarray,
    dt: float = 1.0
) -> LayoutState:
    """
    Unified layout step - uses GPU if available.
    """
    if gpu_available():
        return gpu_layout_step(state, config, node_tiers, dt)
    return cpu_layout_step(state, config, node_tiers, dt)


# ============================================================================
# Layout Initialization
# ============================================================================

def initialize_layout(
    node_ids: List[str],
    node_tiers: List[float],
    edges: List[Tuple[int, int, float]],
    constraints: Optional[Dict[str, NodeConstraints]] = None,
    seed: int = 42
) -> LayoutState:
    """
    Initialize layout state with hierarchical positioning.
    
    Args:
        node_ids: List of node identifiers
        node_tiers: List of tier values (0.5, 1.0, 2.0, etc.)
        edges: List of (source_idx, target_idx, weight) tuples
        constraints: Optional node constraints
        seed: Random seed for initial positions
    """
    rng = np.random.default_rng(seed)
    n = len(node_ids)
    
    # Initialize positions based on tier
    positions = np.zeros((n, 3), dtype=np.float32)
    
    for i, (node_id, tier) in enumerate(zip(node_ids, node_tiers)):
        radius = TIER_RADII.get(tier, 200.0)
        
        # Check for axis lock
        if node_id in TIER_AXIS_LOCKS:
            axis = np.array(TIER_AXIS_LOCKS[node_id])
            positions[i] = axis * radius
        else:
            # Random position at tier radius
            angle = rng.uniform(0, 2 * np.pi)
            positions[i] = np.array([
                radius * np.cos(angle),
                radius * np.sin(angle),
                0.0
            ])
    
    # Initialize velocities to zero
    velocities = np.zeros((n, 3), dtype=np.float32)
    forces = np.zeros((n, 3), dtype=np.float32)
    
    # Parse edges
    if edges:
        edge_sources = np.array([e[0] for e in edges], dtype=np.int32)
        edge_targets = np.array([e[1] for e in edges], dtype=np.int32)
        edge_weights = np.array([e[2] for e in edges], dtype=np.float32)
    else:
        edge_sources = np.array([], dtype=np.int32)
        edge_targets = np.array([], dtype=np.int32)
        edge_weights = np.array([], dtype=np.float32)
    
    return LayoutState(
        positions=positions,
        velocities=velocities,
        forces=forces,
        node_ids=node_ids,
        constraints=constraints or {},
        edge_sources=edge_sources,
        edge_targets=edge_targets,
        edge_weights=edge_weights
    )


def run_layout(
    state: LayoutState,
    config: LayoutConfig,
    node_tiers: np.ndarray,
    callback: Optional[callable] = None
) -> LayoutState:
    """
    Run layout to convergence or max iterations.
    
    Args:
        state: Initial layout state
        config: Layout configuration
        node_tiers: Tier values for each node
        callback: Optional callback(state, iteration) for progressive rendering
    """
    for i in range(config.max_iterations):
        state = layout_step(state, config, node_tiers)
        
        if callback and (i % config.render_every_n == 0 or state.converged):
            callback(state, i)
        
        if state.converged:
            logger.info(f"Layout converged at iteration {i}")
            break
    
    return state
