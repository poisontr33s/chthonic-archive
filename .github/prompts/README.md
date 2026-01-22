# Prompt Library

VS Code Copilot Chat reusable prompts. Invoke via `/commandName` in chat.

## Available Commands

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

[saveprompt_algorithm.py](../../scripts/saveprompt_algorithm.py) - Batch processor for:
- Beautifying raw session exports → archives
- Extracting patterns → `.prompt.md` templates

```bash
# Archive mode
uv run python scripts/saveprompt_algorithm.py session.txt

# Extract mode
uv run python scripts/saveprompt_algorithm.py session.txt --extract-prompts
```

## Source

- Native `/savePrompt`: VS Code Copilot Chat extension
- Custom extractions: `saveprompt_algorithm.py` pattern detection
