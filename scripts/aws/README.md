# AWS + Bedrock quickstart (local)

1) Load repo AWS env (fixes PATH for aws shim, sets defaults):

```powershell
. .\scripts\aws\env.ps1
```

2) Authenticate (choose one):

SSO:
```powershell
aws configure sso --profile my-sso
aws sso login --profile my-sso
aws sts get-caller-identity --profile my-sso
```

Access keys (learning/personal):
- Copy templates:
  - `scripts/aws/credentials.template` -> `%USERPROFILE%\.aws\credentials`
  - `scripts/aws/config.template` -> `%USERPROFILE%\.aws\config`
- Then:
```powershell
aws sts get-caller-identity --profile bedrock
```

3) Bedrock sanity:
```powershell
aws bedrock list-foundation-models --region $env:AWS_REGION --profile $env:AWS_PROFILE
```

4) Run the Python tests:
```powershell
uv run python .\scripts\aws\claude_opus46_invoke.py
uv run python .\scripts\aws\claude_opus46_large_context.py
```

Notes:
- The Python scripts read: `AWS_PROFILE`, `AWS_REGION`, `BEDROCK_MODEL_ID`.
- 1M context uses the beta flag `context-1m-2025-08-07`.
