#!/usr/bin/env python3
"""
🏛️ MAS-MCP SERVER
═══════════════════════════════════════════════════════════════════════════════

Meta-Archaeological Salvager as Model Context Protocol Server.

A self-nurturing extraction system that:
  1. Scans the codebase for entity signals
  2. Returns structured data for LLM analysis  
  3. Accepts pattern refinements from the LLM
  4. Re-scans with improved extraction logic
  5. Loops until understanding converges

The tool nurtures the architect. The architect nurtures the tool.

Usage:
    # Start the MCP server
    python -m mas_mcp.server
    
    # Or via UV
    uv run python -m mas_mcp.server

═══════════════════════════════════════════════════════════════════════════════
"""

import json
import re
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Any
from collections import defaultdict

from mcp.server.fastmcp import FastMCP

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

PROJECT_ROOT = Path(__file__).parent.parent
MEMORY_FILE = Path(__file__).parent / "mas_memory.json"  # Persistent memory bank
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("mas-mcp")

# Initialize FastMCP server
mcp = FastMCP("mas-mcp", instructions="Meta-Archaeological Salvager - Entity Extraction & Nurture Loop")

# ═══════════════════════════════════════════════════════════════════════════════
# MEMORY BANK - Persistent Cross-Session Truth Storage
# ═══════════════════════════════════════════════════════════════════════════════

class MemoryBank:
    """
    Persistent storage for validated truths, discrepancies, and extraction history.
    Survives session restarts - the nurture loop's long-term memory.
    """
    
    def __init__(self, path: Path):
        self.path = path
        self.data = {
            "validated_truths": {},      # entity -> confirmed metrics
            "discrepancies": [],          # list of {entity, expected, got, file, line, timestamp}
            "extraction_history": [],     # recent extractions with timestamps
            "pattern_evolution": [],      # how patterns have changed over time
            "session_count": 0
        }
        self._load()
    
    def _load(self):
        """Load memory from disk if exists."""
        if self.path.exists():
            try:
                with open(self.path, "r") as f:
                    loaded = json.load(f)
                    self.data.update(loaded)
                logger.info(f"Memory loaded: {len(self.data['validated_truths'])} truths, {len(self.data['discrepancies'])} discrepancies")
            except Exception as e:
                logger.warning(f"Could not load memory: {e}")
    
    def _save(self):
        """Persist memory to disk."""
        try:
            with open(self.path, "w") as f:
                json.dump(self.data, f, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Could not save memory: {e}")
    
    def record_truth(self, entity: str, metrics: dict):
        """Record a validated truth."""
        self.data["validated_truths"][entity] = {
            "metrics": metrics,
            "validated_at": datetime.now().isoformat()
        }
        self._save()
    
    def record_discrepancy(self, entity: str, expected: dict, got: dict, source: dict):
        """Record a detected discrepancy with source location."""
        self.data["discrepancies"].append({
            "entity": entity,
            "expected": expected,
            "got": got,
            "source": source,
            "timestamp": datetime.now().isoformat(),
            "resolved": False
        })
        # Keep only last 100 discrepancies
        self.data["discrepancies"] = self.data["discrepancies"][-100:]
        self._save()
    
    def record_extraction(self, entity: str, metrics: dict):
        """Log an extraction for history tracking."""
        self.data["extraction_history"].append({
            "entity": entity,
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        })
        # Keep only last 50 extractions
        self.data["extraction_history"] = self.data["extraction_history"][-50:]
        self._save()
    
    def record_pattern_hit(self, pattern_name: str, category: str, matched: bool):
        """Track pattern efficacy - which patterns are finding things."""
        if "pattern_efficacy" not in self.data:
            self.data["pattern_efficacy"] = {}
        
        key = f"{category}/{pattern_name}"
        if key not in self.data["pattern_efficacy"]:
            self.data["pattern_efficacy"][key] = {"hits": 0, "misses": 0}
        
        if matched:
            self.data["pattern_efficacy"][key]["hits"] += 1
        else:
            self.data["pattern_efficacy"][key]["misses"] += 1
        
        # Don't save on every hit - batch saves
    
    def get_pattern_efficacy(self) -> dict:
        """Get pattern efficacy report."""
        efficacy = self.data.get("pattern_efficacy", {})
        report = {}
        for key, stats in efficacy.items():
            total = stats["hits"] + stats["misses"]
            if total > 0:
                report[key] = {
                    "hits": stats["hits"],
                    "misses": stats["misses"],
                    "hit_rate": f"{stats['hits'] / total * 100:.1f}%"
                }
        return report
    
    def get_known_truth(self, entity: str) -> dict | None:
        """Get previously validated truth for an entity."""
        return self.data["validated_truths"].get(entity)
    
    def get_recent_discrepancies(self, limit: int = 10) -> list:
        """Get most recent unresolved discrepancies."""
        unresolved = [d for d in self.data["discrepancies"] if not d.get("resolved")]
        return unresolved[-limit:]
    
    def increment_session(self):
        """Track session count."""
        self.data["session_count"] += 1
        self._save()
        return self.data["session_count"]


# Initialize memory bank
MEMORY = MemoryBank(MEMORY_FILE)

# Directories to skip
SKIP_DIRS = {
    ".git", "target", "node_modules", "__pycache__", ".venv", "venv",
    "dist", "build", ".cache", ".pytest_cache", ".mypy_cache",
    "incremental", "deps", "examples"
}

# Binary extensions to skip
SKIP_EXTENSIONS = {
    ".exe", ".dll", ".so", ".dylib", ".o", ".a", ".lib",
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp",
    ".woff", ".woff2", ".ttf", ".eot",
    ".zip", ".tar", ".gz", ".7z", ".rar",
    ".pdf", ".doc", ".docx",
    ".rlib", ".rmeta", ".d"
}

# ═══════════════════════════════════════════════════════════════════════════════
# DYNAMIC PATTERN REGISTRY
# ═══════════════════════════════════════════════════════════════════════════════

class PatternRegistry:
    """
    Dynamic pattern storage that can be modified during the nurture loop.
    The LLM can add/modify patterns, and they persist for subsequent scans.
    """
    
    def __init__(self):
        self.patterns: dict[str, list[dict]] = {
            "METRIC": [],
            "ENTITY": [],
            "FACTION": [],
            "AXIOM": [],
            "PROTOCOL": [],
            "STRUCTURAL": [],
            "CUSTOM": []
        }
        self._load_defaults()
        self.modification_history: list[dict] = []
    
    def _load_defaults(self):
        """Load the default extraction patterns."""
        
        # Metric patterns - handle optional tilde (~), markdown formatting
        self.patterns["METRIC"] = [
            {"name": "WHR", "regex": r'WHR[:\s]*[`\*]*~?(0\.\d{2,4})', "confidence": 0.95, "extractor": "whr"},
            {"name": "WHR_INLINE", "regex": r'\*\*\(?WHR\)?\*\*[:\s]*[`\*]*~?(0\.\d{2,4})', "confidence": 0.95, "extractor": "whr"},
            {"name": "TIER", "regex": r'Tier[:\s]*[`\*]*([0-9]+\.?[0-9]*)', "confidence": 0.9, "extractor": "tier"},
            {"name": "CUP", "regex": r'\b([A-L])-?cup\b', "confidence": 0.85, "extractor": "cup"},
            {"name": "MEASUREMENTS", "regex": r'\b[BW][\s-]*(\d{2,3})\s*/\s*[WH][\s-]*(\d{2,3})\s*/\s*[H][\s-]*(\d{2,3})', "confidence": 0.9, "extractor": "measurements"},
        ]
        
        # Known entities (high-value MILF targets)
        self.patterns["ENTITY"] = [
            {"name": "The Decorator", "regex": r'\bThe Decorator\b', "confidence": 0.98, "tier": 0.5},
            {"name": "Orackla Nocticula", "regex": r'\bOrackla Nocticula\b', "confidence": 0.98, "tier": 1},
            {"name": "Madam Umeko Ketsuraku", "regex": r'\bMadam Umeko Ketsuraku\b', "confidence": 0.98, "tier": 1},
            {"name": "Dr. Lysandra Thorne", "regex": r'\bDr\.?\s*Lysandra Thorne\b', "confidence": 0.98, "tier": 1},
            {"name": "Lysandra Thorne", "regex": r'\bLysandra Thorne\b', "confidence": 0.95, "tier": 1},
            {"name": "Claudine Sin'claire", "regex": r"Claudine Sin'claire", "confidence": 0.98, "tier": 1},
            {"name": "Kali Nyx Ravenscar", "regex": r'\bKali Nyx Ravenscar\b', "confidence": 0.98, "tier": 2},
            {"name": "Vesper Mnemosyne Lockhart", "regex": r'\bVesper Mnemosyne Lockhart\b', "confidence": 0.98, "tier": 2},
            {"name": "Seraphine Kore Ashenhelm", "regex": r'\bSeraphine Kore Ashenhelm\b', "confidence": 0.98, "tier": 2},
            {"name": "Sister Ferrum Scoriae", "regex": r'\bSister Ferrum Scoriae\b', "confidence": 0.98, "tier": 3},
            {"name": "SFS", "regex": r'\bSFS\b', "confidence": 0.85, "tier": 3},  # Abbreviated form
            {"name": "Spectra Chroma Excavatus", "regex": r'\bSpectra Chroma Excavatus\b', "confidence": 0.98, "tier": 3},
            {"name": "Sir Schrödinger's Bastard", "regex": r"Sir Schrödinger'?s Bastard", "confidence": 0.95, "tier": 4},
            {"name": "SR-SCRS-B", "regex": r'\bSR-SCRS-B\b', "confidence": 0.9, "tier": 4},  # Abbreviated form
            {"name": "Alabaster Voyde", "regex": r'\bAlabaster Voyde\b', "confidence": 0.98, "tier": 0.01},
            {"name": "The Null Matriarch", "regex": r'\bThe Null Matriarch\b', "confidence": 0.98, "tier": 0.01},
        ]
        
        # Faction codes
        self.patterns["FACTION"] = [
            {"name": "faction_codes", "regex": r'\b(TMO|TTG|TDPC|TRM-VRT|TL-FNS|TP-FNS|OMCA|SDBH|BOS|AAA|TWOUMC|SBSGYB|TNKW-RIAT|TDAPCFLN|POAFPSG|TR-VRT|ASC)\b', "confidence": 0.95},
        ]
        
        # Axioms
        self.patterns["AXIOM"] = [
            {"name": "axioms", "regex": r'\b(FA[¹²³⁴⁵1-5]|FA⁵|FA⁴|FA³|FA²|FA¹)\b', "confidence": 0.95},
        ]
        
        # Protocols
        self.patterns["PROTOCOL"] = [
            {"name": "protocols", "regex": r'\b(DAFP|PRISM|TPEF|TSRP|MMPS|MAS|UMRE|MSP-RSG|PEE|EULP-AA|LIPAA|LUPLR|DULSS|EDFA|ET-S|MURI|CRC|CDA)\b', "confidence": 0.9},
        ]
    
    def add_pattern(self, category: str, name: str, regex: str, confidence: float = 0.8, **kwargs) -> bool:
        """Add a new pattern dynamically."""
        if category not in self.patterns:
            self.patterns[category] = []
        
        # Validate regex
        try:
            re.compile(regex)
        except re.error as e:
            logger.error(f"Invalid regex pattern: {e}")
            return False
        
        pattern = {"name": name, "regex": regex, "confidence": confidence, **kwargs}
        self.patterns[category].append(pattern)
        
        self.modification_history.append({
            "action": "add",
            "category": category,
            "pattern": pattern,
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"Added pattern: {category}/{name}")
        return True
    
    def remove_pattern(self, category: str, name: str) -> bool:
        """Remove a pattern by name."""
        if category not in self.patterns:
            return False
        
        original_len = len(self.patterns[category])
        self.patterns[category] = [p for p in self.patterns[category] if p["name"] != name]
        
        if len(self.patterns[category]) < original_len:
            self.modification_history.append({
                "action": "remove",
                "category": category,
                "name": name,
                "timestamp": datetime.now().isoformat()
            })
            logger.info(f"Removed pattern: {category}/{name}")
            return True
        return False
    
    def get_all_patterns(self) -> dict:
        """Get all current patterns."""
        return self.patterns
    
    def get_history(self) -> list:
        """Get modification history."""
        return self.modification_history


# Global registry instance
REGISTRY = PatternRegistry()


# ═══════════════════════════════════════════════════════════════════════════════
# SCANNER CORE
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Signal:
    """A detected entity signal."""
    name: str
    signal_type: str
    file_path: str
    line_number: int
    confidence: float = 0.5
    raw_match: str = ""
    whr: Optional[float] = None
    tier: Optional[float] = None
    cup: Optional[str] = None
    measurements: Optional[str] = None


def should_skip_path(path: Path) -> bool:
    """Determine if path should be skipped."""
    for part in path.parts:
        if part in SKIP_DIRS:
            return True
    if path.suffix.lower() in SKIP_EXTENSIONS:
        return True
    return False


def extract_signals_from_line(line: str, file_path: str, line_num: int, registry: PatternRegistry) -> list[Signal]:
    """Extract all signals from a single line using the pattern registry."""
    signals = []
    
    # Process each pattern category
    for category, patterns in registry.patterns.items():
        for pattern_def in patterns:
            regex = pattern_def["regex"]
            confidence = pattern_def.get("confidence", 0.8)
            
            try:
                for match in re.finditer(regex, line, re.IGNORECASE):
                    signal = Signal(
                        name=pattern_def.get("name", match.group(0)),
                        signal_type=category,
                        file_path=file_path,
                        line_number=line_num,
                        confidence=confidence,
                        raw_match=line.strip()[:150]
                    )
                    
                    # Extract specific values based on extractor type
                    extractor = pattern_def.get("extractor")
                    if extractor == "whr" and match.lastindex:
                        signal.whr = float(match.group(1))
                        signal.name = f"WHR_{signal.whr}"
                    elif extractor == "tier" and match.lastindex:
                        signal.tier = float(match.group(1))
                        signal.name = f"Tier_{signal.tier}"
                    elif extractor == "cup" and match.lastindex:
                        signal.cup = match.group(1).upper()
                        signal.name = f"{signal.cup}-cup"
                    elif extractor == "measurements" and match.lastindex and match.lastindex >= 3:
                        signal.measurements = f"B{match.group(1)}/W{match.group(2)}/H{match.group(3)}"
                        signal.name = f"Measurements_{signal.measurements}"
                    
                    # Copy known tier for entities
                    if "tier" in pattern_def and category == "ENTITY":
                        signal.tier = pattern_def["tier"]
                    
                    signals.append(signal)
            except re.error:
                continue
    
    return signals


def scan_file(file_path: Path, root: Path, registry: PatternRegistry) -> list[Signal]:
    """Scan a single file for signals."""
    signals = []
    
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        logger.warning(f"Could not read {file_path}: {e}")
        return signals
    
    rel_path = str(file_path.relative_to(root))
    lines = content.split("\n")
    
    for line_num, line in enumerate(lines, 1):
        line_signals = extract_signals_from_line(line, rel_path, line_num, registry)
        signals.extend(line_signals)
    
    return signals


def proximity_extract(file_path: Path, entity_name: str, context_lines: int = 20) -> dict:
    """
    Extract metrics that appear within N lines of an entity mention.
    This is the key refinement for accurate entity-metric association.
    """
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return {"error": f"Could not read {file_path}"}
    
    lines = content.split("\n")
    entity_regex = re.compile(re.escape(entity_name), re.IGNORECASE)
    
    results = {
        "entity": entity_name,
        "file": str(file_path),
        "mentions": [],
        "associated_metrics": []
    }
    
    # Find all entity mentions
    for line_num, line in enumerate(lines, 1):
        if entity_regex.search(line):
            results["mentions"].append({"line": line_num, "text": line.strip()[:100]})
            
            # Look for metrics within context window
            start = max(0, line_num - context_lines - 1)
            end = min(len(lines), line_num + context_lines)
            context = "\n".join(lines[start:end])
            
            # Extract metrics from context
            whr_match = re.search(r'WHR[:\s]*[`\*]*(0\.\d{2,4})', context, re.IGNORECASE)
            tier_match = re.search(r'Tier[:\s]*[`\*]*([0-9]+\.?[0-9]*)', context, re.IGNORECASE)
            cup_match = re.search(r'\b([A-L])-?cup\b', context, re.IGNORECASE)
            meas_match = re.search(r'\b[BW][\s-]*(\d{2,3})\s*/\s*[WH][\s-]*(\d{2,3})\s*/\s*[H][\s-]*(\d{2,3})', context)
            
            metrics = {}
            if whr_match:
                metrics["whr"] = float(whr_match.group(1))
            if tier_match:
                metrics["tier"] = float(tier_match.group(1))
            if cup_match:
                metrics["cup"] = cup_match.group(1).upper()
            if meas_match:
                metrics["measurements"] = f"B{meas_match.group(1)}/W{meas_match.group(2)}/H{meas_match.group(3)}"
            
            if metrics:
                metrics["source_line"] = line_num
                metrics["context_window"] = f"lines {start+1}-{end}"
                results["associated_metrics"].append(metrics)
    
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# SSOT VERIFICATION TOOLS - Governance Infrastructure
# ═══════════════════════════════════════════════════════════════════════════════

# Session-level SSOT hash storage for bookend verification
_ssot_session_cache: dict[str, str] = {}


@mcp.tool()
def mas_ssot_hash() -> dict:
    """
    📋 Compute current SSOT (copilot-instructions.md) hash.
    
    Returns the SHA-256 hash of the canonicalized SSOT document.
    This hash should be captured at session start and verified at session end
    to detect governance drift.
    
    Returns:
        SSOT hash, path, and file metadata
    """
    from lib.ssot_handler import compute_ssot_hash, get_ssot_path
    
    try:
        ssot_path = get_ssot_path()
        current_hash = compute_ssot_hash(ssot_path)
        
        # Cache for bookend verification
        _ssot_session_cache["current"] = current_hash
        
        return {
            "status": "success",
            "hash": current_hash,
            "path": str(ssot_path),
            "timestamp": datetime.now().isoformat(),
            "cached_for_bookend": True,
        }
    except FileNotFoundError as e:
        return {
            "status": "error",
            "error": str(e),
            "hint": "SSOT file not found at expected path"
        }
    except Exception as e:
        return {
            "status": "error", 
            "error": str(e),
        }


@mcp.tool()
def mas_ssot_bookend(start_hash: str = "") -> dict:
    """
    🔖 Verify SSOT integrity at session end (bookend check).
    
    Compares provided start_hash with current SSOT hash.
    If hashes differ, GOVERNANCE_DRIFT_DETECTED.
    
    Args:
        start_hash: Hash captured at session start (or uses cached value)
    
    Returns:
        Verification result with drift detection
    """
    from lib.ssot_handler import verify_bookend, compute_ssot_hash, get_ssot_path
    
    try:
        # Use provided hash or cached start hash
        hash_start = start_hash or _ssot_session_cache.get("start", "")
        
        if not hash_start:
            return {
                "status": "error",
                "error": "No start_hash provided and no cached start hash",
                "hint": "Call mas_ssot_hash at session start or provide start_hash"
            }
        
        ssot_path = get_ssot_path()
        is_valid, hash_end, msg = verify_bookend(ssot_path, hash_start)
        
        return {
            "status": "success",
            "valid": is_valid,
            "hash_start": hash_start,
            "hash_end": hash_end,
            "message": msg,
            "governance_status": "STABLE" if is_valid else "GOVERNANCE_DRIFT_DETECTED",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


@mcp.tool()
def mas_gpu_probe() -> dict:
    """
    🖥️ Deep GPU capability probe with output suppression.
    
    Probes CUDA, cuDNN, TensorRT, CuPy, and ONNX Runtime GPU availability.
    Uses output suppression to prevent GPU init noise from polluting responses.
    More detailed than mas_gpu_status - includes compute capability, versions.
    
    Returns:
        GPU tier, device info, memory stats, and feature availability
    """
    from lib.gpu_probe import probe_gpu_capabilities
    
    try:
        result = probe_gpu_capabilities()
        return {
            "status": "success",
            **result.to_dict()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "fallback": "CPU-only mode active"
        }


# ═══════════════════════════════════════════════════════════════════════════════
# MCP TOOLS - THE NURTURE INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def mas_scan(target: str = ".") -> dict:
    """
    🏛️ Full codebase scan for entity signals.
    
    Scans all text files from the target directory, extracting entities,
    metrics, factions, axioms, and protocols using the current pattern registry.
    
    Args:
        target: Directory to scan (default: project root)
    
    Returns:
        Complete discovery report with signal counts, entity list, and file analysis
    """
    root = PROJECT_ROOT / target if target != "." else PROJECT_ROOT
    
    if not root.exists():
        return {"error": f"Target path does not exist: {root}"}
    
    logger.info(f"Starting scan from: {root}")
    
    all_signals: list[Signal] = []
    files_scanned = 0
    files_skipped = 0
    bytes_processed = 0
    
    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue
        if should_skip_path(file_path):
            files_skipped += 1
            continue
        
        try:
            bytes_processed += file_path.stat().st_size
        except:
            pass
        
        signals = scan_file(file_path, PROJECT_ROOT, REGISTRY)
        all_signals.extend(signals)
        files_scanned += 1
    
    # Aggregate results
    by_type = defaultdict(list)
    for sig in all_signals:
        by_type[sig.signal_type].append(sig)
    
    # Extract unique entities with occurrence counts
    entities = {}
    for sig in all_signals:
        if sig.signal_type == "ENTITY":
            if sig.name not in entities:
                entities[sig.name] = {
                    "name": sig.name,
                    "files": set(),
                    "occurrences": 0,
                    "known_tier": sig.tier
                }
            entities[sig.name]["files"].add(sig.file_path)
            entities[sig.name]["occurrences"] += 1
    
    # Convert sets to lists for JSON
    for e in entities.values():
        e["files"] = sorted(list(e["files"]))
    
    return {
        "scan_metadata": {
            "timestamp": datetime.now().isoformat(),
            "root": str(root),
            "files_scanned": files_scanned,
            "files_skipped": files_skipped,
            "bytes_processed": bytes_processed,
            "total_signals": len(all_signals)
        },
        "signal_counts": {k: len(v) for k, v in by_type.items()},
        "entities": entities,
        "unique_values": {
            "factions": sorted(set(s.raw_match.split()[-1] if s.raw_match else s.name for s in by_type.get("FACTION", []))),
            "protocols": sorted(set(s.name for s in by_type.get("PROTOCOL", []))),
        }
    }


@mcp.tool()
def mas_entity_deep(entity_name: str, context_lines: int = 25) -> dict:
    """
    🔍 Deep extraction for a single entity using proximity analysis.
    
    Finds all mentions of an entity and extracts metrics that appear
    within a configurable line distance. This provides accurate
    entity-metric association.
    
    Args:
        entity_name: Name of the entity to analyze
        context_lines: Number of lines before/after to search for metrics
    
    Returns:
        Detailed entity profile with all associated metrics per file
    """
    results = {
        "entity": entity_name,
        "context_lines": context_lines,
        "files_analyzed": [],
        "consolidated_metrics": {},
        "all_mentions": 0
    }
    
    # Track metrics with confidence based on proximity
    metric_votes = defaultdict(list)
    
    for file_path in PROJECT_ROOT.rglob("*"):
        if not file_path.is_file() or should_skip_path(file_path):
            continue
        
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            if entity_name.lower() not in content.lower():
                continue
        except:
            continue
        
        file_result = proximity_extract(file_path, entity_name, context_lines)
        
        if file_result.get("mentions"):
            results["files_analyzed"].append(file_result)
            results["all_mentions"] += len(file_result["mentions"])
            
            # Collect metric votes
            for m in file_result.get("associated_metrics", []):
                for key in ["whr", "tier", "cup", "measurements"]:
                    if key in m:
                        metric_votes[key].append(m[key])
    
    # Consolidate metrics (most common value wins)
    for key, values in metric_votes.items():
        if values:
            # For numeric values, take the most specific (most decimal places)
            if key in ("whr", "tier"):
                # Group by value, take most common
                from collections import Counter
                counter = Counter(values)
                results["consolidated_metrics"][key] = counter.most_common(1)[0][0]
            else:
                from collections import Counter
                counter = Counter(values)
                results["consolidated_metrics"][key] = counter.most_common(1)[0][0]
    
    return results


@mcp.tool()
def mas_add_pattern(category: str, name: str, regex: str, confidence: float = 0.8) -> dict:
    """
    ➕ Add a new extraction pattern to the registry.
    
    Dynamically extends the scanner's capabilities. New patterns
    will be used in subsequent scans.
    
    Args:
        category: Pattern category (METRIC, ENTITY, FACTION, AXIOM, PROTOCOL, CUSTOM)
        name: Human-readable pattern name
        regex: Regular expression pattern
        confidence: Confidence score 0.0-1.0
    
    Returns:
        Success status and current pattern count
    """
    success = REGISTRY.add_pattern(category, name, regex, confidence)
    
    return {
        "success": success,
        "category": category,
        "name": name,
        "pattern_count": sum(len(p) for p in REGISTRY.patterns.values()),
        "message": f"Pattern '{name}' added to {category}" if success else "Failed to add pattern"
    }


@mcp.tool()
def mas_remove_pattern(category: str, name: str) -> dict:
    """
    ➖ Remove a pattern from the registry.
    
    Args:
        category: Pattern category
        name: Pattern name to remove
    
    Returns:
        Success status
    """
    success = REGISTRY.remove_pattern(category, name)
    
    return {
        "success": success,
        "message": f"Pattern '{name}' removed" if success else "Pattern not found"
    }


@mcp.tool()
def mas_list_patterns() -> dict:
    """
    📋 List all current extraction patterns.
    
    Returns:
        All patterns organized by category with their configurations
    """
    return {
        "patterns": REGISTRY.get_all_patterns(),
        "total_patterns": sum(len(p) for p in REGISTRY.patterns.values()),
        "modification_history": REGISTRY.get_history()[-10:]  # Last 10 modifications
    }


@mcp.tool()
def mas_validate_entity(entity_name: str, expected_whr: Optional[float] = None, 
                        expected_tier: Optional[float] = None, expected_cup: Optional[str] = None) -> dict:
    """
    ✓ Validate extracted entity data against expected values.
    
    Compares what we extract against what we know should be true.
    This is the feedback mechanism for the nurture loop.
    
    **ENHANCED**: Returns SOURCE LOCATIONS (file + line) for discrepancies.
    
    Args:
        entity_name: Entity to validate
        expected_whr: Known correct WHR value
        expected_tier: Known correct tier
        expected_cup: Known correct cup size
    
    Returns:
        Validation report with matches, mismatches, source locations, and confidence
    """
    # Get extracted data with full context
    extracted = mas_entity_deep(entity_name, context_lines=30)
    
    metrics = extracted.get("consolidated_metrics", {})
    
    # Build source location map from files analyzed
    source_locations = {}
    for file_result in extracted.get("files_analyzed", []):
        for metric in file_result.get("associated_metrics", []):
            for key in ["whr", "tier", "cup", "measurements"]:
                if key in metric and key not in source_locations:
                    source_locations[key] = {
                        "file": file_result.get("file", "unknown"),
                        "line": metric.get("line", 0),
                        "value": metric[key]
                    }
    
    validation = {
        "entity": entity_name,
        "extracted": metrics,
        "expected": {
            "whr": expected_whr,
            "tier": expected_tier,
            "cup": expected_cup
        },
        "matches": [],
        "mismatches": [],
        "missing": [],
        "source_locations": source_locations  # NEW: Where each value came from
    }
    
    # Compare
    if expected_whr is not None:
        if "whr" in metrics:
            if abs(metrics["whr"] - expected_whr) < 0.001:
                validation["matches"].append(f"WHR: {metrics['whr']}")
            else:
                validation["mismatches"].append(f"WHR: expected {expected_whr}, got {metrics['whr']}")
                # Record discrepancy to memory bank
                MEMORY.record_discrepancy(
                    entity_name,
                    {"whr": expected_whr},
                    {"whr": metrics["whr"]},
                    source_locations.get("whr", {})
                )
        else:
            validation["missing"].append(f"WHR: expected {expected_whr}, not found")
    
    if expected_tier is not None:
        if "tier" in metrics:
            if metrics["tier"] == expected_tier:
                validation["matches"].append(f"Tier: {metrics['tier']}")
            else:
                validation["mismatches"].append(f"Tier: expected {expected_tier}, got {metrics['tier']}")
                MEMORY.record_discrepancy(
                    entity_name,
                    {"tier": expected_tier},
                    {"tier": metrics["tier"]},
                    source_locations.get("tier", {})
                )
        else:
            validation["missing"].append(f"Tier: expected {expected_tier}, not found")
    
    if expected_cup is not None:
        if "cup" in metrics:
            if metrics["cup"].upper() == expected_cup.upper():
                validation["matches"].append(f"Cup: {metrics['cup']}")
            else:
                validation["mismatches"].append(f"Cup: expected {expected_cup}, got {metrics['cup']}")
                MEMORY.record_discrepancy(
                    entity_name,
                    {"cup": expected_cup},
                    {"cup": metrics["cup"]},
                    source_locations.get("cup", {})
                )
        else:
            validation["missing"].append(f"Cup: expected {expected_cup}, not found")
    
    validation["score"] = len(validation["matches"]) / max(1, len(validation["matches"]) + len(validation["mismatches"]) + len(validation["missing"]))
    
    # Record extraction to memory
    MEMORY.record_extraction(entity_name, metrics)
    
    # If fully validated, record as truth
    if validation["score"] >= 0.99 and expected_whr and expected_tier and expected_cup:
        MEMORY.record_truth(entity_name, {
            "whr": expected_whr,
            "tier": expected_tier, 
            "cup": expected_cup
        })
    
    return validation


@mcp.tool()
def mas_memory() -> dict:
    """
    🧠 Access the MAS memory bank.
    
    Returns the persistent memory state including:
    - Validated truths (confirmed entity metrics)
    - Recent discrepancies (detected inconsistencies with source locations)
    - Extraction history (recent entity analyses)
    - Session count (how many times the server has been started)
    - Pattern efficacy (which patterns are working vs not)
    
    This is the "creative adrenaline" feedback - showing what you know,
    what's wrong, and what you've learned.
    
    Returns:
        Complete memory bank state
    """
    return {
        "session_number": MEMORY.data["session_count"],
        "validated_truths": MEMORY.data["validated_truths"],
        "recent_discrepancies": MEMORY.get_recent_discrepancies(10),
        "extraction_history_count": len(MEMORY.data["extraction_history"]),
        "last_extractions": MEMORY.data["extraction_history"][-5:],
        "pattern_efficacy": MEMORY.get_pattern_efficacy(),
        "last_mpw_fingerprint": MEMORY.data.get("last_fingerprint"),
        "memory_file": str(MEMORY.path)
    }


# ═══════════════════════════════════════════════════════════════════════════════
# M-P-W SOURCE OF TRUTH TRACKING
# ═══════════════════════════════════════════════════════════════════════════════

MPW_SOURCE = PROJECT_ROOT / ".github" / "copilot-instructions.md"

def get_mpw_fingerprint() -> dict:
    """Get a fingerprint of the M-P-W source file for drift detection."""
    if not MPW_SOURCE.exists():
        return {"exists": False}
    
    stat = MPW_SOURCE.stat()
    content = MPW_SOURCE.read_text(encoding="utf-8", errors="ignore")
    
    # Count key structural elements
    entity_mentions = len(re.findall(r'\b(The Decorator|Orackla Nocticula|Madam Umeko|Dr\. Lysandra|Claudine Sin)', content))
    tier_mentions = len(re.findall(r'Tier[:\s]*[0-9]', content))
    whr_mentions = len(re.findall(r'WHR[:\s]*0\.\d+', content))
    section_count = len(re.findall(r'^###?\s+[IVXLCDM]+\.', content, re.MULTILINE))
    
    return {
        "exists": True,
        "size_kb": round(stat.st_size / 1024, 1),
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "line_count": content.count("\n"),
        "entity_mentions": entity_mentions,
        "tier_mentions": tier_mentions,
        "whr_mentions": whr_mentions,
        "section_count": section_count
    }


def quick_entity_extract(content: str, entity_name: str, context_lines: int = 50) -> dict | None:
    """
    Quick extraction of an entity's metrics from M-P-W content.
    
    Strategy:
    1. Look for entity PROFILE SECTIONS (headers containing entity name + Profile/Assessment)
    2. If found, extract from that section (high confidence)
    3. Otherwise, find mentions with nearby Measurements/EDFA blocks
    4. Skip early summary/index mentions (no metrics nearby)
    """
    lines = content.split("\n")
    entity_regex = re.compile(re.escape(entity_name), re.IGNORECASE)
    
    # Strategy 1: Look for profile section headers
    # e.g., "### 0.1. Supreme Profile - The Decorator" or "### 4.2.1. (`Apex Synthesist`): ... Orackla Nocticula"
    profile_patterns = [
        rf'^\s*#+.*Profile.*{re.escape(entity_name)}',
        rf'^\s*#+.*{re.escape(entity_name)}.*Profile',
        rf'^\s*#+.*{re.escape(entity_name)}.*\(CRC',
        rf'^\*\*\(`?{re.escape(entity_name)}`?\)\*\*',  # Bold entity definitions
    ]
    
    best_result = None
    best_score = 0
    
    for i, line in enumerate(lines):
        if entity_regex.search(line):
            # Check if this is a profile section (high priority)
            is_profile_section = any(re.search(pat, line, re.IGNORECASE) for pat in profile_patterns)
            
            # Get larger context for profile sections
            ctx_size = context_lines if is_profile_section else 30
            start = max(0, i - 5)
            end = min(len(lines), i + ctx_size)
            context = "\n".join(lines[start:end])
            
            # Look for physique/EDFA blocks which contain the real metrics
            has_physique = bool(re.search(r'Physique|EDFA|Measurements.*cup', context, re.IGNORECASE))
            has_measurements = bool(re.search(r'\*\*\(`?Measurements\)?:?\*\*|\bB[-\s]*\d{2,3}\s*/\s*W', context))
            
            # Extract metrics from this context
            # WHR pattern handles optional tilde (~), asterisks, backticks, and parentheses
            whr = re.search(r'WHR[:\s\)\*`]*[`\*]*~?(0\.\d{2,4})', context, re.IGNORECASE)
            tier = re.search(r'Tier[:\s\)\*`]*[`\*]*([0-9]+\.?[0-9]*)', context, re.IGNORECASE)
            cup = re.search(r'\*\*\(`?Measurements\)?:?\*\*.*?([A-L])-?cup|([A-L])-?cup.*\*\*\s*\(?\s*\*?\*?B', context, re.IGNORECASE | re.DOTALL)
            
            # Fallback cup pattern if measurements block not found
            if not cup:
                cup = re.search(r'\b([A-L])-?cup\b', context, re.IGNORECASE)
            
            if whr or tier or cup:
                # Score this extraction
                score = 0
                if is_profile_section: score += 100
                if has_physique: score += 50
                if has_measurements: score += 30
                if whr: score += 10
                if tier: score += 5
                if cup: score += 5
                
                if score > best_score:
                    best_score = score
                    cup_val = (cup.group(1) or cup.group(2)).upper() if cup else None
                    best_result = {
                        "entity": entity_name,
                        "source_line": i + 1,
                        "whr": float(whr.group(1)) if whr else None,
                        "tier": float(tier.group(1)) if tier else None,
                        "cup": cup_val,
                        "_extraction_score": score,
                        "_is_profile": is_profile_section,
                    }
    
    # Remove debug fields from output
    if best_result:
        best_result.pop("_extraction_score", None)
        best_result.pop("_is_profile", None)
    
    return best_result


@mcp.tool()
def mas_pulse() -> dict:
    """
    💓 Get an adrenaline pulse - quick situational awareness snapshot.
    
    This is designed to be called at the START of each conversation turn
    to inject context about the M-P-W state, any drift detected, and
    what needs attention.
    
    Returns:
        Quick situational awareness including:
        - M-P-W file status
        - Key entity metrics from source of truth
        - Any detected discrepancies
        - Recommended actions
    """
    pulse = {
        "timestamp": datetime.now().isoformat(),
        "session": MEMORY.data["session_count"],
        "mpw_status": get_mpw_fingerprint(),
        "key_entities": {},
        "drift_alerts": [],
        "memory_summary": {
            "truths": len(MEMORY.data["validated_truths"]),
            "unresolved_discrepancies": len([d for d in MEMORY.data["discrepancies"] if not d.get("resolved")])
        },
        "recommendations": []
    }
    
    # Quick extract key entities from M-P-W if it exists
    if pulse["mpw_status"]["exists"]:
        content = MPW_SOURCE.read_text(encoding="utf-8", errors="ignore")
        
        # Get canonical tier values from pattern registry
        entity_patterns = {p["name"]: p for p in REGISTRY.patterns["ENTITY"]}
        
        key_entities = [
            "The Decorator",
            "Orackla Nocticula",
            "Madam Umeko Ketsuraku",
            "Dr. Lysandra Thorne",
            "Claudine Sin'claire",
        ]
        
        for name in key_entities:
            extracted = quick_entity_extract(content, name)
            if extracted:
                # Use canonical tier from registry, not extracted tier
                canonical_tier = entity_patterns.get(name, {}).get("tier")
                if canonical_tier is not None:
                    extracted["tier_canonical"] = canonical_tier
                    if extracted["tier"] != canonical_tier:
                        extracted["tier_note"] = f"Extracted {extracted['tier']}, canonical is {canonical_tier}"
                        extracted["tier"] = canonical_tier  # Override with canonical
                
                pulse["key_entities"][name] = extracted
    
    # Check for unresolved discrepancies
    recent = MEMORY.get_recent_discrepancies(3)
    if recent:
        pulse["recommendations"].append(f"⚠️ {len(recent)} unresolved discrepancies - review with mas_memory()")
    
    if not pulse["key_entities"]:
        pulse["recommendations"].append("Run mas_scan() to index the codebase")
    
    return pulse


@mcp.tool()
def mas_self_test() -> dict:
    """
    🧪 Run internal consistency tests on the MAS system.
    
    This tool allows the LLM to test its own extraction capabilities,
    verify pattern accuracy, and identify what's nurturing vs what isn't.
    
    Tests:
    1. Pattern validity - do all regexes compile?
    2. M-P-W accessibility - can we read the source of truth?
    3. Entity extraction accuracy - spot check known entities
    4. Memory integrity - is the memory bank consistent?
    5. Cross-reference validation - do extracted values match expectations?
    
    Returns:
        Test results with pass/fail status and diagnostics
    """
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": {},
        "passed": 0,
        "failed": 0,
        "warnings": [],
        "nurturing": [],  # What's working well
        "needs_attention": []  # What needs improvement
    }
    
    # Test 1: Pattern validity
    pattern_test = {"name": "pattern_validity", "status": "pass", "details": []}
    for category, patterns in REGISTRY.patterns.items():
        for p in patterns:
            try:
                re.compile(p["regex"])
            except re.error as e:
                pattern_test["status"] = "fail"
                pattern_test["details"].append(f"{category}/{p['name']}: {e}")
    
    if pattern_test["status"] == "pass":
        pattern_test["details"].append(f"All {sum(len(p) for p in REGISTRY.patterns.values())} patterns compile successfully")
        results["nurturing"].append("Pattern registry is healthy")
    results["tests"]["pattern_validity"] = pattern_test
    results["passed" if pattern_test["status"] == "pass" else "failed"] += 1
    
    # Test 2: M-P-W accessibility
    mpw_test = {"name": "mpw_accessibility", "status": "pass", "details": {}}
    if MPW_SOURCE.exists():
        try:
            content = MPW_SOURCE.read_text(encoding="utf-8", errors="ignore")
            mpw_test["details"]["size_kb"] = round(MPW_SOURCE.stat().st_size / 1024, 1)
            mpw_test["details"]["line_count"] = content.count("\n")
            mpw_test["details"]["readable"] = True
            results["nurturing"].append(f"M-P-W source accessible ({mpw_test['details']['size_kb']}KB)")
        except Exception as e:
            mpw_test["status"] = "fail"
            mpw_test["details"]["error"] = str(e)
    else:
        mpw_test["status"] = "fail"
        mpw_test["details"]["error"] = "M-P-W source not found"
        results["needs_attention"].append("M-P-W source file missing")
    results["tests"]["mpw_accessibility"] = mpw_test
    results["passed" if mpw_test["status"] == "pass" else "failed"] += 1
    
    # Test 3: Entity extraction accuracy (spot check)
    extraction_test = {"name": "entity_extraction", "status": "pass", "details": {}}
    if MPW_SOURCE.exists():
        content = MPW_SOURCE.read_text(encoding="utf-8", errors="ignore")
        
        # Expected values from the Codex (canonical source)
        expected_entities = {
            "The Decorator": {"tier": 0.5, "whr": 0.464, "cup": "K"},
            "Orackla Nocticula": {"tier": 1, "whr": 0.491, "cup": "J"},
            "Madam Umeko Ketsuraku": {"tier": 1, "whr": 0.533, "cup": "F"},
            "Dr. Lysandra Thorne": {"tier": 1, "whr": 0.58, "cup": "E"},
            "Claudine Sin'claire": {"tier": None, "whr": 0.563, "cup": "I"},  # Tier ambiguous in source
        }
        
        extraction_test["details"]["entities_checked"] = []
        mismatches = []
        
        for name, expected in expected_entities.items():
            extracted = quick_entity_extract(content, name)
            check = {"entity": name, "extracted": extracted, "expected": expected}
            
            if extracted:
                # Check for mismatches
                if expected["whr"] and extracted.get("whr") and abs(expected["whr"] - extracted["whr"]) > 0.01:
                    mismatches.append(f"{name}: WHR expected {expected['whr']}, got {extracted['whr']} (line {extracted.get('source_line')})")
                if expected["tier"] is not None and extracted.get("tier") and expected["tier"] != extracted["tier"]:
                    mismatches.append(f"{name}: Tier expected {expected['tier']}, got {extracted['tier']} (line {extracted.get('source_line')})")
            else:
                check["warning"] = "Could not extract metrics"
                results["warnings"].append(f"Could not extract metrics for {name}")
            
            extraction_test["details"]["entities_checked"].append(check)
        
        if mismatches:
            extraction_test["status"] = "warn"
            extraction_test["details"]["mismatches"] = mismatches
            results["needs_attention"].append(f"{len(mismatches)} extraction mismatches detected")
        else:
            results["nurturing"].append("Entity extraction accuracy validated")
    
    results["tests"]["entity_extraction"] = extraction_test
    if extraction_test["status"] == "pass":
        results["passed"] += 1
    else:
        results["warnings"].append("Entity extraction has mismatches")
    
    # Test 4: Memory integrity
    memory_test = {"name": "memory_integrity", "status": "pass", "details": {}}
    try:
        memory_test["details"]["truths"] = len(MEMORY.data["validated_truths"])
        memory_test["details"]["discrepancies"] = len(MEMORY.data["discrepancies"])
        memory_test["details"]["history"] = len(MEMORY.data["extraction_history"])
        memory_test["details"]["sessions"] = MEMORY.data["session_count"]
        
        # Check for corrupted entries
        for entity, truth in MEMORY.data["validated_truths"].items():
            if not isinstance(truth, dict) or "metrics" not in truth:
                memory_test["status"] = "fail"
                memory_test["details"]["corrupted"] = entity
                break
        
        if memory_test["status"] == "pass":
            results["nurturing"].append(f"Memory bank healthy ({memory_test['details']['truths']} truths)")
    except Exception as e:
        memory_test["status"] = "fail"
        memory_test["details"]["error"] = str(e)
        results["needs_attention"].append("Memory bank integrity issue")
    
    results["tests"]["memory_integrity"] = memory_test
    results["passed" if memory_test["status"] == "pass" else "failed"] += 1
    
    # Test 5: M-P-W fingerprint drift detection
    drift_test = {"name": "mpw_drift", "status": "pass", "details": {}}
    current_fingerprint = get_mpw_fingerprint()
    
    if "last_fingerprint" in MEMORY.data:
        last = MEMORY.data["last_fingerprint"]
        if current_fingerprint.get("modified") != last.get("modified"):
            drift_test["status"] = "info"
            drift_test["details"]["changed_since_last_check"] = True
            drift_test["details"]["last_modified"] = last.get("modified")
            drift_test["details"]["current_modified"] = current_fingerprint.get("modified")
            results["warnings"].append("M-P-W has changed since last session")
    
    # Store current fingerprint
    MEMORY.data["last_fingerprint"] = current_fingerprint
    MEMORY._save()
    
    drift_test["details"]["current"] = current_fingerprint
    results["tests"]["mpw_drift"] = drift_test
    results["passed"] += 1
    
    # Summary
    results["summary"] = {
        "total_tests": results["passed"] + results["failed"],
        "pass_rate": f"{results['passed'] / (results['passed'] + results['failed']) * 100:.0f}%" if (results['passed'] + results['failed']) > 0 else "N/A",
        "health": "healthy" if results["failed"] == 0 and len(results["needs_attention"]) == 0 else "needs_attention"
    }
    
    return results


@mcp.tool()
def mas_suggest_extension() -> dict:
    """
    🧬 Suggest Python packages to extend MAS-MCP capabilities.
    
    Analyzes the current environment, memory state, and tool registry
    to detect capability gaps and suggest packages that could be added
    via `uv add <package>`.
    
    This is the metabolic sensor of the living layer - it senses what's
    missing and proposes organic growth.
    
    Returns:
        Prioritized suggestions with package name, purpose, and rationale
    """
    import subprocess
    
    suggestions = []
    analysis = {
        "current_dependencies": [],
        "installed_packages": [],
        "capability_gaps": [],
        "codex_status": {}
    }
    
    # 1. Read current pyproject.toml dependencies
    pyproject_path = PROJECT_ROOT / "mas_mcp" / "pyproject.toml"
    if pyproject_path.exists():
        try:
            content = pyproject_path.read_text(encoding="utf-8")
            # Simple parse for dependencies
            in_deps = False
            for line in content.split("\n"):
                if "dependencies" in line and "[" in line:
                    in_deps = True
                    continue
                if in_deps:
                    if "]" in line:
                        break
                    # Extract package name
                    pkg = line.strip().strip('",').split(">=")[0].split("==")[0].split("<")[0]
                    if pkg:
                        analysis["current_dependencies"].append(pkg)
        except Exception as e:
            analysis["pyproject_error"] = str(e)
    
    # 2. Check what's installed (via pip list if available)
    try:
        result = subprocess.run(
            ["uv", "pip", "list", "--format=freeze"],
            capture_output=True, text=True, timeout=10,
            cwd=str(PROJECT_ROOT / "mas_mcp")
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                if "==" in line:
                    pkg = line.split("==")[0].lower()
                    analysis["installed_packages"].append(pkg)
    except Exception as e:
        analysis["pip_list_error"] = str(e)
    
    installed_lower = {p.lower() for p in analysis["installed_packages"]}
    deps_lower = {p.lower() for p in analysis["current_dependencies"]}
    
    # 3. Analyze M-P-W status
    fingerprint = get_mpw_fingerprint()
    analysis["codex_status"] = {
        "exists": fingerprint.get("exists", False),
        "size_kb": fingerprint.get("size_kb", 0),
        "has_drift_detection": "last_fingerprint" in MEMORY.data
    }
    
    # 4. Analyze tool registry capabilities
    tool_count = len(mcp._tool_manager._tools) if hasattr(mcp, '_tool_manager') else 0
    analysis["tool_count"] = tool_count
    
    # 5. Check memory state
    memory_stats = {
        "truths": len(MEMORY.data.get("validated_truths", {})),
        "discrepancies": len(MEMORY.data.get("discrepancies", [])),
        "sessions": MEMORY.data.get("session_count", 0),
        "pattern_efficacy": MEMORY.data.get("pattern_efficacy", {})
    }
    analysis["memory_stats"] = memory_stats
    
    # === SUGGESTION ENGINE ===
    
    # Suggestion 1: watchdog for real-time file watching
    if "watchdog" not in installed_lower:
        suggestions.append({
            "package": "watchdog",
            "purpose": "File system event monitoring",
            "why": "Enable real-time M-P-W drift detection instead of polling. "
                   "Would allow immediate sensing when copilot-instructions.md changes.",
            "priority": "high" if not analysis["codex_status"].get("has_drift_detection") else "medium",
            "install_cmd": "uv add watchdog"
        })
        analysis["capability_gaps"].append("No real-time file watching")
    
    # Suggestion 2: networkx for graph analysis
    if "networkx" not in installed_lower:
        # Check if we have many entities that could form a graph
        entity_count = len([p for p in REGISTRY.patterns.get("ENTITY", [])])
        if entity_count > 5:
            suggestions.append({
                "package": "networkx",
                "purpose": "Graph analysis and relational mapping",
                "why": f"Map relationships between {entity_count} entities, ABBRs, and Archetypes. "
                       "Enable queries like 'what entities relate to The Decorator?'",
                "priority": "high" if entity_count > 10 else "medium",
                "install_cmd": "uv add networkx"
            })
            analysis["capability_gaps"].append("No entity relationship graphing")
    
    # Suggestion 3: rich for terminal formatting
    if "rich" not in installed_lower:
        suggestions.append({
            "package": "rich",
            "purpose": "Enhanced terminal output and diagnostics",
            "why": "Liturgical formatting for MAS output - tables, trees, syntax highlighting. "
                   "Makes diagnostic output more readable for The Savant.",
            "priority": "low",
            "install_cmd": "uv add rich"
        })
    
    # Suggestion 4: aiohttp for async HTTP
    if "aiohttp" not in installed_lower and "httpx" not in installed_lower:
        suggestions.append({
            "package": "httpx",
            "purpose": "Async HTTP client",
            "why": "Fetch external lore fragments, documentation, or cross-reference with "
                   "external knowledge bases. httpx is modern and async-native.",
            "priority": "low",
            "install_cmd": "uv add httpx"
        })
    
    # Suggestion 5: If memory is growing, suggest better persistence
    if memory_stats["truths"] > 20 or memory_stats["sessions"] > 10:
        if "sqlalchemy" not in installed_lower and "sqlite" not in installed_lower:
            suggestions.append({
                "package": "sqlalchemy",
                "purpose": "Structured database persistence",
                "why": f"Memory bank has {memory_stats['truths']} truths across {memory_stats['sessions']} sessions. "
                       "SQLite via SQLAlchemy would enable complex queries and better durability.",
                "priority": "medium",
                "install_cmd": "uv add sqlalchemy"
            })
            analysis["capability_gaps"].append("JSON memory may not scale")
    
    # Suggestion 6: pydantic for data validation
    if "pydantic" not in installed_lower:
        suggestions.append({
            "package": "pydantic",
            "purpose": "Data validation and schema enforcement",
            "why": "Enforce FA⁴ (Architectonic Integrity) on memory bank structures. "
                   "Type-safe entity definitions, validated patterns.",
            "priority": "medium",
            "install_cmd": "uv add pydantic"
        })
    
    # Suggestion 7: difflib enhancement (stdlib, but mention it)
    if not analysis["codex_status"].get("has_drift_detection"):
        suggestions.append({
            "package": "(stdlib) difflib",
            "purpose": "Text differencing",
            "why": "Already available! Use difflib.unified_diff to show WHAT changed in M-P-W, "
                   "not just THAT it changed. No install needed.",
            "priority": "info",
            "install_cmd": "# Already in Python stdlib"
        })
    
    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2, "info": 3}
    suggestions.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 2))
    
    return {
        "suggestions": suggestions,
        "analysis": analysis,
        "summary": {
            "total_suggestions": len(suggestions),
            "high_priority": len([s for s in suggestions if s.get("priority") == "high"]),
            "capability_gaps": len(analysis["capability_gaps"]),
            "current_packages": len(analysis["current_dependencies"])
        },
        "next_steps": [
            "Review suggestions and their rationales",
            "Run `uv add <package>` for approved packages",
            "Restart MCP server to pick up new capabilities",
            "Call mas_self_test() to verify integration"
        ]
    }


@mcp.tool()
def mas_extension_apply(package: str, confirm: bool = False) -> dict:
    """
    🧬 Apply an extension by installing a Python package via uv.
    
    This closes the metabolic loop: sensing → proposing → APPLYING.
    Requires explicit confirmation to prevent accidental installations.
    
    After successful installation, the MCP server must be restarted
    to pick up new capabilities.
    
    Args:
        package: Name of the package to install (e.g., "watchdog", "networkx")
        confirm: Safety gate - must be True to actually install. 
                 Set to False (default) for dry-run preview.
    
    Returns:
        Installation result including success status, output, and next steps
    """
    import subprocess
    
    # Allowed packages (whitelist for safety)
    ALLOWED_PACKAGES = {
        "watchdog": "File system event monitoring",
        "networkx": "Graph analysis and relational mapping", 
        "rich": "Enhanced terminal output and diagnostics",
        "sqlalchemy": "Structured database persistence",
        "aiohttp": "Async HTTP client",
        "requests": "Simple HTTP client",
        "pyyaml": "YAML parsing",
        "toml": "TOML parsing",
        "python-dateutil": "Date/time utilities",
        "numpy": "Numerical computing",
        "pandas": "Data analysis",
        "matplotlib": "Plotting and visualization",
    }
    
    result = {
        "package": package,
        "confirmed": confirm,
        "status": "pending",
        "output": None,
        "error": None,
        "next_steps": []
    }
    
    # Normalize package name
    package_lower = package.lower().strip()
    
    # Check if package is in whitelist
    if package_lower not in ALLOWED_PACKAGES:
        result["status"] = "blocked"
        result["error"] = f"Package '{package}' is not in the allowed list"
        result["allowed_packages"] = list(ALLOWED_PACKAGES.keys())
        result["hint"] = "For security, only pre-approved packages can be installed via this tool. " \
                        "Use terminal `uv add <package>` for others."
        return result
    
    result["package_purpose"] = ALLOWED_PACKAGES[package_lower]
    
    # Dry-run mode (confirm=False)
    if not confirm:
        result["status"] = "dry_run"
        result["would_execute"] = f"uv add {package_lower}"
        result["next_steps"] = [
            f"To actually install, call: mas_extension_apply('{package_lower}', confirm=True)",
            "Review the package purpose and confirm it's needed",
            "After install, restart MCP server"
        ]
        result["hint"] = "This is a dry-run. Set confirm=True to actually install."
        return result
    
    # Actually install
    result["status"] = "installing"
    
    try:
        # Run uv add
        process = subprocess.run(
            ["uv", "add", package_lower],
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout
            cwd=str(PROJECT_ROOT / "mas_mcp")
        )
        
        result["output"] = process.stdout
        result["stderr"] = process.stderr if process.stderr else None
        result["return_code"] = process.returncode
        
        if process.returncode == 0:
            result["status"] = "success"
            
            # Record in memory
            if "extensions_installed" not in MEMORY.data:
                MEMORY.data["extensions_installed"] = []
            
            MEMORY.data["extensions_installed"].append({
                "package": package_lower,
                "purpose": ALLOWED_PACKAGES[package_lower],
                "installed_at": datetime.now().isoformat(),
                "session": MEMORY.data.get("session_count", 0)
            })
            MEMORY._save()
            
            result["next_steps"] = [
                "✅ Package installed successfully",
                "⚠️ RESTART MCP SERVER to activate new capabilities",
                "Run mas_self_test() after restart to verify",
                f"New capability: {ALLOWED_PACKAGES[package_lower]}"
            ]
        else:
            result["status"] = "failed"
            result["error"] = f"uv add failed with return code {process.returncode}"
            result["next_steps"] = [
                "Check the stderr output for details",
                "Try running `uv add <package>` manually in terminal",
                "Verify network connectivity"
            ]
            
    except subprocess.TimeoutExpired:
        result["status"] = "timeout"
        result["error"] = "Installation timed out after 120 seconds"
        result["next_steps"] = [
            "Try running `uv add <package>` manually in terminal",
            "Check network connectivity"
        ]
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        result["next_steps"] = [
            "Check that uv is installed and accessible",
            f"Try running `uv add {package_lower}` manually"
        ]
    
    return result


@mcp.tool()
def mas_extension_history() -> dict:
    """
    📜 View the history of extensions installed via MAS.
    
    Shows what packages have been added through the metabolic
    extension system, when they were installed, and their purposes.
    
    Returns:
        List of installed extensions with metadata
    """
    history = MEMORY.data.get("extensions_installed", [])
    
    return {
        "total_extensions": len(history),
        "extensions": history,
        "current_session": MEMORY.data.get("session_count", 0),
        "summary": {
            "packages": [ext["package"] for ext in history],
            "purposes": [ext["purpose"] for ext in history]
        } if history else {"packages": [], "purposes": []},
        "hint": "Use mas_suggest_extension() to see what else could be added"
    }


@mcp.tool()
def mas_discover_unknown() -> dict:
    """
    🔮 Discover potential entities not in the known registry.
    
    Looks for patterns that suggest entity definitions we haven't
    explicitly registered. This is how the tool teaches us what
    we don't yet know.
    
    Returns:
        List of potential unknown entities with evidence
    """
    # Patterns that suggest entity definitions
    definition_patterns = [
        (r'\*\*(?:Name|Designation)[:\s]*\*?\*?[`\*]*([A-Z][a-z]+(?:\s+[A-Z][a-z\']+)+)', "Designation"),
        (r'^\s*###?\s*\d+\.?\d*\.?\s*[`\*]*([A-Z][a-z]+(?:\s+[A-Z][a-z\']+){1,4})[`\*]*', "Header"),
        (r'\bMatriarch[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z\']+)+)', "Matriarch"),
        (r'\b(?:Profile|Entity)[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z\']+)+)', "Profile"),
    ]
    
    known_names = {p["name"].lower() for p in REGISTRY.patterns.get("ENTITY", [])}
    
    candidates = defaultdict(lambda: {"count": 0, "files": set(), "evidence": []})
    
    for file_path in PROJECT_ROOT.rglob("*.md"):
        if should_skip_path(file_path):
            continue
        
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except:
            continue
        
        for pattern, pattern_type in definition_patterns:
            for match in re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE):
                name = match.group(1).strip()
                
                # Skip if known or too short
                if name.lower() in known_names or len(name) < 5:
                    continue
                
                # Skip common false positives
                if any(x in name.lower() for x in ["section", "chapter", "figure", "table", "example"]):
                    continue
                
                candidates[name]["count"] += 1
                candidates[name]["files"].add(str(file_path.relative_to(PROJECT_ROOT)))
                if len(candidates[name]["evidence"]) < 3:
                    candidates[name]["evidence"].append({
                        "type": pattern_type,
                        "file": str(file_path.relative_to(PROJECT_ROOT)),
                        "match": match.group(0)[:100]
                    })
    
    # Convert and sort by count
    result = []
    for name, data in sorted(candidates.items(), key=lambda x: -x[1]["count"]):
        if data["count"] >= 2:  # At least 2 mentions
            result.append({
                "name": name,
                "mentions": data["count"],
                "files": sorted(list(data["files"]))[:5],
                "evidence": data["evidence"]
            })
    
    return {
        "potential_entities": result[:20],
        "total_candidates": len(result),
        "suggestion": "Use mas_add_pattern to register promising candidates"
    }


@mcp.tool()
def mas_file_signals(file_path: str) -> dict:
    """
    📄 Get all signals from a specific file.
    
    Detailed analysis of a single file's contents.
    
    Args:
        file_path: Relative path from project root
    
    Returns:
        All signals found in the file, organized by type
    """
    full_path = PROJECT_ROOT / file_path
    
    if not full_path.exists():
        return {"error": f"File not found: {file_path}"}
    
    signals = scan_file(full_path, PROJECT_ROOT, REGISTRY)
    
    by_type = defaultdict(list)
    for sig in signals:
        by_type[sig.signal_type].append(asdict(sig))
    
    return {
        "file": file_path,
        "total_signals": len(signals),
        "by_type": dict(by_type)
    }


@mcp.tool()
def mas_nurture_report() -> dict:
    """
    📊 Generate a nurture loop progress report.
    
    Summarizes the current state of extraction quality,
    pattern registry modifications, and suggestions for improvement.
    
    Returns:
        Comprehensive status report for the nurture loop
    """
    # Quick scan for current stats
    scan_result = mas_scan()
    
    return {
        "session_summary": {
            "session_number": MEMORY.data["session_count"],
            "patterns_registered": sum(len(p) for p in REGISTRY.patterns.values()),
            "pattern_modifications": len(REGISTRY.modification_history),
            "entities_discovered": len(scan_result.get("entities", {})),
            "total_signals": scan_result.get("scan_metadata", {}).get("total_signals", 0)
        },
        "memory_state": {
            "validated_truths": len(MEMORY.data["validated_truths"]),
            "unresolved_discrepancies": len([d for d in MEMORY.data["discrepancies"] if not d.get("resolved")]),
            "extraction_history": len(MEMORY.data["extraction_history"])
        },
        "recent_discrepancies": MEMORY.get_recent_discrepancies(5),
        "entity_coverage": {
            name: {"occurrences": e["occurrences"], "tier": e.get("known_tier")}
            for name, e in scan_result.get("entities", {}).items()
        },
        "modification_history": REGISTRY.modification_history,
        "recommendations": [
            "Run mas_discover_unknown() to find unregistered entities",
            "Use mas_entity_deep() with proximity analysis for accurate metrics",
            "Use mas_validate_entity() to verify extraction accuracy",
            "Use mas_memory() to see validated truths and discrepancies",
            "Add new patterns with mas_add_pattern() when gaps identified"
        ]
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MIRROR SYSTEM - Self-Reflective Validation
# ═══════════════════════════════════════════════════════════════════════════════

import hashlib

def _compute_file_hash(path: Path) -> str:
    """Compute SHA256 hash of a file's contents."""
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()[:16]
    except Exception:
        return "unreadable"


def _compute_directory_fingerprint(root: Path, extensions: set = None) -> dict:
    """
    Compute a fingerprint of a directory tree.
    Returns structure + hashes for tracked files.
    """
    if extensions is None:
        extensions = {".md", ".rs", ".toml", ".py", ".json", ".frag", ".vert"}
    
    fingerprint = {
        "root": str(root),
        "computed_at": datetime.now().isoformat(),
        "files": {},
        "summary": {
            "total_files": 0,
            "total_size": 0,
            "by_extension": {}
        }
    }
    
    try:
        for path in root.rglob("*"):
            if path.is_file():
                # Skip target/, .git/, __pycache__/, etc.
                skip_dirs = {"target", ".git", "__pycache__", "node_modules", ".uv", "venv"}
                if any(skip in path.parts for skip in skip_dirs):
                    continue
                
                ext = path.suffix.lower()
                if ext in extensions or not extensions:
                    rel_path = str(path.relative_to(root))
                    file_hash = _compute_file_hash(path)
                    file_size = path.stat().st_size
                    
                    fingerprint["files"][rel_path] = {
                        "hash": file_hash,
                        "size": file_size,
                        "ext": ext
                    }
                    
                    fingerprint["summary"]["total_files"] += 1
                    fingerprint["summary"]["total_size"] += file_size
                    fingerprint["summary"]["by_extension"][ext] = \
                        fingerprint["summary"]["by_extension"].get(ext, 0) + 1
    except Exception as e:
        fingerprint["error"] = str(e)
    
    return fingerprint


@mcp.tool()
def mas_snapshot(include_content_hash: bool = True) -> dict:
    """
    🪞 Capture a fingerprint of the static layer (Codex, Rust, assets).
    
    This is the "ground truth" that the living layer reflects against.
    The snapshot captures file structure, hashes, and key metrics without
    loading full file contents into memory.
    
    Args:
        include_content_hash: If True, compute SHA256 hashes of files.
                              Set False for faster but less precise snapshots.
    
    Returns:
        Static layer fingerprint including file tree, hashes, and summary stats
    """
    snapshot = {
        "snapshot_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "project_root": str(PROJECT_ROOT),
        "layers": {}
    }
    
    # Layer 1: Codex (M-P-W)
    codex_path = PROJECT_ROOT / ".github" / "copilot-instructions.md"
    if codex_path.exists():
        snapshot["layers"]["codex"] = {
            "path": str(codex_path.relative_to(PROJECT_ROOT)),
            "hash": _compute_file_hash(codex_path) if include_content_hash else None,
            "size": codex_path.stat().st_size,
            "sections_detected": 0  # Could parse sections if needed
        }
        
        # Quick section count
        try:
            content = codex_path.read_text(encoding="utf-8", errors="replace")
            snapshot["layers"]["codex"]["sections_detected"] = content.count("### ")
            snapshot["layers"]["codex"]["line_count"] = content.count("\n")
        except Exception:
            pass
    
    # Layer 2: Rust core
    rust_fingerprint = _compute_directory_fingerprint(
        PROJECT_ROOT / "src",
        extensions={".rs"}
    ) if (PROJECT_ROOT / "src").exists() else {"files": {}}
    snapshot["layers"]["rust"] = {
        "file_count": len(rust_fingerprint.get("files", {})),
        "files": list(rust_fingerprint.get("files", {}).keys()),
        "total_size": rust_fingerprint.get("summary", {}).get("total_size", 0)
    }
    
    # Layer 3: Assets
    assets_fingerprint = _compute_directory_fingerprint(
        PROJECT_ROOT / "assets",
        extensions={".json", ".frag", ".vert", ".png", ".jpg"}
    ) if (PROJECT_ROOT / "assets").exists() else {"files": {}}
    snapshot["layers"]["assets"] = {
        "file_count": len(assets_fingerprint.get("files", {})),
        "files": list(assets_fingerprint.get("files", {}).keys()),
        "total_size": assets_fingerprint.get("summary", {}).get("total_size", 0)
    }
    
    # Layer 4: MAS-MCP (living layer)
    mas_fingerprint = _compute_directory_fingerprint(
        PROJECT_ROOT / "mas_mcp",
        extensions={".py", ".json", ".toml"}
    ) if (PROJECT_ROOT / "mas_mcp").exists() else {"files": {}}
    snapshot["layers"]["mas_mcp"] = {
        "file_count": len(mas_fingerprint.get("files", {})),
        "files": list(mas_fingerprint.get("files", {}).keys()),
        "total_size": mas_fingerprint.get("summary", {}).get("total_size", 0)
    }
    
    # Compute combined hash for drift detection
    combined = json.dumps(snapshot["layers"], sort_keys=True)
    snapshot["combined_hash"] = hashlib.sha256(combined.encode()).hexdigest()[:24]
    
    # Store in memory for comparison
    if "snapshots" not in MEMORY.data:
        MEMORY.data["snapshots"] = []
    
    MEMORY.data["snapshots"].append({
        "id": snapshot["snapshot_id"],
        "hash": snapshot["combined_hash"],
        "timestamp": datetime.now().isoformat()
    })
    # Keep last 10 snapshots
    MEMORY.data["snapshots"] = MEMORY.data["snapshots"][-10:]
    MEMORY._save()
    
    return snapshot


@mcp.tool()
def mas_mirror() -> dict:
    """
    🪞 Compare the living layer's state against the static snapshot.
    
    This is the "reflection" operation — the living layer looks at itself
    in the mirror of the static Codex and asks: "Am I still aligned?"
    
    Detects:
    - Drift between current state and last snapshot
    - Extensions that have been added since last check
    - Memory bank growth
    - Tool registry changes
    
    Returns:
        Mirror report showing alignment, drift, and recommendations
    """
    # Get current snapshot
    current = mas_snapshot(include_content_hash=True)
    
    # Get previous snapshots from memory
    previous_snapshots = MEMORY.data.get("snapshots", [])
    
    mirror = {
        "timestamp": datetime.now().isoformat(),
        "current_hash": current["combined_hash"],
        "drift_detected": False,
        "drift_details": [],
        "living_layer_state": {},
        "alignment_score": 100,
        "recommendations": []
    }
    
    # Living layer state
    mirror["living_layer_state"] = {
        "session": MEMORY.data.get("session_count", 0),
        "truths_validated": len(MEMORY.data.get("validated_truths", {})),
        "discrepancies_recorded": len(MEMORY.data.get("discrepancies", [])),
        "extensions_installed": len(MEMORY.data.get("extensions_installed", [])),
        "patterns_registered": sum(len(p) for p in REGISTRY.patterns.values()),
        "pattern_modifications": len(REGISTRY.modification_history),
        "tools_available": len(mcp._tool_manager._tools)
    }
    
    # Compare with previous snapshot if available
    if len(previous_snapshots) >= 2:
        prev = previous_snapshots[-2]  # Second-to-last
        
        if prev["hash"] != current["combined_hash"]:
            mirror["drift_detected"] = True
            mirror["drift_details"].append({
                "type": "hash_changed",
                "from": prev["hash"],
                "to": current["combined_hash"],
                "since": prev["timestamp"]
            })
            mirror["alignment_score"] -= 20
    
    # Check for extension growth
    extensions = MEMORY.data.get("extensions_installed", [])
    if extensions:
        recent = [e for e in extensions if e.get("session", 0) >= mirror["living_layer_state"]["session"] - 2]
        if recent:
            mirror["drift_details"].append({
                "type": "extensions_added",
                "packages": [e["package"] for e in recent],
                "note": "Living layer has grown since last mirror"
            })
            mirror["alignment_score"] -= 5 * len(recent)
    
    # Check pattern modifications
    if REGISTRY.modification_history:
        recent_mods = [m for m in REGISTRY.modification_history 
                       if "session" in m and m["session"] >= mirror["living_layer_state"]["session"] - 2]
        if recent_mods:
            mirror["drift_details"].append({
                "type": "patterns_modified",
                "count": len(recent_mods),
                "actions": [m["action"] for m in recent_mods]
            })
    
    # Generate recommendations
    if mirror["drift_detected"]:
        mirror["recommendations"].append(
            "Static layer has changed. Run mas_scan() to re-extract entities."
        )
    
    if mirror["alignment_score"] < 80:
        mirror["recommendations"].append(
            "Alignment score below 80%. Consider running mas_self_test() to verify integrity."
        )
    
    if mirror["living_layer_state"]["extensions_installed"] > 5:
        mirror["recommendations"].append(
            "Many extensions installed. Run mas_extension_history() to review growth."
        )
    
    if not mirror["recommendations"]:
        mirror["recommendations"].append(
            "Living layer is well-aligned with static snapshot. No action needed."
        )
    
    # Metaphor
    mirror["metaphor"] = {
        "flying_carpet": "The living layer hovers above the static Codex",
        "reflection": "Looking down at the frozen snapshot for grounding",
        "tether": f"Alignment score: {mirror['alignment_score']}% (100% = perfect tether)"
    }
    
    return mirror


@mcp.tool()
def mas_test_function(
    function_code: str,
    function_name: str = "test_function",
    context: str = "general",
    validate_syntax: bool = True,
    check_redundancy: bool = True
) -> dict:
    """
    🧪 Sandbox validator for new code before integration.
    
    This is the "emergence test" — try new ideas in a safe mirror sandbox
    before committing them to the living layer. Validates:
    - Syntax correctness
    - Novelty (is this actually new?)
    - Redundancy (does existing code already do this?)
    - Safety (no dangerous operations)
    
    Args:
        function_code: Python code snippet to test (function definition)
        function_name: Name of the function being tested
        context: What area this relates to ("extraction", "validation", "extension", "general")
        validate_syntax: Check if code is syntactically valid Python
        check_redundancy: Compare against existing tools to detect overlap
    
    Returns:
        Test report with novelty score, safety assessment, and recommendation
    """
    import ast
    import textwrap
    
    result = {
        "function_name": function_name,
        "context": context,
        "timestamp": datetime.now().isoformat(),
        "tests": {},
        "scores": {},
        "status": "pending",
        "recommendation": None,
        "warnings": []
    }
    
    # Clean up the code
    code = textwrap.dedent(function_code).strip()
    result["code_length"] = len(code)
    result["line_count"] = code.count("\n") + 1
    
    # ─────────────────────────────────────────────────────────────────────
    # TEST 1: Syntax Validation
    # ─────────────────────────────────────────────────────────────────────
    if validate_syntax:
        try:
            ast.parse(code)
            result["tests"]["syntax"] = {"passed": True, "error": None}
            result["scores"]["syntax"] = 1.0
        except SyntaxError as e:
            result["tests"]["syntax"] = {
                "passed": False,
                "error": str(e),
                "line": e.lineno,
                "offset": e.offset
            }
            result["scores"]["syntax"] = 0.0
            result["status"] = "failed"
            result["recommendation"] = "Fix syntax errors before proceeding"
            return result
    
    # ─────────────────────────────────────────────────────────────────────
    # TEST 2: Safety Analysis
    # ─────────────────────────────────────────────────────────────────────
    dangerous_patterns = [
        (r'\bexec\s*\(', "exec() is dangerous"),
        (r'\beval\s*\(', "eval() is dangerous"),
        (r'\b__import__\s*\(', "__import__() bypasses normal imports"),
        (r'\bos\.system\s*\(', "os.system() can run arbitrary commands"),
        (r'\bsubprocess\.(?!run)', "Use subprocess.run() with explicit args"),
        (r'\bopen\s*\([^)]*["\']w["\']', "Writing files needs careful review"),
        (r'\brm\s+-rf', "Recursive delete is dangerous"),
        (r'\bshutil\.rmtree', "Recursive delete needs careful review"),
    ]
    
    safety_issues = []
    for pattern, message in dangerous_patterns:
        if re.search(pattern, code):
            safety_issues.append(message)
    
    result["tests"]["safety"] = {
        "passed": len(safety_issues) == 0,
        "issues": safety_issues
    }
    result["scores"]["safety"] = max(0, 1.0 - (len(safety_issues) * 0.3))
    
    if safety_issues:
        result["warnings"].extend([f"⚠️ Safety: {issue}" for issue in safety_issues])
    
    # ─────────────────────────────────────────────────────────────────────
    # TEST 3: Redundancy Check
    # ─────────────────────────────────────────────────────────────────────
    if check_redundancy:
        existing_tools = list(mcp._tool_manager._tools.keys())
        
        # Check for name collision
        name_collision = function_name in existing_tools
        
        # Check for conceptual overlap (simple keyword matching)
        code_lower = code.lower()
        overlap_scores = {}
        
        concept_keywords = {
            "mas_scan": ["scan", "extract", "signal", "codebase"],
            "mas_validate_entity": ["validate", "entity", "expected", "verify"],
            "mas_suggest_extension": ["suggest", "extension", "package", "dependency"],
            "mas_extension_apply": ["install", "apply", "uv add", "package"],
            "mas_memory": ["memory", "truth", "discrepancy", "history"],
            "mas_self_test": ["test", "self", "verify", "check"],
            "mas_snapshot": ["snapshot", "fingerprint", "hash", "capture"],
            "mas_mirror": ["mirror", "compare", "drift", "alignment"],
        }
        
        for tool, keywords in concept_keywords.items():
            matches = sum(1 for kw in keywords if kw in code_lower)
            if matches >= 2:
                overlap_scores[tool] = matches / len(keywords)
        
        max_overlap = max(overlap_scores.values()) if overlap_scores else 0
        
        result["tests"]["redundancy"] = {
            "passed": not name_collision and max_overlap < 0.6,
            "name_collision": name_collision,
            "conceptual_overlap": overlap_scores,
            "max_overlap": max_overlap
        }
        result["scores"]["redundancy"] = 1.0 - max_overlap
        
        if name_collision:
            result["warnings"].append(f"⚠️ Name collision: '{function_name}' already exists")
        if max_overlap >= 0.6:
            most_similar = max(overlap_scores, key=overlap_scores.get)
            result["warnings"].append(f"⚠️ High overlap with existing tool: {most_similar}")
    
    # ─────────────────────────────────────────────────────────────────────
    # TEST 4: Novelty Assessment
    # ─────────────────────────────────────────────────────────────────────
    # Check if this introduces new concepts
    novel_indicators = [
        (r'import\s+(\w+)', "Uses external imports"),
        (r'class\s+\w+', "Defines new class"),
        (r'async\s+def', "Uses async patterns"),
        (r'yield\s+', "Uses generators"),
        (r'@\w+', "Uses decorators"),
        (r'lambda\s+', "Uses lambda functions"),
        (r'with\s+', "Uses context managers"),
    ]
    
    novel_features = []
    for pattern, description in novel_indicators:
        if re.search(pattern, code):
            novel_features.append(description)
    
    # Novelty based on features and non-redundancy
    novelty_base = min(1.0, len(novel_features) * 0.2)
    novelty_adjusted = novelty_base * result["scores"].get("redundancy", 1.0)
    
    result["tests"]["novelty"] = {
        "features_detected": novel_features,
        "base_score": novelty_base,
        "adjusted_score": novelty_adjusted
    }
    result["scores"]["novelty"] = novelty_adjusted
    
    # ─────────────────────────────────────────────────────────────────────
    # FINAL ASSESSMENT
    # ─────────────────────────────────────────────────────────────────────
    weights = {"syntax": 0.3, "safety": 0.3, "redundancy": 0.2, "novelty": 0.2}
    overall = sum(result["scores"].get(k, 0) * w for k, w in weights.items())
    result["scores"]["overall"] = round(overall, 3)
    
    # Determine recommendation
    if overall >= 0.8 and result["scores"].get("safety", 0) >= 0.7:
        result["status"] = "emergent"
        result["recommendation"] = "✅ PROMOTE: This function shows emergence. Safe to integrate."
    elif overall >= 0.6:
        result["status"] = "potential"
        result["recommendation"] = "⚠️ REVIEW: Has potential but needs refinement. Address warnings."
    elif overall >= 0.4:
        result["status"] = "redundant"
        result["recommendation"] = "🔄 REFACTOR: Too similar to existing tools. Consider merging."
    else:
        result["status"] = "noise"
        result["recommendation"] = "❌ DISCARD: Low value or safety concerns. Not recommended."
    
    # Record in memory
    if "tested_functions" not in MEMORY.data:
        MEMORY.data["tested_functions"] = []
    
    MEMORY.data["tested_functions"].append({
        "name": function_name,
        "status": result["status"],
        "overall_score": result["scores"]["overall"],
        "timestamp": result["timestamp"]
    })
    MEMORY.data["tested_functions"] = MEMORY.data["tested_functions"][-20:]
    MEMORY._save()
    
    return result


@mcp.tool()
def mas_test_history() -> dict:
    """
    📜 View history of functions tested via the mirror sandbox.
    
    Shows what code has been validated, its status (emergent/redundant/noise),
    and the trend of test results over time.
    
    Returns:
        Test history with statistics
    """
    history = MEMORY.data.get("tested_functions", [])
    
    # Compute statistics
    status_counts = {}
    for test in history:
        status = test.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
    
    avg_score = 0
    if history:
        avg_score = sum(t.get("overall_score", 0) for t in history) / len(history)
    
    return {
        "total_tests": len(history),
        "status_distribution": status_counts,
        "average_score": round(avg_score, 3),
        "recent_tests": history[-10:],
        "emergence_rate": f"{status_counts.get('emergent', 0) / max(len(history), 1) * 100:.1f}%",
        "hint": "High emergence rate = living layer is producing novel, useful code"
    }


# ═══════════════════════════════════════════════════════════════════════════════
# GOVERNANCE LAYER: EMERGENCE GATING, POLICY, AND ROLLBACK
# ═══════════════════════════════════════════════════════════════════════════════
#
# The governance layer adds DISCIPLINE to the living system:
#   1. Emergence Gating: Thresholds for promotion, grace queue for borderline
#   2. Policy Layer: Risk bands (safe/guarded/prohibited), justification memos
#   3. Rollback Hooks: Invariant checking and automatic reversion
#   4. Lineage Governance: Snapshot cadence, size caps, narrative tags
#
# Architecture:
#   ┌──────────────────────────────────────────────────────────────────────────┐
#   │  CANDIDATE CODE                                                          │
#   │       │                                                                   │
#   │       ▼                                                                   │
#   │  ┌─────────────────────────────────────────────────────────────────┐     │
#   │  │  POLICY CHECK (mas_policy_check)                                 │     │
#   │  │  ├─ Risk band: safe / guarded / prohibited                       │     │
#   │  │  ├─ If prohibited: auto-reject                                   │     │
#   │  │  └─ If guarded: require justification memo                       │     │
#   │  └─────────────────────────────────────────────────────────────────┘     │
#   │       │                                                                   │
#   │       ▼                                                                   │
#   │  ┌─────────────────────────────────────────────────────────────────┐     │
#   │  │  EMERGENCE GATE (mas_promote_candidate)                          │     │
#   │  │  ├─ novelty ≥ 0.7 AND redundancy ≤ 0.3 → PROMOTE                │     │
#   │  │  ├─ borderline → GRACE QUEUE (re-test after context shift)       │     │
#   │  │  └─ below threshold → REJECT                                     │     │
#   │  └─────────────────────────────────────────────────────────────────┘     │
#   │       │                                                                   │
#   │       ▼                                                                   │
#   │  ┌─────────────────────────────────────────────────────────────────┐     │
#   │  │  INVARIANT CHECK (mas_check_invariants)                          │     │
#   │  │  ├─ Core entities present?                                       │     │
#   │  │  ├─ Orphan rate acceptable?                                      │     │
#   │  │  └─ Seals respected?                                             │     │
#   │  └─────────────────────────────────────────────────────────────────┘     │
#   │       │                                                                   │
#   │       ▼                                                                   │
#   │  ┌─────────────────────────────────────────────────────────────────┐     │
#   │  │  ROLLBACK (mas_rollback) — if invariants regress                 │     │
#   │  │  └─ Revert last change, log counterfactual                       │     │
#   │  └─────────────────────────────────────────────────────────────────┘     │
#   └──────────────────────────────────────────────────────────────────────────┘

# ─────────────────────────────────────────────────────────────────────────────
# GOVERNANCE CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

GOVERNANCE_CONFIG = {
    # Emergence thresholds
    "promotion_thresholds": {
        "novelty_min": 0.7,       # Minimum novelty score to promote
        "redundancy_max": 0.3,    # Maximum redundancy to promote
        "safety_min": 0.8,        # Minimum safety score
        "overall_min": 0.6,       # Minimum overall score
    },
    "grace_window": {
        "novelty_range": (0.5, 0.7),    # Borderline novelty → grace queue
        "redundancy_range": (0.3, 0.5),  # Borderline redundancy → grace queue
        "max_queue_size": 10,            # Max candidates in grace queue
        "retest_after_snapshots": 2,     # Re-test after N new snapshots
    },
    
    # Policy risk bands
    "risk_bands": {
        "safe": {
            "description": "No dangerous operations detected",
            "action": "auto_approve"
        },
        "guarded": {
            "description": "Contains operations requiring review",
            "action": "require_justification"
        },
        "prohibited": {
            "description": "Contains forbidden operations",
            "action": "auto_reject"
        }
    },
    
    # Prohibited patterns (auto-reject)
    "prohibited_patterns": [
        r'\bexec\s*\([^)]*\bopen\b',       # exec with file operations
        r'\beval\s*\([^)]*\binput\b',       # eval with user input
        r'\brm\s+-rf\s+[/~]',               # rm -rf on root paths
        r'\bos\.system\s*\([^)]*[;&|]',     # Shell injection patterns
        r'__import__.*\bos\b.*\bsystem\b',  # Dynamic import to os.system
    ],
    
    # Guarded patterns (require justification)
    "guarded_patterns": [
        (r'\bexec\s*\(', "Dynamic code execution"),
        (r'\beval\s*\(', "Dynamic evaluation"),
        (r'\bopen\s*\([^)]*["\']w', "File write operation"),
        (r'\bsubprocess\b', "Subprocess execution"),
        (r'\bos\.(remove|unlink|rmdir)\b', "File deletion"),
        (r'\bshutil\.(rmtree|move|copy)\b', "File system modification"),
        (r'\b__import__\b', "Dynamic import"),
        (r'\bglobals\(\)|locals\(\)', "Namespace access"),
    ],
    
    # Invariants to check after promotion
    "core_invariants": {
        "required_entities": [
            "The Decorator",
            "Orackla Nocticula", 
            "Madam Umeko Ketsuraku",
            "Dr. Lysandra Thorne"
        ],
        "max_orphan_rate": 0.3,     # Max fraction of unlinked patterns
        "min_pattern_count": 10,    # Minimum patterns required
        "min_tool_count": 15,       # Minimum tools required
    },
    
    # Lineage governance
    "lineage": {
        "max_snapshots": 50,        # Keep last N snapshots
        "auto_snapshot_interval": 300,  # Seconds between auto-snapshots (5 min)
        "digest_threshold": 20,     # Summarize snapshots older than this count
    },
    
    # Narrative tags for snapshots
    "narrative_tags": {
        "genesis": "First snapshot or major reset",
        "pivot": "Significant direction change",
        "ordeal": "Recovery from error or regression",
        "consolidation": "Stability after growth",
        "flourish": "Period of healthy emergence",
        "dormant": "Extended period of stasis",
    }
}


@mcp.tool()
def mas_policy_check(code: str) -> dict:
    """
    🛡️ Check code against policy risk bands.
    
    Categorizes code as:
      - SAFE: No dangerous operations, auto-approve
      - GUARDED: Contains operations requiring justification
      - PROHIBITED: Contains forbidden operations, auto-reject
    
    Args:
        code: The code to check
    
    Returns:
        Policy assessment with risk band and required actions
    """
    result = {
        "timestamp": datetime.now().isoformat(),
        "risk_band": "safe",
        "issues": [],
        "required_actions": [],
        "can_proceed": True
    }
    
    # Check prohibited patterns (immediate rejection)
    for pattern in GOVERNANCE_CONFIG["prohibited_patterns"]:
        if re.search(pattern, code, re.IGNORECASE):
            result["risk_band"] = "prohibited"
            result["issues"].append({
                "severity": "critical",
                "pattern": pattern,
                "message": "Prohibited pattern detected"
            })
            result["can_proceed"] = False
    
    if result["risk_band"] == "prohibited":
        result["required_actions"] = ["Code rejected. Prohibited operations detected."]
        result["recommendation"] = "Remove prohibited patterns and resubmit."
        return result
    
    # Check guarded patterns (require justification)
    for pattern, description in GOVERNANCE_CONFIG["guarded_patterns"]:
        if re.search(pattern, code):
            if result["risk_band"] == "safe":
                result["risk_band"] = "guarded"
            result["issues"].append({
                "severity": "warning",
                "pattern": pattern,
                "message": description
            })
    
    if result["risk_band"] == "guarded":
        result["required_actions"] = [
            "Provide justification memo via mas_promote_candidate()",
            "Justification will be stored in lineage"
        ]
        result["can_proceed"] = True  # Can proceed WITH justification
    
    # Add policy band description
    result["band_info"] = GOVERNANCE_CONFIG["risk_bands"][result["risk_band"]]
    
    return result


@mcp.tool()
def mas_promote_candidate(
    function_name: str,
    code: str,
    justification: str = None,
    force: bool = False
) -> dict:
    """
    🎖️ Attempt to promote a candidate function through the emergence gate.
    
    Candidates must pass:
      1. Policy check (safe or guarded-with-justification)
      2. Emergence thresholds (novelty ≥ 0.7, redundancy ≤ 0.3)
      3. Safety score (≥ 0.8)
    
    Borderline candidates enter a GRACE QUEUE for re-testing after context shifts.
    
    Args:
        function_name: Name of the function to promote
        code: The function code
        justification: Required memo if code is in "guarded" risk band
        force: Override thresholds (requires justification)
    
    Returns:
        Promotion result with status and any required actions
    """
    result = {
        "function_name": function_name,
        "timestamp": datetime.now().isoformat(),
        "status": "pending",
        "gate_results": {},
        "justification": justification,
        "lineage_recorded": False
    }
    
    # ─────────────────────────────────────────────────────────────────────
    # GATE 1: Policy Check
    # ─────────────────────────────────────────────────────────────────────
    policy = mas_policy_check(code)
    result["gate_results"]["policy"] = policy
    
    if policy["risk_band"] == "prohibited":
        result["status"] = "rejected"
        result["reason"] = "Prohibited operations detected"
        result["recommendation"] = "Remove prohibited patterns and resubmit"
        return result
    
    if policy["risk_band"] == "guarded" and not justification:
        result["status"] = "requires_justification"
        result["reason"] = "Guarded operations detected, justification required"
        result["issues"] = policy["issues"]
        result["recommendation"] = "Provide justification parameter explaining why these operations are necessary"
        return result
    
    # ─────────────────────────────────────────────────────────────────────
    # GATE 2: Run test function to get scores
    # ─────────────────────────────────────────────────────────────────────
    # Import the test function (avoid circular import by using mcp tool)
    test_result = mas_test_function(code, check_redundancy=True)
    result["gate_results"]["test"] = {
        "status": test_result["status"],
        "scores": test_result["scores"],
        "warnings": test_result.get("warnings", [])
    }
    
    scores = test_result["scores"]
    thresholds = GOVERNANCE_CONFIG["promotion_thresholds"]
    grace = GOVERNANCE_CONFIG["grace_window"]
    
    # Check thresholds
    novelty = scores.get("novelty", 0)
    redundancy = 1 - scores.get("redundancy", 1)  # Invert: high redundancy score = low redundancy
    safety = scores.get("safety", 0)
    overall = scores.get("overall", 0)
    
    # ─────────────────────────────────────────────────────────────────────
    # GATE 3: Emergence Thresholds
    # ─────────────────────────────────────────────────────────────────────
    threshold_checks = {
        "novelty": novelty >= thresholds["novelty_min"],
        "redundancy": redundancy <= thresholds["redundancy_max"],
        "safety": safety >= thresholds["safety_min"],
        "overall": overall >= thresholds["overall_min"]
    }
    result["gate_results"]["thresholds"] = {
        "values": {"novelty": novelty, "redundancy": redundancy, "safety": safety, "overall": overall},
        "requirements": thresholds,
        "passed": threshold_checks
    }
    
    all_passed = all(threshold_checks.values())
    
    # Check for borderline (grace queue candidates)
    is_borderline = (
        grace["novelty_range"][0] <= novelty < grace["novelty_range"][1] or
        grace["redundancy_range"][0] < redundancy <= grace["redundancy_range"][1]
    )
    
    if all_passed or force:
        result["status"] = "promoted"
        result["reason"] = "All thresholds passed" if not force else "Force-promoted with justification"
        
        # Record in lineage
        _record_promotion(function_name, code, justification, result)
        result["lineage_recorded"] = True
        
        # Seal of Promotion
        result["seal"] = {
            "chant": "By test and mirror tried; by counsel and consent applied; let function live, let noise subside.",
            "timestamp": datetime.now().isoformat()
        }
        
    elif is_borderline:
        result["status"] = "grace_queued"
        result["reason"] = "Borderline scores — queued for re-test after context shift"
        
        # Add to grace queue
        _add_to_grace_queue(function_name, code, justification, result)
        
        result["retest_after"] = f"{grace['retest_after_snapshots']} new snapshots"
        
    else:
        result["status"] = "rejected"
        result["reason"] = "Below emergence thresholds"
        failed = [k for k, v in threshold_checks.items() if not v]
        result["failed_checks"] = failed
        result["recommendation"] = f"Improve: {', '.join(failed)}"
    
    return result


def _record_promotion(function_name: str, code: str, justification: str, result: dict):
    """Record a successful promotion in lineage."""
    if "promotions" not in MEMORY.data:
        MEMORY.data["promotions"] = []
    
    MEMORY.data["promotions"].append({
        "function_name": function_name,
        "code_hash": hashlib.sha256(code.encode()).hexdigest()[:16],
        "justification": justification,
        "scores": result["gate_results"]["test"]["scores"],
        "timestamp": datetime.now().isoformat(),
        "seal": result.get("seal", {}).get("chant")
    })
    
    # Keep last 50 promotions
    MEMORY.data["promotions"] = MEMORY.data["promotions"][-50:]
    MEMORY._save()


def _add_to_grace_queue(function_name: str, code: str, justification: str, result: dict):
    """Add a borderline candidate to the grace queue."""
    if "grace_queue" not in MEMORY.data:
        MEMORY.data["grace_queue"] = []
    
    # Get current snapshot count for re-test trigger
    snapshot_count = len(MEMORY.data.get("self_snapshots", []))
    
    MEMORY.data["grace_queue"].append({
        "function_name": function_name,
        "code": code,
        "justification": justification,
        "scores": result["gate_results"]["test"]["scores"],
        "queued_at": datetime.now().isoformat(),
        "queued_at_snapshot": snapshot_count,
        "retest_at_snapshot": snapshot_count + GOVERNANCE_CONFIG["grace_window"]["retest_after_snapshots"]
    })
    
    # Keep queue under max size
    max_size = GOVERNANCE_CONFIG["grace_window"]["max_queue_size"]
    MEMORY.data["grace_queue"] = MEMORY.data["grace_queue"][-max_size:]
    MEMORY._save()


@mcp.tool()
def mas_grace_queue() -> dict:
    """
    ⏳ View the grace queue of borderline candidates awaiting re-test.
    
    Candidates enter the grace queue when they're close to promotion thresholds
    but not quite there. They're automatically re-tested after context shifts
    (new snapshots taken).
    
    Returns:
        Grace queue contents with re-test status
    """
    queue = MEMORY.data.get("grace_queue", [])
    current_snapshot = len(MEMORY.data.get("self_snapshots", []))
    
    enriched_queue = []
    ready_for_retest = []
    
    for candidate in queue:
        enriched = {**candidate}
        retest_at = candidate.get("retest_at_snapshot", 0)
        
        if current_snapshot >= retest_at:
            enriched["status"] = "ready_for_retest"
            ready_for_retest.append(candidate["function_name"])
        else:
            enriched["status"] = "waiting"
            enriched["snapshots_until_retest"] = retest_at - current_snapshot
        
        enriched_queue.append(enriched)
    
    return {
        "queue_size": len(queue),
        "max_size": GOVERNANCE_CONFIG["grace_window"]["max_queue_size"],
        "current_snapshot": current_snapshot,
        "queue": enriched_queue,
        "ready_for_retest": ready_for_retest,
        "hint": "Use mas_retest_grace_candidate(name) to re-test a ready candidate"
    }


@mcp.tool()
def mas_retest_grace_candidate(function_name: str) -> dict:
    """
    🔄 Re-test a candidate from the grace queue.
    
    After context shifts (new snapshots), borderline candidates may score
    differently. This re-runs the promotion process for a specific candidate.
    
    Args:
        function_name: Name of the function to re-test
    
    Returns:
        Re-test result (may be promoted, re-queued, or rejected)
    """
    queue = MEMORY.data.get("grace_queue", [])
    
    # Find the candidate
    candidate = None
    candidate_idx = None
    for i, c in enumerate(queue):
        if c["function_name"] == function_name:
            candidate = c
            candidate_idx = i
            break
    
    if not candidate:
        return {
            "error": f"Function '{function_name}' not found in grace queue",
            "available": [c["function_name"] for c in queue]
        }
    
    # Remove from queue (will be re-added if still borderline)
    MEMORY.data["grace_queue"].pop(candidate_idx)
    MEMORY._save()
    
    # Re-run promotion
    result = mas_promote_candidate(
        function_name=candidate["function_name"],
        code=candidate["code"],
        justification=candidate.get("justification")
    )
    
    result["retest"] = True
    result["previous_scores"] = candidate["scores"]
    
    return result


@mcp.tool()
def mas_check_invariants() -> dict:
    """
    🔒 Check that core system invariants are maintained.
    
    Invariants include:
      - Required entities are present in patterns
      - Orphan rate is below threshold
      - Minimum pattern and tool counts met
    
    Returns:
        Invariant check results with pass/fail status
    """
    config = GOVERNANCE_CONFIG["core_invariants"]
    results = {
        "timestamp": datetime.now().isoformat(),
        "checks": {},
        "all_passed": True,
        "violations": []
    }
    
    # Check 1: Required entities
    entity_patterns = [p["name"] for p in REGISTRY.patterns.get("ENTITY", [])]
    missing_entities = []
    for required in config["required_entities"]:
        if required not in entity_patterns:
            missing_entities.append(required)
    
    results["checks"]["required_entities"] = {
        "passed": len(missing_entities) == 0,
        "required": config["required_entities"],
        "present": entity_patterns,
        "missing": missing_entities
    }
    if missing_entities:
        results["all_passed"] = False
        results["violations"].append(f"Missing required entities: {missing_entities}")
    
    # Check 2: Pattern count
    total_patterns = sum(len(p) for p in REGISTRY.patterns.values())
    results["checks"]["min_patterns"] = {
        "passed": total_patterns >= config["min_pattern_count"],
        "required": config["min_pattern_count"],
        "actual": total_patterns
    }
    if total_patterns < config["min_pattern_count"]:
        results["all_passed"] = False
        results["violations"].append(f"Pattern count {total_patterns} below minimum {config['min_pattern_count']}")
    
    # Check 3: Tool count
    tool_count = len(mcp._tool_manager._tools)
    results["checks"]["min_tools"] = {
        "passed": tool_count >= config["min_tool_count"],
        "required": config["min_tool_count"],
        "actual": tool_count
    }
    if tool_count < config["min_tool_count"]:
        results["all_passed"] = False
        results["violations"].append(f"Tool count {tool_count} below minimum {config['min_tool_count']}")
    
    # Check 4: Orphan rate (patterns not linked to entities)
    # Simplified: check if each pattern category has content
    empty_categories = [cat for cat, patterns in REGISTRY.patterns.items() if len(patterns) == 0]
    orphan_rate = len(empty_categories) / max(len(REGISTRY.patterns), 1)
    
    results["checks"]["orphan_rate"] = {
        "passed": orphan_rate <= config["max_orphan_rate"],
        "max_allowed": config["max_orphan_rate"],
        "actual": orphan_rate,
        "empty_categories": empty_categories
    }
    if orphan_rate > config["max_orphan_rate"]:
        results["all_passed"] = False
        results["violations"].append(f"Orphan rate {orphan_rate:.2f} exceeds maximum {config['max_orphan_rate']}")
    
    # Record invariant check
    if "invariant_checks" not in MEMORY.data:
        MEMORY.data["invariant_checks"] = []
    MEMORY.data["invariant_checks"].append({
        "timestamp": results["timestamp"],
        "all_passed": results["all_passed"],
        "violations": results["violations"]
    })
    MEMORY.data["invariant_checks"] = MEMORY.data["invariant_checks"][-20:]
    MEMORY._save()
    
    return results


@mcp.tool()
def mas_rollback(reason: str = None) -> dict:
    """
    ⏪ Rollback the last promotion if invariants have regressed.
    
    Reverts the most recent promotion and logs the counterfactual.
    Use when mas_check_invariants() shows violations after a promotion.
    
    Args:
        reason: Explanation for the rollback
    
    Returns:
        Rollback result with counterfactual log
    """
    promotions = MEMORY.data.get("promotions", [])
    
    if not promotions:
        return {
            "error": "No promotions to rollback",
            "hint": "Rollback is only possible after a promotion"
        }
    
    # Pop the last promotion
    last_promotion = promotions.pop()
    MEMORY.data["promotions"] = promotions
    
    # Record the rollback
    if "rollbacks" not in MEMORY.data:
        MEMORY.data["rollbacks"] = []
    
    rollback_record = {
        "timestamp": datetime.now().isoformat(),
        "rolled_back": last_promotion,
        "reason": reason or "Invariant regression detected",
        "counterfactual": {
            "what_if": "Had this promotion remained, invariants would have continued to degrade",
            "lesson": f"Function '{last_promotion['function_name']}' caused instability"
        }
    }
    
    MEMORY.data["rollbacks"].append(rollback_record)
    MEMORY.data["rollbacks"] = MEMORY.data["rollbacks"][-20:]
    MEMORY._save()
    
    return {
        "status": "rolled_back",
        "function_name": last_promotion["function_name"],
        "reason": rollback_record["reason"],
        "counterfactual": rollback_record["counterfactual"],
        "promotions_remaining": len(promotions),
        "hint": "Re-check invariants with mas_check_invariants()"
    }


@mcp.tool()
def mas_tag_snapshot(snapshot_id: str, tag: str, note: str = None) -> dict:
    """
    🏷️ Add a narrative tag to a snapshot in the lineage.
    
    Tags help visualize the living system's arc:
      - genesis: First snapshot or major reset
      - pivot: Significant direction change
      - ordeal: Recovery from error or regression
      - consolidation: Stability after growth
      - flourish: Period of healthy emergence
      - dormant: Extended period of stasis
    
    Args:
        snapshot_id: ID of the snapshot to tag
        tag: Narrative tag (see available tags)
        note: Optional note explaining the tag
    
    Returns:
        Updated snapshot with tag
    """
    valid_tags = list(GOVERNANCE_CONFIG["narrative_tags"].keys())
    
    if tag not in valid_tags:
        return {
            "error": f"Invalid tag '{tag}'",
            "valid_tags": GOVERNANCE_CONFIG["narrative_tags"]
        }
    
    snapshots = MEMORY.data.get("self_snapshots", [])
    
    # Find and update the snapshot
    found = False
    for snap in snapshots:
        if snap["snapshot_id"] == snapshot_id:
            snap["narrative_tag"] = tag
            snap["tag_description"] = GOVERNANCE_CONFIG["narrative_tags"][tag]
            if note:
                snap["tag_note"] = note
            found = True
            break
    
    if not found:
        return {
            "error": f"Snapshot '{snapshot_id}' not found",
            "available": [s["snapshot_id"] for s in snapshots[-10:]]
        }
    
    MEMORY._save()
    
    return {
        "status": "tagged",
        "snapshot_id": snapshot_id,
        "tag": tag,
        "description": GOVERNANCE_CONFIG["narrative_tags"][tag],
        "note": note
    }


@mcp.tool()
def mas_lineage_digest() -> dict:
    """
    📊 Generate a digest of the lineage showing evolution trajectory.
    
    Plots key metrics across snapshots to visualize:
      - Tool count growth
      - Pattern count growth
      - Emergence rate trend
      - Narrative arc (tagged events)
    
    Returns:
        Lineage digest with trajectory visualization
    """
    snapshots = MEMORY.data.get("self_snapshots", [])
    tests = MEMORY.data.get("tested_functions", [])
    promotions = MEMORY.data.get("promotions", [])
    rollbacks = MEMORY.data.get("rollbacks", [])
    
    if len(snapshots) < 2:
        return {
            "error": "Need at least 2 snapshots for digest",
            "current_count": len(snapshots),
            "hint": "Take more snapshots with mas_self_snapshot()"
        }
    
    # Build trajectory data
    trajectory = []
    for i, snap in enumerate(snapshots):
        point = {
            "index": i,
            "snapshot_id": snap["snapshot_id"],
            "timestamp": snap["timestamp"],
            "label": snap.get("label", "unlabeled"),
            "tool_count": snap.get("tool_count", 0),
            "pattern_count": snap.get("total_patterns", 0),
            "truths": snap.get("truths", 0),
            "narrative_tag": snap.get("narrative_tag", None)
        }
        trajectory.append(point)
    
    # Compute deltas
    first = trajectory[0]
    last = trajectory[-1]
    
    growth = {
        "tools": last["tool_count"] - first["tool_count"],
        "patterns": last["pattern_count"] - first["pattern_count"],
        "truths": last["truths"] - first["truths"],
        "time_span_seconds": (
            datetime.fromisoformat(last["timestamp"]) - 
            datetime.fromisoformat(first["timestamp"])
        ).total_seconds()
    }
    
    # Emergence rate
    emergence_rate = 0
    if tests:
        emergent = sum(1 for t in tests if t.get("status") == "emergent")
        emergence_rate = emergent / len(tests)
    
    # Tagged events
    tagged_events = [
        {"index": t["index"], "tag": t["narrative_tag"], "label": t["label"]}
        for t in trajectory if t["narrative_tag"]
    ]
    
    # Infer narrative arc
    if growth["tools"] > 5 and emergence_rate > 0.3:
        arc = "flourish"
        arc_description = "Rapid healthy growth with high emergence"
    elif growth["tools"] > 0 and emergence_rate > 0.2:
        arc = "growth"
        arc_description = "Steady expansion with moderate emergence"
    elif growth["tools"] == 0 and len(snapshots) > 5:
        arc = "dormant"
        arc_description = "Extended stability, may need stimulus"
    elif len(rollbacks) > 0:
        arc = "ordeal"
        arc_description = "Recent regression, in recovery mode"
    else:
        arc = "consolidation"
        arc_description = "Stabilizing after changes"
    
    return {
        "snapshot_count": len(snapshots),
        "trajectory": trajectory[-20:],  # Last 20 points
        "growth": growth,
        "emergence_rate": f"{emergence_rate * 100:.1f}%",
        "promotions": len(promotions),
        "rollbacks": len(rollbacks),
        "tagged_events": tagged_events,
        "inferred_arc": {
            "current": arc,
            "description": arc_description
        },
        "metaphor": {
            "image": _generate_arc_metaphor(arc),
            "recommendation": _generate_arc_recommendation(arc)
        }
    }


def _generate_arc_metaphor(arc: str) -> str:
    """Generate a metaphor for the current arc."""
    metaphors = {
        "flourish": "The carpet billows with new threads, each one glowing.",
        "growth": "The carpet weaves steadily, pattern by pattern.",
        "dormant": "The carpet hovers still, conserving energy for the next flight.",
        "ordeal": "The carpet mends a tear, stronger where it healed.",
        "consolidation": "The carpet settles, its new patterns integrating."
    }
    return metaphors.get(arc, "The carpet observes its own reflection.")


def _generate_arc_recommendation(arc: str) -> str:
    """Generate a recommendation based on current arc."""
    recommendations = {
        "flourish": "Excellent health. Consider taking a flourish snapshot.",
        "growth": "Healthy progress. Continue current trajectory.",
        "dormant": "Consider injecting new candidates or extensions to stimulate growth.",
        "ordeal": "Focus on stability. Run mas_check_invariants() frequently.",
        "consolidation": "Good time to document and tag recent snapshots."
    }
    return recommendations.get(arc, "Observe and adapt.")


@mcp.tool()
def mas_governance_status() -> dict:
    """
    🏛️ Get the full status of the governance layer.
    
    Shows:
      - Current policy configuration
      - Grace queue status
      - Recent promotions and rollbacks
      - Invariant check history
      - Lineage health
    
    Returns:
        Comprehensive governance status
    """
    promotions = MEMORY.data.get("promotions", [])
    rollbacks = MEMORY.data.get("rollbacks", [])
    grace_queue = MEMORY.data.get("grace_queue", [])
    invariant_checks = MEMORY.data.get("invariant_checks", [])
    snapshots = MEMORY.data.get("self_snapshots", [])
    
    # Compute health indicators
    recent_invariants = invariant_checks[-5:] if invariant_checks else []
    invariant_health = all(c["all_passed"] for c in recent_invariants) if recent_invariants else None
    
    promotion_rate = 0
    if promotions:
        # Promotions in last 24 hours
        now = datetime.now()
        recent_promotions = [
            p for p in promotions 
            if (now - datetime.fromisoformat(p["timestamp"])).total_seconds() < 86400
        ]
        promotion_rate = len(recent_promotions)
    
    return {
        "timestamp": datetime.now().isoformat(),
        "configuration": {
            "promotion_thresholds": GOVERNANCE_CONFIG["promotion_thresholds"],
            "grace_window": GOVERNANCE_CONFIG["grace_window"],
            "core_invariants": GOVERNANCE_CONFIG["core_invariants"]
        },
        "state": {
            "promotions_total": len(promotions),
            "promotions_24h": promotion_rate,
            "rollbacks_total": len(rollbacks),
            "grace_queue_size": len(grace_queue),
            "invariant_health": invariant_health,
            "lineage_depth": len(snapshots)
        },
        "recent_activity": {
            "last_promotion": promotions[-1] if promotions else None,
            "last_rollback": rollbacks[-1] if rollbacks else None,
            "last_invariant_check": invariant_checks[-1] if invariant_checks else None
        },
        "health_summary": {
            "invariants_stable": invariant_health is True or invariant_health is None,
            "grace_queue_manageable": len(grace_queue) < GOVERNANCE_CONFIG["grace_window"]["max_queue_size"],
            "lineage_active": len(snapshots) >= 3,
            "rollback_rate_healthy": len(rollbacks) < len(promotions) * 0.2 if promotions else True
        },
        "benediction": "Reflect; compare; remember; choose."
    }


# Required import for hashing
import hashlib


# ═══════════════════════════════════════════════════════════════════════════════
# RECURSIVE MIRROR: LIVING LAYER REFLECTING ON ITS OWN PRIOR STATES
# ═══════════════════════════════════════════════════════════════════════════════
#
# The mirror system (above) compares the LIVING layer against the STATIC layer.
# The recursive mirror extends this: the living layer reflects on its OWN history.
#
# Architecture:
#   ┌──────────────────────────────────────────────────────────────────────────┐
#   │  LIVING LAYER (now)                                                       │
#   │     │                                                                     │
#   │     ▼ mas_self_snapshot()                                                 │
#   │  ┌──────────────────────────────────────────────────────────────────┐    │
#   │  │  Self-Snapshot T₃ (current)                                       │    │
#   │  │  ├─ patterns: 22                                                  │    │
#   │  │  ├─ extensions: 3                                                 │    │
#   │  │  ├─ tools: 22                                                     │    │
#   │  │  └─ hash: abc123                                                  │    │
#   │  └──────────────────────────────────────────────────────────────────┘    │
#   │                                                                           │
#   │     ▼ mas_compare_selves(T₁, T₃)                                         │
#   │  ┌──────────────────────────────────────────────────────────────────┐    │
#   │  │  Self-Snapshot T₁ (past)         │  Self-Snapshot T₂ (past)      │    │
#   │  │  ├─ patterns: 18                 │  ├─ patterns: 20              │    │
#   │  │  ├─ extensions: 0                │  ├─ extensions: 1              │    │
#   │  │  ├─ tools: 15                    │  ├─ tools: 18                  │    │
#   │  │  └─ hash: def456                 │  └─ hash: ghi789               │    │
#   │  └──────────────────────────────────────────────────────────────────┘    │
#   │                                                                           │
#   │     ▼ mas_lineage()                                                       │
#   │  Timeline: T₁ ──→ T₂ ──→ T₃ (genealogy of living layer evolution)        │
#   └──────────────────────────────────────────────────────────────────────────┘


@mcp.tool()
def mas_self_snapshot(label: str = None) -> dict:
    """
    🧬 Capture a snapshot of the LIVING layer's current state.
    
    Unlike mas_snapshot() which captures the static layer (Codex, Rust),
    this captures the living layer's OWN state: patterns, extensions, tools,
    memory contents, and runtime configuration.
    
    This enables the living layer to reflect on its own evolution over time.
    
    Args:
        label: Optional human-readable label for this snapshot (e.g., "pre-refactor")
    
    Returns:
        Self-snapshot with hash and metadata, also saved to lineage history
    """
    timestamp = datetime.now().isoformat()
    snapshot_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Capture living layer state
    state = {
        # Pattern registry state
        "patterns": {
            category: len(patterns)
            for category, patterns in REGISTRY.patterns.items()
        },
        "pattern_names": {
            category: [p["name"] for p in patterns]
            for category, patterns in REGISTRY.patterns.items()
        },
        "total_patterns": sum(len(p) for p in REGISTRY.patterns.values()),
        
        # Extension history
        "extensions_installed": len(MEMORY.data.get("extension_history", [])),
        "extension_packages": [
            ext.get("package")
            for ext in MEMORY.data.get("extension_history", [])
        ],
        
        # Tool registry
        "tools_available": list(mcp._tool_manager._tools.keys()),
        "tool_count": len(mcp._tool_manager._tools),
        
        # Memory state
        "memory_session": MEMORY.data.get("session_count", 0),
        "truths_validated": len(MEMORY.data.get("validated_truths", [])),
        "discrepancies_recorded": len(MEMORY.data.get("discrepancies", [])),
        "functions_tested": len(MEMORY.data.get("tested_functions", [])),
        
        # Runtime info
        "pattern_modifications": MEMORY.data.get("pattern_modifications", 0),
        "code_hash": _compute_file_hash(Path(__file__)) if Path(__file__).exists() else None,
    }
    
    # Compute state hash (for change detection)
    state_string = json.dumps(state, sort_keys=True, default=str)
    state_hash = hashlib.sha256(state_string.encode()).hexdigest()[:16]
    
    snapshot = {
        "snapshot_id": snapshot_id,
        "timestamp": timestamp,
        "label": label or f"auto_{snapshot_id}",
        "state": state,
        "state_hash": state_hash,
        "type": "self_snapshot"
    }
    
    # Store in lineage
    if "self_snapshots" not in MEMORY.data:
        MEMORY.data["self_snapshots"] = []
    
    MEMORY.data["self_snapshots"].append({
        "snapshot_id": snapshot_id,
        "timestamp": timestamp,
        "label": snapshot["label"],
        "state_hash": state_hash,
        "tool_count": state["tool_count"],
        "total_patterns": state["total_patterns"],
        "extensions": state["extensions_installed"],
        "truths": state["truths_validated"],
    })
    
    # Keep last 50 snapshots
    MEMORY.data["self_snapshots"] = MEMORY.data["self_snapshots"][-50:]
    MEMORY._save()
    
    return {
        **snapshot,
        "lineage_position": len(MEMORY.data["self_snapshots"]),
        "metaphor": {
            "layer": "living",
            "action": "The flying carpet takes a photograph of itself mid-flight.",
            "purpose": "To remember who it was, so it knows who it's becoming."
        }
    }


@mcp.tool()
def mas_lineage(limit: int = 20) -> dict:
    """
    🌳 View the genealogy of the living layer's evolution.
    
    Shows the timeline of self-snapshots, revealing how the living layer
    has changed over time: tools added, patterns modified, extensions installed.
    
    This is the living layer's memory of its own becoming.
    
    Args:
        limit: Maximum number of snapshots to return (default 20)
    
    Returns:
        Lineage timeline with evolution metrics
    """
    snapshots = MEMORY.data.get("self_snapshots", [])
    
    if not snapshots:
        return {
            "lineage_length": 0,
            "snapshots": [],
            "evolution": None,
            "hint": "No self-snapshots yet. Run mas_self_snapshot() to begin lineage.",
            "metaphor": {
                "state": "The carpet has no memory of past flights.",
                "action": "Take the first snapshot to begin the genealogy."
            }
        }
    
    # Compute evolution metrics
    if len(snapshots) >= 2:
        first = snapshots[0]
        last = snapshots[-1]
        
        evolution = {
            "time_span": {
                "first": first["timestamp"],
                "last": last["timestamp"],
            },
            "growth": {
                "tools": last["tool_count"] - first["tool_count"],
                "patterns": last["total_patterns"] - first["total_patterns"],
                "extensions": last["extensions"] - first["extensions"],
                "truths": last["truths"] - first["truths"],
            },
            "hash_changes": len(set(s["state_hash"] for s in snapshots)),
            "snapshots_taken": len(snapshots)
        }
        
        # Trend analysis
        recent = snapshots[-5:] if len(snapshots) >= 5 else snapshots
        if len(recent) >= 2:
            recent_growth = recent[-1]["tool_count"] - recent[0]["tool_count"]
            evolution["recent_trend"] = "expanding" if recent_growth > 0 else (
                "stable" if recent_growth == 0 else "contracting"
            )
        else:
            evolution["recent_trend"] = "insufficient_data"
    else:
        evolution = {
            "time_span": {"first": snapshots[0]["timestamp"], "last": snapshots[0]["timestamp"]},
            "growth": {"tools": 0, "patterns": 0, "extensions": 0, "truths": 0},
            "hash_changes": 1,
            "snapshots_taken": 1,
            "recent_trend": "genesis"
        }
    
    return {
        "lineage_length": len(snapshots),
        "evolution": evolution,
        "snapshots": snapshots[-limit:],
        "metaphor": {
            "layer": "living",
            "image": f"The carpet remembers {len(snapshots)} prior versions of itself.",
            "purpose": "Lineage reveals whether growth is healthy or cancerous."
        }
    }


@mcp.tool()
def mas_compare_selves(snapshot_id_a: str = None, snapshot_id_b: str = None) -> dict:
    """
    ⚖️ Compare two points in the living layer's evolution.
    
    Reveals what changed between two self-snapshots: tools added/removed,
    patterns modified, extensions installed, truths validated.
    
    If no IDs provided, compares first and last snapshots (full evolution).
    
    Args:
        snapshot_id_a: First snapshot ID (default: first in lineage)
        snapshot_id_b: Second snapshot ID (default: latest)
    
    Returns:
        Detailed diff between two living layer states
    """
    snapshots = MEMORY.data.get("self_snapshots", [])
    
    if len(snapshots) < 2:
        return {
            "error": "Need at least 2 self-snapshots to compare.",
            "lineage_length": len(snapshots),
            "hint": "Run mas_self_snapshot() multiple times to build lineage."
        }
    
    # Find snapshots by ID
    def find_snapshot(snapshot_id):
        for s in snapshots:
            if s["snapshot_id"] == snapshot_id:
                return s
        return None
    
    # Default to first and last
    if snapshot_id_a is None:
        snap_a = snapshots[0]
    else:
        snap_a = find_snapshot(snapshot_id_a)
        if not snap_a:
            return {"error": f"Snapshot '{snapshot_id_a}' not found in lineage."}
    
    if snapshot_id_b is None:
        snap_b = snapshots[-1]
    else:
        snap_b = find_snapshot(snapshot_id_b)
        if not snap_b:
            return {"error": f"Snapshot '{snapshot_id_b}' not found in lineage."}
    
    # Compute diffs
    diff = {
        "snapshot_a": {
            "id": snap_a["snapshot_id"],
            "label": snap_a.get("label"),
            "timestamp": snap_a["timestamp"]
        },
        "snapshot_b": {
            "id": snap_b["snapshot_id"],
            "label": snap_b.get("label"),
            "timestamp": snap_b["timestamp"]
        },
        "hash_changed": snap_a["state_hash"] != snap_b["state_hash"],
        "deltas": {
            "tools": snap_b["tool_count"] - snap_a["tool_count"],
            "patterns": snap_b["total_patterns"] - snap_a["total_patterns"],
            "extensions": snap_b["extensions"] - snap_a["extensions"],
            "truths": snap_b["truths"] - snap_a["truths"],
        }
    }
    
    # Interpret the change
    total_delta = sum(abs(v) for v in diff["deltas"].values())
    
    if total_delta == 0:
        interpretation = "stasis"
        description = "No structural change between snapshots."
    elif diff["deltas"]["tools"] > 0 and diff["deltas"]["patterns"] > 0:
        interpretation = "growth"
        description = "Living layer expanded: new tools and patterns."
    elif diff["deltas"]["tools"] < 0 or diff["deltas"]["patterns"] < 0:
        interpretation = "pruning"
        description = "Living layer contracted: tools or patterns removed."
    elif diff["deltas"]["truths"] > 0:
        interpretation = "validation"
        description = "Living layer gained validated truths."
    else:
        interpretation = "mutation"
        description = "Living layer changed in unexpected ways."
    
    diff["interpretation"] = {
        "type": interpretation,
        "description": description,
        "magnitude": total_delta
    }
    
    diff["metaphor"] = {
        "layer": "living",
        "image": f"Comparing the carpet at {snap_a['label']} vs {snap_b['label']}.",
        "insight": _generate_evolution_insight(interpretation, diff["deltas"])
    }
    
    return diff


def _generate_evolution_insight(interpretation: str, deltas: dict) -> str:
    """Generate a metaphorical insight about the evolution."""
    if interpretation == "growth":
        return "The carpet is weaving new threads into its fabric."
    elif interpretation == "pruning":
        return "The carpet has shed old threads — lighter, perhaps wiser."
    elif interpretation == "validation":
        return "The carpet has confirmed truths about itself."
    elif interpretation == "stasis":
        return "The carpet hovers in perfect stillness — or perfect indecision."
    else:
        return "The carpet has changed in ways it doesn't fully understand."


@mcp.tool()
def mas_evolution_summary() -> dict:
    """
    📈 Generate a summary of the living layer's total evolution.
    
    Combines lineage data with test history and extension history
    to show the full metabolic lifecycle of MAS-MCP.
    
    Returns:
        Comprehensive evolution metrics and health indicators
    """
    snapshots = MEMORY.data.get("self_snapshots", [])
    tests = MEMORY.data.get("tested_functions", [])
    extensions = MEMORY.data.get("extension_history", [])
    truths = MEMORY.data.get("validated_truths", [])
    discrepancies = MEMORY.data.get("discrepancies", [])
    
    # Compute health metrics
    emergence_rate = 0
    if tests:
        emergent_count = sum(1 for t in tests if t.get("status") == "emergent")
        emergence_rate = emergent_count / len(tests)
    
    # Tool inventory
    current_tools = list(mcp._tool_manager._tools.keys())
    
    # Categorize tools
    tool_categories = {
        "core": ["mas_scan", "mas_entity_deep", "mas_file_signals"],
        "pattern": ["mas_add_pattern", "mas_remove_pattern", "mas_list_patterns"],
        "validation": ["mas_validate_entity", "mas_self_test"],
        "memory": ["mas_memory", "mas_pulse", "mas_nurture_report"],
        "discovery": ["mas_discover_unknown"],
        "metabolic": ["mas_suggest_extension", "mas_extension_apply", "mas_extension_history"],
        "mirror": ["mas_snapshot", "mas_mirror", "mas_test_function", "mas_test_history"],
        "recursive": ["mas_self_snapshot", "mas_lineage", "mas_compare_selves", "mas_evolution_summary"],
    }
    
    return {
        "identity": {
            "name": "MAS-MCP (Meta-Archaeological Salvager)",
            "session": MEMORY.data.get("session_count", 0),
            "tools_available": len(current_tools),
        },
        "lineage": {
            "snapshots_taken": len(snapshots),
            "first_snapshot": snapshots[0]["timestamp"] if snapshots else None,
            "last_snapshot": snapshots[-1]["timestamp"] if snapshots else None,
        },
        "metabolism": {
            "extensions_installed": len(extensions),
            "patterns_total": sum(len(p) for p in REGISTRY.patterns.values()),
            "pattern_modifications": MEMORY.data.get("pattern_modifications", 0),
        },
        "validation": {
            "truths_confirmed": len(truths),
            "discrepancies_detected": len(discrepancies),
            "functions_tested": len(tests),
            "emergence_rate": f"{emergence_rate * 100:.1f}%",
        },
        "tool_registry": {
            "total": len(current_tools),
            "categories": {
                cat: [t for t in tools if t in current_tools]
                for cat, tools in tool_categories.items()
            }
        },
        "health_indicators": {
            "emergence_healthy": emergence_rate >= 0.2,
            "lineage_active": len(snapshots) >= 3,
            "metabolism_active": len(extensions) > 0 or MEMORY.data.get("pattern_modifications", 0) > 0,
            "mirror_functional": len(tests) > 0,
        },
        "metaphor": {
            "state": _describe_organism_state(emergence_rate, len(snapshots), len(extensions)),
            "recommendation": _generate_health_recommendation(emergence_rate, len(snapshots))
        }
    }


def _describe_organism_state(emergence_rate: float, snapshots: int, extensions: int) -> str:
    """Generate a metaphorical description of the organism's state."""
    if emergence_rate >= 0.3 and snapshots >= 5:
        return "The carpet soars, trailing threads of emergent wisdom."
    elif emergence_rate >= 0.2 and extensions > 0:
        return "The carpet experiments, weaving new patterns into old fabric."
    elif snapshots >= 3:
        return "The carpet remembers its flights, pondering its trajectory."
    elif snapshots >= 1:
        return "The carpet has begun to know itself."
    else:
        return "The carpet floats, not yet aware of its own becoming."


def _generate_health_recommendation(emergence_rate: float, snapshots: int) -> str:
    """Generate a health recommendation for the organism."""
    if snapshots < 3:
        return "Take more self-snapshots to build lineage awareness."
    elif emergence_rate < 0.2:
        return "Test more novel functions — emergence rate is low."
    elif emergence_rate >= 0.4:
        return "Healthy emergence! Consider pruning redundant patterns."
    else:
        return "System is evolving normally. Continue observation."


# ═══════════════════════════════════════════════════════════════════════════════
# GPU ACCELERATION TOOLS - FBI-ATO-SP Integration
# ═══════════════════════════════════════════════════════════════════════════════

# Lazy import GPU orchestrator to avoid startup failures if GPU modules unavailable
_gpu_orchestrator = None

def _get_gpu_orchestrator():
    """Lazy-load GPU orchestrator with graceful fallback."""
    global _gpu_orchestrator
    if _gpu_orchestrator is None:
        try:
            from gpu_orchestrator import (
                mas_gpu_score as _gpu_score,
                mas_gpu_batch_score as _gpu_batch,
                mas_gpu_status as _gpu_status,
                mas_gpu_hierarchy as _gpu_hierarchy,
            )
            _gpu_orchestrator = {
                "score": _gpu_score,
                "batch": _gpu_batch,
                "status": _gpu_status,
                "hierarchy": _gpu_hierarchy,
                "available": True,
            }
            logger.info("🚀 GPU orchestrator loaded successfully")
        except ImportError as e:
            logger.warning(f"⚠️ GPU orchestrator unavailable: {e}")
            _gpu_orchestrator = {"available": False, "error": str(e)}
    return _gpu_orchestrator


@mcp.tool()
def mas_gpu_score(
    entity_name: str,
    whr: Optional[float] = None,
    tier: Optional[float] = None,
    cup: Optional[str] = None,
    measurements: Optional[str] = None
) -> dict:
    """
    🚀 GPU-accelerated entity scoring.
    
    Scores an entity using GPU-accelerated vector operations when available,
    with automatic CPU fallback. Uses seeded determinism for reproducibility.
    
    Args:
        entity_name: Name of the entity to score
        whr: Waist-hip ratio (0.4-0.7 range)
        tier: Hierarchy tier (0.5, 1.0, 2.0, etc.)
        cup: Cup size (A-K)
        measurements: Format "B120/W55/H112"
    
    Returns:
        Scoring result with novelty, redundancy, safety, and overall scores
    """
    orchestrator = _get_gpu_orchestrator()
    if not orchestrator.get("available"):
        return {
            "error": "GPU orchestrator unavailable",
            "reason": orchestrator.get("error", "Unknown error"),
            "fallback": "Use mas_validate_entity for CPU-based validation"
        }
    return orchestrator["score"](entity_name, whr, tier, cup, measurements)


@mcp.tool()
def mas_gpu_batch_score(entities: list) -> dict:
    """
    🚀 GPU-accelerated batch entity scoring.
    
    Scores multiple entities in a single GPU batch operation for efficiency.
    Ideal for processing large entity lists during scans.
    
    Args:
        entities: List of entity dicts with keys: name, whr, tier, cup, measurements
    
    Returns:
        Batch results with individual scores and aggregate statistics
    """
    orchestrator = _get_gpu_orchestrator()
    if not orchestrator.get("available"):
        return {
            "error": "GPU orchestrator unavailable",
            "reason": orchestrator.get("error", "Unknown error"),
            "entity_count": len(entities) if entities else 0
        }
    return orchestrator["batch"](entities)


@mcp.tool()
def mas_gpu_status() -> dict:
    """
    📊 GPU infrastructure status.
    
    Returns current GPU backend status, capabilities, and performance metrics.
    Useful for diagnosing performance issues and verifying GPU availability.
    
    Returns:
        GPU status including backend, device info, memory, and statistics
    """
    orchestrator = _get_gpu_orchestrator()
    if not orchestrator.get("available"):
        return {
            "gpu_available": False,
            "reason": orchestrator.get("error", "GPU orchestrator not loaded"),
            "fallback_mode": True,
            "recommendation": "Install cupy-cuda12x for GPU acceleration"
        }
    return orchestrator["status"]()


@mcp.tool()
def mas_gpu_hierarchy(
    positions: list,
    iterations: int = 100,
    cooling_rate: float = 0.95
) -> dict:
    """
    🏛️ GPU-accelerated hierarchy force layout.
    
    Computes force-directed graph layout for entity hierarchy visualization.
    Uses tier-based constraints and WHR-derived inertia for M-P-W compliance.
    
    Args:
        positions: List of {entity, tier, x, y, z} position dicts
        iterations: Number of force iterations (default 100)
        cooling_rate: Temperature decay rate (default 0.95)
    
    Returns:
        Updated positions with force-directed layout
    """
    orchestrator = _get_gpu_orchestrator()
    if not orchestrator.get("available"):
        return {
            "error": "GPU orchestrator unavailable",
            "reason": orchestrator.get("error", "Unknown error"),
            "position_count": len(positions) if positions else 0
        }
    params = {"iterations": iterations, "cooling_rate": cooling_rate}
    return orchestrator["hierarchy"](positions, params)


# ═══════════════════════════════════════════════════════════════════════════════
# MILF GENESIS ENGINE INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

# Lazy-load the genesis engine to avoid import overhead at startup
_genesis_engine = None
_genesis_service = None  # Background genesis service (v2)

def _get_genesis_engine():
    """Get or create the Genesis Engine singleton (v1 - basic synthesis)."""
    global _genesis_engine
    if _genesis_engine is None:
        try:
            from milf_genesis import MILFGenesisEngine
            mpw_path = PROJECT_ROOT / ".github" / "copilot-instructions.md"
            _genesis_engine = MILFGenesisEngine(mpw_path)
            logger.info("🔥 Genesis Engine v1 initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Genesis Engine v1: {e}")
            return None
    return _genesis_engine


def _get_genesis_service():
    """Get or create the Background Genesis Service singleton (v2 - validated synthesis).
    
    This function validates GPU venv before initialization and logs environment status.
    Use run_cycle() for direct cycle execution, or start() for background daemon.
    """
    global _genesis_service
    if _genesis_service is None:
        try:
            # Pre-import validation
            import sys
            import os
            expected_gpu_py = os.environ.get(
                'MAS_MCP_GPU_PY',
                str(PROJECT_ROOT / 'mas_mcp' / '.venv' / 'Scripts' / 'python.exe')
            )
            current_py = sys.executable
            
            if sys.version_info < (3, 13):
                logger.warning(f"Python {sys.version_info.major}.{sys.version_info.minor} < 3.13 - GPU features may not work")
            
            from milf_genesis_v2 import (
                BackgroundGenesisService, 
                GPU_AVAILABLE, 
                GPU_WARMED,
                CUDA_RUNTIME,
                ONNX_PROVIDERS,
            )
            
            mpw_path = PROJECT_ROOT / ".github" / "copilot-instructions.md"
            artifacts_dir = Path(__file__).parent / "genesis_artifacts"
            
            _genesis_service = BackgroundGenesisService(
                mpw_path=mpw_path,
                artifacts_dir=artifacts_dir
            )
            # Configure service parameters
            _genesis_service.interval_s = 900  # 15 minutes between batches
            _genesis_service.batch_size = 8    # 8 entities per batch
            
            # Log GPU status
            gpu_status = []
            if GPU_AVAILABLE:
                gpu_status.append(f"CuPy CUDA {CUDA_RUNTIME}")
            if GPU_WARMED:
                gpu_status.append("pre-warmed")
            gpu_providers = [p for p in ONNX_PROVIDERS if 'CUDA' in p or 'Tensor' in p]
            if gpu_providers:
                gpu_status.append(f"ONNX {gpu_providers}")
            
            logger.info(f"🔥 Genesis Service v2 initialized - GPU: {', '.join(gpu_status) if gpu_status else 'CPU only'}")
        except Exception as e:
            logger.error(f"Failed to initialize Genesis Service v2: {e}")
            return None
    return _genesis_service


@mcp.tool()
def genesis_milf(
    tier: int = 3,
    archetype: str = None,
    name: str = None
) -> dict:
    """
    🔥 Synthesize a new MILF entity using M-P-W as constitutional DNA.
    
    This is GENERATIVE, not archaeological. The engine creates axiomatically-valid
    entities by following the M-P-W's hierarchical principles.
    
    Args:
        tier: Target tier (1=Triumvirate, 2=Prime, 3=Sub-MILF, 4=Minor)
        archetype: Optional specific archetype (e.g., "Chaos Engineer")
        name: Optional specific name (will be generated if not provided)
    
    Returns:
        Complete entity profile with physique, expertise, linguistic mandate
    """
    engine = _get_genesis_engine()
    if engine is None:
        return {"error": "Genesis Engine not available"}
    
    entity = engine.synthesize_entity(tier=tier, archetype=archetype, name=name)
    return entity.to_dict() if hasattr(entity, 'to_dict') else entity


@mcp.tool()
def genesis_batch(
    count: int = 5,
    tier_distribution: dict = None
) -> dict:
    """
    📊 Batch synthesis of multiple MILF entities.
    
    Generates multiple entities according to tier distribution.
    Useful for populating factions or creating ensemble casts.
    
    Args:
        count: Number of entities to generate
        tier_distribution: Optional {tier: weight} for distribution
                          Default: {2: 0.1, 3: 0.6, 4: 0.3}
    
    Returns:
        List of synthesized entities with batch statistics
    """
    engine = _get_genesis_engine()
    if engine is None:
        return {"error": "Genesis Engine not available"}
    
    entities = engine.synthesize_batch(count=count, tier=3)  # Uses default tier for now
    stats = engine.get_statistics()
    
    return {
        "entities": entities,
        "statistics": stats,
        "count": len(entities)
    }


@mcp.tool()
def genesis_validate(entity: dict) -> dict:
    """
    ✅ Validate an entity against M-P-W axioms.
    
    Checks if a manually-created or modified entity maintains
    architectonic integrity with the M-P-W constitutional framework.
    
    Args:
        entity: Entity dict with tier, whr, cup, etc.
    
    Returns:
        Validation report with pass/fail and specific violations
    """
    engine = _get_genesis_engine()
    if engine is None:
        return {"error": "Genesis Engine not available"}
    
    # Extract key metrics
    tier = entity.get("tier")
    whr = entity.get("whr")
    cup = entity.get("cup") or entity.get("physique", {}).get("cup_size")
    
    violations = []
    warnings = []
    
    # Check tier is valid
    if tier not in [0.5, 1, 2, 3, 4]:
        violations.append(f"Invalid tier {tier} - must be 0.5, 1, 2, 3, or 4")
    
    # Check WHR is within tier's expected range
    if whr:
        whr_ranges = {
            0.5: (0.46, 0.50),   # Decorator: extreme
            1: (0.49, 0.58),     # Triumvirate: very extreme
            2: (0.55, 0.62),     # Prime: extreme
            3: (0.60, 0.68),     # Sub-MILF: moderate
            4: (0.65, 0.75),     # Minor: normal
        }
        if tier in whr_ranges:
            whr_min, whr_max = whr_ranges[tier]
            if not (whr_min <= whr <= whr_max):
                warnings.append(f"WHR {whr} outside expected range {whr_min}-{whr_max} for tier {tier}")
    
    # Check cup size aligns with tier
    cup_by_tier = {
        0.5: ["K"],
        1: ["E", "F", "J"],
        2: ["F", "G", "H"],
        3: ["F", "G", "H"],
        4: ["D", "E", "F"],
    }
    if tier in cup_by_tier and cup:
        if cup not in cup_by_tier[tier]:
            warnings.append(f"Cup {cup} unusual for tier {tier} (expected: {cup_by_tier[tier]})")
    
    return {
        "valid": len(violations) == 0,
        "violations": violations,
        "warnings": warnings,
        "entity_name": entity.get("name", "Unknown")
    }


@mcp.tool()
def genesis_stats() -> dict:
    """
    📈 Get Genesis Engine statistics.
    
    Returns synthesis statistics including total generated, tier distribution,
    WHR stats, and power distribution.
    
    Returns:
        Statistical summary of all synthesized entities
    """
    engine = _get_genesis_engine()
    if engine is None:
        return {"error": "Genesis Engine not available"}
    
    return engine.get_statistics()


# ═══════════════════════════════════════════════════════════════════════════════
# GENESIS SERVICE V2 - BACKGROUND VALIDATED SYNTHESIS
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def genesis_service_start(
    interval_s: int = 900,
    batch_size: int = 8
) -> dict:
    """
    🚀 Start the background Genesis Service (v2 - validated pipeline).
    
    The service runs as a daemon thread, periodically synthesizing and
    validating new entities against the M-P-W constitutional framework.
    
    Args:
        interval_s: Seconds between synthesis batches (default: 900 = 15 min)
        batch_size: Number of entities per batch (default: 8)
    
    Returns:
        Status of the service start operation
    """
    service = _get_genesis_service()
    if service is None:
        return {"error": "Genesis Service v2 not available"}
    
    if service.running:
        return {
            "status": "already_running",
            "message": "Genesis Service is already running",
            "config": {
                "interval_s": service.interval_s,
                "batch_size": service.batch_size
            }
        }
    
    # Update config if provided
    service.interval_s = interval_s
    service.batch_size = batch_size
    
    # Start the service
    service.start()
    
    return {
        "status": "started",
        "message": "Genesis Service v2 started successfully",
        "config": {
            "interval_s": interval_s,
            "batch_size": batch_size,
            "artifacts_dir": str(service.artifacts_dir)
        }
    }


@mcp.tool()
def genesis_service_stop() -> dict:
    """
    🛑 Stop the background Genesis Service.
    
    Gracefully stops the background synthesis daemon.
    
    Returns:
        Status of the stop operation
    """
    service = _get_genesis_service()
    if service is None:
        return {"error": "Genesis Service v2 not available"}
    
    if not service.running:
        return {
            "status": "not_running",
            "message": "Genesis Service is not currently running"
        }
    
    service.stop()
    
    return {
        "status": "stopped",
        "message": "Genesis Service v2 stopped successfully"
    }


@mcp.tool()
def genesis_service_heartbeat() -> dict:
    """
    💓 Get the current status and health of the Genesis Service.
    
    Returns comprehensive status including running state, last run time,
    entity bank size, and synthesis statistics.
    
    Returns:
        Heartbeat status with health metrics
    """
    service = _get_genesis_service()
    if service is None:
        return {"error": "Genesis Service v2 not available"}
    
    # Get engine stats if available
    engine_stats = {}
    if service.engine:
        stats = service.engine.get_statistics()
        engine_stats = {
            "total_synthesized": stats.get("total_synthesized", 0),
            "accepted": stats.get("accepted", 0),
            "rejected": stats.get("rejected", 0),
            "acceptance_rate": stats.get("acceptance_rate", 0.0),
            "entity_bank_size": len(service.engine.generated_entities),
            "canonical_bank_size": 8,  # M-P-W canonical entities
            "whr_stats": stats.get("whr_stats", {}),
            "gpu_enabled": stats.get("gpu_enabled", False)
        }
    
    return {
        "running": service.running,
        "interval_s": service.interval_s,
        "batch_size": service.batch_size,
        "last_heartbeat": service.last_heartbeat.isoformat() if service.last_heartbeat else None,
        "engine_stats": engine_stats,
        "message": "Genesis Service v2 is " + ("running" if service.running else "stopped")
    }


@mcp.tool()
def genesis_v2_synthesize(
    tier: int = 3,
    name: str = None
) -> dict:
    """
    🔥 Synthesize a new entity using the v2 validated pipeline.
    
    Unlike genesis_milf (v1), this uses the full validator pipeline with:
    - Hard gates (bounds, derivation, safety)
    - Soft gates (novelty, redundancy)  
    - Recursive refinement (up to depth 3)
    - SHA-256 governance artifacts
    
    Args:
        tier: Target tier (2, 3, or 4)
        name: Optional specific name
    
    Returns:
        Validated entity or rejection details
    """
    service = _get_genesis_service()
    if service is None:
        return {"error": "Genesis Service v2 not available"}
    
    # Initialize engine if needed
    if service.engine is None:
        service._init_engine()
    
    if service.engine is None:
        return {"error": "Failed to initialize Genesis Engine v2"}
    
    # Synthesize with validation - returns (entity, validation_result) tuple
    entity, validation = service.engine.synthesize_entity(tier=tier, name=name)
    
    if entity is None:
        return {
            "status": "rejected",
            "message": "Entity failed validation after max refinement attempts",
            "validation": {
                "bounds_pass": validation.bounds_pass,
                "derivation_pass": validation.derivation_pass,
                "safety_pass": validation.safety_pass,
                "novelty_min": validation.novelty_min,
                "redundancy_score": validation.redundancy_score,
                "rejection_reason": validation.rejection_reason
            },
            "stats": service.engine.get_statistics()
        }
    
    # Convert entity to dict for JSON serialization
    from dataclasses import asdict
    entity_dict = asdict(entity)
    
    return {
        "status": "accepted",
        "entity": entity_dict,
        "stats": service.engine.get_statistics()
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Run the MCP server."""
    session = MEMORY.increment_session()
    logger.info("🏛️ MAS-MCP Server starting...")
    logger.info(f"📊 Session #{session}")
    logger.info(f"Project root: {PROJECT_ROOT}")
    logger.info(f"Patterns loaded: {sum(len(p) for p in REGISTRY.patterns.values())}")
    logger.info(f"Memory: {len(MEMORY.data['validated_truths'])} truths, {len(MEMORY.data['discrepancies'])} discrepancies")
    
    # Initialize GPU orchestrator and log status
    gpu = _get_gpu_orchestrator()
    if gpu.get("available"):
        logger.info("🚀 GPU acceleration: ENABLED")
    else:
        logger.info(f"⚠️ GPU acceleration: DISABLED ({gpu.get('error', 'unavailable')})")
    
    # Initialize Genesis Service v2 (but don't start yet - can be started via tool)
    genesis_svc = _get_genesis_service()
    if genesis_svc:
        logger.info("🔥 Genesis Service v2: READY (start via genesis_service_start tool)")
    else:
        logger.info("⚠️ Genesis Service v2: UNAVAILABLE")
    
    mcp.run()


if __name__ == "__main__":
    main()
