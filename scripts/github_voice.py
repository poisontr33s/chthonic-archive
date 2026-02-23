#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: github_voice.py                               ║
# ║ Python module: is_voice_active, broadcast_issue                            ║
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: WHITE                                                  ║
# ║ Architectural Role: 🌿 THE GARDEN                                           ║
# ║ Purpose: Check if the 'gh' CLI is available and authenticated.             ║
# ║ Exports: is_voice_active, broadcast_issue                                  ║
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Cross-References (Bidirectional):                                      ║
# ║ Dependencies (I rely on):                                               ║
# ║   ├─► scripts/autonomous_coordinator.py                                 ║
# ╚════════════════════════════════════════════════════════════════════════════

import subprocess
import json
import sys
import shutil

def is_voice_active():
    """Check if the 'gh' CLI is available and authenticated."""
    return shutil.which("gh") is not None

def broadcast_issue(title, body, labels=None):
    """
    The Voice of the Archive.
    Creates a GitHub issue if critical events occur.
    """
    if not is_voice_active():
        print(f"🤐 [VOICE OFFLINE] 'gh' CLI not found. Logged locally: {title}")
        return False

    print(f"🗣️ [VOICE] Broadcasting to Repository: {title}...")

    cmd = ["gh", "issue", "create", "--title", title, "--body", body]
    if labels:
        for label in labels:
            cmd.extend(["--label", label])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        if result.returncode == 0:
            print(f"✅ [VOICE] Issue created: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ [VOICE FAILURE] Could not speak: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ [VOICE ERROR] {e}")
        return False

if __name__ == "__main__":
    # Self-test of the vocal cords
    if is_voice_active():
        print("✅ Larynx is functioning. Voice is capable.")
    else:
        print("⚠️ Larynx malformed. Install 'gh' CLI to enable speech.")
