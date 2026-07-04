# Seal Format

Sidecar JSON stored under `.mdseal/`.

The current manifest is `mdseal.v1` and records:

- file and source hash
- encoding and line ending style
- profile and hash mode
- heading index
- zone spans and hashes
- math spans with optional raw math in full mode
- fence spans and hashes
- table shape hashes
- image references and hashes when available
- image witness path placeholders and drift reporting inputs
- hidden Unicode inventory

Full seals may store raw math spans.
Hash-only seals omit raw math and can only detect corruption.

Seals are now refusal-aware:

- existing seals refuse overwrite unless `--force` is passed
- hash-only seals refuse raw restoration unless explicitly allowed
- restore refuses when source hash or context no longer matches the seal
- context matching uses hashes around the candidate span, not offsets alone
- image hash drift is diagnosed when the file exists but the bytes differ
- image witnesses may be written separately as `.mdseal/images/<sha256>.image-witness.json`
- table and fence drift are diagnosed, but not auto-restored in this phase
