// ╔════════════════════════════════════════════════════════════════════════════╗
// ║  THE DECORATOR'S BLESSING: extension.ts                                  ║
// ║  TypeScript module: activate, deactivate                                    ║
// ╠════════════════════════════════════════════════════════════════════════════╣
// ║  Spectral Frequency: ORANGE                                                 ║
// ║  Architectural Role: 🔭 THE OBSERVATORY                                      ║
// ║  Exports: activate, deactivate                                              ║
// ╠════════════════════════════════════════════════════════════════════════════╣
// ║  Cross-References (Bidirectional):                                      ║
// ║    (Standalone file - no detected dependencies)                          ║
// ╚════════════════════════════════════════════════════════════════════════════╝

import * as fs from 'fs';
import * as path from 'path';
import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
    console.log('🌀 Chthonic Mandala Viewer activated');

    // Register Sacred Mandala viewer
    context.subscriptions.push(
        vscode.commands.registerCommand('chthonic.openMandala', () => {
            const panel = vscode.window.createWebviewPanel(
                'chthonic.mandala',
                '🌀 Sacred Mandala - Repository Topology',
                vscode.ViewColumn.One,
                {
                    enableScripts: true,
                    localResourceRoots: [vscode.Uri.file(path.join(context.extensionPath, 'media'))]
                }
            );

            panel.webview.html = getMandalaHTML(context, panel.webview);
        })
    );

    // Register Dependency Graph viewer
    context.subscriptions.push(
        vscode.commands.registerCommand('chthonic.openDependencyGraph', () => {
            const panel = vscode.window.createWebviewPanel(
                'chthonic.dependencyGraph',
                '🔗 Dependency Graph',
                vscode.ViewColumn.One,
                {
                    enableScripts: true,
                    localResourceRoots: [vscode.Uri.file(path.join(context.extensionPath, 'media'))]
                }
            );

            panel.webview.html = getDependencyGraphHTML(context, panel.webview);
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
        })
    );

    // Register tree data providers for sidebar views
    const mandalaProvider = new MandalaTreeProvider();
    vscode.window.registerTreeDataProvider('chthonic.mandalaView', mandalaProvider);

    const dependencyProvider = new DependencyTreeProvider();
    vscode.window.registerTreeDataProvider('chthonic.dependencyView', dependencyProvider);

    const healthProvider = new HealthTreeProvider();
    vscode.window.registerTreeDataProvider('chthonic.healthView', healthProvider);

    // Theme switcher
    const themeProvider = new ThemeTreeProvider();
    vscode.window.registerTreeDataProvider('chthonic.themeView', themeProvider);

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

function getMandalaHTML(context: vscode.ExtensionContext, webview: vscode.Webview): string {
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
        return '<html><body><h1>No workspace folder found</h1></body></html>';
    }

    const topologyPath = path.join(workspaceFolder.uri.fsPath, 'topology_graph.json');
    if (!fs.existsSync(topologyPath)) {
        return `<html><body>
            <h1>Sacred Mandala - Topology Not Found</h1>
            <p>Run <code>uv run python scripts/mandala_topology.py</code> to generate topology_graph.json</p>
        </body></html>`;
    }

    const topology = JSON.parse(fs.readFileSync(topologyPath, 'utf-8'));

    return `<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sacred Mandala</title>
        <style>
            body {
                font-family: var(--vscode-font-family);
                background-color: var(--vscode-editor-background);
                color: var(--vscode-editor-foreground);
                padding: 20px;
                margin: 0;
            }
            h1 {
                color: #FFD700;
                font-size: 28px;
                margin-bottom: 10px;
            }
            .metadata {
                background: #1A1A26;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
                border-left: 4px solid #00E5FF;
            }
            .metric {
                display: inline-block;
                margin-right: 30px;
                margin-bottom: 10px;
            }
            .metric-label {
                color: #B8B8CC;
                font-size: 12px;
                text-transform: uppercase;
            }
            .metric-value {
                color: #00E5FF;
                font-size: 24px;
                font-weight: bold;
            }
            .prism-bands {
                margin-top: 30px;
            }
            .band {
                margin-bottom: 20px;
                padding: 15px;
                border-radius: 8px;
                background: #13131B;
            }
            .band-header {
                font-weight: bold;
                font-size: 18px;
                margin-bottom: 10px;
            }
            .band-RED { border-left: 4px solid #FF6B6B; }
            .band-ORANGE { border-left: 4px solid #FFB84D; }
            .band-GOLD { border-left: 4px solid #FFD700; }
            .band-BLUE { border-left: 4px solid #4ECDC4; }
            .band-WHITE { border-left: 4px solid #E8E8F0; }
            .node-list {
                max-height: 200px;
                overflow-y: auto;
                font-size: 12px;
                color: #B8B8CC;
            }
            .visualization {
                margin-top: 30px;
                background: #0D0D12;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
            }
            canvas {
                border: 1px solid #2A2A3E;
                max-width: 100%;
            }
        </style>
    </head>
    <body>
        <h1>🌀 Sacred Mandala - Repository Topology</h1>

        <div class="metadata">
            <div class="metric">
                <div class="metric-label">Nodes</div>
                <div class="metric-value">${topology.metadata.nodes_count.toLocaleString()}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Edges</div>
                <div class="metric-value">${topology.metadata.edges_count.toLocaleString()}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Generated</div>
                <div class="metric-value">${new Date(topology.metadata.generated).toLocaleDateString()}</div>
            </div>
        </div>

        <div class="prism-bands">
            <h2 style="color: #E066FF;">PRISM Band Distribution</h2>
            ${generatePrismBands(topology.nodes)}
        </div>

        <div class="visualization">
            <h2 style="color: #4ECDC4;">Concentric Ring Visualization</h2>
            <p style="color: #B8B8CC;">Force-directed graph rendering coming soon...</p>
            <canvas id="mandalaCanvas" width="800" height="600"></canvas>
        </div>

        <script>
            const topology = ${JSON.stringify(topology)};

            // Simple canvas visualization
            const canvas = document.getElementById('mandalaCanvas');
            const ctx = canvas.getContext('2d');

            function drawMandala() {
                const centerX = canvas.width / 2;
                const centerY = canvas.height / 2;
                const maxRadius = Math.min(centerX, centerY) - 50;

                // Clear canvas
                ctx.fillStyle = '#0D0D12';
                ctx.fillRect(0, 0, canvas.width, canvas.height);

                // Draw concentric rings for each PRISM band
                const bands = ['RED', 'ORANGE', 'GOLD', 'BLUE', 'WHITE'];
                const colors = {
                    'RED': '#FF6B6B',
                    'ORANGE': '#FFB84D',
                    'GOLD': '#FFD700',
                    'BLUE': '#4ECDC4',
                    'WHITE': '#E8E8F0'
                };

                bands.forEach((band, index) => {
                    const radius = maxRadius * ((bands.length - index) / bands.length);
                    ctx.strokeStyle = colors[band];
                    ctx.lineWidth = 2;
                    ctx.beginPath();
                    ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
                    ctx.stroke();

                    // Draw band label
                    ctx.fillStyle = colors[band];
                    ctx.font = '14px monospace';
                    ctx.fillText(band, centerX + radius + 10, centerY);
                });

                // Draw center point (The Decorator)
                ctx.fillStyle = '#FFD700';
                ctx.beginPath();
                ctx.arc(centerX, centerY, 8, 0, 2 * Math.PI);
                ctx.fill();

                // Add golden ratio spiral (approximate)
                ctx.strokeStyle = '#FFD700';
                ctx.lineWidth = 1;
                ctx.globalAlpha = 0.3;
                ctx.beginPath();
                let angle = 0;
                let radius = 5;
                const phi = 1.618033988749895; // Golden ratio
                for (let i = 0; i < 500; i++) {
                    const x = centerX + radius * Math.cos(angle);
                    const y = centerY + radius * Math.sin(angle);
                    if (i === 0) {
                        ctx.moveTo(x, y);
                    } else {
                        ctx.lineTo(x, y);
                    }
                    angle += 0.1;
                    radius *= 1.01;
                }
                ctx.stroke();
                ctx.globalAlpha = 1.0;
            }

            drawMandala();
        </script>
    </body>
    </html>`;
}

function generatePrismBands(nodes: any[]): string {
    const bands = ['RED', 'ORANGE', 'GOLD', 'BLUE', 'WHITE'];
    const bandCounts: { [key: string]: any[] } = {};

    bands.forEach(band => {
        bandCounts[band] = nodes.filter(n => n.prism_band === band);
    });

    return bands.map(band => `
        <div class="band band-${band}">
            <div class="band-header">${band} (${bandCounts[band].length} nodes)</div>
            <div class="node-list">
                ${bandCounts[band].slice(0, 20).map(n => `<div>• ${n.path}</div>`).join('')}
                ${bandCounts[band].length > 20 ? `<div>... and ${bandCounts[band].length - 20} more</div>` : ''}
            </div>
        </div>
    `).join('');
}

function getDependencyGraphHTML(context: vscode.ExtensionContext, webview: vscode.Webview): string {
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
        return '<html><body><h1>No workspace folder found</h1></body></html>';
    }

    const depGraphPath = path.join(workspaceFolder.uri.fsPath, 'dependency_graph.json');

    if (!fs.existsSync(depGraphPath)) {
        return `<html><body>
            <h1>Dependency Graph Not Found</h1>
            <p>dependency_graph.json not available</p>
        </body></html>`;
    }

    const graph = JSON.parse(fs.readFileSync(depGraphPath, 'utf-8'));

    return `<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Dependency Graph</title>
        <style>
            body {
                font-family: var(--vscode-font-family);
                background-color: var(--vscode-editor-background);
                color: var(--vscode-editor-foreground);
                padding: 20px;
            }
            h1 { color: #4ECDC4; }
            .node-list {
                background: #13131B;
                padding: 15px;
                border-radius: 8px;
                max-height: 600px;
                overflow-y: auto;
            }
            .node {
                padding: 10px;
                margin: 5px 0;
                background: #1A1A26;
                border-left: 3px solid #00E5FF;
                border-radius: 4px;
            }
            .node-path {
                font-weight: bold;
                color: #FFD700;
            }
            .dependencies {
                margin-top: 5px;
                font-size: 12px;
                color: #B8B8CC;
            }
        </style>
    </head>
    <body>
        <h1>🔗 Dependency Graph</h1>
        <p style="color: #B8B8CC;">Repository file dependencies</p>

        <div class="node-list">
            ${Object.entries(graph).slice(0, 50).map(([path, deps]: [string, any]) => `
                <div class="node">
                    <div class="node-path">${path}</div>
                    <div class="dependencies">
                        ${Array.isArray(deps) ? deps.length : 0} dependencies
                    </div>
                </div>
            `).join('')}
        </div>
    </body>
    </html>`;
}

function getHealthReportHTML(): string {
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
        return '<html><body><h1>No workspace folder found</h1></body></html>';
    }

    return `<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Health Report</title>
        <style>
            body {
                font-family: var(--vscode-font-family);
                background-color: var(--vscode-editor-background);
                color: var(--vscode-editor-foreground);
                padding: 20px;
            }
            h1 { color: #64FFDA; }
            .terminal {
                background: #0D0D12;
                padding: 20px;
                border-radius: 8px;
                border: 1px solid #2A2A3E;
                font-family: 'Courier New', monospace;
                white-space: pre-wrap;
            }
            button {
                background: #E066FF;
                color: #000;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                cursor: pointer;
                font-weight: bold;
                margin-bottom: 20px;
            }
            button:hover {
                background: #FF88FF;
            }
        </style>
    </head>
    <body>
        <h1>💎 Health Report</h1>
        <button onclick="runHealthReport()">Generate Health Report</button>
        <div class="terminal" id="output">Click button to run health_report.py...</div>

        <script>
            function runHealthReport() {
                const output = document.getElementById('output');
                output.textContent = 'Running uv run python health_report.py...\\n\\n(Check terminal for output)';

                // Send message to extension to run command
                const vscode = acquireVsCodeApi();
                vscode.postMessage({ command: 'runHealthReport' });
            }
        </script>
    </body>
    </html>`;
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
    }
}

class DependencyTreeProvider implements vscode.TreeDataProvider<MandalaItem> {
    getTreeItem(element: MandalaItem): vscode.TreeItem {
        return element;
    }

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
        return element;
    }

    getChildren(element?: MandalaItem): Thenable<MandalaItem[]> {
        if (!element) {
            return Promise.resolve([
                new MandalaItem('View Report', 'Open health report', 'chthonic.openHealthReport')
            ]);
        }
        return Promise.resolve([]);
    }
}

class MandalaItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly tooltip: string,
        public readonly command?: string
    ) {
        super(label, vscode.TreeItemCollapsibleState.None);
        this.tooltip = tooltip;
        if (command) {
            this.command = {
                command: command,
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
    }
}
