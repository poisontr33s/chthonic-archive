#!/usr/bin/env pwsh
#
# @SID: SCRIPT_AWS_V1
# @Type: UTILITY
# @Spectrum: WHITE
# @Zone: THE GARDEN
# @Purpose: Shim to make AWS CLI available in shells that don't inherit updated PATH.
#

# Shim to make AWS CLI available in shells that don't inherit updated PATH.
# Forwards all args to the real AWS CLI install.
$awsExe = "C:\Program Files\Amazon\AWSCLIV2\aws.exe"
if (!(Test-Path $awsExe)) {
  Write-Error "AWS CLI not found at: $awsExe"
  exit 127
}
& $awsExe @args
exit $LASTEXITCODE
