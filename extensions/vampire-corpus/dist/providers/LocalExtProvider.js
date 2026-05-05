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
exports.LocalExtProvider = void 0;
// @SID: VAMPIRE_CORPUS_LOCAL_EXT_PROVIDER_V1
const vscode = __importStar(require("vscode"));
const fs = __importStar(require("node:fs"));
const path = __importStar(require("node:path"));
const cp = __importStar(require("node:child_process"));
class LocalExtItem extends vscode.TreeItem {
    extInfo;
    constructor(label, collapsible, kind, info = null, opts = {}) {
        super(label, collapsible);
        this.contextValue = kind;
        this.extInfo = info;
        if (opts.description !== undefined)
            this.description = opts.description;
        if (opts.tooltip !== undefined)
            this.tooltip = opts.tooltip;
        if (opts.icon)
            this.iconPath = new vscode.ThemeIcon(opts.icon);
    }
}
// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------
class LocalExtProvider {
    workspaceRoot;
    _onDidChange = new vscode.EventEmitter();
    onDidChangeTreeData = this._onDidChange.event;
    extensions = [];
    scanError = null;
    constructor(workspaceRoot) {
        this.workspaceRoot = workspaceRoot;
        this.scan();
    }
    refresh() {
        this.scan();
        this._onDidChange.fire(undefined);
    }
    scan() {
        const extsDirRel = vscode.workspace.getConfiguration('vampireCorpus').get('extensionsDir') ?? 'extensions';
        const extsDir = path.isAbsolute(extsDirRel)
            ? extsDirRel
            : path.join(this.workspaceRoot, extsDirRel);
        try {
            if (!fs.existsSync(extsDir)) {
                this.extensions = [];
                this.scanError = `extensions dir not found: ${extsDir}`;
                return;
            }
            const installedIds = new Set(vscode.extensions.all.map(e => e.id.toLowerCase()));
            const entries = fs.readdirSync(extsDir, { withFileTypes: true })
                .filter(d => d.isDirectory());
            const results = [];
            for (const entry of entries) {
                const folderPath = path.join(extsDir, entry.name);
                const pkgPath = path.join(folderPath, 'package.json');
                if (!fs.existsSync(pkgPath))
                    continue;
                let manifest;
                try {
                    manifest = JSON.parse(fs.readFileSync(pkgPath, 'utf8'));
                }
                catch {
                    continue;
                }
                // Find most recent .vsix in the folder (if any)
                const vsixFiles = fs.readdirSync(folderPath)
                    .filter(f => f.endsWith('.vsix'))
                    .map(f => ({ name: f, mtime: fs.statSync(path.join(folderPath, f)).mtimeMs }))
                    .sort((a, b) => b.mtime - a.mtime);
                const vsixPath = vsixFiles.length > 0 ? path.join(folderPath, vsixFiles[0].name) : null;
                const publisher = manifest.publisher ?? 'unknown';
                const name = manifest.name ?? entry.name;
                const extensionId = `${publisher}.${name}`.toLowerCase();
                const isInstalled = installedIds.has(extensionId);
                results.push({
                    folderPath,
                    folderName: entry.name,
                    manifest,
                    vsixPath,
                    isInstalled,
                    extensionId,
                });
            }
            this.extensions = results.sort((a, b) => {
                // Installed first
                if (a.isInstalled !== b.isInstalled)
                    return a.isInstalled ? -1 : 1;
                return a.folderName.localeCompare(b.folderName);
            });
            this.scanError = null;
        }
        catch (e) {
            this.extensions = [];
            this.scanError = String(e);
        }
    }
    getTreeItem(element) {
        return element;
    }
    getChildren(element) {
        if (element)
            return [];
        if (this.scanError) {
            return [new LocalExtItem('Scan error', vscode.TreeItemCollapsibleState.None, 'localExt.error', null, {
                    description: this.scanError,
                    icon: 'error',
                })];
        }
        if (this.extensions.length === 0) {
            return [new LocalExtItem('No local extensions found', vscode.TreeItemCollapsibleState.None, 'localExt.error', null, {
                    icon: 'circle-outline',
                })];
        }
        const installed = this.extensions.filter(e => e.isInstalled);
        const notInstalled = this.extensions.filter(e => !e.isInstalled);
        const items = [];
        if (installed.length > 0) {
            const section = new vscode.TreeItem(`Installed (${installed.length})`, vscode.TreeItemCollapsibleState.Expanded);
            section.iconPath = new vscode.ThemeIcon('check');
            section.contextValue = 'localExt.section';
            items.push(section);
            items.push(...installed.map(e => this.makeItem(e)));
        }
        if (notInstalled.length > 0) {
            const section = new vscode.TreeItem(`Not installed (${notInstalled.length})`, vscode.TreeItemCollapsibleState.Expanded);
            section.iconPath = new vscode.ThemeIcon('extensions');
            section.contextValue = 'localExt.section';
            items.push(section);
            items.push(...notInstalled.map(e => this.makeItem(e)));
        }
        return items;
    }
    makeItem(info) {
        const label = info.manifest.displayName ?? info.manifest.name ?? info.folderName;
        const version = info.manifest.version ? `v${info.manifest.version}` : '';
        const kind = info.isInstalled ? 'localExt.installed' : 'localExt.notInstalled';
        const icon = info.isInstalled ? 'extensions' : 'cloud-download';
        const vsixNote = info.vsixPath
            ? `\n\n**VSIX:** ${path.basename(info.vsixPath)}`
            : '\n\n**VSIX:** none — build with `vsce package` or `bun run build` first';
        const tooltip = new vscode.MarkdownString(`**${label}** ${version}\n\n` +
            `ID: \`${info.extensionId}\`\n\n` +
            `${info.manifest.description ?? ''}\n\n` +
            `**Status:** ${info.isInstalled ? '✅ Installed' : '🔷 Not installed'}` +
            vsixNote);
        return new LocalExtItem(label, vscode.TreeItemCollapsibleState.None, kind, info, {
            description: info.isInstalled ? `${version} ✅` : version,
            tooltip,
            icon,
        });
    }
    // ---------------------------------------------------------------------------
    // Commands
    // ---------------------------------------------------------------------------
    async installExt(item) {
        const info = this.extractInfo(item);
        if (!info) {
            void vscode.window.showErrorMessage('Vampire Corpus: cannot determine extension to install.');
            return;
        }
        // Prefer .vsix, fall back to folder install
        const target = info.vsixPath ?? info.folderPath;
        const label = info.manifest.displayName ?? info.folderName;
        const confirmed = await vscode.window.showInformationMessage(`Install local extension "${label}"?`, { modal: false }, 'Install');
        if (confirmed !== 'Install')
            return;
        try {
            await runCodeCommand(['--install-extension', target, '--force']);
            void vscode.window.showInformationMessage(`✅ Installed: ${label}. Reload window to activate.`);
        }
        catch (e) {
            void vscode.window.showErrorMessage(`Install failed: ${String(e)}`);
        }
        this.refresh();
    }
    async uninstallExt(item) {
        const info = this.extractInfo(item);
        if (!info) {
            void vscode.window.showErrorMessage('Vampire Corpus: cannot determine extension to uninstall.');
            return;
        }
        const label = info.manifest.displayName ?? info.folderName;
        const confirmed = await vscode.window.showWarningMessage(`Uninstall "${label}" (${info.extensionId})?`, { modal: false }, 'Uninstall');
        if (confirmed !== 'Uninstall')
            return;
        try {
            await runCodeCommand(['--uninstall-extension', info.extensionId]);
            void vscode.window.showInformationMessage(`Uninstalled: ${label}. Reload to complete.`);
        }
        catch (e) {
            void vscode.window.showErrorMessage(`Uninstall failed: ${String(e)}`);
        }
        this.refresh();
    }
    openFolder(item) {
        const info = this.extractInfo(item);
        if (!info)
            return;
        void vscode.commands.executeCommand('revealFileInOS', vscode.Uri.file(info.folderPath));
    }
    extractInfo(item) {
        if (item instanceof LocalExtItem)
            return item.extInfo;
        return null;
    }
}
exports.LocalExtProvider = LocalExtProvider;
// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function resolveCodeCli() {
    // VS Code exposes `code` or `code-insiders` depending on variant
    // Try to find via VSCODE_GIT_ASKPASS_MAIN env (reliable in extension host)
    const askpass = process.env['VSCODE_GIT_ASKPASS_MAIN'];
    if (askpass) {
        // askpass is at <install>/resources/app/extensions/git/dist/askpass.js
        // code executable is at <install>/bin/code or bin/code-insiders
        const installRoot = path.resolve(askpass, '..', '..', '..', '..', '..', '..', '..');
        for (const name of ['code-insiders.cmd', 'code.cmd', 'code-insiders', 'code']) {
            const candidate = path.join(installRoot, 'bin', name);
            if (fs.existsSync(candidate))
                return candidate;
        }
    }
    // Fall back to PATH
    return process.platform === 'win32' ? 'code-insiders.cmd' : 'code-insiders';
}
async function runCodeCommand(args) {
    const cli = resolveCodeCli();
    return new Promise((resolve, reject) => {
        cp.execFile(cli, args, { timeout: 30_000 }, (err, _stdout, stderr) => {
            if (err) {
                reject(new Error(stderr || err.message));
            }
            else {
                resolve();
            }
        });
    });
}
//# sourceMappingURL=LocalExtProvider.js.map