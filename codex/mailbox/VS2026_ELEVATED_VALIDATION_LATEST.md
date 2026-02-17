# VS2026 Elevated Validation (Latest)

- Timestamp: 2026-02-18T00:11:06
- Elevated User: LAPTOP-DRAQGN8A\eld
- Skip Modify: False
- Log: "C:\Users\erdno\chthonic-archive\codex\mailbox\VS2026_ELEVATED_VALIDATE_20260218_001043.log"

## Lane Results

- [ok] professional_insiders: pre_missing=0, post_missing=0, exit_code=0
- [ok] buildtools_insiders: pre_missing=0, post_missing=0, exit_code=0
- [ok] ssms22: pre_missing=0, post_missing=0, exit_code=0

## chthonic status --json

```json
{"sqlpackage":"170.3.93.6","mdbook":"0.5.2","az":"2.83.0","vs_ide":"18.4.11506.43","ssms":"22.3.11505.172","msvc_cl":"C:\\Program Files\\Microsoft Visual Studio\\18\\Insiders\\VC\\Tools\\MSVC\\14.50.35717\\bin\\Hostx64\\x64","biome":"2.4.1","uv":"0.10.3","bun":"1.3.9","make":"4.4.1","clang":"20.1.8","vulkan":"1.4.341.1","ruby":"4.0.1 (2026-01-13 revision e04267a14b) +PRISM [x64-mingw-ucrt]","msbuild":"18.4.0.7901","vs_professional":"18.4.11506.43","code-insiders":"1.110.0-insider","sqlcmd":"1.9.0","python":"3.13.11","workspace":"C:\\Users\\erdno\\chthonic-archive","vs_enterprise":"not found","vs_buildtools":"18.4.11506.43","bicep":"0.40.2","rust":"1.93.1 (01f6ddf75 2026-02-11)","go":"1.26.0 windows/amd64","git":"2.52.0.windows.1","vs_community":"not found","gcc":"15.2.0","ruff":"0.15.0"}
```

## chthonic doctor --origins

```text

CHTHONIC ORIGINS v3.2.0
========================================================================
  ruby      ~\AppData\Roaming\rv\rubies\ruby-4.0.1\bin\ruby.exe rv (cargo install rv)
  python    ~\.local\bin\uv.exe                          irm astral.sh/uv
  bun       ~\.bun\bin\bun.exe                           irm bun.sh
  rust      ~\.cargo\bin\rustc.exe                       rustup (irm rustup.rs)
  go        ~\.goup\current\bin\go.exe                   goup (cargo install goup-rs)
  --------------------------------------------------------------------
  goup      ~\.cargo\bin\goup.exe                        GH release binary
  biome     ~\.bun\bin\biome.exe                         bun add -g
  ruff      ~\.local\bin\ruff.exe                        uv tool
  cmake     ~\.local\bin\cmake.exe                       uv tool
  ninja     ~\.local\bin\ninja.exe                       uv tool
  mdbook    ~\.cargo\bin\mdbook.exe                      cargo install
  git       C:\Program Files\Git\cmd\git.exe             native installer
  gcc       C:\Ruby40-x64\msys64\ucrt64\bin\gcc.exe      MSYS2 (RubyInstaller)
  az        C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd Azure CLI MSI
  bicep     ~\AppData\Local\Microsoft\WinGet\Links\bicep.exe winget (Microsoft.Bicep)
  sqlcmd    C:\Program Files\SqlCmd\sqlcmd.exe           winget (Microsoft.Sqlcmd)
  sqlpackage~\AppData\Local\Microsoft\WinGet\Packages\Microsoft.SqlPackage_Microsoft.Winget.Source_8wekyb3d8bbwe\sqlpackage.exe winget (Microsoft.SqlPackage)
  cl        C:\Program Files\Microsoft Visual Studio\18\Insiders\VC\Tools\MSVC\14.50.35717\bin\Hostx64\x64\cl.exe Visual Studio 2026 C++ toolchain
  msbuild   C:\Program Files\Microsoft Visual Studio\18\Insiders\MSBuild\Current\Bin\MSBuild.exe Visual Studio 2026 Build Tools
  clang     C:\Program Files\Microsoft Visual Studio\18\Insiders\VC\Tools\Llvm\bin\clang.exe Visual Studio 2026 LLVM toolset
  glslc     C:\VulkanSDK\1.4.341.1\Bin\glslc.exe         Vulkan SDK
  ssms      C:\Program Files\Microsoft SQL Server Management Studio 22\Release SSMS (Visual Studio Installer)
  claude    ~\.local\bin\claude.exe                      standalone
========================================================================
  ~/.local/bin/  uv ecosystem (uv, ruff, cmake, ninja, claude)
  ~/.bun/bin/  bun ecosystem (bun, biome, codex, gemini)
  ~/.cargo/bin/  cargo ecosystem (rustc, rustup, mdbook, rv, goup)
  ~/.goup/  goup-managed Go versions (go.dev source)
  %APPDATA%\rv\  rv-managed Ruby versions
  C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin  Azure CLI (az)
  C:\Users\erdno\AppData\Local\Microsoft\WinGet\Links  Bicep CLI (winget)
  C:\Program Files\SqlCmd  Sqlcmd Tools (winget)
  C:\Users\erdno\AppData\Local\Microsoft\WinGet\Packages\Microsoft.SqlPackage_Microsoft.Winget.Source_8wekyb3d8bbwe  SqlPackage (winget)
  C:\Program Files (x86)\Microsoft Visual Studio\18\Insiders  Visual Studio Build Tools 2026 (Insiders)
  C:\Program Files\Microsoft Visual Studio\18\Insiders  Visual Studio Professional 2026 (Insiders)
========================================================================
```
