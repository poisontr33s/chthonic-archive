---
sid: DOC_OXIDIZED_CHEATSHEET
title: Oxidized Toolchain — Command Cheatsheet & Cross-Tool Pattern Map
type: reference
status: canonical
created: 2026-03-11
updated: 2026-03-23 (Windows Ruby 4.0.2 + OpenSSL + Agave/Anchor lane repairs)
authors:
  - Claude
audience:
  - all
tags:
  - toolchain
  - cheatsheet
  - oxidized
  - commands
  - qol
---

<!--
@SID:    DOC_OXIDIZED_CHEATSHEET
@Type:   Reference / Cheatsheet
@Context: Toolchain QoL — command discoverability
-->

# Oxidized Toolchain Cheatsheet

> Problem this solves: you have the tools but don't know what they can do beyond the basics.
> Structure: cross-tool pattern map first (find by concept), per-tool quick ref second.
> Full command surfaces: documented in source READMEs — this surfaces the non-obvious.
> Rationale: [OXIDIZED_TOOLCHAIN_RATIONALE.md](OXIDIZED_TOOLCHAIN_RATIONALE.md)
> Migration memory: [LAPTOP_TO_DESKTOP_EMIGRATION.md](../codex/artifacts/LAPTOP_TO_DESKTOP_EMIGRATION.md)
> Local note: `uv`, `rv`, `goup`, `bun`, `cargo`, `brush`, `zv`, and `rv-r` are installed here. `rig` remains documented as an R version-manager option, but this workstation centers the unmanaged current `R` runtime plus `rv-r`.

---

## Naming Canon

- `rv` = Ruby manager
- `rig` = R version manager
- `R rv` / `rv-r` = the A2-ai R package manager in documentation only
- `zv` = Rust-native Zig version manager

Use that naming in repo docs and tasks so `rv` does not collide with the Ruby lane.
Repo wrapper: `scripts/rv-r.ps1`

---

## Cross-Tool Pattern Map

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

## Per-Tool Quick Reference

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
- In this workspace, prefer `rv` directly. `rvw` is only a fallback when a shell still binds `rv` to PowerShell `Remove-Variable`.
- `rv r <cmd>` is the short alias for `rv run <cmd>`; e.g. `rv r ruby -v`, `rv r ridk version`, `rv r gem env`

**Windows Ruby lane: what owns what**
- `rv` owns the Ruby runtime itself: install, switch, pin, and isolated gem tools.
- RubyInstaller DevKit / `MSYS2` owns the native build toolchain around Ruby: `gcc`, `make`, `pacman`, UCRT64 headers/libs.
- They cooperate, but they are not the same tool. `rv` gives you `ruby`; DevKit/MSYS gives Ruby native-extension gems something to compile with.

**Windows Ruby lane: update + verify**

```powershell
rv selfupdate                        # update rv itself
rv ruby list                         # see installed + available Rubies
rv ruby install 4.0.2               # install the target Ruby runtime
rv ruby pin 4.0.2                   # pin project version explicitly
rv ruby find 4.0.2                  # show the exact binary path for 4.0.2
rv r ruby -v                        # verify active runtime quickly
rv r gem env                        # inspect active gem paths
rv r ridk version                   # verify RubyInstaller + MSYS2 binding

ruby --version                      # verify active Ruby
gcc --version                       # verify C compiler from DevKit/MSYS2
make --version                      # verify make
pacman -Q mingw-w64-ucrt-x86_64-gcc make   # verify package ownership/versions
where.exe ruby                      # verify command resolution on Windows
where.exe ridk
where.exe gcc
```

**Windows Ruby lane: MSYS2 / DevKit maintenance**

```powershell
pacman -Syu                         # full package database + system update
pacman -Qu                          # list pending package upgrades
pacman -S mingw-w64-ucrt-x86_64-gcc mingw-w64-ucrt-x86_64-make make
```

**Windows Ruby lane: `ridk` component sequencing**

Run the RubyInstaller components one step at a time, not as `1 2 3` in one shot:

```powershell
rv r ridk install 1                # install MSYS2 base into the active rv Ruby
rv r ridk install 2                # optional pacman system update
rv r ridk install 3                # install the MINGW/UCRT dev toolchain
```

Validated migration pattern for `ruby-4.0.2`:

```powershell
rv ruby install 4.0.2
rv ruby pin 4.0.2
rv r ridk install 1
rv r ridk install 3
rv r ridk exec pacman -S --needed --noconfirm mingw-w64-ucrt-x86_64-tcl mingw-w64-ucrt-x86_64-tk
rv r ridk version
```

Do not treat `ridk install 1 2 3` as the preferred recovery path when you are intentionally rebuilding the lane. Base first, toolchain second, update only when you actually want the package refresh.

**Windows Ruby lane: migrate old gems/settings into rv**

Library gems that belong to the active Ruby go into the active runtime:

```powershell
rv r gem install --no-document colorize mini_portile2 sqlite3
```

CLI gems that should stay isolated go in the tool lane:

```powershell
rv tool install --gem-server https://rubygems.org/ bundler-audit
rv tool install --gem-server https://rubygems.org/ thor
rv tool list
rv tool run bundler-audit --version
rv tool run thor version
```

If Bundler build flags still point at an old `C:\Ruby*` tree, rewrite them to the active `rv` Ruby's `ucrt64` tree:

```powershell
rv r bundle config list
rv r bundle config set --global build.tk "--with-tcltk-framework=false --with-tcl-lib=C:/Users/<user>/AppData/Roaming/rv/rubies/ruby-4.0.2/msys64/ucrt64/lib --with-tk-lib=C:/Users/<user>/AppData/Roaming/rv/rubies/ruby-4.0.2/msys64/ucrt64/lib --with-tcl-include=C:/Users/<user>/AppData/Roaming/rv/rubies/ruby-4.0.2/msys64/ucrt64/include --with-tk-include=C:/Users/<user>/AppData/Roaming/rv/rubies/ruby-4.0.2/msys64/ucrt64/include"
```

**Observed package names in this workspace**
- `mingw-w64-ucrt-x86_64-gcc`
- `mingw-w64-ucrt-x86_64-gcc-libs`
- `mingw-w64-ucrt-x86_64-make`
- `make`
- `mingw-w64-ucrt-x86_64-tcl`
- `mingw-w64-ucrt-x86_64-tk`

**Mental model**
- `rv` answers: "which Ruby am I using?"
- `MSYS2` / `pacman` answers: "what native toolchain is Ruby compiling against?"

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
goup init powershell         # emit/init shell integration material
goup remove 1.25.0           # remove a version
goup self update             # update goup itself
```

**Non-obvious:**
- `goup update` is not a separate upgrade verb; it is an alias of `goup install`
- `goup self update` is the manager self-update path
- `goup install` with no argument means "install current stable"; `goup install stable` is the explicit form
- `goup install go`, `goup update go`, `goup update all` and similar words are parsed as version strings and fail semver parsing
- For an explicit version, prefer `goup install 1.26.1`; use `--use-raw-version` when you intentionally want raw version parsing
- `goup install tip` tracks Go's main development branch — useful for testing your code against unreleased Go
- `goup default` changes the default Go version; `goup shell` is the shell-scoped switch
- `GOUP_GO_HOST=golang.google.cn goup install` uses Chinese mirror (or any custom mirror)
- `goup env` is the quickest truth source for current registry/home/version variables

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
- `brush -c` is the normal bash-like mode. `BASH_VERSION` is set (`5.2.15(1)-release`) and `set -o` shows `posix off`.
- `brush --posix` does set `set -o posix` to `on`, but it is not a full hard-POSIX shell fence in this build:
  - arrays like `x=(a b)` still parse
  - `[[ ... ]]` still parses
  - `shopt -p extglob` still reports `extglob` enabled
- `brush --sh` is materially stricter than `--posix`:
  - `set -o` also shows `posix on`
  - array syntax errors near `(`
  - `pwd` remains a shell builtin
  - `echo` and `printf` were not available as builtins in the tested Windows path; direct `echo hi` / `printf ...` failed with `command not found`
- `brush --noenv` starts with `HOME` unset and `PATH` empty. Builtins still work; external commands should not be assumed.
- In Windows batch / `-c` mode, bare external command names are not trustworthy even when `command -v` resolves them:
  - `command -v bash` and `command -v go` can report `C\bash` / `C\go`
  - `bash --version` and `go version` can still fail with `command not found`
  - absolute Windows executable paths such as `C:/Users/eldno/.cargo/bin/brush.exe --version` do work
  - MSYS-style paths like `/c/Users/.../brush.exe` did not work in `brush -c`
- If you need the real GNU/MSYS bash from inside brush on this workstation, invoke the executable explicitly:
  - `C:/Users/eldno/AppData/Roaming/rv/rubies/ruby-4.0.2/msys64/usr/bin/bash.exe`
  - once inside that shell, `bash` resolves to `/usr/bin/bash`, `echo`/`printf` are normal bash builtins, and `shopt -p extglob` behaves like GNU bash rather than brush
- `/dev/null` is not a safe sink in tested Windows brush runs; `echo hi >/dev/null` failed with `C:/dev/null` missing. `NUL` worked.
- Interactive `set` on this workstation exposed a Windows-specific split:
  - `PATH=''`
  - `Path='C:\...;...'` still contained the real Windows search path
  - inference: interactive command discovery is at least partially consulting Windows `Path`, which helps explain why prompt-time behavior can differ from `brush -c`
- Interactive prompt/version state also appears inconsistent:
  - prompt showed `brush.exe-0.4$` with `PS1='\s-\v\$ '`
  - `BRUSH_VERSION=0.3.0`
  - `brush --version` reported `0.3.0`
  - treat `brush --version` / `BRUSH_VERSION` as authoritative, and treat the prompt's `0.4` as a likely brush prompt/version-display quirk

**Practical Windows rescue snippet for `~/.brushrc`:**

```sh
if [ -z "$PATH" ] && [ -n "$Path" ]; then
  PATH="$Path"
  export PATH
fi

if [ -n "$MSYS2_HOME" ] && [ -x "$MSYS2_HOME/usr/bin/bash.exe" ]; then
  alias bash="$MSYS2_HOME/usr/bin/bash.exe"
fi

if [ -n "$MSYS2_HOME" ] && [ -x "$MSYS2_HOME/usr/bin/sh.exe" ]; then
  alias sh="$MSYS2_HOME/usr/bin/sh.exe"
fi
```

This was validated locally with:
- `brush -i --rcfile <file> -c 'bash --version'` -> succeeded once `PATH` was populated from `Path`
- `bash --version` then resolved to the GNU/MSYS bash shipped in the active Ruby DevKit lane

**Startup-file behavior verified in a disposable test home:**
- `brush -i -c ...` loaded both `~/.bashrc` and `~/.brushrc`
- `brush -i --norc -c ...` suppressed rc loading
- `brush -i --rcfile <file> -c ...` loaded only the specified rc file and skipped default rc files
- `brush -l -c ...` and `brush -l -i -c ...` did not load `~/.profile` or `~/.bash_profile` in these Windows tests

**Mental model:**
- `pwsh` remains the canonical shell in this repo
- `brush` is the sanctioned bash-compatible companion when you need Bourne/bash semantics on Windows
- prefer `brush -c '...'` for bash-ish one-shots
- prefer `brush --sh -c '...'` only when you explicitly want to probe `/bin/sh`-style compatibility
- for Windows batch probes, prefer builtins or absolute `.exe` paths over bare external command names
- do not assume `--posix` and `--sh` are interchangeable

---

### Agave / Solana CLI

```
solana --version                    # show installed Solana CLI version
agave-install --version             # show installed Agave installer/update lane
where.exe solana
where.exe agave-install
```

**Windows lane note:**
- In this workstation pass, the official Agave Windows installer required elevation.
- The working non-admin fallback was the official prebuilt Windows Agave release bundle, which already contained both:
  - `solana.exe`
  - `agave-install.exe`
- User-scoped bundle path used here:
  - `C:\Users\<user>\AppData\Local\solana\install\releases\v3.1.9\solana-release\bin`

**Verified locally:**
- `solana-cli 3.1.9`
- `agave-install 3.1.9`

---

### AVM / Anchor

```
avm install latest                 # install latest Anchor CLI via AVM
avm use latest                     # activate latest Anchor CLI
anchor --version                   # verify active Anchor CLI
where.exe avm
where.exe anchor
```

**Windows lane note:**
- `avm` installation landed in Cargo's bin lane (`.cargo\bin`).
- On Windows without symlink privilege, `avm use latest` can fall back from symlink to copy.
- That fallback is acceptable as long as `anchor --version` resolves afterward.

**Verified locally:**
- `anchor-cli 0.32.1`

---

### OpenSSL / Native Cargo on Windows

If a native Rust crate on MSVC fails on `openssl-sys`, bind a real Windows OpenSSL install instead of assuming Visual Studio handled it:

```powershell
[Environment]::SetEnvironmentVariable('OPENSSL_DIR', 'C:\Program Files\OpenSSL-Win64', 'User')
[Environment]::SetEnvironmentVariable('OPENSSL_INCLUDE_DIR', 'C:\Program Files\OpenSSL-Win64\include', 'User')
[Environment]::SetEnvironmentVariable('OPENSSL_LIB_DIR', 'C:\Program Files\OpenSSL-Win64\lib\VC\x64\MD', 'User')
[Environment]::SetEnvironmentVariable('OPENSSL_NO_VENDOR', '1', 'User')
[Environment]::SetEnvironmentVariable('VCPKG_ROOT', 'C:\Users\<user>\vcpkg', 'User')
```

**Do not rely on:**
- vendored OpenSSL via MSYS/Cygwin Perl on an MSVC Rust lane
- Visual Studio alone to surface a usable OpenSSL install to Cargo

**Verified locally against:**
- `extensions/chthonic-archive/native/entropy-ledger-host`
- full native workspace `cargo check --manifest-path extensions/chthonic-archive/native/Cargo.toml`

---

### chthonic — Repo Control Surface

These are the repo-native meta-commands that surface the repaired workstation state:

```powershell
.\scripts\chthonic.ps1 commands counts
.\scripts\chthonic.ps1 commands inventory
.\scripts\chthonic.ps1 toolchain hierarchy
.\scripts\chthonic.ps1 toolchain verify
.\scripts\chthonic.ps1 toolchain scan --json
.\scripts\chthonic.ps1 toolchain paths

.\scripts\chthonic.ps1 memory map
.\scripts\chthonic.ps1 memory migration
.\scripts\chthonic.ps1 memory next
.\scripts\chthonic.ps1 memory cheatsheet
.\scripts\chthonic.ps1 memory session
.\scripts\chthonic.ps1 r lane
.\scripts\chthonic.ps1 zig lane
```

Compatibility wrapper:

```powershell
.\scripts\claudine.ps1 commands counts
.\scripts\claudine.ps1 toolchain hierarchy
.\scripts\claudine.ps1 memory session
```

**Intent:**
- `commands counts` gives the current surface arithmetic: `23` canonical domains, `8` compatibility domains, `68` canonical documented forms, `76` direct documented forms, `17` nested action aliases
- `commands inventory` shows the live domain/action matrix, compatibility watchlist, and `claudine` forward reach (`153` combined entrypoint forms across both executable names)
- `toolchain hierarchy` shows the ordered lane model plus current command ownership/paths
- `toolchain verify` runs the extension host verifier in a fresh env merge
- `memory session` recalls the winning state, order, anti-patterns, and next hierarchy from the migration/session artifacts
- `r lane` shows the current unmanaged `R` runtime plus `rv-r`
- `zig lane` shows `zv` and active `zig`

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
- `bun run --hot` enables HMR for server processes — edits reload without restarting
- `bun install --minimum-release-age 259200` (3 days) blocks packages published < 72 hours ago — supply chain protection
- `bun install --linker=isolated` enables pnpm-style strict isolation (no hoisting)
- `bun install --os linux --cpu x64` installs native binaries for a different platform (cross-install for Docker)
- `bun pm migrate` migrates from npm/yarn/pnpm lockfile to bun.lock

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
fnm exec --using=20 node -e "console.log(process.version)"  # one-off
fnm alias 22 my-alias        # create named alias
fnm uninstall 20             # remove version
fnm env --use-on-cd | Out-String | Invoke-Expression  # pwsh auto-switch init
```

**Non-obvious:**
- `--version-file-strategy recursive` walks parent directories for `.node-version` / `.nvmrc` (like nvm behavior)
- `FNM_RESOLVE_ENGINES=true` reads `engines.node` from `package.json` — no version file needed
- `fnm exec --using=lts` uses whatever is currently the latest LTS without hardcoding a version number
- `FNM_NODE_DIST_MIRROR` for custom Node.js distribution mirrors (corporate proxies / air-gapped)

---

### rig — R versions

Local status: not currently installed on this workstation.

```
rig list                     # installed R versions (alias: ls)
rig available                # R versions available to install
rig add release              # install latest stable R
rig add devel                # install R development build
rig add 4.4.0                # install specific version
rig add oldrel-1             # install previous release
rig default                  # show current default R version
rig default 4.4.0            # set default R (what 'R' and 'Rscript' point to)
rig resolve release          # resolve symbolic name to actual version number
rig rm 4.3.0                 # remove R version (alias: remove, del, delete)
rig rstudio                  # launch RStudio with default R
rig rstudio 4.4.0            # launch RStudio with specific R version
rig rstudio 4.4.0 myproject.Rproj  # launch RStudio with R + project

# Windows system operations
rig system add-pak           # install pak package manager for active R
rig system setup-user-lib    # configure per-version user package library
rig system make-links        # create R-4.4, R-4.3 etc. in PATH
rig system clean-registry    # clean stale R registry entries
rig system rtools            # manage Rtools (compiler toolchain for R on Windows)
```

**Non-obvious:**
- `rig rstudio 4.3.0 project.Rproj` — launches RStudio pinned to a specific R without changing system default
- `rig system setup-user-lib` creates `~/R/x86_64-pc-windows-gnu/4.4/` per-version library — packages for R 4.4 and R 4.3 never conflict
- `rig system add-pak` installs the `pak` R package manager which is much faster than base `install.packages()`
- `rig add oldrel-1` / `oldrel-2` symbolic names — don't need to know exact version numbers
- `rig system rtools` manages Rtools (the Windows C/C++ compiler for R packages with native code)

---

### R rv — R packages

`A2-ai/rv` is the Rust-native R package manager discussed in the reference doc.

Repo naming rule:

- write `R rv` or `rv-r` in docs and tasks
- do not use bare `rv` for R inside this repo, because bare `rv` is reserved for the Ruby lane

Local status: installed via repo wrapper.

Wrapper path in this repo:

```powershell
pwsh -NoProfile -File scripts/rv-r.ps1 <args>
```

Wrapper lookup order:

1. `R_RV_BIN`
2. `R_RV_HOME`
3. `%USERPROFILE%\.r-rv\bin\rv.exe`

Architectural cues from the research set:

- `rproject.toml` is the explicit project manifest / lock anchor
- `.rv` is the local project environment
- console ergonomics are centered around calls like `.rv$sync()` and `.rv$add("pkg")`

---

### zv — Zig versions

```
zv --version                 # show installed zv version
zv install 0.13.0            # install specific Zig version
zv use 0.13.0                # switch active Zig version
zv list                      # list installed Zig versions
zv current                   # show active Zig version
```

**Non-obvious:**
- `zv` is the Rust-native Zig lane this repo references
- `.zigversion` is the project-facing version file in the `zv` ecosystem
- `zv use <version>` is the core project-aware switching flow
- keep `zv` distinct from `zigup` and `zvm` when writing repo docs

---

### mise — Polyglot

```
# Install + use tools
mise install node@22         # install specific version
mise install python@3.13     # install
mise use node@22             # set version for current dir (writes mise.toml)
mise use --global node@22    # set global default
mise ls                      # list all installed tools
mise ls-remote node          # list available node versions
mise outdated                # check all tools for updates
mise upgrade                 # upgrade all tools

# Environment
mise exec node@22 -- node script.js   # run with specific version
mise env node@22                      # print env vars to set
mise set MY_VAR=value                 # set env var in mise.toml
mise run build                        # run a task from mise.toml
mise watch build                      # watch + rerun task on file change

# Config
mise edit                    # open mise.toml in editor
mise fmt                     # format mise.toml
mise doctor                  # diagnose configuration issues
mise trust                   # mark config file as trusted

# Plugins
mise plugins ls              # list installed plugins
mise plugins ls-remote       # list available plugins
mise plugins install java    # add java plugin
mise search java             # search for tools

# Generate
mise generate github-action  # output GitHub Actions workflow
mise generate git-pre-commit # output pre-commit hook
mise generate task-docs      # document tasks in mise.toml

# Sync with other tools
mise sync python --uv        # register uv-managed Pythons in mise
mise self-update             # update mise itself
```

**Non-obvious:**
- `mise run` is a full task runner — define tasks in `mise.toml` with `[tasks.build]` blocks, deps, env vars, file-watching
- `mise exec --` vs `mise shell`: exec runs one command; shell changes the current shell session
- `-E staging` flag loads `mise.staging.toml` — environment-specific configs without duplicating tool versions
- `mise sync python --uv` lets mise discover Pythons installed by uv — the two tools cooperate
- `mise generate github-action` outputs a complete CI workflow with exact pinned versions from your config
- `[task.test] depends = ["build"]` in `mise.toml` — task dependency graph, run in correct order automatically

---

### proto — Polyglot (moonrepo)

```
proto install node 22        # install Node 22
proto install bun            # install latest bun
proto install python 3.13    # install Python 3.13
proto install --build node   # compile from source
proto versions node          # list installed Node versions
proto status                 # show all current tool versions
proto outdated               # check for newer versions
proto pin node 22            # pin version in .prototools
proto pin --global node 22   # pin globally
proto exec node -- node script.js  # run with specific version
proto bin node               # print path to node binary
proto upgrade                # update proto itself
proto plugin ls              # list installed plugins
proto clean                  # clean old cached data
proto diagnose               # diagnose environment
```

**Non-obvious:**
- `.prototools` is TOML — commit it to pin all tools for a project in one file (like `rust-toolchain.toml` but for everything)
- `proto install --build node` compiles Node from source — useful when no prebuilt binary exists for your target
- `proto exec` never changes your active version — strictly isolated one-off execution
- `proto pin --global` sets a system fallback — project `.prototools` always takes precedence
- proto ships `proto mcp` — an MCP server so AI agents (including Claude) can query and manage your toolchain

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
rustup toolchain link my-build /path/to/custom/rust  # use local build

rustup override set nightly  # this directory uses nightly (writes override)
rustup override unset        # remove override for current dir
rustup override list         # all active overrides

rustup target add wasm32-unknown-unknown   # add cross-compile target
rustup target add x86_64-unknown-linux-gnu
rustup target list --installed
rustup target remove wasm32-unknown-unknown

rustup component add rustfmt clippy rust-src rust-analyzer
rustup component list --installed
rustup component remove rust-docs

rustup run nightly -- rustc --version   # one-off with specific toolchain
cargo +nightly build                     # inline toolchain selection

rustup self update           # update rustup itself
rustup check                 # check for updates without installing
rustup completions powershell | Out-String | Invoke-Expression  # pwsh completions
```

**Non-obvious:**
- `rust-toolchain.toml` checked into repo root is picked up by `cargo` automatically — everyone on the project uses the same toolchain
- `--profile minimal` for CI: installs only `rustc` + `cargo`, skips docs and other components (much faster)
- `rustup component add rust-src` is required for `rust-analyzer` to work fully and for `cargo-expand`
- `rustup toolchain link` lets you name a locally-compiled Rust build — useful for testing compiler patches
- `cargo +nightly <cmd>` is cleaner than `rustup override set nightly` for one-off nightly commands
- `rustup target add wasm32-unknown-unknown` enables WebAssembly; combine with `wasm-pack` for web output

---

## Version File Reference

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

---

## OxidizedIndex — Concept for Tracking This Space

No single API or tool tracks Rust-native toolchain managers by domain. The gap:

### What would solve it

A Rust tool (`oxidized-index`) that:
1. **Crawls** GitHub Search API (`topic:version-manager language:rust`) + crates.io keywords
2. **Probes** each candidate: `cargo install <crate>` — does it compile? Smoke test the core command.
3. **Enriches** from endoflife.date API (`GET /api/{lang}.json`) — what's the current stable + EOL date for the managed language?
4. **Outputs** `verified.json` — structured manifest with `win11_verified` (actual probe, not README badge)

### Why the Win11 badge is a Horse-Market signal

A tool claiming "no Windows support" just means the maintainer doesn't test on Windows. With `cargo` available:
- Pure-Rust crates compile to `.exe` via `cargo install <crate>` — no additional tooling
- `brush` runs Unix shell install scripts natively — eliminates the remaining OS discrepancy

The compilation probe IS the real Windows test. The reference doc is the verified result of doing that manually.

### Data sources

| Source | Endpoint | Auth |
|--------|----------|------|
| GitHub Search API | `api.github.com/search/repositories?q=topic:version-manager+language:rust` | None (60 req/h unauth, 5000 auth) |
| crates.io API | `crates.io/api/v1/crates?keyword=version-manager` | None |
| endoflife.date | `endoflife.date/api/{product}.json` | None |
| awesome-version-managers | Static GitHub README | N/A — seed data |

### Seed data (from this cheatsheet — already research-verified)

| Language | Tool | crate | Domain |
|----------|------|-------|--------|
| Python | uv | `uv` | runtime + packages |
| Ruby | rv | *(binary release)* | runtime |
| Ruby | frum | `frum` | runtime (alt) |
| Go | goup | *(binary release)* | runtime |
| Node.js | fnm | `fnm` | runtime |
| Node.js | volta | *(binary release)* | runtime + project pin |
| R | rig | *(binary release)* | runtime |
| R | R rv (A2-ai) | `rv` | packages |
| Zig | zv | `zv` | runtime |
| Polyglot | mise | `mise` | runtime + tasks |
| Polyglot | proto | `proto` | runtime + plugins |
| PHP | phpup | `phpup` | runtime (WIP) |
| Godot | gdvm | `gdvm` | runtime |
| Shell (bash) | brush | `brush-shell` | shell |

---

*Authored: 2026-03-11. Command data sourced from official docs for uv, rv, goup, bun, fnm, rig, mise, proto, rustup.*

