# Poe Transport Audit

- Generated: `2026-02-23T17:01:16Z`
- Control model: `claude-sonnet-4.5`
- Target bot: `app-creator`
- Recommendation: `openai-compatible`
- Rationale: `Both lanes work for control probes, but App-Creator is not API-accessible on tested keys.`

## Accounts
- Account `1`
  - OpenAI control ok: `True`
  - OpenAI app-creator ok: `False`
  - SDK control ok: `True`
  - SDK app-creator ok: `False`
  - OpenAI model count inspected: `333`
  - OpenAI has app-creator id: `False`
- Account `2`
  - OpenAI control ok: `True`
  - OpenAI app-creator ok: `False`
  - SDK control ok: `False`
  - SDK app-creator ok: `False`
  - OpenAI model count inspected: `333`
  - OpenAI has app-creator id: `False`
