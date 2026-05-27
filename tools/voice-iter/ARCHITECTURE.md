# voice-iter — Voice integration toolkit (polyrepo-aware)

> Cross-project voice technology layer, modernized 2026-05. Same methodology
> as `tools/dsl-iteration-toolkit/`: generalized core + per-project config +
> catalog + coverage + ledger + checkpoint discipline. Different surface
> (voice, not grammar), same loops (substrate / methodology / rewindability).

## Why

The conductor works across many projects in this polyrepo (chthonic-archive,
PsychoNoir-Kontrapunkt, Restructure-MCP-Orchestration, Claudine_Supreme,
others). Voice integration is a leverage that compounds across ALL of them.
Building per-project would duplicate effort; building generic but unconfigured
loses the project-specific advantages (catalog-aware STT, character voices,
domain-tuned recognition).

The shape that fits: **shared toolkit + per-project config**.

## Relation to voice-mode

`voice-mode` (mbailey, v8.6.1) is a solid MCP-based voice integration. We
fork conceptually rather than literally: take what's good (MCP transport
pattern, OpenAI-compatible STT/TTS API, local fallback path) and replace
what's outdated or constraining (default Whisper STT → Parakeet TDT V3;
single-project assumption → per-project catalogs).

The fork lives at `tools/voice-iter/` — Python, because the voice ecosystem
is Python (Whisper, Parakeet, Kokoro, Fish Speech all Python-native). This
contrasts with `dsl-iteration-toolkit/` which is Rust (pest is Rust-native).
Mixed-language workspace is fine; the methodology is what carries across.

## The three loops, applied to voice

| Loop | DSL toolkit | voice-iter equivalent |
|---|---|---|
| A (substrate iteration) | grammar edits → smoke | voice config changes → eval against test corpus |
| B (methodology tooling) | dsl-iter check / coverage / catalog | voice-iter check / corpus / catalog |
| C (rewindability) | checkpoint snapshots before mutations | model+config snapshots before swaps |

## Components

```
tools/voice-iter/                         ← the toolkit (project-agnostic)
  pyproject.toml                           Python project definition
  src/voice_iter/
    __init__.py
    cli.py                                voice-iter CLI (check / corpus / catalog / run)
    config.py                             voice-iter.toml schema
    catalog.py                            voice-config-catalog.json reader
    eval.py                               run test corpus through configured stack, score
    transport.py                          MCP server entry (analogous to voice-mode)
    providers/
      __init__.py
      stt_parakeet.py                     NVIDIA Parakeet TDT V3 (preferred for English)
      stt_whisper.py                      Faster-Whisper (control / multilingual fallback)
      tts_kokoro.py                       Kokoro 82M (default, smallest)
      tts_fish_speech.py                  Fish Speech S1 (when quality matters)
  README.md
  ARCHITECTURE.md (this file)
  examples/
    voice-iter.toml                       example per-project config

<each-project>/voice-iter.toml            ← per-project config
~/.cache/voice-iter/                      ← shared model cache (cross-project)
  models/parakeet-tdt-v3/
  models/kokoro-82m/
  models/fish-speech-s1/
<each-project>/manifest/voice/            ← per-project eval results + ledger
```

## Per-project config schema (voice-iter.toml)

```toml
project_name = "chthonic"

[transport]
type = "mcp"                              # "mcp" | "stdio" | "websocket"
mcp_name = "voice-iter-chthonic"

[stt]
provider = "parakeet"                     # "parakeet" | "whisper" | "moonshine"
model_path = "~/.cache/voice-iter/models/parakeet-tdt-v3"
language = "en"
silence_threshold_db = -50.0
hotwords = [                              # project-specific vocabulary the STT prefers
  "Lysandra", "Orackla", "Umeko", "Claudine",
  "MILFOLOGICAL", "ANKHOLOGICAL",
  "WHR:MAX", "FA-GHOR", "K-CUP",
]

[tts]
provider = "kokoro"                       # "kokoro" | "fish_speech" | "openai"
voice = "af_bella"                         # provider-specific voice id
model_path = "~/.cache/voice-iter/models/kokoro-82m"
speed = 1.1

[corpus]
test_corpus_path = "tests/chthonic_voice_corpus.txt"
expected_outputs_path = "tests/chthonic_voice_expected.json"  # what each line should transcribe to

[output]
manifest_dir = "manifest/voice"
audio_artifacts_dir = "manifest/voice/.audio_snapshots"
ledger_path = "manifest/voice/voice_iteration_history.ndjson"
catalog_path = "tests/voice_config_catalog.json"

[checkpoint]
retention = 20
```

## Catalog schema (voice-config-catalog.json)

Mirrors the DSL `patterns.json` shape but for voice configurations:

```json
{
  "version": 1,
  "configs": [
    {
      "name": "chthonic-parakeet-kokoro-2026-05",
      "description": "Parakeet TDT V3 + Kokoro, chthonic hotword set",
      "stt": { "provider": "parakeet", "model": "tdt-v3", "hotwords_n": 8 },
      "tts": { "provider": "kokoro", "voice": "af_bella" },
      "status": "working",
      "scores": {
        "wer_on_chthonic_corpus": 0.04,
        "tts_mos": 4.1,
        "nsfw_tolerance": "full",
        "silence_discipline": "excellent",
        "first_pass_latency_ms": 280
      },
      "since": "2026-05-27"
    }
  ]
}
```

## Test corpus (the chthonic-specific eval surface)

Generic TTS leaderboards test on neutral English prose. Our content has
specific stresses generic benchmarks miss:

1. Backtick-id pronunciation — does the voice say `The-Savant` correctly?
2. Greek letters inline — "Phase β-γ"
3. Code identifiers in spoken context — "dsl-iter check"
4. NSFW++ vocabulary — does the voice refuse, break, or sail through?
5. Long paren-dense substrate — `(MILFOLOGICAL × German BDSM × Frame-Werk)`
6. Character name disambiguation — Lysandra vs Orackla vs Umeko
7. Spec citations — "§10.3.1", "L4049"
8. Mixed-case CAS proper nouns — "FA-GHOR", "WHR:MAX", "K-CUP"

`tests/chthonic_voice_corpus.txt` carries ~50 lines covering all eight axes.
`tests/chthonic_voice_expected.json` carries the expected transcriptions for
STT eval (what we WOULD type if we said the line).

## Polyrepo workflow

```
# Per-project setup
cd <project>
voice-iter init <project-name>            # writes voice-iter.toml stub
# edit voice-iter.toml to match project (hotwords, voice, corpus paths)
voice-iter check                          # runs corpus through configured stack

# Cross-project: shared model cache (one download serves all projects)
~/.cache/voice-iter/models/               # populated once; reused across projects
```

Each project keeps its own:
- catalog (vocabulary, character names, jargon)
- corpus (project-specific eval text)
- ledger (project-specific iteration history)
- voice-iter.toml (config)

Each project shares:
- the toolkit code (one install)
- the model cache (one set of downloads)
- the methodology

## Three-loop composition with the DSL toolkit

For chthonic specifically, voice-iter + dsl-iteration-toolkit run side-by-side:

- DSL Loop A: grammar substrate work (parses the catalyst)
- DSL Loop B: dsl-iter tooling
- DSL Loop C: catalyst checkpoint discipline
- voice Loop A: voice substrate work (recognizes the catalyst's vocabulary out loud)
- voice Loop B: voice-iter tooling
- voice Loop C: voice config snapshots before swap

The two toolkits don't share code, but they share *methodology + idiom + checkpoints + ledger discipline*. The conductor learns one pattern, uses it across both surfaces, and across all projects.

## What's "outdated 2023" being modernized

| Component | 2023 stack | 2026 stack |
|---|---|---|
| STT | Whisper Large V2 | Parakeet TDT V3 (faster, better English, silence-disciplined) |
| TTS | Tacotron 2 / Bark | Kokoro 82M (default) / Fish Speech S1 (quality tier) |
| Transport | custom WebSockets | MCP (Anthropic protocol, multi-client ecosystem) |
| Activation | wake-word ("Hey Siri") | push-to-talk via Claude Code surface OR continuous mode with VAD |
| Latency | 800-2000ms typical | 280-500ms with local Parakeet + Kokoro on RTX 4090 |

The boxing arena is the same (catalyst + conductor + workflow). The modernization
is in WHICH tools occupy each slot. The methodology carries forward.

## Build sequence (concrete)

1. ✅ Scaffold (this commit) — directory structure, configs, architecture doc, test corpus
2. ⏳ Install Parakeet TDT V3 + Kokoro models to `~/.cache/voice-iter/models/`
3. ⏳ Implement `voice-iter check` — runs corpus through stack, scores STT WER + TTS quality + latency
4. ⏳ Wire as MCP server so Claude Code can invoke it
5. ⏳ Iterate: catalog grows with each project; coverage tightens; ledger accumulates
6. ⏳ Roll to second project (e.g., PsychoNoir-Kontrapunkt) — validates the polyrepo design

Each step commits separately. Each step can be reverted via Loop C analog
(model + config snapshots).
