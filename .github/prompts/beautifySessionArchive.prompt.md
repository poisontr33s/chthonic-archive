---
name: beautifySessionArchive
description: Transform raw AI chat sessions into organized archives and extract reusable prompts
argument-hint: Provide the raw chat session file or folder path to process
tools:
  - edit
  - search
  - read_file
  - run_in_terminal
mode: agent
---
Process raw AI chat session exports into organized, useful artifacts.

## Task

Given a raw chat session export (verbose text file from Copilot, Claude, or similar):

1. **Archive Mode (Beautification)**
   - Parse conversation structure (User/Assistant turns)
   - Extract key artifacts (code blocks, file changes, decisions)
   - Apply compression to remove redundant tool outputs
   - Format with consistent markdown structure
   - Add metadata header (line counts, artifact counts, hash)
   - Generate session summary with topics covered

2. **Extract Mode (Prompt Templates)**
   - Identify recurring task patterns from user queries
   - Generalize into reusable `.prompt.md` templates
   - Follow VS Code's `/savePrompt` format conventions
   - Only extract patterns with ≥2 occurrences

## Workflow

```
Raw Session → [Parse] → [Extract Artifacts] → [Compress] → [Beautify] → Archive.md
                                                      ↓
                                              [Pattern Detection] → *.prompt.md
```

## Output Structure

**Archive output** (`*_Beautified.md`):
- YAML frontmatter with metadata
- Session summary
- Full formatted conversation

**Prompt output** (`*.prompt.md`):
- VS Code-insiders-compatible format
- Generalized with placeholders
- Tool requirements specified

## Usage

Process the selected session file or folder, generating both archival documents for reference and reusable prompt templates for automation.
