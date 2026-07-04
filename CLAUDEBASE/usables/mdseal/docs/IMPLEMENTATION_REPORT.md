# Implementation Report

`mdseal` now focuses on a refusal-first core:

- deterministic scan and repair
- explicit validation gates
- protected-zone preservation checks
- parser-comparison validation
- KaTeX validation
- image witness sidecars without OCR
- provider doctor checks without live OCR
- HTML image parsing as metadata-only reference discovery
- seal overwrite protection
- hash-only restore refusal
- JSON-shaped command output for the main commands
- rich seal manifests with math, fence, table, image, and hidden-symbol records

What it still does not do:

- live OCR
- provider-driven mutation
- whole-document rewriting
- heuristic guessing inside protected zones
- hard dependency on Pandoc
- auto-restoration of tables or fences
- rewriting unsupported KaTeX commands by guesswork
- OCR-backed image rewriting
- provider-backed OCR execution
- HTML image decoding or fetching
