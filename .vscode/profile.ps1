# ╔══════════════════════════════════════════════════════════════════╗
# ║   THE CHTHONIC ARCHIVE - PowerShell Profile                      ║
# ║   Workspace-specific PATH and aliases for native toolchain       ║
# ║   🔥💀⚓ CLAUDINE POLYGLOT ENVIRONMENT                            ║
# ╚══════════════════════════════════════════════════════════════════╝

# Prioritize native toolchain over Ruby's MSYS2
$env:PATH = "$env:USERPROFILE\.local\bin;" +
            "$env:USERPROFILE\.bun\bin;" +
            "$env:USERPROFILE\.cargo\bin;" +
            "$env:PATH"

# Python 3.14 alias (since uv installs as python3.14.exe)
function python {
    & "$env:USERPROFILE\.local\bin\python3.14.exe" @args
}

# Quick version check
function claudine-versions {
    Write-Host "🔥💀⚓ CLAUDINE POLYGLOT ENVIRONMENT" -ForegroundColor Cyan
    Write-Host "══════════════════════════════════════════════════════════" -ForegroundColor DarkGray
    Write-Host "  🍞 Bun     $(bun --version)" -ForegroundColor Yellow
    Write-Host "  🎨 Biome   $(biome --version)" -ForegroundColor Magenta
    Write-Host "  📦 Rust    $(rustc --version)" -ForegroundColor Red
    Write-Host "  🐹 Go      $(go version)" -ForegroundColor Cyan
    Write-Host "  🐍 Python  $(python --version)" -ForegroundColor Blue
    Write-Host "  🧹 Ruff    $(ruff --version)" -ForegroundColor Green
    Write-Host "  💎 Ruby    $(ruby --version)" -ForegroundColor Red
    Write-Host "  🔧 GCC     $(gcc --version | Select-Object -First 1)" -ForegroundColor White
    Write-Host "══════════════════════════════════════════════════════════" -ForegroundColor DarkGray
}

Write-Host "✅ Chthonic Archive workspace profile loaded" -ForegroundColor Green
Write-Host "   Python 3.14.0 aliased to 'python' command" -ForegroundColor DarkGray
Write-Host "   Run 'claudine-versions' to verify toolchain" -ForegroundColor DarkGray
