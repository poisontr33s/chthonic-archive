var _e=Object.create;var{getPrototypeOf:Ve,defineProperty:H,getOwnPropertyNames:Ht,getOwnPropertyDescriptor:Oe}=Object,qt=Object.prototype.hasOwnProperty;var d=(t,e,i)=>{i=t!=null?_e(Ve(t)):{};let n=e||!t||!t.__esModule?H(i,"default",{value:t,enumerable:!0}):i;for(let s of Ht(t))if(!qt.call(n,s))H(n,s,{get:()=>t[s],enumerable:!0});return n},jt=new WeakMap,je=(t)=>{var e=jt.get(t),i;if(e)return e;if(e=H({},"__esModule",{value:!0}),t&&typeof t==="object"||typeof t==="function")Ht(t).map((n)=>!qt.call(e,n)&&H(e,n,{get:()=>t[n],enumerable:!(i=Oe(t,n))||i.enumerable}));return jt.set(t,e),e};var He=(t,e)=>{for(var i in e)H(t,i,{get:e[i],enumerable:!0,configurable:!0,set:(n)=>e[i]=()=>n})};var ki={};He(ki,{deactivate:()=>xi,activate:()=>bi});module.exports=je(ki);var c=d(require("vscode")),he=d(require("crypto")),D=d(require("fs")),J=d(require("path"));var Nt=d(require("vscode")),lt=d(require("child_process"));var Ft=d(require("child_process")),Ut=d(require("readline")),W=d(require("path"));class dt{harnessPath;log;process=null;rl=null;handlers=new Set;authenticated=!1;ready=!1;constructor(t,e){this.harnessPath=t;this.log=e}async start(){if(this.process)return;let t=W.dirname(this.harnessPath),e=W.basename(this.harnessPath);this.process=Ft.spawn("bun",["run",e],{cwd:t,stdio:["pipe","pipe","pipe"],env:{...process.env}}),this.process.stderr?.on("data",(i)=>{this.log(`[harness stderr] ${i.toString().trim()}`)}),this.process.on("close",(i)=>{this.log(`[harness] exited with code ${i}`),this.process=null,this.rl=null,this.ready=!1,this.authenticated=!1}),this.rl=Ut.createInterface({input:this.process.stdout}),this.rl.on("line",(i)=>{try{let n=JSON.parse(i);if(n.type==="ready")this.ready=!0,this.log(`[harness] ready: ${n.sdk}`);for(let s of this.handlers)s(n)}catch{this.log(`[harness] non-JSON: ${i.substring(0,200)}`)}}),await new Promise((i,n)=>{let s=setTimeout(()=>n(Error("Harness startup timeout")),15000),o=(a)=>{if(a.type==="ready")clearTimeout(s),this.handlers.delete(o),i()};this.handlers.add(o)})}async authenticate(t,e){this.send({cmd:"auth",token:t,login:e}),await this.waitFor("auth_ok"),this.authenticated=!0,this.log(`[harness] authenticated as ${e}`)}query(t,e,i,n,s){return new Promise((o,a)=>{let l=(h)=>{if(h.id!==t)return;if(h.type==="event"&&h.event)n(h.event);else if(h.type==="done")this.handlers.delete(l),o();else if(h.type==="cancelled")this.handlers.delete(l),o();else if(h.type==="error")this.handlers.delete(l),a(Error(h.message||"Query failed"))};this.handlers.add(l),this.send({cmd:"query",id:t,prompt:e,workingDirectory:i,model:s?.model,reasoningEffort:s?.reasoningEffort})})}cancel(t){this.send({cmd:"cancel",id:t})}async getModels(){return this.send({cmd:"models"}),(await this.waitFor("models")).data||[]}isReady(){return this.ready&&this.authenticated&&this.process!==null}stop(){if(this.process)this.process.kill(),this.process=null;this.rl=null,this.ready=!1,this.authenticated=!1,this.handlers.clear()}send(t){if(!this.process?.stdin?.writable)throw Error("Harness not running");this.process.stdin.write(JSON.stringify(t)+`
`)}waitFor(t,e=15000){return new Promise((i,n)=>{let s=setTimeout(()=>{this.handlers.delete(o),n(Error(`Timeout waiting for ${t}`))},e),o=(a)=>{if(a.type===t)clearTimeout(s),this.handlers.delete(o),i(a);else if(a.type==="error")clearTimeout(s),this.handlers.delete(o),n(Error(a.message||"Error"))};this.handlers.add(o)})}}class G{extensionUri;harnessPath;log;static viewType="chthonic.chatView";view;connection=null;isConnecting=!1;activeQueryId=null;constructor(t,e,i){this.extensionUri=t;this.harnessPath=e;this.log=i}resolveWebviewView(t,e,i){this.view=t,t.webview.options={enableScripts:!0,localResourceRoots:[this.extensionUri]},t.webview.html=this.getHtml(),t.webview.onDidReceiveMessage(async(n)=>{switch(n.type){case"connect":await this.connectAgent();break;case"prompt":await this.sendPrompt(n.text);break;case"cancel":this.cancelQuery();break;case"disconnect":this.disconnectAgent();break}})}async connectAgent(){if(this.isConnecting||this.connection?.isReady())return;this.isConnecting=!0,this.postMessage({type:"status",status:"connecting"});try{this.connection=new dt(this.harnessPath,this.log),await this.connection.start();let t=lt.execSync("gh auth token",{encoding:"utf-8"}).trim(),e=lt.execSync("gh api user --jq .login",{encoding:"utf-8"}).trim();await this.connection.authenticate(t,e),this.postMessage({type:"connected",agentName:"Chthonic SDK",agentVersion:"0.1.0",login:e}),this.log(`Chat connected: ${e}`)}catch(t){this.log(`Chat connect failed: ${t.message}`),this.postMessage({type:"error",message:t.message}),this.connection?.stop(),this.connection=null}finally{this.isConnecting=!1}}async sendPrompt(t){if(!this.connection?.isReady()){this.postMessage({type:"error",message:"Not connected"});return}let e=crypto.randomUUID();this.activeQueryId=e,this.postMessage({type:"prompt-start"});let i=Nt.workspace.workspaceFolders?.[0]?.uri.fsPath||process.cwd();try{await this.connection.query(e,t,i,(n)=>this.handleSdkEvent(n))}catch(n){this.postMessage({type:"error",message:n.message})}finally{this.activeQueryId=null,this.postMessage({type:"prompt-end"})}}handleSdkEvent(t){switch(t.type){case"assistant.message":if(t.data?.content)this.postMessage({type:"agent-message",content:t.data.content});break;case"assistant.message.delta":if(t.data?.delta)this.postMessage({type:"agent-delta",delta:t.data.delta});break;case"tool.execution_start":this.postMessage({type:"tool-start",name:t.data?.name,args:t.data?.arguments});break;case"tool.execution_complete":this.postMessage({type:"tool-end",name:t.data?.name});break;case"assistant.reasoning":this.postMessage({type:"reasoning"});break;case"assistant.usage":this.postMessage({type:"usage",model:t.data?.model,inputTokens:t.data?.inputTokens,outputTokens:t.data?.outputTokens,duration:t.data?.duration});break;case"session.usage_info":this.postMessage({type:"context-info",tokenLimit:t.data?.tokenLimit,currentTokens:t.data?.currentTokens});break}}cancelQuery(){if(this.activeQueryId&&this.connection)this.connection.cancel(this.activeQueryId)}disconnectAgent(){this.connection?.stop(),this.connection=null,this.activeQueryId=null,this.postMessage({type:"disconnected"})}postMessage(t){this.view?.webview.postMessage(t)}dispose(){this.connection?.stop()}getHtml(){return`<!DOCTYPE html>
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
</html>`}}var q=d(require("path")),_=d(require("vscode")),Jt=require("worker_threads");class pt{extensionContext;output;records=new Map;recordUris=new Map;onDidUpdateRecordsEmitter=new _.EventEmitter;onDidUpdateRecords=this.onDidUpdateRecordsEmitter.event;onDidUpdateGraphEmitter=new _.EventEmitter;onDidUpdateGraph=this.onDidUpdateGraphEmitter.event;onDidUpdateSnapshotEmitter=new _.EventEmitter;onDidUpdateSnapshot=this.onDidUpdateSnapshotEmitter.event;worker=null;rootPath=null;workerPath;maxFiles=1e4;lastScanDurationMs=0;lastScanAt=0;scanTimer=null;disposed=!1;constructor(t,e){this.extensionContext=t;this.output=e;this.workerPath=t.asAbsolutePath(q.join("dist","entropy-worker.js"))}start(t,e,i){this.rootPath=t,this.maxFiles=e,this.ensureWorker(),this.send({type:"scan",root:t,maxFiles:this.maxFiles}),this.scheduleScanLoop(i)}rescanNow(){if(!this.rootPath)return;this.send({type:"scan",root:this.rootPath,maxFiles:this.maxFiles})}refreshFile(t){if(!this.rootPath||t.scheme!=="file")return;this.send({type:"refresh-file",root:this.rootPath,path:t.fsPath})}requestGraph(t){this.send({type:"graph",limit:t})}getRecord(t){if(!this.rootPath||t.scheme!=="file")return;let e=qe(q.relative(this.rootPath,t.fsPath));return this.records.get(e)}getSnapshot(t=40){let e=Array.from(this.records.values()),i=e.length===0?0:e.reduce((s,o)=>s+o.entropy,0)/e.length,n=e.sort((s,o)=>o.entropy-s.entropy).slice(0,t);return{totalFiles:e.length,topEntropy:n,averageEntropy:i,lastScanDurationMs:this.lastScanDurationMs,lastScanAt:this.lastScanAt}}dispose(){if(this.disposed=!0,this.scanTimer)clearInterval(this.scanTimer),this.scanTimer=null;this.send({type:"stop"}),this.worker?.terminate(),this.worker=null,this.onDidUpdateRecordsEmitter.dispose(),this.onDidUpdateGraphEmitter.dispose(),this.onDidUpdateSnapshotEmitter.dispose()}scheduleScanLoop(t){if(this.scanTimer)clearInterval(this.scanTimer);let e=Math.max(5000,t);this.scanTimer=setInterval(()=>{if(!this.disposed)this.rescanNow()},e)}ensureWorker(){if(this.worker)return;this.worker=new Jt.Worker(this.workerPath),this.worker.on("message",(t)=>this.handleWorkerEvent(t)),this.worker.on("error",(t)=>{this.output.appendLine(`[entropy] worker error: ${t.message}`)}),this.worker.on("exit",(t)=>{if(this.output.appendLine(`[entropy] worker exited with code ${t}`),this.worker=null,!this.disposed&&t!==0)this.ensureWorker(),this.rescanNow()})}send(t){this.ensureWorker(),this.worker?.postMessage(t)}handleWorkerEvent(t){switch(t.type){case"scan-progress":{if(!this.rootPath)return;let e=[];for(let i of t.records){this.records.set(i.path,i);let n=this.recordUris.get(i.path);if(!n)n=_.Uri.file(q.join(this.rootPath,i.path)),this.recordUris.set(i.path,n);e.push(n)}if(e.length>0)this.onDidUpdateRecordsEmitter.fire(e);break}case"scan-complete":this.lastScanDurationMs=t.durationMs,this.lastScanAt=Date.now(),this.onDidUpdateSnapshotEmitter.fire(this.getSnapshot());break;case"graph-result":this.onDidUpdateGraphEmitter.fire(t.graph);break;case"error":this.output.appendLine(`[entropy] ${t.message}${t.detail?`
${t.detail}`:""}`);break}}}function qe(t){return t.replace(/\\/g,"/")}var zt=d(require("vscode"));class ht{workerClient;debounceMs;maxPerFlush;tooltipAugmentProvider;onDidChangeEmitter=new zt.EventEmitter;onDidChangeFileDecorations=this.onDidChangeEmitter.event;pending=new Map;flushTimer=null;constructor(t,e,i,n){this.workerClient=t;this.debounceMs=e;this.maxPerFlush=i;this.tooltipAugmentProvider=n;this.workerClient.onDidUpdateRecords((s)=>this.enqueueUpdates(s))}dispose(){if(this.flushTimer)clearTimeout(this.flushTimer),this.flushTimer=null;this.onDidChangeEmitter.dispose()}updateConfig(t,e){this.debounceMs=Math.max(30,t),this.maxPerFlush=Math.max(64,e)}provideFileDecoration(t){if(t.scheme!=="file")return;let e=this.workerClient.getRecord(t);if(!e)return;let i=Fe(e),n=[`Entropy ${(e.entropy*100).toFixed(0)}%`,`Complexity ${e.complexity}`,`Debt ${e.debt}`,`Freshness ${(e.freshness*100).toFixed(0)}%`];if(this.tooltipAugmentProvider)n.push(...this.tooltipAugmentProvider(t));return{color:i,tooltip:n.join(`
`),propagate:!1}}enqueueExternalUpdates(t){this.enqueueUpdates(t)}enqueueUpdates(t){for(let e of t)this.pending.set(e.toString(),e);if(!this.flushTimer)this.flushTimer=setTimeout(()=>this.flush(),this.debounceMs)}flush(){if(this.flushTimer=null,this.pending.size===0)return;let t=Array.from(this.pending.values()).slice(0,this.maxPerFlush);for(let e of t)this.pending.delete(e.toString());if(this.onDidChangeEmitter.fire(t),this.pending.size>0)this.flushTimer=setTimeout(()=>this.flush(),this.debounceMs)}}function Fe(t){let e=Ne(t.entropy*0.78+(1-t.freshness)*0.22),i=ut(118,24,e),n=ut(36,46,e),s=ut(58,42,e);return Ue(i,n,s)}function Ue(t,e,i){let n=t/360,s=e/100,o=i/100,a=(g,S,st)=>{let w=st;if(w<0)w+=1;if(w>1)w-=1;if(w<0.16666666666666666)return g+(S-g)*6*w;if(w<0.5)return S;if(w<0.6666666666666666)return g+(S-g)*(0.6666666666666666-w)*6;return g},l,h,P;if(s===0)l=o,h=o,P=o;else{let g=o<0.5?o*(1+s):o+s-o*s,S=2*o-g;l=a(S,g,n+0.3333333333333333),h=a(S,g,n),P=a(S,g,n-0.3333333333333333)}let p=(g)=>{return Math.round(g*255).toString(16).padStart(2,"0")};return`#${p(l)}${p(h)}${p(P)}`}function Ne(t){if(t<0)return 0;if(t>1)return 1;return t}function ut(t,e,i){return t+(e-t)*i}var V=d(require("path")),b=d(require("vscode"));class K{extensionUri;workerClient;static viewType="chthonic.abyssalView";disposables=[];view=null;rootPath=null;sedimentRequestCallback=null;constructor(t,e){this.extensionUri=t;this.workerClient=e;this.disposables.push(this.workerClient.onDidUpdateGraph((i)=>this.postMessage({type:"graph",graph:i})),this.workerClient.onDidUpdateSnapshot((i)=>this.postMessage({type:"snapshot",snapshot:i})))}setRootPath(t){this.rootPath=t}onRequestSediment(t){this.sedimentRequestCallback=t}postSedimentData(t){this.postMessage({type:"sediment",sediment:t})}postSedimentChunk(t){this.postMessage({type:"sedimentChunk",chunk:t})}postSedimentBinary(t){let e=t.buffer.slice(t.byteOffset,t.byteOffset+t.byteLength);this.postMessage({type:"sedimentBinary",payload:e})}dispose(){this.disposables.forEach((t)=>t.dispose()),this.disposables.length=0}resolveWebviewView(t,e,i){this.view=t,t.webview.options={enableScripts:!0,localResourceRoots:[this.extensionUri]},t.webview.html=this.getHtml(t.webview),t.webview.onDidReceiveMessage((n)=>{this.handleMessage(n)})}handleMessage(t){if(!t||typeof t!=="object")return;let e=t;if(!e.type)return;if(e.type==="ready"){this.postMessage({type:"snapshot",snapshot:this.workerClient.getSnapshot()}),this.workerClient.requestGraph(260);return}if(e.type==="requestGraph"){this.workerClient.requestGraph(260);return}if(e.type==="requestSediment"){this.sedimentRequestCallback?.();return}if(e.type==="openFile"&&e.path&&this.rootPath){let i=V.normalize(e.path);if(i.startsWith("..")||V.isAbsolute(i))return;let n=V.join(this.rootPath,i),s=b.Uri.file(n);b.workspace.openTextDocument(s).then((o)=>{b.window.showTextDocument(o,{preview:!1})},()=>{b.window.showWarningMessage(`Unable to open ${e.path}`)})}}postMessage(t){if(!this.view)return;this.view.webview.postMessage(t)}getHtml(t){let e=Je(),i=t.asWebviewUri(b.Uri.joinPath(this.extensionUri,"media","abyssalPane.js")),n=t.asWebviewUri(b.Uri.joinPath(this.extensionUri,"media","wasm","pkg","entropy_renderer_wasm.js")),s=t.asWebviewUri(b.Uri.joinPath(this.extensionUri,"media","wasm","pkg","entropy_renderer_wasm_bg.wasm")),o=t.asWebviewUri(b.Uri.joinPath(this.extensionUri,"media","wasm","pkg","chthonic_loom.js")),a=t.asWebviewUri(b.Uri.joinPath(this.extensionUri,"media","wasm","pkg","chthonic_loom_bg.wasm")),l=["default-src 'none'",`img-src ${t.cspSource} data:`,`style-src ${t.cspSource} 'unsafe-inline'`,`script-src 'nonce-${e}' ${t.cspSource}`,`connect-src ${t.cspSource}`].join("; "),h=JSON.stringify({wasmModuleUri:n.toString(),wasmBinaryUri:s.toString(),loomWasmModuleUri:o.toString(),loomWasmBinaryUri:a.toString()});return`<!DOCTYPE html>
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
    <script nonce="${e}" type="module" src="${i}"></script>
</body>
</html>`}}function Je(){let e="";for(let i=0;i<32;i+=1)e+="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789".charAt(Math.floor(Math.random()*62));return e}var xt=d(require("fs/promises")),E=d(require("path")),wt=d(require("vscode"));var Qt=d(require("crypto"));class mt{leaves=new Map;dirty=!1;upsert(t){let e=We(t.path),i=ze(e,t);if(this.leaves.get(e)!==i)this.leaves.set(e,i),this.dirty=!0}hasDirty(){return this.dirty}settle(t){if(!this.dirty||this.leaves.size===0)return null;let e=Qe(Array.from(this.leaves.entries()).sort((i,n)=>i[0].localeCompare(n[0])));return this.dirty=!1,{reason:t,rootHash:e,leafCount:this.leaves.size,generatedAt:Date.now()}}}function ze(t,e){let i=[t,e.entropy.toFixed(6),e.complexity,e.debt,e.freshness.toFixed(6),e.ruffViolations,e.updatedAt].join("|");return Y(i)}function Qe(t){if(t.length===0)return Y("EMPTY");let e=t.map(([i,n])=>Y(`${i}:${n}`));while(e.length>1){let i=[];for(let n=0;n<e.length;n+=2){let s=e[n],o=e[n+1]??e[n];i.push(Y(`${s}${o}`))}e=i}return e[0]}function Y(t){return Qt.createHash("sha256").update(t,"utf8").digest("hex")}function We(t){return t.replace(/\\/g,"/")}var X=d(require("path")),ft=require("child_process"),Z=d(require("vscode"));function A(t,e){let i="",n=(s)=>{let o=s.trim();if(!o)return;try{let a=JSON.parse(o);if(!a||typeof a!=="object"||Array.isArray(a))throw Error("JSONL payload must be an object");t(a)}catch(a){e(a instanceof Error?a:Error(String(a)))}};return{push(s){i+=s.toString();while(!0){let o=i.indexOf(`
`);if(o<0)return;let a=i.slice(0,o);i=i.slice(o+1),n(a)}},flush(){if(!i.trim()){i="";return}n(i),i=""}}}class gt{output;rootPath=null;pythonSidecar=null;rubySidecar=null;onDidReceiveRuffEmitter=new Z.EventEmitter;onDidReceiveRuff=this.onDidReceiveRuffEmitter.event;onDidReceiveLoreEmitter=new Z.EventEmitter;onDidReceiveLore=this.onDidReceiveLoreEmitter.event;onDidReceiveSidecarErrorEmitter=new Z.EventEmitter;onDidReceiveSidecarError=this.onDidReceiveSidecarErrorEmitter.event;constructor(t){this.output=t}start(t){this.rootPath=t,this.startPythonSidecar(),this.startRubySidecar()}requestScan(t){if(!this.pythonSidecar||this.pythonSidecar.killed)this.startPythonSidecar();this.writeJson(this.pythonSidecar,t)}requestLore(t){if(!this.rubySidecar||this.rubySidecar.killed)this.startRubySidecar();this.writeJson(this.rubySidecar,t)}dispose(){this.pythonSidecar?.kill(),this.rubySidecar?.kill(),this.pythonSidecar=null,this.rubySidecar=null,this.onDidReceiveRuffEmitter.dispose(),this.onDidReceiveLoreEmitter.dispose(),this.onDidReceiveSidecarErrorEmitter.dispose()}startPythonSidecar(){if(!this.rootPath||this.pythonSidecar)return;let t=X.join(this.rootPath,".chthonic","python","entropy_scan.py"),e=X.join(this.rootPath,".chthonic","venv",process.platform==="win32"?"Scripts/python.exe":"bin/python");this.pythonSidecar=ft.spawn("uv",["run","--python",e,t,"--stdio"],{cwd:this.rootPath,stdio:["pipe","pipe","pipe"]});let i=A((n)=>this.handlePythonPayload(n),(n)=>this.output.appendLine(`[polyglot:python] invalid JSONL payload: ${n.message}`));this.pythonSidecar.stdout?.on("data",(n)=>i.push(n)),this.pythonSidecar.stderr?.on("data",(n)=>{this.output.appendLine(`[polyglot:python] ${n.toString().trimEnd()}`)}),this.pythonSidecar.on("error",(n)=>{this.onDidReceiveSidecarErrorEmitter.fire({type:"error",source:"python",message:n.message}),this.output.appendLine(`[polyglot:python] failed to spawn: ${n.message}`),this.pythonSidecar=null}),this.pythonSidecar.on("exit",(n)=>{i.flush(),this.output.appendLine(`[polyglot:python] exited with code ${n??-1}`),this.pythonSidecar=null})}startRubySidecar(){if(!this.rootPath||this.rubySidecar)return;let t=X.join(this.rootPath,".chthonic","ruby","lore.rb");this.rubySidecar=ft.spawn("ruby",[t],{cwd:this.rootPath,stdio:["pipe","pipe","pipe"]});let e=A((i)=>this.handleRubyPayload(i),(i)=>this.output.appendLine(`[polyglot:ruby] invalid JSONL payload: ${i.message}`));this.rubySidecar.stdout?.on("data",(i)=>e.push(i)),this.rubySidecar.stderr?.on("data",(i)=>{this.output.appendLine(`[polyglot:ruby] ${i.toString().trimEnd()}`)}),this.rubySidecar.on("error",(i)=>{this.onDidReceiveSidecarErrorEmitter.fire({type:"error",source:"ruby",message:i.message}),this.output.appendLine(`[polyglot:ruby] failed to spawn: ${i.message}`),this.rubySidecar=null}),this.rubySidecar.on("exit",(i)=>{e.flush(),this.output.appendLine(`[polyglot:ruby] exited with code ${i??-1}`),this.rubySidecar=null})}writeJson(t,e){if(!t?.stdin||t.killed)return;try{t.stdin.write(`${JSON.stringify(e)}
`)}catch(i){this.output.appendLine(`[polyglot] sidecar write failed: ${Ge(i)}`)}}handlePythonPayload(t){if(t.type==="ruff-summary"){let e=t;this.onDidReceiveRuffEmitter.fire(e);return}if(t.type==="error"){let e=String(t.message??"python sidecar error");this.output.appendLine(`[polyglot:python] ${e}`),this.onDidReceiveSidecarErrorEmitter.fire({type:"error",source:"python",message:e})}}handleRubyPayload(t){if(t.type==="lore"){this.onDidReceiveLoreEmitter.fire(t);return}if(t.type==="error"){let e=String(t.message??"ruby sidecar error");this.output.appendLine(`[polyglot:ruby] ${e}`),this.onDidReceiveSidecarErrorEmitter.fire({type:"error",source:"ruby",message:e})}}}function Ge(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}var Wt=d(require("fs")),tt=d(require("fs/promises")),R=d(require("path")),yt=require("child_process");class vt{output;rootPath=null;options={rpcUrl:"http://127.0.0.1:8899",autostartValidator:!1};ledgerFilePath=null;validatorProcess=null;hostProcess=null;requestCounter=1;pending=new Map;constructor(t){this.output=t}async start(t,e){this.rootPath=t,this.options=e;let i=R.join(t,".chthonic","ledger");if(await tt.mkdir(i,{recursive:!0}),this.ledgerFilePath=R.join(i,"entropy-settlements.jsonl"),e.autostartValidator)this.startValidator();this.startHostProcess()}async commitEntropy(t){if(!this.rootPath||!this.ledgerFilePath)return{mode:"offline",detail:"Ledger host not started"};let e={...t,rpcUrl:this.options.rpcUrl,recordedAt:Date.now()},i={mode:"offline",detail:"Rust ledger host unavailable; persisted settlement locally."};try{i=await this.submitToHost(t)}catch(n){this.output.appendLine(`[ledger-rust] submit failed: ${Ze(n)}`)}return await tt.appendFile(this.ledgerFilePath,`${JSON.stringify({...e,receipt:i})}
`,"utf8"),i}dispose(){for(let[t,e]of this.pending)e.reject(Error(`request ${t} cancelled`));this.pending.clear(),this.hostProcess?.kill(),this.hostProcess=null,this.validatorProcess?.kill(),this.validatorProcess=null}startHostProcess(){if(!this.rootPath||this.hostProcess)return;let t=Ke(this.rootPath,this.options.hostBinaryPath),e=this.options.walletPath??R.join(this.rootPath,".chthonic","wallets","payer.json"),i=this.options.idlPath??R.join(this.rootPath,".chthonic","wallets","entropy_ledger.json");this.hostProcess=yt.spawn(t,["--wallet",e,"--idl",i,"--rpc-url",this.options.rpcUrl],{cwd:this.rootPath,stdio:["pipe","pipe","pipe"]});let n=A((s)=>this.handleHostPayload(s),(s)=>this.output.appendLine(`[ledger-rust] invalid JSON payload: ${s.message}`));this.hostProcess.stdout?.on("data",(s)=>n.push(s)),this.hostProcess.stderr?.on("data",(s)=>{this.output.appendLine(`[ledger-rust] ${s.toString().trimEnd()}`)}),this.hostProcess.on("error",(s)=>{this.output.appendLine(`[ledger-rust] failed to spawn host: ${s.message}`),this.rejectAllPending(Error(`host spawn failed: ${s.message}`)),this.hostProcess=null}),this.hostProcess.on("exit",(s)=>{n.flush(),this.output.appendLine(`[ledger-rust] host exited with code ${s??-1}`),this.rejectAllPending(Error("ledger host exited")),this.hostProcess=null})}async submitToHost(t){if(!this.hostProcess||this.hostProcess.killed)this.startHostProcess();if(!this.hostProcess?.stdin||this.hostProcess.killed)return{mode:"offline",detail:"Rust host binary is missing or not executable."};let e=this.requestCounter++,i={jsonrpc:"2.0",id:e,method:"submit_entropy",params:{entropy_score:Math.max(0,Math.round(t.leafCount*17+13)),merkle_root:t.rootHash,leaf_count:t.leafCount,reason:t.reason}};return await new Promise((s,o)=>{this.pending.set(e,{resolve:s,reject:o}),this.hostProcess?.stdin?.write(`${JSON.stringify(i)}
`,(a)=>{if(!a)return;this.pending.delete(e),o(a)})})}handleHostPayload(t){let e=t.id;if(typeof e!=="number")return;let i=this.pending.get(e);if(!i)return;if(this.pending.delete(e),t.error&&typeof t.error==="object"){let s=t;i.resolve({mode:"offline",detail:`Rust ledger error ${s.error.code}: ${s.error.message}`});return}let n=t;i.resolve({mode:"validator-rust",txSignature:n.result.signature,detail:`Rust anchor-client submission accepted${n.result.slot?` (slot ${n.result.slot})`:""}.`})}rejectAllPending(t){for(let[e,i]of this.pending)this.pending.delete(e),i.reject(t)}startValidator(){if(!this.rootPath||this.validatorProcess)return;let t=Ye(this.rootPath),e=Xe(this.options.rpcUrl)??8899,i=R.join(this.rootPath,".chthonic","solana-ledger");this.validatorProcess=yt.spawn(t,["--ledger",i,"--rpc-port",String(e),"--reset","--quiet"],{cwd:this.rootPath,stdio:["ignore","pipe","pipe"]}),this.validatorProcess.stdout?.on("data",(n)=>{this.output.appendLine(`[solana] ${n.toString().trimEnd()}`)}),this.validatorProcess.stderr?.on("data",(n)=>{this.output.appendLine(`[solana] ${n.toString().trimEnd()}`)}),this.validatorProcess.on("error",(n)=>{this.output.appendLine(`[solana] validator spawn error: ${n.message}`),this.validatorProcess=null}),this.validatorProcess.on("exit",(n)=>{this.output.appendLine(`[solana] validator exited with code ${n??-1}`),this.validatorProcess=null})}}function Ke(t,e){if(e)return e;let i=process.platform==="win32"?"entropy-ledger-host.exe":"entropy-ledger-host";return R.join(t,"native","target","release",i)}function Ye(t){let e=process.platform==="win32"?"solana-test-validator.exe":"solana-test-validator",i=R.join(t,".chthonic","bin",e);if(Wt.existsSync(i))return i;return process.platform==="win32"?"solana-test-validator":e}function Xe(t){try{let e=new URL(t);if(!e.port)return null;let i=Number(e.port);return Number.isFinite(i)?i:null}catch{return null}}function Ze(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}class bt{output;options;backend=null;constructor(t,e){this.output=t;this.options=e}async start(t){this.backend=this.options.mode==="bankrun"?new Gt(this.output):new Kt(this.output,this.options),await this.backend.start(t)}async commitEntropy(t){if(!this.backend)return{mode:"offline",detail:"LedgerBroker backend not initialized."};return this.backend.commitEntropy(t)}dispose(){this.backend?.dispose(),this.backend=null}}class Gt{output;sequence=0;constructor(t){this.output=t}async start(t){this.output.appendLine("[ledger] phantom mode active (bankrun simulation).")}async commitEntropy(t){return this.sequence+=1,{mode:"bankrun",txSignature:`bankrun-${t.rootHash.slice(0,20)}-${this.sequence}`,detail:"In-memory bankrun simulation accepted the entropy settlement."}}dispose(){}}class Kt{options;client;constructor(t,e){this.options=e;this.client=new vt(t)}async start(t){await this.client.start(t,{rpcUrl:this.options.rpcUrl,autostartValidator:this.options.autostartValidator,hostBinaryPath:this.options.hostBinaryPath,walletPath:this.options.walletPath,idlPath:this.options.idlPath})}async commitEntropy(t){return this.client.commitEntropy(t)}dispose(){this.client.dispose()}}class St{output;workerClient;options;requestDecorationRefresh;broker;merkle=new mt;ledger;tooltipAugments=new Map;rootPath=null;scanTimer=null;settleTimer=null;gitPollTimer=null;gitHeadSnapshot=null;pendingSettleReason=null;disposables=[];constructor(t,e,i,n){this.output=t;this.workerClient=e;this.options=i;this.requestDecorationRefresh=n;this.broker=new gt(t),this.ledger=new bt(t,{mode:this.options.ledgerMode,rpcUrl:this.options.solanaRpcUrl,autostartValidator:this.options.solanaAutostartValidator,hostBinaryPath:this.options.solanaLedgerHostBinaryPath,walletPath:this.options.solanaWalletPath,idlPath:this.options.solanaIdlPath}),this.disposables.push(this.broker.onDidReceiveRuff((s)=>this.applyRuffSummary(s.files)),this.broker.onDidReceiveLore((s)=>this.applyLore(s)),this.workerClient.onDidUpdateRecords((s)=>this.captureEntropyLeaves(s)))}async start(t){if(this.rootPath=t,!this.options.enabled)return;this.broker.start(t),await this.ledger.start(t),this.broker.requestScan({type:"scan",reason:"manual",root:t}),this.startScanLoop(),this.startGitWatcher()}onDidSaveDocument(t){if(!this.rootPath||!this.options.enabled||t.uri.scheme!=="file")return;let e=Yt(this.rootPath,t.uri.fsPath);if(!e)return;this.broker.requestScan({type:"scan",reason:"save",root:this.rootPath,files:[e]}),this.scheduleSettlement("save")}requestManualScan(){if(!this.rootPath||!this.options.enabled)return;this.broker.requestScan({type:"scan",reason:"manual",root:this.rootPath})}getTooltipFragments(t){if(!this.rootPath||t.scheme!=="file")return[];let e=Yt(this.rootPath,t.fsPath);if(!e)return[];let i=this.tooltipAugments.get(e);if(!i)return[];let n=[];if(i.ruffViolations>0)n.push(`Ruff ${i.ruffViolations} violation${i.ruffViolations===1?"":"s"}`);if(i.loreLine)n.push(i.loreLine);return n}dispose(){if(this.scanTimer)clearInterval(this.scanTimer),this.scanTimer=null;if(this.settleTimer)clearTimeout(this.settleTimer),this.settleTimer=null;if(this.gitPollTimer)clearInterval(this.gitPollTimer),this.gitPollTimer=null;this.broker.dispose(),this.ledger.dispose(),this.disposables.forEach((t)=>t.dispose()),this.disposables.length=0}captureEntropyLeaves(t){if(!this.options.enabled)return;for(let e of t){let i=this.workerClient.getRecord(e);if(!i)continue;let n=this.tooltipAugments.get(i.path);this.merkle.upsert({path:i.path,entropy:i.entropy,complexity:i.complexity,debt:i.debt,freshness:i.freshness,ruffViolations:n?.ruffViolations??0,updatedAt:Date.now()})}}applyRuffSummary(t){if(!this.rootPath||!this.options.enabled)return;let e=[];for(let i of t){let n=this.tooltipAugments.get(i.path),s={ruffViolations:i.violations,loreLine:n?.loreLine};this.tooltipAugments.set(i.path,s);let o=wt.Uri.file(E.join(this.rootPath,i.path));e.push(o);let a=this.workerClient.getRecord(o);if(a){if(this.merkle.upsert({path:a.path,entropy:a.entropy,complexity:a.complexity,debt:a.debt,freshness:a.freshness,ruffViolations:i.violations,updatedAt:Date.now()}),a.entropy>=0.45||i.violations>0)this.broker.requestLore({type:"lore-request",root:this.rootPath,path:i.path,entropy:a.entropy,violations:i.violations})}}if(e.length>0)this.requestDecorationRefresh(e)}applyLore(t){if(!this.rootPath||!this.options.enabled)return;if(t.root!==this.rootPath)return;let e=this.tooltipAugments.get(t.path);this.tooltipAugments.set(t.path,{ruffViolations:e?.ruffViolations??t.violations,loreLine:t.line}),this.requestDecorationRefresh([wt.Uri.file(E.join(this.rootPath,t.path))])}startScanLoop(){if(this.scanTimer||!this.rootPath)return;let t=Math.max(this.options.pythonScanIntervalMs,1e4);this.scanTimer=setInterval(()=>{if(!this.rootPath)return;this.broker.requestScan({type:"scan",reason:"interval",root:this.rootPath})},t)}startGitWatcher(){if(!this.rootPath||this.gitPollTimer)return;this.gitHeadSnapshot=null,this.gitPollTimer=setInterval(async()=>{if(!this.rootPath)return;let t=await ti(this.rootPath);if(!t)return;if(!this.gitHeadSnapshot){this.gitHeadSnapshot=t;return}if(t!==this.gitHeadSnapshot){if(this.gitHeadSnapshot=t,this.output.appendLine("[polyglot] git HEAD changed, scheduling Merkle settlement."),this.rootPath)this.broker.requestScan({type:"scan",reason:"commit",root:this.rootPath});this.scheduleSettlement("commit")}},6000)}scheduleSettlement(t){if(!this.options.enabled)return;if(this.pendingSettleReason=t==="commit"?"commit":this.pendingSettleReason??t,this.settleTimer)clearTimeout(this.settleTimer);this.settleTimer=setTimeout(()=>{this.settleTimer=null,this.flushSettlement()},Math.max(this.options.settleDebounceMs,300))}async flushSettlement(){let t=this.pendingSettleReason??"manual";this.pendingSettleReason=null;let e=this.merkle.settle(t);if(!e)return;let i=await this.ledger.commitEntropy(e),n=[`[polyglot] settled Merkle root ${e.rootHash.slice(0,16)}...`,`leaves=${e.leafCount}`,`mode=${i.mode}`];if(i.txSignature)n.push(`tx=${i.txSignature}`);n.push(`detail=${i.detail}`),this.output.appendLine(n.join(" "))}}async function ti(t){let e=E.join(t,".git"),i=E.join(e,"HEAD"),n="";try{n=await xt.readFile(i,"utf8")}catch{return null}let s=n.trim();if(!s)return null;if(!s.startsWith("ref:"))return s;let o=s.slice(4).trim(),a=E.join(e,o);try{let l=await xt.readFile(a,"utf8");return`ref:${o}:${l.trim()}`}catch{return`ref:${o}:missing`}}function Yt(t,e){let i=E.relative(t,e);if(!i||i.startsWith("..")||E.isAbsolute(i))return null;return i.replace(/\\/g,"/")}var Xt=d(require("path")),Zt=require("child_process"),M=d(require("vscode"));class kt{output;headlessVulkan;daemonBinaryOverride;eolApiBase;entropyMonitorIntervalMs;rootPath=null;daemonProcess=null;requestCounter=1;pending=new Map;onDidReceiveManifestEmitter=new M.EventEmitter;onDidReceiveManifest=this.onDidReceiveManifestEmitter.event;onDidReceiveEnvEmitter=new M.EventEmitter;onDidReceiveEnv=this.onDidReceiveEnvEmitter.event;onDidReceiveSedimentEmitter=new M.EventEmitter;onDidReceiveSediment=this.onDidReceiveSedimentEmitter.event;onDidReceiveSedimentChunkEmitter=new M.EventEmitter;onDidReceiveSedimentChunk=this.onDidReceiveSedimentChunkEmitter.event;onDidReceiveSynapseEmitter=new M.EventEmitter;onDidReceiveSynapse=this.onDidReceiveSynapseEmitter.event;onDidReceiveEntropyStateEmitter=new M.EventEmitter;onDidReceiveEntropyState=this.onDidReceiveEntropyStateEmitter.event;onDidReceiveFiredancerSurgeEmitter=new M.EventEmitter;onDidReceiveFiredancerSurge=this.onDidReceiveFiredancerSurgeEmitter.event;constructor(t,e,i,n="https://endoflife.date/api/v1",s=21600000){this.output=t;this.headlessVulkan=e;this.daemonBinaryOverride=i;this.eolApiBase=n;this.entropyMonitorIntervalMs=s}start(t){this.rootPath=t,this.startDaemon()}async requestSediment(t,e){return this.submitRequest("reactor/sediment",{max_layers:t,max_files:e})}async requestSedimentStream(t,e,i=220){return this.submitRequest("reactor/sediment_stream",{max_layers:t,max_files:e,chunk_size:i})}async requestSedimentSynapse(t,e,i=220){return this.submitRequest("reactor/sediment_synapse",{max_layers:t,max_files:e,chunk_size:i})}async requestDetect(){return this.submitRequest("anno/detect",{})}async requestProvision(){return this.submitRequest("anno/provision",{})}async requestEntropyState(){return this.submitRequest("reactor/entropy_state",{})}dispose(){for(let[,t]of this.pending)t.reject(Error("AnnoClient disposed"));this.pending.clear(),this.daemonProcess?.kill(),this.daemonProcess=null,this.onDidReceiveManifestEmitter.dispose(),this.onDidReceiveEnvEmitter.dispose(),this.onDidReceiveSedimentEmitter.dispose(),this.onDidReceiveSedimentChunkEmitter.dispose(),this.onDidReceiveSynapseEmitter.dispose(),this.onDidReceiveEntropyStateEmitter.dispose(),this.onDidReceiveFiredancerSurgeEmitter.dispose()}startDaemon(){if(!this.rootPath||this.daemonProcess)return;let t=this.daemonBinaryOverride??ei(this.rootPath),e=["--workspace",this.rootPath];if(this.headlessVulkan)e.push("--headless-vulkan");this.daemonProcess=Zt.spawn(t,e,{cwd:this.rootPath,env:{...process.env,CHTHONIC_EOL_API_BASE:this.eolApiBase,CHTHONIC_ENTROPY_MONITOR_INTERVAL_MS:String(Math.max(60000,this.entropyMonitorIntervalMs))},stdio:["pipe","pipe","pipe"]});let i=A((n)=>this.handlePayload(n),(n)=>this.output.appendLine(`[daemon] invalid JSONL: ${n.message}`));this.daemonProcess.stdout?.on("data",(n)=>i.push(n)),this.daemonProcess.stderr?.on("data",(n)=>{this.output.appendLine(`[daemon] ${n.toString().trimEnd()}`)}),this.daemonProcess.on("error",(n)=>{this.output.appendLine(`[daemon] spawn failed: ${n.message}`),this.rejectAllPending(Error(`daemon spawn failed: ${n.message}`)),this.daemonProcess=null}),this.daemonProcess.on("exit",(n)=>{i.flush(),this.output.appendLine(`[daemon] exited with code ${n??-1}`),this.rejectAllPending(Error("daemon exited")),this.daemonProcess=null})}handlePayload(t){if("method"in t&&!("id"in t)){this.handleNotification(t);return}if("id"in t&&typeof t.id==="number")this.handleResponse(t)}handleNotification(t){let{method:e,params:i}=t;switch(e){case"anno/manifest":this.onDidReceiveManifestEmitter.fire(i),this.output.appendLine(`[daemon] ANNO manifest received (${i.languages?.length??0} languages)`);break;case"anno/env":this.onDidReceiveEnvEmitter.fire(i),this.output.appendLine("[daemon] env report received");break;case"reactor/status":{let n=i.status??"unknown";this.output.appendLine(`[daemon] reactor status: ${n}`);break}case"reactor/sedimentChunk":this.onDidReceiveSedimentChunkEmitter.fire(i);break;case"reactor/synapse":this.onDidReceiveSynapseEmitter.fire(i),this.output.appendLine(`[daemon] synapse status: ${i.status} (${i.mode})`);break;case"reactor/entropyState":this.onDidReceiveEntropyStateEmitter.fire(i),this.output.appendLine(`[daemon] entropy state: ${i.status} (${Math.round((i.decay_score??0)*100)}%)`);break;case"reactor/firedancerSurge":this.onDidReceiveFiredancerSurgeEmitter.fire(i),this.output.appendLine(`[daemon] firedancer slot ${i.slot} tps ${i.simulated_tps} (${i.surge?"surge":"flow"})`);break;default:this.output.appendLine(`[daemon] unknown notification: ${e}`)}}handleResponse(t){let e=t.id,i=this.pending.get(e);if(!i)return;if(this.pending.delete(e),t.error&&typeof t.error==="object"){let n=t.error;i.reject(Error(n.message));return}i.resolve(t.result)}submitRequest(t,e){if(!this.daemonProcess?.stdin||this.daemonProcess.killed)this.startDaemon();if(!this.daemonProcess?.stdin)return Promise.reject(Error("daemon not available"));let i=this.requestCounter++,n={jsonrpc:"2.0",id:i,method:t,params:e};return new Promise((s,o)=>{this.pending.set(i,{resolve:s,reject:o}),this.daemonProcess?.stdin?.write(`${JSON.stringify(n)}
`,(a)=>{if(a)this.pending.delete(i),o(a)})})}rejectAllPending(t){for(let[e,i]of this.pending)this.pending.delete(e),i.reject(t)}}function ei(t){let e=process.platform==="win32"?"chthonic-daemon.exe":"chthonic-daemon";return Xt.join(t,"native","target","release",e)}var $=d(require("vscode"));class Et{output;envCollection;disposed=!1;constructor(t,e){this.output=t;this.envCollection=e}async activate(){if(this.disposed)return;try{await $.commands.executeCommand("workbench.action.closeSidebar"),await $.commands.executeCommand("workbench.action.terminal.moveToSidePanel"),await $.commands.executeCommand("workbench.action.toggleAuxiliaryBar"),await $.commands.executeCommand("workbench.action.toggleMaximizedPanel"),await $.commands.executeCommand("workbench.action.focusActiveEditorGroup"),this.output.appendLine("[cockpit] layout activated: sidebar=closed, terminal=AuxBar, panel=maximized, editor=Center")}catch(t){this.output.appendLine(`[cockpit] layout activation failed: ${ii(t)}`)}}applyTerminalEnv(t){if(this.disposed)return;if(!t.path_mutations.length)return;let e=t.path_mutations.sort((n,s)=>n.priority-s.priority).map((n)=>n.path),i=process.platform==="win32"?";":":";for(let n of e)this.envCollection.prepend("PATH",`${n}${i}`);for(let n of $.window.terminals)if(process.platform==="win32")for(let s of e)n.sendText(`$env:PATH = "${s};$env:PATH"`,!0);else for(let s of e)n.sendText(`export PATH="${s}:$PATH"`,!0);if(this.output.appendLine(`[cockpit] terminal env updated: ${e.length} PATH mutations applied`),t.warnings.length>0)for(let n of t.warnings)this.output.appendLine(`[cockpit] warning: ${n}`)}dispose(){this.disposed=!0}}function ii(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}var ee=d(require("fs")),Pt=d(require("path"));class SynapseBridge{output;extensionRoot;binding=null;reader=null;descriptor=null;transportMode;constructor(t,e,i){this.output=t;this.extensionRoot=e;this.transportMode=ni(i)}updateDescriptor(t){if(this.descriptor=t,this.transportMode==="jsonl"){this.output.appendLine("[synapse] disabled by transport=jsonl");return}if(t.status!=="ready"||t.mode!=="shared_memory"||!t.shm_id){this.output.appendLine(`[synapse] unavailable: ${t.reason??t.status}`);return}try{let e=this.ensureBindingLoaded();this.reader=new e.SynapseReader(t.shm_id,t.event_name??void 0),this.output.appendLine(`[synapse] connected (shm=${t.shm_id})`)}catch(e){this.reader=null,this.output.appendLine(`[synapse] init failed, falling back to JSONL: ${si(e)}`)}}isReady(){if(this.transportMode==="jsonl")return!1;return this.reader!==null&&this.descriptor?.status==="ready"&&this.descriptor.mode==="shared_memory"}async drain(t,e){if(!this.reader||t.transport!=="shared_memory")return 0;let i=Math.max(0,t.chunks_written??t.total_chunks??0);if(i===0)return 0;let n=0,s=Date.now();while(n<i&&Date.now()-s<4000){if(!this.reader.wait_for_signal(120)){await te();continue}while(!0){let a=this.reader.read_chunk();if(!a||a.byteLength===0)break;let l=new Uint8Array(a.buffer,a.byteOffset,a.byteLength),h=new Uint8Array(l.byteLength);if(h.set(l),e(h),n+=1,n>=i)break}await te()}if(n<i)this.output.appendLine(`[synapse] partial drain: ${n}/${i}`);return n}dispose(){this.reader=null}ensureBindingLoaded(){if(this.binding)return this.binding;let candidates=[Pt.join(this.extensionRoot,"src","reactor","synapse.node"),Pt.join(this.extensionRoot,"native","target","release","synapse.node")],existing=candidates.find((t)=>ee.existsSync(t));if(!existing)throw Error(`synapse.node not found in ${candidates.join(", ")}`);let req=eval("require");return this.binding=req(existing),this.binding}}function ni(t){let e=t.trim().toLowerCase();if(e==="shared_memory")return"shared_memory";if(e==="jsonl")return"jsonl";return"auto"}function si(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}async function te(){await new Promise((t)=>setTimeout(t,0))}var x=d(require("vscode"));var ie=d(require("fs")),ne=d(require("path")),oi=[{file:"mise.toml",weight:16},{file:".mise.toml",weight:6},{file:"Cargo.toml",weight:20},{file:"native/Cargo.toml",weight:8},{file:"anno-manifest.toml",weight:8},{file:"uv.lock",weight:10},{file:".python-version",weight:5},{file:".ruby-version",weight:10},{file:"Gemfile",weight:6},{file:"go.mod",weight:10},{file:".node-version",weight:4},{file:".nvmrc",weight:4},{file:"package.json",weight:5},{file:"bun.lock",weight:4}];async function se(t){let e=oi.map((s)=>{let o=ne.join(t,s.file),a=ie.existsSync(o);return{...s,present:a}}),i=Math.min(100,e.reduce((s,o)=>o.present?s+o.weight:s,0)),n=ri(i);return{score:i,tier:n,markers:e,present:e.filter((s)=>s.present).map((s)=>s.file),missing:e.filter((s)=>!s.present).map((s)=>s.file)}}function oe(t){switch(t){case"loom":return"loom.svg";case"lens":return"lens.svg";default:return"gate.svg"}}function ri(t){if(t>=80)return"loom";if(t>=45)return"lens";return"gate"}class Lt{extensionUri;output;containerId;fallbackItem;proposalAvailable=null;latestRustification=null;latestEntropy=null;constructor(t,e,i="chthonic-archive"){this.extensionUri=t;this.output=e;this.containerId=i;this.fallbackItem=x.window.createStatusBarItem(x.StatusBarAlignment.Left,47),this.fallbackItem.command="chthonic.refreshRustification",this.fallbackItem.tooltip="Rustification score and activity bar icon fallback",this.fallbackItem.show()}async update(t){this.latestRustification=t,await x.commands.executeCommand("setContext","chthonic.rustificationTier",t.tier),await x.commands.executeCommand("setContext","chthonic.rustificationScore",t.score),await this.apply()}async updateEntropy(t){this.latestEntropy=t,await x.commands.executeCommand("setContext","chthonic.decayStatus",t.status),await x.commands.executeCommand("setContext","chthonic.decayScore",Math.round(t.decay_score*100)),await this.apply()}dispose(){this.fallbackItem.dispose()}async apply(){let t=this.resolveIconFile(),e=x.Uri.joinPath(this.extensionUri,"resources",t);if(!await this.tryApplyProposedIcon(e))this.updateFallbackStatus();else this.fallbackItem.text=this.fallbackSummary(),this.fallbackItem.backgroundColor=void 0}resolveIconFile(){let t=this.latestEntropy;if(t){if(t.decay_score>0.5||t.status==="critical")return"hazard.svg";if(t.decay_score<0.2&&t.status==="pristine")return"gate.svg";return"lens.svg"}let e=this.latestRustification?.tier??"gate";return oe(e)}async tryApplyProposedIcon(t){if(this.proposalAvailable===!1)return!1;let e=x.window,i=["setActivityBarIcon","updateActivityBarIcon","setViewContainerIcon","updateViewContainerIcon"];for(let n of i){let s=e[n];if(typeof s!=="function")continue;try{return await s(this.containerId,t),this.proposalAvailable=!0,!0}catch(o){this.output.appendLine(`[morph] ${n} failed: ${ci(o)}`)}}return this.proposalAvailable=!1,!1}updateFallbackStatus(){let t=this.latestRustification,e=this.latestEntropy;if(!t){this.fallbackItem.text="$(pulse) Slab boot",this.fallbackItem.tooltip="Rustification score pending";return}let i=ai(t.tier),n=e?Math.round(e.decay_score*100):null,s=e?`${e.status} ${n}%`:"unknown";this.fallbackItem.text=`$(pulse) ${i} ${t.score}% · Decay ${n??"?"}%`,this.fallbackItem.tooltip=[`Rustification ${t.score}% (${t.tier})`,`Decay ${s}`,`Present: ${t.present.join(", ")||"none"}`,`Missing: ${t.missing.join(", ")||"none"}`,e&&e.critical_tools.length>0?`Critical tools: ${e.critical_tools.join(", ")}`:void 0].filter(Boolean).join(`
`)}fallbackSummary(){let t=this.latestRustification,e=this.latestEntropy,i=t?`${t.score}%`:"?",n=e?`${Math.round(e.decay_score*100)}%`:"?";return`$(pulse) Slab ${i} · Decay ${n}`}}function ai(t){switch(t){case"loom":return"Loom";case"lens":return"Lens";default:return"Gate"}}function ci(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}var C=d(require("vscode"));class Rt{output;constructor(t){this.output=t}async activate(){let t=await this.tryProposedLayout();if(!t)await this.applyCommandFallback();await C.commands.executeCommand("workbench.view.extension.chthonic-archive"),await C.commands.executeCommand("chthonic.loomView.focus"),this.output.appendLine(`[deep-focus] activated via ${t?"proposed-api":"command-fallback"} lane`)}async tryProposedLayout(){let t=C.window,e=t.moveViewTo;if(typeof e!=="function")return!1;let i=[t.ViewContainerLocation&&t.ViewContainerLocation.AuxiliaryBar,"auxiliaryBar","secondarySidebar"];for(let n of i){if(!n)continue;try{return await e("terminal",n),!0}catch(s){this.output.appendLine(`[deep-focus] proposed moveViewTo failed: ${re(s)}`)}}return!1}async applyCommandFallback(){try{await C.commands.executeCommand("workbench.action.terminal.moveToSidePanel"),await C.commands.executeCommand("workbench.action.toggleAuxiliaryBar"),await C.commands.executeCommand("workbench.action.focusActiveEditorGroup")}catch(t){this.output.appendLine(`[deep-focus] fallback layout failed: ${re(t)}`)}}}function re(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}var F=d(require("vscode")),di="chthonic.statusView",li="chthonic.loomView";class Mt{output;constructor(t){this.output=t}async activate(){let t=await this.tryProposedLayout();if(!t)await this.applyCommandFallback();await F.commands.executeCommand("workbench.view.extension.chthonic-archive"),this.output.appendLine(`[restore-order] completed via ${t?"proposed-api":"command-fallback"} lane`)}async tryProposedLayout(){let t=F.window,e=t.moveViewTo;if(typeof e!=="function")return!1;let i=t.ViewContainerLocation,n=ae([i?.AuxiliaryBar,i?.SecondarySideBar,"auxiliaryBar","secondarySidebar"]),s=ae([i?.Panel,"panel"]);for(let o of n)for(let a of s)try{return await e(di,o),await e(li,a),!0}catch(l){this.output.appendLine(`[restore-order] proposed moveViewTo failed: ${ce(l)}`)}return!1}async applyCommandFallback(){await pi(this.output,[["workbench.view.extension.chthonic-archive"],["chthonic.statusView.focus"],["workbench.action.moveFocusedViewToSecondarySidebar"],["chthonic.loomView.focus"],["workbench.action.moveFocusedViewToPanel"],["workbench.action.positionPanelBottom"],["workbench.action.focusActiveEditorGroup"]])}}async function pi(t,e){for(let i of e){let[n,...s]=i;try{await F.commands.executeCommand(n,...s)}catch(o){t.appendLine(`[restore-order] command failed (${n}): ${ce(o)}`)}}}function ae(t){return t.filter((e)=>e!==void 0&&e!==null)}function ce(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}var U=d(require("vscode"));class et{static viewType="chthonic.loomView";view=null;report=null;resolveWebviewView(t,e,i){this.view=t,t.webview.options={enableScripts:!0},t.webview.html=this.buildHtml(),t.webview.onDidReceiveMessage((n)=>{if(!n||typeof n!=="object")return;let s=n;if(s.type==="refresh")U.commands.executeCommand("chthonic.refreshRustification");if(s.type==="heal")U.commands.executeCommand("chthonic.slabHeal");if(s.type==="deepFocus")U.commands.executeCommand("chthonic.deepFocus");if(s.type==="restoreOrder")U.commands.executeCommand("chthonic.restoreOrder")}),this.postState()}update(t){this.report=t,this.postState()}dispose(){this.view=null}postState(){if(!this.view||!this.report)return;this.view.webview.postMessage({type:"state",report:this.report})}buildHtml(){let t=ui();return`<!DOCTYPE html>
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
</html>`}}function ui(){let e="";for(let i=0;i<24;i+=1)e+="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789".charAt(Math.floor(Math.random()*62));return e}var m=d(require("fs")),f=d(require("path")),it=d(require("child_process")),pe=d(require("vscode"));class Ct{output;envCollection;workspaceRoot;timer=null;running=!1;options={intervalMs:21600000,eolApiBase:"https://endoflife.date/api"};constructor(t,e,i){this.output=t;this.envCollection=e;this.workspaceRoot=i}start(t){this.options=t,this.stopTimer(),this.timer=setInterval(()=>{this.runNow("interval")},Math.max(60000,t.intervalMs))}async runNow(t="manual"){if(this.running){this.output.appendLine("[slab-heal] skipped; already running");return}this.running=!0;try{let e=await this.auditVsToolchain();if(e&&(!e.allRequiredComponentsPresent||!e.allCriticalBinariesPresent))this.output.appendLine(`[slab-heal] vs2026 audit drift detected: components=${e.missingComponentCount}, binaries=${e.missingBinaryCount}`);let i=await this.collectRuntimeStates();if(i.length===0){this.output.appendLine("[slab-heal] no runtime states detected; skipping");return}let n=[];for(let s of i)if(await this.isEol(s.language,s.version))n.push(s);if(n.length===0){this.output.appendLine(`[slab-heal] ${t}: all slab runtimes are supported`);return}this.output.appendLine(`[slab-heal] ${t}: stale runtimes detected: ${n.map((s)=>`${s.language}@${s.version}`).join(", ")}`),await this.repair(n)}catch(e){this.output.appendLine(`[slab-heal] run failed: ${N(e)}`)}finally{this.running=!1}}dispose(){this.stopTimer()}stopTimer(){if(this.timer)clearInterval(this.timer),this.timer=null}async collectRuntimeStates(){let t=[{language:"python",command:"python",args:["-c",'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")']},{language:"ruby",command:"ruby",args:["-e","print RUBY_VERSION"]},{language:"go",command:"go",args:["env","GOVERSION"]},{language:"rust",command:"rustc",args:["--version"]},{language:"solana",command:"solana",args:["--version"]}],e=[];for(let n of t)try{let s=await O(n.command,n.args,this.workspaceRoot),o=gi(s,n.language);if(!o)continue;e.push({language:n.language,version:o})}catch(s){this.output.appendLine(`[slab-heal] probe ${n.language} failed: ${N(s)}`)}let i=await mi(this.workspaceRoot);if(i)e.push({language:"visual-studio",version:i});else this.output.appendLine("[slab-heal] probe visual-studio failed: VS 2026 Insiders not detected");return e}async isEol(t,e){let i=await this.fetchCycles(t);if(!i||!Array.isArray(i))return!1;let n=yi(t,e),s=i.find((a)=>{let l=a;return l.cycle===n||l.cycle===n.split(".").slice(0,1).join(".")});if(!s||s.eol==null)return!1;if(typeof s.eol==="boolean")return s.eol;let o=Date.parse(s.eol);if(Number.isNaN(o))return!1;return o<=Date.now()}async fetchCycles(t){let e=vi(t);for(let i of e){let n=await fetch(`${this.options.eolApiBase}/${i}.json`,{headers:{accept:"application/json"}});if(!n.ok)continue;let s=await n.json();if(Array.isArray(s))return s}return this.output.appendLine(`[slab-heal] endoflife feed unavailable for ${t}; skipping lifecycle gate`),null}async repair(t){if(await fi("mise",this.workspaceRoot))await $t("mise",["upgrade"],this.workspaceRoot,this.output),await $t("mise",["reshim"],this.workspaceRoot,this.output);else this.output.appendLine("[slab-heal] mise not found on PATH; skipped upgrade/reshim");await this.refreshToolpoolSnapshot();let i=await this.relinkVsHeaders();if(i)this.output.appendLine(`[slab-heal] relinked MSVC headers at ${i}`);else this.output.appendLine("[slab-heal] VS include relink skipped (MSVC path not found)");pe.window.showInformationMessage(`Chthonic self-heal complete: ${t.map((n)=>`${n.language}@${n.version}`).join(", ")}`)}async relinkVsHeaders(){let t=await hi(this.workspaceRoot);if(!t||!this.workspaceRoot)return null;let e=f.join(this.workspaceRoot,".chthonic","native","msvc"),i=f.join(e,"include");m.mkdirSync(e,{recursive:!0});try{m.rmSync(i,{recursive:!0,force:!0})}catch{}try{m.symlinkSync(t,i,"junction")}catch(n){let s=f.join(e,"include.path.txt");m.writeFileSync(s,t,"utf8"),this.output.appendLine(`[slab-heal] symlink failed; wrote include manifest ${s}: ${N(n)}`)}return this.envCollection.replace("CHTHONIC_VS_CPP_INCLUDE",t),this.envCollection.prepend("INCLUDE",`${t};`),t}async auditVsToolchain(){let t=de(this.workspaceRoot);if(!t)return null;let e=f.join(t,"scripts","vs2026_audit.ps1");if(!m.existsSync(e))return null;try{let i=await O("pwsh",["-NoProfile","-File",e,"-Json"],t);return JSON.parse(i).summary??null}catch(i){return this.output.appendLine(`[slab-heal] vs2026 audit script failed: ${N(i)}`),null}}async refreshToolpoolSnapshot(){let t=de(this.workspaceRoot);if(!t)return;let e=f.join(t,"scripts","toolpool-scan.ts");if(!m.existsSync(e))return;try{await $t("bun",["run","scripts/toolpool-scan.ts","--write-env","--quiet"],t,this.output),this.output.appendLine("[slab-heal] tool-pool snapshot refreshed")}catch(i){this.output.appendLine(`[slab-heal] tool-pool snapshot failed: ${N(i)}`)}}}async function hi(t){let e=f.join(process.env["ProgramFiles(x86)"]||"C:\\Program Files (x86)","Microsoft Visual Studio","Installer","vswhere.exe");if(m.existsSync(e))try{let n=await O(e,["-latest","-products","*","-requires","Microsoft.VisualStudio.Component.VC.Tools.x86.x64","-property","installationPath"],t),s=le(n.trim());if(s)return s}catch{}let i=["C:\\Program Files\\Microsoft Visual Studio\\18","C:\\Program Files\\Microsoft Visual Studio\\2026","C:\\Program Files\\Microsoft Visual Studio\\2022"];for(let n of i){let s=le(n);if(s)return s}return null}function de(t){if(!t)return null;let e=f.join(t,"extensions","chthonic-archive");if(m.existsSync(f.join(e,"package.json")))return e;if(m.existsSync(f.join(t,"package.json")))return t;return null}async function mi(t){let e=f.join(process.env["ProgramFiles(x86)"]||"C:\\Program Files (x86)","Microsoft Visual Studio","Installer","vswhere.exe");if(!m.existsSync(e))return null;let i=[["-prerelease","-latest","-products","Microsoft.VisualStudio.Product.Professional","-property","installationVersion"],["-prerelease","-latest","-products","Microsoft.VisualStudio.Product.BuildTools","-property","installationVersion"]];for(let n of i)try{let o=(await O(e,n,t)).trim();if(o.length>0)return o}catch{}return null}function le(t){if(!m.existsSync(t))return null;let e=[],i=[t];while(i.length>0){let n=i.pop(),s=[];try{s=m.readdirSync(n,{withFileTypes:!0})}catch{continue}for(let o of s){let a=f.join(n,o.name);if(!o.isDirectory())continue;if(o.name==="include"&&a.includes(`${f.sep}VC${f.sep}Tools${f.sep}MSVC${f.sep}`)){e.push(a);continue}i.push(a)}}if(e.length===0)return null;return e.sort((n,s)=>s.localeCompare(n,void 0,{numeric:!0,sensitivity:"base"})),e[0]}async function O(t,e,i){return new Promise((n,s)=>{it.execFile(t,e,{cwd:i||void 0,windowsHide:!0,timeout:15000},(o,a,l)=>{if(o){s(Error(`${t} ${e.join(" ")} failed: ${l||o.message}`));return}n(String(a).trim())})})}async function fi(t,e){if(process.platform==="win32")try{return await O("where",[t],e),!0}catch{return!1}try{return await O("which",[t],e),!0}catch{return!1}}async function $t(t,e,i,n){await new Promise((s,o)=>{let a=it.spawn(t,e,{cwd:i||void 0,windowsHide:!0,stdio:["ignore","pipe","pipe"]});a.stdout.on("data",(l)=>{n.appendLine(`[slab-heal] ${l.toString().trimEnd()}`)}),a.stderr.on("data",(l)=>{n.appendLine(`[slab-heal] ${l.toString().trimEnd()}`)}),a.on("error",o),a.on("exit",(l)=>{if(l===0)s();else o(Error(`${t} ${e.join(" ")} exited with code ${l??-1}`))})})}function gi(t,e){let i=t.trim();if(!i)return"";switch(e){case"go":return i.replace(/^go/i,"");case"rust":return i.replace(/^rustc\s+/i,"").split(/\s+/)[0]??"";case"solana":return i.replace(/^solana-cli\s+/i,"").split(/\s+/)[0]??"";case"visual-studio":return i.split(/\s+/)[0]??"";default:return i}}function yi(t,e){let i=e.split(".");if(t==="go")return i.slice(0,2).join(".");if(t==="solana")return i.slice(0,1).join(".");if(t==="visual-studio")return i.slice(0,2).join(".");return i.slice(0,2).join(".")}function vi(t){switch(t){case"solana":return["solana","agave","solana-cli"];case"visual-studio":return["visual-studio"];default:return[t]}}function N(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}function bi(t){console.log("☥ Chthonic Archive extension activated");let e=c.window.createOutputChannel("Chthonic SDK"),i=c.workspace.workspaceFolders?.[0]?.uri.fsPath||null,n=J.join(i||"","meta-ide","copilot-sdk","harness.ts"),s=new G(t.extensionUri,n,(r)=>e.appendLine(`[${new Date().toISOString()}] ${r}`));t.subscriptions.push(c.window.registerWebviewViewProvider(G.viewType,s));let o=new Lt(t.extensionUri,e),a=new Rt(e),l=new Mt(e),h=new et,P=new Ct(e,t.environmentVariableCollection,i);t.subscriptions.push(o,h,P,c.window.registerWebviewViewProvider(et.viewType,h));let p=c.workspace.getConfiguration("chthonic"),g=p.get("entropy.enabled",!0),S=p.get("entropy.maxFiles",1e4),st=p.get("entropy.scanIntervalMs",20000),w=p.get("entropy.decorationDebounceMs",120),ge=p.get("entropy.decorationBatchSize",240),ye=p.get("entropy.polyglotEnabled",!0),ve=p.get("entropy.pythonScanIntervalMs",30000),be=p.get("entropy.ledgerSettleDebounceMs",1400),xe=p.get("entropy.ledgerMode","validator"),we=p.get("entropy.solanaRpcUrl","http://127.0.0.1:8899"),Se=p.get("entropy.solanaAutostartValidator",!1),ke=nt(p.get("entropy.solanaLedgerHostBinaryPath","")),Ee=nt(p.get("entropy.solanaWalletPath","")),Pe=nt(p.get("entropy.solanaIdlPath","")),k=new pt(t,e),z,T=new St(e,k,{enabled:ye,pythonScanIntervalMs:ve,settleDebounceMs:be,ledgerMode:xe,solanaRpcUrl:we,solanaAutostartValidator:Se,solanaLedgerHostBinaryPath:ke,solanaWalletPath:Ee,solanaIdlPath:Pe},(r)=>z?.enqueueExternalUpdates(r));z=new ht(k,w,ge,(r)=>T.getTooltipFragments(r));let B=new K(t.extensionUri,k);B.setRootPath(i),t.subscriptions.push(k,z,B,T,c.window.registerFileDecorationProvider(z),c.window.registerWebviewViewProvider(K.viewType,B));let I=async(r)=>{if(!i)return;let u=await se(i);h.update(u),await o.update(u),e.appendLine(`[monolith] rustification ${u.score}% (${u.tier}) via ${r}`)};if(i){I("startup");let r=c.workspace.createFileSystemWatcher(new c.RelativePattern(i,"{uv.lock,Cargo.toml,native/Cargo.toml,mise.toml,.mise.toml,anno-manifest.toml,go.mod,.ruby-version,Gemfile,.node-version,.nvmrc,package.json,bun.lock,.python-version}"));t.subscriptions.push(r,r.onDidCreate(()=>{I("marker-create")}),r.onDidChange(()=>{I("marker-change")}),r.onDidDelete(()=>{I("marker-delete")}))}if(i&&g)k.start(i,S,st),T.start(i);t.subscriptions.push(c.workspace.onDidSaveTextDocument((r)=>{k.refreshFile(r.uri),T.onDidSaveDocument(r)})),t.subscriptions.push(c.commands.registerCommand("chthonic.entropyRefresh",()=>{k.rescanNow(),k.requestGraph(260),T.requestManualScan(),c.window.showInformationMessage("Chthonic entropy scan requested")}));let Le=p.get("reactor.enabled",!0),Re=p.get("reactor.headlessVulkan",!0),Me=p.get("reactor.cockpitAutoLayout",!1),$e=p.get("reactor.transport","auto"),Ce=nt(p.get("reactor.daemonBinaryPath","")),Be=p.get("slab.selfHealingEnabled",!0),At=p.get("slab.selfHealingIntervalMs",21600000),Dt=p.get("slab.eolApiBase","https://endoflife.date/api"),Ae=Si(Dt),De=Math.max(60000,Math.floor(At/2)),y=new kt(e,Re,Ce,Ae,De),Q=new Et(e,t.environmentVariableCollection),ot=new SynapseBridge(e,t.extensionPath,$e),rt=null,at=null,j=null,Tt=(r,u)=>{let L=u?`${r} (${u.toLocaleString()} tps)`:r;e.appendLine(`[loom-reflex] panel lane ${L}`),l.activate()},Te=(r)=>{e.appendLine(`[loom-reflex] primary lane ${r}`),c.commands.executeCommand("workbench.view.extension.chthonic-archive"),c.commands.executeCommand("chthonic.loomView.focus")};t.subscriptions.push(y,Q,ot);let It=(r)=>{if(o.updateEntropy(r),e.appendLine(`[lens] decay ${Math.round(r.decay_score*100)}% (${r.status}) from ${r.source_mise??"no-mise"}`),r.validator_active){let v=`${r.validator_process??"validator"}:${r.validator_source_mise}`;if(v!==at)at=v,Te(`validator-online:${v}`)}else at=null;if(r.firedancer_surge&&r.validator_active){let v=`${r.checked_at_epoch_ms}:${r.simulated_tps}`;if(v!==j)j=v,Tt("entropy-surge",r.simulated_tps)}else j=null;if(!r.critical||!r.auto_update_enabled){rt=null;return}let u=`${r.status}:${r.auto_update}:${[...r.critical_tools].sort().join(",")}`;if(u===rt)return;rt=u;let L=r.critical_tools.length>0?r.critical_tools.join(", "):"runtime toolchain";c.window.showWarningMessage(`Chthonic decay is critical (${Math.round(r.decay_score*100)}%). ${L} needs healing.`,"Run mise upgrade","Later").then((v)=>{if(v==="Run mise upgrade")P.runNow("manual")})};if(t.subscriptions.push(y.onDidReceiveEnv((r)=>{Q.applyTerminalEnv(r)}),y.onDidReceiveSediment((r)=>{B.postSedimentData(r)}),y.onDidReceiveSedimentChunk((r)=>{B.postSedimentChunk(r)}),y.onDidReceiveSynapse((r)=>{ot.updateDescriptor(r)}),y.onDidReceiveEntropyState((r)=>{It(r)}),y.onDidReceiveFiredancerSurge((r)=>{if(r.surge){let u=`${r.slot}:${r.simulated_tps}`;if(u!==j)j=u,Tt("daemon-surge",r.simulated_tps)}})),B.onRequestSediment(()=>{wi(y,B,ot,e)}),i&&Le){if(y.start(i),y.requestEntropyState().then((u)=>{It(u)}).catch((u)=>{e.appendLine(`[lens] initial entropy snapshot unavailable: ${u}`)}),Me)Q.activate();let r=J.join(i,".git","HEAD");if(D.existsSync(r)){let u=null,L=D.watch(J.join(i,".git"),{persistent:!1},(v,Ot)=>{if(Ot==="HEAD"||Ot?.startsWith("refs")){if(u)clearTimeout(u);u=setTimeout(()=>{e.appendLine("[reactor] git change detected, recomputing sediment"),y.requestSediment(10,500).catch((Ie)=>{e.appendLine(`[reactor] live-loop sediment failed: ${Ie}`)})},800)}});t.subscriptions.push({dispose:()=>L.close()})}}if(i&&Be)P.start({intervalMs:At,eolApiBase:Dt}),P.runNow("interval");t.subscriptions.push(c.commands.registerCommand("chthonic.activateCockpit",()=>{Q.activate()}),c.commands.registerCommand("chthonic.deepFocus",()=>{a.activate()}),c.commands.registerCommand("chthonic.restoreOrder",()=>{l.activate()}),c.commands.registerCommand("chthonic.slabHeal",()=>{P.runNow("manual")}),c.commands.registerCommand("chthonic.refreshRustification",()=>{I("manual-command")}),c.commands.registerCommand("chthonic.annoDetect",()=>{if(i)y.start(i);c.window.showInformationMessage("ANNO project detection triggered")}),c.commands.registerCommand("chthonic.reactorSediment",async()=>{try{let r=await y.requestSediment(10,500);c.window.showInformationMessage(`Sediment computed: ${r.file_count} files, ${r.layer_count} layers (${r.backend}, ${r.compute_time_ms}ms)`)}catch(r){c.window.showErrorMessage(`Sediment computation failed: ${r}`)}}));let ct=new me;c.window.registerTreeDataProvider("chthonic.themeView",ct),t.subscriptions.push(c.commands.registerCommand("chthonic.switchTheme",async()=>{let r=[{label:"$(paintcan) Flesh & Earth",description:"Warm earth · WCAG AA · Distribution palette",id:"Chthonic Mandala - Flesh & Earth"},{label:"$(zap) ROGBIV",description:"SSOT spectral · FA¹⁻⁵ canonical hexes",id:"Chthonic Mandala - ROGBIV"}],u=c.workspace.getConfiguration("workbench").get("colorTheme"),L=await c.window.showQuickPick(r.map((v)=>({...v,picked:u===v.id})),{placeHolder:`Current: ${u}`});if(L)await c.workspace.getConfiguration("workbench").update("colorTheme",L.id,c.ConfigurationTarget.Workspace),c.window.showInformationMessage(`Theme: ${L.id}`),ct.refresh()}));let _t=c.workspace.getConfiguration("chthonic");if(_t.get("showSSOTHash",!0)){let r=c.window.createStatusBarItem(c.StatusBarAlignment.Left,50);r.command="chthonic.verifySSOT",r.tooltip="SSOT integrity hash — click to verify",t.subscriptions.push(r),ue(r),t.subscriptions.push(c.workspace.onDidSaveTextDocument((u)=>{if(u.fileName.includes("copilot-instructions"))ue(r)}))}if(_t.get("showLineage",!0)){let r=c.window.createStatusBarItem(c.StatusBarAlignment.Left,49);r.text="$(git-branch) ☥ main",r.tooltip="Chthonic lineage",r.show(),t.subscriptions.push(r)}let Vt=new fe;c.window.registerTreeDataProvider("chthonic.statusView",Vt),t.subscriptions.push(c.commands.registerCommand("chthonic.verifySSOT",async()=>{let r=Bt();if(r)c.window.showInformationMessage(`SSOT SHA-256: ${r.substring(0,16)}…`);else c.window.showWarningMessage("SSOT file not found")})),t.subscriptions.push(c.commands.registerCommand("chthonic.refreshStatus",()=>{Vt.refresh(),ct.refresh(),k.rescanNow(),k.requestGraph(260),T.requestManualScan(),I("refresh-status")}))}function xi(){}async function wi(t,e,i,n){try{if(i.isReady()){let s=await t.requestSedimentSynapse(10,500,220);if(s.transport==="shared_memory"){let o=await i.drain(s,(a)=>{e.postSedimentBinary(a)});n.appendLine(`[reactor] synapse drain ${o}/${s.chunks_written} chunks`);return}}await t.requestSedimentStream(10,500)}catch(s){n.appendLine(`[reactor] sediment request failed: ${s}`)}}function Bt(){let t=c.workspace.workspaceFolders?.[0];if(!t)return null;let e=c.workspace.getConfiguration("chthonic").get("ssotPath",".github/copilot-instructions.md"),i=J.join(t.uri.fsPath,e);if(!D.existsSync(i))return null;let s=D.readFileSync(i,"utf-8").replace(/\r\n/g,`
`).replace(/\r/g,`
`).split(`
`).map((o)=>o.trimEnd()).join(`
`).trim();return he.createHash("sha256").update(s,"utf-8").digest("hex")}function ue(t){let e=Bt();if(e)t.text=`$(shield) ${e.substring(0,8)}`,t.show();else t.text="$(shield) SSOT ??",t.show()}function nt(t){let e=t.trim();return e.length>0?e:void 0}function Si(t){let e=t.trim().replace(/\/+$/,"");if(e.endsWith("/api"))return`${e}/v1`;return e.length>0?e:"https://endoflife.date/api/v1"}class me{_onDidChange=new c.EventEmitter;onDidChangeTreeData=this._onDidChange.event;refresh(){this._onDidChange.fire()}getTreeItem(t){return t}getChildren(){let t=c.workspace.getConfiguration("workbench").get("colorTheme")||"";return[{name:"Chthonic Mandala - Flesh & Earth",short:"Flesh & Earth",icon:"\uD83C\uDF0D",desc:"Warm earth · Distribution"},{name:"Chthonic Mandala - ROGBIV",short:"ROGBIV",icon:"\uD83C\uDF08",desc:"SSOT spectral · Research"}].map((i)=>{let n=t===i.name,s=new c.TreeItem(`${n?"◉":"○"} ${i.icon} ${i.short}`,c.TreeItemCollapsibleState.None);return s.tooltip=`${i.name}
${i.desc}${n?`

✅ ACTIVE`:""}`,s.description=n?"active":"",s.command={command:"chthonic.switchTheme",title:"Switch"},s})}}class fe{_onDidChange=new c.EventEmitter;onDidChangeTreeData=this._onDidChange.event;refresh(){this._onDidChange.fire()}getTreeItem(t){return t}getChildren(){let t=Bt(),e=[],i=new c.TreeItem(`$(shield) SSOT: ${t?t.substring(0,12)+"…":"not found"}`,c.TreeItemCollapsibleState.None);i.command={command:"chthonic.verifySSOT",title:"Verify"},e.push(i);let n=new c.TreeItem(`$(paintcan) Theme: ${(c.workspace.getConfiguration("workbench").get("colorTheme")||"default").replace("Chthonic Mandala - ","")}`,c.TreeItemCollapsibleState.None);return n.command={command:"chthonic.switchTheme",title:"Switch"},e.push(n),e}}
