#!/usr/bin/env pwsh
#
# @SID: SCRIPT_BOOTSTRAP_GCP_V1
# @Type: UTILITY
# @Spectrum: WHITE
# @Zone: FLUX_GATE
# @Purpose: Bootstrap a GCP project for the Chthonic FLUX OAuth gate.
#
# Provisions a Google Cloud project and enables the APIs required by the
# Phase 4 Google OAuth 2.0 loopback flow. Google does not permit IaC
# creation of the OAuth Consent Screen or Desktop OAuth Clients, so those
# steps are emitted as manual operator instructions at the tail.
#
# Usage (interactive):
#   pwsh -NoProfile -File .\scripts\bootstrap_gcp.ps1
#
# Usage (non-interactive / IaC):
#   pwsh -NoProfile -File .\scripts\bootstrap_gcp.ps1 -ProjectId chthonic-flux-auth
#
# Idempotent: re-running with an existing -ProjectId is safe; project create
# is skipped on AlreadyExists and API enable is a no-op when already enabled.

[CmdletBinding()]
param(
    [string]$ProjectId
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Log([string]$msg) { Write-Host "[bootstrap_gcp] $msg" }
function Warn([string]$msg) { Write-Warning "[bootstrap_gcp] $msg" }
function Fail([string]$msg) { Write-Error "[bootstrap_gcp] $msg"; exit 1 }

# --- Preflight ---------------------------------------------------------------

$gcloud = Get-Command gcloud -ErrorAction SilentlyContinue
if (-not $gcloud) {
    Fail @"
gcloud CLI not found on PATH.

Install Google Cloud SDK first:
  Windows (winget):  winget install --id Google.CloudSDK -e
  Windows (manual):  https://cloud.google.com/sdk/docs/install#windows
  macOS (brew):      brew install --cask google-cloud-sdk
  Linux:             https://cloud.google.com/sdk/docs/install#linux

After install, run: gcloud auth login
Then re-run this script.
"@
}
Log "gcloud found at: $($gcloud.Source)"

# Verify the user is logged in (at least one ACTIVE account)
$activeAccount = (& gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>$null | Select-Object -First 1)
if ([string]::IsNullOrWhiteSpace($activeAccount)) {
    Fail "No ACTIVE gcloud account. Run: gcloud auth login   then re-run this script."
}
Log "active account: $activeAccount"

# --- Project ID resolution ---------------------------------------------------

if ([string]::IsNullOrWhiteSpace($ProjectId)) {
    if ([Environment]::UserInteractive -and -not [Console]::IsInputRedirected) {
        $ProjectId = Read-Host "Enter desired GCP Project ID (e.g. chthonic-flux-auth)"
    } else {
        Fail "ProjectId is required when running non-interactively. Pass -ProjectId <id>."
    }
}
$ProjectId = $ProjectId.Trim()

if ($ProjectId -notmatch '^[a-z][a-z0-9-]{5,29}$') {
    Fail "Invalid Project ID '$ProjectId'. Must be 6-30 chars, lowercase, start with a letter, only [a-z0-9-]."
}
Log "Project ID: $ProjectId"

# --- Create project (idempotent) --------------------------------------------

$existing = (& gcloud projects describe $ProjectId --format="value(projectId)" 2>$null)
if ($LASTEXITCODE -eq 0 -and $existing -eq $ProjectId) {
    Log "project '$ProjectId' already exists, skipping create"
} else {
    Log "creating project '$ProjectId' ..."
    & gcloud projects create $ProjectId --quiet
    if ($LASTEXITCODE -ne 0) { Fail "gcloud projects create failed (exit $LASTEXITCODE)" }
}

# --- Set active project ------------------------------------------------------

Log "setting active project ..."
& gcloud config set project $ProjectId --quiet
if ($LASTEXITCODE -ne 0) { Fail "gcloud config set project failed (exit $LASTEXITCODE)" }

# --- Enable APIs -------------------------------------------------------------

$apis = @(
    'oauth2.googleapis.com',
    'cloudresourcemanager.googleapis.com'
)
Log "enabling APIs: $($apis -join ', ')"
& gcloud services enable $apis --project $ProjectId --quiet
if ($LASTEXITCODE -ne 0) { Fail "gcloud services enable failed (exit $LASTEXITCODE)" }

# --- Manual operator instructions (verbatim, non-skippable) -----------------

$banner = "=" * 78
Write-Host ""
Write-Host $banner
Write-Host "GCP Project initialized. Google restricts automated creation of Desktop OAuth Clients. You must perform the following manual steps:"
Write-Host "1. Open https://console.cloud.google.com/apis/credentials/consent?project=$ProjectId"
Write-Host "2. Select External -> Create. Name it `"Chthonic Flux`". Add your email. Save and Continue."
Write-Host "3. Go to Credentials -> Create Credentials -> OAuth Client ID."
Write-Host "4. Application Type: Desktop App. Name: `"Chthonic Desktop Gate`". Create."
Write-Host "5. Copy the Client ID and inject it into the VS Code settings (chthonic.flux.googleClientId)."
Write-Host $banner
Write-Host ""

Log "done."
exit 0
