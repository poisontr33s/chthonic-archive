# API Key Gap Report

- Generated (UTC): 2026-02-26T04:20:39.3614831Z
- Total keys checked: `8`
- Available: `6`
- Missing: `2`
- Missing required: `1`

## Key Matrix

| Key | Provider | Required | Available | In Pool | In Process | In User Env | Acquire URL |
|---|---|---:|---:|---:|---:|---:|---|
| OPENAI_API_KEY | OpenAI | False | False | False | False | False | https://platform.openai.com/api-keys |
| GITHUB_TOKEN | GitHub | True | True | True | False | True | https://github.com/settings/tokens |
| GEMINI_API_KEY | Google AI Studio | True | False | False | False | False | https://aistudio.google.com/apikey |
| POE_API_KEY | Poe | True | True | True | False | True | https://poe.com/api_key |
| POE_API_KEY_1 | Poe | True | True | True | False | True | https://poe.com/api_key |
| POE_API_KEY_2 | Poe | True | True | True | False | True | https://poe.com/api_key |
| HUGGINGFACE_HUB_TOKEN | Hugging Face | True | True | True | True | True | https://huggingface.co/settings/tokens |
| HF_TOKEN | Hugging Face | False | True | False | True | True | https://huggingface.co/settings/tokens |

## Missing Keys (Priority Acquisition Queue)
1. GEMINI_API_KEY -> https://aistudio.google.com/apikey
