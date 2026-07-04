# 🚀 Chthonic-Archive-Quick Reference
**VSCode-Insiders | PowerShell-7.x.x | Win-11**

---

## ⚡ Essential-Commands

### VSCode-CLI
```pwsh
code-insiders .                    # Open current dir
code-insiders --version            # Version check
code-insiders --list-extensions    # List extensions
code-insiders --install-extension  # Install extension
```

### Shell-Integration
```pwsh
Ctrl+Up / Ctrl+Down               # Navigate commands
Ctrl+Alt+R                        # Recent command palette
Ctrl+Space                        # Terminal IntelliSense
Hover terminal tab                # Check integration quality
```

### Chthonic-Extensions
```pwsh
# Compile extensions (from root)
cd extensions\%name-of-extension%; bun run compile
# Load (F5 in extension directory)
```

### Podman-Management
```pwsh
podman --list --containers        # List containers
podman stop <container_id>        # Stop
podman --list --verbose           # Check distributions
podman --shutdown/wsl --shutdown  # Stop all WSL instances
exit (from bash)                  # Exit WSL properly
# ⚠️ PROTECTED: Typing 'bash' blocked in VSCode terminal
# Use explicit profile selection if needed
```

---

## 🛡️ Safety-Guardrails

### Terminal-Command-Skip-List
```jsonc
"terminal.integrated.commandsToSkipShell": ["bash", "wsl", "ubuntu"]
```
**Effect**: *Prevents accidental WSL launches from Pwsh terminal*

### WSL-Automount-Disabled
```ini
# C:\Users\erdno\.wslconfig
[wsl2]
automount=false  # No /mnt/c mounting
```
**Effect**: `bash` *won't mount Windows drives unless explicitly configured*

### Crude-Mode (No Profile)
```pwsh
pwsh.exe -NoProfile -NoExit
```
**Effect**: *Deterministic startup, no hidden aliases/functions*

---

## 📊 Resource Monitoring

```pwsh
# Quick check
Get-Process | Where-Object { $_.ProcessName -like '*Code*' } |
  Measure-Object -Property WS -Sum |
  Select-Object @{Name='Total MB';Expression={[math]::Round($_.Sum/1MB,2)}}

# Detailed view
Get-Process | Where-Object { $_.ProcessName -like '*Code*' } |
  Select-Object ProcessName, Id,
    @{Name='MB';Expression={[math]::Round($_.WS/1MB,2)}},
    @{Name='CPU';Expression={[math]::Round($_.CPU,2)}} |
  Sort-Object MB -Descending
```

**Normal-Range**: *2.5-3.5 GB total (12 processes)*
**⚠️-Warning**: *>4 GB (check for leaks)*

---

## 🔧 Configuration Paths

| Item | Location |
|------|----------|
| **VSCode Insiders Bin** | `C:\Users\erdno\AppData\Local\Programs\Microsoft VS Code Insiders\bin` |
| **Shell Integration** | `...\7c62052af6\resources\app\out\vs\workbench\contrib\terminal\common\scripts\shellIntegration.ps1` |
| **WSL Config** | `C:\Users\erdno\.wslconfig` |
| **Workspace Settings** | `c:\Users\erdno\chthonic-archive\.vscode\settings.json` |
| **Extensions** | `c:\Users\erdno\chthonic-archive\extensions\` |

---

## 🎯 Common Tasks

### Reload VSCode Window
```
Ctrl+Shift+P → "Developer: Reload Window"
```

### Open New Terminal
```
Ctrl+Shift+`
```

### Select Terminal Profile
```
Ctrl+Shift+P → "Terminal: Select Default Profile"
```

### View Extension Logs
```
Ctrl+Shift+P → "Developer: Show Running Extensions"
Ctrl+Shift+P → "Developer: Show Logs"
```

### Kill-Low-Resource-Processes
```pwsh
Get-Process | Where-Object {
  $_.ProcessName -eq 'Code - Insiders' -and
  $_.CPU -lt 0.5 -and $_.WS -lt 100MB
} | Stop-Process -Force
```

---

## ✅ Health-Checks

### Shell Integration: Rich
```pwsh
# Hover terminal tab → Should show:
# "Shell Integration: Rich"
```

### WSL-Stopped
```pwsh
wsl --list --verbose
# Expected: Ubuntu | Stopped | 2
```

### Extensions-Compiled
```pwsh
Get-ChildItem -Path ".\extensions" -Recurse -Include "extension.js"
# Expected: 2 files (20.67 KB + 16.91 KB)
```

### CLI-Available
```pwsh
code-insiders --version
# Expected: 1.109.0-insider
```

---

**Last Updated**: January 9, 2026
**Status**: ✅ All systems operational
