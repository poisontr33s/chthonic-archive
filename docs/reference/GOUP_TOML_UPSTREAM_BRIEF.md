# goup TOML Upstream Brief

@SID: DOC_GOUP_TOML_UPSTREAM_BRIEF
@Type: Reference
@Context: Toolchain / Go / Rustified Managers

## Verdict

`goup-rs` is good enough to own Go versions for this workspace, but it is not
yet good enough as a policy/config layer. The missing piece is first-class
project config, ideally `goup.toml`.

Rating:

- Go version management: 8/10
- Cross-platform implementation hygiene: 8/10
- Project policy/config ergonomics: 5/10
- Fit as a general multi-language manager: 4/10

## Source Findings

Reviewed current goup-rs source and installed CLI:

- Installed: `goup 0.16.11`, built from commit `d384f4b1902830e787bbf40380b18923ec215892`.
- Upstream main reviewed at `bdbdbfa1681b797325152c09296356a3b4b0418f`.
- `cargo check --locked` passed on a clean source checkout.
- `goup shell` currently autodetects only `go.work` then `go.mod`.
- `goup shell` parses `go` and `toolchain` directives, so `toolchain go1.26.4` is already understood when a real Go module/workspace exists.
- `goup install stable` updates Go and switches default.
- `goup self update` updates goup itself, but does not currently combine self-update, stable Go update, and old-version pruning into one policy-driven operation.

## Why Not Root `go.work`

An empty root `go.work` parses, but `go list ./...` fails because the workspace
has no modules. That makes it a bad root anchor for this repository today.
Create `go.work` only when it can list real module directories.

## Proposed `goup.toml`

This repo now uses root `goup.toml` as policy metadata and proposed upstream
schema:

```toml
[toolchain]
channel = "1.26.4"
profile = "stable"
targets = ["windows/amd64"]

[goup]
manager = "goup"
project_detection = ["goup.toml", "go.work", "go.mod"]

[commands]
install_stable = "goup install stable"
self_update = "goup self update"
list = "goup list"
env = "goup env"
shell = "goup shell"

[policy]
no_raw_go_bootstrap = true
no_runtime_go_install = true
prefer_goup_for_go_updates = true

[cleanup]
keep_previous_versions = 0
prune_after_stable_update = true
```

## PR Shape for goup-rs

Minimal upstream change:

1. Add `toml` dependency.
2. Add config loader that searches upward from current directory for `goup.toml`.
3. Parse `[toolchain] channel`, `[toolchain] version`, or `[toolchain] toolchain`.
4. Make `goup shell` precedence:
   - explicit CLI version
   - `goup.toml`
   - `go.work`
   - `go.mod`
   - prompt/default fallback
5. Add optional `goup sync` or `goup up` command:
   - run `goup self update`
   - run `goup install <toolchain.channel>`
   - optionally prune old non-active versions according to `[cleanup]`

Keep pruning conservative. Refuse to delete active/default/session versions.

## Other Managers

- `uv` already consumes TOML via `pyproject.toml` and `uv.toml`, and uses
  `.python-version` for version pinning. Do not invent a duplicate Python
  policy format unless the repo needs cross-manager inventory.
- `rv` from Spinel is installed here (`rv 0.5.3`) and exposes `selfupdate`,
  `ruby`, `tool`, and `clean-install` lanes. Treat Ruby `rv` and R `rv-r` as
  separate lanes.
- `zv` is installed here and already uses `.zigversion`; newer zv also has TOML
  state. Prefer native `zv` behavior before adding wrappers.

## Repo Rule

Rustified managers are preferred when they are the native owner of a language
lane, but they should not hide policy. Each lane needs one visible config file
and one explicit update command path.
