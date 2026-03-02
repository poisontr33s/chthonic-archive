// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: claude-ide-e2e-check.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: ORANGE
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ║ Ogdoad-Ceque Radiance: (standalone)
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * Claude Code IDE — End-to-End Integration Check
 *
 * @SID           TEST_CLAUDE_IDE_E2E_V1
 * @Shabti        Test Script
 * @Purpose       Validates Claude Code IDE integration via Bun.
 */

import fs from "fs";
import path from "path";
import { execSync } from "child_process";

console.log(
  `\n╔════════════════════════════════════════════════════════════════════════════╗`
);
console.log(
  `║  Claude Code IDE - End-to-End Integration Check (Bun Version)            ║`
);
console.log(
  `╚════════════════════════════════════════════════════════════════════════════╝\n`
);

const checks: Record<string, boolean> = {
  "VS Code Installation": false,
  "VS Code Running": false,
  "Claude Code Extension": false,
  "API Key Valid": false,
  "MCP Bridge Running": false,
};

// ═══════════════════════════════════════════════════════════════════════════
// 1. VS CODE INSTALLATION
// ═══════════════════════════════════════════════════════════════════════════
console.log(
  `📍 Check 1: VS Code Installation\n${"─".repeat(77)}`
);

try {
  // Check PATH for code-insiders or code command
  const binPath = Bun.which("code-insiders") || Bun.which("code");
  if (binPath) {
    console.log(`✅ VS Code found: ${binPath}`);
    checks["VS Code Installation"] = true;
  }
} catch {
  console.log(
    `❌ VS Code not found. Install from: https://code.visualstudio.com`
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// 2. VS CODE RUNNING
// ═══════════════════════════════════════════════════════════════════════════
console.log(
  `\n📍 Check 2: VS Code Running Status\n${"─".repeat(77)}`
);

try {
  const tasklist = execSync("tasklist", { encoding: "utf-8" });
  const isRunning =
    tasklist.includes("Code.exe") ||
    tasklist.includes("Code-Insiders.exe") ||
    tasklist.includes("code");
  if (isRunning) {
    console.log(`✅ VS Code is running`);
    checks["VS Code Running"] = true;
  } else {
    console.log(`❌ VS Code is not running. Start it: code-insiders .`);
  }
} catch {
  console.log(`⚠️  Could not check running processes`);
}

// ═══════════════════════════════════════════════════════════════════════════
// 3. CLAUDE CODE EXTENSION
// ═══════════════════════════════════════════════════════════════════════════
console.log(
  `\n📍 Check 3: Claude Code Extension\n${"─".repeat(77)}`
);

const extPath = path.join(
  process.env.APPDATA || "",
  "Code - Insiders",
  "User",
  "extensions"
);

if (fs.existsSync(extPath)) {
  try {
    const exts = fs.readdirSync(extPath);
    const claudeExt = exts.find(
      (e) => e.includes("anthropic") || e.includes("claude")
    );
    if (claudeExt) {
      console.log(`✅ Claude Code extension found: ${claudeExt}`);
      checks["Claude Code Extension"] = true;
    } else {
      console.log(`⚠️  Extension not found. Install: @anthropic-ai/claude-code`);
    }
  } catch {
    console.log(`⚠️  Could not read extensions directory`);
  }
} else {
  console.log(`⚠️  Extensions directory not found`);
}

// ═══════════════════════════════════════════════════════════════════════════
// 4. API KEY VALIDATION
// ═══════════════════════════════════════════════════════════════════════════
console.log(
  `\n📍 Check 4: API Key Configuration\n${"─".repeat(77)}`
);

let apiKey = process.env.ANTHROPIC_API_KEY;
if (!apiKey) {
  const envPath = path.join(process.cwd(), ".env.local");
  if (fs.existsSync(envPath)) {
    const envContent = fs.readFileSync(envPath, "utf-8");
    const match = envContent.match(/ANTHROPIC_API_KEY=(.+)/);
    if (match) {
      apiKey = match[1].trim();
    }
  }
}

if (apiKey && !apiKey.includes("sk_your") && !apiKey.includes("placeholder")) {
  console.log(`✅ Valid API key detected`);
  console.log(`   Key: ${apiKey.substring(0, 10)}...`);
  checks["API Key Valid"] = true;
} else {
  console.log(
    `❌ API key is missing or invalid (currently: ${apiKey || "MISSING"})`
  );
  console.log(`\n🔧 FIX:`);
  console.log(`   1. Get API key: https://console.anthropic.com/account/keys`);
  console.log(
    `   2. Edit .env.local and set: ANTHROPIC_API_KEY=sk_your_actual_key`
  );
  console.log(`   3. Save the file`);
  console.log(`   4. Reload VS Code (Ctrl+Shift+P → Reload Window)`);
}

// ═══════════════════════════════════════════════════════════════════════════
// 5. MCP BRIDGE STATUS
// ═══════════════════════════════════════════════════════════════════════════
console.log(
  `\n📍 Check 5: MCP Bridge Server\n${"─".repeat(77)}`
);

try {
  const response = await fetch("http://localhost:8888/status", {
    timeout: 2000,
  });
  if (response.ok) {
    const status = await response.text();
    console.log(`✅ MCP Bridge running on port 8888`);
    console.log(`   Status: ${status}`);
    checks["MCP Bridge Running"] = true;
  }
} catch {
  console.log(`⚠️  MCP Bridge not running`);
  console.log(`→ Start it: bun run scripts/bridge-server.ts`);
}

// ═══════════════════════════════════════════════════════════════════════════
// 6. SUMMARY
// ═══════════════════════════════════════════════════════════════════════════
console.log(
  `\n╔════════════════════════════════════════════════════════════════════════════╗`
);
console.log(
  `║  Integration Status Summary                                              ║`
);
console.log(
  `╚════════════════════════════════════════════════════════════════════════════╝\n`
);

let passCount = 0;
for (const [check, passed] of Object.entries(checks)) {
  const symbol = passed ? "✅" : "❌";
  console.log(`${symbol} ${check}`);
  if (passed) passCount++;
}

const totalCount = Object.keys(checks).length;
console.log(`\nStatus: ${passCount}/${totalCount} checks passed\n`);

if (checks["API Key Valid"]) {
  console.log(`🚀 READY TO LAUNCH:\n   chthonic claude-ide\nor:\n   claude --ide\n`);
} else {
  console.log(`⚠️  ACTION REQUIRED:\n`);
  console.log(`   1. Add valid ANTHROPIC_API_KEY to .env.local`);
  console.log(`   2. Save the file`);
  console.log(`   3. Reload VS Code (Ctrl+Shift+P → Reload Window)`);
  console.log(`   4. Run this check again\n`);
}

process.exit(passCount === totalCount ? 0 : 1);
