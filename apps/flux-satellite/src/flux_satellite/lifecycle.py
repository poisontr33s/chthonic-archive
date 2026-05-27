#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""Top-level satellite lifecycle.

Boot sequence (post C++ TRT pivot):
  1. drain stdin (parent may still write a token to maintain the spawn protocol;
     this lane no longer needs the master secret -- the C++ bridge owns the seal)
  2. write PID file
  3. start IPC server (Pipe-A for `generate` requests from the bridge + MMF
     for RGBA payload egress)
  4. wait on shutdown event (SIGINT / shutdown op / parent exit)
  5. graceful tear-down: stop IPC, drop pipeline, clear caches

The DiT FP8 inference is now delegated to the C++ bridge over Pipe-B; this
process owns CLIP-L + T5-XXL text encoding, the scheduler / latent buffer,
and VAE decode only.
"""
from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from flux_satellite.ipc_server import IpcConfig, IpcServer
from flux_satellite.memory_fence import post_generation_fence
from flux_satellite.pipeline import BridgeDitClient, FluxOrchestrator

log: Final[logging.Logger] = logging.getLogger("flux.lifecycle")


@dataclass(frozen=True)
class LifecycleConfig:
    pipe_name: str        # Pipe-A: extension/bridge -> satellite (generate)
    mmf_name: str         # MMF: image RGBA egress
    dit_pipe_name: str    # Pipe-B: satellite -> bridge (per-step DiT)
    logs_dir: Path


def _drain_stdin_if_piped() -> None:
    """The bridge's spawn_satellite.cc still pipes a startup token to keep
    its existing CreateProcessW + handle-list contract intact. We no longer
    consume the master secret here (the C++ bridge owns the seal), but we
    must drain stdin so the writer's CloseHandle does not deadlock."""
    if sys.stdin is None or sys.stdin.isatty():
        return
    try:
        _ = sys.stdin.read()
    except Exception:
        pass


def _setup_logging(logs_dir: Path) -> None:
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / "flux-satellite.log"
    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    sh = logging.StreamHandler(sys.stderr)
    sh.setFormatter(fmt)
    root.addHandler(sh)
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(fmt)
    root.addHandler(fh)


def _write_pid(logs_dir: Path) -> Path:
    pid_path = logs_dir / "flux-satellite.pid"
    pid_path.write_text(str(os.getpid()), encoding="utf-8")
    return pid_path


async def run(cfg: LifecycleConfig) -> int:
    _setup_logging(cfg.logs_dir)
    log.info("flux-satellite booting (pid=%d)", os.getpid())
    _drain_stdin_if_piped()

    log.info("DiT delegated to C++ bridge via Pipe-B: %s", cfg.dit_pipe_name)
    dit_client = BridgeDitClient(pipe_name=cfg.dit_pipe_name)
    orchestrator = FluxOrchestrator(client=dit_client)
    log.info("orchestrator ready (CLIP-L + T5-XXL + VAE in-process; DiT in bridge)")

    shutdown = asyncio.Event()
    loop = asyncio.get_running_loop()

    def _signal_handler(signum, _frame=None) -> None:
        log.info("signal %s received — initiating shutdown", signum)
        loop.call_soon_threadsafe(shutdown.set)

    if sys.platform == "win32":
        # SIGBREAK is delivered for CTRL_BREAK_EVENT on Windows console groups.
        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGBREAK, _signal_handler)
    else:
        for s in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(s, _signal_handler, int(s))

    pid_path = _write_pid(cfg.logs_dir)
    try:
        ipc = IpcServer(
            IpcConfig(pipe_name=cfg.pipe_name, mmf_name=cfg.mmf_name),
            orchestrator=orchestrator,
            shutdown_event=shutdown,
        )
        ipc.start()
        try:
            await shutdown.wait()
        finally:
            ipc.stop(timeout=10.0)
        log.info("shutdown clean")
        return 0
    finally:
        try:
            pid_path.unlink(missing_ok=True)
        except OSError:
            pass
        post_generation_fence("post_shutdown")
