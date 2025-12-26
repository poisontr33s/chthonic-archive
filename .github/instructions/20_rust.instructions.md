---
applyTo: "src/**/*.rs"
---

# Rust Implementation Instructions

| Category | Instruction |
|---|---|
| Scope control | Make the smallest correct change; avoid refactors not required by the task. |
| Style | Match existing module/style conventions; keep public APIs stable unless asked. |
| Errors | Prefer explicit, actionable error messages; propagate with context when useful. |
| Safety | Avoid `unsafe` unless explicitly required; if used, justify via minimal invariants. |
| Validation | Prefer `cargo build` / `cargo test` relevant to touched code. |

<details>
<summary><strong>Repo Build/Check Defaults</strong></summary>

| Task | Command |
|---|---|
| Build | `cargo build` |
| Tests | `cargo test` |
| Lint | `cargo clippy --all-targets --all-features -- -W clippy::pedantic` |

</details>
