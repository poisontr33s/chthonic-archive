var __create = Object.create;
var __getProtoOf = Object.getPrototypeOf;
var __defProp = Object.defineProperty;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __toESM = (mod, isNodeMode, target) => {
  target = mod != null ? __create(__getProtoOf(mod)) : {};
  const to = isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target;
  for (let key of __getOwnPropNames(mod))
    if (!__hasOwnProp.call(to, key))
      __defProp(to, key, {
        get: () => mod[key],
        enumerable: true
      });
  return to;
};
var __moduleCache = /* @__PURE__ */ new WeakMap;
var __toCommonJS = (from) => {
  var entry = __moduleCache.get(from), desc;
  if (entry)
    return entry;
  entry = __defProp({}, "__esModule", { value: true });
  if (from && typeof from === "object" || typeof from === "function")
    __getOwnPropNames(from).map((key) => !__hasOwnProp.call(entry, key) && __defProp(entry, key, {
      get: () => from[key],
      enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable
    }));
  __moduleCache.set(from, entry);
  return entry;
};
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, {
      get: all[name],
      enumerable: true,
      configurable: true,
      set: (newValue) => all[name] = () => newValue
    });
};

// src/extension.ts
var exports_extension = {};
__export(exports_extension, {
  deactivate: () => deactivate,
  activate: () => activate
});
module.exports = __toCommonJS(exports_extension);
var fs = __toESM(require("fs"));
var path = __toESM(require("path"));
var vscode = __toESM(require("vscode"));
function activate(context) {
  console.log("\uD83C\uDF00 Chthonic Mandala Viewer activated");
  context.subscriptions.push(vscode.commands.registerCommand("chthonic.openMandala", () => {
    const panel = vscode.window.createWebviewPanel("chthonic.mandala", "\uD83C\uDF00 Sacred Mandala - Repository Topology", vscode.ViewColumn.One, {
      enableScripts: true,
      localResourceRoots: [vscode.Uri.file(path.join(context.extensionPath, "media"))]
    });
    panel.webview.html = getMandalaHTML(context, panel.webview);
  }));
  context.subscriptions.push(vscode.commands.registerCommand("chthonic.openDependencyGraph", () => {
    const panel = vscode.window.createWebviewPanel("chthonic.dependencyGraph", "\uD83D\uDD17 Dependency Graph", vscode.ViewColumn.One, {
      enableScripts: true,
      localResourceRoots: [vscode.Uri.file(path.join(context.extensionPath, "media"))]
    });
    panel.webview.html = getDependencyGraphHTML(context, panel.webview);
  }));
  context.subscriptions.push(vscode.commands.registerCommand("chthonic.openHealthReport", () => {
    const panel = vscode.window.createWebviewPanel("chthonic.healthReport", "\uD83D\uDC8E Health Report", vscode.ViewColumn.One, {
      enableScripts: true
    });
    panel.webview.html = getHealthReportHTML();
  }));
  const mandalaProvider = new MandalaTreeProvider;
  vscode.window.registerTreeDataProvider("chthonic.mandalaView", mandalaProvider);
  const dependencyProvider = new DependencyTreeProvider;
  vscode.window.registerTreeDataProvider("chthonic.dependencyView", dependencyProvider);
  const healthProvider = new HealthTreeProvider;
  vscode.window.registerTreeDataProvider("chthonic.healthView", healthProvider);
}
function deactivate() {}
function getMandalaHTML(context, webview) {
  const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
  if (!workspaceFolder) {
    return "<html><body><h1>No workspace folder found</h1></body></html>";
  }
  const topologyPath = path.join(workspaceFolder.uri.fsPath, "topology_graph.json");
  if (!fs.existsSync(topologyPath)) {
    return `<html><body>
            <h1>Sacred Mandala - Topology Not Found</h1>
            <p>Run <code>uv run python scripts/mandala_topology.py</code> to generate topology_graph.json</p>
        </body></html>`;
  }
  const topology = JSON.parse(fs.readFileSync(topologyPath, "utf-8"));
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
        <h1>\uD83C\uDF00 Sacred Mandala - Repository Topology</h1>

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
function generatePrismBands(nodes) {
  const bands = ["RED", "ORANGE", "GOLD", "BLUE", "WHITE"];
  const bandCounts = {};
  bands.forEach((band) => {
    bandCounts[band] = nodes.filter((n) => n.prism_band === band);
  });
  return bands.map((band) => `
        <div class="band band-${band}">
            <div class="band-header">${band} (${bandCounts[band].length} nodes)</div>
            <div class="node-list">
                ${bandCounts[band].slice(0, 20).map((n) => `<div>• ${n.path}</div>`).join("")}
                ${bandCounts[band].length > 20 ? `<div>... and ${bandCounts[band].length - 20} more</div>` : ""}
            </div>
        </div>
    `).join("");
}
function getDependencyGraphHTML(context, webview) {
  const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
  if (!workspaceFolder) {
    return "<html><body><h1>No workspace folder found</h1></body></html>";
  }
  const depGraphPath = path.join(workspaceFolder.uri.fsPath, "dependency_graph.json");
  if (!fs.existsSync(depGraphPath)) {
    return `<html><body>
            <h1>Dependency Graph Not Found</h1>
            <p>dependency_graph.json not available</p>
        </body></html>`;
  }
  const graph = JSON.parse(fs.readFileSync(depGraphPath, "utf-8"));
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
        <h1>\uD83D\uDD17 Dependency Graph</h1>
        <p style="color: #B8B8CC;">Repository file dependencies</p>

        <div class="node-list">
            ${Object.entries(graph).slice(0, 50).map(([path2, deps]) => `
                <div class="node">
                    <div class="node-path">${path2}</div>
                    <div class="dependencies">
                        ${Array.isArray(deps) ? deps.length : 0} dependencies
                    </div>
                </div>
            `).join("")}
        </div>
    </body>
    </html>`;
}
function getHealthReportHTML() {
  const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
  if (!workspaceFolder) {
    return "<html><body><h1>No workspace folder found</h1></body></html>";
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
        <h1>\uD83D\uDC8E Health Report</h1>
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

class MandalaTreeProvider {
  getTreeItem(element) {
    return element;
  }
  getChildren(element) {
    if (!element) {
      return Promise.resolve([
        new MandalaItem("Sacred Geometry", "View mandala visualization", "chthonic.openMandala"),
        new MandalaItem("Topology Stats", "View repository metrics", "")
      ]);
    }
    return Promise.resolve([]);
  }
}

class DependencyTreeProvider {
  getTreeItem(element) {
    return element;
  }
  getChildren(element) {
    if (!element) {
      return Promise.resolve([
        new MandalaItem("View Graph", "Open dependency graph", "chthonic.openDependencyGraph")
      ]);
    }
    return Promise.resolve([]);
  }
}

class HealthTreeProvider {
  getTreeItem(element) {
    return element;
  }
  getChildren(element) {
    if (!element) {
      return Promise.resolve([
        new MandalaItem("View Report", "Open health report", "chthonic.openHealthReport")
      ]);
    }
    return Promise.resolve([]);
  }
}

class MandalaItem extends vscode.TreeItem {
  label;
  tooltip;
  command;
  constructor(label, tooltip, command) {
    super(label, vscode.TreeItemCollapsibleState.None);
    this.label = label;
    this.tooltip = tooltip;
    this.command = command;
    this.tooltip = tooltip;
    if (command) {
      this.command = {
        command,
        title: label
      };
    }
  }
}
