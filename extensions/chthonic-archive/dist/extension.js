var De=Object.create;var{getPrototypeOf:Me,defineProperty:N,getOwnPropertyNames:Ht,getOwnPropertyDescriptor:Te}=Object,Jt=Object.prototype.hasOwnProperty;var h=(t,e,i)=>{i=t!=null?De(Me(t)):{};let o=e||!t||!t.__esModule?N(i,"default",{value:t,enumerable:!0}):i;for(let s of Ht(t))if(!Jt.call(o,s))N(o,s,{get:()=>t[s],enumerable:!0});return o},Ot=new WeakMap,we=(t)=>{var e=Ot.get(t),i;if(e)return e;if(e=N({},"__esModule",{value:!0}),t&&typeof t==="object"||typeof t==="function")Ht(t).map((o)=>!Jt.call(e,o)&&N(e,o,{get:()=>t[o],enumerable:!(i=Te(t,o))||i.enumerable}));return Ot.set(t,e),e};var Be=(t,e)=>{for(var i in e)N(t,i,{get:e[i],enumerable:!0,configurable:!0,set:(o)=>e[i]=()=>o})};var Ci={};Be(Ci,{deactivate:()=>mi,activate:()=>fi});module.exports=we(Ci);var r=h(require("vscode")),ae=h(require("crypto")),P=h(require("fs")),E=h(require("path"));var I=h(require("path")),j=h(require("vscode")),Nt=require("worker_threads");class st{extensionContext;output;records=new Map;recordUris=new Map;onDidUpdateRecordsEmitter=new j.EventEmitter;onDidUpdateRecords=this.onDidUpdateRecordsEmitter.event;onDidUpdateGraphEmitter=new j.EventEmitter;onDidUpdateGraph=this.onDidUpdateGraphEmitter.event;onDidUpdateSnapshotEmitter=new j.EventEmitter;onDidUpdateSnapshot=this.onDidUpdateSnapshotEmitter.event;worker=null;rootPath=null;workerPath;maxFiles=1e4;lastScanDurationMs=0;lastScanAt=0;scanTimer=null;disposed=!1;constructor(t,e){this.extensionContext=t;this.output=e;this.workerPath=t.asAbsolutePath(I.join("dist","entropy-worker.js"))}start(t,e,i){this.rootPath=t,this.maxFiles=e,this.ensureWorker(),this.send({type:"scan",root:t,maxFiles:this.maxFiles}),this.scheduleScanLoop(i)}rescanNow(){if(!this.rootPath)return;this.send({type:"scan",root:this.rootPath,maxFiles:this.maxFiles})}refreshFile(t){if(!this.rootPath||t.scheme!=="file")return;this.send({type:"refresh-file",root:this.rootPath,path:t.fsPath})}requestGraph(t){this.send({type:"graph",limit:t})}getRecord(t){if(!this.rootPath||t.scheme!=="file")return;let e=je(I.relative(this.rootPath,t.fsPath));return this.records.get(e)}getSnapshot(t=40){let e=Array.from(this.records.values()),i=e.length===0?0:e.reduce((s,a)=>s+a.entropy,0)/e.length,o=e.sort((s,a)=>a.entropy-s.entropy).slice(0,t);return{totalFiles:e.length,topEntropy:o,averageEntropy:i,lastScanDurationMs:this.lastScanDurationMs,lastScanAt:this.lastScanAt}}dispose(){if(this.disposed=!0,this.scanTimer)clearInterval(this.scanTimer),this.scanTimer=null;this.send({type:"stop"}),this.worker?.terminate(),this.worker=null,this.onDidUpdateRecordsEmitter.dispose(),this.onDidUpdateGraphEmitter.dispose(),this.onDidUpdateSnapshotEmitter.dispose()}scheduleScanLoop(t){if(this.scanTimer)clearInterval(this.scanTimer);let e=Math.max(5000,t);this.scanTimer=setInterval(()=>{if(!this.disposed)this.rescanNow()},e)}ensureWorker(){if(this.worker)return;this.worker=new Nt.Worker(this.workerPath),this.worker.on("message",(t)=>this.handleWorkerEvent(t)),this.worker.on("error",(t)=>{this.output.appendLine(`[entropy] worker error: ${t.message}`)}),this.worker.on("exit",(t)=>{if(this.output.appendLine(`[entropy] worker exited with code ${t}`),this.worker=null,!this.disposed&&t!==0)this.ensureWorker(),this.rescanNow()})}send(t){this.ensureWorker(),this.worker?.postMessage(t)}handleWorkerEvent(t){switch(t.type){case"scan-progress":{if(!this.rootPath)return;let e=[];for(let i of t.records){this.records.set(i.path,i);let o=this.recordUris.get(i.path);if(!o)o=j.Uri.file(I.join(this.rootPath,i.path)),this.recordUris.set(i.path,o);e.push(o)}if(e.length>0)this.onDidUpdateRecordsEmitter.fire(e);break}case"scan-complete":this.lastScanDurationMs=t.durationMs,this.lastScanAt=Date.now(),this.onDidUpdateSnapshotEmitter.fire(this.getSnapshot());break;case"graph-result":this.onDidUpdateGraphEmitter.fire(t.graph);break;case"error":this.output.appendLine(`[entropy] ${t.message}${t.detail?`
${t.detail}`:""}`);break}}}function je(t){return t.replace(/\\/g,"/")}var A=h(require("vscode"));class nt{workerClient;debounceMs;maxPerFlush;tooltipAugmentProvider;onDidChangeEmitter=new A.EventEmitter;onDidChangeFileDecorations=this.onDidChangeEmitter.event;pending=new Map;flushTimer=null;constructor(t,e,i,o){this.workerClient=t;this.debounceMs=e;this.maxPerFlush=i;this.tooltipAugmentProvider=o;this.workerClient.onDidUpdateRecords((s)=>this.enqueueUpdates(s))}dispose(){if(this.flushTimer)clearTimeout(this.flushTimer),this.flushTimer=null;this.onDidChangeEmitter.dispose()}updateConfig(t,e){this.debounceMs=Math.max(30,t),this.maxPerFlush=Math.max(64,e)}provideFileDecoration(t){if(t.scheme!=="file")return;let e=this.workerClient.getRecord(t);if(!e)return;let i=Ae(e),o=[`Entropy ${(e.entropy*100).toFixed(0)}%`,`Complexity ${e.complexity}`,`Debt ${e.debt}`,`Freshness ${(e.freshness*100).toFixed(0)}%`];if(this.tooltipAugmentProvider)o.push(...this.tooltipAugmentProvider(t));return{color:i,tooltip:o.join(`
`),propagate:!1}}enqueueExternalUpdates(t){this.enqueueUpdates(t)}enqueueUpdates(t){for(let e of t)this.pending.set(e.toString(),e);if(!this.flushTimer)this.flushTimer=setTimeout(()=>this.flush(),this.debounceMs)}flush(){if(this.flushTimer=null,this.pending.size===0)return;let t=Array.from(this.pending.values()).slice(0,this.maxPerFlush);for(let e of t)this.pending.delete(e.toString());if(this.onDidChangeEmitter.fire(t),this.pending.size>0)this.flushTimer=setTimeout(()=>this.flush(),this.debounceMs)}}function Ae(t){let e=_e(t.entropy*0.78+(1-t.freshness)*0.22);if(e>=0.72)return new A.ThemeColor("problemsErrorIcon.foreground");if(e>=0.45)return new A.ThemeColor("charts.yellow");return new A.ThemeColor("charts.green")}function _e(t){if(t<0)return 0;if(t>1)return 1;return t}var _=h(require("path")),b=h(require("vscode"));class F{extensionUri;workerClient;static viewType="chthonic.abyssalView";disposables=[];view=null;rootPath=null;constructor(t,e){this.extensionUri=t;this.workerClient=e;this.disposables.push(this.workerClient.onDidUpdateGraph((i)=>this.postMessage({type:"graph",graph:i})),this.workerClient.onDidUpdateSnapshot((i)=>this.postMessage({type:"snapshot",snapshot:i})))}setRootPath(t){this.rootPath=t}dispose(){this.disposables.forEach((t)=>t.dispose()),this.disposables.length=0}resolveWebviewView(t,e,i){this.view=t,t.webview.options={enableScripts:!0,localResourceRoots:[this.extensionUri]},t.webview.html=this.getHtml(t.webview),t.webview.onDidReceiveMessage((o)=>{this.handleMessage(o)})}handleMessage(t){if(!t||typeof t!=="object")return;let e=t;if(!e.type)return;if(e.type==="ready"){this.postMessage({type:"snapshot",snapshot:this.workerClient.getSnapshot()}),this.workerClient.requestGraph(260);return}if(e.type==="requestGraph"){this.workerClient.requestGraph(260);return}if(e.type==="requestScan"||e.type==="requestSediment"){this.workerClient.rescanNow(),this.workerClient.requestGraph(260);return}if(e.type==="openFile"&&e.path&&this.rootPath){let i=_.normalize(e.path);if(i.startsWith("..")||_.isAbsolute(i))return;let o=_.join(this.rootPath,i),s=b.Uri.file(o);b.workspace.openTextDocument(s).then((a)=>{b.window.showTextDocument(a,{preview:!1})},()=>{b.window.showWarningMessage(`Unable to open ${e.path}`)})}}postMessage(t){if(!this.view)return;this.view.webview.postMessage(t)}getHtml(t){let e=qe(),i=t.asWebviewUri(b.Uri.joinPath(this.extensionUri,"media","abyssalPane.js")),o=t.asWebviewUri(b.Uri.joinPath(this.extensionUri,"media","wasm","pkg","entropy_renderer_wasm.js")),s=t.asWebviewUri(b.Uri.joinPath(this.extensionUri,"media","wasm","pkg","entropy_renderer_wasm_bg.wasm")),a=t.asWebviewUri(b.Uri.joinPath(this.extensionUri,"media","wasm","pkg","chthonic_loom.js")),l=t.asWebviewUri(b.Uri.joinPath(this.extensionUri,"media","wasm","pkg","chthonic_loom_bg.wasm")),c=["default-src 'none'",`img-src ${t.cspSource} data:`,`style-src ${t.cspSource} 'unsafe-inline'`,`script-src 'nonce-${e}' ${t.cspSource}`,`connect-src ${t.cspSource}`].join("; "),f=JSON.stringify({wasmModuleUri:o.toString(),wasmBinaryUri:s.toString(),loomWasmModuleUri:a.toString(),loomWasmBinaryUri:l.toString()});return`<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="${c}">
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
        window.__CHTHONIC_ABYSSAL__ = ${f};
    </script>
    <script nonce="${e}" type="module" src="${i}"></script>
</body>
</html>`}}function qe(){let e="";for(let i=0;i<32;i+=1)e+="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789".charAt(Math.floor(Math.random()*62));return e}var pt=h(require("fs/promises")),L=h(require("path")),ut=h(require("vscode"));var It=h(require("crypto"));class rt{leaves=new Map;dirty=!1;upsert(t){let e=Je(t.path),i=Oe(e,t);if(this.leaves.get(e)!==i)return this.leaves.set(e,i),this.dirty=!0,!0;return!1}hasDirty(){return this.dirty}settle(t){if(!this.dirty||this.leaves.size===0)return null;let e=He(Array.from(this.leaves.entries()).sort((i,o)=>i[0].localeCompare(o[0])));return this.dirty=!1,{reason:t,rootHash:e,leafCount:this.leaves.size,generatedAt:Date.now()}}}function Oe(t,e){let i=[t,e.entropy.toFixed(6),e.complexity,e.debt,e.freshness.toFixed(6),e.ruffViolations,e.updatedAt].join("|");return z(i)}function He(t){if(t.length===0)return z("EMPTY");let e=t.map(([i,o])=>z(`${i}:${o}`));while(e.length>1){let i=[];for(let o=0;o<e.length;o+=2){let s=e[o],a=e[o+1]??e[o];i.push(z(`${s}${a}`))}e=i}return e[0]}function z(t){return It.createHash("sha256").update(t,"utf8").digest("hex")}function Je(t){return t.replace(/\\/g,"/")}var T=h(require("fs")),S=h(require("path")),at=require("child_process"),W=h(require("vscode"));function M(t,e){let i="",o=(s)=>{let a=s.trim();if(!a)return;try{let l=JSON.parse(a);if(!l||typeof l!=="object"||Array.isArray(l))throw Error("JSONL payload must be an object");t(l)}catch(l){e(l instanceof Error?l:Error(String(l)))}};return{push(s){i+=s.toString();while(!0){let a=i.indexOf(`
`);if(a<0)return;let l=i.slice(0,a);i=i.slice(a+1),o(l)}},flush(){if(!i.trim()){i="";return}o(i),i=""}}}var __dirname="C:\\Users\\erdno\\chthonic-archive\\extensions\\chthonic-archive\\src\\polyglot";class lt{output;rootPath=null;sidecarRootPath=null;pythonSidecar=null;rubySidecar=null;onDidReceiveRuffEmitter=new W.EventEmitter;onDidReceiveRuff=this.onDidReceiveRuffEmitter.event;onDidReceiveLoreEmitter=new W.EventEmitter;onDidReceiveLore=this.onDidReceiveLoreEmitter.event;onDidReceiveSidecarErrorEmitter=new W.EventEmitter;onDidReceiveSidecarError=this.onDidReceiveSidecarErrorEmitter.event;constructor(t){this.output=t}start(t){if(this.rootPath=t,this.sidecarRootPath=Ie(t),!this.sidecarRootPath){let i=`sidecar scripts not found. checked: ${Vt(t).join(", ")}`;this.output.appendLine(`[polyglot] ${i}`),this.fireSidecarError("python",i),this.fireSidecarError("ruby",i);return}this.output.appendLine(`[polyglot] sidecar root: ${this.sidecarRootPath}`),this.startPythonSidecar(),this.startRubySidecar()}requestScan(t){if(!this.pythonSidecar||this.pythonSidecar.killed)this.startPythonSidecar();this.writeJson(this.pythonSidecar,t)}requestLore(t){if(!this.rubySidecar||this.rubySidecar.killed)this.startRubySidecar();this.writeJson(this.rubySidecar,t)}dispose(){this.pythonSidecar?.kill(),this.rubySidecar?.kill(),this.pythonSidecar=null,this.rubySidecar=null,this.sidecarRootPath=null,this.onDidReceiveRuffEmitter.dispose(),this.onDidReceiveLoreEmitter.dispose(),this.onDidReceiveSidecarErrorEmitter.dispose()}startPythonSidecar(){if(!this.rootPath||this.pythonSidecar)return;if(!this.sidecarRootPath){this.fireSidecarError("python","sidecar root unresolved; python scan unavailable.");return}let t=S.join(this.sidecarRootPath,"python","entropy_scan.py");if(!T.existsSync(t)){this.fireSidecarError("python",`python sidecar missing: ${t}`);return}let e=S.join(this.sidecarRootPath,"venv",process.platform==="win32"?"Scripts":"bin"),i=S.join(e,process.platform==="win32"?"python.exe":"python"),o=T.existsSync(i),s=o?i:"uv",a=o?[t,"--stdio"]:["run",t,"--stdio"];if(!o)this.output.appendLine("[polyglot:python] .chthonic/venv not found, falling back to uv run.");this.pythonSidecar=at.spawn(s,a,{cwd:this.rootPath,stdio:["pipe","pipe","pipe"],env:Ve(process.env,e)});let l=M((c)=>this.handlePythonPayload(c),(c)=>this.output.appendLine(`[polyglot:python] invalid JSONL payload: ${c.message}`));this.pythonSidecar.stdout?.on("data",(c)=>l.push(c)),this.pythonSidecar.stderr?.on("data",(c)=>{this.output.appendLine(`[polyglot:python] ${c.toString().trimEnd()}`)}),this.pythonSidecar.on("error",(c)=>{this.fireSidecarError("python",`failed to spawn: ${c.message}`),this.pythonSidecar=null}),this.pythonSidecar.on("exit",(c)=>{l.flush(),this.output.appendLine(`[polyglot:python] exited with code ${c??-1}`),this.pythonSidecar=null})}startRubySidecar(){if(!this.rootPath||this.rubySidecar)return;if(!this.sidecarRootPath){this.fireSidecarError("ruby","sidecar root unresolved; lore unavailable.");return}let t=S.join(this.sidecarRootPath,"ruby","lore.rb");if(!T.existsSync(t)){this.fireSidecarError("ruby",`ruby sidecar missing: ${t}`);return}this.rubySidecar=at.spawn("ruby",[t],{cwd:this.rootPath,stdio:["pipe","pipe","pipe"]});let e=M((i)=>this.handleRubyPayload(i),(i)=>this.output.appendLine(`[polyglot:ruby] invalid JSONL payload: ${i.message}`));this.rubySidecar.stdout?.on("data",(i)=>e.push(i)),this.rubySidecar.stderr?.on("data",(i)=>{this.output.appendLine(`[polyglot:ruby] ${i.toString().trimEnd()}`)}),this.rubySidecar.on("error",(i)=>{this.fireSidecarError("ruby",`failed to spawn: ${i.message}`),this.rubySidecar=null}),this.rubySidecar.on("exit",(i)=>{e.flush(),this.output.appendLine(`[polyglot:ruby] exited with code ${i??-1}`),this.rubySidecar=null})}writeJson(t,e){if(!t?.stdin||t.killed)return;try{t.stdin.write(`${JSON.stringify(e)}
`)}catch(i){this.output.appendLine(`[polyglot] sidecar write failed: ${Ne(i)}`)}}fireSidecarError(t,e){this.onDidReceiveSidecarErrorEmitter.fire({type:"error",source:t,message:e}),this.output.appendLine(`[polyglot:${t}] ${e}`)}handlePythonPayload(t){if(t.type==="ruff-summary"){let e=t;this.onDidReceiveRuffEmitter.fire(e);return}if(t.type==="error"){let e=String(t.message??"python sidecar error");this.output.appendLine(`[polyglot:python] ${e}`),this.onDidReceiveSidecarErrorEmitter.fire({type:"error",source:"python",message:e})}}handleRubyPayload(t){if(t.type==="lore"){this.onDidReceiveLoreEmitter.fire(t);return}if(t.type==="error"){let e=String(t.message??"ruby sidecar error");this.output.appendLine(`[polyglot:ruby] ${e}`),this.onDidReceiveSidecarErrorEmitter.fire({type:"error",source:"ruby",message:e})}}}function Ne(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}function Ie(t){for(let e of Vt(t))if(T.existsSync(S.join(e,"python","entropy_scan.py"))&&T.existsSync(S.join(e,"ruby","lore.rb")))return e;return null}function Vt(t){let e=[S.join(t,".chthonic"),S.join(t,"extensions","chthonic-archive",".chthonic"),S.resolve(__dirname,"..",".chthonic")];return Array.from(new Set(e))}function Ve(t,e){if(!T.existsSync(e))return t;let i=process.platform==="win32"?"Path":"PATH",o=t[i]??process.env[i]??"";return{...t,[i]:o?`${e}${S.delimiter}${o}`:e}}var Ut=h(require("fs")),Y=h(require("fs/promises")),k=h(require("path")),ct=require("child_process");class dt{output;rootPath=null;options={rpcUrl:"http://127.0.0.1:8899",autostartValidator:!1};ledgerFilePath=null;validatorProcess=null;hostProcess=null;requestCounter=1;pending=new Map;constructor(t){this.output=t}async start(t,e){this.rootPath=t,this.options=e;let i=k.join(t,".chthonic","ledger");if(await Y.mkdir(i,{recursive:!0}),this.ledgerFilePath=k.join(i,"entropy-settlements.jsonl"),e.autostartValidator)this.startValidator();this.startHostProcess()}async commitEntropy(t){if(!this.rootPath||!this.ledgerFilePath)return{mode:"offline",detail:"Ledger host not started"};let e={...t,rpcUrl:this.options.rpcUrl,recordedAt:Date.now()},i={mode:"offline",detail:"Rust ledger host unavailable; persisted settlement locally."};try{i=await this.submitToHost(t)}catch(o){this.output.appendLine(`[ledger-rust] submit failed: ${ze(o)}`)}return await Y.appendFile(this.ledgerFilePath,`${JSON.stringify({...e,receipt:i})}
`,"utf8"),i}dispose(){for(let[t,e]of this.pending)e.reject(Error(`request ${t} cancelled`));this.pending.clear(),this.hostProcess?.kill(),this.hostProcess=null,this.validatorProcess?.kill(),this.validatorProcess=null}startHostProcess(){if(!this.rootPath||this.hostProcess)return;let t=Ue(this.rootPath,this.options.hostBinaryPath),e=this.options.walletPath??k.join(this.rootPath,".chthonic","wallets","payer.json"),i=this.options.idlPath??k.join(this.rootPath,".chthonic","wallets","entropy_ledger.json");this.hostProcess=ct.spawn(t,["--wallet",e,"--idl",i,"--rpc-url",this.options.rpcUrl],{cwd:this.rootPath,stdio:["pipe","pipe","pipe"]});let o=M((s)=>this.handleHostPayload(s),(s)=>this.output.appendLine(`[ledger-rust] invalid JSON payload: ${s.message}`));this.hostProcess.stdout?.on("data",(s)=>o.push(s)),this.hostProcess.stderr?.on("data",(s)=>{this.output.appendLine(`[ledger-rust] ${s.toString().trimEnd()}`)}),this.hostProcess.on("error",(s)=>{this.output.appendLine(`[ledger-rust] failed to spawn host: ${s.message}`),this.rejectAllPending(Error(`host spawn failed: ${s.message}`)),this.hostProcess=null}),this.hostProcess.on("exit",(s)=>{o.flush(),this.output.appendLine(`[ledger-rust] host exited with code ${s??-1}`),this.rejectAllPending(Error("ledger host exited")),this.hostProcess=null})}async submitToHost(t){if(!this.hostProcess||this.hostProcess.killed)this.startHostProcess();if(!this.hostProcess?.stdin||this.hostProcess.killed)return{mode:"offline",detail:"Rust host binary is missing or not executable."};let e=this.requestCounter++,i={jsonrpc:"2.0",id:e,method:"submit_entropy",params:{entropy_score:Math.max(0,Math.round(t.leafCount*17+13)),merkle_root:t.rootHash,leaf_count:t.leafCount,reason:t.reason}};return await new Promise((s,a)=>{this.pending.set(e,{resolve:s,reject:a}),this.hostProcess?.stdin?.write(`${JSON.stringify(i)}
`,(l)=>{if(!l)return;this.pending.delete(e),a(l)})})}handleHostPayload(t){let e=t.id;if(typeof e!=="number")return;let i=this.pending.get(e);if(!i)return;if(this.pending.delete(e),t.error&&typeof t.error==="object"){let s=t;i.resolve({mode:"offline",detail:`Rust ledger error ${s.error.code}: ${s.error.message}`});return}let o=t;i.resolve({mode:"validator-rust",txSignature:o.result.signature,detail:`Rust anchor-client submission accepted${o.result.slot?` (slot ${o.result.slot})`:""}.`})}rejectAllPending(t){for(let[e,i]of this.pending)this.pending.delete(e),i.reject(t)}startValidator(){if(!this.rootPath||this.validatorProcess)return;let t=Ge(this.rootPath),e=Fe(this.options.rpcUrl)??8899,i=k.join(this.rootPath,".chthonic","solana-ledger");this.validatorProcess=ct.spawn(t,["--ledger",i,"--rpc-port",String(e),"--reset","--quiet"],{cwd:this.rootPath,stdio:["ignore","pipe","pipe"]}),this.validatorProcess.stdout?.on("data",(o)=>{this.output.appendLine(`[solana] ${o.toString().trimEnd()}`)}),this.validatorProcess.stderr?.on("data",(o)=>{this.output.appendLine(`[solana] ${o.toString().trimEnd()}`)}),this.validatorProcess.on("error",(o)=>{this.output.appendLine(`[solana] validator spawn error: ${o.message}`),this.validatorProcess=null}),this.validatorProcess.on("exit",(o)=>{this.output.appendLine(`[solana] validator exited with code ${o??-1}`),this.validatorProcess=null})}}function Ue(t,e){if(e)return e;let i=process.platform==="win32"?"entropy-ledger-host.exe":"entropy-ledger-host";return k.join(t,"native","target","release",i)}function Ge(t){let e=process.platform==="win32"?"solana-test-validator.exe":"solana-test-validator",i=k.join(t,".chthonic","bin",e);if(Ut.existsSync(i))return i;return process.platform==="win32"?"solana-test-validator":e}function Fe(t){try{let e=new URL(t);if(!e.port)return null;let i=Number(e.port);return Number.isFinite(i)?i:null}catch{return null}}function ze(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}class ht{output;options;backend=null;constructor(t,e){this.output=t;this.options=e}async start(t){this.backend=this.options.mode==="bankrun"?new Gt(this.output):new Ft(this.output,this.options),await this.backend.start(t)}async commitEntropy(t){if(!this.backend)return{mode:"offline",detail:"LedgerBroker backend not initialized."};return this.backend.commitEntropy(t)}dispose(){this.backend?.dispose(),this.backend=null}}class Gt{output;sequence=0;constructor(t){this.output=t}async start(t){this.output.appendLine("[ledger] phantom mode active (bankrun simulation).")}async commitEntropy(t){return this.sequence+=1,{mode:"bankrun",txSignature:`bankrun-${t.rootHash.slice(0,20)}-${this.sequence}`,detail:"In-memory bankrun simulation accepted the entropy settlement."}}dispose(){}}class Ft{options;client;constructor(t,e){this.options=e;this.client=new dt(t)}async start(t){await this.client.start(t,{rpcUrl:this.options.rpcUrl,autostartValidator:this.options.autostartValidator,hostBinaryPath:this.options.hostBinaryPath,walletPath:this.options.walletPath,idlPath:this.options.idlPath})}async commitEntropy(t){return this.client.commitEntropy(t)}dispose(){this.client.dispose()}}class ft{output;workerClient;options;requestDecorationRefresh;broker;merkle=new rt;ledger;tooltipAugments=new Map;rootPath=null;scanTimer=null;settleTimer=null;gitPollTimer=null;gitHeadSnapshot=null;pendingSettleReason=null;disposables=[];constructor(t,e,i,o){this.output=t;this.workerClient=e;this.options=i;this.requestDecorationRefresh=o;this.broker=new lt(t),this.ledger=new ht(t,{mode:this.options.ledgerMode,rpcUrl:this.options.solanaRpcUrl,autostartValidator:this.options.solanaAutostartValidator,hostBinaryPath:this.options.solanaLedgerHostBinaryPath,walletPath:this.options.solanaWalletPath,idlPath:this.options.solanaIdlPath}),this.disposables.push(this.broker.onDidReceiveRuff((s)=>this.applyRuffSummary(s)),this.broker.onDidReceiveLore((s)=>this.applyLore(s)),this.workerClient.onDidUpdateRecords((s)=>this.captureEntropyLeaves(s)))}async start(t){if(this.rootPath=t,!this.options.enabled)return;this.broker.start(t),await this.ledger.start(t),this.broker.requestScan({type:"scan",reason:"manual",root:t}),this.startScanLoop(),this.startGitWatcher()}onDidSaveDocument(t){if(!this.rootPath||!this.options.enabled||t.uri.scheme!=="file")return;let e=zt(this.rootPath,t.uri.fsPath);if(!e)return;this.broker.requestScan({type:"scan",reason:"save",root:this.rootPath,files:[e]}),this.scheduleSettlement("save")}requestManualScan(){if(!this.rootPath||!this.options.enabled)return;this.broker.requestScan({type:"scan",reason:"manual",root:this.rootPath})}getTooltipFragments(t){if(!this.rootPath||t.scheme!=="file")return[];let e=zt(this.rootPath,t.fsPath);if(!e)return[];let i=this.tooltipAugments.get(e);if(!i)return[];let o=[];if(i.ruffViolations>0){if(o.push(`Ruff ${i.ruffViolations} violation${i.ruffViolations===1?"":"s"}`),i.ruffCodeSummary)o.push(`Codes ${i.ruffCodeSummary}`)}if(i.loreLine)o.push(i.loreLine);return o}dispose(){if(this.scanTimer)clearInterval(this.scanTimer),this.scanTimer=null;if(this.settleTimer)clearTimeout(this.settleTimer),this.settleTimer=null;if(this.gitPollTimer)clearInterval(this.gitPollTimer),this.gitPollTimer=null;this.broker.dispose(),this.ledger.dispose(),this.disposables.forEach((t)=>t.dispose()),this.disposables.length=0}captureEntropyLeaves(t){if(!this.options.enabled)return;let e=0;for(let i of t){let o=this.workerClient.getRecord(i);if(!o)continue;let s=this.tooltipAugments.get(o.path);if(this.merkle.upsert({path:o.path,entropy:o.entropy,complexity:o.complexity,debt:o.debt,freshness:o.freshness,ruffViolations:s?.ruffViolations??0,updatedAt:Date.now()}))e+=1}if(e>0)this.scheduleSettlement("interval")}applyRuffSummary(t){if(!this.rootPath||!this.options.enabled)return;let e=t.files,i=[],o=0;for(let s of e){let a=this.tooltipAugments.get(s.path),l={ruffViolations:s.violations,ruffCodeSummary:Ye(s.byCode),loreLine:a?.loreLine};this.tooltipAugments.set(s.path,l);let c=ut.Uri.file(L.join(this.rootPath,s.path));i.push(c);let f=this.workerClient.getRecord(c);if(f){if(this.merkle.upsert({path:f.path,entropy:f.entropy,complexity:f.complexity,debt:f.debt,freshness:f.freshness,ruffViolations:s.violations,updatedAt:Date.now()}))o+=1;if(f.entropy>=0.45||s.violations>0)this.broker.requestLore({type:"lore-request",root:this.rootPath,path:s.path,entropy:f.entropy,violations:s.violations})}}if(i.length>0)this.requestDecorationRefresh(i);if(o>0||this.merkle.hasDirty())this.scheduleSettlement(t.reason)}applyLore(t){if(!this.rootPath||!this.options.enabled)return;if(t.root!==this.rootPath)return;let e=this.tooltipAugments.get(t.path);this.tooltipAugments.set(t.path,{ruffViolations:e?.ruffViolations??t.violations,ruffCodeSummary:e?.ruffCodeSummary,loreLine:t.line}),this.requestDecorationRefresh([ut.Uri.file(L.join(this.rootPath,t.path))])}startScanLoop(){if(this.scanTimer||!this.rootPath)return;let t=Math.max(this.options.pythonScanIntervalMs,1e4);this.scanTimer=setInterval(()=>{if(!this.rootPath)return;this.broker.requestScan({type:"scan",reason:"interval",root:this.rootPath})},t)}startGitWatcher(){if(!this.rootPath||this.gitPollTimer)return;this.gitHeadSnapshot=null,this.gitPollTimer=setInterval(async()=>{if(!this.rootPath)return;let t=await We(this.rootPath);if(!t)return;if(!this.gitHeadSnapshot){this.gitHeadSnapshot=t;return}if(t!==this.gitHeadSnapshot){if(this.gitHeadSnapshot=t,this.output.appendLine("[polyglot] git HEAD changed, scheduling Merkle settlement."),this.rootPath)this.broker.requestScan({type:"scan",reason:"commit",root:this.rootPath});this.scheduleSettlement("commit")}},6000)}scheduleSettlement(t){if(!this.options.enabled)return;if(this.pendingSettleReason=Ke(this.pendingSettleReason,t),this.settleTimer)clearTimeout(this.settleTimer);this.settleTimer=setTimeout(()=>{this.settleTimer=null,this.flushSettlement()},Math.max(this.options.settleDebounceMs,300))}async flushSettlement(){let t=this.pendingSettleReason??"manual";this.pendingSettleReason=null;let e=this.merkle.settle(t);if(!e)return;let i=await this.ledger.commitEntropy(e),o=[`[polyglot] settled Merkle root ${e.rootHash.slice(0,16)}...`,`leaves=${e.leafCount}`,`mode=${i.mode}`];if(i.txSignature)o.push(`tx=${i.txSignature}`);o.push(`detail=${i.detail}`),this.output.appendLine(o.join(" "))}}async function We(t){let e=L.join(t,".git"),i=L.join(e,"HEAD"),o="";try{o=await pt.readFile(i,"utf8")}catch{return null}let s=o.trim();if(!s)return null;if(!s.startsWith("ref:"))return s;let a=s.slice(4).trim(),l=L.join(e,a);try{let c=await pt.readFile(l,"utf8");return`ref:${a}:${c.trim()}`}catch{return`ref:${a}:missing`}}function zt(t,e){let i=L.relative(t,e);if(!i||i.startsWith("..")||L.isAbsolute(i))return null;return i.replace(/\\/g,"/")}function Ye(t){let e=Object.entries(t).filter((i)=>i[1]>0).sort((i,o)=>o[1]-i[1]||i[0].localeCompare(o[0])).slice(0,3).map(([i,o])=>`${i}×${o}`);return e.length>0?e.join(", "):void 0}function Ke(t,e){if(!t)return e;return Wt(e)>=Wt(t)?e:t}function Wt(t){switch(t){case"commit":return 4;case"save":return 3;case"manual":return 2;case"interval":default:return 1}}var Yt=h(require("path")),Kt=require("child_process"),C=h(require("vscode"));class mt{output;headlessVulkan;daemonBinaryOverride;eolApiBase;entropyMonitorIntervalMs;rootPath=null;daemonProcess=null;requestCounter=1;pending=new Map;onDidReceiveManifestEmitter=new C.EventEmitter;onDidReceiveManifest=this.onDidReceiveManifestEmitter.event;onDidReceiveEnvEmitter=new C.EventEmitter;onDidReceiveEnv=this.onDidReceiveEnvEmitter.event;onDidReceiveSedimentEmitter=new C.EventEmitter;onDidReceiveSediment=this.onDidReceiveSedimentEmitter.event;onDidReceiveSedimentChunkEmitter=new C.EventEmitter;onDidReceiveSedimentChunk=this.onDidReceiveSedimentChunkEmitter.event;onDidReceiveSynapseEmitter=new C.EventEmitter;onDidReceiveSynapse=this.onDidReceiveSynapseEmitter.event;onDidReceiveEntropyStateEmitter=new C.EventEmitter;onDidReceiveEntropyState=this.onDidReceiveEntropyStateEmitter.event;onDidReceiveFiredancerSurgeEmitter=new C.EventEmitter;onDidReceiveFiredancerSurge=this.onDidReceiveFiredancerSurgeEmitter.event;constructor(t,e,i,o="https://endoflife.date/api/v1",s=21600000){this.output=t;this.headlessVulkan=e;this.daemonBinaryOverride=i;this.eolApiBase=o;this.entropyMonitorIntervalMs=s}start(t){this.rootPath=t,this.startDaemon()}async requestSediment(t,e){return this.submitRequest("reactor/sediment",{max_layers:t,max_files:e})}async requestSedimentStream(t,e,i=220){return this.submitRequest("reactor/sediment_stream",{max_layers:t,max_files:e,chunk_size:i})}async requestSedimentSynapse(t,e,i=220){return this.submitRequest("reactor/sediment_synapse",{max_layers:t,max_files:e,chunk_size:i})}async requestDetect(){return this.submitRequest("anno/detect",{})}async requestProvision(){return this.submitRequest("anno/provision",{})}async requestEntropyState(){return this.submitRequest("reactor/entropy_state",{})}dispose(){for(let[,t]of this.pending)t.reject(Error("AnnoClient disposed"));this.pending.clear(),this.daemonProcess?.kill(),this.daemonProcess=null,this.onDidReceiveManifestEmitter.dispose(),this.onDidReceiveEnvEmitter.dispose(),this.onDidReceiveSedimentEmitter.dispose(),this.onDidReceiveSedimentChunkEmitter.dispose(),this.onDidReceiveSynapseEmitter.dispose(),this.onDidReceiveEntropyStateEmitter.dispose(),this.onDidReceiveFiredancerSurgeEmitter.dispose()}startDaemon(){if(!this.rootPath||this.daemonProcess)return;let t=this.daemonBinaryOverride??Xe(this.rootPath),e=["--workspace",this.rootPath];if(this.headlessVulkan)e.push("--headless-vulkan");this.daemonProcess=Kt.spawn(t,e,{cwd:this.rootPath,env:{...process.env,CHTHONIC_EOL_API_BASE:this.eolApiBase,CHTHONIC_ENTROPY_MONITOR_INTERVAL_MS:String(Math.max(60000,this.entropyMonitorIntervalMs))},stdio:["pipe","pipe","pipe"]});let i=M((o)=>this.handlePayload(o),(o)=>this.output.appendLine(`[daemon] invalid JSONL: ${o.message}`));this.daemonProcess.stdout?.on("data",(o)=>i.push(o)),this.daemonProcess.stderr?.on("data",(o)=>{this.output.appendLine(`[daemon] ${o.toString().trimEnd()}`)}),this.daemonProcess.on("error",(o)=>{this.output.appendLine(`[daemon] spawn failed: ${o.message}`),this.rejectAllPending(Error(`daemon spawn failed: ${o.message}`)),this.daemonProcess=null}),this.daemonProcess.on("exit",(o)=>{i.flush(),this.output.appendLine(`[daemon] exited with code ${o??-1}`),this.rejectAllPending(Error("daemon exited")),this.daemonProcess=null})}handlePayload(t){if("method"in t&&!("id"in t)){this.handleNotification(t);return}if("id"in t&&typeof t.id==="number")this.handleResponse(t)}handleNotification(t){let{method:e,params:i}=t;switch(e){case"anno/manifest":this.onDidReceiveManifestEmitter.fire(i),this.output.appendLine(`[daemon] ANNO manifest received (${i.languages?.length??0} languages)`);break;case"anno/env":this.onDidReceiveEnvEmitter.fire(i),this.output.appendLine("[daemon] env report received");break;case"reactor/status":{let o=i.status??"unknown";this.output.appendLine(`[daemon] reactor status: ${o}`);break}case"reactor/sedimentChunk":this.onDidReceiveSedimentChunkEmitter.fire(i);break;case"reactor/synapse":this.onDidReceiveSynapseEmitter.fire(i),this.output.appendLine(`[daemon] synapse status: ${i.status} (${i.mode})`);break;case"reactor/entropyState":this.onDidReceiveEntropyStateEmitter.fire(i),this.output.appendLine(`[daemon] entropy state: ${i.status} (${Math.round((i.decay_score??0)*100)}%)`);break;case"reactor/firedancerSurge":this.onDidReceiveFiredancerSurgeEmitter.fire(i),this.output.appendLine(`[daemon] firedancer slot ${i.slot} tps ${i.simulated_tps} (${i.surge?"surge":"flow"})`);break;default:this.output.appendLine(`[daemon] unknown notification: ${e}`)}}handleResponse(t){let e=t.id,i=this.pending.get(e);if(!i)return;if(this.pending.delete(e),t.error&&typeof t.error==="object"){let o=t.error;i.reject(Error(o.message));return}i.resolve(t.result)}submitRequest(t,e){if(!this.daemonProcess?.stdin||this.daemonProcess.killed)this.startDaemon();if(!this.daemonProcess?.stdin)return Promise.reject(Error("daemon not available"));let i=this.requestCounter++,o={jsonrpc:"2.0",id:i,method:t,params:e};return new Promise((s,a)=>{this.pending.set(i,{resolve:s,reject:a}),this.daemonProcess?.stdin?.write(`${JSON.stringify(o)}
`,(l)=>{if(l)this.pending.delete(i),a(l)})})}rejectAllPending(t){for(let[e,i]of this.pending)this.pending.delete(e),i.reject(t)}}function Xe(t){let e=process.platform==="win32"?"chthonic-daemon.exe":"chthonic-daemon";return Yt.join(t,"native","target","release",e)}var D=h(require("vscode"));class yt{output;envCollection;disposed=!1;constructor(t,e){this.output=t;this.envCollection=e}async activate(){if(this.disposed)return;try{await D.commands.executeCommand("workbench.action.closeSidebar"),await D.commands.executeCommand("workbench.action.terminal.moveToSidePanel"),await D.commands.executeCommand("workbench.action.toggleAuxiliaryBar"),await D.commands.executeCommand("workbench.action.toggleMaximizedPanel"),await D.commands.executeCommand("workbench.action.focusActiveEditorGroup"),this.output.appendLine("[cockpit] layout activated: sidebar=closed, terminal=AuxBar, panel=maximized, editor=Center")}catch(t){this.output.appendLine(`[cockpit] layout activation failed: ${Ze(t)}`)}}applyTerminalEnv(t){if(this.disposed)return;if(!t.path_mutations.length)return;let e=t.path_mutations.sort((o,s)=>o.priority-s.priority).map((o)=>o.path),i=process.platform==="win32"?";":":";for(let o of e)this.envCollection.prepend("PATH",`${o}${i}`);for(let o of D.window.terminals)if(process.platform==="win32")for(let s of e)o.sendText(`$env:PATH = "${s};$env:PATH"`,!0);else for(let s of e)o.sendText(`export PATH="${s}:$PATH"`,!0);if(this.output.appendLine(`[cockpit] terminal env updated: ${e.length} PATH mutations applied`),t.warnings.length>0)for(let o of t.warnings)this.output.appendLine(`[cockpit] warning: ${o}`)}dispose(){this.disposed=!0}}function Ze(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}var Zt=h(require("fs")),vt=h(require("path"));class SynapseBridge{output;extensionRoot;binding=null;reader=null;descriptor=null;transportMode;constructor(t,e,i){this.output=t;this.extensionRoot=e;this.transportMode=Qe(i)}updateDescriptor(t){if(this.descriptor=t,this.transportMode==="jsonl"){this.output.appendLine("[synapse] disabled by transport=jsonl");return}if(t.status!=="ready"||t.mode!=="shared_memory"||!t.shm_id){this.output.appendLine(`[synapse] unavailable: ${t.reason??t.status}`);return}try{let e=this.ensureBindingLoaded();this.reader=new e.SynapseReader(t.shm_id,t.event_name??void 0),this.output.appendLine(`[synapse] connected (shm=${t.shm_id})`)}catch(e){this.reader=null,this.output.appendLine(`[synapse] init failed, falling back to JSONL: ${ti(e)}`)}}isReady(){if(this.transportMode==="jsonl")return!1;return this.reader!==null&&this.descriptor?.status==="ready"&&this.descriptor.mode==="shared_memory"}async drain(t,e){if(!this.reader||t.transport!=="shared_memory")return 0;let i=Math.max(0,t.chunks_written??t.total_chunks??0);if(i===0)return 0;let o=0,s=Date.now();while(o<i&&Date.now()-s<4000){if(!this.reader.wait_for_signal(120)){await Xt();continue}while(!0){let l=this.reader.read_chunk();if(!l||l.byteLength===0)break;let c=new Uint8Array(l.buffer,l.byteOffset,l.byteLength),f=new Uint8Array(c.byteLength);if(f.set(c),e(f),o+=1,o>=i)break}await Xt()}if(o<i)this.output.appendLine(`[synapse] partial drain: ${o}/${i}`);return o}dispose(){this.reader=null}ensureBindingLoaded(){if(this.binding)return this.binding;let candidates=[vt.join(this.extensionRoot,"src","reactor","synapse.node"),vt.join(this.extensionRoot,"native","target","release","synapse.node")],existing=candidates.find((t)=>Zt.existsSync(t));if(!existing)throw Error(`synapse.node not found in ${candidates.join(", ")}`);let req=eval("require");return this.binding=req(existing),this.binding}}function Qe(t){let e=t.trim().toLowerCase();if(e==="shared_memory")return"shared_memory";if(e==="jsonl")return"jsonl";return"auto"}function ti(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}async function Xt(){await new Promise((t)=>setTimeout(t,0))}var x=h(require("vscode"));var Qt=h(require("fs")),te=h(require("path")),ei=[{file:"mise.toml",weight:16},{file:".mise.toml",weight:6},{file:"Cargo.toml",weight:20},{file:"native/Cargo.toml",weight:8},{file:"anno-manifest.toml",weight:8},{file:"uv.lock",weight:10},{file:".python-version",weight:5},{file:".ruby-version",weight:10},{file:"Gemfile",weight:6},{file:"go.mod",weight:10},{file:".node-version",weight:4},{file:".nvmrc",weight:4},{file:"package.json",weight:5},{file:"bun.lock",weight:4}];async function ee(t){let e=ei.map((s)=>{let a=te.join(t,s.file),l=Qt.existsSync(a);return{...s,present:l}}),i=Math.min(100,e.reduce((s,a)=>a.present?s+a.weight:s,0)),o=ii(i);return{score:i,tier:o,markers:e,present:e.filter((s)=>s.present).map((s)=>s.file),missing:e.filter((s)=>!s.present).map((s)=>s.file)}}function ie(t){switch(t){case"loom":return"loom.svg";case"lens":return"lens.svg";default:return"gate.svg"}}function ii(t){if(t>=80)return"loom";if(t>=45)return"lens";return"gate"}class gt{extensionUri;output;containerId;fallbackItem;fallbackNoticeEmitted=!1;latestRustification=null;latestEntropy=null;constructor(t,e,i="chthonic-archive"){this.extensionUri=t;this.output=e;this.containerId=i;this.fallbackItem=x.window.createStatusBarItem(x.StatusBarAlignment.Left,47),this.fallbackItem.command="chthonic.refreshRustification",this.fallbackItem.tooltip="Rustification score and activity bar icon fallback",this.fallbackItem.show()}async update(t){this.latestRustification=t,await x.commands.executeCommand("setContext","chthonic.rustificationTier",t.tier),await x.commands.executeCommand("setContext","chthonic.rustificationScore",t.score),await this.apply()}async updateEntropy(t){this.latestEntropy=t,await x.commands.executeCommand("setContext","chthonic.decayStatus",t.status),await x.commands.executeCommand("setContext","chthonic.decayScore",Math.round(t.decay_score*100)),await this.apply()}dispose(){this.fallbackItem.dispose()}async apply(){if(!this.fallbackNoticeEmitted)this.output.appendLine("[morph] dynamic Activity Bar icon updates are unavailable on stable API; using status lane fallback"),this.fallbackNoticeEmitted=!0;this.updateFallbackStatus()}resolveIconFile(){let t=this.latestEntropy;if(t){if(t.decay_score>0.5||t.status==="critical")return"hazard.svg";if(t.decay_score<0.2&&t.status==="pristine")return"gate.svg";return"lens.svg"}let e=this.latestRustification?.tier??"gate";return ie(e)}updateFallbackStatus(){let t=this.latestRustification,e=this.latestEntropy;if(!t){this.fallbackItem.text="$(pulse) Slab boot",this.fallbackItem.tooltip="Rustification score pending";return}let i=oi(t.tier),o=e?Math.round(e.decay_score*100):null,s=e?`${e.status} ${o}%`:"unknown";this.fallbackItem.text=`$(pulse) ${i} ${t.score}% · Decay ${o??"?"}%`,this.fallbackItem.tooltip=[`Rustification ${t.score}% (${t.tier})`,`Decay ${s}`,`Glyph: ${this.resolveIconFile()}`,`Present: ${t.present.join(", ")||"none"}`,`Missing: ${t.missing.join(", ")||"none"}`,e&&e.critical_tools.length>0?`Critical tools: ${e.critical_tools.join(", ")}`:void 0].filter(Boolean).join(`
`)}}function oi(t){switch(t){case"loom":return"Loom";case"lens":return"Lens";default:return"Gate"}}var q=h(require("vscode"));class St{output;constructor(t){this.output=t}async activate(){await this.applyCommandLayout(),await q.commands.executeCommand("workbench.view.extension.chthonic-archive"),await q.commands.executeCommand("chthonic.loomView.focus"),this.output.appendLine("[deep-focus] activated via stable command lane")}async applyCommandLayout(){try{await q.commands.executeCommand("workbench.action.terminal.moveToSidePanel"),await q.commands.executeCommand("workbench.action.toggleAuxiliaryBar"),await q.commands.executeCommand("workbench.action.focusActiveEditorGroup")}catch(t){this.output.appendLine(`[deep-focus] command layout failed: ${si(t)}`)}}}function si(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}var bt=h(require("vscode"));class Pt{output;constructor(t){this.output=t}async activate(){await this.applyCommandLayout(),await bt.commands.executeCommand("workbench.view.extension.chthonic-archive"),this.output.appendLine("[restore-order] completed via stable command lane")}async applyCommandLayout(){await ni(this.output,[["workbench.view.extension.chthonic-archive"],["chthonic.statusView.focus"],["workbench.action.moveFocusedViewToSecondarySidebar"],["chthonic.loomView.focus"],["workbench.action.moveFocusedViewToPanel"],["workbench.action.positionPanelBottom"],["workbench.action.focusActiveEditorGroup"]])}}async function ni(t,e){for(let i of e){let[o,...s]=i;try{await bt.commands.executeCommand(o,...s)}catch(a){t.appendLine(`[restore-order] command failed (${o}): ${ri(a)}`)}}}function ri(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}var O=h(require("vscode"));class K{static viewType="chthonic.loomView";view=null;report=null;snapshot=null;resolveWebviewView(t,e,i){this.view=t,t.webview.options={enableScripts:!0},t.webview.html=this.buildHtml(),t.webview.onDidReceiveMessage((o)=>{if(!o||typeof o!=="object")return;let s=o;if(s.type==="refresh")O.commands.executeCommand("chthonic.refreshRustification");if(s.type==="rescan")O.commands.executeCommand("chthonic.entropyRefresh");if(s.type==="heal")O.commands.executeCommand("chthonic.slabHeal");if(s.type==="deepFocus")O.commands.executeCommand("chthonic.deepFocus");if(s.type==="restoreOrder")O.commands.executeCommand("chthonic.restoreOrder")}),this.postState()}update(t){this.report=t,this.postState()}updateWorkspaceHealth(t){this.snapshot=t,this.postState()}dispose(){this.view=null}postState(){if(!this.view)return;this.view.webview.postMessage({type:"state",report:this.report,snapshot:this.snapshot})}buildHtml(){let t=ai();return`<!DOCTYPE html>
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
            }
        });
    </script>
</body>
</html>`}}function ai(){let e="";for(let i=0;i<24;i+=1)e+="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789".charAt(Math.floor(Math.random()*62));return e}var m=h(require("fs")),y=h(require("path")),X=h(require("child_process")),ne=h(require("vscode"));class Rt{output;envCollection;workspaceRoot;timer=null;running=!1;options={intervalMs:21600000,eolApiBase:"https://endoflife.date/api"};constructor(t,e,i){this.output=t;this.envCollection=e;this.workspaceRoot=i}start(t){this.options=t,this.stopTimer(),this.timer=setInterval(()=>{this.runNow("interval")},Math.max(60000,t.intervalMs))}async runNow(t="manual"){if(this.running){this.output.appendLine("[slab-heal] skipped; already running");return}this.running=!0;try{let e=await this.auditVsToolchain();if(e&&(!e.allRequiredComponentsPresent||!e.allCriticalBinariesPresent))this.output.appendLine(`[slab-heal] vs2026 audit drift detected: components=${e.missingComponentCount}, binaries=${e.missingBinaryCount}`);let i=await this.collectRuntimeStates();if(i.length===0){this.output.appendLine("[slab-heal] no runtime states detected; skipping");return}let o=[];for(let s of i)if(await this.isEol(s.language,s.version))o.push(s);if(o.length===0){this.output.appendLine(`[slab-heal] ${t}: all slab runtimes are supported`);return}this.output.appendLine(`[slab-heal] ${t}: stale runtimes detected: ${o.map((s)=>`${s.language}@${s.version}`).join(", ")}`),await this.repair(o)}catch(e){this.output.appendLine(`[slab-heal] run failed: ${V(e)}`)}finally{this.running=!1}}dispose(){this.stopTimer()}stopTimer(){if(this.timer)clearInterval(this.timer),this.timer=null}async collectRuntimeStates(){let t=[{language:"python",command:process.platform==="win32"?"python3":"python",args:["-c",'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")']},{language:"ruby",command:"ruby",args:["-e","print RUBY_VERSION"]},{language:"go",command:"go",args:["env","GOVERSION"]},{language:"rust",command:"rustc",args:["--version"]},{language:"solana",command:"solana",args:["--version"]}],e=[];for(let o of t)try{let s=await H(o.command,o.args,this.workspaceRoot),a=hi(s,o.language);if(!a)continue;e.push({language:o.language,version:a})}catch(s){this.output.appendLine(`[slab-heal] probe ${o.language} failed: ${V(s)}`)}let i=await ci(this.workspaceRoot);if(i)e.push({language:"visual-studio",version:i});else this.output.appendLine("[slab-heal] probe visual-studio failed: VS 2026 Insiders not detected");return e}async isEol(t,e){let i=await this.fetchCycles(t);if(!i||!Array.isArray(i))return!1;let o=pi(t,e),s=i.find((l)=>{let c=l;return c.cycle===o||c.cycle===o.split(".").slice(0,1).join(".")});if(!s||s.eol==null)return!1;if(typeof s.eol==="boolean")return s.eol;let a=Date.parse(s.eol);if(Number.isNaN(a))return!1;return a<=Date.now()}async fetchCycles(t){let e=ui(t);for(let i of e){let o=await fetch(`${this.options.eolApiBase}/${i}.json`,{headers:{accept:"application/json"}});if(!o.ok)continue;let s=await o.json();if(Array.isArray(s))return s}return this.output.appendLine(`[slab-heal] endoflife feed unavailable for ${t}; skipping lifecycle gate`),null}async repair(t){if(await di("mise",this.workspaceRoot))await Et("mise",["upgrade"],this.workspaceRoot,this.output),await Et("mise",["reshim"],this.workspaceRoot,this.output);else this.output.appendLine("[slab-heal] mise not found on PATH; skipped upgrade/reshim");await this.refreshToolpoolSnapshot();let i=await this.relinkVsHeaders();if(i)this.output.appendLine(`[slab-heal] relinked MSVC headers at ${i}`);else this.output.appendLine("[slab-heal] VS include relink skipped (MSVC path not found)");ne.window.showInformationMessage(`Chthonic self-heal complete: ${t.map((o)=>`${o.language}@${o.version}`).join(", ")}`)}async relinkVsHeaders(){let t=await li(this.workspaceRoot);if(!t||!this.workspaceRoot)return null;let e=y.join(this.workspaceRoot,".chthonic","native","msvc"),i=y.join(e,"include");m.mkdirSync(e,{recursive:!0});try{m.rmSync(i,{recursive:!0,force:!0})}catch{}try{m.symlinkSync(t,i,"junction")}catch(o){let s=y.join(e,"include.path.txt");m.writeFileSync(s,t,"utf8"),this.output.appendLine(`[slab-heal] symlink failed; wrote include manifest ${s}: ${V(o)}`)}return this.envCollection.replace("CHTHONIC_VS_CPP_INCLUDE",t),this.envCollection.prepend("INCLUDE",`${t};`),t}async auditVsToolchain(){let t=oe(this.workspaceRoot);if(!t)return null;let e=y.join(t,"scripts","vs2026_audit.ps1");if(!m.existsSync(e))return null;try{let i=await H("pwsh",["-NoProfile","-File",e,"-Json"],t);return JSON.parse(i).summary??null}catch(i){return this.output.appendLine(`[slab-heal] vs2026 audit script failed: ${V(i)}`),null}}async refreshToolpoolSnapshot(){let t=oe(this.workspaceRoot);if(!t)return;let e=y.join(t,"scripts","toolpool-scan.ts");if(!m.existsSync(e))return;try{await Et("bun",["run","scripts/toolpool-scan.ts","--write-env","--quiet"],t,this.output),this.output.appendLine("[slab-heal] tool-pool snapshot refreshed")}catch(i){this.output.appendLine(`[slab-heal] tool-pool snapshot failed: ${V(i)}`)}}}async function li(t){let e=y.join(process.env["ProgramFiles(x86)"]||"C:\\Program Files (x86)","Microsoft Visual Studio","Installer","vswhere.exe");if(m.existsSync(e))try{let o=await H(e,["-latest","-products","*","-requires","Microsoft.VisualStudio.Component.VC.Tools.x86.x64","-property","installationPath"],t),s=se(o.trim());if(s)return s}catch{}let i=["C:\\Program Files\\Microsoft Visual Studio\\18","C:\\Program Files\\Microsoft Visual Studio\\2026","C:\\Program Files\\Microsoft Visual Studio\\2022"];for(let o of i){let s=se(o);if(s)return s}return null}function oe(t){if(!t)return null;let e=y.join(t,"extensions","chthonic-archive");if(m.existsSync(y.join(e,"package.json")))return e;if(m.existsSync(y.join(t,"package.json")))return t;return null}async function ci(t){let e=y.join(process.env["ProgramFiles(x86)"]||"C:\\Program Files (x86)","Microsoft Visual Studio","Installer","vswhere.exe");if(!m.existsSync(e))return null;let i=[["-prerelease","-latest","-products","Microsoft.VisualStudio.Product.Professional","-property","installationVersion"],["-prerelease","-latest","-products","Microsoft.VisualStudio.Product.BuildTools","-property","installationVersion"]];for(let o of i)try{let a=(await H(e,o,t)).trim();if(a.length>0)return a}catch{}return null}function se(t){if(!m.existsSync(t))return null;let e=[],i=[t];while(i.length>0){let o=i.pop(),s=[];try{s=m.readdirSync(o,{withFileTypes:!0})}catch{continue}for(let a of s){let l=y.join(o,a.name);if(!a.isDirectory())continue;if(a.name==="include"&&l.includes(`${y.sep}VC${y.sep}Tools${y.sep}MSVC${y.sep}`)){e.push(l);continue}i.push(l)}}if(e.length===0)return null;return e.sort((o,s)=>s.localeCompare(o,void 0,{numeric:!0,sensitivity:"base"})),e[0]}async function H(t,e,i){return new Promise((o,s)=>{X.execFile(t,e,{cwd:i||void 0,windowsHide:!0,timeout:15000},(a,l,c)=>{if(a){s(Error(`${t} ${e.join(" ")} failed: ${c||a.message}`));return}o(String(l).trim())})})}async function di(t,e){if(process.platform==="win32")try{return await H("where",[t],e),!0}catch{return!1}try{return await H("which",[t],e),!0}catch{return!1}}async function Et(t,e,i,o){await new Promise((s,a)=>{let l=X.spawn(t,e,{cwd:i||void 0,windowsHide:!0,stdio:["ignore","pipe","pipe"]});l.stdout.on("data",(c)=>{o.appendLine(`[slab-heal] ${c.toString().trimEnd()}`)}),l.stderr.on("data",(c)=>{o.appendLine(`[slab-heal] ${c.toString().trimEnd()}`)}),l.on("error",a),l.on("exit",(c)=>{if(c===0)s();else a(Error(`${t} ${e.join(" ")} exited with code ${c??-1}`))})})}function hi(t,e){let i=t.trim();if(!i)return"";switch(e){case"go":return i.replace(/^go/i,"");case"rust":return i.replace(/^rustc\s+/i,"").split(/\s+/)[0]??"";case"solana":return i.replace(/^solana-cli\s+/i,"").split(/\s+/)[0]??"";case"visual-studio":return i.split(/\s+/)[0]??"";default:return i}}function pi(t,e){let i=e.split(".");if(t==="go")return i.slice(0,2).join(".");if(t==="solana")return i.slice(0,1).join(".");if(t==="visual-studio")return i.slice(0,2).join(".");return i.slice(0,2).join(".")}function ui(t){switch(t){case"solana":return["solana","agave","solana-cli"];case"visual-studio":return["visual-studio"];default:return[t]}}function V(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}function fi(t){console.log("☥ Chthonic Archive extension activated");let e=r.window.createOutputChannel("Chthonic Archive"),i=r.workspace.workspaceFolders?.[0]?.uri.fsPath||null,o=r.workspace.getConfiguration("chthonic");t.subscriptions.push(e,r.window.registerWebviewViewProvider("chthonic.chatView",new le));let s=new gt(t.extensionUri,e),a=new St(e),l=new Pt(e),c=new K,f=new Rt(e,t.environmentVariableCollection,i);t.subscriptions.push(s,c,f,r.window.registerWebviewViewProvider(K.viewType,c));let p=o,Q=p.get("entropy.enabled",!0),he=p.get("entropy.maxFiles",1e4),pe=p.get("entropy.scanIntervalMs",20000),ue=p.get("entropy.decorationDebounceMs",120),fe=p.get("entropy.decorationBatchSize",240),xt=p.get("entropy.polyglotEnabled",!0),me=p.get("entropy.pythonScanIntervalMs",30000),ye=p.get("entropy.ledgerSettleDebounceMs",1400),$t=p.get("entropy.ledgerMode","bankrun"),ve=p.get("entropy.solanaRpcUrl","http://127.0.0.1:8899"),ge=p.get("entropy.solanaAutostartValidator",!1),Se=Z(p.get("entropy.solanaLedgerHostBinaryPath","")),be=Z(p.get("entropy.solanaWalletPath","")),Pe=Z(p.get("entropy.solanaIdlPath","")),g=new st(t,e),U,w=new ft(e,g,{enabled:xt,pythonScanIntervalMs:me,settleDebounceMs:ye,ledgerMode:$t,solanaRpcUrl:ve,solanaAutostartValidator:ge,solanaLedgerHostBinaryPath:Se,solanaWalletPath:be,solanaIdlPath:Pe},(n)=>U?.enqueueExternalUpdates(n));U=new nt(g,ue,fe,(n)=>w.getTooltipFragments(n));let tt=new F(t.extensionUri,g);tt.setRootPath(i),c.updateWorkspaceHealth(g.getSnapshot()),t.subscriptions.push(g,U,tt,w,g.onDidUpdateSnapshot((n)=>{c.updateWorkspaceHealth(n)}),r.window.registerFileDecorationProvider(U),r.window.registerWebviewViewProvider(F.viewType,tt));let B=async(n)=>{if(!i)return;let d=await ee(i);c.update(d),await s.update(d),e.appendLine(`[monolith] toolchain completeness ${d.score}% (${d.tier}) via ${n}`)};if(i){B("startup");let n=r.workspace.createFileSystemWatcher(new r.RelativePattern(i,"{uv.lock,Cargo.toml,native/Cargo.toml,mise.toml,.mise.toml,anno-manifest.toml,go.mod,.ruby-version,Gemfile,.node-version,.nvmrc,package.json,bun.lock,.python-version}"));t.subscriptions.push(n,n.onDidCreate(()=>{B("marker-create")}),n.onDidChange(()=>{B("marker-change")}),n.onDidDelete(()=>{B("marker-delete")}))}if(i&&Q)g.start(i,he,pe),w.start(i);t.subscriptions.push(r.workspace.onDidSaveTextDocument((n)=>{g.refreshFile(n.uri),w.onDidSaveDocument(n)})),t.subscriptions.push(r.commands.registerCommand("chthonic.entropyRefresh",()=>{if(!i){r.window.showWarningMessage("Workspace root is required to refresh workspace health.");return}if(!Q){r.window.showWarningMessage("Workspace health lane is disabled (chthonic.entropy.enabled=false).");return}g.rescanNow(),g.requestGraph(260),w.requestManualScan(),r.window.showInformationMessage("Chthonic workspace health scan requested")}));let kt=p.get("reactor.enabled",!0),Ee=p.get("reactor.headlessVulkan",!0),Re=p.get("reactor.cockpitAutoLayout",!1),Le=p.get("reactor.transport","auto"),Ct=Z(p.get("reactor.daemonBinaryPath","")),$=Li(i,kt,Ct),Dt=p.get("slab.selfHealingEnabled",!0),Mt=p.get("slab.selfHealingIntervalMs",21600000),Tt=p.get("slab.eolApiBase","https://endoflife.date/api"),xe=yi(Tt),$e=Math.max(60000,Math.floor(Mt/2)),R=new mt(e,Ee,Ct,xe,$e),G=new yt(e,t.environmentVariableCollection),wt=new SynapseBridge(e,t.extensionPath,Le),et=null,it=null,J=null,Bt=(n,d)=>{let u=d?`${n} (${d.toLocaleString()} tps)`:n;e.appendLine(`[loom-reflex] panel lane ${u}`),l.activate()},ke=(n)=>{e.appendLine(`[loom-reflex] primary lane ${n}`),r.commands.executeCommand("workbench.view.extension.chthonic-archive"),r.commands.executeCommand("chthonic.loomView.focus")};if(!$.ready)e.appendLine(`[reactor] lane parked: ${$.reason}`);t.subscriptions.push(R,G,wt);let jt=(n)=>{if(s.updateEntropy(n),e.appendLine(`[workspace-health] score ${Math.round(n.decay_score*100)}% (${n.status}) from ${n.source_mise??"no-mise"}`),n.validator_active){let v=`${n.validator_process??"validator"}:${n.validator_source_mise}`;if(v!==it)it=v,ke(`validator-online:${v}`)}else it=null;if(n.firedancer_surge&&n.validator_active){let v=`${n.checked_at_epoch_ms}:${n.simulated_tps}`;if(v!==J)J=v,Bt("workspace-health-surge",n.simulated_tps)}else J=null;if(!n.critical||!n.auto_update_enabled){et=null;return}let d=`${n.status}:${n.auto_update}:${[...n.critical_tools].sort().join(",")}`;if(d===et)return;et=d;let u=n.critical_tools.length>0?n.critical_tools.join(", "):"runtime toolchain";r.window.showWarningMessage(`Workspace health is critical (${Math.round(n.decay_score*100)}%). ${u} needs healing.`,"Run mise upgrade","Later").then((v)=>{if(v==="Run mise upgrade")f.runNow("manual")})};if(t.subscriptions.push(R.onDidReceiveEnv((n)=>{G.applyTerminalEnv(n)}),R.onDidReceiveSynapse((n)=>{wt.updateDescriptor(n)}),R.onDidReceiveEntropyState((n)=>{jt(n)}),R.onDidReceiveFiredancerSurge((n)=>{if(n.surge){let d=`${n.slot}:${n.simulated_tps}`;if(d!==J)J=d,Bt("daemon-surge",n.simulated_tps)}})),$.ready&&i&&kt){if(R.start(i),R.requestEntropyState().then((d)=>{jt(d)}).catch((d)=>{e.appendLine(`[workspace-health] initial snapshot unavailable: ${d}`)}),Re)G.activate();let n=E.join(i,".git","HEAD");if(P.existsSync(n)){let d=null,u=P.watch(E.join(i,".git"),{persistent:!1},(v,qt)=>{if(qt==="HEAD"||qt?.startsWith("refs")){if(d)clearTimeout(d);d=setTimeout(()=>{e.appendLine("[reactor] git change detected, recomputing sediment"),R.requestSediment(10,500).catch((Ce)=>{e.appendLine(`[reactor] live-loop sediment failed: ${Ce}`)})},800)}});t.subscriptions.push({dispose:()=>u.close()})}}if(i&&Dt)f.start({intervalMs:Mt,eolApiBase:Tt}),f.runNow("interval");if(t.subscriptions.push(r.commands.registerCommand("chthonic.activateCockpit",()=>{G.activate()}),r.commands.registerCommand("chthonic.deepFocus",()=>{a.activate()}),r.commands.registerCommand("chthonic.restoreOrder",()=>{l.activate()}),r.commands.registerCommand("chthonic.slabHeal",()=>{f.runNow("manual")}),r.commands.registerCommand("chthonic.refreshRustification",()=>{B("manual-command")}),r.commands.registerCommand("chthonic.annoDetect",()=>{if(!$.ready){r.window.showWarningMessage(`ANNO lane unavailable: ${$.reason}. Using workspace-health fallback.`),r.commands.executeCommand("chthonic.entropyRefresh");return}if(i)R.start(i);r.window.showInformationMessage("ANNO project detection triggered")}),r.commands.registerCommand("chthonic.reactorSediment",async()=>{if(!$.ready){g.rescanNow(),g.requestGraph(260),r.window.showInformationMessage(`Reactor sediment lane unavailable (${$.reason}); refreshed workspace-health graph instead.`);return}try{let n=await R.requestSediment(10,500);r.window.showInformationMessage(`Sediment computed: ${n.file_count} files, ${n.layer_count} layers (${n.backend}, ${n.compute_time_ms}ms)`)}catch(n){r.window.showErrorMessage(`Sediment computation failed: ${n}`)}}),r.commands.registerCommand("chthonic.openWebCockpit",async()=>{let n=vi(o);if(!await bi(n,1200)){let u=await r.window.showWarningMessage(`Web cockpit is not responding at ${n}.`,"Start and Open","Open Anyway","Cancel");if(!u||u==="Cancel")return;if(u==="Start and Open")await r.commands.executeCommand("chthonic.startWebCockpit"),await Pi(1800)}gi(t,e,n)}),r.commands.registerCommand("chthonic.startWebCockpit",()=>{if(!i){r.window.showWarningMessage("Workspace root is required to start the Bun/Next cockpit.");return}let n=r.window.createTerminal({name:"Chthonic Web Cockpit",cwd:i});n.show(),n.sendText("bun run web:dev"),e.appendLine("[web-cockpit] started via bun run web:dev")}),r.commands.registerCommand("chthonic.openBunTrainingDocs",async()=>{let n=[{label:"Bun React Guide",description:"Build a React app with Bun",url:"https://bun.com/docs/guides/ecosystem/react#build-a-react-app-with-bun"},{label:"Bun Next.js Guide",description:"Build an app with Next.js and Bun",url:"https://bun.com/docs/guides/ecosystem/nextjs#build-an-app-with-next-js-and-bun"},{label:"Bun Tailwind (Fullstack Bundler)",description:"Tailwind plugin lane for Bun fullstack",url:"https://bun.com/docs/bundler/fullstack#tailwindcss-plugin"},{label:"Bun SQLite API",description:"Typed SQL training lane (bun:sqlite)",url:"https://bun.com/docs/api/sqlite"}],d=await r.window.showQuickPick(n,{placeHolder:"Open Bun training docs"});if(!d)return;r.env.openExternal(r.Uri.parse(d.url))}),r.commands.registerCommand("chthonic.postRestartVerify",()=>{if(!i){r.window.showWarningMessage("Workspace root is required to run post-restart verification.");return}let n=r.window.createTerminal({name:"Chthonic Post-Restart Verify",cwd:i});n.show(),n.sendText("bun run --cwd extensions/chthonic-archive insiders:post-restart:verify"),e.appendLine("[insiders] post-restart verification lane started")}),r.commands.registerCommand("chthonic.restartGate",()=>{if(!i){r.window.showWarningMessage("Workspace root is required to run restart gate checks.");return}let n=r.window.createTerminal({name:"Chthonic Restart Gate",cwd:i});n.show(),n.sendText("bun run --cwd extensions/chthonic-archive insiders:restart:gate"),e.appendLine("[insiders] restart gate check lane started")}),r.commands.registerCommand("chthonic.runtimeStatus",()=>{let n=$i({workspaceRoot:i,entropyEnabled:Q,entropyPolyglotEnabled:xt,entropyLedgerMode:$t,reactorReadiness:$,slabSelfHealingEnabled:Dt});e.show(!0),e.appendLine("[runtime] component status");for(let u of n)e.appendLine(`[runtime] ${u}`);let d=n.some((u)=>u.includes("DISABLED")||u.includes("PARKED")||u.includes("UNAVAILABLE"));r.window.showInformationMessage(d?"Some runtime lanes are parked. See Chthonic Archive output for details.":"All runtime lanes are operational.")})),i&&o.get("webCockpit.autoStart",!1))r.commands.executeCommand("chthonic.startWebCockpit");let ot=new ce;r.window.registerTreeDataProvider("chthonic.themeView",ot),t.subscriptions.push(r.commands.registerCommand("chthonic.switchTheme",async()=>{let n=[{label:"$(paintcan) Flesh & Earth",description:"Warm earth · WCAG AA · Distribution palette",id:"Chthonic Mandala - Flesh & Earth"},{label:"$(zap) ROGBIV",description:"SSOT spectral · FA¹⁻⁵ canonical hexes",id:"Chthonic Mandala - ROGBIV"},{label:"$(symbol-color) Geological Core",description:"Mineral strata palette · deep earth lane",id:"Chthonic Geological Core"}],d=r.workspace.getConfiguration("workbench").get("colorTheme"),u=await r.window.showQuickPick(n.map((v)=>({...v,picked:d===v.id})),{placeHolder:`Current: ${d}`});if(u)await r.workspace.getConfiguration("workbench").update("colorTheme",u.id,r.ConfigurationTarget.Workspace),r.window.showInformationMessage(`Theme: ${u.id}`),ot.refresh()}));let At=o;if(At.get("showSSOTHash",!0)){let n=r.window.createStatusBarItem(r.StatusBarAlignment.Left,50);n.command="chthonic.verifySSOT",n.tooltip="SSOT integrity hash — click to verify",t.subscriptions.push(n),re(n),t.subscriptions.push(r.workspace.onDidSaveTextDocument((d)=>{if(d.fileName.includes("copilot-instructions"))re(n)}))}if(At.get("showLineage",!0)){let n=r.window.createStatusBarItem(r.StatusBarAlignment.Left,49);n.command="workbench.view.scm";let d=()=>{let v=ki(i);n.text=`$(git-branch) ${v.label}`,n.tooltip=v.tooltip,n.show()};d();let u=setInterval(d,6000);t.subscriptions.push({dispose:()=>clearInterval(u)}),n.show(),t.subscriptions.push(n)}let _t=new de;r.window.registerTreeDataProvider("chthonic.statusView",_t),t.subscriptions.push(r.commands.registerCommand("chthonic.verifySSOT",async()=>{let n=Lt();if(n)r.window.showInformationMessage(`SSOT SHA-256: ${n.substring(0,16)}…`);else r.window.showWarningMessage("SSOT file not found")})),t.subscriptions.push(r.commands.registerCommand("chthonic.refreshStatus",()=>{_t.refresh(),ot.refresh(),g.rescanNow(),g.requestGraph(260),w.requestManualScan(),B("refresh-status")}))}function mi(){}function Lt(){let t=r.workspace.workspaceFolders?.[0];if(!t)return null;let e=r.workspace.getConfiguration("chthonic").get("ssotPath",".github/copilot-instructions.md"),i=E.join(t.uri.fsPath,e);if(!P.existsSync(i))return null;let s=P.readFileSync(i,"utf-8").replace(/\r\n/g,`
`).replace(/\r/g,`
`).split(`
`).map((a)=>a.trimEnd()).join(`
`).trim();return ae.createHash("sha256").update(s,"utf-8").digest("hex")}function re(t){let e=Lt();if(e)t.text=`$(shield) ${e.substring(0,8)}`,t.show();else t.text="$(shield) SSOT ??",t.show()}function Z(t){let e=t.trim();return e.length>0?e:void 0}function yi(t){let e=t.trim().replace(/\/+$/,"");if(e.endsWith("/api"))return`${e}/v1`;return e.length>0?e:"https://endoflife.date/api/v1"}function vi(t){let e=t.get("webCockpit.url","http://127.0.0.1:3000").trim();if(/^https?:\/\//i.test(e))return e;return`http://${e}`}function gi(t,e,i){let o=r.window.createWebviewPanel("chthonicWebCockpit","Chthonic Web Cockpit",r.ViewColumn.Active,{enableScripts:!0,retainContextWhenHidden:!0});o.webview.html=Si(i),o.webview.onDidReceiveMessage(async(s)=>{if(!s||typeof s!=="object")return;let a=s;if(a.type==="start"){await r.commands.executeCommand("chthonic.startWebCockpit");return}if(a.type==="openExternal"&&a.url){await r.env.openExternal(r.Uri.parse(a.url));return}e.appendLine(`[webview] Received message: ${JSON.stringify(s)}`)},void 0,t.subscriptions),o.onDidDispose(()=>{e.appendLine("[webview] Chthonic Web Cockpit panel disposed")},void 0,t.subscriptions)}function Si(t){let e=Ri(),i=Ei(t);return`<!DOCTYPE html>
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
</html>`}async function bi(t,e=1200){let i=new AbortController,o=setTimeout(()=>i.abort(),Math.max(300,e));try{return(await fetch(t,{method:"GET",redirect:"follow",signal:i.signal})).ok}catch{return!1}finally{clearTimeout(o)}}function Pi(t){return new Promise((e)=>setTimeout(e,t))}function Ei(t){return t.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;")}function Ri(){let e="";for(let i=0;i<24;i+=1)e+="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789".charAt(Math.floor(Math.random()*62));return e}function Li(t,e,i){if(!e)return{ready:!1,reason:"disabled by chthonic.reactor.enabled=false"};if(!t)return{ready:!1,reason:"workspace root is unavailable"};let o=xi(t,i);if(!P.existsSync(o))return{ready:!1,reason:`daemon binary missing (${o})`,daemonPath:o};return{ready:!0,reason:"ready",daemonPath:o}}function xi(t,e){if(e)return E.isAbsolute(e)?e:E.join(t,e);let i=process.platform==="win32"?"chthonic-daemon.exe":"chthonic-daemon";return E.join(t,"native","target","release",i)}function $i(t){let e=[];if(e.push(`workspace=${t.workspaceRoot?"READY":"UNAVAILABLE"}`),e.push(`workspace-health=${t.entropyEnabled?"ENABLED":"DISABLED"}`),e.push(`polyglot-sidecars=${t.entropyPolyglotEnabled?"ENABLED":"DISABLED"}`),e.push(`ledger-mode=${t.entropyLedgerMode}`),e.push(`self-healing=${t.slabSelfHealingEnabled?"ENABLED":"DISABLED"}`),e.push(`reactor=${t.reactorReadiness.ready?"READY":`PARKED (${t.reactorReadiness.reason})`}`),t.reactorReadiness.daemonPath)e.push(`reactor-daemon=${t.reactorReadiness.daemonPath}`);return e}function ki(t){if(!t)return{label:"no-workspace",tooltip:"Chthonic lineage unavailable: no workspace root."};let e=E.join(t,".git"),i=E.join(e,"HEAD");if(!P.existsSync(i))return{label:"no-git",tooltip:"Chthonic lineage unavailable: .git/HEAD not found."};try{let o=P.readFileSync(i,"utf8").trim();if(!o)return{label:"detached",tooltip:"Chthonic lineage unavailable: empty git HEAD."};if(!o.startsWith("ref:"))return{label:`detached@${o.slice(0,8)}`,tooltip:`Detached HEAD ${o}`};let s=o.slice(4).trim(),a=s.split("/").pop()||s,l=E.join(e,...s.split("/")),c=P.existsSync(l)?P.readFileSync(l,"utf8").trim().slice(0,8):"unknown";return{label:`${a}@${c}`,tooltip:`Chthonic lineage
${s}
${c}`}}catch(o){return{label:"lineage-error",tooltip:`Chthonic lineage read failed: ${String(o)}`}}}class le{resolveWebviewView(t,e,i){t.webview.options={enableScripts:!1},t.webview.html=`
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8" />
                <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                <style>
                    body {
                        margin: 0;
                        padding: 16px;
                        font-family: var(--vscode-font-family);
                        color: var(--vscode-foreground);
                        background: var(--vscode-editor-background);
                    }
                    h3 {
                        margin: 0 0 8px 0;
                        font-size: 14px;
                    }
                    p {
                        margin: 0;
                        line-height: 1.4;
                        color: var(--vscode-descriptionForeground);
                    }
                </style>
            </head>
            <body>
                <h3>Agent Chat Parked</h3>
                <p>
                    SDK/ACP chat integration is intentionally parked during runtime hardening.
                    Existing SDK files remain in source for later reactivation.
                </p>
            </body>
            </html>
        `}}class ce{_onDidChange=new r.EventEmitter;onDidChangeTreeData=this._onDidChange.event;refresh(){this._onDidChange.fire()}getTreeItem(t){return t}getChildren(){let t=r.workspace.getConfiguration("workbench").get("colorTheme")||"";return[{name:"Chthonic Mandala - Flesh & Earth",short:"Flesh & Earth",icon:"\uD83C\uDF0D",desc:"Warm earth · Distribution"},{name:"Chthonic Mandala - ROGBIV",short:"ROGBIV",icon:"\uD83C\uDF08",desc:"SSOT spectral · Research"},{name:"Chthonic Geological Core",short:"Geological Core",icon:"\uD83E\uDEA8",desc:"Mineral strata · Deep earth"}].map((i)=>{let o=t===i.name,s=new r.TreeItem(`${o?"◉":"○"} ${i.icon} ${i.short}`,r.TreeItemCollapsibleState.None);return s.tooltip=`${i.name}
${i.desc}${o?`

✅ ACTIVE`:""}`,s.description=o?"active":"",s.command={command:"chthonic.switchTheme",title:"Switch"},s})}}class de{_onDidChange=new r.EventEmitter;onDidChangeTreeData=this._onDidChange.event;refresh(){this._onDidChange.fire()}getTreeItem(t){return t}getChildren(){let t=Lt(),e=[],i=new r.TreeItem(`$(shield) SSOT: ${t?t.substring(0,12)+"…":"not found"}`,r.TreeItemCollapsibleState.None);i.command={command:"chthonic.verifySSOT",title:"Verify"},e.push(i);let o=new r.TreeItem(`$(paintcan) Theme: ${(r.workspace.getConfiguration("workbench").get("colorTheme")||"default").replace("Chthonic Mandala - ","")}`,r.TreeItemCollapsibleState.None);return o.command={command:"chthonic.switchTheme",title:"Switch"},e.push(o),e}}
