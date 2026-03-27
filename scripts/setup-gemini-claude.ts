// @SID: SCRIPT_SETUP_GEMINI_CLAUDE_V1
#!/usr/bin/env bun

// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: setup-gemini-claude.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: ORANGE
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ║ Ogdoad-Ceque Radiance: (standalone)
// ╚════════════════════════════════════════════════════════════════════════════


/**
 * Gemini + Claude Code Setup
 *
 * @SID           TOOL_GEMINI_CLAUDE_SETUP_V1
 * @Shabti        CLI Script
 * @Heka-Ayni     CONCEPT_GEMINI_CLAUDE_BRIDGE
 * @Ankh-Tinku    STATE_GEMINI_CLAUDE_ACTIVE
 * @Purpose       Initialize Gemini API and validate Claude Code IDE
 *                connection. Configures both Gemini Google CLI and
 *                Claude Code IDE for Bun runtime.
 */

import { resolve } from "path";
import { writeFileSync, readFileSync, existsSync } from "fs";

const CHTHONIC_ROOT = process.env.CHTHONIC_ROOT || "C:\\Users\\erdno\\chthonic-archive";
const ENV_FILE = resolve(CHTHONIC_ROOT, ".env.local");
const SETUP_FILE = resolve(CHTHONIC_ROOT, "SETUP_GEMINI_CLAUDE.md");

// ═════════════════════════════════════════════════════════════════════════════
// SECTION 1: Validate Installations
// ═════════════════════════════════════════════════════════════════════════════

async function validateInstallations(): Promise<{ claude: string; gemini: string }> {
  const results = { claude: "", gemini: "" };

  // Check Claude Code
  try {
    const proc = Bun.spawn(["claude", "--version"], {
      stdout: "pipe",
      stderr: "pipe",
    });
    const output = await new Response(proc.stdout).text();
    results.claude = output.trim();
    console.log(`✅ Claude Code: ${results.claude}`);
  } catch (e) {
    console.log("❌ Claude Code not found. Install with: bun install -g @anthropic-ai/claude-code");
    results.claude = "NOT_INSTALLED";
  }

  // Check Gemini SDK
  try {
    await import("@google/generative-ai");
    results.gemini = "installed";
    console.log("✅ Google Generative AI SDK: @google/generative-ai");
  } catch {
    console.log("⚠️ Google Generative AI SDK not found. Installing...");
    const installProc = Bun.spawn(["bun", "install", "-g", "@google/generative-ai"]);
    await installProc.exited;
    results.gemini = "installed";
    console.log("✅ Google Generative AI SDK: installed");
  }

  return results;
}

// ═════════════════════════════════════════════════════════════════════════════
// SECTION 2: Environment Configuration
// ═════════════════════════════════════════════════════════════════════════════

function generateEnvTemplate(): string {
  return `# 🔥💀⚓ CHTHONIC GEMINI + CLAUDE CODE CREDENTIALS
# This file contains sensitive API keys. DO NOT commit to git.
# Add to .gitignore: .env.local

# ═════════════════════════════════════════════════════════════════════════════
# ANTHROPIC (Claude Code)
# ═════════════════════════════════════════════════════════════════════════════
# Get your API key from: https://console.anthropic.com/account/keys
# Required for: Claude Code IDE, API calls
ANTHROPIC_API_KEY=sk_your_key_here

# ═════════════════════════════════════════════════════════════════════════════
# GOOGLE GEMINI
# ═════════════════════════════════════════════════════════════════════════════
# Get your API key from: https://aistudio.google.com/app/apikey
# Required for: Gemini API access, generative tasks
GOOGLE_API_KEY=your_gemini_key_here

# Optional: Google Cloud credentials for advanced features
GOOGLE_APPLICATION_CREDENTIALS=

# ═════════════════════════════════════════════════════════════════════════════
# CLAUDE CODE PREFERENCES
# ═════════════════════════════════════════════════════════════════════════════
# Model: claude-3-5-sonnet-20241022 (default), claude-3-opus-20250219, etc.
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# Permission mode: default, acceptEdits, dontAsk, plan
CLAUDE_PERMISSION_MODE=acceptEdits

# Enable IDE integration
CLAUDE_IDE_ENABLED=true

# ═════════════════════════════════════════════════════════════════════════════
# GEMINI PREFERENCES
# ═════════════════════════════════════════════════════════════════════════════
# Model: gemini-2.0-flash (recommended), gemini-1.5-pro, etc.
GEMINI_MODEL=gemini-2.0-flash

# Safety settings: BLOCK_NONE, BLOCK_ONLY_HIGH, BLOCK_MEDIUM_AND_ABOVE
GEMINI_SAFETY_SETTING=BLOCK_ONLY_HIGH
`;
}

function setupEnvFile(): void {
  if (existsSync(ENV_FILE)) {
    console.log(`ℹ️ ${ENV_FILE} already exists. Skipping creation.`);
    return;
  }

  writeFileSync(ENV_FILE, generateEnvTemplate(), "utf-8");
  console.log(`✅ Created ${ENV_FILE}`);
  console.log("   📝 Please add your API keys to the file!");
}

// ═════════════════════════════════════════════════════════════════════════════
// SECTION 3: Generate Setup Documentation
// ═════════════════════════════════════════════════════════════════════════════

function generateSetupGuide(versions: { claude: string; gemini: string }): string {
  return `# 🔥💀⚓ Gemini + Claude Code IDE Setup Guide

## Installation Status (${new Date().toISOString()})

### ✅ Installed Components
- **Claude Code**: ${versions.claude === "NOT_INSTALLED" ? "❌ NOT INSTALLED" : versions.claude}
- **Google Generative AI SDK**: ${versions.gemini}

## Quick Start

### 1. Add API Keys
Edit \`.env.local\` in the chthonic-archive root:

\`\`\`bash
ANTHROPIC_API_KEY=sk_your_anthropic_key_here
GOOGLE_API_KEY=your_google_api_key_here
\`\`\`

### 2. Get API Keys

#### Anthropic (Claude Code)
1. Go to https://console.anthropic.com/account/keys
2. Create a new API key
3. Copy and paste into ANTHROPIC_API_KEY in .env.local

#### Google Gemini
1. Go to https://aistudio.google.com/app/apikey
2. Create a new API key for your project
3. Copy and paste into GOOGLE_API_KEY in .env.local

### 3. Launch Claude Code IDE

\`\`\`bash
# Interactive mode (recommended for IDE)
claude --ide

# Or with specific project directory
cd C:\\Users\\erdno\\chthonic-archive
claude --ide
\`\`\`

### 4. Using Gemini in Bun Scripts

\`\`\`typescript
import { GoogleGenerativeAI } from "@google/generative-ai";

const client = new GoogleGenerativeAI(process.env.GOOGLE_API_KEY);
const model = client.getGenerativeModel({ model: "gemini-2.0-flash" });

const result = await model.generateContent("Your prompt here");
console.log(result.response.text());
\`\`\`

## Claude Code Commands

### Basic Usage
\`\`\`bash
# Start interactive session
claude

# With specific prompt
claude "Explain how this works" < file.ts

# Continue last session
claude --continue

# Create new code
claude --ide
\`\`\`

### Advanced Options
\`\`\`bash
# With MCP servers
claude --mcp-config .vscode/mcp.json --ide

# With debug logging
claude --debug --ide

# Custom tools
claude --tools "Bash,Edit,Read" --ide

# Specific model
claude --model opus --ide
\`\`\`

## Gemini Integration

### Using in CLI
\`\`\`bash
bun run scripts/gemini-cli.ts "Your prompt here"
\`\`\`

### Using in Node/Bun Code
\`\`\`typescript
import { GoogleGenerativeAI } from "@google/generative-ai";

const genAI = new GoogleGenerativeAI(process.env.GOOGLE_API_KEY);

async function generateWithGemini(prompt: string) {
  const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash" });
  const result = await model.generateContent(prompt);
  return result.response.text();
}
\`\`\`

## Troubleshooting

### Claude Code IDE not connecting
- Ensure you're in an interactive terminal (not --print mode)
- Check that ANTHROPIC_API_KEY is set in environment
- VS Code: Install "Anthropic Claude" extension

### Gemini API errors
- Verify GOOGLE_API_KEY is valid and has correct permissions
- Check API is enabled in Google Cloud Console
- Rate limit? Use exponential backoff

### Permission denied on scripts
\`\`\`bash
chmod +x scripts/setup-gemini-claude.ts
\`\`\`

## Environment Variables

### From .env.local
- \`ANTHROPIC_API_KEY\` - Claude API key
- \`GOOGLE_API_KEY\` - Gemini API key
- \`CLAUDE_MODEL\` - Model to use (default: claude-3-5-sonnet-20241022)
- \`GEMINI_MODEL\` - Model to use (default: gemini-2.0-flash)

### System
- \`CHTHONIC_ROOT\` - Workspace root (${process.env.CHTHONIC_ROOT})
- \`USERPROFILE\` - User home directory

## Next Steps

1. ✅ Install packages (done)
2. ⏳ Add API keys to .env.local
3. ⏳ Test Claude Code: \`claude --ide\`
4. ⏳ Test Gemini: \`bun run scripts/gemini-cli.ts "test"\`
5. ⏳ Configure VS Code integration

## Resources

- [Claude Code Docs](https://github.com/anthropics/claude-code)
- [Gemini API Docs](https://ai.google.dev/)
- [Bun Package Manager](https://bun.sh/)
`;
}

function writeSetupGuide(guide: string): void {
  writeFileSync(SETUP_FILE, guide, "utf-8");
  console.log(`ℹ️ Setup guide written to ${SETUP_FILE}`);
}

// ═════════════════════════════════════════════════════════════════════════════
// MAIN EXECUTION
// ═════════════════════════════════════════════════════════════════════════════

async function main() {
  console.log("\n🔥💀⚓ GEMINI + CLAUDE CODE SETUP\n" + "═".repeat(50));

  const versions = await validateInstallations();
  setupEnvFile();

  const guide = generateSetupGuide(versions);
  writeSetupGuide(guide);

  console.log("\n" + "═".repeat(50));
  console.log("✅ Setup complete!");
  console.log("📖 See SETUP_GEMINI_CLAUDE.md for full instructions");
  console.log("⏳ Next: Add your API keys to .env.local");
  console.log("🚀 Then run: claude --ide\n");
}

main().catch(console.error);
