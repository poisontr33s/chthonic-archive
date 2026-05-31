#!/usr/bin/env bun

// @SID: EXT_STATUSBAR_LANE_V1
//
// Folded from the former chthonic-statusbar extension (seed kept at
// extensions/chthonic-statusbar). That extension existed only to BRIDGE into
// chthonic-archive from a separate process: it registered chthonic.bridge.*
// commands that forwarded via executeCommand to chthonic.* commands, guarded by
// getCommands() availability probes, "Bridge Missing" status states, and
// resolveArchiveExtensionPath() host discovery.
//
// In-process, that seam dissolves. The forwarders become thin aliases to the
// in-process targets (no probe, no missing-state — the targets are always
// present here). The two status items are dropped: the monolith's own status
// lane (activateStatus) already owns the status-bar surface. What survives net-new
// is the terminal-task launchers (verify:host / audit:vs2026), kept as direct
// commands. Command ids are preserved for keybinding + muscle-memory compat
// (no-delete); only the redundant chrome is shed (compact-with-more).

import * as fs from 'node:fs';
import * as path from 'node:path';
import * as vscode from 'vscode';

// from-id -> in-process target command. Modern routes + legacy aliases collapse
// to the same five targets, all registered in activateCommands.
const FORWARDERS: ReadonlyArray<readonly [string, string]> = [
    ['chthonic.bridge.verifySSOT', 'chthonic.verifySSOT'],
    ['chthonic.bridge.selfHeal', 'chthonic.slabHeal'],
    ['chthonic.bridge.sediment', 'chthonic.reactorSediment'],
    ['chthonic.bridge.webCockpit', 'chthonic.openWebCockpit'],
    ['chthonic.bridge.bunDocs', 'chthonic.openBunTrainingDocs'],
    // legacy aliases (kept for keybindings / muscle memory)
    ['chthonic.verifySSO_T', 'chthonic.verifySSOT'],
    ['chthonic.runMetabolicCycle', 'chthonic.slabHeal'],
    ['chthonic.showGPUStats', 'chthonic.reactorSediment'],
    ['chthonic.openWebCockpitBridge', 'chthonic.openWebCockpit'],
    ['chthonic.openBunTrainingDocsBridge', 'chthonic.openBunTrainingDocs'],
];

// from-id -> bun task. The genuinely additive function statusbar carried.
const TASK_LAUNCHERS: ReadonlyArray<readonly [string, string]> = [
    ['chthonic.bridge.verifyHost', 'verify:host'],
    ['chthonic.bridge.vsAudit', 'audit:vs2026'],
    ['chthonic.runHostVerify', 'verify:host'],   // legacy alias
    ['chthonic.runVsAudit', 'audit:vs2026'],     // legacy alias
];

function resolveArchiveDir(workspaceRoot: string | null): string | null {
    if (!workspaceRoot) return null;
    // Running with the chthonic-archive workspace open: the extension's own
    // package.json (carrying verify:host / audit:vs2026) lives here.
    const nested = path.join(workspaceRoot, 'extensions', 'chthonic-archive', 'package.json');
    if (fs.existsSync(nested)) return path.dirname(nested);
    if (fs.existsSync(path.join(workspaceRoot, 'package.json'))) return workspaceRoot;
    return null;
}

export function registerStatusBridgeLane(
    context: vscode.ExtensionContext,
    output: vscode.OutputChannel,
    workspaceRoot: string | null,
): void {
    for (const [from, to] of FORWARDERS) {
        context.subscriptions.push(
            vscode.commands.registerCommand(from, () => vscode.commands.executeCommand(to)),
        );
    }

    for (const [from, task] of TASK_LAUNCHERS) {
        context.subscriptions.push(
            vscode.commands.registerCommand(from, () => {
                const cwd = resolveArchiveDir(workspaceRoot);
                if (!cwd) {
                    void vscode.window.showWarningMessage(
                        `Cannot resolve chthonic-archive dir to run "${task}". Open the repository root.`,
                    );
                    return;
                }
                const terminal = vscode.window.createTerminal({ name: `Chthonic ${task}`, cwd });
                terminal.show();
                terminal.sendText(`bun run ${task}`);
                output.appendLine(`[statusbar] task dispatched: bun run ${task} @ ${cwd}`);
            }),
        );
    }

    output.appendLine(
        `[statusbar] folded: ${FORWARDERS.length} in-process aliases + ${TASK_LAUNCHERS.length} task launchers; ` +
        `seam dissolved (no cross-extension probe), status items deferred to the status lane`,
    );
}
