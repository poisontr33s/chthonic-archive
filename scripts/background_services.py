#!/usr/bin/env python3
"""
Chthonic Archive - Background Services
=======================================

A collection of background services that supplement the main development workflow.
These run independently and provide continuous monitoring, validation, and generation.

Services:
1. File Watcher - Monitors file changes and triggers validations
2. Entity Extractor - Periodic M-P-W scanning for drift detection
3. Architecture Validator - Continuous Rust/Python/Shader coherence checks
4. Session Logger - Maintains detailed work session logs

Usage:
    python background_services.py --service watcher
    python background_services.py --service all
    python background_services.py --list
"""

import argparse
import asyncio
import hashlib
import json
import logging
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("background_services")

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
MPW_PATH = PROJECT_ROOT / ".github" / "copilot-instructions.md"
SRC_PATH = PROJECT_ROOT / "src"
ASSETS_PATH = PROJECT_ROOT / "assets"
LOGS_PATH = PROJECT_ROOT / "logs"
CACHE_PATH = PROJECT_ROOT / ".cache"

# Ensure directories exist
LOGS_PATH.mkdir(exist_ok=True)
CACHE_PATH.mkdir(exist_ok=True)


class EntityExtractor:
    """Extracts and monitors entity metrics from M-P-W."""
    
    CANONICAL_ENTITIES = {
        "The Decorator": {"tier": 0.5, "cup": "K", "whr": 0.464},
        "Orackla Nocticula": {"tier": 1, "cup": "J", "whr": 0.491},
        "Madam Umeko Ketsuraku": {"tier": 1, "cup": "F", "whr": 0.533},
        "Dr. Lysandra Thorne": {"tier": 1, "cup": "E", "whr": 0.58},
        "Claudine Sin'claire": {"tier": 1, "cup": "I", "whr": 0.563},
        "Kali Nyx Ravenscar": {"tier": 2, "cup": "H", "whr": 0.556},
        "Vesper Mnemosyne Lockhart": {"tier": 2, "cup": "F", "whr": 0.573},
        "Seraphine Kore Ashenhelm": {"tier": 2, "cup": "G", "whr": 0.592},
    }
    
    def __init__(self):
        self.last_check = None
        self.drift_log = []
        
    def extract_entity_metrics(self, content: str, entity_name: str) -> dict:
        """Extract WHR, cup, tier for a specific entity."""
        lines = content.split("\n")
        entity_regex = re.compile(re.escape(entity_name), re.IGNORECASE)
        
        # Find entity profile sections
        profile_patterns = [
            rf'^\s*#+.*Profile.*{re.escape(entity_name)}',
            rf'^\s*#+.*{re.escape(entity_name)}.*Profile',
            rf'^\s*#+.*{re.escape(entity_name)}.*\(CRC',
        ]
        
        best_result = None
        best_score = 0
        
        for i, line in enumerate(lines):
            if entity_regex.search(line):
                is_profile = any(re.search(pat, line, re.IGNORECASE) for pat in profile_patterns)
                
                start = max(0, i - 5)
                end = min(len(lines), i + 50)
                context = "\n".join(lines[start:end])
                
                # Extract metrics
                whr_match = re.search(r'WHR[:\s\)\*`]*[`\*]*~?(0\.\d{2,4})', context, re.IGNORECASE)
                tier_match = re.search(r'Tier[:\s\)\*`]*[`\*]*([0-9]+\.?[0-9]*)', context, re.IGNORECASE)
                cup_match = re.search(r'\b([A-L])-?cup\b', context, re.IGNORECASE)
                has_physique = bool(re.search(r'Physique|EDFA|Measurements', context, re.IGNORECASE))
                
                score = 0
                if is_profile: score += 100
                if has_physique: score += 50
                if whr_match: score += 10
                if tier_match: score += 5
                if cup_match: score += 5
                
                if score > best_score:
                    best_score = score
                    best_result = {
                        "entity": entity_name,
                        "line": i + 1,
                        "whr": float(whr_match.group(1)) if whr_match else None,
                        "tier": float(tier_match.group(1)) if tier_match else None,
                        "cup": cup_match.group(1).upper() if cup_match else None,
                    }
        
        return best_result or {"entity": entity_name, "line": None, "whr": None, "tier": None, "cup": None}
    
    def check_drift(self) -> list[dict]:
        """Check for drift between canonical and extracted values."""
        if not MPW_PATH.exists():
            return [{"error": "M-P-W not found"}]
            
        content = MPW_PATH.read_text(encoding="utf-8", errors="ignore")
        drifts = []
        
        for entity_name, canonical in self.CANONICAL_ENTITIES.items():
            extracted = self.extract_entity_metrics(content, entity_name)
            
            for metric in ["whr", "cup", "tier"]:
                if extracted.get(metric) is not None and canonical.get(metric) is not None:
                    if extracted[metric] != canonical[metric]:
                        drifts.append({
                            "entity": entity_name,
                            "metric": metric,
                            "canonical": canonical[metric],
                            "extracted": extracted[metric],
                            "line": extracted.get("line"),
                            "timestamp": datetime.now().isoformat()
                        })
        
        self.last_check = datetime.now()
        self.drift_log.extend(drifts)
        return drifts


class FileWatcher:
    """Watches for file changes and triggers appropriate actions."""
    
    def __init__(self):
        self.file_hashes: dict[str, str] = {}
        self.handlers: dict[str, list[Callable]] = {}
        self.watch_patterns = [
            ("*.rs", self._on_rust_change),
            ("*.py", self._on_python_change),
            ("*.md", self._on_markdown_change),
            ("*.frag", self._on_shader_change),
            ("*.vert", self._on_shader_change),
        ]
    
    def _hash_file(self, path: Path) -> str:
        """Get file hash for change detection."""
        try:
            return hashlib.md5(path.read_bytes()).hexdigest()
        except Exception:
            return ""
    
    def _on_rust_change(self, path: Path):
        """Handle Rust file changes."""
        logger.info(f"🦀 Rust change: {path.name}")
        # Could trigger: cargo check, cargo clippy
        
    def _on_python_change(self, path: Path):
        """Handle Python file changes."""
        logger.info(f"🐍 Python change: {path.name}")
        # Could trigger: mypy, ruff, pytest
        
    def _on_markdown_change(self, path: Path):
        """Handle Markdown changes."""
        logger.info(f"📝 Markdown change: {path.name}")
        if "copilot-instructions" in str(path):
            logger.info("  → M-P-W modified! Running entity extraction...")
            extractor = EntityExtractor()
            drifts = extractor.check_drift()
            if drifts:
                logger.warning(f"  → Found {len(drifts)} drift(s)!")
                for d in drifts:
                    logger.warning(f"     {d['entity']}.{d['metric']}: {d['canonical']} → {d['extracted']}")
    
    def _on_shader_change(self, path: Path):
        """Handle shader file changes."""
        logger.info(f"🎨 Shader change: {path.name}")
        # Could trigger: glslangValidator, shader compilation
    
    def scan_changes(self) -> list[Path]:
        """Scan for changed files."""
        changed = []
        
        for pattern, handler in self.watch_patterns:
            for path in PROJECT_ROOT.rglob(pattern):
                if "target" in str(path) or ".venv" in str(path) or "node_modules" in str(path):
                    continue
                    
                current_hash = self._hash_file(path)
                if path not in self.file_hashes:
                    self.file_hashes[path] = current_hash
                elif self.file_hashes[path] != current_hash:
                    self.file_hashes[path] = current_hash
                    changed.append(path)
                    handler(path)
        
        return changed


class ArchitectureValidator:
    """Validates architectural coherence across the project."""
    
    def __init__(self):
        self.issues: list[dict] = []
    
    def validate_rust_structure(self) -> list[dict]:
        """Check Rust module structure."""
        issues = []
        src = PROJECT_ROOT / "src"
        
        if not src.exists():
            return [{"type": "error", "message": "src/ directory not found"}]
        
        # Check for mod.rs in each subdirectory
        for subdir in src.iterdir():
            if subdir.is_dir() and subdir.name != "target":
                mod_rs = subdir / "mod.rs"
                if not mod_rs.exists():
                    issues.append({
                        "type": "warning",
                        "message": f"Missing mod.rs in {subdir.name}/",
                        "path": str(subdir)
                    })
        
        # Check main.rs exists
        if not (src / "main.rs").exists():
            issues.append({
                "type": "error",
                "message": "Missing main.rs",
                "path": str(src)
            })
        
        return issues
    
    def validate_shader_pairs(self) -> list[dict]:
        """Check that vertex and fragment shaders are paired."""
        issues = []
        shaders = ASSETS_PATH / "shaders"
        
        if not shaders.exists():
            return []
        
        vert_shaders = set(p.stem for p in shaders.glob("*.vert"))
        frag_shaders = set(p.stem for p in shaders.glob("*.frag"))
        
        # Check for unpaired shaders
        for v in vert_shaders - frag_shaders:
            issues.append({
                "type": "warning",
                "message": f"Vertex shader {v}.vert has no matching fragment shader",
                "path": str(shaders / f"{v}.vert")
            })
        
        for f in frag_shaders - vert_shaders:
            issues.append({
                "type": "warning",
                "message": f"Fragment shader {f}.frag has no matching vertex shader",
                "path": str(shaders / f"{f}.frag")
            })
        
        return issues
    
    def validate_all(self) -> dict:
        """Run all validations."""
        results = {
            "rust_structure": self.validate_rust_structure(),
            "shader_pairs": self.validate_shader_pairs(),
            "timestamp": datetime.now().isoformat()
        }
        
        total_issues = sum(len(v) for v in results.values() if isinstance(v, list))
        results["total_issues"] = total_issues
        
        return results


class SessionLogger:
    """Maintains detailed session logs."""
    
    def __init__(self):
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = LOGS_PATH / f"session_{self.session_id}.jsonl"
        self.events: list[dict] = []
    
    def log_event(self, event_type: str, data: Any = None):
        """Log an event to the session."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "data": data
        }
        self.events.append(event)
        
        # Append to file
        with open(self.log_file, "a") as f:
            f.write(json.dumps(event) + "\n")
        
        return event
    
    def get_summary(self) -> dict:
        """Get session summary."""
        return {
            "session_id": self.session_id,
            "log_file": str(self.log_file),
            "event_count": len(self.events),
            "start_time": self.events[0]["timestamp"] if self.events else None,
            "last_event": self.events[-1]["timestamp"] if self.events else None,
        }


class BackgroundServiceManager:
    """Manages all background services."""
    
    def __init__(self):
        self.file_watcher = FileWatcher()
        self.entity_extractor = EntityExtractor()
        self.arch_validator = ArchitectureValidator()
        self.session_logger = SessionLogger()
        self.running = False
    
    async def run_watcher(self, interval: int = 5):
        """Run file watcher service."""
        self.running = True
        logger.info(f"👁️ Starting file watcher (interval: {interval}s)")
        self.session_logger.log_event("service_start", {"service": "watcher", "interval": interval})
        
        while self.running:
            changed = self.file_watcher.scan_changes()
            if changed:
                self.session_logger.log_event("files_changed", {"files": [str(p) for p in changed]})
            await asyncio.sleep(interval)
    
    async def run_entity_monitor(self, interval: int = 60):
        """Run entity drift monitor."""
        self.running = True
        logger.info(f"🔍 Starting entity monitor (interval: {interval}s)")
        self.session_logger.log_event("service_start", {"service": "entity_monitor", "interval": interval})
        
        while self.running:
            drifts = self.entity_extractor.check_drift()
            if drifts:
                logger.warning(f"🚨 Drift detected: {len(drifts)} issue(s)")
                self.session_logger.log_event("drift_detected", {"drifts": drifts})
            await asyncio.sleep(interval)
    
    async def run_arch_validator(self, interval: int = 300):
        """Run architecture validator."""
        self.running = True
        logger.info(f"🏗️ Starting architecture validator (interval: {interval}s)")
        self.session_logger.log_event("service_start", {"service": "arch_validator", "interval": interval})
        
        while self.running:
            results = self.arch_validator.validate_all()
            if results["total_issues"] > 0:
                logger.warning(f"⚠️ Architecture issues: {results['total_issues']}")
                self.session_logger.log_event("arch_issues", results)
            else:
                logger.info("✅ Architecture validation passed")
            await asyncio.sleep(interval)
    
    async def run_all(self):
        """Run all services concurrently."""
        self.running = True
        logger.info("🚀 Starting all background services...")
        
        try:
            await asyncio.gather(
                self.run_watcher(interval=5),
                self.run_entity_monitor(interval=60),
                self.run_arch_validator(interval=300),
            )
        except asyncio.CancelledError:
            logger.info("🛑 Services cancelled")
        finally:
            self.running = False
            self.session_logger.log_event("shutdown", self.session_logger.get_summary())
            logger.info(f"📝 Session log: {self.session_logger.log_file}")
    
    def stop(self):
        """Stop all services."""
        self.running = False


def main():
    parser = argparse.ArgumentParser(
        description="Chthonic Archive Background Services",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Services:
  watcher     - Monitor file changes and trigger validations
  entity      - Periodic M-P-W entity extraction and drift detection
  arch        - Architecture coherence validation
  all         - Run all services concurrently

Examples:
  python background_services.py --service all
  python background_services.py --service watcher --interval 10
  python background_services.py --validate
        """
    )
    parser.add_argument("--service", choices=["watcher", "entity", "arch", "all"], 
                        default="all", help="Which service to run")
    parser.add_argument("--interval", type=int, default=5, help="Check interval in seconds")
    parser.add_argument("--validate", action="store_true", help="Run single validation and exit")
    parser.add_argument("--extract", type=str, help="Extract metrics for a specific entity")
    
    args = parser.parse_args()
    
    manager = BackgroundServiceManager()
    
    if args.validate:
        # Single validation run
        results = manager.arch_validator.validate_all()
        print(json.dumps(results, indent=2))
        
        drifts = manager.entity_extractor.check_drift()
        if drifts:
            print("\n🚨 Entity Drifts:")
            print(json.dumps(drifts, indent=2))
        else:
            print("\n✅ No entity drift detected")
        return
    
    if args.extract:
        # Extract single entity
        if MPW_PATH.exists():
            content = MPW_PATH.read_text(encoding="utf-8", errors="ignore")
            result = manager.entity_extractor.extract_entity_metrics(content, args.extract)
            print(json.dumps(result, indent=2))
        else:
            print("Error: M-P-W not found")
        return
    
    # Run service(s)
    try:
        if args.service == "all":
            asyncio.run(manager.run_all())
        elif args.service == "watcher":
            asyncio.run(manager.run_watcher(args.interval))
        elif args.service == "entity":
            asyncio.run(manager.run_entity_monitor(args.interval))
        elif args.service == "arch":
            asyncio.run(manager.run_arch_validator(args.interval))
    except KeyboardInterrupt:
        logger.info("👋 Shutdown requested")
        manager.stop()


if __name__ == "__main__":
    main()
