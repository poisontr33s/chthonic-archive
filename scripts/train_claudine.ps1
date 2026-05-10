#!/usr/bin/env pwsh
# @SID: train_claudine.ps1 — LoRA training launcher for C-G4
# Wraps P-04_lora_train.py with correct PATH for uv

param(
    [int]$Steps = 2000,
    [switch]$DryRun
)

$env:PATH = "C:\Users\eldno\.local\bin;$env:PATH"

$args_list = @("run", "probes/claudine/P-04_lora_train.py", "--steps", $Steps)
if ($DryRun) { $args_list += "--dry-run" }

& uv @args_list 2>&1 | Tee-Object -FilePath manifest/p04_train_log.txt
