#!/usr/bin/env pwsh
# Tool validation script — honest exit codes, no pipelines
$d = "C:\Users\eldno\AppData\Roaming\uv\tools"
$pass = 0; $fail = 0

function Check {
    param([string]$Name, [string]$Bin, [string[]]$A)
    if (-not (Test-Path $Bin)) {
        Write-Host "MISSING  $Name => $Bin" -ForegroundColor Red
        $script:fail++
        return
    }
    $proc = Start-Process -FilePath $Bin -ArgumentList $A -NoNewWindow -Wait -PassThru -RedirectStandardOutput "$env:TEMP\_uv_val_stdout.txt" -RedirectStandardError "$env:TEMP\_uv_val_stderr.txt"
    $ec = $proc.ExitCode
    $out = (Get-Content "$env:TEMP\_uv_val_stdout.txt" -ErrorAction SilentlyContinue) -join "`n"
    $err = (Get-Content "$env:TEMP\_uv_val_stderr.txt" -ErrorAction SilentlyContinue) -join "`n"
    $combined = ($out + $err).Trim() -split "`n" | Select-Object -First 1
    if ($ec -eq 0) {
        Write-Host "OK       $Name => $combined" -ForegroundColor Green
        $script:pass++
    } else {
        Write-Host "FAIL[$ec] $Name => $combined" -ForegroundColor Red
        $script:fail++
    }
}

Write-Host "`n=== uv tool validation ===" -ForegroundColor Cyan
Check "cmake"             "$d\cmake\Scripts\cmake.exe"                       @("--version")
Check "cpack"             "$d\cmake\Scripts\cpack.exe"                       @("--version")
Check "ctest"             "$d\cmake\Scripts\ctest.exe"                       @("--version")
Check "ninja"             "$d\ninja\Scripts\ninja.exe"                       @("--version")
Check "ruff"              "$d\ruff\Scripts\ruff.exe"                         @("version")
Check "ipython"           "$d\ipython\Scripts\ipython.exe"                   @("--version")
Check "ipython3"          "$d\ipython\Scripts\ipython3.exe"                  @("--version")
Check "debugpy"           "$d\debugpy\Scripts\debugpy.exe"                   @("--version")
Check "debugpy-adapter"   "$d\debugpy\Scripts\debugpy-adapter.exe"           @("--help")
Check "hf"                "$d\huggingface-hub\Scripts\hf.exe"                @("version")
Check "tiny-agents"       "$d\huggingface-hub\Scripts\tiny-agents.exe"       @("--help")
Check "jupyter-lab"       "$d\jupyterlab\Scripts\jupyter-lab.exe"            @("--version")
Check "jlpm"              "$d\jupyterlab\Scripts\jlpm.exe"                   @("--version")
Check "jupyter-labext"    "$d\jupyterlab\Scripts\jupyter-labextension.exe"   @("--version")
Check "ccc"               "$d\cocoindex-code\Scripts\ccc.exe"                @("--help")
Check "cocoindex-code"    "$d\cocoindex-code\Scripts\cocoindex-code.exe"     @("--help")

# node hard-link state
Write-Host "`n=== node hard-link state ===" -ForegroundColor Cyan
$nl = "$env:USERPROFILE\.local\bin\node.exe"
if (Test-Path $nl) {
    $size = (Get-Item $nl).Length
    Write-Host "OK       node.exe exists ($size bytes)" -ForegroundColor Green
    $script:pass++
} else {
    Write-Host "MISSING  node.exe not in ~/.local/bin — jlpm will fail" -ForegroundColor Red
    $script:fail++
}

Write-Host "`n=== result: $pass passed, $fail failed ===" -ForegroundColor Cyan
exit $fail
