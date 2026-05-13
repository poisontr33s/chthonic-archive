---
sid: FORGE_ENVIRONMENT_MAP_V1
title: Recovered Environment Integration Map
created: 2026-03-05T19:27:19+00:00
source_files: ["claude-codex-gemini/session_resumption_pickup/UNCENSORED_LANE_RUNTIME_20260219_231721.env", "claude-codex-gemini/session_resumption_pickup/UNCENSORED_LANE_RUNTIME_LATEST.env", "codex/mailbox/API_KEY_ENV_TEMPLATE_20260226T045112Z.env", "mas_mcp/frontend/.env"]
pathway: env -> service hint extraction -> integration map
kept: Variable names, sample shapes, and secret/config classification.
discarded: Concrete secret values.
---
# Recovered Environment Integration Map

- `ANTHROPIC_API_KEY` | type `string` | secret `True` | sources: `codex/mailbox/API_KEY_ENV_TEMPLATE_20260226T045112Z.env`
- `ASSEMBLYAI_API_KEY` | type `string` | secret `True` | sources: `codex/mailbox/API_KEY_ENV_TEMPLATE_20260226T045112Z.env`
- `AZURE_OPENAI_API_KEY` | type `string` | secret `True` | sources: `codex/mailbox/API_KEY_ENV_TEMPLATE_20260226T045112Z.env`
- `BRAVE_SEARCH_API_KEY` | type `string` | secret `True` | sources: `codex/mailbox/API_KEY_ENV_TEMPLATE_20260226T045112Z.env`
- `CEREBRAS_API_KEY` | type `string` | secret `True` | sources: `codex/mailbox/API_KEY_ENV_TEMPLATE_20260226T045112Z.env`
- `CHTHONIC_LLM_BASE_URL` | type `string` | secret `False` | sources: [`claude-codex-gemini/session_resumption_pickup/UNCENSORED_LANE_RUNTIME_20260219_231721.env`](../../../../claude-codex-gemini/session_resumption_pickup/UNCENSORED_LANE_RUNTIME_20260219_231721.env), [`claude-codex-gemini/session_resumption_pickup/UNCENSORED_LANE_RUNTIME_LATEST.env`](../../../../claude-codex-gemini/session_resumption_pickup/UNCENSORED_LANE_RUNTIME_LATEST.env)
- `CHTHONIC_LLM_CODE_MODEL_PATH` | type `string` | secret `False` | sources: [`claude-codex-gemini/session_resumption_pickup/UNCENSORED_LANE_RUNTIME_20260219_231721.env`](../../../../claude-codex-gemini/session_resumption_pickup/UNCENSORED_LANE_RUNTIME_20260219_231721.env), [`claude-codex-gemini/session_resumption_pickup/UNCENSORED_LANE_RUNTIME_LATEST.env`](../../../../claude-codex-gemini/session_resumption_pickup/UNCENSORED_LANE_RUNTIME_LATEST.env)
- `CHTHONIC_LLM_DEFAULT_LANE` | type `string` | secret `False` | sources: [`claude-codex-gemini/session_resumption_pickup/UNCENSORED_LANE_RUNTIME_20260219_231721.env`](../../../../claude-codex-gemini/session_resumption_pickup/UNCENSORED_LANE_RUNTIME_20260219_231721.env), [`claude-codex-gemini/session_resumption_pickup/UNCENSORED_LANE_RUNTIME_LATEST.env`](../../../../claude-codex-gemini/session_resumption_pickup/UNCENSORED_LANE_RUNTIME_LATEST.env)
- `CHTHONIC_LLM_DEFAULT_MODEL_PATH` | type `string` | secret `False` | sources: [`claude-codex-gemini/session_resumption_pickup/UNCENSORED_LANE_RUNTIME_20260219_231721.env`](../../../../claude-codex-gemini/session_resumption_pickup/UNCENSORED_LANE_RUNTIME_20260219_231721.env), [`claude-codex-gemini/session_resumption_pickup/UNCENSORED_LANE_RUNTIME_LATEST.env`](../../../../claude-codex-gemini/session_resumption_pickup/UNCENSORED_LANE_RUNTIME_LATEST.env)
- `CHTHONIC_LLM_STRICT_JSON_MODEL_PATH` | type `string` | secret `False` | sources: [`claude-codex-gemini/session_resumption_pickup/UNCENSORED_LANE_RUNTIME_20260219_231721.env`](../../../../claude-codex-gemini/session_resumption_pickup/UNCENSORED_LANE_RUNTIME_20260219_231721.env), [`claude-codex-gemini/session_resumption_pickup/UNCENSORED_LANE_RUNTIME_LATEST.env`](../../../../claude-codex-gemini/session_resumption_pickup/UNCENSORED_LANE_RUNTIME_LATEST.env)
- `CHTHONIC_LLM_UNRESTRICTED_MODEL_PATH` | type `string` | secret `False` | sources: [`claude-codex-gemini/session_resumption_pickup/UNCENSORED_LANE_RUNTIME_20260219_231721.env`](../../../../claude-codex-gemini/session_resumption_pickup/UNCENSORED_LANE_RUNTIME_20260219_231721.env), [`claude-codex-gemini/session_resumption_pickup/UNCENSORED_LANE_RUNTIME_LATEST.env`](../../../../claude-codex-gemini/session_resumption_pickup/UNCENSORED_LANE_RUNTIME_LATEST.env)
- `COHERE_API_KEY` | type `string` | secret `True` | sources: `codex/mailbox/API_KEY_ENV_TEMPLATE_20260226T045112Z.env`
- `DEEPSEEK_API_KEY` | type `string` | secret `True` | sources: `codex/mailbox/API_KEY_ENV_TEMPLATE_20260226T045112Z.env`
- `ELEVENLABS_API_KEY` | type `string` | secret `True` | sources: `codex/mailbox/API_KEY_ENV_TEMPLATE_20260226T045112Z.env`
- `ENTITY_REGISTRY_PATH` | type `string` | secret `False` | sources: [`mas_mcp/frontend/.env`](../../../../mas_mcp/frontend/.env)
- `EXA_API_KEY` | type `string` | secret `True` | sources: `codex/mailbox/API_KEY_ENV_TEMPLATE_20260226T045112Z.env`
- `FIREWORKS_API_KEY` | type `string` | secret `True` | sources: `codex/mailbox/API_KEY_ENV_TEMPLATE_20260226T045112Z.env`
- `GEMINI_API_KEY` | type `string` | secret `True` | sources: `codex/mailbox/API_KEY_ENV_TEMPLATE_20260226T045112Z.env`
- `GENESIS_ARTIFACTS_DIR` | type `string` | secret `False` | sources: [`mas_mcp/frontend/.env`](../../../../mas_mcp/frontend/.env)
- `GENESIS_GPU_PROVIDER` | type `string` | secret `False` | sources: [`mas_mcp/frontend/.env`](../../../../mas_mcp/frontend/.env)
- `GENESIS_LOGS_DIR` | type `string` | secret `False` | sources: [`mas_mcp/frontend/.env`](../../../../mas_mcp/frontend/.env)
- `GROQ_API_KEY` | type `string` | secret `True` | sources: `codex/mailbox/API_KEY_ENV_TEMPLATE_20260226T045112Z.env`
- `HOST` | type `string` | secret `False` | sources: [`mas_mcp/frontend/.env`](../../../../mas_mcp/frontend/.env)
- `LANGSMITH_API_KEY` | type `string` | secret `True` | sources: `codex/mailbox/API_KEY_ENV_TEMPLATE_20260226T045112Z.env`
- `MISTRAL_API_KEY` | type `string` | secret `True` | sources: `codex/mailbox/API_KEY_ENV_TEMPLATE_20260226T045112Z.env`
- `OPENAI_API_KEY` | type `string` | secret `True` | sources: `codex/mailbox/API_KEY_ENV_TEMPLATE_20260226T045112Z.env`
- `OPENROUTER_API_KEY` | type `string` | secret `True` | sources: `codex/mailbox/API_KEY_ENV_TEMPLATE_20260226T045112Z.env`
- `PERPLEXITY_API_KEY` | type `string` | secret `True` | sources: `codex/mailbox/API_KEY_ENV_TEMPLATE_20260226T045112Z.env`
- `PINECONE_API_KEY` | type `string` | secret `True` | sources: `codex/mailbox/API_KEY_ENV_TEMPLATE_20260226T045112Z.env`
- `PORT` | type `integer` | secret `False` | sources: [`mas_mcp/frontend/.env`](../../../../mas_mcp/frontend/.env)
- `REPLICATE_API_TOKEN` | type `string` | secret `True` | sources: `codex/mailbox/API_KEY_ENV_TEMPLATE_20260226T045112Z.env`
- `SERPAPI_API_KEY` | type `string` | secret `True` | sources: `codex/mailbox/API_KEY_ENV_TEMPLATE_20260226T045112Z.env`
- `SLO_ACCEPTANCE_RATE` | type `string` | secret `False` | sources: [`mas_mcp/frontend/.env`](../../../../mas_mcp/frontend/.env)
- `SLO_P50_LATENCY_MS` | type `integer` | secret `False` | sources: [`mas_mcp/frontend/.env`](../../../../mas_mcp/frontend/.env)
- `SLO_P95_LATENCY_MS` | type `integer` | secret `False` | sources: [`mas_mcp/frontend/.env`](../../../../mas_mcp/frontend/.env)
- `SLO_VRAM_PCT` | type `integer` | secret `False` | sources: [`mas_mcp/frontend/.env`](../../../../mas_mcp/frontend/.env)
- `TAVILY_API_KEY` | type `string` | secret `True` | sources: `codex/mailbox/API_KEY_ENV_TEMPLATE_20260226T045112Z.env`
- `TOGETHER_API_KEY` | type `string` | secret `True` | sources: `codex/mailbox/API_KEY_ENV_TEMPLATE_20260226T045112Z.env`
- `VOYAGE_API_KEY` | type `string` | secret `True` | sources: `codex/mailbox/API_KEY_ENV_TEMPLATE_20260226T045112Z.env`
- `XAI_API_KEY` | type `string` | secret `True` | sources: `codex/mailbox/API_KEY_ENV_TEMPLATE_20260226T045112Z.env`
