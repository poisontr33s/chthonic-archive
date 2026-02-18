var Ee=Object.create;var{getPrototypeOf:ke,defineProperty:H,getOwnPropertyNames:Ct,getOwnPropertyDescriptor:we}=Object,$t=Object.prototype.hasOwnProperty;var c=(t,e,s)=>{s=t!=null?Ee(ke(t)):{};let i=e||!t||!t.__esModule?H(s,"default",{value:t,enumerable:!0}):s;for(let n of Ct(t))if(!$t.call(i,n))H(i,n,{get:()=>t[n],enumerable:!0});return i},Mt=new WeakMap,Pe=(t)=>{var e=Mt.get(t),s;if(e)return e;if(e=H({},"__esModule",{value:!0}),t&&typeof t==="object"||typeof t==="function")Ct(t).map((i)=>!$t.call(e,i)&&H(e,i,{get:()=>t[i],enumerable:!(s=we(t,i))||s.enumerable}));return Mt.set(t,e),e};var Le=(t,e)=>{for(var s in e)H(t,s,{get:e[s],enumerable:!0,configurable:!0,set:(i)=>e[s]=()=>i})};var ss={};Le(ss,{deactivate:()=>ts,activate:()=>Ze});module.exports=Pe(ss);var a=c(require("vscode")),ee=c(require("crypto")),C=c(require("fs")),j=c(require("path"));var Dt=c(require("vscode")),nt=c(require("child_process"));var At=c(require("child_process")),Bt=c(require("readline")),U=c(require("path"));class it{harnessPath;log;process=null;rl=null;handlers=new Set;authenticated=!1;ready=!1;constructor(t,e){this.harnessPath=t;this.log=e}async start(){if(this.process)return;let t=U.dirname(this.harnessPath),e=U.basename(this.harnessPath);this.process=At.spawn("bun",["run",e],{cwd:t,stdio:["pipe","pipe","pipe"],env:{...process.env}}),this.process.stderr?.on("data",(s)=>{this.log(`[harness stderr] ${s.toString().trim()}`)}),this.process.on("close",(s)=>{this.log(`[harness] exited with code ${s}`),this.process=null,this.rl=null,this.ready=!1,this.authenticated=!1}),this.rl=Bt.createInterface({input:this.process.stdout}),this.rl.on("line",(s)=>{try{let i=JSON.parse(s);if(i.type==="ready")this.ready=!0,this.log(`[harness] ready: ${i.sdk}`);for(let n of this.handlers)n(i)}catch{this.log(`[harness] non-JSON: ${s.substring(0,200)}`)}}),await new Promise((s,i)=>{let n=setTimeout(()=>i(Error("Harness startup timeout")),15000),o=(r)=>{if(r.type==="ready")clearTimeout(n),this.handlers.delete(o),s()};this.handlers.add(o)})}async authenticate(t,e){this.send({cmd:"auth",token:t,login:e}),await this.waitFor("auth_ok"),this.authenticated=!0,this.log(`[harness] authenticated as ${e}`)}query(t,e,s,i,n){return new Promise((o,r)=>{let l=(u)=>{if(u.id!==t)return;if(u.type==="event"&&u.event)i(u.event);else if(u.type==="done")this.handlers.delete(l),o();else if(u.type==="cancelled")this.handlers.delete(l),o();else if(u.type==="error")this.handlers.delete(l),r(Error(u.message||"Query failed"))};this.handlers.add(l),this.send({cmd:"query",id:t,prompt:e,workingDirectory:s,model:n?.model,reasoningEffort:n?.reasoningEffort})})}cancel(t){this.send({cmd:"cancel",id:t})}async getModels(){return this.send({cmd:"models"}),(await this.waitFor("models")).data||[]}isReady(){return this.ready&&this.authenticated&&this.process!==null}stop(){if(this.process)this.process.kill(),this.process=null;this.rl=null,this.ready=!1,this.authenticated=!1,this.handlers.clear()}send(t){if(!this.process?.stdin?.writable)throw Error("Harness not running");this.process.stdin.write(JSON.stringify(t)+`
`)}waitFor(t,e=15000){return new Promise((s,i)=>{let n=setTimeout(()=>{this.handlers.delete(o),i(Error(`Timeout waiting for ${t}`))},e),o=(r)=>{if(r.type===t)clearTimeout(n),this.handlers.delete(o),s(r);else if(r.type==="error")clearTimeout(n),this.handlers.delete(o),i(Error(r.message||"Error"))};this.handlers.add(o)})}}class V{extensionUri;harnessPath;log;static viewType="chthonic.chatView";view;connection=null;isConnecting=!1;activeQueryId=null;constructor(t,e,s){this.extensionUri=t;this.harnessPath=e;this.log=s}resolveWebviewView(t,e,s){this.view=t,t.webview.options={enableScripts:!0,localResourceRoots:[this.extensionUri]},t.webview.html=this.getHtml(),t.webview.onDidReceiveMessage(async(i)=>{switch(i.type){case"connect":await this.connectAgent();break;case"prompt":await this.sendPrompt(i.text);break;case"cancel":this.cancelQuery();break;case"disconnect":this.disconnectAgent();break}})}async connectAgent(){if(this.isConnecting||this.connection?.isReady())return;this.isConnecting=!0,this.postMessage({type:"status",status:"connecting"});try{this.connection=new it(this.harnessPath,this.log),await this.connection.start();let t=nt.execSync("gh auth token",{encoding:"utf-8"}).trim(),e=nt.execSync("gh api user --jq .login",{encoding:"utf-8"}).trim();await this.connection.authenticate(t,e),this.postMessage({type:"connected",agentName:"Chthonic SDK",agentVersion:"0.1.0",login:e}),this.log(`Chat connected: ${e}`)}catch(t){this.log(`Chat connect failed: ${t.message}`),this.postMessage({type:"error",message:t.message}),this.connection?.stop(),this.connection=null}finally{this.isConnecting=!1}}async sendPrompt(t){if(!this.connection?.isReady()){this.postMessage({type:"error",message:"Not connected"});return}let e=crypto.randomUUID();this.activeQueryId=e,this.postMessage({type:"prompt-start"});let s=Dt.workspace.workspaceFolders?.[0]?.uri.fsPath||process.cwd();try{await this.connection.query(e,t,s,(i)=>this.handleSdkEvent(i))}catch(i){this.postMessage({type:"error",message:i.message})}finally{this.activeQueryId=null,this.postMessage({type:"prompt-end"})}}handleSdkEvent(t){switch(t.type){case"assistant.message":if(t.data?.content)this.postMessage({type:"agent-message",content:t.data.content});break;case"assistant.message.delta":if(t.data?.delta)this.postMessage({type:"agent-delta",delta:t.data.delta});break;case"tool.execution_start":this.postMessage({type:"tool-start",name:t.data?.name,args:t.data?.arguments});break;case"tool.execution_complete":this.postMessage({type:"tool-end",name:t.data?.name});break;case"assistant.reasoning":this.postMessage({type:"reasoning"});break;case"assistant.usage":this.postMessage({type:"usage",model:t.data?.model,inputTokens:t.data?.inputTokens,outputTokens:t.data?.outputTokens,duration:t.data?.duration});break;case"session.usage_info":this.postMessage({type:"context-info",tokenLimit:t.data?.tokenLimit,currentTokens:t.data?.currentTokens});break}}cancelQuery(){if(this.activeQueryId&&this.connection)this.connection.cancel(this.activeQueryId)}disconnectAgent(){this.connection?.stop(),this.connection=null,this.activeQueryId=null,this.postMessage({type:"disconnected"})}postMessage(t){this.view?.webview.postMessage(t)}dispose(){this.connection?.stop()}getHtml(){return`<!DOCTYPE html>
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
</html>`}}var O=c(require("path")),B=c(require("vscode")),Tt=require("worker_threads");class ot{extensionContext;output;records=new Map;recordUris=new Map;onDidUpdateRecordsEmitter=new B.EventEmitter;onDidUpdateRecords=this.onDidUpdateRecordsEmitter.event;onDidUpdateGraphEmitter=new B.EventEmitter;onDidUpdateGraph=this.onDidUpdateGraphEmitter.event;onDidUpdateSnapshotEmitter=new B.EventEmitter;onDidUpdateSnapshot=this.onDidUpdateSnapshotEmitter.event;worker=null;rootPath=null;workerPath;maxFiles=1e4;lastScanDurationMs=0;lastScanAt=0;scanTimer=null;disposed=!1;constructor(t,e){this.extensionContext=t;this.output=e;this.workerPath=t.asAbsolutePath(O.join("dist","entropy-worker.js"))}start(t,e,s){this.rootPath=t,this.maxFiles=e,this.ensureWorker(),this.send({type:"scan",root:t,maxFiles:this.maxFiles}),this.scheduleScanLoop(s)}rescanNow(){if(!this.rootPath)return;this.send({type:"scan",root:this.rootPath,maxFiles:this.maxFiles})}refreshFile(t){if(!this.rootPath||t.scheme!=="file")return;this.send({type:"refresh-file",root:this.rootPath,path:t.fsPath})}requestGraph(t){this.send({type:"graph",limit:t})}getRecord(t){if(!this.rootPath||t.scheme!=="file")return;let e=Re(O.relative(this.rootPath,t.fsPath));return this.records.get(e)}getSnapshot(t=40){let e=Array.from(this.records.values()),s=e.length===0?0:e.reduce((n,o)=>n+o.entropy,0)/e.length,i=e.sort((n,o)=>o.entropy-n.entropy).slice(0,t);return{totalFiles:e.length,topEntropy:i,averageEntropy:s,lastScanDurationMs:this.lastScanDurationMs,lastScanAt:this.lastScanAt}}dispose(){if(this.disposed=!0,this.scanTimer)clearInterval(this.scanTimer),this.scanTimer=null;this.send({type:"stop"}),this.worker?.terminate(),this.worker=null,this.onDidUpdateRecordsEmitter.dispose(),this.onDidUpdateGraphEmitter.dispose(),this.onDidUpdateSnapshotEmitter.dispose()}scheduleScanLoop(t){if(this.scanTimer)clearInterval(this.scanTimer);let e=Math.max(5000,t);this.scanTimer=setInterval(()=>{if(!this.disposed)this.rescanNow()},e)}ensureWorker(){if(this.worker)return;this.worker=new Tt.Worker(this.workerPath),this.worker.on("message",(t)=>this.handleWorkerEvent(t)),this.worker.on("error",(t)=>{this.output.appendLine(`[entropy] worker error: ${t.message}`)}),this.worker.on("exit",(t)=>{if(this.output.appendLine(`[entropy] worker exited with code ${t}`),this.worker=null,!this.disposed&&t!==0)this.ensureWorker(),this.rescanNow()})}send(t){this.ensureWorker(),this.worker?.postMessage(t)}handleWorkerEvent(t){switch(t.type){case"scan-progress":{if(!this.rootPath)return;let e=[];for(let s of t.records){this.records.set(s.path,s);let i=this.recordUris.get(s.path);if(!i)i=B.Uri.file(O.join(this.rootPath,s.path)),this.recordUris.set(s.path,i);e.push(i)}if(e.length>0)this.onDidUpdateRecordsEmitter.fire(e);break}case"scan-complete":this.lastScanDurationMs=t.durationMs,this.lastScanAt=Date.now(),this.onDidUpdateSnapshotEmitter.fire(this.getSnapshot());break;case"graph-result":this.onDidUpdateGraphEmitter.fire(t.graph);break;case"error":this.output.appendLine(`[entropy] ${t.message}${t.detail?`
${t.detail}`:""}`);break}}}function Re(t){return t.replace(/\\/g,"/")}var It=c(require("vscode"));class at{workerClient;debounceMs;maxPerFlush;tooltipAugmentProvider;onDidChangeEmitter=new It.EventEmitter;onDidChangeFileDecorations=this.onDidChangeEmitter.event;pending=new Map;flushTimer=null;constructor(t,e,s,i){this.workerClient=t;this.debounceMs=e;this.maxPerFlush=s;this.tooltipAugmentProvider=i;this.workerClient.onDidUpdateRecords((n)=>this.enqueueUpdates(n))}dispose(){if(this.flushTimer)clearTimeout(this.flushTimer),this.flushTimer=null;this.onDidChangeEmitter.dispose()}updateConfig(t,e){this.debounceMs=Math.max(30,t),this.maxPerFlush=Math.max(64,e)}provideFileDecoration(t){if(t.scheme!=="file")return;let e=this.workerClient.getRecord(t);if(!e)return;let s=Me(e),i=[`Entropy ${(e.entropy*100).toFixed(0)}%`,`Complexity ${e.complexity}`,`Debt ${e.debt}`,`Freshness ${(e.freshness*100).toFixed(0)}%`];if(this.tooltipAugmentProvider)i.push(...this.tooltipAugmentProvider(t));return{color:s,tooltip:i.join(`
`),propagate:!1}}enqueueExternalUpdates(t){this.enqueueUpdates(t)}enqueueUpdates(t){for(let e of t)this.pending.set(e.toString(),e);if(!this.flushTimer)this.flushTimer=setTimeout(()=>this.flush(),this.debounceMs)}flush(){if(this.flushTimer=null,this.pending.size===0)return;let t=Array.from(this.pending.values()).slice(0,this.maxPerFlush);for(let e of t)this.pending.delete(e.toString());if(this.onDidChangeEmitter.fire(t),this.pending.size>0)this.flushTimer=setTimeout(()=>this.flush(),this.debounceMs)}}function Me(t){let e=$e(t.entropy*0.78+(1-t.freshness)*0.22),s=rt(118,24,e),i=rt(36,46,e),n=rt(58,42,e);return Ce(s,i,n)}function Ce(t,e,s){let i=t/360,n=e/100,o=s/100,r=(h,v,Z)=>{let f=Z;if(f<0)f+=1;if(f>1)f-=1;if(f<0.16666666666666666)return h+(v-h)*6*f;if(f<0.5)return v;if(f<0.6666666666666666)return h+(v-h)*(0.6666666666666666-f)*6;return h},l,u,p;if(n===0)l=o,u=o,p=o;else{let h=o<0.5?o*(1+n):o+n-o*n,v=2*o-h;l=r(v,h,i+0.3333333333333333),u=r(v,h,i),p=r(v,h,i-0.3333333333333333)}let I=(h)=>{return Math.round(h*255).toString(16).padStart(2,"0")};return`#${I(l)}${I(u)}${I(p)}`}function $e(t){if(t<0)return 0;if(t>1)return 1;return t}function rt(t,e,s){return t+(e-t)*s}var D=c(require("path")),S=c(require("vscode"));class N{extensionUri;workerClient;static viewType="chthonic.abyssalView";disposables=[];view=null;rootPath=null;sedimentRequestCallback=null;constructor(t,e){this.extensionUri=t;this.workerClient=e;this.disposables.push(this.workerClient.onDidUpdateGraph((s)=>this.postMessage({type:"graph",graph:s})),this.workerClient.onDidUpdateSnapshot((s)=>this.postMessage({type:"snapshot",snapshot:s})))}setRootPath(t){this.rootPath=t}onRequestSediment(t){this.sedimentRequestCallback=t}postSedimentData(t){this.postMessage({type:"sediment",sediment:t})}postSedimentChunk(t){this.postMessage({type:"sedimentChunk",chunk:t})}postSedimentBinary(t){let e=t.buffer.slice(t.byteOffset,t.byteOffset+t.byteLength);this.postMessage({type:"sedimentBinary",payload:e})}dispose(){this.disposables.forEach((t)=>t.dispose()),this.disposables.length=0}resolveWebviewView(t,e,s){this.view=t,t.webview.options={enableScripts:!0,localResourceRoots:[this.extensionUri]},t.webview.html=this.getHtml(t.webview),t.webview.onDidReceiveMessage((i)=>{this.handleMessage(i)})}handleMessage(t){if(!t||typeof t!=="object")return;let e=t;if(!e.type)return;if(e.type==="ready"){this.postMessage({type:"snapshot",snapshot:this.workerClient.getSnapshot()}),this.workerClient.requestGraph(260);return}if(e.type==="requestGraph"){this.workerClient.requestGraph(260);return}if(e.type==="requestSediment"){this.sedimentRequestCallback?.();return}if(e.type==="openFile"&&e.path&&this.rootPath){let s=D.normalize(e.path);if(s.startsWith("..")||D.isAbsolute(s))return;let i=D.join(this.rootPath,s),n=S.Uri.file(i);S.workspace.openTextDocument(n).then((o)=>{S.window.showTextDocument(o,{preview:!1})},()=>{S.window.showWarningMessage(`Unable to open ${e.path}`)})}}postMessage(t){if(!this.view)return;this.view.webview.postMessage(t)}getHtml(t){let e=Ae(),s=t.asWebviewUri(S.Uri.joinPath(this.extensionUri,"media","abyssalPane.js")),i=t.asWebviewUri(S.Uri.joinPath(this.extensionUri,"media","wasm","pkg","entropy_renderer_wasm.js")),n=t.asWebviewUri(S.Uri.joinPath(this.extensionUri,"media","wasm","pkg","entropy_renderer_wasm_bg.wasm")),o=["default-src 'none'",`img-src ${t.cspSource} data:`,`style-src ${t.cspSource} 'unsafe-inline'`,`script-src 'nonce-${e}' ${t.cspSource}`,`connect-src ${t.cspSource}`].join("; "),r=JSON.stringify({wasmModuleUri:i.toString(),wasmBinaryUri:n.toString()});return`<!DOCTYPE html>
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
        window.__CHTHONIC_ABYSSAL__ = ${r};
    </script>
    <script nonce="${e}" type="module" src="${s}"></script>
</body>
</html>`}}function Ae(){let e="";for(let s=0;s<32;s+=1)e+="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789".charAt(Math.floor(Math.random()*62));return e}var gt=c(require("fs/promises")),E=c(require("path")),mt=c(require("vscode"));var _t=c(require("crypto"));class dt{leaves=new Map;dirty=!1;upsert(t){let e=Te(t.path),s=Be(e,t);if(this.leaves.get(e)!==s)this.leaves.set(e,s),this.dirty=!0}hasDirty(){return this.dirty}settle(t){if(!this.dirty||this.leaves.size===0)return null;let e=De(Array.from(this.leaves.entries()).sort((s,i)=>s[0].localeCompare(i[0])));return this.dirty=!1,{reason:t,rootHash:e,leafCount:this.leaves.size,generatedAt:Date.now()}}}function Be(t,e){let s=[t,e.entropy.toFixed(6),e.complexity,e.debt,e.freshness.toFixed(6),e.ruffViolations,e.updatedAt].join("|");return J(s)}function De(t){if(t.length===0)return J("EMPTY");let e=t.map(([s,i])=>J(`${s}:${i}`));while(e.length>1){let s=[];for(let i=0;i<e.length;i+=2){let n=e[i],o=e[i+1]??e[i];s.push(J(`${n}${o}`))}e=s}return e[0]}function J(t){return _t.createHash("sha256").update(t,"utf8").digest("hex")}function Te(t){return t.replace(/\\/g,"/")}var z=c(require("path")),ct=require("child_process"),Q=c(require("vscode"));function M(t,e){let s="",i=(n)=>{let o=n.trim();if(!o)return;try{let r=JSON.parse(o);if(!r||typeof r!=="object"||Array.isArray(r))throw Error("JSONL payload must be an object");t(r)}catch(r){e(r instanceof Error?r:Error(String(r)))}};return{push(n){s+=n.toString();while(!0){let o=s.indexOf(`
`);if(o<0)return;let r=s.slice(0,o);s=s.slice(o+1),i(r)}},flush(){if(!s.trim()){s="";return}i(s),s=""}}}class lt{output;rootPath=null;pythonSidecar=null;rubySidecar=null;onDidReceiveRuffEmitter=new Q.EventEmitter;onDidReceiveRuff=this.onDidReceiveRuffEmitter.event;onDidReceiveLoreEmitter=new Q.EventEmitter;onDidReceiveLore=this.onDidReceiveLoreEmitter.event;onDidReceiveSidecarErrorEmitter=new Q.EventEmitter;onDidReceiveSidecarError=this.onDidReceiveSidecarErrorEmitter.event;constructor(t){this.output=t}start(t){this.rootPath=t,this.startPythonSidecar(),this.startRubySidecar()}requestScan(t){if(!this.pythonSidecar||this.pythonSidecar.killed)this.startPythonSidecar();this.writeJson(this.pythonSidecar,t)}requestLore(t){if(!this.rubySidecar||this.rubySidecar.killed)this.startRubySidecar();this.writeJson(this.rubySidecar,t)}dispose(){this.pythonSidecar?.kill(),this.rubySidecar?.kill(),this.pythonSidecar=null,this.rubySidecar=null,this.onDidReceiveRuffEmitter.dispose(),this.onDidReceiveLoreEmitter.dispose(),this.onDidReceiveSidecarErrorEmitter.dispose()}startPythonSidecar(){if(!this.rootPath||this.pythonSidecar)return;let t=z.join(this.rootPath,".chthonic","python","entropy_scan.py"),e=z.join(this.rootPath,".chthonic","venv",process.platform==="win32"?"Scripts/python.exe":"bin/python");this.pythonSidecar=ct.spawn("uv",["run","--python",e,t,"--stdio"],{cwd:this.rootPath,stdio:["pipe","pipe","pipe"]});let s=M((i)=>this.handlePythonPayload(i),(i)=>this.output.appendLine(`[polyglot:python] invalid JSONL payload: ${i.message}`));this.pythonSidecar.stdout?.on("data",(i)=>s.push(i)),this.pythonSidecar.stderr?.on("data",(i)=>{this.output.appendLine(`[polyglot:python] ${i.toString().trimEnd()}`)}),this.pythonSidecar.on("error",(i)=>{this.onDidReceiveSidecarErrorEmitter.fire({type:"error",source:"python",message:i.message}),this.output.appendLine(`[polyglot:python] failed to spawn: ${i.message}`),this.pythonSidecar=null}),this.pythonSidecar.on("exit",(i)=>{s.flush(),this.output.appendLine(`[polyglot:python] exited with code ${i??-1}`),this.pythonSidecar=null})}startRubySidecar(){if(!this.rootPath||this.rubySidecar)return;let t=z.join(this.rootPath,".chthonic","ruby","lore.rb");this.rubySidecar=ct.spawn("ruby",[t],{cwd:this.rootPath,stdio:["pipe","pipe","pipe"]});let e=M((s)=>this.handleRubyPayload(s),(s)=>this.output.appendLine(`[polyglot:ruby] invalid JSONL payload: ${s.message}`));this.rubySidecar.stdout?.on("data",(s)=>e.push(s)),this.rubySidecar.stderr?.on("data",(s)=>{this.output.appendLine(`[polyglot:ruby] ${s.toString().trimEnd()}`)}),this.rubySidecar.on("error",(s)=>{this.onDidReceiveSidecarErrorEmitter.fire({type:"error",source:"ruby",message:s.message}),this.output.appendLine(`[polyglot:ruby] failed to spawn: ${s.message}`),this.rubySidecar=null}),this.rubySidecar.on("exit",(s)=>{e.flush(),this.output.appendLine(`[polyglot:ruby] exited with code ${s??-1}`),this.rubySidecar=null})}writeJson(t,e){if(!t?.stdin||t.killed)return;try{t.stdin.write(`${JSON.stringify(e)}
`)}catch(s){this.output.appendLine(`[polyglot] sidecar write failed: ${Ie(s)}`)}}handlePythonPayload(t){if(t.type==="ruff-summary"){let e=t;this.onDidReceiveRuffEmitter.fire(e);return}if(t.type==="error"){let e=String(t.message??"python sidecar error");this.output.appendLine(`[polyglot:python] ${e}`),this.onDidReceiveSidecarErrorEmitter.fire({type:"error",source:"python",message:e})}}handleRubyPayload(t){if(t.type==="lore"){this.onDidReceiveLoreEmitter.fire(t);return}if(t.type==="error"){let e=String(t.message??"ruby sidecar error");this.output.appendLine(`[polyglot:ruby] ${e}`),this.onDidReceiveSidecarErrorEmitter.fire({type:"error",source:"ruby",message:e})}}}function Ie(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}var Ht=c(require("fs")),W=c(require("fs/promises")),w=c(require("path")),pt=require("child_process");class ut{output;rootPath=null;options={rpcUrl:"http://127.0.0.1:8899",autostartValidator:!1};ledgerFilePath=null;validatorProcess=null;hostProcess=null;requestCounter=1;pending=new Map;constructor(t){this.output=t}async start(t,e){this.rootPath=t,this.options=e;let s=w.join(t,".chthonic","ledger");if(await W.mkdir(s,{recursive:!0}),this.ledgerFilePath=w.join(s,"entropy-settlements.jsonl"),e.autostartValidator)this.startValidator();this.startHostProcess()}async commitEntropy(t){if(!this.rootPath||!this.ledgerFilePath)return{mode:"offline",detail:"Ledger host not started"};let e={...t,rpcUrl:this.options.rpcUrl,recordedAt:Date.now()},s={mode:"offline",detail:"Rust ledger host unavailable; persisted settlement locally."};try{s=await this.submitToHost(t)}catch(i){this.output.appendLine(`[ledger-rust] submit failed: ${je(i)}`)}return await W.appendFile(this.ledgerFilePath,`${JSON.stringify({...e,receipt:s})}
`,"utf8"),s}dispose(){for(let[t,e]of this.pending)e.reject(Error(`request ${t} cancelled`));this.pending.clear(),this.hostProcess?.kill(),this.hostProcess=null,this.validatorProcess?.kill(),this.validatorProcess=null}startHostProcess(){if(!this.rootPath||this.hostProcess)return;let t=_e(this.rootPath,this.options.hostBinaryPath),e=this.options.walletPath??w.join(this.rootPath,".chthonic","wallets","payer.json"),s=this.options.idlPath??w.join(this.rootPath,".chthonic","wallets","entropy_ledger.json");this.hostProcess=pt.spawn(t,["--wallet",e,"--idl",s,"--rpc-url",this.options.rpcUrl],{cwd:this.rootPath,stdio:["pipe","pipe","pipe"]});let i=M((n)=>this.handleHostPayload(n),(n)=>this.output.appendLine(`[ledger-rust] invalid JSON payload: ${n.message}`));this.hostProcess.stdout?.on("data",(n)=>i.push(n)),this.hostProcess.stderr?.on("data",(n)=>{this.output.appendLine(`[ledger-rust] ${n.toString().trimEnd()}`)}),this.hostProcess.on("error",(n)=>{this.output.appendLine(`[ledger-rust] failed to spawn host: ${n.message}`),this.rejectAllPending(Error(`host spawn failed: ${n.message}`)),this.hostProcess=null}),this.hostProcess.on("exit",(n)=>{i.flush(),this.output.appendLine(`[ledger-rust] host exited with code ${n??-1}`),this.rejectAllPending(Error("ledger host exited")),this.hostProcess=null})}async submitToHost(t){if(!this.hostProcess||this.hostProcess.killed)this.startHostProcess();if(!this.hostProcess?.stdin||this.hostProcess.killed)return{mode:"offline",detail:"Rust host binary is missing or not executable."};let e=this.requestCounter++,s={jsonrpc:"2.0",id:e,method:"submit_entropy",params:{entropy_score:Math.max(0,Math.round(t.leafCount*17+13)),merkle_root:t.rootHash,leaf_count:t.leafCount,reason:t.reason}};return await new Promise((n,o)=>{this.pending.set(e,{resolve:n,reject:o}),this.hostProcess?.stdin?.write(`${JSON.stringify(s)}
`,(r)=>{if(!r)return;this.pending.delete(e),o(r)})})}handleHostPayload(t){let e=t.id;if(typeof e!=="number")return;let s=this.pending.get(e);if(!s)return;if(this.pending.delete(e),t.error&&typeof t.error==="object"){let n=t;s.resolve({mode:"offline",detail:`Rust ledger error ${n.error.code}: ${n.error.message}`});return}let i=t;s.resolve({mode:"validator-rust",txSignature:i.result.signature,detail:`Rust anchor-client submission accepted${i.result.slot?` (slot ${i.result.slot})`:""}.`})}rejectAllPending(t){for(let[e,s]of this.pending)this.pending.delete(e),s.reject(t)}startValidator(){if(!this.rootPath||this.validatorProcess)return;let t=He(this.rootPath),e=Oe(this.options.rpcUrl)??8899,s=w.join(this.rootPath,".chthonic","solana-ledger");this.validatorProcess=pt.spawn(t,["--ledger",s,"--rpc-port",String(e),"--reset","--quiet"],{cwd:this.rootPath,stdio:["ignore","pipe","pipe"]}),this.validatorProcess.stdout?.on("data",(i)=>{this.output.appendLine(`[solana] ${i.toString().trimEnd()}`)}),this.validatorProcess.stderr?.on("data",(i)=>{this.output.appendLine(`[solana] ${i.toString().trimEnd()}`)}),this.validatorProcess.on("error",(i)=>{this.output.appendLine(`[solana] validator spawn error: ${i.message}`),this.validatorProcess=null}),this.validatorProcess.on("exit",(i)=>{this.output.appendLine(`[solana] validator exited with code ${i??-1}`),this.validatorProcess=null})}}function _e(t,e){if(e)return e;let s=process.platform==="win32"?"entropy-ledger-host.exe":"entropy-ledger-host";return w.join(t,"native","target","release",s)}function He(t){let e=process.platform==="win32"?"solana-test-validator.exe":"solana-test-validator",s=w.join(t,".chthonic","bin",e);if(Ht.existsSync(s))return s;return process.platform==="win32"?"solana-test-validator":e}function Oe(t){try{let e=new URL(t);if(!e.port)return null;let s=Number(e.port);return Number.isFinite(s)?s:null}catch{return null}}function je(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}class ht{output;options;backend=null;constructor(t,e){this.output=t;this.options=e}async start(t){this.backend=this.options.mode==="bankrun"?new Ot(this.output):new jt(this.output,this.options),await this.backend.start(t)}async commitEntropy(t){if(!this.backend)return{mode:"offline",detail:"LedgerBroker backend not initialized."};return this.backend.commitEntropy(t)}dispose(){this.backend?.dispose(),this.backend=null}}class Ot{output;sequence=0;constructor(t){this.output=t}async start(t){this.output.appendLine("[ledger] phantom mode active (bankrun simulation).")}async commitEntropy(t){return this.sequence+=1,{mode:"bankrun",txSignature:`bankrun-${t.rootHash.slice(0,20)}-${this.sequence}`,detail:"In-memory bankrun simulation accepted the entropy settlement."}}dispose(){}}class jt{options;client;constructor(t,e){this.options=e;this.client=new ut(t)}async start(t){await this.client.start(t,{rpcUrl:this.options.rpcUrl,autostartValidator:this.options.autostartValidator,hostBinaryPath:this.options.hostBinaryPath,walletPath:this.options.walletPath,idlPath:this.options.idlPath})}async commitEntropy(t){return this.client.commitEntropy(t)}dispose(){this.client.dispose()}}class ft{output;workerClient;options;requestDecorationRefresh;broker;merkle=new dt;ledger;tooltipAugments=new Map;rootPath=null;scanTimer=null;settleTimer=null;gitPollTimer=null;gitHeadSnapshot=null;pendingSettleReason=null;disposables=[];constructor(t,e,s,i){this.output=t;this.workerClient=e;this.options=s;this.requestDecorationRefresh=i;this.broker=new lt(t),this.ledger=new ht(t,{mode:this.options.ledgerMode,rpcUrl:this.options.solanaRpcUrl,autostartValidator:this.options.solanaAutostartValidator,hostBinaryPath:this.options.solanaLedgerHostBinaryPath,walletPath:this.options.solanaWalletPath,idlPath:this.options.solanaIdlPath}),this.disposables.push(this.broker.onDidReceiveRuff((n)=>this.applyRuffSummary(n.files)),this.broker.onDidReceiveLore((n)=>this.applyLore(n)),this.workerClient.onDidUpdateRecords((n)=>this.captureEntropyLeaves(n)))}async start(t){if(this.rootPath=t,!this.options.enabled)return;this.broker.start(t),await this.ledger.start(t),this.broker.requestScan({type:"scan",reason:"manual",root:t}),this.startScanLoop(),this.startGitWatcher()}onDidSaveDocument(t){if(!this.rootPath||!this.options.enabled||t.uri.scheme!=="file")return;let e=Ft(this.rootPath,t.uri.fsPath);if(!e)return;this.broker.requestScan({type:"scan",reason:"save",root:this.rootPath,files:[e]}),this.scheduleSettlement("save")}requestManualScan(){if(!this.rootPath||!this.options.enabled)return;this.broker.requestScan({type:"scan",reason:"manual",root:this.rootPath})}getTooltipFragments(t){if(!this.rootPath||t.scheme!=="file")return[];let e=Ft(this.rootPath,t.fsPath);if(!e)return[];let s=this.tooltipAugments.get(e);if(!s)return[];let i=[];if(s.ruffViolations>0)i.push(`Ruff ${s.ruffViolations} violation${s.ruffViolations===1?"":"s"}`);if(s.loreLine)i.push(s.loreLine);return i}dispose(){if(this.scanTimer)clearInterval(this.scanTimer),this.scanTimer=null;if(this.settleTimer)clearTimeout(this.settleTimer),this.settleTimer=null;if(this.gitPollTimer)clearInterval(this.gitPollTimer),this.gitPollTimer=null;this.broker.dispose(),this.ledger.dispose(),this.disposables.forEach((t)=>t.dispose()),this.disposables.length=0}captureEntropyLeaves(t){if(!this.options.enabled)return;for(let e of t){let s=this.workerClient.getRecord(e);if(!s)continue;let i=this.tooltipAugments.get(s.path);this.merkle.upsert({path:s.path,entropy:s.entropy,complexity:s.complexity,debt:s.debt,freshness:s.freshness,ruffViolations:i?.ruffViolations??0,updatedAt:Date.now()})}}applyRuffSummary(t){if(!this.rootPath||!this.options.enabled)return;let e=[];for(let s of t){let i=this.tooltipAugments.get(s.path),n={ruffViolations:s.violations,loreLine:i?.loreLine};this.tooltipAugments.set(s.path,n);let o=mt.Uri.file(E.join(this.rootPath,s.path));e.push(o);let r=this.workerClient.getRecord(o);if(r){if(this.merkle.upsert({path:r.path,entropy:r.entropy,complexity:r.complexity,debt:r.debt,freshness:r.freshness,ruffViolations:s.violations,updatedAt:Date.now()}),r.entropy>=0.45||s.violations>0)this.broker.requestLore({type:"lore-request",root:this.rootPath,path:s.path,entropy:r.entropy,violations:s.violations})}}if(e.length>0)this.requestDecorationRefresh(e)}applyLore(t){if(!this.rootPath||!this.options.enabled)return;if(t.root!==this.rootPath)return;let e=this.tooltipAugments.get(t.path);this.tooltipAugments.set(t.path,{ruffViolations:e?.ruffViolations??t.violations,loreLine:t.line}),this.requestDecorationRefresh([mt.Uri.file(E.join(this.rootPath,t.path))])}startScanLoop(){if(this.scanTimer||!this.rootPath)return;let t=Math.max(this.options.pythonScanIntervalMs,1e4);this.scanTimer=setInterval(()=>{if(!this.rootPath)return;this.broker.requestScan({type:"scan",reason:"interval",root:this.rootPath})},t)}startGitWatcher(){if(!this.rootPath||this.gitPollTimer)return;this.gitHeadSnapshot=null,this.gitPollTimer=setInterval(async()=>{if(!this.rootPath)return;let t=await Fe(this.rootPath);if(!t)return;if(!this.gitHeadSnapshot){this.gitHeadSnapshot=t;return}if(t!==this.gitHeadSnapshot){if(this.gitHeadSnapshot=t,this.output.appendLine("[polyglot] git HEAD changed, scheduling Merkle settlement."),this.rootPath)this.broker.requestScan({type:"scan",reason:"commit",root:this.rootPath});this.scheduleSettlement("commit")}},6000)}scheduleSettlement(t){if(!this.options.enabled)return;if(this.pendingSettleReason=t==="commit"?"commit":this.pendingSettleReason??t,this.settleTimer)clearTimeout(this.settleTimer);this.settleTimer=setTimeout(()=>{this.settleTimer=null,this.flushSettlement()},Math.max(this.options.settleDebounceMs,300))}async flushSettlement(){let t=this.pendingSettleReason??"manual";this.pendingSettleReason=null;let e=this.merkle.settle(t);if(!e)return;let s=await this.ledger.commitEntropy(e),i=[`[polyglot] settled Merkle root ${e.rootHash.slice(0,16)}...`,`leaves=${e.leafCount}`,`mode=${s.mode}`];if(s.txSignature)i.push(`tx=${s.txSignature}`);i.push(`detail=${s.detail}`),this.output.appendLine(i.join(" "))}}async function Fe(t){let e=E.join(t,".git"),s=E.join(e,"HEAD"),i="";try{i=await gt.readFile(s,"utf8")}catch{return null}let n=i.trim();if(!n)return null;if(!n.startsWith("ref:"))return n;let o=n.slice(4).trim(),r=E.join(e,o);try{let l=await gt.readFile(r,"utf8");return`ref:${o}:${l.trim()}`}catch{return`ref:${o}:missing`}}function Ft(t,e){let s=E.relative(t,e);if(!s||s.startsWith("..")||E.isAbsolute(s))return null;return s.replace(/\\/g,"/")}var qt=c(require("path")),Ut=require("child_process"),T=c(require("vscode"));class yt{output;headlessVulkan;daemonBinaryOverride;rootPath=null;daemonProcess=null;requestCounter=1;pending=new Map;onDidReceiveManifestEmitter=new T.EventEmitter;onDidReceiveManifest=this.onDidReceiveManifestEmitter.event;onDidReceiveEnvEmitter=new T.EventEmitter;onDidReceiveEnv=this.onDidReceiveEnvEmitter.event;onDidReceiveSedimentEmitter=new T.EventEmitter;onDidReceiveSediment=this.onDidReceiveSedimentEmitter.event;onDidReceiveSedimentChunkEmitter=new T.EventEmitter;onDidReceiveSedimentChunk=this.onDidReceiveSedimentChunkEmitter.event;onDidReceiveSynapseEmitter=new T.EventEmitter;onDidReceiveSynapse=this.onDidReceiveSynapseEmitter.event;constructor(t,e,s){this.output=t;this.headlessVulkan=e;this.daemonBinaryOverride=s}start(t){this.rootPath=t,this.startDaemon()}async requestSediment(t,e){return this.submitRequest("reactor/sediment",{max_layers:t,max_files:e})}async requestSedimentStream(t,e,s=220){return this.submitRequest("reactor/sediment_stream",{max_layers:t,max_files:e,chunk_size:s})}async requestSedimentSynapse(t,e,s=220){return this.submitRequest("reactor/sediment_synapse",{max_layers:t,max_files:e,chunk_size:s})}async requestDetect(){return this.submitRequest("anno/detect",{})}async requestProvision(){return this.submitRequest("anno/provision",{})}dispose(){for(let[,t]of this.pending)t.reject(Error("AnnoClient disposed"));this.pending.clear(),this.daemonProcess?.kill(),this.daemonProcess=null,this.onDidReceiveManifestEmitter.dispose(),this.onDidReceiveEnvEmitter.dispose(),this.onDidReceiveSedimentEmitter.dispose(),this.onDidReceiveSedimentChunkEmitter.dispose(),this.onDidReceiveSynapseEmitter.dispose()}startDaemon(){if(!this.rootPath||this.daemonProcess)return;let t=this.daemonBinaryOverride??qe(this.rootPath),e=["--workspace",this.rootPath];if(this.headlessVulkan)e.push("--headless-vulkan");this.daemonProcess=Ut.spawn(t,e,{cwd:this.rootPath,stdio:["pipe","pipe","pipe"]});let s=M((i)=>this.handlePayload(i),(i)=>this.output.appendLine(`[daemon] invalid JSONL: ${i.message}`));this.daemonProcess.stdout?.on("data",(i)=>s.push(i)),this.daemonProcess.stderr?.on("data",(i)=>{this.output.appendLine(`[daemon] ${i.toString().trimEnd()}`)}),this.daemonProcess.on("error",(i)=>{this.output.appendLine(`[daemon] spawn failed: ${i.message}`),this.rejectAllPending(Error(`daemon spawn failed: ${i.message}`)),this.daemonProcess=null}),this.daemonProcess.on("exit",(i)=>{s.flush(),this.output.appendLine(`[daemon] exited with code ${i??-1}`),this.rejectAllPending(Error("daemon exited")),this.daemonProcess=null})}handlePayload(t){if("method"in t&&!("id"in t)){this.handleNotification(t);return}if("id"in t&&typeof t.id==="number")this.handleResponse(t)}handleNotification(t){let{method:e,params:s}=t;switch(e){case"anno/manifest":this.onDidReceiveManifestEmitter.fire(s),this.output.appendLine(`[daemon] ANNO manifest received (${s.languages?.length??0} languages)`);break;case"anno/env":this.onDidReceiveEnvEmitter.fire(s),this.output.appendLine("[daemon] env report received");break;case"reactor/status":{let i=s.status??"unknown";this.output.appendLine(`[daemon] reactor status: ${i}`);break}case"reactor/sedimentChunk":this.onDidReceiveSedimentChunkEmitter.fire(s);break;case"reactor/synapse":this.onDidReceiveSynapseEmitter.fire(s),this.output.appendLine(`[daemon] synapse status: ${s.status} (${s.mode})`);break;default:this.output.appendLine(`[daemon] unknown notification: ${e}`)}}handleResponse(t){let e=t.id,s=this.pending.get(e);if(!s)return;if(this.pending.delete(e),t.error&&typeof t.error==="object"){let i=t.error;s.reject(Error(i.message));return}s.resolve(t.result)}submitRequest(t,e){if(!this.daemonProcess?.stdin||this.daemonProcess.killed)this.startDaemon();if(!this.daemonProcess?.stdin)return Promise.reject(Error("daemon not available"));let s=this.requestCounter++,i={jsonrpc:"2.0",id:s,method:t,params:e};return new Promise((n,o)=>{this.pending.set(s,{resolve:n,reject:o}),this.daemonProcess?.stdin?.write(`${JSON.stringify(i)}
`,(r)=>{if(r)this.pending.delete(s),o(r)})})}rejectAllPending(t){for(let[e,s]of this.pending)this.pending.delete(e),s.reject(t)}}function qe(t){let e=process.platform==="win32"?"chthonic-daemon.exe":"chthonic-daemon";return qt.join(t,"native","target","release",e)}var P=c(require("vscode"));class vt{output;envCollection;disposed=!1;constructor(t,e){this.output=t;this.envCollection=e}async activate(){if(this.disposed)return;try{await P.commands.executeCommand("workbench.action.closeSidebar"),await P.commands.executeCommand("workbench.action.terminal.moveToSidePanel"),await P.commands.executeCommand("workbench.action.toggleAuxiliaryBar"),await P.commands.executeCommand("workbench.action.toggleMaximizedPanel"),await P.commands.executeCommand("workbench.action.focusActiveEditorGroup"),this.output.appendLine("[cockpit] layout activated: sidebar=closed, terminal=AuxBar, panel=maximized, editor=Center")}catch(t){this.output.appendLine(`[cockpit] layout activation failed: ${Ue(t)}`)}}applyTerminalEnv(t){if(this.disposed)return;if(!t.path_mutations.length&&!t.dev_kit)return;let e=t.path_mutations.sort((n,o)=>n.priority-o.priority).map((n)=>n.path),s=process.platform==="win32"?";":":";for(let n of e)this.envCollection.prepend("PATH",`${n}${s}`);if(t.dev_kit){for(let[n,o]of t.dev_kit.env_vars)this.envCollection.replace(n,o);for(let n of t.dev_kit.path_prepend)this.envCollection.prepend("PATH",`${n}${s}`)}for(let n of P.window.terminals)if(process.platform==="win32"){for(let o of e)n.sendText(`$env:PATH = "${o};$env:PATH"`,!0);if(t.dev_kit)for(let[o,r]of t.dev_kit.env_vars)n.sendText(`$env:${o} = "${r}"`,!0)}else{for(let o of e)n.sendText(`export PATH="${o}:$PATH"`,!0);if(t.dev_kit)for(let[o,r]of t.dev_kit.env_vars)n.sendText(`export ${o}="${r}"`,!0)}let i=e.length+(t.dev_kit?.env_vars.length??0);if(this.output.appendLine(`[cockpit] terminal env updated: ${i} mutations applied`),t.warnings.length>0)for(let n of t.warnings)this.output.appendLine(`[cockpit] warning: ${n}`)}dispose(){this.disposed=!0}}function Ue(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}var Nt=c(require("fs")),bt=c(require("path"));class SynapseBridge{output;extensionRoot;binding=null;reader=null;descriptor=null;transportMode;constructor(t,e,s){this.output=t;this.extensionRoot=e;this.transportMode=Ve(s)}updateDescriptor(t){if(this.descriptor=t,this.transportMode==="jsonl"){this.output.appendLine("[synapse] disabled by transport=jsonl");return}if(t.status!=="ready"||t.mode!=="shared_memory"||!t.shm_id){this.output.appendLine(`[synapse] unavailable: ${t.reason??t.status}`);return}try{let e=this.ensureBindingLoaded();this.reader=new e.SynapseReader(t.shm_id,t.event_name??void 0),this.output.appendLine(`[synapse] connected (shm=${t.shm_id})`)}catch(e){this.reader=null,this.output.appendLine(`[synapse] init failed, falling back to JSONL: ${Ne(e)}`)}}isReady(){if(this.transportMode==="jsonl")return!1;return this.reader!==null&&this.descriptor?.status==="ready"&&this.descriptor.mode==="shared_memory"}async drain(t,e){if(!this.reader||t.transport!=="shared_memory")return 0;let s=Math.max(0,t.chunks_written??t.total_chunks??0);if(s===0)return 0;let i=0,n=Date.now();while(i<s&&Date.now()-n<4000){if(!this.reader.wait_for_signal(120)){await Vt();continue}while(!0){let r=this.reader.read_chunk();if(!r||r.byteLength===0)break;let l=new Uint8Array(r.buffer,r.byteOffset,r.byteLength),u=new Uint8Array(l.byteLength);if(u.set(l),e(u),i+=1,i>=s)break}await Vt()}if(i<s)this.output.appendLine(`[synapse] partial drain: ${i}/${s}`);return i}dispose(){this.reader=null}ensureBindingLoaded(){if(this.binding)return this.binding;let candidates=[bt.join(this.extensionRoot,"src","reactor","synapse.node"),bt.join(this.extensionRoot,"native","target","release","synapse.node")],existing=candidates.find((t)=>Nt.existsSync(t));if(!existing)throw Error(`synapse.node not found in ${candidates.join(", ")}`);let req=eval("require");return this.binding=req(existing),this.binding}}function Ve(t){let e=t.trim().toLowerCase();if(e==="shared_memory")return"shared_memory";if(e==="jsonl")return"jsonl";return"auto"}function Ne(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}async function Vt(){await new Promise((t)=>setTimeout(t,0))}var k=c(require("vscode"));var Jt=c(require("fs")),zt=c(require("path")),Je=[{file:"uv.lock",weight:25},{file:"Cargo.toml",weight:22},{file:"mise.toml",weight:18},{file:".mise.toml",weight:8},{file:".ruby-version",weight:10},{file:"go.mod",weight:10},{file:"native/Cargo.toml",weight:7}];async function Qt(t){let e=Je.map((n)=>{let o=zt.join(t,n.file),r=Jt.existsSync(o);return{...n,present:r}}),s=Math.min(100,e.reduce((n,o)=>o.present?n+o.weight:n,0)),i=ze(s);return{score:s,tier:i,markers:e,present:e.filter((n)=>n.present).map((n)=>n.file),missing:e.filter((n)=>!n.present).map((n)=>n.file)}}function Wt(t){switch(t){case"loom":return"loom.svg";case"lens":return"lens.svg";default:return"gate.svg"}}function ze(t){if(t>=80)return"loom";if(t>=45)return"lens";return"gate"}class xt{extensionUri;output;containerId;fallbackItem;proposalAvailable=null;constructor(t,e,s="chthonic-archive"){this.extensionUri=t;this.output=e;this.containerId=s;this.fallbackItem=k.window.createStatusBarItem(k.StatusBarAlignment.Left,47),this.fallbackItem.command="chthonic.refreshRustification",this.fallbackItem.tooltip="Rustification score and activity bar icon fallback",this.fallbackItem.show()}async update(t){await k.commands.executeCommand("setContext","chthonic.rustificationTier",t.tier),await k.commands.executeCommand("setContext","chthonic.rustificationScore",t.score);let e=k.Uri.joinPath(this.extensionUri,"resources",Wt(t.tier));if(!await this.tryApplyProposedIcon(e))this.updateFallbackStatus(t);else this.fallbackItem.text=`$(pulse) Slab ${t.score}%`,this.fallbackItem.backgroundColor=void 0}dispose(){this.fallbackItem.dispose()}async tryApplyProposedIcon(t){if(this.proposalAvailable===!1)return!1;let e=k.window,s=["setActivityBarIcon","updateActivityBarIcon","setViewContainerIcon","updateViewContainerIcon"];for(let i of s){let n=e[i];if(typeof n!=="function")continue;try{return await n(this.containerId,t),this.proposalAvailable=!0,!0}catch(o){this.output.appendLine(`[morph] ${i} failed: ${We(o)}`)}}return this.proposalAvailable=!1,!1}updateFallbackStatus(t){let e=Qe(t.tier);this.fallbackItem.text=`$(pulse) ${e} ${t.score}%`,this.fallbackItem.tooltip=`Rustification ${t.score}%
Present: ${t.present.join(", ")||"none"}
Missing: ${t.missing.join(", ")||"none"}`}}function Qe(t){switch(t){case"loom":return"Loom";case"lens":return"Lens";default:return"Gate"}}function We(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}var L=c(require("vscode"));class St{output;constructor(t){this.output=t}async activate(){let t=await this.tryProposedLayout();if(!t)await this.applyCommandFallback();await L.commands.executeCommand("workbench.view.extension.chthonic-archive"),await L.commands.executeCommand("chthonic.loomView.focus"),this.output.appendLine(`[deep-focus] activated via ${t?"proposed-api":"command-fallback"} lane`)}async tryProposedLayout(){let t=L.window,e=t.moveViewTo;if(typeof e!=="function")return!1;let s=[t.ViewContainerLocation&&t.ViewContainerLocation.AuxiliaryBar,"auxiliaryBar","secondarySidebar"];for(let i of s){if(!i)continue;try{return await e("terminal",i),!0}catch(n){this.output.appendLine(`[deep-focus] proposed moveViewTo failed: ${Kt(n)}`)}}return!1}async applyCommandFallback(){try{await L.commands.executeCommand("workbench.action.terminal.moveToSidePanel"),await L.commands.executeCommand("workbench.action.toggleAuxiliaryBar"),await L.commands.executeCommand("workbench.action.focusActiveEditorGroup")}catch(t){this.output.appendLine(`[deep-focus] fallback layout failed: ${Kt(t)}`)}}}function Kt(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}var K=c(require("vscode"));class G{static viewType="chthonic.loomView";view=null;report=null;resolveWebviewView(t,e,s){this.view=t,t.webview.options={enableScripts:!0},t.webview.html=this.buildHtml(),t.webview.onDidReceiveMessage((i)=>{if(!i||typeof i!=="object")return;let n=i;if(n.type==="refresh")K.commands.executeCommand("chthonic.refreshRustification");if(n.type==="heal")K.commands.executeCommand("chthonic.slabHeal");if(n.type==="deepFocus")K.commands.executeCommand("chthonic.deepFocus")}),this.postState()}update(t){this.report=t,this.postState()}dispose(){this.view=null}postState(){if(!this.view||!this.report)return;this.view.webview.postMessage({type:"state",report:this.report})}buildHtml(){let t=Ke();return`<!DOCTYPE html>
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
</html>`}}function Ke(){let e="";for(let s=0;s<24;s+=1)e+="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789".charAt(Math.floor(Math.random()*62));return e}var m=c(require("fs")),y=c(require("path")),Y=c(require("child_process")),Xt=c(require("vscode"));class kt{output;envCollection;workspaceRoot;timer=null;running=!1;options={intervalMs:21600000,eolApiBase:"https://endoflife.date/api"};constructor(t,e,s){this.output=t;this.envCollection=e;this.workspaceRoot=s}start(t){this.options=t,this.stopTimer(),this.timer=setInterval(()=>{this.runNow("interval")},Math.max(60000,t.intervalMs))}async runNow(t="manual"){if(this.running){this.output.appendLine("[slab-heal] skipped; already running");return}this.running=!0;try{let e=await this.collectRuntimeStates();if(e.length===0){this.output.appendLine("[slab-heal] no runtime states detected; skipping");return}let s=[];for(let i of e)if(await this.isEol(i.language,i.version))s.push(i);if(s.length===0){this.output.appendLine(`[slab-heal] ${t}: all slab runtimes are supported`);return}this.output.appendLine(`[slab-heal] ${t}: stale runtimes detected: ${s.map((i)=>`${i.language}@${i.version}`).join(", ")}`),await this.repair(s)}catch(e){this.output.appendLine(`[slab-heal] run failed: ${Et(e)}`)}finally{this.running=!1}}dispose(){this.stopTimer()}stopTimer(){if(this.timer)clearInterval(this.timer),this.timer=null}async collectRuntimeStates(){let t=[{language:"python",command:"python",args:["-c",'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")']},{language:"ruby",command:"ruby",args:["-e","print RUBY_VERSION"]},{language:"go",command:"go",args:["env","GOVERSION"]}],e=[];for(let s of t)try{let i=await Zt(s.command,s.args,this.workspaceRoot),n=Ye(i,s.language);if(!n)continue;e.push({language:s.language,version:n})}catch(i){this.output.appendLine(`[slab-heal] probe ${s.language} failed: ${Et(i)}`)}return e}async isEol(t,e){let s=await fetch(`${this.options.eolApiBase}/${t}.json`,{headers:{accept:"application/json"}});if(!s.ok)throw Error(`endoflife query failed for ${t}: ${s.status}`);let i=await s.json();if(!Array.isArray(i))return!1;let n=Xe(t,e),o=i.find((l)=>{let u=l;return u.cycle===n||u.cycle===n.split(".").slice(0,1).join(".")});if(!o||o.eol==null)return!1;if(typeof o.eol==="boolean")return o.eol;let r=Date.parse(o.eol);if(Number.isNaN(r))return!1;return r<=Date.now()}async repair(t){await Yt("mise",["upgrade"],this.workspaceRoot,this.output),await Yt("mise",["reshim"],this.workspaceRoot,this.output);let e=await this.relinkVsHeaders();if(e)this.output.appendLine(`[slab-heal] relinked MSVC headers at ${e}`);else this.output.appendLine("[slab-heal] VS include relink skipped (MSVC path not found)");Xt.window.showInformationMessage(`Chthonic self-heal complete: ${t.map((s)=>`${s.language}@${s.version}`).join(", ")}`)}async relinkVsHeaders(){let t=await Ge(this.workspaceRoot);if(!t||!this.workspaceRoot)return null;let e=y.join(this.workspaceRoot,".chthonic","native","msvc"),s=y.join(e,"include");m.mkdirSync(e,{recursive:!0});try{m.rmSync(s,{recursive:!0,force:!0})}catch{}try{m.symlinkSync(t,s,"junction")}catch(i){let n=y.join(e,"include.path.txt");m.writeFileSync(n,t,"utf8"),this.output.appendLine(`[slab-heal] symlink failed; wrote include manifest ${n}: ${Et(i)}`)}return this.envCollection.replace("CHTHONIC_VS_CPP_INCLUDE",t),this.envCollection.prepend("INCLUDE",`${t};`),t}}async function Ge(t){let e=y.join(process.env["ProgramFiles(x86)"]||"C:\\Program Files (x86)","Microsoft Visual Studio","Installer","vswhere.exe");if(m.existsSync(e))try{let i=await Zt(e,["-latest","-products","*","-requires","Microsoft.VisualStudio.Component.VC.Tools.x86.x64","-property","installationPath"],t),n=Gt(i.trim());if(n)return n}catch{}let s=["C:\\Program Files\\Microsoft Visual Studio\\2026","C:\\Program Files\\Microsoft Visual Studio\\2022"];for(let i of s){let n=Gt(i);if(n)return n}return null}function Gt(t){if(!m.existsSync(t))return null;let e=[],s=[t];while(s.length>0){let i=s.pop(),n=[];try{n=m.readdirSync(i,{withFileTypes:!0})}catch{continue}for(let o of n){let r=y.join(i,o.name);if(!o.isDirectory())continue;if(o.name==="include"&&r.includes(`${y.sep}VC${y.sep}Tools${y.sep}MSVC${y.sep}`)){e.push(r);continue}s.push(r)}}if(e.length===0)return null;return e.sort((i,n)=>n.localeCompare(i,void 0,{numeric:!0,sensitivity:"base"})),e[0]}async function Zt(t,e,s){return new Promise((i,n)=>{Y.execFile(t,e,{cwd:s||void 0,windowsHide:!0,timeout:15000},(o,r,l)=>{if(o){n(Error(`${t} ${e.join(" ")} failed: ${l||o.message}`));return}i(String(r).trim())})})}async function Yt(t,e,s,i){await new Promise((n,o)=>{let r=Y.spawn(t,e,{cwd:s||void 0,windowsHide:!0,stdio:["ignore","pipe","pipe"]});r.stdout.on("data",(l)=>{i.appendLine(`[slab-heal] ${l.toString().trimEnd()}`)}),r.stderr.on("data",(l)=>{i.appendLine(`[slab-heal] ${l.toString().trimEnd()}`)}),r.on("error",o),r.on("exit",(l)=>{if(l===0)n();else o(Error(`${t} ${e.join(" ")} exited with code ${l??-1}`))})})}function Ye(t,e){let s=t.trim();if(!s)return"";switch(e){case"go":return s.replace(/^go/i,"");default:return s}}function Xe(t,e){let s=e.split(".");if(t==="go")return s.slice(0,2).join(".");return s.slice(0,2).join(".")}function Et(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}function Ze(t){console.log("☥ Chthonic Archive extension activated");let e=a.window.createOutputChannel("Chthonic SDK"),s=a.workspace.workspaceFolders?.[0]?.uri.fsPath||null,i=j.join(s||"","meta-ide","copilot-sdk","harness.ts"),n=new V(t.extensionUri,i,(d)=>e.appendLine(`[${new Date().toISOString()}] ${d}`));t.subscriptions.push(a.window.registerWebviewViewProvider(V.viewType,n));let o=new xt(t.extensionUri,e),r=new St(e),l=new G,u=new kt(e,t.environmentVariableCollection,s);t.subscriptions.push(o,l,u,a.window.registerWebviewViewProvider(G.viewType,l));let p=a.workspace.getConfiguration("chthonic"),I=p.get("entropy.enabled",!0),h=p.get("entropy.maxFiles",1e4),v=p.get("entropy.scanIntervalMs",20000),Z=p.get("entropy.decorationDebounceMs",120),f=p.get("entropy.decorationBatchSize",240),ne=p.get("entropy.polyglotEnabled",!0),oe=p.get("entropy.pythonScanIntervalMs",30000),re=p.get("entropy.ledgerSettleDebounceMs",1400),ae=p.get("entropy.ledgerMode","validator"),de=p.get("entropy.solanaRpcUrl","http://127.0.0.1:8899"),ce=p.get("entropy.solanaAutostartValidator",!1),le=X(p.get("entropy.solanaLedgerHostBinaryPath","")),pe=X(p.get("entropy.solanaWalletPath","")),ue=X(p.get("entropy.solanaIdlPath","")),b=new ot(t,e),F,$=new ft(e,b,{enabled:ne,pythonScanIntervalMs:oe,settleDebounceMs:re,ledgerMode:ae,solanaRpcUrl:de,solanaAutostartValidator:ce,solanaLedgerHostBinaryPath:le,solanaWalletPath:pe,solanaIdlPath:ue},(d)=>F?.enqueueExternalUpdates(d));F=new at(b,Z,f,(d)=>$.getTooltipFragments(d));let R=new N(t.extensionUri,b);R.setRootPath(s),t.subscriptions.push(b,F,R,$,a.window.registerFileDecorationProvider(F),a.window.registerWebviewViewProvider(N.viewType,R));let A=async(d)=>{if(!s)return;let g=await Qt(s);l.update(g),await o.update(g),e.appendLine(`[monolith] rustification ${g.score}% (${g.tier}) via ${d}`)};if(s){A("startup");let d=a.workspace.createFileSystemWatcher(new a.RelativePattern(s,"{uv.lock,Cargo.toml,mise.toml,.mise.toml,go.mod,.ruby-version}"));t.subscriptions.push(d,d.onDidCreate(()=>{A("marker-create")}),d.onDidChange(()=>{A("marker-change")}),d.onDidDelete(()=>{A("marker-delete")}))}if(s&&I)b.start(s,h,v),$.start(s);t.subscriptions.push(a.workspace.onDidSaveTextDocument((d)=>{b.refreshFile(d.uri),$.onDidSaveDocument(d)})),t.subscriptions.push(a.commands.registerCommand("chthonic.entropyRefresh",()=>{b.rescanNow(),b.requestGraph(260),$.requestManualScan(),a.window.showInformationMessage("Chthonic entropy scan requested")}));let he=p.get("reactor.enabled",!0),ge=p.get("reactor.headlessVulkan",!0),me=p.get("reactor.cockpitAutoLayout",!1),fe=p.get("reactor.transport","auto"),ye=X(p.get("reactor.daemonBinaryPath","")),ve=p.get("slab.selfHealingEnabled",!0),be=p.get("slab.selfHealingIntervalMs",21600000),xe=p.get("slab.eolApiBase","https://endoflife.date/api"),x=new yt(e,ge,ye),q=new vt(e,t.environmentVariableCollection),tt=new SynapseBridge(e,t.extensionPath,fe);if(t.subscriptions.push(x,q,tt),t.subscriptions.push(x.onDidReceiveEnv((d)=>{q.applyTerminalEnv(d)}),x.onDidReceiveSediment((d)=>{R.postSedimentData(d)}),x.onDidReceiveSedimentChunk((d)=>{R.postSedimentChunk(d)}),x.onDidReceiveSynapse((d)=>{tt.updateDescriptor(d)})),R.onRequestSediment(()=>{es(x,R,tt,e)}),s&&he){if(x.start(s),me)q.activate();let d=j.join(s,".git","HEAD");if(C.existsSync(d)){let g=null,_=C.watch(j.join(s,".git"),{persistent:!1},(st,Rt)=>{if(Rt==="HEAD"||Rt?.startsWith("refs")){if(g)clearTimeout(g);g=setTimeout(()=>{e.appendLine("[reactor] git change detected, recomputing sediment"),x.requestSediment(10,500).catch((Se)=>{e.appendLine(`[reactor] live-loop sediment failed: ${Se}`)})},800)}});t.subscriptions.push({dispose:()=>_.close()})}}if(s&&ve)u.start({intervalMs:be,eolApiBase:xe}),u.runNow("interval");t.subscriptions.push(a.commands.registerCommand("chthonic.activateCockpit",()=>{q.activate()}),a.commands.registerCommand("chthonic.deepFocus",()=>{r.activate()}),a.commands.registerCommand("chthonic.slabHeal",()=>{u.runNow("manual")}),a.commands.registerCommand("chthonic.refreshRustification",()=>{A("manual-command")}),a.commands.registerCommand("chthonic.annoDetect",()=>{if(s)x.start(s);a.window.showInformationMessage("ANNO project detection triggered")}),a.commands.registerCommand("chthonic.reactorSediment",async()=>{try{let d=await x.requestSediment(10,500);a.window.showInformationMessage(`Sediment computed: ${d.file_count} files, ${d.layer_count} layers (${d.backend}, ${d.compute_time_ms}ms)`)}catch(d){a.window.showErrorMessage(`Sediment computation failed: ${d}`)}}));let et=new se;a.window.registerTreeDataProvider("chthonic.themeView",et),t.subscriptions.push(a.commands.registerCommand("chthonic.switchTheme",async()=>{let d=[{label:"$(paintcan) Flesh & Earth",description:"Warm earth · WCAG AA · Distribution palette",id:"Chthonic Mandala - Flesh & Earth"},{label:"$(zap) ROGBIV",description:"SSOT spectral · FA¹⁻⁵ canonical hexes",id:"Chthonic Mandala - ROGBIV"}],g=a.workspace.getConfiguration("workbench").get("colorTheme"),_=await a.window.showQuickPick(d.map((st)=>({...st,picked:g===st.id})),{placeHolder:`Current: ${g}`});if(_)await a.workspace.getConfiguration("workbench").update("colorTheme",_.id,a.ConfigurationTarget.Workspace),a.window.showInformationMessage(`Theme: ${_.id}`),et.refresh()}));let Pt=a.workspace.getConfiguration("chthonic");if(Pt.get("showSSOTHash",!0)){let d=a.window.createStatusBarItem(a.StatusBarAlignment.Left,50);d.command="chthonic.verifySSOT",d.tooltip="SSOT integrity hash — click to verify",t.subscriptions.push(d),te(d),t.subscriptions.push(a.workspace.onDidSaveTextDocument((g)=>{if(g.fileName.includes("copilot-instructions"))te(d)}))}if(Pt.get("showLineage",!0)){let d=a.window.createStatusBarItem(a.StatusBarAlignment.Left,49);d.text="$(git-branch) ☥ main",d.tooltip="Chthonic lineage",d.show(),t.subscriptions.push(d)}let Lt=new ie;a.window.registerTreeDataProvider("chthonic.statusView",Lt),t.subscriptions.push(a.commands.registerCommand("chthonic.verifySSOT",async()=>{let d=wt();if(d)a.window.showInformationMessage(`SSOT SHA-256: ${d.substring(0,16)}…`);else a.window.showWarningMessage("SSOT file not found")})),t.subscriptions.push(a.commands.registerCommand("chthonic.refreshStatus",()=>{Lt.refresh(),et.refresh(),b.rescanNow(),b.requestGraph(260),$.requestManualScan(),A("refresh-status")}))}function ts(){}async function es(t,e,s,i){try{if(s.isReady()){let n=await t.requestSedimentSynapse(10,500,220);if(n.transport==="shared_memory"){let o=await s.drain(n,(r)=>{e.postSedimentBinary(r)});i.appendLine(`[reactor] synapse drain ${o}/${n.chunks_written} chunks`);return}}await t.requestSedimentStream(10,500)}catch(n){i.appendLine(`[reactor] sediment request failed: ${n}`)}}function wt(){let t=a.workspace.workspaceFolders?.[0];if(!t)return null;let e=a.workspace.getConfiguration("chthonic").get("ssotPath",".github/copilot-instructions.md"),s=j.join(t.uri.fsPath,e);if(!C.existsSync(s))return null;let n=C.readFileSync(s,"utf-8").replace(/\r\n/g,`
`).replace(/\r/g,`
`).split(`
`).map((o)=>o.trimEnd()).join(`
`).trim();return ee.createHash("sha256").update(n,"utf-8").digest("hex")}function te(t){let e=wt();if(e)t.text=`$(shield) ${e.substring(0,8)}`,t.show();else t.text="$(shield) SSOT ??",t.show()}function X(t){let e=t.trim();return e.length>0?e:void 0}class se{_onDidChange=new a.EventEmitter;onDidChangeTreeData=this._onDidChange.event;refresh(){this._onDidChange.fire()}getTreeItem(t){return t}getChildren(){let t=a.workspace.getConfiguration("workbench").get("colorTheme")||"";return[{name:"Chthonic Mandala - Flesh & Earth",short:"Flesh & Earth",icon:"\uD83C\uDF0D",desc:"Warm earth · Distribution"},{name:"Chthonic Mandala - ROGBIV",short:"ROGBIV",icon:"\uD83C\uDF08",desc:"SSOT spectral · Research"}].map((s)=>{let i=t===s.name,n=new a.TreeItem(`${i?"◉":"○"} ${s.icon} ${s.short}`,a.TreeItemCollapsibleState.None);return n.tooltip=`${s.name}
${s.desc}${i?`

✅ ACTIVE`:""}`,n.description=i?"active":"",n.command={command:"chthonic.switchTheme",title:"Switch"},n})}}class ie{_onDidChange=new a.EventEmitter;onDidChangeTreeData=this._onDidChange.event;refresh(){this._onDidChange.fire()}getTreeItem(t){return t}getChildren(){let t=wt(),e=[],s=new a.TreeItem(`$(shield) SSOT: ${t?t.substring(0,12)+"…":"not found"}`,a.TreeItemCollapsibleState.None);s.command={command:"chthonic.verifySSOT",title:"Verify"},e.push(s);let i=new a.TreeItem(`$(paintcan) Theme: ${(a.workspace.getConfiguration("workbench").get("colorTheme")||"default").replace("Chthonic Mandala - ","")}`,a.TreeItemCollapsibleState.None);return i.command={command:"chthonic.switchTheme",title:"Switch"},e.push(i),e}}
