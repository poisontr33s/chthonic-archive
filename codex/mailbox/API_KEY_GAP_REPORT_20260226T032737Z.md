# API Key Gap Report

- Generated (UTC): 2026-02-26T03:27:37.9862265Z
- Total keys checked: `8`
- Available: `6`
- Missing: `2`

## Key Matrix

| Key | Provider | Available | In Pool | In Process | In User Env | Acquire URL |
|---|---|---:|---:|---:|---:|---|
| OPENAI_API_KEY | OpenAI | False | False | False | False | https://platform.openai.com/api-keys |
| GITHUB_TOKEN | GitHub | True | True | False | True | https://github.com/settings/tokens |
| GEMINI_API_KEY | Google AI Studio | False | False | False | False | https://aistudio.google.com/apikey |
| POE_API_KEY | Poe | True | True | False | True | https://poe.com/api_key |
| POE_API_KEY_1 | Poe | True | True | False | True | https://poe.com/api_key |
| POE_API_KEY_2 | Poe | True | True | False | True | https://poe.com/api_key |
| HUGGINGFACE_HUB_TOKEN | Hugging Face | True | True | True | True | https://huggingface.co/settings/tokens |
| HF_TOKEN | Hugging Face | True | False | True | True | https://huggingface.co/settings/tokens |

## Missing Keys (Priority Acquisition Queue)
1. OPENAI_API_KEY -> https://platform.openai.com/api-keys
1. GEMINI_API_KEY -> https://aistudio.google.com/apikey
