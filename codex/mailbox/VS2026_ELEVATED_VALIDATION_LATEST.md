# VS2026 Elevated Validation (Latest)

- Timestamp: 2026-07-03T23:39:49
- Elevated User: erd\eldno
- Skip Modify: False
- Log: "C:\Users\eldno\chthonic-archive\codex\mailbox\VS2026_ELEVATED_VALIDATE_20260703_233927.log"

## Lane Results

- [ok] community_insiders: pre_missing=0, post_missing=0, exit_code=0
- [ok] buildtools_insiders: pre_missing=0, post_missing=0, exit_code=0
- [ok] ssms22: pre_missing=0, post_missing=0, exit_code=0

## chthonic status --json

```json
{"pacman":"not found","goup":"0.16.12","msvc_cl":"C:\\Program Files\\Microsoft Visual Studio\\18\\Insiders\\VC\\Tools\\MSVC\\14.51.36231\\bin\\Hostx64\\x64","ssms":"22.7.11919.86","handler_shell":"pwsh primary, brush experimental, bash fallback","az":"2.86.0","code-insiders":"1.128.0-insider","sqlpackage":"not found","rvar_cmd":"not found","vs_professional":"not found","proto_cmd":"not found","rv":"0.6.0","uv":"0.11.25","gemini_cmd":"C:\\Users\\eldno\\chthonic-archive\\node_modules\\.bin\\gemini.exe","git":"2.54.0.windows.1","node_cmd":"C:\\Users\\eldno\\.local\\bin\\node.exe","ruff":"0.15.10","proto":"not found","brush":"0.4.0","go":"1.26.4 windows/amd64","python_cmd":"C:\\Users\\eldno\\chthonic-archive\\.venv\\Scripts\\python.exe","vs_buildtools":"18.8.11925.187","handler_r_packages":"rv-r (A2-ai/rv - rproject.toml + rv.lock)","claude":"2.1.183","rscript_cmd":"C:\\Program Files\\R\\bin\\Rscript.bat","handler_ruby":"rv (rvw wrapper optional)","manager_model":"hybrid(chthonic_ssot+mise_overlay)","rustup":"1.29.0","rust":"1.96.0 (ac68faa20 2026-05-25)","mdbook":"0.4.49","r":"not found","chthonic_cmd":"C:\\Users\\eldno\\chthonic-archive\\scripts\\chthonic.ps1","handler_node":"fnm (optional Node version lane)","handler_go":"goup","fnm":"not found","bicep":"0.43.8","msys2_home":"C:\\Users\\eldno\\AppData\\Roaming\\rv\\rubies\\ruby-4.0.5\\msys64","pacman_cmd":"not found","vs_ide":"18.8.11925.187","rv_binding_reason":"accepted by design; R handled via rv-r, Remove-Variable unused","workspace":"C:\\Users\\eldno\\chthonic-archive","vs_enterprise":"not found","claudine_cmd":"C:\\Users\\eldno\\chthonic-archive\\scripts\\claudine.ps1","unified_overlay_optional":"mise/proto","gcc":"not found","fnm_cmd":"not found","node":"not found","zig_cmd":"C:\\Users\\eldno\\.zv\\bin\\zig.exe","sqlcmd":"15.0.1300","r_binding_reason":"accepted by design; R accessed via rv-r","handler_zig":"zv","msbuild":"18.8.2.30814","handler_rust":"rustup/cargo","cargo":"1.96.0","vulkan":"1.4.350.0","rv_r":"0.19.0","ruby":"4.0.5 (2026-05-20 revision 64336ffd0e) +PRISM [x64-mingw-ucrt]","clang":"not found","zig":"0.16.0","claude_cmd":"C:\\Users\\eldno\\.local\\bin\\claude.exe","handler_r":"unmanaged runtime (rig not installed - R 4.5.3 ucrt installed externally)","handler_python":"uv","rv_r_cmd":"C:\\Users\\eldno\\chthonic-archive\\scripts\\rv-r.ps1","mise_cmd":"C:\\Users\\eldno\\.cargo\\bin\\mise.exe","zv":"0.15.0","gemini":"0.49.0","uv_tool_lane":"python,ruff,cmake,ninja","python_origin":"workspace_venv","vs_community":"18.8.11925.187","bun":"1.3.14","rv_cmd":"alias -> Remove-Variable","brush_cmd":"C:\\Users\\eldno\\.cargo\\bin\\brush.exe","handler_js":"bun","orchestrator_ssot":"chthonic","zv_cmd":"C:\\Users\\eldno\\.zv\\bin\\zv.exe","rv_binding":"alias -> Remove-Variable","rvw":"0.6.0","python":"3.14.6","research_ingest_role":"supplemental_input","r_cmd":"not found","orchestration_mode":"polyglot_router","biome":"not found","r_binding":"alias -> Invoke-History","rscript":"not found","make":"not found","mise":"2026.6.14"}
```

## chthonic doctor --origins

```text

CHTHONIC ORIGINS v3.3.0
========================================================================
  ruby      ~\AppData\Roaming\rv\rubies\ruby-4.0.5\bin\ruby.exe rv (irm rv.dev/install.ps1)
  python    ~\.local\bin\uv.exe                          irm astral.sh/uv
  bun       ~\.bun\bin\bun.exe                           irm bun.sh
  rust      ~\.cargo\bin\rustc.exe                       rustup (irm rustup.rs)
  go        ~\.goup\current\bin\go.exe                   goup (cargo install goup-rs)
  --------------------------------------------------------------------
  rv        alias -> Remove-Variable                     primary Ruby lane
  rvw       ~\.cargo\bin\rvw.exe                         fallback rv wrapper
  fnm       (not found)                                  winget/cargo (Fast Node Manager)
  node      (not found)                                  fnm-managed Node runtime
  mise      ~\.cargo\bin\mise.exe                        optional unified overlay (not SSOT)
  proto     (not found)                                  cargo install proto_cli
  zv        ~\.zv\bin\zv.exe                             Zig version manager
  zig       ~\.zv\bin\zig.exe                            zv-managed Zig runtime
  R         (not found)                                  current R runtime (manager intentionally none)
  Rscript   (not found)                                  current R helper (manager intentionally none)
  rv-r      ~\chthonic-archive\scripts\rv-r.ps1          A2-ai/rv via repo wrapper
  goup      ~\.cargo\bin\goup.exe                        GH release binary
  cargo     ~\.cargo\bin\cargo.exe                       rustup toolchain
  rustup    ~\.cargo\bin\rustup.exe                      rustup manager
  brush     ~\.cargo\bin\brush.exe                       cargo install brush-shell
  pacman    ~\AppData\Roaming\rv\rubies\ruby-4.0.5\msys64\usr\bin\pacman.exe MSYS2 package manager (RubyInstaller DevKit)
  msys2     (not found)                                  RubyInstaller DevKit / MSYS2 root
  biome     (not found)                                  repo bun dependency or curated global tool
  ruff      ~\AppData\Local\hermes\hermes-agent\venv\Scripts\ruff.exe uv tool
  cmake     ~\.local\bin\cmake.exe                       uv tool
  ninja     ~\.local\bin\ninja.exe                       uv tool
  mdbook    ~\.cargo\bin\mdbook.exe                      cargo install
  git       C:\Program Files\Git\mingw64\bin\git.exe     native installer
  gcc       (not found)                                  MSYS2 (RubyInstaller)
  az        C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd Azure CLI MSI
  bicep     ~\AppData\Local\Microsoft\WinGet\Packages\Microsoft.Bicep_Microsoft.Winget.Source_8wekyb3d8bbwe\bicep.exe winget (Microsoft.Bicep)
  sqlcmd    C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\170\Tools\Binn\SQLCMD.EXE winget (Microsoft.Sqlcmd)
  sqlpackage(not found)                                  winget (Microsoft.SqlPackage)
  cl        C:\Program Files\Microsoft Visual Studio\18\Insiders\VC\Tools\MSVC\14.51.36231\bin\Hostx64\x64\cl.exe Visual Studio 2026 C++ toolchain
  msbuild   C:\Program Files\Microsoft Visual Studio\18\Insiders\MSBuild\Current\Bin\MSBuild.exe Visual Studio 2026 Build Tools
  clang     (not found)                                  Visual Studio 2026 LLVM toolset
  glslc     C:\VulkanSDK\1.4.350.0\Bin\glslc.exe         Vulkan SDK
  ssms      C:\Program Files\Microsoft SQL Server Management Studio 22\Release SSMS (Visual Studio Installer)
  claude    ~\.local\bin\claude.exe                      standalone CLI
  claudine  ~\chthonic-archive\scripts\claudine.ps1      shell wrapper (chthonic env)
  gemini    ~\chthonic-archive\node_modules\.bin\gemini.exe bun-managed workspace dep (repo-local)
========================================================================
  ~/.local/bin/  user local bin (uv + standalone CLIs)
  ~/.bun/bin/  bun runtime bin (bun/bunx; ambient shims are not authoritative for repo CLIs)
  ~/.cargo/bin/  cargo ecosystem (rustc, rustup, mdbook, rv, goup)
  ~/.goup/  goup-managed Go versions (go.dev source)
  %APPDATA%\rv\  rv-managed Ruby versions
  %LOCALAPPDATA%\fnm\  fnm-managed Node versions
  C:\Users\eldno\OneDrive\Documents\PowerShell  PowerShell profile wrappers (e.g., claudine function)
  C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin  Azure CLI (az)
  C:\Users\eldno\AppData\Local\Microsoft\WinGet\Packages\Microsoft.Bicep_Microsoft.Winget.Source_8wekyb3d8bbwe  Bicep CLI (winget)
  C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\170\Tools\Binn  Sqlcmd Tools (winget)
  C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools  Visual Studio Build Tools 2026 (Insiders)
  C:\Program Files\Microsoft Visual Studio\18\Insiders  Visual Studio Community 2026 (Insiders)
========================================================================
```
