const assert = require('node:assert/strict');
const vscode = require('vscode');

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
    const extensionId = process.env.CHTHONIC_E2E_EXTENSION_ID;
    if (!extensionId) {
        throw new Error('Missing CHTHONIC_E2E_EXTENSION_ID');
    }

    const expectedCommands = parseJsonEnv('CHTHONIC_E2E_EXPECTED_COMMANDS', []);
    const smokeCommands = parseJsonEnv('CHTHONIC_E2E_SMOKE_COMMANDS', []);

    const extension = vscode.extensions.getExtension(extensionId);
    assert.ok(extension, `Extension not found: ${extensionId}`);

    await withTimeout(Promise.resolve(extension.activate()), `activate(${extensionId})`);

    const registered = await withTimeout(
        vscode.commands.getCommands(true),
        `getCommands(${extensionId})`,
    );

    for (const command of expectedCommands) {
        assert.ok(
            registered.includes(command),
            `Expected command "${command}" to be registered for ${extensionId}`,
        );
    }

    for (const command of smokeCommands) {
        await withTimeout(
            Promise.resolve(vscode.commands.executeCommand(command)),
            `executeCommand(${command})`,
        );
    }
}

module.exports = { run };
