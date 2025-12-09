"""
SSOT Handler: Cryptographic Binding to Single Source of Truth
==============================================================

Implements Section XIV.3 of the Codex Brahmanica Perfectus.

The SSOT (Single Source of Truth) is `.github/copilot-instructions.md`.
This module provides cryptographic verification that the ASC Framework
operates with grounded, consistent governance.

Key Functions:
- canonicalize_text(): Normalize text for consistent hashing
- compute_ssot_hash(): SHA-256 of canonical SSOT content
- verify_bookend(): Compare start/end hashes for drift detection

Usage:
    from mas_mcp.lib import compute_ssot_hash, verify_bookend
    
    # At session start
    hash_start = compute_ssot_hash()
    
    # ... do work ...
    
    # At session end
    is_consistent, hash_end = verify_bookend(hash_start)
    if not is_consistent:
        raise GovernanceDriftError("SSOT modified during session!")

Per Section XIV.1: Always invoke via `uv run python`, never `python` directly.
"""

from __future__ import annotations

import hashlib
import os
import unicodedata
from pathlib import Path
from typing import Tuple

# Default SSOT path relative to repository root
SSOT_DEFAULT_PATH = ".github/copilot-instructions.md"


def get_ssot_path() -> Path:
    """
    Resolve the absolute path to the SSOT file.
    
    Priority:
    1. SSOT_PATH environment variable (if set)
    2. Relative to detected repository root
    3. Relative to this file's location (fallback)
    
    Returns:
        Absolute Path to the SSOT file
        
    Raises:
        FileNotFoundError: If SSOT file cannot be located
    """
    # Check environment variable first
    env_path = os.environ.get("SSOT_PATH")
    if env_path:
        p = Path(env_path)
        if p.exists():
            return p.resolve()
        raise FileNotFoundError(f"SSOT_PATH set but file not found: {env_path}")
    
    # Find repository root by looking for .git
    # Start from this file's location and walk up
    current = Path(__file__).resolve().parent
    
    while current != current.parent:
        if (current / ".git").exists():
            ssot = current / SSOT_DEFAULT_PATH
            if ssot.exists():
                return ssot
            raise FileNotFoundError(
                f"Repository root found at {current}, but SSOT not at {ssot}"
            )
        current = current.parent
    
    # Fallback: try relative to cwd
    fallback = Path.cwd() / SSOT_DEFAULT_PATH
    if fallback.exists():
        return fallback.resolve()
    
    raise FileNotFoundError(
        f"Cannot locate SSOT. Set SSOT_PATH env var or ensure "
        f"{SSOT_DEFAULT_PATH} exists in repository root."
    )


def canonicalize_text(text: str) -> str:
    """
    Canonicalize text for consistent hashing across platforms.
    
    Per Section XIV.3 (SSOT-VP):
    1. Convert CRLF and CR to LF (line ending normalization)
    2. Strip trailing whitespace from each line
    3. Apply Unicode NFC normalization
    4. Strip leading/trailing whitespace from entire document
    
    This ensures identical content produces identical hashes regardless of:
    - Windows vs Unix line endings
    - Editor trailing whitespace behavior
    - Unicode composition differences
    
    Args:
        text: Raw file content
        
    Returns:
        Canonicalized text ready for hashing
    """
    # Step 1: Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Step 2: Strip trailing whitespace from each line
    lines = [line.rstrip() for line in text.split('\n')]
    text = '\n'.join(lines)
    
    # Step 3: Unicode NFC normalization
    text = unicodedata.normalize('NFC', text)
    
    # Step 4: Strip document-level whitespace
    text = text.strip()
    
    return text


def compute_ssot_hash(ssot_path: Path | str | None = None) -> str:
    """
    Compute SHA-256 hash of the canonical SSOT content.
    
    Args:
        ssot_path: Optional explicit path to SSOT file.
                   If None, uses get_ssot_path() to locate it.
                   
    Returns:
        Lowercase hex digest of SHA-256 hash (64 characters)
        
    Raises:
        FileNotFoundError: If SSOT file cannot be located
        UnicodeDecodeError: If file is not valid UTF-8
    """
    if ssot_path is None:
        path = get_ssot_path()
    else:
        path = Path(ssot_path)
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    canonical = canonicalize_text(content)
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def verify_bookend(hash_start: str, ssot_path: Path | str | None = None) -> Tuple[bool, str]:
    """
    Verify that SSOT content has not drifted since session start.
    
    Per Section XIV.3: Bookend Verification
    - Compute hash_start at cycle/session initiation
    - Compute hash_end at cycle/session completion
    - If hash_start != hash_end: GOVERNANCE_DRIFT_DETECTED
    
    Args:
        hash_start: Hash computed at session start
        ssot_path: Optional explicit path to SSOT file
        
    Returns:
        Tuple of (is_consistent: bool, hash_end: str)
        
    Example:
        hash_start = compute_ssot_hash()
        # ... session work ...
        is_ok, hash_end = verify_bookend(hash_start)
        if not is_ok:
            print(f"DRIFT! {hash_start[:16]}... → {hash_end[:16]}...")
    """
    hash_end = compute_ssot_hash(ssot_path)
    is_consistent = hash_start == hash_end
    return is_consistent, hash_end


# ─────────────────────────────────────────────────────────────────────────────
# CLI Interface (for testing)
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    """CLI entry point for SSOT verification."""
    import sys
    
    try:
        path = get_ssot_path()
        print(f"SSOT Location: {path}")
        print(f"SSOT Size: {path.stat().st_size:,} bytes")
        
        h = compute_ssot_hash(path)
        print(f"SSOT Hash: {h}")
        print(f"Hash (short): {h[:16]}...")
        
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
