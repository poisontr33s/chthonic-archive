var S=Object.create;var{getPrototypeOf:b,defineProperty:z,getOwnPropertyNames:k,getOwnPropertyDescriptor:x}=Object,D=Object.prototype.hasOwnProperty;var N=(j,U,J)=>{J=j!=null?S(b(j)):{};let q=U||!j||!j.__esModule?z(J,"default",{value:j,enumerable:!0}):J;for(let K of k(j))if(!D.call(q,K))z(q,K,{get:()=>j[K],enumerable:!0});return q},_=new WeakMap,v=(j)=>{var U=_.get(j),J;if(U)return U;if(U=z({},"__esModule",{value:!0}),j&&typeof j==="object"||typeof j==="function")k(j).map((q)=>!D.call(U,q)&&z(U,q,{get:()=>j[q],enumerable:!(J=x(j,q))||J.enumerable}));return _.set(j,U),U};var P=(j,U)=>{for(var J in U)z(j,J,{get:U[J],enumerable:!0,configurable:!0,set:(q)=>U[J]=()=>q})};var n={};P(n,{deactivate:()=>u,activate:()=>g});module.exports=v(n);var F=require("fs"),A=N(require("path")),B=N(require("child_process")),Q=N(require("vscode"));function g(j){console.log("\uD83C\uDF00 Chthonic Mandala Viewer activated"),j.subscriptions.push(Q.commands.registerCommand("chthonic.openMandala",async()=>{let V=Q.window.createWebviewPanel("chthonic.mandala","\uD83C\uDF00 Sacred Mandala - Repository Topology",Q.ViewColumn.One,{enableScripts:!0,localResourceRoots:[Q.Uri.file(A.join(j.extensionPath,"media"))]});V.webview.html=await m(j,V.webview)})),j.subscriptions.push(Q.commands.registerCommand("chthonic.openDependencyGraph",async()=>{let V=Q.window.createWebviewPanel("chthonic.dependencyGraph","\uD83D\uDD17 Dependency Graph",Q.ViewColumn.One,{enableScripts:!0,localResourceRoots:[Q.Uri.file(A.join(j.extensionPath,"media"))]});V.webview.html=await c(j,V.webview)})),j.subscriptions.push(Q.commands.registerCommand("chthonic.openHealthReport",()=>{let V=Q.window.createWebviewPanel("chthonic.healthReport","\uD83D\uDC8E Health Report",Q.ViewColumn.One,{enableScripts:!0});V.webview.html=p(),V.webview.onDidReceiveMessage(async(Y)=>{if(Y.command!=="runHealthReport")return;let Z=Q.workspace.workspaceFolders?.[0];if(!Z){V.webview.postMessage({type:"healthStatus",running:!1,text:"No workspace folder found."}),V.webview.postMessage({type:"healthOutput",text:"Open a workspace folder before running health diagnostics."});return}V.webview.postMessage({type:"healthStatus",running:!0,text:"Running bun run scripts/health_report.py (uv fallback)..."});let X=await h(Z.uri.fsPath);V.webview.postMessage({type:"healthOutput",text:X.output}),V.webview.postMessage({type:"healthStatus",running:!1,text:X.success?"Health report complete.":"Health report failed."})})}));let U=new T;j.subscriptions.push(Q.window.registerTreeDataProvider("chthonic.mandalaView",U));let J=new I;j.subscriptions.push(Q.window.registerTreeDataProvider("chthonic.dependencyView",J));let q=new M;j.subscriptions.push(Q.window.registerTreeDataProvider("chthonic.healthView",q));let K=new w;j.subscriptions.push(Q.window.registerTreeDataProvider("chthonic.themeView",K)),j.subscriptions.push(Q.commands.registerCommand("chthonic.switchTheme",async()=>{let V=[{label:"$(paintcan) Flesh & Earth",description:"Warm earthy tones — The Decorator's distribution palette",id:"Chthonic Mandala - Flesh & Earth"},{label:"$(zap) ROGBIV",description:"SSOT spectral frequencies — FA¹⁻⁵ canonical hexes",id:"Chthonic Mandala - ROGBIV"}],Y=Q.workspace.getConfiguration("workbench").get("colorTheme"),Z=await Q.window.showQuickPick(V.map((X)=>({...X,picked:Y===X.id})),{placeHolder:`Current: ${Y}`});if(Z)await Q.workspace.getConfiguration("workbench").update("colorTheme",Z.id,Q.ConfigurationTarget.Workspace),Q.window.showInformationMessage(`Theme: ${Z.id}`),K.refresh()}))}function u(){}var E=["RED","ORANGE","GOLD","BLUE","WHITE"],R={RED:"#FF6B6B",ORANGE:"#FFB84D",GOLD:"#FFD700",BLUE:"#4ECDC4",WHITE:"#DADAE6"};async function h(j){let U=[{command:"bun",args:["run","scripts/health_report.py"],label:"bun run scripts/health_report.py"},{command:"uv",args:["run","scripts/health_report.py"],label:"uv run scripts/health_report.py"}],J=[];for(let q of U){let K=await d(q.command,q.args,j),V=[K.stdout.trim(),K.stderr.trim()].filter(Boolean).join(`

`);if(!K.error)return{success:!0,output:V||`${q.label} finished with no output.`};if(J.push(`${q.label}: ${K.error.message}`),K.error.code!=="ENOENT")return{success:!1,output:V?`${V}

Command failed: ${K.error.message}`:`Command failed: ${K.error.message}`}}return{success:!1,output:`No health command available.
${J.join(`
`)}`}}async function m(j,U){let J=Q.workspace.workspaceFolders?.[0];if(!J)return'<html><body style="font-family: sans-serif; padding: 20px;"><h1>No workspace folder found</h1></body></html>';let q=A.join(J.uri.fsPath,"topology_graph.json");if(!await f(q))return`<!DOCTYPE html>
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
</html>`;let K=await l(q),V=H(K.nodes),Y=E.reduce((W,C)=>{return W[C]=V[C].length,W},{}),Z=K.metadata.nodes_count??K.nodes.length,X=K.metadata.edges_count??0,$=K.metadata.generated?new Date(K.metadata.generated).toLocaleString():"Unknown";return`<!DOCTYPE html>
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
                ${i(K.nodes)}
            </div>
        </section>

        <section class="canvas-wrap">
            <h2>Concentric Ring Render</h2>
            <canvas id="mandalaCanvas" width="1040" height="640"></canvas>
            <p class="canvas-meta">Ring thickness and point density scale with band population. Gold center marks The Decorator axis.</p>
        </section>
    </div>

    <script>
        const topology = ${JSON.stringify(K)};
        const bands = ${JSON.stringify(E)};
        const colors = ${JSON.stringify(R)};
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
</html>`}function i(j){let U=H(j),J=Math.max(1,j.length);return E.map((q)=>{let K=U[q],V=(K.length/J*100).toFixed(1),Y=K.slice(0,8).map((X)=>`<li>${G(X.path)}</li>`).join(""),Z=K.length>8?`<li>+ ${K.length-8} more</li>`:"";return`<article class="band-card" style="--band-color:${R[q]}">
    <div class="band-header">
        <span class="name">${q}</span>
        <span class="count">${K.length} · ${V}%</span>
    </div>
    <ol class="band-paths">${Y}${Z}</ol>
</article>`}).join("")}async function c(j,U){let J=Q.workspace.workspaceFolders?.[0];if(!J)return'<html><body style="font-family: sans-serif; padding: 20px;"><h1>No workspace folder found</h1></body></html>';let q=A.join(J.uri.fsPath,"dependency_graph.json");if(!await f(q))return`<!DOCTYPE html>
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
</html>`;let K=await r(q),V=Object.entries(K).sort((X,$)=>$[1].length-X[1].length),Y=V.reduce((X,[,$])=>X+$.length,0),Z=V.slice(0,120);return`<!DOCTYPE html>
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
            ${Z.map(([X,$])=>{let W=$.slice(0,4).map((y)=>`<li>${G(y)}</li>`).join(""),C=$.length>4?`<li>+ ${$.length-4} more</li>`:"";return`<article class="node">
    <div class="node-path">${G(X)}</div>
    <div class="node-meta">${$.length} dependencies</div>
    ${$.length?`<ol class="deps">${W}${C}</ol>`:""}
</article>`}).join("")}
        </section>
    </div>
</body>
</html>`}function p(){if(!Q.workspace.workspaceFolders?.[0])return'<html><body style="font-family: sans-serif; padding: 20px;"><h1>No workspace folder found</h1></body></html>';return`<!DOCTYPE html>
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
    `}function s(j){if(typeof j!=="string")return null;let U=j.toUpperCase();return E.includes(U)?U:null}function H(j){let U={RED:[],ORANGE:[],GOLD:[],BLUE:[],WHITE:[]};for(let J of j){let q=s(J.prism_band);if(q)U[q].push(J)}return U}async function l(j){let U=JSON.parse(await F.promises.readFile(j,"utf-8")),J=Array.isArray(U.nodes)?U.nodes.map((q)=>({path:typeof q.path==="string"?q.path:"(unknown)",prism_band:typeof q.prism_band==="string"?q.prism_band:void 0})):[];return{metadata:U.metadata??{},nodes:J}}async function r(j){let U=JSON.parse(await F.promises.readFile(j,"utf-8")),J={};for(let[q,K]of Object.entries(U))J[q]=Array.isArray(K)?K.filter((V)=>typeof V==="string"):[];return J}function f(j){return F.promises.access(j).then(()=>!0).catch(()=>!1)}function d(j,U,J){return new Promise((q)=>{B.execFile(j,U,{cwd:J,encoding:"utf-8",maxBuffer:10485760},(K,V,Y)=>{q({stdout:V,stderr:Y,error:K})})})}function G(j){return j.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}class T{getTreeItem(j){return j}getChildren(j){if(!j)return Promise.resolve([new L("Sacred Geometry","View mandala visualization","chthonic.openMandala"),new L("Topology Stats","View repository metrics","")]);return Promise.resolve([])}}class I{getTreeItem(j){return j}getChildren(j){if(!j)return Promise.resolve([new L("View Graph","Open dependency graph","chthonic.openDependencyGraph")]);return Promise.resolve([])}}class M{getTreeItem(j){return j}getChildren(j){if(!j)return Promise.resolve([new L("View Report","Open health report","chthonic.openHealthReport")]);return Promise.resolve([])}}class L extends Q.TreeItem{label;tooltipText;constructor(j,U,J){super(j,Q.TreeItemCollapsibleState.None);this.label=j;this.tooltipText=U;if(this.tooltip=U,J)this.command={command:J,title:j}}}class w{_onDidChangeTreeData=new Q.EventEmitter;onDidChangeTreeData=this._onDidChangeTreeData.event;refresh(){this._onDidChangeTreeData.fire()}getTreeItem(j){return j}getChildren(){let j=Q.workspace.getConfiguration("workbench").get("colorTheme")||"";return Promise.resolve([{name:"Chthonic Mandala - Flesh & Earth",icon:"\uD83C\uDF0D",desc:"Warm earth · WCAG AA · Distribution"},{name:"Chthonic Mandala - ROGBIV",icon:"\uD83C\uDF08",desc:"SSOT spectral · FA¹⁻⁵ canonical"}].map((J)=>{let q=j===J.name,K=new Q.TreeItem(`${q?"◉":"○"} ${J.icon} ${J.name.replace("Chthonic Mandala - ","")}`,Q.TreeItemCollapsibleState.None);return K.tooltip=`${J.name}
${J.desc}${q?`

✅ ACTIVE`:""}`,K.description=q?"active":"",K.command={command:"chthonic.switchTheme",title:"Switch Theme"},K}))}}
