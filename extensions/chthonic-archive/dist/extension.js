var X=Object.create;var{getPrototypeOf:Z,defineProperty:k,getOwnPropertyNames:L,getOwnPropertyDescriptor:O}=Object,U=Object.prototype.hasOwnProperty;var p=(e,t,s)=>{s=e!=null?X(Z(e)):{};let n=t||!e||!e.__esModule?k(s,"default",{value:e,enumerable:!0}):s;for(let o of L(e))if(!U.call(n,o))k(n,o,{get:()=>e[o],enumerable:!0});return n},G=new WeakMap,ee=(e)=>{var t=G.get(e),s;if(t)return t;if(t=k({},"__esModule",{value:!0}),e&&typeof e==="object"||typeof e==="function")L(e).map((n)=>!U.call(t,n)&&k(t,n,{get:()=>e[n],enumerable:!(s=O(e,n))||s.enumerable}));return G.set(e,t),t};var te=(e,t)=>{for(var s in t)k(e,s,{get:t[s],enumerable:!0,configurable:!0,set:(n)=>t[s]=()=>n})};var ce={};te(ce,{deactivate:()=>de,activate:()=>ie});module.exports=ee(ce);var a=p(require("vscode")),Y=p(require("crypto")),B=p(require("fs")),P=p(require("path"));var V=p(require("vscode")),I=p(require("child_process"));var T=p(require("child_process")),H=p(require("readline")),M=p(require("path"));class z{harnessPath;log;process=null;rl=null;handlers=new Set;authenticated=!1;ready=!1;constructor(e,t){this.harnessPath=e;this.log=t}async start(){if(this.process)return;let e=M.dirname(this.harnessPath),t=M.basename(this.harnessPath);this.process=T.spawn("bun",["run",t],{cwd:e,stdio:["pipe","pipe","pipe"],env:{...process.env}}),this.process.stderr?.on("data",(s)=>{this.log(`[harness stderr] ${s.toString().trim()}`)}),this.process.on("close",(s)=>{this.log(`[harness] exited with code ${s}`),this.process=null,this.rl=null,this.ready=!1,this.authenticated=!1}),this.rl=H.createInterface({input:this.process.stdout}),this.rl.on("line",(s)=>{try{let n=JSON.parse(s);if(n.type==="ready")this.ready=!0,this.log(`[harness] ready: ${n.sdk}`);for(let o of this.handlers)o(n)}catch{this.log(`[harness] non-JSON: ${s.substring(0,200)}`)}}),await new Promise((s,n)=>{let o=setTimeout(()=>n(Error("Harness startup timeout")),15000),r=(c)=>{if(c.type==="ready")clearTimeout(o),this.handlers.delete(r),s()};this.handlers.add(r)})}async authenticate(e,t){this.send({cmd:"auth",token:e,login:t}),await this.waitFor("auth_ok"),this.authenticated=!0,this.log(`[harness] authenticated as ${t}`)}query(e,t,s,n,o){return new Promise((r,c)=>{let h=(l)=>{if(l.id!==e)return;if(l.type==="event"&&l.event)n(l.event);else if(l.type==="done")this.handlers.delete(h),r();else if(l.type==="cancelled")this.handlers.delete(h),r();else if(l.type==="error")this.handlers.delete(h),c(Error(l.message||"Query failed"))};this.handlers.add(h),this.send({cmd:"query",id:e,prompt:t,workingDirectory:s,model:o?.model,reasoningEffort:o?.reasoningEffort})})}cancel(e){this.send({cmd:"cancel",id:e})}async getModels(){return this.send({cmd:"models"}),(await this.waitFor("models")).data||[]}isReady(){return this.ready&&this.authenticated&&this.process!==null}stop(){if(this.process)this.process.kill(),this.process=null;this.rl=null,this.ready=!1,this.authenticated=!1,this.handlers.clear()}send(e){if(!this.process?.stdin?.writable)throw Error("Harness not running");this.process.stdin.write(JSON.stringify(e)+`
`)}waitFor(e,t=15000){return new Promise((s,n)=>{let o=setTimeout(()=>{this.handlers.delete(r),n(Error(`Timeout waiting for ${e}`))},t),r=(c)=>{if(c.type===e)clearTimeout(o),this.handlers.delete(r),s(c);else if(c.type==="error")clearTimeout(o),this.handlers.delete(r),n(Error(c.message||"Error"))};this.handlers.add(r)})}}class C{extensionUri;harnessPath;log;static viewType="chthonic.chatView";view;connection=null;isConnecting=!1;activeQueryId=null;constructor(e,t,s){this.extensionUri=e;this.harnessPath=t;this.log=s}resolveWebviewView(e,t,s){this.view=e,e.webview.options={enableScripts:!0,localResourceRoots:[this.extensionUri]},e.webview.html=this.getHtml(),e.webview.onDidReceiveMessage(async(n)=>{switch(n.type){case"connect":await this.connectAgent();break;case"prompt":await this.sendPrompt(n.text);break;case"cancel":this.cancelQuery();break;case"disconnect":this.disconnectAgent();break}})}async connectAgent(){if(this.isConnecting||this.connection?.isReady())return;this.isConnecting=!0,this.postMessage({type:"status",status:"connecting"});try{this.connection=new z(this.harnessPath,this.log),await this.connection.start();let e=I.execSync("gh auth token",{encoding:"utf-8"}).trim(),t=I.execSync("gh api user --jq .login",{encoding:"utf-8"}).trim();await this.connection.authenticate(e,t),this.postMessage({type:"connected",agentName:"Chthonic SDK",agentVersion:"0.1.0",login:t}),this.log(`Chat connected: ${t}`)}catch(e){this.log(`Chat connect failed: ${e.message}`),this.postMessage({type:"error",message:e.message}),this.connection?.stop(),this.connection=null}finally{this.isConnecting=!1}}async sendPrompt(e){if(!this.connection?.isReady()){this.postMessage({type:"error",message:"Not connected"});return}let t=crypto.randomUUID();this.activeQueryId=t,this.postMessage({type:"prompt-start"});let s=V.workspace.workspaceFolders?.[0]?.uri.fsPath||process.cwd();try{await this.connection.query(t,e,s,(n)=>this.handleSdkEvent(n))}catch(n){this.postMessage({type:"error",message:n.message})}finally{this.activeQueryId=null,this.postMessage({type:"prompt-end"})}}handleSdkEvent(e){switch(e.type){case"assistant.message":if(e.data?.content)this.postMessage({type:"agent-message",content:e.data.content});break;case"assistant.message.delta":if(e.data?.delta)this.postMessage({type:"agent-delta",delta:e.data.delta});break;case"tool.execution_start":this.postMessage({type:"tool-start",name:e.data?.name,args:e.data?.arguments});break;case"tool.execution_complete":this.postMessage({type:"tool-end",name:e.data?.name});break;case"assistant.reasoning":this.postMessage({type:"reasoning"});break;case"assistant.usage":this.postMessage({type:"usage",model:e.data?.model,inputTokens:e.data?.inputTokens,outputTokens:e.data?.outputTokens,duration:e.data?.duration});break;case"session.usage_info":this.postMessage({type:"context-info",tokenLimit:e.data?.tokenLimit,currentTokens:e.data?.currentTokens});break}}cancelQuery(){if(this.activeQueryId&&this.connection)this.connection.cancel(this.activeQueryId)}disconnectAgent(){this.connection?.stop(),this.connection=null,this.activeQueryId=null,this.postMessage({type:"disconnected"})}postMessage(e){this.view?.webview.postMessage(e)}dispose(){this.connection?.stop()}getHtml(){return`<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: var(--vscode-font-family, 'Segoe UI', sans-serif);
    font-size: var(--vscode-font-size, 13px);
    color: var(--vscode-foreground);
    background: var(--vscode-sideBar-background);
    height: 100vh;
    display: flex;
    flex-direction: column;
}
#status-bar {
    padding: 6px 10px;
    background: var(--vscode-sideBarSectionHeader-background);
    border-bottom: 1px solid var(--vscode-panel-border);
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 11px;
}
#status-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: var(--vscode-editorWarning-foreground, #C9A55A);
}
#status-dot.connected { background: var(--vscode-charts-green, #A8C686); }
#status-dot.connecting { background: var(--vscode-editorWarning-foreground); animation: pulse 1s infinite; }
@keyframes pulse { 50% { opacity: 0.4; } }

#context-bar {
    padding: 2px 10px;
    font-size: 10px;
    color: var(--vscode-descriptionForeground);
    background: var(--vscode-sideBarSectionHeader-background);
    border-bottom: 1px solid var(--vscode-panel-border);
    display: none;
}

#messages {
    flex: 1;
    overflow-y: auto;
    padding: 10px;
    display: flex;
    flex-direction: column;
    gap: 8px;
}
.msg {
    padding: 8px 12px;
    border-radius: 6px;
    max-width: 95%;
    line-height: 1.5;
    white-space: pre-wrap;
    word-break: break-word;
}
.msg.user {
    align-self: flex-end;
    background: var(--vscode-button-background, #D4A5A5);
    color: var(--vscode-button-foreground, #0E0B09);
}
.msg.agent {
    align-self: flex-start;
    background: var(--vscode-editorWidget-background);
    border: 1px solid var(--vscode-editorWidget-border);
}
.msg.system {
    align-self: center;
    color: var(--vscode-descriptionForeground);
    font-style: italic;
    font-size: 11px;
}
.msg.tool {
    align-self: flex-start;
    color: var(--vscode-descriptionForeground);
    font-size: 11px;
    padding: 4px 12px;
    opacity: 0.7;
}
.msg code {
    font-family: var(--vscode-editor-font-family, 'Cascadia Code', monospace);
    background: var(--vscode-textCodeBlock-background, rgba(0,0,0,0.2));
    padding: 1px 4px;
    border-radius: 3px;
    font-size: 12px;
}
.msg pre {
    background: var(--vscode-textCodeBlock-background, rgba(0,0,0,0.3));
    padding: 8px;
    border-radius: 4px;
    overflow-x: auto;
    margin: 6px 0;
}
.msg pre code { background: none; padding: 0; }

#input-area {
    padding: 8px 10px;
    border-top: 1px solid var(--vscode-panel-border);
    display: flex;
    gap: 6px;
}
#prompt-input {
    flex: 1;
    background: var(--vscode-input-background);
    color: var(--vscode-input-foreground);
    border: 1px solid var(--vscode-input-border);
    border-radius: 4px;
    padding: 6px 10px;
    font-family: inherit;
    font-size: inherit;
    resize: none;
    min-height: 32px;
    max-height: 120px;
}
#prompt-input:focus { outline: 1px solid var(--vscode-focusBorder); }
button {
    background: var(--vscode-button-background);
    color: var(--vscode-button-foreground);
    border: none;
    border-radius: 4px;
    padding: 6px 12px;
    cursor: pointer;
    font-size: 12px;
}
button:hover { background: var(--vscode-button-hoverBackground); }
button:disabled { opacity: 0.5; cursor: not-allowed; }
#connect-area {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    flex: 1;
    gap: 12px;
}
#connect-area h3 { color: var(--vscode-sideBarTitle-foreground); }
</style>
</head>
<body>
<div id="status-bar">
    <span id="status-dot"></span>
    <span id="status-text">Disconnected</span>
    <span style="flex:1"></span>
    <button id="btn-cancel" style="display:none;font-size:10px;padding:2px 8px" onclick="cancel()">⬜ Stop</button>
    <button id="btn-disconnect" style="display:none;font-size:10px;padding:2px 8px" onclick="disconnect()">×</button>
</div>

<div id="context-bar"></div>

<div id="connect-area">
    <h3>☥ Chthonic Agent</h3>
    <p style="color:var(--vscode-descriptionForeground);font-size:11px;text-align:center">
        Direct SDK — Copilot engine via Bun
    </p>
    <button onclick="connect()" id="btn-connect">Connect Agent</button>
</div>

<div id="messages" style="display:none"></div>

<div id="input-area" style="display:none">
    <textarea id="prompt-input" rows="1" placeholder="Ask the agent..." disabled></textarea>
    <button id="btn-send" onclick="send()" disabled>Send</button>
</div>

<script>
const vscode = acquireVsCodeApi();
const messagesEl = document.getElementById('messages');
const inputEl = document.getElementById('prompt-input');
const connectArea = document.getElementById('connect-area');
const inputArea = document.getElementById('input-area');
const contextBar = document.getElementById('context-bar');

let currentAgentMsg = null;
let isQuerying = false;

function connect() {
    vscode.postMessage({ type: 'connect' });
}

function disconnect() {
    vscode.postMessage({ type: 'disconnect' });
}

function cancel() {
    vscode.postMessage({ type: 'cancel' });
}

function send() {
    const text = inputEl.value.trim();
    if (!text) return;
    addMessage('user', text);
    inputEl.value = '';
    inputEl.style.height = 'auto';
    setQueryState(true);
    vscode.postMessage({ type: 'prompt', text });
}

function setQueryState(querying) {
    isQuerying = querying;
    inputEl.disabled = querying;
    document.getElementById('btn-send').disabled = querying;
    document.getElementById('btn-cancel').style.display = querying ? '' : 'none';
}

function addMessage(role, text) {
    const el = document.createElement('div');
    el.className = 'msg ' + role;
    el.textContent = text;
    messagesEl.appendChild(el);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return el;
}

inputEl.addEventListener('input', () => {
    inputEl.style.height = 'auto';
    inputEl.style.height = Math.min(inputEl.scrollHeight, 120) + 'px';
});

inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        send();
    }
});

window.addEventListener('message', (event) => {
    const msg = event.data;
    switch (msg.type) {
        case 'status':
            document.getElementById('status-dot').className = msg.status;
            document.getElementById('status-text').textContent =
                msg.status === 'connecting' ? 'Connecting...' : msg.status;
            break;

        case 'connected':
            document.getElementById('status-dot').className = 'connected';
            document.getElementById('status-text').textContent = msg.agentName + ' · ' + msg.login;
            document.getElementById('btn-disconnect').style.display = '';
            connectArea.style.display = 'none';
            messagesEl.style.display = 'flex';
            inputArea.style.display = 'flex';
            inputEl.disabled = false;
            document.getElementById('btn-send').disabled = false;
            addMessage('system', '☥ Connected via SDK · ' + msg.login);
            inputEl.focus();
            break;

        case 'disconnected':
            document.getElementById('status-dot').className = '';
            document.getElementById('status-text').textContent = 'Disconnected';
            document.getElementById('btn-disconnect').style.display = 'none';
            connectArea.style.display = 'flex';
            messagesEl.style.display = 'none';
            inputArea.style.display = 'none';
            contextBar.style.display = 'none';
            currentAgentMsg = null;
            break;

        case 'prompt-start':
            currentAgentMsg = null;
            break;

        case 'prompt-end':
            currentAgentMsg = null;
            setQueryState(false);
            inputEl.focus();
            break;

        case 'agent-message':
            if (currentAgentMsg) {
                currentAgentMsg.textContent = msg.content;
            } else {
                addMessage('agent', msg.content);
            }
            currentAgentMsg = null;
            break;

        case 'agent-delta':
            if (!currentAgentMsg) {
                currentAgentMsg = addMessage('agent', '');
            }
            currentAgentMsg.textContent += msg.delta;
            messagesEl.scrollTop = messagesEl.scrollHeight;
            break;

        case 'tool-start':
            addMessage('tool', '⚙ ' + (msg.name || 'tool'));
            break;

        case 'tool-end':
            break;

        case 'reasoning':
            if (!currentAgentMsg) {
                currentAgentMsg = addMessage('agent', '');
            }
            break;

        case 'usage':
            document.getElementById('status-text').textContent =
                (msg.model || 'agent') + ' · ' + (msg.duration ? (msg.duration/1000).toFixed(1) + 's' : '');
            break;

        case 'context-info':
            if (msg.tokenLimit && msg.currentTokens) {
                const pct = ((msg.currentTokens / msg.tokenLimit) * 100).toFixed(0);
                contextBar.textContent = 'Context: ' + pct + '% · ' + msg.currentTokens.toLocaleString() + '/' + msg.tokenLimit.toLocaleString() + ' tokens';
                contextBar.style.display = '';
            }
            break;

        case 'error':
            addMessage('system', '⚠ ' + msg.message);
            setQueryState(false);
            break;
    }
});
</script>
</body>
</html>`}}var w=p(require("path")),m=p(require("vscode")),j=require("worker_threads");class W{extensionContext;output;records=new Map;recordUris=new Map;onDidUpdateRecordsEmitter=new m.EventEmitter;onDidUpdateRecords=this.onDidUpdateRecordsEmitter.event;onDidUpdateGraphEmitter=new m.EventEmitter;onDidUpdateGraph=this.onDidUpdateGraphEmitter.event;onDidUpdateSnapshotEmitter=new m.EventEmitter;onDidUpdateSnapshot=this.onDidUpdateSnapshotEmitter.event;worker=null;rootPath=null;workerPath;maxFiles=1e4;lastScanDurationMs=0;lastScanAt=0;scanTimer=null;disposed=!1;constructor(e,t){this.extensionContext=e;this.output=t;this.workerPath=e.asAbsolutePath(w.join("dist","entropy-worker.js"))}start(e,t,s){this.rootPath=e,this.maxFiles=t,this.ensureWorker(),this.send({type:"scan",root:e,maxFiles:this.maxFiles}),this.scheduleScanLoop(s)}rescanNow(){if(!this.rootPath)return;this.send({type:"scan",root:this.rootPath,maxFiles:this.maxFiles})}refreshFile(e){if(!this.rootPath||e.scheme!=="file")return;this.send({type:"refresh-file",root:this.rootPath,path:e.fsPath})}requestGraph(e){this.send({type:"graph",limit:e})}getRecord(e){if(!this.rootPath||e.scheme!=="file")return;let t=se(w.relative(this.rootPath,e.fsPath));return this.records.get(t)}getSnapshot(e=40){let t=Array.from(this.records.values()),s=t.length===0?0:t.reduce((o,r)=>o+r.entropy,0)/t.length,n=t.sort((o,r)=>r.entropy-o.entropy).slice(0,e);return{totalFiles:t.length,topEntropy:n,averageEntropy:s,lastScanDurationMs:this.lastScanDurationMs,lastScanAt:this.lastScanAt}}dispose(){if(this.disposed=!0,this.scanTimer)clearInterval(this.scanTimer),this.scanTimer=null;this.send({type:"stop"}),this.worker?.terminate(),this.worker=null,this.onDidUpdateRecordsEmitter.dispose(),this.onDidUpdateGraphEmitter.dispose(),this.onDidUpdateSnapshotEmitter.dispose()}scheduleScanLoop(e){if(this.scanTimer)clearInterval(this.scanTimer);let t=Math.max(5000,e);this.scanTimer=setInterval(()=>{if(!this.disposed)this.rescanNow()},t)}ensureWorker(){if(this.worker)return;this.worker=new j.Worker(this.workerPath),this.worker.on("message",(e)=>this.handleWorkerEvent(e)),this.worker.on("error",(e)=>{this.output.appendLine(`[entropy] worker error: ${e.message}`)}),this.worker.on("exit",(e)=>{if(this.output.appendLine(`[entropy] worker exited with code ${e}`),this.worker=null,!this.disposed&&e!==0)this.ensureWorker(),this.rescanNow()})}send(e){this.ensureWorker(),this.worker?.postMessage(e)}handleWorkerEvent(e){switch(e.type){case"scan-progress":{if(!this.rootPath)return;let t=[];for(let s of e.records){this.records.set(s.path,s);let n=this.recordUris.get(s.path);if(!n)n=m.Uri.file(w.join(this.rootPath,s.path)),this.recordUris.set(s.path,n);t.push(n)}if(t.length>0)this.onDidUpdateRecordsEmitter.fire(t);break}case"scan-complete":this.lastScanDurationMs=e.durationMs,this.lastScanAt=Date.now(),this.onDidUpdateSnapshotEmitter.fire(this.getSnapshot());break;case"graph-result":this.onDidUpdateGraphEmitter.fire(e.graph);break;case"error":this.output.appendLine(`[entropy] ${e.message}${e.detail?`
${e.detail}`:""}`);break}}}function se(e){return e.replace(/\\/g,"/")}var R=p(require("vscode"));class F{workerClient;debounceMs;maxPerFlush;onDidChangeEmitter=new R.EventEmitter;onDidChangeFileDecorations=this.onDidChangeEmitter.event;pending=new Map;flushTimer=null;constructor(e,t,s){this.workerClient=e;this.debounceMs=t;this.maxPerFlush=s;this.workerClient.onDidUpdateRecords((n)=>this.enqueueUpdates(n))}dispose(){if(this.flushTimer)clearTimeout(this.flushTimer),this.flushTimer=null;this.onDidChangeEmitter.dispose()}updateConfig(e,t){this.debounceMs=Math.max(30,e),this.maxPerFlush=Math.max(64,t)}provideFileDecoration(e){if(e.scheme!=="file")return;let t=this.workerClient.getRecord(e);if(!t)return;let s=ne(t),n=[`Entropy ${(t.entropy*100).toFixed(0)}%`,`Complexity ${t.complexity}`,`Debt ${t.debt}`,`Freshness ${(t.freshness*100).toFixed(0)}%`].join(" • ");return{color:s,tooltip:n,propagate:!1}}enqueueUpdates(e){for(let t of e)this.pending.set(t.toString(),t);if(!this.flushTimer)this.flushTimer=setTimeout(()=>this.flush(),this.debounceMs)}flush(){if(this.flushTimer=null,this.pending.size===0)return;let e=Array.from(this.pending.values()).slice(0,this.maxPerFlush);for(let t of e)this.pending.delete(t.toString());if(this.onDidChangeEmitter.fire(e),this.pending.size>0)this.flushTimer=setTimeout(()=>this.flush(),this.debounceMs)}}function ne(e){let t=oe(e.entropy*0.78+(1-e.freshness)*0.22),s=D(118,24,t),n=D(36,46,t),o=D(58,42,t);return ae(s,n,o)}function ae(e,t,s){let n=e/360,o=t/100,r=s/100,c=(i,u,x)=>{let g=x;if(g<0)g+=1;if(g>1)g-=1;if(g<0.16666666666666666)return i+(u-i)*6*g;if(g<0.5)return u;if(g<0.6666666666666666)return i+(u-i)*(0.6666666666666666-g)*6;return i},h,l,v;if(o===0)h=r,l=r,v=r;else{let i=r<0.5?r*(1+o):r+o-r*o,u=2*r-i;h=c(u,i,n+0.3333333333333333),l=c(u,i,n),v=c(u,i,n-0.3333333333333333)}let f=(i)=>{return Math.round(i*255).toString(16).padStart(2,"0")};return`#${f(h)}${f(l)}${f(v)}`}function oe(e){if(e<0)return 0;if(e>1)return 1;return e}function D(e,t,s){return e+(t-e)*s}var b=p(require("path")),y=p(require("vscode"));class A{extensionUri;workerClient;static viewType="chthonic.abyssalView";disposables=[];view=null;rootPath=null;constructor(e,t){this.extensionUri=e;this.workerClient=t;this.disposables.push(this.workerClient.onDidUpdateGraph((s)=>this.postMessage({type:"graph",graph:s})),this.workerClient.onDidUpdateSnapshot((s)=>this.postMessage({type:"snapshot",snapshot:s})))}setRootPath(e){this.rootPath=e}dispose(){this.disposables.forEach((e)=>e.dispose()),this.disposables.length=0}resolveWebviewView(e,t,s){this.view=e,e.webview.options={enableScripts:!0,localResourceRoots:[this.extensionUri]},e.webview.html=this.getHtml(e.webview),e.webview.onDidReceiveMessage((n)=>{this.handleMessage(n)})}handleMessage(e){if(!e||typeof e!=="object")return;let t=e;if(!t.type)return;if(t.type==="ready"){this.postMessage({type:"snapshot",snapshot:this.workerClient.getSnapshot()}),this.workerClient.requestGraph(260);return}if(t.type==="requestGraph"){this.workerClient.requestGraph(260);return}if(t.type==="openFile"&&t.path&&this.rootPath){let s=b.normalize(t.path);if(s.startsWith("..")||b.isAbsolute(s))return;let n=b.join(this.rootPath,s),o=y.Uri.file(n);y.workspace.openTextDocument(o).then((r)=>{y.window.showTextDocument(r,{preview:!1})},()=>{y.window.showWarningMessage(`Unable to open ${t.path}`)})}}postMessage(e){if(!this.view)return;this.view.webview.postMessage(e)}getHtml(e){let t=re();return`<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="${["default-src 'none'",`img-src ${e.cspSource} data: https:`,`style-src ${e.cspSource} 'unsafe-inline'`,`script-src 'nonce-${t}' https://cdn.jsdelivr.net`].join("; ")}">
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

    <script nonce="${t}" src="https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js"></script>
    <script nonce="${t}">
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
</html>`}}function re(){let t="";for(let s=0;s<32;s+=1)t+="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789".charAt(Math.floor(Math.random()*62));return t}function ie(e){console.log("☥ Chthonic Archive extension activated");let t=a.window.createOutputChannel("Chthonic SDK"),s=a.workspace.workspaceFolders?.[0]?.uri.fsPath||null,n=P.join(s||"","meta-ide","copilot-sdk","harness.ts"),o=new C(e.extensionUri,n,(d)=>t.appendLine(`[${new Date().toISOString()}] ${d}`));e.subscriptions.push(a.window.registerWebviewViewProvider(C.viewType,o));let r=a.workspace.getConfiguration("chthonic"),c=r.get("entropy.enabled",!0),h=r.get("entropy.maxFiles",1e4),l=r.get("entropy.scanIntervalMs",20000),v=r.get("entropy.decorationDebounceMs",120),f=r.get("entropy.decorationBatchSize",240),i=new W(e,t),u=new F(i,v,f),x=new A(e.extensionUri,i);if(x.setRootPath(s),e.subscriptions.push(i,u,x,a.window.registerFileDecorationProvider(u),a.window.registerWebviewViewProvider(A.viewType,x)),s&&c)i.start(s,h,l);e.subscriptions.push(a.workspace.onDidSaveTextDocument((d)=>{i.refreshFile(d.uri)})),e.subscriptions.push(a.commands.registerCommand("chthonic.entropyRefresh",()=>{i.rescanNow(),i.requestGraph(260),a.window.showInformationMessage("Chthonic entropy scan requested")}));let g=new q;a.window.registerTreeDataProvider("chthonic.themeView",g),e.subscriptions.push(a.commands.registerCommand("chthonic.switchTheme",async()=>{let d=[{label:"$(paintcan) Flesh & Earth",description:"Warm earth · WCAG AA · Distribution palette",id:"Chthonic Mandala - Flesh & Earth"},{label:"$(zap) ROGBIV",description:"SSOT spectral · FA¹⁻⁵ canonical hexes",id:"Chthonic Mandala - ROGBIV"}],E=a.workspace.getConfiguration("workbench").get("colorTheme"),S=await a.window.showQuickPick(d.map(($)=>({...$,picked:E===$.id})),{placeHolder:`Current: ${E}`});if(S)await a.workspace.getConfiguration("workbench").update("colorTheme",S.id,a.ConfigurationTarget.Workspace),a.window.showInformationMessage(`Theme: ${S.id}`),g.refresh()}));let Q=a.workspace.getConfiguration("chthonic");if(Q.get("showSSOTHash",!0)){let d=a.window.createStatusBarItem(a.StatusBarAlignment.Left,50);d.command="chthonic.verifySSOT",d.tooltip="SSOT integrity hash — click to verify",e.subscriptions.push(d),K(d),e.subscriptions.push(a.workspace.onDidSaveTextDocument((E)=>{if(E.fileName.includes("copilot-instructions"))K(d)}))}if(Q.get("showLineage",!0)){let d=a.window.createStatusBarItem(a.StatusBarAlignment.Left,49);d.text="$(git-branch) ☥ main",d.tooltip="Chthonic lineage",d.show(),e.subscriptions.push(d)}let _=new J;a.window.registerTreeDataProvider("chthonic.statusView",_),e.subscriptions.push(a.commands.registerCommand("chthonic.verifySSOT",async()=>{let d=N();if(d)a.window.showInformationMessage(`SSOT SHA-256: ${d.substring(0,16)}…`);else a.window.showWarningMessage("SSOT file not found")})),e.subscriptions.push(a.commands.registerCommand("chthonic.refreshStatus",()=>{_.refresh(),g.refresh(),i.rescanNow(),i.requestGraph(260)}))}function de(){}function N(){let e=a.workspace.workspaceFolders?.[0];if(!e)return null;let t=a.workspace.getConfiguration("chthonic").get("ssotPath",".github/copilot-instructions.md"),s=P.join(e.uri.fsPath,t);if(!B.existsSync(s))return null;let o=B.readFileSync(s,"utf-8").replace(/\r\n/g,`
`).replace(/\r/g,`
`).split(`
`).map((r)=>r.trimEnd()).join(`
`).trim();return Y.createHash("sha256").update(o,"utf-8").digest("hex")}function K(e){let t=N();if(t)e.text=`$(shield) ${t.substring(0,8)}`,e.show();else e.text="$(shield) SSOT ??",e.show()}class q{_onDidChange=new a.EventEmitter;onDidChangeTreeData=this._onDidChange.event;refresh(){this._onDidChange.fire()}getTreeItem(e){return e}getChildren(){let e=a.workspace.getConfiguration("workbench").get("colorTheme")||"";return[{name:"Chthonic Mandala - Flesh & Earth",short:"Flesh & Earth",icon:"\uD83C\uDF0D",desc:"Warm earth · Distribution"},{name:"Chthonic Mandala - ROGBIV",short:"ROGBIV",icon:"\uD83C\uDF08",desc:"SSOT spectral · Research"}].map((s)=>{let n=e===s.name,o=new a.TreeItem(`${n?"◉":"○"} ${s.icon} ${s.short}`,a.TreeItemCollapsibleState.None);return o.tooltip=`${s.name}
${s.desc}${n?`

✅ ACTIVE`:""}`,o.description=n?"active":"",o.command={command:"chthonic.switchTheme",title:"Switch"},o})}}class J{_onDidChange=new a.EventEmitter;onDidChangeTreeData=this._onDidChange.event;refresh(){this._onDidChange.fire()}getTreeItem(e){return e}getChildren(){let e=N(),t=[],s=new a.TreeItem(`$(shield) SSOT: ${e?e.substring(0,12)+"…":"not found"}`,a.TreeItemCollapsibleState.None);s.command={command:"chthonic.verifySSOT",title:"Verify"},t.push(s);let n=new a.TreeItem(`$(paintcan) Theme: ${(a.workspace.getConfiguration("workbench").get("colorTheme")||"default").replace("Chthonic Mandala - ","")}`,a.TreeItemCollapsibleState.None);return n.command={command:"chthonic.switchTheme",title:"Switch"},t.push(n),t}}
