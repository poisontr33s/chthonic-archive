"""
tabby-modern settings — Pydantic Settings primary, env-first.
Config priority (highest to lowest): env vars → YAML file overlay → defaults.
No ruamel.yaml. No argparse wizard. Python objects are the contract.
"""

from __future__ import annotations

import os
import pathlib
from typing import Annotated, Literal, Optional, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# --- Type aliases ---

CacheMode = Union[
    Literal["FP16", "Q8", "Q6", "Q4"],
    str,  # exllamav3 k_bits,v_bits format e.g. "8,8"
]


# --- Sub-models ---

class NetworkSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TABBY_NETWORK_")

    host: str = Field("127.0.0.1", description="Bind host. Use 0.0.0.0 in container.")
    port: int = Field(5000, ge=1, le=65535)
    disable_auth: bool = Field(False)


class ModelSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TABBY_MODEL_")

    model_dir: pathlib.Path = Field(
        pathlib.Path("models"),
        description="Directory containing model files. Container: /models (CDI mount).",
    )
    # exllamav3 only — exllamav2 path is container-layer (G4 Linux admitted_L2_source_linux)
    # No backend selection enum needed — this service is exllamav3-native.
    model_name: Optional[str] = Field(None, description="Model subdirectory to load on startup.")

    cache_mode: CacheMode = Field(
        "FP16",
        description=(
            "KV cache precision. FP16 baseline for RTX 4090 (24 GB VRAM). "
            "exllamav3: k_bits,v_bits string (e.g. '8,8') or FP16/Q8/Q6/Q4."
        ),
    )
    max_seq_len: Optional[int] = Field(
        None,
        description="Max sequence length. None = derive from model config.json.",
    )
    cache_size: Optional[Annotated[int, Field(multiple_of=256)]] = Field(
        None,
        description="KV cache token allocation. Must be multiple of 256. None = 4096.",
    )
    output_chunking: bool = Field(
        True,
        description="EXL3: allocate cache in chunks instead of upfront (VRAM efficiency).",
    )
    chunk_size: int = Field(
        2048,
        ge=128,
        le=8192,
        description="Prompt ingestion chunk size. Sweet spot for Ada Lovelace: 2048.",
    )
    gpu_split_auto: bool = Field(True)
    autosplit_reserve: list[int] = Field(
        [96],
        description="VRAM reserved for autosplit (MB per GPU). Single RTX 4090: [96].",
    )
    max_batch_size: Optional[int] = Field(
        None,
        description="Max concurrent prompts. None = automatic (Ampere+ only).",
    )

    @field_validator("cache_size", mode="before")
    @classmethod
    def _validate_cache_size(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v % 256 != 0:
            raise ValueError(f"cache_size must be a multiple of 256, got {v}")
        return v


class LoggingSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TABBY_LOG_")

    log_prompt: bool = False
    log_generation_params: bool = False
    log_requests: bool = False


# --- Root settings ---

class Settings(BaseSettings):
    """
    tabby-modern root configuration.

    Config resolution order (highest priority wins):
      1. Environment variables (TABBY_* prefix, mapped to nested fields)
      2. YAML overlay file (TABBY_CONFIG_FILE env var, default: config.yml if present)
      3. Pydantic field defaults

    Container deployment pattern:
      ENV TABBY_MODEL_MODEL_DIR=/models
      ENV TABBY_NETWORK_HOST=0.0.0.0
      ENV TABBY_MODEL_MODEL_NAME=my-model-dir
    """

    model_config = SettingsConfigDict(
        env_prefix="TABBY_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    network: NetworkSettings = Field(default_factory=NetworkSettings)
    model: ModelSettings = Field(default_factory=ModelSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)

    @classmethod
    def from_env(cls) -> "Settings":
        """Primary constructor — reads env vars + optional YAML overlay."""
        cfg_file = os.environ.get("TABBY_CONFIG_FILE", "config.yml")
        path = pathlib.Path(cfg_file)
        if path.exists():
            return cls._from_yaml_overlay(path)
        return cls()

    @classmethod
    def _from_yaml_overlay(cls, path: pathlib.Path) -> "Settings":
        """Load base settings then overlay YAML file values (non-None only)."""
        try:
            import yaml  # PyYAML — available via uvicorn[standard] deps
        except ImportError:
            from loguru import logger
            logger.warning(f"PyYAML not available — skipping YAML overlay from {path}")
            return cls()

        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        # Flatten nested dict into env-style keys for pydantic-settings
        flat: dict[str, object] = {}
        for section, values in raw.items():
            if isinstance(values, dict):
                for k, v in values.items():
                    if v is not None:
                        flat[f"TABBY_{section.upper()}__{k.upper()}"] = str(v)
        for k, v in flat.items():
            if k not in os.environ:
                os.environ[k] = v
        return cls()


# Module-level singleton — populated at server startup via Settings.from_env()
settings: Settings = Settings()
