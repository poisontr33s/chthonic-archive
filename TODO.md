# TODO.md — BridgeTroll Remediation List

Derived from `ROAST.md`. Ordered by severity: security-relevant first, then drift, then config hygiene, then watch-items with no action yet.

---

## 1. Rust — security patch behind (P1)

```powershell
rustup update stable
rustc --version   # confirm 1.96.1
```
Fixes CVE-2026-5223 (medium) and CVE-2026-5222 (low) — both affect crate extraction/auth via third-party registries. `rust-toolchain.toml` needs no edit (`channel = "stable"` already floats), this is purely a local sync gap.

---

## 2. Python (`uv`) and JS runtime (`bun`) — confirm on latest patch (P2)

```powershell
uv self update
uv --version      # was 0.11.25 (2026-06-26 build)

bun upgrade
bun --version     # was 1.3.14
```
Both ship multiple releases a week; no specific missed version was confirmed, so this is a "sync and check" action, not a targeted fix.

---

## 3. `.cargo/config.toml` — scope machine-specific/debug rustflags per profile

File: `.cargo/config.toml:29-34`

Current:
```toml
[target.x86_64-pc-windows-msvc]
rustflags = [
    "-C", "target-cpu=native",
    "-C", "link-arg=/OPT:ICF",
    "-C", "link-arg=/OPT:REF",
    "-C", "link-arg=/DEBUG",
    "-C", "link-arg=/LTCG",
]
```
Decide and apply one of:
- **If this machine will always be the only build machine:** no code change needed, but add a one-line comment above `target-cpu=native` stating that explicitly, so a future reader doesn't copy this config to a CI runner or another dev's machine and get `SIGILL`.
- **If portability might matter later:** move `target-cpu=native` behind a `profile.release`-only path (Cargo doesn't support per-profile `rustflags` natively in `config.toml` — use a `[env]` var toggled by a build script, or drop `native` and pin an explicit `-C target-cpu=x86-64-v3` baseline instead).

Separately, confirm release link times are acceptable with both `lto = true` (root `Cargo.toml:57`, fat LTO) and `/LTCG` (`.cargo/config.toml:34`) active simultaneously — if release builds are link-time-bound, drop one of the two.

---

## 4. `extensions/chthonic-archive/.chthonic/mise.toml` — remove or fix dead tool pins

File: `extensions/chthonic-archive/.chthonic/mise.toml:21-23`

```toml
cargo-binstall = "latest"
terraform = "latest"
kubectl = "latest"
```
The file's own comment confirms these have never resolved in any mise version. Pick one:
```powershell
# Option A — find correct mise registry names and re-pin:
mise registry | Select-String -Pattern "cargo-binstall|terraform|kubectl"

# Option B — delete the three lines outright if these tools are actually
# managed some other way (cargo-binstall is already reachable via `cargo binstall`
# once installed through cargo itself, per SCRIPTS_README's cargo-ecosystem lane).
```

---

## 5. `goup.toml:3` — update stale version reference in comment

File: `goup.toml`, line 3

```diff
- # Current goup-rs v0.16.11 does not consume TOML project config. Its native
+ # Current goup-rs v0.16.12 does not consume TOML project config. Its native
```
Installed version confirmed via `chthonic status --json` → `"goup":"0.16.12"`.

---

## 6. `zig-toolchain.toml:33,35` — fix stale example paths

File: `zig-toolchain.toml`, lines 33 and 35

```diff
- # ZIG_BIN  = "$env:USERPROFILE\\.zig\\0.14.0\\zig.exe"
+ # ZIG_BIN  = "$env:USERPROFILE\\.zig\\0.16.0\\zig.exe"
- # ZIG_LIB  = "$env:USERPROFILE\\.zig\\0.14.0\\lib"
+ # ZIG_LIB  = "$env:USERPROFILE\\.zig\\0.16.0\\lib"
```
Purely cosmetic today (both lines are commented out), but keep it consistent with `[toolchain].channel = "0.16.0"` above so an emergency uncomment doesn't silently point at a two-versions-old path.

---

## 7. `biome` — install or remove the dead scripts

File: `package.json:69-70`

```powershell
# If Biome is meant to be active:
bun run biome:install
bun run biome:version   # confirm resolution

# If Biome was abandoned in favor of something else, remove both script
# entries from package.json instead — don't leave a script pointing at a
# tool nobody has installed.
```
You (the maintainer) know which; this repo alone doesn't disambiguate it.

---

## 8. `sqlpackage` — install to complete the SQL toolchain

```powershell
winget install Microsoft.SqlPackage
sqlpackage /version
```
`sqlcmd` and SSMS are already present and origin-tracked; this is the one missing piece of that lane.

---

## 9. Watch-items — no action needed now, re-check later

- **R (`rv-r`) 4.5.3 → 4.6.1:** Do **not** bump yet. The 4.5.3 pin was just stabilized 2026-07-04 (a PATH collision fix in `.Rprofile`, per session record). Let it soak before touching `rproject.toml:2` (`r_version = "4.5"`). When ready to re-test:
  ```powershell
  # After confirming current 4.5.3 lane has been stable for a while:
  chthonic ruby doctor   # sanity-pass unrelated lanes first
  # then bump rproject.toml r_version to "4.6" and re-run the same
  # rv-r + .Rprofile validation that fixed the 2026-07-04 collision,
  # before trusting the new version in daily use.
  ```
- **Zig 0.17.0:** Not confirmed shipped as of this audit. Check `https://ziglang.org/download/` periodically; when it lands, re-pin `zig-toolchain.toml:15` (`channel = "0.16.0"`) deliberately, don't auto-float.
- **NVIDIA driver/CUDA/cuDNN/DLSS baseline:** Internally consistent (`hw_drift_check` reports full sync against this repo's own documented baseline). No search-confirmed newer number exists to act on — if you want bleeding-edge, check nvidia.com manually; this is not a config defect.

---

*Companion to `ROAST.md`. Both generated 2026-07-05 from a live audit of the main archive only — sibling-repo junctions were excluded per the BridgeTroll brief.*
