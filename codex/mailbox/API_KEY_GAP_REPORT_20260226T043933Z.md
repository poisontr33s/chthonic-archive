# API Key Gap Report

- Generated (UTC): 2026-02-26T04:39:33.3467233Z
- Total keys checked: `17`
- Available: `6`
- Missing: `11`
- Missing required: `0`
- Missing optional: `11`
- Providers with any key: `1/1`
- Registry path: `C:\Users\erdno\chthonic-archive\docs\standards\API_PROVIDER_REGISTRY.json`

## Key Matrix

| Key | Provider | Required | Available | Auth Mode | OAuth Alt | IaC | Source | In Pool | In Process | In User Env | Acquire URL |
|---|---|---:|---:|---|---:|---|---|---:|---:|---:|---|
| GITHUB_TOKEN | GitHub | True | True | api_key | False | high | pool | True | False | True | https://github.com/settings/tokens |
| POE_API_KEY | Poe | True | True | api_key | False | medium | pool | True | False | True | https://poe.com/api_key |
| POE_API_KEY_1 | Poe | True | True | api_key | False | medium | pool | True | False | True | https://poe.com/api_key |
| POE_API_KEY_2 | Poe | True | True | api_key | False | medium | pool | True | False | True | https://poe.com/api_key |
| HUGGINGFACE_HUB_TOKEN | Hugging Face | True | True | api_key | False | high | pool | True | True | True | https://huggingface.co/settings/tokens |
| HF_TOKEN | Hugging Face | False | True | api_key | False | high | process_env | False | True | True | https://huggingface.co/settings/tokens |
| OPENAI_API_KEY | OpenAI | False | False | api_key | True | high | none | False | False | False | https://platform.openai.com/api-keys |
| GEMINI_API_KEY | Google AI Studio | False | False | api_key|oauth | True | high | none | False | False | False | https://aistudio.google.com/apikey |
| ANTHROPIC_API_KEY | Anthropic | False | False | api_key | False | high | none | False | False | False | https://docs.anthropic.com/en/api/getting-started |
| OPENROUTER_API_KEY | OpenRouter | False | False | api_key|oauth | True | high | none | False | False | False | https://openrouter.ai/docs/api-keys |
| GROQ_API_KEY | Groq | False | False | api_key | False | medium | none | False | False | False | https://console.groq.com/keys |
| TOGETHER_API_KEY | Together | False | False | api_key | False | medium | none | False | False | False | https://docs.together.ai/reference/authentication-1 |
| FIREWORKS_API_KEY | Fireworks AI | False | False | api_key | False | high | none | False | False | False | https://docs.fireworks.ai/getting-started/onboarding |
| REPLICATE_API_TOKEN | Replicate | False | False | api_key | False | medium | none | False | False | False | https://replicate.com/account/api-tokens |
| COHERE_API_KEY | Cohere | False | False | api_key | False | medium | none | False | False | False | https://dashboard.cohere.com/api-keys |
| PINECONE_API_KEY | Pinecone | False | False | api_key | False | high | none | False | False | False | https://docs.pinecone.io/guides/projects/manage-api-keys |
| TAVILY_API_KEY | Tavily | False | False | api_key | False | medium | none | False | False | False | https://docs.tavily.com/api-reference/introduction |

## Missing Required Keys
- None.

## IaC-Weighted Acquisition Queue (Required First)
1. ANTHROPIC_API_KEY (Anthropic, required=False, IaC=high) -> https://docs.anthropic.com/en/api/getting-started
   - Acquire when needed; IaC automation is straightforward.
1. FIREWORKS_API_KEY (Fireworks AI, required=False, IaC=high) -> https://docs.fireworks.ai/getting-started/onboarding
   - Acquire when needed; IaC automation is straightforward.
1. GEMINI_API_KEY (Google AI Studio, required=False, IaC=high) -> https://aistudio.google.com/apikey
   - OAuth-supported lane available; mint only if direct API lane is needed.
1. OPENAI_API_KEY (OpenAI, required=False, IaC=high) -> https://platform.openai.com/api-keys
   - OAuth-supported lane available; mint only if direct API lane is needed.
1. OPENROUTER_API_KEY (OpenRouter, required=False, IaC=high) -> https://openrouter.ai/docs/api-keys
   - OAuth-supported lane available; mint only if direct API lane is needed.
1. PINECONE_API_KEY (Pinecone, required=False, IaC=high) -> https://docs.pinecone.io/guides/projects/manage-api-keys
   - Acquire when needed; IaC automation is straightforward.
1. COHERE_API_KEY (Cohere, required=False, IaC=medium) -> https://dashboard.cohere.com/api-keys
   - Acquire manually, then automate distribution and rotation.
1. GROQ_API_KEY (Groq, required=False, IaC=medium) -> https://console.groq.com/keys
   - Acquire manually, then automate distribution and rotation.
1. REPLICATE_API_TOKEN (Replicate, required=False, IaC=medium) -> https://replicate.com/account/api-tokens
   - Acquire manually, then automate distribution and rotation.
1. TAVILY_API_KEY (Tavily, required=False, IaC=medium) -> https://docs.tavily.com/api-reference/introduction
   - Acquire manually, then automate distribution and rotation.
1. TOGETHER_API_KEY (Together, required=False, IaC=medium) -> https://docs.together.ai/reference/authentication-1
   - Acquire manually, then automate distribution and rotation.

## Provider Coverage

| Provider | Total Keys | Available | Missing | Has Any Key |
|---|---:|---:|---:|---:|
|  | 17 | 6 | 11 | True |
