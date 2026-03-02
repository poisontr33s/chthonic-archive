#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: mailbox_check.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🔥 THE FOUNDRY
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Mailbox Check (continuation-first).

This script makes "check your mail" mean something operational:
- Read mailbox manifest (if present).
- Find the newest SESSION_HANDOFF_*.md (fallback: newest *.md).
- Extract a continuation summary: what changed, how to verify, what's next, blockers.
- Optionally emit a response handoff skeleton into the other mailbox.
- Verify handoff presence across canonical and shadow mailbox roots.
- Orchestrate mailbox ops (Postman handoff, Scribe packet refresh, Polisher cleanup).

No network. No non-stdlib deps.

@SID:           TOOL_MAILBOX_CHECK_V1
@Shabti:        CLI Script
@Purpose:       Mailbox Check (continuation-first).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RE_HM_START = re.compile(r"^---\s*$")
RE_HM_KV = re.compile(r"^([A-Za-z0-9_-]+)\s*:\s*(.*?)\s*$")
RE_SECTION = re.compile(r"^#{1,6}\s+(.+?)\s*$")
RE_MD_LINK = re.compile(r"\[([^\]\n]+)\]\(([^)\n]+)\)")
RE_MD_LINK_MALFORMED_BRACKET = re.compile(r"\[([^\]\n]+)\]\(([^)\n\]]+)\]")
RE_INLINE_CODE_SPAN = re.compile(r"(`+)([^`]*?)\1")
REPO_ROOT = Path.cwd().resolve()

MAILBOX_ALIASES: dict[str, str] = {
    "codex": "codex/mailbox",
    "claude": "claude/mailbox",
    "gemini": "gemini/mailbox",
    ".codex": ".codex/mailbox",
    ".claude": ".claude/mailbox",
}

DEFAULT_VERIFY_ROOTS = "codex,claude,.codex,.claude,claude-codex-gemini"
GENERIC_LINK_LABELS = {
    "file",
    "files",
    "path",
    "paths",
    "pathtofile",
    "pathtofiles",
    "pathoffile",
    "pathoffiles",
    "path-to-file",
    "path-to-files",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def mailbox_root(name: str) -> Path:
    path = MAILBOX_ALIASES.get(name)
    if not path:
        raise SystemExit(
            f"Unknown mailbox: {name!r} "
            + f"(expected one of: {','.join(sorted(MAILBOX_ALIASES))})"
        )
    return Path(path)


def canonical_lane(name: str) -> str:
    if name in {"codex", "claude", "gemini"}:
        return name
    if name == ".codex":
        return "codex"
    if name == ".claude":
        return "claude"
    return name


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_frontmatter(md: str) -> tuple[dict[str, str], str]:
    lines = md.splitlines()
    if not lines or not RE_HM_START.match(lines[0]):
        return {}, md
    end = None
    for i in range(1, len(lines)):
        if RE_HM_START.match(lines[i]):
            end = i
            break
    if end is None:
        return {}, md
    fm: dict[str, str] = {}
    for ln in lines[1:end]:
        m = RE_HM_KV.match(ln)
        if not m:
            continue
        fm[m.group(1).strip()] = m.group(2).strip()
    body = "\n".join(lines[end + 1 :])
    return fm, body


def newest_file(root: Path, pattern: str) -> Path | None:
    items = sorted(root.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return items[0] if items else None


def newest_file_recursive(root: Path, pattern: str) -> Path | None:
    items = sorted(root.rglob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return items[0] if items else None


def pick_primary_message(root: Path) -> Path | None:
    # Continuation-first: prefer handoffs over chronicles/payload.
    p = newest_file(root, "SESSION_HANDOFF_*.md")
    if p:
        return p
    return newest_file(root, "*.md")


@dataclass(frozen=True)
class MessageSummary:
    path: Path
    frontmatter: dict[str, str]
    title: str
    key_sections: dict[str, str]


@dataclass(frozen=True)
class HandoffRootAudit:
    token: str
    path: str
    exists: bool
    recursive: bool
    md_count: int
    handoff_count: int
    latest_handoff: str | None
    latest_handoff_mtime: str | None
    latest_markdown: str | None
    latest_markdown_mtime: str | None
    is_shadow_mailbox: bool
    shadow_non_gitkeep_files: list[str]
    notes: list[str]


def extract_sections(body: str, wanted: set[str]) -> dict[str, str]:
    current: str | None = None
    buf: dict[str, list[str]] = {}
    for ln in body.splitlines():
        m = RE_SECTION.match(ln)
        if m:
            name = m.group(1).strip()
            current = name
            if name in wanted and name not in buf:
                buf[name] = []
            continue
        if current in wanted:
            buf.setdefault(current, []).append(ln)
    out: dict[str, str] = {}
    for k, lines in buf.items():
        text = "\n".join(lines).strip()
        if text:
            out[k] = text
    return out


def summarize_message(path: Path) -> MessageSummary:
    raw = path.read_text(encoding="utf-8", errors="replace")
    fm, body = parse_frontmatter(raw)
    title = path.name
    # Prefer first H1 as title.
    for ln in body.splitlines():
        if ln.startswith("# "):
            title = ln[2:].strip()
            break
    wanted = {
        "What I Did (Concrete Changes)",
        "What I Did",
        "Actions Taken",
        "How to verify",
        "How To Verify",
        "Next Actions",
        "What’s next",
        "What's next",
        "Blockers",
    }
    sections = extract_sections(body, wanted)
    return MessageSummary(path=path, frontmatter=fm, title=title, key_sections=sections)


def print_inbox(root: Path) -> None:
    print(f"Mailbox: {root.as_posix()}")
    manifest = root / "mailbox_manifest.json"
    if manifest.exists():
        m = read_json(manifest)
        print(f"- manifest: {manifest.as_posix()}")
        print(f"- generated_on: {m.get('generated_on', '?')}")
        active = m.get("active", {})
        md = active.get("md", [])
        js = active.get("json", [])
        print(f"- active_md: {len(md)}")
        print(f"- active_json: {len(js)}")
    else:
        print("- manifest: (missing)")

    primary = pick_primary_message(root)
    if not primary:
        print("- primary: (no .md files)")
        return

    s = summarize_message(primary)
    print(f"- primary: {primary.name}")
    if s.frontmatter:
        for k in ("type", "from", "to", "created", "priority", "scope"):
            if k in s.frontmatter:
                print(f"  - {k}: {s.frontmatter[k]}")
    print(f"- title: {s.title}")

    # Continuation summary
    for k in (
        "What I Did (Concrete Changes)",
        "What I Did",
        "Actions Taken",
        "How to verify",
        "How To Verify",
        "Next Actions",
        "What's next",
        "What’s next",
        "Blockers",
    ):
        if k in s.key_sections:
            print("")
            print(f"## {k}")
            print(s.key_sections[k])


def parse_roots_csv(value: str) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for chunk in (value or "").split(","):
        token = chunk.strip()
        if not token or token in seen:
            continue
        seen.add(token)
        out.append(token)
    return out


def resolve_root_token(token: str) -> tuple[str, Path, bool]:
    # returns: (display token, resolved path, recursive scan flag)
    if token in MAILBOX_ALIASES:
        return token, Path(MAILBOX_ALIASES[token]), False
    if token == "claude-codex-gemini":
        return token, Path("claude-codex-gemini"), True
    # Treat any other value as explicit path.
    return token, Path(token), True


def count_glob(root: Path, pattern: str, recursive: bool) -> int:
    if recursive:
        return sum(1 for _ in root.rglob(pattern))
    return sum(1 for _ in root.glob(pattern))


def audit_handoff_root(token: str) -> HandoffRootAudit:
    token, root, recursive = resolve_root_token(token)
    exists = root.exists()
    if not exists:
        return HandoffRootAudit(
            token=token,
            path=root.as_posix(),
            exists=False,
            recursive=recursive,
            md_count=0,
            handoff_count=0,
            latest_handoff=None,
            latest_handoff_mtime=None,
            latest_markdown=None,
            latest_markdown_mtime=None,
            is_shadow_mailbox=token in {".codex", ".claude"},
            shadow_non_gitkeep_files=[],
            notes=["missing_root"],
        )

    if recursive:
        md_count = count_glob(root, "*.md", True)
        handoff_count = count_glob(root, "*HANDOFF*.md", True)
        latest_handoff_path = newest_file_recursive(root, "*HANDOFF*.md")
        latest_md_path = newest_file_recursive(root, "*.md")
    else:
        md_count = count_glob(root, "*.md", False)
        handoff_count = count_glob(root, "SESSION_HANDOFF_*.md", False)
        latest_handoff_path = newest_file(root, "SESSION_HANDOFF_*.md")
        latest_md_path = newest_file(root, "*.md")

    latest_handoff = (
        latest_handoff_path.relative_to(REPO_ROOT).as_posix()
        if latest_handoff_path and latest_handoff_path.is_relative_to(REPO_ROOT)
        else (latest_handoff_path.as_posix() if latest_handoff_path else None)
    )
    latest_markdown = (
        latest_md_path.relative_to(REPO_ROOT).as_posix()
        if latest_md_path and latest_md_path.is_relative_to(REPO_ROOT)
        else (latest_md_path.as_posix() if latest_md_path else None)
    )

    shadow_non_gitkeep_files: list[str] = []
    notes: list[str] = []
    is_shadow = token in {".codex", ".claude"}
    if is_shadow:
        for p in sorted(root.iterdir()):
            if not p.is_file():
                continue
            if p.name == ".gitkeep":
                continue
            shadow_non_gitkeep_files.append(p.name)
        if shadow_non_gitkeep_files:
            notes.append("shadow_mailbox_not_empty")
        else:
            notes.append("shadow_mailbox_clean")

    if handoff_count == 0:
        notes.append("no_handoff_files_detected")
    else:
        notes.append("handoff_files_present")

    return HandoffRootAudit(
        token=token,
        path=root.as_posix(),
        exists=True,
        recursive=recursive,
        md_count=md_count,
        handoff_count=handoff_count,
        latest_handoff=latest_handoff,
        latest_handoff_mtime=(
            datetime.fromtimestamp(latest_handoff_path.stat().st_mtime, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            if latest_handoff_path
            else None
        ),
        latest_markdown=latest_markdown,
        latest_markdown_mtime=(
            datetime.fromtimestamp(latest_md_path.stat().st_mtime, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            if latest_md_path
            else None
        ),
        is_shadow_mailbox=is_shadow,
        shadow_non_gitkeep_files=shadow_non_gitkeep_files,
        notes=notes,
    )


def build_verify_payload(tokens: list[str]) -> dict[str, Any]:
    audits = [audit_handoff_root(token) for token in tokens]
    missing = [a.path for a in audits if not a.exists]
    no_handoffs = [a.path for a in audits if a.exists and a.handoff_count == 0]
    shadow_violations = [a.path for a in audits if a.shadow_non_gitkeep_files]
    return {
        "generated_on": utc_now(),
        "schema_version": 1,
        "roots": [a.__dict__ for a in audits],
        "summary": {
            "root_count": len(audits),
            "existing_roots": len([a for a in audits if a.exists]),
            "missing_roots": len(missing),
            "roots_without_handoff": len(no_handoffs),
            "shadow_mailbox_violations": len(shadow_violations),
        },
        "issues": {
            "missing_roots": missing,
            "roots_without_handoff": no_handoffs,
            "shadow_mailbox_violations": shadow_violations,
        },
    }


def print_verify(payload: dict[str, Any]) -> None:
    print("Handoff Verification Matrix")
    print(f"- generated_on: {payload.get('generated_on')}")
    summary = payload.get("summary", {})
    print(
        "- summary: "
        + f"roots={summary.get('root_count')} "
        + f"existing={summary.get('existing_roots')} "
        + f"missing={summary.get('missing_roots')} "
        + f"no_handoff={summary.get('roots_without_handoff')} "
        + f"shadow_violations={summary.get('shadow_mailbox_violations')}"
    )
    print("")
    for row in payload.get("roots", []):
        print(f"- {row.get('token')} -> {row.get('path')}")
        print(
            "  "
            + f"exists={row.get('exists')} "
            + f"recursive={row.get('recursive')} "
            + f"md_count={row.get('md_count')} "
            + f"handoff_count={row.get('handoff_count')}"
        )
        print(
            "  "
            + f"latest_handoff={row.get('latest_handoff')} "
            + f"latest_handoff_mtime={row.get('latest_handoff_mtime')}"
        )
        if row.get("is_shadow_mailbox"):
            print(
                "  "
                + f"shadow_non_gitkeep_files={row.get('shadow_non_gitkeep_files')}"
            )
        print("  " + f"notes={row.get('notes')}")


def write_verify_report(payload: dict[str, Any], lane: str, name: str) -> Path:
    root = mailbox_root(lane)
    root.mkdir(parents=True, exist_ok=True)
    out_path = root / name
    lines = [
        "---",
        "type: mailbox-handoff-verification",
        "from: mailbox-handoff-skill",
        f"to: {canonical_lane(lane)}",
        f"created: {utc_now()}",
        "priority: inform",
        "---",
        "",
        "# Mailbox Handoff Verification",
        "",
        f"- Generated: `{payload.get('generated_on')}`",
        "",
        "## Summary",
    ]
    summary = payload.get("summary", {})
    for key in (
        "root_count",
        "existing_roots",
        "missing_roots",
        "roots_without_handoff",
        "shadow_mailbox_violations",
    ):
        lines.append(f"- {key}: `{summary.get(key)}`")
    lines.extend(["", "## Roots"])
    for row in payload.get("roots", []):
        lines.append(f"- `{row.get('token')}` -> `{row.get('path')}`")
        lines.append(
            f"  exists=`{row.get('exists')}` handoff_count=`{row.get('handoff_count')}` latest_handoff=`{row.get('latest_handoff')}`"
        )
        lines.append(f"  notes=`{row.get('notes')}`")
    lines.extend(["", "## Issues"])
    issues = payload.get("issues", {})
    for key in ("missing_roots", "roots_without_handoff", "shadow_mailbox_violations"):
        lines.append(f"- {key}: `{issues.get(key)}`")
    out_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return out_path


def run_cmd(cmd: list[str]) -> None:
    proc = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.stdout:
        print(proc.stdout.rstrip())
    if proc.stderr:
        print(proc.stderr.rstrip())
    if proc.returncode != 0:
        raise SystemExit(f"Command failed ({proc.returncode}): {' '.join(cmd)}")


def run_postman(
    *,
    target: str,
    source: str | None,
    inbox: str | None,
    send_latest: bool,
    send_all: bool,
) -> None:
    cmd = ["pwsh", "-File", "scripts/mailbox_handoff.ps1", "-Target", target]
    if source:
        cmd.extend(["-Source", source])
    if inbox:
        cmd.extend(["-Inbox", inbox])
    if send_latest:
        cmd.append("-SendLatest")
    if send_all:
        cmd.append("-SendAll")
    run_cmd(cmd)


def run_scribe(target: str) -> None:
    packet = f"{canonical_lane(target)}/mailbox/TETRAGRAMMATON_PACKET.md"
    cmd = ["uv", "run", "scripts/mailbox_scribe.py", "--target", canonical_lane(target), "--packet", packet]
    run_cmd(cmd)


def run_polisher(target: str, apply: bool) -> None:
    cmd = ["uv", "run", "scripts/mailbox_polisher.py", "--target", canonical_lane(target)]
    if apply:
        cmd.append("--apply")
    run_cmd(cmd)


def to_repo_relative(path: Path) -> str:
    if path.is_relative_to(REPO_ROOT):
        return path.relative_to(REPO_ROOT).as_posix()
    return path.as_posix()


def build_basename_index() -> dict[str, list[Path]]:
    skip_dirs = {".git", "node_modules", "target", "__pycache__", ".venv", "venv"}
    out: dict[str, list[Path]] = {}
    for p in REPO_ROOT.rglob("*"):
        if not p.is_file():
            continue
        if any(part in skip_dirs for part in p.parts):
            continue
        out.setdefault(p.name, []).append(p)
    return out


def resolve_markdown_target(md_file: Path, target: str) -> Path | None:
    candidate = target.strip()
    if not candidate:
        return None
    # Ignore URLs, anchors, and data URIs.
    if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", candidate):
        return None
    if candidate.startswith("#"):
        return None
    candidate = candidate.split("#", 1)[0].split("?", 1)[0].strip()
    if not candidate:
        return None
    # Mailbox canonical convention: "./..." is repo-root relative.
    if candidate.startswith("./"):
        return (REPO_ROOT / candidate[2:]).resolve(strict=False)
    if candidate.startswith(".\\"):
        return (REPO_ROOT / candidate[2:]).resolve(strict=False)
    if candidate.startswith("/"):
        return (REPO_ROOT / candidate.lstrip("/")).resolve(strict=False)
    return (md_file.parent / candidate).resolve(strict=False)


def needs_label_qualifier(label: str, basename: str) -> bool:
    clean = label.strip()
    if not clean:
        return True
    # Any explicit path or qualifier counts as already disambiguated.
    if "/" in clean or "\\" in clean:
        return False
    if "(" in clean and ")" in clean:
        return False
    low = clean.lower()
    if low in GENERIC_LINK_LABELS:
        return True
    if low == basename.lower():
        return True
    return False


def report_line(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def canonical_link_label(resolved_target: Path) -> str:
    basename = resolved_target.name
    parent = resolved_target.parent
    parent_label = to_repo_relative(parent)
    return f"{basename} ({parent_label})"


def transform_non_code_segments(line: str, transform: Any) -> str:
    """
    Apply transform() only to non-inline-code segments in a line.
    Splits on single backticks and preserves code spans untouched.
    """
    parts = line.split("`")
    if len(parts) <= 1:
        return transform(line)
    out: list[str] = []
    for idx, chunk in enumerate(parts):
        if idx % 2 == 0:
            out.append(transform(chunk))
        else:
            out.append(chunk)
    return "`".join(out)


def run_link_canon(
    *,
    files: list[str],
    apply: bool,
    max_findings: int,
) -> int:
    if not files:
        return 0

    basename_index = build_basename_index()
    issues = 0

    for raw_path in files:
        md_path = Path(raw_path)
        if not md_path.is_absolute():
            md_path = (REPO_ROOT / md_path).resolve(strict=False)
        if not md_path.exists() or not md_path.is_file():
            print(f"[link-canon] missing file: {raw_path}")
            issues += 1
            continue
        if md_path.suffix.lower() != ".md":
            print(f"[link-canon] skip non-markdown: {to_repo_relative(md_path)}")
            continue

        text = md_path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines(keepends=True)
        findings: list[str] = []
        malformed_count = 0
        missing_count = 0
        ambiguous_count = 0
        in_fence = False

        for idx, original in enumerate(lines, start=1):
            line = original.rstrip("\r\n")
            stripped = line.strip()
            if stripped.startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue

            non_code = RE_INLINE_CODE_SPAN.sub("", line)
            for m in RE_MD_LINK_MALFORMED_BRACKET.finditer(non_code):
                malformed_count += 1
                findings.append(
                    f"L{idx}: malformed link `{m.group(0)}` -> expected `[{m.group(1)}]({m.group(2)})`"
                )

            for m in RE_MD_LINK.finditer(non_code):
                label = m.group(1).strip()
                target = m.group(2).strip()
                resolved = resolve_markdown_target(md_path, target)
                if not resolved:
                    continue
                if not resolved.exists():
                    missing_count += 1
                    findings.append(
                        f"L{idx}: missing path for link `{m.group(0)}` -> `{to_repo_relative(resolved)}`"
                    )
                    continue
                dupes = basename_index.get(resolved.name, [])
                if len(dupes) > 1 and needs_label_qualifier(label, resolved.name):
                    ambiguous_count += 1
                    new_label = canonical_link_label(resolved)
                    findings.append(
                        f"L{idx}: ambiguous duplicate basename `{resolved.name}` -> suggest `[{new_label}]({target})`"
                    )

        updated_lines = list(lines)
        applied_changes = 0
        if apply:
            in_fence_apply = False
            for idx, original in enumerate(updated_lines):
                line = original.rstrip("\r\n")
                newline = original[len(line):]
                stripped = line.strip()
                if stripped.startswith("```"):
                    in_fence_apply = not in_fence_apply
                    continue
                if in_fence_apply:
                    continue
                if "`" in line:
                    # Avoid mutating inline code examples.
                    continue

                def _transform(chunk: str) -> str:
                    fixed = RE_MD_LINK_MALFORMED_BRACKET.sub(
                        lambda mm: f"[{mm.group(1)}]({mm.group(2)})",
                        chunk,
                    )

                    def _rewrite_link(mm: re.Match[str]) -> str:
                        nonlocal applied_changes
                        label = mm.group(1).strip()
                        target = mm.group(2).strip()
                        resolved = resolve_markdown_target(md_path, target)
                        if not resolved or not resolved.exists():
                            return mm.group(0)
                        dupes = basename_index.get(resolved.name, [])
                        if len(dupes) <= 1:
                            return mm.group(0)
                        if not needs_label_qualifier(label, resolved.name):
                            return mm.group(0)
                        applied_changes += 1
                        return f"[{canonical_link_label(resolved)}]({target})"

                    return RE_MD_LINK.sub(_rewrite_link, fixed)

                transformed = transform_non_code_segments(line, _transform) + newline
                updated_lines[idx] = transformed

            updated = "".join(updated_lines)
            if updated != text:
                md_path.write_text(updated, encoding="utf-8")

        mode = "apply" if apply else "dry-run"
        print(f"[link-canon:{mode}] {to_repo_relative(md_path)}")
        print(
            "  "
            + f"malformed={malformed_count} missing={missing_count} ambiguous={ambiguous_count} "
            + f"rewritten={applied_changes if apply else 0}"
        )

        if findings:
            issues += len(findings)
            for line in findings[:max_findings]:
                print(f"  - {line}")
            if len(findings) > max_findings:
                print(f"  - ... {len(findings) - max_findings} more findings")

    return issues


def write_response(
    *,
    src_mailbox: str,
    dst_mailbox: str,
    in_response_to: str,
    subject: str,
    context_md: str,
    out_path: Path,
) -> None:
    today = datetime.now().strftime("%Y-%m-%d")
    text = "\n".join(
        [
            "---",
            "type: handoff",
            f"from: {src_mailbox}",
            f"to: {dst_mailbox}",
            f"created: {today}",
            "priority: inform",
            f"in_response_to: {in_response_to}",
            "---",
            "",
            f"# Response: {subject}",
            "",
            "## Context (From Incoming Handoff)",
            context_md.strip() if context_md.strip() else "- (none extracted)",
            "",
            "## Actions Taken",
            "-",
            "",
            "## Files Changed",
            "-",
            "",
            "## Tests",
            "- Not run",
            "",
            "## Next Actions",
            "-",
            "",
        ]
    )
    out_path.write_text(text + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mailbox", choices=sorted(MAILBOX_ALIASES), default="codex")
    ap.add_argument("--mode", choices=["inbox", "verify", "link-canon"], default="inbox")
    ap.add_argument("--verify-roots", default=DEFAULT_VERIFY_ROOTS)
    ap.add_argument("--json", action="store_true", help="Emit JSON for --mode verify.")
    ap.add_argument("--emit-report", action="store_true", help="Write markdown verify report to mailbox.")
    ap.add_argument("--report-target", choices=["codex", "claude", "gemini"], default="codex")
    ap.add_argument("--report-name", default="MAILBOX_HANDOFF_VERIFICATION_LATEST.md")
    ap.add_argument("--emit-response", action="store_true")
    ap.add_argument("--to", choices=["codex", "claude", "gemini"], help="Response target mailbox.")
    ap.add_argument(
        "--subject",
        default=None,
        help="Optional response subject. If omitted, derives from the newest handoff title.",
    )
    ap.add_argument("--postman-target", choices=["codex", "claude"])
    ap.add_argument("--postman-source", default="")
    ap.add_argument("--postman-inbox", default="")
    ap.add_argument("--send-latest", action="store_true")
    ap.add_argument("--send-all", action="store_true")
    ap.add_argument("--scribe-target", choices=["codex", "claude", "gemini"])
    ap.add_argument("--polish-target", choices=["codex", "claude", "gemini"])
    ap.add_argument("--polish-apply", action="store_true")
    ap.add_argument(
        "--link-canon-file",
        action="append",
        default=[],
        help="Markdown file to validate/fix [label](path) links. Repeatable.",
    )
    ap.add_argument(
        "--link-canon-apply",
        action="store_true",
        help="Apply link canon fixes in-place. Default is dry-run.",
    )
    ap.add_argument(
        "--link-canon-max-findings",
        type=int,
        default=40,
        help="Max findings to print per file (default: 40).",
    )
    ap.add_argument(
        "--link-canon-no-fail",
        action="store_true",
        help="Do not fail when dry-run finds link issues.",
    )
    args = ap.parse_args()

    root = mailbox_root(args.mailbox)
    root.mkdir(parents=True, exist_ok=True)

    if args.mode == "inbox":
        print_inbox(root)
    elif args.mode == "verify":
        tokens = parse_roots_csv(args.verify_roots)
        if not tokens:
            raise SystemExit("--verify-roots produced no tokens")
        payload = build_verify_payload(tokens)
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print_verify(payload)
        if args.emit_report:
            path = write_verify_report(payload, args.report_target, args.report_name)
            print("")
            print(f"Wrote verification report: {path.as_posix()}")
    elif args.mode == "link-canon":
        # Dedicated mode: run only link canon checks/fixes.
        pass

    if args.emit_response:
        if not args.to:
            raise SystemExit("--emit-response requires --to codex|claude|gemini")
        primary = pick_primary_message(root)
        if not primary:
            raise SystemExit("No primary .md message to respond to.")
        summary = summarize_message(primary)
        subject = args.subject
        if not subject:
            subject = summary.title.replace("\n", " ").strip()
        dst_root = mailbox_root(args.to)
        dst_root.mkdir(parents=True, exist_ok=True)
        out_name = f"SESSION_HANDOFF_{datetime.now().strftime('%Y_%m_%d')}_RESPONSE.md"
        out_path = dst_root / out_name
        # Pre-fill context from the incoming handoff so responses are not empty ceremony.
        ctx_parts: list[str] = []
        for key in (
            "What I Did (Concrete Changes)",
            "What I Did",
            "Actions Taken",
            "How to verify",
            "How To Verify",
            "Next Actions",
            "What's next",
            "What’s next",
            "Blockers",
        ):
            val = summary.key_sections.get(key)
            if not val:
                continue
            ctx_parts.append(f"### {key}\n{val.strip()}")
        context_md = "\n\n".join(ctx_parts)
        write_response(
            src_mailbox=args.mailbox,
            dst_mailbox=args.to,
            in_response_to=primary.name,
            subject=subject,
            context_md=context_md,
            out_path=out_path,
        )
        print("")
        print(f"Wrote response skeleton: {out_path.as_posix()}")

        # Creation-time guard: validate/fix links in the newly generated handoff.
        auto_findings = run_link_canon(
            files=[out_path.as_posix()],
            apply=bool(args.link_canon_apply),
            max_findings=max(1, int(args.link_canon_max_findings)),
        )
        if auto_findings > 0 and not args.link_canon_apply and not args.link_canon_no_fail:
            raise SystemExit(
                f"new response handoff has {auto_findings} link issue(s). "
                + "Re-run with --link-canon-apply to fix."
            )

    if args.postman_target:
        source = args.postman_source.strip() or None
        inbox = args.postman_inbox.strip() or None
        if bool(source) == bool(inbox):
            raise SystemExit(
                "--postman-target requires exactly one of --postman-source or --postman-inbox"
            )
        if inbox and not (args.send_latest or args.send_all):
            raise SystemExit("--postman-inbox requires --send-latest or --send-all")
        if args.send_latest and args.send_all:
            raise SystemExit("Choose one: --send-latest or --send-all")
        run_postman(
            target=args.postman_target,
            source=source,
            inbox=inbox,
            send_latest=bool(args.send_latest),
            send_all=bool(args.send_all),
        )

    if args.scribe_target:
        run_scribe(args.scribe_target)

    if args.polish_target:
        run_polisher(args.polish_target, bool(args.polish_apply))

    if args.link_canon_file:
        finding_count = run_link_canon(
            files=args.link_canon_file,
            apply=bool(args.link_canon_apply),
            max_findings=max(1, int(args.link_canon_max_findings)),
        )
        if finding_count > 0 and not args.link_canon_apply and not args.link_canon_no_fail:
            raise SystemExit(
                f"link-canon dry-run found {finding_count} issue(s). "
                + "Re-run with --link-canon-apply to fix."
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
