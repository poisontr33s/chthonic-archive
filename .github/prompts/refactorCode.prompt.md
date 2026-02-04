---
name: refactorCode
description: Improve code structure while preserving behavior
argument-hint: Select the code to refactor
tools: 
  - edit
  - search
  - read_file
mode: agent
---

Refactor {{argument}}.

## Considerations

- Maintain existing behavior
- Improve code clarity
- Optimize performance where applicable
- Follow language idioms and best practices

## Process

1. Analyze current implementation
2. Identify improvement opportunities
3. Apply changes incrementally
4. Verify behavior preservation
