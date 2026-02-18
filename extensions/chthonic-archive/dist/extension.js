var Ie=Object.create;var{getPrototypeOf:_e,defineProperty:j,getOwnPropertyNames:Ot,getOwnPropertyDescriptor:Ve}=Object,jt=Object.prototype.hasOwnProperty;var d=(t,e,s)=>{s=t!=null?Ie(_e(t)):{};let i=e||!t||!t.__esModule?j(s,"default",{value:t,enumerable:!0}):s;for(let o of Ot(t))if(!jt.call(i,o))j(i,o,{get:()=>t[o],enumerable:!0});return i},Vt=new WeakMap,Oe=(t)=>{var e=Vt.get(t),s;if(e)return e;if(e=j({},"__esModule",{value:!0}),t&&typeof t==="object"||typeof t==="function")Ot(t).map((i)=>!jt.call(e,i)&&j(e,i,{get:()=>t[i],enumerable:!(s=Ve(t,i))||s.enumerable}));return Vt.set(t,e),e};var je=(t,e)=>{for(var s in e)j(t,s,{get:e[s],enumerable:!0,configurable:!0,set:(i)=>e[s]=()=>i})};var xs={};je(xs,{deactivate:()=>ys,activate:()=>gs});module.exports=Oe(xs);var c=d(require("vscode")),ue=d(require("crypto")),D=d(require("fs")),U=d(require("path"));var Ft=d(require("vscode")),ct=d(require("child_process"));var Ht=d(require("child_process")),qt=d(require("readline")),z=d(require("path"));class at{harnessPath;log;process=null;rl=null;handlers=new Set;authenticated=!1;ready=!1;constructor(t,e){this.harnessPath=t;this.log=e}async start(){if(this.process)return;let t=z.dirname(this.harnessPath),e=z.basename(this.harnessPath);this.process=Ht.spawn("bun",["run",e],{cwd:t,stdio:["pipe","pipe","pipe"],env:{...process.env}}),this.process.stderr?.on("data",(s)=>{this.log(`[harness stderr] ${s.toString().trim()}`)}),this.process.on("close",(s)=>{this.log(`[harness] exited with code ${s}`),this.process=null,this.rl=null,this.ready=!1,this.authenticated=!1}),this.rl=qt.createInterface({input:this.process.stdout}),this.rl.on("line",(s)=>{try{let i=JSON.parse(s);if(i.type==="ready")this.ready=!0,this.log(`[harness] ready: ${i.sdk}`);for(let o of this.handlers)o(i)}catch{this.log(`[harness] non-JSON: ${s.substring(0,200)}`)}}),await new Promise((s,i)=>{let o=setTimeout(()=>i(Error("Harness startup timeout")),15000),n=(a)=>{if(a.type==="ready")clearTimeout(o),this.handlers.delete(n),s()};this.handlers.add(n)})}async authenticate(t,e){this.send({cmd:"auth",token:t,login:e}),await this.waitFor("auth_ok"),this.authenticated=!0,this.log(`[harness] authenticated as ${e}`)}query(t,e,s,i,o){return new Promise((n,a)=>{let l=(h)=>{if(h.id!==t)return;if(h.type==="event"&&h.event)i(h.event);else if(h.type==="done")this.handlers.delete(l),n();else if(h.type==="cancelled")this.handlers.delete(l),n();else if(h.type==="error")this.handlers.delete(l),a(Error(h.message||"Query failed"))};this.handlers.add(l),this.send({cmd:"query",id:t,prompt:e,workingDirectory:s,model:o?.model,reasoningEffort:o?.reasoningEffort})})}cancel(t){this.send({cmd:"cancel",id:t})}async getModels(){return this.send({cmd:"models"}),(await this.waitFor("models")).data||[]}isReady(){return this.ready&&this.authenticated&&this.process!==null}stop(){if(this.process)this.process.kill(),this.process=null;this.rl=null,this.ready=!1,this.authenticated=!1,this.handlers.clear()}send(t){if(!this.process?.stdin?.writable)throw Error("Harness not running");this.process.stdin.write(JSON.stringify(t)+`
`)}waitFor(t,e=15000){return new Promise((s,i)=>{let o=setTimeout(()=>{this.handlers.delete(n),i(Error(`Timeout waiting for ${t}`))},e),n=(a)=>{if(a.type===t)clearTimeout(o),this.handlers.delete(n),s(a);else if(a.type==="error")clearTimeout(o),this.handlers.delete(n),i(Error(a.message||"Error"))};this.handlers.add(n)})}}class Q{extensionUri;harnessPath;log;static viewType="chthonic.chatView";view;connection=null;isConnecting=!1;activeQueryId=null;constructor(t,e,s){this.extensionUri=t;this.harnessPath=e;this.log=s}resolveWebviewView(t,e,s){this.view=t,t.webview.options={enableScripts:!0,localResourceRoots:[this.extensionUri]},t.webview.html=this.getHtml(),t.webview.onDidReceiveMessage(async(i)=>{switch(i.type){case"connect":await this.connectAgent();break;case"prompt":await this.sendPrompt(i.text);break;case"cancel":this.cancelQuery();break;case"disconnect":this.disconnectAgent();break}})}async connectAgent(){if(this.isConnecting||this.connection?.isReady())return;this.isConnecting=!0,this.postMessage({type:"status",status:"connecting"});try{this.connection=new at(this.harnessPath,this.log),await this.connection.start();let t=ct.execSync("gh auth token",{encoding:"utf-8"}).trim(),e=ct.execSync("gh api user --jq .login",{encoding:"utf-8"}).trim();await this.connection.authenticate(t,e),this.postMessage({type:"connected",agentName:"Chthonic SDK",agentVersion:"0.1.0",login:e}),this.log(`Chat connected: ${e}`)}catch(t){this.log(`Chat connect failed: ${t.message}`),this.postMessage({type:"error",message:t.message}),this.connection?.stop(),this.connection=null}finally{this.isConnecting=!1}}async sendPrompt(t){if(!this.connection?.isReady()){this.postMessage({type:"error",message:"Not connected"});return}let e=crypto.randomUUID();this.activeQueryId=e,this.postMessage({type:"prompt-start"});let s=Ft.workspace.workspaceFolders?.[0]?.uri.fsPath||process.cwd();try{await this.connection.query(e,t,s,(i)=>this.handleSdkEvent(i))}catch(i){this.postMessage({type:"error",message:i.message})}finally{this.activeQueryId=null,this.postMessage({type:"prompt-end"})}}handleSdkEvent(t){switch(t.type){case"assistant.message":if(t.data?.content)this.postMessage({type:"agent-message",content:t.data.content});break;case"assistant.message.delta":if(t.data?.delta)this.postMessage({type:"agent-delta",delta:t.data.delta});break;case"tool.execution_start":this.postMessage({type:"tool-start",name:t.data?.name,args:t.data?.arguments});break;case"tool.execution_complete":this.postMessage({type:"tool-end",name:t.data?.name});break;case"assistant.reasoning":this.postMessage({type:"reasoning"});break;case"assistant.usage":this.postMessage({type:"usage",model:t.data?.model,inputTokens:t.data?.inputTokens,outputTokens:t.data?.outputTokens,duration:t.data?.duration});break;case"session.usage_info":this.postMessage({type:"context-info",tokenLimit:t.data?.tokenLimit,currentTokens:t.data?.currentTokens});break}}cancelQuery(){if(this.activeQueryId&&this.connection)this.connection.cancel(this.activeQueryId)}disconnectAgent(){this.connection?.stop(),this.connection=null,this.activeQueryId=null,this.postMessage({type:"disconnected"})}postMessage(t){this.view?.webview.postMessage(t)}dispose(){this.connection?.stop()}getHtml(){return`<!DOCTYPE html>
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
</html>`}}var H=d(require("path")),_=d(require("vscode")),Ut=require("worker_threads");class dt{extensionContext;output;records=new Map;recordUris=new Map;onDidUpdateRecordsEmitter=new _.EventEmitter;onDidUpdateRecords=this.onDidUpdateRecordsEmitter.event;onDidUpdateGraphEmitter=new _.EventEmitter;onDidUpdateGraph=this.onDidUpdateGraphEmitter.event;onDidUpdateSnapshotEmitter=new _.EventEmitter;onDidUpdateSnapshot=this.onDidUpdateSnapshotEmitter.event;worker=null;rootPath=null;workerPath;maxFiles=1e4;lastScanDurationMs=0;lastScanAt=0;scanTimer=null;disposed=!1;constructor(t,e){this.extensionContext=t;this.output=e;this.workerPath=t.asAbsolutePath(H.join("dist","entropy-worker.js"))}start(t,e,s){this.rootPath=t,this.maxFiles=e,this.ensureWorker(),this.send({type:"scan",root:t,maxFiles:this.maxFiles}),this.scheduleScanLoop(s)}rescanNow(){if(!this.rootPath)return;this.send({type:"scan",root:this.rootPath,maxFiles:this.maxFiles})}refreshFile(t){if(!this.rootPath||t.scheme!=="file")return;this.send({type:"refresh-file",root:this.rootPath,path:t.fsPath})}requestGraph(t){this.send({type:"graph",limit:t})}getRecord(t){if(!this.rootPath||t.scheme!=="file")return;let e=He(H.relative(this.rootPath,t.fsPath));return this.records.get(e)}getSnapshot(t=40){let e=Array.from(this.records.values()),s=e.length===0?0:e.reduce((o,n)=>o+n.entropy,0)/e.length,i=e.sort((o,n)=>n.entropy-o.entropy).slice(0,t);return{totalFiles:e.length,topEntropy:i,averageEntropy:s,lastScanDurationMs:this.lastScanDurationMs,lastScanAt:this.lastScanAt}}dispose(){if(this.disposed=!0,this.scanTimer)clearInterval(this.scanTimer),this.scanTimer=null;this.send({type:"stop"}),this.worker?.terminate(),this.worker=null,this.onDidUpdateRecordsEmitter.dispose(),this.onDidUpdateGraphEmitter.dispose(),this.onDidUpdateSnapshotEmitter.dispose()}scheduleScanLoop(t){if(this.scanTimer)clearInterval(this.scanTimer);let e=Math.max(5000,t);this.scanTimer=setInterval(()=>{if(!this.disposed)this.rescanNow()},e)}ensureWorker(){if(this.worker)return;this.worker=new Ut.Worker(this.workerPath),this.worker.on("message",(t)=>this.handleWorkerEvent(t)),this.worker.on("error",(t)=>{this.output.appendLine(`[entropy] worker error: ${t.message}`)}),this.worker.on("exit",(t)=>{if(this.output.appendLine(`[entropy] worker exited with code ${t}`),this.worker=null,!this.disposed&&t!==0)this.ensureWorker(),this.rescanNow()})}send(t){this.ensureWorker(),this.worker?.postMessage(t)}handleWorkerEvent(t){switch(t.type){case"scan-progress":{if(!this.rootPath)return;let e=[];for(let s of t.records){this.records.set(s.path,s);let i=this.recordUris.get(s.path);if(!i)i=_.Uri.file(H.join(this.rootPath,s.path)),this.recordUris.set(s.path,i);e.push(i)}if(e.length>0)this.onDidUpdateRecordsEmitter.fire(e);break}case"scan-complete":this.lastScanDurationMs=t.durationMs,this.lastScanAt=Date.now(),this.onDidUpdateSnapshotEmitter.fire(this.getSnapshot());break;case"graph-result":this.onDidUpdateGraphEmitter.fire(t.graph);break;case"error":this.output.appendLine(`[entropy] ${t.message}${t.detail?`
${t.detail}`:""}`);break}}}function He(t){return t.replace(/\\/g,"/")}var Nt=d(require("vscode"));class pt{workerClient;debounceMs;maxPerFlush;tooltipAugmentProvider;onDidChangeEmitter=new Nt.EventEmitter;onDidChangeFileDecorations=this.onDidChangeEmitter.event;pending=new Map;flushTimer=null;constructor(t,e,s,i){this.workerClient=t;this.debounceMs=e;this.maxPerFlush=s;this.tooltipAugmentProvider=i;this.workerClient.onDidUpdateRecords((o)=>this.enqueueUpdates(o))}dispose(){if(this.flushTimer)clearTimeout(this.flushTimer),this.flushTimer=null;this.onDidChangeEmitter.dispose()}updateConfig(t,e){this.debounceMs=Math.max(30,t),this.maxPerFlush=Math.max(64,e)}provideFileDecoration(t){if(t.scheme!=="file")return;let e=this.workerClient.getRecord(t);if(!e)return;let s=qe(e),i=[`Entropy ${(e.entropy*100).toFixed(0)}%`,`Complexity ${e.complexity}`,`Debt ${e.debt}`,`Freshness ${(e.freshness*100).toFixed(0)}%`];if(this.tooltipAugmentProvider)i.push(...this.tooltipAugmentProvider(t));return{color:s,tooltip:i.join(`
`),propagate:!1}}enqueueExternalUpdates(t){this.enqueueUpdates(t)}enqueueUpdates(t){for(let e of t)this.pending.set(e.toString(),e);if(!this.flushTimer)this.flushTimer=setTimeout(()=>this.flush(),this.debounceMs)}flush(){if(this.flushTimer=null,this.pending.size===0)return;let t=Array.from(this.pending.values()).slice(0,this.maxPerFlush);for(let e of t)this.pending.delete(e.toString());if(this.onDidChangeEmitter.fire(t),this.pending.size>0)this.flushTimer=setTimeout(()=>this.flush(),this.debounceMs)}}function qe(t){let e=Ue(t.entropy*0.78+(1-t.freshness)*0.22),s=lt(118,24,e),i=lt(36,46,e),o=lt(58,42,e);return Fe(s,i,o)}function Fe(t,e,s){let i=t/360,o=e/100,n=s/100,a=(m,k,st)=>{let x=st;if(x<0)x+=1;if(x>1)x-=1;if(x<0.16666666666666666)return m+(k-m)*6*x;if(x<0.5)return k;if(x<0.6666666666666666)return m+(k-m)*(0.6666666666666666-x)*6;return m},l,h,P;if(o===0)l=n,h=n,P=n;else{let m=n<0.5?n*(1+o):n+o-n*o,k=2*n-m;l=a(k,m,i+0.3333333333333333),h=a(k,m,i),P=a(k,m,i-0.3333333333333333)}let p=(m)=>{return Math.round(m*255).toString(16).padStart(2,"0")};return`#${p(l)}${p(h)}${p(P)}`}function Ue(t){if(t<0)return 0;if(t>1)return 1;return t}function lt(t,e,s){return t+(e-t)*s}var V=d(require("path")),v=d(require("vscode"));class W{extensionUri;workerClient;static viewType="chthonic.abyssalView";disposables=[];view=null;rootPath=null;sedimentRequestCallback=null;constructor(t,e){this.extensionUri=t;this.workerClient=e;this.disposables.push(this.workerClient.onDidUpdateGraph((s)=>this.postMessage({type:"graph",graph:s})),this.workerClient.onDidUpdateSnapshot((s)=>this.postMessage({type:"snapshot",snapshot:s})))}setRootPath(t){this.rootPath=t}onRequestSediment(t){this.sedimentRequestCallback=t}postSedimentData(t){this.postMessage({type:"sediment",sediment:t})}postSedimentChunk(t){this.postMessage({type:"sedimentChunk",chunk:t})}postSedimentBinary(t){let e=t.buffer.slice(t.byteOffset,t.byteOffset+t.byteLength);this.postMessage({type:"sedimentBinary",payload:e})}dispose(){this.disposables.forEach((t)=>t.dispose()),this.disposables.length=0}resolveWebviewView(t,e,s){this.view=t,t.webview.options={enableScripts:!0,localResourceRoots:[this.extensionUri]},t.webview.html=this.getHtml(t.webview),t.webview.onDidReceiveMessage((i)=>{this.handleMessage(i)})}handleMessage(t){if(!t||typeof t!=="object")return;let e=t;if(!e.type)return;if(e.type==="ready"){this.postMessage({type:"snapshot",snapshot:this.workerClient.getSnapshot()}),this.workerClient.requestGraph(260);return}if(e.type==="requestGraph"){this.workerClient.requestGraph(260);return}if(e.type==="requestSediment"){this.sedimentRequestCallback?.();return}if(e.type==="openFile"&&e.path&&this.rootPath){let s=V.normalize(e.path);if(s.startsWith("..")||V.isAbsolute(s))return;let i=V.join(this.rootPath,s),o=v.Uri.file(i);v.workspace.openTextDocument(o).then((n)=>{v.window.showTextDocument(n,{preview:!1})},()=>{v.window.showWarningMessage(`Unable to open ${e.path}`)})}}postMessage(t){if(!this.view)return;this.view.webview.postMessage(t)}getHtml(t){let e=Ne(),s=t.asWebviewUri(v.Uri.joinPath(this.extensionUri,"media","abyssalPane.js")),i=t.asWebviewUri(v.Uri.joinPath(this.extensionUri,"media","wasm","pkg","entropy_renderer_wasm.js")),o=t.asWebviewUri(v.Uri.joinPath(this.extensionUri,"media","wasm","pkg","entropy_renderer_wasm_bg.wasm")),n=t.asWebviewUri(v.Uri.joinPath(this.extensionUri,"media","wasm","pkg","chthonic_loom.js")),a=t.asWebviewUri(v.Uri.joinPath(this.extensionUri,"media","wasm","pkg","chthonic_loom_bg.wasm")),l=["default-src 'none'",`img-src ${t.cspSource} data:`,`style-src ${t.cspSource} 'unsafe-inline'`,`script-src 'nonce-${e}' ${t.cspSource}`,`connect-src ${t.cspSource}`].join("; "),h=JSON.stringify({wasmModuleUri:i.toString(),wasmBinaryUri:o.toString(),loomWasmModuleUri:n.toString(),loomWasmBinaryUri:a.toString()});return`<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="${l}">
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
        <p class="subtitle">Rust/WASM bridge to Loom + WebGPU, canvas fallback when binaries are absent.</p>
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
        window.__CHTHONIC_ABYSSAL__ = ${h};
    </script>
    <script nonce="${e}" type="module" src="${s}"></script>
</body>
</html>`}}function Ne(){let e="";for(let s=0;s<32;s+=1)e+="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789".charAt(Math.floor(Math.random()*62));return e}var vt=d(require("fs/promises")),E=d(require("path")),bt=d(require("vscode"));var Jt=d(require("crypto"));class ut{leaves=new Map;dirty=!1;upsert(t){let e=Qe(t.path),s=Je(e,t);if(this.leaves.get(e)!==s)this.leaves.set(e,s),this.dirty=!0}hasDirty(){return this.dirty}settle(t){if(!this.dirty||this.leaves.size===0)return null;let e=ze(Array.from(this.leaves.entries()).sort((s,i)=>s[0].localeCompare(i[0])));return this.dirty=!1,{reason:t,rootHash:e,leafCount:this.leaves.size,generatedAt:Date.now()}}}function Je(t,e){let s=[t,e.entropy.toFixed(6),e.complexity,e.debt,e.freshness.toFixed(6),e.ruffViolations,e.updatedAt].join("|");return G(s)}function ze(t){if(t.length===0)return G("EMPTY");let e=t.map(([s,i])=>G(`${s}:${i}`));while(e.length>1){let s=[];for(let i=0;i<e.length;i+=2){let o=e[i],n=e[i+1]??e[i];s.push(G(`${o}${n}`))}e=s}return e[0]}function G(t){return Jt.createHash("sha256").update(t,"utf8").digest("hex")}function Qe(t){return t.replace(/\\/g,"/")}var K=d(require("path")),ht=require("child_process"),Y=d(require("vscode"));function B(t,e){let s="",i=(o)=>{let n=o.trim();if(!n)return;try{let a=JSON.parse(n);if(!a||typeof a!=="object"||Array.isArray(a))throw Error("JSONL payload must be an object");t(a)}catch(a){e(a instanceof Error?a:Error(String(a)))}};return{push(o){s+=o.toString();while(!0){let n=s.indexOf(`
`);if(n<0)return;let a=s.slice(0,n);s=s.slice(n+1),i(a)}},flush(){if(!s.trim()){s="";return}i(s),s=""}}}class mt{output;rootPath=null;pythonSidecar=null;rubySidecar=null;onDidReceiveRuffEmitter=new Y.EventEmitter;onDidReceiveRuff=this.onDidReceiveRuffEmitter.event;onDidReceiveLoreEmitter=new Y.EventEmitter;onDidReceiveLore=this.onDidReceiveLoreEmitter.event;onDidReceiveSidecarErrorEmitter=new Y.EventEmitter;onDidReceiveSidecarError=this.onDidReceiveSidecarErrorEmitter.event;constructor(t){this.output=t}start(t){this.rootPath=t,this.startPythonSidecar(),this.startRubySidecar()}requestScan(t){if(!this.pythonSidecar||this.pythonSidecar.killed)this.startPythonSidecar();this.writeJson(this.pythonSidecar,t)}requestLore(t){if(!this.rubySidecar||this.rubySidecar.killed)this.startRubySidecar();this.writeJson(this.rubySidecar,t)}dispose(){this.pythonSidecar?.kill(),this.rubySidecar?.kill(),this.pythonSidecar=null,this.rubySidecar=null,this.onDidReceiveRuffEmitter.dispose(),this.onDidReceiveLoreEmitter.dispose(),this.onDidReceiveSidecarErrorEmitter.dispose()}startPythonSidecar(){if(!this.rootPath||this.pythonSidecar)return;let t=K.join(this.rootPath,".chthonic","python","entropy_scan.py"),e=K.join(this.rootPath,".chthonic","venv",process.platform==="win32"?"Scripts/python.exe":"bin/python");this.pythonSidecar=ht.spawn("uv",["run","--python",e,t,"--stdio"],{cwd:this.rootPath,stdio:["pipe","pipe","pipe"]});let s=B((i)=>this.handlePythonPayload(i),(i)=>this.output.appendLine(`[polyglot:python] invalid JSONL payload: ${i.message}`));this.pythonSidecar.stdout?.on("data",(i)=>s.push(i)),this.pythonSidecar.stderr?.on("data",(i)=>{this.output.appendLine(`[polyglot:python] ${i.toString().trimEnd()}`)}),this.pythonSidecar.on("error",(i)=>{this.onDidReceiveSidecarErrorEmitter.fire({type:"error",source:"python",message:i.message}),this.output.appendLine(`[polyglot:python] failed to spawn: ${i.message}`),this.pythonSidecar=null}),this.pythonSidecar.on("exit",(i)=>{s.flush(),this.output.appendLine(`[polyglot:python] exited with code ${i??-1}`),this.pythonSidecar=null})}startRubySidecar(){if(!this.rootPath||this.rubySidecar)return;let t=K.join(this.rootPath,".chthonic","ruby","lore.rb");this.rubySidecar=ht.spawn("ruby",[t],{cwd:this.rootPath,stdio:["pipe","pipe","pipe"]});let e=B((s)=>this.handleRubyPayload(s),(s)=>this.output.appendLine(`[polyglot:ruby] invalid JSONL payload: ${s.message}`));this.rubySidecar.stdout?.on("data",(s)=>e.push(s)),this.rubySidecar.stderr?.on("data",(s)=>{this.output.appendLine(`[polyglot:ruby] ${s.toString().trimEnd()}`)}),this.rubySidecar.on("error",(s)=>{this.onDidReceiveSidecarErrorEmitter.fire({type:"error",source:"ruby",message:s.message}),this.output.appendLine(`[polyglot:ruby] failed to spawn: ${s.message}`),this.rubySidecar=null}),this.rubySidecar.on("exit",(s)=>{e.flush(),this.output.appendLine(`[polyglot:ruby] exited with code ${s??-1}`),this.rubySidecar=null})}writeJson(t,e){if(!t?.stdin||t.killed)return;try{t.stdin.write(`${JSON.stringify(e)}
`)}catch(s){this.output.appendLine(`[polyglot] sidecar write failed: ${We(s)}`)}}handlePythonPayload(t){if(t.type==="ruff-summary"){let e=t;this.onDidReceiveRuffEmitter.fire(e);return}if(t.type==="error"){let e=String(t.message??"python sidecar error");this.output.appendLine(`[polyglot:python] ${e}`),this.onDidReceiveSidecarErrorEmitter.fire({type:"error",source:"python",message:e})}}handleRubyPayload(t){if(t.type==="lore"){this.onDidReceiveLoreEmitter.fire(t);return}if(t.type==="error"){let e=String(t.message??"ruby sidecar error");this.output.appendLine(`[polyglot:ruby] ${e}`),this.onDidReceiveSidecarErrorEmitter.fire({type:"error",source:"ruby",message:e})}}}function We(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}var zt=d(require("fs")),X=d(require("fs/promises")),R=d(require("path")),ft=require("child_process");class gt{output;rootPath=null;options={rpcUrl:"http://127.0.0.1:8899",autostartValidator:!1};ledgerFilePath=null;validatorProcess=null;hostProcess=null;requestCounter=1;pending=new Map;constructor(t){this.output=t}async start(t,e){this.rootPath=t,this.options=e;let s=R.join(t,".chthonic","ledger");if(await X.mkdir(s,{recursive:!0}),this.ledgerFilePath=R.join(s,"entropy-settlements.jsonl"),e.autostartValidator)this.startValidator();this.startHostProcess()}async commitEntropy(t){if(!this.rootPath||!this.ledgerFilePath)return{mode:"offline",detail:"Ledger host not started"};let e={...t,rpcUrl:this.options.rpcUrl,recordedAt:Date.now()},s={mode:"offline",detail:"Rust ledger host unavailable; persisted settlement locally."};try{s=await this.submitToHost(t)}catch(i){this.output.appendLine(`[ledger-rust] submit failed: ${Xe(i)}`)}return await X.appendFile(this.ledgerFilePath,`${JSON.stringify({...e,receipt:s})}
`,"utf8"),s}dispose(){for(let[t,e]of this.pending)e.reject(Error(`request ${t} cancelled`));this.pending.clear(),this.hostProcess?.kill(),this.hostProcess=null,this.validatorProcess?.kill(),this.validatorProcess=null}startHostProcess(){if(!this.rootPath||this.hostProcess)return;let t=Ge(this.rootPath,this.options.hostBinaryPath),e=this.options.walletPath??R.join(this.rootPath,".chthonic","wallets","payer.json"),s=this.options.idlPath??R.join(this.rootPath,".chthonic","wallets","entropy_ledger.json");this.hostProcess=ft.spawn(t,["--wallet",e,"--idl",s,"--rpc-url",this.options.rpcUrl],{cwd:this.rootPath,stdio:["pipe","pipe","pipe"]});let i=B((o)=>this.handleHostPayload(o),(o)=>this.output.appendLine(`[ledger-rust] invalid JSON payload: ${o.message}`));this.hostProcess.stdout?.on("data",(o)=>i.push(o)),this.hostProcess.stderr?.on("data",(o)=>{this.output.appendLine(`[ledger-rust] ${o.toString().trimEnd()}`)}),this.hostProcess.on("error",(o)=>{this.output.appendLine(`[ledger-rust] failed to spawn host: ${o.message}`),this.rejectAllPending(Error(`host spawn failed: ${o.message}`)),this.hostProcess=null}),this.hostProcess.on("exit",(o)=>{i.flush(),this.output.appendLine(`[ledger-rust] host exited with code ${o??-1}`),this.rejectAllPending(Error("ledger host exited")),this.hostProcess=null})}async submitToHost(t){if(!this.hostProcess||this.hostProcess.killed)this.startHostProcess();if(!this.hostProcess?.stdin||this.hostProcess.killed)return{mode:"offline",detail:"Rust host binary is missing or not executable."};let e=this.requestCounter++,s={jsonrpc:"2.0",id:e,method:"submit_entropy",params:{entropy_score:Math.max(0,Math.round(t.leafCount*17+13)),merkle_root:t.rootHash,leaf_count:t.leafCount,reason:t.reason}};return await new Promise((o,n)=>{this.pending.set(e,{resolve:o,reject:n}),this.hostProcess?.stdin?.write(`${JSON.stringify(s)}
`,(a)=>{if(!a)return;this.pending.delete(e),n(a)})})}handleHostPayload(t){let e=t.id;if(typeof e!=="number")return;let s=this.pending.get(e);if(!s)return;if(this.pending.delete(e),t.error&&typeof t.error==="object"){let o=t;s.resolve({mode:"offline",detail:`Rust ledger error ${o.error.code}: ${o.error.message}`});return}let i=t;s.resolve({mode:"validator-rust",txSignature:i.result.signature,detail:`Rust anchor-client submission accepted${i.result.slot?` (slot ${i.result.slot})`:""}.`})}rejectAllPending(t){for(let[e,s]of this.pending)this.pending.delete(e),s.reject(t)}startValidator(){if(!this.rootPath||this.validatorProcess)return;let t=Ke(this.rootPath),e=Ye(this.options.rpcUrl)??8899,s=R.join(this.rootPath,".chthonic","solana-ledger");this.validatorProcess=ft.spawn(t,["--ledger",s,"--rpc-port",String(e),"--reset","--quiet"],{cwd:this.rootPath,stdio:["ignore","pipe","pipe"]}),this.validatorProcess.stdout?.on("data",(i)=>{this.output.appendLine(`[solana] ${i.toString().trimEnd()}`)}),this.validatorProcess.stderr?.on("data",(i)=>{this.output.appendLine(`[solana] ${i.toString().trimEnd()}`)}),this.validatorProcess.on("error",(i)=>{this.output.appendLine(`[solana] validator spawn error: ${i.message}`),this.validatorProcess=null}),this.validatorProcess.on("exit",(i)=>{this.output.appendLine(`[solana] validator exited with code ${i??-1}`),this.validatorProcess=null})}}function Ge(t,e){if(e)return e;let s=process.platform==="win32"?"entropy-ledger-host.exe":"entropy-ledger-host";return R.join(t,"native","target","release",s)}function Ke(t){let e=process.platform==="win32"?"solana-test-validator.exe":"solana-test-validator",s=R.join(t,".chthonic","bin",e);if(zt.existsSync(s))return s;return process.platform==="win32"?"solana-test-validator":e}function Ye(t){try{let e=new URL(t);if(!e.port)return null;let s=Number(e.port);return Number.isFinite(s)?s:null}catch{return null}}function Xe(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}class yt{output;options;backend=null;constructor(t,e){this.output=t;this.options=e}async start(t){this.backend=this.options.mode==="bankrun"?new Qt(this.output):new Wt(this.output,this.options),await this.backend.start(t)}async commitEntropy(t){if(!this.backend)return{mode:"offline",detail:"LedgerBroker backend not initialized."};return this.backend.commitEntropy(t)}dispose(){this.backend?.dispose(),this.backend=null}}class Qt{output;sequence=0;constructor(t){this.output=t}async start(t){this.output.appendLine("[ledger] phantom mode active (bankrun simulation).")}async commitEntropy(t){return this.sequence+=1,{mode:"bankrun",txSignature:`bankrun-${t.rootHash.slice(0,20)}-${this.sequence}`,detail:"In-memory bankrun simulation accepted the entropy settlement."}}dispose(){}}class Wt{options;client;constructor(t,e){this.options=e;this.client=new gt(t)}async start(t){await this.client.start(t,{rpcUrl:this.options.rpcUrl,autostartValidator:this.options.autostartValidator,hostBinaryPath:this.options.hostBinaryPath,walletPath:this.options.walletPath,idlPath:this.options.idlPath})}async commitEntropy(t){return this.client.commitEntropy(t)}dispose(){this.client.dispose()}}class xt{output;workerClient;options;requestDecorationRefresh;broker;merkle=new ut;ledger;tooltipAugments=new Map;rootPath=null;scanTimer=null;settleTimer=null;gitPollTimer=null;gitHeadSnapshot=null;pendingSettleReason=null;disposables=[];constructor(t,e,s,i){this.output=t;this.workerClient=e;this.options=s;this.requestDecorationRefresh=i;this.broker=new mt(t),this.ledger=new yt(t,{mode:this.options.ledgerMode,rpcUrl:this.options.solanaRpcUrl,autostartValidator:this.options.solanaAutostartValidator,hostBinaryPath:this.options.solanaLedgerHostBinaryPath,walletPath:this.options.solanaWalletPath,idlPath:this.options.solanaIdlPath}),this.disposables.push(this.broker.onDidReceiveRuff((o)=>this.applyRuffSummary(o.files)),this.broker.onDidReceiveLore((o)=>this.applyLore(o)),this.workerClient.onDidUpdateRecords((o)=>this.captureEntropyLeaves(o)))}async start(t){if(this.rootPath=t,!this.options.enabled)return;this.broker.start(t),await this.ledger.start(t),this.broker.requestScan({type:"scan",reason:"manual",root:t}),this.startScanLoop(),this.startGitWatcher()}onDidSaveDocument(t){if(!this.rootPath||!this.options.enabled||t.uri.scheme!=="file")return;let e=Gt(this.rootPath,t.uri.fsPath);if(!e)return;this.broker.requestScan({type:"scan",reason:"save",root:this.rootPath,files:[e]}),this.scheduleSettlement("save")}requestManualScan(){if(!this.rootPath||!this.options.enabled)return;this.broker.requestScan({type:"scan",reason:"manual",root:this.rootPath})}getTooltipFragments(t){if(!this.rootPath||t.scheme!=="file")return[];let e=Gt(this.rootPath,t.fsPath);if(!e)return[];let s=this.tooltipAugments.get(e);if(!s)return[];let i=[];if(s.ruffViolations>0)i.push(`Ruff ${s.ruffViolations} violation${s.ruffViolations===1?"":"s"}`);if(s.loreLine)i.push(s.loreLine);return i}dispose(){if(this.scanTimer)clearInterval(this.scanTimer),this.scanTimer=null;if(this.settleTimer)clearTimeout(this.settleTimer),this.settleTimer=null;if(this.gitPollTimer)clearInterval(this.gitPollTimer),this.gitPollTimer=null;this.broker.dispose(),this.ledger.dispose(),this.disposables.forEach((t)=>t.dispose()),this.disposables.length=0}captureEntropyLeaves(t){if(!this.options.enabled)return;for(let e of t){let s=this.workerClient.getRecord(e);if(!s)continue;let i=this.tooltipAugments.get(s.path);this.merkle.upsert({path:s.path,entropy:s.entropy,complexity:s.complexity,debt:s.debt,freshness:s.freshness,ruffViolations:i?.ruffViolations??0,updatedAt:Date.now()})}}applyRuffSummary(t){if(!this.rootPath||!this.options.enabled)return;let e=[];for(let s of t){let i=this.tooltipAugments.get(s.path),o={ruffViolations:s.violations,loreLine:i?.loreLine};this.tooltipAugments.set(s.path,o);let n=bt.Uri.file(E.join(this.rootPath,s.path));e.push(n);let a=this.workerClient.getRecord(n);if(a){if(this.merkle.upsert({path:a.path,entropy:a.entropy,complexity:a.complexity,debt:a.debt,freshness:a.freshness,ruffViolations:s.violations,updatedAt:Date.now()}),a.entropy>=0.45||s.violations>0)this.broker.requestLore({type:"lore-request",root:this.rootPath,path:s.path,entropy:a.entropy,violations:s.violations})}}if(e.length>0)this.requestDecorationRefresh(e)}applyLore(t){if(!this.rootPath||!this.options.enabled)return;if(t.root!==this.rootPath)return;let e=this.tooltipAugments.get(t.path);this.tooltipAugments.set(t.path,{ruffViolations:e?.ruffViolations??t.violations,loreLine:t.line}),this.requestDecorationRefresh([bt.Uri.file(E.join(this.rootPath,t.path))])}startScanLoop(){if(this.scanTimer||!this.rootPath)return;let t=Math.max(this.options.pythonScanIntervalMs,1e4);this.scanTimer=setInterval(()=>{if(!this.rootPath)return;this.broker.requestScan({type:"scan",reason:"interval",root:this.rootPath})},t)}startGitWatcher(){if(!this.rootPath||this.gitPollTimer)return;this.gitHeadSnapshot=null,this.gitPollTimer=setInterval(async()=>{if(!this.rootPath)return;let t=await Ze(this.rootPath);if(!t)return;if(!this.gitHeadSnapshot){this.gitHeadSnapshot=t;return}if(t!==this.gitHeadSnapshot){if(this.gitHeadSnapshot=t,this.output.appendLine("[polyglot] git HEAD changed, scheduling Merkle settlement."),this.rootPath)this.broker.requestScan({type:"scan",reason:"commit",root:this.rootPath});this.scheduleSettlement("commit")}},6000)}scheduleSettlement(t){if(!this.options.enabled)return;if(this.pendingSettleReason=t==="commit"?"commit":this.pendingSettleReason??t,this.settleTimer)clearTimeout(this.settleTimer);this.settleTimer=setTimeout(()=>{this.settleTimer=null,this.flushSettlement()},Math.max(this.options.settleDebounceMs,300))}async flushSettlement(){let t=this.pendingSettleReason??"manual";this.pendingSettleReason=null;let e=this.merkle.settle(t);if(!e)return;let s=await this.ledger.commitEntropy(e),i=[`[polyglot] settled Merkle root ${e.rootHash.slice(0,16)}...`,`leaves=${e.leafCount}`,`mode=${s.mode}`];if(s.txSignature)i.push(`tx=${s.txSignature}`);i.push(`detail=${s.detail}`),this.output.appendLine(i.join(" "))}}async function Ze(t){let e=E.join(t,".git"),s=E.join(e,"HEAD"),i="";try{i=await vt.readFile(s,"utf8")}catch{return null}let o=i.trim();if(!o)return null;if(!o.startsWith("ref:"))return o;let n=o.slice(4).trim(),a=E.join(e,n);try{let l=await vt.readFile(a,"utf8");return`ref:${n}:${l.trim()}`}catch{return`ref:${n}:missing`}}function Gt(t,e){let s=E.relative(t,e);if(!s||s.startsWith("..")||E.isAbsolute(s))return null;return s.replace(/\\/g,"/")}var Kt=d(require("path")),Yt=require("child_process"),M=d(require("vscode"));class wt{output;headlessVulkan;daemonBinaryOverride;eolApiBase;entropyMonitorIntervalMs;rootPath=null;daemonProcess=null;requestCounter=1;pending=new Map;onDidReceiveManifestEmitter=new M.EventEmitter;onDidReceiveManifest=this.onDidReceiveManifestEmitter.event;onDidReceiveEnvEmitter=new M.EventEmitter;onDidReceiveEnv=this.onDidReceiveEnvEmitter.event;onDidReceiveSedimentEmitter=new M.EventEmitter;onDidReceiveSediment=this.onDidReceiveSedimentEmitter.event;onDidReceiveSedimentChunkEmitter=new M.EventEmitter;onDidReceiveSedimentChunk=this.onDidReceiveSedimentChunkEmitter.event;onDidReceiveSynapseEmitter=new M.EventEmitter;onDidReceiveSynapse=this.onDidReceiveSynapseEmitter.event;onDidReceiveEntropyStateEmitter=new M.EventEmitter;onDidReceiveEntropyState=this.onDidReceiveEntropyStateEmitter.event;onDidReceiveFiredancerSurgeEmitter=new M.EventEmitter;onDidReceiveFiredancerSurge=this.onDidReceiveFiredancerSurgeEmitter.event;constructor(t,e,s,i="https://endoflife.date/api/v1",o=21600000){this.output=t;this.headlessVulkan=e;this.daemonBinaryOverride=s;this.eolApiBase=i;this.entropyMonitorIntervalMs=o}start(t){this.rootPath=t,this.startDaemon()}async requestSediment(t,e){return this.submitRequest("reactor/sediment",{max_layers:t,max_files:e})}async requestSedimentStream(t,e,s=220){return this.submitRequest("reactor/sediment_stream",{max_layers:t,max_files:e,chunk_size:s})}async requestSedimentSynapse(t,e,s=220){return this.submitRequest("reactor/sediment_synapse",{max_layers:t,max_files:e,chunk_size:s})}async requestDetect(){return this.submitRequest("anno/detect",{})}async requestProvision(){return this.submitRequest("anno/provision",{})}async requestEntropyState(){return this.submitRequest("reactor/entropy_state",{})}dispose(){for(let[,t]of this.pending)t.reject(Error("AnnoClient disposed"));this.pending.clear(),this.daemonProcess?.kill(),this.daemonProcess=null,this.onDidReceiveManifestEmitter.dispose(),this.onDidReceiveEnvEmitter.dispose(),this.onDidReceiveSedimentEmitter.dispose(),this.onDidReceiveSedimentChunkEmitter.dispose(),this.onDidReceiveSynapseEmitter.dispose(),this.onDidReceiveEntropyStateEmitter.dispose(),this.onDidReceiveFiredancerSurgeEmitter.dispose()}startDaemon(){if(!this.rootPath||this.daemonProcess)return;let t=this.daemonBinaryOverride??ts(this.rootPath),e=["--workspace",this.rootPath];if(this.headlessVulkan)e.push("--headless-vulkan");this.daemonProcess=Yt.spawn(t,e,{cwd:this.rootPath,env:{...process.env,CHTHONIC_EOL_API_BASE:this.eolApiBase,CHTHONIC_ENTROPY_MONITOR_INTERVAL_MS:String(Math.max(60000,this.entropyMonitorIntervalMs))},stdio:["pipe","pipe","pipe"]});let s=B((i)=>this.handlePayload(i),(i)=>this.output.appendLine(`[daemon] invalid JSONL: ${i.message}`));this.daemonProcess.stdout?.on("data",(i)=>s.push(i)),this.daemonProcess.stderr?.on("data",(i)=>{this.output.appendLine(`[daemon] ${i.toString().trimEnd()}`)}),this.daemonProcess.on("error",(i)=>{this.output.appendLine(`[daemon] spawn failed: ${i.message}`),this.rejectAllPending(Error(`daemon spawn failed: ${i.message}`)),this.daemonProcess=null}),this.daemonProcess.on("exit",(i)=>{s.flush(),this.output.appendLine(`[daemon] exited with code ${i??-1}`),this.rejectAllPending(Error("daemon exited")),this.daemonProcess=null})}handlePayload(t){if("method"in t&&!("id"in t)){this.handleNotification(t);return}if("id"in t&&typeof t.id==="number")this.handleResponse(t)}handleNotification(t){let{method:e,params:s}=t;switch(e){case"anno/manifest":this.onDidReceiveManifestEmitter.fire(s),this.output.appendLine(`[daemon] ANNO manifest received (${s.languages?.length??0} languages)`);break;case"anno/env":this.onDidReceiveEnvEmitter.fire(s),this.output.appendLine("[daemon] env report received");break;case"reactor/status":{let i=s.status??"unknown";this.output.appendLine(`[daemon] reactor status: ${i}`);break}case"reactor/sedimentChunk":this.onDidReceiveSedimentChunkEmitter.fire(s);break;case"reactor/synapse":this.onDidReceiveSynapseEmitter.fire(s),this.output.appendLine(`[daemon] synapse status: ${s.status} (${s.mode})`);break;case"reactor/entropyState":this.onDidReceiveEntropyStateEmitter.fire(s),this.output.appendLine(`[daemon] entropy state: ${s.status} (${Math.round((s.decay_score??0)*100)}%)`);break;case"reactor/firedancerSurge":this.onDidReceiveFiredancerSurgeEmitter.fire(s),this.output.appendLine(`[daemon] firedancer slot ${s.slot} tps ${s.simulated_tps} (${s.surge?"surge":"flow"})`);break;default:this.output.appendLine(`[daemon] unknown notification: ${e}`)}}handleResponse(t){let e=t.id,s=this.pending.get(e);if(!s)return;if(this.pending.delete(e),t.error&&typeof t.error==="object"){let i=t.error;s.reject(Error(i.message));return}s.resolve(t.result)}submitRequest(t,e){if(!this.daemonProcess?.stdin||this.daemonProcess.killed)this.startDaemon();if(!this.daemonProcess?.stdin)return Promise.reject(Error("daemon not available"));let s=this.requestCounter++,i={jsonrpc:"2.0",id:s,method:t,params:e};return new Promise((o,n)=>{this.pending.set(s,{resolve:o,reject:n}),this.daemonProcess?.stdin?.write(`${JSON.stringify(i)}
`,(a)=>{if(a)this.pending.delete(s),n(a)})})}rejectAllPending(t){for(let[e,s]of this.pending)this.pending.delete(e),s.reject(t)}}function ts(t){let e=process.platform==="win32"?"chthonic-daemon.exe":"chthonic-daemon";return Kt.join(t,"native","target","release",e)}var $=d(require("vscode"));class kt{output;envCollection;disposed=!1;constructor(t,e){this.output=t;this.envCollection=e}async activate(){if(this.disposed)return;try{await $.commands.executeCommand("workbench.action.closeSidebar"),await $.commands.executeCommand("workbench.action.terminal.moveToSidePanel"),await $.commands.executeCommand("workbench.action.toggleAuxiliaryBar"),await $.commands.executeCommand("workbench.action.toggleMaximizedPanel"),await $.commands.executeCommand("workbench.action.focusActiveEditorGroup"),this.output.appendLine("[cockpit] layout activated: sidebar=closed, terminal=AuxBar, panel=maximized, editor=Center")}catch(t){this.output.appendLine(`[cockpit] layout activation failed: ${es(t)}`)}}applyTerminalEnv(t){if(this.disposed)return;if(!t.path_mutations.length&&!t.dev_kit)return;let e=t.path_mutations.sort((o,n)=>o.priority-n.priority).map((o)=>o.path),s=process.platform==="win32"?";":":";for(let o of e)this.envCollection.prepend("PATH",`${o}${s}`);if(t.dev_kit){for(let[o,n]of t.dev_kit.env_vars)this.envCollection.replace(o,n);for(let o of t.dev_kit.path_prepend)this.envCollection.prepend("PATH",`${o}${s}`)}for(let o of $.window.terminals)if(process.platform==="win32"){for(let n of e)o.sendText(`$env:PATH = "${n};$env:PATH"`,!0);if(t.dev_kit)for(let[n,a]of t.dev_kit.env_vars)o.sendText(`$env:${n} = "${a}"`,!0)}else{for(let n of e)o.sendText(`export PATH="${n}:$PATH"`,!0);if(t.dev_kit)for(let[n,a]of t.dev_kit.env_vars)o.sendText(`export ${n}="${a}"`,!0)}let i=e.length+(t.dev_kit?.env_vars.length??0);if(this.output.appendLine(`[cockpit] terminal env updated: ${i} mutations applied`),t.warnings.length>0)for(let o of t.warnings)this.output.appendLine(`[cockpit] warning: ${o}`)}dispose(){this.disposed=!0}}function es(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}var Zt=d(require("fs")),St=d(require("path"));class SynapseBridge{output;extensionRoot;binding=null;reader=null;descriptor=null;transportMode;constructor(t,e,s){this.output=t;this.extensionRoot=e;this.transportMode=ss(s)}updateDescriptor(t){if(this.descriptor=t,this.transportMode==="jsonl"){this.output.appendLine("[synapse] disabled by transport=jsonl");return}if(t.status!=="ready"||t.mode!=="shared_memory"||!t.shm_id){this.output.appendLine(`[synapse] unavailable: ${t.reason??t.status}`);return}try{let e=this.ensureBindingLoaded();this.reader=new e.SynapseReader(t.shm_id,t.event_name??void 0),this.output.appendLine(`[synapse] connected (shm=${t.shm_id})`)}catch(e){this.reader=null,this.output.appendLine(`[synapse] init failed, falling back to JSONL: ${is(e)}`)}}isReady(){if(this.transportMode==="jsonl")return!1;return this.reader!==null&&this.descriptor?.status==="ready"&&this.descriptor.mode==="shared_memory"}async drain(t,e){if(!this.reader||t.transport!=="shared_memory")return 0;let s=Math.max(0,t.chunks_written??t.total_chunks??0);if(s===0)return 0;let i=0,o=Date.now();while(i<s&&Date.now()-o<4000){if(!this.reader.wait_for_signal(120)){await Xt();continue}while(!0){let a=this.reader.read_chunk();if(!a||a.byteLength===0)break;let l=new Uint8Array(a.buffer,a.byteOffset,a.byteLength),h=new Uint8Array(l.byteLength);if(h.set(l),e(h),i+=1,i>=s)break}await Xt()}if(i<s)this.output.appendLine(`[synapse] partial drain: ${i}/${s}`);return i}dispose(){this.reader=null}ensureBindingLoaded(){if(this.binding)return this.binding;let candidates=[St.join(this.extensionRoot,"src","reactor","synapse.node"),St.join(this.extensionRoot,"native","target","release","synapse.node")],existing=candidates.find((t)=>Zt.existsSync(t));if(!existing)throw Error(`synapse.node not found in ${candidates.join(", ")}`);let req=eval("require");return this.binding=req(existing),this.binding}}function ss(t){let e=t.trim().toLowerCase();if(e==="shared_memory")return"shared_memory";if(e==="jsonl")return"jsonl";return"auto"}function is(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}async function Xt(){await new Promise((t)=>setTimeout(t,0))}var b=d(require("vscode"));var te=d(require("fs")),ee=d(require("path")),os=[{file:"uv.lock",weight:25},{file:"Cargo.toml",weight:22},{file:"mise.toml",weight:18},{file:".mise.toml",weight:8},{file:".ruby-version",weight:10},{file:"go.mod",weight:10},{file:"native/Cargo.toml",weight:7}];async function se(t){let e=os.map((o)=>{let n=ee.join(t,o.file),a=te.existsSync(n);return{...o,present:a}}),s=Math.min(100,e.reduce((o,n)=>n.present?o+n.weight:o,0)),i=ns(s);return{score:s,tier:i,markers:e,present:e.filter((o)=>o.present).map((o)=>o.file),missing:e.filter((o)=>!o.present).map((o)=>o.file)}}function ie(t){switch(t){case"loom":return"loom.svg";case"lens":return"lens.svg";default:return"gate.svg"}}function ns(t){if(t>=80)return"loom";if(t>=45)return"lens";return"gate"}class Et{extensionUri;output;containerId;fallbackItem;proposalAvailable=null;latestRustification=null;latestEntropy=null;constructor(t,e,s="chthonic-archive"){this.extensionUri=t;this.output=e;this.containerId=s;this.fallbackItem=b.window.createStatusBarItem(b.StatusBarAlignment.Left,47),this.fallbackItem.command="chthonic.refreshRustification",this.fallbackItem.tooltip="Rustification score and activity bar icon fallback",this.fallbackItem.show()}async update(t){this.latestRustification=t,await b.commands.executeCommand("setContext","chthonic.rustificationTier",t.tier),await b.commands.executeCommand("setContext","chthonic.rustificationScore",t.score),await this.apply()}async updateEntropy(t){this.latestEntropy=t,await b.commands.executeCommand("setContext","chthonic.decayStatus",t.status),await b.commands.executeCommand("setContext","chthonic.decayScore",Math.round(t.decay_score*100)),await this.apply()}dispose(){this.fallbackItem.dispose()}async apply(){let t=this.resolveIconFile(),e=b.Uri.joinPath(this.extensionUri,"resources",t);if(!await this.tryApplyProposedIcon(e))this.updateFallbackStatus();else this.fallbackItem.text=this.fallbackSummary(),this.fallbackItem.backgroundColor=void 0}resolveIconFile(){let t=this.latestEntropy;if(t){if(t.decay_score>0.5||t.status==="critical")return"hazard.svg";if(t.decay_score<0.2&&t.status==="pristine")return"gate.svg";return"lens.svg"}let e=this.latestRustification?.tier??"gate";return ie(e)}async tryApplyProposedIcon(t){if(this.proposalAvailable===!1)return!1;let e=b.window,s=["setActivityBarIcon","updateActivityBarIcon","setViewContainerIcon","updateViewContainerIcon"];for(let i of s){let o=e[i];if(typeof o!=="function")continue;try{return await o(this.containerId,t),this.proposalAvailable=!0,!0}catch(n){this.output.appendLine(`[morph] ${i} failed: ${as(n)}`)}}return this.proposalAvailable=!1,!1}updateFallbackStatus(){let t=this.latestRustification,e=this.latestEntropy;if(!t){this.fallbackItem.text="$(pulse) Slab boot",this.fallbackItem.tooltip="Rustification score pending";return}let s=rs(t.tier),i=e?Math.round(e.decay_score*100):null,o=e?`${e.status} ${i}%`:"unknown";this.fallbackItem.text=`$(pulse) ${s} ${t.score}% · Decay ${i??"?"}%`,this.fallbackItem.tooltip=[`Rustification ${t.score}% (${t.tier})`,`Decay ${o}`,`Present: ${t.present.join(", ")||"none"}`,`Missing: ${t.missing.join(", ")||"none"}`,e&&e.critical_tools.length>0?`Critical tools: ${e.critical_tools.join(", ")}`:void 0].filter(Boolean).join(`
`)}fallbackSummary(){let t=this.latestRustification,e=this.latestEntropy,s=t?`${t.score}%`:"?",i=e?`${Math.round(e.decay_score*100)}%`:"?";return`$(pulse) Slab ${s} · Decay ${i}`}}function rs(t){switch(t){case"loom":return"Loom";case"lens":return"Lens";default:return"Gate"}}function as(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}var C=d(require("vscode"));class Pt{output;constructor(t){this.output=t}async activate(){let t=await this.tryProposedLayout();if(!t)await this.applyCommandFallback();await C.commands.executeCommand("workbench.view.extension.chthonic-archive"),await C.commands.executeCommand("chthonic.loomView.focus"),this.output.appendLine(`[deep-focus] activated via ${t?"proposed-api":"command-fallback"} lane`)}async tryProposedLayout(){let t=C.window,e=t.moveViewTo;if(typeof e!=="function")return!1;let s=[t.ViewContainerLocation&&t.ViewContainerLocation.AuxiliaryBar,"auxiliaryBar","secondarySidebar"];for(let i of s){if(!i)continue;try{return await e("terminal",i),!0}catch(o){this.output.appendLine(`[deep-focus] proposed moveViewTo failed: ${oe(o)}`)}}return!1}async applyCommandFallback(){try{await C.commands.executeCommand("workbench.action.terminal.moveToSidePanel"),await C.commands.executeCommand("workbench.action.toggleAuxiliaryBar"),await C.commands.executeCommand("workbench.action.focusActiveEditorGroup")}catch(t){this.output.appendLine(`[deep-focus] fallback layout failed: ${oe(t)}`)}}}function oe(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}var q=d(require("vscode")),cs="chthonic.statusView",ds="chthonic.loomView";class Lt{output;constructor(t){this.output=t}async activate(){let t=await this.tryProposedLayout();if(!t)await this.applyCommandFallback();await q.commands.executeCommand("workbench.view.extension.chthonic-archive"),this.output.appendLine(`[restore-order] completed via ${t?"proposed-api":"command-fallback"} lane`)}async tryProposedLayout(){let t=q.window,e=t.moveViewTo;if(typeof e!=="function")return!1;let s=t.ViewContainerLocation,i=ne([s?.AuxiliaryBar,s?.SecondarySideBar,"auxiliaryBar","secondarySidebar"]),o=ne([s?.Panel,"panel"]);for(let n of i)for(let a of o)try{return await e(cs,n),await e(ds,a),!0}catch(l){this.output.appendLine(`[restore-order] proposed moveViewTo failed: ${re(l)}`)}return!1}async applyCommandFallback(){await ls(this.output,[["workbench.view.extension.chthonic-archive"],["chthonic.statusView.focus"],["workbench.action.moveFocusedViewToSecondarySidebar"],["chthonic.loomView.focus"],["workbench.action.moveFocusedViewToPanel"],["workbench.action.positionPanelBottom"],["workbench.action.focusActiveEditorGroup"]])}}async function ls(t,e){for(let s of e){let[i,...o]=s;try{await q.commands.executeCommand(i,...o)}catch(n){t.appendLine(`[restore-order] command failed (${i}): ${re(n)}`)}}}function ne(t){return t.filter((e)=>e!==void 0&&e!==null)}function re(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}var F=d(require("vscode"));class Z{static viewType="chthonic.loomView";view=null;report=null;resolveWebviewView(t,e,s){this.view=t,t.webview.options={enableScripts:!0},t.webview.html=this.buildHtml(),t.webview.onDidReceiveMessage((i)=>{if(!i||typeof i!=="object")return;let o=i;if(o.type==="refresh")F.commands.executeCommand("chthonic.refreshRustification");if(o.type==="heal")F.commands.executeCommand("chthonic.slabHeal");if(o.type==="deepFocus")F.commands.executeCommand("chthonic.deepFocus");if(o.type==="restoreOrder")F.commands.executeCommand("chthonic.restoreOrder")}),this.postState()}update(t){this.report=t,this.postState()}dispose(){this.view=null}postState(){if(!this.view||!this.report)return;this.view.webview.postMessage({type:"state",report:this.report})}buildHtml(){let t=ps();return`<!DOCTYPE html>
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
        body { padding: 10px; display: grid; grid-template-rows: auto auto 1fr auto; gap: 10px; }
        .panel {
            border: 1px solid var(--border);
            border-radius: 10px;
            background: var(--panel);
            padding: 10px;
        }
        .title { margin: 0; font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase; color: var(--accent); }
        .score { font-size: 28px; margin: 8px 0 0; }
        .meta { color: var(--muted); font-size: 11px; }
        .list { margin: 8px 0 0; padding: 0; list-style: none; max-height: 180px; overflow: auto; }
        .list li { font-size: 11px; color: var(--muted); padding: 2px 0; }
        .row { display: flex; gap: 8px; }
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
        <div class="title">Markers Present</div>
        <ul id="present" class="list"></ul>
    </section>

    <section class="panel">
        <div class="title">Markers Missing</div>
        <ul id="missing" class="list"></ul>
    </section>

    <div class="row">
        <button id="refresh">Refresh</button>
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

        document.getElementById('refresh').addEventListener('click', () => vscode.postMessage({ type: 'refresh' }));
        document.getElementById('heal').addEventListener('click', () => vscode.postMessage({ type: 'heal' }));
        document.getElementById('focus').addEventListener('click', () => vscode.postMessage({ type: 'deepFocus' }));
        document.getElementById('restore').addEventListener('click', () => vscode.postMessage({ type: 'restoreOrder' }));

        window.addEventListener('message', (event) => {
            const message = event.data;
            if (!message || message.type !== 'state' || !message.report) {
                return;
            }
            const report = message.report;
            score.textContent = report.score + '%';
            tier.textContent = report.tier;
            setList(present, report.present || []);
            setList(missing, report.missing || []);
        });
    </script>
</body>
</html>`}}function ps(){let e="";for(let s=0;s<24;s+=1)e+="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789".charAt(Math.floor(Math.random()*62));return e}var g=d(require("fs")),w=d(require("path")),tt=d(require("child_process")),de=d(require("vscode"));class Mt{output;envCollection;workspaceRoot;timer=null;running=!1;options={intervalMs:21600000,eolApiBase:"https://endoflife.date/api"};constructor(t,e,s){this.output=t;this.envCollection=e;this.workspaceRoot=s}start(t){this.options=t,this.stopTimer(),this.timer=setInterval(()=>{this.runNow("interval")},Math.max(60000,t.intervalMs))}async runNow(t="manual"){if(this.running){this.output.appendLine("[slab-heal] skipped; already running");return}this.running=!0;try{let e=await this.collectRuntimeStates();if(e.length===0){this.output.appendLine("[slab-heal] no runtime states detected; skipping");return}let s=[];for(let i of e)if(await this.isEol(i.language,i.version))s.push(i);if(s.length===0){this.output.appendLine(`[slab-heal] ${t}: all slab runtimes are supported`);return}this.output.appendLine(`[slab-heal] ${t}: stale runtimes detected: ${s.map((i)=>`${i.language}@${i.version}`).join(", ")}`),await this.repair(s)}catch(e){this.output.appendLine(`[slab-heal] run failed: ${Rt(e)}`)}finally{this.running=!1}}dispose(){this.stopTimer()}stopTimer(){if(this.timer)clearInterval(this.timer),this.timer=null}async collectRuntimeStates(){let t=[{language:"python",command:"python",args:["-c",'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")']},{language:"ruby",command:"ruby",args:["-e","print RUBY_VERSION"]},{language:"go",command:"go",args:["env","GOVERSION"]},{language:"rust",command:"rustc",args:["--version"]},{language:"solana",command:"solana",args:["--version"]}],e=[];for(let s of t)try{let i=await le(s.command,s.args,this.workspaceRoot),o=hs(i,s.language);if(!o)continue;e.push({language:s.language,version:o})}catch(i){this.output.appendLine(`[slab-heal] probe ${s.language} failed: ${Rt(i)}`)}return e}async isEol(t,e){let s=await this.fetchCycles(t);if(!s||!Array.isArray(s))return!1;let i=ms(t,e),o=s.find((a)=>{let l=a;return l.cycle===i||l.cycle===i.split(".").slice(0,1).join(".")});if(!o||o.eol==null)return!1;if(typeof o.eol==="boolean")return o.eol;let n=Date.parse(o.eol);if(Number.isNaN(n))return!1;return n<=Date.now()}async fetchCycles(t){let e=fs(t);for(let s of e){let i=await fetch(`${this.options.eolApiBase}/${s}.json`,{headers:{accept:"application/json"}});if(!i.ok)continue;let o=await i.json();if(Array.isArray(o))return o}return this.output.appendLine(`[slab-heal] endoflife feed unavailable for ${t}; skipping lifecycle gate`),null}async repair(t){await ce("mise",["upgrade"],this.workspaceRoot,this.output),await ce("mise",["reshim"],this.workspaceRoot,this.output);let e=await this.relinkVsHeaders();if(e)this.output.appendLine(`[slab-heal] relinked MSVC headers at ${e}`);else this.output.appendLine("[slab-heal] VS include relink skipped (MSVC path not found)");de.window.showInformationMessage(`Chthonic self-heal complete: ${t.map((s)=>`${s.language}@${s.version}`).join(", ")}`)}async relinkVsHeaders(){let t=await us(this.workspaceRoot);if(!t||!this.workspaceRoot)return null;let e=w.join(this.workspaceRoot,".chthonic","native","msvc"),s=w.join(e,"include");g.mkdirSync(e,{recursive:!0});try{g.rmSync(s,{recursive:!0,force:!0})}catch{}try{g.symlinkSync(t,s,"junction")}catch(i){let o=w.join(e,"include.path.txt");g.writeFileSync(o,t,"utf8"),this.output.appendLine(`[slab-heal] symlink failed; wrote include manifest ${o}: ${Rt(i)}`)}return this.envCollection.replace("CHTHONIC_VS_CPP_INCLUDE",t),this.envCollection.prepend("INCLUDE",`${t};`),t}}async function us(t){let e=w.join(process.env["ProgramFiles(x86)"]||"C:\\Program Files (x86)","Microsoft Visual Studio","Installer","vswhere.exe");if(g.existsSync(e))try{let i=await le(e,["-latest","-products","*","-requires","Microsoft.VisualStudio.Component.VC.Tools.x86.x64","-property","installationPath"],t),o=ae(i.trim());if(o)return o}catch{}let s=["C:\\Program Files\\Microsoft Visual Studio\\2026","C:\\Program Files\\Microsoft Visual Studio\\2022"];for(let i of s){let o=ae(i);if(o)return o}return null}function ae(t){if(!g.existsSync(t))return null;let e=[],s=[t];while(s.length>0){let i=s.pop(),o=[];try{o=g.readdirSync(i,{withFileTypes:!0})}catch{continue}for(let n of o){let a=w.join(i,n.name);if(!n.isDirectory())continue;if(n.name==="include"&&a.includes(`${w.sep}VC${w.sep}Tools${w.sep}MSVC${w.sep}`)){e.push(a);continue}s.push(a)}}if(e.length===0)return null;return e.sort((i,o)=>o.localeCompare(i,void 0,{numeric:!0,sensitivity:"base"})),e[0]}async function le(t,e,s){return new Promise((i,o)=>{tt.execFile(t,e,{cwd:s||void 0,windowsHide:!0,timeout:15000},(n,a,l)=>{if(n){o(Error(`${t} ${e.join(" ")} failed: ${l||n.message}`));return}i(String(a).trim())})})}async function ce(t,e,s,i){await new Promise((o,n)=>{let a=tt.spawn(t,e,{cwd:s||void 0,windowsHide:!0,stdio:["ignore","pipe","pipe"]});a.stdout.on("data",(l)=>{i.appendLine(`[slab-heal] ${l.toString().trimEnd()}`)}),a.stderr.on("data",(l)=>{i.appendLine(`[slab-heal] ${l.toString().trimEnd()}`)}),a.on("error",n),a.on("exit",(l)=>{if(l===0)o();else n(Error(`${t} ${e.join(" ")} exited with code ${l??-1}`))})})}function hs(t,e){let s=t.trim();if(!s)return"";switch(e){case"go":return s.replace(/^go/i,"");case"rust":return s.replace(/^rustc\s+/i,"").split(/\s+/)[0]??"";case"solana":return s.replace(/^solana-cli\s+/i,"").split(/\s+/)[0]??"";default:return s}}function ms(t,e){let s=e.split(".");if(t==="go")return s.slice(0,2).join(".");if(t==="solana")return s.slice(0,1).join(".");return s.slice(0,2).join(".")}function fs(t){switch(t){case"solana":return["solana","agave","solana-cli"];default:return[t]}}function Rt(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}function gs(t){console.log("☥ Chthonic Archive extension activated");let e=c.window.createOutputChannel("Chthonic SDK"),s=c.workspace.workspaceFolders?.[0]?.uri.fsPath||null,i=U.join(s||"","meta-ide","copilot-sdk","harness.ts"),o=new Q(t.extensionUri,i,(r)=>e.appendLine(`[${new Date().toISOString()}] ${r}`));t.subscriptions.push(c.window.registerWebviewViewProvider(Q.viewType,o));let n=new Et(t.extensionUri,e),a=new Pt(e),l=new Lt(e),h=new Z,P=new Mt(e,t.environmentVariableCollection,s);t.subscriptions.push(n,h,P,c.window.registerWebviewViewProvider(Z.viewType,h));let p=c.workspace.getConfiguration("chthonic"),m=p.get("entropy.enabled",!0),k=p.get("entropy.maxFiles",1e4),st=p.get("entropy.scanIntervalMs",20000),x=p.get("entropy.decorationDebounceMs",120),fe=p.get("entropy.decorationBatchSize",240),ge=p.get("entropy.polyglotEnabled",!0),ye=p.get("entropy.pythonScanIntervalMs",30000),ve=p.get("entropy.ledgerSettleDebounceMs",1400),be=p.get("entropy.ledgerMode","validator"),xe=p.get("entropy.solanaRpcUrl","http://127.0.0.1:8899"),we=p.get("entropy.solanaAutostartValidator",!1),ke=et(p.get("entropy.solanaLedgerHostBinaryPath","")),Se=et(p.get("entropy.solanaWalletPath","")),Ee=et(p.get("entropy.solanaIdlPath","")),S=new dt(t,e),N,T=new xt(e,S,{enabled:ge,pythonScanIntervalMs:ye,settleDebounceMs:ve,ledgerMode:be,solanaRpcUrl:xe,solanaAutostartValidator:we,solanaLedgerHostBinaryPath:ke,solanaWalletPath:Se,solanaIdlPath:Ee},(r)=>N?.enqueueExternalUpdates(r));N=new pt(S,x,fe,(r)=>T.getTooltipFragments(r));let A=new W(t.extensionUri,S);A.setRootPath(s),t.subscriptions.push(S,N,A,T,c.window.registerFileDecorationProvider(N),c.window.registerWebviewViewProvider(W.viewType,A));let I=async(r)=>{if(!s)return;let u=await se(s);h.update(u),await n.update(u),e.appendLine(`[monolith] rustification ${u.score}% (${u.tier}) via ${r}`)};if(s){I("startup");let r=c.workspace.createFileSystemWatcher(new c.RelativePattern(s,"{uv.lock,Cargo.toml,mise.toml,.mise.toml,go.mod,.ruby-version}"));t.subscriptions.push(r,r.onDidCreate(()=>{I("marker-create")}),r.onDidChange(()=>{I("marker-change")}),r.onDidDelete(()=>{I("marker-delete")}))}if(s&&m)S.start(s,k,st),T.start(s);t.subscriptions.push(c.workspace.onDidSaveTextDocument((r)=>{S.refreshFile(r.uri),T.onDidSaveDocument(r)})),t.subscriptions.push(c.commands.registerCommand("chthonic.entropyRefresh",()=>{S.rescanNow(),S.requestGraph(260),T.requestManualScan(),c.window.showInformationMessage("Chthonic entropy scan requested")}));let Pe=p.get("reactor.enabled",!0),Le=p.get("reactor.headlessVulkan",!0),Re=p.get("reactor.cockpitAutoLayout",!1),Me=p.get("reactor.transport","auto"),$e=et(p.get("reactor.daemonBinaryPath","")),Ce=p.get("slab.selfHealingEnabled",!0),Ct=p.get("slab.selfHealingIntervalMs",21600000),At=p.get("slab.eolApiBase","https://endoflife.date/api"),Ae=bs(At),Be=Math.max(60000,Math.floor(Ct/2)),f=new wt(e,Le,$e,Ae,Be),J=new kt(e,t.environmentVariableCollection),it=new SynapseBridge(e,t.extensionPath,Me),ot=null,nt=null,O=null,Bt=(r,u)=>{let L=u?`${r} (${u.toLocaleString()} tps)`:r;e.appendLine(`[loom-reflex] panel lane ${L}`),l.activate()},De=(r)=>{e.appendLine(`[loom-reflex] primary lane ${r}`),c.commands.executeCommand("workbench.view.extension.chthonic-archive"),c.commands.executeCommand("chthonic.loomView.focus")};t.subscriptions.push(f,J,it);let Dt=(r)=>{if(n.updateEntropy(r),e.appendLine(`[lens] decay ${Math.round(r.decay_score*100)}% (${r.status}) from ${r.source_mise??"no-mise"}`),r.validator_active){let y=`${r.validator_process??"validator"}:${r.validator_source_mise}`;if(y!==nt)nt=y,De(`validator-online:${y}`)}else nt=null;if(r.firedancer_surge&&r.validator_active){let y=`${r.checked_at_epoch_ms}:${r.simulated_tps}`;if(y!==O)O=y,Bt("entropy-surge",r.simulated_tps)}else O=null;if(!r.critical||!r.auto_update_enabled){ot=null;return}let u=`${r.status}:${r.auto_update}:${[...r.critical_tools].sort().join(",")}`;if(u===ot)return;ot=u;let L=r.critical_tools.length>0?r.critical_tools.join(", "):"runtime toolchain";c.window.showWarningMessage(`Chthonic decay is critical (${Math.round(r.decay_score*100)}%). ${L} needs healing.`,"Run mise upgrade","Later").then((y)=>{if(y==="Run mise upgrade")P.runNow("manual")})};if(t.subscriptions.push(f.onDidReceiveEnv((r)=>{J.applyTerminalEnv(r)}),f.onDidReceiveSediment((r)=>{A.postSedimentData(r)}),f.onDidReceiveSedimentChunk((r)=>{A.postSedimentChunk(r)}),f.onDidReceiveSynapse((r)=>{it.updateDescriptor(r)}),f.onDidReceiveEntropyState((r)=>{Dt(r)}),f.onDidReceiveFiredancerSurge((r)=>{if(r.surge){let u=`${r.slot}:${r.simulated_tps}`;if(u!==O)O=u,Bt("daemon-surge",r.simulated_tps)}})),A.onRequestSediment(()=>{vs(f,A,it,e)}),s&&Pe){if(f.start(s),f.requestEntropyState().then((u)=>{Dt(u)}).catch((u)=>{e.appendLine(`[lens] initial entropy snapshot unavailable: ${u}`)}),Re)J.activate();let r=U.join(s,".git","HEAD");if(D.existsSync(r)){let u=null,L=D.watch(U.join(s,".git"),{persistent:!1},(y,_t)=>{if(_t==="HEAD"||_t?.startsWith("refs")){if(u)clearTimeout(u);u=setTimeout(()=>{e.appendLine("[reactor] git change detected, recomputing sediment"),f.requestSediment(10,500).catch((Te)=>{e.appendLine(`[reactor] live-loop sediment failed: ${Te}`)})},800)}});t.subscriptions.push({dispose:()=>L.close()})}}if(s&&Ce)P.start({intervalMs:Ct,eolApiBase:At}),P.runNow("interval");t.subscriptions.push(c.commands.registerCommand("chthonic.activateCockpit",()=>{J.activate()}),c.commands.registerCommand("chthonic.deepFocus",()=>{a.activate()}),c.commands.registerCommand("chthonic.restoreOrder",()=>{l.activate()}),c.commands.registerCommand("chthonic.slabHeal",()=>{P.runNow("manual")}),c.commands.registerCommand("chthonic.refreshRustification",()=>{I("manual-command")}),c.commands.registerCommand("chthonic.annoDetect",()=>{if(s)f.start(s);c.window.showInformationMessage("ANNO project detection triggered")}),c.commands.registerCommand("chthonic.reactorSediment",async()=>{try{let r=await f.requestSediment(10,500);c.window.showInformationMessage(`Sediment computed: ${r.file_count} files, ${r.layer_count} layers (${r.backend}, ${r.compute_time_ms}ms)`)}catch(r){c.window.showErrorMessage(`Sediment computation failed: ${r}`)}}));let rt=new he;c.window.registerTreeDataProvider("chthonic.themeView",rt),t.subscriptions.push(c.commands.registerCommand("chthonic.switchTheme",async()=>{let r=[{label:"$(paintcan) Flesh & Earth",description:"Warm earth · WCAG AA · Distribution palette",id:"Chthonic Mandala - Flesh & Earth"},{label:"$(zap) ROGBIV",description:"SSOT spectral · FA¹⁻⁵ canonical hexes",id:"Chthonic Mandala - ROGBIV"}],u=c.workspace.getConfiguration("workbench").get("colorTheme"),L=await c.window.showQuickPick(r.map((y)=>({...y,picked:u===y.id})),{placeHolder:`Current: ${u}`});if(L)await c.workspace.getConfiguration("workbench").update("colorTheme",L.id,c.ConfigurationTarget.Workspace),c.window.showInformationMessage(`Theme: ${L.id}`),rt.refresh()}));let Tt=c.workspace.getConfiguration("chthonic");if(Tt.get("showSSOTHash",!0)){let r=c.window.createStatusBarItem(c.StatusBarAlignment.Left,50);r.command="chthonic.verifySSOT",r.tooltip="SSOT integrity hash — click to verify",t.subscriptions.push(r),pe(r),t.subscriptions.push(c.workspace.onDidSaveTextDocument((u)=>{if(u.fileName.includes("copilot-instructions"))pe(r)}))}if(Tt.get("showLineage",!0)){let r=c.window.createStatusBarItem(c.StatusBarAlignment.Left,49);r.text="$(git-branch) ☥ main",r.tooltip="Chthonic lineage",r.show(),t.subscriptions.push(r)}let It=new me;c.window.registerTreeDataProvider("chthonic.statusView",It),t.subscriptions.push(c.commands.registerCommand("chthonic.verifySSOT",async()=>{let r=$t();if(r)c.window.showInformationMessage(`SSOT SHA-256: ${r.substring(0,16)}…`);else c.window.showWarningMessage("SSOT file not found")})),t.subscriptions.push(c.commands.registerCommand("chthonic.refreshStatus",()=>{It.refresh(),rt.refresh(),S.rescanNow(),S.requestGraph(260),T.requestManualScan(),I("refresh-status")}))}function ys(){}async function vs(t,e,s,i){try{if(s.isReady()){let o=await t.requestSedimentSynapse(10,500,220);if(o.transport==="shared_memory"){let n=await s.drain(o,(a)=>{e.postSedimentBinary(a)});i.appendLine(`[reactor] synapse drain ${n}/${o.chunks_written} chunks`);return}}await t.requestSedimentStream(10,500)}catch(o){i.appendLine(`[reactor] sediment request failed: ${o}`)}}function $t(){let t=c.workspace.workspaceFolders?.[0];if(!t)return null;let e=c.workspace.getConfiguration("chthonic").get("ssotPath",".github/copilot-instructions.md"),s=U.join(t.uri.fsPath,e);if(!D.existsSync(s))return null;let o=D.readFileSync(s,"utf-8").replace(/\r\n/g,`
`).replace(/\r/g,`
`).split(`
`).map((n)=>n.trimEnd()).join(`
`).trim();return ue.createHash("sha256").update(o,"utf-8").digest("hex")}function pe(t){let e=$t();if(e)t.text=`$(shield) ${e.substring(0,8)}`,t.show();else t.text="$(shield) SSOT ??",t.show()}function et(t){let e=t.trim();return e.length>0?e:void 0}function bs(t){let e=t.trim().replace(/\/+$/,"");if(e.endsWith("/api"))return`${e}/v1`;return e.length>0?e:"https://endoflife.date/api/v1"}class he{_onDidChange=new c.EventEmitter;onDidChangeTreeData=this._onDidChange.event;refresh(){this._onDidChange.fire()}getTreeItem(t){return t}getChildren(){let t=c.workspace.getConfiguration("workbench").get("colorTheme")||"";return[{name:"Chthonic Mandala - Flesh & Earth",short:"Flesh & Earth",icon:"\uD83C\uDF0D",desc:"Warm earth · Distribution"},{name:"Chthonic Mandala - ROGBIV",short:"ROGBIV",icon:"\uD83C\uDF08",desc:"SSOT spectral · Research"}].map((s)=>{let i=t===s.name,o=new c.TreeItem(`${i?"◉":"○"} ${s.icon} ${s.short}`,c.TreeItemCollapsibleState.None);return o.tooltip=`${s.name}
${s.desc}${i?`

✅ ACTIVE`:""}`,o.description=i?"active":"",o.command={command:"chthonic.switchTheme",title:"Switch"},o})}}class me{_onDidChange=new c.EventEmitter;onDidChangeTreeData=this._onDidChange.event;refresh(){this._onDidChange.fire()}getTreeItem(t){return t}getChildren(){let t=$t(),e=[],s=new c.TreeItem(`$(shield) SSOT: ${t?t.substring(0,12)+"…":"not found"}`,c.TreeItemCollapsibleState.None);s.command={command:"chthonic.verifySSOT",title:"Verify"},e.push(s);let i=new c.TreeItem(`$(paintcan) Theme: ${(c.workspace.getConfiguration("workbench").get("colorTheme")||"default").replace("Chthonic Mandala - ","")}`,c.TreeItemCollapsibleState.None);return i.command={command:"chthonic.switchTheme",title:"Switch"},e.push(i),e}}
