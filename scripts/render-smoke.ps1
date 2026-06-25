#!/usr/bin/env pwsh
#
# render-smoke.ps1 — build the renderer, run it for a bounded window, capture ALL output,
# kill it, and report validation/NGX/panic status. Lets the agent self-verify a render increment
# (the loop's Test/Verify step) without babysitting a window.
#
#   pwsh -File scripts/render-smoke.ps1 [-Seconds 6] [-Profile]
#
# -Profile: run for 300 frames (CHTHONIC_MAX_FRAMES=300) and print a GPU timing summary
#           from the "GPU |" info lines emitted every 120 frames.
#
# Exit 0 = PASS (no validation / NGX / panic failures). Exit 1 = build failed or FAIL.

param(
    [int]$Seconds = 6,
    [switch]$Profile
)

$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$exe  = Join-Path $root 'target\debug\chthonic-archive.exe'
$log  = Join-Path $root 'target\render-smoke.log'
$out  = "$log.out"
$err  = "$log.err"
$rdir = Join-Path $root 'renders'
$png  = Join-Path $rdir 'render-smoke.png'

# The renderer reads CHTHONIC_SCREENSHOT and dumps frame >=5 to this PNG so the
# agent can self-verify the pixels (Read the file) instead of needing a human screenshot.
# renders/ lives at repo root (visible in VS Code, unlike target/) but is gitignored.
New-Item -ItemType Directory -Force -Path $rdir | Out-Null
Remove-Item $png -ErrorAction SilentlyContinue
$env:CHTHONIC_SCREENSHOT = $png

if ($Profile) {
    $env:CHTHONIC_MAX_FRAMES   = '300'
    $env:CHTHONIC_PRESENT_MODE = 'immediate'  # bypass V-sync so background window doesn't throttle
    $runSec = 60   # 300 frames uncapped should finish in <10s; 60s is safety ceiling
    Write-Output "== PROFILE MODE: running up to 300 frames (${runSec}s ceiling, IMMEDIATE present) =="
} else {
    Remove-Item env:CHTHONIC_MAX_FRAMES   -ErrorAction SilentlyContinue
    Remove-Item env:CHTHONIC_PRESENT_MODE -ErrorAction SilentlyContinue
    $runSec = $Seconds
}

Write-Output "== cargo build =="
& cargo build --manifest-path (Join-Path $root 'Cargo.toml') -p chthonic-archive 2>&1 | Tee-Object -FilePath $log
if ($LASTEXITCODE -ne 0) { Write-Output "BUILD FAILED (exit $LASTEXITCODE)"; exit 1 }
if (-not (Test-Path $exe)) { Write-Output "exe not found after build: $exe"; exit 1 }

Write-Output "== run ${runSec}s (windowed; killed after timeout) =="
$p = Start-Process -FilePath $exe -WorkingDirectory $root -PassThru `
        -RedirectStandardOutput $out -RedirectStandardError $err
try { Wait-Process -Id $p.Id -Timeout $runSec -ErrorAction Stop }
catch { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }

# Fold the run's stdout+stderr into the build log so the whole record is one file.
Get-Content $err, $out -ErrorAction SilentlyContinue | Add-Content -Path $log

$signal = Select-String -Path $log -Pattern 'Bathymetry loaded|RENDERER READY|GRAPHICS PIPELINE CREATED' -EA SilentlyContinue
$bad = Select-String -Path $log -Pattern 'VUID-|Validation Error|\bpanicked\b|FATAL|NVSDK_NGX_Result_FAIL|slEvaluateFeature returned|presentCommon\(\) was not observed|Failed to create renderer|failed to read.*\.spv' -EA SilentlyContinue |
       Where-Object { $_.Line -notmatch 'layers enabled|VkLayer_khronos' } |
       Where-Object { $_.Line -notmatch 'VUID-vkDestroyDevice-device-05137' }  # force-kill teardown noise

# GPU timing summary (Profile mode only)
if ($Profile) {
    Write-Output ""
    Write-Output "== GPU timing summary =="
    $gpuLines = Select-String -Path $log -Pattern 'GPU \|' -EA SilentlyContinue
    if ($gpuLines) {
        # Parse "cloud: X.XXms | dlaa: X.XXms | frame: X.XXms" from each line
        $cloudVals = @(); $dlaaVals = @(); $frameVals = @()
        foreach ($gl in $gpuLines) {
            if ($gl.Line -match 'cloud:\s*([\d.]+)ms') { $cloudVals += [double]$Matches[1] }
            if ($gl.Line -match 'dlaa:\s*([\d.]+)ms')  { $dlaaVals  += [double]$Matches[1] }
            if ($gl.Line -match 'frame:\s*([\d.]+)ms') { $frameVals += [double]$Matches[1] }
        }
        function Stats($vals, $label) {
            if ($vals.Count -eq 0) { Write-Output "  $label : no data"; return }
            $mn = ($vals | Measure-Object -Minimum).Minimum
            $mx = ($vals | Measure-Object -Maximum).Maximum
            $av = ($vals | Measure-Object -Average).Average
            $budget = if ($label -eq 'frame') { ' (budget: 4.17ms@240Hz)' } else { '' }
            Write-Output ("  {0,-8}: min={1:F2}ms  avg={2:F2}ms  max={3:F2}ms  ({4} samples){5}" `
                -f $label, $mn, $av, $mx, $vals.Count, $budget)
        }
        Stats $cloudVals 'cloud'
        Stats $dlaaVals  'dlaa'
        Stats $frameVals 'frame'
        Write-Output ""
        Write-Output "  Decision gate: cloud avg < 2.0ms → full-res OK | 2.0–3.5ms → headroom noted | >3.5ms → checkerboard needed"
    } else {
        Write-Output "  No 'GPU |' lines found in log — timestamp queries may not have fired yet (check DLAA state)"
    }
    Write-Output ""
}

Write-Output "== summary =="
$signal | ForEach-Object { ($_.Line -replace '\x1b\[[0-9;]*m','').Trim() }
if ($bad) {
    Write-Output "FAIL: $($bad.Count) validation/NGX/panic line(s):"
    $bad | Select-Object -First 12 | ForEach-Object { ($_.Line -replace '\x1b\[[0-9;]*m','').Trim() }
    Write-Output "full log: $log"
} else {
    Write-Output "PASS: no validation / NGX / panic failures"
}
if (Test-Path $png) {
    Write-Output "screenshot: $png ($((Get-Item $png).Length) bytes)"
} else {
    Write-Output "screenshot: NOT WRITTEN (capture failed or env not honored)"
}
Write-Output "full log: $log"
if ($bad) { exit 1 }
exit 0
