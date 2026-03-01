var Ve=Object.create;var{getPrototypeOf:ze,defineProperty:rt,getOwnPropertyNames:re,getOwnPropertyDescriptor:Fe}=Object,ae=Object.prototype.hasOwnProperty;var c=(t,e,i)=>{i=t!=null?Ve(ze(t)):{};let o=e||!t||!t.__esModule?rt(i,"default",{value:t,enumerable:!0}):i;for(let s of re(t))if(!ae.call(o,s))rt(o,s,{get:()=>t[s],enumerable:!0});return o},ne=new WeakMap,Ie=(t)=>{var e=ne.get(t),i;if(e)return e;if(e=rt({},"__esModule",{value:!0}),t&&typeof t==="object"||typeof t==="function")re(t).map((o)=>!ae.call(e,o)&&rt(e,o,{get:()=>t[o],enumerable:!(i=Fe(t,o))||i.enumerable}));return ne.set(t,e),e};var We=(t,e)=>{for(var i in e)rt(t,i,{get:e[i],enumerable:!0,configurable:!0,set:(o)=>e[i]=()=>o})};var Fi={};We(Fi,{deactivate:()=>Ai,activate:()=>ji});module.exports=Ie(Fi);var n=c(require("vscode")),St=c(require("crypto")),R=c(require("fs")),x=c(require("path"));var at=c(require("path")),K=c(require("vscode")),le=require("worker_threads");class kt{extensionContext;output;records=new Map;recordUris=new Map;onDidUpdateRecordsEmitter=new K.EventEmitter;onDidUpdateRecords=this.onDidUpdateRecordsEmitter.event;onDidUpdateGraphEmitter=new K.EventEmitter;onDidUpdateGraph=this.onDidUpdateGraphEmitter.event;onDidUpdateSnapshotEmitter=new K.EventEmitter;onDidUpdateSnapshot=this.onDidUpdateSnapshotEmitter.event;worker=null;rootPath=null;workerPath;maxFiles=1e4;lastScanDurationMs=0;lastScanAt=0;scanTimer=null;disposed=!1;constructor(t,e){this.extensionContext=t;this.output=e;this.workerPath=t.asAbsolutePath(at.join("dist","entropy-worker.js"))}start(t,e,i){this.rootPath=t,this.maxFiles=e,this.ensureWorker(),this.send({type:"scan",root:t,maxFiles:this.maxFiles}),this.scheduleScanLoop(i)}rescanNow(){if(!this.rootPath)return;this.send({type:"scan",root:this.rootPath,maxFiles:this.maxFiles})}refreshFile(t){if(!this.rootPath||t.scheme!=="file")return;this.send({type:"refresh-file",root:this.rootPath,path:t.fsPath})}requestGraph(t){if(!this.rootPath)return;this.send({type:"graph",limit:t})}getRecord(t){if(!this.rootPath||t.scheme!=="file")return;let e=Ye(at.relative(this.rootPath,t.fsPath));return this.records.get(e)}getSnapshot(t=40){let e=Array.from(this.records.values()),i=e.length===0?0:e.reduce((s,r)=>s+r.entropy,0)/e.length,o=e.sort((s,r)=>r.entropy-s.entropy).slice(0,t);return{totalFiles:e.length,topEntropy:o,averageEntropy:i,lastScanDurationMs:this.lastScanDurationMs,lastScanAt:this.lastScanAt}}dispose(){if(this.disposed=!0,this.scanTimer)clearInterval(this.scanTimer),this.scanTimer=null;this.send({type:"stop"}),this.worker?.terminate(),this.worker=null,this.onDidUpdateRecordsEmitter.dispose(),this.onDidUpdateGraphEmitter.dispose(),this.onDidUpdateSnapshotEmitter.dispose()}scheduleScanLoop(t){if(this.scanTimer)clearInterval(this.scanTimer);let e=Math.max(5000,t);this.scanTimer=setInterval(()=>{if(!this.disposed)this.rescanNow()},e)}ensureWorker(){if(this.worker)return;this.worker=new le.Worker(this.workerPath),this.worker.on("message",(t)=>this.handleWorkerEvent(t)),this.worker.on("error",(t)=>{this.output.appendLine(`[entropy] worker error: ${t.message}`)}),this.worker.on("exit",(t)=>{if(this.output.appendLine(`[entropy] worker exited with code ${t}`),this.worker=null,!this.disposed&&t!==0)this.ensureWorker(),this.rescanNow()})}send(t){this.ensureWorker(),this.worker?.postMessage(t)}handleWorkerEvent(t){switch(t.type){case"scan-progress":{if(!this.rootPath)return;let e=[];for(let i of t.records){this.records.set(i.path,i);let o=this.recordUris.get(i.path);if(!o)o=K.Uri.file(at.join(this.rootPath,i.path)),this.recordUris.set(i.path,o);e.push(o)}if(e.length>0)this.onDidUpdateRecordsEmitter.fire(e);break}case"scan-complete":this.lastScanDurationMs=t.durationMs,this.lastScanAt=Date.now(),this.onDidUpdateSnapshotEmitter.fire(this.getSnapshot());break;case"graph-result":this.onDidUpdateGraphEmitter.fire(t.graph);break;case"error":this.output.appendLine(`[entropy] ${t.message}${t.detail?`
${t.detail}`:""}`);break}}}function Ye(t){return t.replace(/\\/g,"/")}var X=c(require("vscode"));class Ct{workerClient;debounceMs;maxPerFlush;tooltipAugmentProvider;onDidChangeEmitter=new X.EventEmitter;onDidChangeFileDecorations=this.onDidChangeEmitter.event;pending=new Map;flushTimer=null;constructor(t,e,i,o){this.workerClient=t;this.debounceMs=e;this.maxPerFlush=i;this.tooltipAugmentProvider=o;this.workerClient.onDidUpdateRecords((s)=>this.enqueueUpdates(s))}dispose(){if(this.flushTimer)clearTimeout(this.flushTimer),this.flushTimer=null;this.onDidChangeEmitter.dispose()}updateConfig(t,e){this.debounceMs=Math.max(30,t),this.maxPerFlush=Math.max(64,e)}provideFileDecoration(t){if(t.scheme!=="file")return;let e=this.workerClient.getRecord(t);if(!e)return;let i=we(e),o=[`Entropy ${(e.entropy*100).toFixed(0)}%`,`Complexity ${e.complexity}`,`Debt ${e.debt}`,`Freshness ${(e.freshness*100).toFixed(0)}%`];if(this.tooltipAugmentProvider)o.push(...this.tooltipAugmentProvider(t));return{color:i,tooltip:o.join(`
`),propagate:!1}}enqueueExternalUpdates(t){this.enqueueUpdates(t)}enqueueUpdates(t){for(let e of t)this.pending.set(e.toString(),e);if(!this.flushTimer)this.flushTimer=setTimeout(()=>this.flush(),this.debounceMs)}flush(){if(this.flushTimer=null,this.pending.size===0)return;let t=Array.from(this.pending.values()).slice(0,this.maxPerFlush);for(let e of t)this.pending.delete(e.toString());if(this.onDidChangeEmitter.fire(t),this.pending.size>0)this.flushTimer=setTimeout(()=>this.flush(),this.debounceMs)}}function we(t){let e=Ke(t.entropy*0.78+(1-t.freshness)*0.22);if(e>=0.72)return new X.ThemeColor("problemsErrorIcon.foreground");if(e>=0.45)return new X.ThemeColor("charts.yellow");return new X.ThemeColor("charts.green")}function Ke(t){if(t<0)return 0;if(t>1)return 1;return t}var Z=c(require("path")),L=c(require("vscode"));class pt{extensionUri;workerClient;static viewType="chthonic.abyssalView";disposables=[];view=null;rootPath=null;constructor(t,e){this.extensionUri=t;this.workerClient=e;this.disposables.push(this.workerClient.onDidUpdateGraph((i)=>this.postMessage({type:"graph",graph:i})),this.workerClient.onDidUpdateSnapshot((i)=>this.postMessage({type:"snapshot",snapshot:i})))}setRootPath(t){this.rootPath=t}dispose(){this.disposables.forEach((t)=>t.dispose()),this.disposables.length=0}resolveWebviewView(t,e,i){this.view=t,t.webview.options={enableScripts:!0,localResourceRoots:[this.extensionUri]},t.webview.html=this.getHtml(t.webview),t.webview.onDidReceiveMessage((o)=>{this.handleMessage(o)})}handleMessage(t){if(!t||typeof t!=="object")return;let e=t;if(!e.type)return;if(e.type==="ready"){this.postMessage({type:"snapshot",snapshot:this.workerClient.getSnapshot()}),this.workerClient.requestGraph(260);return}if(e.type==="requestGraph"){this.workerClient.requestGraph(260);return}if(e.type==="requestScan"||e.type==="requestSediment"){this.workerClient.rescanNow(),this.workerClient.requestGraph(260);return}if(e.type==="openFile"&&e.path&&this.rootPath){let i=Z.normalize(e.path);if(i.startsWith("..")||Z.isAbsolute(i))return;let o=Z.join(this.rootPath,i),s=L.Uri.file(o);L.workspace.openTextDocument(s).then((r)=>{L.window.showTextDocument(r,{preview:!1})},()=>{L.window.showWarningMessage(`Unable to open ${e.path}`)})}}postMessage(t){if(!this.view)return;this.view.webview.postMessage(t)}getHtml(t){let e=Xe(),i=t.asWebviewUri(L.Uri.joinPath(this.extensionUri,"media","abyssalPane.js")),o=t.asWebviewUri(L.Uri.joinPath(this.extensionUri,"media","wasm","pkg","entropy_renderer_wasm.js")),s=t.asWebviewUri(L.Uri.joinPath(this.extensionUri,"media","wasm","pkg","entropy_renderer_wasm_bg.wasm")),r=t.asWebviewUri(L.Uri.joinPath(this.extensionUri,"media","wasm","pkg","chthonic_loom.js")),l=t.asWebviewUri(L.Uri.joinPath(this.extensionUri,"media","wasm","pkg","chthonic_loom_bg.wasm")),h=["default-src 'none'",`img-src ${t.cspSource} data:`,`style-src ${t.cspSource} 'unsafe-inline'`,`script-src 'nonce-${e}' ${t.cspSource}`,`connect-src ${t.cspSource}`].join("; "),d=JSON.stringify({wasmModuleUri:o.toString(),wasmBinaryUri:s.toString(),loomWasmModuleUri:r.toString(),loomWasmBinaryUri:l.toString()});return`<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="${h}">
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
            font-size: 14px;
            color: var(--abyss-fg);
        }
        .canvas-shell {
            position: relative;
            border: 1px solid var(--abyss-border);
            border-radius: 10px;
            overflow: hidden;
            background: linear-gradient(160deg, rgba(0, 0, 0, 0.14), rgba(0, 0, 0, 0.04));
        }
        #graph-canvas {
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
        <p class="subtitle">Live workspace-health stream from the worker (snapshot + dependency graph).</p>
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
            <div class="stat-label">Render Mode</div>
            <div id="stat-renderer" class="stat-value">booting</div>
        </article>
    </section>
    <section class="canvas-shell">
        <canvas id="graph-canvas" aria-label="Abyssal dependency graph"></canvas>
        <div class="legend">
            <div class="legend-row"><span class="legend-dot" style="background:#7cae67"></span>low entropy</div>
            <div class="legend-row"><span class="legend-dot" style="background:#c9a962"></span>medium entropy</div>
            <div class="legend-row"><span class="legend-dot" style="background:#8a4c2a"></span>high entropy</div>
        </div>
    </section>

    <script nonce="${e}">
        window.__CHTHONIC_ABYSSAL__ = ${d};
    </script>
    <script nonce="${e}" type="module" src="${i}"></script>
</body>
</html>`}}function Xe(){let e="";for(let i=0;i<32;i+=1)e+="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789".charAt(Math.floor(Math.random()*62));return e}var Mt=c(require("fs/promises")),C=c(require("path")),qt=c(require("vscode"));var he=c(require("crypto"));class Dt{leaves=new Map;dirty=!1;upsert(t){let e=ti(t.path),i=Ze(e,t);if(this.leaves.get(e)!==i)return this.leaves.set(e,i),this.dirty=!0,!0;return!1}hasDirty(){return this.dirty}settle(t){if(!this.dirty||this.leaves.size===0)return null;let e=Qe(Array.from(this.leaves.entries()).sort((i,o)=>i[0].localeCompare(o[0])));return this.dirty=!1,{reason:t,rootHash:e,leafCount:this.leaves.size,generatedAt:Date.now()}}}function Ze(t,e){let i=[t,e.entropy.toFixed(6),e.complexity,e.debt,e.freshness.toFixed(6),e.ruffViolations,e.updatedAt].join("|");return ut(i)}function Qe(t){if(t.length===0)return ut("EMPTY");let e=t.map(([i,o])=>ut(`${i}:${o}`));while(e.length>1){let i=[];for(let o=0;o<e.length;o+=2){let s=e[o],r=e[o+1]??e[o];i.push(ut(`${s}${r}`))}e=i}return e[0]}function ut(t){return he.createHash("sha256").update(t,"utf8").digest("hex")}function ti(t){return t.replace(/\\/g,"/")}var F=c(require("fs")),E=c(require("path")),Tt=require("child_process"),ft=c(require("vscode"));function z(t,e){let i="",o=(s)=>{let r=s.trim();if(!r)return;try{let l=JSON.parse(r);if(!l||typeof l!=="object"||Array.isArray(l))throw Error("JSONL payload must be an object");t(l)}catch(l){e(l instanceof Error?l:Error(String(l)))}};return{push(s){i+=s.toString();while(!0){let r=i.indexOf(`
`);if(r<0)return;let l=i.slice(0,r);i=i.slice(r+1),o(l)}},flush(){if(!i.trim()){i="";return}o(i),i=""}}}var __dirname="C:\\Users\\erdno\\chthonic-archive\\extensions\\chthonic-archive\\src\\polyglot";class Bt{output;rootPath=null;sidecarRootPath=null;pythonSidecar=null;rubySidecar=null;onDidReceiveRuffEmitter=new ft.EventEmitter;onDidReceiveRuff=this.onDidReceiveRuffEmitter.event;onDidReceiveLoreEmitter=new ft.EventEmitter;onDidReceiveLore=this.onDidReceiveLoreEmitter.event;onDidReceiveSidecarErrorEmitter=new ft.EventEmitter;onDidReceiveSidecarError=this.onDidReceiveSidecarErrorEmitter.event;constructor(t){this.output=t}start(t){if(this.rootPath=t,this.sidecarRootPath=ii(t),!this.sidecarRootPath){let i=`sidecar scripts not found. checked: ${de(t).join(", ")}`;this.output.appendLine(`[polyglot] ${i}`),this.fireSidecarError("python",i),this.fireSidecarError("ruby",i);return}this.output.appendLine(`[polyglot] sidecar root: ${this.sidecarRootPath}`),this.startPythonSidecar(),this.startRubySidecar()}requestScan(t){if(!this.pythonSidecar||this.pythonSidecar.killed)this.startPythonSidecar();this.writeJson(this.pythonSidecar,t)}requestLore(t){if(!this.rubySidecar||this.rubySidecar.killed)this.startRubySidecar();this.writeJson(this.rubySidecar,t)}dispose(){this.pythonSidecar?.kill(),this.rubySidecar?.kill(),this.pythonSidecar=null,this.rubySidecar=null,this.sidecarRootPath=null,this.onDidReceiveRuffEmitter.dispose(),this.onDidReceiveLoreEmitter.dispose(),this.onDidReceiveSidecarErrorEmitter.dispose()}startPythonSidecar(){if(!this.rootPath||this.pythonSidecar)return;if(!this.sidecarRootPath){this.fireSidecarError("python","sidecar root unresolved; python scan unavailable.");return}let t=E.join(this.sidecarRootPath,"python","entropy_scan.py");if(!F.existsSync(t)){this.fireSidecarError("python",`python sidecar missing: ${t}`);return}let e=E.join(this.sidecarRootPath,"venv",process.platform==="win32"?"Scripts":"bin"),i=E.join(e,process.platform==="win32"?"python.exe":"python"),o=F.existsSync(i),s=o?i:"uv",r=o?[t,"--stdio"]:["run",t,"--stdio"];if(!o)this.output.appendLine("[polyglot:python] .chthonic/venv not found, falling back to uv run.");this.pythonSidecar=Tt.spawn(s,r,{cwd:this.rootPath,stdio:["pipe","pipe","pipe"],env:oi(process.env,e)});let l=z((h)=>this.handlePythonPayload(h),(h)=>this.output.appendLine(`[polyglot:python] invalid JSONL payload: ${h.message}`));this.pythonSidecar.stdout?.on("data",(h)=>l.push(h)),this.pythonSidecar.stderr?.on("data",(h)=>{this.output.appendLine(`[polyglot:python] ${h.toString().trimEnd()}`)}),this.pythonSidecar.on("error",(h)=>{this.fireSidecarError("python",`failed to spawn: ${h.message}`),this.pythonSidecar=null}),this.pythonSidecar.on("exit",(h)=>{l.flush(),this.output.appendLine(`[polyglot:python] exited with code ${h??-1}`),this.pythonSidecar=null})}startRubySidecar(){if(!this.rootPath||this.rubySidecar)return;if(!this.sidecarRootPath){this.fireSidecarError("ruby","sidecar root unresolved; lore unavailable.");return}let t=E.join(this.sidecarRootPath,"ruby","lore.rb");if(!F.existsSync(t)){this.fireSidecarError("ruby",`ruby sidecar missing: ${t}`);return}this.rubySidecar=Tt.spawn("ruby",[t],{cwd:this.rootPath,stdio:["pipe","pipe","pipe"]});let e=z((i)=>this.handleRubyPayload(i),(i)=>this.output.appendLine(`[polyglot:ruby] invalid JSONL payload: ${i.message}`));this.rubySidecar.stdout?.on("data",(i)=>e.push(i)),this.rubySidecar.stderr?.on("data",(i)=>{this.output.appendLine(`[polyglot:ruby] ${i.toString().trimEnd()}`)}),this.rubySidecar.on("error",(i)=>{this.fireSidecarError("ruby",`failed to spawn: ${i.message}`),this.rubySidecar=null}),this.rubySidecar.on("exit",(i)=>{e.flush(),this.output.appendLine(`[polyglot:ruby] exited with code ${i??-1}`),this.rubySidecar=null})}writeJson(t,e){if(!t?.stdin||t.killed)return;try{t.stdin.write(`${JSON.stringify(e)}
`)}catch(i){this.output.appendLine(`[polyglot] sidecar write failed: ${ei(i)}`)}}fireSidecarError(t,e){this.onDidReceiveSidecarErrorEmitter.fire({type:"error",source:t,message:e}),this.output.appendLine(`[polyglot:${t}] ${e}`)}handlePythonPayload(t){if(t.type==="ruff-summary"){let e=t;this.onDidReceiveRuffEmitter.fire(e);return}if(t.type==="error"){let e=String(t.message??"python sidecar error");this.output.appendLine(`[polyglot:python] ${e}`),this.onDidReceiveSidecarErrorEmitter.fire({type:"error",source:"python",message:e})}}handleRubyPayload(t){if(t.type==="lore"){this.onDidReceiveLoreEmitter.fire(t);return}if(t.type==="error"){let e=String(t.message??"ruby sidecar error");this.output.appendLine(`[polyglot:ruby] ${e}`),this.onDidReceiveSidecarErrorEmitter.fire({type:"error",source:"ruby",message:e})}}}function ei(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}function ii(t){for(let e of de(t))if(F.existsSync(E.join(e,"python","entropy_scan.py"))&&F.existsSync(E.join(e,"ruby","lore.rb")))return e;return null}function de(t){let e=[E.join(t,".chthonic"),E.join(t,"extensions","chthonic-archive",".chthonic"),E.resolve(__dirname,"..",".chthonic")];return Array.from(new Set(e))}function oi(t,e){if(!F.existsSync(e))return t;let i=process.platform==="win32"?"Path":"PATH",o=t[i]??process.env[i]??"";return{...t,[i]:o?`${e}${E.delimiter}${o}`:e}}var ce=c(require("fs")),mt=c(require("fs/promises")),q=c(require("path")),_t=require("child_process");class jt{output;rootPath=null;options={rpcUrl:"http://127.0.0.1:8899",autostartValidator:!1};ledgerFilePath=null;validatorProcess=null;hostProcess=null;requestCounter=1;pending=new Map;constructor(t){this.output=t}async start(t,e){this.rootPath=t,this.options=e;let i=q.join(t,".chthonic","ledger");if(await mt.mkdir(i,{recursive:!0}),this.ledgerFilePath=q.join(i,"entropy-settlements.jsonl"),e.autostartValidator)this.startValidator();this.startHostProcess()}async commitEntropy(t){if(!this.rootPath||!this.ledgerFilePath)return{mode:"offline",detail:"Ledger host not started"};let e={...t,rpcUrl:this.options.rpcUrl,recordedAt:Date.now()},i={mode:"offline",detail:"Rust ledger host unavailable; persisted settlement locally."};try{i=await this.submitToHost(t)}catch(o){this.output.appendLine(`[ledger-rust] submit failed: ${ai(o)}`)}return await mt.appendFile(this.ledgerFilePath,`${JSON.stringify({...e,receipt:i})}
`,"utf8"),i}dispose(){for(let[t,e]of this.pending)e.reject(Error(`request ${t} cancelled`));this.pending.clear(),this.hostProcess?.kill(),this.hostProcess=null,this.validatorProcess?.kill(),this.validatorProcess=null}startHostProcess(){if(!this.rootPath||this.hostProcess)return;let t=si(this.rootPath,this.options.hostBinaryPath),e=this.options.walletPath??q.join(this.rootPath,".chthonic","wallets","payer.json"),i=this.options.idlPath??q.join(this.rootPath,".chthonic","wallets","entropy_ledger.json");this.hostProcess=_t.spawn(t,["--wallet",e,"--idl",i,"--rpc-url",this.options.rpcUrl],{cwd:this.rootPath,stdio:["pipe","pipe","pipe"]});let o=z((s)=>this.handleHostPayload(s),(s)=>this.output.appendLine(`[ledger-rust] invalid JSON payload: ${s.message}`));this.hostProcess.stdout?.on("data",(s)=>o.push(s)),this.hostProcess.stderr?.on("data",(s)=>{this.output.appendLine(`[ledger-rust] ${s.toString().trimEnd()}`)}),this.hostProcess.on("error",(s)=>{this.output.appendLine(`[ledger-rust] failed to spawn host: ${s.message}`),this.rejectAllPending(Error(`host spawn failed: ${s.message}`)),this.hostProcess=null}),this.hostProcess.on("exit",(s)=>{o.flush(),this.output.appendLine(`[ledger-rust] host exited with code ${s??-1}`),this.rejectAllPending(Error("ledger host exited")),this.hostProcess=null})}async submitToHost(t){if(!this.hostProcess||this.hostProcess.killed)this.startHostProcess();if(!this.hostProcess?.stdin||this.hostProcess.killed)return{mode:"offline",detail:"Rust host binary is missing or not executable."};let e=this.requestCounter++,i={jsonrpc:"2.0",id:e,method:"submit_entropy",params:{entropy_score:Math.max(0,Math.round(t.leafCount*17+13)),merkle_root:t.rootHash,leaf_count:t.leafCount,reason:t.reason}};return await new Promise((s,r)=>{this.pending.set(e,{resolve:s,reject:r}),this.hostProcess?.stdin?.write(`${JSON.stringify(i)}
`,(l)=>{if(!l)return;this.pending.delete(e),r(l)})})}handleHostPayload(t){let e=t.id;if(typeof e!=="number")return;let i=this.pending.get(e);if(!i)return;if(this.pending.delete(e),t.error&&typeof t.error==="object"){let s=t;i.resolve({mode:"offline",detail:`Rust ledger error ${s.error.code}: ${s.error.message}`});return}let o=t;i.resolve({mode:"validator-rust",txSignature:o.result.signature,detail:`Rust anchor-client submission accepted${o.result.slot?` (slot ${o.result.slot})`:""}.`})}rejectAllPending(t){for(let[e,i]of this.pending)this.pending.delete(e),i.reject(t)}startValidator(){if(!this.rootPath||this.validatorProcess)return;let t=ni(this.rootPath),e=ri(this.options.rpcUrl)??8899,i=q.join(this.rootPath,".chthonic","solana-ledger");this.validatorProcess=_t.spawn(t,["--ledger",i,"--rpc-port",String(e),"--reset","--quiet"],{cwd:this.rootPath,stdio:["ignore","pipe","pipe"]}),this.validatorProcess.stdout?.on("data",(o)=>{this.output.appendLine(`[solana] ${o.toString().trimEnd()}`)}),this.validatorProcess.stderr?.on("data",(o)=>{this.output.appendLine(`[solana] ${o.toString().trimEnd()}`)}),this.validatorProcess.on("error",(o)=>{this.output.appendLine(`[solana] validator spawn error: ${o.message}`),this.validatorProcess=null}),this.validatorProcess.on("exit",(o)=>{this.output.appendLine(`[solana] validator exited with code ${o??-1}`),this.validatorProcess=null})}}function si(t,e){if(e)return e;let i=process.platform==="win32"?"entropy-ledger-host.exe":"entropy-ledger-host";return q.join(t,"native","target","release",i)}function ni(t){let e=process.platform==="win32"?"solana-test-validator.exe":"solana-test-validator",i=q.join(t,".chthonic","bin",e);if(ce.existsSync(i))return i;return process.platform==="win32"?"solana-test-validator":e}function ri(t){try{let e=new URL(t);if(!e.port)return null;let i=Number(e.port);return Number.isFinite(i)?i:null}catch{return null}}function ai(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}class At{output;options;backend=null;constructor(t,e){this.output=t;this.options=e}async start(t){this.backend=this.options.mode==="bankrun"?new pe(this.output):new ue(this.output,this.options),await this.backend.start(t)}async commitEntropy(t){if(!this.backend)return{mode:"offline",detail:"LedgerBroker backend not initialized."};return this.backend.commitEntropy(t)}dispose(){this.backend?.dispose(),this.backend=null}}class pe{output;sequence=0;constructor(t){this.output=t}async start(t){this.output.appendLine("[ledger] phantom mode active (bankrun simulation).")}async commitEntropy(t){return this.sequence+=1,{mode:"bankrun",txSignature:`bankrun-${t.rootHash.slice(0,20)}-${this.sequence}`,detail:"In-memory bankrun simulation accepted the entropy settlement."}}dispose(){}}class ue{options;client;constructor(t,e){this.options=e;this.client=new jt(t)}async start(t){await this.client.start(t,{rpcUrl:this.options.rpcUrl,autostartValidator:this.options.autostartValidator,hostBinaryPath:this.options.hostBinaryPath,walletPath:this.options.walletPath,idlPath:this.options.idlPath})}async commitEntropy(t){return this.client.commitEntropy(t)}dispose(){this.client.dispose()}}class Ht{output;workerClient;options;requestDecorationRefresh;broker;merkle=new Dt;ledger;tooltipAugments=new Map;rootPath=null;scanTimer=null;settleTimer=null;gitPollTimer=null;gitHeadSnapshot=null;pendingSettleReason=null;disposables=[];constructor(t,e,i,o){this.output=t;this.workerClient=e;this.options=i;this.requestDecorationRefresh=o;this.broker=new Bt(t),this.ledger=new At(t,{mode:this.options.ledgerMode,rpcUrl:this.options.solanaRpcUrl,autostartValidator:this.options.solanaAutostartValidator,hostBinaryPath:this.options.solanaLedgerHostBinaryPath,walletPath:this.options.solanaWalletPath,idlPath:this.options.solanaIdlPath}),this.disposables.push(this.broker.onDidReceiveRuff((s)=>this.applyRuffSummary(s)),this.broker.onDidReceiveLore((s)=>this.applyLore(s)),this.workerClient.onDidUpdateRecords((s)=>this.captureEntropyLeaves(s)))}async start(t){if(this.rootPath=t,!this.options.enabled)return;this.broker.start(t),await this.ledger.start(t),this.broker.requestScan({type:"scan",reason:"manual",root:t}),this.startScanLoop(),this.startGitWatcher()}onDidSaveDocument(t){if(!this.rootPath||!this.options.enabled||t.uri.scheme!=="file")return;let e=fe(this.rootPath,t.uri.fsPath);if(!e)return;this.broker.requestScan({type:"scan",reason:"save",root:this.rootPath,files:[e]}),this.scheduleSettlement("save")}requestManualScan(){if(!this.rootPath||!this.options.enabled)return;this.broker.requestScan({type:"scan",reason:"manual",root:this.rootPath})}getTooltipFragments(t){if(!this.rootPath||t.scheme!=="file")return[];let e=fe(this.rootPath,t.fsPath);if(!e)return[];let i=this.tooltipAugments.get(e);if(!i)return[];let o=[];if(i.ruffViolations>0){if(o.push(`Ruff ${i.ruffViolations} violation${i.ruffViolations===1?"":"s"}`),i.ruffCodeSummary)o.push(`Codes ${i.ruffCodeSummary}`)}if(i.loreLine)o.push(i.loreLine);return o}dispose(){if(this.scanTimer)clearInterval(this.scanTimer),this.scanTimer=null;if(this.settleTimer)clearTimeout(this.settleTimer),this.settleTimer=null;if(this.gitPollTimer)clearInterval(this.gitPollTimer),this.gitPollTimer=null;this.broker.dispose(),this.ledger.dispose(),this.disposables.forEach((t)=>t.dispose()),this.disposables.length=0}captureEntropyLeaves(t){if(!this.options.enabled)return;let e=0;for(let i of t){let o=this.workerClient.getRecord(i);if(!o)continue;let s=this.tooltipAugments.get(o.path);if(this.merkle.upsert({path:o.path,entropy:o.entropy,complexity:o.complexity,debt:o.debt,freshness:o.freshness,ruffViolations:s?.ruffViolations??0,updatedAt:Date.now()}))e+=1}if(e>0)this.scheduleSettlement("interval")}applyRuffSummary(t){if(!this.rootPath||!this.options.enabled)return;let e=t.files,i=[],o=0;for(let s of e){let r=this.tooltipAugments.get(s.path),l={ruffViolations:s.violations,ruffCodeSummary:hi(s.byCode),loreLine:r?.loreLine};this.tooltipAugments.set(s.path,l);let h=qt.Uri.file(C.join(this.rootPath,s.path));i.push(h);let d=this.workerClient.getRecord(h);if(d){if(this.merkle.upsert({path:d.path,entropy:d.entropy,complexity:d.complexity,debt:d.debt,freshness:d.freshness,ruffViolations:s.violations,updatedAt:Date.now()}))o+=1;if(d.entropy>=0.45||s.violations>0)this.broker.requestLore({type:"lore-request",root:this.rootPath,path:s.path,entropy:d.entropy,violations:s.violations})}}if(i.length>0)this.requestDecorationRefresh(i);if(o>0||this.merkle.hasDirty())this.scheduleSettlement(t.reason)}applyLore(t){if(!this.rootPath||!this.options.enabled)return;if(t.root!==this.rootPath)return;let e=this.tooltipAugments.get(t.path);this.tooltipAugments.set(t.path,{ruffViolations:e?.ruffViolations??t.violations,ruffCodeSummary:e?.ruffCodeSummary,loreLine:t.line}),this.requestDecorationRefresh([qt.Uri.file(C.join(this.rootPath,t.path))])}startScanLoop(){if(this.scanTimer||!this.rootPath)return;let t=Math.max(this.options.pythonScanIntervalMs,1e4);this.scanTimer=setInterval(()=>{if(!this.rootPath)return;this.broker.requestScan({type:"scan",reason:"interval",root:this.rootPath})},t)}startGitWatcher(){if(!this.rootPath||this.gitPollTimer)return;this.gitHeadSnapshot=null,this.gitPollTimer=setInterval(async()=>{if(!this.rootPath)return;let t=await li(this.rootPath);if(!t)return;if(!this.gitHeadSnapshot){this.gitHeadSnapshot=t;return}if(t!==this.gitHeadSnapshot){if(this.gitHeadSnapshot=t,this.output.appendLine("[polyglot] git HEAD changed, scheduling Merkle settlement."),this.rootPath)this.broker.requestScan({type:"scan",reason:"commit",root:this.rootPath});this.scheduleSettlement("commit")}},6000)}scheduleSettlement(t){if(!this.options.enabled)return;if(this.pendingSettleReason=di(this.pendingSettleReason,t),this.settleTimer)clearTimeout(this.settleTimer);this.settleTimer=setTimeout(()=>{this.settleTimer=null,this.flushSettlement()},Math.max(this.options.settleDebounceMs,300))}async flushSettlement(){let t=this.pendingSettleReason??"manual";this.pendingSettleReason=null;let e=this.merkle.settle(t);if(!e)return;let i=await this.ledger.commitEntropy(e),o=[`[polyglot] settled Merkle root ${e.rootHash.slice(0,16)}...`,`leaves=${e.leafCount}`,`mode=${i.mode}`];if(i.txSignature)o.push(`tx=${i.txSignature}`);o.push(`detail=${i.detail}`),this.output.appendLine(o.join(" "))}}async function li(t){let e=C.join(t,".git"),i=C.join(e,"HEAD"),o="";try{o=await Mt.readFile(i,"utf8")}catch{return null}let s=o.trim();if(!s)return null;if(!s.startsWith("ref:"))return s;let r=s.slice(4).trim(),l=C.join(e,r);try{let h=await Mt.readFile(l,"utf8");return`ref:${r}:${h.trim()}`}catch{return`ref:${r}:missing`}}function fe(t,e){let i=C.relative(t,e);if(!i||i.startsWith("..")||C.isAbsolute(i))return null;return i.replace(/\\/g,"/")}function hi(t){let e=Object.entries(t).filter((i)=>i[1]>0).sort((i,o)=>o[1]-i[1]||i[0].localeCompare(o[0])).slice(0,3).map(([i,o])=>`${i}×${o}`);return e.length>0?e.join(", "):void 0}function di(t,e){if(!t)return e;return me(e)>=me(t)?e:t}function me(t){switch(t){case"commit":return 4;case"save":return 3;case"manual":return 2;case"interval":default:return 1}}var ye=c(require("path")),ve=require("child_process"),H=c(require("vscode"));class Ot{output;headlessVulkan;daemonBinaryOverride;eolApiBase;entropyMonitorIntervalMs;rootPath=null;daemonProcess=null;requestCounter=1;pending=new Map;onDidReceiveManifestEmitter=new H.EventEmitter;onDidReceiveManifest=this.onDidReceiveManifestEmitter.event;onDidReceiveEnvEmitter=new H.EventEmitter;onDidReceiveEnv=this.onDidReceiveEnvEmitter.event;onDidReceiveSedimentEmitter=new H.EventEmitter;onDidReceiveSediment=this.onDidReceiveSedimentEmitter.event;onDidReceiveSedimentChunkEmitter=new H.EventEmitter;onDidReceiveSedimentChunk=this.onDidReceiveSedimentChunkEmitter.event;onDidReceiveSynapseEmitter=new H.EventEmitter;onDidReceiveSynapse=this.onDidReceiveSynapseEmitter.event;onDidReceiveEntropyStateEmitter=new H.EventEmitter;onDidReceiveEntropyState=this.onDidReceiveEntropyStateEmitter.event;onDidReceiveFiredancerSurgeEmitter=new H.EventEmitter;onDidReceiveFiredancerSurge=this.onDidReceiveFiredancerSurgeEmitter.event;constructor(t,e,i,o="https://endoflife.date/api/v1",s=21600000){this.output=t;this.headlessVulkan=e;this.daemonBinaryOverride=i;this.eolApiBase=o;this.entropyMonitorIntervalMs=s}start(t){this.rootPath=t,this.startDaemon()}async requestSediment(t,e){return this.submitRequest("reactor/sediment",{max_layers:t,max_files:e})}async requestSedimentStream(t,e,i=220){return this.submitRequest("reactor/sediment_stream",{max_layers:t,max_files:e,chunk_size:i})}async requestSedimentSynapse(t,e,i=220){return this.submitRequest("reactor/sediment_synapse",{max_layers:t,max_files:e,chunk_size:i})}async requestDetect(){return this.submitRequest("anno/detect",{})}async requestProvision(){return this.submitRequest("anno/provision",{})}async requestEntropyState(){return this.submitRequest("reactor/entropy_state",{})}dispose(){for(let[,t]of this.pending)t.reject(Error("AnnoClient disposed"));this.pending.clear(),this.daemonProcess?.kill(),this.daemonProcess=null,this.onDidReceiveManifestEmitter.dispose(),this.onDidReceiveEnvEmitter.dispose(),this.onDidReceiveSedimentEmitter.dispose(),this.onDidReceiveSedimentChunkEmitter.dispose(),this.onDidReceiveSynapseEmitter.dispose(),this.onDidReceiveEntropyStateEmitter.dispose(),this.onDidReceiveFiredancerSurgeEmitter.dispose()}startDaemon(){if(!this.rootPath||this.daemonProcess)return;let t=this.daemonBinaryOverride??ci(this.rootPath),e=["--workspace",this.rootPath];if(this.headlessVulkan)e.push("--headless-vulkan");this.daemonProcess=ve.spawn(t,e,{cwd:this.rootPath,env:{...process.env,CHTHONIC_EOL_API_BASE:this.eolApiBase,CHTHONIC_ENTROPY_MONITOR_INTERVAL_MS:String(Math.max(60000,this.entropyMonitorIntervalMs))},stdio:["pipe","pipe","pipe"]});let i=z((o)=>this.handlePayload(o),(o)=>this.output.appendLine(`[daemon] invalid JSONL: ${o.message}`));this.daemonProcess.stdout?.on("data",(o)=>i.push(o)),this.daemonProcess.stderr?.on("data",(o)=>{this.output.appendLine(`[daemon] ${o.toString().trimEnd()}`)}),this.daemonProcess.on("error",(o)=>{this.output.appendLine(`[daemon] spawn failed: ${o.message}`),this.rejectAllPending(Error(`daemon spawn failed: ${o.message}`)),this.daemonProcess=null}),this.daemonProcess.on("exit",(o)=>{i.flush(),this.output.appendLine(`[daemon] exited with code ${o??-1}`),this.rejectAllPending(Error("daemon exited")),this.daemonProcess=null})}handlePayload(t){if("method"in t&&!("id"in t)){this.handleNotification(t);return}if("id"in t&&typeof t.id==="number")this.handleResponse(t)}handleNotification(t){let{method:e,params:i}=t;switch(e){case"anno/manifest":this.onDidReceiveManifestEmitter.fire(i),this.output.appendLine(`[daemon] ANNO manifest received (${i.languages?.length??0} languages)`);break;case"anno/env":this.onDidReceiveEnvEmitter.fire(i),this.output.appendLine("[daemon] env report received");break;case"reactor/status":{let o=i.status??"unknown";this.output.appendLine(`[daemon] reactor status: ${o}`);break}case"reactor/sedimentChunk":this.onDidReceiveSedimentChunkEmitter.fire(i);break;case"reactor/synapse":this.onDidReceiveSynapseEmitter.fire(i),this.output.appendLine(`[daemon] synapse status: ${i.status} (${i.mode})`);break;case"reactor/entropyState":this.onDidReceiveEntropyStateEmitter.fire(i),this.output.appendLine(`[daemon] entropy state: ${i.status} (${Math.round((i.decay_score??0)*100)}%)`);break;case"reactor/firedancerSurge":this.onDidReceiveFiredancerSurgeEmitter.fire(i),this.output.appendLine(`[daemon] firedancer slot ${i.slot} tps ${i.simulated_tps} (${i.surge?"surge":"flow"})`);break;default:this.output.appendLine(`[daemon] unknown notification: ${e}`)}}handleResponse(t){let e=t.id,i=this.pending.get(e);if(!i)return;if(this.pending.delete(e),t.error&&typeof t.error==="object"){let o=t.error;i.reject(Error(o.message));return}i.resolve(t.result)}submitRequest(t,e){if(!this.daemonProcess?.stdin||this.daemonProcess.killed)this.startDaemon();if(!this.daemonProcess?.stdin)return Promise.reject(Error("daemon not available"));let i=this.requestCounter++,o={jsonrpc:"2.0",id:i,method:t,params:e};return new Promise((s,r)=>{this.pending.set(i,{resolve:s,reject:r}),this.daemonProcess?.stdin?.write(`${JSON.stringify(o)}
`,(l)=>{if(l)this.pending.delete(i),r(l)})})}rejectAllPending(t){for(let[e,i]of this.pending)this.pending.delete(e),i.reject(t)}}function ci(t){let e=process.platform==="win32"?"chthonic-daemon.exe":"chthonic-daemon";return ye.join(t,"native","target","release",e)}var O=c(require("vscode"));class Jt{output;envCollection;disposed=!1;cockpitActive=!1;constructor(t,e){this.output=t;this.envCollection=e}async activate(){if(this.disposed||this.cockpitActive)return;try{await O.commands.executeCommand("workbench.action.closeSidebar"),await O.commands.executeCommand("workbench.action.terminal.moveToSidePanel"),await O.commands.executeCommand("workbench.action.focusAuxiliaryBar"),await O.commands.executeCommand("workbench.action.maximizePanel"),await O.commands.executeCommand("workbench.action.focusActiveEditorGroup"),this.cockpitActive=!0,this.output.appendLine("[cockpit] layout activated: sidebar=closed, terminal=AuxBar, panel=maximized, editor=Center")}catch(t){this.output.appendLine(`[cockpit] layout activation failed: ${pi(t)}`)}}applyTerminalEnv(t){if(this.disposed)return;if(!t.path_mutations.length)return;let e=t.path_mutations.sort((r,l)=>r.priority-l.priority).map((r)=>r.path),i=process.platform==="win32"?";":":";for(let r=e.length-1;r>=0;r--)this.envCollection.prepend("PATH",`${e[r]}${i}`);let o=/^[A-Za-z0-9_./\\: -]+$/,s=e.filter((r)=>{if(!o.test(r))return this.output.appendLine(`[cockpit] WARNING: skipping unsafe PATH segment: ${r}`),!1;return!0});for(let r of O.window.terminals)if(process.platform==="win32")for(let l of s)r.sendText(`$env:PATH = "${l};$env:PATH"`,!0);else for(let l of s)r.sendText(`export PATH="${l}:$PATH"`,!0);if(this.output.appendLine(`[cockpit] terminal env updated: ${e.length} PATH mutations applied`),t.warnings.length>0)for(let r of t.warnings)this.output.appendLine(`[cockpit] warning: ${r}`)}dispose(){this.disposed=!0}}function pi(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}var j=c(require("vscode")),B=c(require("fs")),_=c(require("path"));function Q(t){return t.replace(/[`*_]/g,"").replace(/\s*→\s*/g," → ").trim().slice(0,120)}function ui(t){let e=t.split(`
`),i=[],o=/\(`([A-Z][A-Za-z0-9_-]+(?:[-/][A-Za-z0-9_-]+)*)`\)/,s=/\(`(T\d(?:\.\d)?)`\)\s*:\s*→\s*\(`([^`]+)`\)/,r=/\(`(§[IVXLC]+(?:\.\d+)?)`\)/,l=/\[([^\]]+)\]\(([^)]+\.md)\)/;for(let h=0;h<e.length;h++){let d=e[h],p=d.match(/^(#{1,4})\s+(.+)/);if(p){let D=p[1].length,I=Q(p[2]),N=[];for(let P=h+1;P<e.length&&N.length<3;P++){if(e[P].match(/^#{1,4}\s/))break;let ot=e[P].trim();if(ot.length>5)N.push(ot.slice(0,120))}i.push({level:D,title:I,snippet:N.join(" "),line:h,kind:"heading"});continue}let g=d.match(s);if(g){i.push({level:4,title:`${g[1]}: ${Q(g[2])}`,snippet:d.trim().slice(0,120),line:h,kind:"tier",tag:g[1]});continue}let $=d.match(r);if($&&!p)i.push({level:4,title:$[1],snippet:Q(d).slice(0,120),line:h,kind:"anchor",tag:$[1]});let f=d.match(/\(`([A-Z][A-Za-z0-9_-]{3,})`\)\s*:\s*=\s*\(`([^`]+)`\)/);if(f){i.push({level:4,title:`${f[1]} = ${Q(f[2])}`,snippet:d.trim().slice(0,120),line:h,kind:"entity",tag:f[1]});continue}if(d.includes("(`")&&d.includes("`):")&&!g&&!f){let D=d.match(/\(`([A-Z][A-Za-z0-9_-]{4,}(?:[-/][A-Za-z0-9_-]+)*)`\)\s*:/);if(D){i.push({level:4,title:D[1],snippet:Q(d).slice(0,120),line:h,kind:"entity",tag:D[1]});continue}}let J=d.match(l);if(J&&J[2].endsWith(".md")&&!d.match(/^#{1,4}\s/))i.push({level:4,title:`→ ${J[1]}`,snippet:J[2],line:h,kind:"xref",tag:J[2]});if(!p&&!g&&!f){let D=/\(`([A-Za-z][A-Za-z0-9_-]{1,}(?:[-/][A-Za-z0-9_'-]+)*)`\)/g,I=new Set,N;while((N=D.exec(d))!==null){let P=N[1];if(P.startsWith("§"))continue;if(/^T\d/.test(P))continue;let W=P.replace(/'s$/,"").split("/"),U=W[0],st=W.length>1?W[W.length-1]:"",ht=U.toLowerCase();if(I.has(ht))continue;I.add(ht);let bt=Q(d).slice(0,140);i.push({level:4,title:st?`${U} (${st})`:U,snippet:bt,line:h,kind:"mention",tag:st||U})}}}return i}function fi(){let e="";for(let i=0;i<24;i++)e+="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"[Math.floor(Math.random()*62)];return e}class Nt{static viewType="chthonic.chatView";workspaceRoot;_currentSourcePath=null;_configListener;constructor(t){this.workspaceRoot=t}resolveSourcePath(){if(!this.workspaceRoot)return null;let t=j.workspace.getConfiguration("chthonic").get("ankh.sourcePath");if(t){let o=_.isAbsolute(t)?t:_.join(this.workspaceRoot,t);if(B.existsSync(o))return o}let e=_.join(this.workspaceRoot,".temple","session-archives");if(B.existsSync(e))try{let o=B.readdirSync(e).filter((s)=>s.startsWith("EPOCH_")&&s.endsWith(".md")).sort().reverse();if(o.length>0)return _.join(e,o[0])}catch{}let i=_.join(this.workspaceRoot,".github","copilot-instructions.archive.md");if(B.existsSync(i))return i;return null}resolveWebviewView(t,e,i){t.webview.options={enableScripts:!0};let o=()=>{let s=this.resolveSourcePath(),r=this.loadSections(s);t.webview.html=this.buildHtml(r,s),this._currentSourcePath=s};o(),t.webview.onDidReceiveMessage((s)=>{if(!s||typeof s!=="object")return;let r=s;if(r.type==="open"&&this._currentSourcePath&&typeof r.line==="number"){let l=j.Uri.file(this._currentSourcePath);j.window.showTextDocument(l,{preview:!0,selection:new j.Range(r.line,0,r.line,0)})}}),this._configListener=j.workspace.onDidChangeConfiguration((s)=>{if(s.affectsConfiguration("chthonic.ankh.sourcePath"))o()}),t.onDidDispose(()=>{this._configListener?.dispose(),this._configListener=void 0})}loadSections(t){if(!t||!B.existsSync(t))return[];try{let e=B.readFileSync(t,"utf8");return ui(e)}catch{return[]}}buildHtml(t,e){let i=fi(),o=JSON.stringify(t.map((f)=>({l:f.level,t:f.title,s:f.snippet,n:f.line,k:f.kind,g:f.tag||""}))),s=t.filter((f)=>f.kind==="heading").length,r=t.filter((f)=>f.kind==="entity").length,l=t.filter((f)=>f.kind==="tier").length,h=t.filter((f)=>f.kind==="xref").length,d=t.filter((f)=>f.kind==="anchor").length,p=t.filter((f)=>f.kind==="mention").length,g=t.length,$=e?_.basename(e):"no source found";return`<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-${i}';">
    <title>ANKH Reference</title>
    <style>
        :root {
            --bg: #050505;
            --fg: var(--vscode-editor-foreground);
            --muted: var(--vscode-descriptionForeground);
            --accent: #F4C430;
            --accent2: #c0a020;
            --panel: color-mix(in srgb, var(--bg) 88%, #161616);
            --border: color-mix(in srgb, var(--accent) 32%, transparent);
        }
        * { box-sizing: border-box; }
        html, body {
            margin: 0; height: 100%;
            background: var(--bg);
            color: var(--fg);
            font-family: var(--vscode-font-family, 'Segoe UI', sans-serif);
        }
        body { display: flex; flex-direction: column; height: 100%; }

        .header {
            padding: 8px 10px 4px;
            border-bottom: 1px solid var(--border);
            flex-shrink: 0;
        }
        .header-title {
            font-size: 11px;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--accent);
            margin: 0 0 4px 0;
        }
        .header-meta { font-size: 10px; color: var(--muted); }

        #search {
            width: 100%;
            padding: 5px 8px;
            margin: 6px 0 0;
            border: 1px solid var(--border);
            border-radius: 6px;
            background: var(--panel);
            color: var(--fg);
            font-size: 12px;
            outline: none;
        }
        #search:focus { border-color: var(--accent); }

        #list {
            flex: 1;
            overflow-y: auto;
            padding: 6px 0;
        }

        .section-item {
            padding: 5px 10px;
            cursor: pointer;
            border-left: 2px solid transparent;
            transition: border-color 0.1s, background 0.1s;
        }
        .section-item:hover { background: var(--panel); border-left-color: var(--accent); }
        .section-item.active { background: var(--panel); border-left-color: var(--accent); }
        .section-item.l1 { padding-left: 10px; }
        .section-item.l2 { padding-left: 18px; }
        .section-item.l3 { padding-left: 26px; }

        .section-title {
            font-size: 12px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            color: var(--fg);
        }
        .section-item.l1 .section-title { color: var(--accent); font-weight: 600; }
        .section-item.l2 .section-title { color: var(--fg); }
        .section-item.l3 .section-title { color: var(--muted); font-size: 11px; }
        .section-item.l4 .section-title { color: var(--muted); font-size: 10px; padding-left: 34px; }

        .section-item[data-kind="entity"] .section-title { color: #D4907A; }
        .section-item[data-kind="tier"] .section-title { color: #F4C430; font-weight: 600; }
        .section-item[data-kind="xref"] .section-title { color: #7AAAB2; font-style: italic; }
        .section-item[data-kind="anchor"] .section-title { color: #8CB87A; }
        .section-item[data-kind="mention"] .section-title { color: #B0A0D0; font-size: 10px; }

        .kind-icon {
            display: inline-block;
            width: 14px;
            font-size: 10px;
            margin-right: 4px;
            opacity: 0.7;
        }

        .header-counts {
            font-size: 10px;
            color: var(--muted);
            letter-spacing: 0.5px;
            margin-top: 2px;
        }

        .filter-row {
            display: flex;
            gap: 2px;
            margin-top: 6px;
            flex-wrap: wrap;
        }
        .filter-btn {
            background: var(--panel);
            border: 1px solid var(--border);
            color: var(--muted);
            font-size: 10px;
            padding: 2px 6px;
            border-radius: 4px;
            cursor: pointer;
        }
        .filter-btn:hover { border-color: var(--accent); color: var(--fg); }
        .filter-btn.active { border-color: var(--accent); color: var(--accent); background: color-mix(in srgb, var(--accent) 12%, transparent); }

        .snippet {
            font-size: 10px;
            color: var(--muted);
            margin-top: 2px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            display: none;
        }
        .section-item.active .snippet { display: block; }

        .open-link {
            display: none;
            font-size: 10px;
            color: var(--accent2);
            text-decoration: underline;
            cursor: pointer;
            margin-top: 4px;
        }
        .section-item.active .open-link { display: block; }

        #count { font-size: 10px; color: var(--muted); padding: 0 10px 4px; flex-shrink: 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1 class="header-title">☥ ANKH Reference</h1>
        <div class="header-meta">${$} · ${g} entries</div>
        <div class="header-counts">${s}§ ${r}⚙ ${l}♔ ${h}→ ${d}⚓ ${p}◆</div>
        <input id="search" type="text" placeholder="Search sections, entities, tiers…" autocomplete="off" />
        <div class="filter-row">
            <button class="filter-btn active" data-kind="all">All</button>
            <button class="filter-btn" data-kind="heading">§</button>
            <button class="filter-btn" data-kind="entity">⚙</button>
            <button class="filter-btn" data-kind="tier">♔</button>
            <button class="filter-btn" data-kind="xref">→</button>
            <button class="filter-btn" data-kind="anchor">⚓</button>
            <button class="filter-btn" data-kind="mention">◆</button>
        </div>
    </div>
    <div id="count"></div>
    <div id="list"></div>

    <script nonce="${i}">
        const vscode = acquireVsCodeApi();
        const sections = ${o};
        const listEl = document.getElementById('list');
        const searchEl = document.getElementById('search');
        const countEl = document.getElementById('count');
        let activeItem = null;
        let activeKind = 'all';

        const kindIcons = { heading: '§', entity: '⚙', tier: '♔', xref: '→', anchor: '⚓', mention: '◆' };

        function render(filter) {
            const q = (filter || '').toLowerCase();
            let filtered = sections;
            if (activeKind !== 'all') {
                filtered = filtered.filter(s => s.k === activeKind);
            }
            if (q) {
                filtered = filtered.filter(s =>
                    s.t.toLowerCase().includes(q) ||
                    (s.s && s.s.toLowerCase().includes(q)) ||
                    (s.g && s.g.toLowerCase().includes(q))
                );
            }

            listEl.innerHTML = '';
            activeItem = null;
            countEl.textContent = filtered.length + ' / ' + sections.length + ' entries';

            filtered.forEach(sec => {
                const div = document.createElement('div');
                div.className = 'section-item l' + sec.l;
                div.setAttribute('data-kind', sec.k);
                const icon = kindIcons[sec.k] || '';
                div.innerHTML =
                    '<div class="section-title"><span class="kind-icon">' + icon + '</span>' + escHtml(sec.t) + '</div>' +
                    '<div class="snippet">' + escHtml(sec.s || '') + '</div>' +
                    '<span class="open-link">Open in editor ↗</span>';

                div.querySelector('.section-title').addEventListener('click', () => {
                    if (activeItem === div) {
                        activeItem.classList.remove('active');
                        activeItem = null;
                    } else {
                        if (activeItem) { activeItem.classList.remove('active'); }
                        div.classList.add('active');
                        activeItem = div;
                    }
                });

                div.querySelector('.open-link').addEventListener('click', (e) => {
                    e.stopPropagation();
                    vscode.postMessage({ type: 'open', line: sec.n });
                });

                listEl.appendChild(div);
            });
        }

        function escHtml(s) {
            return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
        }

        // Filter buttons
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                activeKind = btn.getAttribute('data-kind');
                render(searchEl.value);
            });
        });

        searchEl.addEventListener('input', () => render(searchEl.value));
        render('');
    </script>
</body>
</html>`}}var Se=c(require("fs")),be=require("module"),Ut=c(require("path")),__filename="C:\\Users\\erdno\\chthonic-archive\\extensions\\chthonic-archive\\src\\reactor\\synapseBridge.ts";class Gt{output;extensionRoot;binding=null;reader=null;descriptor=null;transportMode;constructor(t,e,i){this.output=t;this.extensionRoot=e;this.transportMode=mi(i)}updateDescriptor(t){if(this.descriptor=t,this.transportMode==="jsonl"){this.output.appendLine("[synapse] disabled by transport=jsonl");return}if(t.status!=="ready"||t.mode!=="shared_memory"||!t.shm_id){this.output.appendLine(`[synapse] unavailable: ${t.reason??t.status}`);return}try{let e=this.ensureBindingLoaded();this.reader=new e.SynapseReader(t.shm_id,t.event_name??void 0),this.output.appendLine(`[synapse] connected (shm=${t.shm_id})`)}catch(e){this.reader=null,this.output.appendLine(`[synapse] init failed, falling back to JSONL: ${yi(e)}`)}}isReady(){if(this.transportMode==="jsonl")return!1;return this.reader!==null&&this.descriptor?.status==="ready"&&this.descriptor.mode==="shared_memory"}async drain(t,e){if(!this.reader||t.transport!=="shared_memory")return 0;let i=Math.max(0,t.chunks_written??t.total_chunks??0);if(i===0)return 0;let o=0,s=Date.now();while(o<i&&Date.now()-s<4000){if(!this.reader.wait_for_signal(120)){await ge();continue}while(!0){let l=this.reader.read_chunk();if(!l||l.byteLength===0)break;let h=new Uint8Array(l.buffer,l.byteOffset,l.byteLength),d=new Uint8Array(h.byteLength);if(d.set(h),e(d),o+=1,o>=i)break}await ge()}if(o<i)this.output.appendLine(`[synapse] partial drain: ${o}/${i}`);return o}dispose(){this.reader=null}ensureBindingLoaded(){if(this.binding)return this.binding;let t=[Ut.join(this.extensionRoot,"src","reactor","synapse.node"),Ut.join(this.extensionRoot,"native","target","release","synapse.node")],e=t.find((o)=>Se.existsSync(o));if(!e)throw Error(`synapse.node not found in ${t.join(", ")}`);let i=be.createRequire(__filename);return this.binding=i(e),this.binding}}function mi(t){let e=t.trim().toLowerCase();if(e==="shared_memory")return"shared_memory";if(e==="jsonl")return"jsonl";return"auto"}function yi(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}async function ge(){await new Promise((t)=>setTimeout(t,0))}var A=c(require("vscode"));var Ee=c(require("fs")),Re=c(require("path")),vi=[{file:"mise.toml",weight:16},{file:".mise.toml",weight:6},{file:"Cargo.toml",weight:20},{file:"native/Cargo.toml",weight:8},{file:"anno-manifest.toml",weight:8},{file:"uv.lock",weight:10},{file:".python-version",weight:5},{file:".ruby-version",weight:10},{file:"Gemfile",weight:6},{file:"go.mod",weight:10},{file:".node-version",weight:4},{file:".nvmrc",weight:4},{file:"package.json",weight:5},{file:"bun.lock",weight:4}];async function Pe(t){let e=vi.map((s)=>{let r=Re.join(t,s.file),l=Ee.existsSync(r);return{...s,present:l}}),i=Math.min(100,e.reduce((s,r)=>r.present?s+r.weight:s,0)),o=gi(i);return{score:i,tier:o,markers:e,present:e.filter((s)=>s.present).map((s)=>s.file),missing:e.filter((s)=>!s.present).map((s)=>s.file)}}function Le(t){switch(t){case"loom":return"loom.svg";case"lens":return"lens.svg";default:return"gate.svg"}}function gi(t){if(t>=80)return"loom";if(t>=45)return"lens";return"gate"}class Vt{extensionUri;output;containerId;fallbackItem;fallbackNoticeEmitted=!1;latestRustification=null;latestEntropy=null;constructor(t,e,i="chthonic-archive"){this.extensionUri=t;this.output=e;this.containerId=i;this.fallbackItem=A.window.createStatusBarItem(A.StatusBarAlignment.Left,47),this.fallbackItem.command="chthonic.refreshRustification",this.fallbackItem.tooltip="Rustification score and activity bar icon fallback",this.fallbackItem.show()}async update(t){this.latestRustification=t,await A.commands.executeCommand("setContext","chthonic.rustificationTier",t.tier),await A.commands.executeCommand("setContext","chthonic.rustificationScore",t.score),await this.apply()}async updateEntropy(t){this.latestEntropy=t,await A.commands.executeCommand("setContext","chthonic.decayStatus",t.status),await A.commands.executeCommand("setContext","chthonic.decayScore",Math.round(t.decay_score*100)),await this.apply()}dispose(){this.fallbackItem.dispose()}async apply(){if(!this.fallbackNoticeEmitted)this.output.appendLine("[morph] dynamic Activity Bar icon updates are unavailable on stable API; using status lane fallback"),this.fallbackNoticeEmitted=!0;this.updateFallbackStatus()}resolveIconFile(){let t=this.latestEntropy;if(t){if(t.decay_score>0.5||t.status==="critical")return"hazard.svg";if(t.decay_score<0.2&&t.status==="pristine")return"gate.svg";return"lens.svg"}let e=this.latestRustification?.tier??"gate";return Le(e)}updateFallbackStatus(){let t=this.latestRustification,e=this.latestEntropy;if(!t){this.fallbackItem.text="$(pulse) Slab boot",this.fallbackItem.tooltip="Rustification score pending";return}let i=Si(t.tier),o=e?Math.round(e.decay_score*100):null,s=e?`${e.status} ${o}%`:"unknown",r=o!==null?` · Decay ${o}%`:"";this.fallbackItem.text=`$(pulse) ${i} ${t.score}%${r}`,this.fallbackItem.tooltip=[`Toolchain completeness: ${t.score}% (${t.tier})`,`Present: ${t.present.join(", ")||"none"}`,`Missing: ${t.missing.join(", ")||"none"}`,e?`Workspace health: ${s}`:"Workspace health: entropy disabled",e&&e.critical_tools.length>0?`Critical tools: ${e.critical_tools.join(", ")}`:void 0].filter(Boolean).join(`
`)}}function Si(t){switch(t){case"loom":return"Loom";case"lens":return"Lens";default:return"Gate"}}var tt=c(require("vscode"));class zt{output;constructor(t){this.output=t}async activate(){await this.applyCommandLayout(),await tt.commands.executeCommand("workbench.view.extension.chthonic-archive"),await tt.commands.executeCommand("chthonic.loomView.focus"),this.output.appendLine("[deep-focus] activated via stable command lane")}async applyCommandLayout(){try{await tt.commands.executeCommand("workbench.action.terminal.moveToSidePanel"),await tt.commands.executeCommand("workbench.action.toggleAuxiliaryBar"),await tt.commands.executeCommand("workbench.action.focusActiveEditorGroup")}catch(t){this.output.appendLine(`[deep-focus] command layout failed: ${bi(t)}`)}}}function bi(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}var Ft=c(require("vscode"));class It{output;constructor(t){this.output=t}async activate(){await this.applyCommandLayout(),await Ft.commands.executeCommand("workbench.view.extension.chthonic-archive"),this.output.appendLine("[restore-order] completed via stable command lane")}async applyCommandLayout(){await Ei(this.output,[["workbench.view.extension.chthonic-archive"],["chthonic.statusView.focus"],["workbench.action.moveFocusedViewToSecondarySidebar"],["chthonic.loomView.focus"],["workbench.action.moveFocusedViewToPanel"],["workbench.action.positionPanelBottom"],["workbench.action.focusActiveEditorGroup"]])}}async function Ei(t,e){for(let i of e){let[o,...s]=i;try{await Ft.commands.executeCommand(o,...s)}catch(r){t.appendLine(`[restore-order] command failed (${o}): ${Ri(r)}`)}}}function Ri(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}var et=c(require("vscode"));class yt{static viewType="chthonic.loomView";view=null;report=null;snapshot=null;resolveWebviewView(t,e,i){this.view=t,t.webview.options={enableScripts:!0},t.webview.html=this.buildHtml(),t.webview.onDidReceiveMessage((o)=>{if(!o||typeof o!=="object")return;let s=o;if(s.type==="refresh")et.commands.executeCommand("chthonic.refreshRustification");if(s.type==="rescan")et.commands.executeCommand("chthonic.entropyRefresh");if(s.type==="heal")et.commands.executeCommand("chthonic.slabHeal");if(s.type==="deepFocus")et.commands.executeCommand("chthonic.deepFocus");if(s.type==="restoreOrder")et.commands.executeCommand("chthonic.restoreOrder")}),this.postState()}update(t){this.report=t,this.postState()}updateWorkspaceHealth(t){this.snapshot=t,this.postState()}dispose(){this.view=null}postState(){if(!this.view)return;this.view.webview.postMessage({type:"state",report:this.report,snapshot:this.snapshot})}buildHtml(){let t=Pi();return`<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-${t}';">
    <title>The Loom</title>
    <style>
        :root {
            --bg: #050505;
            --fg: var(--vscode-editor-foreground);
            --muted: var(--vscode-descriptionForeground);
            --accent: #F4C430;
            --panel: color-mix(in srgb, var(--bg) 88%, #161616);
            --border: color-mix(in srgb, var(--accent) 32%, transparent);
        }
        * { box-sizing: border-box; }
        html, body {
            margin: 0;
            height: 100%;
            background: var(--bg);
            color: var(--fg);
            font-family: var(--vscode-font-family, Segoe UI, sans-serif);
        }
        body { padding: 10px; display: flex; flex-direction: column; gap: 10px; min-height: 100%; }
        .panel {
            border: 1px solid var(--border);
            border-radius: 10px;
            background: var(--panel);
            padding: 10px;
        }
        .title { margin: 0; font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase; color: var(--accent); }
        .score { font-size: 28px; margin: 8px 0 0; }
        .meta { color: var(--muted); font-size: 11px; }
        .list { margin: 8px 0 0; padding: 0; list-style: none; max-height: 140px; overflow: auto; }
        .list li { font-size: 11px; color: var(--muted); padding: 2px 0; }
        .row { display: flex; gap: 8px; }
        .row button { min-width: 0; }
        .health-grid {
            margin-top: 8px;
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 8px;
        }
        .health-cell {
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 8px;
            background: color-mix(in srgb, var(--panel) 90%, transparent);
        }
        .health-label {
            color: var(--muted);
            font-size: 10px;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }
        .health-value {
            margin-top: 4px;
            font-size: 13px;
        }
        button {
            flex: 1;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: transparent;
            color: var(--fg);
            padding: 8px;
            cursor: pointer;
        }
        button:hover {
            border-color: var(--accent);
            color: var(--accent);
        }
    </style>
</head>
<body>
    <section class="panel">
        <h1 class="title">The Loom</h1>
        <div id="score" class="score">0%</div>
        <div id="tier" class="meta">Gate</div>
    </section>

    <section class="panel">
        <div class="title">Workspace Health Stream</div>
        <div class="health-grid">
            <div class="health-cell">
                <div class="health-label">Tracked Files</div>
                <div id="health-files" class="health-value">0</div>
            </div>
            <div class="health-cell">
                <div class="health-label">Average Entropy</div>
                <div id="health-entropy" class="health-value">0%</div>
            </div>
            <div class="health-cell">
                <div class="health-label">Last Scan</div>
                <div id="health-duration" class="health-value">0 ms</div>
            </div>
            <div class="health-cell">
                <div class="health-label">Updated</div>
                <div id="health-updated" class="health-value">n/a</div>
            </div>
        </div>
    </section>

    <section class="panel">
        <div class="title">Markers Present</div>
        <ul id="present" class="list"></ul>
    </section>

    <section class="panel">
        <div class="title">Markers Missing</div>
        <ul id="missing" class="list"></ul>
    </section>

    <div class="row">
        <button id="refresh">Refresh Toolchain</button>
        <button id="rescan">Rescan Health</button>
        <button id="heal">Self-Heal</button>
        <button id="focus">Deep Focus</button>
        <button id="restore">Restore Order</button>
    </div>

    <script nonce="${t}">
        const vscode = acquireVsCodeApi();
        const score = document.getElementById('score');
        const tier = document.getElementById('tier');
        const present = document.getElementById('present');
        const missing = document.getElementById('missing');
        const healthFiles = document.getElementById('health-files');
        const healthEntropy = document.getElementById('health-entropy');
        const healthDuration = document.getElementById('health-duration');
        const healthUpdated = document.getElementById('health-updated');

        function setList(element, values) {
            element.innerHTML = '';
            if (!values.length) {
                const item = document.createElement('li');
                item.textContent = 'none';
                element.appendChild(item);
                return;
            }
            for (const value of values) {
                const item = document.createElement('li');
                item.textContent = value;
                element.appendChild(item);
            }
        }

        function formatElapsed(epochMs) {
            if (!epochMs || Number.isNaN(epochMs)) {
                return 'n/a';
            }
            const elapsed = Math.max(0, Date.now() - epochMs);
            if (elapsed < 1000) return 'just now';
            const sec = Math.floor(elapsed / 1000);
            if (sec < 60) return sec + 's ago';
            const min = Math.floor(sec / 60);
            if (min < 60) return min + 'm ago';
            const hr = Math.floor(min / 60);
            if (hr < 48) return hr + 'h ago';
            const day = Math.floor(hr / 24);
            return day + 'd ago';
        }

        document.getElementById('refresh').addEventListener('click', () => vscode.postMessage({ type: 'refresh' }));
        document.getElementById('rescan').addEventListener('click', () => vscode.postMessage({ type: 'rescan' }));
        document.getElementById('heal').addEventListener('click', () => vscode.postMessage({ type: 'heal' }));
        document.getElementById('focus').addEventListener('click', () => vscode.postMessage({ type: 'deepFocus' }));
        document.getElementById('restore').addEventListener('click', () => vscode.postMessage({ type: 'restoreOrder' }));

        window.addEventListener('message', (event) => {
            const message = event.data;
            if (!message || message.type !== 'state') {
                return;
            }

            const report = message.report;
            if (report) {
                score.textContent = report.score + '%';
                tier.textContent = report.tier;
                setList(present, report.present || []);
                setList(missing, report.missing || []);
            }

            const snapshot = message.snapshot;
            if (snapshot) {
                healthFiles.textContent = String(snapshot.totalFiles || 0);
                healthEntropy.textContent = Math.round((snapshot.averageEntropy || 0) * 100) + '%';
                healthDuration.textContent = String(snapshot.lastScanDurationMs || 0) + ' ms';
                healthUpdated.textContent = formatElapsed(snapshot.lastScanAt || 0);
            } else {
                healthFiles.textContent = '—';
                healthEntropy.textContent = '—';
                healthDuration.textContent = '—';
                healthUpdated.textContent = 'entropy disabled';
            }
        });
    </script>
</body>
</html>`}}function Pi(){let e="";for(let i=0;i<24;i+=1)e+="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789".charAt(Math.floor(Math.random()*62));return e}var v=c(require("fs")),S=c(require("path")),vt=c(require("child_process")),ke=c(require("vscode"));class Yt{output;envCollection;workspaceRoot;timer=null;running=!1;options={intervalMs:21600000,eolApiBase:"https://endoflife.date/api"};constructor(t,e,i){this.output=t;this.envCollection=e;this.workspaceRoot=i}start(t){this.options=t,this.stopTimer(),this.timer=setInterval(()=>{this.runNow("interval")},Math.max(60000,t.intervalMs))}async runNow(t="manual"){if(this.running){this.output.appendLine("[slab-heal] skipped; already running");return}this.running=!0;try{let e=await this.auditVsToolchain();if(e&&(!e.allRequiredComponentsPresent||!e.allCriticalBinariesPresent))this.output.appendLine(`[slab-heal] vs2026 audit drift detected: components=${e.missingComponentCount}, binaries=${e.missingBinaryCount}`);let i=await this.collectRuntimeStates();if(i.length===0){this.output.appendLine("[slab-heal] no runtime states detected; skipping");return}let o=[];for(let s of i)if(await this.isEol(s.language,s.version))o.push(s);if(o.length===0){this.output.appendLine(`[slab-heal] ${t}: all slab runtimes are supported`);return}this.output.appendLine(`[slab-heal] ${t}: stale runtimes detected: ${o.map((s)=>`${s.language}@${s.version}`).join(", ")}`),await this.repair(o)}catch(e){this.output.appendLine(`[slab-heal] run failed: ${lt(e)}`)}finally{this.running=!1}}dispose(){this.stopTimer()}stopTimer(){if(this.timer)clearInterval(this.timer),this.timer=null}async collectRuntimeStates(){let t=[{language:"python",command:process.platform==="win32"?"python3":"python",args:["-c",'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")']},{language:"ruby",command:"ruby",args:["-e","print RUBY_VERSION"]},{language:"go",command:"go",args:["env","GOVERSION"]},{language:"rust",command:"rustc",args:["--version"]},{language:"solana",command:"solana",args:["--version"]}],e=[];for(let o of t){let s=Li(o),r=await $i(s,this.workspaceRoot);if(!r.version){this.output.appendLine(`[slab-heal] probe ${o.language} failed (${xi(s)}): ${lt(r.error)}`);continue}let l=Ti(r.version,o.language);if(!l)continue;e.push({language:o.language,version:l})}let i=await Ci(this.workspaceRoot);if(i)e.push({language:"visual-studio",version:i});else this.output.appendLine("[slab-heal] probe visual-studio failed: VS 2026 Insiders not detected");return e}async isEol(t,e){let i=await this.fetchCycles(t);if(!i||!Array.isArray(i))return!1;let o=Bi(t,e),s=i.find((l)=>{let h=l;return h.cycle===o||h.cycle===o.split(".").slice(0,1).join(".")});if(!s||s.eol==null)return!1;if(typeof s.eol==="boolean")return s.eol;let r=Date.parse(s.eol);if(Number.isNaN(r))return!1;return r<=Date.now()}async fetchCycles(t){let e=_i(t);for(let i of e){let o=await fetch(`${this.options.eolApiBase}/${i}.json`,{headers:{accept:"application/json"}});if(!o.ok)continue;let s=await o.json();if(Array.isArray(s))return s}return this.output.appendLine(`[slab-heal] endoflife feed unavailable for ${t}; skipping lifecycle gate`),null}async repair(t){if(await Di("mise",this.workspaceRoot))await Wt("mise",["upgrade"],this.workspaceRoot,this.output),await Wt("mise",["reshim"],this.workspaceRoot,this.output);else this.output.appendLine("[slab-heal] mise not found on PATH; skipped upgrade/reshim");await this.refreshToolpoolSnapshot();let i=await this.relinkVsHeaders();if(i)this.output.appendLine(`[slab-heal] relinked MSVC headers at ${i}`);else this.output.appendLine("[slab-heal] VS include relink skipped (MSVC path not found)");ke.window.showInformationMessage(`Chthonic self-heal complete: ${t.map((o)=>`${o.language}@${o.version}`).join(", ")}`)}async relinkVsHeaders(){let t=await ki(this.workspaceRoot);if(!t||!this.workspaceRoot)return null;let e=S.join(this.workspaceRoot,".chthonic","native","msvc"),i=S.join(e,"include");v.mkdirSync(e,{recursive:!0});try{v.rmSync(i,{recursive:!0,force:!0})}catch{}try{v.symlinkSync(t,i,"junction")}catch(o){let s=S.join(e,"include.path.txt");v.writeFileSync(s,t,"utf8"),this.output.appendLine(`[slab-heal] symlink failed; wrote include manifest ${s}: ${lt(o)}`)}return this.envCollection.replace("CHTHONIC_VS_CPP_INCLUDE",t),this.envCollection.prepend("INCLUDE",`${t};`),t}async auditVsToolchain(){let t=xe(this.workspaceRoot);if(!t)return null;let e=S.join(t,"scripts","vs2026_audit.ps1");if(!v.existsSync(e))return null;try{let i=await it("pwsh",["-NoProfile","-File",e,"-Json"],t);return JSON.parse(i).summary??null}catch(i){return this.output.appendLine(`[slab-heal] vs2026 audit script failed: ${lt(i)}`),null}}async refreshToolpoolSnapshot(){let t=xe(this.workspaceRoot);if(!t)return;let e=S.join(t,"scripts","toolpool-scan.ts");if(!v.existsSync(e))return;try{await Wt("bun",["run","scripts/toolpool-scan.ts","--write-env","--quiet"],t,this.output),this.output.appendLine("[slab-heal] tool-pool snapshot refreshed")}catch(i){this.output.appendLine(`[slab-heal] tool-pool snapshot failed: ${lt(i)}`)}}}function Li(t){if(t.language==="python"&&process.platform==="win32")return[{command:"python3",args:t.args},{command:"py",args:["-3",...t.args]},{command:"python",args:t.args}];if(t.language==="go"&&process.platform==="win32")return[{command:"go",args:t.args},{command:"goup",args:["go",...t.args]},{command:"goup",args:["current"]}];return[{command:t.command,args:t.args}]}function xi(t){return t.map((e)=>`${e.command} ${e.args.join(" ")}`.trim()).join(" | ")}async function $i(t,e){let i=Error("no probe candidates defined");for(let o of t)try{let s=await it(o.command,o.args,e);if(s.trim().length>0)return{version:s,error:null};i=Error(`${o.command} returned empty output`)}catch(s){i=s}return{version:null,error:i}}async function ki(t){let e=S.join(process.env["ProgramFiles(x86)"]||"C:\\Program Files (x86)","Microsoft Visual Studio","Installer","vswhere.exe");if(v.existsSync(e))try{let o=await it(e,["-latest","-products","*","-requires","Microsoft.VisualStudio.Component.VC.Tools.x86.x64","-property","installationPath"],t),s=$e(o.trim());if(s)return s}catch{}let i=["C:\\Program Files\\Microsoft Visual Studio\\18","C:\\Program Files\\Microsoft Visual Studio\\2026","C:\\Program Files\\Microsoft Visual Studio\\2022"];for(let o of i){let s=$e(o);if(s)return s}return null}function xe(t){if(!t)return null;let e=S.join(t,"extensions","chthonic-archive");if(v.existsSync(S.join(e,"package.json")))return e;if(v.existsSync(S.join(t,"package.json")))return t;return null}async function Ci(t){let e=S.join(process.env["ProgramFiles(x86)"]||"C:\\Program Files (x86)","Microsoft Visual Studio","Installer","vswhere.exe");if(!v.existsSync(e))return null;let i=[["-prerelease","-latest","-products","Microsoft.VisualStudio.Product.Professional","-property","installationVersion"],["-prerelease","-latest","-products","Microsoft.VisualStudio.Product.BuildTools","-property","installationVersion"]];for(let o of i)try{let r=(await it(e,o,t)).trim();if(r.length>0)return r}catch{}return null}function $e(t){if(!v.existsSync(t))return null;let e=[],i=[t];while(i.length>0){let o=i.pop(),s=[];try{s=v.readdirSync(o,{withFileTypes:!0})}catch{continue}for(let r of s){let l=S.join(o,r.name);if(!r.isDirectory())continue;if(r.name==="include"&&l.includes(`${S.sep}VC${S.sep}Tools${S.sep}MSVC${S.sep}`)){e.push(l);continue}i.push(l)}}if(e.length===0)return null;return e.sort((o,s)=>s.localeCompare(o,void 0,{numeric:!0,sensitivity:"base"})),e[0]}async function it(t,e,i){return new Promise((o,s)=>{vt.execFile(t,e,{cwd:i||void 0,windowsHide:!0,timeout:15000},(r,l,h)=>{if(r){s(Error(`${t} ${e.join(" ")} failed: ${h||r.message}`));return}o(String(l).trim())})})}async function Di(t,e){if(process.platform==="win32")try{return await it("where",[t],e),!0}catch{return!1}try{return await it("which",[t],e),!0}catch{return!1}}async function Wt(t,e,i,o){await new Promise((s,r)=>{let l=vt.spawn(t,e,{cwd:i||void 0,windowsHide:!0,stdio:["ignore","pipe","pipe"]});l.stdout.on("data",(h)=>{o.appendLine(`[slab-heal] ${h.toString().trimEnd()}`)}),l.stderr.on("data",(h)=>{o.appendLine(`[slab-heal] ${h.toString().trimEnd()}`)}),l.on("error",r),l.on("exit",(h)=>{if(h===0)s();else r(Error(`${t} ${e.join(" ")} exited with code ${h??-1}`))})})}function Ti(t,e){let i=t.trim();if(!i)return"";switch(e){case"go":return i.replace(/^go/i,"");case"rust":return i.replace(/^rustc\s+/i,"").split(/\s+/)[0]??"";case"solana":return i.replace(/^solana-cli\s+/i,"").split(/\s+/)[0]??"";case"visual-studio":return i.split(/\s+/)[0]??"";default:return i}}function Bi(t,e){let i=e.split(".");if(t==="go")return i.slice(0,2).join(".");if(t==="solana")return i.slice(0,1).join(".");if(t==="visual-studio")return i.slice(0,2).join(".");return i.slice(0,2).join(".")}function _i(t){switch(t){case"solana":return["solana","agave","solana-cli"];case"visual-studio":return["visual-studio"];default:return[t]}}function lt(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}function ji(t){console.log("☥ Chthonic Archive extension activated");let e=n.window.createOutputChannel("Chthonic Archive"),i=n.workspace.workspaceFolders?.[0]?.uri.fsPath||null,o=n.workspace.getConfiguration("chthonic");t.subscriptions.push(e,n.window.registerWebviewViewProvider("chthonic.chatView",new Nt(i)));let s=new Vt(t.extensionUri,e),r=new zt(e),l=new It(e),h=new yt,d=new Yt(e,t.environmentVariableCollection,i);t.subscriptions.push(s,h,d,n.window.registerWebviewViewProvider(yt.viewType,h));let p=o,g=p.get("security.allowNativeSidecars",!1),$=p.get("entropy.enabled",!1),f=p.get("entropy.maxFiles",3000),J=p.get("entropy.scanIntervalMs",60000),D=p.get("entropy.decorationDebounceMs",120),I=p.get("entropy.decorationBatchSize",240),P=p.get("entropy.polyglotEnabled",!1)&&g,ot=p.get("entropy.pythonScanIntervalMs",30000),W=p.get("entropy.ledgerSettleDebounceMs",1400),U=p.get("entropy.ledgerMode","bankrun"),st=p.get("entropy.solanaRpcUrl","http://127.0.0.1:8899"),ht=p.get("entropy.solanaAutostartValidator",!1),bt=gt(p.get("entropy.solanaLedgerHostBinaryPath","")),Ae=gt(p.get("entropy.solanaWalletPath","")),Me=gt(p.get("entropy.solanaIdlPath","")),b=new kt(t,e),dt,Y=new Ht(e,b,{enabled:P,pythonScanIntervalMs:ot,settleDebounceMs:W,ledgerMode:U,solanaRpcUrl:st,solanaAutostartValidator:ht,solanaLedgerHostBinaryPath:bt,solanaWalletPath:Ae,solanaIdlPath:Me},(a)=>dt?.enqueueExternalUpdates(a));dt=new Ct(b,D,I,(a)=>Y.getTooltipFragments(a));let Et=new pt(t.extensionUri,b);Et.setRootPath(i),h.updateWorkspaceHealth(b.getSnapshot()),t.subscriptions.push(b,dt,Et,Y,b.onDidUpdateSnapshot((a)=>{h.updateWorkspaceHealth(a)}),n.window.registerFileDecorationProvider(dt),n.window.registerWebviewViewProvider(pt.viewType,Et));let w=async(a)=>{if(!i)return;let u=await Pe(i);h.update(u),await s.update(u),e.appendLine(`[monolith] toolchain completeness ${u.score}% (${u.tier}) via ${a}`)};if(i){w("startup");let a=n.workspace.createFileSystemWatcher(new n.RelativePattern(i,"{uv.lock,Cargo.toml,native/Cargo.toml,mise.toml,.mise.toml,anno-manifest.toml,go.mod,.ruby-version,Gemfile,.node-version,.nvmrc,package.json,bun.lock,.python-version}"));t.subscriptions.push(a,a.onDidCreate(()=>{w("marker-create")}),a.onDidChange(()=>{w("marker-change")}),a.onDidDelete(()=>{w("marker-delete")}))}if(i&&$){if(b.start(i,f,J),P)Y.start(i)}t.subscriptions.push(n.workspace.onDidSaveTextDocument((a)=>{b.refreshFile(a.uri),Y.onDidSaveDocument(a)})),t.subscriptions.push(n.commands.registerCommand("chthonic.entropyRefresh",()=>{if(!i){n.window.showWarningMessage("Workspace root is required to refresh workspace health.");return}if(!$){n.window.showWarningMessage("Workspace health lane is disabled (chthonic.entropy.enabled=false).");return}b.rescanNow(),b.requestGraph(260),Y.requestManualScan(),n.window.showInformationMessage("Chthonic workspace health scan requested")}));let Kt=p.get("reactor.enabled",!1),Xt=Kt&&g,qe=p.get("reactor.headlessVulkan",!0),He=p.get("reactor.cockpitAutoLayout",!1),Oe=p.get("reactor.transport","auto"),Zt=gt(p.get("reactor.daemonBinaryPath","")),T=Ui(i,Xt,Zt,g,Kt),Rt=p.get("slab.selfHealingEnabled",!1)&&g,Qt=p.get("slab.selfHealingIntervalMs",21600000),te=p.get("slab.eolApiBase","https://endoflife.date/api"),Je=Mi(te),Ne=Math.max(60000,Math.floor(Qt/2)),k=new Ot(e,qe,Zt,Je,Ne),ct=new Jt(e,t.environmentVariableCollection),ee=new Gt(e,t.extensionPath,Oe),Pt=null,Lt=null,nt=null,ie=(a,u)=>{let m=u?`${a} (${u.toLocaleString()} tps)`:a;e.appendLine(`[loom-reflex] panel lane ${m}`),l.activate()},Ue=(a)=>{e.appendLine(`[loom-reflex] primary lane ${a}`),n.commands.executeCommand("workbench.view.extension.chthonic-archive"),n.commands.executeCommand("chthonic.loomView.focus")};if(!T.ready)e.appendLine(`[reactor] lane parked: ${T.reason}`);t.subscriptions.push(k,ct,ee);let oe=(a)=>{if(s.updateEntropy(a),e.appendLine(`[workspace-health] score ${Math.round(a.decay_score*100)}% (${a.status}) from ${a.source_mise??"no-mise"}`),a.validator_active){let y=`${a.validator_process??"validator"}:${a.validator_source_mise}`;if(y!==Lt)Lt=y,Ue(`validator-online:${y}`)}else Lt=null;if(a.firedancer_surge&&a.validator_active){let y=`${a.checked_at_epoch_ms}:${a.simulated_tps}`;if(y!==nt)nt=y,ie("workspace-health-surge",a.simulated_tps)}else nt=null;if(!a.critical||!a.auto_update_enabled){Pt=null;return}let u=`${a.status}:${a.auto_update}:${[...a.critical_tools].sort().join(",")}`;if(u===Pt)return;Pt=u;let m=a.critical_tools.length>0?a.critical_tools.join(", "):"runtime toolchain";n.window.showWarningMessage(`Workspace health is critical (${Math.round(a.decay_score*100)}%). ${m} needs healing.`,"Run mise upgrade","Later").then((y)=>{if(y==="Run mise upgrade")d.runNow("manual")})};if(t.subscriptions.push(k.onDidReceiveEnv((a)=>{ct.applyTerminalEnv(a)}),k.onDidReceiveSynapse((a)=>{ee.updateDescriptor(a)}),k.onDidReceiveEntropyState((a)=>{oe(a)}),k.onDidReceiveFiredancerSurge((a)=>{if(a.surge){let u=`${a.slot}:${a.simulated_tps}`;if(u!==nt)nt=u,ie("daemon-surge",a.simulated_tps)}})),T.ready&&i&&Xt){if(k.start(i),k.requestEntropyState().then((u)=>{oe(u)}).catch((u)=>{e.appendLine(`[workspace-health] initial snapshot unavailable: ${u}`)}),He)ct.activate();let a=x.join(i,".git","HEAD");if(R.existsSync(a)){let u=null,m=R.watch(x.join(i,".git"),{persistent:!1},(y,M)=>{if(M==="HEAD"||M?.startsWith("refs")){if(u)clearTimeout(u);u=setTimeout(()=>{e.appendLine("[reactor] git change detected, recomputing sediment"),k.requestSediment(10,500).catch((G)=>{e.appendLine(`[reactor] live-loop sediment failed: ${G}`)})},800)}});t.subscriptions.push({dispose:()=>m.close()})}}if(i&&Rt)d.start({intervalMs:Qt,eolApiBase:te}),d.runNow("interval");if(t.subscriptions.push(n.commands.registerCommand("chthonic.activateCockpit",()=>{ct.activate()}),n.commands.registerCommand("chthonic.deepFocus",()=>{r.activate()}),n.commands.registerCommand("chthonic.restoreOrder",()=>{l.activate()}),n.commands.registerCommand("chthonic.slabHeal",()=>{if(!g){n.window.showWarningMessage("Native sidecars are disabled (chthonic.security.allowNativeSidecars=false).");return}d.runNow("manual")}),n.commands.registerCommand("chthonic.refreshRustification",()=>{w("manual-command")}),n.commands.registerCommand("chthonic.annoDetect",()=>{if(!g){n.window.showWarningMessage("ANNO lane is disabled by chthonic.security.allowNativeSidecars=false."),n.commands.executeCommand("chthonic.entropyRefresh");return}if(!T.ready){n.window.showWarningMessage(`ANNO lane unavailable: ${T.reason}. Using workspace-health fallback.`),n.commands.executeCommand("chthonic.entropyRefresh");return}if(i)k.start(i);n.window.showInformationMessage("ANNO project detection triggered")}),n.commands.registerCommand("chthonic.reactorSediment",async()=>{if(!T.ready){b.rescanNow(),b.requestGraph(260),n.window.showInformationMessage(`Reactor sediment lane unavailable (${T.reason}); refreshed workspace-health graph instead.`);return}try{let a=await k.requestSediment(10,500);n.window.showInformationMessage(`Sediment computed: ${a.file_count} files, ${a.layer_count} layers (${a.backend}, ${a.compute_time_ms}ms)`)}catch(a){n.window.showErrorMessage(`Sediment computation failed: ${a}`)}}),n.commands.registerCommand("chthonic.openWebCockpit",async()=>{let a=De(o);if(!await Te(a,1200)){let m=await n.window.showWarningMessage(`Web cockpit is not responding at ${a}.`,"Start and Open","Open Anyway","Cancel");if(!m||m==="Cancel")return;if(m==="Start and Open")await n.commands.executeCommand("chthonic.startWebCockpit"),await Oi(1800)}qi(t,e,a)}),n.commands.registerCommand("chthonic.startWebCockpit",()=>{if(!i){n.window.showWarningMessage("Workspace root is required to start the Bun/Next cockpit.");return}let a=n.window.createTerminal({name:"Chthonic Web Cockpit",cwd:i});a.show(),a.sendText("bun run web:dev"),e.appendLine("[web-cockpit] started via bun run web:dev")}),n.commands.registerCommand("chthonic.openBunTrainingDocs",async()=>{let a=[{label:"Bun React Guide",description:"Build a React app with Bun",url:"https://bun.com/docs/guides/ecosystem/react#build-a-react-app-with-bun"},{label:"Bun Next.js Guide",description:"Build an app with Next.js and Bun",url:"https://bun.com/docs/guides/ecosystem/nextjs#build-an-app-with-next-js-and-bun"},{label:"Bun Tailwind (Fullstack Bundler)",description:"Tailwind plugin lane for Bun fullstack",url:"https://bun.com/docs/bundler/fullstack#tailwindcss-plugin"},{label:"Bun SQLite API",description:"Typed SQL training lane (bun:sqlite)",url:"https://bun.com/docs/api/sqlite"}],u=await n.window.showQuickPick(a,{placeHolder:"Open Bun training docs"});if(!u)return;n.env.openExternal(n.Uri.parse(u.url))}),n.commands.registerCommand("chthonic.postRestartVerify",()=>{if(!i){n.window.showWarningMessage("Workspace root is required to run post-restart verification.");return}let a=n.window.createTerminal({name:"Chthonic Post-Restart Verify",cwd:i});a.show(),a.sendText("bun run --cwd extensions/chthonic-archive insiders:post-restart:verify"),e.appendLine("[insiders] post-restart verification lane started")}),n.commands.registerCommand("chthonic.restartGate",()=>{if(!i){n.window.showWarningMessage("Workspace root is required to run restart gate checks.");return}let a=n.window.createTerminal({name:"Chthonic Restart Gate",cwd:i});a.show(),a.sendText("bun run --cwd extensions/chthonic-archive insiders:restart:gate"),e.appendLine("[insiders] restart gate check lane started")}),n.commands.registerCommand("chthonic.runtimeStatus",async()=>{let a=De(o),u=await Te(a,900),m=new Set(await n.commands.getCommands(!0)),y=n.extensions.getExtension("chthonic-archive.chthonic-mandala"),M=n.extensions.getExtension("chthonic-archive.chthonic-statusbar"),G=Vi({workspaceRoot:i,entropyEnabled:$,entropyPolyglotEnabled:P,entropyLedgerMode:U,reactorReadiness:T,slabSelfHealingEnabled:Rt,allowNativeSidecars:g,extensionPath:t.extensionPath,webCockpitUrl:a,webCockpitReachable:u,commandCatalog:m,bridgeMandala:{installed:Boolean(y),active:y?.isActive??!1,commandAvailable:m.has("chthonic.mandalaBridge.switchTheme")},bridgeStatusbar:{installed:Boolean(M),active:M?.isActive??!1,commandAvailable:m.has("chthonic.bridge.verifySSOT")}});e.show(!0),e.appendLine("[runtime] component status");for(let V of G)e.appendLine(`[runtime] ${V}`);let Ge=G.some((V)=>V.includes("DISABLED")||V.includes("PARKED")||V.includes("UNAVAILABLE")||V.includes("MISSING")||V.includes("UNREACHABLE"));n.window.showInformationMessage(Ge?"Some runtime lanes are parked. See Chthonic Archive output for details.":"All runtime lanes are operational.")})),i&&o.get("webCockpit.autoStart",!1))n.commands.executeCommand("chthonic.startWebCockpit");let xt=new _e;n.window.registerTreeDataProvider("chthonic.themeView",xt),t.subscriptions.push(n.commands.registerCommand("chthonic.switchTheme",async(a)=>{let u=[{label:"$(paintcan) Flesh & Earth",description:"The Decorator · Warm earth · WCAG AA",id:"Chthonic — Flesh & Earth (The Decorator)"},{label:"$(zap) ROGBIV",description:"Spectra Chroma · Spectral canon · FA¹⁻⁵",id:"Chthonic — ROGBIV (Spectra Chroma)"},{label:"$(symbol-color) Geological Core",description:"Sister Ferrum Scoriae · Forge strata · WCAG AA",id:"Chthonic — Geological Core (Sister Ferrum Scoriae)"},{label:"$(flame) The Decorator",description:"The Decorator · Tier 0.5 · Ornamental precision",id:"Chthonic — The Decorator"}],m=a;if(!m){let y=n.workspace.getConfiguration("workbench").get("colorTheme"),M=await n.window.showQuickPick(u.map((G)=>({...G,picked:y===G.id})),{placeHolder:`Current: ${y}`});if(!M)return;m=M.id}await n.workspace.getConfiguration("workbench").update("colorTheme",m,n.ConfigurationTarget.Workspace),n.window.showInformationMessage(`Theme: ${m}`),xt.refresh()}));let se=o;if(se.get("showSSOTHash",!0)){let a=n.window.createStatusBarItem(n.StatusBarAlignment.Left,50);a.command="chthonic.verifySSOT",a.tooltip="Policy fingerprint — click to verify integrity",t.subscriptions.push(a),Ce(a),t.subscriptions.push(n.workspace.onDidSaveTextDocument((u)=>{if(u.fileName.includes("copilot-instructions"))Ce(a)}))}if(se.get("showLineage",!1)){let a=n.window.createStatusBarItem(n.StatusBarAlignment.Left,49);a.command="workbench.view.scm";let u=()=>{let y=zi(i);a.text=`$(git-branch) ${y.label}`,a.tooltip=y.tooltip,a.show()};u();let m=setInterval(u,6000);t.subscriptions.push({dispose:()=>clearInterval(m)}),a.show(),t.subscriptions.push(a)}let $t=new je;$t.configure({entropyEnabled:$,allowSidecars:g,reactorReady:T.ready,selfHealing:Rt}),n.window.registerTreeDataProvider("chthonic.statusView",$t),t.subscriptions.push(n.commands.registerCommand("chthonic.verifySSOT",async()=>{let a=wt();if(a)n.window.showInformationMessage(`Policy fingerprint: ${a.substring(0,16)}…`);else n.window.showWarningMessage("Policy file not found")})),t.subscriptions.push(n.commands.registerCommand("chthonic.refreshStatus",()=>{if($t.refresh(),xt.refresh(),$)b.rescanNow(),b.requestGraph(260),Y.requestManualScan();w("refresh-status")}))}function Ai(){}function wt(){let t=n.workspace.workspaceFolders?.[0];if(!t)return null;let e=n.workspace.getConfiguration("chthonic").get("ssotPath",".github/copilot-instructions.md"),i=x.join(t.uri.fsPath,e);if(!R.existsSync(i))return null;let s=R.readFileSync(i,"utf-8").replace(/\r\n/g,`
`).replace(/\r/g,`
`).split(`
`).map((r)=>r.trimEnd()).join(`
`).trim();return St.createHash("sha256").update(s,"utf-8").digest("hex")}function Ce(t){let e=wt();if(e)t.text=`$(shield) ${e.substring(0,8)}`,t.show();else t.text="$(shield) Policy ??",t.show()}function gt(t){let e=t.trim();return e.length>0?e:void 0}function Mi(t){let e=t.trim().replace(/\/+$/,"");if(e.endsWith("/api"))return`${e}/v1`;return e.length>0?e:"https://endoflife.date/api/v1"}function De(t){let e=t.get("webCockpit.url","http://127.0.0.1:3000").trim();if(/^https?:\/\//i.test(e))return e;return`http://${e}`}function qi(t,e,i){let o=n.window.createWebviewPanel("chthonicWebCockpit","Chthonic Web Cockpit",n.ViewColumn.Active,{enableScripts:!0,retainContextWhenHidden:!0});o.webview.html=Hi(i),o.webview.onDidReceiveMessage(async(s)=>{if(!s||typeof s!=="object")return;let r=s;if(r.type==="start"){await n.commands.executeCommand("chthonic.startWebCockpit");return}if(r.type==="openExternal"&&r.url){await n.env.openExternal(n.Uri.parse(r.url));return}e.appendLine(`[webview] Received message: ${JSON.stringify(s)}`)},void 0,t.subscriptions),o.onDidDispose(()=>{e.appendLine("[webview] Chthonic Web Cockpit panel disposed")},void 0,t.subscriptions)}function Hi(t){let e=Ni(),i=Ji(t);return`<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; frame-src http: https:; style-src 'unsafe-inline'; script-src 'nonce-${e}';">
    <title>Chthonic Web Cockpit</title>
    <style>
        html, body {
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
            background: var(--vscode-editor-background);
            color: var(--vscode-editor-foreground);
            font-family: var(--vscode-font-family, Segoe UI, sans-serif);
        }
        .shell {
            display: grid;
            grid-template-rows: auto 1fr;
            height: 100%;
        }
        .bar {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 10px;
            border-bottom: 1px solid var(--vscode-panel-border);
            background: var(--vscode-sideBar-background);
            font-size: 12px;
        }
        .status {
            flex: 1;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            color: var(--vscode-descriptionForeground);
        }
        .btn {
            border: 1px solid var(--vscode-button-border, var(--vscode-panel-border));
            background: var(--vscode-button-secondaryBackground);
            color: var(--vscode-button-secondaryForeground);
            border-radius: 6px;
            padding: 4px 8px;
            font-size: 11px;
            cursor: pointer;
        }
        .btn:hover {
            background: var(--vscode-button-secondaryHoverBackground);
        }
        iframe {
            border: 0;
            width: 100%;
            height: 100%;
            background: #0b0b0b;
        }
    </style>
</head>
<body>
    <section class="shell">
        <header class="bar">
            <div id="status" class="status">Connecting to ${i}</div>
            <button id="start" class="btn" type="button">Start Server</button>
            <button id="external" class="btn" type="button">Open Browser</button>
        </header>
        <iframe id="cockpit" src="${i}" title="Chthonic Web Cockpit"></iframe>
    </section>
    <script nonce="${e}">
        const vscode = acquireVsCodeApi();
        const targetUrl = ${JSON.stringify(t)};
        const statusNode = document.getElementById('status');
        const iframe = document.getElementById('cockpit');
        let loaded = false;

        iframe.addEventListener('load', () => {
            loaded = true;
            statusNode.textContent = 'Connected: ' + targetUrl;
        });

        setTimeout(() => {
            if (!loaded) {
                statusNode.textContent = 'No response from ' + targetUrl + ' (try Start Server).';
            }
        }, 5000);

        document.getElementById('start').addEventListener('click', () => {
            vscode.postMessage({ type: 'start' });
        });
        document.getElementById('external').addEventListener('click', () => {
            vscode.postMessage({ type: 'openExternal', url: targetUrl });
        });
    </script>
</body>
</html>`}async function Te(t,e=1200){let i=new AbortController,o=setTimeout(()=>i.abort(),Math.max(300,e));try{return(await fetch(t,{method:"GET",redirect:"follow",signal:i.signal})).ok}catch{return!1}finally{clearTimeout(o)}}function Oi(t){return new Promise((e)=>setTimeout(e,t))}function Ji(t){return t.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function Ni(){return St.randomBytes(18).toString("base64")}function Ui(t,e,i,o=!1,s=!1){if(!o&&s)return{ready:!1,reason:"disabled by chthonic.security.allowNativeSidecars=false"};if(!e)return{ready:!1,reason:"disabled by chthonic.reactor.enabled=false"};if(!t)return{ready:!1,reason:"workspace root is unavailable"};let r=Gi(t,i);if(!R.existsSync(r))return{ready:!1,reason:`daemon binary missing (${r})`,daemonPath:r};return{ready:!0,reason:"ready",daemonPath:r}}function Gi(t,e){if(e)return x.isAbsolute(e)?e:x.join(t,e);let i=process.platform==="win32"?"chthonic-daemon.exe":"chthonic-daemon";return x.join(t,"native","target","release",i)}function Vi(t){let e=[],i=x.join(t.extensionPath,"dist","entropy-worker.js"),o=R.existsSync(i);if(e.push(`workspace=${t.workspaceRoot?"READY":"UNAVAILABLE"}`),e.push(`workspace-health=${t.entropyEnabled?"ENABLED":"DISABLED"}`),e.push(`native-sidecars=${t.allowNativeSidecars?"ENABLED":"DISABLED (chthonic.security.allowNativeSidecars=false)"}`),e.push(`polyglot-sidecars=${t.entropyEnabled?t.entropyPolyglotEnabled?"ENABLED":"DISABLED":"PARKED (workspace-health disabled)"}`),e.push(`ledger-mode=${t.entropyEnabled&&t.entropyPolyglotEnabled?t.entropyLedgerMode:`PARKED (${t.entropyLedgerMode}, polyglot disabled)`}`),e.push(`self-healing=${t.slabSelfHealingEnabled?"ENABLED":"DISABLED"}`),e.push(`reactor=${t.reactorReadiness.ready?"READY":`PARKED (${t.reactorReadiness.reason})`}`),e.push(`entropy-worker=${o?"READY":"MISSING"}`),e.push(`abyssal-view=${t.entropyEnabled?o?"READY":`PARKED (worker missing at ${i})`:"PARKED (workspace-health disabled)"}`),e.push(`loom-view=${t.workspaceRoot?"READY":"PARKED (workspace unavailable)"}`),e.push(`web-cockpit-url=${t.webCockpitUrl}`),e.push(`web-cockpit=${t.webCockpitReachable?"REACHABLE":'UNREACHABLE (run "Chthonic: Start Next Cockpit")'}`),e.push(`bridge-mandala=${Be(t.bridgeMandala)}`),e.push(`bridge-statusbar=${Be(t.bridgeStatusbar)}`),t.reactorReadiness.daemonPath)e.push(`reactor-daemon=${t.reactorReadiness.daemonPath}`);return e}function Be(t){if(!t.installed)return"UNAVAILABLE (extension not installed)";if(t.commandAvailable)return"READY";if(t.active)return"DEGRADED (active but command missing)";return"INSTALLED (awaiting activation)"}function zi(t){if(!t)return{label:"no-workspace",tooltip:"Chthonic lineage unavailable: no workspace root."};let e=x.join(t,".git"),i=x.join(e,"HEAD");if(!R.existsSync(i))return{label:"no-git",tooltip:"Chthonic lineage unavailable: .git/HEAD not found."};try{let o=R.readFileSync(i,"utf8").trim();if(!o)return{label:"detached",tooltip:"Chthonic lineage unavailable: empty git HEAD."};if(!o.startsWith("ref:"))return{label:`detached@${o.slice(0,8)}`,tooltip:`Detached HEAD ${o}`};let s=o.slice(4).trim(),r=s.split("/").pop()||s,l=x.join(e,...s.split("/")),h=R.existsSync(l)?R.readFileSync(l,"utf8").trim().slice(0,8):"unknown";return{label:`${r}@${h}`,tooltip:`Chthonic lineage
${s}
${h}`}}catch(o){return{label:"lineage-error",tooltip:`Chthonic lineage read failed: ${String(o)}`}}}class _e{_onDidChange=new n.EventEmitter;onDidChangeTreeData=this._onDidChange.event;refresh(){this._onDidChange.fire()}getTreeItem(t){return t}getChildren(){let t=n.workspace.getConfiguration("workbench").get("colorTheme")||"";return[{name:"Chthonic — Flesh & Earth (The Decorator)",short:"Flesh & Earth",icon:"paintcan",desc:"The Decorator · Warm earth"},{name:"Chthonic — ROGBIV (Spectra Chroma)",short:"ROGBIV",icon:"zap",desc:"Spectra Chroma · Spectral canon"},{name:"Chthonic — Geological Core (Sister Ferrum Scoriae)",short:"Geological Core",icon:"symbol-color",desc:"Ferrum Scoriae · Forge strata"},{name:"Chthonic — The Decorator",short:"The Decorator",icon:"flame",desc:"Tier 0.5 · Ornamental precision"}].map((i)=>{let o=t===i.name,s=new n.TreeItem(`${o?"◉":"○"} ${i.short}`,n.TreeItemCollapsibleState.None);return s.iconPath=new n.ThemeIcon(i.icon),s.tooltip=`${i.name}
${i.desc}${o?`

✅ ACTIVE`:""}`,s.description=o?"✅ Active":i.desc,s.command={command:"chthonic.switchTheme",title:"Switch Theme",arguments:[i.name]},s})}}class je{_onDidChange=new n.EventEmitter;onDidChangeTreeData=this._onDidChange.event;_entropyEnabled=!1;_allowSidecars=!1;_reactorReady=!1;_selfHealing=!1;configure(t){this._entropyEnabled=t.entropyEnabled,this._allowSidecars=t.allowSidecars,this._reactorReady=t.reactorReady,this._selfHealing=t.selfHealing}refresh(){this._onDidChange.fire()}getTreeItem(t){return t}getChildren(){let t=[],e=wt(),i=new n.TreeItem(`Policy: ${e?e.substring(0,12)+"…":"not found"}`,n.TreeItemCollapsibleState.None);i.iconPath=new n.ThemeIcon("shield"),i.command={command:"chthonic.verifySSOT",title:"Verify"},t.push(i);let o=(n.workspace.getConfiguration("workbench").get("colorTheme")||"default").replace("Chthonic Mandala - ",""),s=new n.TreeItem(`Theme: ${o}`,n.TreeItemCollapsibleState.None);s.iconPath=new n.ThemeIcon("paintcan"),s.command={command:"chthonic.switchTheme",title:"Switch"},t.push(s);let r=new n.TreeItem(`Sidecars: ${this._allowSidecars?"unlocked":"locked"}`,n.TreeItemCollapsibleState.None);r.iconPath=new n.ThemeIcon(this._allowSidecars?"unlock":"lock"),r.tooltip=this._allowSidecars?"Native sidecars are enabled — polyglot, reactor, and self-healing lanes are permitted.":"Native sidecars disabled (safe mode). Set chthonic.security.allowNativeSidecars to enable.",t.push(r);let l=[{label:"Entropy",on:this._entropyEnabled,icon:"pulse"},{label:"Reactor",on:this._reactorReady,icon:"flame"},{label:"Self-Heal",on:this._selfHealing,icon:"hammer"}];for(let d of l){let p=new n.TreeItem(`${d.label}: ${d.on?"active":"off"}`,n.TreeItemCollapsibleState.None);p.iconPath=new n.ThemeIcon(d.on?d.icon:"circle-slash"),t.push(p)}let h=new n.TreeItem("Full Runtime Status…",n.TreeItemCollapsibleState.None);return h.iconPath=new n.ThemeIcon("output"),h.command={command:"chthonic.runtimeStatus",title:"Runtime Status"},t.push(h),t}}
