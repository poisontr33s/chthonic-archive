// @SID: EXT_DEV_AUTORELOAD_V1
import * as fs from 'node:fs';
import * as path from 'node:path';
import * as vscode from 'vscode';

const DEBOUNCE_MS = 400;

export function registerDevAutoReload(context: vscode.ExtensionContext, output: vscode.OutputChannel): void {
    let watcher: fs.FSWatcher | undefined;
    let pending: NodeJS.Timeout | undefined;
    let lastMtimeMs = 0;

    const distFile = path.join(context.extensionPath, 'dist', 'extension.js');

    const start = (): void => {
        if (watcher) return;
        if (!fs.existsSync(distFile)) {
            output.appendLine(`[dev-reload] watch skipped, missing ${distFile}`);
            return;
        }
        try {
            lastMtimeMs = fs.statSync(distFile).mtimeMs;
            watcher = fs.watch(distFile, () => {
                if (pending) clearTimeout(pending);
                pending = setTimeout(() => {
                    pending = undefined;
                    let mtimeMs: number;
                    try {
                        mtimeMs = fs.statSync(distFile).mtimeMs;
                    } catch {
                        return;
                    }
                    if (mtimeMs === lastMtimeMs) return;
                    lastMtimeMs = mtimeMs;
                    output.appendLine('[dev-reload] dist/extension.js changed, reloading window');
                    void vscode.commands.executeCommand('workbench.action.reloadWindow');
                }, DEBOUNCE_MS);
            });
            output.appendLine(`[dev-reload] watching ${distFile}`);
        } catch (error) {
            output.appendLine(`[dev-reload] watch failed: ${String(error)}`);
        }
    };

    const stop = (): void => {
        if (pending) {
            clearTimeout(pending);
            pending = undefined;
        }
        if (watcher) {
            watcher.close();
            watcher = undefined;
            output.appendLine('[dev-reload] watch stopped');
        }
    };

    const sync = (): void => {
        const enabled = vscode.workspace.getConfiguration('chthonic').get<boolean>('dev.autoReload', false);
        enabled ? start() : stop();
    };

    sync();
    context.subscriptions.push(
        vscode.workspace.onDidChangeConfiguration((event) => {
            if (event.affectsConfiguration('chthonic.dev.autoReload')) {
                sync();
            }
        }),
        { dispose: stop },
    );
}
