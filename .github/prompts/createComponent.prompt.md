---
name: createComponent
description: Generate new code components based on specifications
argument-hint: Describe what to create
tools:
  - edit
  - search
  - read_file
mode: agent
---

Create {{argument}}.

## Guidelines

- Follow existing codebase conventions
- Include appropriate error handling
- Add inline documentation
- Consider edge cases

## Output

Provide the complete implementation with:
1. The component code
2. Any necessary imports
3. Brief usage example
