# Corpus Guide

Each case needs `broken.md`, `golden.md`, and `meta.json`.

Image cases may also include a small local `images/` folder. The corpus stays deterministic: no OCR, no remote image fetches, and no provider calls.

The corpus is used to verify both transformation and refusal behavior.

For parser-comparison cases, meta may include `expectedValidationGates` and refusal expectations.
