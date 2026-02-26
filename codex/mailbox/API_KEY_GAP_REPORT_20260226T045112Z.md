# API Key Gap Report

- Generated (UTC): 2026-02-26T04:51:12.2573797Z
- Total keys checked: `30`
- Available: `6`
- Missing: `24`
- Missing required: `0`
- Missing optional: `24`
- Providers with any key: `3/27`
- Registry path: `C:\Users\erdno\chthonic-archive\docs\standards\API_PROVIDER_REGISTRY.json`
- Env template: `C:\Users\erdno\chthonic-archive\codex\mailbox\API_KEY_ENV_TEMPLATE_20260226T045112Z.env`

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
| GEMINI_API_KEY | Google AI Studio | False | False | api_key\|oauth | True | high | none | False | False | False | https://aistudio.google.com/apikey |
| ANTHROPIC_API_KEY | Anthropic | False | False | api_key | False | high | none | False | False | False | https://docs.anthropic.com/en/api/getting-started |
| OPENROUTER_API_KEY | OpenRouter | False | False | api_key\|oauth | True | high | none | False | False | False | https://openrouter.ai/docs/api-keys |
| GROQ_API_KEY | Groq | False | False | api_key | False | medium | none | False | False | False | https://console.groq.com/keys |
| TOGETHER_API_KEY | Together | False | False | api_key | False | medium | none | False | False | False | https://docs.together.ai/reference/authentication-1 |
| FIREWORKS_API_KEY | Fireworks AI | False | False | api_key | False | high | none | False | False | False | https://docs.fireworks.ai/getting-started/onboarding |
| REPLICATE_API_TOKEN | Replicate | False | False | api_key | False | medium | none | False | False | False | https://replicate.com/account/api-tokens |
| COHERE_API_KEY | Cohere | False | False | api_key | False | medium | none | False | False | False | https://dashboard.cohere.com/api-keys |
| PINECONE_API_KEY | Pinecone | False | False | api_key | False | high | none | False | False | False | https://docs.pinecone.io/guides/projects/manage-api-keys |
| TAVILY_API_KEY | Tavily | False | False | api_key | False | medium | none | False | False | False | https://docs.tavily.com/api-reference/introduction |
| MISTRAL_API_KEY | Mistral | False | False | api_key | False | high | none | False | False | False | https://docs.mistral.ai/getting-started/quickstart/ |
| PERPLEXITY_API_KEY | Perplexity | False | False | api_key | False | medium | none | False | False | False | https://docs.perplexity.ai/guides/getting-started |
| XAI_API_KEY | xAI | False | False | api_key | False | medium | none | False | False | False | https://docs.x.ai/docs/overview |
| DEEPSEEK_API_KEY | DeepSeek | False | False | api_key | False | medium | none | False | False | False | https://api-docs.deepseek.com/ |
| AZURE_OPENAI_API_KEY | Azure OpenAI | False | False | api_key\|aad_oauth | True | high | none | False | False | False | https://learn.microsoft.com/azure/ai-services/openai/ |
| VOYAGE_API_KEY | Voyage AI | False | False | api_key | False | high | none | False | False | False | https://docs.voyageai.com/docs/api-key-and-installation |
| EXA_API_KEY | Exa | False | False | api_key | False | medium | none | False | False | False | https://docs.exa.ai/reference/authentication |
| BRAVE_SEARCH_API_KEY | Brave Search | False | False | api_key | False | medium | none | False | False | False | https://api.search.brave.com/app/keys |
| SERPAPI_API_KEY | SerpAPI | False | False | api_key | False | high | none | False | False | False | https://serpapi.com/manage-api-key |
| ELEVENLABS_API_KEY | ElevenLabs | False | False | api_key | False | medium | none | False | False | False | https://elevenlabs.io/docs/api-reference/authentication |
| ASSEMBLYAI_API_KEY | AssemblyAI | False | False | api_key | False | medium | none | False | False | False | https://www.assemblyai.com/docs/getting-started |
| CEREBRAS_API_KEY | Cerebras | False | False | api_key | False | medium | none | False | False | False | https://inference-docs.cerebras.ai/introduction |
| LANGSMITH_API_KEY | LangSmith | False | False | api_key | False | high | none | False | False | False | https://docs.langchain.com/langsmith/create-account-api-key |

## Missing Required Keys
- None.

## IaC-Weighted Acquisition Queue (Required First)
1. ANTHROPIC_API_KEY (Anthropic, required=False, IaC=high) -> https://docs.anthropic.com/en/api/getting-started
   - Acquire when needed; IaC automation is straightforward.
1. AZURE_OPENAI_API_KEY (Azure OpenAI, required=False, IaC=high) -> https://learn.microsoft.com/azure/ai-services/openai/
   - OAuth-supported lane available; mint only if direct API lane is needed.
1. FIREWORKS_API_KEY (Fireworks AI, required=False, IaC=high) -> https://docs.fireworks.ai/getting-started/onboarding
   - Acquire when needed; IaC automation is straightforward.
1. GEMINI_API_KEY (Google AI Studio, required=False, IaC=high) -> https://aistudio.google.com/apikey
   - OAuth-supported lane available; mint only if direct API lane is needed.
1. LANGSMITH_API_KEY (LangSmith, required=False, IaC=high) -> https://docs.langchain.com/langsmith/create-account-api-key
   - Acquire when needed; IaC automation is straightforward.
1. MISTRAL_API_KEY (Mistral, required=False, IaC=high) -> https://docs.mistral.ai/getting-started/quickstart/
   - Acquire when needed; IaC automation is straightforward.
1. OPENAI_API_KEY (OpenAI, required=False, IaC=high) -> https://platform.openai.com/api-keys
   - OAuth-supported lane available; mint only if direct API lane is needed.
1. OPENROUTER_API_KEY (OpenRouter, required=False, IaC=high) -> https://openrouter.ai/docs/api-keys
   - OAuth-supported lane available; mint only if direct API lane is needed.
1. PINECONE_API_KEY (Pinecone, required=False, IaC=high) -> https://docs.pinecone.io/guides/projects/manage-api-keys
   - Acquire when needed; IaC automation is straightforward.
1. SERPAPI_API_KEY (SerpAPI, required=False, IaC=high) -> https://serpapi.com/manage-api-key
   - Acquire when needed; IaC automation is straightforward.
1. VOYAGE_API_KEY (Voyage AI, required=False, IaC=high) -> https://docs.voyageai.com/docs/api-key-and-installation
   - Acquire when needed; IaC automation is straightforward.
1. ASSEMBLYAI_API_KEY (AssemblyAI, required=False, IaC=medium) -> https://www.assemblyai.com/docs/getting-started
   - Acquire manually, then automate distribution and rotation.
1. BRAVE_SEARCH_API_KEY (Brave Search, required=False, IaC=medium) -> https://api.search.brave.com/app/keys
   - Acquire manually, then automate distribution and rotation.
1. CEREBRAS_API_KEY (Cerebras, required=False, IaC=medium) -> https://inference-docs.cerebras.ai/introduction
   - Acquire manually, then automate distribution and rotation.
1. COHERE_API_KEY (Cohere, required=False, IaC=medium) -> https://dashboard.cohere.com/api-keys
   - Acquire manually, then automate distribution and rotation.
1. DEEPSEEK_API_KEY (DeepSeek, required=False, IaC=medium) -> https://api-docs.deepseek.com/
   - Acquire manually, then automate distribution and rotation.
1. ELEVENLABS_API_KEY (ElevenLabs, required=False, IaC=medium) -> https://elevenlabs.io/docs/api-reference/authentication
   - Acquire manually, then automate distribution and rotation.
1. EXA_API_KEY (Exa, required=False, IaC=medium) -> https://docs.exa.ai/reference/authentication
   - Acquire manually, then automate distribution and rotation.
1. GROQ_API_KEY (Groq, required=False, IaC=medium) -> https://console.groq.com/keys
   - Acquire manually, then automate distribution and rotation.
1. PERPLEXITY_API_KEY (Perplexity, required=False, IaC=medium) -> https://docs.perplexity.ai/guides/getting-started
   - Acquire manually, then automate distribution and rotation.
1. REPLICATE_API_TOKEN (Replicate, required=False, IaC=medium) -> https://replicate.com/account/api-tokens
   - Acquire manually, then automate distribution and rotation.
1. TAVILY_API_KEY (Tavily, required=False, IaC=medium) -> https://docs.tavily.com/api-reference/introduction
   - Acquire manually, then automate distribution and rotation.
1. TOGETHER_API_KEY (Together, required=False, IaC=medium) -> https://docs.together.ai/reference/authentication-1
   - Acquire manually, then automate distribution and rotation.
1. XAI_API_KEY (xAI, required=False, IaC=medium) -> https://docs.x.ai/docs/overview
   - Acquire manually, then automate distribution and rotation.

## Provider Coverage

| Provider | Total Keys | Available | Missing | Has Any Key |
|---|---:|---:|---:|---:|
| Anthropic | 1 | 0 | 1 | False |
| AssemblyAI | 1 | 0 | 1 | False |
| Azure OpenAI | 1 | 0 | 1 | False |
| Brave Search | 1 | 0 | 1 | False |
| Cerebras | 1 | 0 | 1 | False |
| Cohere | 1 | 0 | 1 | False |
| DeepSeek | 1 | 0 | 1 | False |
| ElevenLabs | 1 | 0 | 1 | False |
| Exa | 1 | 0 | 1 | False |
| Fireworks AI | 1 | 0 | 1 | False |
| GitHub | 1 | 1 | 0 | True |
| Google AI Studio | 1 | 0 | 1 | False |
| Groq | 1 | 0 | 1 | False |
| Hugging Face | 2 | 2 | 0 | True |
| LangSmith | 1 | 0 | 1 | False |
| Mistral | 1 | 0 | 1 | False |
| OpenAI | 1 | 0 | 1 | False |
| OpenRouter | 1 | 0 | 1 | False |
| Perplexity | 1 | 0 | 1 | False |
| Pinecone | 1 | 0 | 1 | False |
| Poe | 3 | 3 | 0 | True |
| Replicate | 1 | 0 | 1 | False |
| SerpAPI | 1 | 0 | 1 | False |
| Tavily | 1 | 0 | 1 | False |
| Together | 1 | 0 | 1 | False |
| Voyage AI | 1 | 0 | 1 | False |
| xAI | 1 | 0 | 1 | False |
