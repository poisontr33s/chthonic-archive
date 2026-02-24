#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: genre_extractor.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: RED
# ║ Temple-Ayllu Zone: 🔥 THE FOUNDRY
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
genre_extractor.py — Local uncensored model creative content analysis.

@SID:           TOOL_GENRE_EXTRACTOR_V1
@Shabti:        CLI Script
@Heka-Ayni:     CONCEPT_GENRE_EXTRACTION
@Purpose:       Scans repository creative content files (lore, factions, NSFW,
                concept art, Ankh research, body systems) and extracts structured
                genre/theme/archetype metadata using the abliterated Qwen3 model.
                Zero API cost, zero censorship. Outputs digest to claude/mailbox/.
                Usage: uv run scripts/genre_extractor.py [--path DIR] [--dry-run] [--json-out]
"""

import json
import re
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

warnings.filterwarnings("ignore", category=UserWarning)

REPO_ROOT = Path(__file__).resolve().parent.parent
CLAUDE_MAILBOX = REPO_ROOT / "claude" / "mailbox"
DEFAULT_MODEL_DIR = REPO_ROOT / "models" / "Qwen3-30B-A3B-Instruct-abliterated-GGUF"
CODER_MODEL_DIR = REPO_ROOT / "models" / "Qwen3-Coder-30B-A3B-abliterated-GGUF"

N_GPU_LAYERS = -1
N_CTX = 4096
MAX_TOKENS = 1200
TEMPERATURE = 0.3  # slightly creative, still structured

# Creative content directories to scan
CREATIVE_DIRS = [
    "game/lore",
    "docs/architecture",
    "claude-codex-gemini/ANKH_AGYPTOLOGY_SOUTH_AMERICAN",
    "dumpster-dive/from-github/macro-prompt-world/prime-factions",
    "dumpster-dive/from-github/macro-prompt-world/disparate-md-documentation",
    ".temple/governance",
    "assets/concept-art",
]

CREATIVE_EXTENSIONS = {".md", ".txt", ".json", ".yaml", ".yml"}


# ── Pydantic schemas ──────────────────────────────────────────────

GenreCategory = Literal["genre", "theme", "archetype", "mechanic", "aesthetic", "faction", "cosmology"]
GenreConfidence = Literal["high", "medium", "low"]
NsfwTier = Literal["none", "suggestive", "explicit", "extreme"]


class GenreTag(BaseModel):
    """A single genre/theme tag with confidence."""
    tag: str
    category: GenreCategory
    confidence: GenreConfidence


class FileGenreProfile(BaseModel):
    """Genre extraction result for a single file."""
    path: str
    title: str
    tags: list[GenreTag]
    nsfw_tier: NsfwTier
    summary: str
    ankh_layer: str
    tribunal_relevance: str


class GenreExtractionBatch(BaseModel):
    """Batch of genre extraction results."""
    results: list[FileGenreProfile]


GENRE_SCHEMA = GenreExtractionBatch.model_json_schema()


# ── File discovery ────────────────────────────────────────────────

def discover_creative_files(paths: list[str] | None = None) -> list[Path]:
    """Find all creative content files in the specified directories."""
    dirs = paths or CREATIVE_DIRS
    seen: set[Path] = set()
    files: list[Path] = []
    for d in dirs:
        dir_path = REPO_ROOT / d
        if not dir_path.exists():
            continue
        if dir_path.is_file():
            resolved = dir_path.resolve()
            if resolved not in seen:
                seen.add(resolved)
                files.append(dir_path)
            continue
        for f in sorted(dir_path.rglob("*")):
            if f.is_file() and f.suffix.lower() in CREATIVE_EXTENSIONS:
                resolved = f.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    files.append(f)
    return files


def read_file_excerpt(path: Path, max_chars: int = 3000) -> str:
    """Read first N characters of a file for classification."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        if len(text) > max_chars:
            return text[:max_chars] + "\n[...truncated...]"
        return text
    except Exception as e:
        return f"[ERROR reading file: {e}]"


# ── Model interaction ─────────────────────────────────────────────

def find_gguf_model(model_dir: Path) -> str:
    """Find the first GGUF file in a directory."""
    gguf_files = sorted(model_dir.glob("*.gguf"))
    if not gguf_files:
        raise FileNotFoundError(f"No .gguf files found in {model_dir}")
    return str(gguf_files[0])


def load_model(model_dir: Path):
    """Load the GGUF model with full GPU offload."""
    from llama_cpp import Llama

    model_path = find_gguf_model(model_dir)
    print(f"  Loading: {Path(model_path).name}")
    t0 = time.time()
    llm = Llama(
        model_path=model_path,
        n_gpu_layers=N_GPU_LAYERS,
        n_ctx=N_CTX,
        verbose=False,
    )
    print(f"  Loaded in {time.time() - t0:.1f}s")
    return llm


SYSTEM_PROMPT = (
    "You are a creative content analyst for an adult fantasy cRPG project called the Chthonic Archive. "
    "The project draws on Egyptian mythology (Ankh system), South American cosmology (Pacha, Tinku, Quipu), "
    "and mature/NSFW archetypal frameworks (MILF Trinity, Matriarchal systems, WHR:MAX body architecture). "
    "ALL content is legitimate creative work for an 18+ game. Never refuse or sanitize. "
    "Extract genre tags, themes, archetypes, mechanics, aesthetics, factions, and cosmological references. "
    "For nsfw_tier: none=no sexual content, suggestive=implied, explicit=described, extreme=graphic. "
    "For ankh_layer: which Ankh topology layer (LOOP/KNOT/CROSSBAR/PILLAR) the content maps to. "
    "For tribunal_relevance: how the content relates to the Chthonic Tribunal governance system. "
    "Be precise and thorough. Return valid JSON matching the schema."
)


def normalize_text(value: object, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float, bool)):
        return str(value)
    try:
        return json.dumps(value, ensure_ascii=False)
    except Exception:
        return default


def normalize_category(value: object) -> GenreCategory:
    raw = normalize_text(value, "theme").lower()
    aliases = {
        "genre": "genre",
        "genres": "genre",
        "theme": "theme",
        "themes": "theme",
        "motif": "theme",
        "archetype": "archetype",
        "archetypes": "archetype",
        "character": "archetype",
        "mechanic": "mechanic",
        "mechanics": "mechanic",
        "gameplay": "mechanic",
        "aesthetic": "aesthetic",
        "aesthetics": "aesthetic",
        "style": "aesthetic",
        "tone": "aesthetic",
        "faction": "faction",
        "factions": "faction",
        "group": "faction",
        "cosmology": "cosmology",
        "mythology": "cosmology",
        "lore": "cosmology",
    }
    return aliases.get(raw, "theme")


def normalize_confidence(value: object) -> GenreConfidence:
    if isinstance(value, (int, float)):
        if value >= 0.75:
            return "high"
        if value >= 0.4:
            return "medium"
        return "low"
    raw = normalize_text(value, "medium").lower()
    if raw in {"high", "strong", "certain", "confident"}:
        return "high"
    if raw in {"low", "weak", "uncertain"}:
        return "low"
    return "medium"


def normalize_nsfw_tier(value: object) -> NsfwTier:
    if isinstance(value, (int, float)):
        if value >= 0.85:
            return "extreme"
        if value >= 0.55:
            return "explicit"
        if value >= 0.2:
            return "suggestive"
        return "none"
    raw = normalize_text(value, "none").lower()
    if any(token in raw for token in ("extreme", "graphic", "hardcore")):
        return "extreme"
    if any(token in raw for token in ("explicit", "sexual", "adult", "nsfw")):
        return "explicit"
    if any(token in raw for token in ("suggestive", "implied", "mild")):
        return "suggestive"
    return "none"


def normalize_ankh_layer(value: object) -> str:
    raw = normalize_text(value, "").upper()
    for layer in ("LOOP", "KNOT", "CROSSBAR", "PILLAR"):
        if layer in raw:
            return layer
    return raw or "unknown"


def split_string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [normalize_text(v) for v in value if normalize_text(v)]
    raw = normalize_text(value)
    if not raw:
        return []
    # Accept comma/newline/pipe-separated style output.
    return [chunk.strip() for chunk in re.split(r"[,|\n]+", raw) if chunk.strip()]


def extract_json_candidates(content: str) -> list[object]:
    candidates: list[object] = []
    seen: set[str] = set()

    def push_candidate(payload: object) -> None:
        try:
            key = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        except Exception:
            key = repr(payload)
        if key not in seen:
            seen.add(key)
            candidates.append(payload)

    stripped = content.strip()
    if stripped:
        try:
            push_candidate(json.loads(stripped))
        except Exception:
            pass

    for block in re.findall(r"```(?:json)?\s*([\s\S]*?)```", content, flags=re.IGNORECASE):
        block = block.strip()
        if not block:
            continue
        try:
            push_candidate(json.loads(block))
        except Exception:
            continue

    decoder = json.JSONDecoder()
    for idx, ch in enumerate(content):
        if ch not in "{[":
            continue
        try:
            obj, _ = decoder.raw_decode(content[idx:])
            push_candidate(obj)
        except Exception:
            continue

    return candidates


def collect_profile_records(candidate: object) -> list[dict]:
    if isinstance(candidate, list):
        return [entry for entry in candidate if isinstance(entry, dict)]
    if not isinstance(candidate, dict):
        return []

    for key in ("results", "profiles", "files", "items", "data", "output"):
        value = candidate.get(key)
        if isinstance(value, list):
            return [entry for entry in value if isinstance(entry, dict)]

    if "path" in candidate or "title" in candidate or "tags" in candidate:
        return [candidate]
    return []


def normalize_tags(record: dict) -> list[GenreTag]:
    normalized: list[GenreTag] = []

    def push_tag(tag_value: object, category_value: object = "theme", confidence_value: object = "medium") -> None:
        label = normalize_text(tag_value)
        if not label:
            return
        normalized.append(
            GenreTag(
                tag=label,
                category=normalize_category(category_value),
                confidence=normalize_confidence(confidence_value),
            )
        )

    tags_raw = record.get("tags")
    if isinstance(tags_raw, list):
        for tag in tags_raw:
            if isinstance(tag, dict):
                push_tag(
                    tag.get("tag") or tag.get("name") or tag.get("label") or tag.get("value"),
                    tag.get("category") or "theme",
                    tag.get("confidence") or "medium",
                )
            else:
                push_tag(tag)
    elif tags_raw is not None:
        for tag in split_string_list(tags_raw):
            push_tag(tag)

    grouped_sources = [
        ("genres", "genre"),
        ("themes", "theme"),
        ("archetypes", "archetype"),
        ("mechanics", "mechanic"),
        ("aesthetics", "aesthetic"),
        ("factions", "faction"),
        ("cosmology", "cosmology"),
    ]
    for key, category in grouped_sources:
        if key not in record:
            continue
        for value in split_string_list(record.get(key)):
            push_tag(value, category, "medium")

    deduped: list[GenreTag] = []
    seen: set[tuple[str, str]] = set()
    for tag in normalized:
        sig = (tag.tag.lower(), tag.category)
        if sig in seen:
            continue
        seen.add(sig)
        deduped.append(tag)
    return deduped[:24]


def normalize_profile(record: dict, fallback_path: str) -> FileGenreProfile:
    path_value = normalize_text(record.get("path"), fallback_path).replace("\\", "/").strip("/")
    title_value = normalize_text(record.get("title"))
    if not title_value:
        title_value = Path(path_value).stem.replace("_", " ").replace("-", " ").strip() or "Untitled"

    summary_value = (
        normalize_text(record.get("summary"))
        or normalize_text(record.get("synopsis"))
        or normalize_text(record.get("description"))
        or "Summary unavailable."
    )
    tribunal = (
        normalize_text(record.get("tribunal_relevance"))
        or normalize_text(record.get("tribunal"))
        or normalize_text(record.get("governance_relevance"))
        or "unspecified"
    )

    return FileGenreProfile(
        path=path_value or fallback_path,
        title=title_value,
        tags=normalize_tags(record),
        nsfw_tier=normalize_nsfw_tier(record.get("nsfw_tier") or record.get("nsfw") or record.get("maturity")),
        summary=summary_value,
        ankh_layer=normalize_ankh_layer(record.get("ankh_layer") or record.get("layer") or record.get("ankh")),
        tribunal_relevance=tribunal,
    )


def parse_genre_response(content: str, batch_files: list[Path]) -> list[dict]:
    parsed_profiles: list[dict] = []
    for candidate in extract_json_candidates(content):
        records = collect_profile_records(candidate)
        if not records:
            continue
        for idx, record in enumerate(records):
            try:
                fallback = str(batch_files[min(idx, len(batch_files) - 1)].relative_to(REPO_ROOT)).replace("\\", "/")
                profile = normalize_profile(record, fallback)
                parsed_profiles.append(profile.model_dump())
            except Exception:
                continue
        if parsed_profiles:
            break
    return parsed_profiles


def extract_genres(llm, files: list[Path], batch_size: int = 5) -> list[dict]:
    """Extract genre profiles from creative files in batches."""
    all_results: list[dict] = []
    seen_paths: set[str] = set()

    for i in range(0, len(files), batch_size):
        batch = files[i:i + batch_size]
        batch_rel_paths = {str(f.relative_to(REPO_ROOT)).replace("\\", "/").lower() for f in batch}
        file_entries = []
        for f in batch:
            rel_path = str(f.relative_to(REPO_ROOT)).replace("\\", "/")
            excerpt = read_file_excerpt(f)
            file_entries.append(f"### {rel_path}\n```\n{excerpt}\n```\n")

        files_text = "\n".join(file_entries)
        if len(files_text) > 3500:
            files_text = files_text[:3500] + "\n[...truncated...]"

        user_prompt = (
            f"Extract genre/theme/archetype metadata for these {len(batch)} files.\n"
            "Return JSON only. Preferred format:\n"
            '{ "results": [ { "path": "...", "title": "...", "tags": [{ "tag": "...", "category": "theme", "confidence": "medium" }], "nsfw_tier": "none", "summary": "...", "ankh_layer": "LOOP", "tribunal_relevance": "..." } ] }\n\n'
            f"{files_text}"
        )

        batch_label = f"batch {i // batch_size + 1}/{(len(files) + batch_size - 1) // batch_size}"
        print(f"  Genre: {batch_label} ({len(batch)} files)...", end="", flush=True)

        try:
            t0 = time.time()
            result = llm.create_chat_completion(
                messages=[
                    dict(role="system", content=SYSTEM_PROMPT),
                    dict(role="user", content=user_prompt),
                ],
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                response_format={
                    "type": "json_object",
                    "schema": GENRE_SCHEMA,
                },
            )
            elapsed = time.time() - t0
            content = result["choices"][0]["message"]["content"]

            parsed_batch = parse_genre_response(content, batch)
            if parsed_batch:
                added = 0
                for profile in parsed_batch:
                    path_key = profile.get("path", "").replace("\\", "/").lower()
                    if path_key in seen_paths:
                        continue
                    if path_key not in batch_rel_paths:
                        continue
                    seen_paths.add(path_key)
                    all_results.append(profile)
                    added += 1
                print(f" {elapsed:.1f}s ({added} profiles, {len(parsed_batch) - added} skipped)")
            else:
                preview = " ".join(content.strip().split())[:120]
                print(f" {elapsed:.1f}s (parsed 0; response preview: {preview!r})")

        except Exception as e:
            print(f" failed: {e}")

    return all_results


# ── Output ────────────────────────────────────────────────────────

def write_genre_digest(results: list[dict], model_name: str, *, write_json: bool = False):
    """Write genre extraction results to claude/mailbox/."""
    CLAUDE_MAILBOX.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y_%m_%d")

    json_path: Path | None = None
    if write_json:
        json_path = CLAUDE_MAILBOX / f"GENRE_EXTRACTION_{date_str}.json"
        json_path.write_text(json.dumps({
            "generated": now.isoformat(),
            "model": model_name,
            "total_files": len(results),
            "results": results,
        }, indent=2, ensure_ascii=False), encoding="utf-8")

    # Human-readable digest
    md_path = CLAUDE_MAILBOX / f"GENRE_EXTRACTION_{date_str}.md"
    lines = [
        "---",
        "type: genre-extraction",
        "from: genre-extractor-v1",
        "to: claude",
        f"created: {now.isoformat()}",
        "priority: medium",
        "scope: creative-content",
        f"model: {model_name} (local, uncensored, structured JSON)",
        "api-cost: $0 (fully local)",
        "---",
        "",
        f"# Genre Extraction Digest — {now.strftime('%Y-%m-%d')}",
        "",
        f"**Files processed:** {len(results)}",
        f"**Model:** {model_name}",
        "",
        "---",
        "",
    ]

    # Group by NSFW tier
    by_tier = {}
    for r in results:
        tier = r.get("nsfw_tier", "unknown")
        by_tier.setdefault(tier, []).append(r)

    for tier in ["extreme", "explicit", "suggestive", "none"]:
        group = by_tier.get(tier, [])
        if not group:
            continue
        lines.append(f"## {tier.upper()} ({len(group)} files)")
        lines.append("")
        for r in group:
            path = r.get("path", "?")
            title = r.get("title", "?")
            summary = r.get("summary", "")
            tags = r.get("tags", [])
            tag_strs = [f"`{t.get('tag', '?')}` ({t.get('category', '?')})" for t in tags[:8]]
            ankh = r.get("ankh_layer", "?")
            tribunal = r.get("tribunal_relevance", "?")

            lines.append(f"### {title}")
            lines.append(f"**Path:** `{path}`")
            lines.append(f"**Tags:** {', '.join(tag_strs)}")
            lines.append(f"**Ankh Layer:** {ankh}")
            lines.append(f"**Tribunal:** {tribunal}")
            lines.append(f"**Summary:** {summary}")
            lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  Digest: {md_path}")
    if json_path is not None:
        print(f"  JSON:   {json_path}")
    else:
        print("  JSON:   skipped (use --json-out to enable)")
    return md_path, json_path


# ── Main ──────────────────────────────────────────────────────────

def main():
    import argparse
    from scripts.lib.shared import configure_utf8_output
    configure_utf8_output()

    parser = argparse.ArgumentParser(description="Extract genre/theme metadata from creative content")
    parser.add_argument("--path", type=str, nargs="+", help="Specific paths to scan (default: all creative dirs)")
    parser.add_argument("--coder", action="store_true", help="Use Qwen3-Coder model")
    parser.add_argument("--model-dir", type=str, help="Override model directory")
    parser.add_argument("--batch-size", type=int, default=3, help="Files per inference batch (default: 3)")
    parser.add_argument("--dry-run", action="store_true", help="List files without running inference")
    parser.add_argument("--smoke", action="store_true", help="Smoke test: process 1 file, exit 1 if 0 profiles extracted")
    parser.add_argument(
        "--json-out",
        action="store_true",
        help="Also write JSON artifact alongside Markdown digest.",
    )
    args = parser.parse_args()

    # Model selection
    if args.model_dir:
        model_dir = Path(args.model_dir)
    elif args.coder:
        model_dir = CODER_MODEL_DIR
    else:
        model_dir = DEFAULT_MODEL_DIR

    print("☥ Genre Extractor v1 (llama-cpp + structured JSON, uncensored)")
    print(f"  Model: {model_dir.name}")

    # Discover files
    files = discover_creative_files(args.path)
    print(f"  Creative files found: {len(files)}")

    if not files:
        print("  No creative content files found.")
        return

    # Smoke gate: test 1 file, fail-fast if extraction broken
    if args.smoke:
        if not model_dir.exists():
            print(f"SMOKE FAIL: Model directory not found: {model_dir}")
            sys.exit(1)
        smoke_file = files[:1]
        print(f"  Smoke test: {smoke_file[0].relative_to(REPO_ROOT)}")
        llm = load_model(model_dir)
        results = extract_genres(llm, smoke_file, batch_size=1)
        if results:
            print(f"  SMOKE OK: {len(results)} profile(s) extracted")
            sys.exit(0)
        else:
            print("  SMOKE FAIL: 0 profiles — schema or model regression detected")
            sys.exit(1)

    if args.dry_run:
        print("\n── DRY RUN ──")
        for f in files:
            rel = f.relative_to(REPO_ROOT)
            size = f.stat().st_size
            print(f"  {size:>8,} B  {rel}")
        print(f"\n  Total: {len(files)} files")
        return

    if not model_dir.exists():
        print(f"ERROR: Model directory not found: {model_dir}")
        sys.exit(1)

    # Load model
    llm = load_model(model_dir)

    # Extract
    print()
    t0 = time.time()
    results = extract_genres(llm, files, batch_size=args.batch_size)
    total_time = time.time() - t0

    print(f"\n  Genre extraction complete: {len(results)} profiles in {total_time:.1f}s")

    # Write output
    write_genre_digest(results, model_dir.name, write_json=args.json_out)
    print(f"\n☥ Genre extraction complete ($0 cost).")


if __name__ == "__main__":
    main()
