#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: github_activity_index.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
scripts/github_activity_index.py - GitHub activity lens (PRs/Issues/Branches).

Gitological Noise As Structured Data — classifies repo activity by actor type
(human, bot, copilot, dependabot) and state. Compounds with dependabot_index
and git_rot_index through shared envelope shape.

Calls gh API for pulls, issues, branches. Classifies each by:
  - actor_type: human | bot | copilot | dependabot | actions
  - state: open | closed | merged | stale
  - staleness: days since last update

Emits:
  manifest/github_activity_index.json  - machine-readable snapshot
  manifest/github_activity_index.md    - human-readable digest

Usage:
  uv run scripts/github_activity_index.py
  uv run scripts/github_activity_index.py --repo owner/name
  uv run scripts/github_activity_index.py --no-md

@SID: GITHUB_ACTIVITY_INDEX_V1
"""

from __future__ import annotations


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import argparse
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

BOT_PATTERNS = {
    "dependabot", "dependabot[bot]", "github-actions", "github-actions[bot]",
    "renovate", "renovate[bot]", "snyk-bot", "codecov[bot]", "mergify[bot]",
}

COPILOT_PATTERNS = {"copilot", "github-copilot"}


def gh_api(path: str) -> list[dict]:
    result = subprocess.run(
        ["gh", "api", path, "--paginate"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(f"gh api {path} failed: {result.stderr}")
    out = result.stdout.strip()
    if not out:
        return []
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        items: list[dict] = []
        for chunk in out.split("]["):
            chunk = chunk.strip()
            if not chunk.startswith("["):
                chunk = "[" + chunk
            if not chunk.endswith("]"):
                chunk = chunk + "]"
            try:
                items.extend(json.loads(chunk))
            except json.JSONDecodeError:
                continue
        return items


def classify_actor(user: dict | None) -> str:
    if user is None:
        return "unknown"
    login = (user.get("login") or "").lower()
    user_type = (user.get("type") or "").lower()

    if user_type == "bot" or login in BOT_PATTERNS or "[bot]" in login:
        if "dependabot" in login:
            return "dependabot"
        if "copilot" in login:
            return "copilot"
        return "bot"

    if login.startswith("copilot/") or "copilot" in login:
        return "copilot"

    return "human"


def days_since(iso_str: str | None) -> int | None:
    if not iso_str:
        return None
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - dt).days
    except (ValueError, TypeError):
        return None


def classify_branch_actor(name: str) -> str:
    lower = name.lower()
    if lower.startswith("copilot/"):
        return "copilot"
    if lower.startswith("dependabot/"):
        return "dependabot"
    if lower.startswith("renovate/"):
        return "bot"
    if lower.startswith("github-actions/"):
        return "bot"
    return "human"


def classify_pr(pr: dict) -> dict:
    user = pr.get("user")
    merged = pr.get("merged_at") is not None
    state = "merged" if merged else pr.get("state", "unknown")
    return {
        "number": pr.get("number"),
        "title": (pr.get("title") or "").strip(),
        "state": state,
        "actor": (user or {}).get("login"),
        "actor_type": classify_actor(user),
        "created_at": pr.get("created_at"),
        "updated_at": pr.get("updated_at"),
        "merged_at": pr.get("merged_at"),
        "closed_at": pr.get("closed_at"),
        "days_stale": days_since(pr.get("updated_at")),
        "labels": [l.get("name") for l in (pr.get("labels") or [])],
        "draft": pr.get("draft", False),
        "head_ref": (pr.get("head") or {}).get("ref"),
        "url": pr.get("html_url"),
    }


def classify_issue(issue: dict) -> dict | None:
    if issue.get("pull_request"):
        return None
    user = issue.get("user")
    return {
        "number": issue.get("number"),
        "title": (issue.get("title") or "").strip(),
        "state": issue.get("state", "unknown"),
        "actor": (user or {}).get("login"),
        "actor_type": classify_actor(user),
        "created_at": issue.get("created_at"),
        "updated_at": issue.get("updated_at"),
        "closed_at": issue.get("closed_at"),
        "days_stale": days_since(issue.get("updated_at")),
        "labels": [l.get("name") for l in (issue.get("labels") or [])],
        "url": issue.get("html_url"),
    }


def classify_branch(branch: dict, repo: str) -> dict:
    name = branch.get("name", "")
    return {
        "name": name,
        "sha": (branch.get("commit") or {}).get("sha"),
        "actor_type": classify_branch_actor(name),
        "protected": branch.get("protected", False),
        "is_default": name == "main",
    }


def build_index(repo: str) -> dict:
    print(f"[activity_index] fetching PRs for {repo} ...", file=sys.stderr)
    raw_prs = gh_api(f"repos/{repo}/pulls?state=all&per_page=100")
    prs = [classify_pr(p) for p in raw_prs]
    print(f"[activity_index] {len(prs)} PRs", file=sys.stderr)

    print(f"[activity_index] fetching issues for {repo} ...", file=sys.stderr)
    raw_issues = gh_api(f"repos/{repo}/issues?state=all&per_page=100")
    issues = [i for i in (classify_issue(x) for x in raw_issues) if i is not None]
    print(f"[activity_index] {len(issues)} issues (excl. PRs)", file=sys.stderr)

    print(f"[activity_index] fetching branches for {repo} ...", file=sys.stderr)
    raw_branches = gh_api(f"repos/{repo}/branches?per_page=100")
    branches = [classify_branch(b, repo) for b in raw_branches]
    print(f"[activity_index] {len(branches)} branches", file=sys.stderr)

    pr_by_actor_type = Counter(p["actor_type"] for p in prs)
    pr_by_state = Counter(p["state"] for p in prs)
    issue_by_actor_type = Counter(i["actor_type"] for i in issues)
    issue_by_state = Counter(i["state"] for i in issues)
    branch_by_actor_type = Counter(b["actor_type"] for b in branches)

    stale_prs = [p for p in prs if p["state"] == "open" and (p["days_stale"] or 0) > 30]
    stale_branches = [b for b in branches if not b["is_default"] and b["actor_type"] != "human"]

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo": repo,
        "summary": {
            "prs": {"total": len(prs), "by_state": dict(pr_by_state), "by_actor_type": dict(pr_by_actor_type)},
            "issues": {"total": len(issues), "by_state": dict(issue_by_state), "by_actor_type": dict(issue_by_actor_type)},
            "branches": {"total": len(branches), "by_actor_type": dict(branch_by_actor_type)},
        },
        "signals": {
            "stale_open_prs": len(stale_prs),
            "bot_branches": len(stale_branches),
            "dependabot_prs": sum(1 for p in prs if p["actor_type"] == "dependabot"),
            "copilot_branches": sum(1 for b in branches if b["actor_type"] == "copilot"),
        },
        "pulls": prs,
        "issues": issues,
        "branches": branches,
    }


def render_md(index: dict) -> str:
    s = index["summary"]
    sig = index["signals"]
    lines = [
        "# GitHub Activity Index",
        "",
        f"Generated: {index['generated_at']}",
        f"Repo: `{index['repo']}`",
        f"Source: `manifest/github_activity_index.json` (regenerate via `uv run scripts/github_activity_index.py`)",
        "",
        "## Summary",
        "",
        f"- PRs: {s['prs']['total']} | Issues: {s['issues']['total']} | Branches: {s['branches']['total']}",
        "",
        "### Signals",
        "",
        f"- Stale open PRs (>30d): **{sig['stale_open_prs']}**",
        f"- Bot/pilot branches (non-default): **{sig['bot_branches']}**",
        f"- Dependabot PRs (total): **{sig['dependabot_prs']}**",
        f"- Copilot branches: **{sig['copilot_branches']}**",
        "",
        "### PRs by state",
        "",
    ]
    for state, count in sorted(s["prs"]["by_state"].items()):
        lines.append(f"- `{state}`: {count}")

    lines += ["", "### PRs by actor type", ""]
    for atype, count in sorted(s["prs"]["by_actor_type"].items(), key=lambda x: -x[1]):
        lines.append(f"- `{atype}`: {count}")

    lines += ["", "### Issues by state", ""]
    for state, count in sorted(s["issues"]["by_state"].items()):
        lines.append(f"- `{state}`: {count}")

    lines += ["", "### Issues by actor type", ""]
    for atype, count in sorted(s["issues"]["by_actor_type"].items(), key=lambda x: -x[1]):
        lines.append(f"- `{atype}`: {count}")

    lines += ["", "### Branches by actor type", ""]
    for atype, count in sorted(s["branches"]["by_actor_type"].items(), key=lambda x: -x[1]):
        lines.append(f"- `{atype}`: {count}")

    # Detail: open PRs
    open_prs = [p for p in index["pulls"] if p["state"] == "open"]
    if open_prs:
        lines += ["", "## Open PRs", ""]
        for p in sorted(open_prs, key=lambda x: -(x["days_stale"] or 0)):
            stale_tag = f" ⚠️ {p['days_stale']}d stale" if (p["days_stale"] or 0) > 30 else ""
            lines.append(f"### [{p['actor_type'].upper()}] #{p['number']} — {p['title']}{stale_tag}")
            lines.append(f"- actor: `{p['actor']}` | created: {p['created_at'][:10]}")
            lines.append(f"- branch: `{p['head_ref']}`")
            lines.append(f"- view: {p['url']}")
            lines.append("")

    # Detail: bot/copilot branches
    bot_branches = [b for b in index["branches"] if b["actor_type"] != "human" and not b["is_default"]]
    if bot_branches:
        lines += ["## Bot/Pilot Branches", ""]
        for b in bot_branches:
            lines.append(f"- `{b['name']}` [{b['actor_type']}] — `{(b['sha'] or '')[:8]}`")
        lines.append("")

    # Detail: open issues
    open_issues = [i for i in index["issues"] if i["state"] == "open"]
    if open_issues:
        lines += ["## Open Issues", ""]
        for i in sorted(open_issues, key=lambda x: -(x["days_stale"] or 0)):
            stale_tag = f" ({i['days_stale']}d)" if i["days_stale"] else ""
            lines.append(f"- #{i['number']} — {i['title']}{stale_tag} [`{i['actor_type']}`]")
        lines.append("")

    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="GitHub activity lens")
    parser.add_argument("--repo", default=None, help="owner/repo (default: detect from gh)")
    parser.add_argument("--no-md", action="store_true", help="skip markdown digest")
    args = parser.parse_args()

    repo = args.repo
    if not repo:
        r = subprocess.run(
            ["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            print("Error: could not detect repo. Use --repo owner/name", file=sys.stderr)
            sys.exit(1)
        repo = r.stdout.strip()

    index = build_index(repo)

    out_dir = REPO_ROOT / "manifest"
    out_dir.mkdir(exist_ok=True)

    json_path = out_dir / "github_activity_index.json"
    json_path.write_text(json.dumps(index, indent=2, default=str), encoding="utf-8")
    print(f"[activity_index] wrote {json_path}", file=sys.stderr)

    if not args.no_md:
        md_path = out_dir / "github_activity_index.md"
        md_path.write_text(render_md(index), encoding="utf-8")
        print(f"[activity_index] wrote {md_path}", file=sys.stderr)

    total = index["summary"]
    sig = index["signals"]
    print(
        f"[activity_index] PRs={total['prs']['total']} Issues={total['issues']['total']} "
        f"Branches={total['branches']['total']}; "
        f"dependabot_prs={sig['dependabot_prs']} copilot_branches={sig['copilot_branches']} "
        f"stale_open={sig['stale_open_prs']}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
