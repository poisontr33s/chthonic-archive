# Poe Transport Audit

- Generated: `2026-05-04T05:24:35Z`
- Control model: `claude-sonnet-4.5`
- Target bot: `app-creator`
- OpenAI max tokens: `1`
- Recommendation: `openai-compatible`
- Rationale: `Both lanes can access App-Creator; OpenAI-compatible is better for portability.`

## Accounts
- Account `1`
  - OpenAI control: `subscription_required`
  - OpenAI app-creator: `subscription_required`
  - SDK control: `subscription_required`
  - SDK app-creator: `subscription_required`
  - OpenAI model count inspected: `382`
  - OpenAI has app-creator id: `False`
- Account `2`
  - OpenAI control: `callable`
  - OpenAI app-creator: `callable`
  - SDK control: `callable`
  - SDK app-creator: `callable`
  - OpenAI model count inspected: `382`
  - OpenAI has app-creator id: `False`
