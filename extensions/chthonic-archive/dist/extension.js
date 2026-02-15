var Ct=Object.create;var{getPrototypeOf:Dt,defineProperty:S,getOwnPropertyNames:dt,getOwnPropertyDescriptor:At}=Object,lt=Object.prototype.hasOwnProperty;var l=(t,e,s)=>{s=t!=null?Ct(Dt(t)):{};let o=e||!t||!t.__esModule?S(s,"default",{value:t,enumerable:!0}):s;for(let r of dt(t))if(!lt.call(o,r))S(o,r,{get:()=>t[r],enumerable:!0});return o},at=new WeakMap,Bt=(t)=>{var e=at.get(t),s;if(e)return e;if(e=S({},"__esModule",{value:!0}),t&&typeof t==="object"||typeof t==="function")dt(t).map((o)=>!lt.call(e,o)&&S(e,o,{get:()=>t[o],enumerable:!(s=At(t,o))||s.enumerable}));return at.set(t,e),e};var $t=(t,e)=>{for(var s in e)S(t,s,{get:e[s],enumerable:!0,configurable:!0,set:(o)=>e[s]=()=>o})};var Kt={};$t(Kt,{deactivate:()=>Gt,activate:()=>Qt});module.exports=Bt(Kt);var n=l(require("vscode")),kt=l(require("crypto")),H=l(require("fs")),st=l(require("path"));var ht=l(require("vscode")),V=l(require("child_process"));var ct=l(require("child_process")),pt=l(require("readline")),C=l(require("path"));class q{harnessPath;log;process=null;rl=null;handlers=new Set;authenticated=!1;ready=!1;constructor(t,e){this.harnessPath=t;this.log=e}async start(){if(this.process)return;let t=C.dirname(this.harnessPath),e=C.basename(this.harnessPath);this.process=ct.spawn("bun",["run",e],{cwd:t,stdio:["pipe","pipe","pipe"],env:{...process.env}}),this.process.stderr?.on("data",(s)=>{this.log(`[harness stderr] ${s.toString().trim()}`)}),this.process.on("close",(s)=>{this.log(`[harness] exited with code ${s}`),this.process=null,this.rl=null,this.ready=!1,this.authenticated=!1}),this.rl=pt.createInterface({input:this.process.stdout}),this.rl.on("line",(s)=>{try{let o=JSON.parse(s);if(o.type==="ready")this.ready=!0,this.log(`[harness] ready: ${o.sdk}`);for(let r of this.handlers)r(o)}catch{this.log(`[harness] non-JSON: ${s.substring(0,200)}`)}}),await new Promise((s,o)=>{let r=setTimeout(()=>o(Error("Harness startup timeout")),15000),i=(a)=>{if(a.type==="ready")clearTimeout(r),this.handlers.delete(i),s()};this.handlers.add(i)})}async authenticate(t,e){this.send({cmd:"auth",token:t,login:e}),await this.waitFor("auth_ok"),this.authenticated=!0,this.log(`[harness] authenticated as ${e}`)}query(t,e,s,o,r){return new Promise((i,a)=>{let h=(c)=>{if(c.id!==t)return;if(c.type==="event"&&c.event)o(c.event);else if(c.type==="done")this.handlers.delete(h),i();else if(c.type==="cancelled")this.handlers.delete(h),i();else if(c.type==="error")this.handlers.delete(h),a(Error(c.message||"Query failed"))};this.handlers.add(h),this.send({cmd:"query",id:t,prompt:e,workingDirectory:s,model:r?.model,reasoningEffort:r?.reasoningEffort})})}cancel(t){this.send({cmd:"cancel",id:t})}async getModels(){return this.send({cmd:"models"}),(await this.waitFor("models")).data||[]}isReady(){return this.ready&&this.authenticated&&this.process!==null}stop(){if(this.process)this.process.kill(),this.process=null;this.rl=null,this.ready=!1,this.authenticated=!1,this.handlers.clear()}send(t){if(!this.process?.stdin?.writable)throw Error("Harness not running");this.process.stdin.write(JSON.stringify(t)+`
`)}waitFor(t,e=15000){return new Promise((s,o)=>{let r=setTimeout(()=>{this.handlers.delete(i),o(Error(`Timeout waiting for ${t}`))},e),i=(a)=>{if(a.type===t)clearTimeout(r),this.handlers.delete(i),s(a);else if(a.type==="error")clearTimeout(r),this.handlers.delete(i),o(Error(a.message||"Error"))};this.handlers.add(i)})}}class D{extensionUri;harnessPath;log;static viewType="chthonic.chatView";view;connection=null;isConnecting=!1;activeQueryId=null;constructor(t,e,s){this.extensionUri=t;this.harnessPath=e;this.log=s}resolveWebviewView(t,e,s){this.view=t,t.webview.options={enableScripts:!0,localResourceRoots:[this.extensionUri]},t.webview.html=this.getHtml(),t.webview.onDidReceiveMessage(async(o)=>{switch(o.type){case"connect":await this.connectAgent();break;case"prompt":await this.sendPrompt(o.text);break;case"cancel":this.cancelQuery();break;case"disconnect":this.disconnectAgent();break}})}async connectAgent(){if(this.isConnecting||this.connection?.isReady())return;this.isConnecting=!0,this.postMessage({type:"status",status:"connecting"});try{this.connection=new q(this.harnessPath,this.log),await this.connection.start();let t=V.execSync("gh auth token",{encoding:"utf-8"}).trim(),e=V.execSync("gh api user --jq .login",{encoding:"utf-8"}).trim();await this.connection.authenticate(t,e),this.postMessage({type:"connected",agentName:"Chthonic SDK",agentVersion:"0.1.0",login:e}),this.log(`Chat connected: ${e}`)}catch(t){this.log(`Chat connect failed: ${t.message}`),this.postMessage({type:"error",message:t.message}),this.connection?.stop(),this.connection=null}finally{this.isConnecting=!1}}async sendPrompt(t){if(!this.connection?.isReady()){this.postMessage({type:"error",message:"Not connected"});return}let e=crypto.randomUUID();this.activeQueryId=e,this.postMessage({type:"prompt-start"});let s=ht.workspace.workspaceFolders?.[0]?.uri.fsPath||process.cwd();try{await this.connection.query(e,t,s,(o)=>this.handleSdkEvent(o))}catch(o){this.postMessage({type:"error",message:o.message})}finally{this.activeQueryId=null,this.postMessage({type:"prompt-end"})}}handleSdkEvent(t){switch(t.type){case"assistant.message":if(t.data?.content)this.postMessage({type:"agent-message",content:t.data.content});break;case"assistant.message.delta":if(t.data?.delta)this.postMessage({type:"agent-delta",delta:t.data.delta});break;case"tool.execution_start":this.postMessage({type:"tool-start",name:t.data?.name,args:t.data?.arguments});break;case"tool.execution_complete":this.postMessage({type:"tool-end",name:t.data?.name});break;case"assistant.reasoning":this.postMessage({type:"reasoning"});break;case"assistant.usage":this.postMessage({type:"usage",model:t.data?.model,inputTokens:t.data?.inputTokens,outputTokens:t.data?.outputTokens,duration:t.data?.duration});break;case"session.usage_info":this.postMessage({type:"context-info",tokenLimit:t.data?.tokenLimit,currentTokens:t.data?.currentTokens});break}}cancelQuery(){if(this.activeQueryId&&this.connection)this.connection.cancel(this.activeQueryId)}disconnectAgent(){this.connection?.stop(),this.connection=null,this.activeQueryId=null,this.postMessage({type:"disconnected"})}postMessage(t){this.view?.webview.postMessage(t)}dispose(){this.connection?.stop()}getHtml(){return`<!DOCTYPE html>
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
</html>`}}var E=l(require("path")),x=l(require("vscode")),ut=require("worker_threads");class N{extensionContext;output;records=new Map;recordUris=new Map;onDidUpdateRecordsEmitter=new x.EventEmitter;onDidUpdateRecords=this.onDidUpdateRecordsEmitter.event;onDidUpdateGraphEmitter=new x.EventEmitter;onDidUpdateGraph=this.onDidUpdateGraphEmitter.event;onDidUpdateSnapshotEmitter=new x.EventEmitter;onDidUpdateSnapshot=this.onDidUpdateSnapshotEmitter.event;worker=null;rootPath=null;workerPath;maxFiles=1e4;lastScanDurationMs=0;lastScanAt=0;scanTimer=null;disposed=!1;constructor(t,e){this.extensionContext=t;this.output=e;this.workerPath=t.asAbsolutePath(E.join("dist","entropy-worker.js"))}start(t,e,s){this.rootPath=t,this.maxFiles=e,this.ensureWorker(),this.send({type:"scan",root:t,maxFiles:this.maxFiles}),this.scheduleScanLoop(s)}rescanNow(){if(!this.rootPath)return;this.send({type:"scan",root:this.rootPath,maxFiles:this.maxFiles})}refreshFile(t){if(!this.rootPath||t.scheme!=="file")return;this.send({type:"refresh-file",root:this.rootPath,path:t.fsPath})}requestGraph(t){this.send({type:"graph",limit:t})}getRecord(t){if(!this.rootPath||t.scheme!=="file")return;let e=Tt(E.relative(this.rootPath,t.fsPath));return this.records.get(e)}getSnapshot(t=40){let e=Array.from(this.records.values()),s=e.length===0?0:e.reduce((r,i)=>r+i.entropy,0)/e.length,o=e.sort((r,i)=>i.entropy-r.entropy).slice(0,t);return{totalFiles:e.length,topEntropy:o,averageEntropy:s,lastScanDurationMs:this.lastScanDurationMs,lastScanAt:this.lastScanAt}}dispose(){if(this.disposed=!0,this.scanTimer)clearInterval(this.scanTimer),this.scanTimer=null;this.send({type:"stop"}),this.worker?.terminate(),this.worker=null,this.onDidUpdateRecordsEmitter.dispose(),this.onDidUpdateGraphEmitter.dispose(),this.onDidUpdateSnapshotEmitter.dispose()}scheduleScanLoop(t){if(this.scanTimer)clearInterval(this.scanTimer);let e=Math.max(5000,t);this.scanTimer=setInterval(()=>{if(!this.disposed)this.rescanNow()},e)}ensureWorker(){if(this.worker)return;this.worker=new ut.Worker(this.workerPath),this.worker.on("message",(t)=>this.handleWorkerEvent(t)),this.worker.on("error",(t)=>{this.output.appendLine(`[entropy] worker error: ${t.message}`)}),this.worker.on("exit",(t)=>{if(this.output.appendLine(`[entropy] worker exited with code ${t}`),this.worker=null,!this.disposed&&t!==0)this.ensureWorker(),this.rescanNow()})}send(t){this.ensureWorker(),this.worker?.postMessage(t)}handleWorkerEvent(t){switch(t.type){case"scan-progress":{if(!this.rootPath)return;let e=[];for(let s of t.records){this.records.set(s.path,s);let o=this.recordUris.get(s.path);if(!o)o=x.Uri.file(E.join(this.rootPath,s.path)),this.recordUris.set(s.path,o);e.push(o)}if(e.length>0)this.onDidUpdateRecordsEmitter.fire(e);break}case"scan-complete":this.lastScanDurationMs=t.durationMs,this.lastScanAt=Date.now(),this.onDidUpdateSnapshotEmitter.fire(this.getSnapshot());break;case"graph-result":this.onDidUpdateGraphEmitter.fire(t.graph);break;case"error":this.output.appendLine(`[entropy] ${t.message}${t.detail?`
${t.detail}`:""}`);break}}}function Tt(t){return t.replace(/\\/g,"/")}var gt=l(require("vscode"));class F{workerClient;debounceMs;maxPerFlush;tooltipAugmentProvider;onDidChangeEmitter=new gt.EventEmitter;onDidChangeFileDecorations=this.onDidChangeEmitter.event;pending=new Map;flushTimer=null;constructor(t,e,s,o){this.workerClient=t;this.debounceMs=e;this.maxPerFlush=s;this.tooltipAugmentProvider=o;this.workerClient.onDidUpdateRecords((r)=>this.enqueueUpdates(r))}dispose(){if(this.flushTimer)clearTimeout(this.flushTimer),this.flushTimer=null;this.onDidChangeEmitter.dispose()}updateConfig(t,e){this.debounceMs=Math.max(30,t),this.maxPerFlush=Math.max(64,e)}provideFileDecoration(t){if(t.scheme!=="file")return;let e=this.workerClient.getRecord(t);if(!e)return;let s=Ut(e),o=[`Entropy ${(e.entropy*100).toFixed(0)}%`,`Complexity ${e.complexity}`,`Debt ${e.debt}`,`Freshness ${(e.freshness*100).toFixed(0)}%`];if(this.tooltipAugmentProvider)o.push(...this.tooltipAugmentProvider(t));return{color:s,tooltip:o.join(`
`),propagate:!1}}enqueueExternalUpdates(t){this.enqueueUpdates(t)}enqueueUpdates(t){for(let e of t)this.pending.set(e.toString(),e);if(!this.flushTimer)this.flushTimer=setTimeout(()=>this.flush(),this.debounceMs)}flush(){if(this.flushTimer=null,this.pending.size===0)return;let t=Array.from(this.pending.values()).slice(0,this.maxPerFlush);for(let e of t)this.pending.delete(e.toString());if(this.onDidChangeEmitter.fire(t),this.pending.size>0)this.flushTimer=setTimeout(()=>this.flush(),this.debounceMs)}}function Ut(t){let e=jt(t.entropy*0.78+(1-t.freshness)*0.22),s=z(118,24,e),o=z(36,46,e),r=z(58,42,e);return Ht(s,o,r)}function Ht(t,e,s){let o=t/360,r=e/100,i=s/100,a=(p,g,j)=>{let u=j;if(u<0)u+=1;if(u>1)u-=1;if(u<0.16666666666666666)return p+(g-p)*6*u;if(u<0.5)return g;if(u<0.6666666666666666)return p+(g-p)*(0.6666666666666666-u)*6;return p},h,c,w;if(r===0)h=i,c=i,w=i;else{let p=i<0.5?i*(1+r):i+r-i*r,g=2*i-p;h=a(g,p,o+0.3333333333333333),c=a(g,p,o),w=a(g,p,o-0.3333333333333333)}let P=(p)=>{return Math.round(p*255).toString(16).padStart(2,"0")};return`#${P(h)}${P(c)}${P(w)}`}function jt(t){if(t<0)return 0;if(t>1)return 1;return t}function z(t,e,s){return t+(e-t)*s}var k=l(require("path")),y=l(require("vscode"));class A{extensionUri;workerClient;static viewType="chthonic.abyssalView";disposables=[];view=null;rootPath=null;constructor(t,e){this.extensionUri=t;this.workerClient=e;this.disposables.push(this.workerClient.onDidUpdateGraph((s)=>this.postMessage({type:"graph",graph:s})),this.workerClient.onDidUpdateSnapshot((s)=>this.postMessage({type:"snapshot",snapshot:s})))}setRootPath(t){this.rootPath=t}dispose(){this.disposables.forEach((t)=>t.dispose()),this.disposables.length=0}resolveWebviewView(t,e,s){this.view=t,t.webview.options={enableScripts:!0,localResourceRoots:[this.extensionUri]},t.webview.html=this.getHtml(t.webview),t.webview.onDidReceiveMessage((o)=>{this.handleMessage(o)})}handleMessage(t){if(!t||typeof t!=="object")return;let e=t;if(!e.type)return;if(e.type==="ready"){this.postMessage({type:"snapshot",snapshot:this.workerClient.getSnapshot()}),this.workerClient.requestGraph(260);return}if(e.type==="requestGraph"){this.workerClient.requestGraph(260);return}if(e.type==="openFile"&&e.path&&this.rootPath){let s=k.normalize(e.path);if(s.startsWith("..")||k.isAbsolute(s))return;let o=k.join(this.rootPath,s),r=y.Uri.file(o);y.workspace.openTextDocument(r).then((i)=>{y.window.showTextDocument(i,{preview:!1})},()=>{y.window.showWarningMessage(`Unable to open ${e.path}`)})}}postMessage(t){if(!this.view)return;this.view.webview.postMessage(t)}getHtml(t){let e=_t(),s=t.asWebviewUri(y.Uri.joinPath(this.extensionUri,"media","abyssalPane.js")),o=t.asWebviewUri(y.Uri.joinPath(this.extensionUri,"media","wasm","pkg","entropy_renderer_wasm.js")),r=t.asWebviewUri(y.Uri.joinPath(this.extensionUri,"media","wasm","pkg","entropy_renderer_wasm_bg.wasm")),i=["default-src 'none'",`img-src ${t.cspSource} data:`,`style-src ${t.cspSource} 'unsafe-inline'`,`script-src 'nonce-${e}' ${t.cspSource}`,`connect-src ${t.cspSource}`].join("; "),a=JSON.stringify({wasmModuleUri:o.toString(),wasmBinaryUri:r.toString()});return`<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="${i}">
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
</html>`}}function _t(){let e="";for(let s=0;s<32;s+=1)e+="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789".charAt(Math.floor(Math.random()*62));return e}var X=l(require("fs/promises")),f=l(require("path")),Z=l(require("vscode"));var mt=l(require("crypto"));class J{leaves=new Map;dirty=!1;upsert(t){let e=qt(t.path),s=Ot(e,t);if(this.leaves.get(e)!==s)this.leaves.set(e,s),this.dirty=!0}hasDirty(){return this.dirty}settle(t){if(!this.dirty||this.leaves.size===0)return null;let e=Wt(Array.from(this.leaves.entries()).sort((s,o)=>s[0].localeCompare(o[0])));return this.dirty=!1,{reason:t,rootHash:e,leafCount:this.leaves.size,generatedAt:Date.now()}}}function Ot(t,e){let s=[t,e.entropy.toFixed(6),e.complexity,e.debt,e.freshness.toFixed(6),e.ruffViolations,e.updatedAt].join("|");return B(s)}function Wt(t){if(t.length===0)return B("EMPTY");let e=t.map(([s,o])=>B(`${s}:${o}`));while(e.length>1){let s=[];for(let o=0;o<e.length;o+=2){let r=e[o],i=e[o+1]??e[o];s.push(B(`${r}${i}`))}e=s}return e[0]}function B(t){return mt.createHash("sha256").update(t,"utf8").digest("hex")}function qt(t){return t.replace(/\\/g,"/")}var $=l(require("path")),I=require("child_process"),T=l(require("vscode"));function R(t,e){let s="",o=(r)=>{let i=r.trim();if(!i)return;try{let a=JSON.parse(i);if(!a||typeof a!=="object"||Array.isArray(a))throw Error("JSONL payload must be an object");t(a)}catch(a){e(a instanceof Error?a:Error(String(a)))}};return{push(r){s+=r.toString();while(!0){let i=s.indexOf(`
`);if(i<0)return;let a=s.slice(0,i);s=s.slice(i+1),o(a)}},flush(){if(!s.trim()){s="";return}o(s),s=""}}}class Q{output;rootPath=null;pythonSidecar=null;rubySidecar=null;onDidReceiveRuffEmitter=new T.EventEmitter;onDidReceiveRuff=this.onDidReceiveRuffEmitter.event;onDidReceiveLoreEmitter=new T.EventEmitter;onDidReceiveLore=this.onDidReceiveLoreEmitter.event;onDidReceiveSidecarErrorEmitter=new T.EventEmitter;onDidReceiveSidecarError=this.onDidReceiveSidecarErrorEmitter.event;constructor(t){this.output=t}start(t){this.rootPath=t,this.startPythonSidecar(),this.startRubySidecar()}requestScan(t){if(!this.pythonSidecar||this.pythonSidecar.killed)this.startPythonSidecar();this.writeJson(this.pythonSidecar,t)}requestLore(t){if(!this.rubySidecar||this.rubySidecar.killed)this.startRubySidecar();this.writeJson(this.rubySidecar,t)}dispose(){this.pythonSidecar?.kill(),this.rubySidecar?.kill(),this.pythonSidecar=null,this.rubySidecar=null,this.onDidReceiveRuffEmitter.dispose(),this.onDidReceiveLoreEmitter.dispose(),this.onDidReceiveSidecarErrorEmitter.dispose()}startPythonSidecar(){if(!this.rootPath||this.pythonSidecar)return;let t=$.join(this.rootPath,".chthonic","python","entropy_scan.py"),e=$.join(this.rootPath,".chthonic","venv",process.platform==="win32"?"Scripts/python.exe":"bin/python");this.pythonSidecar=I.spawn("uv",["run","--python",e,t,"--stdio"],{cwd:this.rootPath,stdio:["pipe","pipe","pipe"]});let s=R((o)=>this.handlePythonPayload(o),(o)=>this.output.appendLine(`[polyglot:python] invalid JSONL payload: ${o.message}`));this.pythonSidecar.stdout?.on("data",(o)=>s.push(o)),this.pythonSidecar.stderr?.on("data",(o)=>{this.output.appendLine(`[polyglot:python] ${o.toString().trimEnd()}`)}),this.pythonSidecar.on("error",(o)=>{this.onDidReceiveSidecarErrorEmitter.fire({type:"error",source:"python",message:o.message}),this.output.appendLine(`[polyglot:python] failed to spawn: ${o.message}`),this.pythonSidecar=null}),this.pythonSidecar.on("exit",(o)=>{s.flush(),this.output.appendLine(`[polyglot:python] exited with code ${o??-1}`),this.pythonSidecar=null})}startRubySidecar(){if(!this.rootPath||this.rubySidecar)return;let t=$.join(this.rootPath,".chthonic","ruby","lore.rb");this.rubySidecar=I.spawn("ruby",[t],{cwd:this.rootPath,stdio:["pipe","pipe","pipe"]});let e=R((s)=>this.handleRubyPayload(s),(s)=>this.output.appendLine(`[polyglot:ruby] invalid JSONL payload: ${s.message}`));this.rubySidecar.stdout?.on("data",(s)=>e.push(s)),this.rubySidecar.stderr?.on("data",(s)=>{this.output.appendLine(`[polyglot:ruby] ${s.toString().trimEnd()}`)}),this.rubySidecar.on("error",(s)=>{this.onDidReceiveSidecarErrorEmitter.fire({type:"error",source:"ruby",message:s.message}),this.output.appendLine(`[polyglot:ruby] failed to spawn: ${s.message}`),this.rubySidecar=null}),this.rubySidecar.on("exit",(s)=>{e.flush(),this.output.appendLine(`[polyglot:ruby] exited with code ${s??-1}`),this.rubySidecar=null})}writeJson(t,e){if(!t?.stdin||t.killed)return;try{t.stdin.write(`${JSON.stringify(e)}
`)}catch(s){this.output.appendLine(`[polyglot] sidecar write failed: ${Vt(s)}`)}}handlePythonPayload(t){if(t.type==="ruff-summary"){let e=t;this.onDidReceiveRuffEmitter.fire(e);return}if(t.type==="error"){let e=String(t.message??"python sidecar error");this.output.appendLine(`[polyglot:python] ${e}`),this.onDidReceiveSidecarErrorEmitter.fire({type:"error",source:"python",message:e})}}handleRubyPayload(t){if(t.type==="lore"){this.onDidReceiveLoreEmitter.fire(t);return}if(t.type==="error"){let e=String(t.message??"ruby sidecar error");this.output.appendLine(`[polyglot:ruby] ${e}`),this.onDidReceiveSidecarErrorEmitter.fire({type:"error",source:"ruby",message:e})}}}function Vt(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}var yt=l(require("fs")),U=l(require("fs/promises")),v=l(require("path")),G=require("child_process");class K{output;rootPath=null;options={rpcUrl:"http://127.0.0.1:8899",autostartValidator:!1};ledgerFilePath=null;validatorProcess=null;hostProcess=null;requestCounter=1;pending=new Map;constructor(t){this.output=t}async start(t,e){this.rootPath=t,this.options=e;let s=v.join(t,".chthonic","ledger");if(await U.mkdir(s,{recursive:!0}),this.ledgerFilePath=v.join(s,"entropy-settlements.jsonl"),e.autostartValidator)this.startValidator();this.startHostProcess()}async commitEntropy(t){if(!this.rootPath||!this.ledgerFilePath)return{mode:"offline",detail:"Ledger host not started"};let e={...t,rpcUrl:this.options.rpcUrl,recordedAt:Date.now()},s={mode:"offline",detail:"Rust ledger host unavailable; persisted settlement locally."};try{s=await this.submitToHost(t)}catch(o){this.output.appendLine(`[ledger-rust] submit failed: ${Jt(o)}`)}return await U.appendFile(this.ledgerFilePath,`${JSON.stringify({...e,receipt:s})}
`,"utf8"),s}dispose(){for(let[t,e]of this.pending)e.reject(Error(`request ${t} cancelled`));this.pending.clear(),this.hostProcess?.kill(),this.hostProcess=null,this.validatorProcess?.kill(),this.validatorProcess=null}startHostProcess(){if(!this.rootPath||this.hostProcess)return;let t=Nt(this.rootPath,this.options.hostBinaryPath),e=this.options.walletPath??v.join(this.rootPath,".chthonic","wallets","payer.json"),s=this.options.idlPath??v.join(this.rootPath,".chthonic","wallets","entropy_ledger.json");this.hostProcess=G.spawn(t,["--wallet",e,"--idl",s,"--rpc-url",this.options.rpcUrl],{cwd:this.rootPath,stdio:["pipe","pipe","pipe"]});let o=R((r)=>this.handleHostPayload(r),(r)=>this.output.appendLine(`[ledger-rust] invalid JSON payload: ${r.message}`));this.hostProcess.stdout?.on("data",(r)=>o.push(r)),this.hostProcess.stderr?.on("data",(r)=>{this.output.appendLine(`[ledger-rust] ${r.toString().trimEnd()}`)}),this.hostProcess.on("error",(r)=>{this.output.appendLine(`[ledger-rust] failed to spawn host: ${r.message}`),this.rejectAllPending(Error(`host spawn failed: ${r.message}`)),this.hostProcess=null}),this.hostProcess.on("exit",(r)=>{o.flush(),this.output.appendLine(`[ledger-rust] host exited with code ${r??-1}`),this.rejectAllPending(Error("ledger host exited")),this.hostProcess=null})}async submitToHost(t){if(!this.hostProcess||this.hostProcess.killed)this.startHostProcess();if(!this.hostProcess?.stdin||this.hostProcess.killed)return{mode:"offline",detail:"Rust host binary is missing or not executable."};let e=this.requestCounter++,s={jsonrpc:"2.0",id:e,method:"submit_entropy",params:{entropy_score:Math.max(0,Math.round(t.leafCount*17+13)),merkle_root:t.rootHash,leaf_count:t.leafCount,reason:t.reason}};return await new Promise((r,i)=>{this.pending.set(e,{resolve:r,reject:i}),this.hostProcess?.stdin?.write(`${JSON.stringify(s)}
`,(a)=>{if(!a)return;this.pending.delete(e),i(a)})})}handleHostPayload(t){let e=t.id;if(typeof e!=="number")return;let s=this.pending.get(e);if(!s)return;if(this.pending.delete(e),t.error&&typeof t.error==="object"){let r=t;s.resolve({mode:"offline",detail:`Rust ledger error ${r.error.code}: ${r.error.message}`});return}let o=t;s.resolve({mode:"validator-rust",txSignature:o.result.signature,detail:`Rust anchor-client submission accepted${o.result.slot?` (slot ${o.result.slot})`:""}.`})}rejectAllPending(t){for(let[e,s]of this.pending)this.pending.delete(e),s.reject(t)}startValidator(){if(!this.rootPath||this.validatorProcess)return;let t=zt(this.rootPath),e=Ft(this.options.rpcUrl)??8899,s=v.join(this.rootPath,".chthonic","solana-ledger");this.validatorProcess=G.spawn(t,["--ledger",s,"--rpc-port",String(e),"--reset","--quiet"],{cwd:this.rootPath,stdio:["ignore","pipe","pipe"]}),this.validatorProcess.stdout?.on("data",(o)=>{this.output.appendLine(`[solana] ${o.toString().trimEnd()}`)}),this.validatorProcess.stderr?.on("data",(o)=>{this.output.appendLine(`[solana] ${o.toString().trimEnd()}`)}),this.validatorProcess.on("error",(o)=>{this.output.appendLine(`[solana] validator spawn error: ${o.message}`),this.validatorProcess=null}),this.validatorProcess.on("exit",(o)=>{this.output.appendLine(`[solana] validator exited with code ${o??-1}`),this.validatorProcess=null})}}function Nt(t,e){if(e)return e;let s=process.platform==="win32"?"entropy-ledger-host.exe":"entropy-ledger-host";return v.join(t,"native","target","release",s)}function zt(t){let e=process.platform==="win32"?"solana-test-validator.exe":"solana-test-validator",s=v.join(t,".chthonic","bin",e);if(yt.existsSync(s))return s;return process.platform==="win32"?"solana-test-validator":e}function Ft(t){try{let e=new URL(t);if(!e.port)return null;let s=Number(e.port);return Number.isFinite(s)?s:null}catch{return null}}function Jt(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}class Y{output;options;backend=null;constructor(t,e){this.output=t;this.options=e}async start(t){this.backend=this.options.mode==="bankrun"?new ft(this.output):new vt(this.output,this.options),await this.backend.start(t)}async commitEntropy(t){if(!this.backend)return{mode:"offline",detail:"LedgerBroker backend not initialized."};return this.backend.commitEntropy(t)}dispose(){this.backend?.dispose(),this.backend=null}}class ft{output;sequence=0;constructor(t){this.output=t}async start(t){this.output.appendLine("[ledger] phantom mode active (bankrun simulation).")}async commitEntropy(t){return this.sequence+=1,{mode:"bankrun",txSignature:`bankrun-${t.rootHash.slice(0,20)}-${this.sequence}`,detail:"In-memory bankrun simulation accepted the entropy settlement."}}dispose(){}}class vt{options;client;constructor(t,e){this.options=e;this.client=new K(t)}async start(t){await this.client.start(t,{rpcUrl:this.options.rpcUrl,autostartValidator:this.options.autostartValidator,hostBinaryPath:this.options.hostBinaryPath,walletPath:this.options.walletPath,idlPath:this.options.idlPath})}async commitEntropy(t){return this.client.commitEntropy(t)}dispose(){this.client.dispose()}}class tt{output;workerClient;options;requestDecorationRefresh;broker;merkle=new J;ledger;tooltipAugments=new Map;rootPath=null;scanTimer=null;settleTimer=null;gitPollTimer=null;gitHeadSnapshot=null;pendingSettleReason=null;disposables=[];constructor(t,e,s,o){this.output=t;this.workerClient=e;this.options=s;this.requestDecorationRefresh=o;this.broker=new Q(t),this.ledger=new Y(t,{mode:this.options.ledgerMode,rpcUrl:this.options.solanaRpcUrl,autostartValidator:this.options.solanaAutostartValidator,hostBinaryPath:this.options.solanaLedgerHostBinaryPath,walletPath:this.options.solanaWalletPath,idlPath:this.options.solanaIdlPath}),this.disposables.push(this.broker.onDidReceiveRuff((r)=>this.applyRuffSummary(r.files)),this.broker.onDidReceiveLore((r)=>this.applyLore(r)),this.workerClient.onDidUpdateRecords((r)=>this.captureEntropyLeaves(r)))}async start(t){if(this.rootPath=t,!this.options.enabled)return;this.broker.start(t),await this.ledger.start(t),this.broker.requestScan({type:"scan",reason:"manual",root:t}),this.startScanLoop(),this.startGitWatcher()}onDidSaveDocument(t){if(!this.rootPath||!this.options.enabled||t.uri.scheme!=="file")return;let e=bt(this.rootPath,t.uri.fsPath);if(!e)return;this.broker.requestScan({type:"scan",reason:"save",root:this.rootPath,files:[e]}),this.scheduleSettlement("save")}requestManualScan(){if(!this.rootPath||!this.options.enabled)return;this.broker.requestScan({type:"scan",reason:"manual",root:this.rootPath})}getTooltipFragments(t){if(!this.rootPath||t.scheme!=="file")return[];let e=bt(this.rootPath,t.fsPath);if(!e)return[];let s=this.tooltipAugments.get(e);if(!s)return[];let o=[];if(s.ruffViolations>0)o.push(`Ruff ${s.ruffViolations} violation${s.ruffViolations===1?"":"s"}`);if(s.loreLine)o.push(s.loreLine);return o}dispose(){if(this.scanTimer)clearInterval(this.scanTimer),this.scanTimer=null;if(this.settleTimer)clearTimeout(this.settleTimer),this.settleTimer=null;if(this.gitPollTimer)clearInterval(this.gitPollTimer),this.gitPollTimer=null;this.broker.dispose(),this.ledger.dispose(),this.disposables.forEach((t)=>t.dispose()),this.disposables.length=0}captureEntropyLeaves(t){if(!this.options.enabled)return;for(let e of t){let s=this.workerClient.getRecord(e);if(!s)continue;let o=this.tooltipAugments.get(s.path);this.merkle.upsert({path:s.path,entropy:s.entropy,complexity:s.complexity,debt:s.debt,freshness:s.freshness,ruffViolations:o?.ruffViolations??0,updatedAt:Date.now()})}}applyRuffSummary(t){if(!this.rootPath||!this.options.enabled)return;let e=[];for(let s of t){let o=this.tooltipAugments.get(s.path),r={ruffViolations:s.violations,loreLine:o?.loreLine};this.tooltipAugments.set(s.path,r);let i=Z.Uri.file(f.join(this.rootPath,s.path));e.push(i);let a=this.workerClient.getRecord(i);if(a){if(this.merkle.upsert({path:a.path,entropy:a.entropy,complexity:a.complexity,debt:a.debt,freshness:a.freshness,ruffViolations:s.violations,updatedAt:Date.now()}),a.entropy>=0.45||s.violations>0)this.broker.requestLore({type:"lore-request",root:this.rootPath,path:s.path,entropy:a.entropy,violations:s.violations})}}if(e.length>0)this.requestDecorationRefresh(e)}applyLore(t){if(!this.rootPath||!this.options.enabled)return;if(t.root!==this.rootPath)return;let e=this.tooltipAugments.get(t.path);this.tooltipAugments.set(t.path,{ruffViolations:e?.ruffViolations??t.violations,loreLine:t.line}),this.requestDecorationRefresh([Z.Uri.file(f.join(this.rootPath,t.path))])}startScanLoop(){if(this.scanTimer||!this.rootPath)return;let t=Math.max(this.options.pythonScanIntervalMs,1e4);this.scanTimer=setInterval(()=>{if(!this.rootPath)return;this.broker.requestScan({type:"scan",reason:"interval",root:this.rootPath})},t)}startGitWatcher(){if(!this.rootPath||this.gitPollTimer)return;this.gitHeadSnapshot=null,this.gitPollTimer=setInterval(async()=>{if(!this.rootPath)return;let t=await It(this.rootPath);if(!t)return;if(!this.gitHeadSnapshot){this.gitHeadSnapshot=t;return}if(t!==this.gitHeadSnapshot){if(this.gitHeadSnapshot=t,this.output.appendLine("[polyglot] git HEAD changed, scheduling Merkle settlement."),this.rootPath)this.broker.requestScan({type:"scan",reason:"commit",root:this.rootPath});this.scheduleSettlement("commit")}},6000)}scheduleSettlement(t){if(!this.options.enabled)return;if(this.pendingSettleReason=t==="commit"?"commit":this.pendingSettleReason??t,this.settleTimer)clearTimeout(this.settleTimer);this.settleTimer=setTimeout(()=>{this.settleTimer=null,this.flushSettlement()},Math.max(this.options.settleDebounceMs,300))}async flushSettlement(){let t=this.pendingSettleReason??"manual";this.pendingSettleReason=null;let e=this.merkle.settle(t);if(!e)return;let s=await this.ledger.commitEntropy(e),o=[`[polyglot] settled Merkle root ${e.rootHash.slice(0,16)}...`,`leaves=${e.leafCount}`,`mode=${s.mode}`];if(s.txSignature)o.push(`tx=${s.txSignature}`);o.push(`detail=${s.detail}`),this.output.appendLine(o.join(" "))}}async function It(t){let e=f.join(t,".git"),s=f.join(e,"HEAD"),o="";try{o=await X.readFile(s,"utf8")}catch{return null}let r=o.trim();if(!r)return null;if(!r.startsWith("ref:"))return r;let i=r.slice(4).trim(),a=f.join(e,i);try{let h=await X.readFile(a,"utf8");return`ref:${i}:${h.trim()}`}catch{return`ref:${i}:missing`}}function bt(t,e){let s=f.relative(t,e);if(!s||s.startsWith("..")||f.isAbsolute(s))return null;return s.replace(/\\/g,"/")}function Qt(t){console.log("☥ Chthonic Archive extension activated");let e=n.window.createOutputChannel("Chthonic SDK"),s=n.workspace.workspaceFolders?.[0]?.uri.fsPath||null,o=st.join(s||"","meta-ide","copilot-sdk","harness.ts"),r=new D(t.extensionUri,o,(d)=>e.appendLine(`[${new Date().toISOString()}] ${d}`));t.subscriptions.push(n.window.registerWebviewViewProvider(D.viewType,r));let i=n.workspace.getConfiguration("chthonic"),a=i.get("entropy.enabled",!0),h=i.get("entropy.maxFiles",1e4),c=i.get("entropy.scanIntervalMs",20000),w=i.get("entropy.decorationDebounceMs",120),P=i.get("entropy.decorationBatchSize",240),p=i.get("entropy.polyglotEnabled",!0),g=i.get("entropy.pythonScanIntervalMs",30000),j=i.get("entropy.ledgerSettleDebounceMs",1400),u=i.get("entropy.ledgerMode","validator"),St=i.get("entropy.solanaRpcUrl","http://127.0.0.1:8899"),Et=i.get("entropy.solanaAutostartValidator",!1),Rt=et(i.get("entropy.solanaLedgerHostBinaryPath","")),Lt=et(i.get("entropy.solanaWalletPath","")),Mt=et(i.get("entropy.solanaIdlPath","")),m=new N(t,e),L,b=new tt(e,m,{enabled:p,pythonScanIntervalMs:g,settleDebounceMs:j,ledgerMode:u,solanaRpcUrl:St,solanaAutostartValidator:Et,solanaLedgerHostBinaryPath:Rt,solanaWalletPath:Lt,solanaIdlPath:Mt},(d)=>L?.enqueueExternalUpdates(d));L=new F(m,w,P,(d)=>b.getTooltipFragments(d));let _=new A(t.extensionUri,m);if(_.setRootPath(s),t.subscriptions.push(m,L,_,b,n.window.registerFileDecorationProvider(L),n.window.registerWebviewViewProvider(A.viewType,_)),s&&a)m.start(s,h,c),b.start(s);t.subscriptions.push(n.workspace.onDidSaveTextDocument((d)=>{m.refreshFile(d.uri),b.onDidSaveDocument(d)})),t.subscriptions.push(n.commands.registerCommand("chthonic.entropyRefresh",()=>{m.rescanNow(),m.requestGraph(260),b.requestManualScan(),n.window.showInformationMessage("Chthonic entropy scan requested")}));let O=new wt;n.window.registerTreeDataProvider("chthonic.themeView",O),t.subscriptions.push(n.commands.registerCommand("chthonic.switchTheme",async()=>{let d=[{label:"$(paintcan) Flesh & Earth",description:"Warm earth · WCAG AA · Distribution palette",id:"Chthonic Mandala - Flesh & Earth"},{label:"$(zap) ROGBIV",description:"SSOT spectral · FA¹⁻⁵ canonical hexes",id:"Chthonic Mandala - ROGBIV"}],M=n.workspace.getConfiguration("workbench").get("colorTheme"),W=await n.window.showQuickPick(d.map((nt)=>({...nt,picked:M===nt.id})),{placeHolder:`Current: ${M}`});if(W)await n.workspace.getConfiguration("workbench").update("colorTheme",W.id,n.ConfigurationTarget.Workspace),n.window.showInformationMessage(`Theme: ${W.id}`),O.refresh()}));let rt=n.workspace.getConfiguration("chthonic");if(rt.get("showSSOTHash",!0)){let d=n.window.createStatusBarItem(n.StatusBarAlignment.Left,50);d.command="chthonic.verifySSOT",d.tooltip="SSOT integrity hash — click to verify",t.subscriptions.push(d),xt(d),t.subscriptions.push(n.workspace.onDidSaveTextDocument((M)=>{if(M.fileName.includes("copilot-instructions"))xt(d)}))}if(rt.get("showLineage",!0)){let d=n.window.createStatusBarItem(n.StatusBarAlignment.Left,49);d.text="$(git-branch) ☥ main",d.tooltip="Chthonic lineage",d.show(),t.subscriptions.push(d)}let it=new Pt;n.window.registerTreeDataProvider("chthonic.statusView",it),t.subscriptions.push(n.commands.registerCommand("chthonic.verifySSOT",async()=>{let d=ot();if(d)n.window.showInformationMessage(`SSOT SHA-256: ${d.substring(0,16)}…`);else n.window.showWarningMessage("SSOT file not found")})),t.subscriptions.push(n.commands.registerCommand("chthonic.refreshStatus",()=>{it.refresh(),O.refresh(),m.rescanNow(),m.requestGraph(260),b.requestManualScan()}))}function Gt(){}function ot(){let t=n.workspace.workspaceFolders?.[0];if(!t)return null;let e=n.workspace.getConfiguration("chthonic").get("ssotPath",".github/copilot-instructions.md"),s=st.join(t.uri.fsPath,e);if(!H.existsSync(s))return null;let r=H.readFileSync(s,"utf-8").replace(/\r\n/g,`
`).replace(/\r/g,`
`).split(`
`).map((i)=>i.trimEnd()).join(`
`).trim();return kt.createHash("sha256").update(r,"utf-8").digest("hex")}function xt(t){let e=ot();if(e)t.text=`$(shield) ${e.substring(0,8)}`,t.show();else t.text="$(shield) SSOT ??",t.show()}function et(t){let e=t.trim();return e.length>0?e:void 0}class wt{_onDidChange=new n.EventEmitter;onDidChangeTreeData=this._onDidChange.event;refresh(){this._onDidChange.fire()}getTreeItem(t){return t}getChildren(){let t=n.workspace.getConfiguration("workbench").get("colorTheme")||"";return[{name:"Chthonic Mandala - Flesh & Earth",short:"Flesh & Earth",icon:"\uD83C\uDF0D",desc:"Warm earth · Distribution"},{name:"Chthonic Mandala - ROGBIV",short:"ROGBIV",icon:"\uD83C\uDF08",desc:"SSOT spectral · Research"}].map((s)=>{let o=t===s.name,r=new n.TreeItem(`${o?"◉":"○"} ${s.icon} ${s.short}`,n.TreeItemCollapsibleState.None);return r.tooltip=`${s.name}
${s.desc}${o?`

✅ ACTIVE`:""}`,r.description=o?"active":"",r.command={command:"chthonic.switchTheme",title:"Switch"},r})}}class Pt{_onDidChange=new n.EventEmitter;onDidChangeTreeData=this._onDidChange.event;refresh(){this._onDidChange.fire()}getTreeItem(t){return t}getChildren(){let t=ot(),e=[],s=new n.TreeItem(`$(shield) SSOT: ${t?t.substring(0,12)+"…":"not found"}`,n.TreeItemCollapsibleState.None);s.command={command:"chthonic.verifySSOT",title:"Verify"},e.push(s);let o=new n.TreeItem(`$(paintcan) Theme: ${(n.workspace.getConfiguration("workbench").get("colorTheme")||"default").replace("Chthonic Mandala - ","")}`,n.TreeItemCollapsibleState.None);return o.command={command:"chthonic.switchTheme",title:"Switch"},e.push(o),e}}
