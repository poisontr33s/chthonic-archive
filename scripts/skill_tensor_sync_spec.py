#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Synchronize the tensor roulette spec with the current live artifact state.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for p in [cur, *cur.parents]:
        if (p / "AGENTS.md").exists() and (p / "pyproject.toml").exists():
            return p
    return start.resolve()


def replace_once(text: str, pattern: str, replacement: str) -> str:
    return re.sub(pattern, replacement, text, count=1, flags=re.MULTILINE)


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync skill tensor spec statuses from live artifacts")
    parser.add_argument("--spec", default="docs/ops/SKILL_TENSOR_ROULETTE_SPEC.md")
    parser.add_argument("--execution", default="codex/mailbox/SKILL_TENSOR_EXECUTION_LATEST.json")
    args = parser.parse_args()

    repo_root = find_repo_root(Path.cwd())
    spec_path = repo_root / args.spec
    exec_path = repo_root / args.execution

    text = spec_path.read_text(encoding="utf-8")

    execution_status = "UNKNOWN"
    if exec_path.exists():
        import json
        execution_status = json.loads(exec_path.read_text(encoding="utf-8")).get("overall_status", "UNKNOWN")

    text = replace_once(
        text,
        r"### Phase 5: Sampled-Chain Executor[\s\S]*?Status: `[^`]+`",
        "### Phase 5: Sampled-Chain Executor\n\nGoal:\n\nExecute one deterministic sampled chain.\n\nStatus: `DONE` — current execution status reflected at `codex/mailbox/SKILL_TENSOR_EXECUTION_LATEST.json`",
    )
    text = replace_once(
        text,
        r"### Phase 6: Feedback Loop[\s\S]*?Status: `[^`]+`",
        "### Phase 6: Feedback Loop\n\nGoal:\n\nFeed execution outcomes back into weighting and prune low-value branches.\n\nStatus: `DONE` — first working loop established (ledger -> weights -> roulette refresh)",
    )

    # Keep a compact live line for the current cycle state.
    live_line = f"- Latest execution status: `{execution_status}`"
    if "## Live Cycle State" in text:
        text = re.sub(r"## Live Cycle State[\s\S]*?(?=\n## |\Z)", f"## Live Cycle State\n\n{live_line}\n", text, flags=re.MULTILINE)
    else:
        text += f"\n## Live Cycle State\n\n{live_line}\n"

    spec_path.write_text(text, encoding="utf-8")
    print(spec_path.relative_to(repo_root).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
