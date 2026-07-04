---
date: 2026-06-30
agent: Codex
substrate: CLAUDEBASE
status: inventory-first challenge plan
project: Extreme Haute Couture - Movement 1
---

# Wide Sweeps and Inventory Management - Three Candidate Grouped Wides

This is not a motivational plan. It is a training gate.

The purpose is to turn disparate wide-lane sweeping into a repeatable method: inventory first, route second, execute third, verify fourth, write back fifth. No reload-flipping. No doctor-worship. No false positive progress.

The challenge is deliberately shaped for repeated runs. Pick one candidate wide sweep, execute the batches, leave a proof trail, then choose the next sweep from evidence rather than pressure.

## 0. Inventory First

### 0.1 Current Toolchain Surface

| Lane | Observed authority | Current local state | Risk signal | First proof command |
|---|---|---:|---|---|
| Bun / Node | `package.json`, `bun.lock` | `bun 1.3.14`; latest observed `bun-v1.3.14` | update lane currently stable, but package surface is large | `bun --version` |
| Python | `pyproject.toml`, `uv.lock` | `uv 0.11.25`; Python lane pinned `>=3.14,<3.15` | must never fall back to bare `python` for repo automation | `uv run python --version` |
| Ruby | `.ruby-version` | `.ruby-version = 4.0.5`; `rvw.exe` present; `rv` is a PowerShell alias collision | bare `rv` is forbidden in repo automation; bare `bundle` is disallowed | `rvw --version`; `rvw r ruby -v` |
| R | `rv.lock` | `rv.lock` is R-lang, not Ruby; wrapper is `scripts\rv-r.ps1`; A2-ai `rv` current `0.19.0`, latest observed `0.22.0` | `Rscript.bat` is broken; `rv-r plan` failed on `r_version = "4.5"` | `pwsh -NoProfile -File scripts\rv-r.ps1 plan` |
| Zig | `zig-toolchain.toml` | `zv 0.15.0`; `zig 0.16.0` from `~\.zv\bin` | pin exists, but authority is separate from `mise` | `zv --version`; `zig version` |
| Go | goup-managed current | `goup 0.16.12`; `go 1.26.4`; active binary from `~\.goup\current\bin` | user-supplied `lpar/goup` is a different release lane than installed `thinkgos/goup-rs` | `goup --version`; `go version` |
| Shell / MSYS / RIDK | Ruby-scoped MSYS2 plus WSL | `mise` present; WSL `bash.exe` present; Ruby `rv` install contains `C:\Users\eldno\AppData\Roaming\rv\rubies\ruby-4.0.5\msys64` with `msys2_shell.cmd` and `pacman.exe`; these are not on global PATH | classify private Ruby/RIDK MSYS versus any future global MSYS; do not add Ruby MSYS to global PATH casually | `Test-Path "$env:APPDATA\rv\rubies\ruby-4.0.5\msys64\usr\bin\pacman.exe"` |
| Brush | Cargo-installed | `brush 0.4.0` | shell lane is available, but not yet bound to repo policy | `brush --version` |
| Rust | Cargo/Rustup | `rustup 1.29.0`; `rustc 1.96.0` stable | currently healthy; still a dependency for the tool managers | `rustup show` |

### 0.2 Root Authority Files

| File | Present | Meaning |
|---|---:|---|
| `.ruby-version` | yes | Ruby pin, currently `4.0.5` |
| `rv.lock` | yes | R-lang lockfile; must not be mistaken for Ruby `rv` state |
| `pyproject.toml` | yes | Python project and `uv` workspace policy |
| `uv.lock` | yes | Python dependency lock |
| `package.json` | yes | Bun/Node script and package surface |
| `bun.lock` | yes | Bun dependency lock |
| `Cargo.toml` / `Cargo.lock` | yes | Rust lane |
| `zig-toolchain.toml` | yes | Zig pin and target policy |
| `mise.toml` / `.mise.toml` | no | no root mise authority yet |

`mise` is installed: `2026.6.14 windows-x64`. `mise doctor` reports `shims_on_path: no`, `self_update_available: yes`, and no active config files. That means `mise` can become an authority layer only after an explicit design pass; it is not already governing the repo.

### 0.3 Skills Surface

Raw skill counts are now treated as weak evidence. The correct inventory unit is not "file exists"; it is `declared -> structurally intact -> flavor-compatible -> currently useful`.

| Skill root | `SKILL.md` files | Unique names | Duplicate names | Signal |
|---|---:|---:|---:|---|
| `.codex\skills` | 43 | 40 | 3 | repo-local Codex skill substrate; some redirects and nested duplicates |
| `.agents\skills` | 73 | 46 | 25 | duplicate-heavy mirror; useful, but unsafe as raw authority |
| `.claude\skills` | 75 | 49 | 26 | repo-local Claude-flavored substrate exists here, not in user-home `.claude\skills` |
| `C:\Users\eldno\.codex\skills` | 18 | 16 | 2 | user-global Codex skills; smaller and not equivalent to repo-local Codex |
| `C:\Users\eldno\.agents\skills` | 7 | 7 | 0 | user-global Azure/Foundry agent skills |
| `C:\Users\eldno\.claude\skills` | missing | missing | missing | absence here is not absence of Claude skills; repo `.claude\skills` exists |
| `claude\skills` | missing | missing | missing | non-dot `claude` exists, but it is not a skill root in this snapshot |

High signal skill families already visible: `toolchain-doctor`, `scm-triage`, `markdown-bridge`, `ingest-research`, `mailbox-handoff`, `git-snapshot`, `conceptualize`, `decision-razor`, `dumpster-upcycler`, `theme-system`.

Known risk: several skills are redirects, stashed protocols, nested duplicates, flavor-crossed mirrors, or stale enough to lie by omission. Skill inventory must classify authority level, not just count files.

Manual marker pass, without invoking any skill:

| Skill root | Redirect markers | Stashed markers | Deprecated markers | Fixture markers | TODO/FIXME markers | Missing `name:` |
|---|---:|---:|---:|---:|---:|---:|
| `.codex\skills` | 9 | 2 | 0 | 6 | 3 | 0 |
| `.agents\skills` | 11 | 5 | 0 | 7 | 4 | 1 |
| `.claude\skills` | 11 | 5 | 1 | 7 | 4 | 1 |
| `C:\Users\eldno\.codex\skills` | 0 | 0 | 0 | 1 | 3 | 0 |
| `C:\Users\eldno\.agents\skills` | 0 | 0 | 0 | 0 | 0 | 0 |

This does not prove the skills are bad. It proves they are not allowed to audit themselves.

### 0.3.1 Dot And Non-Dot Agency Roots

The repo contains both dot and non-dot agency directories. That is not duplication by default; it is a naming-convention hazard.

| Root | Exists | Meaning |
|---|---:|---|
| `.codex` | yes | repo-local Codex substrate |
| `codex` | yes | repo-local mailbox/runtime artifacts; not equivalent to `.codex` |
| `.agents` | yes | repo-local agent skill mirror/substrate |
| `agents` | no | no non-dot twin here |
| `.claude` | yes | repo-local Claude-flavored skill/config substrate |
| `claude` | yes | non-dot Claude artifacts; not a skill root in current inventory |
| `.gemini` | yes | Gemini-side hidden substrate; do not write unless explicitly consolidated |
| `gemini` | yes | non-dot Gemini artifacts; compare before assuming role |
| `CLAUDEBASE` | yes | durable canon and writeback surface |

False-positive rule: a missing user-home directory, missing global binary, or missing non-dot twin is not evidence that the capability does not exist. Check repo-local, user-local, nested toolchain, and generated surfaces separately.

### 0.4 MCP Surface

| Config surface | Server names observed | Risk |
|---|---|---|
| `.mcp.json` | `asc-injector`, `bevy`, `browser`, `bun-docs`, `chthonic-v3`, `cocoindex-code`, `context7`, `corpus`, `fetch`, `filesystem`, `game`, `git`, `github`, `github-archaeology`, `huggingface`, `mas-mcp`, `memory`, `microsoft-docs`, `ncbi`, `sequential-thinking`, `sonic`, `sourcer`, `ssot`, `time`, `vulkan`, `workiq` | repo root has the widest server surface |
| `.vscode\mcp.json` | `asc-injector`, `browser`, `bun-docs`, `chthonic-v3`, `fetch`, `filesystem`, `git`, `github`, `github-archaeology`, `huggingface`, `io.github.upstash/context7`, `mas-mcp`, `memory`, `microsoft-docs`, `sequential-thinking`, `time`, `workiq` | VS Code surface differs from root |
| `C:\Users\eldno\.codex\config.toml` | `github`, `hf-mcp-server`, `node_repl` | Codex API surface is smaller and tool-mediated |
| `C:\Users\eldno\.claude\settings.json` | no direct `mcpServers` / `servers` object found | Claude-side MCP may be indirect, generated, or configured elsewhere |

MCP rule: list names and transports without printing secrets. Use `scripts\mcp_write_local.ps1 -List` before manual config spelunking.

MCP false-positive rule: a configured MCP server is only declared. A command path resolving to `bun`, `uv`, `uvx`, `bunx`, or a repo binary means the entrypoint is reachable. It does not prove the server boots, authenticates, exposes the expected tools, or matches stale documentation.

| MCP proof level | Meaning | Example |
|---|---|---|
| declared | name appears in a config file | `.mcp.json` or `.vscode\mcp.json` |
| entrypoint reachable | command path or command name resolves | `C:\Users\eldno\.bun\bin\bun.exe`, `uvx`, `bunx` |
| bootable | server starts without crashing | requires a non-secret mock or status probe |
| useful | tools/resources match the task | requires client-visible tool list or dry call |
| authoritative | docs, config, code, and runtime all agree | rare; must be earned per server |

Unresolved work: the plan still needs an in-house MCP handshake probe. Until that exists, MCP servers can be listed and entrypoint-checked, but they cannot be promoted above `entrypoint reachable` unless the active client exposes the tools or a safe dry run proves them.

### 0.5 Source, Git, and Temporary Study Lane

| Surface | Current state | Guard |
|---|---|---|
| TEMP source root | `%TEMP%\chthonic-source-code` exists | third-party source stays out of repo |
| TEMP repos | `vscode-vibrancy-continued` | source checkout is evidence, not dependency |
| Vibrancy checkout | commit `f05f30ed0029`; version `1.1.84`; main `./extension/index.js` | study patterns only |
| Git visible changes | `277` paths visible by `git status --porcelain=v1` | no broad stage/commit; classify before action |
| Prior Source Control flood | previously around 500 staged entries | snapshot first; exclusions second; only then judge repo state |

### 0.6 Research Anchors

| Topic | Anchor |
|---|---|
| Vibrancy Continued current public source | `https://github.com/illixion/vscode-vibrancy-continued` |
| Mise configuration model | `https://mise.jdx.dev/configuration.html` |
| `uv` Python manager | `https://docs.astral.sh/uv/` |
| Spinel Ruby `rv` | `https://github.com/spinel-coop/rv` |
| A2-ai R `rv` | `https://github.com/A2-ai/rv` |
| `zv` Zig manager | `https://github.com/weezy20/zv` |
| Installed Go manager family | `https://github.com/thinkgos/goup-rs` |
| Alternate user-supplied Go manager release lane | `https://github.com/lpar/goup/releases/tag/v1.1.6` |
| Brush shell | `https://github.com/reubeno/brush` |

### 0.7 Structural Integrity Scale

Every artifact discovered by a wide sweep gets a rough structural integrity score before it can direct work.

| Score | Meaning | Handling |
|---:|---|---|
| 1-2 | rot; stale or actively misleading | quarantine, cite only as historical sediment |
| 3-4 | partial map; useful only with direct runtime proof | use as lead, not authority |
| 5-6 | workable but uneven | use with verification gates |
| 7-8 | reliable local substrate | can guide a batch after proof |
| 9-10 | current, verified, minimal, and coherent | allowed to become route authority |

KISS here means structural clarity, not simplification by deletion. A tiny stale script can be a `2`; a dense but verified toolchain map can be an `8`.

### 0.8 What This Plan Is Good For

This plan is not a task list. It is a routing instrument.

| Use | Meaning |
|---|---|
| prompt-engineering challenge | give another agent the plan and see whether it inventories before acting |
| hallucination threshold reducer | force declared/reachable/verified distinctions before claims |
| rot detector | find stale docs, stale skills, stale MCP entries, and stale tool wrappers before they compound |
| batch sequencer | choose one wide sweep and run it through inventory, route, execute, verify, writeback |
| memory compression | preserve the method in `CLAUDEBASE` so the next session does not rediscover the same traps |

The plan becomes dangerous if treated as gospel. It stays useful only while it remains editable against new evidence.

### 0.8.1 Invariants Versus Local Facts

Deep Research returned a useful correction: the plan must visibly separate structural invariants from observed local state.

| Type | Definition | Example | How agents may use it |
|---|---|---|---|
| invariant | stable rule that survives version changes | `declared != reachable != healthy != authoritative` | route decisions may depend on it |
| current local fact | observed state at one time | `uv 0.11.25`, `bun 1.3.14`, `.claude\skills` file count | rerun proof before acting |
| hypothesis | likely rule not yet proven locally | `MCP bootability can be checked with a standard handshake script` | create probe, do not assume |
| stale-risk artifact | useful but suspect doc/script/skill/config | `skill-polisher`, old tool doctors, generated research text | quarantine until externally verified |
| style/voice element | context-bearing register | `Extreme Haute Couture - Movement 1` | preserve unless it blocks execution |

Local inventory values belong in the plan as evidence, not law. If a future run sees a different version, file count, or checkout hash, that is not failure by itself. The failure is acting on the difference before classifying it.

### 0.9 Bootstrap Contamination Rule

The first audit of an audit system must not use the audit system.

For skills, this means:

| Phase | Allowed | Forbidden |
|---|---|---|
| bootstrap | plain file reads, marker counts, duplicate grouping, direct script/path checks | invoking `skill-polisher` or any skill to validate skills |
| quarantine | classify stale/redirect/stashed/duplicate/flavor-crossed skills | auto-fixing skill trees |
| rehabilitation | run a suspect skill only after its scripts, references, and target flavor are verified | treating skill output as proof of its own correctness |
| promotion | mark a skill as route-authoritative only after dry-run proof | using a skill because its description sounds right |

`skill-polisher` is therefore a specimen during the first pass, not the judge. It may become useful later, but only after it passes the same structural integrity test it claims to perform.

## 1. Operating Doctrine

### 1.1 The Five-Step Loop

| Step | Name | Rule |
|---:|---|---|
| 1 | Inventory | capture actual files, versions, roots, and server names |
| 2 | Route | choose exactly one wide sweep for the run |
| 3 | Execute | perform only the planned batch, not adjacent temptations |
| 4 | Verify | prove with local command output, diff, or visual/runtime signal |
| 5 | Writeback | record the result in `CLAUDEBASE/harbor/` |

### 1.2 False-Positive Kill Switches

A sweep is not progress if any of these are true:

| False positive | Stop condition |
|---|---|
| "The doctor says it is fine" | doctor output has not been cross-checked with direct binary/version/config proof |
| "The command is missing, so the tool is absent" | nested/private installs have not been checked, especially Ruby `rv` RIDK/MSYS |
| "The file exists, so it is current" | file age, duplicate roots, and runtime reachability have not been checked |
| "The skill exists, so it is usable" | skill has not been classified for duplicate/redirect/stashed/flavor state |
| "The skill auditor can audit skills" | the auditor skill has not first been audited without using itself |
| "The MCP server is configured, so it works" | no mock boot, client-visible tool list, or dry call proves it |
| "The GUI looks the same, reload again" | main-process, renderer, checksum, and human-eye calibration proof have not been separated |
| "The tool exists, so it governs the repo" | no root config or pin file proves authority |
| "The extension source solved it" | source was copied or adopted without translation into Chthonic ownership |
| "The git panel is scary" | no status snapshot exists and excludes have not been checked |
| "The Markdown is prettier" | code fences, Mermaid, references, and content preservation were not verified |
| "MCP is configured" | server names, transports, and active client surfaces were not compared |

### 1.3 Command Conduct

| Lane | Allowed pattern | Disallowed pattern |
|---|---|---|
| Python | `uv run ...`, `uvx ...` | bare `python`, stale venv guessing |
| Ruby | `rvw r ...` or `rvw ruby ...` | bare `ruby`, bare `bundle`, ambiguous `rv` |
| R | `pwsh -NoProfile -File scripts\rv-r.ps1 ...` | treating root `rv.lock` as Ruby state |
| JS/TS | `bun ...` | npm migration by accident |
| MCP | `scripts\mcp_write_local.ps1 -List` | printing secrets or token material |
| Third-party source | `%TEMP%\chthonic-source-code` | cloning studied source into repo |
| Git | snapshot, classify, then stage surgical paths | broad staging from Source Control panic |

### 1.4 Three-Witness Rule

For stale-prone infrastructure, one witness is not enough.

| Surface | Witness 1 | Witness 2 | Witness 3 |
|---|---|---|---|
| Toolchain | version manager output | direct binary path/version | root pin or config file |
| MCP server | config declaration | command/code entrypoint | boot/mock/client-visible tool list |
| Skill | `SKILL.md` metadata | script/reference files exist | successful dry run or task fit |
| Markdown repair tool | README/claim | parser result | diff preserves content |
| VS Code substrate | patched file marker | runtime log | visible or computed renderer proof |

If the three witnesses disagree, the artifact gets an `SI <= 4` until repaired or quarantined.

For skill-auditing tools, the third witness cannot be the tool's own report. It must be an external dry run, fixture result, or manually inspected behavior.

### 1.5 Routing Queues

Inventory does not count as progress until each finding is routed.

| Queue | Entry condition | Allowed action |
|---|---|---|
| Quarantine | stale, recursive, dangerous, or contradicts runtime proof | record, isolate, do not invoke |
| Rehabilitation | useful idea, damaged implementation, needs proof | inspect scripts/references, create dry-run probe |
| Promotion | passes three-witness rule and task-fit test | allow as route authority for a narrow lane |
| Historical sediment | useful only to understand how rot happened | cite, but do not let it steer execution |

Skill duplicate counts, MCP server lists, and tool-version tables must be converted into these queues before any repair batch starts.

## 2. Candidate Wide Sweep A - Agency Surface

### 2.1 What This Sweep Is

This sweep maps the thinking tools: skills, MCP servers, temp source lanes, memory/writeback files, and agent-side surfaces. It is the sweep that lowers hallucination threshold before harder work.

It answers: "Which agent can know what, through which tool, with which proof, and which surfaces are stale or duplicated?"

### 2.2 Why It Is Challenging

The hard part is not counting skills or servers. The hard part is authority classification.

| Object | Naive reading | Correct reading |
|---|---|---|
| Skill file | "available" | active, redirected, stale, duplicate, or protocol-only |
| MCP server | "configured" | root-only, VS Code-visible, Codex-visible, Claude-visible, HTTP, stdio, or dead |
| TEMP source | "downloaded" | quarantined evidence with commit/version provenance |
| Memory file | "notes" | durable handoff or stale decorative sediment |

### 2.3 Execution Batches

#### A0 - Freeze The Surfaces

| Action | Command | Artifact |
|---|---|---|
| Snapshot git state | `git status --porcelain=v1 > CLAUDEBASE\harbor\agency-sweep-git-status-YYYYMMDD.txt` | visible working-tree count |
| List MCP without secrets | `pwsh -NoProfile -File scripts\mcp_write_local.ps1 -List` | server table |
| Compare dot/non-dot agency roots | targeted root existence check for `.codex`, `codex`, `.agents`, `.claude`, `claude`, `.gemini`, `gemini` | naming-convention map |
| Count skill roots with uniqueness | targeted `Get-ChildItem -Filter SKILL.md` per known root, grouped by `name:` | count + unique + duplicate table |
| Check TEMP source | `pwsh -NoProfile -File scripts\chthonic-source-temp.ps1 -Status` | repo list |
| Score stale risk | assign structural integrity score to each discovered skill/MCP/doc surface | `SI 1-10` table |

#### A1 - Classify Skills

| Class | Meaning | Action |
|---|---|---|
| Active | current, callable, task-relevant | keep in routing table |
| Redirect | says to use another skill | collapse into target skill |
| Stashed | policy/protocol only | keep as note, not execution tool |
| Duplicate | same skill nested in multiple roots | choose authority root |
| Flavor twin | same concept exists in Codex and Claude lanes | compare target flavor before using |
| Stale rot | docs/tool claims contradict runtime proof | quarantine as historical lead |
| Auditor specimen | claims to audit or validate other skills/tools | inspect as data first; do not invoke during bootstrap |
| Unknown | cannot parse cleanly | quarantine for later audit |

Output file:

```powershell
CLAUDEBASE\harbor\agency-surface-skill-inventory-YYYYMMDD.md
```

#### A2 - Classify MCP Servers

| Class | Meaning | Required proof |
|---|---|---|
| Root-declared | present in `.mcp.json` | name and transport only |
| VS Code-visible | present in `.vscode\mcp.json` | name match and command type |
| Codex-visible | present in Codex config/tool list | callable tool or config entry |
| Claude-visible | present in Claude config or generated MCP file | no token leakage |
| Entrypoint-reachable | command path or command name resolves | `Test-Path`, `Get-Command`, or HTTP endpoint shape |
| Boot-proven | server starts in mock/status mode | no-secret dry run or client-visible tool list |
| Dormant | declared but binary missing, or code exists but cannot boot | path proof plus failed dry run |
| Dangerous | token-heavy, filesystem-heavy, or write-capable | explicit user intent before live use |

#### A3 - Agency Routing Matrix

Build a small table that answers:

| Task family | First agent/tool | Verification surface | Writeback |
|---|---|---|---|
| Git panic / staged flood | `scm-triage` plus direct `git status` | snapshot file | `CLAUDEBASE/harbor/` |
| Research ingestion | `ingest-research` plus manual diff | cleaned `.md` + backup | `CLAUDEBASE/sub-surface...` |
| Source contender study | temp source lane | commit/version/path | source-study note |
| API/MCP drift | `api_pool.ps1 -Doctor`, `mcp_write_local.ps1 -List` | redacted lists only | harbor note |
| Toolchain drift | `oxidized-toolchain-audit.ps1`, direct version commands | JSON/report | harbor note |

### 2.4 Pass Criteria

This sweep passes only when:

- each skill root has count + class summary;
- MCP surfaces have name-only comparisons;
- TEMP source policy is written and verified;
- at least one stale/duplicate skill or MCP surface is identified without deleting it;
- output is a durable `CLAUDEBASE/harbor/` map.

## 3. Candidate Wide Sweep B - Oxidized Toolchain

### 3.1 What This Sweep Is

This sweep hardens the language managers that allow the repo to work at all: `uv`, `rvw`, R `rv`, `zv`, `goup`, `brush`, `mise`, Rust, Bun, and the Ruby-scoped RIDK/MSYS lane.

It answers: "Which runtime owns which language, which pins are real, which managers are stale, and where should root authority live?"

### 3.2 The Current Fracture

| Fracture | Evidence | Meaning |
|---|---|---|
| Ruby/R name collision | `rv` is a PowerShell alias; Ruby tool is `rvw`; root `rv.lock` is R | never use bare `rv` as proof |
| R lane broken | `Rscript.bat` broken; A2-ai `rv` behind current release; `rv-r plan` fails on `4.5` | R must be isolated and repaired before trust |
| `mise` present but not governing | no root `mise.toml`; shims not on PATH | `mise` is candidate authority, not current authority |
| MSYS not global | `msys2_shell.cmd` and `pacman.exe` exist under `C:\Users\eldno\AppData\Roaming\rv\rubies\ruby-4.0.5\msys64`, but are not exposed by repo-shell PATH | treat this as RubyInstaller/RIDK-private unless a wrapper/export policy is deliberately created |
| Tool doctors can lie | stale meta-CLI docs exist | direct commands outrank wrappers |

### 3.3 Execution Batches

#### B0 - Non-Mutating Audit

| Action | Command | Pass signal |
|---|---|---|
| Run oxidized audit | `pwsh -NoProfile -File scripts\oxidized-toolchain-audit.ps1 -Json` | JSON records all lanes |
| Check command resolution | `Get-Command uv,rvw,rv,Rscript,zv,goup,brush,bun,cargo,rustup,zig,go,mise` | no accidental bare alias use |
| Check root pins | list `.ruby-version`, `rv.lock`, `pyproject.toml`, `uv.lock`, `zig-toolchain.toml`, `package.json`, `Cargo.toml` | authority map exists |

#### B1 - Ruby Lane

| Rule | Action |
|---|---|
| Ruby goes through `rvw` | use `rvw r ruby -v` and `rvw r bundle ...` only inside directories with a `Gemfile` |
| No broad bundle install | first find actual Ruby projects by `Gemfile` location |
| `.ruby-version` is real | keep `4.0.5` unless a deliberate upgrade gate is opened |

Deliverable:

```powershell
CLAUDEBASE\harbor\ruby-rv-lane-inventory-YYYYMMDD.md
```

#### B2 - R Lane

| Step | Action | Stop if |
|---|---|---|
| Identify wrapper | inspect `scripts\rv-r.ps1` | wrapper prints secrets or mutates unexpectedly |
| Compare R pin | read `rv.lock` `r_version` | pin has no installable match |
| Repair `Rscript` path | locate installed R root | multiple R roots conflict |
| Protect Ruby lane | verify R `rv` commands never touch Ruby `rvw` state | a command crosses the R/Ruby boundary |
| Update A2-ai `rv` only by explicit command | use release evidence before mutating | current projects cannot be verified after update |

Deliverable:

```powershell
CLAUDEBASE\harbor\r-rv-lane-repair-plan-YYYYMMDD.md
```

#### B3 - Root Authority Decision

Do not create `mise.toml` as a decoration. Create it only if it can answer:

| Question | Required answer |
|---|---|
| Does `mise` manage Ruby here, or does `rvw` remain Ruby authority? | one lane owns execution |
| Can `mise.toml` serve as a readable root policy manifest while `rvw` still executes Ruby? | allowed if it documents authority without hijacking it |
| Does `mise` manage Python, or does `uv` remain Python authority? | `uv` remains package/project authority |
| Does `mise` manage Go/Zig, or only document them? | avoid fighting `goup` / `zv` |
| Are shims on PATH? | no today; do not assume |
| Is MSYS private to Ruby/RIDK, exposed by wrappers, or separated into a global MSYS install? | classify before changing PATH or installing anything |

Possible authority outputs:

| Candidate | Use when |
|---|---|
| `mise.toml` | `mise` actually controls versions without fighting existing managers, or it is explicitly marked as a policy manifest |
| `CLAUDEBASE/harbor/toolchain-authority-map-YYYYMMDD.md` | existing managers remain authoritative |
| `scripts/toolchain-policy.ps1` | repo needs a single non-mutating verifier |

#### B4 - Verification Gate

| Lane | Verification command |
|---|---|
| Python | `uv run python --version` |
| Ruby | `rvw r ruby -v` |
| R | `pwsh -NoProfile -File scripts\rv-r.ps1 plan` |
| Zig | `zv --version`; `zig version` |
| Go | `goup --version`; `go version` |
| Bun | `bun --version`; `bun install --frozen-lockfile` only if chosen |
| Rust | `cargo --version`; `rustup show` |
| Mise | `mise doctor`; root config proof |

### 3.4 Pass Criteria

This sweep passes only when:

- Ruby and R `rv` lanes are no longer linguistically or operationally confused;
- bare `python`, `ruby`, `bundle`, and ambiguous `rv` are absent from new maintenance docs;
- one authority map exists for all runtime managers;
- every mutating update has a prior dry-run or explicit risk note;
- `Rscript` is either repaired or documented as blocked with exact path evidence.

## 4. Candidate Wide Sweep C - Movement 1 Substrate And Research Body

### 4.1 What This Sweep Is

This sweep returns to the artwork after the infrastructure can tell the truth. It binds together:

- VS Code Insiders Mica substrate;
- latest Vibrancy Continued source study;
- SFS theme/icon ownership;
- Markdown research repair;
- hardware MCP architecture decision;
- Surface Pass 3 calibration.

It answers: "What must be learned from contenders and research artifacts before Movement 1 resumes visual work?"

### 4.2 Current Proof

| Layer | Proof today | Meaning |
|---|---|---|
| Main-process Mica | `.chthonic/mica-diag.txt` showed `setBackgroundMaterial('mica') ok` and `setBackgroundColor(#00000000) ok` | Electron material call executes |
| Renderer CSS | visual probe showed banner/outlines | workbench CSS injection works |
| Integrity | checksum reconcile removed warnings | patch ownership is honest |
| Visual outcome | Mica remains subtle under SFS opacity and dark wallpaper | calibration problem, not plumbing proof |
| Contender source | TEMP checkout of Vibrancy Continued `1.1.84` | source study can proceed safely |

### 4.3 Execution Batches

#### C0 - Return Workbench To Non-Probe State

| Action | Command |
|---|---|
| Disable visual probe if active | `pwsh -NoProfile -File scripts\mica-renderer-visual-probe.ps1 -Disable` |
| Verify substrate | `pwsh -NoProfile -File scripts\mica-substrate.ps1 -Verify` |
| Verify checksum | `pwsh -NoProfile -File scripts\insiders-integrity-reconcile.ps1 -Verify` |

Stop if warnings return. Do not tune visuals while integrity is noisy.

Checksum nuance: generic Vibrancy-style patching may treat a VS Code corruption warning as expected evidence of mutation. The Chthonic in-house substrate does not accept that as the desired end state. Here, an unreconciled warning means the ownership loop is incomplete: verify substrate markers, then reconcile checksums or restore through the owned scripts. Do not auto-repair VS Code by reinstalling, and do not normalize the warning as success.

#### C1 - Contender Pattern Harvest

Study latest Vibrancy Continued from TEMP source only.

| Pattern | Question | Adopt? |
|---|---|---|
| material timing | when does it call material/background APIs? | translate if it improves our `chthonic-mica.cjs` |
| renderer CSS delivery | inline, file link, CSP, protocol handling | translate only if source proves a better path |
| checksum story | how it handles VS Code modified-file warnings | compare against our reconcile path |
| overlay styling | quick input, menus, widgets, editor overlays | harvest selector knowledge, not color authority |
| update resilience | behavior across Insiders update | compare to `mica-substrate.ps1` |

Output:

```powershell
CLAUDEBASE\harbor\vibrancy-continued-source-study-YYYYMMDD.md
```

#### C2 - Research Body Repair

| Artifact family | Repair rule | Verification |
|---|---|---|
| Gemini Markdown | preserve content; clean fences; remove Google Docs escape damage only where safe | fence count, Mermaid parse if available |
| Hardware MCP docs | keep both consolidation and isolation arguments visible | decision table, not premature conclusion |
| Deep research packets | preserve references and quoted technical claims | link/reference audit |
| Movement docs | keep high style, but make gates executable | command tables and pass criteria |

Use `uv` for any Python repair tooling.

#### C3 - Hardware MCP Decision

| Candidate | When it wins | When it loses |
|---|---|---|
| integrate into existing MCP server | context economy matters more than FFI isolation | COM/NVML/GPU probing increases blast radius |
| create `chthonic-hw-mcp-server` | hardware probing needs isolation and native bindings | too much duplicate MCP infrastructure |
| defer | toolchain and Markdown lanes are not stable | hardware truth is needed for imminent design/runtime work |

#### C4 - Surface Pass 3 Resume

Only after C0-C3:

| Surface | Move |
|---|---|
| command palette | verdigris glass cast, calibrated by eye after proof |
| sidebar/activity bar | keep SFS authority; adjust opacity only if evidence says invisible |
| editor | protect reading surface before spectacle |
| acrylic contrast test | temporary only, to prove material chain if Mica is too quiet |

### 4.4 Pass Criteria

This sweep passes only when:

- visual probe is disabled or explicitly marked active;
- main-process and renderer proofs are separated;
- Vibrancy source study exists with commit/version;
- research docs are repaired without content loss;
- hardware MCP decision is framed by failure modes;
- Surface Pass 3 changes are verified visually and by file diff.

## 5. Selection Matrix

| Candidate | Challenge | Reward | Blast radius | Best time to choose |
|---|---:|---:|---:|---|
| A - Agency Surface | high abstraction | lower hallucination, cleaner agent routing | low to medium | before asking Claude/Codex to execute complex work |
| B - Oxidized Toolchain | high plumbing difficulty | stable language/runtime substrate | medium | now, because R/Ruby/RIDK-MSYS/mise are unresolved |
| C - Movement 1 Substrate | high aesthetic + architecture pressure | resumes the actual couture work | medium to high | after toolchain and docs stop lying |

Recommended first challenge: **A - Agency Surface**.

Reason: stale skills, stale MCP entries, stale docs, and stale tool wrappers can poison every other lane. The first run must prove which agency surfaces are trustworthy before those surfaces are allowed to steer the toolchain or Movement 1 work.

Second challenge: **B - Oxidized Toolchain**.

Reason: after the agency map stops lying, harden the runtime substrate: R/Ruby `rv` collision, Ruby-scoped RIDK/MSYS exposure, `mise.toml` policy, `uv`, `zv`, `goup`, Bun, Rust.

Third challenge: **C - Movement 1 Substrate**.

Reason: the visual/artistic work should resume from a quieter base, not from toolchain anxiety.

## 6. Repeatable Wide-Sweep Drill

### 6.1 The Drill

| Round | Timebox | Output |
|---:|---|---|
| 1 | inventory only | one table of facts, no fixes |
| 2 | route | one chosen candidate, one rejected candidate with reason |
| 3 | execute batch 0 and 1 | small diff or note, not a grand refactor |
| 4 | verify | command output, visual proof, or parse result |
| 5 | writeback | `CLAUDEBASE/harbor/<sweep>-<date>.md` |

### 6.2 The Prompt To Give Another Agent

```text
Inventory first. Do not mutate files until you have a table of observed state.
Do not use a skill to audit skills in Round 1. Treat every skill as a specimen until externally verified.
Use uv for Python, rvw for Ruby, scripts\rv-r.ps1 for R, and do not trust tool doctors without direct proof.
Pick exactly one candidate sweep: Agency Surface, Oxidized Toolchain, or Movement 1 Substrate.
Execute only Batch 0 and Batch 1 unless verification passes.
Write the result to CLAUDEBASE/harbor with commands, files touched, and stop conditions.
Do not clone studied source into the repo. Use %TEMP%\chthonic-source-code.
Do not stage or commit.
```

### 6.3 The Anti-Ping-Pong Rule

If an agent asks for a reload, reinstall, retry, or token refresh before producing an evidence table, stop the sweep and force Round 1 again.

## 7. Stale Project Classifier

Any stale project can be routed through the same shape.

| Project symptom | Wide sweep type | First inventory |
|---|---|---|
| too many tools, unclear authority | B - Oxidized Toolchain | version/pin/manager table |
| too many agents, conflicting advice | A - Agency Surface | skill/MCP/memory map |
| visual or design claims not matching human eye | C - Movement 1 Substrate | runtime proof + screenshot/visual probe |
| Markdown/RAG documents decaying | C, then A | fence/reference/content preservation table |
| source-control flood | A, then B if generated by tools | git snapshot + exclude map |

## 8. First Concrete Run

Start with the Agency Surface bootstrap, without invoking any skill:

```powershell
git status --porcelain=v1 > CLAUDEBASE\harbor\agency-surface-bootstrap-git-2026-06-30.txt
pwsh -NoProfile -File scripts\mcp_write_local.ps1 -List
pwsh -NoProfile -File scripts\chthonic-source-temp.ps1 -Status
Get-ChildItem .codex\skills,.agents\skills,.claude\skills -Filter SKILL.md -Recurse
Get-Item .codex,codex,.agents,.claude,claude,.gemini,gemini,CLAUDEBASE -Force
```

Then write:

```powershell
CLAUDEBASE\harbor\agency-surface-bootstrap-2026-06-30.md
```

That writeback must include:

| Required table | Purpose |
|---|---|
| dot/non-dot agency roots | prevent naming-convention false positives |
| skill count + unique name + duplicate name + rot marker counts | prevent skill-count false positives |
| MCP declared + entrypoint reachable + boot status if safely knowable | prevent configured-server false positives |
| suspect auditor list | mark `skill-polisher` and similar tools as specimens until externally verified |
| next sweep recommendation | choose Toolchain or Movement 1 from evidence |

Do not run `skill-polisher` in this first run. Do not update anything in this first run. The first run is truth acquisition. The second run may repair.
