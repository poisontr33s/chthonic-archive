# Polyrepo Runner Debug State

## CURRENT STATUS
- Claudine lint: ✅ FIXED (commit 5112e73)
- PNK typecheck: ✅ FIXED (prior session)
- MCP typecheck: ✅ FIXED (prior session)
- Archive cargo check: 🔴 STILL FAILING

## Archive Cargo Check Issue
- `.cargo/config.toml` has `[env] SHADERC_LIB_DIR = "C:\\VulkanSDK\\1.4.341.1\\Lib"`
- Runner cargo check inline: `'$env:SHADERC_LIB_DIR="C:\VulkanSDK\1.4.341.1\Lib"; cargo check --quiet 2>&1'`
- TERMINAL cargo check exits 0 (warm cache, builds fine with SHADERC_LIB_DIR)
- RUNNER cargo check ALWAYS triggers `build_from_source` → cmake panic (exit 103)
- Runner time: 1.5s (fast panic) vs terminal: 0.29s (cached)

## shaderc-sys build.rs logic
- First checks SHADERC_LIB_DIR env var → use prebuilt lib
- Falls back to VULKAN_SDK env var → use that SDK's lib
- Falls back to build_from_source → requires cmake + git + python3/python
- `C:\VulkanSDK\1.4.341.1\Lib\shaderc_combined.lib` EXISTS
- VULKAN_SDK = C:\VulkanSDK\1.4.341.1 (set system-wide)

## Key Mystery
- `Invoke-Expression '$env:SHADERC_LIB_DIR="C:\VulkanSDK\1.4.341.1\Lib"; cargo check --quiet 2>&1'` passes in terminal
- SAME command fails in runner subprocess
- VULKAN_SDK IS set in environment (should also trigger prebuilt path)
- Fingerprint: `"local":[{"Precalculated":"0.10.1"}]`, `"config":0`
- No `cargo:rerun-if-env-changed` emitted by shaderc-sys build script
- MAYBE: CARGO_FEATURE_BUILD_FROM_SOURCE is set in runner env (check this!)
- OR: runner subprocess doesn't see VULKAN_SDK for some reason

## Files Changed
- `C:\Users\eldno\chthonic-archive\.cargo\config.toml` - added [env] SHADERC_LIB_DIR
- `C:\Users\eldno\chthonic-archive\scripts\polyrepo-runner.ps1` - inline SHADERC_LIB_DIR in cargo cmd

## Status Update 2
- VULKAN_SDK=C:\VulkanSDK\1.4.341.1 IS set in all subprocesses (inherited from Windows env)
- SHADERC_LIB_DIR IS set by .cargo/config.toml [env] AND by current terminal env
- vk.xml EXISTS at C:\VulkanSDK\1.4.341.1\share\vulkan\registry\vk.xml
- shaderc_combined.lib EXISTS at C:\VulkanSDK\1.4.341.1\Lib\shaderc_combined.lib
- Terminal cargo check: exits 0 (uses cache)
- Runner cargo check: ALWAYS re-runs build_from_source, takes 0.8-1.5s, exits 103
- Runner TRUNCATES cargo output — only shows frames 6-8, not the actual panic message
- To get full cargo output from runner: run cargo check directly in runner subprocess with RUST_BACKTRACE=full

## ROOT CAUSE FOUND
The runner subprocess builds for `x86_64-pc-windows-gnu` (GNU/MinGW), NOT `x86_64-pc-windows-msvc`.
- shaderc-sys looks for `libshaderc_combined.a` for GNU target (not `shaderc_combined.lib`)
- `libshaderc_combined.a` doesn't exist in VulkanSDK → falls back to build_from_source
- cmake uses Ninja + GCC flags → fails because python.exe not found via uv path
- VULKAN_SDK and SHADERC_LIB_DIR ARE set correctly, but wrong target means wrong lib name
- Rust toolchain: 1.95.0-x86_64-pc-windows-msvc (MSVC) BUT x86_64-pc-windows-gnu target IS installed
- SOMETHING in the PowerShell profile sets CARGO_BUILD_TARGET=x86_64-pc-windows-gnu or similar
  OR the profile activates a different toolchain that defaults to GNU
- The terminal (no profile loaded?) uses MSVC target

## THE FIX
Add `target = "x86_64-pc-windows-msvc"` to the `[build]` section in `.cargo/config.toml`:
```toml
[build]
jobs = 12
target = "x86_64-pc-windows-msvc"
```
This forces MSVC target regardless of what the profile sets.
OR: check `CARGO_BUILD_TARGET` env var in profile and remove/override it.

## Key Debug Evidence
- cmake output: `-DCMAKE_C_FLAGS= -ffunction-sections -fdata-sections -m64 -w` → GCC flags!
- `CMAKE_TOOLCHAIN_FILE_x86_64-pc-windows-gnu = None` → target IS x86_64-pc-windows-gnu
- build script says: `cannot find native shaderc library on system; falling back to build from source`
- After finding SHADERC_LIB_DIR, it still falls back because for GNU target it needs `libshaderc_combined.a`
- Runner profile shows: `env: rb:4.0.3 | gcc/msys2` (the gcc/msys2 is significant)

## Fix to Apply
Edit `C:\Users\eldno\chthonic-archive\.cargo\config.toml`:
Change `[build]` section from:
```
[build]
jobs = 12
```
To:
```
[build]
jobs = 12
target = "x86_64-pc-windows-msvc"
```
Then run the runner to verify. Also check if CARGO_BUILD_TARGET is set in the profile.
