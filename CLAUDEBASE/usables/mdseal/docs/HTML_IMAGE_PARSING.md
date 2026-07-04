# HTML Image Parsing

HTML image parsing is reference discovery only.

It detects image-bearing HTML fragments embedded in Markdown and converts them into inventory metadata. It does not inspect pixels or render HTML.

Supported tags:
- `img`
- `picture`
- `source`
- `srcset`

Captured metadata:
- `src`
- `srcset`
- `alt`
- `title`
- `width`
- `height`
- raw attributes
- line and column when available
- remote, data URI, relative, and absolute classification

For `<picture>`, the parser preserves child `<source>` candidates and the fallback `<img>` as metadata.

Non-goals:
- no fetches
- no OCR
- no decoding
- no model downloads
- no file mutation
- no Markdown or HTML rewriting

HTML image references feed the existing image inventory surface so Markdown and HTML references can be reported together without creating a second image pipeline.
