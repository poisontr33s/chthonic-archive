---
applyTo: "**/*.{ps1,psm1,psd1}"
---

# PowerShell + uv Lanes (Determinism)

| Area | Contract |
|---|---|
| Terminal bootstrap | Prefer `-NoProfile` and PATH-only lane wiring via VS Code `terminal.integrated.env.windows` (avoid dot-sourcing, banners, aliases, wrapper functions). |
| Lane policy | `python` = uv-managed 3.13 lane; `python314` = uv-managed 3.14 lane. |
| claudine | Must resolve repo-locally and behave deterministically across terminal PIDs. |
| PATH edits | Keep PATH changes minimal and de-duplicated; avoid global profile dependencies. |
| No “auto magic” | Do not introduce background auto-activation that triggers in other repos. |

## Backtracking Guardrails

| Situation | Required behavior |
|---|---|
| Something works already | Don’t replace it with a new mechanism; extend it. |
| Multiple entrypoints appear | Collapse to one canonical entrypoint, or ask the user before choosing. |
