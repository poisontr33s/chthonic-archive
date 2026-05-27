#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""flux-engine-forge entrypoint.

Reads the master secret from stdin (never from argv) and dispatches the forge.
Invocation:
    echo -n "$MASTER_SECRET" | uv run -m flux_engine_forge --target sm89

The secret is intentionally not passable via flag — argv leaks to
Process Explorer, ETW, and wmic, while a stdin pipe is private to the
parent/child relationship.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Final

DEFAULT_MODEL: Final[str] = "black-forest-labs/FLUX.1-dev"
DEFAULT_TARGET: Final[str] = "sm89"
DEFAULT_OUT_DIR: Final[Path] = Path(__file__).resolve().parents[3] / "flux-satellite" / "engines"


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="flux-engine-forge",
        description="Compile FLUX.1-dev DiT to a hardware-bound FP8 TensorRT engine.",
    )
    p.add_argument("--target", default=DEFAULT_TARGET, choices=["sm89"],
                   help="GPU compute capability target (default: sm89 for RTX 4090).")
    p.add_argument("--model", default=DEFAULT_MODEL,
                   help=f"HuggingFace model id (default: {DEFAULT_MODEL}).")
    p.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR,
                   help="Output directory for .engine.enc + .seal.json.")
    p.add_argument("--scratch-dir", type=Path,
                   default=Path(__file__).resolve().parents[3] / "flux-engine-forge" / "scratch",
                   help="Scratch directory for ONNX + intermediates.")
    p.add_argument("--dry-run", action="store_true",
                   help="Run environment preflight only; do not download or compile.")
    p.add_argument("--inspect-seal", type=Path, default=None,
                   help="Inspect an existing .seal.json and exit (no secret needed).")
    p.add_argument("--reseal", action="store_true",
                   help="Skip ONNX export and trtexec; only re-run seal() against "
                        "the existing scratch/<basename>.engine.plain. Reads secret "
                        "from stdin as usual.")
    p.add_argument("--install-plain", action="store_true",
                   help="Crypto-free install: copy scratch/<basename>.engine.plain "
                        "to out_dir/<basename>.engine.plain. No seal, no secret "
                        "required. Use for the 'make it work first' lane.")
    return p.parse_args(argv)


def _read_master_secret() -> str:
    """Read the secret from stdin. Empty input is a fatal error."""
    if sys.stdin.isatty():
        print(
            "FATAL: master secret expected on stdin (no TTY allowed).\n"
            "Invoke with a piped secret, e.g.: type secret.bin | uv run -m flux_engine_forge",
            file=sys.stderr,
        )
        sys.exit(2)
    raw = sys.stdin.read()
    secret = raw.strip()
    if not secret:
        print("FATAL: empty master secret on stdin.", file=sys.stderr)
        sys.exit(2)
    if len(secret) < 32:
        print(
            f"FATAL: master secret is {len(secret)} chars; require >= 32 for "
            "AES-256 key strength.",
            file=sys.stderr,
        )
        sys.exit(2)
    return secret


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    if args.inspect_seal is not None:
        from flux_engine_forge.forge import inspect_seal
        inspect_seal(args.inspect_seal)
        return 0

    if args.dry_run:
        from flux_engine_forge.forge import run_preflight
        run_preflight(target=args.target, scratch_dir=args.scratch_dir)
        print("[forge] dry-run OK — environment satisfies preflight.")
        return 0

    if args.install_plain:
        # No secret needed in the plaintext lane.
        from flux_engine_forge.forge import install_plain_only
        install_plain_only(out_dir=args.out_dir, scratch_dir=args.scratch_dir)
        return 0

    master_secret = _read_master_secret()

    if args.reseal:
        from flux_engine_forge.forge import reseal_from_scratch
        reseal_from_scratch(
            master_secret=master_secret,
            out_dir=args.out_dir,
            scratch_dir=args.scratch_dir,
        )
        return 0

    from flux_engine_forge.forge import run_forge
    run_forge(
        master_secret=master_secret,
        model_id=args.model,
        target=args.target,
        out_dir=args.out_dir,
        scratch_dir=args.scratch_dir,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
