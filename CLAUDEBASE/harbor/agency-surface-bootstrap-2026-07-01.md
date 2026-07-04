---
date: 2026-07-01
agent: Codex
substrate: CLAUDEBASE
status: completed-static-bootstrap
skill-invocation: none
source-plan: CLAUDEBASE/harbor/wide-sweeps-inventory-management-plan-2026-06-30.md
---

# Agency Surface Bootstrap

This is the first execution fruit from the Wide Sweeps plan.

No skill was invoked. No MCP server was called. No generated doctor was trusted. This pass used only static file reads, path checks, config parsing, and Git status.

## Result

The Agency Surface is **not promotable yet**.

It is usable as a map, but not as an execution authority. The repo has enough duplicate skill surfaces, dot/non-dot naming splits, and MCP declarations-without-boot-proof that the next batch must be local hardening, not another research delegation.

## Commands Run

| Purpose | Method |
|---|---|
| root surface map | `Get-Item` / `Test-Path` on dot and non-dot agency roots |
| skill inventory | static `SKILL.md` reads; grouped by `name:`; marker counts |
| MCP inventory | parsed `.mcp.json` and `.vscode\mcp.json`; checked command path reachability only |
| Git pressure check | `git status --porcelain=v1` count and top directory grouping |

## Dot And Non-Dot Roots

| Root | Exists | Type | Meaning | Queue |
|---|---:|---|---|---|
| `.codex` | yes | directory | repo-local Codex substrate | Rehabilitation |
| `codex` | yes | directory | mailbox/runtime artifacts; not equal to `.codex` | Rehabilitation |
| `.agents` | yes | directory | repo-local agent skill mirror/substrate | Rehabilitation |
| `agents` | no | missing | no non-dot twin here | Historical sediment |
| `.claude` | yes | directory | repo-local Claude-flavored skill/config substrate | Rehabilitation |
| `claude` | yes | directory | non-dot Claude artifacts; not a skill root in this pass | Rehabilitation |
| `.gemini` | yes | directory | hidden Gemini-side substrate; do not write unless explicitly consolidated | Quarantine |
| `gemini` | yes | directory | non-dot Gemini artifacts; compare before assuming role | Rehabilitation |
| `CLAUDEBASE` | yes | directory | durable canon/writeback surface | Promotion |
| `.mcp.json` | yes | file | root MCP declaration surface | Rehabilitation |
| `.vscode` | yes | directory | VS Code workspace config surface | Rehabilitation |

### Finding

Dot/non-dot naming is an active false-positive vector. An agent cannot infer role from name alone.

Promoted writeback surface remains `CLAUDEBASE/`. Dot agency folders and non-dot agency folders require mapping before any write or cleanup.

## Skill Surface

| Root | Exists | Files | Unique names | Duplicate names | Redirect | Stashed | Deprecated | Fixture | TODO/FIXME | Missing `name:` | Queue |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `.codex\skills` | yes | 43 | 40 | 3 | 9 | 2 | 0 | 6 | 3 | 0 | Rehabilitation |
| `.agents\skills` | yes | 73 | 45 | 25 | 11 | 5 | 0 | 7 | 4 | 1 | Quarantine/Rehabilitation |
| `.claude\skills` | yes | 75 | 48 | 26 | 11 | 5 | 1 | 7 | 4 | 1 | Quarantine/Rehabilitation |
| `C:\Users\eldno\.codex\skills` | yes | 18 | 16 | 2 | 0 | 0 | 0 | 1 | 3 | 0 | Rehabilitation |
| `C:\Users\eldno\.agents\skills` | yes | 7 | 7 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | Promotion-candidate |
| `C:\Users\eldno\.claude\skills` | no | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | Historical sediment |
| `claude\skills` | no | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | Historical sediment |

### Duplicate Examples

| Root | Top duplicate names |
|---|---|
| `.codex\skills` | `claude-skill-bridge[2]`; `codex-skill-bridge[2]`; `postman[2]` |
| `.agents\skills` | `Codex-skill-bridge[4]`; `api-manager[2]`; `sora[2]`; `skill-polisher[2]`; `skill-installer[2]`; `skill-creator[2]`; `script-envelope[2]`; `scm-triage[2]`; `python-header-canon[2]`; `postman[2]` |
| `.claude\skills` | `api-manager[2]`; `sora[2]`; `skill-polisher[2]`; `skill-installer[2]`; `skill-creator[2]`; `script-envelope[2]`; `scm-triage[2]`; `python-header-canon[2]`; `postman[2]`; `openai-docs[2]` |
| `C:\Users\eldno\.codex\skills` | `imagegen[2]`; `openai-docs[2]` |

### Finding

The skill substrate cannot be treated as a trusted tool layer yet.

`skill-polisher` remains a specimen, not an auditor. The cleanest near-term candidate surface is `C:\Users\eldno\.agents\skills`, but even that only means "low visible rot markers," not task authority.

## MCP Surface

Static parsing found MCP declarations in:

| Config | Server count | Proof ceiling from this pass |
|---|---:|---|
| `.mcp.json` | 26 | entrypoint reachable / declared HTTP |
| `.vscode\mcp.json` | 17 | entrypoint reachable / declared HTTP |

All MCP entries are currently in **Rehabilitation**, not Promotion.

### Why

This pass proved only:

- config declaration exists;
- stdio command path or command name resolves;
- HTTP endpoint string exists.

It did not prove:

- process boots;
- JSON-RPC handshake works;
- tools/resources are visible to a client;
- credentials are valid;
- server behavior matches stale docs.

### Immediate MCP Result

The next useful local artifact is an in-house MCP handshake probe, not another DR packet.

Candidate scope:

| Requirement | Rule |
|---|---|
| language | Bun or `uv`, chosen after checking existing repo patterns |
| input | `.mcp.json`, `.vscode\mcp.json` |
| output | name, config source, transport, command/URL, declared, entrypoint, boot, list-tools |
| safety | no tokens printed; no write operations; short timeout |
| queue result | Quarantine / Rehabilitation / Promotion-candidate |

## Git Pressure

| Metric | Value |
|---|---:|
| visible changes | 276 |

Top visible directories:

| Directory | Count |
|---|---:|
| `manifest` | 46 |
| `scripts` | 38 |
| `CLAUDEBASE` | 33 |
| `renders` | 16 |
| `apps` | 14 |
| `.vscode` | 12 |
| `game` | 9 |
| `vulkan-lab` | 8 |
| `tools` | 8 |
| `extensions` | 7 |
| `docs` | 6 |
| `ankh_atlas` | 5 |
| `dev` | 4 |
| `assets` | 4 |
| `.meta` | 4 |
| `codex` | 4 |
| `probes` | 4 |
| `designs` | 3 |
| `claude` | 3 |

### Finding

Git is still not clean enough for broad action. It is no longer the earlier staged flood, but it remains noisy. Any future batch must use precise path edits and no broad staging.

## Queues

### Promotion

| Surface | Reason |
|---|---|
| `CLAUDEBASE/` | durable writeback canon per repo instructions |

### Promotion-Candidate

| Surface | Reason | Missing proof |
|---|---|---|
| `C:\Users\eldno\.agents\skills` | low visible rot markers, no duplicate names in this pass | task fit and actual invocation behavior |

### Rehabilitation

| Surface | Reason | Next repair/probe |
|---|---|---|
| `.codex\skills` | moderate duplicate/redirect/stashed markers | static skill queue classifier |
| `.agents\skills` | heavy duplicate markers | static skill queue classifier; compare with `.claude\skills` |
| `.claude\skills` | heavy duplicate markers plus one deprecated marker | static skill queue classifier; compare with `.agents\skills` |
| `C:\Users\eldno\.codex\skills` | small duplicate set and TODO markers | compare with repo-local `.codex\skills` |
| `.mcp.json` | declarations and reachable entrypoints only | MCP handshake probe |
| `.vscode\mcp.json` | declarations and reachable entrypoints only | MCP handshake probe |
| `.codex`, `codex`, `.claude`, `claude`, `.gemini`, `gemini` | naming split requires relationship map | dot/non-dot role map |

### Quarantine

| Surface | Reason |
|---|---|
| `.gemini` writes | repo instruction says not to write hidden Gemini substrate unless explicitly consolidated |
| skill self-auditing | recursive contamination risk |
| broad source-control operations | 276 visible paths remain |

### Historical Sediment

| Surface | Reason |
|---|---|
| missing `C:\Users\eldno\.claude\skills` | absence does not mean absence of Claude skills; repo `.claude\skills` exists |
| missing `claude\skills` | non-dot `claude` exists but not as skill root |

## Decisions

| Decision | Outcome |
|---|---|
| Can skills be used as route authority now? | No |
| Can MCP servers be used as route authority now? | No |
| Can `CLAUDEBASE/` remain writeback authority? | Yes |
| Should Toolchain open next? | Not yet |
| Should Movement 1 visual work resume next? | Not yet |
| What is the next executable local batch? | Build static skill queue classifier or MCP handshake probe |

## Recommended Next Batch

Do **MCP handshake probe** first.

Reason: MCP declarations are central to both Codex/Claude execution claims and future research/tool access. Right now they are all stuck at Rehabilitation. A small no-secret handshake probe would convert many entries from "declared/reachable" into actual queues.

Batch shape:

1. inspect existing MCP config schema without secrets;
2. write `scripts/mcp_handshake_probe.ps1` or `scripts/mcp_handshake_probe.ts`;
3. timebox each server boot;
4. capture `initialize` / `tools/list` where possible;
5. write a JSON report under `CLAUDEBASE/harbor/`;
6. do not mutate `.mcp.json` or `.vscode/mcp.json` in the first pass.

Second batch after that:

```text
static skill queue classifier
```

That classifier should be a primitive parser, not a skill invocation.

## Executed Follow-Through

The MCP probe was created and run in safe static mode.

| Artifact | Status |
|---|---|
| `scripts/mcp_handshake_probe.py` | created |
| `uv run python -m py_compile scripts\mcp_handshake_probe.py` | passed |
| `CLAUDEBASE/harbor/mcp-handshake-probe-2026-07-01-static.json` | written |

Static probe result:

| Metric | Value |
|---|---:|
| MCP declarations parsed | 43 |
| boot enabled | false |
| Rehabilitation | 43 |
| Promotion-candidate | 0 |
| Quarantine | 0 |

This does not prove the servers work. It proves the probe can parse both MCP config surfaces, redact environment values, resolve command names/paths, and produce a repeatable report. The next execution step is named boot probing of one or two low-risk servers, not a full blast across every MCP server.
