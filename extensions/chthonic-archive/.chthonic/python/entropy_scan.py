#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

MAX_SCAN_FILES = 3000


def emit(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload) + "\n")
    sys.stdout.flush()


def normalize_path(root: Path, candidate: str) -> str:
    return str(Path(candidate).resolve().relative_to(root.resolve())).replace("\\", "/")


def safe_relative(candidate: Any) -> str | None:
    if not isinstance(candidate, str):
        return None
    raw = candidate.strip()
    if not raw or os.path.isabs(raw) or ".." in raw:
        return None
    if not raw.lower().endswith((".py", ".pyi")):
        return None
    return raw


def gather_targets(root: Path, files: list[Any] | None) -> list[str]:
    if files is not None:
        selected = [item for item in (safe_relative(entry) for entry in files) if item]
        return selected[:MAX_SCAN_FILES]

    output: list[str] = []
    for candidate in root.rglob("*"):
        if len(output) >= MAX_SCAN_FILES:
            break
        if not candidate.is_file():
            continue
        if candidate.suffix.lower() not in {".py", ".pyi"}:
            continue
        output.append(str(candidate.relative_to(root)).replace("\\", "/"))
    return output


def run_ruff_on_target(root: Path, relative_target: str) -> list[dict[str, Any]]:
    command = [
        "ruff",
        "check",
        "--output-format",
        "json",
        "--exit-zero",
        relative_target,
    ]
    process = subprocess.run(
        command,
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
    )
    if process.returncode not in (0, 1):
        raise RuntimeError(process.stderr.strip() or f"ruff failed for {relative_target}")

    stdout = process.stdout.strip()
    if not stdout:
        return []

    parsed = json.loads(stdout)
    if not isinstance(parsed, list):
        raise RuntimeError(f"ruff returned invalid payload for {relative_target}")
    return parsed


def aggregate_violations(root: Path, entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: dict[str, int] = defaultdict(int)
    by_code: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for entry in entries:
        filename = entry.get("filename")
        if not filename:
            continue
        try:
            relative = normalize_path(root, str(filename))
        except Exception:
            continue
        code = str(entry.get("code", "UNKNOWN"))
        counts[relative] += 1
        by_code[relative][code] += 1

    output: list[dict[str, Any]] = []
    for candidate in sorted(counts.keys()):
        output.append(
            {
                "path": candidate,
                "violations": counts[candidate],
                "byCode": dict(sorted(by_code[candidate].items())),
            }
        )
    return output


def threaded_scan(root: Path, targets: list[str]) -> list[dict[str, Any]]:
    if not targets:
        return []

    max_workers = max(1, min(len(targets), os.cpu_count() or 4))
    merged: list[dict[str, Any]] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(run_ruff_on_target, root, target) for target in targets]
        for future in concurrent.futures.as_completed(futures):
            merged.extend(future.result())
    return merged


def handle_scan(payload: dict[str, Any]) -> None:
    root_raw = payload.get("root")
    if not isinstance(root_raw, str) or not root_raw:
        emit(
            {
                "type": "error",
                "source": "python",
                "message": "scan request missing root",
            }
        )
        return

    root = Path(root_raw)
    targets = gather_targets(root, payload.get("files") if isinstance(payload.get("files"), list) else None)
    if not targets:
        emit(
            {
                "type": "ruff-summary",
                "reason": payload.get("reason", "manual"),
                "generatedAt": int(time.time() * 1000),
                "totalViolations": 0,
                "files": [],
                "scannedFiles": 0,
                "pythonRuntime": sys.version,
            }
        )
        return

    entries = threaded_scan(root, targets)
    files = aggregate_violations(root, entries)
    total = sum(item["violations"] for item in files)
    emit(
        {
            "type": "ruff-summary",
            "reason": payload.get("reason", "manual"),
            "generatedAt": int(time.time() * 1000),
            "totalViolations": total,
            "files": files,
            "scannedFiles": len(targets),
            "pythonRuntime": sys.version,
        }
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stdio", action="store_true")
    args = parser.parse_args()

    if not args.stdio:
        sys.stderr.write("entropy_scan.py expects --stdio mode\n")
        return 2

    for raw_line in sys.stdin:
        line = raw_line.lstrip("\ufeff").strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError("payload must be an object")
            message_type = payload.get("type")
            if message_type != "scan":
                emit(
                    {
                        "type": "error",
                        "source": "python",
                        "message": f"unknown request type: {message_type}",
                    }
                )
                continue
            handle_scan(payload)
        except Exception as error:  # noqa: BLE001
            emit(
                {
                    "type": "error",
                    "source": "python",
                    "message": str(error),
                }
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
