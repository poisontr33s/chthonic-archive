#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: link_audit.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Link Audit — Validate and fix markdown [label](path) references in files.

Scans markdown files for broken or ambiguous internal links, detects basename
collisions, and optionally rewrites fixable references in-place.

@SID:           TOOL_LINK_AUDIT_V1
@Shabti:        Guardian
@Context:       Infrastructure / Markdown Quality Gate
@Implements:    Path-Link Disambiguation Canon (SESSION_HANDOFF_2026_02_27)
@Purpose:       Link Audit — Validate and fix markdown [label](path) references in files.

Usage:
    uv run scripts/link_audit.py check <file>              # audit one file
    uv run scripts/link_audit.py check <file> --fix        # audit + rewrite fixes
    uv run scripts/link_audit.py check <file> --dry-run    # show fixes without writing
    uv run scripts/link_audit.py check <file> --github-links
    uv run scripts/link_audit.py check <file> --github-online
    uv run scripts/link_audit.py scan                       # audit ALL markdown files in repo
    uv run scripts/link_audit.py scan --dry-run             # preview repo-wide fixes
    uv run scripts/link_audit.py scan --fix                 # apply repo-wide fixes
    uv run scripts/link_audit.py scan --github-links        # include GitHub/GFM URL shapes
    uv run scripts/link_audit.py scan --github-online       # also check GitHub pages/assets live
    uv run scripts/link_audit.py backticks <file>           # scan for inert backtick file/path refs
    uv run scripts/link_audit.py backticks <file> --dry-run # preview inert backtick upgrades
    uv run scripts/link_audit.py backticks <file> --fix     # rewrite fixable backticks as links
    uv run scripts/link_audit.py renames --staged          # audit markdown links against staged renames
    uv run scripts/link_audit.py renames --staged --dry-run
    uv run scripts/link_audit.py renames --staged --fix
    uv run scripts/link_audit.py collisions                 # list all basename collisions in repo
    uv run scripts/link_audit.py collisions --json          # JSON output

Line anchors are validated when present:
    [label](path/to/file.md#L100)
    [label](path/to/file.md#l100)
    [label](path/to/file.md#L100-L120)
    [label](path/to/file.md#100)

GitHub/GFM mode also recognizes bare GitHub URLs and HTML href/src targets.
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import unquote as _url_unquote
from urllib.parse import quote as _url_quote
from urllib.parse import urlparse, urlunparse
from urllib.request import Request, urlopen

# sys.path guard: ensure repo root is importable regardless of invocation CWD
_REPO_ROOT_CANDIDATE = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT_CANDIDATE) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT_CANDIDATE))

from scripts.lib.shared import configure_utf8_output, find_repo_root, setup_logging

# =============================================================================
# Constants
# =============================================================================

# Legacy simple matcher for narrow call sites. Main extraction below uses a
# small parser so balanced destinations like foo-(SSOT).md are not truncated.
RE_MD_LINK = re.compile(r"(\[([^\]]*)\]\(([^)]+)\))")

# Paths that are never internal file references
EXTERNAL_PREFIXES = (
    "http://", "https://", "mailto:", "tel:", "ftp://",
    "file:///",  # absolute filesystem URIs from VS Code session dumps
)

GITHUB_HOSTS = {"github.com", "www.github.com"}
GITHUB_RAW_HOSTS = {"raw.githubusercontent.com"}
GITHUB_ASSET_HOSTS = {
    "objects.githubusercontent.com",
    "private-user-images.githubusercontent.com",
    "user-images.githubusercontent.com",
}
GITHUB_PAGE_SEGMENTS = {
    "actions", "branches", "commit", "commits", "compare", "deployments",
    "discussions", "fork", "graphs", "issues", "network", "packages",
    "projects", "pull", "pulse", "releases", "security", "settings",
    "stargazers", "tags", "watchers", "wiki",
}

# Directories to skip during scanning and collision indexing.
# Includes build artifacts, vendored third-party content, and directories
# whose markdown links are not repo-internal (Hugo templates, session dumps).
SKIP_DIRS = {
    ".git", "node_modules", "target", "__pycache__", ".venv",
    "build", "dist", ".mypy_cache", ".ruff_cache",
    # Third-party / vendored — links reference their own ecosystems
    "meta-ide", "extensions",
    # Session dumps / debugging artifacts — stale file:/// URIs, old usernames
    "debugging_data",
    # Archive-heavy salvage vault — 19k+ files, no active links target it
    "corpse-vault",
}

# Basenames to skip during scanning (third-party docs whose links are ecosystem-internal)
RE_SKIP_BASENAME = re.compile(r"^(license|readme|changelog|contributing)\b", re.IGNORECASE)

# Backtick-wrapped content: matches `...` outside of [`...`](...) link labels
RE_BACKTICK = re.compile(r"`([^`]+)`")
RE_FILEISH_EXT = re.compile(r"\.(md|py|svg|json|ts|js|toml|yaml|yml|ps1|sh)$")
RE_WINDOWS_ABS = re.compile(r"^[A-Za-z]:[\\/]")
RE_GENERIC_DOTTED_NAME = re.compile(r"^[^`\s\\/]+(?:\.[A-Za-z0-9_-]{1,24})+$")
RE_MD_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
RE_GITHUBISH_URL = re.compile(
    r"https?://(?:www\.)?(?:github\.com|raw\.githubusercontent\.com|"
    r"objects\.githubusercontent\.com|private-user-images\.githubusercontent\.com|"
    r"user-images\.githubusercontent\.com)/[^\s<>\]\)\"']+"
)
RE_HTML_LINK_ATTR = re.compile(r"""(?i)\b(?:href|src)=["']([^"']+)["']""")


# =============================================================================
# Heading Slug Utilities
# =============================================================================

def markdown_to_slug(heading_text: str) -> str:
    """Convert a markdown heading to a GitHub-compatible anchor slug.

    Rules (matching GitHub/VS Code behaviour):
    - Strip leading/trailing whitespace
    - Downcase
    - Strip characters that are not alphanumeric, space, or hyphen
    - Replace spaces with hyphens
    - Do NOT collapse consecutive hyphens (GitHub preserves them)
    """
    slug = heading_text.strip().lower()
    # Remove inline formatting markers (bold, italic, code, links)
    slug = re.sub(r"[`*_~\[\]()]", "", slug)
    # Remove HTML tags
    slug = re.sub(r"<[^>]+>", "", slug)
    # Keep only alphanumeric, spaces, hyphens, and unicode letters
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = slug.replace(" ", "-")
    slug = slug.strip("-")
    return slug


def extract_heading_slugs(text: str) -> set[str]:
    """Extract all heading anchor slugs from markdown text.

    Handles duplicate headings by appending -1, -2, etc. (GitHub convention).
    """
    slugs: set[str] = set()
    slug_counts: dict[str, int] = {}
    in_fence = False
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = RE_MD_HEADING.match(stripped)
        if not m:
            continue
        base_slug = markdown_to_slug(m.group(2))
        if not base_slug:
            continue
        count = slug_counts.get(base_slug, 0)
        if count == 0:
            slugs.add(base_slug)
        else:
            slugs.add(f"{base_slug}-{count}")
        slug_counts[base_slug] = count + 1
    return slugs


# =============================================================================
# Serialization Helpers
# =============================================================================

def _safe_relative_path(p: Path, repo_root: Path) -> str:
    """Return repo-relative posix string, or absolute string if outside repo."""
    if isinstance(p, str):
        return p
    try:
        return str(p.relative_to(repo_root))
    except ValueError:
        return str(p)


# =============================================================================
# GitHub / GFM URL Helpers
# =============================================================================

_current_github_repo_cache: dict[str, tuple[str, str] | None] = {}
_default_ref_cache: dict[str, str] = {}
_http_status_cache: dict[str, tuple[bool, str]] = {}


def _strip_dotgit(repo: str) -> str:
    return repo[:-4] if repo.endswith(".git") else repo


def _quote_url_path(path: str) -> str:
    return "/".join(_url_quote(part) for part in path.split("/"))


def _run_git_text(repo_root: Path, args: list[str]) -> str | None:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=repo_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except FileNotFoundError:
        return None
    if proc.returncode != 0:
        return None
    text = proc.stdout.strip()
    return text or None


def current_github_repo(repo_root: Path) -> tuple[str, str] | None:
    """Return (owner, repo) from origin when this checkout is a GitHub repo."""
    key = str(repo_root)
    if key in _current_github_repo_cache:
        return _current_github_repo_cache[key]

    remote = _run_git_text(repo_root, ["remote", "get-url", "origin"])
    if not remote:
        _current_github_repo_cache[key] = None
        return None

    owner_repo: tuple[str, str] | None = None
    if remote.startswith("git@github.com:"):
        rest = remote.split(":", 1)[1]
        parts = rest.split("/")
        if len(parts) >= 2:
            owner_repo = (parts[0], _strip_dotgit(parts[1]))
    else:
        parsed = urlparse(remote)
        host = (parsed.hostname or "").lower()
        if host in GITHUB_HOSTS:
            parts = [p for p in parsed.path.split("/") if p]
            if len(parts) >= 2:
                owner_repo = (parts[0], _strip_dotgit(parts[1]))

    if owner_repo:
        owner_repo = (owner_repo[0].lower(), owner_repo[1].lower())
    _current_github_repo_cache[key] = owner_repo
    return owner_repo


def default_git_ref(repo_root: Path) -> str:
    """Best-effort default ref for GitHub URL fixes."""
    key = str(repo_root)
    if key in _default_ref_cache:
        return _default_ref_cache[key]

    ref = _run_git_text(repo_root, ["symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"])
    if ref and "/" in ref:
        ref = ref.split("/", 1)[1]
    if not ref:
        ref = _run_git_text(repo_root, ["branch", "--show-current"])
    _default_ref_cache[key] = ref or "main"
    return _default_ref_cache[key]


def _githubish_host(host: str) -> bool:
    return host in GITHUB_HOSTS or host in GITHUB_RAW_HOSTS or host in GITHUB_ASSET_HOSTS


def is_githubish_url(target: str) -> bool:
    parsed = urlparse(target)
    host = (parsed.hostname or "").lower()
    return _githubish_host(host)


def parse_github_url(target: str) -> dict | None:
    """Parse GitHub, raw.githubusercontent.com, and GitHub asset URLs."""
    parsed = urlparse(target)
    host = (parsed.hostname or "").lower()
    if not _githubish_host(host):
        return None

    parts = [_url_unquote(p) for p in parsed.path.split("/") if p]

    if host in GITHUB_RAW_HOSTS:
        if len(parts) < 3:
            return {"kind": "raw_host_malformed", "parsed": parsed, "host": host}
        return {
            "kind": "raw_host",
            "parsed": parsed,
            "host": host,
            "owner": parts[0],
            "repo": _strip_dotgit(parts[1]),
            "segments": parts[2:],
        }

    if host in GITHUB_ASSET_HOSTS:
        return {"kind": "asset", "parsed": parsed, "host": host}

    # github.com/user-attachments/assets/<id> is not a repository route.
    if len(parts) >= 2 and parts[0] == "user-attachments" and parts[1] == "assets":
        return {"kind": "asset", "parsed": parsed, "host": host}

    if len(parts) < 2:
        return {"kind": "github_page", "parsed": parsed, "host": host}

    owner = parts[0]
    repo = _strip_dotgit(parts[1])
    rest = parts[2:]
    if not rest:
        kind = "repo"
    elif rest[0] in {"blob", "tree", "raw"}:
        kind = rest[0]
    elif rest[0] in GITHUB_PAGE_SEGMENTS:
        kind = "page"
    else:
        kind = "maybe_missing_blob"

    return {
        "kind": kind,
        "parsed": parsed,
        "host": host,
        "owner": owner,
        "repo": repo,
        "segments": rest[1:] if kind in {"blob", "tree", "raw"} else rest,
        "page": rest[0] if rest else None,
    }


def _same_github_repo(info: dict, repo_root: Path) -> bool:
    current = current_github_repo(repo_root)
    if not current or "owner" not in info or "repo" not in info:
        return False
    return (info["owner"].lower(), info["repo"].lower()) == current


def _resolve_github_ref_path(
    segments: list[str],
    repo_root: Path,
    want_dir: bool = False,
) -> tuple[str, str, Path] | None:
    """Split GitHub <ref>/<path> segments by finding the local path portion."""
    if len(segments) < 2:
        return None

    for split_at in range(1, len(segments)):
        ref = "/".join(segments[:split_at])
        rel = "/".join(segments[split_at:])
        if not rel:
            continue
        candidate = (repo_root / rel).resolve()
        if want_dir and candidate.is_dir():
            return ref, rel, candidate
        if not want_dir and candidate.is_file():
            return ref, rel, candidate
    return None


def _infer_missing_blob_target(
    rest: list[str],
    repo_root: Path,
) -> tuple[str, str, Path, str] | None:
    """Infer a missing /blob/<ref>/ or /tree/<ref>/ route for same-repo URLs."""
    if not rest:
        return None

    default_ref = default_git_ref(repo_root)
    candidates: list[tuple[str, str]] = []
    if len(rest) >= 2 and rest[0] in {default_ref, "main", "master", "trunk"}:
        candidates.append((rest[0], "/".join(rest[1:])))
    candidates.append((default_ref, "/".join(rest)))

    seen: set[tuple[str, str]] = set()
    for ref, rel in candidates:
        if not rel or (ref, rel) in seen:
            continue
        seen.add((ref, rel))
        candidate = (repo_root / rel).resolve()
        if candidate.is_file():
            return ref, rel, candidate, "blob"
        if candidate.is_dir():
            return ref, rel, candidate, "tree"
    return None


def _github_fix_url(parsed, owner: str, repo: str, mode: str, ref: str, rel: str) -> str:
    path = f"/{owner}/{repo}/{mode}/{_quote_url_path(ref)}/{_quote_url_path(rel)}"
    return urlunparse((parsed.scheme, parsed.netloc, path, "", parsed.query, parsed.fragment))


def _format_target_fix(link: dict, fixed_target: str) -> str:
    if link.get("syntax", "inline") == "inline":
        return f"[{link['label']}]({fixed_target})"
    return fixed_target


def _http_link_status(url: str, timeout: float) -> tuple[bool, str]:
    if url in _http_status_cache:
        return _http_status_cache[url]

    headers = {"User-Agent": "chthonic-pathfinder-link-audit/1.0"}
    try:
        req = Request(url, method="HEAD", headers=headers)
        with urlopen(req, timeout=timeout) as resp:
            code = getattr(resp, "status", resp.getcode())
    except HTTPError as exc:
        if exc.code in {405, 403}:
            try:
                req = Request(url, method="GET", headers=headers)
                with urlopen(req, timeout=timeout) as resp:
                    code = getattr(resp, "status", resp.getcode())
            except (HTTPError, URLError, TimeoutError) as inner:
                result = (False, f"HTTP check failed: {inner}")
            else:
                result = (200 <= int(code) < 400, f"HTTP {code}")
        else:
            result = (False, f"HTTP {exc.code}")
    except (URLError, TimeoutError) as exc:
        result = (False, f"HTTP check failed: {exc}")
    else:
        result = (200 <= int(code) < 400, f"HTTP {code}")

    _http_status_cache[url] = result
    return result


# =============================================================================
# Collision Index
# =============================================================================

def build_collision_index(repo_root: Path) -> dict[str, list[Path]]:
    """Build a map of basename -> [paths] for all files in the repo.

    Uses os.walk with directory pruning to skip heavy dirs early.
    """
    index: dict[str, list[Path]] = {}
    root_str = str(repo_root)
    for dirpath, dirnames, filenames in os.walk(root_str):
        # Prune skip dirs in-place so os.walk won't descend
        dirnames[:] = [
            d for d in dirnames
            if d not in SKIP_DIRS and not d.startswith(".venv")
        ]
        for fname in filenames:
            if RE_SKIP_BASENAME.match(fname):
                continue
            full = Path(dirpath) / fname
            if fname not in index:
                index[fname] = []
            index[fname].append(full)
    return index


def get_collisions(index: dict[str, list[Path]]) -> dict[str, list[Path]]:
    """Filter the index to only basenames with >1 path."""
    return {k: v for k, v in sorted(index.items()) if len(v) > 1}


# =============================================================================
# Link Extraction & Resolution
# =============================================================================

def _mask_inline_code(line: str) -> str:
    """Mask inline code spans while preserving [`code`](target) link labels."""
    chars = list(line)
    i = 0
    while i < len(chars):
        if chars[i] != "`":
            i += 1
            continue
        end = line.find("`", i + 1)
        if end == -1:
            break
        is_code_link_label = (
            i > 0
            and line[i - 1] == "["
            and end + 2 < len(line)
            and line[end + 1] == "]"
            and line[end + 2] == "("
        )
        if not is_code_link_label:
            for j in range(i, end + 1):
                chars[j] = " "
        i = end + 1
    return "".join(chars)


def _find_closing_bracket(line: str, start: int) -> int | None:
    """Find the closing ']' for a markdown label starting after '['."""
    depth = 1
    i = start
    while i < len(line):
        ch = line[i]
        if ch == "\\" and i + 1 < len(line):
            i += 2
            continue
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return None


def _find_link_target_bounds(line: str, start: int) -> tuple[int, int, int] | None:
    """Return (target_start, target_end, close_paren) for a markdown target.

    The target range excludes the closing ')'. Balanced parentheses are allowed
    inside the target, and angle-bracket targets are handled as a single unit.
    """
    i = start
    while i < len(line) and line[i].isspace():
        i += 1
    if i >= len(line):
        return None

    if line[i] == "<":
        j = i + 1
        while j < len(line):
            if line[j] == "\\" and j + 1 < len(line):
                j += 2
                continue
            if line[j] == ">":
                target_end = j + 1
                k = target_end
                while k < len(line) and line[k].isspace():
                    k += 1
                if k < len(line) and line[k] == ")":
                    return i, target_end, k
                return None
            j += 1
        return None

    depth = 0
    j = i
    while j < len(line):
        ch = line[j]
        if ch == "\\" and j + 1 < len(line):
            j += 2
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            if depth == 0:
                return i, j, j
            depth -= 1
        j += 1
    return None


def _normalize_link_target(raw_target: str) -> str:
    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    return target


def _is_external_target(target: str) -> bool:
    return any(target.startswith(p) for p in EXTERNAL_PREFIXES)


def _split_link_target(target: str) -> tuple[str | None, str | None]:
    if "#" in target:
        path_part, fragment = target.split("#", 1)
    else:
        path_part, fragment = target, None
    return path_part if path_part else None, fragment


def _link_record(
    lineno: int,
    full: str,
    label: str,
    target: str,
    syntax: str,
) -> dict:
    path_part, fragment = _split_link_target(target)
    return {
        "line": lineno,
        "full_match": full,
        "label": label,
        "target": target,
        "path_part": path_part,
        "fragment": fragment,
        "external": _is_external_target(target),
        "syntax": syntax,
    }


def _span_contains(spans: list[tuple[int, int]], pos: int) -> bool:
    return any(start <= pos < end for start, end in spans)


def _trim_bare_url(raw: str) -> str:
    return raw.rstrip(".,;:")


def extract_links(text: str, include_external: bool = False) -> list[dict]:
    """Extract all markdown links from text with line numbers.

    Skips links inside fenced code blocks (``` ... ```).
    """
    results = []
    in_fence = False
    for lineno, line in enumerate(text.split("\n"), start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        scanline = _mask_inline_code(line)
        cursor = 0
        inline_spans: list[tuple[int, int]] = []
        while cursor < len(scanline):
            start = scanline.find("[", cursor)
            if start == -1:
                break
            label_end = _find_closing_bracket(scanline, start + 1)
            if label_end is None:
                break
            if label_end + 1 >= len(scanline) or scanline[label_end + 1] != "(":
                cursor = start + 1
                continue
            bounds = _find_link_target_bounds(scanline, label_end + 2)
            if bounds is None:
                cursor = label_end + 1
                continue
            target_start, target_end, close_paren = bounds
            full = line[start:close_paren + 1]
            label = line[start + 1:label_end]
            target = _normalize_link_target(line[target_start:target_end])
            is_external = _is_external_target(target)
            # Skip external links (but NOT Windows absolute paths — resolve_link handles those)
            if is_external and not include_external:
                cursor = close_paren + 1
                continue
            inline_spans.append((start, close_paren + 1))
            results.append(_link_record(lineno, full, label, target, "inline"))
            cursor = close_paren + 1

        if not include_external:
            continue

        # GFM also renders bare URLs, and README media often uses HTML src/href.
        emitted_spans: list[tuple[int, int]] = []
        for m in RE_HTML_LINK_ATTR.finditer(line):
            target = m.group(1)
            if not is_githubish_url(target) or _span_contains(inline_spans, m.start(1)):
                continue
            emitted_spans.append((m.start(1), m.end(1)))
            results.append(_link_record(lineno, target, target, target, "html_attr"))

        for m in RE_GITHUBISH_URL.finditer(line):
            if _span_contains(inline_spans, m.start()) or _span_contains(emitted_spans, m.start()):
                continue
            target = _trim_bare_url(m.group(0))
            if not target:
                continue
            results.append(_link_record(lineno, target, target, target, "bare"))
    return results


_heading_slug_cache: dict[str, set[str]] = {}
_line_count_cache: dict[str, int] = {}

RE_LINE_FRAGMENT = re.compile(r"^[Ll]?(\d+)(?:-[Ll]?(\d+))?$")
RE_INCOMPLETE_LINE_FRAGMENT = re.compile(r"^[Ll]$", re.IGNORECASE)


def _get_heading_slugs(target_path: Path) -> set[str]:
    """Get heading slugs for a file, with caching."""
    key = str(target_path)
    if key not in _heading_slug_cache:
        try:
            text = target_path.read_text(encoding="utf-8", errors="replace")
            _heading_slug_cache[key] = extract_heading_slugs(text)
        except OSError:
            _heading_slug_cache[key] = set()
    return _heading_slug_cache[key]


def _get_line_count(target_path: Path) -> int:
    """Return text line count for a target file, with caching."""
    key = str(target_path)
    if key not in _line_count_cache:
        try:
            text = target_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            _line_count_cache[key] = 0
        else:
            _line_count_cache[key] = len(text.splitlines()) if text else 0
    return _line_count_cache[key]


def _validate_line_fragment(fragment: str, target: Path) -> dict | None:
    """Validate GitHub/VS Code-style line fragments such as #L10 or #L10-L20."""
    if RE_INCOMPLETE_LINE_FRAGMENT.match(fragment):
        return {
            "status": "broken_line",
            "resolved_path": target,
            "fix": None,
            "reason": "Line fragment '#L' is missing a line number",
        }

    match = RE_LINE_FRAGMENT.match(fragment)
    if not match:
        return None

    start = int(match.group(1))
    end = int(match.group(2) or start)
    if start < 1 or end < 1:
        return {
            "status": "broken_line",
            "resolved_path": target,
            "fix": None,
            "reason": f"Line fragment '#{fragment}' must use 1-based line numbers",
        }
    if end < start:
        return {
            "status": "broken_line",
            "resolved_path": target,
            "fix": None,
            "reason": f"Line range '#{fragment}' ends before it starts",
        }

    if not target.is_file():
        return None

    line_count = _get_line_count(target)
    if end > line_count:
        return {
            "status": "broken_line",
            "resolved_path": target,
            "fix": None,
            "reason": (
                f"Line fragment '#{fragment}' points past end of file "
                f"({target.name} has {line_count} line(s))"
            ),
        }

    return {"status": "ok_line", "resolved_path": target, "fix": None, "reason": None}


def _validate_fragment(
    fragment: str | None,
    resolved_path: Path | None,
    file_path: Path,
    link: dict,
) -> dict | None:
    """Check a #fragment against line refs or heading slugs.

    Works for both same-file anchors (resolved_path=file_path) and cross-file:
    - #L10, #l10, #10, #L10-L20, and #10-20 are validated against file length.
    - Markdown heading anchors are validated only for .md files.
    """
    if not fragment:
        return None
    # Determine which file contains the headings
    target = resolved_path if resolved_path is not None else file_path
    if not target.is_file():
        return None  # file doesn't exist — already handled by path resolution

    line_issue = _validate_line_fragment(fragment, target)
    if line_issue is not None:
        return None if line_issue["status"] == "ok_line" else line_issue

    if not str(target).lower().endswith(".md"):
        return None  # can't validate heading anchors in non-markdown files

    slugs = _get_heading_slugs(target)
    # Case-insensitive comparison (GitHub renders anchors lowercase,
    # but browsers resolve them case-insensitively)
    fragment_lower = fragment.lower()
    if fragment_lower in slugs:
        return None  # anchor exists, all good
    return {
        "status": "broken_anchor",
        "resolved_path": resolved_path,
        "fix": None,
        "reason": f"No header found: '{fragment}' in {target.name}",
    }


def resolve_github_link(
    link: dict,
    file_path: Path,
    repo_root: Path,
    github_online: bool = False,
    http_timeout: float = 10.0,
) -> dict:
    """Validate a GitHub/GFM HTTP link.

    Same-repo blob/tree/raw URLs are validated against the local checkout.
    Other GitHub pages/assets are checked only when --github-online is enabled.
    """
    target = link["target"]
    info = parse_github_url(target)
    if info is None:
        return {"status": "ok", "resolved_path": None, "fix": None, "reason": None}

    kind = info["kind"]

    if kind == "raw_host_malformed":
        return {
            "status": "broken_github",
            "resolved_path": None,
            "fix": None,
            "reason": "raw.githubusercontent.com URL is missing owner/repo/ref/path",
        }

    def online_result() -> dict:
        if not github_online:
            return {
                "status": "ok",
                "resolved_path": None,
                "fix": None,
                "reason": "GitHub URL shape recognized; live HTTP check not requested",
            }
        ok, reason = _http_link_status(target, http_timeout)
        return {
            "status": "ok" if ok else "broken_github",
            "resolved_path": None,
            "fix": None,
            "reason": None if ok else reason,
        }

    if kind in {"repo", "page", "github_page", "asset"}:
        return online_result()

    if kind in {"blob", "raw", "raw_host", "tree"}:
        if not _same_github_repo(info, repo_root):
            return online_result()

        want_dir = kind == "tree"
        resolved = _resolve_github_ref_path(info.get("segments", []), repo_root, want_dir=want_dir)
        if resolved is None:
            return {
                "status": "broken_github",
                "resolved_path": None,
                "fix": None,
                "reason": f"Same-repo GitHub {kind} URL does not resolve to a local {'directory' if want_dir else 'file'}",
            }

        _ref, _rel, local_path = resolved
        if local_path.is_file():
            anchor_issue = _validate_fragment(link.get("fragment"), local_path, file_path, link)
            if anchor_issue is not None:
                return anchor_issue
        return {"status": "ok", "resolved_path": local_path, "fix": None, "reason": None}

    if kind == "maybe_missing_blob":
        if not _same_github_repo(info, repo_root):
            return online_result()

        inferred = _infer_missing_blob_target(info.get("segments", []), repo_root)
        if inferred is None:
            if github_online:
                return online_result()
            return {
                "status": "broken_github",
                "resolved_path": None,
                "fix": None,
                "reason": (
                    "Same-repo GitHub URL is not a known page and is missing "
                    "'/blob/<ref>/', '/tree/<ref>/', or '/raw/<ref>/'"
                ),
            }

        ref, rel, local_path, mode = inferred
        fixed_url = _github_fix_url(info["parsed"], info["owner"], info["repo"], mode, ref, rel)
        fix = _format_target_fix(link, fixed_url)
        return {
            "status": "broken_github",
            "resolved_path": local_path,
            "fix": fix,
            "reason": (
                f"GitHub URL points at a same-repo {mode} path but is missing "
                f"'/{mode}/{ref}/'"
            ),
        }

    return online_result()


def resolve_link(
    link: dict,
    file_path: Path,
    repo_root: Path,
    collision_index: dict[str, list[Path]],
) -> dict:
    """Resolve a single link and return a diagnostic record.

    Returns a dict with:
        status: "ok" | "broken" | "ambiguous" | "empty_label" | "collision_unlabeled" | "broken_anchor" | "broken_line"
        resolved_path: the resolved Path (or None)
        fix: suggested replacement string (or None)
        reason: human-readable explanation
    """
    fragment = link.get("fragment")

    # --- Pure same-file anchor: [text](#slug) ---
    if link["path_part"] is None:
        issue = _validate_fragment(fragment, file_path, file_path, link)
        if issue is not None:
            return issue
        return {"status": "ok", "resolved_path": file_path, "fix": None, "reason": None}

    target_str = link["path_part"]
    file_dir = file_path.parent

    # Normalize: strip leading ./ prefix (not lstrip which eats chars individually)
    clean = target_str
    if clean.startswith("./"):
        clean = clean[2:]

    # --- Absolute path detection (Windows C:\... or /c:/... or /repo/path) ---
    # URL-decode percent-encoded chars (%20 etc.) before path construction
    decoded = _url_unquote(clean)
    abs_candidate = None
    if RE_WINDOWS_ABS.match(decoded):
        abs_candidate = Path(decoded)
    elif RE_WINDOWS_ABS.match(decoded.lstrip("/")):
        # Handle /c:/Users/... (leading slash before drive letter)
        abs_candidate = Path(decoded.lstrip("/"))

    if abs_candidate is not None:
        resolved_abs = abs_candidate.resolve()
        if resolved_abs.is_file() or resolved_abs.is_dir():
            try:
                resolved_abs.relative_to(repo_root)
            except ValueError:
                return {
                    "status": "ok",
                    "resolved_path": resolved_abs,
                    "fix": None,
                    "reason": "absolute path points outside repo",
                }
            # Absolute path points inside repo — generate correct relative path
            correct_rel = os.path.relpath(resolved_abs, file_dir).replace("\\", "/")
            frag = ""
            if fragment:
                frag = f"#{fragment}"
            fix = f"[{link['label']}]({correct_rel}{frag})"
            return {
                "status": "broken",
                "resolved_path": resolved_abs,
                "fix": fix,
                "reason": (
                    f"Absolute path '{target_str}' should be relative; "
                    f"correct relative path is '{correct_rel}'"
                ),
            }
        # Absolute path doesn't exist — fall through to normal resolution

    # Try resolve relative to the file's directory
    candidate_rel = (file_dir / clean).resolve()
    # Try resolve relative to repo root
    candidate_root = (repo_root / clean).resolve()

    resolved = None
    needs_path_fix = False
    if candidate_rel.is_file() or candidate_rel.is_dir():
        resolved = candidate_rel
    elif candidate_root.is_file() or candidate_root.is_dir():
        resolved = candidate_root
        # The link text resolves from repo root but NOT from the file's directory.
        # Markdown renderers resolve relative to the file — this link is effectively broken.
        needs_path_fix = True

    basename = Path(clean).name

    # Case 1: target resolves to a real file or directory
    if resolved is not None:
        # If the resolved path is outside the repo, it's still valid but skip
        # collision labeling (we can't compute a relative path).
        try:
            rel_path = resolved.relative_to(repo_root)
        except ValueError:
            return {"status": "ok", "resolved_path": resolved, "fix": None, "reason": None}

        # Case 0.5: target is a directory.
        # If the target explicitly ends with "/" the author means the directory
        # itself — that's intentional, treat it as OK. GitHub renders directory
        # links correctly even if VS Code's ctrl+click can't open them.
        # Only flag as dir_link when the target looks like it was meant to be
        # a file (no trailing slash, no slash in the label).
        if resolved.is_dir():
            target_looks_intentional = (
                target_str.endswith("/")
                or "/" in link["label"]
                or "\\" in link["label"]
            )
            if target_looks_intentional:
                # Author explicitly referenced a directory — valid
                pass  # fall through to normal collision/fragment checks below
            else:
                # Target resolves to a directory but doesn't look intentional
                readme_candidates = ["README.md", "readme.md", "index.md"]
                for rc in readme_candidates:
                    readme_path = resolved / rc
                    if readme_path.is_file():
                        correct_rel = os.path.relpath(readme_path, file_dir).replace("\\", "/")
                        fix = f"[{link['label']}]({correct_rel})"
                        return {
                            "status": "dir_link",
                            "resolved_path": resolved,
                            "fix": fix,
                            "reason": (
                                f"Target '{target_str}' resolves to a directory but lacks trailing '/'. "
                                f"Found '{rc}' inside; linking to that instead"
                            ),
                        }
                return {
                    "status": "dir_link",
                    "resolved_path": resolved,
                    "fix": None,
                    "reason": (
                        f"Target '{target_str}' resolves to a directory but lacks trailing '/'. "
                        f"No README.md found inside to link to"
                    ),
                }

        # Case 1a: Link resolves from repo root but not from the file's directory.
        # Markdown renderers resolve relative to the file — generate corrected path.
        if needs_path_fix:
            correct_rel = os.path.relpath(resolved, file_dir).replace("\\", "/")
            # Preserve fragment if present
            frag = ""
            if "#" in link["target"]:
                frag = "#" + link["target"].split("#", 1)[1]
            fix = f"[{link['label']}]({correct_rel}{frag})"
            return {
                "status": "broken",
                "resolved_path": resolved,
                "fix": fix,
                "reason": (
                    f"Path '{target_str}' resolves from repo root but not from "
                    f"file directory '{file_dir.relative_to(repo_root)}'; "
                    f"correct relative path is '{correct_rel}'"
                ),
            }

        # Check if the basename has collisions
        siblings = collision_index.get(basename, [])
        if len(siblings) > 1:
            # The link works, but the basename is ambiguous in the repo.
            # However, if the target path already contains directory components
            # (e.g., "../../AGENT_COMMON.md" or "docs/foo.md"), the path itself
            # disambiguates which copy is meant — no label fix needed.
            target_has_dir = "/" in clean or "\\" in clean
            # Check if the label includes a directory qualifier
            label = link["label"]
            if (
                not target_has_dir
                and basename in label
                and "(" not in label
                and "/" not in label
            ):
                # Bare basename target AND bare basename label — recommend disambiguation
                parent_hint = rel_path.parent.name or str(rel_path.parent)
                if parent_hint == ".":
                    parent_hint = "repo-root"
                suggested_label = f"{basename} ({parent_hint})"
                fix = f"[{suggested_label}]({link['target']})"
                return {
                    "status": "collision_unlabeled",
                    "resolved_path": resolved,
                    "fix": fix,
                    "reason": (
                        f"'{basename}' exists in {len(siblings)} locations; "
                        f"label should disambiguate with directory qualifier"
                    ),
                }
        # File resolves — now validate fragment if present
        anchor_issue = _validate_fragment(fragment, resolved, file_path, link)
        if anchor_issue is not None:
            return anchor_issue
        return {"status": "ok", "resolved_path": resolved, "fix": None, "reason": None}

    # Case 2: target doesn't resolve — can we find a unique match?
    candidates = collision_index.get(basename, [])

    if len(candidates) == 1:
        # Unique match — the path was just wrong. Suggest fix.
        correct = candidates[0]
        correct_rel = os.path.relpath(correct, file_dir).replace("\\", "/")
        # Preserve fragment if present
        fragment = ""
        if "#" in link["target"]:
            fragment = "#" + link["target"].split("#", 1)[1]
        fix = f"[{link['label']}]({correct_rel}{fragment})"
        return {
            "status": "broken",
            "resolved_path": correct,
            "fix": fix,
            "reason": f"Path '{target_str}' not found; unique match at '{correct_rel}'",
        }

    if len(candidates) > 1:
        # Multiple candidates — ambiguous, can't auto-fix
        locs = [str(c.relative_to(repo_root)) for c in candidates]
        # Empty-label links [](path) are structural noise, not real ambiguity
        status = "empty_label" if not link["label"] else "ambiguous"
        return {
            "status": status,
            "resolved_path": None,
            "fix": None,
            "reason": (
                f"Path '{target_str}' not found; basename '{basename}' exists in "
                f"{len(candidates)} locations: {', '.join(locs[:5])}"
            ),
        }

    # Case 3: no match at all — file is genuinely deleted.
    # Empty-label links with no matches are structural noise, not broken refs
    if not link["label"]:
        return {
            "status": "empty_label",
            "resolved_path": None,
            "fix": None,
            "reason": f"Empty-label link to '{target_str}'; no file named '{basename}' in repo",
        }
    # Delink: replace [label](path) with just the label text.
    label = link["label"]
    delink = label if label else ""
    return {
        "status": "broken",
        "resolved_path": None,
        "fix": delink,
        "reason": f"Path '{target_str}' not found and no file named '{basename}' exists in repo — delinked",
    }


# =============================================================================
# Audit Engine
# =============================================================================

def audit_file(
    file_path: Path,
    repo_root: Path,
    collision_index: dict[str, list[Path]],
    github_links: bool = False,
    github_online: bool = False,
    github_timeout: float = 10.0,
) -> dict:
    """Audit all internal markdown links in a file.

    Returns a summary dict with diagnostics per link.
    """
    text = file_path.read_text(encoding="utf-8", errors="replace")
    links = extract_links(text, include_external=github_links or github_online)
    results = []

    for link in links:
        if link.get("external"):
            if not is_githubish_url(link["target"]):
                continue
            diag = resolve_github_link(
                link,
                file_path,
                repo_root,
                github_online=github_online,
                http_timeout=github_timeout,
            )
        else:
            diag = resolve_link(link, file_path, repo_root, collision_index)
        results.append({
            "line": link["line"],
            "original": link["full_match"],
            "label": link["label"],
            "target": link["target"],
            **diag,
        })

    ok = [r for r in results if r["status"] == "ok"]
    broken = [r for r in results if r["status"] in ("broken", "broken_anchor", "broken_line", "broken_github")]
    ambiguous = [r for r in results if r["status"] == "ambiguous"]
    empty_label = [r for r in results if r["status"] == "empty_label"]
    unlabeled = [r for r in results if r["status"] == "collision_unlabeled"]
    fixable = [r for r in results if r["fix"] is not None]

    return {
        "file": str(file_path.relative_to(repo_root)),
        "total_links": len(results),
        "ok": len(ok),
        "broken": len(broken),
        "ambiguous": len(ambiguous),
        "empty_label": len(empty_label),
        "collision_unlabeled": len(unlabeled),
        "fixable": len(fixable),
        "issues": [r for r in results if r["status"] != "ok"],
        "all": results,
    }


def load_staged_renames(repo_root: Path) -> list[dict]:
    """Load staged rename pairs from git index."""
    proc = subprocess.run(
        ["git", "diff", "--cached", "--name-status", "--diff-filter=R"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "git diff --cached failed")

    renames: list[dict] = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        status, old_path, new_path = parts[0], parts[1], parts[2]
        renames.append({
            "status": status,
            "old_rel": old_path.replace("\\", "/"),
            "new_rel": new_path.replace("\\", "/"),
            "old_abs": (repo_root / old_path).resolve(),
            "new_abs": (repo_root / new_path).resolve(),
        })
    return renames


# Lifecycle values that exclude a file from active link auditing.
# - tombstone: file is dead, preserved for history
# - ssot-canon: file is the macro-prompt-world / unabridged source from
#   which downstream slimmed references are derived. Scanning broken refs
#   on the SSOT itself inverts the dependency direction.
# Mirrors EXCLUDED_LIFECYCLES in scripts/git_rot_index.py and
# ci/checks/link-audit.ts so the method travels consistently wherever
# link auditing happens.
EXCLUDED_LIFECYCLES = {"tombstone", "ssot-canon"}


def is_lifecycle_excluded(path: Path) -> bool:
    """
    True when the file's YAML frontmatter declares lifecycle: <value>
    where <value> is in EXCLUDED_LIFECYCLES. BOM-tolerant.
    """
    try:
        head = path.read_text(encoding="utf-8", errors="replace").splitlines()[:20]
    except OSError:
        return False
    in_fm = False
    for line in head:
        # Strip UTF-8 BOM if present (some files are saved with BOM by editors).
        clean = line.lstrip("﻿").strip()
        if clean == "---":
            if in_fm:
                return False
            in_fm = True
            continue
        if in_fm:
            m = re.match(r"^\s*lifecycle\s*:\s*([\w-]+)", line.lstrip("﻿"))
            if m and m.group(1) in EXCLUDED_LIFECYCLES:
                return True
    return False


def scan_repo_markdown(repo_root: Path) -> list[Path]:
    """Collect markdown files in the repo, skipping generated/heavy dirs
    and files marked with EXCLUDED_LIFECYCLES (tombstone / ssot-canon).
    """
    files: list[Path] = []
    root_str = str(repo_root)
    for dirpath, dirnames, filenames in os.walk(root_str):
        dirnames[:] = [
            d for d in dirnames
            if d not in SKIP_DIRS and not d.startswith(".venv")
        ]
        for fname in filenames:
            if fname.lower().endswith(".md") and not RE_SKIP_BASENAME.match(fname):
                p = Path(dirpath) / fname
                if is_lifecycle_excluded(p):
                    continue
                files.append(p)
    return sorted(files)


def resolve_staged_rename_fix(link: dict, file_path: Path, repo_root: Path, renames: list[dict]) -> dict | None:
    """Resolve a markdown link against staged rename pairs."""
    target = link["target"]
    path_part = link["path_part"]
    if path_part is None:
        return None
    fragment = ""
    if "#" in target:
        fragment = "#" + target.split("#", 1)[1]

    file_dir = file_path.parent
    clean = path_part[2:] if path_part.startswith("./") else path_part
    candidate_rel = (file_dir / clean).resolve()
    candidate_root = (repo_root / clean).resolve()

    for rename in renames:
        if candidate_rel == rename["old_abs"] or candidate_root == rename["old_abs"]:
            replacement_rel = os.path.relpath(rename["new_abs"], file_dir).replace("\\", "/")
            if not replacement_rel.startswith(".") and "/" not in replacement_rel:
                replacement_rel = f"./{replacement_rel}"
            return {
                "status": "staged_rename",
                "resolved_path": str(rename["new_abs"].relative_to(repo_root)),
                "fix": f"[{link['label']}]({replacement_rel}{fragment})",
                "reason": (
                    f"Path '{path_part}' points to staged rename "
                    f"'{rename['old_rel']}' -> '{rename['new_rel']}'"
                ),
            }
    return None


def audit_file_against_staged_renames(file_path: Path, repo_root: Path, renames: list[dict]) -> dict:
    """Audit one markdown file against the staged rename set."""
    text = file_path.read_text(encoding="utf-8", errors="replace")
    links = extract_links(text)
    issues = []

    for link in links:
        diag = resolve_staged_rename_fix(link, file_path, repo_root, renames)
        if diag is None:
            continue
        issues.append({
            "line": link["line"],
            "original": link["full_match"],
            "label": link["label"],
            "target": link["target"],
            **diag,
        })

    return {
        "file": str(file_path.relative_to(repo_root)),
        "total_links": len(links),
        "fixable": len(issues),
        "issues": issues,
    }


def apply_fixes(file_path: Path, issues: list[dict], backup: bool = True) -> int:
    """Apply fixable replacements to a file. Returns count of fixes applied."""
    fixable = [i for i in issues if i["fix"] is not None]
    if not fixable:
        return 0

    text = file_path.read_text(encoding="utf-8", errors="replace")
    count = 0
    for issue in fixable:
        old = issue["original"]
        new = issue["fix"]
        if old in text:
            text = text.replace(old, new, 1)
            count += 1

    if count:
        if backup:
            bak = file_path.with_name(file_path.name + ".bak")
            bak.write_bytes(file_path.read_bytes())
        file_path.write_text(text, encoding="utf-8")
    return count


# =============================================================================
# Inert Backtick Scanner
# =============================================================================

def looks_like_path_literal(text: str) -> bool:
    """Heuristic guard for inert backtick refs.

    Conservative by default:
    - always accept slash-based paths and known extensions
    - accept hidden dot-paths/dotfiles
    - accept generic dotted filenames so new filetypes are discoverable
    """
    candidate = text.strip()
    if not candidate:
        return False
    if "/" in candidate or "\\" in candidate:
        return True
    if RE_FILEISH_EXT.search(candidate):
        return True
    if candidate.startswith("."):
        return True
    return RE_GENERIC_DOTTED_NAME.match(candidate) is not None

def scan_inert_backticks(file_path: Path) -> list[dict]:
    """Find backtick-wrapped file/path-like literals outside code blocks.

    Returns a list of dicts with keys: line, text.
    Skips backticks that are part of markdown link labels ([`x`](url)).
    """
    text = file_path.read_text(encoding="utf-8")
    hits: list[dict] = []
    in_fence = False
    for lineno, line in enumerate(text.split("\n"), start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for m in RE_BACKTICK.finditer(line):
            txt = m.group(1)
            if not looks_like_path_literal(txt):
                continue
            # Skip if part of markdown link label: [`text`](url)
            s = m.start()
            if s > 0 and line[s - 1] == "[":
                continue
            hits.append({"line": lineno, "text": txt, "original": m.group(0)})
    return hits


def format_backtick_target(file_dir: Path, resolved: Path) -> str:
    """Format a resolved path as a markdown target relative to the source file."""
    rel = Path(os.path.relpath(resolved, start=file_dir)).as_posix()
    if rel == ".":
        rel = "./"
    if resolved.is_dir() and not rel.endswith("/"):
        rel += "/"
    return rel


def resolve_backtick_ref(
    hit: dict,
    file_path: Path,
    repo_root: Path,
    collision_index: dict[str, list[Path]],
) -> dict:
    """Resolve an inert backtick ref and suggest a markdown-link replacement when safe."""
    raw = hit["text"].strip()
    clean = raw.replace("\\", "/")
    file_dir = file_path.parent

    if any(ch in raw for ch in ("*", "?", "[", "]", "{", "}")):
        return {
            "status": "skipped_pattern",
            "resolved_path": None,
            "fix": None,
            "reason": "contains wildcard or pattern syntax; keep as illustrative literal",
        }

    resolved: Path | None = None

    if RE_WINDOWS_ABS.match(raw):
        candidate = Path(raw)
        if candidate.exists():
            try:
                candidate.relative_to(repo_root)
            except ValueError:
                return {
                    "status": "skipped_external",
                    "resolved_path": None,
                    "fix": None,
                    "reason": "absolute path points outside repo; keep as literal",
                }
            resolved = candidate.resolve()
    else:
        candidates: list[Path] = []
        if clean.startswith("/"):
            candidates.append((repo_root / clean.lstrip("/")).resolve())
        else:
            candidates.append((file_dir / clean).resolve())
            candidates.append((repo_root / clean).resolve())

        for candidate in candidates:
            if candidate.is_file() or candidate.is_dir():
                resolved = candidate
                break

    if resolved is not None:
        target = format_backtick_target(file_dir, resolved)
        return {
            "status": "fixable",
            "resolved_path": resolved,
            "fix": f"[`{raw}`]({target})",
            "reason": f"resolved to '{target}'",
        }

    basename = Path(clean.rstrip("/")).name
    if not basename:
        return {
            "status": "unresolved",
            "resolved_path": None,
            "fix": None,
            "reason": "empty path component after normalization",
        }

    matches = collision_index.get(basename, [])
    if len(matches) == 1:
        resolved = matches[0]
        target = format_backtick_target(file_dir, resolved)
        return {
            "status": "fixable",
            "resolved_path": resolved,
            "fix": f"[`{raw}`]({target})",
            "reason": f"unique basename match at '{target}'",
        }
    if len(matches) > 1:
        return {
            "status": "ambiguous",
            "resolved_path": None,
            "fix": None,
            "reason": f"basename '{basename}' exists in {len(matches)} repo locations",
        }
    return {
        "status": "unresolved",
        "resolved_path": None,
        "fix": None,
        "reason": f"no repo path resolves for '{raw}'",
    }


def audit_inert_backticks(
    file_path: Path,
    repo_root: Path,
    collision_index: dict[str, list[Path]],
) -> dict:
    """Audit inert backtick refs and classify which can be upgraded into links."""
    hits = scan_inert_backticks(file_path)
    results = []
    for hit in hits:
        diag = resolve_backtick_ref(hit, file_path, repo_root, collision_index)
        results.append(
            {
                "line": hit["line"],
                "text": hit["text"],
                "original": hit["original"],
                **diag,
            }
        )

    counts = {
        "fixable": sum(1 for item in results if item["status"] == "fixable"),
        "ambiguous": sum(1 for item in results if item["status"] == "ambiguous"),
        "unresolved": sum(1 for item in results if item["status"] == "unresolved"),
        "skipped_pattern": sum(1 for item in results if item["status"] == "skipped_pattern"),
        "skipped_external": sum(1 for item in results if item["status"] == "skipped_external"),
    }

    return {
        "file": str(file_path.relative_to(repo_root)),
        "inert_backtick_refs": len(results),
        **counts,
        "hits": results,
    }


def apply_backtick_fixes(file_path: Path, hits: list[dict], backup: bool = True) -> int:
    """Apply fixable inert-backtick rewrites to a file."""
    fixable = [item for item in hits if item["fix"] is not None]
    if not fixable:
        return 0

    text = file_path.read_text(encoding="utf-8", errors="replace")
    applied = 0
    for item in fixable:
        old = item["original"]
        new = item["fix"]
        if old in text:
            text = text.replace(old, new, 1)
            applied += 1

    if applied:
        if backup:
            bak = file_path.with_name(file_path.name + ".bak")
            bak.write_bytes(file_path.read_bytes())
        file_path.write_text(text, encoding="utf-8")
    return applied


# =============================================================================
# CLI
# =============================================================================

def main() -> int:
    configure_utf8_output()

    parser = argparse.ArgumentParser(
        description="Audit and fix markdown [label](path) references."
    )
    sub = parser.add_subparsers(dest="command")

    # check
    p_check = sub.add_parser("check", help="Audit links in a markdown file")
    p_check.add_argument("file", type=Path, help="File to audit")
    p_check.add_argument("--fix", action="store_true",
                         help="Apply fixes to the file in-place")
    p_check.add_argument("--dry-run", action="store_true",
                         help="Show what --fix would do without writing")
    p_check.add_argument("--no-backup", action="store_true",
                         help="Skip .bak backup before in-place rewrite")
    p_check.add_argument("--github-links", action="store_true",
                         help="Also audit GitHub/GFM HTTP URL shapes")
    p_check.add_argument("--github-online", action="store_true",
                         help="Also perform live HTTP checks for GitHub pages/assets")
    p_check.add_argument("--github-timeout", type=float, default=10.0,
                         help="Timeout in seconds for --github-online checks (default: 10)")

    # collisions
    p_coll = sub.add_parser("collisions", help="List all basename collisions in the repo")
    p_coll.add_argument("--min-count", type=int, default=2,
                        help="Minimum collision count to report (default: 2)")
    p_coll.add_argument("--filter", type=str, default=None,
                        help="Filter by extension (e.g., .md)")

    # backticks
    p_bt = sub.add_parser("backticks", help="Scan for inert backtick file/path refs outside code blocks")
    p_bt.add_argument("file", type=Path, help="File to scan")
    p_bt.add_argument("--fix", action="store_true", help="Upgrade fixable inert backticks to markdown links")
    p_bt.add_argument("--dry-run", action="store_true", help="Show what --fix would rewrite without writing")
    p_bt.add_argument("--no-backup", action="store_true", help="Skip .bak backup before in-place rewrite")
    p_bt.add_argument("--json", dest="bt_json", action="store_true", help="JSON output")

    # scan
    p_scan = sub.add_parser("scan", help="Audit all markdown files in the repo")
    p_scan.add_argument("--fix", action="store_true",
                        help="Apply fixes to all files in-place")
    p_scan.add_argument("--dry-run", action="store_true",
                        help="Show what --fix would do without writing")
    p_scan.add_argument("--no-backup", action="store_true",
                        help="Skip .bak backups before in-place rewrites")
    p_scan.add_argument("--changed", action="store_true",
                        help="Only scan files changed vs HEAD (git diff --name-only)")
    p_scan.add_argument("--paths", nargs="*", type=Path, metavar="FILE",
                        help="Only scan these specific files")
    p_scan.add_argument("--json", action="store_true", help="JSON output")
    p_scan.add_argument("--github-links", action="store_true",
                        help="Also audit GitHub/GFM HTTP URL shapes")
    p_scan.add_argument("--github-online", action="store_true",
                        help="Also perform live HTTP checks for GitHub pages/assets")
    p_scan.add_argument("--github-timeout", type=float, default=10.0,
                        help="Timeout in seconds for --github-online checks (default: 10)")

    # renames
    p_renames = sub.add_parser("renames", help="Audit markdown links against staged renames")
    p_renames.add_argument("--staged", action="store_true",
                           help="Use staged git renames as the source set")
    p_renames.add_argument("--fix", action="store_true",
                           help="Apply fixable replacements to affected markdown files")
    p_renames.add_argument("--dry-run", action="store_true",
                           help="Show what --fix would do without writing")
    p_renames.add_argument("--no-backup", action="store_true",
                           help="Skip .bak backup before in-place rewrite")
    p_renames.add_argument("--json", action="store_true", help="JSON output")

    # Common options (--json is now per-subcommand; check + collisions get it here)
    p_check.add_argument("--json", action="store_true", help="JSON output")
    p_coll.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--quiet", "-q", action="store_true")

    args = parser.parse_args()
    log = setup_logging(verbose=args.verbose, quiet=args.quiet)
    repo_root = find_repo_root()

    if not args.command:
        parser.print_help()
        return 0

    no_backup = getattr(args, "no_backup", False)
    if args.command == "backticks":
        file_path = args.file.resolve()
        if not file_path.is_file():
            log.error("File not found: %s", file_path)
            return 1
        index = build_collision_index(repo_root)
        result = audit_inert_backticks(file_path, repo_root, index)
        use_json = getattr(args, "bt_json", False) or getattr(args, "json", False)
        if use_json:
            payload = dict(result)
            for item in payload["hits"]:
                if item.get("resolved_path"):
                    item["resolved_path"] = _safe_relative_path(item["resolved_path"], repo_root)
            print(json.dumps(payload, indent=2))
        else:
            if not result["hits"]:
                print(f"OK: {result['file']} — 0 inert backtick file/path refs")
            else:
                print(f"AUDIT: {result['file']}")
                print(
                    f"  Inert refs: {result['inert_backtick_refs']} total, "
                    f"{result['fixable']} fixable, {result['ambiguous']} ambiguous, "
                    f"{result['unresolved']} unresolved, "
                    f"{result['skipped_pattern'] + result['skipped_external']} skipped"
                )
                for hit in result["hits"]:
                    tag = {
                        "fixable": "FIXABLE",
                        "ambiguous": "AMBIG",
                        "unresolved": "UNRESOLVED",
                        "skipped_pattern": "SKIP",
                        "skipped_external": "SKIP",
                    }.get(hit["status"], hit["status"].upper())
                    print(f"\n  L{hit['line']} [{tag}] {hit['original']}")
                    print(f"    Reason: {hit['reason']}")
                    if hit["fix"]:
                        print(f"    Fix:    {hit['fix']}")

        if args.dry_run:
            print(f"\n--dry-run: {result['fixable']} fixes would be applied (no changes written)")
            return 0 if result["inert_backtick_refs"] == 0 else 1

        if args.fix and result["fixable"]:
            applied = apply_backtick_fixes(file_path, result["hits"], backup=not no_backup)
            rerun = audit_inert_backticks(file_path, repo_root, index)
            print(f"\nApplied {applied} fix(es)")
            return 0 if rerun["inert_backtick_refs"] == 0 else 1

        return 1 if result["hits"] else 0

    # --- collisions ---
    if args.command == "collisions":
        log.info("Building file index from %s ...", repo_root)
        index = build_collision_index(repo_root)
        collisions = get_collisions(index)

        if args.filter:
            collisions = {
                k: v for k, v in collisions.items()
                if k.endswith(args.filter)
            }

        collisions = {
            k: v for k, v in collisions.items()
            if len(v) >= args.min_count
        }

        if args.json:
            out = {
                name: [str(p.relative_to(repo_root)) for p in paths]
                for name, paths in sorted(collisions.items(), key=lambda x: -len(x[1]))
            }
            print(json.dumps(out, indent=2))
        else:
            print(f"Basename collisions ({len(collisions)} names):\n")
            for name, paths in sorted(collisions.items(), key=lambda x: -len(x[1])):
                print(f"  {name} ({len(paths)} copies):")
                for p in sorted(paths):
                    print(f"    {p.relative_to(repo_root)}")
        return 0

    # --- renames ---
    if args.command == "renames":
        if not args.staged:
            log.error("renames currently requires --staged")
            return 1

        try:
            renames = load_staged_renames(repo_root)
        except RuntimeError as exc:
            log.error("Failed to load staged renames: %s", exc)
            return 1
        if not renames:
            print("No staged renames found.")
            return 0

        markdown_files = scan_repo_markdown(repo_root)
        results = []
        for file_path in markdown_files:
            result = audit_file_against_staged_renames(file_path, repo_root, renames)
            if result["issues"]:
                results.append(result)

        impacted_files = len(results)
        impacted_issues = sum(len(result["issues"]) for result in results)

        if args.json and not args.fix and not args.dry_run:
            print(json.dumps({
                "staged_renames": [
                    {
                        "status": rename["status"],
                        "old_rel": rename["old_rel"],
                        "new_rel": rename["new_rel"],
                    }
                    for rename in renames
                ],
                "impacted_files": impacted_files,
                "impacted_issues": impacted_issues,
                "results": results,
            }, indent=2))
            return 0 if impacted_issues == 0 else 1

        print(f"STAGED RENAMES: {len(renames)}")
        print(f"IMPACTED FILES: {impacted_files}")
        print(f"FIXABLE LINKS: {impacted_issues}")

        for result in results:
            print(f"\nAUDIT: {result['file']}")
            for issue in result["issues"]:
                print(f"  L{issue['line']} [STAGED] {issue['original']}")
                print(f"    Reason: {issue['reason']}")
                print(f"    Fix:    {issue['fix']}")

        if args.dry_run:
            print(f"\n--dry-run: {impacted_issues} fixes would be applied across {impacted_files} files")
            return 0 if impacted_issues == 0 else 1

        if args.fix and impacted_issues:
            applied = 0
            touched = 0
            for result in results:
                file_path = repo_root / result["file"]
                count = apply_fixes(file_path, result["issues"], backup=not no_backup)
                if count:
                    touched += 1
                    applied += count
            print(f"\nApplied {applied} fix(es) across {touched} file(s)")
            return 0 if applied == impacted_issues else 1

        return 0 if impacted_issues == 0 else 1

    # --- scan ---
    if args.command == "scan":
        if args.paths:
            md_files = [p.resolve() for p in args.paths if p.resolve().is_file()]
        elif args.changed:
            try:
                diff_out = subprocess.run(
                    ["git", "diff", "--name-only", "HEAD"],
                    capture_output=True, text=True, cwd=str(repo_root),
                )
            except FileNotFoundError:
                log.error("git not found — cannot use --changed")
                return 1
            changed = [
                (repo_root / line.strip()).resolve()
                for line in diff_out.stdout.splitlines()
                if line.strip().lower().endswith(".md")
            ]
            md_files = sorted(p for p in changed if p.is_file())
        else:
            md_files = scan_repo_markdown(repo_root)

        log.info("Building file index ...")
        index = build_collision_index(repo_root)

        log.info("Scanning %d markdown files ...", len(md_files))

        all_results = []
        github_links = args.github_links or args.github_online
        for md_file in md_files:
            result = audit_file(
                md_file,
                repo_root,
                index,
                github_links=github_links,
                github_online=args.github_online,
                github_timeout=args.github_timeout,
            )
            if result["issues"]:
                all_results.append(result)

        total_files = len(md_files)
        impacted_files = len(all_results)
        total_issues = sum(len(r["issues"]) for r in all_results)
        total_fixable = sum(r["fixable"] for r in all_results)
        total_broken = sum(r["broken"] for r in all_results)
        total_ambiguous = sum(r["ambiguous"] for r in all_results)
        total_empty_label = sum(r["empty_label"] for r in all_results)

        if args.json and not args.fix and not args.dry_run:
            for result in all_results:
                for item in result.get("all", []):
                    if item.get("resolved_path"):
                        item["resolved_path"] = _safe_relative_path(item["resolved_path"], repo_root)
                for item in result.get("issues", []):
                    if item.get("resolved_path"):
                        item["resolved_path"] = _safe_relative_path(item["resolved_path"], repo_root)
            print(json.dumps({
                "total_files": total_files,
                "impacted_files": impacted_files,
                "total_issues": total_issues,
                "total_fixable": total_fixable,
                "total_broken": total_broken,
                "total_ambiguous": total_ambiguous,
                "total_empty_label": total_empty_label,
                "results": all_results,
            }, indent=2))
            return 0 if total_issues == 0 else 1

        if not all_results:
            print(f"OK: {total_files} files scanned, all links valid")
            return 0

        print(f"SCAN: {total_files} files, {impacted_files} with issues")
        print(f"  Issues: {total_issues} total — {total_broken} broken, "
              f"{total_ambiguous} ambiguous, {total_empty_label} empty-label, "
              f"{total_fixable} fixable")

        for result in all_results:
            print(f"\n  {result['file']}:")
            for issue in result["issues"]:
                tag = {
                    "broken": "BROKEN",
                    "broken_anchor": "ANCHOR",
                    "broken_line": "LINE",
                    "broken_github": "GITHUB",
                    "ambiguous": "AMBIG",
                    "empty_label": "EMPTY",
                    "collision_unlabeled": "LABEL",
                    "dir_link": "DIR",
                }.get(issue["status"], issue["status"].upper())
                fix_hint = f" -> {issue['fix']!r}" if issue["fix"] is not None else ""
                print(f"    L{issue['line']} [{tag}] {issue['original']}{fix_hint}")

        if args.dry_run:
            print(f"\n--dry-run: {total_fixable} fixes would be applied "
                  f"across {impacted_files} file(s) (no changes written)")
            return 0 if total_issues == 0 else 1

        if args.fix and total_fixable:
            applied = 0
            touched = 0
            for result in all_results:
                file_path = repo_root / result["file"]
                count = apply_fixes(file_path, result["issues"], backup=not no_backup)
                if count:
                    touched += 1
                    applied += count
            print(f"\nApplied {applied} fix(es) across {touched} file(s)")
            return 0 if applied == total_fixable else 1

        if total_fixable and not args.fix:
            print(f"\n{total_fixable} fixable issue(s). "
                  f"Run with --fix to apply or --dry-run to preview.")

        return 1 if total_issues else 0

    # --- check ---
    if args.command == "check":
        file_path = args.file.resolve()
        if not file_path.is_file():
            log.error("File not found: %s", file_path)
            return 1

        log.info("Building file index ...")
        index = build_collision_index(repo_root)

        github_links = args.github_links or args.github_online
        result = audit_file(
            file_path,
            repo_root,
            index,
            github_links=github_links,
            github_online=args.github_online,
            github_timeout=args.github_timeout,
        )

        if args.json and not args.dry_run and not args.fix:
            # Strip non-serializable Path objects
            for item in result.get("all", []):
                if item.get("resolved_path"):
                    item["resolved_path"] = _safe_relative_path(item["resolved_path"], repo_root)
            for item in result.get("issues", []):
                if item.get("resolved_path"):
                    item["resolved_path"] = _safe_relative_path(item["resolved_path"], repo_root)
            print(json.dumps(result, indent=2))
            return 0 if not result["issues"] else 1

        # Human output
        issues = result["issues"]
        fixable = [i for i in issues if i["fix"] is not None]

        if not issues:
            print(f"OK: {result['file']} — {result['total_links']} links, all valid")
            return 0

        print(f"AUDIT: {result['file']}")
        print(f"  Links: {result['total_links']} total, {result['ok']} ok, "
              f"{result['broken']} broken, {result['ambiguous']} ambiguous, "
              f"{result['empty_label']} empty-label, "
              f"{result['collision_unlabeled']} unlabeled collisions")

        for issue in issues:
            status_icon = {
                "broken": "BROKEN",
                "broken_anchor": "ANCHOR",
                "broken_line": "LINE",
                "broken_github": "GITHUB",
                "ambiguous": "AMBIG",
                "empty_label": "EMPTY",
                "collision_unlabeled": "LABEL",
                "dir_link": "DIR",
            }.get(issue["status"], issue["status"].upper())
            print(f"\n  L{issue['line']} [{status_icon}] {issue['original']}")
            print(f"    Reason: {issue['reason']}")
            if issue["fix"] is not None:
                print(f"    Fix:    {issue['fix']!r}")

        if args.dry_run:
            print(f"\n--dry-run: {len(fixable)} fixes would be applied (no changes written)")
            return 1 if issues else 0

        if args.fix and fixable:
            applied = apply_fixes(file_path, issues, backup=not no_backup)
            print(f"\nApplied {applied} fix(es) to {result['file']}")
            return 0 if applied == len(fixable) else 1

        if fixable and not args.fix:
            print(f"\n{len(fixable)} fixable issue(s). Run with --fix to apply or --dry-run to preview.")

        return 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
