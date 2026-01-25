var B=Object.create;var{getPrototypeOf:R,defineProperty:N,getOwnPropertyNames:W,getOwnPropertyDescriptor:f}=Object,X=Object.prototype.hasOwnProperty;var S=(j,J,z)=>{z=j!=null?B(R(j)):{};let q=J||!j||!j.__esModule?N(z,"default",{value:j,enumerable:!0}):z;for(let E of W(j))if(!X.call(q,E))N(q,E,{get:()=>j[E],enumerable:!0});return q},V=new WeakMap,D=(j)=>{var J=V.get(j),z;if(J)return J;if(J=N({},"__esModule",{value:!0}),j&&typeof j==="object"||typeof j==="function")W(j).map((q)=>!X.call(J,q)&&N(J,q,{get:()=>j[q],enumerable:!(z=f(j,q))||z.enumerable}));return V.set(j,J),J};var G=(j,J)=>{for(var z in J)N(j,z,{get:J[z],enumerable:!0,configurable:!0,set:(q)=>J[z]=()=>q})};var H={};G(H,{deactivate:()=>k,activate:()=>L});module.exports=D(H);var K=S(require("fs")),O=S(require("path")),A=S(require("vscode"));function L(j){console.log("\uD83C\uDF00 Chthonic Mandala Viewer activated"),j.subscriptions.push(A.commands.registerCommand("chthonic.openMandala",()=>{let E=A.window.createWebviewPanel("chthonic.mandala","\uD83C\uDF00 Sacred Mandala - Repository Topology",A.ViewColumn.One,{enableScripts:!0,localResourceRoots:[A.Uri.file(O.join(j.extensionPath,"media"))]});E.webview.html=w(j,E.webview)})),j.subscriptions.push(A.commands.registerCommand("chthonic.openDependencyGraph",()=>{let E=A.window.createWebviewPanel("chthonic.dependencyGraph","\uD83D\uDD17 Dependency Graph",A.ViewColumn.One,{enableScripts:!0,localResourceRoots:[A.Uri.file(O.join(j.extensionPath,"media"))]});E.webview.html=u(j,E.webview)})),j.subscriptions.push(A.commands.registerCommand("chthonic.openHealthReport",()=>{let E=A.window.createWebviewPanel("chthonic.healthReport","\uD83D\uDC8E Health Report",A.ViewColumn.One,{enableScripts:!0});E.webview.html=C()}));let J=new Y;A.window.registerTreeDataProvider("chthonic.mandalaView",J);let z=new Z;A.window.registerTreeDataProvider("chthonic.dependencyView",z);let q=new _;A.window.registerTreeDataProvider("chthonic.healthView",q)}function k(){}function w(j,J){let z=A.workspace.workspaceFolders?.[0];if(!z)return"<html><body><h1>No workspace folder found</h1></body></html>";let q=O.join(z.uri.fsPath,"topology_graph.json");if(!K.existsSync(q))return`<html><body>
            <h1>Sacred Mandala - Topology Not Found</h1>
            <p>Run <code>uv run python scripts/mandala_topology.py</code> to generate topology_graph.json</p>
        </body></html>`;let E=JSON.parse(K.readFileSync(q,"utf-8"));return`<!DOCTYPE html>
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
                <div class="metric-value">${E.metadata.nodes_count.toLocaleString()}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Edges</div>
                <div class="metric-value">${E.metadata.edges_count.toLocaleString()}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Generated</div>
                <div class="metric-value">${new Date(E.metadata.generated).toLocaleDateString()}</div>
            </div>
        </div>

        <div class="prism-bands">
            <h2 style="color: #E066FF;">PRISM Band Distribution</h2>
            ${F(E.nodes)}
        </div>

        <div class="visualization">
            <h2 style="color: #4ECDC4;">Concentric Ring Visualization</h2>
            <p style="color: #B8B8CC;">Force-directed graph rendering coming soon...</p>
            <canvas id="mandalaCanvas" width="800" height="600"></canvas>
        </div>

        <script>
            const topology = ${JSON.stringify(E)};

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
    </html>`}function F(j){let J=["RED","ORANGE","GOLD","BLUE","WHITE"],z={};return J.forEach((q)=>{z[q]=j.filter((E)=>E.prism_band===q)}),J.map((q)=>`
        <div class="band band-${q}">
            <div class="band-header">${q} (${z[q].length} nodes)</div>
            <div class="node-list">
                ${z[q].slice(0,20).map((E)=>`<div>• ${E.path}</div>`).join("")}
                ${z[q].length>20?`<div>... and ${z[q].length-20} more</div>`:""}
            </div>
        </div>
    `).join("")}function u(j,J){let z=A.workspace.workspaceFolders?.[0];if(!z)return"<html><body><h1>No workspace folder found</h1></body></html>";let q=O.join(z.uri.fsPath,"dependency_graph_production.json");if(!K.existsSync(q))return`<html><body>
            <h1>Dependency Graph Not Found</h1>
            <p>dependency_graph_production.json not available</p>
        </body></html>`;let E=JSON.parse(K.readFileSync(q,"utf-8"));return`<!DOCTYPE html>
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
            ${Object.entries(E).slice(0,50).map(([$,U])=>`
                <div class="node">
                    <div class="node-path">${$}</div>
                    <div class="dependencies">
                        ${Array.isArray(U)?U.length:0} dependencies
                    </div>
                </div>
            `).join("")}
        </div>
    </body>
    </html>`}function C(){if(!A.workspace.workspaceFolders?.[0])return"<html><body><h1>No workspace folder found</h1></body></html>";return`<!DOCTYPE html>
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
    </html>`}class Y{getTreeItem(j){return j}getChildren(j){if(!j)return Promise.resolve([new Q("Sacred Geometry","View mandala visualization","chthonic.openMandala"),new Q("Topology Stats","View repository metrics","")]);return Promise.resolve([])}}class Z{getTreeItem(j){return j}getChildren(j){if(!j)return Promise.resolve([new Q("View Graph","Open dependency graph","chthonic.openDependencyGraph")]);return Promise.resolve([])}}class _{getTreeItem(j){return j}getChildren(j){if(!j)return Promise.resolve([new Q("View Report","Open health report","chthonic.openHealthReport")]);return Promise.resolve([])}}class Q extends A.TreeItem{label;tooltip;command;constructor(j,J,z){super(j,A.TreeItemCollapsibleState.None);this.label=j;this.tooltip=J;this.command=z;if(this.tooltip=J,z)this.command={command:z,title:j}}}
