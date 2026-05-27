# VS2026 Elevated Validation (Latest)

- Timestamp: 2026-05-15T06:04:04
- Elevated User: erd\eldno
- Skip Modify: True
- Log: "C:\Users\eldno\chthonic-archive\codex\mailbox\VS2026_ELEVATED_VALIDATE_20260515_060332.log"

## Lane Results

- [ok] community_insiders: pre_missing=0, post_missing=0, exit_code=
- [ok] buildtools_insiders: pre_missing=0, post_missing=0, exit_code=
- [drift_optional] ssms22: pre_missing=1, post_missing=1, exit_code=

## chthonic status --json

```json
{"make":"not found","handler_node":"fnm (optional Node version lane)","python_cmd":"C:\\Users\\eldno\\chthonic-archive\\.venv\\Scripts\\python.exe","chthonic_cmd":"C:\\Users\\eldno\\chthonic-archive\\scripts\\chthonic.ps1","rvw":"0.5.3","vs_professional":"not found","fnm_cmd":"not found","rv_binding_reason":"accepted by design; R handled via rv-r, Remove-Variable unused","claude":"2.1.141","handler_shell":"pwsh primary, brush experimental, bash fallback","vs_community":"18.6.11723.189","rvar_cmd":"not found","proto":"not found","handler_python":"uv","rust":"1.95.0 (59807616e 2026-04-14)","r_cmd":"C:\\Program Files\\R\\R-4.5.3\\bin\\x64\\R.exe","az":"2.86.0","python":"3.14.4","r_binding_reason":"accepted by design; R accessed via rv-r","zv_cmd":"C:\\Users\\eldno\\.local\\bin\\zv.cmd","mise":"2026.4.17","workspace":"C:\\Users\\eldno\\chthonic-archive","r_binding":"alias -> Invoke-History","handler_js":"bun","brush":"0.3.0","ssms":"22.6.11806.211","msys2_home":"C:\\Users\\eldno\\AppData\\Roaming\\rv\\rubies\\ruby-4.0.3\\msys64","git":"2.54.0.windows.1","vs_buildtools":"18.6.11723.189","node_cmd":"C:\\Users\\eldno\\.local\\bin\\node.exe","pacman":"not found","node":"not found","vs_ide":"18.6.11723.189","rv_binding":"alias -> Remove-Variable","uv_tool_lane":"python,ruff,cmake,ninja","bun":"1.3.14","uv":"0.11.14","zv":"0.13.0","claude_cmd":"C:\\Users\\eldno\\.local\\bin\\claude.exe","biome":"2.4.8","msvc_cl":"C:\\Program Files\\Microsoft Visual Studio\\18\\Insiders\\VC\\Tools\\MSVC\\14.51.36231\\bin\\Hostx64\\x64","zig":"0.16.0","ruff":"0.15.12","fnm":"not found","handler_r":"unmanaged runtime (rig not installed — R 4.5.3 ucrt installed externally)","rscript":"4.5.3","mdbook":"0.4.49","brush_cmd":"C:\\Users\\eldno\\.cargo\\bin\\brush.exe","go":"1.26.3 windows/amd64","orchestrator_ssot":"chthonic","proto_cmd":"not found","handler_go":"goup","msbuild":"18.6.3.22110","claudine_cmd":"C:\\Users\\eldno\\chthonic-archive\\scripts\\claudine.ps1","gemini":"0.39.1","ruby":"4.0.3 (2026-04-21 revision 85ddef263a) +PRISM [x64-mingw-ucrt]","gemini_cmd":"C:\\Users\\eldno\\chthonic-archive\\node_modules\\.bin\\gemini.exe","handler_r_packages":"rv-r (A2-ai/rv — rproject.toml + rv.lock)","manager_model":"hybrid(chthonic_ssot+mise_overlay)","rustup":"1.29.0","mise_cmd":"C:\\Users\\eldno\\.cargo\\bin\\mise.exe","r":"4.5.3","goup":"0.16.11","sqlpackage":"not found","python_origin":"workspace_venv","handler_rust":"rustup/cargo","clang":"20.1.8","unified_overlay_optional":"mise/proto","rscript_cmd":"C:\\Program Files\\R\\R-4.5.3\\bin\\x64\\Rscript.exe","gcc":"not found","vs_enterprise":"not found","orchestration_mode":"polyglot_router","research_ingest_role":"supplemental_input","pacman_cmd":"not found","sqlcmd":"15.0.1300","rv_cmd":"alias -> Remove-Variable","handler_ruby":"rv (rvw wrapper optional)","rv_r_cmd":"C:\\Users\\eldno\\chthonic-archive\\scripts\\rv-r.ps1","zig_cmd":"C:\\Users\\eldno\\.zv\\bin\\zig.exe","handler_zig":"zv","cargo":"1.95.0","code-insiders":"1.121.0-insider","rv":"0.5.3","vulkan":"1.4.341.1","bicep":"0.42.1","rv_r":"0.19.0"}
```

## chthonic doctor --origins

```text

CHTHONIC ORIGINS v3.3.0
========================================================================
  ruby      ~\AppData\Roaming\rv\rubies\ruby-4.0.3\bin\ruby.exe rv (irm rv.dev/install.ps1)
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
  R         C:\Program Files\R\R-4.5.3\bin\x64\R.exe     current R runtime (manager intentionally none)
  Rscript   C:\Program Files\R\R-4.5.3\bin\x64\Rscript.exe current R helper (manager intentionally none)
  rv-r      ~\chthonic-archive\scripts\rv-r.ps1          A2-ai/rv via repo wrapper
  goup      ~\.cargo\bin\goup.exe                        GH release binary
  cargo     ~\.cargo\bin\cargo.exe                       rustup toolchain
  rustup    ~\.cargo\bin\rustup.exe                      rustup manager
  brush     ~\.cargo\bin\brush.exe                       cargo install brush-shell
  pacman    ~\AppData\Roaming\rv\rubies\ruby-4.0.3\msys64\usr\bin\pacman.exe MSYS2 package manager (RubyInstaller DevKit)
  msys2     (not found)                                  RubyInstaller DevKit / MSYS2 root
  biome     ~\chthonic-archive\node_modules\.bin\biome.exe repo bun dependency or curated global tool
  ruff      ~\.local\bin\ruff.exe                        uv tool
  cmake     ~\.local\bin\cmake.exe                       uv tool
  ninja     ~\.local\bin\ninja.exe                       uv tool
  mdbook    ~\.cargo\bin\mdbook.exe                      cargo install
  git       C:\Program Files\Git\cmd\git.exe             native installer
  gcc       (not found)                                  MSYS2 (RubyInstaller)
  az        C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd Azure CLI MSI
  bicep     ~\AppData\Local\Microsoft\WinGet\Links\bicep.exe winget (Microsoft.Bicep)
  sqlcmd    C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\170\Tools\Binn\SQLCMD.EXE winget (Microsoft.Sqlcmd)
  sqlpackage(not found)                                  winget (Microsoft.SqlPackage)
  cl        C:\Program Files\Microsoft Visual Studio\18\Insiders\VC\Tools\MSVC\14.51.36231\bin\Hostx64\x64\cl.exe Visual Studio 2026 C++ toolchain
  msbuild   C:\Program Files\Microsoft Visual Studio\18\Insiders\MSBuild\Current\Bin\MSBuild.exe Visual Studio 2026 Build Tools
  clang     C:\Program Files\Microsoft Visual Studio\18\Insiders\VC\Tools\Llvm\bin\clang.exe Visual Studio 2026 LLVM toolset
  glslc     C:\VulkanSDK\1.4.341.1\Bin\glslc.exe         Vulkan SDK
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
  C:\Users\eldno\AppData\Local\Microsoft\WinGet\Links  Bicep CLI (winget)
  C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\170\Tools\Binn  Sqlcmd Tools (winget)
  C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools  Visual Studio Build Tools 2026 (Insiders)
  C:\Program Files\Microsoft Visual Studio\18\Insiders  Visual Studio Community 2026 (Insiders)
========================================================================
```
