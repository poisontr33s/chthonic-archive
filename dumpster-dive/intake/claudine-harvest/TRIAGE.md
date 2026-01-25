# Claudine Harvest — Triage

## High-Signal (Likely Yours / High Impact)

| Staged file | What it looks like | Why it matters | Suggested action |
|---|---|---|---|
| `DF47AE1F882232F3__CantorForge.ps1` | Big “impossible stack” bootstrapper (downloads installers, uv install, rustup, conda, etc.). | High-impact if run accidentally; contains reusable ideas but should not be an implicit dependency. | Keep as reference; upcycle selectively into repo-local scripts only if requested. |
| `84D3C0C8EE47AB4B__create-psycho-noir-kontrapunkt-full.ps1` | A repo-builder generator script (batch-style content, writes many files). | Explains where the PsychoNoir repo scaffolding came from; can carry the “claudine trolling” wiring. | Keep for forensics; do not auto-run; extract only the alias/activation bits if needed. |
| `6CA77E28501F31BF__EnvVarManagerGUI.ps1` | WinForms GUI that edits Machine env vars (requires admin). | Extremely high-impact system mutation tool. | Treat as “dangerous utility”; never auto-run; only run intentionally. |
| `A689EE33F8702A77__Microsoft.VSCode_profile.ps1` | A VS Code profile script (likely integrated-terminal related). | Can change terminal behavior and command resolution. | Inspect for alias/profile hijacks; upcycle only if it improves determinism. |
| `2919D506B1758C9B__Microsoft.PowerShell_profile.ps1` | Global profile with `Set-Alias claudine ...` + auto-activation. | Root cause of cross-repo `claudine` hijack. | Keep as evidence; fix outside-repo only with explicit approval. |
| `556BBC05B819EB8F__profile.ps1` | Same global profile pattern. | Same hijack vector. | Same. |
| `2ED300C9669FC860__claudineENV.ps1` | External env activation (polyglot paths + markers). | Not the hijack; it becomes the hijack because of the global alias. | Keep as upcycle source (PATH patterns) but do not import wholesale. |

## Likely Generated / Low-Signal

These are typically package-manager generated PowerShell shims (often from Node/pnpm) and are usually **not** the “fun scripts” you wrote.

<details>
<summary><strong>Staged shims (Sliding Table)</strong></summary>

| Pattern | Example staged files |
|---|---|
| Node/pnpm shim wrappers | `*__semver.ps1`, `*__mime.ps1`, `*__nodemon.ps1`, `*__node-which.ps1`, `*__browserslist.ps1`, `*__json5.ps1`, `*__jest.ps1` |

</details>

## Next Upcycle Step (Repo-Local Only)

| Goal | Minimal repo-local change |
|---|---|
| Make hijacks visible | Ensure `scripts/claudine.ps1` prints when it neutralizes a preexisting alias/function. |
| Reduce noise in future hunts | Use the harvester defaults + hardened exclusions; avoid scanning `node_modules` trees. |
