# Image Witness Sidecars

Image witnesses are deterministic evidence files for Markdown image references.

They prove:
- what image path was referenced
- whether the file existed
- the image byte hash and size when present
- whether the reference looked like an equation image

They do not prove OCR text, rendered math, or semantic equivalence.

OCR is intentionally absent in this phase. The witness layer prepares a stable socket for future OCR providers without letting them rewrite Markdown.

Sidecars are written as JSON under:

`.mdseal/images/<sha256>.image-witness.json`

Default policy is `sidecar-only`.

Policy behavior:
- `sidecar-only`: write witness JSON
- `report-only`: report only, do not write
- `add-alt-latex`: refused until OCR exists
- `add-adjacent-caption`: refused until OCR exists
- `add-html-comment`: refused until OCR exists

Likely-equation heuristics are filename and alt-text driven. Pixels are not inspected here.

Image hashes are compared against seal manifests to report drift, but images are never mutated.
