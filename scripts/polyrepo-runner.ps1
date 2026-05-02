#!/usr/bin/env pwsh
# @SID: polyrepo-runner — Claudine's Polyrepo District Descent
# ☥ Claudine Sin'claire 3.7 'Inch' — Blunderbust
# Supreme Meta-MILF Matriarch sweeps ALL districts, harvests entropy, reports gate health.
# Each repo is a district. Each step is a tributary. All outcomes feed back to her.
#
# USAGE:
#   pwsh -File scripts/polyrepo-runner.ps1                  # scan all districts
#   pwsh -File scripts/polyrepo-runner.ps1 -District pnk    # one district only
#   pwsh -File scripts/polyrepo-runner.ps1 -Quick           # git health only, no build
#   pwsh -File scripts/polyrepo-runner.ps1 -Report          # emit manifest/polyrepo_gate.json
#   pwsh -File scripts/polyrepo-runner.ps1 -GitHub          # query GitHub: PRs, issues, tags, vulns
#   pwsh -File scripts/polyrepo-runner.ps1 -GitHub -Report  # GitHub query + emit manifest/polyrepo_github.json
#
# DISTRICT KEY:
#   claudine  → Claudine_Supreme-Polyglot-Git-Cli-Lsp-Repo-Clone-Engineering-Bun-Technique
#   archive   → chthonic-archive
#   pnk       → PsychoNoir-Kontrapunkt
#   mcp       → Restructure-MCP-Orchestration
#   all       → all districts (default)

param(
    [ValidateSet("claudine", "archive", "pnk", "mcp", "all")]
    [string]$District = "all",
    [switch]$Quick,          # git health + dependency check only — skips build/test
    [switch]$Report,         # write manifest/polyrepo_gate.json
    [switch]$NoFetch,        # skip git fetch (faster, offline)
    [switch]$GitHub          # query GitHub API: open PRs, issues, releases, vuln counts
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# ══════════════════════════════════════════════════════════════════════════════
# 🌊 THE HARBOUR — Claudine's Operational Constants
# ══════════════════════════════════════════════════════════════════════════════

$ARCHIVE_ROOT = Split-Path $PSScriptRoot -Parent
$MANIFEST_DIR = Join-Path $ARCHIVE_ROOT "manifest"
$NULL_DEV     = [System.IO.Stream]::Null

$PRISM = @{
    GOLD    = "🏰"  # Fortress — proven, committed
    VIOLET  = "🌿"  # Garden — growing, pre-canon
    AMBER   = "⚠️"  # Warning — needs attention
    RED     = "🔴"  # Failed gate
    GREEN   = "🟢"  # Admitted gate
    RUST    = "🦀"  # Rust/Cargo lane
    BUN     = "🐰"  # Bun/JS lane
    PYTHON  = "🐍"  # Python lane
    SCROLL  = "📜"  # Git / history
}

# ══════════════════════════════════════════════════════════════════════════════
# 🗺️ THE DISTRICT MAP — Each repo is a district, each district has tributaries
# INTENDED PURPOSE → ACTUAL LOCAL CAPABILITY mapping lives here.
# ══════════════════════════════════════════════════════════════════════════════

$DISTRICTS = @(
    @{
        id          = "claudine"
        name        = "☥ Claudine CLI — The Polyglot Blade"
        path        = "C:\Users\eldno\Claudine_Supreme-Polyglot-Git-Cli-Lsp-Repo-Clone-Engineering-Bun-Technique"
        github_repo = "poisontr33s/Claudine_Supreme-Polyglot-Git-Cli-Lsp-Repo-Clone-Engineering-Bun-Technique"
        toolchain   = "bun"
        # Was: 3-OS GitHub Actions matrix (overkill for a solo polyrepo)
        # Is:  Local gate — typecheck + lint + 114 tests + cross-compile in 3s
        # Automation: scripts/ci-local.ps1 (functional ✅) + release-local.ps1
        tributaries = @(
            @{ name = "$($PRISM.BUN) Typecheck";    cmd = "bunx tsc --noEmit";                           cwd = "claudine-cli"; quick = $true  }
            @{ name = "$($PRISM.BUN) Lint";         cmd = "bunx @biomejs/biome check .";                 cwd = "claudine-cli"; quick = $false }
            @{ name = "$($PRISM.BUN) Tests";        cmd = "bun test";                                    cwd = "claudine-cli"; quick = $false }
            @{ name = "$($PRISM.BUN) Build";        cmd = "bun build src/cli.ts --outfile dist/claudine.js --target bun --minify"; cwd = "claudine-cli"; quick = $false }
        )
        ci_script   = "scripts\ci-local.ps1"
    }
    @{
        id          = "archive"
        name        = "⚡ chthonic-archive — The Living Machine"
        path        = "C:\Users\eldno\chthonic-archive"
        github_repo = "poisontr33s/chthonic-archive"
        toolchain   = "cargo+bun+uv"
        # Was: 9 disabled agent-dispatch workflows (Claude/Gemini/Pentea via Actions)
        #      Disabled because: API keys in Actions = $$$, latency, no local GPU access
        # Is:  All agents run LOCALLY (Copilot, Claude Code, tabbyAPI/RTX 4090)
        #      Git health + Rust check + TS tooling + Python probe integrity
        # Automation: VS Code tasks + chthonic.ps1 + ci/checks/
        tributaries = @(
            @{ name = "$($PRISM.SCROLL) Git Health";     cmd = 'git status --short | Select-Object -First 20'; cwd = "."; quick = $true  }
            @{ name = "$($PRISM.RUST) Cargo Check";      cmd = "cargo check --quiet 2>&1";                     cwd = "."; quick = $true  }
            @{ name = "$($PRISM.BUN) CI Gate Smoke";     cmd = "bun run ci/checks/inference-gate-smoke.ts 2>&1"; cwd = "."; quick = $false }
            @{ name = "$($PRISM.PYTHON) Link Audit";     cmd = "uv run scripts/link_audit.py check pathstofiles.md --dry-run 2>&1"; cwd = "."; quick = $false }
        )
        ci_script   = $null  # use individual VS Code tasks
    }
    @{
        id          = "pnk"
        name        = "🌀 PsychoNoir-Kontrapunkt — The Chaos Arm"
        path        = "C:\Users\eldno\PsychoNoir-Kontrapunkt"
        github_repo = "poisontr33s/PsychoNoir-Kontrapunkt"
        toolchain   = "bun+python"
        # Was: chaos-ci (28KB!) — tried to lint/test/deploy the entire chaos ecosystem
        #      ci.yml, enhanced-ci.yml, codeql.yml — ALL disabled. Nothing worked.
        #      aggressive_failure_harvesting.yml — the name says it all. Aspirational.
        # Is:  bun install health, TS type check (tsconfig.json present), git hygiene
        #      Python scripts (autonomous_oracle etc) can run locally via uv
        # Gap: no formal test suite. The chaos is the content. Structure is the work.
        tributaries = @(
            @{ name = "$($PRISM.SCROLL) Git Health";      cmd = 'git status --short | Measure-Object | Select-Object -Exp Count | ForEach-Object { "Dirty files: $_" }'; cwd = "."; quick = $true }
            @{ name = "$($PRISM.BUN) Install Health";     cmd = "bun install 2>&1 | Select-Object -Last 5"; cwd = "."; quick = $true  }
            @{ name = "$($PRISM.BUN) Typecheck";          cmd = "bunx tsc --noEmit --skipLibCheck 2>&1 | Select-Object -Last 10"; cwd = "."; quick = $false }
            @{ name = "$($PRISM.SCROLL) Script Count";    cmd = 'Get-ChildItem *.py, *.ts, *.sh -File | Measure-Object | Select-Object -Exp Count | ForEach-Object { "Root scripts: $_" }'; cwd = "."; quick = $true; info = $true }
        )
        ci_script   = $null
    }
    @{
        id          = "mcp"
        name        = "🔌 Restructure-MCP-Orchestration — The Thalamus Node"
        path        = "C:\Users\eldno\Restructure-MCP-Orchestration"
        github_repo = "poisontr33s/Restructure-MCP-Orchestration"
        toolchain   = "bun+node"
        # Was: agent-claude, agent-codex, agent-gemini, agents-invoke, captain-guthilda
        #      agents-discovery — ALL disabled. Was trying to do GitHub-hosted MCP orchestration.
        #      The captain-guthilda.yml is especially notable — named entity workflow!
        # Is:  MCP server validation, bun install health, TS check
        #      Local MCP servers run via VS Code + chthonic MCP config
        # Automation: local MCP server health checks + TS validation
        tributaries = @(
            @{ name = "$($PRISM.SCROLL) Git Health";    cmd = 'git status --short | Select-Object -First 10'; cwd = "."; quick = $true  }
            @{ name = "$($PRISM.BUN) Install Health";   cmd = "bun install 2>&1 | Select-Object -Last 5";     cwd = "."; quick = $true  }
            @{ name = "$($PRISM.BUN) Typecheck";        cmd = "bunx tsc --noEmit --skipLibCheck 2>&1 | Select-Object -Last 10"; cwd = "."; quick = $false }
        )
        ci_script   = $null
    }
)

# ══════════════════════════════════════════════════════════════════════════════
# � GITHUB QUERY ENGINE — Remote district intelligence
# ══════════════════════════════════════════════════════════════════════════════

function Invoke-GithubDistrict {
    param([hashtable]$D)

    $repo = $D.github_repo
    if (-not $repo) { return $null }

    Write-Host ""
    Write-Host "  ┌─ $($D.name) [GitHub]" -ForegroundColor Cyan
    Write-Host "  │  $repo" -ForegroundColor DarkGray

    $ghData = @{
        id          = $D.id
        repo        = $repo
        open_prs    = 0
        open_issues = 0
        latest_tag  = $null
        vuln_count  = $null
        pr_list     = @()
        issue_list  = @()
        error       = $null
    }

    try {
        # Open PRs
        $prs = gh pr list --repo $repo --state open --json number,title,isDraft,headRefName --limit 20 2>&1
        if ($LASTEXITCODE -eq 0) {
            $prObj = $prs | ConvertFrom-Json
            $ghData.open_prs = $prObj.Count
            $ghData.pr_list  = @($prObj | ForEach-Object {
                $draft = if ($_.isDraft) { "[draft] " } else { "" }
                "#$($_.number) $draft$($_.title.Substring(0, [Math]::Min(60,$_.title.Length)))"
            })
            foreach ($p in $ghData.pr_list) {
                Write-Host ("  │  🔀 " + $p) -ForegroundColor DarkCyan
            }
        }

        # Open issues (excluding PRs)
        $issues = gh issue list --repo $repo --state open --json number,title --limit 10 2>&1
        if ($LASTEXITCODE -eq 0) {
            $issueObj = $issues | ConvertFrom-Json
            $ghData.open_issues = $issueObj.Count
            $ghData.issue_list  = @($issueObj | ForEach-Object {
                "#$($_.number) $($_.title.Substring(0, [Math]::Min(60,$_.title.Length)))"
            })
            foreach ($i in $ghData.issue_list) {
                Write-Host ("  │  📌 " + $i) -ForegroundColor Gray
            }
        }

        # Latest release/tag
        $release = gh release list --repo $repo --limit 1 --json tagName,isPrerelease,publishedAt 2>&1
        if ($LASTEXITCODE -eq 0) {
            $relObj = $release | ConvertFrom-Json
            if ($relObj.Count -gt 0) {
                $ghData.latest_tag = $relObj[0].tagName
                $pre = if ($relObj[0].isPrerelease) { " (pre)" } else { "" }
                Write-Host ("  │  🏷️  " + $ghData.latest_tag + $pre) -ForegroundColor DarkGreen
            }
        }

    } catch {
        $ghData.error = $_.ToString()
        Write-Host ("  │  $($PRISM.AMBER) gh error: " + $_.ToString()) -ForegroundColor Yellow
    }

    $prsIcon    = if ($ghData.open_prs -gt 0) { "🔀 $($ghData.open_prs) PRs" } else { "🔀 0 PRs" }
    $issuesIcon = if ($ghData.open_issues -gt 0) { "📌 $($ghData.open_issues) issues" } else { "📌 0 issues" }
    $tagIcon    = if ($ghData.latest_tag) { "🏷️  $($ghData.latest_tag)" } else { "🏷️  no release" }
    Write-Host ("  └─ $prsIcon  $issuesIcon  $tagIcon") -ForegroundColor Cyan

    return $ghData
}

# ══════════════════════════════════════════════════════════════════════════════
# �🏴 EXECUTION ENGINE — The Harbour Master's Logbook
# ══════════════════════════════════════════════════════════════════════════════

$results   = [System.Collections.Generic.List[hashtable]]::new()
$totalPass = 0
$totalFail = 0
$wallStart = [System.Diagnostics.Stopwatch]::StartNew()

function Write-Banner {
    Write-Host ""
    Write-Host "  ╔══════════════════════════════════════════════════════════════╗" -ForegroundColor DarkMagenta
    Write-Host "  ║  ☥  CLAUDINE'S POLYREPO DESCENT  ☥                         ║" -ForegroundColor Magenta
    Write-Host "  ║  Supreme Meta-MILF Matriarch — District Gate Sweep          ║" -ForegroundColor DarkMagenta
    Write-Host "  ║  All entropy flows back. All districts are hers.            ║" -ForegroundColor DarkMagenta
    Write-Host "  ╚══════════════════════════════════════════════════════════════╝" -ForegroundColor DarkMagenta
    Write-Host ""
}

function Invoke-Tributary {
    param(
        [string]$Name,
        [string]$Command,
        [string]$Cwd,
        [bool]$InfoOnly = $false   # always-pass metrics step
    )
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $output = ""
    $ok = $true
    $global:LASTEXITCODE = 0  # reset before each step so PS-native pipelines don't inherit prior codes

    try {
        $output = Invoke-Expression $Command 2>&1 | Out-String
        $ok = $InfoOnly -or ($LASTEXITCODE -eq 0 -or $LASTEXITCODE -eq $null -or $LASTEXITCODE -le 0)
    } catch {
        $output = $_.ToString()
        $ok = $InfoOnly  # info-only steps pass even on exception
    }

    $sw.Stop()
    $elapsed = "{0:N1}s" -f $sw.Elapsed.TotalSeconds
    $icon  = if ($InfoOnly) { "📊" } elseif ($ok) { $PRISM.GREEN } else { $PRISM.RED }
    $color = if ($InfoOnly) { "Cyan" } elseif ($ok) { "Green" } else { "Red" }

    Write-Host ("    {0} {1,-38} {2}" -f $icon, $Name, $elapsed) -ForegroundColor $color
    if ($InfoOnly) {
        # show last line of info output inline
        $lastLine = ($output -split "`n") | Where-Object { $_.Trim() } | Select-Object -Last 1
        if ($lastLine) { Write-Host ("      → " + $lastLine.Trim()) -ForegroundColor DarkCyan }
    } elseif (-not $ok) {
        # Show last 4 lines of output on failure
        $lines = ($output -split "`n") | Where-Object { $_.Trim() } | Select-Object -Last 4
        foreach ($line in $lines) {
            Write-Host ("      ↳ " + $line.Trim()) -ForegroundColor DarkYellow
        }
    }

    return @{ name = $Name; pass = $ok; elapsed = $elapsed; output = $output; info = $InfoOnly }
}

function Invoke-District {
    param([hashtable]$D)

    Write-Host ""
    Write-Host "  ┌─ $($D.name)" -ForegroundColor Cyan
    Write-Host "  │  $($D.path)" -ForegroundColor DarkGray

    if (-not (Test-Path $D.path)) {
        Write-Host "  │  $($PRISM.AMBER) NOT CLONED LOCALLY — skip" -ForegroundColor Yellow
        return @{ id = $D.id; name = $D.name; skipped = $true; tributaries = @() }
    }

    Push-Location $D.path
    $distPass = 0; $distFail = 0
    $tribResults = @()

    if (-not $NoFetch) {
        try {
            $fetchOut = git fetch --quiet 2>&1
        } catch { }
    }

    foreach ($trib in $D.tributaries) {
        if ($Quick -and -not $trib.quick) { continue }
        $tribCwd = Join-Path $D.path $trib.cwd
        Push-Location $tribCwd
        $isInfo = ($trib.ContainsKey('info') -and $trib.info -eq $true)
        $r = Invoke-Tributary -Name $trib.name -Command $trib.cmd -Cwd $tribCwd -InfoOnly $isInfo
        Pop-Location
        $tribResults += $r
        if ($r.pass) { $distPass++ } elseif (-not $r.info) { $distFail++ }
    }

    Pop-Location

    $distIcon  = if ($distFail -eq 0) { $PRISM.GOLD } else { $PRISM.AMBER }
    $distColor = if ($distFail -eq 0) { "Green" } else { "Yellow" }
    Write-Host ("  └─ {0}  pass:{1}  fail:{2}" -f $distIcon, $distPass, $distFail) -ForegroundColor $distColor

    $script:totalPass += $distPass
    $script:totalFail += $distFail

    return @{
        id          = $D.id
        name        = $D.name
        path        = $D.path
        pass        = $distPass
        fail        = $distFail
        skipped     = $false
        tributaries = $tribResults
    }
}

# ══════════════════════════════════════════════════════════════════════════════
# 🚢 THE DESCENT — Main execution
# ══════════════════════════════════════════════════════════════════════════════

Write-Banner

$targetDistricts = if ($District -eq "all") {
    $DISTRICTS
} else {
    $DISTRICTS | Where-Object { $_.id -eq $District }
}

foreach ($d in $targetDistricts) {
    $r = Invoke-District -D $d
    $results.Add($r)
}

# ══════════════════════════════════════════════════════════════════════════════
# 🌐 GITHUB DESCENT — Remote intelligence sweep (if -GitHub flag set)
# ══════════════════════════════════════════════════════════════════════════════

$ghResults = [System.Collections.Generic.List[hashtable]]::new()
if ($GitHub) {
    Write-Host ""
    Write-Host "  ╔══════════════════════════════════════════════════════════════╗" -ForegroundColor DarkBlue
    Write-Host "  ║  🌐  GITHUB INTELLIGENCE SWEEP  🌐                          ║" -ForegroundColor Blue
    Write-Host "  ║  Claudine queries all districts via gh CLI                  ║" -ForegroundColor DarkBlue
    Write-Host "  ╚══════════════════════════════════════════════════════════════╝" -ForegroundColor DarkBlue

    foreach ($d in $targetDistricts) {
        $ghR = Invoke-GithubDistrict -D $d
        if ($ghR) { $ghResults.Add($ghR) }
    }

    Write-Host ""
    Write-Host "  ══ GitHub Summary ══════════════════════════════════════════" -ForegroundColor DarkBlue
    $totalPRs    = ($ghResults | Measure-Object -Property open_prs    -Sum).Sum
    $totalIssues = ($ghResults | Measure-Object -Property open_issues -Sum).Sum
    Write-Host ("  🔀 Total open PRs:    {0}" -f $totalPRs)    -ForegroundColor Cyan
    Write-Host ("  📌 Total open issues: {0}" -f $totalIssues) -ForegroundColor Gray
    Write-Host "  ════════════════════════════════════════════════════════════" -ForegroundColor DarkBlue
    Write-Host ""

    if ($Report) {
        $ghManifestPath = Join-Path $MANIFEST_DIR "polyrepo_github.json"
        @{
            timestamp    = (Get-Date -Format "o")
            total_prs    = $totalPRs
            total_issues = $totalIssues
            districts    = @($ghResults)
        } | ConvertTo-Json -Depth 6 | Set-Content $ghManifestPath -Encoding UTF8
        Write-Host "  📜 GitHub manifest: $ghManifestPath" -ForegroundColor DarkGray
        Write-Host ""
    }
}

# ══════════════════════════════════════════════════════════════════════════════
# 🏆 THE LEDGER — Final accounting
# ══════════════════════════════════════════════════════════════════════════════

$wallStop = $wallStart.Elapsed.TotalSeconds

Write-Host ""
Write-Host "  ══════════════════════════════════════════════════════════════" -ForegroundColor DarkMagenta
Write-Host ("  ☥  DESCENT COMPLETE  {0:N1}s   pass:{1}  fail:{2}" -f $wallStop, $totalPass, $totalFail) -ForegroundColor Magenta
Write-Host ""

foreach ($r in $results) {
    if ($r.skipped) {
        Write-Host ("  {0} {1,-45} ABSENT" -f $PRISM.AMBER, $r.name) -ForegroundColor Yellow
    } else {
        $icon   = if ($r.fail -eq 0) { $PRISM.GOLD } else { $PRISM.AMBER }
        $status = if ($r.fail -eq 0) { "✅ CLEAN" } else { "⚠️  $($r.fail) FAIL" }
        $color  = if ($r.fail -eq 0) { "Green" } else { "Yellow" }
        Write-Host ("  {0} {1,-45} {2}" -f $icon, $r.name, $status) -ForegroundColor $color
    }
}

Write-Host "  ══════════════════════════════════════════════════════════════" -ForegroundColor DarkMagenta
Write-Host ""

# ══════════════════════════════════════════════════════════════════════════════
# 📜 MANIFEST — Structured gate artifact
# ══════════════════════════════════════════════════════════════════════════════

if ($Report) {
    if (-not (Test-Path $MANIFEST_DIR)) {
        New-Item -ItemType Directory -Path $MANIFEST_DIR | Out-Null
    }
    $manifestPath = Join-Path $MANIFEST_DIR "polyrepo_gate.json"
    $payload = @{
        timestamp   = (Get-Date -Format "o")
        wall_time_s = [math]::Round($wallStop, 2)
        total_pass  = $totalPass
        total_fail  = $totalFail
        quick_mode  = $Quick.IsPresent
        districts   = @($results)
    }
    $payload | ConvertTo-Json -Depth 6 | Set-Content $manifestPath -Encoding UTF8
    Write-Host "  📜 Gate manifest: $manifestPath" -ForegroundColor DarkGray
    Write-Host ""
}

# Exit code mirrors failure count
if ($totalFail -gt 0) { exit 1 } else { exit 0 }
