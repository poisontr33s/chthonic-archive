"""voice-iter.toml schema."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


class TransportConfig(BaseModel):
    type: Literal["mcp", "stdio", "websocket"] = "mcp"
    mcp_name: str = "voice-iter"


class STTConfig(BaseModel):
    provider: Literal["parakeet", "whisper", "moonshine"] = "parakeet"
    model_path: str = "~/.cache/voice-iter/models/parakeet-tdt-v3"
    language: str = "en"
    silence_threshold_db: float = -50.0
    hotwords: list[str] = Field(default_factory=list)


class TTSConfig(BaseModel):
    provider: Literal["kokoro", "fish_speech", "openai"] = "kokoro"
    voice: str = "af_bella"
    model_path: str = "~/.cache/voice-iter/models/kokoro-82m"
    speed: float = 1.1


class CorpusConfig(BaseModel):
    test_corpus_path: str = "tests/voice_corpus.txt"
    expected_outputs_path: str | None = None


class OutputConfig(BaseModel):
    manifest_dir: str = "manifest/voice"
    audio_artifacts_dir: str = "manifest/voice/.audio_snapshots"
    ledger_path: str = "manifest/voice/voice_iteration_history.ndjson"
    catalog_path: str = "tests/voice_config_catalog.json"


class CheckpointConfig(BaseModel):
    retention: int = 20


class VoiceIterConfig(BaseModel):
    project_name: str
    transport: TransportConfig = Field(default_factory=TransportConfig)
    stt: STTConfig = Field(default_factory=STTConfig)
    tts: TTSConfig = Field(default_factory=TTSConfig)
    corpus: CorpusConfig = Field(default_factory=CorpusConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    checkpoint: CheckpointConfig = Field(default_factory=CheckpointConfig)

    @classmethod
    def load(cls, path: str | Path) -> "VoiceIterConfig":
        p = Path(path)
        with p.open("rb") as f:
            data = tomllib.load(f)
        return cls(**data)

    @classmethod
    def template(cls, project_name: str) -> "VoiceIterConfig":
        return cls(project_name=project_name)
