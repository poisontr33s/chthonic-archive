---
name: researchFeatureJourney
description: Deep-research a feature and document the learning journey with upcycling opportunities
argument-hint: Specify the VS Code/Copilot feature or tool to research (e.g., /savePrompt, MCP, agents)
tools: [ 'read_file', 'search', 'edit', 'run_in_terminal' ]
mode: agent
---

Research {{argument}} and document the learning journey from pre→post understanding.

## Workflow

1. **Pre-Learning Snapshot**
   - Document current understanding (what's known, what's a "black box")
   - Identify gaps and assumptions

2. **Deep Research**
   - Find source specifications (VS Code docs, extension source, official schemas)
   - Test behavior empirically if needed
   - Cross-reference with existing codebase patterns

3. **Discovery Documentation**
   - Specification details discovered
   - Syntax/format requirements
   - Mode/parameter semantics

4. **Upcycling Analysis**
   - What existing code/algorithms can benefit?
   - Middle ground: portable yet enhanced when context present
   - Avoid hard dependencies; document "afterglow" benefits

5. **Post-Learning Artifacts**
   - Updated code/scripts with fixes
   - Documentation in `_learning/` folder
   - Cross-reference mapping (feature ↔ codebase patterns)

## Output

- `_learning/{FEATURE}_JOURNEY.md` with pre→post documentation
- Code fixes applied to relevant files
- README updates if new commands/capabilities added

## Principle

> Research for understanding, implement for portability, document for continuity.
