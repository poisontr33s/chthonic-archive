import * as path from 'path';
import * as vscode from 'vscode';
import type { EntropyGraphPayload } from './types';
import type { EntropySnapshot } from './entropyWorkerClient';
import { EntropyWorkerClient } from './entropyWorkerClient';

export class AbyssalPaneProvider implements vscode.WebviewViewProvider, vscode.Disposable {
    static readonly viewType = 'chthonic.abyssalView';

    private readonly disposables: vscode.Disposable[] = [];
    private view: vscode.WebviewView | null = null;
    private rootPath: string | null = null;

    constructor(
        private readonly extensionUri: vscode.Uri,
        private readonly workerClient: EntropyWorkerClient,
    ) {
        this.disposables.push(
            this.workerClient.onDidUpdateGraph((graph) => this.postMessage({ type: 'graph', graph })),
            this.workerClient.onDidUpdateSnapshot((snapshot) => this.postMessage({ type: 'snapshot', snapshot })),
        );
    }

    setRootPath(rootPath: string | null): void {
        this.rootPath = rootPath;
    }

    dispose(): void {
        this.disposables.forEach((entry) => entry.dispose());
        this.disposables.length = 0;
    }

    resolveWebviewView(
        webviewView: vscode.WebviewView,
        _context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken,
    ): void {
        this.view = webviewView;
        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this.extensionUri],
        };
        webviewView.webview.html = this.getHtml(webviewView.webview);

        webviewView.webview.onDidReceiveMessage((message: unknown) => {
            this.handleMessage(message);
        });
    }

    private handleMessage(message: unknown): void {
        if (!message || typeof message !== 'object') {
            return;
        }
        const payload = message as { type?: string; path?: string };
        if (!payload.type) {
            return;
        }

        if (payload.type === 'ready') {
            this.postMessage({ type: 'snapshot', snapshot: this.workerClient.getSnapshot() });
            this.workerClient.requestGraph(260);
            return;
        }

        if (payload.type === 'requestGraph') {
            this.workerClient.requestGraph(260);
            return;
        }

        if (payload.type === 'openFile' && payload.path && this.rootPath) {
            const normalizedRelative = path.normalize(payload.path);
            if (normalizedRelative.startsWith('..') || path.isAbsolute(normalizedRelative)) {
                return;
            }
            const absolutePath = path.join(this.rootPath, normalizedRelative);
            const uri = vscode.Uri.file(absolutePath);
            vscode.workspace.openTextDocument(uri).then((document) => {
                vscode.window.showTextDocument(document, { preview: false });
            }, () => {
                vscode.window.showWarningMessage(`Unable to open ${payload.path}`);
            });
        }
    }

    private postMessage(message: { type: string; graph?: EntropyGraphPayload; snapshot?: EntropySnapshot }): void {
        if (!this.view) {
            return;
        }
        this.view.webview.postMessage(message);
    }

    private getHtml(webview: vscode.Webview): string {
        const nonce = createNonce();
        const csp = [
            "default-src 'none'",
            `img-src ${webview.cspSource} data: https:`,
            `style-src ${webview.cspSource} 'unsafe-inline'`,
            `script-src 'nonce-${nonce}' https://cdn.jsdelivr.net`,
        ].join('; ');

        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="${csp}">
    <title>Abyssal Pane</title>
    <style>
        :root {
            --abyss-bg: var(--vscode-editor-background);
            --abyss-panel: var(--vscode-editorWidget-background);
            --abyss-border: var(--vscode-editorWidget-border);
            --abyss-fg: var(--vscode-editor-foreground);
            --abyss-muted: var(--vscode-descriptionForeground);
            --abyss-accent: #c9a962;
        }
        * { box-sizing: border-box; }
        html, body {
            width: 100%;
            height: 100%;
            margin: 0;
            padding: 0;
            background: var(--abyss-bg);
            color: var(--abyss-fg);
            font-family: var(--vscode-font-family, 'Segoe UI', sans-serif);
        }
        body {
            display: grid;
            grid-template-rows: auto auto 1fr;
            gap: 8px;
            padding: 10px;
        }
        .header {
            border: 1px solid var(--abyss-border);
            border-radius: 10px;
            background: var(--abyss-panel);
            padding: 10px;
        }
        .title {
            margin: 0;
            font-size: 13px;
            color: var(--abyss-accent);
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }
        .subtitle {
            margin: 4px 0 0;
            color: var(--abyss-muted);
            font-size: 11px;
        }
        .stats {
            border: 1px solid var(--abyss-border);
            border-radius: 10px;
            background: var(--abyss-panel);
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 8px;
            padding: 8px;
        }
        .stat {
            border: 1px solid var(--abyss-border);
            border-radius: 8px;
            padding: 8px;
            background: rgba(0, 0, 0, 0.08);
        }
        .stat-label {
            color: var(--abyss-muted);
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .stat-value {
            margin-top: 4px;
            font-size: 16px;
            color: var(--abyss-fg);
        }
        .canvas-shell {
            position: relative;
            border: 1px solid var(--abyss-border);
            border-radius: 10px;
            overflow: hidden;
            background: linear-gradient(160deg, rgba(0, 0, 0, 0.14), rgba(0, 0, 0, 0.04));
        }
        #graph {
            width: 100%;
            height: 100%;
            min-height: 360px;
            display: block;
        }
        .legend {
            position: absolute;
            right: 10px;
            top: 10px;
            border: 1px solid var(--abyss-border);
            border-radius: 8px;
            padding: 6px 8px;
            background: color-mix(in srgb, var(--abyss-panel) 90%, transparent);
            font-size: 10px;
            color: var(--abyss-muted);
        }
        .legend-row {
            display: flex;
            align-items: center;
            gap: 6px;
            margin-bottom: 4px;
        }
        .legend-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }
    </style>
</head>
<body>
    <section class="header">
        <h1 class="title">Abyssal Pane · Root System</h1>
        <p class="subtitle">Layout computed off-main-thread, rendered with D3 in webview.</p>
    </section>
    <section class="stats">
        <article class="stat">
            <div class="stat-label">Tracked Files</div>
            <div id="stat-files" class="stat-value">0</div>
        </article>
        <article class="stat">
            <div class="stat-label">Avg Entropy</div>
            <div id="stat-entropy" class="stat-value">0%</div>
        </article>
        <article class="stat">
            <div class="stat-label">Last Scan</div>
            <div id="stat-scan" class="stat-value">n/a</div>
        </article>
    </section>
    <section class="canvas-shell">
        <svg id="graph" role="img" aria-label="Abyssal dependency graph"></svg>
        <div class="legend">
            <div class="legend-row"><span class="legend-dot" style="background:#7cae67"></span>low entropy</div>
            <div class="legend-row"><span class="legend-dot" style="background:#c9a962"></span>medium entropy</div>
            <div class="legend-row"><span class="legend-dot" style="background:#8a4c2a"></span>high entropy</div>
        </div>
    </section>

    <script nonce="${nonce}" src="https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js"></script>
    <script nonce="${nonce}">
        const vscode = acquireVsCodeApi();
        let latestGraph = null;

        const statFiles = document.getElementById('stat-files');
        const statEntropy = document.getElementById('stat-entropy');
        const statScan = document.getElementById('stat-scan');

        function clamp01(value) {
            return Math.max(0, Math.min(1, value));
        }

        function parseCssColor(value) {
            if (!value) return null;
            const raw = value.trim();
            if (raw.startsWith('#')) {
                let hex = raw.slice(1);
                if (hex.length === 3) {
                    hex = hex.split('').map((ch) => ch + ch).join('');
                }
                if (hex.length < 6) return null;
                return [
                    parseInt(hex.slice(0, 2), 16),
                    parseInt(hex.slice(2, 4), 16),
                    parseInt(hex.slice(4, 6), 16),
                ];
            }
            const rgbMatch = raw.match(/rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)/i);
            if (rgbMatch) {
                return [Number(rgbMatch[1]), Number(rgbMatch[2]), Number(rgbMatch[3])];
            }
            return null;
        }

        function mix(a, b, t) {
            return Math.round((a * (1 - t)) + (b * t));
        }

        function toCss(rgb) {
            return 'rgb(' + rgb[0] + ', ' + rgb[1] + ', ' + rgb[2] + ')';
        }

        function sepiaShift(rgb, darkness) {
            const sepia = [112, 93, 68];
            const factor = clamp01((darkness * 0.55) + 0.15);
            return [
                mix(rgb[0], sepia[0], factor),
                mix(rgb[1], sepia[1], factor),
                mix(rgb[2], sepia[2], factor),
            ];
        }

        function darken(rgb, darkness) {
            const factor = 1 - (darkness * 0.28);
            return rgb.map((channel) => Math.round(channel * factor));
        }

        function computeDarkness() {
            const now = new Date();
            const hour = now.getHours() + (now.getMinutes() / 60);
            const daylight = (Math.cos(((hour - 12) / 12) * Math.PI) + 1) / 2;
            return clamp01(1 - daylight);
        }

        function applyCircadianTheme() {
            const css = getComputedStyle(document.documentElement);
            const baseBg = parseCssColor(css.getPropertyValue('--vscode-editor-background')) || [19, 15, 12];
            const basePanel = parseCssColor(css.getPropertyValue('--vscode-editorWidget-background')) || [30, 24, 20];
            const baseFg = parseCssColor(css.getPropertyValue('--vscode-editor-foreground')) || [226, 215, 205];

            const darkness = computeDarkness();
            const shiftedBg = darken(sepiaShift(baseBg, darkness), darkness);
            const shiftedPanel = darken(sepiaShift(basePanel, darkness), darkness * 0.85);
            const shiftedFg = sepiaShift(baseFg, darkness * 0.25);
            const accent = sepiaShift([201, 169, 98], darkness * 0.45);

            document.documentElement.style.setProperty('--abyss-bg', toCss(shiftedBg));
            document.documentElement.style.setProperty('--abyss-panel', toCss(shiftedPanel));
            document.documentElement.style.setProperty('--abyss-fg', toCss(shiftedFg));
            document.documentElement.style.setProperty('--abyss-accent', toCss(accent));
        }

        function entropyColor(entropy) {
            if (entropy >= 0.78) return '#8a4c2a';
            if (entropy >= 0.48) return '#c9a962';
            return '#7cae67';
        }

        function renderGraph(graph) {
            if (!graph || !Array.isArray(graph.nodes)) {
                return;
            }
            if (!window.d3) {
                return;
            }

            latestGraph = graph;
            const svg = d3.select('#graph');
            const width = Math.max(320, svg.node().clientWidth);
            const height = Math.max(240, svg.node().clientHeight);
            svg.attr('viewBox', [0, 0, width, height]);
            svg.selectAll('*').remove();

            const centerX = width / 2;
            const centerY = height / 2;
            const scale = Math.min(width, height) / 980;

            const nodeById = new Map(graph.nodes.map((node) => [node.id, node]));
            const links = graph.edges
                .map((edge) => {
                    const source = nodeById.get(edge.source);
                    const target = nodeById.get(edge.target);
                    if (!source || !target) return null;
                    return { source, target, weight: edge.weight || 1 };
                })
                .filter(Boolean);

            const root = svg.append('g');
            const linkLayer = root.append('g').attr('stroke-linecap', 'round');
            linkLayer.selectAll('line')
                .data(links)
                .enter()
                .append('line')
                .attr('x1', (entry) => centerX + (entry.source.x * scale))
                .attr('y1', (entry) => centerY + (entry.source.y * scale))
                .attr('x2', (entry) => centerX + (entry.target.x * scale))
                .attr('y2', (entry) => centerY + (entry.target.y * scale))
                .attr('stroke', 'var(--abyss-border)')
                .attr('stroke-opacity', 0.35)
                .attr('stroke-width', (entry) => 0.8 + (entry.weight * 0.4));

            const nodes = root.append('g').selectAll('circle')
                .data(graph.nodes)
                .enter()
                .append('circle')
                .attr('cx', (node) => centerX + (node.x * scale))
                .attr('cy', (node) => centerY + (node.y * scale))
                .attr('r', (node) => 2.8 + Math.min(5, node.degree * 0.3))
                .attr('fill', (node) => entropyColor(node.entropy))
                .attr('fill-opacity', 0.92)
                .attr('stroke', 'rgba(0, 0, 0, 0.35)')
                .attr('stroke-width', 0.6)
                .style('cursor', 'pointer');

            nodes.append('title')
                .text((node) => node.label + ' • entropy ' + Math.round(node.entropy * 100) + '%');

            nodes.on('dblclick', (_, node) => {
                vscode.postMessage({ type: 'openFile', path: node.id });
            });
        }

        window.addEventListener('resize', () => {
            if (latestGraph) {
                renderGraph(latestGraph);
            }
        });

        window.addEventListener('message', (event) => {
            const message = event.data;
            if (!message || !message.type) {
                return;
            }
            if (message.type === 'graph') {
                renderGraph(message.graph);
                return;
            }
            if (message.type === 'snapshot' && message.snapshot) {
                const snapshot = message.snapshot;
                statFiles.textContent = String(snapshot.totalFiles || 0);
                statEntropy.textContent = Math.round((snapshot.averageEntropy || 0) * 100) + '%';
                const last = snapshot.lastScanDurationMs
                    ? (snapshot.lastScanDurationMs + 'ms')
                    : 'n/a';
                statScan.textContent = last;
            }
        });

        applyCircadianTheme();
        setInterval(applyCircadianTheme, 60_000);
        vscode.postMessage({ type: 'ready' });
    </script>
</body>
</html>`;
    }
}

function createNonce(): string {
    const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let nonce = '';
    for (let i = 0; i < 32; i += 1) {
        nonce += alphabet.charAt(Math.floor(Math.random() * alphabet.length));
    }
    return nonce;
}
