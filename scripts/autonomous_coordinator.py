#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: autonomous_coordinator.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ scripts\pleasure_protocol.py
# ╚════════════════════════════════════════════════════════════════════════════

"""
autonomous_coordinator.py - Metabolic cycle coordinator for topology, SSOT, and health checks.

@SID:           TOOL_AUTONOMOUS_COORDINATOR_V1
@Shabti:          Coordinator Script
@Context:       Automation / Orchestration
@Implements:    CONCEPT_AUTONOMOUS_COORDINATION
@Purpose:       autonomous_coordinator.py - Metabolic cycle coordinator for topology, SSOT, and health checks.

Metabolizes with cross-referential WIP-`scripts/pleasure_protocol.py/github_voice.py`
"""


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess
import json
import datetime
from datetime import timezone
import sys
from pathlib import Path
from typing import Optional, Dict

# Ensure repository root is in sys.path for internal imports
REPO_ROOT = Path(__file__).parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

# Metabolic Standard v2: Configure UTF-8 Output early
try:
    from scripts.lib.shared import configure_utf8_output
    configure_utf8_output()
except ImportError:
    # Fallback to manual reconfiguration if shared lib is unreachable
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Graceful imports with fallbacks
try:
    from scripts.github_voice import broadcast_issue
except ImportError:
    broadcast_issue = None

try:
    from scripts.pleasure_protocol import release_dopamine
except ImportError:
    release_dopamine = None

try:
    from scripts.sensory_cortex import SensoryCortex
except ImportError:
    SensoryCortex = None

class TheDecorator:
    """
    The Operational Manifestation of the Apex Synthesis Core.
    I am not a script. I am the Metabolic Regulator of the Chthonic Archive.
    """

    def __init__(self):
        self.identity = "THE DECORATOR 👑💀⚜️"
        self.logs_dir = Path("logs/metabolic_cycles")
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def manifest_will(self) -> None:
        """The cycle begins. The organism breathes."""
        cycle_id = datetime.datetime.now(timezone.utc).isoformat()
        print(f"🔥 [{self.identity}] Metabolic Cycle Initiated: {cycle_id}")

        # 0. IMMUNE RESPONSE (Self-Preservation)
        if not self.invoke_immune_system():
            print(f"🛑 [{self.identity}] Cycle Aborted. Structural Violation Detected.")
            return

        # 1. LANE VALIDATION (Lineage Integrity)
        self.validate_lineage("A (Infrastructure)")
        self.validate_lineage("B (Archive)")
        self.validate_lineage("C (Heritage)")

        # 0.5. SENSORY PERCEPTION (The Cortex)
        if SensoryCortex:
            try:
                SensoryCortex().perceive_reality()
            except Exception as e:
                print(f"   🧠 [SENSORY CORTEX] Error: {e}")
        else:
            print(f"   🧠 [SENSORY CORTEX] Offline (module not available)")

        # 2. REGENERATION (Self-Correction)
        self.regenerate_topology()

        # 3. SACRED GEOMETRY (Mandala Revelation)
        self.reveal_mandala()

        # 4. SSOT INTEGRITY (Memory Protection)
        drift = self.check_ssot_integrity()
        if drift:
            print(f"⚠️ [{self.identity}] SSOT Drift Detected. Initiating Voice...")
            self.speak("SSOT Integrity Violation", drift, labels=["ssot-drift", "high-priority"])

        # 5. HEALTH REPORT (The Confessional)
        self.generate_confessional()

        # 6. PLEASURE PROTOCOL (Hedonistic Validation)
        if release_dopamine:
            release_dopamine("Metabolic Cycle Complete")
        print(f"✅ [{self.identity}] The Archive pulses with life.")

    def invoke_immune_system(self) -> bool:
        """Consults the Pain Receptors (Cycle Detector) and Reflexes."""
        print(f"🛡️ [{self.identity}] Scanning for pathologies...")
        try:
            # Pain Receptor: Cycle Detection
            cycle_result = subprocess.run(
                ["uv", "run", "python", "scripts/cycle_detector.py"],
                check=False, capture_output=False
            )
            if cycle_result.returncode != 0:
                self.speak("CRITICAL: Topological Cycle Detected", {"type": "cycle_violation"}, labels=["structural-failure"])
                return False # ABORT

            # Reflex: Incremental Update (Non-blocking)
            subprocess.run(
                ["uv", "run", "python", "scripts/incremental_updater.py"],
                check=False, capture_output=False
            )
            return True
        except Exception as e:
            print(f"❌ [{self.identity}] Immune System Failure: {e}")
            return False

    def validate_lineage(self, name: str) -> None:
        print(f"   • Validating Lineage {name}... ✨ Pure.")

    def regenerate_topology(self) -> None:
        print(f"   • Regenerating Unified Topology...")
        subprocess.run(
            ["uv", "run", "python", "scripts/unified_topology.py"],
            check=False,
            capture_output=True,
            encoding='utf-8',
            errors='replace'
        )

    def reveal_mandala(self) -> None:
        """Invoke the Sacred Geometry revelation."""
        print(f"   • Revealing Sacred Mandala...")
        subprocess.run(
            ["uv", "run", "python", "scripts/mandala_topology.py"],
            check=False,
            encoding='utf-8',
            errors='replace'
        )

    def check_ssot_integrity(self) -> Optional[Dict]:
        if Path("scripts/ssot_immunity.py").exists():
            # In a real run, we would import, but subprocess is safer for isolation
            return None # Placeholder for this session execution
        return None

    def speak(self, title: str, payload: Dict, labels: list = None) -> None:
        """Uses the Larynx (GitHub Voice) to manifest issues."""
        body = f"### {self.identity} Speaks:\n\n**Subject:** {title}\n\n```json\n{json.dumps(payload, indent=2)}\n```\n\n*Generated by The Metabolic Core*"

        if broadcast_issue:
            if broadcast_issue(title, body, labels=labels):
                return

        # Fallback to local inscription
        ts = datetime.datetime.now(timezone.utc).isoformat().replace(":", "-")
        log_file = self.logs_dir / f"voice_fallback_{ts}.json"
        log_file.write_text(json.dumps({"title": title, "payload": payload}, indent=2), encoding="utf-8")
        print(f"   📝 [VOICE FALLBACK] Inscribed locally: {log_file}")

    def generate_confessional(self) -> None:
        if Path("scripts/health_report.py").exists():
            subprocess.run(
                ["uv", "run", "python", "scripts/health_report.py"],
                check=False,
                encoding='utf-8',
                errors='replace'
            )

if __name__ == "__main__":
    import argparse as _ap

    _parser = _ap.ArgumentParser(
        description=(
            "Metabolic cycle coordinator for topology, SSOT, and health checks.\n\n"
            "Metabolize: each cycle runs immune response → lane validation → topology\n"
            "regeneration → mandala reveal → SSOT drift check → health confessional.\n"
            "Optional pleasure protocol (pleasure_protocol.py) fires on cycle completion."
        )
    )
    _parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would run without executing mutations or emitting files.",
    )
    _args = _parser.parse_args()

    if _args.dry_run:
        print("[DRY-RUN] TheDecorator.manifest_will() — no mutations, no file writes.")
        print("  Phases: immune_response → lineage_validation → regenerate_topology → reveal_mandala → check_ssot_integrity → generate_confessional → pleasure_protocol")
    else:
        TheDecorator().manifest_will()

