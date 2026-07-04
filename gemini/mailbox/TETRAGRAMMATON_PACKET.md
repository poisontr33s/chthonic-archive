---
type: packet
created: 2026-03-19T21:20:33.608813+00:00
updated: 2026-03-20T14:14:43.743925+00:00
mailbox: gemini/mailbox
codename: TETRAGRAMMATON
sources_hash: c8eb92432dd4fd9406f49d99896b1febc9fd0078d31bf612d315eb8562f32e4d
sources_count: 2
---

# TETRAGRAMMATON Packet

<!-- @SCRIBED: 2026-03-20T14:14:43.743929+00:00 -->

## Packet Rules
- Paths are repo-relative (portable; no local usernames).
- Large JSON files may be embedded as a valid JSON stub with `_truncated: true`.
- Stub fields: `relative_path`, `bytes`, `sha256`.

## Index
- `MAILBOX_CURRENT_STATE.md`
- `mailbox_manifest.json`

## Snapshot
- Generated: `2026-03-20T14:14:43.743925+00:00`
- Sources hash: `c8eb92432dd4fd9406f49d99896b1febc9fd0078d31bf612d315eb8562f32e4d`

## Content

### MAILBOX_CURRENT_STATE.md
Path: `gemini/mailbox/MAILBOX_CURRENT_STATE.md`

```md
---
type: mailbox-state
updated: 2026-03-20T14:14:43.731993+00:00
mailbox: gemini/mailbox
---

# Mailbox Current State

## Active Files
- `MAILBOX_CURRENT_STATE.md`
- `TETRAGRAMMATON_PACKET.md`
- `mailbox_manifest.json`

## Archive
- Path: `gemini/mailbox/archive`
- Count: 0

## Policy
- Root mailbox keeps only current-cycle files.
- Historical files may remain in `archive/`.
- Hidden dot mailboxes stay sentinel-only (`.gitkeep`).
```

### mailbox_manifest.json
Path: `gemini/mailbox/mailbox_manifest.json`

```json
{
  "schema_version": 2,
  "mailbox": "gemini/mailbox",
  "generated_on": "2026-03-20T14:14:43.731475+00:00",
  "manifest_file": "mailbox_manifest.json",
  "active": {
    "md": [
      "MAILBOX_CURRENT_STATE.md",
      "TETRAGRAMMATON_PACKET.md"
    ],
    "json": []
  },
  "archive_count": 0,
  "archive_files": []
}
```

## Scribe Log

- 2026-03-19T21:20:33.608813+00:00: packet created
- 2026-03-19T21:26:31.963597+00:00: sources changed
- 2026-03-19T21:28:59.568097+00:00: sources changed
- 2026-03-19T21:30:09.444005+00:00: sources changed
- 2026-03-19T21:30:51.321792+00:00: sources changed
- 2026-03-19T21:33:11.180930+00:00: sources changed
- 2026-03-19T21:45:03.955191+00:00: sources changed
- 2026-03-19T21:55:47.080434+00:00: sources changed
- 2026-03-20T14:03:14.055665+00:00: sources changed
- 2026-03-20T14:14:43.743925+00:00: sources changed
