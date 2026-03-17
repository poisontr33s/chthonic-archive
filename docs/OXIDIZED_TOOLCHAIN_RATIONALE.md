---
sid: DOC_OXIDIZED_TOOLCHAIN_RATIONALE
title: Oxidized Toolchain Rationale — Why This Repo Prefers Native Language Managers
type: rationale
status: canonical
created: 2026-03-16
updated: 2026-03-16
authors:
  - Codex
audience:
  - all
tags:
  - toolchain
  - rationale
  - oxidized
  - rust-native
  - polyglot
---

<!--
@SID:    DOC_OXIDIZED_TOOLCHAIN_RATIONALE
@Type:   Rationale
@Context: Toolchain / Architectural policy
-->

# Oxidized Toolchain Rationale

> This document is the short architectural rationale behind the repo's oxidized toolchain policy.
> It distills the larger "Rustification" research into repo-usable rules.
> For the actual tool inventory, use [OXIDIZED_TOOLCHAIN_REFERENCE.md](OXIDIZED_TOOLCHAIN_REFERENCE.md).
> For commands, use [OXIDIZED_CHEATSHEET.md](OXIDIZED_CHEATSHEET.md).

---

## Thesis

This repository prefers compiled, native language managers and infrastructure tools because they reduce runtime drift, remove shell-script fragility, and keep polyglot workflows fast enough to use continuously.

The core split is:

- Application logic can remain in the target language.
- Tooling, orchestration, dependency resolution, and environment management should prefer native compiled implementations.

That is the practical meaning of "oxidized" in this repo.

---

## Policy

### One owner per language lane

The repo favors one primary tool owner for each language/runtime lane:

| Lane | Primary owner |
|------|---------------|
| Python | `uv` |
| Ruby | `rv` |
| Go | `goup` |
| JS/TS | `bun` |
| Rust | `cargo` / `rustup` |
| Bash-compatible shell | `brush` |
| R versions | `rig` |
| Zig versions | `zv` |

This reduces decision churn, command drift, and "which tool owns this install?" ambiguity.

### Native tooling first

Prefer compiled tooling for:

- version management
- dependency resolution
- lockfile sync
- formatting, linting, and static analysis
- shell/runtime bootstrapping

Do not route these workloads through slower wrapper stacks when a stable native path exists.

### Deterministic local workflows

The repo values:

- pinned versions
- reproducible installs
- explicit lockfiles
- project-local activation files
- low-overhead shell startup

This is why `uv`, `rv`, `goup`, `bun`, `rig`, and `zv` fit the direction of the codebase.

---

## Why It Matters Here

This workspace is not single-language. It is a Windows 11 polyglot repo with:

- Python tooling
- Ruby tooling
- Go utilities
- Bun/TypeScript application and extension work
- Rust crates
- shell orchestration
- R and Zig adjacent research/toolchain lanes

A fragmented manager stack costs time every day in:

- PATH confusion
- duplicate caches
- shell startup delay
- mismatched versions between projects
- CI inconsistency
- agent confusion about tool ownership

The oxidized policy is the repo's answer to that.

---

## Case Study: Ruby and `rv`

The Ruby lane is the clearest example of the broader pattern.

Historically, Ruby environment management fragmented across:

- `rvm`
- `rbenv`
- `chruby`
- `ruby-build`
- `ruby-install`
- `bundler`
- ad hoc gem-global workflows

The Rust-based `rv` project exists to collapse that sprawl into one native binary with a faster install path, isolated tool execution, and tighter project pinning.

What matters for this repo:

- precompiled Ruby installs remove the old "compile Ruby from source for 10–40 minutes" tax on supported systems
- `rvx` and `rv tool install` let Ruby CLI tools run without polluting global gem state
- the management layer becomes fast enough to use as normal workflow, not just rare setup ceremony

That is why this repo treats `rv` as the canonical Ruby owner instead of treating Ruby runtime install, gem isolation, and project pinning as separate concerns spread across multiple tools.

The underlying CRuby runtime still matters, but the practical gain here is in orchestration speed and isolation. The repo policy is built around that management-layer improvement.

Illustrative benchmark examples from the supplied research notes:

| Benchmark | CRuby 3.4.7 time (ms) | RSD |
|-----------|-----------------------|-----|
| `railsbench` | 3093.0 | 0.66% |
| `ruby-lsp` | 182.7 | 0.68% |
| `rubocop` | 185.8 | 0.64% |
| `sequel` | 69.3 | 0.36% |
| `addressable-join` | 388.7 | 0.16% |

These figures are not the reason to adopt `rv` by themselves. They matter because they show the runtime is stable while the Rust-native management layer removes the surrounding operational drag.

---

## Secondary Cases: R, Zig, and Shells

### R: `rig` + `R rv`

The R lane separates into two roles:

- `rig` for R runtime installation and switching
- `R rv` for package/environment determinism

That mirrors the split between runtime ownership and package-resolution ownership seen in other ecosystems, but with a naming collision that has to be explicitly controlled in this repo.

The key value of `R rv` is not just speed. It is the move from retrospective environment capture toward declared project state:

- `rproject.toml` as manifest / lock anchor
- `.rv` as the project-local environment
- direct console ergonomics like `.rv$sync()` and `.rv$add("pkg")`

That is the same broader architectural move seen in `uv`, `rv`, and other oxidized managers: explicit state first, reconstruction second.

### Zig: `zv`

`zv` matters because it brings a rustup-style workflow to Zig:

- project-aware switching through `.zigversion`
- no manual PATH editing per project
- a proper version-manager layer rather than ad hoc Zig binary juggling

That makes the Zig lane fit the same repo pattern as Python, Ruby, Go, and Rust.

### Shells: `brush`

The shell layer matters as much as the package-manager layer on Win11.

`brush` is relevant here because it aims to preserve Bash/POSIX compatibility while replacing the memory-unsafe C shell substrate with a Rust-native implementation. In practical repo terms, that means:

- fewer cross-OS shell-script surprises
- one native Bash-compatible companion for Windows
- a lower-friction path for Unix-first install scripts

That is why the repo treats `brush` as part of the oxidized stack rather than as an incidental extra.

---

## The Pattern Extends Beyond Managers

Validation note:

- the concrete example projects below were checked against official repos or official docs on 2026-03-16
- the architectural interpretation remains repo synthesis
- this section is rationale, not enforcement canon

This repo’s oxidized-toolchain policy starts with managers because that is the most operationally visible layer. But the validated examples point to the same migration pattern at adjacent layers:

- **PHP / `Mago`**: Rust-native linting, formatting, and static analysis replacing slower self-hosted PHP tooling.
- **Lua / `mlua`**: Rust acting as the safe embedding and interop substrate around Lua runtimes.
- **Cloudflare / `Wirefilter`**: Rust as a high-performance embedded interpreter for untrusted input.
- **COBOL / `Cobalt`**: Rust moving into enterprise compiler construction, not just modern greenfield tools.
- **Elixir / `Explorer`**: Rust/Polars carrying the heavy compute backend while the host language keeps the high-level API.
- **Julia / `jlrs`**: Rust handling orchestration and interop around scientific compute instead of replacing it.
- **Mojo**: even when the implementation is not Rust, Rust’s ownership model is still shaping the language design.

That matters because the repo should not interpret "oxidized" too narrowly. It is not just:

- a better version manager
- a faster package resolver
- a shell replacement

It is a broader architectural preference for moving infrastructure, orchestration, parsing, linting, embedding, and static-analysis layers onto safer compiled substrates.

---

## Broader Implications

The research is useful because it points to four practical consequences that matter here:

### CI and compute economics

Faster native tooling reduces build minutes, shell overhead, and wasted CI runtime. This matters directly in a polyglot repo with repeated install, lint, and test cycles.

### The decline of the unsafe extension layer

Rust-native bridges reduce the need for fragile C/C++ extension glue in high-level ecosystems. That lowers the stability and security cost of native acceleration.

### Workflow homogenization

When multiple ecosystems converge on "single binary, lockfile-first, project-aware manager," switching languages becomes less cognitively expensive. That matters in this repo because agents and humans cross Python, Ruby, Go, JS/TS, Rust, R, and Zig lanes in the same workspace.

### Interop as infrastructure

Rust increasingly functions as the connective substrate between runtimes, tooling, and embedded systems. Even where a language is not "rewritten in Rust," its orchestration, package, shell, or embedding layer often is.

---

## Naming Canon

### `rv` collision rule

In this repository, unqualified `rv` means the **Ruby** manager.

Reason:

- `spinel-coop/rv` is the Ruby runtime/tool manager actually aligned with this repo's Ruby lane
- `A2-ai/rv` is an **R package manager** with the same binary name
- using `rv` generically creates collisions in docs, tasks, and shell guidance

Repo naming rule:

- `rv` = Ruby manager
- `rig` = R version manager
- `R rv` or `rv-r` = the **R package manager** when discussed in documentation

`rv-r` is a repo documentation label, not a claim about the upstream executable name.

### Zig rule

For Zig, the oxidized version-manager reference is `zv`.

Reason:

- `zv` is the Rust-native Zig manager in scope for this repo's toolchain discussion
- `zigup` and `zvm` exist, but they are not the Rust-native lane this repo is standardizing around

---

## Evidence Standard

The long-form Rustification research is useful as directional analysis, but it mixes:

- primary documentation
- repo sources
- blog posts
- secondary commentary
- community threads

So the repo uses it as a **rationale source**, not as an enforcement SSOT.

Operational enforcement should come from:

1. verified local tool behavior
2. official tool docs
3. repo-specific command ownership rules

That is why the reference and cheatsheet docs exist separately from this rationale.

---

## Practical Outcome

If you are choosing commands in this repo:

- use the oxidized owner first
- avoid duplicate managers unless there is a proven gap
- when documenting the R lane, prefer `rig` for versions and keep `rv` reserved for Ruby
- when documenting the Zig lane, use `zv`

This is the repo-level execution policy derived from the larger Rustification research.
