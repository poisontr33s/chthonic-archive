# KaTeX Validation

KaTeX validation checks whether extracted math spans can be parsed by KaTeX without guessing repairs.

It exists to separate:

- valid math
- syntax errors
- unsupported commands
- unsafe commands
- macro expansion problems
- Unicode noise in math

Inline and display math are validated in their respective modes.

Trust defaults to `false`.

Unsupported commands are reported by default.

Unsafe commands fail by default.

Custom macros may be provided through config.

KaTeX validation influences:

- `check`
- `fix --dry-run`
- `fix --write`
- `restore --dry-run`
- `restore --write`
- `sweep`

KaTeX does not rewrite equations.
It only validates them and helps determine whether a repair made things better or worse.

