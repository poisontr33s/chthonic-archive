#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @SID: TOOL_DSL_ITERATION_CHECK_V1

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: dsl_iteration_check.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: AMETHYST
# ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ .chthonic/grammar/chthonic.peg       (Canonical Phase 0 grammar)
# ║   └─◄ tools/dsl-smoke/                     (Iteration tool suite)
# ║   └─◄ manifest/dsl_iteration_history.ndjson (Time-series ledger this script writes)
# ╚════════════════════════════════════════════════════════════════════════════

"""
TOOL_DSL_ITERATION_CHECK_V1 — Iteration ledger + regression detector.

Runs the dsl-smoke + dsl-audit binaries against the current canonical
grammar (.chthonic/grammar/chthonic.peg), parses their output into
structured form, and appends one row to manifest/dsl_iteration_history.ndjson.

Compares the new row to the previous row and reports regressions:
  - parse_rate_drop  : a slice that previously parsed now fails
  - shadow_rise      : audit shadow count > previous
  - plateau          : same first-failure position 2+ runs in a row
  - new_failure_class : a previously-clean error code appears
  - coverage_drop    : SSOT paren coverage % fell vs previous row
  - pattern_pass_drop: a conformance pattern that passed now fails
                       (also flags dsl-pattern-test's own no-regressions signal)

Exit codes:
  0  no regressions
  1  regressions detected (rewindability signal — consider git revert)
  2  smoke or audit subprocess failed

Usage:
  uv run scripts/dsl_iteration_check.py                  # check + ledger update
  uv run scripts/dsl_iteration_check.py --dry-run        # check, don't update ledger
  uv run scripts/dsl_iteration_check.py --no-regression-exit  # always exit 0
  uv run scripts/dsl_iteration_check.py --show-history N      # show last N rows
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
GRAMMAR_PATH = REPO_ROOT / ".chthonic" / "grammar" / "chthonic.peg"
LEDGER_PATH = REPO_ROOT / "manifest" / "dsl_iteration_history.ndjson"
SSOT_PATH = REPO_ROOT / ".chthonic" / "SSOT.md"


def grammar_hash() -> str:
    if not GRAMMAR_PATH.exists():
        return "absent"
    h = hashlib.sha256()
    h.update(GRAMMAR_PATH.read_bytes())
    return h.hexdigest()[:16]


def git_head_sha() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        )
        return out.stdout.strip()[:12]
    except subprocess.CalledProcessError:
        return "unknown"


def run_smoke() -> tuple[int, str, str]:
    proc = subprocess.run(
        ["cargo", "run", "-p", "dsl-smoke", "--release", "--bin", "dsl-smoke",
         "--quiet", "--", str(SSOT_PATH)],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def run_audit() -> tuple[int, str, str]:
    proc = subprocess.run(
        ["cargo", "run", "-p", "dsl-smoke", "--release", "--bin", "dsl-audit",
         "--quiet", "--", str(SSOT_PATH)],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def run_full_smoke() -> tuple[int, str, str]:
    """Full-SSOT smoke — parses the entire 10,532-line catalyst as one program."""
    proc = subprocess.run(
        ["cargo", "run", "-p", "dsl-smoke", "--release", "--bin", "dsl-full-smoke",
         "--quiet", "--", str(SSOT_PATH)],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def run_pattern_test() -> tuple[int, str, str]:
    """Conformance bench — every (name, example, expected_rule) triple in patterns.json."""
    proc = subprocess.run(
        ["cargo", "run", "-p", "dsl-smoke", "--release", "--bin", "dsl-pattern-test", "--quiet"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def run_coverage() -> tuple[int, str, str]:
    """Paren-occurrence coverage over the full SSOT — the headline progress metric."""
    proc = subprocess.run(
        ["cargo", "run", "-p", "dsl-smoke", "--release", "--bin", "dsl-coverage",
         "--quiet", "--", str(SSOT_PATH)],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def parse_pattern_test(output: str) -> dict:
    res = {"pass": None, "fail_expected": None, "no_regressions": None}
    if (m := PATTERN_PASS_RE.search(output)):
        res["pass"] = int(m.group("n"))
    if (m := PATTERN_FAILEXP_RE.search(output)):
        res["fail_expected"] = int(m.group("n"))
    res["no_regressions"] = bool(PATTERN_NOREG_RE.search(output))
    return res


def parse_coverage(output: str) -> dict:
    res = {"matched": None, "total": None, "pct": None}
    if (m := COVERAGE_RE.search(output)):
        res["matched"] = int(m.group("matched"))
        res["total"] = int(m.group("total"))
        res["pct"] = float(m.group("pct"))
    return res


SLICE_RE = re.compile(r"SLICE: (?P<label>[^\n]+)")
PARSE_RE = re.compile(r"PARSE: (?P<status>OK|FAIL)")
FAIL_POS_RE = re.compile(r"-->\s*(?P<line>\d+):(?P<col>\d+)")
EXPECT_RE = re.compile(r"= expected (?P<expected>[^\n]+)")
SHADOW_TOTAL_RE = re.compile(r"TOTAL CONFIRMED SHADOW FAILURES:\s*(?P<n>\d+)")
SHADOW_LINE_RE = re.compile(r"\[SHADOW-CONFIRMED\] (?P<slice>[^:]+): prose_parens contains '(?P<marker>[^']+)'")
FULL_PARSE_OK_RE = re.compile(r"PARSE: OK — entire catalyst parses")
FULL_PARSE_FAIL_RE = re.compile(r"PARSE: FAIL — full catalyst does not parse")
FULL_FAIL_BISECT_RE = re.compile(r"First failing prefix: lines 1\.\.(?P<n>\d+)")
PATTERN_PASS_RE = re.compile(r"PASS:\s*(?P<n>\d+)")
PATTERN_FAILEXP_RE = re.compile(r"FAIL \(expected\):\s*(?P<n>\d+)")
PATTERN_NOREG_RE = re.compile(r"no regressions")
COVERAGE_RE = re.compile(r"Coverage:\s*(?P<matched>\d+)/(?P<total>\d+)\s+matched_correctly\s*=\s*(?P<pct>[\d.]+)%")


def parse_smoke(output: str) -> list[dict]:
    slices = []
    current = None
    for line in output.split("\n"):
        m = SLICE_RE.search(line)
        if m:
            if current:
                slices.append(current)
            current = {"label": m.group("label").strip(), "status": "UNKNOWN",
                       "fail_line": None, "fail_col": None, "expected": None}
            continue
        if current is None:
            continue
        if (m := PARSE_RE.search(line)):
            current["status"] = m.group("status")
        if (m := FAIL_POS_RE.search(line)):
            current["fail_line"] = int(m.group("line"))
            current["fail_col"] = int(m.group("col"))
        if (m := EXPECT_RE.search(line)):
            current["expected"] = m.group("expected").strip()
    if current:
        slices.append(current)
    return slices


def parse_audit(output: str) -> tuple[int, list[dict]]:
    total = 0
    shadows = []
    if (m := SHADOW_TOTAL_RE.search(output)):
        total = int(m.group("n"))
    for line in output.split("\n"):
        if (m := SHADOW_LINE_RE.search(line)):
            shadows.append({"slice": m.group("slice").strip(),
                            "marker": m.group("marker")})
    return total, shadows


def parse_full_smoke(output: str) -> dict:
    """Parse the dsl-full-smoke output into structured form."""
    result = {"status": "UNKNOWN", "fail_line": None, "fail_col": None,
              "expected": None, "first_failing_prefix_line": None}
    if FULL_PARSE_OK_RE.search(output):
        result["status"] = "OK"
        return result
    if FULL_PARSE_FAIL_RE.search(output):
        result["status"] = "FAIL"
        if (m := FAIL_POS_RE.search(output)):
            result["fail_line"] = int(m.group("line"))
            result["fail_col"] = int(m.group("col"))
        if (m := EXPECT_RE.search(output)):
            result["expected"] = m.group("expected").strip()
        if (m := FULL_FAIL_BISECT_RE.search(output)):
            result["first_failing_prefix_line"] = int(m.group("n"))
    return result


def load_ledger() -> list[dict]:
    if not LEDGER_PATH.exists():
        return []
    rows = []
    with LEDGER_PATH.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def compare_for_regressions(current: dict, previous: dict | None) -> list[str]:
    if previous is None:
        return []
    warnings = []

    # 1. parse_rate_drop: a slice that previously parsed now fails
    prev_pass = {s["label"]: s["status"] for s in previous.get("slices", [])}
    for s in current["slices"]:
        if prev_pass.get(s["label"]) == "OK" and s["status"] != "OK":
            warnings.append(f"REGRESSION parse_rate_drop: '{s['label']}' was OK, now {s['status']}"
                            f" at L{s.get('fail_line')}:{s.get('fail_col')}")

    # 2. shadow_rise: audit shadow count increased
    cur_shadow = current.get("audit_shadow_total", 0)
    prev_shadow = previous.get("audit_shadow_total", 0)
    if cur_shadow > prev_shadow:
        warnings.append(f"REGRESSION shadow_rise: audit shadows {prev_shadow} -> {cur_shadow}")

    # 3. plateau: same fail position on same slice 2x in a row
    prev_fail_pos = {(s["label"], s.get("fail_line"), s.get("fail_col"))
                     for s in previous.get("slices", []) if s["status"] != "OK"}
    cur_fail_pos = {(s["label"], s.get("fail_line"), s.get("fail_col"))
                    for s in current["slices"] if s["status"] != "OK"}
    plateau = cur_fail_pos & prev_fail_pos
    for label, line, col in plateau:
        if line is not None:
            warnings.append(f"PLATEAU plateau: '{label}' failed at L{line}:{col} for 2+ runs")

    # 4. coverage_drop: SSOT paren coverage % fell vs prior row
    cur_cov = (current.get("coverage") or {}).get("pct")
    prev_cov = (previous.get("coverage") or {}).get("pct")
    if cur_cov is not None and prev_cov is not None and cur_cov + 0.01 < prev_cov:
        warnings.append(f"REGRESSION coverage_drop: {prev_cov}% -> {cur_cov}%")

    # 5. pattern_pass_drop: a conformance pattern that passed now fails
    cur_pp = (current.get("pattern_test") or {}).get("pass")
    prev_pp = (previous.get("pattern_test") or {}).get("pass")
    if cur_pp is not None and prev_pp is not None and cur_pp < prev_pp:
        warnings.append(f"REGRESSION pattern_pass_drop: {prev_pp} -> {cur_pp} patterns passing")
    if (current.get("pattern_test") or {}).get("no_regressions") is False:
        warnings.append("REGRESSION pattern_test: dsl-pattern-test reports regressions vs patterns.json baseline")

    return warnings


def main():
    ap = argparse.ArgumentParser(description="DSL iteration check + ledger.")
    ap.add_argument("--dry-run", action="store_true", help="Don't update ledger.")
    ap.add_argument("--no-regression-exit", action="store_true", help="Always exit 0.")
    ap.add_argument("--show-history", type=int, metavar="N",
                    help="Print last N ledger rows and exit.")
    args = ap.parse_args()

    if args.show_history is not None:
        rows = load_ledger()
        for r in rows[-args.show_history:]:
            print(json.dumps(r, indent=2, ensure_ascii=False))
        return 0

    # Run smoke
    rc, stdout, stderr = run_smoke()
    if rc != 0:
        print(f"[iteration-check] FATAL: dsl-smoke failed (rc={rc})", file=sys.stderr)
        print(stderr, file=sys.stderr)
        return 2
    slices = parse_smoke(stdout)

    # Run audit
    rc, audit_stdout, audit_stderr = run_audit()
    if rc != 0:
        print(f"[iteration-check] FATAL: dsl-audit failed (rc={rc})", file=sys.stderr)
        print(audit_stderr, file=sys.stderr)
        return 2
    shadow_total, shadows = parse_audit(audit_stdout)

    # Run full-SSOT smoke (different exit codes don't matter — we capture state)
    _, full_stdout, _ = run_full_smoke()
    full_result = parse_full_smoke(full_stdout)

    # Run pattern conformance + coverage (the metrics the grammar iteration optimizes).
    _, pt_stdout, _ = run_pattern_test()
    pattern_result = parse_pattern_test(pt_stdout)
    _, cov_stdout, _ = run_coverage()
    coverage_result = parse_coverage(cov_stdout)

    current = {
        "tool": "TOOL_DSL_ITERATION_CHECK_V1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git_head": git_head_sha(),
        "grammar_hash": grammar_hash(),
        "slice_count": len(slices),
        "slice_pass_count": sum(1 for s in slices if s["status"] == "OK"),
        "slice_fail_count": sum(1 for s in slices if s["status"] != "OK"),
        "audit_shadow_total": shadow_total,
        "full_ssot": full_result,
        "pattern_test": pattern_result,
        "coverage": coverage_result,
        "slices": slices,
        "shadow_examples": shadows[:10],  # cap detail
    }

    # Compare with previous
    ledger = load_ledger()
    previous = ledger[-1] if ledger else None
    warnings = compare_for_regressions(current, previous)
    current["regression_warnings"] = warnings

    # Output
    full_summary = full_result["status"]
    if full_result["status"] == "FAIL" and full_result["first_failing_prefix_line"]:
        full_summary = f"FAIL@L{full_result['first_failing_prefix_line']}"
    cov_pct = (coverage_result or {}).get("pct")
    pat_pass = (pattern_result or {}).get("pass")
    pat_fail_exp = (pattern_result or {}).get("fail_expected")
    print(f"[iteration-check] grammar_hash={current['grammar_hash']} "
          f"slices={current['slice_pass_count']}/{current['slice_count']} "
          f"shadows={shadow_total} "
          f"full_ssot={full_summary} "
          f"coverage={cov_pct}% "
          f"patterns={pat_pass}pass/{pat_fail_exp}expected-fail")
    if warnings:
        for w in warnings:
            print(f"  ! {w}")
        print("[iteration-check] Consider: git diff vs prior commit, OR git revert HEAD if not yet pushed.")
    else:
        print("[iteration-check] no regressions vs prior ledger row")

    # De-duplicate: skip append if grammar_hash + results identical to last row.
    # Prevents ledger pollution from rerunning without grammar changes.
    is_duplicate = (
        previous is not None
        and previous.get("grammar_hash") == current["grammar_hash"]
        and previous.get("slice_pass_count") == current["slice_pass_count"]
        and previous.get("audit_shadow_total") == current["audit_shadow_total"]
        and (previous.get("coverage") or {}).get("matched") == (current.get("coverage") or {}).get("matched")
        and (previous.get("pattern_test") or {}).get("pass") == (current.get("pattern_test") or {}).get("pass")
    )

    if not args.dry_run and not is_duplicate:
        LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LEDGER_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(current, ensure_ascii=False) + "\n")
        print(f"[iteration-check] appended ledger row -> {LEDGER_PATH.relative_to(REPO_ROOT)}")
    elif is_duplicate:
        print(f"[iteration-check] no change vs last row (grammar_hash matches) — skipping ledger append")

    if warnings and not args.no_regression_exit:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
