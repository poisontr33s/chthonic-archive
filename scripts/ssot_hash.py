#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: ssot_hash.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
ssot_hash.py — SSOT Hash Verification

@SID:           TOOL_SSOT_HASH_V1
@Shabti:        CLI Script
@Purpose:       Computes canonical hash of the SSOT file for drift
                detection per §XIV.3. Normalizes line endings, Unicode,
                and whitespace before hashing.
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


import hashlib
import sys
import unicodedata
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.lib.ssot_paths import SSOT_HOLDER  # noqa: E402


def canonicalize(text: str) -> str:
    """
    Canonicalize text for consistent hashing.

    Transformations:
    - Normalize line endings to LF
    - Strip trailing whitespace from each line
    - Normalize Unicode to NFC form
    - Strip leading/trailing document whitespace
    """
    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # Strip trailing whitespace from each line
    lines = [line.rstrip() for line in text.split('\n')]
    text = '\n'.join(lines)

    # Normalize Unicode
    text = unicodedata.normalize('NFC', text)

    # Strip document whitespace
    return text.strip()


def ssot_hash(filepath: str | Path) -> str:
    """
    Compute SHA-256 hash of canonicalized SSOT file.

    Args:
        filepath: Path to SSOT file (copilot-instructions.md)

    Returns:
        Hexadecimal SHA-256 hash string
    """
    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"SSOT file not found: {filepath}")

    # Read file content
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Canonicalize
    canonical = canonicalize(content)

    # Hash
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def verify_ssot_integrity(
    ssot_path: str | Path,
    expected_hash: str | None = None
) -> tuple[str, bool]:
    """
    Verify SSOT file integrity.

    Args:
        ssot_path: Path to SSOT file
        expected_hash: Optional expected hash for comparison

    Returns:
        Tuple of (computed_hash, is_valid)
        - computed_hash: Current hash of file
        - is_valid: True if matches expected_hash (or True if no expected provided)
    """
    computed = ssot_hash(ssot_path)

    if expected_hash is None:
        return computed, True

    is_valid = computed == expected_hash
    return computed, is_valid


def main():
    """CLI interface for SSOT hash verification."""
    import sys
    import argparse

    parser = argparse.ArgumentParser(
        description='SSOT Hash Verification (┬ºXIV.3)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compute current hash
  python ssot_hash.py

  # Verify against expected hash
  python ssot_hash.py --verify abc123...

  # Compute hash for specific file
  python ssot_hash.py --file /path/to/copilot-instructions.md
        """
    )

    parser.add_argument(
        '--compare',
        type=str,
        metavar='HASH_OR_FILE',
        help='Compare computed hash against a hash string or a file containing a hash',
    )

    parser.add_argument(
        '--write',
        action='store_true',
        help='Write the computed hash to .chthonic/ssot.sha256',
    )

    parser.add_argument(
        '--file',
        type=Path,
        default=None,
        help='Path to SSOT file (default: resolved via ssot_paths bridge)'
    )

    parser.add_argument(
        '--verify',
        type=str,
        metavar='EXPECTED_HASH',
        help='Expected hash for verification'
    )

    parser.add_argument(
        '--bookend',
        choices=['start', 'end'],
        help='Bookend mode: compute hash at cycle start/end for drift detection'
    )

    args = parser.parse_args()

    if args.file is None:
        args.file = _REPO_ROOT / SSOT_HOLDER

    try:
        computed_hash, is_valid = verify_ssot_integrity(
            args.file,
            args.verify
        )

        # --write: persist hash to .chthonic/ssot.sha256
        if args.write:
            sha_path = _REPO_ROOT / ".chthonic" / "ssot.sha256"
            sha_path.parent.mkdir(parents=True, exist_ok=True)
            sha_path.write_text(computed_hash + "\n", encoding="utf-8")
            print(f"Written: {sha_path.relative_to(_REPO_ROOT)}")

        # --compare: compare against hash string or file containing hash
        if args.compare:
            compare_hash = args.compare
            cmp_path = Path(args.compare)
            if cmp_path.exists():
                compare_hash = cmp_path.read_text(encoding="utf-8").strip()
            match = computed_hash == compare_hash
            if match:
                print(f"MATCH: {computed_hash}")
                sys.exit(0)
            else:
                print(f"MISMATCH")
                print(f"  computed:  {computed_hash}")
                print(f"  reference: {compare_hash}")
                sys.exit(1)

        # Output format depends on mode
        if args.bookend:
            # Bookend mode: output hash with label for logging
            print(f"SSOT_HASH_{args.bookend.upper()}: {computed_hash}")

            if args.bookend == 'end' and args.verify:
                if is_valid:
                    print("DRIFT_STATUS: NO_DRIFT_DETECTED")
                    sys.exit(0)
                else:
                    print("DRIFT_STATUS: GOVERNANCE_DRIFT_DETECTED")
                    print(f"EXPECTED: {args.verify}")
                    print(f"COMPUTED: {computed_hash}")
                    sys.exit(1)

        elif args.verify:
            # Verification mode
            if is_valid:
                print(f"✅ SSOT Integrity: VALID")
                print(f"Hash: {computed_hash}")
                sys.exit(0)
            else:
                print(f"⚠️  SSOT Integrity: DRIFT_DETECTED")
                print(f"Expected: {args.verify}")
                print(f"Computed: {computed_hash}")
                sys.exit(1)

        else:
            # Hash computation mode
            print(computed_hash)
            sys.exit(0)

    except FileNotFoundError as e:
        print(f"⚠️  Error: {e}", file=sys.stderr)
        sys.exit(2)

    except Exception as e:
        print(f"⚠️  Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(3)


if __name__ == '__main__':
    main()
