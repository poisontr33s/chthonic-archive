# Poe API Dual Discrepancy

- Generated: `2026-03-05T21:46:21Z`
- Preferred account for calls: `1`

## Balance Ranking
- Account `1`: balance=`3000` error=`None`
- Account `2`: balance=`3000` error=`None`

## Account Summaries
- Account `1`
  - entitlement_verdict=`api_access_blocked_by_subscription_or_points`
  - callable_count=`0`
  - counts_by_best_status=`{'subscription_required': 1}`
  - targeted_model_statuses=`{'qwen3.5-397b-a17b-t': 'callable', 'app-creator': 'subscription_required'}`
- Account `2`
  - entitlement_verdict=`api_access_blocked_by_subscription_or_points`
  - callable_count=`0`
  - counts_by_best_status=`{'subscription_required': 1}`
  - targeted_model_statuses=`{'qwen3.5-397b-a17b-t': 'callable', 'app-creator': 'subscription_required'}`

## Callable Overlap
- shared_callable_models: `[]`
- unique_callable_by_account: `{'1': [], '2': []}`

## Status Discrepancies
- delta_count: `0`

## Inference
- Higher point balance only matters when statuses include `insufficient_fund`; subscription-gated models remain blocked regardless of balance.
- No model-level status deltas detected across tested accounts in this run.

## Rerun Commands
- `uv run scripts/poe_transport_audit.py --registry --registry-account 1 --registry-limit 1 --registry-transports openai,sdk --sdk-probe-limit 1 --openai-max-tokens 1 --prompt 'Return exactly: OK' --json`
- `uv run scripts/poe_transport_audit.py --registry --registry-account 1 --registry-models qwen3.5-397b-a17b-t,app-creator --registry-transports openai,sdk --sdk-probe-limit 0 --openai-max-tokens 1 --prompt 'Return exactly: OK' --json`
- `uv run scripts/poe_transport_audit.py --registry --registry-account 2 --registry-limit 1 --registry-transports openai,sdk --sdk-probe-limit 1 --openai-max-tokens 1 --prompt 'Return exactly: OK' --json`
- `uv run scripts/poe_transport_audit.py --registry --registry-account 2 --registry-models qwen3.5-397b-a17b-t,app-creator --registry-transports openai,sdk --sdk-probe-limit 0 --openai-max-tokens 1 --prompt 'Return exactly: OK' --json`
- `uv run scripts/poe_api_setup_pull.py --dual-discrepancy --accounts 1,2 --registry-limit 1 --sdk-probe-limit 1 --openai-max-tokens 1 --targeted-models qwen3.5-397b-a17b-t,app-creator --prompt 'Return exactly: OK'`

## Sources
- External application guide: `https://creator.poe.com/docs/external-applications/external-application-guide`
- OpenAI-compatible API limitations: `https://creator.poe.com/docs/external-applications/openai-compatible-api`
- Interface configuration prerequisites: `https://creator.poe.com/docs/external-applications/interface-configuration`
- ListModels API reference: `https://creator.poe.com/api-reference/listModels`
- Official model catalog context: `https://poe.com/explore?category=Official`
