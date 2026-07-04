#!/usr/bin/env pwsh
# @SID: SCRIPT_VALIDATE_DOCS_CONTENT_V1
# -*- coding: utf-8 -*-
# Validate documentation content: file references, paths, and @SID claims
# Usage: .\validate_docs_content.ps1

# Metadata (was a non-parsing pseudo-DSL block since first commit — converted to comments 2026-07-04, content preserved):
#   Title:        Documentation Content Validator
#   Author:       erdn0
#   Description:  Validates file references, paths, and @SID claims in documentation markdown files.
#   Version:      1.0.0
#   Requires:     PowerShell 7.1


[CmdletBinding()]
param()

$ErrorActionPreference = 'Continue'

# UTF-8 output
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$repoRoot = Split-Path $PSScriptRoot -Parent
$docsDir = Join-Path $repoRoot "docs"

Write-Host "`n=== Documentation Content Validation ===" -ForegroundColor Cyan
Write-Host "Validating file references, paths, and claims in docs/*.md`n" -ForegroundColor Gray

$issues = @()
$validated = @()

# Get all markdown files in docs/
$docFiles = Get-ChildItem -Path $docsDir -Filter "*.md" -File

foreach ($doc in $docFiles) {
    Write-Host "Validating: $($doc.Name)" -ForegroundColor Yellow
    $content = Get-Content $doc.FullName -Raw

    # Check for missing Metadata block
    $hasMetadata = $content -match '(^|\r?\n)\s*Metadata\s*\{'
    if (-not $hasMetadata) {
        $issues += [PSCustomObject]@{
            Doc = $doc.Name
            Type = "Missing Metadata"
            Reference = "Metadata"
            Details = "Metadata block not found"
        }
        Write-Host "  ⚠️  Missing Metadata block" -ForegroundColor Yellow
    }
    
    # Extract file path references (various patterns)
    $fileRefs = @()
    
    # Pattern 1: Backtick paths like `path/to/file.ext`
    $fileRefs += [regex]::Matches($content, '`([^`]+\.[a-zA-Z0-9]+)`') | 
        ForEach-Object { $_.Groups[1].Value }
    
    # Pattern 2: Markdown links [text](path)
    $fileRefs += [regex]::Matches($content, '\]\(([^)]+\.(?:md|ts|js|json|ps1|py|txt|toml))\)') | 
        ForEach-Object { $_.Groups[1].Value }
    
    # Pattern 3: Direct mentions of scripts/ mcp/ etc.
    $fileRefs += [regex]::Matches($content, '(?:scripts|mcp|docs|src|packages|mas_mcp)/[^\s`"'']+\.(?:ts|js|json|md|ps1|py)') | 
        ForEach-Object { $_.Value }
    
    # Pattern 4: .github/ references
    $fileRefs += [regex]::Matches($content, '\.github/[^\s`"'']+\.(?:md|json)') | 
        ForEach-Object { $_.Value }
    
    # Deduplicate
    $fileRefs = $fileRefs | Select-Object -Unique | Where-Object { $_ -and $_ -notmatch '^https?://' }
    
    foreach ($ref in $fileRefs) {
        # Clean up
        $cleanRef = $ref.Trim('`\"''')
        
        # Skip if it's a placeholder
        if ($cleanRef -match '<|>|\$|\{|\}') { continue }
        
        # Try to resolve the path
        $fullPath = $null
        
        if ([System.IO.Path]::IsPathRooted($cleanRef)) {
            $fullPath = $cleanRef
        } else {
            # Try relative to repo root
            $fullPath = Join-Path $repoRoot $cleanRef.Replace('/', '\')
        }
        
        if ($fullPath -and -not (Test-Path $fullPath)) {
            $issues += [PSCustomObject]@{
                Doc = $doc.Name
                Type = "Missing File"
                Reference = $cleanRef
                Details = "File does not exist"
            }
            Write-Host "  ❌ Missing: $cleanRef" -ForegroundColor Red
        } else {
            $validated += [PSCustomObject]@{
                Doc = $doc.Name
                Reference = $cleanRef
            }
            Write-Host "  ✅ Valid: $cleanRef" -ForegroundColor Green
        }
    }
    
    # Extract @SID references
    $sidRefs = [regex]::Matches($content, '@(?:References|Implements|Validates|ReferencedBy):\s*([A-Z_,\s]+)') | 
        ForEach-Object { 
            $_.Groups[1].Value -split ',' | 
            ForEach-Object { $_.Trim() } | 
            Where-Object { $_ }
        }
    
    if ($sidRefs) {
        Write-Host "  Checking @SID references..." -ForegroundColor Gray
        
        # Get current SID index
        $sidIndexPath = Join-Path $repoRoot "scripts\data\indices\sid_index.json"
        if (Test-Path $sidIndexPath) {
            $sidIndex = Get-Content $sidIndexPath | ConvertFrom-Json
            $knownSIDs = $sidIndex.entries | ForEach-Object { $_.sid }
            
            foreach ($sidRef in $sidRefs) {
                if ($knownSIDs -notcontains $sidRef) {
                    $issues += [PSCustomObject]@{
                        Doc = $doc.Name
                        Type = "Unknown SID"
                        Reference = $sidRef
                        Details = "SID not found in index"
                    }
                    Write-Host "  ⚠️  Unknown SID: $sidRef" -ForegroundColor Yellow
                } else {
                    Write-Host "  ✅ SID exists: $sidRef" -ForegroundColor Green
                }
            }
        }
    }
    
    Write-Host ""
}

# Summary
Write-Host "`n=== Validation Summary ===" -ForegroundColor Cyan
Write-Host "Total docs validated: $($docFiles.Count)" -ForegroundColor White
Write-Host "File references checked: $($validated.Count)" -ForegroundColor Green
Write-Host "Issues found: $($issues.Count)" -ForegroundColor $(if($issues.Count -eq 0){'Green'}else{'Red'})

if ($issues.Count -gt 0) {
    Write-Host "`n=== Issues Detected ===" -ForegroundColor Red
    $issues | Format-Table -AutoSize
    
    # Export issues to JSON
    $issuesPath = Join-Path $repoRoot "docs\VALIDATION_ISSUES.json"
    $issues | ConvertTo-Json -Depth 3 | Set-Content $issuesPath
    Write-Host "`nIssues exported to: $issuesPath" -ForegroundColor Yellow
}

Write-Host "`n✅ Validation complete!" -ForegroundColor Green

