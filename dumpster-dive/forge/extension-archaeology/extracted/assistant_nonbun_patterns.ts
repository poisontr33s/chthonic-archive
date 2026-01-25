/**
 * EXTRACTED NON-BUN CODE: chthonic-vscode-extension/src/extension.ts
 * 
 * PURPOSE: Research archive for Node.js → Bun conversion
 * STATUS: Extracted 2026-01-24
 * 
 * VIOLATIONS IDENTIFIED:
 * - Line 15: path.join import (NON-BUN)
 * - Line 16: fs/promises.readFile (NON-BUN)
 * - Line 47: await readFile() call (NON-BUN)
 * 
 * ADDITIONAL ISSUES:
 * - $(flame) codicon is INVALID (should be $(flame) but may not render)
 * - Hash validation is TODO stub
 * - Webview HTML is inline string (not componentized)
 */

// ============================================
// EXTRACTED IMPORTS (NON-BUN)
// ============================================

import * as vscode from 'vscode';
import { join } from 'path';                    // NON-BUN: Template literals suffice
import { readFile } from 'fs/promises';         // NON-BUN: Use Bun.file().text()

// ============================================
// EXTRACTED FILE OPERATIONS (NON-BUN)
// ============================================

// SSOT Loading - Prior Agent Pattern
async function loadSSOT_NONBUN(workspaceRoot: string): Promise<string | null> {
  const ssotPath = join(workspaceRoot, '.github', 'copilot-instructions.md');
  
  try {
    // NON-BUN: fs/promises.readFile
    const content = await readFile(ssotPath, 'utf-8');
    return content;
  } catch {
    return null;
  }
}

// ============================================
// BUN EQUIVALENT (FOR REFERENCE)
// ============================================

/*
async function loadSSOT_BUN(workspaceRoot: string): Promise<string | null> {
  const ssotPath = `${workspaceRoot}/.github/copilot-instructions.md`;
  const file = Bun.file(ssotPath);
  
  if (!await file.exists()) return null;
  
  try {
    return await file.text();
  } catch {
    return null;
  }
}
*/

// ============================================
// MILQUETOAST PATTERN: INLINE HTML STRINGS
// ============================================

// Prior agent embedded entire HTML in template literal
function getWebviewContent_MILQUETOAST(): string {
  return `<!DOCTYPE html>
<html>
<head>
  <style>
    /* CYBERPUNK COLORS - FA⁵ VIOLATION */
    body { background: #0d0d12; color: #e0e0e0; }
    .header { color: #00e5ff; }
    /* ... 100+ lines of inline CSS ... */
  </style>
</head>
<body>
  <div class="container">
    <!-- HARDCODED STRUCTURE - NO SSOT INTEGRATION -->
    <h1>Chthonic Assistant</h1>
    <div id="chat"></div>
  </div>
  <script>
    // INLINE JS - NOT BUNDLED, NOT TYPE-CHECKED
    // ... 200+ lines ...
  </script>
</body>
</html>`;
}

// ============================================
// SSOT-ALIGNED PATTERN (CONCEPT)
// ============================================

/*
// Webview should:
// 1. Load CSS from external file (bundled by Bun)
// 2. Use FA⁵ Flesh & Earth palette
// 3. Dynamically render SSOT entity hierarchy
// 4. Type-checked React components (already in webview/index.tsx)

async function getWebviewContent_SSOT(
  webview: vscode.Webview,
  extensionUri: vscode.Uri
): Promise<string> {
  // Load bundled CSS/JS from dist/
  const styleUri = webview.asWebviewUri(
    vscode.Uri.joinPath(extensionUri, 'dist', 'webview.css')
  );
  const scriptUri = webview.asWebviewUri(
    vscode.Uri.joinPath(extensionUri, 'dist', 'webview.js')
  );
  
  // Use Flesh & Earth palette from SSOT (§0.85 DULSS colors)
  return `<!DOCTYPE html>
<html>
<head>
  <link rel="stylesheet" href="${styleUri}">
</head>
<body class="decorator-flesh-earth">
  <div id="root"></div>
  <script src="${scriptUri}"></script>
</body>
</html>`;
}
*/

// ============================================
// STUB PATTERN: TODO COMMENTS
// ============================================

// Prior agent left unimplemented features:

async function validateSSOTHash_STUB(ssotPath: string): Promise<boolean> {
  // TODO: Implement hash validation
  // FA¹ VIOLATION: Perpetual incompleteness
  // This function is registered as a command but DOES NOTHING
  return true;
}

// $(flame) CODICON ISSUE:
// The package.json uses $(flame) but this codicon may not exist
// in VS Code's icon set. Should use $(zap), $(fire), or custom icon.

// ============================================
// HALLUCINATION DETECTION NOTES
// ============================================

/**
 * HALLUCINATIONS FOUND:
 * 
 * 1. Hash validation command exists but handler is TODO stub
 * 2. $(flame) codicon referenced but may not render
 * 3. Chat panel claims MCP integration but connection logic incomplete
 * 4. Copilot LM API usage correct but no fallback for older VS Code
 * 5. getHashFromFile() called but function definition missing
 * 
 * LEGITIMATE CODE:
 * - Webview provider structure is correct
 * - vscode.lm API usage is valid
 * - Activation events are properly defined
 * - React webview bundling via Bun is working
 */

// ============================================
// VSCODE EXTENSION NODE.JS CONSTRAINT
// ============================================

/**
 * CRITICAL INSIGHT FROM RESEARCH:
 * 
 * VS Code extensions run in Node.js context.
 * Bun APIs (Bun.file, Bun.$) are NOT available.
 * 
 * RESOLUTION:
 * - Keep Node.js fs/path for extension runtime code
 * - Use Bun for: build scripts, tests, MCP servers, CLI tools
 * - Create bun-compat.ts polyfill with Bun-like API surface
 * 
 * The "non-Bun" code in extensions is PARTIALLY valid
 * because VS Code mandates Node.js runtime.
 * 
 * However, the STYLE should still align with SSOT:
 * - Async over sync (readFile over readFileSync)
 * - FA⁵ error messages
 * - Proper typing
 */
