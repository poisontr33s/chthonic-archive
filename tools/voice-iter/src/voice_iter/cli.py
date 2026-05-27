"""voice-iter CLI entry point. Subcommands: init / check / corpus / catalog / run."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import VoiceIterConfig


def cmd_init(args: argparse.Namespace) -> int:
    """Scaffold a voice-iter.toml in the current directory."""
    cfg = VoiceIterConfig.template(args.project_name)
    out_path = Path(args.config)
    if out_path.exists() and not args.force:
        print(f"[voice-iter] {out_path} already exists. Pass --force to overwrite.", file=sys.stderr)
        return 1
    # Write as TOML manually (tomli is read-only; tomli_w would add a dep we don't need yet)
    out_path.write_text(_dump_template_toml(cfg), encoding="utf-8")
    print(f"[voice-iter] wrote template config at {out_path}")
    print("Next: edit hotwords, voice, corpus paths to match your project.")
    return 0


def _dump_template_toml(cfg: VoiceIterConfig) -> str:
    """Hand-rolled TOML serialization (kept dependency-free for V1)."""
    return f"""project_name = "{cfg.project_name}"

[transport]
type = "mcp"
mcp_name = "voice-iter-{cfg.project_name}"

[stt]
provider = "parakeet"
model_path = "~/.cache/voice-iter/models/parakeet-tdt-v3"
language = "en"
silence_threshold_db = -50.0
hotwords = []  # project-specific vocabulary the STT should prefer

[tts]
provider = "kokoro"
voice = "af_bella"
model_path = "~/.cache/voice-iter/models/kokoro-82m"
speed = 1.1

[corpus]
test_corpus_path = "tests/voice_corpus.txt"

[output]
manifest_dir = "manifest/voice"
audio_artifacts_dir = "manifest/voice/.audio_snapshots"
ledger_path = "manifest/voice/voice_iteration_history.ndjson"
catalog_path = "tests/voice_config_catalog.json"

[checkpoint]
retention = 20
"""


def cmd_check(args: argparse.Namespace) -> int:
    """Run the test corpus through the configured stack; score; append to ledger."""
    cfg = VoiceIterConfig.load(args.config)
    print(f"[voice-iter] project={cfg.project_name}")
    print(f"[voice-iter] STT: {cfg.stt.provider} ({cfg.stt.model_path})")
    print(f"[voice-iter] TTS: {cfg.tts.provider} voice={cfg.tts.voice}")
    print("[voice-iter] eval pipeline NOT YET IMPLEMENTED (V0.1 scaffold)")
    print("            implementation lands once models are installed locally")
    return 0


def cmd_corpus(args: argparse.Namespace) -> int:
    """Show the configured test corpus stats."""
    cfg = VoiceIterConfig.load(args.config)
    corpus_path = Path(cfg.corpus.test_corpus_path)
    if not corpus_path.exists():
        print(f"[voice-iter] corpus not found at {corpus_path}", file=sys.stderr)
        return 1
    lines = corpus_path.read_text(encoding="utf-8").splitlines()
    nonblank = [l for l in lines if l.strip() and not l.strip().startswith("#")]
    print(f"[voice-iter] corpus: {corpus_path}")
    print(f"           total lines: {len(lines)}")
    print(f"           eval lines:  {len(nonblank)} (excluding comments + blanks)")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    """Run as MCP server (placeholder until transport.py lands)."""
    cfg = VoiceIterConfig.load(args.config)
    print(f"[voice-iter] MCP server mode — NOT YET IMPLEMENTED")
    print(f"            transport: {cfg.transport.type} name={cfg.transport.mcp_name}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="voice-iter", description="Voice integration toolkit (polyrepo-aware)")
    p.add_argument("--config", default="voice-iter.toml", help="Path to voice-iter.toml")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="Scaffold a voice-iter.toml")
    p_init.add_argument("project_name")
    p_init.add_argument("--force", action="store_true")
    p_init.set_defaults(func=cmd_init)

    p_check = sub.add_parser("check", help="Run corpus eval + ledger append")
    p_check.set_defaults(func=cmd_check)

    p_corpus = sub.add_parser("corpus", help="Show corpus stats")
    p_corpus.set_defaults(func=cmd_corpus)

    p_run = sub.add_parser("run", help="Run as MCP server")
    p_run.set_defaults(func=cmd_run)

    return p


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
