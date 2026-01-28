# Hallucination Review & Repurpose TODO

**Scope:** scripts/ and docs/ (focus on high-emoji / narrative-heavy artifacts)

## 1) Inventory (initial candidates)

### Docs (session/lore/reference)
- docs/sessions/AUTONOMOUS_SESSION_2_COMPLETE.md
- docs/sessions/AUTONOMOUS_SESSION_3_DEEP_DIVE_SYNTHESIS.md
- docs/sessions/AUTONOMOUS_SESSION_3_DEEP_RESEARCH.md
- docs/sessions/AUTONOMOUS_SESSION_3_EXECUTION_COMPLETE.md
- docs/lore/Spectra_Chroma_Excavatus.md
- docs/reference/VSCODE_GUI_ENHANCEMENT_COMPLETE.md
- docs/COPILOT_SESSION_PERSISTENCE.md

### Scripts (narrative/branding output or emoji-heavy)
- scripts/mandala_topology.py
- scripts/mcp-chthonic-server.ts
- scripts/setup-gemini-claude.ts
- scripts/schema_validation_report.md
- scripts/test-chthonic-mcp.ps1
- scripts/Discover-SSOT-Treasure.ps1

## 2) Classification (draft)

**Legend**
- **KEEP**: legit doc/tool, minor style cleanup only
- **REFORMAT**: rewrite into concise technical doc
- **ARCHIVE**: move to docs/legacy or docs/archive
- **REMOVE**: delete if not needed

| Path | Category | Action | Rationale (summary) |
|---|---|---|---|
| docs/sessions/AUTONOMOUS_SESSION_2_COMPLETE.md | Docs | ARCHIVE | narrative-heavy session artifact |
| docs/sessions/AUTONOMOUS_SESSION_3_DEEP_DIVE_SYNTHESIS.md | Docs | ARCHIVE | narrative-heavy session artifact |
| docs/sessions/AUTONOMOUS_SESSION_3_DEEP_RESEARCH.md | Docs | ARCHIVE | narrative-heavy session artifact |
| docs/sessions/AUTONOMOUS_SESSION_3_EXECUTION_COMPLETE.md | Docs | ARCHIVE | narrative-heavy session artifact |
| docs/lore/Spectra_Chroma_Excavatus.md | Docs | ARCHIVE | lore-only, not operational |
| docs/reference/VSCODE_GUI_ENHANCEMENT_COMPLETE.md | Docs | REFORMAT | technical content mixed with lore |
| docs/COPILOT_SESSION_PERSISTENCE.md | Docs | REFORMAT | useful content, remove flamboyant tone |
| scripts/mandala_topology.py | Script | REFORMAT | keep logic, reduce narrative output |
| scripts/mcp-chthonic-server.ts | Script | KEEP | infrastructure; style cleanup optional |
| scripts/setup-gemini-claude.ts | Script | KEEP | functional setup; reduce header branding |
| scripts/schema_validation_report.md | Script doc | KEEP | technical report; remove emoji tags if desired |
| scripts/test-chthonic-mcp.ps1 | Script | REFORMAT | keep tests, simplify output labels |
| scripts/Discover-SSOT-Treasure.ps1 | Script | REFORMAT | keep logic, reduce narrative/emoji output |

## 3) Repurpose actions (next implementation steps)

1. **Docs archiving**
   - Create docs/legacy/ or docs/archive/ and move session/lore artifacts.
   - Add a short README in the archive folder with retention policy.

2. **Doc reformatting**
   - Rewrite docs/reference/VSCODE_GUI_ENHANCEMENT_COMPLETE.md into a concise technical spec. ✅
   - Rewrite docs/COPILOT_SESSION_PERSISTENCE.md into a minimal usage guide. ✅

3. **Script output cleanup**
   - Normalize output messaging in scripts/mandala_topology.py, scripts/test-chthonic-mcp.ps1, scripts/Discover-SSOT-Treasure.ps1. ✅
   - Keep behavior identical; remove flamboyant labels/emoji.

4. **Index update**
   - Add or update a docs index to point to current authoritative docs and mark legacy content.

## 4) Decision points

- Confirm archive location: docs/legacy vs docs/archive.
- Confirm whether to *delete* any artifacts or only archive.
- Confirm whether to keep emoji branding in MCP server banners.
