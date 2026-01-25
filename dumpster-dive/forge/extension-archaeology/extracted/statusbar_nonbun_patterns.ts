/**
 * EXTRACTED NON-BUN CODE: chthonic-statusbar/src/extension.ts
 * 
 * PURPOSE: Research archive for Node.js → Bun conversion
 * STATUS: Extracted 2026-01-24
 * 
 * VIOLATIONS IDENTIFIED:
 * - Line 15: execSync, execFile imports (NON-BUN)
 * - Line 16-17: fs/path imports (NON-BUN)
 * - Lines 133+: execSync() calls for nvidia-smi, python (NON-BUN)
 * - Various: fs.existsSync(), fs.statSync() (NON-BUN)
 */

// ============================================
// EXTRACTED IMPORTS (NON-BUN)
// ============================================

import * as vscode from 'vscode';
import { execSync, execFile } from 'child_process';  // NON-BUN: Use Bun.$ or Bun.spawn
import * as path from 'path';                         // NON-BUN: Template literals
import * as fs from 'fs';                             // NON-BUN: Use Bun.file()

// ============================================
// EXTRACTED SHELL OPERATIONS (NON-BUN)
// ============================================

// GPU Status Check - SYNCHRONOUS (BLOCKS!)
function getGpuStatus_NONBUN(): string {
  try {
    // NON-BUN: execSync blocks the entire extension host
    // ALSO: String command is injection-vulnerable
    const output = execSync(
      'nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits',
      { encoding: 'utf-8', timeout: 5000 }
    );
    const utilization = parseInt(output.trim(), 10);
    return isNaN(utilization) ? '?' : `${utilization}%`;
  } catch {
    return 'N/A';
  }
}

// Session Status Check - More execSync
function checkSessionStatus_NONBUN(sessionPath: string): 'active' | 'stale' | 'none' {
  // NON-BUN: fs.existsSync is synchronous
  if (!fs.existsSync(sessionPath)) return 'none';
  
  try {
    // NON-BUN: fs.statSync blocks
    const stats = fs.statSync(sessionPath);
    const hourAgo = Date.now() - 60 * 60 * 1000;
    return stats.mtimeMs > hourAgo ? 'active' : 'stale';
  } catch {
    return 'none';
  }
}

// SSOT Hash Check via git
function getSSOTHash_NONBUN(ssotPath: string): string {
  try {
    // NON-BUN: execSync + string interpolation = injection risk
    return execSync(`git hash-object "${ssotPath}"`).toString().trim();
  } catch {
    return 'unknown';
  }
}

// ============================================
// BUN EQUIVALENTS (FOR REFERENCE)
// ============================================

/*
import { $ } from "bun";

// GPU Status - ASYNC (non-blocking)
async function getGpuStatus_BUN(): Promise<string> {
  try {
    // Bun Shell: async, injection-safe template literal
    const output = await $`nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits`
      .timeout(5000)
      .text();
    const utilization = parseInt(output.trim(), 10);
    return isNaN(utilization) ? '?' : `${utilization}%`;
  } catch {
    return 'N/A';
  }
}

// Session Status - ASYNC
async function checkSessionStatus_BUN(sessionPath: string): Promise<'active' | 'stale' | 'none'> {
  const file = Bun.file(sessionPath);
  
  if (!await file.exists()) return 'none';
  
  // Note: Bun.file() doesn't have .stat() directly
  // Use Bun.spawn for stat or fs.promises (which Bun supports)
  try {
    const stats = await Bun.file(sessionPath).stat?.() ?? 
                  await import('fs/promises').then(fs => fs.stat(sessionPath));
    const hourAgo = Date.now() - 60 * 60 * 1000;
    return stats.mtimeMs > hourAgo ? 'active' : 'stale';
  } catch {
    return 'none';
  }
}

// SSOT Hash - Bun Shell (injection-safe)
async function getSSOTHash_BUN(ssotPath: string): Promise<string> {
  try {
    // Template literal is SAFE - Bun escapes the path
    const result = await $`git hash-object ${ssotPath}`.text();
    return result.trim();
  } catch {
    return 'unknown';
  }
}
*/

// ============================================
// MILQUETOAST PATTERN: GENERIC ERRORS
// ============================================

// Prior agent's pattern - NO FA⁵ SEMANTICS
function genericErrorHandling_MILQUETOAST() {
  try {
    // ... operation
  } catch (error) {
    // MILQUETOAST: Just logs error, no classification
    console.error('Error:', error);
  }
}

// ============================================
// SSOT-ALIGNED ERROR HANDLING
// ============================================

/*
// FA⁵ Violation-aware error handling (§2.5.4)
function ssotAlignedErrorHandling() {
  try {
    // ... operation
  } catch (error) {
    const msg = error instanceof Error ? error.message : String(error);
    
    // Classify by FA⁵ violation type
    if (msg.includes('ENOENT')) {
      console.error(`[V5-001] SSOT Desecration: File not found - ${msg}`);
    } else if (msg.includes('EPERM')) {
      console.error(`[V5-005] Tier Violation: Permission denied - ${msg}`);
    } else {
      console.error(`[V5-007] Chromatic Incoherence: ${msg}`);
    }
  }
}
*/

// ============================================
// ORPHANED CODE ISSUE: hedonisticValidation.ts
// ============================================

/**
 * The file hedonisticValidation.ts (200+ lines) was NEVER IMPORTED
 * by the prior agent. It contains:
 * 
 * - PleasureTier system (TRIUMVIRATE_BLISS_SPECTRUM)
 * - Triumvirate color mappings
 * - FA⁵ violation warnings for SSOT integrity
 * - Status bar integration logic
 * 
 * This has been FIXED by adding:
 *   import { activate as activateHedonistic } from './hedonisticValidation';
 * 
 * And calling activateHedonistic(context) in the main activate().
 */
