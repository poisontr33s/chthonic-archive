---
name: documentCode
description: Add documentation and comments to code
argument-hint: Select code to document
tools: [ 'edit', 'read_file' ]
mode: agent
---

Document {{argument}}.

## Documentation Elements

- **Purpose**: What does this code do
- **Parameters**: Input descriptions with types
- **Returns**: Output description
- **Raises**: Possible exceptions
- **Examples**: Usage demonstrations

Follow the codebase's existing documentation style (docstrings, JSDoc, etc.).
