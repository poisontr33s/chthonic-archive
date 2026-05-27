#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""Windows named-pipe + MMF IPC server.

Wire protocol mirrors apps/chthonic-tensor-bridge/src/bridge.cc exactly:

  pipe name:   \\.\pipe\chthonic-flux
  mmf name:    Local\chthonic-flux-img   (32 MB; fits 2048x2048 RGBA + slack)
  frame:       one JSON message in, one JSON message out, per pipe instance
  data plane:  [uint32 LE length][raw RGBA bytes] at MMF offset 0
"""
from __future__ import annotations

import asyncio
import json
import logging
import mmap
import struct
import threading
import time
from dataclasses import dataclass
from typing import Final, Optional

from flux_satellite.memory_fence import post_generation_fence
from flux_satellite.pipeline import FluxOrchestrator, GenerationRequest

log: Final[logging.Logger] = logging.getLogger("flux.ipc")

MMF_SIZE: Final[int] = 32 * 1024 * 1024
PIPE_BUF: Final[int] = 65_536


@dataclass
class IpcConfig:
    pipe_name: str    # full pipe path, e.g. r"\\.\pipe\chthonic-flux"
    mmf_name: str     # bare MMF name, e.g. "Local\\chthonic-flux-img"


class IpcServer:
    """Synchronous pipe server (one connection at a time) driven by a worker thread."""

    def __init__(self, cfg: IpcConfig, orchestrator: FluxOrchestrator,
                 shutdown_event: asyncio.Event):
        self.cfg = cfg
        self.orchestrator = orchestrator
        self.shutdown_event = shutdown_event
        self._thread: Optional[threading.Thread] = None
        self._stop_flag = threading.Event()
        self._mmf: Optional[mmap.mmap] = None

    def start(self) -> None:
        if self._thread is not None:
            raise RuntimeError("IpcServer already started")
        self._mmf = mmap.mmap(-1, MMF_SIZE, tagname=self.cfg.mmf_name)
        self._thread = threading.Thread(
            target=self._serve_forever, name="flux-ipc", daemon=True
        )
        self._thread.start()
        log.info("IPC server running (pipe=%s, mmf=%s)",
                 self.cfg.pipe_name, self.cfg.mmf_name)

    def stop(self, timeout: float = 5.0) -> None:
        self._stop_flag.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
            self._thread = None
        if self._mmf is not None:
            self._mmf.close()
            self._mmf = None
        log.info("IPC server stopped")

    # --- serve loop --------------------------------------------------------

    def _serve_forever(self) -> None:
        import win32pipe
        import win32file
        import pywintypes
        import winerror

        while not self._stop_flag.is_set():
            handle = win32pipe.CreateNamedPipe(
                self.cfg.pipe_name,
                win32pipe.PIPE_ACCESS_DUPLEX,
                win32pipe.PIPE_TYPE_MESSAGE
                    | win32pipe.PIPE_READMODE_MESSAGE
                    | win32pipe.PIPE_WAIT,
                1,        # max instances
                PIPE_BUF, # out buffer
                PIPE_BUF, # in buffer
                0,        # default timeout
                None,     # security attributes
            )
            try:
                # ConnectNamedPipe blocks until a client connects. To make
                # the shutdown path responsive we poll the stop flag every
                # 200 ms via overlapped + completion.
                self._connect_with_poll(handle)
                if self._stop_flag.is_set():
                    break

                raw_in, _ = win32file.ReadFile(handle, PIPE_BUF)
                try:
                    req = json.loads(raw_in.decode("utf-8"))
                except Exception as e:
                    self._write_err(handle, req_id="", code="BAD_JSON", msg=str(e))
                    continue

                resp = self._dispatch(req)
                payload = (json.dumps(resp, separators=(",", ":")) + "\n").encode("utf-8")
                win32file.WriteFile(handle, payload)
            except pywintypes.error as e:
                if e.winerror == winerror.ERROR_BROKEN_PIPE:
                    log.debug("client disconnected")
                else:
                    log.exception("pipe error: %r", e)
            finally:
                try:
                    win32pipe.DisconnectNamedPipe(handle)
                except Exception:
                    pass
                win32file.CloseHandle(handle)

    def _connect_with_poll(self, handle) -> None:
        import win32pipe
        import win32event
        import win32file
        import pywintypes
        import winerror

        overlapped = pywintypes.OVERLAPPED()
        overlapped.hEvent = win32event.CreateEvent(None, True, False, None)
        try:
            rc = win32pipe.ConnectNamedPipe(handle, overlapped)
            if rc == 0 or rc == winerror.ERROR_PIPE_CONNECTED:
                return
            while True:
                if self._stop_flag.is_set():
                    win32file.CancelIoEx(handle, overlapped)
                    return
                rv = win32event.WaitForSingleObject(overlapped.hEvent, 200)
                if rv == win32event.WAIT_OBJECT_0:
                    return
        finally:
            win32file.CloseHandle(overlapped.hEvent)

    # --- dispatch ----------------------------------------------------------

    def _dispatch(self, req: dict) -> dict:
        op = req.get("op")
        req_id = req.get("req_id", "")
        try:
            if op == "generate":
                return self._handle_generate(req, req_id)
            if op == "health":
                return {"ok": True, "req_id": req_id, "engine": "loaded",
                        "stream": "suspended"}
            if op == "shutdown":
                # Signal the asyncio main loop to stop. The IPC server itself
                # is torn down by lifecycle.run() after the loop exits.
                try:
                    self.shutdown_event._loop.call_soon_threadsafe(  # type: ignore[attr-defined]
                        self.shutdown_event.set)
                except Exception:
                    self.shutdown_event.set()
                self._stop_flag.set()
                return {"ok": True, "req_id": req_id}
            return {"ok": False, "req_id": req_id, "err_code": "BAD_OP",
                    "err_msg": f"unknown op '{op}'"}
        except Exception as e:
            log.exception("dispatch failed for op=%s", op)
            return {"ok": False, "req_id": req_id, "err_code": "INTERNAL",
                    "err_msg": str(e)}

    def _handle_generate(self, req: dict, req_id: str) -> dict:
        gen_req = GenerationRequest(
            prompt=str(req["prompt"]),
            steps=int(req.get("steps", 22)),
            guidance=float(req.get("guidance", 3.5)),
            width=int(req.get("width", 1024)),
            height=int(req.get("height", 1024)),
            seed=int(req.get("seed", 0)),
        )
        t0 = time.perf_counter()
        result = self.orchestrator.generate(gen_req)
        wall_ms = int((time.perf_counter() - t0) * 1000)

        rgba_bytes = result.image_rgba.tobytes()
        needed = 4 + len(rgba_bytes)
        if needed > MMF_SIZE:
            raise RuntimeError(
                f"output payload {needed} bytes exceeds MMF capacity {MMF_SIZE}"
            )
        assert self._mmf is not None
        self._mmf.seek(0)
        self._mmf.write(struct.pack("<I", len(rgba_bytes)))
        self._mmf.write(rgba_bytes)

        post_generation_fence("post_gen")

        return {
            "ok": True,
            "req_id": req_id,
            "gen_ms": result.gen_ms,
            "wall_ms": wall_ms,
            "mmf_offset": 4,
            "mmf_size": len(rgba_bytes),
            "w": gen_req.width,
            "h": gen_req.height,
            "channels": 4,
        }

    def _write_err(self, handle, req_id: str, code: str, msg: str) -> None:
        import win32file
        payload = (json.dumps({
            "ok": False, "req_id": req_id, "err_code": code, "err_msg": msg,
        }, separators=(",", ":")) + "\n").encode("utf-8")
        try:
            win32file.WriteFile(handle, payload)
        except Exception:
            pass
