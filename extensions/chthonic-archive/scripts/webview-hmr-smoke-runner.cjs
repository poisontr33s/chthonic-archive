// @SID: EXT_WEBVIEW_HMR_SMOKE_RUNNER_V1
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const vscode = require('vscode');

const SURFACES = {
    stylus: {
        viewId: 'chthonic.stylusView',
        openCommands: ['workbench.view.extension.chthonic-archive', 'chthonic.openStylusInput', 'chthonic.stylusView.focus'],
    },
    loom: {
        viewId: 'chthonic.loomView',
        openCommands: ['workbench.view.extension.chthonic-archive', 'chthonic.loomView.focus'],
    },
    ankh: {
        viewId: 'chthonic.chatView',
        openCommands: ['workbench.view.extension.chthonic-archive', 'chthonic.chatView.focus'],
    },
    abyssal: {
        viewId: 'chthonic.abyssalView',
        openCommands: ['workbench.view.extension.chthonic-archive', 'chthonic.abyssalView.focus'],
    },
};

function parseJsonEnv(name, fallback) {
    const raw = process.env[name];
    if (!raw) {
        return fallback;
    }

    try {
        return JSON.parse(raw);
    } catch (error) {
        throw new Error(`Invalid JSON in ${name}: ${String(error)}`);
    }
}

function delay(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

function withTimeout(promise, label, timeoutMs = 30_000) {
    let timer = null;
    const timeoutPromise = new Promise((_, reject) => {
        timer = setTimeout(() => {
            reject(new Error(`Timed out while executing ${label} after ${timeoutMs}ms`));
        }, timeoutMs);
    });

    return Promise.race([promise, timeoutPromise]).finally(() => {
        if (timer) {
            clearTimeout(timer);
        }
    });
}

async function run() {
    const extensionId = process.env.CHTHONIC_E2E_EXTENSION_ID ?? 'chthonic-archive.chthonic-archive';
    const surfaces = parseJsonEnv('CHTHONIC_WEBVIEW_HMR_SURFACES', ['stylus', 'loom', 'ankh', 'abyssal']);
    const reloadSpy = installReloadSpy();
    const previousSettings = await applyWorkspaceSettings({
        'dev.autoReload': true,
    });

    try {
        const extension = vscode.extensions.getExtension(extensionId);
        assert.ok(extension, `Extension not found: ${extensionId}`);
        await withTimeout(Promise.resolve(extension.activate()), `activate(${extensionId})`);

        const results = [];
        for (const surface of surfaces) {
            assert.ok(SURFACES[surface], `Unknown webview HMR surface: ${surface}`);
            results.push(await runSurfaceProbe(extension.extensionPath, surface));
        }

        const state = await vscode.commands.executeCommand('chthonic.__webviewHmrState');
        assert.equal(state?.lane?.state, 'LIVE', `Expected webviewHmr lane LIVE, got ${JSON.stringify(state?.lane)}`);
        assert.equal(reloadSpy.calls(), 0, 'workbench.action.reloadWindow was invoked during webview HMR smoke');

        const payload = {
            results,
            lane: state?.lane,
            reloadSpyInstalled: reloadSpy.installed,
            reloadWindowCalls: reloadSpy.calls(),
            completedAt: new Date().toISOString(),
        };
        await writeResult(payload);
        console.log(JSON.stringify(payload, null, 2));
    } finally {
        await restoreWorkspaceSettings(previousSettings);
    }
}

async function applyWorkspaceSettings(settings) {
    const target = vscode.workspace.workspaceFolders?.length
        ? vscode.ConfigurationTarget.Workspace
        : vscode.ConfigurationTarget.Global;
    const config = vscode.workspace.getConfiguration('chthonic');
    const previous = [];
    for (const [key, value] of Object.entries(settings)) {
        const section = key.startsWith('chthonic.') ? key.slice('chthonic.'.length) : key;
        previous.push({ section, value: config.inspect(section)?.workspaceValue, target });
        await config.update(section, value, target);
    }
    return previous;
}

async function restoreWorkspaceSettings(previous) {
    const config = vscode.workspace.getConfiguration('chthonic');
    for (const { section, value, target } of previous) {
        await config.update(section, value, target);
    }
}

async function runSurfaceProbe(extensionPath, surface) {
    await openSurface(surface);
    await waitForTrackedSurface(surface);

    const filePath = path.join(extensionPath, 'media', 'views', surface, 'index.html');
    const original = await fs.readFile(filePath, 'utf8');
    const marker = `webview-hmr-${surface}-${Date.now()}`;
    const mutated = injectMarker(original, marker);
    const before = await vscode.commands.executeCommand('chthonic.__webviewHmrState');

    const probe = vscode.commands.executeCommand('chthonic.__webviewHmrProbe', {
        surface,
        marker,
        timeoutMs: 1500,
    });

    try {
        await fs.writeFile(filePath, mutated, 'utf8');
        const result = await withTimeout(Promise.resolve(probe), `webview HMR ${surface}`, 3000);
        assert.ok(
            result.reloadLatencyMs <= 1500,
            `${surface} HMR reload exceeded 1500ms: ${result.reloadLatencyMs}ms`,
        );
        assert.ok(
            result.watchEvents > before.watchEventCount,
            `${surface} HMR did not observe a media/views watcher event`,
        );
        return result;
    } catch (error) {
        const after = await vscode.commands.executeCommand('chthonic.__webviewHmrState');
        throw new Error(
            `${surface} HMR failed: ${error instanceof Error ? error.message : String(error)}; state=${JSON.stringify(after)}`,
        );
    } finally {
        await fs.writeFile(filePath, original, 'utf8');
        await delay(300);
    }
}

async function openSurface(surface) {
    for (const command of SURFACES[surface].openCommands) {
        try {
            await withTimeout(Promise.resolve(vscode.commands.executeCommand(command)), command, 5000);
        } catch (error) {
            if (command.endsWith('.focus')) {
                throw error;
            }
        }
        await delay(150);
    }
}

async function waitForTrackedSurface(surface) {
    const deadline = Date.now() + 5000;
    while (Date.now() < deadline) {
        const state = await vscode.commands.executeCommand('chthonic.__webviewHmrState');
        const tracked = state?.tracked?.find((entry) => entry.surface === surface);
        if (tracked?.count > 0) {
            return;
        }
        await delay(100);
    }
    throw new Error(`Timed out waiting for ${surface} webview tracking`);
}

function injectMarker(html, marker) {
    const comment = `<!-- ${marker} -->`;
    const markerNode = `<meta name="chthonic-hmr-marker" content="${marker}">`;
    if (html.includes('</head>')) {
        return html.replace('</head>', `${markerNode}\n${comment}\n</head>`);
    }
    if (html.includes('</body>')) {
        return html.replace('</body>', `${comment}\n</body>`);
    }
    return `${html}\n${comment}\n`;
}

function installReloadSpy() {
    const original = vscode.commands.executeCommand;
    let reloadCalls = 0;
    try {
        vscode.commands.executeCommand = function patchedExecuteCommand(command, ...args) {
            if (command === 'workbench.action.reloadWindow') {
                reloadCalls += 1;
            }
            return original.call(this, command, ...args);
        };
        return {
            installed: true,
            calls: () => reloadCalls,
        };
    } catch {
        return {
            installed: false,
            calls: () => reloadCalls,
        };
    }
}

async function writeResult(payload) {
    const resultPath = process.env.CHTHONIC_WEBVIEW_HMR_RESULT;
    if (!resultPath) {
        return;
    }
    await fs.mkdir(path.dirname(resultPath), { recursive: true });
    await fs.writeFile(resultPath, `${JSON.stringify(payload, null, 2)}\n`, 'utf8');
}

module.exports = { run };
