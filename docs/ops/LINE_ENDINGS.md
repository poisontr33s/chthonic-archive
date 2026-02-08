---
type: ops
status: active
created: 2026-02-07
---

# Line Endings (LF Policy)

This repo standardizes on LF for all files Git classifies as text via `.gitattributes` (`* text=auto eol=lf`).

## One-Time Normalization
After adding or changing `.gitattributes`, run:
```powershell
git add --renormalize .
```

Notes:
- Run from the repo root on a clean working tree.
- Expect a large staged diff; review with `git status` and `git diff --cached`.
- Prefer committing renormalization as a dedicated "EOL normalization" commit.

## Contributor Git Settings
On Windows, `core.autocrlf=true` commonly reintroduces CRLF into the working copy.
Recommended:
- Repo-local: `git config core.autocrlf false` (preferred when `.gitattributes` is authoritative), or `input`
- Global: `git config --global core.autocrlf false` if you want the same behavior in all repos

Check:
```powershell
git config --global core.autocrlf
```

Set (example):
```powershell
git config --global core.autocrlf false
```
