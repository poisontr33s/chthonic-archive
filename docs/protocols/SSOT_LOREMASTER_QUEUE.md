# SSOT Loremaster Queue

Source tool: `scripts/ssot_loremaster.py`

| Phase | Status | Title | Rationale | Deliverable | Dependencies |
|-------|--------|-------|-----------|-------------|--------------|
| P1 | active | Codex-side Loremaster CLI | Codex needs a direct, archive-reading lane that can answer section/entity/drift questions without hand-scanning the SSOT. | scripts/ssot_loremaster.py | ssot_structural_extractor.py |
| P2 | active | Mirror Governance Pass | Stale mirrors and proto backups must be distinguished from live canon or they will keep re-injecting drift. | Explicit sync/freeze policy for .temple/architecture and .github/copilot-instructions-copy.md via docs/protocols/SSOT_MIRROR_GOVERNANCE.md | P1 |
| P3 | active | Full-Name Law Pass | The SSOT abbreviation system depends on original full names. Load-bearing tables should preserve those names rather than inventing replacement aliases. | Full-name restoration matrix for load-bearing tables and registry rows | P1 |
| P4 | pending | SSOT-to-MPW Lineage Join | Lore work benefits from a deliberate join between archive entities and MPW documents, rather than memory-based linkage. | Entity lineage map with archive sections and MPW document anchors | P1 |
| P5 | pending | Chthonic or MCP Exposure | Once the query surface is stable, it should be callable from the house tools instead of remaining a raw script. | chthonic subcommand or mcp-chthonic-server tool binding | P1-P4 |
