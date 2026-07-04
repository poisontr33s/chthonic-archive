# Provider Doctor

The provider doctor is a local readiness check.

It checks:
- registry metadata
- enabled/disabled provider state
- network and download policy
- Python sidecar command presence when enabled
- transformer readiness flags when configured
- unknown configured provider IDs
- OCR-dependent image policy refusals remain safe

It does not:
- run OCR
- download models
- mutate files
- require GPU
- call Hugging Face services

Providers are disabled by default so the doctor can report readiness without becoming a runtime dependency.

The Python sidecar stub supports `--doctor` and returns JSON only, so the CLI can probe reachability without loading a model.
