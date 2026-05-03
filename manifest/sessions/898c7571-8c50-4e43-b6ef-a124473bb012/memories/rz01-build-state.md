# RZ-01 Build State

## Containerfile fix applied (2026-04-24)
- Layer 4: removed `spirv-cross` (not in Fedora 40 repos), removed `shaderc-devel` → split to optional `shaderc`
- Build retry terminal ID: 87bfe42d-b26e-4e37-a532-1d6e56494ad0
- Layer 4 now passes (vulkan-devel, vulkan-headers, glslang, spirv-tools all installed)
- Layer 10 (shaderc) in progress at last check

## Duplicate `$Verbose` fix in test_win32.ps1
- Removed `[switch] $Verbose` from param block — CmdletBinding injects it automatically
- Fix committed pending (not yet git-added)

## RZ-03 StartupProbe
- Script fixed (Verbose param removed)
- Blocked on StartupProbe — `rv r ruby -e "exit 0"` works in direct shell
- Error was "A positional parameter cannot be found that accepts argument 'ruby'" — this is a PowerShell argument parsing issue inside the script when called from -File mode
- `& rv r ruby -e "exit 0"` works fine directly

## Layer counts
- Total layers: 39 (STEP 1/39 through 39/39)
- Last seen: STEP 10/39 (shaderc)
- Remaining after shaderc: DXC (11), Rust (12-13), Ruby fetch (14), Ruby configure (15), Ruby build (16), Ruby install (17), Layer 8 ext copies (18+), ext builds (19-25), verify (26-32), gems (33), WORKDIR+CMD (34-35)
- Ruby build will be the longest step (~5-10 min for make -j$(nproc))

## Commits pending (not yet in git)
- test_win32.ps1 Verbose param fix (unstaged)
- Containerfile Layer 4 fix (unstaged)
