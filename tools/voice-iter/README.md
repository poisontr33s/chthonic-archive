# voice-iter

Voice integration toolkit, polyrepo-aware. Generalized core + per-project config.
Companion to `tools/dsl-iteration-toolkit/` (same methodology, different surface).

## Status

V0.1 scaffold (2026-05-27). Configuration schema + CLI skeleton + chthonic
instance config + test corpus + architecture doc. Provider implementations
(Parakeet STT, Kokoro TTS, etc.) pending model installs.

## What is it

A single voice integration tool that works across all projects in this poly-repo,
modernized for 2026:

- **STT**: NVIDIA Parakeet TDT V3 (default) — 3-6× faster than Whisper for English,
  doesn't hallucinate during silences, trained on 36K hours of pure non-speech
  audio. Faster-Whisper Large V3 as control / multilingual fallback.
- **TTS**: Kokoro 82M (default) — 210× real-time on a 4090, Apache 2.0,
  uncensored. Fish Speech S1 as quality-tier alternative.
- **Transport**: MCP server (compatible with Claude Code and other MCP clients).
- **Polyrepo aware**: per-project `voice-iter.toml`; shared model cache at
  `~/.cache/voice-iter/models/`; per-project catalog + ledger.

See `ARCHITECTURE.md` for the design vision.

## Quick start

```powershell
# Install (development; uses uv per repo Python policy)
uv pip install -e tools/voice-iter

# Scaffold a per-project config (run inside the target project)
voice-iter init my-project

# Show what's currently configured
voice-iter --config voice-iter.toml corpus

# Run the corpus eval (once providers are wired)
voice-iter --config voice-iter.toml check
```

For the chthonic instance, the config already exists at `.chthonic/voice-iter.toml`:

```powershell
voice-iter --config .chthonic/voice-iter.toml corpus
voice-iter --config .chthonic/voice-iter.toml check
```

## Why a separate toolkit (not just install voice-mode)

`voice-mode` (mbailey, v8.6.1) is a solid MCP-based voice integration. We
build voice-iter alongside it rather than instead of it because:

1. **Polyrepo support**: voice-mode assumes single-project; voice-iter's
   per-project config + shared model cache reflects how the conductor actually
   works across many projects.
2. **Modernized STT default**: Parakeet TDT V3 (post-Jan-2026) is significantly
   better for English than Whisper, and voice-mode hasn't switched defaults.
3. **Methodology compounds**: voice-iter shares the catalog/coverage/ledger/
   checkpoint discipline from `dsl-iteration-toolkit`. The conductor learns
   one pattern; applies it to grammar work, voice work, future surfaces.
4. **Catalyst-aware**: chthonic-specific hotwords baked into STT for better
   recognition of project vocabulary (Lysandra, MILFOLOGICAL, WHR:MAX, etc.).

voice-mode remains as the alternative reference implementation; the in-house
toolkit is for the polyrepo's specific shape.

## Three loops (composes with the DSL toolkit)

| Loop | DSL toolkit | voice-iter |
|---|---|---|
| A (substrate) | grammar edits → smoke | voice config swaps → eval |
| B (methodology) | dsl-iter check/coverage/catalog | voice-iter check/corpus/catalog |
| C (rewindability) | checkpoint snapshots | voice config snapshots + audio artifacts |

Both toolkits run side-by-side. The conductor uses the same discipline across
both surfaces.

## Test corpus (the chthonic-specific eval)

`tests/chthonic_voice_corpus.txt` carries ~50 lines covering 8 evaluation axes
that generic TTS leaderboards miss:

1. Backtick-id pronunciation (`` `The-Savant` ``)
2. Greek letters inline (Phase β-γ)
3. Code identifiers in spoken context
4. NSFW++ vocabulary tolerance
5. Long paren-dense substrate
6. Character name disambiguation
7. Spec citations (§10.3.1, L4049)
8. Mixed-case CAS proper nouns (FA-GHOR, WHR:MAX)

The corpus IS the eval contract. Future iterations will measure WER per axis,
TTS quality per axis, refusal rate per axis.

## Roadmap

| Step | Status | Notes |
|---|---|---|
| Scaffold + config schema + corpus | ✅ done (this commit) | |
| Install Parakeet TDT V3 + Kokoro models | ⏳ pending | ~2GB download to ~/.cache/voice-iter/ |
| Implement provider modules | ⏳ pending | wires NeMo Parakeet + Kokoro pip packages |
| `voice-iter check` real implementation | ⏳ pending | runs corpus through stack, scores |
| MCP server transport | ⏳ pending | analogous to voice-mode's MCP layer |
| Polyrepo roll-out | ⏳ pending | first second-project install (PsychoNoir or similar) |

See `ARCHITECTURE.md` for full design.
