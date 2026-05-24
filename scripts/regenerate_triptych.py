#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: regenerate_triptych.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
regenerate_triptych.py — Regenerate CROSS_REFERENCE_TRIPTYCH.md for the current repo.

Walks the actual filesystem, classifies every project-relevant file into
Fortress/Garden/Observatory/Documentation/Configuration, assigns spectral
frequencies and theatrical essences via heuristic analysis, then writes
the updated triptych.

Excludes vendored/build artifacts while including all new project areas
discovered since the original DCRP generation.

Usage: python scripts/regenerate_triptych.py [--dry-run]

@SID:           TOOL_REGENERATE_TRIPTYCH_V1
@Shabti:        CLI Script
@Purpose:       regenerate_triptych.py — Regenerate CROSS_REFERENCE_TRIPTYCH.md for the current repo.
"""


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import ast
import os
import re
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).parent.parent

# ═══════════════════════════════════════════════════════════════════════════
#  EXCLUSIONS — vendored, build, transient
# ═══════════════════════════════════════════════════════════════════════════
EXCLUDE_DIRS = {
    ".git", "node_modules", "target", "build", "dist", ".next",
    "__pycache__", ".venv", ".venv-py314-parked", "site-packages",
    ".cache", ".ruff_cache", "crawl-output",
    # Vendored third-party
    "LocalAI-3.11.0",
    # Deep archive/corpse trees (thousands of files, not project code)
    "corpse-vault",
    # Extension bundled dependencies / compiled output
    "out",
    # Bulk generated artifacts
    "genesis_artifacts", "frontend",
    # Model weights
    "Llama-3.1-8B-Instruct-exl2-8.0bpw",
    # Deprecated scripts archive
    ".deprecated",
    # Session logs (bulk)
    "codex-session-logs",
    # Ruby/Go vendored inside extensions
    "vendor", "gems",
}
EXCLUDE_DIR_PREFIXES = {
    # Don't exclude dumpster-dive entirely — it has some project scripts
}
EXCLUDE_FILES = {
    ".DS_Store", "Thumbs.db", ".gitignore", ".gitattributes",
    "uv.lock", "bun.lock", "Cargo.lock", "package-lock.json",
}
# Skip binary/media extensions
BINARY_EXTS = {
    ".exe", ".dll", ".so", ".node", ".wasm", ".pak", ".asar",
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp",
    ".mp3", ".wav", ".ogg", ".mp4", ".webm",
    ".ttf", ".woff", ".woff2", ".otf",
    ".zip", ".gz", ".tgz", ".tar", ".7z",
    ".gguf", ".safetensors", ".bin", ".dat",
    ".gem", ".pdb", ".rlib", ".rmeta", ".o",
    ".delta", ".pack", ".idx",
    ".vsix", ".appx",
    # Non-project bulk extensions
    ".fragment", ".log", ".snapshot", ".metadata", ".marker",
    ".sst", ".tag", ".off", ".rsc",
    ".scpt", ".standalone",
    ".map",  # Source maps
}

# ═══════════════════════════════════════════════════════════════════════════
#  SPECTRAL FREQUENCY MAP (PRISM - from Section III.4)
# ═══════════════════════════════════════════════════════════════════════════
SPECTRAL_MAP = {
    ".rs": "RED",
    ".toml": "BLUE",
    ".py": "GREEN",
    ".md": "GOLD",
    ".json": "BLUE",
    ".yaml": "BLUE",
    ".yml": "BLUE",
    ".ts": "ORANGE",
    ".tsx": "ORANGE",
    ".js": "ORANGE",
    ".jsx": "ORANGE",
    ".glsl": "INDIGO",
    ".vert": "INDIGO",
    ".frag": "INDIGO",
    ".ps1": "VIOLET",
    ".sh": "VIOLET",
    ".bat": "VIOLET",
    ".cmd": "VIOLET",
    ".zsh": "VIOLET",
    ".fish": "VIOLET",
    ".nu": "VIOLET",
    ".html": "GREEN",
    ".css": "GREEN",
    ".lock": "BLUE",
    ".ipynb": "WHITE",
    ".sql": "BLUE",
    ".rb": "WHITE",
    ".go": "RED",
    ".c": "RED",
    ".h": "RED",
    ".cpp": "RED",
    ".txt": "GOLD",
    ".log": "GOLD",
}

# ═══════════════════════════════════════════════════════════════════════════
#  THEATRICAL ESSENCE — directory/file heuristics
# ═══════════════════════════════════════════════════════════════════════════

def classify_theatrical_essence(rel_path: str, ext: str) -> str:
    """Assign theatrical essence based on path patterns and content heuristics."""
    p = rel_path.replace("\\", "/").lower()

    # Rust domain
    if ext == ".rs":
        if "render" in p or "vulkan" in p or "pipeline" in p or "swapchain" in p:
            return "Vulkan rendering pipeline - visual truth incarnate"
        if "camera" in p:
            return "Isometric camera - spatial perception engine"
        if "daemon" in p or "reactor" in p:
            return "Chthonic daemon - entropy monitoring reactor"
        if "synapse" in p or "loom" in p:
            return "Neural synapse - cross-language bridge"
        if "entropy" in p:
            return "Entropy ledger - chaos measurement host"
        if "wasm" in p:
            return "WebAssembly module - browser-portable logic"
        if "data" in p:
            if "faction" in p:
                return "Faction data model - cRPG entity definitions"
            if "loader" in p:
                return "Data loader - game state hydration"
            if "persistence" in p:
                return "Save/load persistence - state serialization"
            if "procedural" in p:
                return "Procedural generation - algorithmic world-building"
            if "verifier" in p:
                return "Data integrity verifier - corruption sentinel"
            if "types" in p or "mod" in p:
                return "Type definitions - structural foundation"
        if "xtask" in p:
            return "Build task runner - cargo xtask automation"
        if "lib.rs" in p:
            return "Library root - module re-exports"
        if "main.rs" in p:
            return "Entry point - execution bootstrap"
        if "build.rs" in p:
            return "Build script - compile-time orchestration"
        return "Rust module - Fortress infrastructure"

    # Python domain
    if ext == ".py":
        if "mcp" in p or "server" in p:
            return "MCP server - AI governance bridge"
        if "gpu" in p or "cuda" in p or "benchmark" in p:
            return "GPU execution lane - computational muscle"
        if "governance" in p or "milf" in p or "genesis" in p:
            return "Governance operative - matriarchal command structure"
        if "skill" in p:
            if "polisher" in p or "polish" in p:
                return "Skill polisher - quality enforcement"
            if "install" in p:
                return "Skill installer - capability provisioning"
            if "creator" in p or "init" in p:
                return "Skill creator - capability scaffolding"
            return "Skill script - agent capability"
        if "mailbox" in p or "handoff" in p:
            return "Mailbox handler - inter-agent communication"
        if "image_gen" in p or "sora" in p:
            return "Media generation - OpenAI creative API"
        if "ssot" in p or "hash" in p:
            return "SSOT integrity - canonical truth verification"
        if "scan" in p or "audit" in p or "validate" in p:
            return "Audit/validation - structural integrity check"
        if "topology" in p or "mandala" in p:
            return "Topology mapper - architectural visualization"
        if "decorator" in p or "dcrp" in p or "cross_ref" in p:
            return "DCRP generator - cross-reference protocol"
        if "extract" in p or "ingest" in p:
            return "Content extractor - knowledge distillation"
        if "health" in p or "diagnostic" in p:
            return "Health diagnostics - system vitality probe"
        if "test" in p:
            return "Test suite - verification harness"
        if "codekiller" in p:
            return "CodeKiller remediation - anti-pattern gate"
        if "corpse" in p or "upcycle" in p or "dumpster" in p:
            return "Artifact upcycler - dead code salvage"
        if "overnight" in p or "daemon" in p:
            return "Overnight daemon - autonomous batch processor"
        if "session" in p or "resumer" in p:
            return "Session management - continuity protocol"
        if "orchestrat" in p or "coordinat" in p:
            return "Orchestration coordinator - workflow sequencer"
        if "bridge" in p:
            return "Bridge connector - cross-system integration"
        if "sentry" in p:
            return "Sentry integration - error telemetry"
        if "resolve" in p or "sid" in p:
            return "SID resolver - section identity lookup"
        if "lib" in p and ("__init__" in p or "shared" in p):
            return "Shared library - common utilities"
        if "__init__" in p or "__main__" in p:
            return "Package module - namespace entry"
        if "compact" in p or "strip" in p:
            return "Content compactor - noise reduction"
        if "map" in p or "codebase" in p:
            return "Codebase mapper - structural survey"
        if "qualia" in p or "resonance" in p or "narrative" in p:
            return "Aesthetic logic - qualitative synthesis"
        if "abbreviat" in p:
            return "Abbreviation system - notation standardization"
        return "Python module - Garden infrastructure"

    # TypeScript domain
    if ext in (".ts", ".tsx"):
        if "mcp" in p or "server" in p:
            if "injector" in p or "asc" in p:
                return "ASC injector - framework context MCP server"
            if "chthonic" in p:
                return "Chthonic MCP server - repository introspection"
            if "artisan" in p:
                return "Artisan MCP server - creative tooling"
            if "sentry" in p:
                return "Sentry MCP proxy - error telemetry bridge"
            if "tool" in p or "preflight" in p:
                return "MCP tool implementation - server capability"
            if "validation" in p or "validate" in p:
                return "MCP validation - server health check"
            return "MCP integration - Observatory communication layer"
        if "playwright" in p or "cdp" in p or "browser" in p:
            return "Browser automation - CDP/Playwright integration"
        if "extension" in p:
            if "mandala" in p:
                return "VS Code extension - sacred geometry visualization"
            if "statusbar" in p:
                return "VS Code extension - SSOT status indicators"
            if "chthonic-archive" in p:
                return "VS Code extension - Chthonic Archive core"
            return "VS Code extension module"
        if "bridge" in p or "plugin" in p:
            return "Bridge/plugin - cross-system connector"
        if "daemon" in p or "overnight" in p:
            return "Overnight daemon - autonomous batch TypeScript"
        if "setup" in p or "install" in p:
            return "Setup script - environment provisioning"
        if "test" in p or "smoke" in p or "spec" in p:
            return "Test harness - verification suite"
        if "sentry" in p:
            return "Sentry telemetry - error tracking"
        if "hf-model" in p or "ranker" in p:
            return "HuggingFace model ranker - AI model discovery"
        if "art-cop" in p or "artcop" in p:
            return "ArtCop - visual regression screener"
        if "next" in p or "app" in p:
            if ".tsx" == ext:
                return "Next.js component - web application UI"
            return "Next.js module - web application logic"
        return "TypeScript module - Observatory infrastructure"

    # Documentation
    if ext in (".md", ".txt"):
        if "readme" in p.lower():
            return "Entry portal - first architectural revelation"
        if "ssot" in p or "copilot-instructions" in p or "codex" in p:
            return "Single Source of Truth - the Codex Brahmanica Perfectus"
        if "ankh" in p:
            return "ANKH lineage heritage - ancestral knowledge vessel"
        if "handoff" in p:
            return "Agent handoff - cross-session continuity"
        if "session" in p:
            return "Session record - archaeological stratum"
        if "lore" in p or "mythology" in p:
            return "Lore document - narrative world-building"
        if "protocol" in p:
            return "Protocol specification - operational contract"
        if "architecture" in p or "topology" in p:
            return "Architecture document - structural blueprint"
        if "health" in p or "report" in p:
            return "Health/status report - system vitality record"
        if "claude" in p or "gemini" in p:
            return "Agent configuration - triad governance document"
        if "skill" in p:
            return "Skill documentation - capability reference"
        if "framework" in p:
            return "Framework specification - structural canon"
        if "reference" in p:
            return "Reference document - knowledge anchor"
        if "validation" in p or "audit" in p:
            return "Validation record - integrity proof"
        if "design" in p or "concept" in p:
            return "Design document - creative specification"
        if "standard" in p or "canon" in p:
            return "Standard/canon - normative specification"
        if "instruction" in p or "rule" in p:
            return "Instruction file - behavioral directive"
        return "Documentation - architectural knowledge"

    # Configuration
    if ext in (".json", ".toml", ".yaml", ".yml"):
        if "package.json" in p:
            return "Node package manifest - dependency declaration"
        if "cargo.toml" in p:
            return "Rust crate manifest - Fortress build config"
        if "pyproject.toml" in p:
            return "Python project manifest - Garden build config"
        if "tsconfig" in p:
            return "TypeScript compiler config"
        if "mcp" in p:
            return "MCP server configuration"
        if "task" in p:
            return "VS Code task runner config"
        if "launch" in p:
            return "VS Code debug launch config"
        if "settings" in p:
            return "Settings configuration"
        if "theme" in p or "color" in p:
            return "Theme definition - visual identity"
        if "graph" in p or "topology" in p:
            return "Dependency graph data - structural topology"
        if "schema" in p:
            return "Schema definition - data contract"
        if "index" in p or "registry" in p:
            return "Index/registry - lookup table"
        if "state" in p or "dcrp" in p:
            return "DCRP state cache - protocol memory"
        if "curriculum" in p:
            return "Curriculum data - learning extraction"
        if "artifact" in p:
            return "MCP run artifact - execution record"
        return f"Configuration: {Path(rel_path).name}"

    # Shell scripts
    if ext in (".ps1", ".sh", ".bat", ".cmd", ".zsh", ".fish", ".nu"):
        if "patch" in p:
            return "Patch script - environment fix"
        if "install" in p or "setup" in p:
            return "Setup script - environment provisioning"
        if "fix" in p:
            return "Fix script - corrective action"
        return "Shell script - automation utility"

    return f"File: {Path(rel_path).name}"


# ═══════════════════════════════════════════════════════════════════════════
#  DOMAIN CLASSIFICATION
# ═══════════════════════════════════════════════════════════════════════════

def classify_domain(rel_path: str, ext: str) -> str:
    """Classify a file into its Triptych domain."""
    if ext in (".rs",):
        return "FORTRESS"
    if ext in (".py", ".ipynb"):
        return "GARDEN"
    if ext in (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"):
        return "OBSERVATORY"
    if ext in (".md", ".txt"):
        return "DOCUMENTATION"
    if ext in (".json", ".toml", ".yaml", ".yml", ".lock"):
        return "CONFIGURATION"
    if ext in (".ps1", ".sh", ".bat", ".cmd", ".zsh", ".fish", ".nu"):
        return "CONFIGURATION"  # Shell scripts as config/automation
    if ext in (".html", ".css"):
        return "OBSERVATORY"
    if ext in (".glsl", ".vert", ".frag"):
        return "FORTRESS"  # Shaders are Fortress
    if ext in (".go", ".c", ".h", ".cpp"):
        return "FORTRESS"  # Systems languages
    if ext in (".rb",):
        return "GARDEN"  # Ruby is Garden-adjacent
    return "CONFIGURATION"  # Default


def should_include(rel_path: str, is_dumpster: bool = False) -> bool:
    """Decide if a file is project-relevant enough for the triptych."""
    p = rel_path.replace("\\", "/").lower()

    # Always exclude vendored third-party
    if "site-packages" in p or ".venv" in p:
        return False

    # Dumpster-dive: only include top-level scripts/readmes, not deep archives
    if is_dumpster:
        depth = p.count("/")
        if depth > 2:
            return False
        return True

    # meta-ide: only include top-level config/readmes, not vendored tools
    if p.startswith("meta-ide/"):
        depth = p.count("/")
        if depth > 1:
            return False
        return True

    # models/: skip model weight directories entirely
    if p.startswith("models/"):
        return False

    # Skip bulk artifact runs (MCP run JSONs)
    if "mcp_run_" in p:
        return False

    # Skip bulk health reports
    if "health_report" in p:
        return False

    # Skip bulk mailbox content (keep only READMEs and recent)
    if "/mailbox/" in p:
        depth_in_mailbox = p.split("/mailbox/")[1].count("/")
        if depth_in_mailbox > 1:
            return False

    # Skip session-archives bulk content
    if "session-archives/" in p or "session_resumption_pickup" in p:
        return False

    # Skip tabbyAPI vendored content
    if "tabbyapi" in p:
        return False

    # Extensions: for chthonic-archive ext, only include src/ and native/ code
    if "extensions/chthonic-archive/" in p:
        kept = ("src/", "native/", "wasm/", "package.json", "readme",
                "cargo.toml", "tsconfig")
        if not any(k in p for k in kept):
            return False

    return True


# ═══════════════════════════════════════════════════════════════════════════
#  REPO SCANNER
# ═══════════════════════════════════════════════════════════════════════════

def scan_repo():
    """Walk the repo and classify all project-relevant files."""
    results = defaultdict(list)  # domain -> [(rel_path, spectral, essence)]

    KNOWN_HIDDEN = {".vscode", ".github", ".claude", ".codex", ".gemini",
                     ".temple", ".chthonic", ".meta", ".claude-plugin"}

    for dirpath, dirnames, filenames in os.walk(str(REPO_ROOT)):
        # Prune excluded directories
        dirnames[:] = [
            d for d in dirnames
            if (d not in EXCLUDE_DIRS
                and (not d.startswith(".") or d in KNOWN_HIDDEN))
        ]

        try:
            rel_dir = os.path.relpath(dirpath, str(REPO_ROOT))
        except ValueError:
            continue
        is_dumpster = rel_dir.startswith("dumpster-dive")

        for fname in sorted(filenames):
            if fname in EXCLUDE_FILES:
                continue
            ext = os.path.splitext(fname)[1].lower()
            if ext in BINARY_EXTS:
                continue

            rel_path = os.path.join(rel_dir, fname)
            if rel_path.startswith(".\\") or rel_path.startswith("./"):
                rel_path = rel_path[2:]

            if not should_include(rel_path, is_dumpster):
                continue

            domain = classify_domain(rel_path, ext)
            spectral = SPECTRAL_MAP.get(ext, "VIOLET")
            essence = classify_theatrical_essence(rel_path, ext)
            results[domain].append((rel_path, spectral, essence))

    return results


# ═══════════════════════════════════════════════════════════════════════════
#  TRIPTYCH GENERATOR
# ═══════════════════════════════════════════════════════════════════════════

def generate_triptych(domains: dict) -> str:
    """Generate the CROSS_REFERENCE_TRIPTYCH.md content."""
    lines = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    lines.append("# THE CHTHONIC ARCHIVE: Cross-Reference Triptych")
    lines.append("")
    lines.append("**Generated by The Decorator's Cross-Reference Protocol (DCRP)**")
    lines.append(f"**Regenerated:** {now}")
    lines.append("")
    lines.append("This document maps the bidirectional relationships across all files in the repository,")
    lines.append("revealing the tri-modal architecture (Fortress/Garden/Observatory) through")
    lines.append("spectral frequency mapping and theatrical essence classification.")
    lines.append("")
    lines.append("---")
    lines.append("")

    section_config = [
        ("FORTRESS", "## \U0001f3f0 THE FORTRESS (Rust/Vulkan/Systems)",
         "**Architectural Domain:** Game engine, visual rendering, native daemons, WASM modules"),
        ("GARDEN", "## \U0001f33f THE GARDEN (Python/MCP)",
         "**Architectural Domain:** AI governance, GPU execution, skills, automation scripts"),
        ("OBSERVATORY", "## \U0001f52d THE OBSERVATORY (TypeScript/Bun)",
         "**Architectural Domain:** MCP servers, VS Code extensions, browser automation, web apps"),
        ("DOCUMENTATION", "## \U0001f4dc DOCUMENTATION",
         None),
        ("CONFIGURATION", "## \u2699\ufe0f CONFIGURATION",
         None),
    ]

    total_files = 0
    for domain, heading, description in section_config:
        files = domains.get(domain, [])
        total_files += len(files)

        lines.append(heading)
        lines.append("")
        if description:
            lines.append(description)
            lines.append("")
        lines.append("| File | Spectral Freq | Theatrical Essence |")
        lines.append("|------|---------------|-------------------|")
        for rel_path, spectral, essence in sorted(files, key=lambda x: x[0]):
            lines.append(f"| `{rel_path}` | {spectral} | {essence} |")
        lines.append("")

    # Stats section
    lines.append("## \U0001f4ca CROSS-REFERENCE STATISTICS")
    lines.append("")
    lines.append(f"- **Total Files Mapped:** {total_files}")
    for domain, heading, _ in section_config:
        count = len(domains.get(domain, []))
        emoji = heading.split(" ")[1] if " " in heading else ""
        name = domain.title()
        lines.append(f"- **{name}:** {count} files")
    lines.append("")

    # Domain evolution note
    lines.append("### Evolution from Original (b45a0f90)")
    lines.append("")
    lines.append("| Domain | Original (6,637L) | Current | Delta | Notes |")
    lines.append("|--------|-------------------|---------|-------|-------|")
    orig_counts = {"FORTRESS": 15, "GARDEN": 5704, "OBSERVATORY": 102,
                   "DOCUMENTATION": 306, "CONFIGURATION": 611}
    for domain, _, _ in section_config:
        o = orig_counts.get(domain, 0)
        c = len(domains.get(domain, []))
        delta = c - o
        sign = "+" if delta > 0 else ""
        note = ""
        if domain == "GARDEN" and delta < -1000:
            note = "5,721 vendored .venv files removed"
        elif domain == "FORTRESS" and delta > 0:
            note = "New: chthonic-daemon, synapse, WASM, context-compressor"
        elif domain == "OBSERVATORY" and delta > 0:
            note = "New: chthonic-archive ext, Next.js app, HF ranker"
        lines.append(f"| {domain.title()} | {o} | {c} | {sign}{delta} | {note} |")
    lines.append("")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

    dry_run = "--dry-run" in sys.argv

    print("\n=== DCRP Triptych Regeneration ===\n")

    domains = scan_repo()

    total = sum(len(v) for v in domains.values())
    for domain in ["FORTRESS", "GARDEN", "OBSERVATORY", "DOCUMENTATION", "CONFIGURATION"]:
        count = len(domains.get(domain, []))
        print(f"  {domain:20s}: {count:>4} files")
    print(f"  {'TOTAL':20s}: {total:>4} files")

    content = generate_triptych(domains)
    line_count = content.count("\n") + 1

    output = REPO_ROOT / "docs" / "protocols" / "CROSS_REFERENCE_TRIPTYCH.md"

    if dry_run:
        print(f"\n  [DRY RUN] Would write {line_count} lines to {output}")
        print(f"  First 20 lines:")
        for line in content.split("\n")[:20]:
            print(f"    {line}")
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
        print(f"\n  Written: {output} ({line_count} lines)")

    print("\nDone.")


if __name__ == "__main__":
    main()
