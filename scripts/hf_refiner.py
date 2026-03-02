#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: hf_refiner.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Overnight Archaeology Refiner — HuggingFace Inference Edition

Reads L1 ore (from the local scavenge daemon) and sends it to a free
HuggingFace open-source model for PROMOTE/FLAG/SKIP classification.
Zero Copilot API cost. Uses HF_TOKEN from environment.

Designed to run as Loop 2 replacement: the local daemon produces L1 ore,
this script refines it into L2 digest using an open-source LLM.

@SID:           TOOL_HF_REFINER_V1
@Shabti:          Synthesis
@Purpose:       Overnight Archaeology Refiner — HuggingFace Inference Edition

Usage:
  uv run scripts/hf_refiner.py                          # auto-find latest L1 ore
  uv run scripts/hf_refiner.py --ore path/to/L1-ore.json
  uv run scripts/hf_refiner.py --model mistralai/Mistral-7B-Instruct-v0.3
  uv run scripts/hf_refiner.py --dry-run                # show what would be sent
"""

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLAUDE_MAILBOX = REPO_ROOT / "claude" / "mailbox"
ORE_BASE = REPO_ROOT / "dumpster-dive" / "intake" / "overnight-intelligence"

# Model choices (free tier compatible, structured output capable)
DEFAULT_MODEL = "meta-llama/Meta-Llama-3-8B-Instruct"
FALLBACK_MODELS = [
    "meta-llama/Llama-3.1-8B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.3",
    "Qwen/Qwen2.5-7B-Instruct",
]

HF_API_URL = "https://router.huggingface.co/v1/chat/completions"
MAX_RETRIES = 3
RETRY_DELAY = 15  # seconds (free tier cold starts)
QUERY_DELAY = 2   # seconds between domain calls
MAX_INPUT_CHARS = 4000  # per domain prompt
REQUEST_TIMEOUT = 180   # 3 min timeout per request (free tier can be slow)


def get_hf_token() -> str:
    """Get HuggingFace token from environment."""
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_HUB_TOKEN")
    if not token:
        print("ERROR: No HF_TOKEN or HUGGINGFACE_HUB_TOKEN in environment.")
        print("  Set it: $env:HF_TOKEN = 'hf_...'")
        sys.exit(1)
    return token


def find_latest_ore() -> Path | None:
    """Find the most recent L1-ore.json from the overnight scavenge."""
    if not ORE_BASE.exists():
        return None
    arch_dirs = sorted(
        [d for d in ORE_BASE.iterdir() if d.is_dir() and d.name.startswith("arch-")],
        reverse=True,
    )
    for d in arch_dirs:
        ore_file = d / "L1-ore.json"
        if ore_file.exists():
            return ore_file
    return None


def load_ore(ore_path: Path) -> list[dict]:
    """Load L1 ore entries."""
    with open(ore_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Handle both raw array and wrapped format
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "ore" in data:
        return data["ore"]
    return []


def load_prior_digest() -> dict | None:
    """Load the most recent archaeology digest as L0 newsfeed."""
    if not CLAUDE_MAILBOX.exists():
        return None
    digests = sorted(
        [f for f in CLAUDE_MAILBOX.iterdir()
         if f.name.startswith("ARCHAEOLOGY_DIGEST_") and f.name.endswith(".md")],
        reverse=True,
    )
    if not digests:
        return None

    raw = digests[0].read_text(encoding="utf-8")
    date_match = re.search(r"DIGEST_(\d{4}_\d{2}_\d{2})", digests[0].name)
    date = date_match.group(1).replace("_", "-") if date_match else "unknown"

    promotes = [
        line.strip() for line in raw.split("\n")
        if line.strip().startswith("- **") and "Promoted" not in line
        and "## ⬆" in raw[:raw.index(line)] if line in raw
    ]
    flags = [
        line.strip() for line in raw.split("\n")
        if line.strip().startswith("- **") and "## 🚩" in raw[:raw.index(line)] if line in raw
    ]

    return {"date": date, "promotes": promotes[:15], "flags": flags[:15], "path": str(digests[0])}


def query_hf(prompt: str, token: str, model: str) -> str:
    """Send a chat completion request to HuggingFace Inference API."""
    import urllib.request
    import urllib.error

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1500,
        "temperature": 0.3,
    }).encode("utf-8")

    for attempt in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(
                HF_API_URL, data=payload, headers=headers, method="POST"
            )
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                result = json.loads(resp.read().decode("utf-8"))

            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"].strip()
            if "error" in result:
                err_msg = result["error"]
                if isinstance(err_msg, dict):
                    err_msg = err_msg.get("message", str(err_msg))
                if "loading" in str(err_msg).lower():
                    print(f"    Model loading... waiting {RETRY_DELAY}s")
                    time.sleep(RETRY_DELAY)
                    continue
                raise RuntimeError(err_msg)
            return str(result)

        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            if e.code == 503:
                print(f"    Model loading (503)... waiting {RETRY_DELAY}s (attempt {attempt + 1})")
                time.sleep(RETRY_DELAY)
                continue
            if e.code == 429:
                print(f"    Rate limited (429)... waiting {RETRY_DELAY * 2}s")
                time.sleep(RETRY_DELAY * 2)
                continue
            raise RuntimeError(f"HF API error {e.code}: {body[:200]}")
        except TimeoutError:
            print(f"    Timeout ({REQUEST_TIMEOUT}s)... retrying (attempt {attempt + 1})")
            continue

    raise RuntimeError(f"Failed after {MAX_RETRIES} retries")


def build_domain_prompt(domain: str, entries: list[dict], prior: dict | None) -> str:
    """Build the PROMOTE/FLAG/SKIP prompt for one domain."""
    ore_lines = []
    for e in entries[:40]:
        signals = ", ".join(s.get("pattern", "") for s in e.get("nameSignals", []))
        snippet = e.get("headSnippet", "")[:100].replace("\n", " ↵ ")
        line = (
            f"- {e['path']} | {e.get('ext', '?')} | {e.get('lines', '?')}L | "
            f"age:{e.get('age_days', '?')}d | tier:{e.get('gold', {}).get('tier', '?')} | "
            f"{e.get('gold', {}).get('category', '?')}"
        )
        if signals:
            line += f" | signals:{signals}"
        if snippet:
            line += f' | head:"{snippet}"'
        ore_lines.append(line)

    ore_text = "\n".join(ore_lines)
    # Truncate if too long
    if len(ore_text) > MAX_INPUT_CHARS:
        ore_text = ore_text[:MAX_INPUT_CHARS] + "\n... (truncated)"

    prior_ctx = ""
    if prior:
        prior_ctx = (
            f"\n\nPRIOR DIGEST ({prior['date']}): "
            f"Skip files already promoted/flagged unless status changed.\n"
        )

    return f"""You are the overnight data archaeologist for a polyglot repository.

Below are files from the "{domain}/" domain with metadata and content head.
{prior_ctx}
YOUR TASK: For each file, judge:
1. PROMOTE: Worth surfacing — name what makes it gold (max 20 words)
2. FLAG: Stale, drifted, orphaned — name what's wrong (max 20 words)
3. SKIP: No action needed — do NOT list these

Format each line exactly as:
[PROMOTE] path — reason
[FLAG] path — reason

If nothing matters, say: DOMAIN CLEAN

FILES:
{ore_text}"""


def refine_ore(ore: list[dict], token: str, model: str, prior: dict | None, dry_run: bool = False):
    """Group ore by domain and send each to HF for classification."""
    # Group by top-level directory
    by_domain: dict[str, list[dict]] = {}
    for entry in ore:
        path = entry.get("path", "")
        parts = path.replace("\\", "/").split("/")
        domain = parts[0] if len(parts) > 1 else "."
        by_domain.setdefault(domain, []).append(entry)

    # Sort by file count descending
    domains = sorted(by_domain.items(), key=lambda x: len(x[1]), reverse=True)

    all_findings = []
    all_raw = []
    processed = 0

    for domain, entries in domains:
        if len(entries) < 3:
            continue

        prompt = build_domain_prompt(domain, entries, prior)

        if dry_run:
            print(f"  [DRY] {domain}: {len(entries)} files, prompt {len(prompt)} chars")
            continue

        print(f"  L2: Refining \"{domain}\" ({len(entries)} files, sending {min(len(entries), 40)})...")

        try:
            response = query_hf(prompt, token, model)
            all_raw.append(f"## {domain}\n{response}")

            # Parse PROMOTE/FLAG lines
            for line in response.split("\n"):
                line = line.strip()
                match = re.match(r"^\[?(PROMOTE|FLAG)\]?\s*(.+?)\s*[—–\-]\s*(.+)$", line)
                if match:
                    all_findings.append({
                        "domain": domain,
                        "verdict": match.group(1),
                        "path": match.group(2).strip(),
                        "reason": match.group(3).strip(),
                    })

            processed += 1
            time.sleep(QUERY_DELAY)

        except Exception as e:
            print(f"  ⚠ {domain} failed: {e}")
            all_raw.append(f"## {domain}\nERROR: {e}")

    return all_findings, all_raw, processed


def write_digest(findings: list[dict], raw_responses: list[str], model: str, prior: dict | None, domains_processed: int):
    """Write the L2 digest to claude/mailbox/."""
    CLAUDE_MAILBOX.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y_%m_%d")
    filename = f"ARCHAEOLOGY_DIGEST_{date_str}.md"

    promotes = [f for f in findings if f["verdict"] == "PROMOTE"]
    flags = [f for f in findings if f["verdict"] == "FLAG"]

    prior_line = f"{prior['date']} ({len(prior['promotes'])}P/{len(prior['flags'])}F)" if prior else "none (first run)"

    lines = [
        "---",
        "type: archaeology-digest",
        "from: hf-refiner-daemon",
        "to: claude",
        f"created: {now.isoformat()}",
        "priority: low",
        "scope: repo-wide",
        f"model: {model}",
        f"loop-level: L1 (fed by L0 from {prior['date']})" if prior else "loop-level: L1 (first run, no L0 prior)",
        "---",
        "",
        f"# ☥ Archaeology Digest — {now.strftime('%Y-%m-%d')}",
        "",
        f"**Generated by:** hf_refiner.py (HuggingFace open-source LLM)",
        f"**Model:** {model}",
        f"**Domains scanned:** {domains_processed}",
        f"**Promotions:** {len(promotes)} | **Flags:** {len(flags)}",
        f"**Prior digest (L0 newsfeed):** {prior_line}",
        f"**API cost:** $0 (free tier open-source model)",
        "",
        "---",
        "",
        "## ⬆️ Promoted to Level 2 Gold",
        "",
    ]

    if promotes:
        for p in promotes:
            lines.append(f"- **{p['path']}** — {p['reason']}")
    else:
        lines.append("_No promotions this run._")

    lines += [
        "",
        "## 🚩 Flagged for Attention",
        "",
    ]

    if flags:
        for f in flags:
            lines.append(f"- **{f['path']}** — {f['reason']}")
    else:
        lines.append("_No flags this run._")

    lines += ["", ""]

    digest_path = CLAUDE_MAILBOX / filename
    digest_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  ☥ Digest written: {digest_path}")
    return digest_path


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Refine L1 ore using HuggingFace Inference API")
    parser.add_argument("--ore", type=str, help="Path to L1-ore.json (auto-detects latest if omitted)")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help=f"HF model ID (default: {DEFAULT_MODEL})")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be sent without calling API")
    parser.add_argument("--no-digest", action="store_true", help="Don't write digest to mailbox")
    args = parser.parse_args()

    print("☥ HF Archaeology Refiner starting")
    print(f"  Model: {args.model}")

    # Find ore
    if args.ore:
        ore_path = Path(args.ore)
    else:
        ore_path = find_latest_ore()

    if not ore_path or not ore_path.exists():
        print("ERROR: No L1 ore found. Run the nightly scavenge first:")
        print("  .\\scripts\\run_archaeology.ps1 -SkipDaemon")
        sys.exit(1)

    print(f"  Ore: {ore_path}")

    # Load ore
    ore = load_ore(ore_path)
    print(f"  Ore entries: {len(ore)}")

    # Load prior digest
    prior = load_prior_digest()
    if prior:
        print(f"  L0 newsfeed: {prior['date']} ({len(prior['promotes'])}P/{len(prior['flags'])}F)")
    else:
        print("  L0 newsfeed: none (first run)")

    # Get token
    token = get_hf_token()

    # Warm-up probe — wake the model before batch processing
    if not args.dry_run:
        print("  Warming up model...", end="", flush=True)
        try:
            start = time.time()
            warmup = query_hf("Say OK.", token, args.model)
            elapsed = time.time() - start
            print(f" ready ({elapsed:.1f}s)")
        except Exception as e:
            print(f" failed: {e}")
            print("  Trying fallback models...")
            for fallback in FALLBACK_MODELS:
                try:
                    warmup = query_hf("Say OK.", token, fallback)
                    print(f"  ✅ Fallback model: {fallback}")
                    args.model = fallback
                    break
                except Exception:
                    continue
            else:
                print("  ❌ No models available. HF free tier may be overloaded.")
                sys.exit(1)

    if args.dry_run:
        print("\n── DRY RUN ──")

    # Refine
    print()
    findings, raw, processed = refine_ore(ore, token, args.model, prior, dry_run=args.dry_run)

    if args.dry_run:
        print(f"\nDry run complete. Would process {processed} domains.")
        return

    promotes = [f for f in findings if f["verdict"] == "PROMOTE"]
    flags = [f for f in findings if f["verdict"] == "FLAG"]
    print(f"\n  L2 complete: {processed} domains, {len(promotes)} promotions, {len(flags)} flags")

    # Write digest
    if not args.no_digest:
        write_digest(findings, raw, args.model, prior, processed)

    print(f"\n☥ Refinement complete.")


if __name__ == "__main__":
    main()
