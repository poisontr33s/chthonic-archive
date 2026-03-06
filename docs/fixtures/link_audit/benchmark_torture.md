# Link Audit Torture Fixture

This fixture mixes easy wins, ambiguous collisions, skipped patterns, and
broken markdown references so `link_audit.py` can prove what it can fix.

## Inert Backticks

- Known canonical file: `AGENTS.md`
- Known canonical methodology file: `WET_PAPER_TO_GOLD_METHODOLOGY.md`
- Directory target: `.github/`
- New filetype in the same folder: `entropy-scroll.ankh`
- New filetype with runtime flavor: `polyglot-cadence.rv`
- New filetype with runtime flavor: `oxidized-bridge.goup`
- Multi-dot filename: `human.digital.bridge.lore`
- Hidden dotfile: `.oracle`
- Nested directory path: `docs/fixtures/link_audit/`
- Ambiguous shared basename: `README.md`
- Ambiguous skill basename: `SKILL.md`
- Skipped wildcard pattern: `*.reference.md`
- Unresolved fantasy token: `nonexistent-bridge.ankh`

## Markdown Links

- Broken-but-unique: [methodology](WET_PAPER_TO_GOLD_METHODOLOGY.md)
- Broken-but-unique weird extension: [entropy](entropy-scroll.ankh)
- Ambiguous broken basename: [readme](README.md)
- Collision unlabeled but resolvable: [README.md](../../../docs/README.md)
- Already good disambiguated link:
  [copilot-instructions.archive.md (.github)](../../../.github/copilot-instructions.archive.md)

## Ignore These

Code fences should stay untouched:

```md
`AGENTS.md`
`entropy-scroll.ankh`
[README.md](../../README.md)
```

Inline markdown link labels should not be treated as inert backticks:

- [`AGENTS.md`](../../../AGENTS.md)
- [`entropy-scroll.ankh`](./entropy-scroll.ankh)
