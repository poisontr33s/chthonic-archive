var Ut=Object.create;var{getPrototypeOf:Ft,defineProperty:A,getOwnPropertyNames:ft,getOwnPropertyDescriptor:Vt}=Object,mt=Object.prototype.hasOwnProperty;var c=(t,e,s)=>{s=t!=null?Ut(Ft(t)):{};let i=e||!t||!t.__esModule?A(s,"default",{value:t,enumerable:!0}):s;for(let n of ft(t))if(!mt.call(i,n))A(i,n,{get:()=>t[n],enumerable:!0});return i},gt=new WeakMap,Qt=(t)=>{var e=gt.get(t),s;if(e)return e;if(e=A({},"__esModule",{value:!0}),t&&typeof t==="object"||typeof t==="function")ft(t).map((i)=>!mt.call(e,i)&&A(e,i,{get:()=>t[i],enumerable:!(s=Vt(t,i))||s.enumerable}));return gt.set(t,e),e};var zt=(t,e)=>{for(var s in e)A(t,s,{get:e[s],enumerable:!0,configurable:!0,set:(i)=>e[s]=()=>i})};var he={};zt(he,{deactivate:()=>pe,activate:()=>le});module.exports=Qt(he);var r=c(require("vscode")),Dt=c(require("crypto")),x=c(require("fs")),C=c(require("path"));var bt=c(require("vscode")),K=c(require("child_process"));var yt=c(require("child_process")),vt=c(require("readline")),O=c(require("path"));class W{harnessPath;log;process=null;rl=null;handlers=new Set;authenticated=!1;ready=!1;constructor(t,e){this.harnessPath=t;this.log=e}async start(){if(this.process)return;let t=O.dirname(this.harnessPath),e=O.basename(this.harnessPath);this.process=yt.spawn("bun",["run",e],{cwd:t,stdio:["pipe","pipe","pipe"],env:{...process.env}}),this.process.stderr?.on("data",(s)=>{this.log(`[harness stderr] ${s.toString().trim()}`)}),this.process.on("close",(s)=>{this.log(`[harness] exited with code ${s}`),this.process=null,this.rl=null,this.ready=!1,this.authenticated=!1}),this.rl=vt.createInterface({input:this.process.stdout}),this.rl.on("line",(s)=>{try{let i=JSON.parse(s);if(i.type==="ready")this.ready=!0,this.log(`[harness] ready: ${i.sdk}`);for(let n of this.handlers)n(i)}catch{this.log(`[harness] non-JSON: ${s.substring(0,200)}`)}}),await new Promise((s,i)=>{let n=setTimeout(()=>i(Error("Harness startup timeout")),15000),o=(a)=>{if(a.type==="ready")clearTimeout(n),this.handlers.delete(o),s()};this.handlers.add(o)})}async authenticate(t,e){this.send({cmd:"auth",token:t,login:e}),await this.waitFor("auth_ok"),this.authenticated=!0,this.log(`[harness] authenticated as ${e}`)}query(t,e,s,i,n){return new Promise((o,a)=>{let h=(l)=>{if(l.id!==t)return;if(l.type==="event"&&l.event)i(l.event);else if(l.type==="done")this.handlers.delete(h),o();else if(l.type==="cancelled")this.handlers.delete(h),o();else if(l.type==="error")this.handlers.delete(h),a(Error(l.message||"Query failed"))};this.handlers.add(h),this.send({cmd:"query",id:t,prompt:e,workingDirectory:s,model:n?.model,reasoningEffort:n?.reasoningEffort})})}cancel(t){this.send({cmd:"cancel",id:t})}async getModels(){return this.send({cmd:"models"}),(await this.waitFor("models")).data||[]}isReady(){return this.ready&&this.authenticated&&this.process!==null}stop(){if(this.process)this.process.kill(),this.process=null;this.rl=null,this.ready=!1,this.authenticated=!1,this.handlers.clear()}send(t){if(!this.process?.stdin?.writable)throw Error("Harness not running");this.process.stdin.write(JSON.stringify(t)+`
`)}waitFor(t,e=15000){return new Promise((s,i)=>{let n=setTimeout(()=>{this.handlers.delete(o),i(Error(`Timeout waiting for ${t}`))},e),o=(a)=>{if(a.type===t)clearTimeout(n),this.handlers.delete(o),s(a);else if(a.type==="error")clearTimeout(n),this.handlers.delete(o),i(Error(a.message||"Error"))};this.handlers.add(o)})}}class q{extensionUri;harnessPath;log;static viewType="chthonic.chatView";view;connection=null;isConnecting=!1;activeQueryId=null;constructor(t,e,s){this.extensionUri=t;this.harnessPath=e;this.log=s}resolveWebviewView(t,e,s){this.view=t,t.webview.options={enableScripts:!0,localResourceRoots:[this.extensionUri]},t.webview.html=this.getHtml(),t.webview.onDidReceiveMessage(async(i)=>{switch(i.type){case"connect":await this.connectAgent();break;case"prompt":await this.sendPrompt(i.text);break;case"cancel":this.cancelQuery();break;case"disconnect":this.disconnectAgent();break}})}async connectAgent(){if(this.isConnecting||this.connection?.isReady())return;this.isConnecting=!0,this.postMessage({type:"status",status:"connecting"});try{this.connection=new W(this.harnessPath,this.log),await this.connection.start();let t=K.execSync("gh auth token",{encoding:"utf-8"}).trim(),e=K.execSync("gh api user --jq .login",{encoding:"utf-8"}).trim();await this.connection.authenticate(t,e),this.postMessage({type:"connected",agentName:"Chthonic SDK",agentVersion:"0.1.0",login:e}),this.log(`Chat connected: ${e}`)}catch(t){this.log(`Chat connect failed: ${t.message}`),this.postMessage({type:"error",message:t.message}),this.connection?.stop(),this.connection=null}finally{this.isConnecting=!1}}async sendPrompt(t){if(!this.connection?.isReady()){this.postMessage({type:"error",message:"Not connected"});return}let e=crypto.randomUUID();this.activeQueryId=e,this.postMessage({type:"prompt-start"});let s=bt.workspace.workspaceFolders?.[0]?.uri.fsPath||process.cwd();try{await this.connection.query(e,t,s,(i)=>this.handleSdkEvent(i))}catch(i){this.postMessage({type:"error",message:i.message})}finally{this.activeQueryId=null,this.postMessage({type:"prompt-end"})}}handleSdkEvent(t){switch(t.type){case"assistant.message":if(t.data?.content)this.postMessage({type:"agent-message",content:t.data.content});break;case"assistant.message.delta":if(t.data?.delta)this.postMessage({type:"agent-delta",delta:t.data.delta});break;case"tool.execution_start":this.postMessage({type:"tool-start",name:t.data?.name,args:t.data?.arguments});break;case"tool.execution_complete":this.postMessage({type:"tool-end",name:t.data?.name});break;case"assistant.reasoning":this.postMessage({type:"reasoning"});break;case"assistant.usage":this.postMessage({type:"usage",model:t.data?.model,inputTokens:t.data?.inputTokens,outputTokens:t.data?.outputTokens,duration:t.data?.duration});break;case"session.usage_info":this.postMessage({type:"context-info",tokenLimit:t.data?.tokenLimit,currentTokens:t.data?.currentTokens});break}}cancelQuery(){if(this.activeQueryId&&this.connection)this.connection.cancel(this.activeQueryId)}disconnectAgent(){this.connection?.stop(),this.connection=null,this.activeQueryId=null,this.postMessage({type:"disconnected"})}postMessage(t){this.view?.webview.postMessage(t)}dispose(){this.connection?.stop()}getHtml(){return`<!DOCTYPE html>
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
</html>`}}var $=c(require("path")),L=c(require("vscode")),Pt=require("worker_threads");class G{extensionContext;output;records=new Map;recordUris=new Map;onDidUpdateRecordsEmitter=new L.EventEmitter;onDidUpdateRecords=this.onDidUpdateRecordsEmitter.event;onDidUpdateGraphEmitter=new L.EventEmitter;onDidUpdateGraph=this.onDidUpdateGraphEmitter.event;onDidUpdateSnapshotEmitter=new L.EventEmitter;onDidUpdateSnapshot=this.onDidUpdateSnapshotEmitter.event;worker=null;rootPath=null;workerPath;maxFiles=1e4;lastScanDurationMs=0;lastScanAt=0;scanTimer=null;disposed=!1;constructor(t,e){this.extensionContext=t;this.output=e;this.workerPath=t.asAbsolutePath($.join("dist","entropy-worker.js"))}start(t,e,s){this.rootPath=t,this.maxFiles=e,this.ensureWorker(),this.send({type:"scan",root:t,maxFiles:this.maxFiles}),this.scheduleScanLoop(s)}rescanNow(){if(!this.rootPath)return;this.send({type:"scan",root:this.rootPath,maxFiles:this.maxFiles})}refreshFile(t){if(!this.rootPath||t.scheme!=="file")return;this.send({type:"refresh-file",root:this.rootPath,path:t.fsPath})}requestGraph(t){this.send({type:"graph",limit:t})}getRecord(t){if(!this.rootPath||t.scheme!=="file")return;let e=Wt($.relative(this.rootPath,t.fsPath));return this.records.get(e)}getSnapshot(t=40){let e=Array.from(this.records.values()),s=e.length===0?0:e.reduce((n,o)=>n+o.entropy,0)/e.length,i=e.sort((n,o)=>o.entropy-n.entropy).slice(0,t);return{totalFiles:e.length,topEntropy:i,averageEntropy:s,lastScanDurationMs:this.lastScanDurationMs,lastScanAt:this.lastScanAt}}dispose(){if(this.disposed=!0,this.scanTimer)clearInterval(this.scanTimer),this.scanTimer=null;this.send({type:"stop"}),this.worker?.terminate(),this.worker=null,this.onDidUpdateRecordsEmitter.dispose(),this.onDidUpdateGraphEmitter.dispose(),this.onDidUpdateSnapshotEmitter.dispose()}scheduleScanLoop(t){if(this.scanTimer)clearInterval(this.scanTimer);let e=Math.max(5000,t);this.scanTimer=setInterval(()=>{if(!this.disposed)this.rescanNow()},e)}ensureWorker(){if(this.worker)return;this.worker=new Pt.Worker(this.workerPath),this.worker.on("message",(t)=>this.handleWorkerEvent(t)),this.worker.on("error",(t)=>{this.output.appendLine(`[entropy] worker error: ${t.message}`)}),this.worker.on("exit",(t)=>{if(this.output.appendLine(`[entropy] worker exited with code ${t}`),this.worker=null,!this.disposed&&t!==0)this.ensureWorker(),this.rescanNow()})}send(t){this.ensureWorker(),this.worker?.postMessage(t)}handleWorkerEvent(t){switch(t.type){case"scan-progress":{if(!this.rootPath)return;let e=[];for(let s of t.records){this.records.set(s.path,s);let i=this.recordUris.get(s.path);if(!i)i=L.Uri.file($.join(this.rootPath,s.path)),this.recordUris.set(s.path,i);e.push(i)}if(e.length>0)this.onDidUpdateRecordsEmitter.fire(e);break}case"scan-complete":this.lastScanDurationMs=t.durationMs,this.lastScanAt=Date.now(),this.onDidUpdateSnapshotEmitter.fire(this.getSnapshot());break;case"graph-result":this.onDidUpdateGraphEmitter.fire(t.graph);break;case"error":this.output.appendLine(`[entropy] ${t.message}${t.detail?`
${t.detail}`:""}`);break}}}function Wt(t){return t.replace(/\\/g,"/")}var St=c(require("vscode"));class X{workerClient;debounceMs;maxPerFlush;tooltipAugmentProvider;onDidChangeEmitter=new St.EventEmitter;onDidChangeFileDecorations=this.onDidChangeEmitter.event;pending=new Map;flushTimer=null;constructor(t,e,s,i){this.workerClient=t;this.debounceMs=e;this.maxPerFlush=s;this.tooltipAugmentProvider=i;this.workerClient.onDidUpdateRecords((n)=>this.enqueueUpdates(n))}dispose(){if(this.flushTimer)clearTimeout(this.flushTimer),this.flushTimer=null;this.onDidChangeEmitter.dispose()}updateConfig(t,e){this.debounceMs=Math.max(30,t),this.maxPerFlush=Math.max(64,e)}provideFileDecoration(t){if(t.scheme!=="file")return;let e=this.workerClient.getRecord(t);if(!e)return;let s=Kt(e),i=[`Entropy ${(e.entropy*100).toFixed(0)}%`,`Complexity ${e.complexity}`,`Debt ${e.debt}`,`Freshness ${(e.freshness*100).toFixed(0)}%`];if(this.tooltipAugmentProvider)i.push(...this.tooltipAugmentProvider(t));return{color:s,tooltip:i.join(`
`),propagate:!1}}enqueueExternalUpdates(t){this.enqueueUpdates(t)}enqueueUpdates(t){for(let e of t)this.pending.set(e.toString(),e);if(!this.flushTimer)this.flushTimer=setTimeout(()=>this.flush(),this.debounceMs)}flush(){if(this.flushTimer=null,this.pending.size===0)return;let t=Array.from(this.pending.values()).slice(0,this.maxPerFlush);for(let e of t)this.pending.delete(e.toString());if(this.onDidChangeEmitter.fire(t),this.pending.size>0)this.flushTimer=setTimeout(()=>this.flush(),this.debounceMs)}}function Kt(t){let e=Yt(t.entropy*0.78+(1-t.freshness)*0.22),s=Y(118,24,e),i=Y(36,46,e),n=Y(58,42,e);return Gt(s,i,n)}function Gt(t,e,s){let i=t/360,n=e/100,o=s/100,a=(p,g,V)=>{let u=V;if(u<0)u+=1;if(u>1)u-=1;if(u<0.16666666666666666)return p+(g-p)*6*u;if(u<0.5)return g;if(u<0.6666666666666666)return p+(g-p)*(0.6666666666666666-u)*6;return p},h,l,M;if(n===0)h=o,l=o,M=o;else{let p=o<0.5?o*(1+n):o+n-o*n,g=2*o-p;h=a(g,p,i+0.3333333333333333),l=a(g,p,i),M=a(g,p,i-0.3333333333333333)}let R=(p)=>{return Math.round(p*255).toString(16).padStart(2,"0")};return`#${R(h)}${R(l)}${R(M)}`}function Yt(t){if(t<0)return 0;if(t>1)return 1;return t}function Y(t,e,s){return t+(e-t)*s}var w=c(require("path")),m=c(require("vscode"));class j{extensionUri;workerClient;static viewType="chthonic.abyssalView";disposables=[];view=null;rootPath=null;sedimentRequestCallback=null;constructor(t,e){this.extensionUri=t;this.workerClient=e;this.disposables.push(this.workerClient.onDidUpdateGraph((s)=>this.postMessage({type:"graph",graph:s})),this.workerClient.onDidUpdateSnapshot((s)=>this.postMessage({type:"snapshot",snapshot:s})))}setRootPath(t){this.rootPath=t}onRequestSediment(t){this.sedimentRequestCallback=t}postSedimentData(t){this.postMessage({type:"sediment",sediment:t})}dispose(){this.disposables.forEach((t)=>t.dispose()),this.disposables.length=0}resolveWebviewView(t,e,s){this.view=t,t.webview.options={enableScripts:!0,localResourceRoots:[this.extensionUri]},t.webview.html=this.getHtml(t.webview),t.webview.onDidReceiveMessage((i)=>{this.handleMessage(i)})}handleMessage(t){if(!t||typeof t!=="object")return;let e=t;if(!e.type)return;if(e.type==="ready"){this.postMessage({type:"snapshot",snapshot:this.workerClient.getSnapshot()}),this.workerClient.requestGraph(260);return}if(e.type==="requestGraph"){this.workerClient.requestGraph(260);return}if(e.type==="requestSediment"){this.sedimentRequestCallback?.();return}if(e.type==="openFile"&&e.path&&this.rootPath){let s=w.normalize(e.path);if(s.startsWith("..")||w.isAbsolute(s))return;let i=w.join(this.rootPath,s),n=m.Uri.file(i);m.workspace.openTextDocument(n).then((o)=>{m.window.showTextDocument(o,{preview:!1})},()=>{m.window.showWarningMessage(`Unable to open ${e.path}`)})}}postMessage(t){if(!this.view)return;this.view.webview.postMessage(t)}getHtml(t){let e=Xt(),s=t.asWebviewUri(m.Uri.joinPath(this.extensionUri,"media","abyssalPane.js")),i=t.asWebviewUri(m.Uri.joinPath(this.extensionUri,"media","wasm","pkg","entropy_renderer_wasm.js")),n=t.asWebviewUri(m.Uri.joinPath(this.extensionUri,"media","wasm","pkg","entropy_renderer_wasm_bg.wasm")),o=["default-src 'none'",`img-src ${t.cspSource} data:`,`style-src ${t.cspSource} 'unsafe-inline'`,`script-src 'nonce-${e}' ${t.cspSource}`,`connect-src ${t.cspSource}`].join("; "),a=JSON.stringify({wasmModuleUri:i.toString(),wasmBinaryUri:n.toString()});return`<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="${o}">
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
        <p class="subtitle">Rust/WASM bridge to WebGPU, canvas fallback when binaries are absent.</p>
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
        window.__CHTHONIC_ABYSSAL__ = ${a};
    </script>
    <script nonce="${e}" type="module" src="${s}"></script>
</body>
</html>`}}function Xt(){let e="";for(let s=0;s<32;s+=1)e+="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789".charAt(Math.floor(Math.random()*62));return e}var ot=c(require("fs/promises")),y=c(require("path")),rt=c(require("vscode"));var Et=c(require("crypto"));class Z{leaves=new Map;dirty=!1;upsert(t){let e=ee(t.path),s=Zt(e,t);if(this.leaves.get(e)!==s)this.leaves.set(e,s),this.dirty=!0}hasDirty(){return this.dirty}settle(t){if(!this.dirty||this.leaves.size===0)return null;let e=te(Array.from(this.leaves.entries()).sort((s,i)=>s[0].localeCompare(i[0])));return this.dirty=!1,{reason:t,rootHash:e,leafCount:this.leaves.size,generatedAt:Date.now()}}}function Zt(t,e){let s=[t,e.entropy.toFixed(6),e.complexity,e.debt,e.freshness.toFixed(6),e.ruffViolations,e.updatedAt].join("|");return _(s)}function te(t){if(t.length===0)return _("EMPTY");let e=t.map(([s,i])=>_(`${s}:${i}`));while(e.length>1){let s=[];for(let i=0;i<e.length;i+=2){let n=e[i],o=e[i+1]??e[i];s.push(_(`${n}${o}`))}e=s}return e[0]}function _(t){return Et.createHash("sha256").update(t,"utf8").digest("hex")}function ee(t){return t.replace(/\\/g,"/")}var J=c(require("path")),tt=require("child_process"),N=c(require("vscode"));function E(t,e){let s="",i=(n)=>{let o=n.trim();if(!o)return;try{let a=JSON.parse(o);if(!a||typeof a!=="object"||Array.isArray(a))throw Error("JSONL payload must be an object");t(a)}catch(a){e(a instanceof Error?a:Error(String(a)))}};return{push(n){s+=n.toString();while(!0){let o=s.indexOf(`
`);if(o<0)return;let a=s.slice(0,o);s=s.slice(o+1),i(a)}},flush(){if(!s.trim()){s="";return}i(s),s=""}}}class et{output;rootPath=null;pythonSidecar=null;rubySidecar=null;onDidReceiveRuffEmitter=new N.EventEmitter;onDidReceiveRuff=this.onDidReceiveRuffEmitter.event;onDidReceiveLoreEmitter=new N.EventEmitter;onDidReceiveLore=this.onDidReceiveLoreEmitter.event;onDidReceiveSidecarErrorEmitter=new N.EventEmitter;onDidReceiveSidecarError=this.onDidReceiveSidecarErrorEmitter.event;constructor(t){this.output=t}start(t){this.rootPath=t,this.startPythonSidecar(),this.startRubySidecar()}requestScan(t){if(!this.pythonSidecar||this.pythonSidecar.killed)this.startPythonSidecar();this.writeJson(this.pythonSidecar,t)}requestLore(t){if(!this.rubySidecar||this.rubySidecar.killed)this.startRubySidecar();this.writeJson(this.rubySidecar,t)}dispose(){this.pythonSidecar?.kill(),this.rubySidecar?.kill(),this.pythonSidecar=null,this.rubySidecar=null,this.onDidReceiveRuffEmitter.dispose(),this.onDidReceiveLoreEmitter.dispose(),this.onDidReceiveSidecarErrorEmitter.dispose()}startPythonSidecar(){if(!this.rootPath||this.pythonSidecar)return;let t=J.join(this.rootPath,".chthonic","python","entropy_scan.py"),e=J.join(this.rootPath,".chthonic","venv",process.platform==="win32"?"Scripts/python.exe":"bin/python");this.pythonSidecar=tt.spawn("uv",["run","--python",e,t,"--stdio"],{cwd:this.rootPath,stdio:["pipe","pipe","pipe"]});let s=E((i)=>this.handlePythonPayload(i),(i)=>this.output.appendLine(`[polyglot:python] invalid JSONL payload: ${i.message}`));this.pythonSidecar.stdout?.on("data",(i)=>s.push(i)),this.pythonSidecar.stderr?.on("data",(i)=>{this.output.appendLine(`[polyglot:python] ${i.toString().trimEnd()}`)}),this.pythonSidecar.on("error",(i)=>{this.onDidReceiveSidecarErrorEmitter.fire({type:"error",source:"python",message:i.message}),this.output.appendLine(`[polyglot:python] failed to spawn: ${i.message}`),this.pythonSidecar=null}),this.pythonSidecar.on("exit",(i)=>{s.flush(),this.output.appendLine(`[polyglot:python] exited with code ${i??-1}`),this.pythonSidecar=null})}startRubySidecar(){if(!this.rootPath||this.rubySidecar)return;let t=J.join(this.rootPath,".chthonic","ruby","lore.rb");this.rubySidecar=tt.spawn("ruby",[t],{cwd:this.rootPath,stdio:["pipe","pipe","pipe"]});let e=E((s)=>this.handleRubyPayload(s),(s)=>this.output.appendLine(`[polyglot:ruby] invalid JSONL payload: ${s.message}`));this.rubySidecar.stdout?.on("data",(s)=>e.push(s)),this.rubySidecar.stderr?.on("data",(s)=>{this.output.appendLine(`[polyglot:ruby] ${s.toString().trimEnd()}`)}),this.rubySidecar.on("error",(s)=>{this.onDidReceiveSidecarErrorEmitter.fire({type:"error",source:"ruby",message:s.message}),this.output.appendLine(`[polyglot:ruby] failed to spawn: ${s.message}`),this.rubySidecar=null}),this.rubySidecar.on("exit",(s)=>{e.flush(),this.output.appendLine(`[polyglot:ruby] exited with code ${s??-1}`),this.rubySidecar=null})}writeJson(t,e){if(!t?.stdin||t.killed)return;try{t.stdin.write(`${JSON.stringify(e)}
`)}catch(s){this.output.appendLine(`[polyglot] sidecar write failed: ${se(s)}`)}}handlePythonPayload(t){if(t.type==="ruff-summary"){let e=t;this.onDidReceiveRuffEmitter.fire(e);return}if(t.type==="error"){let e=String(t.message??"python sidecar error");this.output.appendLine(`[polyglot:python] ${e}`),this.onDidReceiveSidecarErrorEmitter.fire({type:"error",source:"python",message:e})}}handleRubyPayload(t){if(t.type==="lore"){this.onDidReceiveLoreEmitter.fire(t);return}if(t.type==="error"){let e=String(t.message??"ruby sidecar error");this.output.appendLine(`[polyglot:ruby] ${e}`),this.onDidReceiveSidecarErrorEmitter.fire({type:"error",source:"ruby",message:e})}}}function se(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}var xt=c(require("fs")),I=c(require("fs/promises")),P=c(require("path")),st=require("child_process");class it{output;rootPath=null;options={rpcUrl:"http://127.0.0.1:8899",autostartValidator:!1};ledgerFilePath=null;validatorProcess=null;hostProcess=null;requestCounter=1;pending=new Map;constructor(t){this.output=t}async start(t,e){this.rootPath=t,this.options=e;let s=P.join(t,".chthonic","ledger");if(await I.mkdir(s,{recursive:!0}),this.ledgerFilePath=P.join(s,"entropy-settlements.jsonl"),e.autostartValidator)this.startValidator();this.startHostProcess()}async commitEntropy(t){if(!this.rootPath||!this.ledgerFilePath)return{mode:"offline",detail:"Ledger host not started"};let e={...t,rpcUrl:this.options.rpcUrl,recordedAt:Date.now()},s={mode:"offline",detail:"Rust ledger host unavailable; persisted settlement locally."};try{s=await this.submitToHost(t)}catch(i){this.output.appendLine(`[ledger-rust] submit failed: ${re(i)}`)}return await I.appendFile(this.ledgerFilePath,`${JSON.stringify({...e,receipt:s})}
`,"utf8"),s}dispose(){for(let[t,e]of this.pending)e.reject(Error(`request ${t} cancelled`));this.pending.clear(),this.hostProcess?.kill(),this.hostProcess=null,this.validatorProcess?.kill(),this.validatorProcess=null}startHostProcess(){if(!this.rootPath||this.hostProcess)return;let t=ie(this.rootPath,this.options.hostBinaryPath),e=this.options.walletPath??P.join(this.rootPath,".chthonic","wallets","payer.json"),s=this.options.idlPath??P.join(this.rootPath,".chthonic","wallets","entropy_ledger.json");this.hostProcess=st.spawn(t,["--wallet",e,"--idl",s,"--rpc-url",this.options.rpcUrl],{cwd:this.rootPath,stdio:["pipe","pipe","pipe"]});let i=E((n)=>this.handleHostPayload(n),(n)=>this.output.appendLine(`[ledger-rust] invalid JSON payload: ${n.message}`));this.hostProcess.stdout?.on("data",(n)=>i.push(n)),this.hostProcess.stderr?.on("data",(n)=>{this.output.appendLine(`[ledger-rust] ${n.toString().trimEnd()}`)}),this.hostProcess.on("error",(n)=>{this.output.appendLine(`[ledger-rust] failed to spawn host: ${n.message}`),this.rejectAllPending(Error(`host spawn failed: ${n.message}`)),this.hostProcess=null}),this.hostProcess.on("exit",(n)=>{i.flush(),this.output.appendLine(`[ledger-rust] host exited with code ${n??-1}`),this.rejectAllPending(Error("ledger host exited")),this.hostProcess=null})}async submitToHost(t){if(!this.hostProcess||this.hostProcess.killed)this.startHostProcess();if(!this.hostProcess?.stdin||this.hostProcess.killed)return{mode:"offline",detail:"Rust host binary is missing or not executable."};let e=this.requestCounter++,s={jsonrpc:"2.0",id:e,method:"submit_entropy",params:{entropy_score:Math.max(0,Math.round(t.leafCount*17+13)),merkle_root:t.rootHash,leaf_count:t.leafCount,reason:t.reason}};return await new Promise((n,o)=>{this.pending.set(e,{resolve:n,reject:o}),this.hostProcess?.stdin?.write(`${JSON.stringify(s)}
`,(a)=>{if(!a)return;this.pending.delete(e),o(a)})})}handleHostPayload(t){let e=t.id;if(typeof e!=="number")return;let s=this.pending.get(e);if(!s)return;if(this.pending.delete(e),t.error&&typeof t.error==="object"){let n=t;s.resolve({mode:"offline",detail:`Rust ledger error ${n.error.code}: ${n.error.message}`});return}let i=t;s.resolve({mode:"validator-rust",txSignature:i.result.signature,detail:`Rust anchor-client submission accepted${i.result.slot?` (slot ${i.result.slot})`:""}.`})}rejectAllPending(t){for(let[e,s]of this.pending)this.pending.delete(e),s.reject(t)}startValidator(){if(!this.rootPath||this.validatorProcess)return;let t=ne(this.rootPath),e=oe(this.options.rpcUrl)??8899,s=P.join(this.rootPath,".chthonic","solana-ledger");this.validatorProcess=st.spawn(t,["--ledger",s,"--rpc-port",String(e),"--reset","--quiet"],{cwd:this.rootPath,stdio:["ignore","pipe","pipe"]}),this.validatorProcess.stdout?.on("data",(i)=>{this.output.appendLine(`[solana] ${i.toString().trimEnd()}`)}),this.validatorProcess.stderr?.on("data",(i)=>{this.output.appendLine(`[solana] ${i.toString().trimEnd()}`)}),this.validatorProcess.on("error",(i)=>{this.output.appendLine(`[solana] validator spawn error: ${i.message}`),this.validatorProcess=null}),this.validatorProcess.on("exit",(i)=>{this.output.appendLine(`[solana] validator exited with code ${i??-1}`),this.validatorProcess=null})}}function ie(t,e){if(e)return e;let s=process.platform==="win32"?"entropy-ledger-host.exe":"entropy-ledger-host";return P.join(t,"native","target","release",s)}function ne(t){let e=process.platform==="win32"?"solana-test-validator.exe":"solana-test-validator",s=P.join(t,".chthonic","bin",e);if(xt.existsSync(s))return s;return process.platform==="win32"?"solana-test-validator":e}function oe(t){try{let e=new URL(t);if(!e.port)return null;let s=Number(e.port);return Number.isFinite(s)?s:null}catch{return null}}function re(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}class nt{output;options;backend=null;constructor(t,e){this.output=t;this.options=e}async start(t){this.backend=this.options.mode==="bankrun"?new kt(this.output):new Lt(this.output,this.options),await this.backend.start(t)}async commitEntropy(t){if(!this.backend)return{mode:"offline",detail:"LedgerBroker backend not initialized."};return this.backend.commitEntropy(t)}dispose(){this.backend?.dispose(),this.backend=null}}class kt{output;sequence=0;constructor(t){this.output=t}async start(t){this.output.appendLine("[ledger] phantom mode active (bankrun simulation).")}async commitEntropy(t){return this.sequence+=1,{mode:"bankrun",txSignature:`bankrun-${t.rootHash.slice(0,20)}-${this.sequence}`,detail:"In-memory bankrun simulation accepted the entropy settlement."}}dispose(){}}class Lt{options;client;constructor(t,e){this.options=e;this.client=new it(t)}async start(t){await this.client.start(t,{rpcUrl:this.options.rpcUrl,autostartValidator:this.options.autostartValidator,hostBinaryPath:this.options.hostBinaryPath,walletPath:this.options.walletPath,idlPath:this.options.idlPath})}async commitEntropy(t){return this.client.commitEntropy(t)}dispose(){this.client.dispose()}}class at{output;workerClient;options;requestDecorationRefresh;broker;merkle=new Z;ledger;tooltipAugments=new Map;rootPath=null;scanTimer=null;settleTimer=null;gitPollTimer=null;gitHeadSnapshot=null;pendingSettleReason=null;disposables=[];constructor(t,e,s,i){this.output=t;this.workerClient=e;this.options=s;this.requestDecorationRefresh=i;this.broker=new et(t),this.ledger=new nt(t,{mode:this.options.ledgerMode,rpcUrl:this.options.solanaRpcUrl,autostartValidator:this.options.solanaAutostartValidator,hostBinaryPath:this.options.solanaLedgerHostBinaryPath,walletPath:this.options.solanaWalletPath,idlPath:this.options.solanaIdlPath}),this.disposables.push(this.broker.onDidReceiveRuff((n)=>this.applyRuffSummary(n.files)),this.broker.onDidReceiveLore((n)=>this.applyLore(n)),this.workerClient.onDidUpdateRecords((n)=>this.captureEntropyLeaves(n)))}async start(t){if(this.rootPath=t,!this.options.enabled)return;this.broker.start(t),await this.ledger.start(t),this.broker.requestScan({type:"scan",reason:"manual",root:t}),this.startScanLoop(),this.startGitWatcher()}onDidSaveDocument(t){if(!this.rootPath||!this.options.enabled||t.uri.scheme!=="file")return;let e=wt(this.rootPath,t.uri.fsPath);if(!e)return;this.broker.requestScan({type:"scan",reason:"save",root:this.rootPath,files:[e]}),this.scheduleSettlement("save")}requestManualScan(){if(!this.rootPath||!this.options.enabled)return;this.broker.requestScan({type:"scan",reason:"manual",root:this.rootPath})}getTooltipFragments(t){if(!this.rootPath||t.scheme!=="file")return[];let e=wt(this.rootPath,t.fsPath);if(!e)return[];let s=this.tooltipAugments.get(e);if(!s)return[];let i=[];if(s.ruffViolations>0)i.push(`Ruff ${s.ruffViolations} violation${s.ruffViolations===1?"":"s"}`);if(s.loreLine)i.push(s.loreLine);return i}dispose(){if(this.scanTimer)clearInterval(this.scanTimer),this.scanTimer=null;if(this.settleTimer)clearTimeout(this.settleTimer),this.settleTimer=null;if(this.gitPollTimer)clearInterval(this.gitPollTimer),this.gitPollTimer=null;this.broker.dispose(),this.ledger.dispose(),this.disposables.forEach((t)=>t.dispose()),this.disposables.length=0}captureEntropyLeaves(t){if(!this.options.enabled)return;for(let e of t){let s=this.workerClient.getRecord(e);if(!s)continue;let i=this.tooltipAugments.get(s.path);this.merkle.upsert({path:s.path,entropy:s.entropy,complexity:s.complexity,debt:s.debt,freshness:s.freshness,ruffViolations:i?.ruffViolations??0,updatedAt:Date.now()})}}applyRuffSummary(t){if(!this.rootPath||!this.options.enabled)return;let e=[];for(let s of t){let i=this.tooltipAugments.get(s.path),n={ruffViolations:s.violations,loreLine:i?.loreLine};this.tooltipAugments.set(s.path,n);let o=rt.Uri.file(y.join(this.rootPath,s.path));e.push(o);let a=this.workerClient.getRecord(o);if(a){if(this.merkle.upsert({path:a.path,entropy:a.entropy,complexity:a.complexity,debt:a.debt,freshness:a.freshness,ruffViolations:s.violations,updatedAt:Date.now()}),a.entropy>=0.45||s.violations>0)this.broker.requestLore({type:"lore-request",root:this.rootPath,path:s.path,entropy:a.entropy,violations:s.violations})}}if(e.length>0)this.requestDecorationRefresh(e)}applyLore(t){if(!this.rootPath||!this.options.enabled)return;if(t.root!==this.rootPath)return;let e=this.tooltipAugments.get(t.path);this.tooltipAugments.set(t.path,{ruffViolations:e?.ruffViolations??t.violations,loreLine:t.line}),this.requestDecorationRefresh([rt.Uri.file(y.join(this.rootPath,t.path))])}startScanLoop(){if(this.scanTimer||!this.rootPath)return;let t=Math.max(this.options.pythonScanIntervalMs,1e4);this.scanTimer=setInterval(()=>{if(!this.rootPath)return;this.broker.requestScan({type:"scan",reason:"interval",root:this.rootPath})},t)}startGitWatcher(){if(!this.rootPath||this.gitPollTimer)return;this.gitHeadSnapshot=null,this.gitPollTimer=setInterval(async()=>{if(!this.rootPath)return;let t=await ae(this.rootPath);if(!t)return;if(!this.gitHeadSnapshot){this.gitHeadSnapshot=t;return}if(t!==this.gitHeadSnapshot){if(this.gitHeadSnapshot=t,this.output.appendLine("[polyglot] git HEAD changed, scheduling Merkle settlement."),this.rootPath)this.broker.requestScan({type:"scan",reason:"commit",root:this.rootPath});this.scheduleSettlement("commit")}},6000)}scheduleSettlement(t){if(!this.options.enabled)return;if(this.pendingSettleReason=t==="commit"?"commit":this.pendingSettleReason??t,this.settleTimer)clearTimeout(this.settleTimer);this.settleTimer=setTimeout(()=>{this.settleTimer=null,this.flushSettlement()},Math.max(this.options.settleDebounceMs,300))}async flushSettlement(){let t=this.pendingSettleReason??"manual";this.pendingSettleReason=null;let e=this.merkle.settle(t);if(!e)return;let s=await this.ledger.commitEntropy(e),i=[`[polyglot] settled Merkle root ${e.rootHash.slice(0,16)}...`,`leaves=${e.leafCount}`,`mode=${s.mode}`];if(s.txSignature)i.push(`tx=${s.txSignature}`);i.push(`detail=${s.detail}`),this.output.appendLine(i.join(" "))}}async function ae(t){let e=y.join(t,".git"),s=y.join(e,"HEAD"),i="";try{i=await ot.readFile(s,"utf8")}catch{return null}let n=i.trim();if(!n)return null;if(!n.startsWith("ref:"))return n;let o=n.slice(4).trim(),a=y.join(e,o);try{let h=await ot.readFile(a,"utf8");return`ref:${o}:${h.trim()}`}catch{return`ref:${o}:missing`}}function wt(t,e){let s=y.relative(t,e);if(!s||s.startsWith("..")||y.isAbsolute(s))return null;return s.replace(/\\/g,"/")}var Mt=c(require("path")),Rt=require("child_process"),U=c(require("vscode"));class dt{output;headlessVulkan;daemonBinaryOverride;rootPath=null;daemonProcess=null;requestCounter=1;pending=new Map;onDidReceiveManifestEmitter=new U.EventEmitter;onDidReceiveManifest=this.onDidReceiveManifestEmitter.event;onDidReceiveEnvEmitter=new U.EventEmitter;onDidReceiveEnv=this.onDidReceiveEnvEmitter.event;onDidReceiveSedimentEmitter=new U.EventEmitter;onDidReceiveSediment=this.onDidReceiveSedimentEmitter.event;constructor(t,e,s){this.output=t;this.headlessVulkan=e;this.daemonBinaryOverride=s}start(t){this.rootPath=t,this.startDaemon()}async requestSediment(t,e){return this.submitRequest("reactor/sediment",{max_layers:t,max_files:e})}async requestDetect(){return this.submitRequest("anno/detect",{})}async requestProvision(){return this.submitRequest("anno/provision",{})}dispose(){for(let[,t]of this.pending)t.reject(Error("AnnoClient disposed"));this.pending.clear(),this.daemonProcess?.kill(),this.daemonProcess=null,this.onDidReceiveManifestEmitter.dispose(),this.onDidReceiveEnvEmitter.dispose(),this.onDidReceiveSedimentEmitter.dispose()}startDaemon(){if(!this.rootPath||this.daemonProcess)return;let t=this.daemonBinaryOverride??de(this.rootPath),e=["--workspace",this.rootPath];if(this.headlessVulkan)e.push("--headless-vulkan");this.daemonProcess=Rt.spawn(t,e,{cwd:this.rootPath,stdio:["pipe","pipe","pipe"]});let s=E((i)=>this.handlePayload(i),(i)=>this.output.appendLine(`[daemon] invalid JSONL: ${i.message}`));this.daemonProcess.stdout?.on("data",(i)=>s.push(i)),this.daemonProcess.stderr?.on("data",(i)=>{this.output.appendLine(`[daemon] ${i.toString().trimEnd()}`)}),this.daemonProcess.on("error",(i)=>{this.output.appendLine(`[daemon] spawn failed: ${i.message}`),this.rejectAllPending(Error(`daemon spawn failed: ${i.message}`)),this.daemonProcess=null}),this.daemonProcess.on("exit",(i)=>{s.flush(),this.output.appendLine(`[daemon] exited with code ${i??-1}`),this.rejectAllPending(Error("daemon exited")),this.daemonProcess=null})}handlePayload(t){if("method"in t&&!("id"in t)){this.handleNotification(t);return}if("id"in t&&typeof t.id==="number")this.handleResponse(t)}handleNotification(t){let{method:e,params:s}=t;switch(e){case"anno/manifest":this.onDidReceiveManifestEmitter.fire(s),this.output.appendLine(`[daemon] ANNO manifest received (${s.languages?.length??0} languages)`);break;case"anno/env":this.onDidReceiveEnvEmitter.fire(s),this.output.appendLine("[daemon] env report received");break;case"reactor/status":{let i=s.status??"unknown";this.output.appendLine(`[daemon] reactor status: ${i}`);break}default:this.output.appendLine(`[daemon] unknown notification: ${e}`)}}handleResponse(t){let e=t.id,s=this.pending.get(e);if(!s)return;if(this.pending.delete(e),t.error&&typeof t.error==="object"){let i=t.error;s.reject(Error(i.message));return}s.resolve(t.result)}submitRequest(t,e){if(!this.daemonProcess?.stdin||this.daemonProcess.killed)this.startDaemon();if(!this.daemonProcess?.stdin)return Promise.reject(Error("daemon not available"));let s=this.requestCounter++,i={jsonrpc:"2.0",id:s,method:t,params:e};return new Promise((n,o)=>{this.pending.set(s,{resolve:n,reject:o}),this.daemonProcess?.stdin?.write(`${JSON.stringify(i)}
`,(a)=>{if(a)this.pending.delete(s),o(a)})})}rejectAllPending(t){for(let[e,s]of this.pending)this.pending.delete(e),s.reject(t)}}function de(t){let e=process.platform==="win32"?"chthonic-daemon.exe":"chthonic-daemon";return Mt.join(t,"native","target","release",e)}var S=c(require("vscode"));class ct{output;envCollection;disposed=!1;constructor(t,e){this.output=t;this.envCollection=e}async activate(){if(this.disposed)return;try{await S.commands.executeCommand("workbench.action.closeSidebar"),await S.commands.executeCommand("workbench.action.terminal.moveToSidePanel"),await S.commands.executeCommand("workbench.action.toggleAuxiliaryBar"),await S.commands.executeCommand("workbench.action.toggleMaximizedPanel"),await S.commands.executeCommand("workbench.action.focusActiveEditorGroup"),this.output.appendLine("[cockpit] layout activated: sidebar=closed, terminal=AuxBar, panel=maximized, editor=Center")}catch(t){this.output.appendLine(`[cockpit] layout activation failed: ${ce(t)}`)}}applyTerminalEnv(t){if(this.disposed)return;if(!t.path_mutations.length&&!t.dev_kit)return;let e=t.path_mutations.sort((n,o)=>n.priority-o.priority).map((n)=>n.path),s=process.platform==="win32"?";":":";for(let n of e)this.envCollection.prepend("PATH",`${n}${s}`);if(t.dev_kit){for(let[n,o]of t.dev_kit.env_vars)this.envCollection.replace(n,o);for(let n of t.dev_kit.path_prepend)this.envCollection.prepend("PATH",`${n}${s}`)}for(let n of S.window.terminals)if(process.platform==="win32"){for(let o of e)n.sendText(`$env:PATH = "${o};$env:PATH"`,!0);if(t.dev_kit)for(let[o,a]of t.dev_kit.env_vars)n.sendText(`$env:${o} = "${a}"`,!0)}else{for(let o of e)n.sendText(`export PATH="${o}:$PATH"`,!0);if(t.dev_kit)for(let[o,a]of t.dev_kit.env_vars)n.sendText(`export ${o}="${a}"`,!0)}let i=e.length+(t.dev_kit?.env_vars.length??0);if(this.output.appendLine(`[cockpit] terminal env updated: ${i} mutations applied`),t.warnings.length>0)for(let n of t.warnings)this.output.appendLine(`[cockpit] warning: ${n}`)}dispose(){this.disposed=!0}}function ce(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}function le(t){console.log("☥ Chthonic Archive extension activated");let e=r.window.createOutputChannel("Chthonic SDK"),s=r.workspace.workspaceFolders?.[0]?.uri.fsPath||null,i=C.join(s||"","meta-ide","copilot-sdk","harness.ts"),n=new q(t.extensionUri,i,(d)=>e.appendLine(`[${new Date().toISOString()}] ${d}`));t.subscriptions.push(r.window.registerWebviewViewProvider(q.viewType,n));let o=r.workspace.getConfiguration("chthonic"),a=o.get("entropy.enabled",!0),h=o.get("entropy.maxFiles",1e4),l=o.get("entropy.scanIntervalMs",20000),M=o.get("entropy.decorationDebounceMs",120),R=o.get("entropy.decorationBatchSize",240),p=o.get("entropy.polyglotEnabled",!0),g=o.get("entropy.pythonScanIntervalMs",30000),V=o.get("entropy.ledgerSettleDebounceMs",1400),u=o.get("entropy.ledgerMode","validator"),Ct=o.get("entropy.solanaRpcUrl","http://127.0.0.1:8899"),Tt=o.get("entropy.solanaAutostartValidator",!1),Ht=F(o.get("entropy.solanaLedgerHostBinaryPath","")),Ot=F(o.get("entropy.solanaWalletPath","")),qt=F(o.get("entropy.solanaIdlPath","")),f=new G(t,e),T,k=new at(e,f,{enabled:p,pythonScanIntervalMs:g,settleDebounceMs:V,ledgerMode:u,solanaRpcUrl:Ct,solanaAutostartValidator:Tt,solanaLedgerHostBinaryPath:Ht,solanaWalletPath:Ot,solanaIdlPath:qt},(d)=>T?.enqueueExternalUpdates(d));T=new X(f,M,R,(d)=>k.getTooltipFragments(d));let B=new j(t.extensionUri,f);if(B.setRootPath(s),t.subscriptions.push(f,T,B,k,r.window.registerFileDecorationProvider(T),r.window.registerWebviewViewProvider(j.viewType,B)),s&&a)f.start(s,h,l),k.start(s);t.subscriptions.push(r.workspace.onDidSaveTextDocument((d)=>{f.refreshFile(d.uri),k.onDidSaveDocument(d)})),t.subscriptions.push(r.commands.registerCommand("chthonic.entropyRefresh",()=>{f.rescanNow(),f.requestGraph(260),k.requestManualScan(),r.window.showInformationMessage("Chthonic entropy scan requested")}));let jt=o.get("reactor.enabled",!0),_t=o.get("reactor.headlessVulkan",!0),Jt=o.get("reactor.cockpitAutoLayout",!1),Nt=F(o.get("reactor.daemonBinaryPath","")),v=new dt(e,_t,Nt),H=new ct(e,t.environmentVariableCollection);if(t.subscriptions.push(v,H),t.subscriptions.push(v.onDidReceiveEnv((d)=>{H.applyTerminalEnv(d)}),v.onDidReceiveSediment((d)=>{B.postSedimentData(d)})),B.onRequestSediment(()=>{v.requestSediment(10,500).catch((d)=>{e.appendLine(`[reactor] sediment request from webview failed: ${d}`)})}),s&&jt){if(v.start(s),Jt)H.activate();let d=C.join(s,".git","HEAD");if(x.existsSync(d)){let b=null,D=x.watch(C.join(s,".git"),{persistent:!1},(z,ut)=>{if(ut==="HEAD"||ut?.startsWith("refs")){if(b)clearTimeout(b);b=setTimeout(()=>{e.appendLine("[reactor] git change detected, recomputing sediment"),v.requestSediment(10,500).catch((It)=>{e.appendLine(`[reactor] live-loop sediment failed: ${It}`)})},800)}});t.subscriptions.push({dispose:()=>D.close()})}}t.subscriptions.push(r.commands.registerCommand("chthonic.activateCockpit",()=>{H.activate()}),r.commands.registerCommand("chthonic.annoDetect",()=>{if(s)v.start(s);r.window.showInformationMessage("ANNO project detection triggered")}),r.commands.registerCommand("chthonic.reactorSediment",async()=>{try{let d=await v.requestSediment(10,500);r.window.showInformationMessage(`Sediment computed: ${d.file_count} files, ${d.layer_count} layers (${d.backend}, ${d.compute_time_ms}ms)`)}catch(d){r.window.showErrorMessage(`Sediment computation failed: ${d}`)}}));let Q=new At;r.window.registerTreeDataProvider("chthonic.themeView",Q),t.subscriptions.push(r.commands.registerCommand("chthonic.switchTheme",async()=>{let d=[{label:"$(paintcan) Flesh & Earth",description:"Warm earth · WCAG AA · Distribution palette",id:"Chthonic Mandala - Flesh & Earth"},{label:"$(zap) ROGBIV",description:"SSOT spectral · FA¹⁻⁵ canonical hexes",id:"Chthonic Mandala - ROGBIV"}],b=r.workspace.getConfiguration("workbench").get("colorTheme"),D=await r.window.showQuickPick(d.map((z)=>({...z,picked:b===z.id})),{placeHolder:`Current: ${b}`});if(D)await r.workspace.getConfiguration("workbench").update("colorTheme",D.id,r.ConfigurationTarget.Workspace),r.window.showInformationMessage(`Theme: ${D.id}`),Q.refresh()}));let pt=r.workspace.getConfiguration("chthonic");if(pt.get("showSSOTHash",!0)){let d=r.window.createStatusBarItem(r.StatusBarAlignment.Left,50);d.command="chthonic.verifySSOT",d.tooltip="SSOT integrity hash — click to verify",t.subscriptions.push(d),Bt(d),t.subscriptions.push(r.workspace.onDidSaveTextDocument((b)=>{if(b.fileName.includes("copilot-instructions"))Bt(d)}))}if(pt.get("showLineage",!0)){let d=r.window.createStatusBarItem(r.StatusBarAlignment.Left,49);d.text="$(git-branch) ☥ main",d.tooltip="Chthonic lineage",d.show(),t.subscriptions.push(d)}let ht=new $t;r.window.registerTreeDataProvider("chthonic.statusView",ht),t.subscriptions.push(r.commands.registerCommand("chthonic.verifySSOT",async()=>{let d=lt();if(d)r.window.showInformationMessage(`SSOT SHA-256: ${d.substring(0,16)}…`);else r.window.showWarningMessage("SSOT file not found")})),t.subscriptions.push(r.commands.registerCommand("chthonic.refreshStatus",()=>{ht.refresh(),Q.refresh(),f.rescanNow(),f.requestGraph(260),k.requestManualScan()}))}function pe(){}function lt(){let t=r.workspace.workspaceFolders?.[0];if(!t)return null;let e=r.workspace.getConfiguration("chthonic").get("ssotPath",".github/copilot-instructions.md"),s=C.join(t.uri.fsPath,e);if(!x.existsSync(s))return null;let n=x.readFileSync(s,"utf-8").replace(/\r\n/g,`
`).replace(/\r/g,`
`).split(`
`).map((o)=>o.trimEnd()).join(`
`).trim();return Dt.createHash("sha256").update(n,"utf-8").digest("hex")}function Bt(t){let e=lt();if(e)t.text=`$(shield) ${e.substring(0,8)}`,t.show();else t.text="$(shield) SSOT ??",t.show()}function F(t){let e=t.trim();return e.length>0?e:void 0}class At{_onDidChange=new r.EventEmitter;onDidChangeTreeData=this._onDidChange.event;refresh(){this._onDidChange.fire()}getTreeItem(t){return t}getChildren(){let t=r.workspace.getConfiguration("workbench").get("colorTheme")||"";return[{name:"Chthonic Mandala - Flesh & Earth",short:"Flesh & Earth",icon:"\uD83C\uDF0D",desc:"Warm earth · Distribution"},{name:"Chthonic Mandala - ROGBIV",short:"ROGBIV",icon:"\uD83C\uDF08",desc:"SSOT spectral · Research"}].map((s)=>{let i=t===s.name,n=new r.TreeItem(`${i?"◉":"○"} ${s.icon} ${s.short}`,r.TreeItemCollapsibleState.None);return n.tooltip=`${s.name}
${s.desc}${i?`

✅ ACTIVE`:""}`,n.description=i?"active":"",n.command={command:"chthonic.switchTheme",title:"Switch"},n})}}class $t{_onDidChange=new r.EventEmitter;onDidChangeTreeData=this._onDidChange.event;refresh(){this._onDidChange.fire()}getTreeItem(t){return t}getChildren(){let t=lt(),e=[],s=new r.TreeItem(`$(shield) SSOT: ${t?t.substring(0,12)+"…":"not found"}`,r.TreeItemCollapsibleState.None);s.command={command:"chthonic.verifySSOT",title:"Verify"},e.push(s);let i=new r.TreeItem(`$(paintcan) Theme: ${(r.workspace.getConfiguration("workbench").get("colorTheme")||"default").replace("Chthonic Mandala - ","")}`,r.TreeItemCollapsibleState.None);return i.command={command:"chthonic.switchTheme",title:"Switch"},e.push(i),e}}
