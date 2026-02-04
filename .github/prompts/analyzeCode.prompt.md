---
name: analyzeCode
description: Review code for issues and improvements
argument-hint: Select code or file to analyze
tools:
  - search
  - read_file
  - get_errors
mode: ask
---

Analyze {{argument}}.

## Review Areas

- **Potential issues**: Bugs, security vulnerabilities, race conditions
- **Performance**: Inefficiencies, optimization opportunities
- **Best practices**: Idiomatic patterns, code style
- **Maintainability**: Complexity, readability, modularity

## Output

Provide prioritized findings with:
1. Issue severity (critical/warning/info)
2. Location and context
3. Recommended fix
