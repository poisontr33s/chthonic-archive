# ROAST.md — BridgeTroll Configuration & Version Audit

**Scope:** `C:\Users\eldno\chthonic-archive` main archive only. Sibling-repo junctions/symlinks (`csb-live/`, `pnk-live/`, `rmco-live/`, `poisontr33s-live/`, `git-dump-live/`, `eoai-live/`, `pnk-lfh-live/`) were **not** traversed — excluded per brief, to avoid mixing context from downloaded sister repositories.

**Method:** Live `chthonic status --json` / `chthonic doctor --dry-run --origins`, `chthonic-hw` MCP live probe + `hw_drift_check`, `uv lock --check`, `bun run sdk:check`, direct read of every version-pinning config file, and targeted verification against each tool's own release channel (rust-lang.org, ziglang.org, go.dev, ruby-lang.org, r-project.org, git-scm.com, lunarg.com). Where upstream "latest" couldn't be pinned to an exact build (uv, bun — both ship multiple times a week), that uncertainty is stated rather than guessed.

---

## 1. Version state, A (installed) vs B (upstream latest)

| Domain | A (installed) | B (upstream latest) | Verdict |
|---|---|---|---|
| Rust (`cargo`/`rustc`) | 1.96.0 (2026-05-25 build) | **1.96.1** (2026-06-30) | **BEHIND — security-relevant.** 1.96.1 fixes CVE-2026-5223 (medium, symlink extraction from third-party-registry crate tarballs) and CVE-2026-5222 (low, auth with normalized URLs). `rust-toolchain.toml` pins `channel = "stable"` (no version), so this is a `rustup` sync gap, not a pin problem. |
| Python (`uv`) | 0.11.25 (built 2026-06-26) | unconfirmed exact, but uv ships multiple releases a week — a 9-day-old build is presumptively 1–3 patches behind | **LIKELY BEHIND**, low severity. `uv.lock` itself is healthy — `uv lock --check` resolved all 228 packages clean, no drift despite the lockfile's older mtime (2026-06-21) vs. recent repo activity. |
| JS runtime (`bun`) | 1.3.14 | unconfirmed exact (same weekly-ish cadence as uv) | **LIKELY BEHIND**, low severity. |
| Ruby (`rv`) | 4.0.5 | 4.0.5 (released 2026-05-20, CVE-2026-46727 fix already included) | **MATCH.** No action. |
| Go (`goup`) | 1.26.4 | 1.26.4 (released 2026-06-02) | **MATCH.** 1.27rc1 exists but is a release candidate — correctly not adopted. |
| Git | 2.55.0.windows.2 | 2.55.0 (released 2026-06-29) | **MATCH.** No action. |
| Zig (`zv`) | 0.16.0 | 0.16.0 still current; 0.17.0 (build-system rework + LLVM 22) was "weeks out" as of the May 2026 devlog, not confirmed shipped | **MATCH for now** — watch item, not a gap. |
| R (`rv-r`) | 4.5.3 (pinned `rproject.toml: r_version = "4.5"`) | **4.6.1** (4.6.0 shipped April 2026, 4.6.1 June 2026) | **TWO MINOR VERSIONS BEHIND — but hold.** This lane was just stabilized 2026-07-04 (a day before this audit) after fixing an `rv`/`rv-r` PATH collision in `.Rprofile`. Bumping to 4.6.x now, one day after that fix landed, risks re-triggering the same class of collision before the fix has had any soak time. Treat as a known, deliberate gap — re-evaluate after the 4.5.3 fix has held for a while, not immediately. |
| Vulkan SDK | 1.4.350.0 | 1.4.350.0 | **MATCH**, confirmed both by LunarG's own release page and by this repo's own `hw_drift_check` (`is_synchronized: true`). |
| NVIDIA driver / CUDA / cuDNN / DLSS | 610.62 / CUDA UMD 13.3 / cuDNN 9.20.0.48 / DLSS 310.7.0.0 | inconclusive via web search — NVIDIA doesn't surface a single clean "latest" version number for GeForce drivers the way SDK vendors do | **NO CLAIM.** `hw_drift_check` confirms live state matches this repo's own documented baseline (`docs/reference/COMPUTE_FRONTIER_LANDSCAPE.md` / `NVIDIA_DLL_INVENTORY.md`) exactly, including every NVML/DLL component. That baseline is a deliberate pin, not staleness — verify manually against nvidia.com if you want bleeding-edge, but this is not a config bug. |
| SDK catalog (`sdk-catalog.toml`, 12 managed JS/TS SDKs) | — | — | **CLEAN.** `bun run sdk:check` reports all 12 present and OK. This lane is already self-auditing; no manual roast needed. |

---

## 2. Config file critique

### `.cargo/config.toml:29-34` — `rustflags` bakes machine-specific + debug-oriented flags into every profile
```toml
rustflags = [
    "-C", "target-cpu=native",
    "-C", "link-arg=/OPT:ICF",
    "-C", "link-arg=/OPT:REF",
    "-C", "link-arg=/DEBUG",
    "-C", "link-arg=/LTCG",
]
```
`[target.x86_64-pc-windows-msvc].rustflags` applies unconditionally to **every** profile, not just `dev` or `release`:
- `target-cpu=native` bakes the exact instruction set of *this* i9-13900 into every binary. That's fine for a single-developer machine, but it means any binary built here (including CI artifacts, if any ever run elsewhere) is not portable — it will `SIGILL`/crash on different CPU microarchitectures. If this box is ever not the only build machine, this line needs to become profile- or environment-gated.
- `/LTCG` (MSVC link-time codegen) stacked on top of root `Cargo.toml`'s `[profile.release] lto = true` (fat LTO, despite a comment nearby claiming "thin") is two overlapping LTO mechanisms firing at once for release builds. Not incorrect, but worth confirming release link times are still acceptable — this combination is a common source of multi-minute link stalls.
- `/DEBUG` unconditionally on every profile means release builds still emit a full PDB even though `[profile.release] strip = true` strips the binary — the PDB is unaffected by `strip`, so you're paying full debug-info generation cost on every release build regardless.

### `extensions/chthonic-archive/.chthonic/mise.toml:21-23` — three tools pinned to `"latest"` that mise cannot resolve
```toml
cargo-binstall = "latest"
terraform = "latest"
kubectl = "latest"
```
The comment two lines above these (`# These two lines never resolved successfully in any mise version.`) already documents that this is dead config — it's been failing silently across every mise version tried and nobody has gone back to either fix the tool names or delete the lines. Live dead weight in an active config file.

### `goup.toml:3` — comment is one patch behind the tool it describes
```
# Current goup-rs v0.16.11 does not consume TOML project config. ...
```
Installed `goup` is **0.16.12** (confirmed via `chthonic status --json`). Minor, but it's a doc-drift smell inside a file whose entire purpose is being the version-pinning source of truth.

### `zig-toolchain.toml:33,35` — stale example paths in commented-out env block
```
# ZIG_BIN  = "$env:USERPROFILE\\.zig\\0.14.0\\zig.exe"
# ZIG_LIB  = "$env:USERPROFILE\\.zig\\0.14.0\\lib"
```
Both reference Zig **0.14.0** while `[toolchain].channel` above is pinned to **0.16.0**. Commented-out, so inert today — but if someone uncomments these as a "quick fix" during a `zv` outage, they'll silently point at a two-versions-stale path.

### `package.json:69-70` — `biome:install`/`biome:version` scripts reference a tool that isn't installed
`chthonic status --json` reports `"biome":"not found"`. Either Biome is meant to be part of the active lint chain (in which case it's simply never been installed — `bun run biome:install` fixes it in one command) or it's a dead script left over from a tool that got dropped. Right now it's ambiguous from the repo alone.

### `sqlpackage` — missing, adjacent SQL tooling is present
`sqlcmd` (15.0.1300) and `ssms` (22.7.11919.86) are installed and origin-tracked, but `sqlpackage` shows `"not found"` in both `status` and `doctor --origins`, despite `SCRIPTS_README.md`/`origins` output already knowing its winget source (`Microsoft.SqlPackage`). Incomplete install, not a missing tool definition.

---

## 3. Confirmed healthy, checked and not flagged

- `.git/config` overriding global `core.autocrlf=true` → `false` at repo scope is **correct**, not a bug: it pairs with `.gitattributes`' explicit `* text=auto eol=lf`, which is the recommended combination to avoid autocrlf fighting attribute-based normalization. No action.
- `core.symlinks=false` doesn't affect the `-live` sibling-repo junctions (NTFS junctions are transparent to the filesystem, not git symlinks) — irrelevant to this audit's exclusion requirement, confirmed by inspection rather than assumption.
- VS 2026 Insiders: Community/BuildTools/IDE all present at `18.8.11925.187`; Enterprise/Professional absent by design (documented prior decision to keep only the free-tier variants installed).
- `rv`/`r` PowerShell alias collisions (`Remove-Variable`/`Invoke-History`) are handled by design — `rvw`/`rv-r` wrapper indirection, not an oversight.
- `pyproject.toml`'s `requires-python = ">=3.14,<3.15"` hard lane-lock is self-documented ("future versions would need re-audit") — intentional, not drift.

---

*Generated by BridgeTroll audit pass, 2026-07-05. See `TODO.md` for the action list derived from this report.*
