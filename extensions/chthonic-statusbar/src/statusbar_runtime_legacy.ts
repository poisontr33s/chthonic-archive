// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: extension.ts
// ║ TypeScript module: activate, deactivate
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Spectral Frequency: ORANGE
// ║ Architectural Role: 🔭 THE OBSERVATORY
// ║ Exports: activate, deactivate
// ╚════════════════════════════════════════════════════════════════════════════

import * as vscode from 'vscode';
import { execSync, execFile } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';

// Status bar items
let ssotStatusItem: vscode.StatusBarItem;
let lineageStatusItem: vscode.StatusBarItem;
let pythonLaneStatusItem: vscode.StatusBarItem;
let gpuStatusItem: vscode.StatusBarItem;
let metabolicCycleStatusItem: vscode.StatusBarItem;

// Refresh interval timer
let refreshTimer: NodeJS.Timeout;

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

    gpuStatusItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 99);
    gpuStatusItem.command = 'chthonic.showGPUStats';
    gpuStatusItem.tooltip = 'GPU VRAM usage (click for details)';
    context.subscriptions.push(gpuStatusItem);

    pythonLaneStatusItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 98);
    pythonLaneStatusItem.tooltip = 'Python lane version (uv managed)';
    context.subscriptions.push(pythonLaneStatusItem);

    lineageStatusItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 97);
    lineageStatusItem.tooltip = 'Active lineage (A: Infrastructure, B: Consolidation, C: Heritage)';
    context.subscriptions.push(lineageStatusItem);

    ssotStatusItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 96);
    ssotStatusItem.command = 'chthonic.verifySSO_T';
    ssotStatusItem.tooltip = 'SSOT integrity status (click to verify)';
    context.subscriptions.push(ssotStatusItem);

    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('chthonic.refreshStatus', refreshAllStatus),
        vscode.commands.registerCommand('chthonic.verifySSO_T', verifySSO_T),
        vscode.commands.registerCommand('chthonic.runMetabolicCycle', runMetabolicCycle),
        vscode.commands.registerCommand('chthonic.showGPUStats', showGPUStats)
    );

    // Initial status update
    refreshAllStatus();

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
}

export function deactivate() {
    if (refreshTimer) {
        clearInterval(refreshTimer);
    }
}

async function refreshAllStatus() {
    const config = vscode.workspace.getConfiguration('chthonic.statusBar');

    if (!config.get('enabled', true)) {
        hideAllItems();
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
    } catch (error) {
        pythonLaneStatusItem.text = '$(symbol-method) err';
        pythonLaneStatusItem.tooltip = `Python lane error: ${error}`;
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
    }
}

async function verifySSO_T() {
    if (!workspaceRoot) {
        vscode.window.showErrorMessage('No workspace folder found');
        return;
    }

    const terminal = vscode.window.createTerminal({
        name: 'SSOT Verification',
        cwd: workspaceRoot
    });

    terminal.show();
    terminal.sendText('uv run python ssot_immunity.py');

    // Refresh status after a delay
    setTimeout(() => updateSSO_TStatus(), 2000);
}

async function runMetabolicCycle() {
    if (!workspaceRoot) {
        vscode.window.showErrorMessage('No workspace folder found');
        return;
    }

    const terminal = vscode.window.createTerminal({
        name: 'Metabolic Cycle',
        cwd: workspaceRoot
    });

    terminal.show();
    terminal.sendText('uv run python autonomous_coordinator.py');

    // Show notification
    vscode.window.showInformationMessage('🔥 Metabolic cycle initiated by The Decorator 👑💀⚜️');

    // Refresh status after execution
    setTimeout(() => {
        refreshAllStatus();
        vscode.window.showInformationMessage('✅ Metabolic cycle complete');
    }, 20000);
}

async function showGPUStats() {
    if (!workspaceRoot) {
        vscode.window.showErrorMessage('No workspace folder found');
        return;
    }

    const terminal = vscode.window.createTerminal({
        name: 'GPU Statistics',
        cwd: workspaceRoot
    });

    terminal.show();
    terminal.sendText('nvidia-smi');
}
