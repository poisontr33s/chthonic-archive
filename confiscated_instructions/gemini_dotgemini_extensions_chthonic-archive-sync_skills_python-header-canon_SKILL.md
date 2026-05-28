---
name: "python-header-canon"
description: "Normalize Python file headers to the repository canon: #!/usr/bin/env python3 plus UTF-8 coding line. Use when standardizing .py files across Codex or Claude skill/script lanes."
metadata:
  short-description: "Normalize Python shebang + UTF-8 header across scoped .py files."
---

# Python Header Canon

Standardize Python headers to this exact two-line canon:

```python
#!/usr/bin/env python3
#-*- coding: utf-8 -*-
```

## Use Cases

- Bulk normalization across `scripts/`, `.codex/`, `.claude/`, or repo-wide.
- Post-merge cleanup when shebang/coding lines drift.
- Enforcing deterministic Python header policy before audits.

## Deterministic Workflow

1. Resolve scope (default `scripts/` unless user provides target path).
2. Collect `*.py` files in scope.
3. For each file:
   - Remove existing shebang/coding header if present at the top.
   - Insert canonical two-line header.
   - Preserve remaining file content exactly.
4. Report changed file count and sample paths.

## Execution

Single target:

```powershell
uv run .codex/skills/python-header-canon/scripts/python_header_canon.py scripts/
```

Multiple targets:

```powershell
uv run .codex/skills/python-header-canon/scripts/python_header_canon.py scripts/ .codex/skills .claude/skills
```

## Constraints

- Never use `cmd /c`.
- Use PowerShell-native paths.
- Do not rewrite non-Python files.
- Do not alter code beyond header normalization.
- Keep Python dependencies in `pyproject.toml` (no inline `# /// script` blocks for repo scripts).
