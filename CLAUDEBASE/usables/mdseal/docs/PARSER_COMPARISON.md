# Parser Comparison

Parser comparison is a validation layer that compares normalized Markdown structure summaries across multiple parser views.

It exists to catch repairs that make a document structurally unstable even if a single scanner accepts it.

Current parser views:

- `remark-gfm-math`
- `micromark-gfm-math`
- `markdownlint`

The implementation normalizes summaries for:

- headings
- code fences
- tables
- inline math
- display math
- HTML blocks
- links
- images
- list items
- blockquotes

A disagreement means the parser views do not agree on one of those counts.

That does not always mean a document is broken.

It becomes a refusal when the candidate repair makes disagreement worse or creates a new regression.

Parser comparison runs alongside KaTeX validation; agreement across parsers is not a substitute for math parseability.

