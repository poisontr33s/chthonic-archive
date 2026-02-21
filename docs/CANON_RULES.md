# Canon Rules Registry

Rules that govern this codebase. Each rule is either **enforceable** (machine-checkable, pass/fail) or **guidance** (human judgment, best-effort).

## Terminology

| Term | Meaning |
|------|---------|
| **Policy file** | A governance document (e.g., `copilot-instructions.md`) |
| **Policy fingerprint** | SHA-256 hash of a policy file's normalized content |
| **Integrity check** | "Did this file change?" — not "is this file correct?" |
| **Canon** | An explicit decision, declared here, with a checker |
| **Guidance** | A preference or convention without automated enforcement |

## Rules

| # | Rule | Scope | Level | Checker | Autofix | Owner |
|---|------|-------|-------|---------|---------|-------|
| 1 | Python shebang: `#!/usr/bin/env python3` | `scripts/*.py` | enforceable | `scripts/check_python_policy.py` | `scripts/fix_headers.py` | user |
| 2 | Python encoding: `#-*- coding: utf-8 -*-` | `scripts/*.py` | enforceable | `scripts/check_python_policy.py` | `scripts/fix_headers.py` | user |
| 3 | Python execution via `uv run` only | all Python | enforceable | manual review | — | user |
| 4 | No `eval('require')` in extensions | `extensions/*/src/**/*.ts` | enforceable | `bun run compile` + grep | manual | user |
| 5 | Native sidecars gated by kill-switch | `extensions/chthonic-archive` | enforceable | `allowNativeSidecars` config flag | — | user |
| 6 | Extension fallback defaults match `package.json` | `extensions/*/src/extension.ts` | enforceable | manual review | manual | user |
| 7 | Policy fingerprint is integrity alarm only | repo-wide | guidance | `chthonic.verifySSOT` command | — | user |
| 8 | Track machinery, ignore exhaust | `.gitignore` | guidance | `git status` | manual | user |
| 9 | Cargo dependency allowlist | `Cargo.toml` | enforceable | `reflex-guard` pre-commit hook | — | user |
| 10 | Genre extractor smoke gate | nightly pipeline | enforceable | smoke check in `genre_extractor.py` | — | user |
| 11 | Nightly retention: keep last 7 runs | `overnight-daemon/`, `overnight-intelligence/` | enforceable | `run_archaeology.ps1` pruning | automatic | user |

## What does NOT belong here

- Stylistic preferences (indentation, naming conventions) — these are IDE settings
- Philosophical frameworks (ANKH, Triumvirate, CRC) — these are creative content
- Session protocols (MASP, handoff semantics) — these are workflow, not code rules

## How to add a rule

1. Write the rule as a single sentence
2. Define scope (which files/paths)
3. Classify: enforceable (has a checker) or guidance (human judgment)
4. If enforceable: identify or create the checker script
5. Add to the table above
6. Commit this file

## Precedence

When rules conflict: **this file > instruction files > memory > convention**.

A rule is canon only when it appears in this table. Everything else is guidance.
