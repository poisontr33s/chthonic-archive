var y=Object.create;var{getPrototypeOf:S,defineProperty:A,getOwnPropertyNames:_,getOwnPropertyDescriptor:b}=Object,k=Object.prototype.hasOwnProperty;var W=(j,Q,J)=>{J=j!=null?y(S(j)):{};let K=Q||!j||!j.__esModule?A(J,"default",{value:j,enumerable:!0}):J;for(let U of _(j))if(!k.call(K,U))A(K,U,{get:()=>j[U],enumerable:!0});return K},N=new WeakMap,x=(j)=>{var Q=N.get(j),J;if(Q)return Q;if(Q=A({},"__esModule",{value:!0}),j&&typeof j==="object"||typeof j==="function")_(j).map((K)=>!k.call(Q,K)&&A(Q,K,{get:()=>j[K],enumerable:!(J=b(j,K))||J.enumerable}));return N.set(j,Q),Q};var u=(j,Q)=>{for(var J in Q)A(j,J,{get:Q[J],enumerable:!0,configurable:!0,set:(K)=>Q[J]=()=>K})};var r={};u(r,{deactivate:()=>g,activate:()=>P});module.exports=x(r);var z=W(require("fs")),E=W(require("path")),D=W(require("child_process")),q=W(require("vscode"));function P(j){console.log("\uD83C\uDF00 Chthonic Mandala Viewer activated"),j.subscriptions.push(q.commands.registerCommand("chthonic.openMandala",()=>{let V=q.window.createWebviewPanel("chthonic.mandala","\uD83C\uDF00 Sacred Mandala - Repository Topology",q.ViewColumn.One,{enableScripts:!0,localResourceRoots:[q.Uri.file(E.join(j.extensionPath,"media"))]});V.webview.html=h(j,V.webview)})),j.subscriptions.push(q.commands.registerCommand("chthonic.openDependencyGraph",()=>{let V=q.window.createWebviewPanel("chthonic.dependencyGraph","\uD83D\uDD17 Dependency Graph",q.ViewColumn.One,{enableScripts:!0,localResourceRoots:[q.Uri.file(E.join(j.extensionPath,"media"))]});V.webview.html=i(j,V.webview)})),j.subscriptions.push(q.commands.registerCommand("chthonic.openHealthReport",()=>{let V=q.window.createWebviewPanel("chthonic.healthReport","\uD83D\uDC8E Health Report",q.ViewColumn.One,{enableScripts:!0});V.webview.html=c(),V.webview.onDidReceiveMessage(async(Y)=>{if(Y.command!=="runHealthReport")return;let Z=q.workspace.workspaceFolders?.[0];if(!Z){V.webview.postMessage({type:"healthStatus",running:!1,text:"No workspace folder found."}),V.webview.postMessage({type:"healthOutput",text:"Open a workspace folder before running health diagnostics."});return}V.webview.postMessage({type:"healthStatus",running:!0,text:"Running uv run scripts/health_report.py..."});let X=await v(Z.uri.fsPath);V.webview.postMessage({type:"healthOutput",text:X.output}),V.webview.postMessage({type:"healthStatus",running:!1,text:X.success?"Health report complete.":"Health report failed."})})}));let Q=new H;j.subscriptions.push(q.window.registerTreeDataProvider("chthonic.mandalaView",Q));let J=new T;j.subscriptions.push(q.window.registerTreeDataProvider("chthonic.dependencyView",J));let K=new I;j.subscriptions.push(q.window.registerTreeDataProvider("chthonic.healthView",K));let U=new M;j.subscriptions.push(q.window.registerTreeDataProvider("chthonic.themeView",U)),j.subscriptions.push(q.commands.registerCommand("chthonic.switchTheme",async()=>{let V=[{label:"$(paintcan) Flesh & Earth",description:"Warm earthy tones — The Decorator's distribution palette",id:"Chthonic Mandala - Flesh & Earth"},{label:"$(zap) ROGBIV",description:"SSOT spectral frequencies — FA¹⁻⁵ canonical hexes",id:"Chthonic Mandala - ROGBIV"}],Y=q.workspace.getConfiguration("workbench").get("colorTheme"),Z=await q.window.showQuickPick(V.map((X)=>({...X,picked:Y===X.id})),{placeHolder:`Current: ${Y}`});if(Z)await q.workspace.getConfiguration("workbench").update("colorTheme",Z.id,q.ConfigurationTarget.Workspace),q.window.showInformationMessage(`Theme: ${Z.id}`),U.refresh()}))}function g(){}var F=["RED","ORANGE","GOLD","BLUE","WHITE"],B={RED:"#FF6B6B",ORANGE:"#FFB84D",GOLD:"#FFD700",BLUE:"#4ECDC4",WHITE:"#DADAE6"};async function v(j){return await new Promise((Q)=>{D.execFile("uv",["run","scripts/health_report.py"],{cwd:j,encoding:"utf-8",maxBuffer:10485760},(J,K,U)=>{let V=[K.trim(),U.trim()].filter(Boolean).join(`

`);if(J){let Y=`Command failed: ${J.message}`;Q({success:!1,output:V?`${V}

${Y}`:Y});return}Q({success:!0,output:V||"Health report finished with no output."})})})}function h(j,Q){let J=q.workspace.workspaceFolders?.[0];if(!J)return'<html><body style="font-family: sans-serif; padding: 20px;"><h1>No workspace folder found</h1></body></html>';let K=E.join(J.uri.fsPath,"topology_graph.json");if(!z.existsSync(K))return`<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        ${O()}
        .panel { max-width: 840px; margin: 24px auto; text-align: center; }
    </style>
</head>
<body>
    <div class="panel">
        <h1>\uD83C\uDF00 Sacred Mandala - Topology Not Found</h1>
        <p>Generate topology data with <code>uv run scripts/mandala_topology.py</code>.</p>
    </div>
</body>
</html>`;let U=p(K),V=R(U.nodes),Y=F.reduce((C,L)=>{return C[L]=V[L].length,C},{}),Z=U.metadata.nodes_count??U.nodes.length,X=U.metadata.edges_count??0,$=U.metadata.generated?new Date(U.metadata.generated).toLocaleString():"Unknown";return`<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sacred Mandala</title>
    <style>
        ${O()}
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
            <h1>\uD83C\uDF00 Sacred Mandala</h1>
            <p>Repository topology rendered as concentric PRISM rings and sampled node clusters.</p>
        </header>

        <section class="metrics">
            <article class="metric">
                <div class="metric-label">Nodes</div>
                <div class="metric-value">${Z.toLocaleString()}</div>
            </article>
            <article class="metric">
                <div class="metric-label">Edges</div>
                <div class="metric-value">${X.toLocaleString()}</div>
            </article>
            <article class="metric">
                <div class="metric-label">Generated</div>
                <div class="metric-value" style="font-size:15px;">${G($)}</div>
            </article>
        </section>

        <section class="panel">
            <h2>PRISM Band Distribution</h2>
            <div class="band-grid">
                ${m(U.nodes)}
            </div>
        </section>

        <section class="canvas-wrap">
            <h2>Concentric Ring Render</h2>
            <canvas id="mandalaCanvas" width="1040" height="640"></canvas>
            <p class="canvas-meta">Ring thickness and point density scale with band population. Gold center marks The Decorator axis.</p>
        </section>
    </div>

    <script>
        const topology = ${JSON.stringify(U)};
        const bands = ${JSON.stringify(F)};
        const colors = ${JSON.stringify(B)};
        const counts = ${JSON.stringify(Y)};

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
</html>`}function m(j){let Q=R(j),J=Math.max(1,j.length);return F.map((K)=>{let U=Q[K],V=(U.length/J*100).toFixed(1),Y=U.slice(0,8).map((X)=>`<li>${G(X.path)}</li>`).join(""),Z=U.length>8?`<li>+ ${U.length-8} more</li>`:"";return`<article class="band-card" style="--band-color:${B[K]}">
    <div class="band-header">
        <span class="name">${K}</span>
        <span class="count">${U.length} · ${V}%</span>
    </div>
    <ol class="band-paths">${Y}${Z}</ol>
</article>`}).join("")}function i(j,Q){let J=q.workspace.workspaceFolders?.[0];if(!J)return'<html><body style="font-family: sans-serif; padding: 20px;"><h1>No workspace folder found</h1></body></html>';let K=E.join(J.uri.fsPath,"dependency_graph.json");if(!z.existsSync(K))return`<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>${O()}</style>
</head>
<body>
    <div class="panel" style="max-width:840px;margin:24px auto;">
        <h1>\uD83D\uDD17 Dependency Graph Not Found</h1>
        <p>Generate <code>dependency_graph.json</code> to populate this view.</p>
    </div>
</body>
</html>`;let U=l(K),V=Object.entries(U).sort((X,$)=>$[1].length-X[1].length),Y=V.reduce((X,[,$])=>X+$.length,0),Z=V.slice(0,120);return`<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dependency Graph</title>
    <style>
        ${O()}
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
            <h1>\uD83D\uDD17 Dependency Graph</h1>
            <p class="sub">High-fanout files first. Showing ${Z.length} of ${V.length} files.</p>
        </header>

        <section class="metrics">
            <article class="metric">
                <div class="label">Files</div>
                <div class="value">${V.length.toLocaleString()}</div>
            </article>
            <article class="metric">
                <div class="label">Edges</div>
                <div class="value">${Y.toLocaleString()}</div>
            </article>
            <article class="metric">
                <div class="label">Average Degree</div>
                <div class="value">${V.length?(Y/V.length).toFixed(2):"0.00"}</div>
            </article>
        </section>

        <section class="grid">
            ${Z.map(([X,$])=>{let C=$.slice(0,4).map((w)=>`<li>${G(w)}</li>`).join(""),L=$.length>4?`<li>+ ${$.length-4} more</li>`:"";return`<article class="node">
    <div class="node-path">${G(X)}</div>
    <div class="node-meta">${$.length} dependencies</div>
    ${$.length?`<ol class="deps">${C}${L}</ol>`:""}
</article>`}).join("")}
        </section>
    </div>
</body>
</html>`}function c(){if(!q.workspace.workspaceFolders?.[0])return'<html><body style="font-family: sans-serif; padding: 20px;"><h1>No workspace folder found</h1></body></html>';return`<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Health Report</title>
    <style>
        ${O()}
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
        <h1>\uD83D\uDC8E Health Report</h1>
        <p class="sub">Run repository diagnostics using <code>uv run scripts/health_report.py</code>.</p>
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
</html>`}function O(){return`
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
    `}function s(j){if(typeof j!=="string")return null;let Q=j.toUpperCase();return F.includes(Q)?Q:null}function R(j){let Q={RED:[],ORANGE:[],GOLD:[],BLUE:[],WHITE:[]};for(let J of j){let K=s(J.prism_band);if(K)Q[K].push(J)}return Q}function p(j){let Q=JSON.parse(z.readFileSync(j,"utf-8")),J=Array.isArray(Q.nodes)?Q.nodes.map((K)=>({path:typeof K.path==="string"?K.path:"(unknown)",prism_band:typeof K.prism_band==="string"?K.prism_band:void 0})):[];return{metadata:Q.metadata??{},nodes:J}}function l(j){let Q=JSON.parse(z.readFileSync(j,"utf-8")),J={};for(let[K,U]of Object.entries(Q))J[K]=Array.isArray(U)?U.filter((V)=>typeof V==="string"):[];return J}function G(j){return j.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}class H{getTreeItem(j){return j}getChildren(j){if(!j)return Promise.resolve([new f("Sacred Geometry","View mandala visualization","chthonic.openMandala"),new f("Topology Stats","View repository metrics","")]);return Promise.resolve([])}}class T{getTreeItem(j){return j}getChildren(j){if(!j)return Promise.resolve([new f("View Graph","Open dependency graph","chthonic.openDependencyGraph")]);return Promise.resolve([])}}class I{getTreeItem(j){return j}getChildren(j){if(!j)return Promise.resolve([new f("View Report","Open health report","chthonic.openHealthReport")]);return Promise.resolve([])}}class f extends q.TreeItem{label;tooltipText;constructor(j,Q,J){super(j,q.TreeItemCollapsibleState.None);this.label=j;this.tooltipText=Q;if(this.tooltip=Q,J)this.command={command:J,title:j}}}class M{_onDidChangeTreeData=new q.EventEmitter;onDidChangeTreeData=this._onDidChangeTreeData.event;refresh(){this._onDidChangeTreeData.fire()}getTreeItem(j){return j}getChildren(){let j=q.workspace.getConfiguration("workbench").get("colorTheme")||"";return Promise.resolve([{name:"Chthonic Mandala - Flesh & Earth",icon:"\uD83C\uDF0D",desc:"Warm earth · WCAG AA · Distribution"},{name:"Chthonic Mandala - ROGBIV",icon:"\uD83C\uDF08",desc:"SSOT spectral · FA¹⁻⁵ canonical"}].map((J)=>{let K=j===J.name,U=new q.TreeItem(`${K?"◉":"○"} ${J.icon} ${J.name.replace("Chthonic Mandala - ","")}`,q.TreeItemCollapsibleState.None);return U.tooltip=`${J.name}
${J.desc}${K?`

✅ ACTIVE`:""}`,U.description=K?"active":"",U.command={command:"chthonic.switchTheme",title:"Switch Theme"},U}))}}
