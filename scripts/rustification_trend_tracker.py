#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: rustification_trend_tracker.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Rustification trend tracker prototype.

Purpose:
- Pull recent language trend signals from GitHub repository activity.
- Cross-reference trend languages against endoflife.date product metadata.
- Compare trend languages with currently available chthonic/polyglot lanes.
- Emit a timestamped trace with the requested minute.day.month.year stamp.

@SID:           TOOL_RUSTIFICATION_TREND_TRACKER_V1
@Shabti:        CLI Script
@Purpose:       Rustification trend tracker prototype.
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


MAILBOX_DIRS = {
    "codex": Path("codex/mailbox"),
    "claude": Path("claude/mailbox"),
}


LANGUAGE_MODEL = {
    "python": {"lane": "python", "tools": ["uv", "python"], "preferred_slug": "python"},
    "ruby": {"lane": "ruby", "tools": ["rvw", "ruby"], "preferred_slug": "ruby"},
    "rust": {"lane": "rust", "tools": ["rustup", "rustc", "cargo"], "preferred_slug": "rust"},
    "go": {"lane": "go", "tools": ["goup", "go"], "preferred_slug": "go"},
    "javascript": {"lane": "javascript", "tools": ["bun", "node"], "preferred_slug": "nodejs"},
    "typescript": {"lane": "javascript", "tools": ["bun", "node"], "preferred_slug": "nodejs"},
    "elixir": {"lane": "elixir", "tools": ["elixir", "mix"], "preferred_slug": "elixir"},
    "erlang": {"lane": "erlang", "tools": ["erl"], "preferred_slug": "erlang"},
    "java": {"lane": "java", "tools": ["java"], "preferred_slug": "openjdk"},
    "c#": {"lane": "dotnet", "tools": ["dotnet"], "preferred_slug": "dotnet"},
    "c++": {"lane": "cpp", "tools": ["cl", "clang++", "g++"], "preferred_slug": None},
    "c": {"lane": "cpp", "tools": ["cl", "clang", "gcc"], "preferred_slug": None},
}


def find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for path in [cur, *cur.parents]:
        if (path / "AGENTS.md").exists() and (path / ".gitignore").exists():
            return path
    raise SystemExit("Could not locate repo root (expected AGENTS.md + .gitignore).")


REPO_ROOT = find_repo_root(Path(__file__))


@dataclass
class TrendRow:
    language: str
    repos: int
    stars: int
    score: float
    lane: str
    lane_present: bool
    runtime_present: bool
    eol_slug: str | None
    eol_latest: str | None
    eol_cycle: str | None
    eol_state: str


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def stamp_minute_day_month_year(now: datetime) -> str:
    # Requested format: minute.day.month.year
    return now.strftime("%M.%d.%m.%Y")


def http_json(url: str, headers: dict[str, str] | None = None) -> dict | list:
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = resp.read().decode("utf-8", errors="replace")
    return json.loads(payload)


def fetch_endoflife_catalog() -> dict:
    data = http_json("https://endoflife.date/api/v1/products")
    if not isinstance(data, dict) or "result" not in data:
        raise RuntimeError("Unexpected endoflife catalog payload.")
    return data


def build_product_index(catalog: dict) -> dict[str, dict]:
    index: dict[str, dict] = {}
    for product in catalog.get("result", []):
        name = (product.get("name") or "").strip().lower()
        if name:
            index[name] = product
        for alias in product.get("aliases", []) or []:
            alias_key = str(alias).strip().lower()
            if alias_key and alias_key not in index:
                index[alias_key] = product
    return index


def fetch_product_details(slug: str) -> dict | None:
    try:
        payload = http_json(f"https://endoflife.date/api/v1/products/{slug}")
    except Exception:
        return None
    if isinstance(payload, dict):
        return payload.get("result")
    return None


def fetch_github_trends(window_days: int, pages: int, per_page: int) -> tuple[dict[str, int], dict[str, int]]:
    since = (utc_now() - timedelta(days=window_days)).date().isoformat()
    query = f"created:>{since} stars:>20"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "chthonic-rustification-tracker",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    counts: dict[str, int] = defaultdict(int)
    stars: dict[str, int] = defaultdict(int)

    for page in range(1, pages + 1):
        q = urllib.parse.quote(query)
        url = (
            "https://api.github.com/search/repositories"
            f"?q={q}&sort=stars&order=desc&per_page={per_page}&page={page}"
        )
        data = http_json(url, headers=headers)
        items = data.get("items", []) if isinstance(data, dict) else []
        if not items:
            break

        for item in items:
            lang = item.get("language")
            if not lang:
                continue
            lang_name = str(lang).strip()
            counts[lang_name] += 1
            stars[lang_name] += int(item.get("stargazers_count") or 0)

    return counts, stars


def safe_lane_key(raw: str) -> str:
    return raw.strip().lower().replace("handler_", "")


def get_chthonic_lanes() -> set[str]:
    script = REPO_ROOT / "scripts" / "chthonic.ps1"
    if not script.exists():
        return set()

    try:
        proc = subprocess.run(
            [
                "pwsh",
                "-NoLogo",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script),
                "status",
                "--json",
            ],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=40,
        )
    except Exception:
        return set()

    if proc.returncode != 0:
        return set()

    text = (proc.stdout or "").strip()
    if not text:
        return set()

    try:
        payload = json.loads(text)
    except Exception:
        return set()

    lanes: set[str] = set()
    for key in ("handler_python", "handler_ruby", "handler_rust", "handler_go", "handler_js"):
        if key in payload:
            lane = safe_lane_key(key)
            if lane == "js":
                lane = "javascript"
            lanes.add(lane)
    return lanes


def normalize_language(language: str) -> str:
    lowered = language.strip().lower()
    alias_map = {
        "c#": "c#",
        "csharp": "c#",
        "js": "javascript",
        "ts": "typescript",
        "objective-c++": "c++",
    }
    return alias_map.get(lowered, lowered)


def resolve_language_profile(language: str) -> dict:
    key = normalize_language(language)
    return LANGUAGE_MODEL.get(key, {"lane": key, "tools": [], "preferred_slug": None})


def resolve_eol_slug(language: str, product_index: dict[str, dict]) -> str | None:
    profile = resolve_language_profile(language)
    preferred = profile.get("preferred_slug")
    if preferred and preferred in product_index:
        return preferred

    key = normalize_language(language)
    if key in product_index:
        return key

    return None


def compute_eol_state(product_result: dict | None) -> tuple[str, str | None, str | None]:
    if not product_result:
        return ("unmapped", None, None)

    releases = product_result.get("releases", []) or []
    if not releases:
        return ("no-release-data", None, None)

    latest_name = None
    latest_cycle = None
    state = "unknown"

    for rel in releases:
        if rel.get("isMaintained"):
            latest_cycle = rel.get("name")
            latest_obj = rel.get("latest") or {}
            latest_name = latest_obj.get("name")
            state = "maintained"
            break

    if not latest_cycle:
        first = releases[0]
        latest_cycle = first.get("name")
        latest_obj = first.get("latest") or {}
        latest_name = latest_obj.get("name")
        if first.get("isEol"):
            state = "eol"
        elif first.get("isEoas"):
            state = "eoas"
        else:
            state = "tracked"

    return (state, latest_name, latest_cycle)


def build_trend_rows(
    counts: dict[str, int],
    stars: dict[str, int],
    top: int,
    chthonic_lanes: set[str],
    product_index: dict[str, dict],
) -> list[TrendRow]:
    ranked = []
    for language, repo_count in counts.items():
        star_total = stars.get(language, 0)
        score = repo_count * 1000 + math.log10(star_total + 1) * 100
        ranked.append((language, repo_count, star_total, score))

    ranked.sort(key=lambda x: (x[3], x[2], x[1], x[0]), reverse=True)

    rows: list[TrendRow] = []
    for language, repo_count, star_total, score in ranked[:top]:
        profile = resolve_language_profile(language)
        lane = profile["lane"]
        lane_present = lane in chthonic_lanes
        runtime_present = any(shutil.which(tool) for tool in profile.get("tools", []))

        slug = resolve_eol_slug(language, product_index)
        detail = fetch_product_details(slug) if slug else None
        eol_state, eol_latest, eol_cycle = compute_eol_state(detail)

        rows.append(
            TrendRow(
                language=language,
                repos=repo_count,
                stars=star_total,
                score=round(score, 2),
                lane=lane,
                lane_present=lane_present,
                runtime_present=runtime_present,
                eol_slug=slug,
                eol_latest=eol_latest,
                eol_cycle=eol_cycle,
                eol_state=eol_state,
            )
        )
    return rows


def render_markdown(report: dict) -> str:
    lines: list[str] = []
    lines.append("# Rustification Trend Tracker (Prototype)")
    lines.append("")
    lines.append(f"- Generated UTC: `{report['generated_at_utc']}`")
    lines.append(f"- Minute.Day.Month.Year: `{report['stamp_minute_day_month_year']}`")
    lines.append(f"- Window days: `{report['window_days']}`")
    lines.append(f"- GitHub pages: `{report['github_pages']}`")
    lines.append(f"- Top languages: `{report['top_n']}`")
    lines.append("")
    lines.append("## Coverage")
    lines.append(f"- Chthonic lanes present: `{', '.join(report['chthonic_lanes']) or '(none)'}`")
    lines.append(f"- Trending lanes covered: `{report['coverage']['covered']}`")
    lines.append(f"- Trending lanes missing: `{report['coverage']['missing']}`")
    lines.append("")
    lines.append("## Top Trends")
    lines.append("| Language | Repos | Stars | Lane | Have Lane | Runtime | EOL Slug | EOL State | Latest |")
    lines.append("|---|---:|---:|---|---|---|---|---|---|")
    for row in report["trends"]:
        lines.append(
            "| {language} | {repos} | {stars} | {lane} | {lane_present} | {runtime_present} | {eol_slug} | {eol_state} | {eol_latest} |".format(
                language=row["language"],
                repos=row["repos"],
                stars=row["stars"],
                lane=row["lane"],
                lane_present="yes" if row["lane_present"] else "no",
                runtime_present="yes" if row["runtime_present"] else "no",
                eol_slug=row["eol_slug"] or "unmapped",
                eol_state=row["eol_state"],
                eol_latest=row["eol_latest"] or "-",
            )
        )
    lines.append("")
    lines.append("## Rustification Finder Signals")
    for signal in report["rustification_finder"]:
        lines.append(f"- {signal}")
    lines.append("")
    lines.append("## Watchlist")
    lines.append("| Language | Repos | Stars | Lane | Have Lane | Runtime | EOL Slug | EOL State | Latest |")
    lines.append("|---|---:|---:|---|---|---|---|---|---|")
    for row in report.get("watchlist", []):
        lines.append(
            "| {language} | {repos} | {stars} | {lane} | {lane_present} | {runtime_present} | {eol_slug} | {eol_state} | {eol_latest} |".format(
                language=row["language"],
                repos=row["repos"],
                stars=row["stars"],
                lane=row["lane"],
                lane_present="yes" if row["lane_present"] else "no",
                runtime_present="yes" if row["runtime_present"] else "no",
                eol_slug=row["eol_slug"] or "unmapped",
                eol_state=row["eol_state"],
                eol_latest=row["eol_latest"] or "-",
            )
        )
    lines.append("")
    return "\n".join(lines)


def write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prototype trend tracker for rustification coverage.")
    parser.add_argument("--window-days", type=int, default=30, help="How many days to look back for GitHub trend query.")
    parser.add_argument("--pages", type=int, default=2, help="How many GitHub API pages to scan.")
    parser.add_argument("--per-page", type=int, default=100, help="Items per GitHub API page.")
    parser.add_argument("--top", type=int, default=12, help="Top languages to include.")
    parser.add_argument(
        "--watch",
        default="Elixir,PowerShell",
        help="Comma-separated languages to track even if not in top trends.",
    )
    parser.add_argument(
        "--target-mailbox",
        choices=sorted(MAILBOX_DIRS.keys()),
        default="codex",
        help="Mailbox location for RUSTIFICATION_TREND_LATEST outputs.",
    )
    parser.add_argument("--json", action="store_true", help="Also print compact JSON to stdout.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    now = utc_now()

    catalog = fetch_endoflife_catalog()
    product_index = build_product_index(catalog)
    chthonic_lanes = sorted(get_chthonic_lanes())
    counts, stars = fetch_github_trends(args.window_days, args.pages, args.per_page)
    trend_rows = build_trend_rows(
        counts=counts,
        stars=stars,
        top=args.top,
        chthonic_lanes=set(chthonic_lanes),
        product_index=product_index,
    )

    watch_rows: list[TrendRow] = []
    counts_lower = {k.lower(): v for k, v in counts.items()}
    stars_lower = {k.lower(): v for k, v in stars.items()}
    for raw_lang in [x.strip() for x in args.watch.split(",") if x.strip()]:
        lang = raw_lang
        profile = resolve_language_profile(lang)
        lane = profile["lane"]
        lane_present = lane in set(chthonic_lanes)
        runtime_present = any(shutil.which(tool) for tool in profile.get("tools", []))
        slug = resolve_eol_slug(lang, product_index)
        detail = fetch_product_details(slug) if slug else None
        eol_state, eol_latest, eol_cycle = compute_eol_state(detail)
        repo_count = counts_lower.get(lang.lower(), 0)
        star_total = stars_lower.get(lang.lower(), 0)
        score = repo_count * 1000 + math.log10(star_total + 1) * 100
        watch_rows.append(
            TrendRow(
                language=lang,
                repos=repo_count,
                stars=star_total,
                score=round(score, 2),
                lane=lane,
                lane_present=lane_present,
                runtime_present=runtime_present,
                eol_slug=slug,
                eol_latest=eol_latest,
                eol_cycle=eol_cycle,
                eol_state=eol_state,
            )
        )

    covered = sum(1 for r in trend_rows if r.lane_present)
    missing_rows = [r for r in trend_rows if not r.lane_present]

    finder_signals: list[str] = []
    if missing_rows:
        top_missing = ", ".join(sorted({r.language for r in missing_rows})[:8])
        finder_signals.append(f"Missing trend lanes detected: {top_missing}")
    else:
        finder_signals.append("All top trend lanes map to existing chthonic handlers.")

    elixir_trend = next((r for r in trend_rows if r.language.lower() == "elixir"), None)
    elixir_watch = next((r for r in watch_rows if r.language.lower() == "elixir"), None)
    if elixir_trend:
        if elixir_trend.lane_present:
            finder_signals.append("Elixir appears in trend set and has handler coverage.")
        else:
            finder_signals.append("Elixir appears in trend set but is not represented in active chthonic handlers.")
    elif elixir_watch:
        if elixir_watch.repos > 0:
            finder_signals.append("Elixir appears in sampled window (outside top trend cut) and is tracked via watchlist.")
        elif elixir_watch.lane_present:
            finder_signals.append("Elixir watchlist tracked with handler coverage; no sampled trend hits this window.")
        else:
            finder_signals.append("Elixir watchlist tracked; no sampled trend hits this window and no handler coverage yet.")
    else:
        finder_signals.append("Elixir is not present in current trend rows or watchlist.")

    watch_missing = [r.language for r in watch_rows if not r.lane_present]
    if watch_missing:
        finder_signals.append("Watchlist languages missing handler coverage: " + ", ".join(watch_missing))
    else:
        finder_signals.append("All watchlist languages currently have handler coverage.")

    report = {
        "generated_at_utc": now.isoformat(),
        "stamp_minute_day_month_year": stamp_minute_day_month_year(now),
        "window_days": args.window_days,
        "github_pages": args.pages,
        "github_per_page": args.per_page,
        "top_n": args.top,
        "chthonic_lanes": chthonic_lanes,
        "coverage": {
            "covered": covered,
            "missing": len(trend_rows) - covered,
        },
        "trends": [row.__dict__ for row in trend_rows],
        "rustification_finder": finder_signals,
        "watchlist": [row.__dict__ for row in watch_rows],
    }

    mailbox_dir = REPO_ROOT / MAILBOX_DIRS[args.target_mailbox]
    json_path = mailbox_dir / "RUSTIFICATION_TREND_LATEST.json"
    md_path = mailbox_dir / "RUSTIFICATION_TREND_LATEST.md"

    write_file(json_path, json.dumps(report, indent=2) + "\n")
    write_file(md_path, render_markdown(report))

    print(f"Wrote: {json_path.as_posix()}")
    print(f"Wrote: {md_path.as_posix()}")
    print(f"Stamp minute.day.month.year: {report['stamp_minute_day_month_year']}")
    print(f"Coverage: {covered}/{len(trend_rows)} lanes represented")

    if args.json:
        print(json.dumps(report, separators=(",", ":")))

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
