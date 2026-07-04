#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: catalyst_lint.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ .chthonic/SSOT.md
# ╚════════════════════════════════════════════════════════════════════════════

"""
catalyst_lint.py - Structural proofreader + safe fixer for the catalyst (SSOT.md).

@SID:           TOOL_CATALYST_LINT_V1
@Shabti:        CLI Script
@Heka-Ayni:     CONCEPT_CATALYST_LINTING
@Ankh-Tinku:    STATE_CATALYST_PROOFREAD
@Purpose:       Finds the structural defects the DSL full-parse trips on, all at
                once instead of one-per-run, and PROPOSES the fix for each so the
                work is review-and-confirm, not find-and-retype by hand (that
                manual one-off loop is the non-compounding RNG this replaces).
                Rule 1 (bold-balance): the catalyst emboldens within a single
                line, so any non-code line with an ODD count of the bold marker
                is unbalanced - an orphan that opens a bold which runs forward
                across newlines and derails the parse downstream. Fenced code
                blocks and inline-code spans are excluded (the marker is literal
                there). --apply writes only the ONE auto-safe class - header
                orphans, where the header already emboldens so the stray marker
                is pure redundancy to drop; every other finding is surfaced with
                a suggestion but never auto-touched (add-opening vs drop-trailing
                is a judgement on the sacred text).
"""

from __future__ import annotations


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SSOT = ROOT / ".chthonic" / "SSOT.md"
BOLD = "*" * 2  # the markdown bold marker, built so this file never self-flags
CODE_SPAN = re.compile(r"`[^`]*`")


def strip_code_spans(line: str) -> str:
    """Drop inline-code spans: `applyTo: \"**\"` is a literal glob, not bold."""
    return CODE_SPAN.sub("", line)


def classify(line: str) -> str:
    s = line.lstrip()
    if s.startswith("#"):
        return "header"
    if s.startswith(">"):
        return "blockquote"
    if s.startswith("|"):
        return "table-row"
    if s.startswith(("- ", "* ", "+ ")) or re.match(r"\d+[.)]\s", s):
        return "list-item"
    return "prose"


def suggest(line: str, kind: str) -> dict:
    """Propose a fix. Only the header class is auto-safe; the rest are review-only."""
    if kind == "header":
        return {
            "fix_type": "auto:drop-bold",
            "safe": True,
            "action": "header already emboldens — strip the redundant ** from the line",
            "fixed": BOLD_RE.sub("", line),
        }
    bare = strip_code_spans(line)
    if "***" in bare:
        return {
            "fix_type": "review:emphasis",
            "safe": False,
            "action": "malformed bold-italic (***...***) — normalize to the intended **label:** form",
        }
    if re.search(r"\)\*\*", bare) and "**(" not in bare:
        return {
            "fix_type": "review:restore-pair",
            "safe": False,
            "action": "paren-group with an orphan closing ** — likely wants the opening pair: **(...)**",
        }
    return {
        "fix_type": "review:ambiguous",
        "safe": False,
        "action": "add the opening ** or drop the trailing ** — needs a look",
    }


BOLD_RE = re.compile(re.escape(BOLD))


def audit_bold(text: str) -> list[dict]:
    findings: list[dict] = []
    in_fence = False
    for i, line in enumerate(text.splitlines(), start=1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if strip_code_spans(line).count(BOLD) % 2 == 1:
            kind = classify(line)
            findings.append({
                "line": i,
                "markers": strip_code_spans(line).count(BOLD),
                "kind": kind,
                "fix": suggest(line, kind),
                "text": line.strip()[:150],
            })
    return findings


def apply_safe(text: str) -> tuple[str, int]:
    """Apply only the auto-safe class (header orphans → strip **). Returns (new_text, n)."""
    out: list[str] = []
    in_fence = False
    applied = 0
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            out.append(line)
            continue
        if not in_fence and strip_code_spans(line).count(BOLD) % 2 == 1 and classify(line) == "header":
            line = BOLD_RE.sub("", line)
            applied += 1
        out.append(line)
    tail = "\n" if text.endswith("\n") else ""
    return "\n".join(out) + tail, applied


def main() -> int:
    ap = argparse.ArgumentParser(description="Structural proofreader + safe fixer for the catalyst")
    ap.add_argument("--path", default=str(SSOT), help="file to lint (default: .chthonic/SSOT.md)")
    ap.add_argument("--json", action="store_true", help="emit JSON (findings carry their proposed fix)")
    ap.add_argument("--apply", action="store_true", help="apply the auto-safe (header) fixes in place; review:* are left untouched")
    args = ap.parse_args()

    path = Path(args.path)
    text = path.read_text(encoding="utf-8")
    findings = audit_bold(text)

    if args.json:
        print(json.dumps({"path": str(path), "unbalanced_bold": len(findings),
                          "auto_safe": sum(1 for f in findings if f["fix"]["safe"]),
                          "findings": findings}, indent=2, ensure_ascii=False))
        return 1 if findings else 0

    print(f"catalyst-lint: {path.name} - {len(findings)} line(s) with unbalanced bold\n")
    by_type: dict[str, int] = {}
    for f in findings:
        ft = f["fix"]["fix_type"]
        by_type[ft] = by_type.get(ft, 0) + 1
        print(f"  L{f['line']:<6} [{f['kind']:<11}] {f['markers']}x  {f['text']}")
        print(f"         -> {ft}: {f['fix']['action']}")
    if findings:
        print("\nby fix-type: " + ", ".join(f"{k}={v}" for k, v in sorted(by_type.items())))

    if args.apply:
        new_text, applied = apply_safe(text)
        if applied and new_text != text:
            path.write_text(new_text, encoding="utf-8")
            print(f"\nAPPLIED {applied} auto-safe header fix(es) to {path.name}. review:* findings untouched.")
        else:
            print("\nNo auto-safe fixes to apply.")
    else:
        auto = sum(1 for f in findings if f["fix"]["safe"])
        print(f"\n{auto} auto-safe (header) fixable now via --apply. The rest are review:* — proposed, not auto-touched.")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
