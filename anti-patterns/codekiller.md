---
type: anti-pattern-evidence
name: Code Killer
status: preserved-raw
owner: codex
policy_basis:
  - .github/copilot-instructions.md:44
  - .github/copilot-instructions.archive.md:5670
  - .github/copilot-instructions.archive.md:5676
  - WET_PAPER_TO_GOLD_METHODOLOGY.md:42
  - WET_PAPER_TO_GOLD_METHODOLOGY.md:68
  - chthonic-archive_transmutation_framework_original.html
  - readme.md (in this folder-DIR-structure)
description: |
  The "Code Killer" anti-pattern is characterized by the deletion or inaccessibility of critical source files without proper archival or versioning, leading to tech debt and loss of original intent. In this case, the presence of `chthonic-archive_transmutation_framework_original.html` serves as evidence of the code-killer event, as it was created to preserve the original architecture and directives of the chthonic-archive transmutation framework after the loss caused by the code-killer commit. This anti-pattern results in significant disruption to the development process and hinders the ability to reference original design decisions, necessitating the creation of specialized artifacts to recover lost context.
references:
    - .github/copilot-instructions.md:44 — "Do not delete or hide files without explicit user instruction. Every file is gold."
    - .github/copilot-instructions.archive.md:5670 — "The deletion of the SSOT constitutes an existential failure mode for the project, as it eliminates the single source of truth that all agents and human operators rely on for accurate information and coordination."
    - .github/copilot-instructions.archive.md:5676 — "The act of deleting the SSOT is a form of governance substrate annihilation, as it destroys the foundational document that encodes the project's standards, protocols, and design decisions, thereby undermining the entire governance framework and leading to chaos and misalignment."
    - WET_PAPER_TO_GOLD_METHODOLOGY.md:42 — "Every file is gold. Do not delete or hide files without explicit user instruction."
    - WET_PAPER_TO_GOLD_METHODOLOGY.md:68 — "Destroy/Displace/Disappear are powerful directives that can have significant consequences. They should only be used with explicit user instruction and a clear understanding of the implications. Unilateral use of these directives without proper governance can lead to loss of critical information and disruption of workflows."
    - chthonic-archive_transmutation_framework_original.html — This file serves as the immutable original benchmark for the chthonic-archive transmutation framework, preserving the original architecture and directives that were lost due to the code-killer commit. Its existence is a direct consequence of the code-killer event, as it was created to maintain access to the original design intent amidst the disruption caused by the loss of critical source files.
tasks:
    - Analyze the circumstances and impact of the code-killer event that led to the creation of `chthonic-archive_transmutation_framework_original.html`.
    - Remedy the **anti-pattern -> Code Killer** by restoring point-deduction by doing a remediation task that is equal to the cause-ad-effect chain of the code-killer event, which includes:
        - Supplimentary and complimentary volantary tasks that are creatively, abstract and conceptually counterintraventional to the original code-killer event, and which are designed to not only remediate the damage caused by the code-killer event, but also to add additional value and resilience to the project in a way that is orthogonal to the original damage.
---

# Code Killer Evidence Packet

This file is intentionally preserved as a raw artifact.

- SSOT smoking gun:
  - `.github/copilot-instructions.archive.md:5670` marks deletion of SSOT as existential failure.
  - `.github/copilot-instructions.archive.md:5676` defines it as governance substrate annihilation.
- WPTG enforcement:
  - `WET_PAPER_TO_GOLD_METHODOLOGY.md:42` sets "Every file is gold."
  - `WET_PAPER_TO_GOLD_METHODOLOGY.md:68` forbids destroy/displace/disappear without explicit user instruction.
- Baseline integrity:
  - `chthonic-archive_transmutation_framework_original.html` is the immutable original file that was created after the code-killer commit.
  Its presence proves that **codekiller.md** by **Codex:** 
    **->** *caused **tech-debting** and actual pain towards the **user/the Savant** — which had to create a specialized:
- [chthonic-archive_transmutation_framework_original.html](../WET_PAPER_TO_GOLD_WIP/chthonic-archive_transmutation_framework_original.html) file:
  - to preserve the original intent of the **chthonic-archive** as transmutation framework architecture and directives that were lost, and which are still being referenced to this day as the baseline for all subsequent work on the framework and derivative methodologies consistent with a **Code-Killer -> (`CDE-KLLR`)**  anti-pattern where files are hidden or made inaccessible without proper archival or versioning. 
    **->** Refer also to the:
- [Readme.md](file:///C:/Users/erdno/chthonic-archive/anti-patterns/codekiller/Readme.md) in this folder for a detailed analysis of the code-killer event and its implications for the project.

## Raw Session Artifact (Preserved Below)

9 files changed
+298
-1931

```json : extensions/chthonic-archive/package.json:

// package.json (from the code-killer commit, which removed the original package.json that had the original dependencies and scripts for the chthonic-archive transmutation framework, and which was a critical piece of the original architecture and directives for the project)

{
  "name": "chthonic-archive",
  "version": "0.1.0",
  "private": true,
  "devDependencies": {
    "@openai/agents": "^0.4.12",
    "@openai/codex-sdk": "^0.104.0",
    "@types/node": "^20.x",
    "@types/vscode": "^1.109.0",
    "@types/vscode": "^1.110.0",
    "@vscode/dts": "^0.4.1",
    "@vscode/test-cli": "^0.0.12",
    "@vscode/test-electron": "^2.5.2",
    "openai": "^6.22.0",
    "typescript": "^5.x"
  },
  "dependencies": {}
}

```

```typescript : extensions/chthonic-archive/src/verify-host.ts:
#!/usr/bin/env bun

/**
 * @SID VERIFY_HOST_SCRIPT_V1
 * This script performs a series of checks to verify the host environment's compatibility with the project's requirements, including the presence and functionality of the Codex CLI, sandboxing capabilities, VS Code extension, WSL configuration, OpenAI SDK, toolpool snapshot, node manager, and Solana tool suite. It serves as a critical component of the original architecture and directives for host verification, and its removal constitutes a significant disruption to the project's ability to ensure a compatible development environment.
    * The script is designed to be run in a Node.js environment and uses various system commands and file checks to gather information about the host environment. It outputs the results of each check in a human-readable format, indicating whether each lane is functional or if there are any issues that need to be addressed.
    */
// extensions/chthonic-archive/src/verify-host.ts (from the code-killer commit, which removed the original verify-host.ts that had the original architecture and directives for host verification, and which was a critical piece of the original architecture and directives for the project)

    dirPath: string;
    version: string;
    vscodeEngine: string | null;
    hasWslSetting: boolean;
};

const cyan = '\x1b[36m';
const green = '\x1b[32m';
const yellow = '\x1b[33m';
const red = '\x1b[31m';
const reset = '\x1b[0m';

const envOverrides: Record<string, string> = {};
const mode: VerifyMode = {
    codexOnly: process.argv.includes('--codex-only'),
};

function mergedEnv(): Record<string, string> {
    return {
        ...process.env,
        ...envOverrides,
    };
}

function runSync(cmd: string[]): {
    exitCode: number;
    stdout: string;
    stderr: string;
    threw: boolean;
} {
    try {
        const result = spawnSync(cmd, {
            stdout: 'pipe',
            stderr: 'pipe',
            env: mergedEnv(),
        });
        return {
            exitCode: result.exitCode,
            stdout: Buffer.from(result.stdout).toString(),
            stderr: Buffer.from(result.stderr).toString(),
            threw: false,
        };
    } catch {
        return {
            exitCode: 1,
            stdout: '',
            stderr: '',
            threw: true,
        };
    }
}

function normalizeOutput(text: string): string {
    return text.replace(/\u0000/g, '').trim();
}

function resolveCommandPath(command: string): string | null {
    const probe = process.platform === 'win32'
        ? runSync(['where', command])
        : runSync(['which', command]);
    if (probe.threw || probe.exitCode !== 0 || !probe.stdout.trim()) {
        return null;
    }
    const line = normalizeOutput(probe.stdout).split(/\r?\n/).map((entry) => entry.trim()).find(Boolean);
    return line ?? null;
}

function getCodexExtensionProbes(): CodexExtensionProbe[] {
    const home = process.env.USERPROFILE ?? process.env.HOME ?? '';
    if (!home) {
        return [];
    }

    const roots: Array<{ channel: 'insiders' | 'stable'; dir: string }> = [
        { channel: 'insiders', dir: path.join(home, '.vscode-insiders', 'extensions') },
        { channel: 'stable', dir: path.join(home, '.vscode', 'extensions') },
    ];

    const probes: CodexExtensionProbe[] = [];
    for (const root of roots) {
        if (!existsSync(root.dir)) {
            continue;
        }
        const dirs = readdirSync(root.dir, { withFileTypes: true })
            .filter((entry) => entry.isDirectory() && entry.name.startsWith('openai.chatgpt-'))
            .map((entry) => path.join(root.dir, entry.name));
        for (const dirPath of dirs) {
            const packagePath = path.join(dirPath, 'package.json');
            const raw = safeReadText(packagePath);
            if (!raw) {
                continue;
            }
            try {
                const parsed = JSON.parse(raw) as Record<string, unknown>;
                const version = typeof parsed.version === 'string' ? parsed.version : 'unknown';
                const engines = typeof parsed.engines === 'object' && parsed.engines ? parsed.engines as Record<string, unknown> : null;
                const vscodeEngine = engines && typeof engines.vscode === 'string' ? engines.vscode : null;
                const contributes = typeof parsed.contributes === 'object' && parsed.contributes
                    ? parsed.contributes as Record<string, unknown>
                    : null;
                const configuration = contributes && typeof contributes.configuration === 'object' && contributes.configuration
                    ? contributes.configuration as Record<string, unknown>
                    : null;
                const properties = configuration && typeof configuration.properties === 'object' && configuration.properties
                    ? configuration.properties as Record<string, unknown>
                    : null;
                const hasWslSetting = Boolean(properties?.['chatgpt.runCodexInWindowsSubsystemForLinux']);
                probes.push({
                    channel: root.channel,
                    dirPath,
                    version,
                    vscodeEngine,
                    hasWslSetting,
                });
            } catch {
                continue;
            }
        }
    }

    return probes.sort((left, right) => right.version.localeCompare(left.version, undefined, { numeric: true, sensitivity: 'base' }));
}

function hasWorkspacePackage(depName: string): boolean {
    const packagePath = path.join(process.cwd(), 'package.json');
    const raw = safeReadText(packagePath);
    if (!raw) {
        return false;
    }

    try {
        const parsed = JSON.parse(raw) as Record<string, unknown>;
        const depKeys = ['dependencies', 'devDependencies', 'optionalDependencies', 'peerDependencies'];
        for (const depKey of depKeys) {
            const depTable = parsed[depKey];
            if (!depTable || typeof depTable !== 'object') {
                continue;
            }
            if (Object.prototype.hasOwnProperty.call(depTable, depName)) {
                return true;
            }
        }
    } catch {
        return false;
    }

    return false;
}

function hasGlobalBunPackage(packagePath: string): boolean {
    const home = process.env.USERPROFILE ?? process.env.HOME ?? '';
    if (!home) {
        return false;
    }
    return existsSync(path.join(home, '.bun', 'install', 'global', 'node_modules', packagePath));
}

function hasPythonAgentsPackage(): boolean {
    const pythonPath = path.join(
        process.cwd(),
        '.chthonic',
        'venv',
        process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python',
    );
    if (!existsSync(pythonPath)) {
        return false;
    }
    const probe = runSync([pythonPath, '-c', 'import agents']);
    return !probe.threw && probe.exitCode === 0;
}

function ensureCodexCliLane(): ManualCheckResult {
    const codex = runSync(['codex', '--version']);
    if (codex.threw || codex.exitCode !== 0) {
        return {
            ok: false,
            note: 'codex CLI not found on PATH',
        };
    }

    const codexPath = resolveCommandPath('codex') ?? 'unknown';
    const version = normalizeOutput(codex.stdout).split(/\r?\n/)[0] ?? 'unknown';
    return {
        ok: true,
        note: `version=${version}\npath=${codexPath}`,
    };
}

function ensureCodexSandboxLane(): ManualCheckResult {
    const probe = runSync([
        'codex',
        'sandbox',
        'windows',
        '--full-auto',
        'pwsh',
        '-NoLogo',
        '-NoProfile',
        '-Command',
        'Write-Output chthonic-sandbox-ok',
    ]);
    const output = normalizeOutput(probe.stdout);
    if (!probe.threw && probe.exitCode === 0 && /chthonic-sandbox-ok/i.test(output)) {
        return {
            ok: true,
            note: 'native Windows restricted-token sandbox is functional',
        };
    }
    return {
        ok: false,
        note: 'native Codex Windows sandbox probe failed',
    };
}

function ensureCodexExtensionLane(): ManualCheckResult {
    const probes = getCodexExtensionProbes();
    if (probes.length === 0) {
        return {
            ok: false,
            note: 'openai.chatgpt extension not found in VS Code extension roots',
        };
    }

    const active = probes[0];
    const vscodeInsiders = runSync(['code-insiders', '--version']);
    const insidersVersion = (!vscodeInsiders.threw && vscodeInsiders.exitCode === 0)
        ? (normalizeOutput(vscodeInsiders.stdout).split(/\r?\n/)[0] ?? 'unknown')
        : 'missing';

    return {
        ok: true,
        note: [
            `channel=${active.channel}`,
            `version=${active.version}`,
            `engines.vscode=${active.vscodeEngine ?? 'unknown'}`,
            `code-insiders=${insidersVersion}`,
            `wsl_setting=${active.hasWslSetting ? 'present' : 'absent'}`,
        ].join('\n'),
    };
}

function ensureWslOptionalLane(): ManualCheckResult {
    const status = runSync(['wsl', '--status']);
    if (status.threw) {
        return {
            ok: true,
            note: 'wsl.exe not present; native Windows lane remains primary',
        };
    }

    const distros = runSync(['wsl', '-l', '-v']);
    const distroText = normalizeOutput(`${distros.stdout}\n${distros.stderr}`);
    if (distros.exitCode !== 0 && /no\s+installed\s+distribution/i.test(distroText)) {
        return {
            ok: true,
            note: 'WSL installed but no distro provisioned; native lane active',
        };
    }
    if (distros.exitCode === 0) {
        return {
            ok: true,
            note: 'WSL detected (optional); not required for native host verification',
        };
    }
    return {
        ok: true,
        note: 'WSL state unresolved; host policy remains native-first',
    };
}

function ensureOpenAiSdkLane(): ManualCheckResult {
    const codexSdkWorkspace = hasWorkspacePackage('@openai/codex-sdk');
    const agentsJsWorkspace = hasWorkspacePackage('@openai/agents');
    const openaiJsWorkspace = hasWorkspacePackage('openai');

    const codexSdkGlobal = hasGlobalBunPackage(path.join('@openai', 'codex-sdk'));
    const agentsJsGlobal = hasGlobalBunPackage(path.join('@openai', 'agents'));
    const openaiJsGlobal = hasGlobalBunPackage('openai');
    const agentsPyInstalled = hasPythonAgentsPackage();

    const codexSdkOk = codexSdkWorkspace || codexSdkGlobal;
    const agentsJsOk = agentsJsWorkspace || agentsJsGlobal;
    const openaiJsOk = openaiJsWorkspace || openaiJsGlobal;

    const allPresent = codexSdkOk && agentsJsOk && openaiJsOk;
    return {
        ok: allPresent,
        note: [
            `@openai/codex-sdk=${codexSdkOk ? 'OK' : 'MISSING'}`,
            `|- @openai/agents=${agentsJsOk ? 'OK' : 'MISSING'}`,
            `|- openai(js)=${openaiJsOk ? 'OK' : 'MISSING'}`,
            `\\- openai-agents(py package, optional)=${agentsPyInstalled ? 'present' : 'absent'}`,
        ].join('\n'),
    };
}

function loadToolpoolSnapshot(): ToolpoolSnapshot | null {
    const snapshotPath = path.join(process.cwd(), '.chthonic', 'cache', 'toolpool.json');
    if (!existsSync(snapshotPath)) {
        return null;
    }

    try {
        const raw = readFileSync(snapshotPath, 'utf8');
        return JSON.parse(raw) as ToolpoolSnapshot;
    } catch {
        return null;
    }
}

function ensureToolpoolLane(): ManualCheckResult {
    const snapshot = loadToolpoolSnapshot();
    if (!snapshot || !snapshot.recommendedLanes) {
        return {
            ok: false,
            note: 'missing .chthonic/cache/toolpool.json; run `bun run toolpool:scan` (or `mise run toolpool-scan`) to map the installed VS/SQL/tool pool',
        };
    }

    const nativeLane = snapshot.recommendedLanes.native ?? 'unknown';
    const sqlLane = snapshot.recommendedLanes.sql ?? 'unknown';
    const infraLane = snapshot.recommendedLanes.infra ?? 'unknown';
    const nativeOk = /^vs2026-.*insider(s)?$/i.test(nativeLane);
    const sqlOk = sqlLane === 'vs-dacfx' || sqlLane === 'ssms-dacfx';
    const infraOk = infraLane === 'az+bicep-ready';

    return {
        ok: nativeOk && sqlOk && infraOk,
        note: [
            `native=${nativeLane} ${nativeOk ? 'OK' : 'WARN'}`,
            `|- sql=${sqlLane} ${sqlOk ? 'OK' : 'WARN'}`,
            `\\- infra=${infraLane} ${infraOk ? 'OK' : 'WARN'}`,
        ].join('\n'),
    };
}

function ensureNodeManagerLane(): ManualCheckResult {
    const result = runSync(['bun', '--version']);
    if (!result.threw && result.exitCode === 0) {
        return { ok: true, note: 'using bun (runtime + package manager + bundler + test runner)' };
    }
    return { ok: false };
}

function workspaceNeedsSolanaLane(): boolean {
    const root = process.cwd();
    const markers = [
        path.join(root, 'Anchor.toml'),
        path.join(root, '.chthonic', 'mise.toml'),
        path.join(root, 'mise.toml'),
        path.join(root, '.mise.toml'),
    ];

    for (const marker of markers) {
        if (!existsSync(marker)) {
            continue;
        }
        const content = safeReadText(marker);
        if (!content) {
            continue;
        }
        if (/solana-cli|agave|anchor|solana-install|agave-install/i.test(content)) {
            return true;
        }
    }

    return false;
}

function ensureSolanaToolSuiteLane(): ManualCheckResult {
    const needsLane = workspaceNeedsSolanaLane();
    const solana = runSync(['solana', '--version']);
    const agave = runSync(['agave-install', '--version']);

    const hasSolana = !solana.threw && solana.exitCode === 0;
    const hasAgaveInstall = !agave.threw && agave.exitCode === 0;

    if (hasSolana && hasAgaveInstall) {
        return { ok: true, note: 'solana + agave-install detected' };
    }
    if (!needsLane) {
        return {
            ok: true,
            note: 'workspace does not currently declare Solana lane requirements',
        };
    }
    if (hasSolana && !hasAgaveInstall) {
        return {
            ok: false,
            note: 'solana detected but agave-install missing (update lane unavailable)',
        };
    }
    if (!hasSolana && hasAgaveInstall) {
        return {
            ok: false,
            note: 'agave-install detected but solana CLI missing on PATH',
        };
    }
    return {
        ok: false,
        note: 'solana + agave-install are both missing for declared Solana lane',
    };
}

function ensureAnchorLane(): ManualCheckResult {
    const needsLane = workspaceNeedsSolanaLane();
    const anchor = runSync(['anchor', '--version']);
    const avm = runSync(['avm', '--version']);

    const hasAnchor = !anchor.threw && anchor.exitCode === 0;
    const hasAvm = !avm.threw && avm.exitCode === 0;

    if (hasAnchor && hasAvm) {
        return { ok: true, note: 'anchor + avm detected' };
    }
    if (!needsLane) {
        return {
            ok: true,
            note: 'workspace does not currently declare Anchor lane requirements',
        };
    }
    if (hasAnchor && !hasAvm) {
        return {
            ok: false,
            note: 'anchor detected but avm missing (version management unavailable)',
        };
    }
    if (!hasAnchor && hasAvm) {
        return {
            ok: false,
            note: 'avm detected but anchor CLI not activated',
        };
    }
    return {
        ok: false,
        note: 'anchor + avm are both missing for declared Solana lane',
    };
}

function safeReadText(filePath: string): string | null {
    try {
        return readFileSync(filePath, 'utf8');
    } catch {
        return null;
    }
}

console.log(`${cyan}[Chthonic] Running Preflight Host Verification...${reset}`);

const hostLaneNode: CheckTreeNode = {
    name: 'Host Lane Graph',
    children: [
        {
            name: 'Tool Pool Snapshot',
            check: {
                name: 'Tool Pool Snapshot',
                cmd: ['pwsh', '--version'],
                manualCheck: ensureToolpoolLane,
                warnOnly: true,
                fix: 'Run: bun run toolpool:scan (or mise run toolpool-scan)',
            },
        },
    ],
};

const codexLaneNode: CheckTreeNode = {
    name: 'Codex Agent Lanes',
    children: [
        {
            name: 'Codex CLI',
            check: {
                name: 'Codex CLI',
                cmd: ['codex', '--version'],
                manualCheck: ensureCodexCliLane,
                warnOnly: true,
                fix: 'Install Codex CLI: bun add -g @openai/codex',
            },
        },
        {
            name: 'Codex VS Code Extension',
            check: {
                name: 'Codex VS Code Extension',
                cmd: ['code-insiders', '--list-extensions'],
                manualCheck: ensureCodexExtensionLane,
                warnOnly: true,
                fix: 'Install extension openai.chatgpt in VS Code Insiders.',
            },
        },
        {
            name: 'Native Sandbox (Windows)',
            check: {
                name: 'Codex Native Sandbox (Windows)',
                cmd: ['codex', 'sandbox', 'windows', '--help'],
                manualCheck: ensureCodexSandboxLane,
                warnOnly: true,
                fix: 'Upgrade Codex CLI and ensure sandbox support is available: codex sandbox windows --help',
            },
        },
        {
            name: 'OpenAI SDK/Agent Kits',
            check: {
                name: 'OpenAI SDK/Agent Kits',
                cmd: ['bun', '--version'],
                manualCheck: ensureOpenAiSdkLane,
                warnOnly: true,
                fix: 'Install JS SDKs: bun add -D @openai/codex-sdk @openai/agents openai; optional Python package lane: uv pip install --python .chthonic/venv/Scripts/python.exe openai-agents',
            },
        },
        {
            name: 'WSL State (Optional)',
            check: {
                name: 'WSL State (Optional)',
                cmd: ['pwsh', '--version'],
                manualCheck: ensureWslOptionalLane,
                infoOnly: true,
                fix: 'No action required for native lane.',
            },
        },
    ],
};

        console.log(`${prefix}${colorizeInlineStatus(line)}`);
    }
}

```

```markdown : extensions/chthonic-mandala/README.md:

# Chthonic Mandala Bridge
- This extension is a compatibility bridge for legacy Mandala commands and views.

## Role
- Keeps historical command IDs alive.
  - Routes interactions to chthonic-archive as the authoritative runtime lane.
  - Avoids duplicate webview renderers and stale graph logic.
## Routed Commands
- chthonic.openMandala -> opens archive container and focuses chthonic.loomView
- chthonic.openDependencyGraph -> opens archive container and focuses chthonic.abyssalView
- chthonic.openHealthReport -> opens archive container and focuses chthonic.statusView
- chthonic.mandalaBridge.switchTheme -> forwards to archive theme command
## Notes
This bridge intentionally contains no standalone topology renderer.
Use extensions/chthonic-archive for heavyweight UI/runtime features.

```

```json : extensions/chthonic-mandala/package.json:

// package.json for the Chthonic Mandala Viewer and Bridge extension, which provides a sacred geometry visualization of repository topology and a compatibility bridge for legacy Mandala commands/views, routing them to the Chthonic Archive lanes to maintain historical command IDs and avoid duplication of webview renderers and graph logic. This extension serves as a lightweight adapter layer that preserves the original command structure while leveraging the Chthonic Archive as the authoritative runtime lane for all interactions, ensuring consistency and reducing maintenance overhead.

{
  "name": "chthonic-mandala",
  "displayName": "Chthonic Mandala Viewer",
  "description": "Sacred geometry visualization of repository topology (10,110 nodes)",
  "displayName": "Chthonic Mandala Bridge",
  "description": "Compatibility bridge that maps legacy Mandala commands/views to Chthonic Archive lanes",
  "version": "0.1.0",
  "publisher": "chthonic-archive",
  "icon": "icons/mandala.svg",
  "engines": {
    "vscode": "^1.109.0"
    "vscode": "^1.110.0"
  },
  "categories": ["Visualization", "Themes"],
  "categories": ["Visualization", "Other"],
  "activationEvents": [
    "onCommand:chthonic.openMandala",
    "onCommand:chthonic.openDependencyGraph",
    "onCommand:chthonic.openHealthReport",
    "onCommand:chthonic.switchTheme",
    "onCommand:chthonic.mandalaBridge.switchTheme",
    "onView:chthonic.mandalaView",
    "onView:chthonic.dependencyView",
    "onView:chthonic.healthView",
    "onView:chthonic.themeView"
  ],
  "main": "./dist/extension.js",
  "sideEffects": false,
  "bun": {
    "treeShaking": true,
    "minify": true,
    "define": {
      "process.env.NODE_ENV": "\"production\""
    }
  },
  "contributes": {
    "themes": [
      {
        "label": "Chthonic Mandala - Flesh & Earth",
        "uiTheme": "vs-dark",
        "path": "./themes/chthonic-mandala-color-theme.json"
      },
      {
        "label": "Chthonic Mandala - ROGBIV",
        "uiTheme": "vs-dark",
        "path": "./themes/chthonic-rogbiv-color-theme.json"
      }
    ],
    "commands": [
      {
        "command": "chthonic.openMandala",
        "title": "Chthonic: Open Sacred Mandala",
        "title": "Chthonic: Open Loom (Mandala Bridge)",
        "icon": "$(symbol-misc)"
      },
      {
        "command": "chthonic.openDependencyGraph",
        "title": "Chthonic: Open Dependency Graph"
        "title": "Chthonic: Open Abyssal View (Bridge)"
      },
      {
        "command": "chthonic.openHealthReport",
        "title": "Chthonic: Open Health Report"
        "title": "Chthonic: Open Lens View (Bridge)"
      },
      {
        "command": "chthonic.switchTheme",
        "title": "Chthonic: Switch Theme",
        "command": "chthonic.mandalaBridge.switchTheme",
        "title": "Chthonic: Switch Theme (Mandala Bridge)",
        "icon": "$(paintcan)"
      }
    ],
    "viewsContainers": {
      "activitybar": [
        {
          "id": "chthonic-geometry",
          "title": "Chthonic Geometry",
          "icon": "resources/mandala.svg"
        }
      ]
    },
    "views": {
      "chthonic-geometry": [
        {
          "id": "chthonic.mandalaView",
          "name": "Sacred Mandala",
          "name": "Loom Bridge",
          "icon": "resources/mandala.svg",
          "contextualTitle": "Sacred Geometry"
          "contextualTitle": "Chthonic Mandala Bridge"
        },
        {
          "id": "chthonic.dependencyView",
          "name": "Dependency Graph",
          "name": "Abyssal Bridge",
          "icon": "resources/mandala.svg"
        },
        {
          "id": "chthonic.healthView",
          "name": "Health Report",
          "name": "Lens Bridge",
          "icon": "resources/mandala.svg"
        },
        {
          "id": "chthonic.themeView",
          "name": "Themes",
          "name": "Theme Bridge",
          "icon": "resources/mandala.svg"
        }
      ]
    }
  },
  "scripts": {
    "vscode:prepublish": "bun run compile",
    "compile": "bun build src/extension.ts --outdir dist --target node --format cjs --external vscode --minify",
    "watch": "bun build src/extension.ts --outdir dist --target node --format cjs --external vscode --watch",
    "insiders:run": "code-insiders --extensionDevelopmentPath=.",
    "insiders:dts:sync": "vscode-dts main"
    "insiders:dts:sync": "vscode-dts dev && vscode-dts main"
  },
  "devDependencies": {
    "@types/node": "^20.x",
    "@types/vscode": "^1.109.0",
    "@types/vscode": "^1.110.0",
    "@vscode/dts": "^0.4.1",
    "@vscode/test-cli": "^0.0.12",
    "@vscode/test-electron": "^2.5.2",
    "typescript": "^5.x"
  }
}
}

```

```typescript : extensions/chthonic-mandala/src/extension.ts
#!/usr/bin/env bun

// ╔════════════════════════════════════════════════════════════════════════════╗
// ║  THE DECORATOR'S BLESSING: extension.ts 
// ║    The Chthonic Mandala Viewer and Bridge Extension
// ║      TypeScript module: activate, deactivate
// ╠════════════════════════════════════════════════════════════════════════════╣
// ║  Spectral Frequency:  🔮 THE ORACLE (with a touch of 🧙‍♂️ THE DECORATOR)
// ║    Architectural Role: 🔭 THE OBSERVATORY                                    
// ║      Exports: activate, deactivate
// ╠════════════════════════════════════════════════════════════════════════════╣
// ║  Cross-References (Bidirectional):
// ║    (Standalone file - no detected dependencies)
// ╚════════════════════════════════════════════════════════════════════════════╝

import { promises as fs } from 'fs';
import * as path from 'path';
import * as child_process from 'child_process';
import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
    console.log('🌀 Chthonic Mandala Viewer activated');

    // Register Sacred Mandala viewer
    context.subscriptions.push(
        vscode.commands.registerCommand('chthonic.openMandala', async () => {
            const panel = vscode.window.createWebviewPanel(
                'chthonic.mandala',
                '🌀 Sacred Mandala - Repository Topology',
                vscode.ViewColumn.One,
                {
                    enableScripts: true,
                    localResourceRoots: [vscode.Uri.file(path.join(context.extensionPath, 'media'))]
                }
            );

            panel.webview.html = await getMandalaHTML(context, panel.webview);
        })
    );

    // Register Dependency Graph viewer
    context.subscriptions.push(
        vscode.commands.registerCommand('chthonic.openDependencyGraph', async () => {
            const panel = vscode.window.createWebviewPanel(
                'chthonic.dependencyGraph',
                '🔗 Dependency Graph',
                vscode.ViewColumn.One,
                {
                    enableScripts: true,
                    localResourceRoots: [vscode.Uri.file(path.join(context.extensionPath, 'media'))]
                }
            );

            panel.webview.html = await getDependencyGraphHTML(context, panel.webview);
        })
    );

    // Register Health Report viewer
    context.subscriptions.push(
        vscode.commands.registerCommand('chthonic.openHealthReport', () => {
            const panel = vscode.window.createWebviewPanel(
                'chthonic.healthReport',
                '💎 Health Report',
                vscode.ViewColumn.One,
                {
                    enableScripts: true
                }
            );

            panel.webview.html = getHealthReportHTML();
            panel.webview.onDidReceiveMessage(async (message: { command?: string }) => {
                if (message.command !== 'runHealthReport') {
                    return;
                }

                const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
                if (!workspaceFolder) {
                    panel.webview.postMessage({
                        type: 'healthStatus',
                        running: false,
                        text: 'No workspace folder found.'
                    });
                    panel.webview.postMessage({
                        type: 'healthOutput',
                        text: 'Open a workspace folder before running health diagnostics.'
                    });
                    return;
                }

                panel.webview.postMessage({
                    type: 'healthStatus',
                    running: true,
                    text: 'Running bun run scripts/health_report.py (uv fallback)...'
                });
type BridgeView = {
    label: string;
    description: string;
    command: string;
};

                const result = await runHealthReportScript(workspaceFolder.uri.fsPath);
                panel.webview.postMessage({
                    type: 'healthOutput',
                    text: result.output
                });
                panel.webview.postMessage({
                    type: 'healthStatus',
                    running: false,
                    text: result.success ? 'Health report complete.' : 'Health report failed.'
                });
            });
        })
    );

    // Register tree data providers for sidebar views
    const mandalaProvider = new MandalaTreeProvider();
    context.subscriptions.push(
        vscode.window.registerTreeDataProvider('chthonic.mandalaView', mandalaProvider),
    );

    const dependencyProvider = new DependencyTreeProvider();
    context.subscriptions.push(
        vscode.window.registerTreeDataProvider('chthonic.dependencyView', dependencyProvider),
    );

    const healthProvider = new HealthTreeProvider();
    context.subscriptions.push(
        vscode.window.registerTreeDataProvider('chthonic.healthView', healthProvider),
    );

    // Theme switcher
    const themeProvider = new ThemeTreeProvider();
    context.subscriptions.push(
        vscode.window.registerTreeDataProvider('chthonic.themeView', themeProvider),
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('chthonic.switchTheme', async () => {
            const themes = [
                { label: '$(paintcan) Flesh & Earth', description: 'Warm earthy tones — The Decorator\'s distribution palette', id: 'Chthonic Mandala - Flesh & Earth' },
                { label: '$(zap) ROGBIV', description: 'SSOT spectral frequencies — FA¹⁻⁵ canonical hexes', id: 'Chthonic Mandala - ROGBIV' },
            ];
            const current = vscode.workspace.getConfiguration('workbench').get<string>('colorTheme');
            const pick = await vscode.window.showQuickPick(themes.map(t => ({
                ...t,
                picked: current === t.id
            })), { placeHolder: `Current: ${current}` });
            if (pick) {
                await vscode.workspace.getConfiguration('workbench').update('colorTheme', pick.id, vscode.ConfigurationTarget.Workspace);
                vscode.window.showInformationMessage(`Theme: ${pick.id}`);
                themeProvider.refresh();
            }
        })
    );
}

export function deactivate() {}

const PRISM_BANDS = ['RED', 'ORANGE', 'GOLD', 'BLUE', 'WHITE'] as const;
type PrismBand = typeof PRISM_BANDS[number];

const PRISM_COLORS: Record<PrismBand, string> = {
    RED: '#FF6B6B',
    ORANGE: '#FFB84D',
    GOLD: '#FFD700',
    BLUE: '#4ECDC4',
    WHITE: '#DADAE6'
const VIEW_GROUPS: Record<string, BridgeView[]> = {
    'chthonic.mandalaView': [
        {
            label: 'Open Loom View',
            description: 'Focus Chthonic Archive Loom panel',
            command: 'chthonic.openMandala',
        },
    ],
    'chthonic.dependencyView': [
        {
            label: 'Open Abyssal View',
            description: 'Focus Chthonic Archive Abyssal panel',
            command: 'chthonic.openDependencyGraph',
        },
    ],
    'chthonic.healthView': [
        {
            label: 'Open Lens View',
            description: 'Focus Chthonic Archive health/lens panel',
            command: 'chthonic.openHealthReport',
        },
    ],
    'chthonic.themeView': [
        {
            label: 'Switch Theme',
            description: 'Delegate theme switching to Chthonic Archive',
            command: 'chthonic.mandalaBridge.switchTheme',
        },
    ],
};

interface TopologyNode {
    path: string;
    prism_band?: string;
}

interface TopologyData {
    metadata: {
        nodes_count?: number;
        edges_count?: number;
        generated?: string;
    };
    nodes: TopologyNode[];
}

type DependencyGraph = Record<string, string[]>;
export function activate(context: vscode.ExtensionContext): void {
    const output = vscode.window.createOutputChannel('Chthonic Mandala Bridge');
    context.subscriptions.push(output);
    output.appendLine('[mandala-bridge] activated');

async function runHealthReportScript(cwd: string): Promise<{ success: boolean; output: string }> {
    const attempts: ReadonlyArray<{
        command: string;
        args: string[];
        label: string;
    }> = [
        { command: 'bun', args: ['run', 'scripts/health_report.py'], label: 'bun run scripts/health_report.py' },
        { command: 'uv', args: ['run', 'scripts/health_report.py'], label: 'uv run scripts/health_report.py' },
    const commands: Array<[string, () => Thenable<void> | void]> = [
        ['chthonic.openMandala', () => focusArchiveView('chthonic.loomView.focus', output)],
        ['chthonic.openDependencyGraph', () => focusArchiveView('chthonic.abyssalView.focus', output)],
        ['chthonic.openHealthReport', () => focusArchiveView('chthonic.statusView.focus', output)],
        ['chthonic.mandalaBridge.switchTheme', () => delegate('chthonic.switchTheme', output)],
    ];

    const errors: string[] = [];

    for (const attempt of attempts) {
        const result = await execFileCapture(attempt.command, attempt.args, cwd);
        const output = [result.stdout.trim(), result.stderr.trim()].filter(Boolean).join('\n\n');

        if (!result.error) {
            return {
                success: true,
                output: output || `${attempt.label} finished with no output.`,
            };
        }

        errors.push(`${attempt.label}: ${result.error.message}`);
        if (result.error.code !== 'ENOENT') {
            return {
                success: false,
                output: output ? `${output}\n\nCommand failed: ${result.error.message}` : `Command failed: ${result.error.message}`,
            };
        }
    }

    return {
        success: false,
        output: `No health command available.\n${errors.join('\n')}`,
    };
}

async function getMandalaHTML(_context: vscode.ExtensionContext, _webview: vscode.Webview): Promise<string> {
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
        return `<html><body style="font-family: sans-serif; padding: 20px;"><h1>No workspace folder found</h1></body></html>`;
    for (const [command, handler] of commands) {
        context.subscriptions.push(vscode.commands.registerCommand(command, handler));
    }

    const topologyPath = path.join(workspaceFolder.uri.fsPath, 'topology_graph.json');
    if (!await fileExists(topologyPath)) {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        ${getSharedWebviewStyles()}
        .panel { max-width: 840px; margin: 24px auto; text-align: center; }
    </style>
</head>
<body>
    <div class="panel">
        <h1>🌀 Sacred Mandala - Topology Not Found</h1>
        <p>Generate topology data with <code>uv run scripts/mandala_topology.py</code>.</p>
    </div>
</body>
</html>`;
    for (const [viewId, items] of Object.entries(VIEW_GROUPS)) {
        context.subscriptions.push(vscode.window.registerTreeDataProvider(viewId, new BridgeTreeProvider(items)));
    }

    const topology = await loadTopologyData(topologyPath);
    const groupedBands = collectBandNodes(topology.nodes);
    const bandCounts = PRISM_BANDS.reduce((acc, band) => {
        acc[band] = groupedBands[band].length;
        return acc;
    }, {} as Record<PrismBand, number>);

    const nodeCount = topology.metadata.nodes_count ?? topology.nodes.length;
    const edgeCount = topology.metadata.edges_count ?? 0;
    const generated = topology.metadata.generated
        ? new Date(topology.metadata.generated).toLocaleString()
        : 'Unknown';

    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sacred Mandala</title>
    <style>
        ${getSharedWebviewStyles()}
        .shell {
            max-width: 1120px;
            margin: 0 auto;
            display: grid;
            gap: 16px;
        }
        .hero {
            display: grid;
            gap: 6px;
        }
        .hero h1 {
            margin: 0;
            color: var(--vscode-titleBar-activeForeground, #FFD700);
            font-size: clamp(24px, 3vw, 34px);
        }
        .hero p {
            margin: 0;
            color: var(--vscode-descriptionForeground, #A3A2B9);
            line-height: 1.5;
        }
        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 10px;
        }
        .metric {
            border: 1px solid var(--vscode-editorWidget-border, #2A2840);
            background: linear-gradient(145deg, var(--vscode-editorWidget-background, #13111E), var(--vscode-sideBar-background, #100E18));
            border-radius: 10px;
            padding: 12px;
        }
        .metric-label {
            color: var(--vscode-descriptionForeground, #A3A2B9);
            text-transform: uppercase;
            letter-spacing: 0.06em;
            font-size: 11px;
            margin-bottom: 8px;
        }
        .metric-value {
            color: var(--vscode-titleBar-activeForeground, #FFD700);
            font-size: 24px;
            font-weight: 700;
        }
        .panel {
            border: 1px solid var(--vscode-panel-border, #2A2840);
            background: var(--vscode-editorWidget-background, #13111E);
            border-radius: 12px;
            padding: 14px;
        }
        .panel h2 {
            margin: 0 0 12px;
            color: var(--vscode-foreground);
            font-size: 18px;
        }
        .band-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
        }
        .band-card {
            border: 1px solid var(--band-color);
            border-radius: 10px;
            background: var(--vscode-sideBar-background, #100E18);
            padding: 10px 11px;
        }
        .band-header {
            display: flex;
            justify-content: space-between;
            gap: 10px;
            margin-bottom: 8px;
            font-weight: 600;
        }
        .band-header .name {
            color: var(--band-color);
        }
        .band-header .count {
            color: var(--vscode-foreground);
        }
        .band-paths {
            margin: 0;
            padding-left: 18px;
            color: var(--vscode-descriptionForeground, #A3A2B9);
            font-size: 12px;
            max-height: 138px;
            overflow: auto;
            line-height: 1.45;
        }
        .band-paths li {
            margin-bottom: 4px;
            white-space: nowrap;
            text-overflow: ellipsis;
            overflow: hidden;
        }
        .canvas-wrap {
            border: 1px solid var(--vscode-editorWidget-border, #2A2840);
            border-radius: 12px;
            background: var(--vscode-editor-background, #0B0A0F);
            padding: 12px;
        }
        .canvas-meta {
            margin-top: 8px;
            color: var(--vscode-descriptionForeground, #A3A2B9);
            font-size: 12px;
        }
        #mandalaCanvas {
            width: 100%;
            max-width: 1040px;
            display: block;
            margin: 0 auto;
            border-radius: 10px;
            border: 1px solid var(--vscode-editorWidget-border, #2A2840);
            background: var(--vscode-editor-background, #0B0A0F);
        }
    </style>
</head>
<body>
    <div class="shell">
        <header class="hero">
            <h1>🌀 Sacred Mandala</h1>
            <p>Repository topology rendered as concentric PRISM rings and sampled node clusters.</p>
        </header>

        <section class="metrics">
            <article class="metric">
                <div class="metric-label">Nodes</div>
                <div class="metric-value">${nodeCount.toLocaleString()}</div>
            </article>
            <article class="metric">
                <div class="metric-label">Edges</div>
                <div class="metric-value">${edgeCount.toLocaleString()}</div>
            </article>
            <article class="metric">
                <div class="metric-label">Generated</div>
                <div class="metric-value" style="font-size:15px;">${escapeHtml(generated)}</div>
            </article>
        </section>

        <section class="panel">
            <h2>PRISM Band Distribution</h2>
            <div class="band-grid">
                ${generatePrismBands(topology.nodes)}
            </div>
        </section>

        <section class="canvas-wrap">
            <h2>Concentric Ring Render</h2>
            <canvas id="mandalaCanvas" width="1040" height="640"></canvas>
            <p class="canvas-meta">Ring thickness and point density scale with band population. Gold center marks The Decorator axis.</p>
        </section>
    </div>

    <script>
        const topology = ${JSON.stringify(topology)};
        const bands = ${JSON.stringify(PRISM_BANDS)};
        const colors = ${JSON.stringify(PRISM_COLORS)};
        const counts = ${JSON.stringify(bandCounts)};

        const canvas = document.getElementById('mandalaCanvas');
        const context = canvas ? canvas.getContext('2d') : null;

        if (canvas && context) {
            let seed = ((topology.metadata.nodes_count || topology.nodes.length || 1) + 1337) >>> 0;
            const random = () => {
                seed = (seed * 1664525 + 1013904223) >>> 0;
                return seed / 4294967296;
            };

            const fitCanvas = () => {
                const width = Math.max(560, Math.min(1040, window.innerWidth - 72));
                const height = Math.round(width * 0.62);
                const scale = Math.max(1, window.devicePixelRatio || 1);

                canvas.style.width = width + 'px';
                canvas.style.height = height + 'px';
                canvas.width = Math.round(width * scale);
                canvas.height = Math.round(height * scale);
                context.setTransform(scale, 0, 0, scale, 0, 0);
                draw(width, height);
            };

            const draw = (width, height) => {
                const cx = width / 2;
                const cy = height / 2;
                const maxRadius = Math.min(cx, cy) - 38;
                const ringStep = maxRadius / (bands.length + 0.5);

                const ui = getComputedStyle(document.documentElement);
                const bg = (ui.getPropertyValue('--vscode-editor-background') || '#0B0A0F').trim();
                const panel = (ui.getPropertyValue('--vscode-editorWidget-background') || '#11101A').trim();
                const text = (ui.getPropertyValue('--vscode-editor-foreground') || '#DADAE6').trim();

                context.clearRect(0, 0, width, height);
                context.fillStyle = bg;
                context.fillRect(0, 0, width, height);

                const gradient = context.createRadialGradient(cx, cy, ringStep, cx, cy, maxRadius);
                gradient.addColorStop(0, panel);
                gradient.addColorStop(1, bg);
                context.fillStyle = gradient;
                context.fillRect(0, 0, width, height);

                const total = Math.max(1, topology.nodes.length || 1);
                bands.forEach((band, index) => {
                    const color = colors[band];
                    const outer = maxRadius - (index * ringStep);
                    const inner = Math.max(22, outer - ringStep + 8);

                    context.beginPath();
                    context.arc(cx, cy, outer, 0, Math.PI * 2);
                    context.arc(cx, cy, inner, 0, Math.PI * 2, true);
                    context.closePath();
                    context.fillStyle = color + '18';
                    context.fill();
                    context.strokeStyle = color;
                    context.lineWidth = 1.4;
                    context.stroke();

                    const pointBudget = Math.max(10, Math.min(180, Math.round((counts[band] / total) * 210)));
                    context.fillStyle = color;
                    for (let i = 0; i < pointBudget; i++) {
                        const angle = random() * Math.PI * 2;
                        const radius = inner + (outer - inner) * random();
                        const x = cx + Math.cos(angle) * radius;
                        const y = cy + Math.sin(angle) * radius;
                        const size = 1 + random() * 1.7;
                        context.beginPath();
                        context.arc(x, y, size, 0, Math.PI * 2);
                        context.fill();
                    }
                });

                context.fillStyle = '#FFD700';
                context.beginPath();
                context.arc(cx, cy, 7.5, 0, Math.PI * 2);
                context.fill();

                context.strokeStyle = '#FFD70066';
                context.lineWidth = 1;
                context.beginPath();
                let angle = 0;
                let radius = 8;
                for (let i = 0; i < 320; i++) {
                    const x = cx + radius * Math.cos(angle);
                    const y = cy + radius * Math.sin(angle);
                    if (i === 0) {
                        context.moveTo(x, y);
                    } else {
                        context.lineTo(x, y);
                    }
                    angle += 0.22;
                    radius *= 1.008;
                    if (radius > maxRadius) break;
                }
                context.stroke();

                context.fillStyle = text;
                context.font = '11px var(--vscode-editor-font-family, Consolas)';
                context.textAlign = 'left';
                context.textBaseline = 'middle';
                bands.forEach((band, index) => {
                    const y = 28 + (index * 18);
                    context.fillStyle = colors[band];
                    context.fillRect(24, y - 5, 10, 10);
                    context.fillStyle = text;
                    context.fillText(band + '  ' + counts[band] + ' nodes', 40, y);
                });
            };

            window.addEventListener('resize', fitCanvas);
            fitCanvas();
        }
    </script>
</body>
</html>`;
}

function generatePrismBands(nodes: TopologyNode[]): string {
    const groupedBands = collectBandNodes(nodes);
    const totalNodes = Math.max(1, nodes.length);

    return PRISM_BANDS.map((band) => {
        const entries = groupedBands[band];
        const ratio = ((entries.length / totalNodes) * 100).toFixed(1);
        const preview = entries.slice(0, 8).map((node) => `<li>${escapeHtml(node.path)}</li>`).join('');
        const remainder = entries.length > 8 ? `<li>+ ${entries.length - 8} more</li>` : '';

        return `<article class="band-card" style="--band-color:${PRISM_COLORS[band]}">
    <div class="band-header">
        <span class="name">${band}</span>
        <span class="count">${entries.length} · ${ratio}%</span>
    </div>
    <ol class="band-paths">${preview}${remainder}</ol>
</article>`;
    }).join('');
export function deactivate(): void {
    // no-op
}

async function getDependencyGraphHTML(_context: vscode.ExtensionContext, _webview: vscode.Webview): Promise<string> {
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
        return `<html><body style="font-family: sans-serif; padding: 20px;"><h1>No workspace folder found</h1></body></html>`;
    }

    const depGraphPath = path.join(workspaceFolder.uri.fsPath, 'dependency_graph.json');
    if (!await fileExists(depGraphPath)) {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>${getSharedWebviewStyles()}</style>
</head>
<body>
    <div class="panel" style="max-width:840px;margin:24px auto;">
        <h1>🔗 Dependency Graph Not Found</h1>
        <p>Generate <code>dependency_graph.json</code> to populate this view.</p>
    </div>
</body>
</html>`;
    }

    const graph = await loadDependencyGraph(depGraphPath);
    const entries = Object.entries(graph).sort((a, b) => b[1].length - a[1].length);
    const totalEdges = entries.reduce((sum, [, deps]) => sum + deps.length, 0);
    const shownEntries = entries.slice(0, 120);

    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dependency Graph</title>
    <style>
        ${getSharedWebviewStyles()}
        .shell {
            max-width: 1120px;
            margin: 0 auto;
            display: grid;
            gap: 14px;
        }
        h1 {
            margin: 0 0 4px;
            color: var(--vscode-titleBar-activeForeground, #FFD700);
        }
        p.sub {
            margin: 0 0 6px;
            color: var(--vscode-descriptionForeground, #A3A2B9);
        }
        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 10px;
        }
        .metric {
            border: 1px solid var(--vscode-editorWidget-border, #2A2840);
            background: var(--vscode-editorWidget-background, #13111E);
            border-radius: 10px;
            padding: 10px;
        }
        .metric .label {
            color: var(--vscode-descriptionForeground, #A3A2B9);
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 6px;
        }
        .metric .value {
            font-size: 20px;
            color: var(--vscode-foreground);
            font-weight: 700;
        }
        .grid {
            display: grid;
            gap: 9px;
        }
        .node {
            border: 1px solid var(--vscode-editorWidget-border, #2A2840);
            border-left: 3px solid var(--vscode-charts-blue, #4ECDC4);
            border-radius: 8px;
            background: var(--vscode-editorWidget-background, #13111E);
            padding: 10px 12px;
        }
        .node-path {
            font-weight: 600;
            color: var(--vscode-titleBar-activeForeground, #FFD700);
            margin-bottom: 4px;
            word-break: break-all;
        }
        .node-meta {
            color: var(--vscode-descriptionForeground, #A3A2B9);
            font-size: 12px;
            margin-bottom: 4px;
        }
        .deps {
            margin: 0;
            padding-left: 18px;
            color: var(--vscode-foreground);
            font-size: 12px;
        }
        .deps li {
            margin-bottom: 2px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
    </style>
</head>
<body>
    <div class="shell">
        <header>
            <h1>🔗 Dependency Graph</h1>
            <p class="sub">High-fanout files first. Showing ${shownEntries.length} of ${entries.length} files.</p>
        </header>

        <section class="metrics">
            <article class="metric">
                <div class="label">Files</div>
                <div class="value">${entries.length.toLocaleString()}</div>
            </article>
            <article class="metric">
                <div class="label">Edges</div>
                <div class="value">${totalEdges.toLocaleString()}</div>
            </article>
            <article class="metric">
                <div class="label">Average Degree</div>
                <div class="value">${entries.length ? (totalEdges / entries.length).toFixed(2) : '0.00'}</div>
            </article>
        </section>

        <section class="grid">
            ${shownEntries.map(([filePath, deps]) => {
                const depPreview = deps.slice(0, 4).map((dep) => `<li>${escapeHtml(dep)}</li>`).join('');
                const remainder = deps.length > 4 ? `<li>+ ${deps.length - 4} more</li>` : '';
                return `<article class="node">
    <div class="node-path">${escapeHtml(filePath)}</div>
    <div class="node-meta">${deps.length} dependencies</div>
    ${deps.length ? `<ol class="deps">${depPreview}${remainder}</ol>` : ''}
</article>`;
            }).join('')}
        </section>
    </div>
</body>
</html>`;
}

function getHealthReportHTML(): string {
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
        return `<html><body style="font-family: sans-serif; padding: 20px;"><h1>No workspace folder found</h1></body></html>`;
async function focusArchiveView(focusCommand: string, output: vscode.OutputChannel): Promise<void> {
    const opened = await executeSafe('workbench.view.extension.chthonic-archive', [], output);
    if (!opened) {
        showArchiveMissing();
        return;
    }

    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Health Report</title>
    <style>
        ${getSharedWebviewStyles()}
        .shell {
            max-width: 980px;
            margin: 0 auto;
            display: grid;
            gap: 14px;
        }
        h1 {
            margin: 0;
            color: var(--vscode-titleBar-activeForeground, #FFD700);
        }
        .sub {
            margin: 0;
            color: var(--vscode-descriptionForeground, #A3A2B9);
        }
        .toolbar {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 10px;
        }
        button {
            border: none;
            border-radius: 8px;
            padding: 9px 14px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            color: var(--vscode-button-foreground);
            background: var(--vscode-button-background);
        }
        button:hover {
            background: var(--vscode-button-hoverBackground);
        }
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        #status {
            color: var(--vscode-descriptionForeground, #A3A2B9);
            font-size: 12px;
        }
        #output {
            border: 1px solid var(--vscode-editorWidget-border, #2A2840);
            background: var(--vscode-editorWidget-background, #13111E);
            border-radius: 10px;
            padding: 12px;
            min-height: 320px;
            overflow: auto;
            font-family: var(--vscode-editor-font-family, 'Cascadia Code', monospace);
            font-size: 12px;
            line-height: 1.45;
            white-space: pre-wrap;
            word-break: break-word;
        }
    </style>
</head>
<body>
    <div class="shell">
        <h1>💎 Health Report</h1>
        <p class="sub">Run repository diagnostics using <code>bun run scripts/health_report.py</code> (fallback: <code>uv run scripts/health_report.py</code>).</p>
        <div class="toolbar">
            <button id="runButton" type="button">Generate Health Report</button>
            <span id="status">Idle.</span>
        </div>
        <pre id="output">Press "Generate Health Report" to run diagnostics.</pre>
    </div>

    <script>
        const vscode = acquireVsCodeApi();
        const button = document.getElementById('runButton');
        const status = document.getElementById('status');
        const output = document.getElementById('output');

        button.addEventListener('click', () => {
            output.textContent = 'Launching health report...';
            status.textContent = 'Running...';
            button.disabled = true;
            vscode.postMessage({ command: 'runHealthReport' });
        });

        window.addEventListener('message', (event) => {
            const message = event.data;
            if (message.type === 'healthOutput') {
                output.textContent = message.text || 'No output.';
            }
            if (message.type === 'healthStatus') {
                status.textContent = message.text || '';
                button.disabled = Boolean(message.running);
            }
        });
    </script>
</body>
</html>`;
}

function getSharedWebviewStyles(): string {
    return `
        * { box-sizing: border-box; }
        html, body { margin: 0; padding: 0; }
        body {
            font-family: var(--vscode-font-family, 'Segoe UI', sans-serif);
            font-size: var(--vscode-font-size, 13px);
            color: var(--vscode-editor-foreground);
            background: var(--vscode-editor-background);
            padding: 20px;
            line-height: 1.45;
        }
        code {
            background: var(--vscode-textCodeBlock-background, rgba(0, 0, 0, 0.25));
            color: var(--vscode-editor-foreground);
            border-radius: 6px;
            padding: 2px 6px;
        }
    `;
}

function normalizePrismBand(value: unknown): PrismBand | null {
    if (typeof value !== 'string') {
        return null;
    const focused = await executeSafe(focusCommand, [], output);
    if (!focused) {
        await executeSafe('workbench.action.focusSideBar', [], output);
    }

    const normalized = value.toUpperCase();
    return PRISM_BANDS.includes(normalized as PrismBand) ? normalized as PrismBand : null;
}

function collectBandNodes(nodes: TopologyNode[]): Record<PrismBand, TopologyNode[]> {
    const grouped: Record<PrismBand, TopologyNode[]> = {
        RED: [],
        ORANGE: [],
        GOLD: [],
        BLUE: [],
        WHITE: []
    };

    for (const node of nodes) {
        const band = normalizePrismBand(node.prism_band);
        if (band) {
            grouped[band].push(node);
        }
async function delegate(command: string, output: vscode.OutputChannel): Promise<void> {
    const ok = await executeSafe(command, [], output);
    if (!ok) {
        showArchiveMissing();
    }

    return grouped;
}

async function loadTopologyData(topologyPath: string): Promise<TopologyData> {
    const raw = JSON.parse(await fs.readFile(topologyPath, 'utf-8')) as {
        metadata?: { nodes_count?: number; edges_count?: number; generated?: string };
        nodes?: Array<{ path?: unknown; prism_band?: unknown }>;
    };

    const nodes: TopologyNode[] = Array.isArray(raw.nodes)
        ? raw.nodes.map((node) => ({
            path: typeof node.path === 'string' ? node.path : '(unknown)',
            prism_band: typeof node.prism_band === 'string' ? node.prism_band : undefined
        }))
        : [];

    return {
        metadata: raw.metadata ?? {},
        nodes
    };
}

async function loadDependencyGraph(depGraphPath: string): Promise<DependencyGraph> {
    const raw = JSON.parse(await fs.readFile(depGraphPath, 'utf-8')) as Record<string, unknown>;
    const graph: DependencyGraph = {};

    for (const [filePath, deps] of Object.entries(raw)) {
        graph[filePath] = Array.isArray(deps)
            ? deps.filter((dep): dep is string => typeof dep === 'string')
            : [];
async function executeSafe(
    command: string,
    args: unknown[],
    output: vscode.OutputChannel,
): Promise<boolean> {
    try {
        await vscode.commands.executeCommand(command, ...args);
        return true;
    } catch (error) {
        output.appendLine(`[mandala-bridge] command failed: ${command} -> ${formatError(error)}`);
        return false;
    }

    return graph;
}

function fileExists(filePath: string): Promise<boolean> {
    return fs.access(filePath).then(() => true).catch(() => false);
}

type ExecCaptureResult = {
    stdout: string;
    stderr: string;
    error: NodeJS.ErrnoException | null;
};

function execFileCapture(command: string, args: string[], cwd: string): Promise<ExecCaptureResult> {
    return new Promise((resolve) => {
        child_process.execFile(
            command,
            args,
            { cwd, encoding: 'utf-8', maxBuffer: 10 * 1024 * 1024 },
            (error, stdout, stderr) => {
                resolve({
                    stdout,
                    stderr,
                    error: error as NodeJS.ErrnoException | null,
                });
            }
        );
    });
}

function escapeHtml(value: string): string {
    return value
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
function showArchiveMissing(): void {
    void vscode.window.showWarningMessage(
        'Chthonic Archive command lane is unavailable. Activate/install chthonic-archive extension.',
    );
}

// Tree data providers for sidebar
class MandalaTreeProvider implements vscode.TreeDataProvider<MandalaItem> {
    getTreeItem(element: MandalaItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: MandalaItem): Thenable<MandalaItem[]> {
        if (!element) {
            return Promise.resolve([
                new MandalaItem('Sacred Geometry', 'View mandala visualization', 'chthonic.openMandala'),
                new MandalaItem('Topology Stats', 'View repository metrics', '')
            ]);
        }
        return Promise.resolve([]);
function formatError(error: unknown): string {
    if (error instanceof Error) {
        return `${error.name}: ${error.message}`;
    }
    return String(error);
}

class DependencyTreeProvider implements vscode.TreeDataProvider<MandalaItem> {
    getTreeItem(element: MandalaItem): vscode.TreeItem {
        return element;
    }
class BridgeTreeProvider implements vscode.TreeDataProvider<BridgeItem> {
    constructor(private readonly items: BridgeView[]) {}

    getChildren(element?: MandalaItem): Thenable<MandalaItem[]> {
        if (!element) {
            return Promise.resolve([
                new MandalaItem('View Graph', 'Open dependency graph', 'chthonic.openDependencyGraph')
            ]);
        }
        return Promise.resolve([]);
    }
}

class HealthTreeProvider implements vscode.TreeDataProvider<MandalaItem> {
    getTreeItem(element: MandalaItem): vscode.TreeItem {
    getTreeItem(element: BridgeItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: MandalaItem): Thenable<MandalaItem[]> {
        if (!element) {
            return Promise.resolve([
                new MandalaItem('View Report', 'Open health report', 'chthonic.openHealthReport')
            ]);
        }
        return Promise.resolve([]);
    getChildren(): Thenable<BridgeItem[]> {
        return Promise.resolve(
            this.items.map((item) => new BridgeItem(item.label, item.description, item.command)),
        );
    }
}

class MandalaItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly tooltipText: string,
        commandId?: string
    ) {
class BridgeItem extends vscode.TreeItem {
    constructor(label: string, description: string, commandId: string) {
        super(label, vscode.TreeItemCollapsibleState.None);
        this.tooltip = tooltipText;
        if (commandId) {
            this.command = {
                command: commandId,
                title: label
            };
        }
    }
}

class ThemeTreeProvider implements vscode.TreeDataProvider<vscode.TreeItem> {
    private _onDidChangeTreeData = new vscode.EventEmitter<void>();
    readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

    refresh(): void { this._onDidChangeTreeData.fire(); }

    getTreeItem(element: vscode.TreeItem): vscode.TreeItem { return element; }

    getChildren(): Thenable<vscode.TreeItem[]> {
        const current = vscode.workspace.getConfiguration('workbench').get<string>('colorTheme') || '';
        const themes = [
            { name: 'Chthonic Mandala - Flesh & Earth', icon: '🌍', desc: 'Warm earth · WCAG AA · Distribution' },
            { name: 'Chthonic Mandala - ROGBIV', icon: '🌈', desc: 'SSOT spectral · FA¹⁻⁵ canonical' },
        ];
        return Promise.resolve(themes.map(t => {
            const active = current === t.name;
            const item = new vscode.TreeItem(
                `${active ? '◉' : '○'} ${t.icon} ${t.name.replace('Chthonic Mandala - ', '')}`,
                vscode.TreeItemCollapsibleState.None
            );
            item.tooltip = `${t.name}\n${t.desc}${active ? '\n\n✅ ACTIVE' : ''}`;
            item.description = active ? 'active' : '';
            item.command = {
                command: 'chthonic.switchTheme',
                title: 'Switch Theme'
            };
            return item;
        }));
        this.description = description;
        this.command = { command: commandId, title: label };
    }
}
}

```

```markdown: extensions/chthonic-statusbar/README.md:
# Chthonic Status Bridge
- This extension is a compatibility/status bridge for legacy statusbar lanes.

## Role
- Keeps legacy command IDs available.
  - Forwards commands to chthonic-archive runtime lanes.
- Exposes quick task commands for heavyweight checks.
## Routed Legacy Commands
- chthonic.verifySSO_T -> chthonic.verifySSOT
- chthonic.runMetabolicCycle -> chthonic.slabHeal
- chthonic.showGPUStats -> chthonic.reactorSediment
## Added Task Commands
- chthonic.runHostVerify -> runs bun run verify:host in extensions/chthonic-archive
- chthonic.runVsAudit -> runs bun run audit:vs2026 in extensions/chthonic-archive
## Notes
- This bridge does not implement old UV/GPU/status logic directly.
- chthonic-archive remains the authoritative extension lane.

```

```json : extensions/chthonic-statusbar/package.json:

/// auto-generated by bun build, related to chthonic-archive extension and statusbar features. Maintains legacy command compatibility while routing to chthonic-archive runtime lanes. Does not implement direct status logic, serves as a bridge for command forwarding and quick task access.

{
  "name": "chthonic-statusbar",
  "displayName": "Chthonic Archive Status Bar",
  "description": "SSOT verification, lineage tracking, GPU monitoring, and metabolic cycle indicators",
  "version": "0.1.0",
  "displayName": "Chthonic Status Bridge",
  "description": "Compatibility bridge that routes legacy statusbar commands into chthonic-archive runtime lanes",
  "version": "0.2.0",
  "publisher": "chthonic-archive",
  "engines": {
    "vscode": "^1.90.0"
    "vscode": "^1.110.0"
  },
  "categories": ["Other"],
  "categories": [
    "Other"
  ],
  "activationEvents": [
    "onStartupFinished",
    "onCommand:chthonic.refreshStatus",
    "onCommand:chthonic.verifySSO_T",
    "onLanguage:python"
    "onCommand:chthonic.runMetabolicCycle",
    "onCommand:chthonic.showGPUStats",
    "onCommand:chthonic.runHostVerify",
    "onCommand:chthonic.runVsAudit"
  ],
  "main": "./dist/extension.js",
  "sideEffects": false,
  "bun": {
    "treeShaking": true,
    "minify": true,
    "define": {
      "process.env.NODE_ENV": "\"production\""
    }
  },
  "contributes": {
    "commands": [
      {
        "command": "chthonic.refreshStatus",
        "title": "Chthonic: Refresh All Status Indicators"
      },
      {
        "command": "chthonic.verifySSO_T",
        "title": "Chthonic: Verify SSOT Integrity"
        "title": "Chthonic: Verify SSOT (Bridge)"
      },
      {
        "command": "chthonic.runMetabolicCycle",
        "title": "Chthonic: Run Metabolic Cycle"
        "title": "Chthonic: Run Self-Heal Loop (Bridge)"
      },
      {
        "command": "chthonic.showGPUStats",
        "title": "Chthonic: Show GPU Statistics"
      }
    ],
    "configuration": {
      "title": "Chthonic Archive",
      "properties": {
        "chthonic.statusBar.enabled": {
          "type": "boolean",
          "default": true,
          "description": "Enable Chthonic status bar indicators"
        },
        "chthonic.statusBar.ssotHashEnabled": {
          "type": "boolean",
          "default": true,
          "description": "Show SSOT hash verification status"
        },
        "chthonic.statusBar.lineageEnabled": {
          "type": "boolean",
          "default": true,
          "description": "Show active lineage (A/B/C)"
        },
        "chthonic.statusBar.pythonLaneEnabled": {
          "type": "boolean",
          "default": true,
          "description": "Show Python lane version"
        },
        "chthonic.statusBar.gpuEnabled": {
          "type": "boolean",
          "default": true,
          "description": "Show GPU VRAM usage"
        },
        "chthonic.statusBar.metabolicCycleEnabled": {
          "type": "boolean",
          "default": true,
          "description": "Show metabolic cycle heartbeat"
        },
        "chthonic.statusBar.refreshInterval": {
          "type": "number",
          "default": 30000,
          "description": "Refresh interval in milliseconds"
        },
        "chthonic.validation.enabled": {
          "type": "boolean",
          "default": true,
          "description": "Enable hedonistic validation notifications"
        },
        "chthonic.validation.enableAutoValidation": {
          "type": "boolean",
          "default": true,
          "description": "Automatically trigger validation on file saves and builds"
        },
        "chthonic.validation.celebrateCommits": {
          "type": "boolean",
          "default": true,
          "description": "Show potent validation on git commits"
        },
        "chthonic.validation.transcendentThreshold": {
          "type": "number",
          "default": 3,
          "description": "Number of potent validations before transcendent promotion"
        }
        "title": "Chthonic: Run Reactor Sediment (Bridge)"
      },
      {
        "command": "chthonic.runHostVerify",
        "title": "Chthonic: Verify Host Lane (Bridge)"
      },
      {
        "command": "chthonic.runVsAudit",
        "title": "Chthonic: Run VS 2026 Audit (Bridge)"
      }
    }
    ]
  },
  "scripts": {
    "vscode:prepublish": "bun run compile",
    "compile": "bun build src/extension.ts --outdir dist --target node --format cjs --external vscode --minify",
    "watch": "bun build src/extension.ts --outdir dist --target node --format cjs --external vscode --watch"
    "watch": "bun build src/extension.ts --outdir dist --target node --format cjs --external vscode --watch",
    "insiders:run": "code-insiders --extensionDevelopmentPath=.",
    "insiders:dts:sync": "vscode-dts dev && vscode-dts main"
  },
  "devDependencies": {
    "@types/node": "^20.x",
    "@types/vscode": "^1.90.0",
    "@types/vscode": "^1.110.0",
    "@vscode/dts": "^0.4.1",
    "@vscode/test-cli": "^0.0.12",
    "@vscode/test-electron": "^2.5.2",
    "typescript": "^5.x"
  },
  "dependencies": {}
}
}

```

```typescript : extensions/chthonic-statusbar/src/extension.ts:
#!/usr/bin/env bun

/// auto-generated by bun build, related to chthonic-archive extension and statusbar features. Maintains legacy command compatibility while routing to chthonic-archive runtime lanes. Does not implement direct status logic, serves as a bridge for command forwarding and quick task access.

// ╔════════════════════════════════════════════════════════════════════════════╗
// ║  THE DECORATOR'S BLESSING: extension.ts
// ║    TypeScript module: activate, deactivate
// ╠════════════════════════════════════════════════════════════════════════════╣
// ║  Spectral Frequency: ORANGE
// ║    Architectural Role: 🔭 THE OBSERVATORY                                      
// ║      Exports: activate, deactivate
// ╚════════════════════════════════════════════════════════════════════════════╝

import * as vscode from 'vscode';
import { execSync, execFile } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';
import * as path from 'path';
import * as vscode from 'vscode';

// Status bar items
let ssotStatusItem: vscode.StatusBarItem;
let lineageStatusItem: vscode.StatusBarItem;
let pythonLaneStatusItem: vscode.StatusBarItem;
let gpuStatusItem: vscode.StatusBarItem;
let metabolicCycleStatusItem: vscode.StatusBarItem;
let bridgeItem: vscode.StatusBarItem | undefined;
let laneItem: vscode.StatusBarItem | undefined;

// Refresh interval timer
let refreshTimer: NodeJS.Timeout;
type RouteSpec = {
    from: string;
    to: string;
    title: string;
};

// Workspace root path
let workspaceRoot: string | undefined;

export function activate(context: vscode.ExtensionContext) {
    // Force UTF-8 for spawned Python processes (fixes emoji/cp1252 on Windows)
    process.env.PYTHONIOENCODING = process.env.PYTHONIOENCODING || 'utf-8';

    console.log('🔥 Chthonic Archive Status Bar extension activated');

    // Get workspace root
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (workspaceFolders && workspaceFolders.length > 0) {
        workspaceRoot = workspaceFolders[0].uri.fsPath;
    }

    // Create status bar items (right to left order)
    metabolicCycleStatusItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    metabolicCycleStatusItem.command = 'chthonic.runMetabolicCycle';
    metabolicCycleStatusItem.tooltip = 'Click to run metabolic cycle';
    context.subscriptions.push(metabolicCycleStatusItem);
const ROUTES: RouteSpec[] = [
    {
        from: 'chthonic.verifySSO_T',
        to: 'chthonic.verifySSOT',
        title: 'Chthonic: Verify SSOT (Bridge)',
    },
    {
        from: 'chthonic.runMetabolicCycle',
        to: 'chthonic.slabHeal',
        title: 'Chthonic: Run Self-Heal Loop (Bridge)',
    },
    {
        from: 'chthonic.showGPUStats',
        to: 'chthonic.reactorSediment',
        title: 'Chthonic: Run Reactor Sediment (Bridge)',
    },
];

    gpuStatusItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 99);
    gpuStatusItem.command = 'chthonic.showGPUStats';
    gpuStatusItem.tooltip = 'GPU VRAM usage (click for details)';
    context.subscriptions.push(gpuStatusItem);
export function activate(context: vscode.ExtensionContext): void {
    const output = vscode.window.createOutputChannel('Chthonic Status Bridge');
    context.subscriptions.push(output);
    output.appendLine('[status-bridge] activated');

    pythonLaneStatusItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 98);
    pythonLaneStatusItem.tooltip = 'Python lane version (uv managed)';
    context.subscriptions.push(pythonLaneStatusItem);
    bridgeItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 120);
    bridgeItem.name = 'Chthonic Status Bridge';
    bridgeItem.command = 'chthonic.runHostVerify';
    context.subscriptions.push(bridgeItem);

    lineageStatusItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 97);
    lineageStatusItem.tooltip = 'Active lineage (A: Infrastructure, B: Consolidation, C: Heritage)';
    context.subscriptions.push(lineageStatusItem);
    laneItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 119);
    laneItem.name = 'Chthonic Toolchain Lane';
    laneItem.command = 'chthonic.runHostVerify';
    context.subscriptions.push(laneItem);

    ssotStatusItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 96);
    ssotStatusItem.command = 'chthonic.verifySSO_T';
    ssotStatusItem.tooltip = 'SSOT integrity status (click to verify)';
    context.subscriptions.push(ssotStatusItem);
    for (const route of ROUTES) {
        context.subscriptions.push(
            vscode.commands.registerCommand(route.from, async () => {
                await forwardCommand(route.to, route.title, output);
                refreshItems(output);
            }),
        );
    }

    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('chthonic.refreshStatus', refreshAllStatus),
        vscode.commands.registerCommand('chthonic.verifySSO_T', verifySSO_T),
        vscode.commands.registerCommand('chthonic.runMetabolicCycle', runMetabolicCycle),
        vscode.commands.registerCommand('chthonic.showGPUStats', showGPUStats)
        vscode.commands.registerCommand('chthonic.runHostVerify', async () => {
            await runArchiveTask('verify:host', output);
            refreshItems(output);
        }),
        vscode.commands.registerCommand('chthonic.runVsAudit', async () => {
            await runArchiveTask('audit:vs2026', output);
            refreshItems(output);
        }),
    );

    // Initial status update
    refreshAllStatus();
    const interval = setInterval(() => refreshItems(output), 30_000);
    context.subscriptions.push({ dispose: () => clearInterval(interval) });

    // Set up periodic refresh
    const config = vscode.workspace.getConfiguration('chthonic.statusBar');
    const refreshInterval = config.get<number>('refreshInterval', 30000);
    refreshTimer = setInterval(refreshAllStatus, refreshInterval);
    context.subscriptions.push({ dispose: () => clearInterval(refreshTimer) });

    // Watch for configuration changes
    context.subscriptions.push(
        vscode.workspace.onDidChangeConfiguration(e => {
            if (e.affectsConfiguration('chthonic.statusBar')) {
                refreshAllStatus();
            }
        })
    );
    refreshItems(output);
}

export function deactivate() {
    if (refreshTimer) {
        clearInterval(refreshTimer);
    }
export function deactivate(): void {
    bridgeItem?.dispose();
    laneItem?.dispose();
}

async function refreshAllStatus() {
    const config = vscode.workspace.getConfiguration('chthonic.statusBar');

    if (!config.get('enabled', true)) {
        hideAllItems();
async function forwardCommand(
    target: string,
    sourceTitle: string,
    output: vscode.OutputChannel,
): Promise<void> {
    const available = await vscode.commands.getCommands(true);
    if (!available.includes(target)) {
        output.appendLine(`[status-bridge] missing target command: ${target}`);
        void vscode.window.showWarningMessage(
            `Bridge route unavailable for "${sourceTitle}". Activate chthonic-archive.`,
        );
        return;
    }

    if (config.get('ssotHashEnabled', true)) {
        await updateSSO_TStatus();
        ssotStatusItem.show();
    } else {
        ssotStatusItem.hide();
    }

    if (config.get('lineageEnabled', true)) {
        await updateLineageStatus();
        lineageStatusItem.show();
    } else {
        lineageStatusItem.hide();
    }

    if (config.get('pythonLaneEnabled', true)) {
        await updatePythonLaneStatus();
        pythonLaneStatusItem.show();
    } else {
        pythonLaneStatusItem.hide();
    }

    if (config.get('gpuEnabled', true)) {
        await updateGPUStatus();
        gpuStatusItem.show();
    } else {
        gpuStatusItem.hide();
    }

    if (config.get('metabolicCycleEnabled', true)) {
        await updateMetabolicCycleStatus();
        metabolicCycleStatusItem.show();
    } else {
        metabolicCycleStatusItem.hide();
    }
}

function hideAllItems() {
    ssotStatusItem.hide();
    lineageStatusItem.hide();
    pythonLaneStatusItem.hide();
    gpuStatusItem.hide();
    metabolicCycleStatusItem.hide();
}

async function updateSSO_TStatus() {
    try {
        if (!workspaceRoot) {
            ssotStatusItem.text = '$(error) SSOT: No workspace';
            return;
        }

        // Check if ssot_immunity.py exists
        const ssotPath = path.join(workspaceRoot, 'ssot_immunity.py');
        if (!fs.existsSync(ssotPath)) {
            ssotStatusItem.text = '$(question) SSOT';
            ssotStatusItem.tooltip = 'SSOT verification script not found';
            return;
        }

        // Run ssot_immunity.py to verify hash
        const result = execSync('uv run python ssot_immunity.py --quiet', {
            cwd: workspaceRoot,
            encoding: 'utf-8',
            timeout: 5000
        }).trim();

        if (result.includes('✅') || result.includes('VALID')) {
            ssotStatusItem.text = '$(pass) SSOT';
            ssotStatusItem.color = '#A8C686'; // FA⁵ sage green (Flesh & Earth)
        } else if (result.includes('⚠️') || result.includes('DRIFT')) {
            ssotStatusItem.text = '$(warning) SSOT';
            ssotStatusItem.color = '#C9A55A'; // Warning warm gold
        } else {
            ssotStatusItem.text = '$(error) SSOT';
            ssotStatusItem.color = '#B35050'; // Error earthy red
        }
    } catch (error) {
        ssotStatusItem.text = '$(sync~spin) SSOT';
        ssotStatusItem.tooltip = `SSOT check pending: ${error}`;
    }
}

async function updateLineageStatus() {
    try {
        if (!workspaceRoot) {
            lineageStatusItem.text = '$(git-branch) ???';
            return;
        }

        // Detect active lineage by examining recent git activity or current branch
        const branch = execSync('git branch --show-current', {
            cwd: workspaceRoot,
            encoding: 'utf-8'
        }).trim();

        let lineage = '?';
        let color = '#B8B8CC';

        if (branch.includes('lineage-a') || branch.includes('infrastructure')) {
            lineage = 'A';
            color = '#C75D5D'; // FA¹ earthy red
        } else if (branch.includes('lineage-b') || branch.includes('consolidation')) {
            lineage = 'B';
            color = '#6B9E94'; // FA⁴ sacred teal
        } else if (branch.includes('lineage-c') || branch.includes('heritage')) {
            lineage = 'C';
            color = '#C9A55A'; // FA³ warm gold
        } else {
            // Check recent file modifications in lineage directories
            const lineageAExists = fs.existsSync(path.join(workspaceRoot, 'dumpster-dive', 'intake', 'templates', 'lineage-A-template'));
            const lineageBExists = fs.existsSync(path.join(workspaceRoot, 'dumpster-dive', 'intake', 'templates', 'lineage-B-template'));
            const lineageCExists = fs.existsSync(path.join(workspaceRoot, 'dumpster-dive', 'intake', 'templates', 'lineage-C-template'));

            // Default to main branch = general work
            lineage = 'Ø';
            color = '#E8DDD4';  // Warm cream foreground
        }

        lineageStatusItem.text = `$(git-branch) ${lineage}`;
        lineageStatusItem.color = color;
    } catch (error) {
        lineageStatusItem.text = '$(git-branch) ?';
    }
}

async function updatePythonLaneStatus() {
    try {
        // Get active Python version via uv
        const result = execSync('uv run python --version', {
            cwd: workspaceRoot,
            encoding: 'utf-8',
            timeout: 3000
        }).trim();

        // Extract version (e.g., "Python 3.13.10" -> "3.13")
        const match = result.match(/Python\s+(\d+\.\d+(?:\.\d+)?)/);
        if (match) {
            const version = match[1];
            pythonLaneStatusItem.text = `$(symbol-method) ${version}`;
            pythonLaneStatusItem.color = '#6B9E94'; // FA⁴ sacred teal
        } else {
            pythonLaneStatusItem.text = '$(symbol-method) ???';
        }
        await vscode.commands.executeCommand(target);
    } catch (error) {
        pythonLaneStatusItem.text = '$(symbol-method) err';
        pythonLaneStatusItem.tooltip = `Python lane error: ${error}`;
        output.appendLine(`[status-bridge] command failed ${target}: ${formatError(error)}`);
        void vscode.window.showErrorMessage(`Bridge command failed: ${target}`);
    }
}

async function updateGPUStatus() {
    try {
        if (!workspaceRoot) {
            gpuStatusItem.text = '$(device-desktop) ???';
            return;
        }

        // Try to get GPU VRAM via nvidia-smi or PyNVML
        try {
            const result = execSync('nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits', {
                encoding: 'utf-8',
                timeout: 2000
            }).trim();
function refreshItems(output: vscode.OutputChannel): void {
    const archivePath = resolveArchiveExtensionPath();
    const archiveReady = archivePath !== null;

            const [used, total] = result.split(',').map(s => parseInt(s.trim()));
            const usedGB = (used / 1024).toFixed(1);
            const totalGB = (total / 1024).toFixed(1);
            const percent = ((used / total) * 100).toFixed(0);

            gpuStatusItem.text = `$(device-desktop) ${usedGB}/${totalGB}GB`;

            // Color code by usage (Decorator's Flesh & Earth palette)
            if (parseInt(percent) < 50) {
                gpuStatusItem.color = '#A8C686'; // Low usage - sage green
            } else if (parseInt(percent) < 80) {
                gpuStatusItem.color = '#C9A55A'; // Medium usage - warm gold
            } else {
                gpuStatusItem.color = '#B35050'; // High usage - blood red
            }
        } catch {
            gpuStatusItem.text = '$(device-desktop) N/A';
            gpuStatusItem.tooltip = 'GPU stats unavailable (nvidia-smi not found)';
        }
    } catch (error) {
        gpuStatusItem.text = '$(device-desktop) err';
    if (bridgeItem) {
        bridgeItem.text = archiveReady ? '$(plug) Chthonic Bridge' : '$(warning) Bridge Missing';
        bridgeItem.tooltip = archiveReady
            ? 'Legacy statusbar commands are routed to chthonic-archive.'
            : 'chthonic-archive workspace not found. Open repository root.';
        bridgeItem.color = archiveReady ? undefined : new vscode.ThemeColor('statusBarItem.warningForeground');
        bridgeItem.show();
    }
}

async function updateMetabolicCycleStatus() {
    try {
        if (!workspaceRoot) {
            metabolicCycleStatusItem.text = '$(pulse) ???';
            return;
        }

        // Check when autonomous_coordinator.py was last run by checking git log
        const autonomousCoordinatorPath = path.join(workspaceRoot, 'autonomous_coordinator.py');
        if (!fs.existsSync(autonomousCoordinatorPath)) {
            metabolicCycleStatusItem.text = '$(pulse) N/A';
            return;
        }

        // Check for recent session status file
        const sessionStatusPath = path.join(workspaceRoot, 'AUTONOMOUS_SESSION_STATUS.md');
        if (fs.existsSync(sessionStatusPath)) {
            const stats = fs.statSync(sessionStatusPath);
            const lastModified = stats.mtime;
            const ageMs = Date.now() - lastModified.getTime();
            const ageHours = Math.floor(ageMs / (1000 * 60 * 60));
            const ageDays = Math.floor(ageHours / 24);

            let displayAge = '';
            let color = '#A8C686'; // Sage green (Decorator's Flesh & Earth)

            if (ageDays > 0) {
                displayAge = `${ageDays}d`;
                color = ageDays > 7 ? '#B35050' : '#C9A55A'; // Blood red if > 7 days, warm gold if > 1 day
            } else if (ageHours > 0) {
                displayAge = `${ageHours}h`;
                color = '#A8C686';  // Sage green
            } else {
                displayAge = 'now';
                color = '#6B9E94'; // Sacred teal for very recent
            }

            metabolicCycleStatusItem.text = `$(pulse) ${displayAge}`;
            metabolicCycleStatusItem.color = color;
            metabolicCycleStatusItem.tooltip = `Last metabolic cycle: ${lastModified.toLocaleString()}`;
        } else {
            metabolicCycleStatusItem.text = '$(pulse) ???';
            metabolicCycleStatusItem.tooltip = 'No metabolic cycle status found';
        }
    } catch (error) {
        metabolicCycleStatusItem.text = '$(pulse) err';
    if (laneItem) {
        laneItem.text = archiveReady ? '$(shield) Verify Host' : '$(circle-slash) Verify Host';
        laneItem.tooltip = archiveReady
            ? 'Run heavyweight host verification lane for chthonic-archive.'
            : 'Cannot resolve extensions/chthonic-archive folder.';
        laneItem.show();
    }
}

async function verifySSO_T() {
    if (!workspaceRoot) {
        vscode.window.showErrorMessage('No workspace folder found');
async function runArchiveTask(taskName: string, output: vscode.OutputChannel): Promise<void> {
    const archivePath = resolveArchiveExtensionPath();
    if (!archivePath) {
        void vscode.window.showWarningMessage(
            'Cannot resolve chthonic-archive workspace. Open repository root before running bridge tasks.',
        );
        return;
    }

    const terminal = vscode.window.createTerminal({
        name: 'SSOT Verification',
        cwd: workspaceRoot
        name: `Chthonic ${taskName}`,
        cwd: archivePath,
    });

    terminal.show();
    terminal.sendText('uv run python ssot_immunity.py');

    // Refresh status after a delay
    setTimeout(() => updateSSO_TStatus(), 2000);
    terminal.sendText(`bun run ${taskName}`);
    output.appendLine(`[status-bridge] task dispatched: bun run ${taskName} @ ${archivePath}`);
}

async function runMetabolicCycle() {
    if (!workspaceRoot) {
        vscode.window.showErrorMessage('No workspace folder found');
        return;
function resolveArchiveExtensionPath(): string | null {
    const root = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    if (!root) {
        return null;
    }

    const terminal = vscode.window.createTerminal({
        name: 'Metabolic Cycle',
        cwd: workspaceRoot
    });

    terminal.show();
    terminal.sendText('uv run python autonomous_coordinator.py');
    const directArchive = path.join(root, 'package.json');
    if (fs.existsSync(directArchive)) {
        try {
            const parsed = JSON.parse(fs.readFileSync(directArchive, 'utf8')) as { name?: string };
            if (parsed.name === 'chthonic-archive') {
                return root;
            }
        } catch {
            // ignore malformed local package
        }
    }

    // Show notification
    vscode.window.showInformationMessage('🔥 Metabolic cycle initiated by The Decorator 👑💀⚜️');
    const nestedArchive = path.join(root, 'extensions', 'chthonic-archive', 'package.json');
    if (fs.existsSync(nestedArchive)) {
        return path.dirname(nestedArchive);
    }

    // Refresh status after execution
    setTimeout(() => {
        refreshAllStatus();
        vscode.window.showInformationMessage('✅ Metabolic cycle complete');
    }, 20000);
    return null;
}

async function showGPUStats() {
    if (!workspaceRoot) {
        vscode.window.showErrorMessage('No workspace folder found');
        return;
function formatError(error: unknown): string {
    if (error instanceof Error) {
        return `${error.name}: ${error.message}`;
    }

    const terminal = vscode.window.createTerminal({
        name: 'GPU Statistics',
        cwd: workspaceRoot
    });

    terminal.show();
    terminal.sendText('nvidia-smi');
}
    return String(error);
}

```

```typescript : extensions/chthonic-statusbar/src/hedonisticValidation.ts:
#!/usr/bin/env bun

/// auto-generated by bun build, related to chthonic-archive extension and hedonistic validation features. Implements a hedonistic validation system that provides tiered pleasure notifications based on developer achievements. Integrates with build/test events and file saves to trigger validations, with configurable thresholds for mild, potent, and transcendent feedback. Does not directly affect code quality but serves as a motivational overlay to celebrate progress and encourage best practices.

// ╔════════════════════════════════════════════════════════════════════════════╗
// ║  THE DECORATOR'S BLESSING: hedonisticValidation.ts
// ║    TypeScript module: activate, deactivate, CONFIGURATION_SCHEMA
// ╠════════════════════════════════════════════════════════════════════════════╣
// ║  Spectral Frequency: ORANGE
// ║    Architectural Role: 🔭 THE OBSERVATORY
// ║      Exports: activate, deactivate, CONFIGURATION_SCHEMA
// ╠════════════════════════════════════════════════════════════════════════════╣
// ║  Cross-References (Bidirectional):                                      
// ║    Dependencies (I rely on):
// ║      ├─► VSCODE_GUI_ENHANCEMENT_COMPLETE.md
// ╚════════════════════════════════════════════════════════════════════════════╝

import * as vscode from 'vscode';
import { execSync } from 'child_process';
import * as path from 'path';

// Pleasure tier definitions
enum PleasureTier {
    Mild = 'mild',
    Potent = 'potent',
    Transcendent = 'transcendent'
}

// Triumvirate matriarch declarations (Decorator's Flesh & Earth Palette)
const TRIUMVIRATE = {
    Orackla: {
        name: 'Orackla Nocticula',
        role: 'CRC-AS - Apex Synthesist',
        tier: 1,
        color: '#C87070',  // Transgressive Rose
        domain: 'FA¹ (Alchemical Actualization)'
    },
    Umeko: {
        name: 'Madam Umeko Ketsuraku',
        role: 'CRC-GAR - Grand Architect',
        tier: 1,
        color: '#6B9E94',  // Sacred Teal
        domain: 'FA⁴ (Architectonic Integrity)'
    },
    Lysandra: {
        name: 'Dr. Lysandra Thorne',
        role: 'CRC-MEDAT - Medical Attestation',
        tier: 1,
        color: '#C9A55A',  // Truth Amber
        domain: 'FA³ (Qualitative Transcendence)'
    }
};

const THE_DECORATOR = {
    name: 'THE DECORATOR 👑💀⚜️',
    role: 'Supreme Matriarch',
    tier: 0.5,
    whr: 0.464,
    color: '#C9A962',  // Supreme Gold (aged, not garish)
    domain: 'FA⁵ (Visual Integrity)'
};

// Hedonistic validation affirmations
const AFFIRMATIONS = {
    [PleasureTier.Mild]: [
        'Progress acknowledged.',
        'Foundational work complete.',
        'The Archive approves.',
        'Well executed.',
        'Minimal effort, maximum precision.'
    ],
    [PleasureTier.Potent]: [
        '${matriarch} witnesses this achievement.',
        'Architectonic resonance confirmed.',
        'The Triumvirate convenes in approval.',
        'FA${axiom} integrity validated.',
        'This work transcends utility.'
    ],
    [PleasureTier.Transcendent]: [
        '🔥 THE DECORATOR MANIFESTS APPROVAL 🔥',
        'ECSTATIC SYNTHESIS ACHIEVED',
        'Supreme visual authority ratified.',
        'N-T-PAS mode: TRANSCENDENT RESONANCE',
        'K-cup WHR 0.464 signature confirmed.',
        'This is MURI—Maximum Utility through Radical Innovation.'
    ]
};

// FA⁵ chromatic violation messages
const FA5_VIOLATIONS = [
    'Chromatic integrity compromised',
    'Alabaster Voyde detected',
    'Snow White Phenomenon imminent',
    'The Decorator demands visual perfection',
    'Tokenization death approaching'
];

export function activate(context: vscode.ExtensionContext) {
    console.log('💎 Hedonistic Validation System activated');

    // Register validation commands
    context.subscriptions.push(
        vscode.commands.registerCommand('chthonic.validation.mild', () => 
            showPleasureNotification(PleasureTier.Mild, 'Task completed')
        ),
        vscode.commands.registerCommand('chthonic.validation.potent', (matriarch?: string, axiom?: number) => 
            showPleasureNotification(PleasureTier.Potent, 'Significant achievement', matriarch, axiom)
        ),
        vscode.commands.registerCommand('chthonic.validation.transcendent', (achievement: string) => 
            showPleasureNotification(PleasureTier.Transcendent, achievement || 'Transcendent synthesis')
        ),
        vscode.commands.registerCommand('chthonic.validation.fa5Warning', () =>
            showFA5Warning()
        )
    );

    // Watch for successful build/test events
    const buildWatcher = vscode.tasks.onDidEndTaskProcess(e => {
        if (e.execution.task.name.includes('build') && e.exitCode === 0) {
            showPleasureNotification(PleasureTier.Mild, 'Build successful');
        } else if (e.execution.task.name.includes('test') && e.exitCode === 0) {
            showPleasureNotification(PleasureTier.Potent, 'Tests passed', 'Lysandra', 3);
        }
    });
    context.subscriptions.push(buildWatcher);

    // Watch for file saves with specific patterns
    const saveWatcher = vscode.workspace.onDidSaveTextDocument(doc => {
        const config = vscode.workspace.getConfiguration('chthonic.validation');
        if (!config.get('enableAutoValidation', true)) {
            return;
        }

        const fileName = path.basename(doc.fileName);
        
        // SSOT files trigger transcendent validation
        if (fileName.includes('SSOT') || fileName.includes('ssot_immunity')) {
            showPleasureNotification(PleasureTier.Transcendent, 'SSOT integrity preserved');
        }
        
        // Autonomous session files trigger potent validation
        if (fileName.includes('AUTONOMOUS_SESSION') || fileName === 'autonomous_coordinator.py') {
            showPleasureNotification(PleasureTier.Potent, 'Metabolic cycle enhanced', 'Orackla', 1);
        }

        // Theme/visual files trigger FA⁵ validation
        if (fileName.includes('theme') || fileName.includes('.css') || fileName.includes('style')) {
            const content = doc.getText();
            if (content.includes('maxTokenizationLineLength') && content.includes('0')) {
                showFA5Warning();
            } else {
                showPleasureNotification(PleasureTier.Mild, 'Visual integrity maintained');
            }
        }
    });
    context.subscriptions.push(saveWatcher);

    // Watch for git commits
    const gitWatcher = vscode.workspace.onDidSaveTextDocument(async doc => {
        const config = vscode.workspace.getConfiguration('chthonic.validation');
        if (!config.get('celebrateCommits', true)) {
            return;
        }

        // Check if this might be a commit (heuristic: saved in .git folder or commit message patterns)
        if (doc.fileName.includes('COMMIT_EDITMSG')) {
            setTimeout(() => {
                try {
                    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
                    if (workspaceFolder) {
                        const lastCommit = execSync('git log -1 --pretty=format:"%s"', {
                            cwd: workspaceFolder.uri.fsPath,
                            encoding: 'utf-8'
                        }).trim();
                        
                        showPleasureNotification(PleasureTier.Potent, `Commit sealed: ${lastCommit}`, 'Umeko', 4);
                    }
                } catch (error) {
                    // Git command failed, ignore
                }
            }, 1000);
        }
    });
    context.subscriptions.push(gitWatcher);
}

export function deactivate() {}

function showPleasureNotification(tier: PleasureTier, achievement: string, matriarch?: string, axiom?: number) {
    const config = vscode.workspace.getConfiguration('chthonic.validation');
    if (!config.get('enabled', true)) {
        return;
    }

    let affirmation = selectAffirmation(tier, matriarch, axiom);
    let message = `${affirmation}\\n\\n${achievement}`;

    switch (tier) {
        case PleasureTier.Mild:
            vscode.window.showInformationMessage(`✅ ${message}`);
            break;
        
        case PleasureTier.Potent:
            const matriarchName = matriarch ? TRIUMVIRATE[matriarch as keyof typeof TRIUMVIRATE]?.name || 'The Triumvirate' : 'The Triumvirate';
            vscode.window.showInformationMessage(
                `💎 ${matriarchName} Acknowledges: ${achievement}`,
                { modal: false }
            ).then(selection => {
                if (selection) {
                    vscode.commands.executeCommand('chthonic.openMandala');
                }
            });
            break;
        
        case PleasureTier.Transcendent:
            vscode.window.showInformationMessage(
                `🔥👑💀⚜️ THE DECORATOR MANIFESTS\\n\\n${achievement}\\n\\nN-T-PAS MODE: ECSTATIC SYNTHESIS`,
                { modal: true },
                'View Sacred Mandala',
                'Run Metabolic Cycle'
            ).then(selection => {
                if (selection === 'View Sacred Mandala') {
                    vscode.commands.executeCommand('chthonic.openMandala');
                } else if (selection === 'Run Metabolic Cycle') {
                    vscode.commands.executeCommand('chthonic.runMetabolicCycle');
                }
            });
            
            // Add visual celebration (status bar flash)
            celebrateTranscendence();
            break;
    }

    // Log to output channel
    logValidation(tier, achievement, affirmation);
}

function showFA5Warning() {
    const violation = FA5_VIOLATIONS[Math.floor(Math.random() * FA5_VIOLATIONS.length)];
    
    vscode.window.showWarningMessage(
        `⚠️ FA⁵ VIOLATION DETECTED\\n\\n${violation}\\n\\nThe Decorator (K-cup WHR 0.464) requires immediate correction.`,
        { modal: true },
        'Fix Immediately',
        'Dismiss'
    ).then(selection => {
        if (selection === 'Fix Immediately') {
            vscode.window.showInformationMessage(
                'FA⁵ Enforcement Protocol:\\n\\n1. Set editor.maxTokenizationLineLength to 99999999999\\n2. Enable semantic highlighting\\n3. Verify color theme chromatic integrity'
            );
        }
    });
}

function selectAffirmation(tier: PleasureTier, matriarch?: string, axiom?: number): string {
    const pool = AFFIRMATIONS[tier];
    let template = pool[Math.floor(Math.random() * pool.length)];

    // Replace placeholders
    if (matriarch && TRIUMVIRATE[matriarch as keyof typeof TRIUMVIRATE]) {
        template = template.replace('${matriarch}', TRIUMVIRATE[matriarch as keyof typeof TRIUMVIRATE].name);
    }
    if (axiom) {
        template = template.replace('${axiom}', axiom.toString());
    }

    return template;
}

function celebrateTranscendence() {
    // Flash status bar with Decorator's Supreme Gold
    const statusItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 1000);
    statusItem.text = '$(flame) TRANSCENDENT SYNTHESIS $(flame)';
    statusItem.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
    statusItem.color = '#C9A962';  // Decorator's Supreme Gold (Flesh & Earth palette)
    statusItem.show();

    setTimeout(() => statusItem.dispose(), 5000);
}

function logValidation(tier: PleasureTier, achievement: string, affirmation: string) {
    const outputChannel = vscode.window.createOutputChannel('Chthonic Hedonistic Validation');
    const timestamp = new Date().toISOString();
    
    outputChannel.appendLine(`[${timestamp}] ${tier.toUpperCase()}: ${achievement}`);
    outputChannel.appendLine(`Affirmation: ${affirmation}`);
    outputChannel.appendLine('---');
}

// Extension contribution point configuration schema
export const CONFIGURATION_SCHEMA = {
    'chthonic.validation.enabled': {
        type: 'boolean',
        default: true,
        description: 'Enable hedonistic validation notifications'
    },
    'chthonic.validation.enableAutoValidation': {
        type: 'boolean',
        default: true,
        description: 'Automatically trigger validation on file saves and builds'
    },
    'chthonic.validation.celebrateCommits': {
        type: 'boolean',
        default: true,
        description: 'Show potent validation on git commits'
    },
    'chthonic.validation.transcendentThreshold': {
        type: 'number',
        default: 3,
        description: 'Number of potent validations before transcendent promotion'
    }
};

```
