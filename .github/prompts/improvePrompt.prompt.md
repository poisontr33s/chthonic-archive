---
name: improvePrompt
description: Apply savePrompt research to enhance existing prompts
argument-hint: Select the .prompt.md file to improve
tools: [ 'edit', 'read_file', 'search' ]
mode: agent
---

Improve {{argument}} by applying VS Code `/savePrompt` best practices.

## Checklist

1. **Frontmatter completeness**:
   - `name`: camelCase, action-oriented
   - `description`: ≤15 words, clear purpose
   - `argument-hint`: Guides user input
   - `tools`: Appropriate permissions
   - `mode`: `agent` (actions) or `ask` (Q&A)

2. **Body structure**:
   - Uses `{{argument}}` for user input interpolation
   - Clean markdown formatting
   - No session-specific noise
   - Actionable instructions

3. **Quality gates**:
   - Concise (under 50 lines)
   - Self-contained instructions
   - Clear output expectations

## Output

Apply fixes directly to the file and summarize changes made.
