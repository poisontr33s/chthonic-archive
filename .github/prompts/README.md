# Prompt Library

VS Code Copilot Chat reusable prompts. Invoke via `/commandName` in chat.

## Afterglow Principle

Prompts work standalone **and** benefit from SSOT context when loaded:

| Layer | Source | Role |
|-------|--------|------|
| **Native** | `/savePrompt` | VS Code's prompt infrastructure |
| **Portable** | `.prompt.md` files | Self-contained, shareable triggers |
| **Enhanced** | `copilot-instructions.md` | FA¹⁻⁵ axioms, DAFP, PRISM (when present) |

> *Prompts don't encode SSOT wisdom—they invoke it through presence.*

## Available Commands

### General Development

| Command | Mode | Description |
|---------|------|-------------|
| `/beautifySessionArchive` | agent | Transform raw AI sessions → archives + prompts |
| `/createComponent` | agent | Generate new code components |
| `/refactorCode` | agent | Improve code structure |
| `/debugIssue` | agent | Identify and fix bugs |
| `/generateTests` | agent | Create comprehensive tests |
| `/documentCode` | agent | Add documentation |
| `/explainCode` | ask | Explain code or concepts |
| `/analyzeCode` | ask | Review for issues |
| `/improvePrompt` | agent | Apply savePrompt best practices |
| `/crossReferenceSSOT` | agent | Map SSOT patterns to feature upcycling |
| `/researchFeatureJourney` | agent | Deep-research a feature with pre→post learning docs |

## Format Specification

```yaml
---
name: commandName        # camelCase → /commandName
description: Brief desc  # Shown in picker
argument-hint: Hint      # Placeholder after /command
tools: [ 'edit', ... ]   # Required permissions
mode: agent|ask|edit     # Execution mode
---

Instructions with {{argument}} placeholder for user input.
```

## Companion Script

`saveprompt_algorithm.py` - Batch processor for:
- Beautifying raw session exports → archives
- Extracting patterns → `.prompt.md` templates

```bash
# Archive mode
uv run python .github/prompts/saveprompt_algorithm.py session.txt

# Extract mode (outputs to .github/prompts/)
uv run python .github/prompts/saveprompt_algorithm.py session.txt --extract-prompts
```

## Directory Structure

```
.github/prompts/
├── README.md                    # This file
├── RESEARCH.md                  # Specification reference
├── saveprompt_algorithm.py      # Batch processor
├── *.prompt.md                  # Reusable prompts
├── _learning/                   # Pre→post research docs
├── archives/                    # Beautified session outputs
└── raw/                         # Input session samples
```
