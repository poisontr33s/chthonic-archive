# ANKH Atlas — Semantic Instrumentation for Chthonic Archive

## What This Is

A **coordinate system over a semantic field**, not a documentation tool.

This scanner answers **"where"** and **"how often."**  
It must **never** answer **"what"** or **"why."**

## Design Philosophy

> "Think of it as the equivalent of: a symbol table for a compiler, a call graph for a codebase, or a linter that never rewrites code."

The tool provides **navigation without narration**. It emits coordinates, not interpretations.

## What It Detects (Tier 1 Signals)

| Signal Type | Pattern | Example |
|-------------|---------|---------|
| `heading-def` | Markdown headings | `# Section Title` |
| `abbrev-def` | First appearance of abbreviation | `(SSOT)` or \`SSOT\` |
| `abbrev-use` | Subsequent uses of abbreviation | `SSOT` (after first def) |
| `invariant-tag` | Parenthetical tags | `(FA⁴)`, `(SSOT-L-H)`, `(T-DECOR)` |
| `crossref` | Section/protocol references | `§XIV.3`, `(Section VIII)`, `(Prt.III.2)` |

## Output Format

`ankh_index.json` at repository root:

```json
{
  "schema_version": "0.1.0",
  "generated_at": "2025-12-30T08:40:01.627822+00:00",
  "commit": "e494aa0df7e70a5bef550b8ba4f80bcf9311e066",
  "repo_root": "C:\\Users\\eldno\\chthonic-archive",
  "signal_count": 35942,
  "signals": [
    {
      "artifact": ".github\\copilot-instructions.md",
      "line": 4,
      "signal_type": "abbrev-def",
      "token": "GOVERNANCE",
      "context": "* **(`Codex-Brahmanica-Perfectus`/`GOVERNANCE`): = ..."
    }
  ]
}
```

## Usage

```powershell
# Generate index
cd ankh_atlas
uv run python -m ankh_atlas

# Output: ankh_index.json at repo root
```

## Design Constraints

1. **Read-only**: Never modifies source files
2. **Deterministic**: Same inputs → same outputs (modulo timestamp)
3. **Git-diffable**: JSON with `sort_keys=True`, `indent=2`
4. **Semantic passivity**: Emits facts, never interpretations
5. **Boring by design**: Output should feel "large, repetitive, obvious"

## Success Criteria

> "Only after you can say: 'This index already saves me time, even though it's annoying to use.' That's the green light."

The tool is **correct** when:
- Output is "ugly but true"
- You resist the temptation to "clean it up"
- It provides coordinates without becoming an authority

## What This Is NOT

- ❌ Documentation generator
- ❌ Summarization tool
- ❌ Narrative explainer
- ❌ Knowledge graph
- ❌ "Book" abstraction

It is a **fact emitter**, nothing more.

## Architecture

```
ankh_atlas/
├── models.py       # Signal dataclass (frozen, immutable)
├── detectors.py    # Tier 1 pattern recognition
├── scan.py         # Deterministic file traversal
├── index.py        # JSON serialization
└── __main__.py     # Orchestration pipeline
```

## Future Work (Deferred)

- **CLI queries**: `ankh_atlas find ABBREV`, `ankh_atlas refs §X`
- **Tier 2 signals**: Protocol blocks, silence markers
- **Tier 3 signals**: Future-tense markers, epistemic hedges

Only after Tier 1 proves its utility.

## License

This tool is part of the Chthonic Archive project.
