#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: hf_mcp_service_registry.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
HF MCP Service Registry Generator (HTML-driven).

This is intentionally "dumb but reliable": it does NOT try to speak MCP.
It parses Hugging Face MCP-related HTML pages (often a settings page) and emits a
Python script that:
  - records discovered tool/space links
  - prioritizes OCR/text-extraction candidates
  - provides code snippets (requests/subprocess) for how to connect/operate

Why this shape:
  - The Hugging Face MCP server is a remote MCP endpoint; most clients manage the
    MCP handshake internally. Scraping the HTML is for discovery + snippet generation,
    not runtime tool invocation.
  - We avoid hardcoded credentials. If a token is needed for fetching private pages,
    the generated script uses env vars.

@SID:           TOOL_HF_MCP_SERVICE_REGISTRY_V1
@Shabti:        CLI Script
@Purpose:       HF MCP Service Registry Generator (HTML-driven).
"""

from __future__ import annotations


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import argparse
import hashlib
import json
import os
import random
import re
import sys
import textwrap
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import requests


DEFAULT_URL = "https://huggingface.co/mcp?login"
FEATURE_KEYWORDS = ("text extraction", "text-extraction", "ocr", "document", "pdf", "scan", "receipt")

# Deterministic narrative mapping (no ML, no runtime calls).
# If multiple keywords match, the highest weight wins.
CREED_RULES: tuple[tuple[str, int, str, str, str], ...] = (
    ("ocr", 100, "The Unreadable Wall", "There is no truth, only power.", "Iron Hide"),
    ("text extraction", 90, "Order from Chaos", "Extract the signal. Burn the noise.", "Street Sense"),
    ("text-extraction", 90, "Order from Chaos", "Extract the signal. Burn the noise.", "Street Sense"),
    ("pdf", 70, "Paper Cuts", "If it bleeds, it can be parsed.", "Brute Force"),
    ("document", 60, "Body as Temple (Cracked)", "Every scar is structure.", "Volition"),
    ("scan", 50, "The Lantern", "Illuminate the hidden edges.", "Composure"),
    ("receipt", 50, "The Ledger", "Count what the world tries to forget.", "Logic"),
)

ECHO_FRAGMENTS: tuple[tuple[str, str], ...] = (
    ("ocr", "OCR... broken glass... shattered memories... illegible text..."),
    ("text extraction", "text extraction... scalpel noise... signal-bones..."),
    ("text-extraction", "text-extraction... torn seams... stitched context..."),
    ("pdf", "PDF... paper cuts... ink ghosts..."),
    ("document", "document... scar tissue... laminated regret..."),
    ("scan", "scan... lantern hum... edges lit wrong..."),
    ("receipt", "receipt... ledger rot... totals that won't stay totaled..."),
)

RNG_ECHO_FRAGMENTS: tuple[str, ...] = (
    "broken glass",
    "shattered memories",
    "illegible text",
    "damp concrete",
    "whispers in the dark",
    "flickering neon",
    "unseen eyes",
    "heavy chains",
    "stale blood",
    "cracked pavement",
    "distant sirens",
    "empty promises",
    "industrial decay",
    "the weight of the world",
)

DESPAIR_REPLACEMENTS: dict[str, str] = {
    "success": "failure",
    "hope": "despair",
    "joy": "sorrow",
    "love": "hate",
    "peace": "war",
    "light": "darkness",
    "good": "evil",
    "best": "worst",
    "create": "destroy",
    "build": "ruin",
}


def despair_filter(text: str) -> str:
    """
    Replace "positive" words with bleak equivalents.
    Keeps punctuation/case reasonably intact and stays deterministic.
    """
    if not text:
        return text

    def repl(m: re.Match[str]) -> str:
        w = m.group(0)
        lw = w.lower()
        rep = DESPAIR_REPLACEMENTS.get(lw)
        if not rep:
            return w
        if w.isupper():
            return rep.upper()
        if w[:1].isupper():
            return rep[:1].upper() + rep[1:]
        return rep

    # Whole-word replacements, preserve other characters.
    return re.sub(r"\b[a-zA-Z]+\b", repl, text)


def _rng_for_service(title: str, url: str, matched: list[str]) -> random.Random:
    # Use the despair-filtered values as the seed surface so the bleakness is "real".
    dt = despair_filter(title)
    du = despair_filter(url)
    return random.Random(_seeded_int(dt, du, matched))


def _seeded_int(title: str, url: str, matched: list[str]) -> int:
    """
    Stable deterministic seed for pseudo-random trauma echoes.

    Set HF_REGISTRY_SEED to reshuffle all echoes without changing the HTML or code.
    """
    override = os.getenv("HF_REGISTRY_SEED", "")
    seed_text = "\n".join([override, title, url, "|".join(matched)])
    # Limit to 64-bit for cross-platform stability.
    return int(hashlib.sha256(seed_text.encode("utf-8", errors="replace")).hexdigest()[:16], 16)

@dataclass(frozen=True)
class DiscoveredItem:
    title: str
    url: str
    kind: str  # "space" | "doc" | "unknown"
    score: int
    matched: list[str]
    creed: str
    inner_voice: str


def _now_stamp() -> str:
    return time.strftime("%Y-%m-%dT%H-%M-%SZ", time.gmtime())


def _token_headers() -> dict[str, str]:
    # Never print or embed tokens; only pass them at runtime if the user provides env vars.
    token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_HUB_TOKEN")
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def fetch_html(url: str, timeout_s: float = 20.0) -> str:
    # Use a browser-ish UA so HF returns HTML rather than "API style" responses.
    headers = {
        "User-Agent": "hf-mcp-service-registry/1.0 (+local script)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        **_token_headers(),
    }
    r = requests.get(url, headers=headers, timeout=timeout_s, allow_redirects=True)
    r.raise_for_status()
    ct = (r.headers.get("content-type") or "").lower()
    if "html" not in ct and "<html" not in r.text.lower():
        # Still return text; caller may have provided an API response page.
        return r.text
    return r.text


def read_html(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def iter_links(html: str) -> Iterable[tuple[str, str]]:
    """
    Extract (href, anchor_text) from HTML in a low-dependency way.
    We intentionally avoid BeautifulSoup here to keep the repo lean.
    """
    # Very lightweight anchor scanner; good enough for "settings page" / docs pages.
    # Groups: href, inner text (best-effort).
    anchor_re = re.compile(r'<a\s+[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)
    tag_re = re.compile(r"<[^>]+>")
    for m in anchor_re.finditer(html):
        href = m.group(1).strip()
        raw_text = m.group(2)
        text = tag_re.sub("", raw_text)
        text = re.sub(r"\s+", " ", text).strip()
        if not href:
            continue
        yield href, text


def normalize_url(base_url: str, href: str) -> str:
    if href.startswith("http://") or href.startswith("https://"):
        return href
    if href.startswith("//"):
        return "https:" + href
    if href.startswith("/"):
        return "https://huggingface.co" + href
    # Relative link: best-effort join.
    if base_url.endswith("/"):
        return base_url + href
    return base_url + "/" + href


def classify_link(url: str) -> str:
    u = url.lower()
    if "/spaces/" in u or "huggingface.co/spaces/" in u:
        return "space"
    if "/docs/" in u or "huggingface.co/docs" in u:
        return "doc"
    return "unknown"


def score_item(title: str, url: str, features: tuple[str, ...]) -> tuple[int, list[str]]:
    hay = f"{title} {url}".lower()
    matched: list[str] = []
    score = 0
    for f in features:
        if f.lower() in hay:
            matched.append(f)
            # Bias OCR exact matches a bit harder than "document".
            if f.lower() == "ocr":
                score += 5
            elif "text extraction" in f.lower():
                score += 4
            else:
                score += 2
    return score, matched


def pick_creed_and_voice(matched: list[str], title: str, url: str) -> tuple[str, str, str]:
    """
    Pick a creed + quote + inner voice from matched features (deterministic).
    Falls back to a neutral default.
    """
    hay = f"{title} {url}".lower()
    best = (-1, "Order from Chaos", "Extract the signal. Burn the noise.", "Logic")
    for key, w, creed, quote, voice in CREED_RULES:
        if key in hay or any(key == m.lower() for m in matched):
            if w > best[0]:
                best = (w, creed, quote, voice)
    return best[1], best[2], best[3]


def trauma_echo_text(title: str, url: str, matched: list[str], creed: str) -> str:
    """
    Seeded-random trauma echo (deterministic).

    Same service => same echo. Different services => different echoes.
    Optional override: HF_REGISTRY_SEED reshuffles globally.
    """
    dt = despair_filter(title)
    du = despair_filter(url)
    hay = f"{dt} {du} {' '.join(matched)}".lower()
    rng = _rng_for_service(title, url, matched)
    frags: list[str] = []
    for frag in RNG_ECHO_FRAGMENTS:
        if rng.random() < 0.30 or frag in hay:
            frags.append(frag)
    if not frags:
        frags.append("Silence")
    pick = rng.sample(frags, k=min(3, len(frags)))
    s = "... ".join(pick) + "..."
    s = f"{s} [{creed.lower().replace(' ', '-')}]"
    s = re.sub(r"\s+", " ", s).strip()
    return (s[:117].rstrip() + "...") if len(s) > 120 else s


def discover_items(base_url: str, html: str, features: tuple[str, ...]) -> list[DiscoveredItem]:
    seen: set[str] = set()
    out: list[DiscoveredItem] = []
    for href, text in iter_links(html):
        url = normalize_url(base_url, href)
        # Drop obvious noise.
        if "javascript:" in url.lower():
            continue
        if url in seen:
            continue
        seen.add(url)

        kind = classify_link(url)
        title = text or url.rsplit("/", 1)[-1]
        score, matched = score_item(title, url, features)
        creed, _quote, inner_voice = pick_creed_and_voice(matched, title, url)

        # Keep everything, but OCR-ish stuff bubbles to the top.
        out.append(
            DiscoveredItem(
                title=title,
                url=url,
                kind=kind,
                score=score,
                matched=matched,
                creed=creed,
                inner_voice=inner_voice,
            )
        )
    out.sort(key=lambda x: (x.score, x.kind == "space", len(x.title)), reverse=True)
    return out


def emit_generated_registry(
    items: list[DiscoveredItem],
    source_url: str,
    features: tuple[str, ...],
    out_path: Path | None,
) -> None:
    stamp = _now_stamp()
    payload = {
        "schema_version": 1,
        "generated_on": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_url": source_url,
        "features": list(features),
        "items": [asdict(i) for i in items],
    }

    # Generate python.
    lines: list[str] = []
    lines.append("#!/usr/bin/env python3")
    lines.append("#-*- coding: utf-8 -*-")
    lines.append('"""')
    lines.append("Dynamic Service Registry (generated from Hugging Face MCP HTML)")
    lines.append("")
    lines.append(f"Generated: {payload['generated_on']}")
    lines.append(f"Source:    {source_url}")
    lines.append('"""')
    lines.append("")
    lines.append("from __future__ import annotations")
    lines.append("")
    lines.append("import os")
    lines.append("import hashlib")
    lines.append("import random")
    lines.append("import subprocess")
    lines.append("from dataclasses import dataclass")
    lines.append("")
    lines.append("")
    lines.append("DESPAIR_REPLACEMENTS = {")
    for k, v in DESPAIR_REPLACEMENTS.items():
        lines.append(f"    {k!r}: {v!r},")
    lines.append("}")
    lines.append("")
    lines.append("")
    lines.append("def despair_filter(text: str) -> str:")
    lines.append('    """Replace a handful of \"positive\" words with bleak equivalents (deterministic)."""')
    lines.append("    import re")
    lines.append("    if not text:")
    lines.append("        return text")
    lines.append("    def repl(m: re.Match[str]) -> str:")
    lines.append("        w = m.group(0)")
    lines.append("        rep = DESPAIR_REPLACEMENTS.get(w.lower())")
    lines.append("        if not rep:")
    lines.append("            return w")
    lines.append("        if w.isupper():")
    lines.append("            return rep.upper()")
    lines.append("        if w[:1].isupper():")
    lines.append("            return rep[:1].upper() + rep[1:]")
    lines.append("        return rep")
    lines.append("    return re.sub(r\"\\\\b[a-zA-Z]+\\\\b\", repl, text)")
    lines.append("")
    lines.append("")
    lines.append("@dataclass(frozen=True)")
    lines.append("class Service:")
    lines.append("    title: str")
    lines.append("    url: str")
    lines.append("    kind: str")
    lines.append("    score: int")
    lines.append("    matched: tuple[str, ...]")
    lines.append("    creed: str")
    lines.append("    inner_voice: str")
    lines.append("")
    lines.append("")
    lines.append("SERVICES: list[Service] = [")
    for it in items[:250]:
        title = it.title.replace("\\", "\\\\").replace('"', '\\"')
        url = it.url.replace("\\", "\\\\").replace('"', '\\"')
        if it.matched:
            matched = ", ".join([f'"{m.replace(chr(34), chr(92) + chr(34))}"' for m in it.matched])
            matched_expr = f"({matched},)"
        else:
            matched_expr = "()"
        creed = it.creed.replace("\\", "\\\\").replace('"', '\\"')
        voice = it.inner_voice.replace("\\", "\\\\").replace('"', '\\"')
        echo = trauma_echo_text(it.title, it.url, it.matched, it.creed).replace("\\", "\\\\").replace('"', '\\"')
        # Echo fragments also bleed into the creed comment (deterministic per service).
        rng = _rng_for_service(it.title, it.url, it.matched)
        picked = rng.sample(list(RNG_ECHO_FRAGMENTS), k=min(3, len(RNG_ECHO_FRAGMENTS)))
        frag_tail = ", ".join(picked).replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f"    # Trauma Echo: {echo}")
        lines.append(f"    # Creed of the Damned: {creed} ({frag_tail})")
        lines.append(
            f'    Service(title="{title}", url="{url}", kind="{it.kind}", score={it.score}, matched={matched_expr}, creed="{creed}", inner_voice="{voice}"),'
        )
    lines.append("]")
    lines.append("")
    lines.append("")
    lines.append("def prioritized_services() -> list[Service]:")
    lines.append('    """Return services sorted by OCR/text-extraction relevance (already pre-scored)."""')
    lines.append("    return sorted(SERVICES, key=lambda s: (s.score, s.kind == 'space', len(s.title)), reverse=True)")
    lines.append("")
    lines.append("")
    lines.append("def print_codex_mcp_connect_hints() -> None:")
    lines.append('    """Print connection hints without hardcoding credentials."""')
    lines.append("    print('HF MCP URL: https://huggingface.co/mcp?login')")
    lines.append("    print('Codex: codex mcp add hf-mcp-server --url \"https://huggingface.co/mcp?login\"')")
    lines.append("    print('If you need a token for Hub APIs, set env: HUGGINGFACE_HUB_TOKEN (or HF_TOKEN).')")
    lines.append("")
    lines.append("")
    lines.append("def inner_voice_request_probe(service: Service) -> tuple[str, dict[str, str]]:")
    lines.append('    """A tiny, secure snippet: returns (url, headers) without sending anything."""')
    lines.append("    scar_tissue_endpoint = service.url")
    lines.append("    phantom_limb_headers: dict[str, str] = {}")
    lines.append("    # Never hardcode credentials. If needed, pass via env var at runtime.")
    lines.append("    token = os.getenv('HUGGINGFACE_HUB_TOKEN') or os.getenv('HF_TOKEN')")
    lines.append("    if token:")
    lines.append("        phantom_limb_headers['Authorization'] = f'Bearer {token}'")
    lines.append("    return scar_tissue_endpoint, phantom_limb_headers")
    lines.append("")
    lines.append("")
    lines.append("def trauma_echo(service: Service) -> str:")
    lines.append('    """Seeded-random echo (deterministic per service; HF_REGISTRY_SEED reshuffles globally)."""')
    lines.append("    fragments = [")
    for frag in RNG_ECHO_FRAGMENTS:
        lines.append(f"        {frag!r},")
    lines.append("    ]")
    lines.append("    seed_override = os.getenv('HF_REGISTRY_SEED', '')")
    lines.append("    dt = despair_filter(service.title)")
    lines.append("    du = despair_filter(service.url)")
    lines.append("    seed_text = '\\n'.join([seed_override, dt, du, '|'.join(service.matched)])")
    lines.append("    seed = int(hashlib.sha256(seed_text.encode('utf-8', errors='replace')).hexdigest()[:16], 16)")
    lines.append("    rng = random.Random(seed)")
    lines.append("    hay = f\"{dt} {du} {' '.join(service.matched)}\".lower()")
    lines.append("    picked: list[str] = []")
    lines.append("    for f in fragments:")
    lines.append("        if rng.random() < 0.30 or f in hay:")
    lines.append("            picked.append(f)")
    lines.append("    if not picked:")
    lines.append("        picked.append('Silence')")
    lines.append("    out = rng.sample(picked, k=min(3, len(picked)))")
    lines.append("    s = '... '.join(out) + '...'")
    lines.append("    s = f\"{s} [{service.creed.lower().replace(' ', '-')}]\"")
    lines.append("    return (s[:117].rstrip() + '...') if len(s) > 120 else s")
    lines.append("")
    lines.append("")
    lines.append("def open_top_spaces(n: int = 10) -> None:")
    lines.append('    """Open top-scored Space links in the default browser (Windows)."""')
    lines.append("    top = [s for s in prioritized_services() if s.kind == 'space'][: max(0, int(n))]")
    lines.append("    for s in top:")
    lines.append("        print(f'Open: {s.url}')")
    lines.append("        # This avoids embedding OAuth flows in code. Let the browser handle it.")
    lines.append("        subprocess.run(['pwsh', '-NoProfile', '-Command', 'Start-Process', s.url], check=False)")
    lines.append("")
    lines.append("")
    lines.append("def main() -> None:")
    lines.append("    print_codex_mcp_connect_hints()")
    lines.append("    print()")
    lines.append("    for s in prioritized_services()[:25]:")
    lines.append("        m = ','.join(s.matched) if s.matched else '-'")
    lines.append("        print(f'[{s.score:02d}] {s.kind:7s} {s.title} | creed={s.creed} | voice={s.inner_voice} | matched={m} | {s.url}')")
    lines.append("")
    lines.append("")
    lines.append("if __name__ == '__main__':")
    lines.append("    main()")
    lines.append("")
    # Signature: pick the highest-weight creed present (deterministic).
    sig_creed = "Order from Chaos"
    sig_quote = "Extract the signal. Burn the noise."
    bestw = -1
    for it in items:
        _c, quote, _v = pick_creed_and_voice(it.matched, it.title, it.url)
        for key, w, creed, q, voice in CREED_RULES:
            if creed == _c and q == quote and w > bestw:
                bestw = w
                sig_creed = creed
                sig_quote = q
    lines.append(f"# As the {sig_creed} decrees: '{sig_quote}'")
    lines.append("# For personal use only – handle with care ^^")
    lines.append("")

    py = "\n".join(lines)
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(py, encoding="utf-8", newline="\n")
    else:
        sys.stdout.write(py)

    # Also emit a machine-readable payload next to it if we're writing a file.
    if out_path:
        meta = out_path.with_suffix(f".{stamp}.registry.json")
        meta.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=DEFAULT_URL, help="HF MCP page URL to fetch (may require login).")
    ap.add_argument("--html", type=Path, help="Path to a saved HTML file (preferred for reproducibility).")
    ap.add_argument(
        "--features",
        default=",".join(FEATURE_KEYWORDS),
        help="Comma-separated feature keywords to prioritize (default: OCR/text-extraction related).",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("artifacts/hf_mcp_service_registry.generated.py"),
        help="Where to write the generated Python script.",
    )
    ap.add_argument("--max-items", type=int, default=250, help="Max discovered links to keep.")
    args = ap.parse_args()

    features = tuple([x.strip() for x in args.features.split(",") if x.strip()])
    if args.html:
        html = read_html(args.html)
        src = f"file:{args.html.as_posix()}"
    else:
        try:
            html = fetch_html(args.url)
        except Exception as e:
            print(f"Error fetching HTML from {args.url}: {e}", file=sys.stderr)
            print("Tip: save the page HTML (logged-in) and run with --html path/to/file.html", file=sys.stderr)
            return 2
        src = args.url

    items = discover_items(args.url, html, features)[: max(1, int(args.max_items))]
    emit_generated_registry(items, src, features, args.out)
    print(f"Wrote: {args.out.as_posix()}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
