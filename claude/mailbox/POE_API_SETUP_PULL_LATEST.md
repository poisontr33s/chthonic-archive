# Poe API Setup Pull

- Generated: `2026-02-25T19:04:43Z`
- Account: `1`
- OpenAI max tokens: `1`
- Registry limit: `338`
- SDK probe limit: `15`
- Prompt: `Return exactly: OK`
- Targeted models: `qwen3.5-397b-a17b-t, app-creator, script-bot-creator`

## Catalog Scope
- API model count: `338`
- Free-like pricing entries: `186`
- Priced entries: `152`

## Entitlement Verdict
- `highly_restricted_api_entitlement`

## Mismatch Explanation
- Poe Explore UI can show far more bots than the API model list (`/v1/models` currently reports 338).
- Model visibility in `/v1/models` does not guarantee your key can invoke that model.
- Your effective key entitlement is inferred from live probe statuses, not catalog count.

## Docs Alignment
- Base URL: `https://api.poe.com/v1`
- OpenAI-compatible endpoints: `/chat/completions, /responses`
- Poe SDK path: `fastapi-poe`
- API access caveat: `Model visibility in catalog does not guarantee API invocation entitlement (subscription/points gates apply).`
- Known limitations: `App-Creator and Script-Bot-Creator are documented as unavailable via OpenAI-compatible endpoint/Poe Python library.`
- UI/API scope note: `Poe UI catalogs community bots; API exposes a smaller, entitlement-gated model list.`

## Registry Summary
- total_models: `338`
- counts_by_best_status: `{'callable': 1, 'subscription_required': 337}`
- cheapest_callable: `['qwen3.5-397b-a17b-t']`

## Targeted Summary
- counts_by_best_status: `{'callable': 1, 'subscription_required': 2}`
- model_statuses: `{'qwen3.5-397b-a17b-t': 'callable', 'app-creator': 'subscription_required', 'script-bot-creator': 'subscription_required'}`

## Rerun Commands
- `uv run scripts/poe_transport_audit.py --registry --registry-account 1 --registry-limit 338 --registry-transports openai,sdk --sdk-probe-limit 15 --openai-max-tokens 1 --prompt 'Return exactly: OK' --json`
- `uv run scripts/poe_transport_audit.py --registry --registry-account 1 --registry-models qwen3.5-397b-a17b-t,app-creator,script-bot-creator --registry-transports openai,sdk --sdk-probe-limit 0 --openai-max-tokens 1 --prompt 'Return exactly: OK' --json`

## Sources
- External application guide: `https://creator.poe.com/docs/external-applications/external-application-guide`
- OpenAI-compatible API limitations: `https://creator.poe.com/docs/external-applications/openai-compatible-api`
- Interface configuration prerequisites: `https://creator.poe.com/docs/external-applications/interface-configuration`
- ListModels API reference: `https://creator.poe.com/api-reference/listModels`
- Official model catalog context: `https://poe.com/explore?category=Official`
