"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
// @SID: VAMPIRE_CORPUS_EXTENSION_V1
const vscode = __importStar(require("vscode"));
const CorpusTreeProvider_1 = require("./providers/CorpusTreeProvider");
const TerminalFeedProvider_1 = require("./providers/TerminalFeedProvider");
const LocalExtProvider_1 = require("./providers/LocalExtProvider");
function activate(context) {
    const workspaceRoot = resolveWorkspaceRoot(context);
    if (!workspaceRoot) {
        void vscode.window.showWarningMessage('Vampire Corpus: no workspace folder found — views inactive.');
        return;
    }
    const corpusProvider = new CorpusTreeProvider_1.CorpusTreeProvider(workspaceRoot);
    const terminalFeedProvider = new TerminalFeedProvider_1.TerminalFeedProvider(workspaceRoot);
    const localExtProvider = new LocalExtProvider_1.LocalExtProvider(workspaceRoot);
    // Register tree data providers
    context.subscriptions.push(vscode.window.registerTreeDataProvider('vampire.corpusView', corpusProvider), vscode.window.registerTreeDataProvider('vampire.feedView', terminalFeedProvider), vscode.window.registerTreeDataProvider('vampire.localExtView', localExtProvider));
    // Commands
    context.subscriptions.push(vscode.commands.registerCommand('vampire.refresh', () => {
        corpusProvider.refresh();
        terminalFeedProvider.refresh();
        localExtProvider.refresh();
    }), vscode.commands.registerCommand('vampire.drain', () => runBunTask('vampire:drain', workspaceRoot, 'Vampire Drain')), vscode.commands.registerCommand('vampire.terminalDrain', () => runBunTask('vampire:terminal', workspaceRoot, 'Vampire Terminal Drain')), vscode.commands.registerCommand('vampire.terminalWatch', () => runBunTask('vampire:terminal:watch', workspaceRoot, 'Vampire Terminal Watch')), vscode.commands.registerCommand('vampire.federationValidate', () => runBunTask('vampire:validate', workspaceRoot, 'Vampire Federation Validate')), vscode.commands.registerCommand('vampire.corpusStats', () => runBunTask('session:corpus', workspaceRoot, 'Vampire Corpus Stats')), vscode.commands.registerCommand('vampire.installLocalExt', (item) => localExtProvider.installExt(item)), vscode.commands.registerCommand('vampire.uninstallLocalExt', (item) => localExtProvider.uninstallExt(item)), vscode.commands.registerCommand('vampire.openExtFolder', (item) => localExtProvider.openFolder(item)));
    // File watchers — refresh views when manifest files change
    const corpusWatcher = vscode.workspace.createFileSystemWatcher(new vscode.RelativePattern(workspaceRoot, 'manifest/corpus-state.json'));
    const feedWatcher = vscode.workspace.createFileSystemWatcher(new vscode.RelativePattern(workspaceRoot, 'manifest/terminal_session.jsonl'));
    corpusWatcher.onDidChange(() => corpusProvider.refresh());
    feedWatcher.onDidChange(() => terminalFeedProvider.refresh());
    context.subscriptions.push(corpusWatcher, feedWatcher);
}
function deactivate() {
    // nothing
}
// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function resolveWorkspaceRoot(context) {
    const configOverride = vscode.workspace.getConfiguration('vampireCorpus').get('workspaceRoot');
    if (configOverride && configOverride.trim().length > 0) {
        return configOverride.trim();
    }
    // Prefer the workspace folder that contains a manifest/corpus-state.json
    const folders = vscode.workspace.workspaceFolders;
    if (!folders || folders.length === 0)
        return undefined;
    const { existsSync } = require('node:fs');
    const { join } = require('node:path');
    for (const folder of folders) {
        if (existsSync(join(folder.uri.fsPath, 'manifest', 'corpus-state.json'))) {
            return folder.uri.fsPath;
        }
    }
    // Fall back to first folder
    return folders[0].uri.fsPath;
}
function runBunTask(npmScript, cwd, label) {
    const terminal = vscode.window.createTerminal({
        name: `⚗ ${label}`,
        cwd,
        iconPath: new vscode.ThemeIcon('terminal-bash'),
    });
    terminal.show(true);
    terminal.sendText(`bun run ${npmScript}`);
}
//# sourceMappingURL=extension.js.map