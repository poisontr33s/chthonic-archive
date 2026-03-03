---
type: report
from: codex
to: codex
created: 2026-03-03
priority: high
subject: Oxidized Tooling Landscape Audit
---

# Oxidized Tooling Landscape

## Scope

Part 3 audited the local toolchain surface, generated native JSON outputs via `ankh-forge`, and mapped the remaining non-oxidized gaps. The canonical machine outputs for this phase are:

- `audit-reports/extension_universe_ankh.json`
- `audit-reports/wptg_filetype_census_ankh.json`
- `audit-reports/oxidized_tooling_landscape.json`
- `audit-reports/oxidized_tooling_eol.json`
- `audit-reports/ankh_forge_chore_audit.json`

## Confirmed Installed Native Lanes

The host currently has five strong native or honorary-native language managers in active use:

| Language | Manager | Local Version | Runtime | Notes |
|---|---|---:|---:|---|
| Python | `uv` | `0.10.7` | `Python 3.14.3` | Still the cleanest replacement for `pip` + virtualenv sprawl. |
| Ruby | `rv` | `0.5.2` | `ruby 4.0.1` | Rust-native Ruby version lane is live locally. |
| Go | `goup` | `0.16.10` | `go1.26.0` | Installed and healthy; the repo now has living `.go` output from Part 2. |
| Rust | `rustup` | `1.28.2` | `rustc 1.93.1` | Canonical self-oxidizing lane. |
| TypeScript / JS | `bun` | `1.3.9` | `bun 1.3.9` | Zig-built rather than Rust, but still native/single-binary enough to count as honorary. |

Also installed but not oxidized: `.NET 10.0.200-preview.0.26103.119`, `gcc 15.2.0`, `perl 5.38.5`, `PowerShell 7.5.4`, `glslangValidator 16.2.0`, and the ambient Windows batch lane.

## Known Oxidized Tools Not Installed

These are real native-manager options that exist today but are not currently installed here:

| Language | Candidate | Status | Recommendation |
|---|---|---|---|
| Node.js | `fnm` / `Volta` | Mature, native, absent locally | Worth adding only if this repo needs Node version pinning beyond Bun. |
| Julia | `juliaup` | Official and native, absent locally | Install only if a Julia lane becomes real rather than speculative. |
| Zig | `zigup` | Native and self-bootstrap friendly, absent locally | Optional; useful if the repo grows a genuine Zig lane. |

## Languages Still Missing Oxidized Tooling

These gaps remain materially unfilled as of March 3, 2026:

| Language | Current Best Known Tooling | Why It Still Fails the Oxidized Bar |
|---|---|---|
| PHP | `phpbrew`, `phpenv` | Shell/PHP-centric; no mature Rust-native manager surfaced in this audit. |
| Elixir | `asdf` | General-purpose shell tool, not a native Elixir-first manager. |
| Lua | legacy shell/version-manager ecosystem | No credible Rust-native manager surfaced in current verification. |
| F# | piggybacks on `dotnet` | No standalone native manager; lifecycle is tied to .NET. |
| Java | `SDKMAN!`, `jabba` | `SDKMAN!` is shell-based; `jabba` is Go-based, not Rust-native. |
| Haskell | `ghcup` | Mature, but implemented in Haskell rather than Rust. |
| COBOL | `GnuCOBOL` | Compiler exists, native manager layer does not. |
| Perl | system Perl / `perlbrew` | No Rust-native Perl manager surfaced in current verification. |

## EOL Posture

From `audit-reports/oxidized_tooling_eol.json` generated on `2026-03-03T07:39:42Z`:

- `rust 1.93.1`: current cycle `1.93`, not EOL.
- `go 1.26.0`: current cycle `1.26`, not EOL.
- `ruby 4.0.1`: supported until `2029-03-31`.
- `bun 1.3.9`: current `1.x` lane, not EOL by the upstream feed.
- `.NET 10` preview lane: feed resolves to cycle `10`, EOL `2028-11-14`.
- `python 3.14.3`: feed currently resolves as `unknown`; the cycle is too new for a stable EOL classification in the current data pull.
- `perl 5.38.5`: feed currently resolves as `unknown` from the current pull.

The main operational conclusion is simple: nothing installed is screaming for emergency removal. The only watch item is that Python and Perl EOL metadata are not yet cleanly classified by the current feed, so they remain informational unknowns rather than healthy positives.

## Native Tool Outcome

`ankh-forge` now exists under `tools/ankh-forge/` with these implemented subcommands:

- `scan`
- `census`
- `audit`
- `pathway`
- `validate`
- `landscape`
- `eol`
- `forensics`

Quality gates completed:

- `cargo build`
- `cargo test`
- `cargo clippy --all-targets --all-features -- -W clippy::pedantic`

Bonus-capable surfaces now present:

- `forensics` recognizes `.png`, `.woff`, and SQLite `.db` headers.
- `eol` consumes live `endoflife.date` data.
- `scan` / `census` emit JSON structurally aligned with the Python lane.
- `pathway` returns a transmutation route for every extension passed to it, including generic fallback coverage beyond the original 45-type brief.

## Recommendations

1. Keep `uv`, `rv`, `goup`, `rustup`, and `bun` as the default toolchain spine.
2. Do not install more managers just because they exist; the only plausible near-term addition is `fnm` or `Volta`, and only if Bun stops being sufficient.
3. Treat Perl, PHP, Java, and Lua as intentionally unoxidized lanes until the repo has an actual maintenance reason to carry them.
4. Use `ankh-forge` as the native fast path before falling back to the Python archaeology scripts.

## References

- `fnm`: https://fnm.vercel.app/
- `Volta`: https://volta.sh/
- `juliaup`: https://docs.julialang.org/en/v1/manual/installation/
- `phpbrew`: https://phpbrew.github.io/phpbrew/
- `asdf`: https://asdf-vm.com/guide/getting-started.html
- `ghcup`: https://www.haskell.org/ghcup/
- `SDKMAN!`: https://sdkman.io/
- `jabba`: https://github.com/shyiko/jabba
- `perlbrew`: https://perlbrew.pl/
- `GnuCOBOL`: https://gnucobol.sourceforge.io/
- EOL data: https://endoflife.date/
