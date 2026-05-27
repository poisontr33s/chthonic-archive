#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""flux-satellite daemon entrypoint.

Spawned by chthonic-tensor-bridge. After the C++ TRT pivot the satellite no
longer holds the master secret -- the bridge owns the engine unseal and runs
the DiT FP8 steps. This process owns text encoders, scheduler, and VAE.

    uv run -m flux_satellite \\
        --pipe        \\\\.\\pipe\\chthonic-flux \\
        --mmf         Local\\chthonic-flux-img \\
        --dit-pipe    \\\\.\\pipe\\chthonic-flux-dit
"""
from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import Final

DEFAULT_PIPE:     Final[str] = r"\\.\pipe\chthonic-flux"
DEFAULT_DIT_PIPE: Final[str] = r"\\.\pipe\chthonic-flux-dit"
DEFAULT_MMF:      Final[str] = "Local\\chthonic-flux-img"
DEFAULT_LOGS_DIR: Final[Path] = Path(__file__).resolve().parents[2] / "logs"


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="flux-satellite",
        description="FLUX text-encode + VAE daemon; DiT delegated to C++ bridge.",
    )
    p.add_argument("--pipe", default=DEFAULT_PIPE,
                   help=f"Pipe-A path; extension -> satellite (default: {DEFAULT_PIPE}).")
    p.add_argument("--mmf", default=DEFAULT_MMF,
                   help=f"MMF tag for RGBA egress (default: {DEFAULT_MMF}).")
    p.add_argument("--dit-pipe", default=DEFAULT_DIT_PIPE,
                   help=f"Pipe-B path; satellite -> bridge per DiT step "
                        f"(default: {DEFAULT_DIT_PIPE}).")
    p.add_argument("--logs-dir", type=Path, default=DEFAULT_LOGS_DIR,
                   help="Directory for log + PID files.")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    from flux_satellite.lifecycle import LifecycleConfig, run

    args = _parse_args(argv)
    cfg = LifecycleConfig(
        pipe_name=args.pipe,
        mmf_name=args.mmf,
        dit_pipe_name=args.dit_pipe,
        logs_dir=args.logs_dir,
    )
    return asyncio.run(run(cfg))


if __name__ == "__main__":
    raise SystemExit(main())
