---
type: ops
status: active
created: 2026-02-07
schema: mailbox_manifest
---

# Mailbox Manifest Schema

This repo generates a mailbox inventory file at:
- `codex/mailbox/mailbox_manifest.json`
- `claude/mailbox/mailbox_manifest.json`

## Schema Versioning
- `schema_version` is an integer.
- Consumers must tolerate unknown fields.
- Consumers should branch behavior on `schema_version` when present.

## v2 (Current)
Top-level fields:
- `schema_version` (required): `2`
- `mailbox` (required): mailbox root path, repo-relative, POSIX
- `generated_on` (required): UTC timestamp (ISO-8601)
- `manifest_file` (required): manifest filename only (not a path), expected to be `mailbox_manifest.json`
- `active` (required): object containing active artifacts
- `archive_count` (required): integer
- `archive_files` (required): list of paths (POSIX) relative to the `archive/` directory under `mailbox` (e.g., `2026_02_07/foo.json` resolves to `${mailbox}/archive/2026_02_07/foo.json`)

`active` fields:
- `md`: list of active `.md` filenames (no paths)
- `json`: list of active `.json` filenames (no paths)

## Important Behavior Change (v2)
The manifest file is intentionally excluded from the `active` object's `json` array.
Reason:
- Including `mailbox_manifest.json` inside its own inventory can create self-referential traversal loops in tools that recursively process `active.*`.

Replacement:
- Use `manifest_file` as the explicit pointer to the manifest itself.

## v1 (Legacy)
Behavioral notes for consumers:
- No `schema_version` field.
- No `manifest_file` field.
- The manifest filename may have been included inside `active.json` (self-inclusion), which can create recursion loops in naive traversers.
- `archive_files` may have been a flat list of filenames (non-recursive), depending on the generator revision.

## Backward Compatibility Notes
If a consumer previously assumed self-inclusion in `active.json`, update it to:
- Always include `manifest_file` explicitly when copying/shipping an “active set”.
- Treat missing `schema_version` as `1`-ish legacy behavior.
