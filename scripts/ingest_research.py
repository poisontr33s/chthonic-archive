#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: ingest_research.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Ingest research artifacts into structured mailbox digests and optional handoff notes.

Usage:
  uv run scripts/ingest_research.py [source-path]
  uv run scripts/ingest_research.py --target-mailbox codex --handoff-to claude --forward-source

@SID:           TOOL_INGEST_RESEARCH_V1
@Shabti:        CLI Script
@Purpose:       Ingest research artifacts into structured mailbox digests and optional handoff notes.
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


SUPPORTED_EXTENSIONS = {".md", ".txt", ".log", ".json", ".html", ".htm", ".pdf"}
MAILBOX_DIRS = {
    "claude": Path("claude/mailbox"),
    "codex": Path("codex/mailbox"),
}


@dataclass(frozen=True)
class DecisionRow:
    decision: str
    options: str
    recommendation: str


@dataclass(frozen=True)
class DependencyRow:
    item: str
    install_vector: str
    evidence: str


@dataclass(frozen=True)
class DigestData:
    source_path: Path
    topic: str
    classification: str
    findings: list[str]
    decisions: list[DecisionRow]
    actionables: list[str]
    dependencies: list[DependencyRow]
    contradictions: list[str]


def find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for path in [cur, *cur.parents]:
        if (path / "AGENTS.md").exists() and (path / "pyproject.toml").exists():
            return path
    raise SystemExit("Could not locate repo root (expected AGENTS.md + pyproject.toml).")


REPO_ROOT = find_repo_root(Path(__file__))


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_stamp() -> str:
    return utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")


def ensure_repo_path(path: Path) -> Path:
    if path.is_absolute():
        return path.resolve()
    return (REPO_ROOT / path).resolve()


def rel_display(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except Exception:
        return path.as_posix()


def slugify_topic(topic: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", topic.strip()).strip("_")
    return cleaned.upper() or "UNTITLED"


def normalize_research_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = normalized.replace("&nbsp;", " ")
    normalized = re.sub(r"\\([#*_`\[\]()|])", r"\1", normalized)
    normalized = normalized.replace("\\-", "-")
    return normalized


def _clean_heading_candidate(raw: str) -> str:
    candidate = clean_line(raw.lstrip("#").strip())
    candidate = re.sub(r"^[*_`~\s]+", "", candidate)
    candidate = re.sub(r"[*_`~\s]+$", "", candidate)
    return clean_line(candidate)


def _is_low_signal_heading(candidate: str) -> bool:
    low = candidate.lower().strip("[](): ")
    if low in {
        "preamble",
        "analyze results",
        "create report",
        "references",
        "referanser",
    }:
        return True
    alnum_len = len(re.sub(r"[^a-z0-9]+", "", low))
    if alnum_len < 8:
        return True
    if len(candidate) > 96:
        return True
    if "|||" in candidate:
        return True
    return False


def _stem_topic_from_source(source_path: Path) -> str:
    stem = source_path.stem
    stem = re.sub(r"^(GEMINI_DEEP_RESEARCH_|DEEP_RESEARCH_|RESEARCH_DIGEST_)", "", stem, flags=re.IGNORECASE)
    return stem.replace("_", " ").strip() or source_path.name


def _prefer_source_stem_topic(source_path: Path) -> bool:
    stem = source_path.stem
    if re.fullmatch(r"[A-Z0-9_]{12,}", stem):
        return True
    if stem.upper().startswith("ANNO_"):
        return True
    return False


def detect_topic(source_path: Path, text: str, topic_override: str | None) -> str:
    if topic_override:
        return topic_override

    if _prefer_source_stem_topic(source_path):
        return _stem_topic_from_source(source_path)

    normalized_text = normalize_research_text(text)
    first_heading = ""
    for line in normalized_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            candidate = _clean_heading_candidate(stripped)
            if candidate and not _is_low_signal_heading(candidate):
                first_heading = candidate
                break

    if first_heading:
        return first_heading

    return _stem_topic_from_source(source_path)


def read_clipboard_text() -> str:
    env_text = os.environ.get("INGEST_RESEARCH_CLIPBOARD_TEXT")
    if env_text and env_text.strip():
        return env_text

    commands = [
        ["pwsh", "-NoProfile", "-Command", "Get-Clipboard -Raw"],
        ["powershell", "-NoProfile", "-Command", "Get-Clipboard -Raw"],
        ["pbpaste"],
        ["xclip", "-selection", "clipboard", "-o"],
        ["wl-paste", "-n"],
    ]

    for cmd in commands:
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError:
            continue

        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout

    raise SystemExit(
        "Unable to read clipboard text. On Windows, ensure PowerShell clipboard access works "
        "(`Get-Clipboard -Raw`) or set INGEST_RESEARCH_CLIPBOARD_TEXT for non-interactive runs."
    )


def normalize_clipboard_markdown(text: str, topic: str) -> str:
    content = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not content:
        raise SystemExit("Clipboard content is empty.")

    has_heading = bool(re.match(r"^\s*#{1,6}\s+\S+", content))
    if has_heading:
        return content + "\n"
    return f"# {topic}\n\n{content}\n"


def normalize_source_name(name: str | None, topic: str) -> str:
    if name:
        raw = name.strip().replace("\\", "_").replace("/", "_")
        if not raw:
            raise SystemExit("Invalid --source-name value.")
        return raw if raw.lower().endswith(".md") else f"{raw}.md"
    return f"RESEARCH_CANDIDATE_{slugify_topic(topic)}.md"


def create_clipboard_source(
    clipboard_text: str,
    topic: str,
    target_mailbox_dir: Path,
    source_name: str | None,
) -> Path:
    filename = normalize_source_name(source_name, topic)
    source_path = target_mailbox_dir / filename

    if source_path.exists() and source_name is None:
        stamp = utc_now().strftime("%Y%m%d_%H%M%S")
        source_path = target_mailbox_dir / f"RESEARCH_CANDIDATE_{slugify_topic(topic)}_{stamp}.md"

    payload = normalize_clipboard_markdown(clipboard_text, topic)
    write_file(source_path, payload)
    return source_path


def discover_latest_research_doc() -> Path:
    candidates: list[Path] = []
    for mailbox in MAILBOX_DIRS.values():
        abs_mailbox = ensure_repo_path(mailbox)
        if not abs_mailbox.exists():
            continue
        for path in abs_mailbox.iterdir():
            if not path.is_file():
                continue
            if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            name = path.name.lower()
            if "research" in name or "deep_research" in name or "gemini" in name:
                candidates.append(path)

    if not candidates:
        raise SystemExit(
            "No research files found. Pass an explicit source path or add a *_RESEARCH_*.md file in claude/codex mailbox."
        )

    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def read_pdf_text(path: Path) -> str:
    proc = subprocess.run(
        ["pdftotext", "-layout", str(path), "-"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise SystemExit(
            f"Failed to extract PDF text via pdftotext for {path}. Install poppler/pdftotext or convert PDF to .md/.txt."
        )
    return proc.stdout


def read_source_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".md", ".txt", ".log"}:
        return path.read_text(encoding="utf-8", errors="replace")
    if suffix == ".json":
        raw = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        return json.dumps(raw, indent=2)
    if suffix in {".html", ".htm"}:
        raw = path.read_text(encoding="utf-8", errors="replace")
        text = re.sub(r"(?is)<script.*?>.*?</script>", " ", raw)
        text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
        text = re.sub(r"(?is)<[^>]+>", " ", text)
        text = html.unescape(text)
        return re.sub(r"[ \t]+", " ", text)
    if suffix == ".pdf":
        return read_pdf_text(path)

    raise SystemExit(f"Unsupported source type: {path.suffix} ({path})")


def is_request_brief(text: str) -> bool:
    lower = text.lower()
    has_questions_header = "research questions" in lower or "expected output" in lower
    question_count = text.count("?")
    recommendation_count = len(re.findall(r"\brecommend(?:ed|ation)?\b", lower))
    return has_questions_header and question_count >= 4 and recommendation_count <= 2


def extract_urls(text: str) -> list[str]:
    urls = re.findall(r"https?://[^\s)>\]]+", text)
    return dedupe_preserve_order(urls)


def extract_bullets(text: str) -> list[str]:
    bullets: list[str] = []
    for line in text.splitlines():
        match = re.match(r"^\s*(?:[-*+]|[0-9]+\.)\s+(.+?)\s*$", line)
        if match:
            bullet = clean_line(match.group(1))
            if bullet:
                bullets.append(bullet)
    return bullets


def extract_sentences(text: str) -> list[str]:
    compact = re.sub(r"\s+", " ", text)
    raw = re.split(r"(?<=[.!?])\s+", compact)
    sentences = [clean_line(s) for s in raw]
    return [s for s in sentences if len(s) >= 20]


def clean_line(text: str) -> str:
    normalized = normalize_research_text(text)
    normalized = re.sub(r"\*\*(.+?)\*\*", r"\1", normalized)
    normalized = re.sub(r"\*(.+?)\*", r"\1", normalized)
    normalized = re.sub(r"`(.+?)`", r"\1", normalized)
    normalized = re.sub(r"\s+", " ", normalized.strip(" -\t"))
    return normalized


def dedupe_preserve_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        key = value.strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


def build_findings(text: str, bullets: list[str], sentences: list[str], request_mode: bool) -> list[str]:
    findings: list[str] = []
    if request_mode:
        findings.append("Document is a research brief with open questions, not a finalized research result packet.")

    finding_keywords = (
        "current",
        "latest",
        "status",
        "recommend",
        "canonical",
        "install",
        "version",
        "dependency",
        "sdk",
        "validator",
        "toolchain",
    )

    for source in bullets + sentences:
        lower = source.lower()
        if len(source) > 450:
            continue
        if any(keyword in lower for keyword in finding_keywords):
            findings.append(source)
        if len(findings) >= 10:
            break

    if not findings:
        findings = (bullets[:8] or sentences[:8] or ["No high-signal findings extracted."])

    return dedupe_preserve_order(findings)


def parse_options(text: str) -> str:
    if " vs " in text:
        parts = [clean_line(p) for p in text.split(" vs ", 1)]
        return " vs ".join(parts)
    if " or " in text:
        parts = [clean_line(p) for p in text.split(" or ", 1)]
        return " or ".join(parts)
    return "Yes / No"


def parse_recommendation(text: str) -> str:
    lower = text.lower()
    if "recommend" in lower:
        idx = lower.find("recommend")
        tail = clean_line(text[idx:])
        return tail if tail else "Review recommendation context."
    if "should " in lower:
        idx = lower.find("should ")
        tail = clean_line(text[idx:])
        return tail if tail else "Review should-statement context."
    return "Needs explicit choice after review."


def build_decisions(bullets: list[str], sentences: list[str], request_mode: bool) -> list[DecisionRow]:
    decision_keywords = (
        "recommend",
        "should",
        "decision",
        "choose",
        "option",
        "whether",
        "prefer",
        "add ",
    )
    rows: list[DecisionRow] = []
    for line in bullets + sentences:
        if len(line) > 350:
            continue
        if re.search(r"https?://", line, flags=re.IGNORECASE):
            continue
        if "## ---" in line:
            continue
        if line.lstrip().startswith("*"):
            continue
        if line.lower().startswith("referanser"):
            continue
        lower = line.lower()
        if any(keyword in lower for keyword in decision_keywords):
            rows.append(
                DecisionRow(
                    decision=line,
                    options=parse_options(line),
                    recommendation=parse_recommendation(line),
                )
            )
        if len(rows) >= 8:
            break

    if not rows and request_mode:
        rows.append(
            DecisionRow(
                decision="Select which research questions should be answered first for implementation planning.",
                options="Priority order by subsystem (toolchain, runtime, validator, dependencies)",
                recommendation="Start with installation + versioning questions that unblock DoctorFixMap.",
            )
        )

    return dedupe_decisions(rows)


def dedupe_decisions(rows: list[DecisionRow]) -> list[DecisionRow]:
    seen: set[str] = set()
    out: list[DecisionRow] = []
    for row in rows:
        key = row.decision.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def route_tag(task: str) -> str:
    lower = task.lower()
    if any(token in lower for token in ("gemini", "deep research", "verify source", "external citation")):
        return "[gemini]"
    if any(token in lower for token in ("chthonic", "doctor", "originmap", "doctorfixmap", "scripts/chthonic.ps1")):
        return "[chthonic]"
    if any(token in lower for token in ("rust", "vulkan", "shader", "pipeline", "renderer", "codex", "src/")):
        return "[codex]"
    return "[manual]"


def infer_component(task: str) -> str:
    match = re.search(r"([A-Za-z0-9_./-]+\.(?:md|ps1|py|rs|toml|json|ya?ml))", task)
    if match:
        return match.group(1)
    lower = task.lower()
    if "chthonic" in lower:
        return "scripts/chthonic.ps1"
    if "shader" in lower or "vulkan" in lower:
        return "assets/shaders + src/render"
    if "mailbox" in lower:
        return "claude/mailbox or codex/mailbox"
    return "manual-review"


def build_actionables(bullets: list[str], sentences: list[str], request_mode: bool) -> list[str]:
    verb_keywords = (
        "add",
        "update",
        "implement",
        "verify",
        "check",
        "research",
        "benchmark",
        "document",
        "wire",
        "map",
        "compare",
        "review",
    )

    candidates: list[str] = []
    for line in bullets + sentences:
        if len(line) > 350:
            continue
        lower = line.lower()
        if any(f" {verb} " in f" {lower} " or lower.startswith(f"{verb} ") for verb in verb_keywords):
            candidates.append(line)
        if len(candidates) >= 14:
            break

    if request_mode and not candidates:
        candidates.append("Answer the listed research questions and convert them into implementation-ready recommendations.")

    out: list[str] = []
    for task in dedupe_preserve_order(candidates):
        tag = route_tag(task)
        component = infer_component(task)
        out.append(f"{tag} {task} ({component})")

    if not out:
        out.append("[manual] Review source and extract concrete next tasks (manual-review)")

    return out


def build_dependencies(bullets: list[str], sentences: list[str], text: str) -> list[DependencyRow]:
    lines = dedupe_preserve_order(bullets + sentences)
    rows: list[DependencyRow] = []

    patterns = [
        (r"\bcargo install\s+([A-Za-z0-9._-]+)", "cargo install"),
        (r"\buv tool(?: install)?\s+([A-Za-z0-9._-]+)", "uv tool"),
        (r"\bbun add -g\s+([A-Za-z0-9._@/\-]+)", "bun add -g"),
        (r"\bwinget install\s+([A-Za-z0-9._\-]+)", "winget"),
    ]

    for line in lines:
        for pattern, vector in patterns:
            match = re.search(pattern, line, flags=re.IGNORECASE)
            if not match:
                continue
            rows.append(
                DependencyRow(
                    item=match.group(1),
                    install_vector=vector,
                    evidence=line,
                )
            )

    low = text.lower()
    manual_tokens = {
        "cmake": "manual",
        "ninja": "manual",
        "vulkan sdk": "manual",
        "solana": "manual",
        "agave": "manual",
    }
    for token, vector in manual_tokens.items():
        if token in low:
            rows.append(
                DependencyRow(
                    item=token,
                    install_vector=vector,
                    evidence=f"Mentioned in source text: {token}",
                )
            )

    return dedupe_dependencies(rows)[:16]


def dedupe_dependencies(rows: list[DependencyRow]) -> list[DependencyRow]:
    seen: set[tuple[str, str]] = set()
    out: list[DependencyRow] = []
    for row in rows:
        key = (row.item.lower(), row.install_vector.lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def build_contradictions(bullets: list[str], sentences: list[str]) -> list[str]:
    contradictions: list[str] = []
    for line in bullets + sentences:
        lower = line.lower()
        if "conflict:" in lower or "contradict" in lower or "in conflict" in lower:
            if line.upper().startswith("CONFLICT:"):
                contradictions.append(line)
            else:
                contradictions.append(f"CONFLICT: {line}")
    return dedupe_preserve_order(contradictions)[:12]


def digest_filename(topic: str) -> str:
    return f"RESEARCH_DIGEST_{slugify_topic(topic)}.md"


def handoff_filename(topic: str) -> str:
    stamp = utc_now().strftime("%Y%m%d_%H%M%S")
    return f"SESSION_HANDOFF_RESEARCH_{slugify_topic(topic)}_{stamp}.md"


def render_digest_markdown(data: DigestData, urls: list[str]) -> str:
    lines: list[str] = []
    lines.append("---")
    lines.append("type: research-digest")
    lines.append(f"created: {utc_stamp()}")
    lines.append(f"source: {rel_display(data.source_path)}")
    lines.append(f"topic: {data.topic}")
    lines.append("---")
    lines.append("")
    lines.append(f"# Research Digest: {data.topic}")
    lines.append("")
    lines.append(f"- Classification: **{data.classification}**")
    lines.append(f"- Source: `{rel_display(data.source_path)}`")
    lines.append("")
    lines.append("## Findings")
    for finding in data.findings:
        lines.append(f"- {finding}")
    if urls:
        lines.append("- Source links observed:")
        for url in urls[:10]:
            lines.append(f"  - {url}")
    lines.append("")
    lines.append("## Decisions")
    lines.append("| Decision | Options | Recommendation |")
    lines.append("|---|---|---|")
    if data.decisions:
        for row in data.decisions:
            lines.append(
                f"| {escape_pipe(row.decision)} | {escape_pipe(row.options)} | {escape_pipe(row.recommendation)} |"
            )
    else:
        lines.append("| No explicit decision statements found. | n/a | Review manually |")
    lines.append("")
    lines.append("## Actionable Items")
    for item in data.actionables:
        lines.append(f"- [ ] {item}")
    lines.append("")
    lines.append("## Dependencies")
    lines.append("| Dependency | Install Vector | Evidence |")
    lines.append("|---|---|---|")
    if data.dependencies:
        for row in data.dependencies:
            lines.append(
                f"| {escape_pipe(row.item)} | {escape_pipe(row.install_vector)} | {escape_pipe(row.evidence)} |"
            )
    else:
        lines.append("| None detected | manual | n/a |")
    lines.append("")
    lines.append("## Contradictions")
    if data.contradictions:
        for row in data.contradictions:
            lines.append(f"- {row}")
    else:
        lines.append("- None detected.")
    lines.append("")
    return "\n".join(lines)


def escape_pipe(text: str) -> str:
    return text.replace("|", "\\|")


def render_handoff_markdown(
    digest_path: Path,
    source_path: Path,
    topic: str,
    from_agent: str,
    to_agent: str,
    data: DigestData,
    forwarded_source: Path | None,
) -> str:
    lines: list[str] = []
    lines.append("---")
    lines.append("type: handoff")
    lines.append(f"from: {from_agent}")
    lines.append(f"to: [{to_agent}]")
    lines.append(f"created: {utc_now().strftime('%Y-%m-%d')}")
    lines.append("priority: inform")
    lines.append(f"in_response_to: {source_path.name}")
    lines.append("---")
    lines.append("")
    lines.append(f"# Research Handoff: {topic}")
    lines.append("")
    lines.append("## Actions Taken")
    lines.append(f"- Ingested research artifact: `{rel_display(source_path)}`")
    lines.append(f"- Generated digest: `{rel_display(digest_path)}`")
    if forwarded_source is not None:
        lines.append(f"- Forwarded source copy: `{rel_display(forwarded_source)}`")
    lines.append("")
    lines.append("## Key Findings")
    for finding in data.findings[:5]:
        lines.append(f"- {finding}")
    lines.append("")
    lines.append("## Decisions Needed")
    if data.decisions:
        for row in data.decisions[:5]:
            lines.append(f"- {row.decision}")
    else:
        lines.append("- No explicit decisions extracted.")
    lines.append("")
    lines.append("## Next Actions")
    for action in data.actionables[:5]:
        lines.append(f"- {action}")
    lines.append("")
    return "\n".join(lines)


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def copy_source_into_mailbox(source_path: Path, mailbox_dir: Path, topic: str) -> Path:
    target_name = f"RESEARCH_SOURCE_{slugify_topic(topic)}{source_path.suffix.lower()}"
    target_path = mailbox_dir / target_name
    shutil.copy2(source_path, target_path)
    return target_path


def build_digest_data(source_path: Path, text: str, topic: str) -> tuple[DigestData, list[str]]:
    bullets = extract_bullets(text)
    sentences = extract_sentences(text)
    urls = extract_urls(text)
    request_mode = is_request_brief(text)

    data = DigestData(
        source_path=source_path,
        topic=topic,
        classification="request-brief" if request_mode else "research-results",
        findings=build_findings(text, bullets, sentences, request_mode),
        decisions=build_decisions(bullets, sentences, request_mode),
        actionables=build_actionables(bullets, sentences, request_mode),
        dependencies=build_dependencies(bullets, sentences, text),
        contradictions=build_contradictions(bullets, sentences),
    )
    return data, urls


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest research docs into structured digests.")
    parser.add_argument("source", nargs="?", help="Path to research source file. If omitted, newest research file is used.")
    parser.add_argument(
        "--clipboard",
        action="store_true",
        help="Use markdown text currently in clipboard as source input.",
    )
    parser.add_argument(
        "--source-name",
        help="Filename for clipboard capture (e.g., equivalent.md). Used with --clipboard.",
    )
    parser.add_argument("--topic", help="Override topic/title used for digest filename.")
    parser.add_argument(
        "--target-mailbox",
        choices=sorted(MAILBOX_DIRS.keys()),
        default="claude",
        help="Mailbox where RESEARCH_DIGEST_<topic>.md is written.",
    )
    parser.add_argument(
        "--output",
        help="Explicit digest output path (overrides --target-mailbox default output name).",
    )
    parser.add_argument(
        "--handoff-to",
        choices=sorted(MAILBOX_DIRS.keys()),
        help="Optional mailbox to receive a SESSION_HANDOFF_RESEARCH_*.md note.",
    )
    parser.add_argument(
        "--from-agent",
        default="codex",
        help="Sender id for generated handoff frontmatter.",
    )
    parser.add_argument(
        "--to-agent",
        help="Receiver id for generated handoff frontmatter. Defaults to --handoff-to value.",
    )
    parser.add_argument(
        "--forward-source",
        action="store_true",
        help="Copy source artifact into --handoff-to mailbox as RESEARCH_SOURCE_<topic>.<ext>.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    if args.clipboard and args.source:
        raise SystemExit("Pass either [source] or --clipboard, not both.")

    if args.source_name and not args.clipboard:
        raise SystemExit("--source-name is only valid with --clipboard.")

    if args.clipboard:
        clipboard_text = read_clipboard_text()
        provisional_topic = detect_topic(Path("clipboard.md"), clipboard_text, args.topic)
        target_mailbox = ensure_repo_path(MAILBOX_DIRS[args.target_mailbox])
        source_path = create_clipboard_source(
            clipboard_text=clipboard_text,
            topic=provisional_topic,
            target_mailbox_dir=target_mailbox,
            source_name=args.source_name,
        )
    else:
        source_path = ensure_repo_path(Path(args.source)) if args.source else discover_latest_research_doc()

    if not source_path.exists():
        raise SystemExit(f"Source not found: {source_path}")
    if source_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise SystemExit(f"Unsupported source extension: {source_path.suffix}")

    source_text = normalize_research_text(read_source_text(source_path))
    topic = detect_topic(source_path, source_text, args.topic)
    digest_data, urls = build_digest_data(source_path, source_text, topic)

    if args.output:
        digest_path = ensure_repo_path(Path(args.output))
    else:
        target_mailbox = ensure_repo_path(MAILBOX_DIRS[args.target_mailbox])
        digest_path = target_mailbox / digest_filename(topic)

    write_file(digest_path, render_digest_markdown(digest_data, urls))

    handoff_path: Path | None = None
    forwarded_source: Path | None = None
    if args.handoff_to:
        handoff_mailbox = ensure_repo_path(MAILBOX_DIRS[args.handoff_to])
        if args.forward_source:
            forwarded_source = copy_source_into_mailbox(source_path, handoff_mailbox, topic)

        handoff_path = handoff_mailbox / handoff_filename(topic)
        to_agent = args.to_agent or args.handoff_to
        write_file(
            handoff_path,
            render_handoff_markdown(
                digest_path=digest_path,
                source_path=source_path,
                topic=topic,
                from_agent=args.from_agent,
                to_agent=to_agent,
                data=digest_data,
                forwarded_source=forwarded_source,
            ),
        )

    print(f"Wrote digest: {rel_display(digest_path)}")
    if handoff_path is not None:
        print(f"Wrote handoff: {rel_display(handoff_path)}")
    if forwarded_source is not None:
        print(f"Forwarded source: {rel_display(forwarded_source)}")

    print(
        "Summary: findings={0} decisions={1} actionables={2} dependencies={3} contradictions={4}".format(
            len(digest_data.findings),
            len(digest_data.decisions),
            len(digest_data.actionables),
            len(digest_data.dependencies),
            len(digest_data.contradictions),
        )
    )

    if digest_data.decisions:
        print("Decisions needing input:")
        for idx, row in enumerate(digest_data.decisions[:5], start=1):
            print(f"  {idx}. {row.decision}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
