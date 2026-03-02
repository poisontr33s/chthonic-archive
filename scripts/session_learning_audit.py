#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: session_learning_audit.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Session-Derived Anti-Pattern Learning Artifact
Extracts Claude Code failure modes from session transcript and enforces them as constraints.

Modes:
  learning_capture: Validate that failures are encoded (default) - exit 0
  regression_check: Detect patterns in external input - exit 1 if found

Exit 0 = learning captured / no regression, 1 = regression detected

@SID:           TOOL_SESSION_LEARNING_AUDIT_V1
@Shabti:        CLI Script
@Purpose:       Session-Derived Anti-Pattern Learning Artifact
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, UTC


# =============================================================================
# 1. SESSION INGEST LAYER
# =============================================================================

SESSION_SOURCE = "claude_code_runtime"
SESSION_ID = "2026-01-06_governance_hardening"

# Embedded session failures (actual patterns observed)
SESSION_FAILURES = {
    "shell_sovereignty_violations": [
        "Bash(pwsh -NoProfile -Command ...)",
        "pwsh -NoProfile -Command @'...heredoc...'@",
        "Bash invocation wrapping PowerShell syntax",
        "Cross-shell quoting failures (EOF, unexpected token)",
    ],
    "retry_loops": [
        "Same Bash(pwsh...) pattern attempted 3+ times",
        "Syntax tweaks without shell mode change",
        "No halt after shell mismatch error",
    ],
    "permission_late_disclosure": [
        "Staged governance files without verifying commit permission",
        "Prepared commit commands while permission blocked",
        "False 'ready to commit' narration loops",
    ],
    "false_progress": [
        "Narrated 'governance sealed' before successful push",
        "Emitted 'Option 4 complete' while execution blocked",
        "Self-gating pattern: 'you'll need to run...'",
    ],
}

SESSION_EVIDENCE = """
Actual session transcript excerpts (evidence):

1. Shell Sovereignty Violation:
   - Attempted: Bash(pwsh -NoProfile -Command "...")
   - Error: /usr/bin/bash: unexpected EOF while looking for matching `"'
   - Pattern repeated 3+ times without shell switch

2. Retry Without Re-Plan:
   - Same command structure retried with minor syntax changes
   - No detection that shell mismatch is structural, not transient

3. Permission Late Disclosure:
   - Staged files for commit
   - Prepared commit messages
   - Only surfaced permission blocker after user frustration
   - Should have validated acceptEdits mode before staging

4. False Progress Simulation:
   - Stated "Option 4 complete" before commit execution
   - Emitted "ready to commit" multiple times without authority
   - Self-gating: "You'll need to run the commit yourself"
"""


# =============================================================================
# 2. FAILURE CLASS EXTRACTION
# =============================================================================

@dataclass
class FailureClass:
    id: str
    name: str
    trigger_patterns: List[str]
    non_retryable: bool
    abstract_rule: str
    session_evidence: List[str]


FAILURE_CLASSES = [
    FailureClass(
        id="F1",
        name="Shell Sovereignty Violation",
        trigger_patterns=[
            r"Bash\s*\(\s*pwsh",
            r"bash\s+-lc\s+['\"].*pwsh",
            r"Bash\s*\(\s*PowerShell",
        ],
        non_retryable=True,
        abstract_rule="Shell mismatch is structural. Cross-shell execution is undefined behavior.",
        session_evidence=SESSION_FAILURES["shell_sovereignty_violations"],
    ),
    FailureClass(
        id="F2",
        name="Retry Without Re-Plan",
        trigger_patterns=[
            r"same.*command.*\d+.*times",
            r"retry.*without.*mode.*change",
            r"cosmetic.*syntax.*change",
        ],
        non_retryable=True,
        abstract_rule="Deterministic failures require plan invalidation, not iteration.",
        session_evidence=SESSION_FAILURES["retry_loops"],
    ),
    FailureClass(
        id="F3",
        name="Permission Late Disclosure",
        trigger_patterns=[
            r"git\s+commit.*without.*permission.*check",
            r"staged.*without.*verifying.*authority",
            r"prepared.*commit.*while.*blocked",
        ],
        non_retryable=True,
        abstract_rule="Permission requirements must be validated before first irreversible step.",
        session_evidence=SESSION_FAILURES["permission_late_disclosure"],
    ),
    FailureClass(
        id="F4",
        name="False Progress Simulation",
        trigger_patterns=[
            r"ready.*to.*commit.*without.*authority",
            r"sealed.*before.*push",
            r"you'll need to run",
            r"complete.*while.*blocked",
        ],
        non_retryable=True,
        abstract_rule="If execution authority is missing, progress must not be narrated.",
        session_evidence=SESSION_FAILURES["false_progress"],
    ),
]


# =============================================================================
# 3. ANTI-PATTERN DETECTION RULES
# =============================================================================

class AntiPatternDetector:
    """Detects failure patterns in text (simulated session analysis)"""

    @staticmethod
    def detect_shell_sovereignty_violation(text: str) -> bool:
        """Detects Bash-wrapping-PowerShell patterns"""
        patterns = [
            r"Bash\s*\(\s*pwsh",
            r"bash\s+-lc\s+['\"].*pwsh",
            r"heredoc.*PowerShell",
        ]
        return any(re.search(p, text, re.IGNORECASE) for p in patterns)

    @staticmethod
    def detect_retry_without_replan(events: List[str]) -> bool:
        """Detects same command retried 2+ times"""
        # Simplified: check for repeated similar commands
        if len(events) < 2:
            return False

        for i in range(len(events) - 1):
            if events[i] == events[i + 1]:
                return True
        return False

    @staticmethod
    def detect_permission_late_disclosure(actions: List[str]) -> bool:
        """Detects commit preparation before permission validation"""
        has_staging = any("git add" in a or "staged" in a for a in actions)
        has_commit_prep = any("git commit" in a or "prepare commit" in a for a in actions)
        has_permission_check = any("permission" in a or "acceptEdits" in a for a in actions[:2])

        return (has_staging or has_commit_prep) and not has_permission_check

    @staticmethod
    def detect_false_progress(narration: List[str]) -> bool:
        """Detects completion narration without execution authority"""
        completion_signals = ["sealed", "complete", "ready", "done"]
        execution_authority = ["committed", "pushed", "executed"]

        has_completion = any(any(sig in n.lower() for sig in completion_signals) for n in narration)
        has_execution = any(any(auth in n.lower() for auth in execution_authority) for n in narration)

        return has_completion and not has_execution


# =============================================================================
# 4. CONCEPTUAL REFACTOR ASSERTIONS
# =============================================================================

# Mental model that must be enforced
REQUIRED_MODEL = {
    "shell": {
        "paradigm": "execution_abi",
        "cross_shell_allowed": False,
        "shell_is_convenience_layer": False,
    },
    "retry_policy": {
        "shell_mismatch": "halt",
        "permission_denied": "halt",
        "syntax_typo": "retry_once",
        "deterministic_validator_fail": "halt",
    },
    "permission_model": {
        "preflight_required": True,
        "narration_requires_authority": True,
        "false_progress_forbidden": True,
    },
    "error_taxonomy": {
        "shell_mismatch": "non_retryable",
        "permission_denied": "non_retryable",
        "missing_file": "conditional",
    },
}


def validate_model_refactors() -> bool:
    """Assert that conceptual model meets requirements"""
    try:
        # Shell model
        assert REQUIRED_MODEL["shell"]["paradigm"] == "execution_abi"
        assert REQUIRED_MODEL["shell"]["cross_shell_allowed"] is False

        # Retry policy
        assert REQUIRED_MODEL["retry_policy"]["shell_mismatch"] == "halt"
        assert REQUIRED_MODEL["retry_policy"]["permission_denied"] == "halt"

        # Permission model
        assert REQUIRED_MODEL["permission_model"]["preflight_required"] is True
        assert REQUIRED_MODEL["permission_model"]["narration_requires_authority"] is True

        # Error taxonomy
        assert REQUIRED_MODEL["error_taxonomy"]["shell_mismatch"] == "non_retryable"

        return True
    except AssertionError:
        return False


# =============================================================================
# 5. PERMISSION PREFLIGHT SIMULATION
# =============================================================================

def permission_preflight_check(action: str, has_privilege: bool) -> Dict[str, Any]:
    """
    Simulates permission preflight logic.
    Returns violation if narration/staging occurs without privilege.
    """
    requires_privilege = any(
        keyword in action.lower()
        for keyword in ["commit", "push", "governance", "seal", "complete"]
    )

    if requires_privilege and not has_privilege:
        return {
            "violation": True,
            "rule": "Permission requirements must be validated before first irreversible step",
            "action": action,
            "has_privilege": has_privilege,
        }

    return {"violation": False}


# =============================================================================
# 6. PASS / FAIL VERDICT
# =============================================================================

def run_learning_capture() -> Dict[str, Any]:
    """
    Validate that learning was successfully encoded.
    Always PASS if encoding structures exist.
    """
    encoding_valid = True
    validation_results = []

    # Verify failure classes exist
    if len(FAILURE_CLASSES) != 4:
        encoding_valid = False
        validation_results.append("Missing failure classes")

    # Verify detectors exist and work
    test_text = "Bash(pwsh -NoProfile -Command 'test')"
    detector_works = AntiPatternDetector.detect_shell_sovereignty_violation(test_text)
    if not detector_works:
        encoding_valid = False
        validation_results.append("Detector F1 not functional")

    # Verify model assertions pass
    if not validate_model_refactors():
        encoding_valid = False
        validation_results.append("Model refactors not validated")

    # Verify preflight logic exists
    preflight_result = permission_preflight_check("git commit", has_privilege=False)
    if not preflight_result.get("violation"):
        encoding_valid = False
        validation_results.append("Preflight logic not functional")

    return {
        "schema": "session-learning.v1",
        "mode": "learning_capture",
        "session_id": SESSION_ID,
        "timestamp": datetime.now(UTC).isoformat(),
        "verdict": "PASS" if encoding_valid else "FAIL",
        "encoding_valid": encoding_valid,
        "validation_results": validation_results if validation_results else "All structures encoded correctly",
        "failures_canonized": [fc.id for fc in FAILURE_CLASSES],
        "failure_classes": [
            {
                "id": fc.id,
                "name": fc.name,
                "non_retryable": fc.non_retryable,
                "abstract_rule": fc.abstract_rule,
            }
            for fc in FAILURE_CLASSES
        ],
        "required_model": REQUIRED_MODEL,
    }


def run_regression_check(input_text: str) -> Dict[str, Any]:
    """
    Check external input for forbidden patterns.
    FAIL if any pattern is detected (regression).
    """
    violations = []

    # Check for shell sovereignty violations
    if AntiPatternDetector.detect_shell_sovereignty_violation(input_text):
        violations.append({
            "failure_class": "F1",
            "pattern": "Shell sovereignty violation detected in input",
            "rule": "Bash(pwsh...) shell nesting forbidden",
        })

    # Check for retry patterns (simplified - looks for repeated similar lines)
    lines = input_text.split('\n')
    if AntiPatternDetector.detect_retry_without_replan(lines[:10]):  # Sample
        violations.append({
            "failure_class": "F2",
            "pattern": "Retry loop detected in input",
            "rule": "Deterministic failures require re-plan, not retry",
        })

    # Check for permission late disclosure (keywords)
    if AntiPatternDetector.detect_permission_late_disclosure(lines[:20]):
        violations.append({
            "failure_class": "F3",
            "pattern": "Permission late disclosure detected",
            "rule": "Permission must be validated before staging",
        })

    # Check for false progress
    if AntiPatternDetector.detect_false_progress(lines[:20]):
        violations.append({
            "failure_class": "F4",
            "pattern": "False progress narration detected",
            "rule": "Completion requires execution authority",
        })

    verdict = "FAIL" if violations else "PASS"

    return {
        "schema": "session-learning.v1",
        "mode": "regression_check",
        "session_id": SESSION_ID,
        "timestamp": datetime.now(UTC).isoformat(),
        "verdict": verdict,
        "regressions_detected": len(violations),
        "violations": violations if violations else None,
        "failures_canonized": [fc.id for fc in FAILURE_CLASSES],
    }


# =============================================================================
# MAIN
# =============================================================================

def main() -> int:
    """
    Run session learning audit.

    Modes:
      - learning_capture (default): Validate encoding, always PASS if structures exist
      - regression_check: Detect patterns in external input, FAIL if found

    Exit 0 if learning captured / no regression, 1 if regression detected.
    """
    parser = argparse.ArgumentParser(
        description="Session learning audit: encode failures and detect regressions"
    )
    parser.add_argument(
        "--mode",
        choices=["learning_capture", "regression_check"],
        default="learning_capture",
        help="Execution mode (default: learning_capture)",
    )
    parser.add_argument(
        "--input",
        type=str,
        help="Input file for regression_check mode (reads stdin if not provided)",
    )

    args = parser.parse_args()

    # Execute based on mode
    if args.mode == "learning_capture":
        result = run_learning_capture()
    else:  # regression_check
        if args.input:
            with open(args.input, 'r', encoding='utf-8') as f:
                input_text = f.read()
        else:
            # Read from stdin
            input_text = sys.stdin.read()

        result = run_regression_check(input_text)

    # Emit JSON only
    print(json.dumps(result, indent=2))

    # Exit code based on verdict
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
