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

async function runHealthReportScript(cwd: string): Promise<{ success: boolean; output: string }> {
    const attempts: ReadonlyArray<{
        command: string;
        args: string[];
        label: string;
    }> = [
        { command: 'bun', args: ['run', 'scripts/health_report.py'], label: 'bun run scripts/health_report.py' },
        { command: 'uv', args: ['run', 'scripts/health_report.py'], label: 'uv run scripts/health_report.py' },
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
        public readonly tooltipText: string,
        commandId?: string
    ) {
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
    }
}
