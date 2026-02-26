# Poe API Dual Discrepancy

- Generated: `2026-02-25T19:17:05Z`
- Preferred account for calls: `1`

## Balance Ranking
- Account `1`: balance=`3000` error=`None`
- Account `2`: balance=`1722` error=`None`

## Account Summaries
- Account `1`
  - entitlement_verdict=`highly_restricted_api_entitlement`
  - callable_count=`1`
  - counts_by_best_status=`{'callable': 1, 'subscription_required': 336, 'unknown_error': 1}`
  - targeted_model_statuses=`{'qwen3.5-397b-a17b-t': 'callable', 'app-creator': 'subscription_required', 'script-bot-creator': 'subscription_required'}`
- Account `2`
  - entitlement_verdict=`highly_restricted_api_entitlement`
  - callable_count=`1`
  - counts_by_best_status=`{'callable': 1, 'subscription_required': 337}`
  - targeted_model_statuses=`{'qwen3.5-397b-a17b-t': 'callable', 'app-creator': 'subscription_required', 'script-bot-creator': 'subscription_required'}`

## Callable Overlap
- shared_callable_models: `['qwen3.5-397b-a17b-t']`
- unique_callable_by_account: `{'1': [], '2': []}`

## Status Discrepancies
- delta_count: `1`

## Inference
- Higher point balance only matters when statuses include `insufficient_fund`; subscription-gated models remain blocked regardless of balance.
- Found 1 model status deltas across accounts; review `status_discrepancies.deltas` for account-specific access drift.

## Rerun Commands
- `uv run scripts/poe_transport_audit.py --registry --registry-account 1 --registry-limit 338 --registry-transports openai,sdk --sdk-probe-limit 15 --openai-max-tokens 1 --prompt 'Return exactly: OK' --json`
- `uv run scripts/poe_transport_audit.py --registry --registry-account 1 --registry-models qwen3.5-397b-a17b-t,app-creator,script-bot-creator --registry-transports openai,sdk --sdk-probe-limit 0 --openai-max-tokens 1 --prompt 'Return exactly: OK' --json`
- `uv run scripts/poe_transport_audit.py --registry --registry-account 2 --registry-limit 338 --registry-transports openai,sdk --sdk-probe-limit 15 --openai-max-tokens 1 --prompt 'Return exactly: OK' --json`
- `uv run scripts/poe_transport_audit.py --registry --registry-account 2 --registry-models qwen3.5-397b-a17b-t,app-creator,script-bot-creator --registry-transports openai,sdk --sdk-probe-limit 0 --openai-max-tokens 1 --prompt 'Return exactly: OK' --json`
- `uv run scripts/poe_api_setup_pull.py --dual-discrepancy --accounts 1,2 --registry-limit 338 --sdk-probe-limit 15 --openai-max-tokens 1 --targeted-models qwen3.5-397b-a17b-t,app-creator,script-bot-creator --prompt 'Return exactly: OK'`

## Sources
- External application guide: `https://creator.poe.com/docs/external-applications/external-application-guide`
- OpenAI-compatible API limitations: `https://creator.poe.com/docs/external-applications/openai-compatible-api`
- Interface configuration prerequisites: `https://creator.poe.com/docs/external-applications/interface-configuration`
- ListModels API reference: `https://creator.poe.com/api-reference/listModels`
- Official model catalog context: `https://poe.com/explore?category=Official`
