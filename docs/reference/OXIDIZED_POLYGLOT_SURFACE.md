---
sid: DOC_OXIDIZED_POLYGLOT_SURFACE
title: Oxidized Polyglot Surface — Stack, Commands & Ecosystem
type: reference
status: canonical
created: 2026-04-20
updated: 2026-04-20 (collapsed OXIDIZED_TOOLCHAIN_REFERENCE + OXIDIZED_CHEATSHEET; §9 Meta-CLI Sync Map added)
supersedes:
  - docs/OXIDIZED_TOOLCHAIN_REFERENCE.md (DOC_OXIDIZED_TOOLCHAIN_REFERENCE)
  - docs/OXIDIZED_CHEATSHEET.md (DOC_OXIDIZED_CHEATSHEET)
authors:
  - Claude
audience:
  - all
tags:
  - toolchain
  - rust-native
  - oxidized
  - version-managers
  - polyglot
  - cheatsheet
  - meta-cli
---

<!--
@SID:    DOC_OXIDIZED_POLYGLOT_SURFACE
@Type:   Reference + Cheatsheet + Meta-CLI Bridge
@Context: Polyglot Toolchain — full surface in one file
@Supersedes: DOC_OXIDIZED_TOOLCHAIN_REFERENCE, DOC_OXIDIZED_CHEATSHEET
-->

# Oxidized Polyglot Surface

> Operational reference for the chthonic-archive polyglot stack — Rust-native managers, command surfaces, and meta-CLI sync points in one place.
>
> **Structure:**
> - §1–§5 — Operational (stack, naming, pattern map, per-tool commands, version files)
> - §6–§8 — Landscape (ecosystem, EOL API, OxidizedIndex concept)
> - §9 — Meta-CLI bridge (maps this doc to `chthonic.ps1` functions)
>
> Primary shell: pwsh 7.5.x. Bash companion: brush (eliminates shell-script OS discrepancies).
> Rationale: [OXIDIZED_TOOLCHAIN_RATIONALE.md](OXIDIZED_TOOLCHAIN_RATIONALE.md)

---

## §1 Current Stack

| Tool | Domain | Replaces | Update Command | Windows 11 |
|------|--------|----------|----------------|------------|
| **uv** | Python versions + packages | pyenv + pip + virtualenv | `uv self update` | ✅ native |
| **rv** | Ruby versions + gems | rbenv + bundler | `rv selfupdate` | ✅ native |
| **goup** | Go versions | manual SDK install | `goup self update` | ✅ native (symlink, needs Dev Mode) |
| **bun** | JS/TS runtime + packages | node + npm/nvm | `bun upgrade` | ✅ native |
| **cargo / rustup** | Rust toolchain | — (canonical) | `rustup update` | ✅ native |
| **brush** | Bash-compatible shell | Git Bash / WSL bash | `cargo install --locked brush-shell` | ✅ native (.exe) |
| **zv** | Zig versions | manual Zig SDK installs | `zv update` (self-update) / `zv use stable` (upgrade Zig) | ✅ native |
| **rv-r** (A2-ai/rv) | R packages (declarative) | `install.packages()` / renv | `cargo install rv` (no self-update subcommand) | ✅ native |

**Validated locally — April 2026:**

- `uv 0.11.7`
- `rv 0.5.3`
- `goup 0.16.10` — Go `1.26.2` active
- `bun 1.3.13`
- `cargo 1.95.0` / `rustup`
- `brush 0.3.0`
- `zv 0.10.0` (manages Zig `0.16.0`)
- `rv-r → rv 0.19.0` (R `4.5.3 ucrt` — runtime unmanaged, rig not installed)

Not currently installed on this workstation: `rig` (R version manager — see §6)

---

## §2 Naming Canon

Use these names consistently in this repo:

- `rv` = Ruby manager (spinel-coop/rv)
- `rv-r` = R **package** manager (A2-ai/rv) — always use `rv-r` in docs and tasks
- `rig` = R **version** manager (r-lib/rig) — not installed; documented as future option
- `zv` = Rust-native Zig version manager

**Why `rv-r` and not bare `rv` for R packages:**
- `rv` binary name collides with Ruby lane
- `rv` in PWSH 7.x also aliases `Remove-Variable`
- repo wrapper: `scripts/rv-r.ps1`
- in shell: `rv-r <args>` via wrapper, not bare `rv`

This naming applies in repo docs, tasks, and scripts. Bare `rv` is reserved for the Ruby lane only.

---

## §3 Cross-Tool Pattern Map

> "I want to ___" → which tool + which command

### Install a language version

| Goal | Command |
|------|---------|
| Install Python 3.13.11 | `uv python install 3.13.11` |
| Install Ruby 4.0.1 | `rv ruby install 4.0.1` |
| Install Go 1.26.1 | `goup install 1.26.1` |
| Install Node 22 | `fnm install 22` |
| Install R 4.4.0 | `rig add 4.4.0` |
| Install latest of anything | `uv python install latest` / `goup install` / `fnm install --latest` / `rig add release` |
| Install Go tip (dev branch) | `goup install tip` |
| Install R devel build | `rig add devel` |

### Switch / activate a version

| Goal | Command |
|------|---------|
| Pin Python for current project | `uv python pin 3.13.11` → writes `.python-version` |
| Pin Ruby for current project | `rv ruby pin 4.0.1` → writes `.ruby-version` |
| Switch default Go version | `goup default 1.26.1` |
| Switch active Node version (shell) | `fnm use 22` |
| Set default R version | `rig default 4.4.0` |
| Set default Node version | `fnm default 22` |
| Activate Rust nightly for one project | `rustup override set nightly` → writes `.rustup-override` |
| Use a different Rust toolchain inline | `cargo +nightly build` |

### Pin versions for a whole project (multi-language)

| Goal | Command |
|------|---------|
| Pin all tools in one file | `proto pin <tool> <version>` → writes `.prototools` |
| Pin all tools via mise | `mise use <tool>@<version>` → writes `mise.toml` or `.tool-versions` |
| Commit a Rust toolchain spec | Create `rust-toolchain.toml` → picked up by `cargo` automatically |

### Run a command with a specific version (without changing active version)

| Goal | Command |
|------|---------|
| Python with specific version | `uv run --python 3.12 script.py` |
| Node with specific version | `fnm exec --using=20 node script.js` |
| Rust with specific toolchain | `rustup run nightly rustc --version` |
| Any tool via proto | `proto exec node@20 -- node script.js` |
| Any tool via mise | `mise exec node@20 -- node script.js` |

### Install a global CLI tool (isolated — no pollution)

| Goal | Command |
|------|---------|
| Python global CLI tool (pipx-style) | `uv tool install <package>` |
| Run Python CLI ephemerally (no install) | `uv tool run <package> <cmd>` |
| Ruby global gem CLI (isolated) | `rv tool install <gem>` |
| Run Ruby gem ephemerally | `rvx <gem-command>` |
| JS/TS CLI ephemerally | `bunx <package>` |
| Node CLI ephemerally (any version) | `fnm exec --using=lts bunx <pkg>` |

### List what's installed / available

| Goal | Command |
|------|---------|
| Python versions (installed) | `uv python list --only-installed` |
| Python versions (all available) | `uv python list` |
| Ruby versions (installed + available) | `rv ruby list` |
| Go versions (installed) | `goup list` |
| Go versions (available upstream) | `goup search` |
| Node versions (installed) | `fnm list` |
| Node versions (available) | `fnm list-remote` |
| Node LTS versions only | `fnm list-remote --lts` |
| R versions (installed) | `rig list` |
| R versions (available) | `rig available` |
| Rust toolchains (installed) | `rustup toolchain list` |
| All tools via mise | `mise ls` |
| Outdated tools via mise | `mise outdated` |

### Update a tool manager itself

| Tool | Self-update command |
|------|---------------------|
| uv | `uv self update` |
| rv | `rv selfupdate` |
| goup | `goup self update` |
| bun | `bun upgrade` |
| zv | `zv update` |
| rv-r | *(cargo install rv — no self-update subcommand)* |
| mise | `mise self-update` |
| proto | `proto upgrade` |
| rig | *(reinstall via package manager: Scoop/WinGet/Chocolatey)* |
| fnm | `fnm` *(reinstall via cargo: `cargo install fnm`)* |
| rustup | `rustup self update` |
| brush | `cargo install --locked brush-shell` |

### Run a script / command in the project environment

| Goal | Command |
|------|---------|
| Python script with auto-env | `uv run script.py` |
| Python one-off with extra deps | `uv run --with httpx script.py` |
| Python self-contained script (PEP 723) | `uv run --script script.py` |
| Ruby script | `rv run ruby script.rb` |
| JS/TS script | `bun run script.ts` |
| Any package.json script | `bun run <scriptname>` |
| Task defined in mise.toml | `mise run <taskname>` |

### Add / remove project dependencies

| Goal | Command |
|------|---------|
| Add Python dep | `uv add httpx` |
| Add Python dev dep | `uv add --dev pytest` |
| Remove Python dep | `uv remove httpx` |
| Add JS dep | `bun add react` |
| Add JS dev dep | `bun add --dev typescript` |
| Remove JS dep | `bun remove react` |
| Add JS dep exact version | `bun add --exact react@18.2.0` |

### Lock / sync environment (CI-safe reproducible installs)

| Goal | Command |
|------|---------|
| Python — install exact from lockfile | `uv sync --frozen` |
| Python — update lockfile | `uv lock` |
| Ruby — install exact from Gemfile.lock | `rv clean-install` |
| JS — install exact from lockfile | `bun ci` (= `bun install --frozen-lockfile`) |
| JS — update lockfile | `bun install` |
| R — install exact from rv.lock | `rv-r sync` |
| R — update all packages + rewrite lock | `rv-r upgrade` |
| All tools via mise | `mise install` (reads `.tool-versions` / `mise.toml`) |

### Cross-compile / target a different platform

| Goal | Command |
|------|---------|
| Python wheels for different platform | `uv pip install --python-platform linux_x86_64` |
| Rust — add cross-compile target | `rustup target add x86_64-unknown-linux-gnu` |
| Rust — compile for target | `cargo build --target x86_64-unknown-linux-gnu` |
| Node — install for different OS | `bun install --os linux --cpu x64` |

### Shell integration / auto-switching on `cd`

| Tool | Shell init line (pwsh) |
|------|------------------------|
| rv (Ruby) | `Invoke-Expression (& "rv" shell init powershell)` |
| fnm (Node) | `fnm env --use-on-cd \| Out-String \| Invoke-Expression` |
| mise (polyglot) | `mise activate powershell \| Out-String \| Invoke-Expression` |
| proto (polyglot) | `proto activate --shell powershell \| Out-String \| Invoke-Expression` |

---

## §4 Per-Tool Quick Reference

---

### uv — Python

```
uv python install 3.13.11    # install version
uv python pin 3.13.11        # write .python-version for this project
uv python list               # all available versions
uv python list --only-installed

uv init --app                # new app project
uv init --lib                # new library project
uv add httpx                 # add dep (updates pyproject.toml + uv.lock)
uv add --dev pytest          # add dev dep
uv remove httpx              # remove dep
uv sync                      # install all deps from lockfile
uv sync --frozen             # CI: exact lockfile, no changes allowed
uv lock                      # update lockfile only

uv run script.py             # run script in project env
uv run --python 3.12 script.py  # run with specific Python version
uv run --with httpx script.py   # run with extra ephemeral dep
uv run -m pytest             # run as module

uv tool install ruff         # install CLI tool globally (isolated)
uv tool run ruff check .     # run CLI tool ephemerally
uv tool list                 # list installed tools
uv tool upgrade ruff         # upgrade a tool

uv self update               # update uv itself
uv cache clean               # clear cache
```

**Non-obvious:**
- `uv run --script script.py` — runs a PEP 723 script with `# /// script` inline deps (self-contained, no project needed)
- `uv add --bounds exact` — pins to exact version (no `^` range)
- `uv export > requirements.txt` — generates requirements.txt from uv.lock for tools that need it
- `uv auth login` — stores credentials for private indices

---

### rv — Ruby

```
rv ruby list                 # installed + available Ruby versions
rv ruby install 4.0.1        # install a version
rv ruby install              # install pinned/current stable from rv
rv ruby pin 4.0.1            # write .ruby-version for this project
rv ruby find                 # show path to active Ruby executable
rv ruby dir                  # show all Ruby install directory

rv run ruby script.rb        # run script with active Ruby
rv run ruby -e "puts 42"     # inline Ruby
rv clean-install             # install .ruby-version + Gemfile.lock exactly (CI)

rv tool install rerun        # install gem CLI in isolated env
rv tool list                 # list installed gem tools
rv tool uninstall rerun
rvx rerun                    # run gem binary (auto-installs if missing)
rvx rails new myapp          # zero-setup gem runner

rv shell bash                # print bash init line
rv shell powershell          # print pwsh init line
rv selfupdate                # update rv itself

rv cache                     # manage rv cache
```

**Non-obvious:**
- `rvx` is the zero-friction gem runner — `rvx rails`, `rvx rubocop`, `rvx rake` all work without manual gem install
- `rv tool install` creates isolated envs so global gems don't pollute each other (equivalent of `uv tool install`)
- `rv clean-install` is the CI-safe command — equivalent of `uv sync --frozen` for Ruby
- `rv r <cmd>` is the short alias for `rv run <cmd>`; e.g. `rv r ruby -v`, `rv r ridk version`

**Windows Ruby lane: what owns what**
- `rv` owns the Ruby runtime itself: install, switch, pin, and isolated gem tools.
- RubyInstaller DevKit / MSYS2 owns the native build toolchain: `gcc`, `make`, `pacman`, UCRT64 headers/libs.

**Windows Ruby lane: update + verify**

```powershell
rv selfupdate                        # update rv itself
rv ruby list                         # see installed + available Rubies
rv ruby install 4.0.2               # install the target Ruby runtime
rv ruby pin 4.0.2                   # pin project version explicitly
rv r ruby -v                        # verify active runtime quickly
rv r gem env                        # inspect active gem paths
rv r ridk version                   # verify RubyInstaller + MSYS2 binding
ruby --version                      # verify active Ruby
```

**Windows Ruby lane: `ridk` component sequencing**

Run components one at a time:

```powershell
rv r ridk install 1                # install MSYS2 base
rv r ridk install 2                # optional pacman system update
rv r ridk install 3                # install the MINGW/UCRT dev toolchain
```

---

### goup — Go

```
goup install                 # install latest stable Go
goup install 1.26.1          # install specific version
goup install tip             # install Go development tip
goup install stable          # explicit latest stable form
goup list                    # list installed versions
goup search                  # list all available versions
goup search stable           # list stable remote versions
goup default 1.26.1          # set default Go version
goup shell 1.26.1 -s powershell  # activate one version for the current shell
goup env                     # show current goup environment values
goup remove 1.25.0           # remove a version
goup self update             # update goup itself
```

**Non-obvious:**
- `goup update` is an alias of `goup install` — not a separate upgrade verb
- `goup self update` is the manager self-update path
- `goup install` with no argument means "install current stable"; `goup install stable` is the explicit form
- `goup install go` and similar words are parsed as version strings and fail — use `goup install 1.26.1` or `goup install stable`
- `goup default` changes the default Go version; `goup shell` is the shell-scoped switch
- `goup env` is the quickest truth source for current registry/home/version variables

---

### bun — JS/TS

```
bun install                  # install all deps from package.json
bun ci                       # = bun install --frozen-lockfile (CI)
bun add react                # add dep
bun add --dev typescript     # add dev dep
bun add --exact react@18.2.0 # pin exact version
bun remove react             # remove dep

bun run dev                  # run package.json script
bun run script.ts            # run file directly
bun run --hot server.ts      # run with HMR (hot reload)
bun run --watch server.ts    # restart on file change

bun test                     # run all tests
bun test --watch             # watch mode
bun test --coverage          # with coverage
bun test -t "pattern"        # filter by name

bun build src/index.ts --outdir dist --target browser
bun build src/index.ts --outdir dist --target bun   # single-file executable

bunx <package>               # run npm package ephemerally (like npx)
bunx --bun <package>         # force Bun runtime (not Node shebang)

bun upgrade                  # update bun itself
bun pm cache rm              # clear package cache
bun pm ls                    # list installed packages
bun pm trusted               # list packages with allowed lifecycle scripts
```

**Non-obvious:**
- `bun build --target=bun` compiles to a standalone executable with bun embedded
- `bun run --hot` enables HMR for server processes
- `bun install --minimum-release-age 259200` (3 days) blocks packages published < 72 hours ago — supply chain protection
- `bun install --linker=isolated` enables pnpm-style strict isolation (no hoisting)
- `bun install --os linux --cpu x64` installs native binaries for a different platform (cross-install for Docker)
- `bun pm migrate` migrates from npm/yarn/pnpm lockfile to bun.lock

---

### brush — Bash-compatible shell

```
brush --version                  # show brush version
brush -c 'echo hi'               # run one command and exit
brush -lc 'pwd'                  # login-style one-shot command
brush -i                         # interactive shell
brush --sh -c 'pwd'              # stricter /bin/sh compatibility mode
brush --posix -c 'set -o'        # enable POSIX mode inside the default shell
brush --noprofile -c '...'       # skip profile/login files
brush --norc -i -c '...'         # skip interactive rc files
brush --rcfile ./.brushrc -i -c '...'   # use a specific rc file
brush --noenv -c 'command -v pwd || true'  # start without inherited environment
```

**Verified behavior on this workstation (`brush 0.3.0`):**
- `brush -c` is the normal bash-like mode. `BASH_VERSION` is set (`5.2.15(1)-release`).
- `brush --posix` sets `posix on` but is not a hard POSIX fence: arrays and `[[ ... ]]` still parse.
- `brush --sh` is materially stricter: array syntax errors near `(`, some builtins absent.
- `brush --noenv` starts with `HOME` unset and `PATH` empty. Builtins still work.
- On Windows, bare external command names are unreliable in `brush -c`; prefer absolute `.exe` paths.
- `/dev/null` is not a safe sink on Windows brush; use `NUL` instead.

**Practical Windows rescue snippet for `~/.brushrc`:**

```sh
if [ -z "$PATH" ] && [ -n "$Path" ]; then
  PATH="$Path"
  export PATH
fi
```

**Mental model:**
- `pwsh` remains the canonical shell in this repo
- `brush` is the sanctioned bash-compatible companion when Bourne/bash semantics are needed on Windows
- prefer `brush -c '...'` for bash-ish one-shots
- for Windows batch probes, prefer builtins or absolute `.exe` paths over bare external command names

---

### rv-r — R Package Manager (A2-ai/rv)

> **Name collision:** `rv` = Ruby. `rv-r` = R packages. Bare `rv` in PWSH 7.x also aliases `Remove-Variable`. Always use `rv-r` in this repo.

```
rv-r sync                    # install exactly what rv.lock specifies
rv-r upgrade                 # upgrade all packages to latest + rewrite rv.lock
rv-r add <pkg>               # add package + sync
rv-r remove <pkg>            # remove package + sync
rv-r plan                    # dry-run: what would sync do?
rv-r summary                 # project + library status (Installed: N/N = clean)
rv-r info                    # OS / R version / worker count
rv-r library                 # print library path (%LOCALAPPDATA%\rv\library\<ver>\x86_64)
rv-r cache                   # print cache location
rv-r tree                    # dependency tree
rv-r fmt                     # format rproject.toml (preserves comments)
rv-r configure               # set project-level options
```

**Config file:** `rproject.toml` in the project root.
**Lockfile:** `rv.lock` — commit this, analog to `uv.lock` / `bun.lock`.

**Schema constraints (as of v0.19.0):**
- Top-level keys: `project`, `library`, `use_lockfile`, `lockfile_name` — no `[dev-dependencies]` table
- `[dev-dependencies]` errors on parse → merge dev packages into `dependencies`
- `r-universe` URLs trigger `remotes.rs` panic in `upgrade` — use CRAN + P3M-WIN only
- P3M Linux `__linux__/jammy/latest` URL is a no-op on Windows; use P3M-WIN (`/cran/latest`)

**Non-obvious:**
- Library is isolated per R minor version: `library/4.5/x86_64` — upgrading R minor creates a fresh library
- `rv-r summary` exits 0 when `Installed: N/N`; scriptable health check without prose parsing
- R runtime version itself is managed separately (rig not installed on this workstation)
- `rv-r upgrade` panics with certain non-standard repo URLs (known upstream bug); stick to CRAN/P3M-WIN

---

### zv — Zig Version Manager

```
zv install <version>         # install a Zig version without activating
zv install stable            # install current stable (0.16.0 as of 2026-04-13)
zv use stable                # install + activate stable Zig
zv use <semver>              # activate a specific installed version
zv use latest                # activate latest (= master dev build)
zv list                      # list installed versions (★ = active)
zv clean                     # remove all non-active installed versions
zv update                    # update zv itself to latest release
zv sync                      # synchronize index + metadata
zv setup                     # (re)configure shell PATH for zv
zv init                      # scaffold a new Zig project (lean or standard template)
```

**Config file:** `zig-toolchain.toml` — repo convention, not a zv native format.
**Version pin file:** `.zigversion` in project root — `zv use <ver>` writes this.

**Non-obvious:**
- `zv update` updates zv the manager; `zv use stable` upgrades the active Zig version
- `zv clean` removes ALL non-active versions — run `zv list` first to confirm which is active
- `zv use master` installs a nightly dev build
- Upgrade sequence with cleanup: `zv use stable` → `zv clean` → `zig version`
- `zigup` (Zig-written) and `zvm` (Go-written) exist but only `zv` is Rust-native

---

### rustup — Rust

```
rustup show                  # active toolchain, installed toolchains, targets
rustup update                # update all installed toolchains
rustup update stable         # update specific channel
rustup default stable        # set global default toolchain
rustup default nightly       # switch to nightly globally

rustup toolchain install nightly
rustup toolchain install nightly --profile minimal    # rustc + cargo only (fast CI)
rustup toolchain install nightly --component clippy rustfmt
rustup toolchain list
rustup toolchain uninstall nightly

rustup override set nightly  # this directory uses nightly (writes override)
rustup override unset
rustup override list

rustup target add wasm32-unknown-unknown
rustup target add x86_64-unknown-linux-gnu
rustup target list --installed
rustup target remove wasm32-unknown-unknown

rustup component add rustfmt clippy rust-src rust-analyzer
rustup component list --installed

rustup run nightly -- rustc --version
cargo +nightly build

rustup self update           # update rustup itself
rustup check                 # check for updates without installing
rustup completions powershell | Out-String | Invoke-Expression
```

**Non-obvious:**
- `rust-toolchain.toml` checked into repo root is picked up by `cargo` automatically
- `--profile minimal` for CI: installs only `rustc` + `cargo` (much faster)
- `rustup component add rust-src` is required for `rust-analyzer` and `cargo-expand`
- `cargo +nightly <cmd>` is cleaner than `rustup override set nightly` for one-off commands
- `rustup target add wasm32-unknown-unknown` enables WebAssembly

---

### fnm — Node.js versions

```
fnm install 22               # install Node 22
fnm install --lts            # install latest LTS
fnm install --latest         # install absolute latest
fnm list                     # installed versions
fnm list-remote              # available versions
fnm list-remote --lts        # LTS versions only
fnm use 22                   # switch active version (current shell)
fnm use --install-if-missing # install if not present, then switch
fnm default 22               # set global default
fnm current                  # show active version
fnm exec --using=20 node -e "console.log(process.version)"
fnm alias 22 my-alias
fnm uninstall 20
fnm env --use-on-cd | Out-String | Invoke-Expression  # pwsh auto-switch init
```

**Non-obvious:**
- `--version-file-strategy recursive` walks parent directories for `.node-version` / `.nvmrc`
- `FNM_RESOLVE_ENGINES=true` reads `engines.node` from `package.json`
- `fnm exec --using=lts` uses current LTS without hardcoding a version number

---

### rig — R versions

Local status: **not currently installed** on this workstation.

```
rig list                     # installed R versions
rig available                # R versions available to install
rig add release              # install latest stable R
rig add devel                # install R development build
rig add 4.4.0                # install specific version
rig add oldrel-1             # install previous release
rig default                  # show current default R version
rig default 4.4.0            # set default R version
rig rm 4.3.0                 # remove R version

# Windows system operations
rig system add-pak           # install pak package manager for active R
rig system setup-user-lib    # configure per-version user package library
rig system make-links        # create R-4.4, R-4.3 etc. in PATH
rig system rtools            # manage Rtools (compiler toolchain for R on Windows)
```

**Non-obvious:**
- `rig rstudio 4.3.0 project.Rproj` launches RStudio pinned to a specific R without changing system default
- `rig system setup-user-lib` creates `~/R/x86_64-pc-windows-gnu/4.4/` per-version library — packages for R 4.4 and R 4.3 never conflict
- `rig system add-pak` installs the `pak` R package manager (much faster than base `install.packages()`)

---

### mise — Polyglot

```
mise install node@22
mise install python@3.13
mise use node@22             # set version for current dir (writes mise.toml)
mise use --global node@22    # set global default
mise ls                      # list all installed tools
mise ls-remote node          # list available node versions
mise outdated                # check all tools for updates
mise upgrade                 # upgrade all tools

mise exec node@22 -- node script.js
mise env node@22
mise set MY_VAR=value
mise run build               # run task from mise.toml
mise watch build             # watch + rerun task on file change

mise edit                    # open mise.toml in editor
mise doctor                  # diagnose configuration issues
mise trust

mise plugins ls
mise plugins ls-remote
mise plugins install java

mise sync python --uv        # register uv-managed Pythons in mise
mise self-update
```

**Non-obvious:**
- `mise run` is a full task runner with `[tasks.build]` blocks, deps, env vars, file-watching
- `-E staging` flag loads `mise.staging.toml` — environment-specific configs
- `mise sync python --uv` lets mise discover Pythons installed by uv — the two tools cooperate
- `mise generate github-action` outputs a complete CI workflow with exact pinned versions

---

### proto — Polyglot (moonrepo)

```
proto install node 22
proto install bun
proto install python 3.13
proto versions node
proto status
proto outdated
proto pin node 22            # pin version in .prototools
proto pin --global node 22   # pin globally
proto exec node -- node script.js
proto bin node               # print path to node binary
proto upgrade                # update proto itself
proto diagnose
```

**Non-obvious:**
- `.prototools` is TOML — commit it to pin all tools in one file (like `rust-toolchain.toml` but polyglot)
- `proto install --build node` compiles Node from source
- `proto exec` never changes your active version — strictly isolated one-off execution
- proto ships `proto mcp` — an MCP server so AI agents can query and manage your toolchain

---

### chthonic / claudine — Repo Control Surface

Meta-CLI entrypoints for this repo. `chthonic` is the canonical shell; `claudine` is the compatibility wrapper.

```powershell
# Toolchain
.\scripts\chthonic.ps1 toolchain hierarchy    # ordered lane model + command ownership/paths
.\scripts\chthonic.ps1 toolchain verify       # extension host verifier
.\scripts\chthonic.ps1 toolchain scan --json  # JSON health scan
.\scripts\chthonic.ps1 toolchain paths        # effective PATH segments

# Language lanes (live version + path per tool)
.\scripts\chthonic.ps1 python lane
.\scripts\chthonic.ps1 ruby lane
.\scripts\chthonic.ps1 go lane
.\scripts\chthonic.ps1 bun lane
.\scripts\chthonic.ps1 rust lane
.\scripts\chthonic.ps1 r lane                 # R 4.5.3 + rv-r 0.19.0
.\scripts\chthonic.ps1 zig lane               # zv 0.10.0 + zig 0.16.0

# Commands surface
.\scripts\chthonic.ps1 commands counts
.\scripts\chthonic.ps1 commands inventory

# Memory / session
.\scripts\chthonic.ps1 memory map
.\scripts\chthonic.ps1 memory session
.\scripts\chthonic.ps1 memory cheatsheet      # → this file

# Status
.\scripts\chthonic.ps1 status                 # desktop-oriented overview

# Doctor (EOL + version gap checks via endoflife.date API)
.\scripts\chthonic.ps1 doctor                 # dry-run, checks ruby/python/bun/brush/rust/go
.\scripts\chthonic.ps1 doctor --fix           # apply fixes

# claudine compatibility wrapper (delegates to chthonic)
.\scripts\claudine.ps1 start                  # = chthonic status
.\scripts\claudine.ps1 repair                 # = chthonic doctor --dry-run
.\scripts\claudine.ps1 repair --fix           # = chthonic doctor --fix
```

**Note on `chthonic doctor`:** currently checks ruby, python, bun, brush, rust, go against endoflife.date API. R and Zig are not tracked by endoflife.date — use `Rscript --version` and `zig version` directly to verify floors.

---

### Agave / Solana CLI

Local status: installed (user-scoped bundle).

```
solana --version
agave-install --version
```

Verified: `solana-cli 3.1.9`, `agave-install 3.1.9`.
Bundle path: `C:\Users\<user>\AppData\Local\solana\install\releases\v3.1.9\solana-release\bin`

---

### AVM / Anchor

```
avm install latest
avm use latest
anchor --version
```

Verified: `anchor-cli 0.32.1`. AVM installed in `.cargo\bin`.

---

### OpenSSL / Native Cargo on Windows

If a native Rust crate fails on `openssl-sys`, bind a real Windows OpenSSL install:

```powershell
[Environment]::SetEnvironmentVariable('OPENSSL_DIR', 'C:\Program Files\OpenSSL-Win64', 'User')
[Environment]::SetEnvironmentVariable('OPENSSL_INCLUDE_DIR', 'C:\Program Files\OpenSSL-Win64\include', 'User')
[Environment]::SetEnvironmentVariable('OPENSSL_LIB_DIR', 'C:\Program Files\OpenSSL-Win64\lib\VC\x64\MD', 'User')
[Environment]::SetEnvironmentVariable('OPENSSL_NO_VENDOR', '1', 'User')
```

Do not rely on vendored OpenSSL via MSYS/Cygwin Perl on an MSVC Rust lane.

---

## §5 Version File Reference

| File | Read by | Written by |
|------|---------|------------|
| `.python-version` | uv, pyenv, mise | `uv python pin 3.13.11` |
| `.ruby-version` | rv, rbenv, mise | `rv ruby pin 4.0.1` |
| `.node-version` | fnm, mise | manual / `fnm alias` |
| `.nvmrc` | fnm, nvm, mise | manual |
| `rust-toolchain.toml` | cargo, rustup | manual |
| `.tool-versions` | mise, asdf | `mise use` |
| `mise.toml` | mise | `mise use`, `mise set` |
| `.prototools` | proto | `proto pin` |
| `rproject.toml` | rv-r | manual / `rv-r configure` |
| `rv.lock` | rv-r | `rv-r sync`, `rv-r upgrade` |
| `zig-toolchain.toml` | repo convention | manual |
| `.zigversion` | zv | `zv use <ver>` |

---

## §6 Ecosystem Landscape

### Node.js Version Managers (beyond bun)

bun is a runtime replacement, not a Node version switcher. For projects requiring a specific system Node:

| Tool | What it does | GitHub | Win11 | Status |
|------|-------------|--------|-------|--------|
| **fnm** | Fast Node Manager — switches Node version globally or per-shell | [Schniz/fnm](https://github.com/Schniz/fnm) | ✅ native, pwsh support | Active |
| **Volta** | Pins Node/npm/yarn per-project via `package.json` | [volta-cli/volta](https://github.com/volta-cli/volta) | ✅ MSI installer | Active |

**Recommendation:** fnm for global Node switching; Volta if per-project pinning in `package.json` is needed.

---

### Polyglot Managers (one tool, all languages)

| Tool | Domain | GitHub | Win11 | Notes |
|------|--------|--------|-------|-------|
| **mise** (formerly rtx) | Python, Node, Ruby, Go, Java, PHP, .NET, + 500+ via asdf plugins | [jdx/mise](https://github.com/jdx/mise) | ✅ experimental but functional | Single replacement for uv+rv+goup+fnm. Also manages env vars and task running. |
| **proto** (moonrepo) | Bun, Deno, Go, Node, Python, Rust, + WASM plugins | [moonrepo/proto](https://github.com/moonrepo/proto) | ✅ first-class | Cleaner plugin architecture (WASM vs shell scripts). Ships `proto mcp` — MCP server for AI agent toolchain queries. |
| **pkgx** | Polyglot runtime execution and package bootstrap | [pkgxdev/pkgx](https://github.com/pkgxdev/pkgx) | Unconfirmed locally | Executes tools on demand with minimal permanent system mutation. |
| **vfox** | Cross-language version manager | [version-fox/vfox](https://github.com/version-fox/vfox) | Unconfirmed locally | Plugin-driven language support. |

**Horse-Market note:** mise and proto are the currently grounded references here. `pkgx`, `vfox` are the same architectural class, not yet the repo's canonical picks.

---

### Shells (Rust-native)

| Tool | What it is | GitHub | Win11 | vs. brush |
|------|-----------|--------|-------|-----------|
| **brush** *(installed)* | Full bash/POSIX reimplementation in Rust | [reubeno/brush](https://github.com/reubeno/brush) | ✅ experimental | Bash-compatible — runs `.bashrc`, aliases, bash scripts unchanged |
| **Nushell** | Structured data shell — every output is a typed table | [nushell/nushell](https://github.com/nushell/nushell) | ✅ native | NOT POSIX-compatible. Complementary to brush. |
| **Fish** | UX-focused shell with autocomplete | [fish-shell/fish-shell](https://github.com/fish-shell/fish-shell) | Partial (WSL) | Rewritten in Rust 2024–2025. Limited Win11 native support. |

`brush` is the Rust-native compatibility substrate for Bash/POSIX workflows on Win11.

---

### Extended Language Coverage

**R Language:**

| Tool | Role | GitHub | Win11 | Status |
|------|------|--------|-------|--------|
| **rig** (r-lib) | R **version** manager | [r-lib/rig](https://github.com/r-lib/rig) | ✅ native | Active, production-ready |
| **rv-r** (A2-ai) | R **package** manager | [A2-ai/rv](https://github.com/A2-ai/rv) | ✅ native | Active, v0.19.0 |

Note: `spinel-coop/rv` = Ruby version manager. `A2-ai/rv` = R package manager. `r-lib/rig` = R version manager. In this repo: `rv` reserved for Ruby, `rv-r` for the R package manager in all prose and scripts.

**Zig:**

| Tool | GitHub | Win11 | Notes |
|------|--------|-------|-------|
| **zv** | [weezy20/zv](https://github.com/weezy20/zv) | ✅ (PowerShell installer) | Rust-native, supports `.zigversion`, inline `zig +<version>` syntax. v0.10.0. Current Zig: `0.16.0`. |

`zigup` (Zig-written) and `zvm` (Go-written) exist but only `zv` is Rust-native.

**Node.js (additional):**

| Tool | GitHub | Win11 | Notes |
|------|--------|-------|-------|
| **snm** | [numToStr/snm](https://github.com/numToStr/snm) | Unconfirmed | Rust-native Node version manager |
| **bum** | [owenizedd/bum](https://github.com/owenizedd/bum) | Unconfirmed | Rust-native Bun version manager (manages bun versions, not Node) |

**Godot:**

| Tool | GitHub | Win11 | Notes |
|------|--------|-------|-------|
| **gdvm** | [adalinesimonian/gdvm](https://github.com/adalinesimonian/gdvm) | Likely (Rust cross-platform) | Godot Engine version manager in Rust |

**Ruby (alternative):**

| Tool | GitHub | Win11 | Notes |
|------|--------|-------|-------|
| **frum** | [TaKO8Ki/frum](https://github.com/TaKO8Ki/frum) | Unconfirmed | Rust-native Ruby version manager — predates rv |

---

### Gaps — Languages with No Rust-native Manager

| Language | Status | Practical path |
|----------|--------|----------------|
| **Lua** | No Rust-native version manager | mise asdf plugin |
| **PHP** | `phpup` ([masan4444/phpup](https://github.com/masan4444/phpup)) — Windows WIP | mise asdf plugin |
| **Elixir / Erlang** | No Rust-native manager | mise asdf plugin |
| **Crystal** | No Rust-native manager | mise asdf plugin |
| **Java/JVM / Kotlin** | No Rust-native manager | mise or proto |
| **.NET** | No Rust-native manager | mise plugin or Microsoft dotnet-install |
| **R (version)** | `rig` (Rust, Win11 native) ✅ — gap is now closed | rig |
| **Zig** | `zv` (Rust, Win11 native) ✅ — gap is now closed | zv |

---

### Rust-Enhanced Infrastructure Beyond Version Managers

| Ecosystem / Tool | Role | Notes |
|------------------|------|-------|
| **brush** | Bash/POSIX shell | Rust-native shell/runtime substrate for Win11 Bash-compatible workflows. |
| **mlua** | Lua interop/bindings | Safe Rust bridge to the Lua runtime. |
| **Wirefilter** | Embedded rules/filter engine | Cloudflare example of Rust as a safe embedded interpreter substrate. |
| **Cobalt** | COBOL compiler | Rust pushing into legacy enterprise compiler territory. |
| **Mago** | PHP formatter/linter/static analysis | Rust replacing slow self-hosted tooling in a dynamic-language ecosystem. |
| **Explorer** | Elixir dataframe backend over Polars | Rust acceleration under a high-level host VM. |
| **jlrs** | Julia ↔ Rust bridge | Rust orchestrating scientific compute interop. |

---

### Scientific / Conda Ecosystem

| Tool | What it is | GitHub | Win11 |
|------|-----------|--------|-------|
| **pixi** | Project-scoped environment manager over conda-forge (Python, R, C++, 30K+ packages) | [prefix-dev/pixi](https://github.com/prefix-dev/pixi) | ✅ native |

Not a version switcher — manages per-project environments like a Rust-native conda/mamba.

---

## §7 EndOfLife.date API

**Base URL:** `https://endoflife.date/api/`
**Auth:** None. Rate limit: CDN-level (static JSON, effectively unlimited for light use).
**OpenAPI spec:** https://endoflife.date/docs/api/v1/

### Endpoints

```
GET /api/all.json                    # All tracked product slugs (~380+ products)
GET /api/{product}.json              # All release cycles for a product
GET /api/{product}/{cycle}.json      # Single cycle details
```

### Response shape (per cycle)

```json
{
  "cycle": "3.12",
  "releaseDate": "2023-10-02",
  "eol": "2028-10-02",
  "latest": "3.12.9",
  "latestReleaseDate": "2025-02-04",
  "lts": false
}
```

### Language coverage

| Language | Tracked | Slug |
|----------|---------|------|
| Python | ✅ | `python` |
| Ruby | ✅ | `ruby` |
| Go | ✅ | `go` |
| Node.js | ✅ | `nodejs` |
| Rust | ✅ | `rust` |
| R | ❌ | not tracked |
| Zig | ❌ | not tracked |

**Used by:** `chthonic doctor` for version currency checks (ruby, python, bun, brush, rust, go).
R and Zig are not tracked — verify via `Rscript --version` and `zig version` directly.

---

## §8 OxidizedIndex Concept

**The gap:** no structured, queryable index of Rust-native toolchain managers organized by language domain, with version currency and Windows support signals.

### What it would do

1. **Crawl** — GitHub Search API (`topic:version-manager language:rust`) + crates.io keyword search + awesome-version-managers list → deduplicated candidate set
2. **Classify** — per candidate: language domain, tool type, Windows support (from README/CI matrix), maintenance status
3. **Probe** — `cargo install <crate>` — does it compile cleanly on Win11? Run the tool's core workflow.
4. **Enrich** — cross-reference against endoflife.date: fetch latest stable version and EOL date per language
5. **Output** — `verified.json`: structured manifest with `win11_verified` (actual probe, not README badge)

```json
{
  "crate": "phpup",
  "domain": "php",
  "compiled": true,
  "smoke_passed": true,
  "version_file": ".php-version",
  "eol_latest": "8.4.4",
  "eol_date": "2028-12-31",
  "win11_claimed": false,
  "win11_verified": true
}
```

### Minimal viable shape

```
oxidized-index/
├── src/
│   ├── crawl.rs       # GitHub API + crates.io + static lists
│   ├── classify.rs    # README/CI matrix parsing for Windows signal
│   ├── probe.rs       # cargo install + smoke test per tool
│   ├── enrich.rs      # endoflife.date cross-reference
│   └── report.rs      # JSON/Markdown/TOML output
├── data/
│   ├── known.toml     # Seed list (hand-curated — from this doc)
│   └── probes.toml    # Per-tool smoke test commands
└── output/
    ├── index.json     # Full manifest with probe results
    └── verified.json  # Subset: tools that passed compilation probe
```

### The Windows-Native Collapse

"No Win11 support" for a Rust-native tool means the maintainer doesn't test on Windows — not that it doesn't work. The real situation: any pure-Rust crate compiles to `.exe` via `cargo install <crate>`. `brush` eliminates shell-script compatibility issues. The compilation probe IS the real Windows test.

### Horse-Market Condition

Stars, download counts, and "Win11 support" badges are surface signals. `frum` (653 stars, Ruby) has been dormant for years. `zv` (33 stars, Zig) is actively maintained. The OxidizedIndex needs a *compilation probe* layer to produce a **verified registry**, not just a curated list.

### Seed data (research-verified, April 2026)

| Language | Tool | crate | Domain |
|----------|------|-------|--------|
| Python | uv | `uv` | runtime + packages |
| Ruby | rv | *(binary release)* | runtime |
| Ruby | frum | `frum` | runtime (alt) |
| Go | goup | *(binary release)* | runtime |
| Node.js | fnm | `fnm` | runtime |
| Node.js | volta | *(binary release)* | runtime + project pin |
| R | rig | *(binary release)* | runtime |
| R | rv-r (A2-ai) | `rv` | packages |
| Zig | zv | `zv` | runtime |
| Polyglot | mise | `mise` | runtime + tasks |
| Polyglot | proto | `proto` | runtime + plugins |
| PHP | phpup | `phpup` | runtime (WIP) |
| Godot | gdvm | `gdvm` | runtime |
| Shell (bash) | brush | `brush-shell` | shell |

### Where it fits

**Delegation path when ready:**
- Claude: spec + `data/known.toml` + `data/probes.toml` seed
- Codex: implement `src/` in Rust — crawl + classify + enrich + report
- Gemini: periodic sweep runs to refresh `output/index.json` nightly (daemon-compatible)

---

## §9 Meta-CLI Sync Map

> Maps §4 per-tool sections to their corresponding `chthonic.ps1` functions.
> When updating per-tool command data in §4, update the corresponding `Invoke-*Lane` function in sync.
> When the `Invoke-*Lane` function changes state (new fields, new paths), update §4 to match.

| §4 Section | chthonic command | `chthonic.ps1` function | Lane data emitted |
|------------|-----------------|------------------------|-------------------|
| uv — Python | `chthonic python lane` | `Invoke-PythonLane` | uv version, Python version, path |
| rv — Ruby | `chthonic ruby lane` | `Invoke-RubyLane` | rv version, Ruby version, DevKit, ridk |
| goup — Go | `chthonic go lane` | `Invoke-GoLane` | goup version, Go version, path |
| bun — JS/TS | `chthonic bun lane` | `Invoke-BunLane` | bun version |
| rustup — Rust | `chthonic rust lane` | `Invoke-RustLane` | rustup, cargo, active toolchain |
| rv-r — R packages | `chthonic r lane` | `Invoke-RLane` | R version, Rscript, rv-r version, binding |
| zv — Zig | `chthonic zig lane` | `Invoke-ZigLane` | zv version, zig version, paths |
| brush | `chthonic doctor` | `Invoke-Doctor` | brush version via endoflife.date API |

**`chthonic doctor` coverage (endoflife.date API):** ruby, python, bun, brush, rust, go.

**Not in doctor (no endoflife.date entry):** R (use `Rscript --version`), Zig (use `zig version`).

**`Show-PolyglotStatus`** (`chthonic status`) reads the `tools[]` map and emits all lanes in one pass — current values for all 8 rows above in one command.

**Cherry-pick pattern:** to sync a new version floor (e.g. Zig 0.17.0):
1. Update §1 validated versions table
2. Update §4 zv section (`zv use stable`)
3. Update `zig-toolchain.toml` pin
4. Verify `Invoke-ZigLane` still reads the correct path (no change needed if `~/.zv/bin/zig.exe` stays)
5. Update §14.9 in `technical-directives.instructions.md` if it's a floor change

---

*Authored: 2026-03-11. Collapsed: 2026-04-20. Sources: official repos, GitHub topics API, lib.rs, crates.io, awesome-version-managers, endoflife.date API docs.*
