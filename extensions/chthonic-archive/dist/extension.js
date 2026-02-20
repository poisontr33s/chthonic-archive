var Te=Object.create;var{getPrototypeOf:Ae,defineProperty:H,getOwnPropertyNames:qt,getOwnPropertyDescriptor:_e}=Object,Ht=Object.prototype.hasOwnProperty;var d=(t,e,i)=>{i=t!=null?Te(Ae(t)):{};let s=e||!t||!t.__esModule?H(i,"default",{value:t,enumerable:!0}):i;for(let n of qt(t))if(!Ht.call(s,n))H(s,n,{get:()=>t[n],enumerable:!0});return s},It=new WeakMap,Ie=(t)=>{var e=It.get(t),i;if(e)return e;if(e=H({},"__esModule",{value:!0}),t&&typeof t==="object"||typeof t==="function")qt(t).map((s)=>!Ht.call(e,s)&&H(e,s,{get:()=>t[s],enumerable:!(i=_e(t,s))||i.enumerable}));return It.set(t,e),e};var qe=(t,e)=>{for(var i in e)H(t,i,{get:e[i],enumerable:!0,configurable:!0,set:(s)=>e[i]=()=>s})};var bi={};qe(bi,{deactivate:()=>gi,activate:()=>mi});module.exports=Ie(bi);var r=d(require("vscode")),re=d(require("crypto")),M=d(require("fs")),U=d(require("path"));var Nt=d(require("vscode")),at=d(require("child_process"));var Ot=d(require("child_process")),jt=d(require("readline")),z=d(require("path"));class rt{harnessPath;log;process=null;rl=null;handlers=new Set;authenticated=!1;ready=!1;constructor(t,e){this.harnessPath=t;this.log=e}async start(){if(this.process)return;let t=z.dirname(this.harnessPath),e=z.basename(this.harnessPath);this.process=Ot.spawn("bun",["run",e],{cwd:t,stdio:["pipe","pipe","pipe"],env:{...process.env}}),this.process.stderr?.on("data",(i)=>{this.log(`[harness stderr] ${i.toString().trim()}`)}),this.process.on("close",(i)=>{this.log(`[harness] exited with code ${i}`),this.process=null,this.rl=null,this.ready=!1,this.authenticated=!1}),this.rl=jt.createInterface({input:this.process.stdout}),this.rl.on("line",(i)=>{try{let s=JSON.parse(i);if(s.type==="ready")this.ready=!0,this.log(`[harness] ready: ${s.sdk}`);for(let n of this.handlers)n(s)}catch{this.log(`[harness] non-JSON: ${i.substring(0,200)}`)}}),await new Promise((i,s)=>{let n=setTimeout(()=>s(Error("Harness startup timeout")),15000),a=(c)=>{if(c.type==="ready")clearTimeout(n),this.handlers.delete(a),i()};this.handlers.add(a)})}async authenticate(t,e){this.send({cmd:"auth",token:t,login:e}),await this.waitFor("auth_ok"),this.authenticated=!0,this.log(`[harness] authenticated as ${e}`)}query(t,e,i,s,n){return new Promise((a,c)=>{let p=(g)=>{if(g.id!==t)return;if(g.type==="event"&&g.event)s(g.event);else if(g.type==="done")this.handlers.delete(p),a();else if(g.type==="cancelled")this.handlers.delete(p),a();else if(g.type==="error")this.handlers.delete(p),c(Error(g.message||"Query failed"))};this.handlers.add(p),this.send({cmd:"query",id:t,prompt:e,workingDirectory:i,model:n?.model,reasoningEffort:n?.reasoningEffort})})}cancel(t){this.send({cmd:"cancel",id:t})}async getModels(){return this.send({cmd:"models"}),(await this.waitFor("models")).data||[]}isReady(){return this.ready&&this.authenticated&&this.process!==null}stop(){if(this.process)this.process.kill(),this.process=null;this.rl=null,this.ready=!1,this.authenticated=!1,this.handlers.clear()}send(t){if(!this.process?.stdin?.writable)throw Error("Harness not running");this.process.stdin.write(JSON.stringify(t)+`
`)}waitFor(t,e=15000){return new Promise((i,s)=>{let n=setTimeout(()=>{this.handlers.delete(a),s(Error(`Timeout waiting for ${t}`))},e),a=(c)=>{if(c.type===t)clearTimeout(n),this.handlers.delete(a),i(c);else if(c.type==="error")clearTimeout(n),this.handlers.delete(a),s(Error(c.message||"Error"))};this.handlers.add(a)})}}class F{extensionUri;harnessPath;log;static viewType="chthonic.chatView";view;connection=null;isConnecting=!1;activeQueryId=null;constructor(t,e,i){this.extensionUri=t;this.harnessPath=e;this.log=i}resolveWebviewView(t,e,i){this.view=t,t.webview.options={enableScripts:!0,localResourceRoots:[this.extensionUri]},t.webview.html=this.getHtml(),t.webview.onDidReceiveMessage(async(s)=>{switch(s.type){case"connect":await this.connectAgent();break;case"prompt":await this.sendPrompt(s.text);break;case"cancel":this.cancelQuery();break;case"disconnect":this.disconnectAgent();break}})}async connectAgent(){if(this.isConnecting||this.connection?.isReady())return;this.isConnecting=!0,this.postMessage({type:"status",status:"connecting"});try{this.connection=new rt(this.harnessPath,this.log),await this.connection.start();let t=at.execSync("gh auth token",{encoding:"utf-8"}).trim(),e=at.execSync("gh api user --jq .login",{encoding:"utf-8"}).trim();await this.connection.authenticate(t,e),this.postMessage({type:"connected",agentName:"Chthonic SDK",agentVersion:"0.1.0",login:e}),this.log(`Chat connected: ${e}`)}catch(t){this.log(`Chat connect failed: ${t.message}`),this.postMessage({type:"error",message:t.message}),this.connection?.stop(),this.connection=null}finally{this.isConnecting=!1}}async sendPrompt(t){if(!this.connection?.isReady()){this.postMessage({type:"error",message:"Not connected"});return}let e=crypto.randomUUID();this.activeQueryId=e,this.postMessage({type:"prompt-start"});let i=Nt.workspace.workspaceFolders?.[0]?.uri.fsPath||process.cwd();try{await this.connection.query(e,t,i,(s)=>this.handleSdkEvent(s))}catch(s){this.postMessage({type:"error",message:s.message})}finally{this.activeQueryId=null,this.postMessage({type:"prompt-end"})}}handleSdkEvent(t){switch(t.type){case"assistant.message":if(t.data?.content)this.postMessage({type:"agent-message",content:t.data.content});break;case"assistant.message.delta":if(t.data?.delta)this.postMessage({type:"agent-delta",delta:t.data.delta});break;case"tool.execution_start":this.postMessage({type:"tool-start",name:t.data?.name,args:t.data?.arguments});break;case"tool.execution_complete":this.postMessage({type:"tool-end",name:t.data?.name});break;case"assistant.reasoning":this.postMessage({type:"reasoning"});break;case"assistant.usage":this.postMessage({type:"usage",model:t.data?.model,inputTokens:t.data?.inputTokens,outputTokens:t.data?.outputTokens,duration:t.data?.duration});break;case"session.usage_info":this.postMessage({type:"context-info",tokenLimit:t.data?.tokenLimit,currentTokens:t.data?.currentTokens});break}}cancelQuery(){if(this.activeQueryId&&this.connection)this.connection.cancel(this.activeQueryId)}disconnectAgent(){this.connection?.stop(),this.connection=null,this.activeQueryId=null,this.postMessage({type:"disconnected"})}postMessage(t){this.view?.webview.postMessage(t)}dispose(){this.connection?.stop()}getHtml(){return`<!DOCTYPE html>
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
</html>`}}var O=d(require("path")),D=d(require("vscode")),Ut=require("worker_threads");class ct{extensionContext;output;records=new Map;recordUris=new Map;onDidUpdateRecordsEmitter=new D.EventEmitter;onDidUpdateRecords=this.onDidUpdateRecordsEmitter.event;onDidUpdateGraphEmitter=new D.EventEmitter;onDidUpdateGraph=this.onDidUpdateGraphEmitter.event;onDidUpdateSnapshotEmitter=new D.EventEmitter;onDidUpdateSnapshot=this.onDidUpdateSnapshotEmitter.event;worker=null;rootPath=null;workerPath;maxFiles=1e4;lastScanDurationMs=0;lastScanAt=0;scanTimer=null;disposed=!1;constructor(t,e){this.extensionContext=t;this.output=e;this.workerPath=t.asAbsolutePath(O.join("dist","entropy-worker.js"))}start(t,e,i){this.rootPath=t,this.maxFiles=e,this.ensureWorker(),this.send({type:"scan",root:t,maxFiles:this.maxFiles}),this.scheduleScanLoop(i)}rescanNow(){if(!this.rootPath)return;this.send({type:"scan",root:this.rootPath,maxFiles:this.maxFiles})}refreshFile(t){if(!this.rootPath||t.scheme!=="file")return;this.send({type:"refresh-file",root:this.rootPath,path:t.fsPath})}requestGraph(t){this.send({type:"graph",limit:t})}getRecord(t){if(!this.rootPath||t.scheme!=="file")return;let e=He(O.relative(this.rootPath,t.fsPath));return this.records.get(e)}getSnapshot(t=40){let e=Array.from(this.records.values()),i=e.length===0?0:e.reduce((n,a)=>n+a.entropy,0)/e.length,s=e.sort((n,a)=>a.entropy-n.entropy).slice(0,t);return{totalFiles:e.length,topEntropy:s,averageEntropy:i,lastScanDurationMs:this.lastScanDurationMs,lastScanAt:this.lastScanAt}}dispose(){if(this.disposed=!0,this.scanTimer)clearInterval(this.scanTimer),this.scanTimer=null;this.send({type:"stop"}),this.worker?.terminate(),this.worker=null,this.onDidUpdateRecordsEmitter.dispose(),this.onDidUpdateGraphEmitter.dispose(),this.onDidUpdateSnapshotEmitter.dispose()}scheduleScanLoop(t){if(this.scanTimer)clearInterval(this.scanTimer);let e=Math.max(5000,t);this.scanTimer=setInterval(()=>{if(!this.disposed)this.rescanNow()},e)}ensureWorker(){if(this.worker)return;this.worker=new Ut.Worker(this.workerPath),this.worker.on("message",(t)=>this.handleWorkerEvent(t)),this.worker.on("error",(t)=>{this.output.appendLine(`[entropy] worker error: ${t.message}`)}),this.worker.on("exit",(t)=>{if(this.output.appendLine(`[entropy] worker exited with code ${t}`),this.worker=null,!this.disposed&&t!==0)this.ensureWorker(),this.rescanNow()})}send(t){this.ensureWorker(),this.worker?.postMessage(t)}handleWorkerEvent(t){switch(t.type){case"scan-progress":{if(!this.rootPath)return;let e=[];for(let i of t.records){this.records.set(i.path,i);let s=this.recordUris.get(i.path);if(!s)s=D.Uri.file(O.join(this.rootPath,i.path)),this.recordUris.set(i.path,s);e.push(s)}if(e.length>0)this.onDidUpdateRecordsEmitter.fire(e);break}case"scan-complete":this.lastScanDurationMs=t.durationMs,this.lastScanAt=Date.now(),this.onDidUpdateSnapshotEmitter.fire(this.getSnapshot());break;case"graph-result":this.onDidUpdateGraphEmitter.fire(t.graph);break;case"error":this.output.appendLine(`[entropy] ${t.message}${t.detail?`
${t.detail}`:""}`);break}}}function He(t){return t.replace(/\\/g,"/")}var B=d(require("vscode"));class dt{workerClient;debounceMs;maxPerFlush;tooltipAugmentProvider;onDidChangeEmitter=new B.EventEmitter;onDidChangeFileDecorations=this.onDidChangeEmitter.event;pending=new Map;flushTimer=null;constructor(t,e,i,s){this.workerClient=t;this.debounceMs=e;this.maxPerFlush=i;this.tooltipAugmentProvider=s;this.workerClient.onDidUpdateRecords((n)=>this.enqueueUpdates(n))}dispose(){if(this.flushTimer)clearTimeout(this.flushTimer),this.flushTimer=null;this.onDidChangeEmitter.dispose()}updateConfig(t,e){this.debounceMs=Math.max(30,t),this.maxPerFlush=Math.max(64,e)}provideFileDecoration(t){if(t.scheme!=="file")return;let e=this.workerClient.getRecord(t);if(!e)return;let i=Oe(e),s=[`Entropy ${(e.entropy*100).toFixed(0)}%`,`Complexity ${e.complexity}`,`Debt ${e.debt}`,`Freshness ${(e.freshness*100).toFixed(0)}%`];if(this.tooltipAugmentProvider)s.push(...this.tooltipAugmentProvider(t));return{color:i,tooltip:s.join(`
`),propagate:!1}}enqueueExternalUpdates(t){this.enqueueUpdates(t)}enqueueUpdates(t){for(let e of t)this.pending.set(e.toString(),e);if(!this.flushTimer)this.flushTimer=setTimeout(()=>this.flush(),this.debounceMs)}flush(){if(this.flushTimer=null,this.pending.size===0)return;let t=Array.from(this.pending.values()).slice(0,this.maxPerFlush);for(let e of t)this.pending.delete(e.toString());if(this.onDidChangeEmitter.fire(t),this.pending.size>0)this.flushTimer=setTimeout(()=>this.flush(),this.debounceMs)}}function Oe(t){let e=je(t.entropy*0.78+(1-t.freshness)*0.22);if(e>=0.72)return new B.ThemeColor("problemsErrorIcon.foreground");if(e>=0.45)return new B.ThemeColor("charts.yellow");return new B.ThemeColor("charts.green")}function je(t){if(t<0)return 0;if(t>1)return 1;return t}var T=d(require("path")),v=d(require("vscode"));class Q{extensionUri;workerClient;static viewType="chthonic.abyssalView";disposables=[];view=null;rootPath=null;sedimentRequestCallback=null;constructor(t,e){this.extensionUri=t;this.workerClient=e;this.disposables.push(this.workerClient.onDidUpdateGraph((i)=>this.postMessage({type:"graph",graph:i})),this.workerClient.onDidUpdateSnapshot((i)=>this.postMessage({type:"snapshot",snapshot:i})))}setRootPath(t){this.rootPath=t}onRequestSediment(t){this.sedimentRequestCallback=t}postSedimentData(t){this.postMessage({type:"sediment",sediment:t})}postSedimentChunk(t){this.postMessage({type:"sedimentChunk",chunk:t})}postSedimentBinary(t){let e=new Uint8Array(t.byteLength);e.set(t),this.postMessage({type:"sedimentBinary",payload:e.buffer})}dispose(){this.disposables.forEach((t)=>t.dispose()),this.disposables.length=0}resolveWebviewView(t,e,i){this.view=t,t.webview.options={enableScripts:!0,localResourceRoots:[this.extensionUri]},t.webview.html=this.getHtml(t.webview),t.webview.onDidReceiveMessage((s)=>{this.handleMessage(s)})}handleMessage(t){if(!t||typeof t!=="object")return;let e=t;if(!e.type)return;if(e.type==="ready"){this.postMessage({type:"snapshot",snapshot:this.workerClient.getSnapshot()}),this.workerClient.requestGraph(260);return}if(e.type==="requestGraph"){this.workerClient.requestGraph(260);return}if(e.type==="requestSediment"){this.sedimentRequestCallback?.();return}if(e.type==="openFile"&&e.path&&this.rootPath){let i=T.normalize(e.path);if(i.startsWith("..")||T.isAbsolute(i))return;let s=T.join(this.rootPath,i),n=v.Uri.file(s);v.workspace.openTextDocument(n).then((a)=>{v.window.showTextDocument(a,{preview:!1})},()=>{v.window.showWarningMessage(`Unable to open ${e.path}`)})}}postMessage(t){if(!this.view)return;this.view.webview.postMessage(t)}getHtml(t){let e=Ne(),i=t.asWebviewUri(v.Uri.joinPath(this.extensionUri,"media","abyssalPane.js")),s=t.asWebviewUri(v.Uri.joinPath(this.extensionUri,"media","wasm","pkg","entropy_renderer_wasm.js")),n=t.asWebviewUri(v.Uri.joinPath(this.extensionUri,"media","wasm","pkg","entropy_renderer_wasm_bg.wasm")),a=t.asWebviewUri(v.Uri.joinPath(this.extensionUri,"media","wasm","pkg","chthonic_loom.js")),c=t.asWebviewUri(v.Uri.joinPath(this.extensionUri,"media","wasm","pkg","chthonic_loom_bg.wasm")),p=["default-src 'none'",`img-src ${t.cspSource} data:`,`style-src ${t.cspSource} 'unsafe-inline'`,`script-src 'nonce-${e}' ${t.cspSource}`,`connect-src ${t.cspSource}`].join("; "),g=JSON.stringify({wasmModuleUri:s.toString(),wasmBinaryUri:n.toString(),loomWasmModuleUri:a.toString(),loomWasmBinaryUri:c.toString()});return`<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="${p}">
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
        window.__CHTHONIC_ABYSSAL__ = ${g};
    </script>
    <script nonce="${e}" type="module" src="${i}"></script>
</body>
</html>`}}function Ne(){let e="";for(let i=0;i<32;i+=1)e+="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789".charAt(Math.floor(Math.random()*62));return e}var ft=d(require("fs/promises")),x=d(require("path")),yt=d(require("vscode"));var Vt=d(require("crypto"));class lt{leaves=new Map;dirty=!1;upsert(t){let e=Je(t.path),i=Ue(e,t);if(this.leaves.get(e)!==i)this.leaves.set(e,i),this.dirty=!0}hasDirty(){return this.dirty}settle(t){if(!this.dirty||this.leaves.size===0)return null;let e=Ve(Array.from(this.leaves.entries()).sort((i,s)=>i[0].localeCompare(s[0])));return this.dirty=!1,{reason:t,rootHash:e,leafCount:this.leaves.size,generatedAt:Date.now()}}}function Ue(t,e){let i=[t,e.entropy.toFixed(6),e.complexity,e.debt,e.freshness.toFixed(6),e.ruffViolations,e.updatedAt].join("|");return W(i)}function Ve(t){if(t.length===0)return W("EMPTY");let e=t.map(([i,s])=>W(`${i}:${s}`));while(e.length>1){let i=[];for(let s=0;s<e.length;s+=2){let n=e[s],a=e[s+1]??e[s];i.push(W(`${n}${a}`))}e=i}return e[0]}function W(t){return Vt.createHash("sha256").update(t,"utf8").digest("hex")}function Je(t){return t.replace(/\\/g,"/")}var G=d(require("path")),pt=require("child_process"),K=d(require("vscode"));function L(t,e){let i="",s=(n)=>{let a=n.trim();if(!a)return;try{let c=JSON.parse(a);if(!c||typeof c!=="object"||Array.isArray(c))throw Error("JSONL payload must be an object");t(c)}catch(c){e(c instanceof Error?c:Error(String(c)))}};return{push(n){i+=n.toString();while(!0){let a=i.indexOf(`
`);if(a<0)return;let c=i.slice(0,a);i=i.slice(a+1),s(c)}},flush(){if(!i.trim()){i="";return}s(i),i=""}}}class ht{output;rootPath=null;pythonSidecar=null;rubySidecar=null;onDidReceiveRuffEmitter=new K.EventEmitter;onDidReceiveRuff=this.onDidReceiveRuffEmitter.event;onDidReceiveLoreEmitter=new K.EventEmitter;onDidReceiveLore=this.onDidReceiveLoreEmitter.event;onDidReceiveSidecarErrorEmitter=new K.EventEmitter;onDidReceiveSidecarError=this.onDidReceiveSidecarErrorEmitter.event;constructor(t){this.output=t}start(t){this.rootPath=t,this.startPythonSidecar(),this.startRubySidecar()}requestScan(t){if(!this.pythonSidecar||this.pythonSidecar.killed)this.startPythonSidecar();this.writeJson(this.pythonSidecar,t)}requestLore(t){if(!this.rubySidecar||this.rubySidecar.killed)this.startRubySidecar();this.writeJson(this.rubySidecar,t)}dispose(){this.pythonSidecar?.kill(),this.rubySidecar?.kill(),this.pythonSidecar=null,this.rubySidecar=null,this.onDidReceiveRuffEmitter.dispose(),this.onDidReceiveLoreEmitter.dispose(),this.onDidReceiveSidecarErrorEmitter.dispose()}startPythonSidecar(){if(!this.rootPath||this.pythonSidecar)return;let t=G.join(this.rootPath,".chthonic","python","entropy_scan.py"),e=G.join(this.rootPath,".chthonic","venv",process.platform==="win32"?"Scripts/python.exe":"bin/python");this.pythonSidecar=pt.spawn("uv",["run","--python",e,t,"--stdio"],{cwd:this.rootPath,stdio:["pipe","pipe","pipe"]});let i=L((s)=>this.handlePythonPayload(s),(s)=>this.output.appendLine(`[polyglot:python] invalid JSONL payload: ${s.message}`));this.pythonSidecar.stdout?.on("data",(s)=>i.push(s)),this.pythonSidecar.stderr?.on("data",(s)=>{this.output.appendLine(`[polyglot:python] ${s.toString().trimEnd()}`)}),this.pythonSidecar.on("error",(s)=>{this.onDidReceiveSidecarErrorEmitter.fire({type:"error",source:"python",message:s.message}),this.output.appendLine(`[polyglot:python] failed to spawn: ${s.message}`),this.pythonSidecar=null}),this.pythonSidecar.on("exit",(s)=>{i.flush(),this.output.appendLine(`[polyglot:python] exited with code ${s??-1}`),this.pythonSidecar=null})}startRubySidecar(){if(!this.rootPath||this.rubySidecar)return;let t=G.join(this.rootPath,".chthonic","ruby","lore.rb");this.rubySidecar=pt.spawn("ruby",[t],{cwd:this.rootPath,stdio:["pipe","pipe","pipe"]});let e=L((i)=>this.handleRubyPayload(i),(i)=>this.output.appendLine(`[polyglot:ruby] invalid JSONL payload: ${i.message}`));this.rubySidecar.stdout?.on("data",(i)=>e.push(i)),this.rubySidecar.stderr?.on("data",(i)=>{this.output.appendLine(`[polyglot:ruby] ${i.toString().trimEnd()}`)}),this.rubySidecar.on("error",(i)=>{this.onDidReceiveSidecarErrorEmitter.fire({type:"error",source:"ruby",message:i.message}),this.output.appendLine(`[polyglot:ruby] failed to spawn: ${i.message}`),this.rubySidecar=null}),this.rubySidecar.on("exit",(i)=>{e.flush(),this.output.appendLine(`[polyglot:ruby] exited with code ${i??-1}`),this.rubySidecar=null})}writeJson(t,e){if(!t?.stdin||t.killed)return;try{t.stdin.write(`${JSON.stringify(e)}
`)}catch(i){this.output.appendLine(`[polyglot] sidecar write failed: ${ze(i)}`)}}handlePythonPayload(t){if(t.type==="ruff-summary"){let e=t;this.onDidReceiveRuffEmitter.fire(e);return}if(t.type==="error"){let e=String(t.message??"python sidecar error");this.output.appendLine(`[polyglot:python] ${e}`),this.onDidReceiveSidecarErrorEmitter.fire({type:"error",source:"python",message:e})}}handleRubyPayload(t){if(t.type==="lore"){this.onDidReceiveLoreEmitter.fire(t);return}if(t.type==="error"){let e=String(t.message??"ruby sidecar error");this.output.appendLine(`[polyglot:ruby] ${e}`),this.onDidReceiveSidecarErrorEmitter.fire({type:"error",source:"ruby",message:e})}}}function ze(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}var Jt=d(require("fs")),Y=d(require("fs/promises")),k=d(require("path")),ut=require("child_process");class mt{output;rootPath=null;options={rpcUrl:"http://127.0.0.1:8899",autostartValidator:!1};ledgerFilePath=null;validatorProcess=null;hostProcess=null;requestCounter=1;pending=new Map;constructor(t){this.output=t}async start(t,e){this.rootPath=t,this.options=e;let i=k.join(t,".chthonic","ledger");if(await Y.mkdir(i,{recursive:!0}),this.ledgerFilePath=k.join(i,"entropy-settlements.jsonl"),e.autostartValidator)this.startValidator();this.startHostProcess()}async commitEntropy(t){if(!this.rootPath||!this.ledgerFilePath)return{mode:"offline",detail:"Ledger host not started"};let e={...t,rpcUrl:this.options.rpcUrl,recordedAt:Date.now()},i={mode:"offline",detail:"Rust ledger host unavailable; persisted settlement locally."};try{i=await this.submitToHost(t)}catch(s){this.output.appendLine(`[ledger-rust] submit failed: ${Ge(s)}`)}return await Y.appendFile(this.ledgerFilePath,`${JSON.stringify({...e,receipt:i})}
`,"utf8"),i}dispose(){for(let[t,e]of this.pending)e.reject(Error(`request ${t} cancelled`));this.pending.clear(),this.hostProcess?.kill(),this.hostProcess=null,this.validatorProcess?.kill(),this.validatorProcess=null}startHostProcess(){if(!this.rootPath||this.hostProcess)return;let t=Fe(this.rootPath,this.options.hostBinaryPath),e=this.options.walletPath??k.join(this.rootPath,".chthonic","wallets","payer.json"),i=this.options.idlPath??k.join(this.rootPath,".chthonic","wallets","entropy_ledger.json");this.hostProcess=ut.spawn(t,["--wallet",e,"--idl",i,"--rpc-url",this.options.rpcUrl],{cwd:this.rootPath,stdio:["pipe","pipe","pipe"]});let s=L((n)=>this.handleHostPayload(n),(n)=>this.output.appendLine(`[ledger-rust] invalid JSON payload: ${n.message}`));this.hostProcess.stdout?.on("data",(n)=>s.push(n)),this.hostProcess.stderr?.on("data",(n)=>{this.output.appendLine(`[ledger-rust] ${n.toString().trimEnd()}`)}),this.hostProcess.on("error",(n)=>{this.output.appendLine(`[ledger-rust] failed to spawn host: ${n.message}`),this.rejectAllPending(Error(`host spawn failed: ${n.message}`)),this.hostProcess=null}),this.hostProcess.on("exit",(n)=>{s.flush(),this.output.appendLine(`[ledger-rust] host exited with code ${n??-1}`),this.rejectAllPending(Error("ledger host exited")),this.hostProcess=null})}async submitToHost(t){if(!this.hostProcess||this.hostProcess.killed)this.startHostProcess();if(!this.hostProcess?.stdin||this.hostProcess.killed)return{mode:"offline",detail:"Rust host binary is missing or not executable."};let e=this.requestCounter++,i={jsonrpc:"2.0",id:e,method:"submit_entropy",params:{entropy_score:Math.max(0,Math.round(t.leafCount*17+13)),merkle_root:t.rootHash,leaf_count:t.leafCount,reason:t.reason}};return await new Promise((n,a)=>{this.pending.set(e,{resolve:n,reject:a}),this.hostProcess?.stdin?.write(`${JSON.stringify(i)}
`,(c)=>{if(!c)return;this.pending.delete(e),a(c)})})}handleHostPayload(t){let e=t.id;if(typeof e!=="number")return;let i=this.pending.get(e);if(!i)return;if(this.pending.delete(e),t.error&&typeof t.error==="object"){let n=t;i.resolve({mode:"offline",detail:`Rust ledger error ${n.error.code}: ${n.error.message}`});return}let s=t;i.resolve({mode:"validator-rust",txSignature:s.result.signature,detail:`Rust anchor-client submission accepted${s.result.slot?` (slot ${s.result.slot})`:""}.`})}rejectAllPending(t){for(let[e,i]of this.pending)this.pending.delete(e),i.reject(t)}startValidator(){if(!this.rootPath||this.validatorProcess)return;let t=Qe(this.rootPath),e=We(this.options.rpcUrl)??8899,i=k.join(this.rootPath,".chthonic","solana-ledger");this.validatorProcess=ut.spawn(t,["--ledger",i,"--rpc-port",String(e),"--reset","--quiet"],{cwd:this.rootPath,stdio:["ignore","pipe","pipe"]}),this.validatorProcess.stdout?.on("data",(s)=>{this.output.appendLine(`[solana] ${s.toString().trimEnd()}`)}),this.validatorProcess.stderr?.on("data",(s)=>{this.output.appendLine(`[solana] ${s.toString().trimEnd()}`)}),this.validatorProcess.on("error",(s)=>{this.output.appendLine(`[solana] validator spawn error: ${s.message}`),this.validatorProcess=null}),this.validatorProcess.on("exit",(s)=>{this.output.appendLine(`[solana] validator exited with code ${s??-1}`),this.validatorProcess=null})}}function Fe(t,e){if(e)return e;let i=process.platform==="win32"?"entropy-ledger-host.exe":"entropy-ledger-host";return k.join(t,"native","target","release",i)}function Qe(t){let e=process.platform==="win32"?"solana-test-validator.exe":"solana-test-validator",i=k.join(t,".chthonic","bin",e);if(Jt.existsSync(i))return i;return process.platform==="win32"?"solana-test-validator":e}function We(t){try{let e=new URL(t);if(!e.port)return null;let i=Number(e.port);return Number.isFinite(i)?i:null}catch{return null}}function Ge(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}class gt{output;options;backend=null;constructor(t,e){this.output=t;this.options=e}async start(t){this.backend=this.options.mode==="bankrun"?new zt(this.output):new Ft(this.output,this.options),await this.backend.start(t)}async commitEntropy(t){if(!this.backend)return{mode:"offline",detail:"LedgerBroker backend not initialized."};return this.backend.commitEntropy(t)}dispose(){this.backend?.dispose(),this.backend=null}}class zt{output;sequence=0;constructor(t){this.output=t}async start(t){this.output.appendLine("[ledger] phantom mode active (bankrun simulation).")}async commitEntropy(t){return this.sequence+=1,{mode:"bankrun",txSignature:`bankrun-${t.rootHash.slice(0,20)}-${this.sequence}`,detail:"In-memory bankrun simulation accepted the entropy settlement."}}dispose(){}}class Ft{options;client;constructor(t,e){this.options=e;this.client=new mt(t)}async start(t){await this.client.start(t,{rpcUrl:this.options.rpcUrl,autostartValidator:this.options.autostartValidator,hostBinaryPath:this.options.hostBinaryPath,walletPath:this.options.walletPath,idlPath:this.options.idlPath})}async commitEntropy(t){return this.client.commitEntropy(t)}dispose(){this.client.dispose()}}class vt{output;workerClient;options;requestDecorationRefresh;broker;merkle=new lt;ledger;tooltipAugments=new Map;rootPath=null;scanTimer=null;settleTimer=null;gitPollTimer=null;gitHeadSnapshot=null;pendingSettleReason=null;disposables=[];constructor(t,e,i,s){this.output=t;this.workerClient=e;this.options=i;this.requestDecorationRefresh=s;this.broker=new ht(t),this.ledger=new gt(t,{mode:this.options.ledgerMode,rpcUrl:this.options.solanaRpcUrl,autostartValidator:this.options.solanaAutostartValidator,hostBinaryPath:this.options.solanaLedgerHostBinaryPath,walletPath:this.options.solanaWalletPath,idlPath:this.options.solanaIdlPath}),this.disposables.push(this.broker.onDidReceiveRuff((n)=>this.applyRuffSummary(n.files)),this.broker.onDidReceiveLore((n)=>this.applyLore(n)),this.workerClient.onDidUpdateRecords((n)=>this.captureEntropyLeaves(n)))}async start(t){if(this.rootPath=t,!this.options.enabled)return;this.broker.start(t),await this.ledger.start(t),this.broker.requestScan({type:"scan",reason:"manual",root:t}),this.startScanLoop(),this.startGitWatcher()}onDidSaveDocument(t){if(!this.rootPath||!this.options.enabled||t.uri.scheme!=="file")return;let e=Qt(this.rootPath,t.uri.fsPath);if(!e)return;this.broker.requestScan({type:"scan",reason:"save",root:this.rootPath,files:[e]}),this.scheduleSettlement("save")}requestManualScan(){if(!this.rootPath||!this.options.enabled)return;this.broker.requestScan({type:"scan",reason:"manual",root:this.rootPath})}getTooltipFragments(t){if(!this.rootPath||t.scheme!=="file")return[];let e=Qt(this.rootPath,t.fsPath);if(!e)return[];let i=this.tooltipAugments.get(e);if(!i)return[];let s=[];if(i.ruffViolations>0)s.push(`Ruff ${i.ruffViolations} violation${i.ruffViolations===1?"":"s"}`);if(i.loreLine)s.push(i.loreLine);return s}dispose(){if(this.scanTimer)clearInterval(this.scanTimer),this.scanTimer=null;if(this.settleTimer)clearTimeout(this.settleTimer),this.settleTimer=null;if(this.gitPollTimer)clearInterval(this.gitPollTimer),this.gitPollTimer=null;this.broker.dispose(),this.ledger.dispose(),this.disposables.forEach((t)=>t.dispose()),this.disposables.length=0}captureEntropyLeaves(t){if(!this.options.enabled)return;for(let e of t){let i=this.workerClient.getRecord(e);if(!i)continue;let s=this.tooltipAugments.get(i.path);this.merkle.upsert({path:i.path,entropy:i.entropy,complexity:i.complexity,debt:i.debt,freshness:i.freshness,ruffViolations:s?.ruffViolations??0,updatedAt:Date.now()})}}applyRuffSummary(t){if(!this.rootPath||!this.options.enabled)return;let e=[];for(let i of t){let s=this.tooltipAugments.get(i.path),n={ruffViolations:i.violations,loreLine:s?.loreLine};this.tooltipAugments.set(i.path,n);let a=yt.Uri.file(x.join(this.rootPath,i.path));e.push(a);let c=this.workerClient.getRecord(a);if(c){if(this.merkle.upsert({path:c.path,entropy:c.entropy,complexity:c.complexity,debt:c.debt,freshness:c.freshness,ruffViolations:i.violations,updatedAt:Date.now()}),c.entropy>=0.45||i.violations>0)this.broker.requestLore({type:"lore-request",root:this.rootPath,path:i.path,entropy:c.entropy,violations:i.violations})}}if(e.length>0)this.requestDecorationRefresh(e)}applyLore(t){if(!this.rootPath||!this.options.enabled)return;if(t.root!==this.rootPath)return;let e=this.tooltipAugments.get(t.path);this.tooltipAugments.set(t.path,{ruffViolations:e?.ruffViolations??t.violations,loreLine:t.line}),this.requestDecorationRefresh([yt.Uri.file(x.join(this.rootPath,t.path))])}startScanLoop(){if(this.scanTimer||!this.rootPath)return;let t=Math.max(this.options.pythonScanIntervalMs,1e4);this.scanTimer=setInterval(()=>{if(!this.rootPath)return;this.broker.requestScan({type:"scan",reason:"interval",root:this.rootPath})},t)}startGitWatcher(){if(!this.rootPath||this.gitPollTimer)return;this.gitHeadSnapshot=null,this.gitPollTimer=setInterval(async()=>{if(!this.rootPath)return;let t=await Ke(this.rootPath);if(!t)return;if(!this.gitHeadSnapshot){this.gitHeadSnapshot=t;return}if(t!==this.gitHeadSnapshot){if(this.gitHeadSnapshot=t,this.output.appendLine("[polyglot] git HEAD changed, scheduling Merkle settlement."),this.rootPath)this.broker.requestScan({type:"scan",reason:"commit",root:this.rootPath});this.scheduleSettlement("commit")}},6000)}scheduleSettlement(t){if(!this.options.enabled)return;if(this.pendingSettleReason=t==="commit"?"commit":this.pendingSettleReason??t,this.settleTimer)clearTimeout(this.settleTimer);this.settleTimer=setTimeout(()=>{this.settleTimer=null,this.flushSettlement()},Math.max(this.options.settleDebounceMs,300))}async flushSettlement(){let t=this.pendingSettleReason??"manual";this.pendingSettleReason=null;let e=this.merkle.settle(t);if(!e)return;let i=await this.ledger.commitEntropy(e),s=[`[polyglot] settled Merkle root ${e.rootHash.slice(0,16)}...`,`leaves=${e.leafCount}`,`mode=${i.mode}`];if(i.txSignature)s.push(`tx=${i.txSignature}`);s.push(`detail=${i.detail}`),this.output.appendLine(s.join(" "))}}async function Ke(t){let e=x.join(t,".git"),i=x.join(e,"HEAD"),s="";try{s=await ft.readFile(i,"utf8")}catch{return null}let n=s.trim();if(!n)return null;if(!n.startsWith("ref:"))return n;let a=n.slice(4).trim(),c=x.join(e,a);try{let p=await ft.readFile(c,"utf8");return`ref:${a}:${p.trim()}`}catch{return`ref:${a}:missing`}}function Qt(t,e){let i=x.relative(t,e);if(!i||i.startsWith("..")||x.isAbsolute(i))return null;return i.replace(/\\/g,"/")}var Wt=d(require("path")),Gt=require("child_process"),P=d(require("vscode"));class bt{output;headlessVulkan;daemonBinaryOverride;eolApiBase;entropyMonitorIntervalMs;rootPath=null;daemonProcess=null;requestCounter=1;pending=new Map;onDidReceiveManifestEmitter=new P.EventEmitter;onDidReceiveManifest=this.onDidReceiveManifestEmitter.event;onDidReceiveEnvEmitter=new P.EventEmitter;onDidReceiveEnv=this.onDidReceiveEnvEmitter.event;onDidReceiveSedimentEmitter=new P.EventEmitter;onDidReceiveSediment=this.onDidReceiveSedimentEmitter.event;onDidReceiveSedimentChunkEmitter=new P.EventEmitter;onDidReceiveSedimentChunk=this.onDidReceiveSedimentChunkEmitter.event;onDidReceiveSynapseEmitter=new P.EventEmitter;onDidReceiveSynapse=this.onDidReceiveSynapseEmitter.event;onDidReceiveEntropyStateEmitter=new P.EventEmitter;onDidReceiveEntropyState=this.onDidReceiveEntropyStateEmitter.event;onDidReceiveFiredancerSurgeEmitter=new P.EventEmitter;onDidReceiveFiredancerSurge=this.onDidReceiveFiredancerSurgeEmitter.event;constructor(t,e,i,s="https://endoflife.date/api/v1",n=21600000){this.output=t;this.headlessVulkan=e;this.daemonBinaryOverride=i;this.eolApiBase=s;this.entropyMonitorIntervalMs=n}start(t){this.rootPath=t,this.startDaemon()}async requestSediment(t,e){return this.submitRequest("reactor/sediment",{max_layers:t,max_files:e})}async requestSedimentStream(t,e,i=220){return this.submitRequest("reactor/sediment_stream",{max_layers:t,max_files:e,chunk_size:i})}async requestSedimentSynapse(t,e,i=220){return this.submitRequest("reactor/sediment_synapse",{max_layers:t,max_files:e,chunk_size:i})}async requestDetect(){return this.submitRequest("anno/detect",{})}async requestProvision(){return this.submitRequest("anno/provision",{})}async requestEntropyState(){return this.submitRequest("reactor/entropy_state",{})}dispose(){for(let[,t]of this.pending)t.reject(Error("AnnoClient disposed"));this.pending.clear(),this.daemonProcess?.kill(),this.daemonProcess=null,this.onDidReceiveManifestEmitter.dispose(),this.onDidReceiveEnvEmitter.dispose(),this.onDidReceiveSedimentEmitter.dispose(),this.onDidReceiveSedimentChunkEmitter.dispose(),this.onDidReceiveSynapseEmitter.dispose(),this.onDidReceiveEntropyStateEmitter.dispose(),this.onDidReceiveFiredancerSurgeEmitter.dispose()}startDaemon(){if(!this.rootPath||this.daemonProcess)return;let t=this.daemonBinaryOverride??Ye(this.rootPath),e=["--workspace",this.rootPath];if(this.headlessVulkan)e.push("--headless-vulkan");this.daemonProcess=Gt.spawn(t,e,{cwd:this.rootPath,env:{...process.env,CHTHONIC_EOL_API_BASE:this.eolApiBase,CHTHONIC_ENTROPY_MONITOR_INTERVAL_MS:String(Math.max(60000,this.entropyMonitorIntervalMs))},stdio:["pipe","pipe","pipe"]});let i=L((s)=>this.handlePayload(s),(s)=>this.output.appendLine(`[daemon] invalid JSONL: ${s.message}`));this.daemonProcess.stdout?.on("data",(s)=>i.push(s)),this.daemonProcess.stderr?.on("data",(s)=>{this.output.appendLine(`[daemon] ${s.toString().trimEnd()}`)}),this.daemonProcess.on("error",(s)=>{this.output.appendLine(`[daemon] spawn failed: ${s.message}`),this.rejectAllPending(Error(`daemon spawn failed: ${s.message}`)),this.daemonProcess=null}),this.daemonProcess.on("exit",(s)=>{i.flush(),this.output.appendLine(`[daemon] exited with code ${s??-1}`),this.rejectAllPending(Error("daemon exited")),this.daemonProcess=null})}handlePayload(t){if("method"in t&&!("id"in t)){this.handleNotification(t);return}if("id"in t&&typeof t.id==="number")this.handleResponse(t)}handleNotification(t){let{method:e,params:i}=t;switch(e){case"anno/manifest":this.onDidReceiveManifestEmitter.fire(i),this.output.appendLine(`[daemon] ANNO manifest received (${i.languages?.length??0} languages)`);break;case"anno/env":this.onDidReceiveEnvEmitter.fire(i),this.output.appendLine("[daemon] env report received");break;case"reactor/status":{let s=i.status??"unknown";this.output.appendLine(`[daemon] reactor status: ${s}`);break}case"reactor/sedimentChunk":this.onDidReceiveSedimentChunkEmitter.fire(i);break;case"reactor/synapse":this.onDidReceiveSynapseEmitter.fire(i),this.output.appendLine(`[daemon] synapse status: ${i.status} (${i.mode})`);break;case"reactor/entropyState":this.onDidReceiveEntropyStateEmitter.fire(i),this.output.appendLine(`[daemon] entropy state: ${i.status} (${Math.round((i.decay_score??0)*100)}%)`);break;case"reactor/firedancerSurge":this.onDidReceiveFiredancerSurgeEmitter.fire(i),this.output.appendLine(`[daemon] firedancer slot ${i.slot} tps ${i.simulated_tps} (${i.surge?"surge":"flow"})`);break;default:this.output.appendLine(`[daemon] unknown notification: ${e}`)}}handleResponse(t){let e=t.id,i=this.pending.get(e);if(!i)return;if(this.pending.delete(e),t.error&&typeof t.error==="object"){let s=t.error;i.reject(Error(s.message));return}i.resolve(t.result)}submitRequest(t,e){if(!this.daemonProcess?.stdin||this.daemonProcess.killed)this.startDaemon();if(!this.daemonProcess?.stdin)return Promise.reject(Error("daemon not available"));let i=this.requestCounter++,s={jsonrpc:"2.0",id:i,method:t,params:e};return new Promise((n,a)=>{this.pending.set(i,{resolve:n,reject:a}),this.daemonProcess?.stdin?.write(`${JSON.stringify(s)}
`,(c)=>{if(c)this.pending.delete(i),a(c)})})}rejectAllPending(t){for(let[e,i]of this.pending)this.pending.delete(e),i.reject(t)}}function Ye(t){let e=process.platform==="win32"?"chthonic-daemon.exe":"chthonic-daemon";return Wt.join(t,"native","target","release",e)}var w=d(require("vscode"));class xt{output;envCollection;disposed=!1;constructor(t,e){this.output=t;this.envCollection=e}async activate(){if(this.disposed)return;try{await w.commands.executeCommand("workbench.action.closeSidebar"),await w.commands.executeCommand("workbench.action.terminal.moveToSidePanel"),await w.commands.executeCommand("workbench.action.toggleAuxiliaryBar"),await w.commands.executeCommand("workbench.action.toggleMaximizedPanel"),await w.commands.executeCommand("workbench.action.focusActiveEditorGroup"),this.output.appendLine("[cockpit] layout activated: sidebar=closed, terminal=AuxBar, panel=maximized, editor=Center")}catch(t){this.output.appendLine(`[cockpit] layout activation failed: ${Xe(t)}`)}}applyTerminalEnv(t){if(this.disposed)return;if(!t.path_mutations.length)return;let e=t.path_mutations.sort((s,n)=>s.priority-n.priority).map((s)=>s.path),i=process.platform==="win32"?";":":";for(let s of e)this.envCollection.prepend("PATH",`${s}${i}`);for(let s of w.window.terminals)if(process.platform==="win32")for(let n of e)s.sendText(`$env:PATH = "${n};$env:PATH"`,!0);else for(let n of e)s.sendText(`export PATH="${n}:$PATH"`,!0);if(this.output.appendLine(`[cockpit] terminal env updated: ${e.length} PATH mutations applied`),t.warnings.length>0)for(let s of t.warnings)this.output.appendLine(`[cockpit] warning: ${s}`)}dispose(){this.disposed=!0}}function Xe(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}var Yt=d(require("fs")),St=d(require("path"));class SynapseBridge{output;extensionRoot;binding=null;reader=null;descriptor=null;transportMode;constructor(t,e,i){this.output=t;this.extensionRoot=e;this.transportMode=Ze(i)}updateDescriptor(t){if(this.descriptor=t,this.transportMode==="jsonl"){this.output.appendLine("[synapse] disabled by transport=jsonl");return}if(t.status!=="ready"||t.mode!=="shared_memory"||!t.shm_id){this.output.appendLine(`[synapse] unavailable: ${t.reason??t.status}`);return}try{let e=this.ensureBindingLoaded();this.reader=new e.SynapseReader(t.shm_id,t.event_name??void 0),this.output.appendLine(`[synapse] connected (shm=${t.shm_id})`)}catch(e){this.reader=null,this.output.appendLine(`[synapse] init failed, falling back to JSONL: ${ti(e)}`)}}isReady(){if(this.transportMode==="jsonl")return!1;return this.reader!==null&&this.descriptor?.status==="ready"&&this.descriptor.mode==="shared_memory"}async drain(t,e){if(!this.reader||t.transport!=="shared_memory")return 0;let i=Math.max(0,t.chunks_written??t.total_chunks??0);if(i===0)return 0;let s=0,n=Date.now();while(s<i&&Date.now()-n<4000){if(!this.reader.wait_for_signal(120)){await Kt();continue}while(!0){let c=this.reader.read_chunk();if(!c||c.byteLength===0)break;let p=new Uint8Array(c.buffer,c.byteOffset,c.byteLength),g=new Uint8Array(p.byteLength);if(g.set(p),e(g),s+=1,s>=i)break}await Kt()}if(s<i)this.output.appendLine(`[synapse] partial drain: ${s}/${i}`);return s}dispose(){this.reader=null}ensureBindingLoaded(){if(this.binding)return this.binding;let candidates=[St.join(this.extensionRoot,"src","reactor","synapse.node"),St.join(this.extensionRoot,"native","target","release","synapse.node")],existing=candidates.find((t)=>Yt.existsSync(t));if(!existing)throw Error(`synapse.node not found in ${candidates.join(", ")}`);let req=eval("require");return this.binding=req(existing),this.binding}}function Ze(t){let e=t.trim().toLowerCase();if(e==="shared_memory")return"shared_memory";if(e==="jsonl")return"jsonl";return"auto"}function ti(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}async function Kt(){await new Promise((t)=>setTimeout(t,0))}var E=d(require("vscode"));var Xt=d(require("fs")),Zt=d(require("path")),ei=[{file:"mise.toml",weight:16},{file:".mise.toml",weight:6},{file:"Cargo.toml",weight:20},{file:"native/Cargo.toml",weight:8},{file:"anno-manifest.toml",weight:8},{file:"uv.lock",weight:10},{file:".python-version",weight:5},{file:".ruby-version",weight:10},{file:"Gemfile",weight:6},{file:"go.mod",weight:10},{file:".node-version",weight:4},{file:".nvmrc",weight:4},{file:"package.json",weight:5},{file:"bun.lock",weight:4}];async function te(t){let e=ei.map((n)=>{let a=Zt.join(t,n.file),c=Xt.existsSync(a);return{...n,present:c}}),i=Math.min(100,e.reduce((n,a)=>a.present?n+a.weight:n,0)),s=ii(i);return{score:i,tier:s,markers:e,present:e.filter((n)=>n.present).map((n)=>n.file),missing:e.filter((n)=>!n.present).map((n)=>n.file)}}function ee(t){switch(t){case"loom":return"loom.svg";case"lens":return"lens.svg";default:return"gate.svg"}}function ii(t){if(t>=80)return"loom";if(t>=45)return"lens";return"gate"}class Et{extensionUri;output;containerId;fallbackItem;fallbackNoticeEmitted=!1;latestRustification=null;latestEntropy=null;constructor(t,e,i="chthonic-archive"){this.extensionUri=t;this.output=e;this.containerId=i;this.fallbackItem=E.window.createStatusBarItem(E.StatusBarAlignment.Left,47),this.fallbackItem.command="chthonic.refreshRustification",this.fallbackItem.tooltip="Rustification score and activity bar icon fallback",this.fallbackItem.show()}async update(t){this.latestRustification=t,await E.commands.executeCommand("setContext","chthonic.rustificationTier",t.tier),await E.commands.executeCommand("setContext","chthonic.rustificationScore",t.score),await this.apply()}async updateEntropy(t){this.latestEntropy=t,await E.commands.executeCommand("setContext","chthonic.decayStatus",t.status),await E.commands.executeCommand("setContext","chthonic.decayScore",Math.round(t.decay_score*100)),await this.apply()}dispose(){this.fallbackItem.dispose()}async apply(){if(!this.fallbackNoticeEmitted)this.output.appendLine("[morph] dynamic Activity Bar icon updates are unavailable on stable API; using status lane fallback"),this.fallbackNoticeEmitted=!0;this.updateFallbackStatus()}resolveIconFile(){let t=this.latestEntropy;if(t){if(t.decay_score>0.5||t.status==="critical")return"hazard.svg";if(t.decay_score<0.2&&t.status==="pristine")return"gate.svg";return"lens.svg"}let e=this.latestRustification?.tier??"gate";return ee(e)}updateFallbackStatus(){let t=this.latestRustification,e=this.latestEntropy;if(!t){this.fallbackItem.text="$(pulse) Slab boot",this.fallbackItem.tooltip="Rustification score pending";return}let i=si(t.tier),s=e?Math.round(e.decay_score*100):null,n=e?`${e.status} ${s}%`:"unknown";this.fallbackItem.text=`$(pulse) ${i} ${t.score}% · Decay ${s??"?"}%`,this.fallbackItem.tooltip=[`Rustification ${t.score}% (${t.tier})`,`Decay ${n}`,`Glyph: ${this.resolveIconFile()}`,`Present: ${t.present.join(", ")||"none"}`,`Missing: ${t.missing.join(", ")||"none"}`,e&&e.critical_tools.length>0?`Critical tools: ${e.critical_tools.join(", ")}`:void 0].filter(Boolean).join(`
`)}}function si(t){switch(t){case"loom":return"Loom";case"lens":return"Lens";default:return"Gate"}}var A=d(require("vscode"));class kt{output;constructor(t){this.output=t}async activate(){await this.applyCommandLayout(),await A.commands.executeCommand("workbench.view.extension.chthonic-archive"),await A.commands.executeCommand("chthonic.loomView.focus"),this.output.appendLine("[deep-focus] activated via stable command lane")}async applyCommandLayout(){try{await A.commands.executeCommand("workbench.action.terminal.moveToSidePanel"),await A.commands.executeCommand("workbench.action.toggleAuxiliaryBar"),await A.commands.executeCommand("workbench.action.focusActiveEditorGroup")}catch(t){this.output.appendLine(`[deep-focus] command layout failed: ${ni(t)}`)}}}function ni(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}var Pt=d(require("vscode"));class wt{output;constructor(t){this.output=t}async activate(){await this.applyCommandLayout(),await Pt.commands.executeCommand("workbench.view.extension.chthonic-archive"),this.output.appendLine("[restore-order] completed via stable command lane")}async applyCommandLayout(){await oi(this.output,[["workbench.view.extension.chthonic-archive"],["chthonic.statusView.focus"],["workbench.action.moveFocusedViewToSecondarySidebar"],["chthonic.loomView.focus"],["workbench.action.moveFocusedViewToPanel"],["workbench.action.positionPanelBottom"],["workbench.action.focusActiveEditorGroup"]])}}async function oi(t,e){for(let i of e){let[s,...n]=i;try{await Pt.commands.executeCommand(s,...n)}catch(a){t.appendLine(`[restore-order] command failed (${s}): ${ri(a)}`)}}}function ri(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}var j=d(require("vscode"));class X{static viewType="chthonic.loomView";view=null;report=null;resolveWebviewView(t,e,i){this.view=t,t.webview.options={enableScripts:!0},t.webview.html=this.buildHtml(),t.webview.onDidReceiveMessage((s)=>{if(!s||typeof s!=="object")return;let n=s;if(n.type==="refresh")j.commands.executeCommand("chthonic.refreshRustification");if(n.type==="heal")j.commands.executeCommand("chthonic.slabHeal");if(n.type==="deepFocus")j.commands.executeCommand("chthonic.deepFocus");if(n.type==="restoreOrder")j.commands.executeCommand("chthonic.restoreOrder")}),this.postState()}update(t){this.report=t,this.postState()}dispose(){this.view=null}postState(){if(!this.view||!this.report)return;this.view.webview.postMessage({type:"state",report:this.report})}buildHtml(){let t=ai();return`<!DOCTYPE html>
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
</html>`}}function ai(){let e="";for(let i=0;i<24;i+=1)e+="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789".charAt(Math.floor(Math.random()*62));return e}var u=d(require("fs")),m=d(require("path")),Z=d(require("child_process")),ne=d(require("vscode"));class Lt{output;envCollection;workspaceRoot;timer=null;running=!1;options={intervalMs:21600000,eolApiBase:"https://endoflife.date/api"};constructor(t,e,i){this.output=t;this.envCollection=e;this.workspaceRoot=i}start(t){this.options=t,this.stopTimer(),this.timer=setInterval(()=>{this.runNow("interval")},Math.max(60000,t.intervalMs))}async runNow(t="manual"){if(this.running){this.output.appendLine("[slab-heal] skipped; already running");return}this.running=!0;try{let e=await this.auditVsToolchain();if(e&&(!e.allRequiredComponentsPresent||!e.allCriticalBinariesPresent))this.output.appendLine(`[slab-heal] vs2026 audit drift detected: components=${e.missingComponentCount}, binaries=${e.missingBinaryCount}`);let i=await this.collectRuntimeStates();if(i.length===0){this.output.appendLine("[slab-heal] no runtime states detected; skipping");return}let s=[];for(let n of i)if(await this.isEol(n.language,n.version))s.push(n);if(s.length===0){this.output.appendLine(`[slab-heal] ${t}: all slab runtimes are supported`);return}this.output.appendLine(`[slab-heal] ${t}: stale runtimes detected: ${s.map((n)=>`${n.language}@${n.version}`).join(", ")}`),await this.repair(s)}catch(e){this.output.appendLine(`[slab-heal] run failed: ${N(e)}`)}finally{this.running=!1}}dispose(){this.stopTimer()}stopTimer(){if(this.timer)clearInterval(this.timer),this.timer=null}async collectRuntimeStates(){let t=[{language:"python",command:"python",args:["-c",'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")']},{language:"ruby",command:"ruby",args:["-e","print RUBY_VERSION"]},{language:"go",command:"go",args:["env","GOVERSION"]},{language:"rust",command:"rustc",args:["--version"]},{language:"solana",command:"solana",args:["--version"]}],e=[];for(let s of t)try{let n=await _(s.command,s.args,this.workspaceRoot),a=pi(n,s.language);if(!a)continue;e.push({language:s.language,version:a})}catch(n){this.output.appendLine(`[slab-heal] probe ${s.language} failed: ${N(n)}`)}let i=await di(this.workspaceRoot);if(i)e.push({language:"visual-studio",version:i});else this.output.appendLine("[slab-heal] probe visual-studio failed: VS 2026 Insiders not detected");return e}async isEol(t,e){let i=await this.fetchCycles(t);if(!i||!Array.isArray(i))return!1;let s=hi(t,e),n=i.find((c)=>{let p=c;return p.cycle===s||p.cycle===s.split(".").slice(0,1).join(".")});if(!n||n.eol==null)return!1;if(typeof n.eol==="boolean")return n.eol;let a=Date.parse(n.eol);if(Number.isNaN(a))return!1;return a<=Date.now()}async fetchCycles(t){let e=ui(t);for(let i of e){let s=await fetch(`${this.options.eolApiBase}/${i}.json`,{headers:{accept:"application/json"}});if(!s.ok)continue;let n=await s.json();if(Array.isArray(n))return n}return this.output.appendLine(`[slab-heal] endoflife feed unavailable for ${t}; skipping lifecycle gate`),null}async repair(t){if(await li("mise",this.workspaceRoot))await Rt("mise",["upgrade"],this.workspaceRoot,this.output),await Rt("mise",["reshim"],this.workspaceRoot,this.output);else this.output.appendLine("[slab-heal] mise not found on PATH; skipped upgrade/reshim");await this.refreshToolpoolSnapshot();let i=await this.relinkVsHeaders();if(i)this.output.appendLine(`[slab-heal] relinked MSVC headers at ${i}`);else this.output.appendLine("[slab-heal] VS include relink skipped (MSVC path not found)");ne.window.showInformationMessage(`Chthonic self-heal complete: ${t.map((s)=>`${s.language}@${s.version}`).join(", ")}`)}async relinkVsHeaders(){let t=await ci(this.workspaceRoot);if(!t||!this.workspaceRoot)return null;let e=m.join(this.workspaceRoot,".chthonic","native","msvc"),i=m.join(e,"include");u.mkdirSync(e,{recursive:!0});try{u.rmSync(i,{recursive:!0,force:!0})}catch{}try{u.symlinkSync(t,i,"junction")}catch(s){let n=m.join(e,"include.path.txt");u.writeFileSync(n,t,"utf8"),this.output.appendLine(`[slab-heal] symlink failed; wrote include manifest ${n}: ${N(s)}`)}return this.envCollection.replace("CHTHONIC_VS_CPP_INCLUDE",t),this.envCollection.prepend("INCLUDE",`${t};`),t}async auditVsToolchain(){let t=ie(this.workspaceRoot);if(!t)return null;let e=m.join(t,"scripts","vs2026_audit.ps1");if(!u.existsSync(e))return null;try{let i=await _("pwsh",["-NoProfile","-File",e,"-Json"],t);return JSON.parse(i).summary??null}catch(i){return this.output.appendLine(`[slab-heal] vs2026 audit script failed: ${N(i)}`),null}}async refreshToolpoolSnapshot(){let t=ie(this.workspaceRoot);if(!t)return;let e=m.join(t,"scripts","toolpool-scan.ts");if(!u.existsSync(e))return;try{await Rt("bun",["run","scripts/toolpool-scan.ts","--write-env","--quiet"],t,this.output),this.output.appendLine("[slab-heal] tool-pool snapshot refreshed")}catch(i){this.output.appendLine(`[slab-heal] tool-pool snapshot failed: ${N(i)}`)}}}async function ci(t){let e=m.join(process.env["ProgramFiles(x86)"]||"C:\\Program Files (x86)","Microsoft Visual Studio","Installer","vswhere.exe");if(u.existsSync(e))try{let s=await _(e,["-latest","-products","*","-requires","Microsoft.VisualStudio.Component.VC.Tools.x86.x64","-property","installationPath"],t),n=se(s.trim());if(n)return n}catch{}let i=["C:\\Program Files\\Microsoft Visual Studio\\18","C:\\Program Files\\Microsoft Visual Studio\\2026","C:\\Program Files\\Microsoft Visual Studio\\2022"];for(let s of i){let n=se(s);if(n)return n}return null}function ie(t){if(!t)return null;let e=m.join(t,"extensions","chthonic-archive");if(u.existsSync(m.join(e,"package.json")))return e;if(u.existsSync(m.join(t,"package.json")))return t;return null}async function di(t){let e=m.join(process.env["ProgramFiles(x86)"]||"C:\\Program Files (x86)","Microsoft Visual Studio","Installer","vswhere.exe");if(!u.existsSync(e))return null;let i=[["-prerelease","-latest","-products","Microsoft.VisualStudio.Product.Professional","-property","installationVersion"],["-prerelease","-latest","-products","Microsoft.VisualStudio.Product.BuildTools","-property","installationVersion"]];for(let s of i)try{let a=(await _(e,s,t)).trim();if(a.length>0)return a}catch{}return null}function se(t){if(!u.existsSync(t))return null;let e=[],i=[t];while(i.length>0){let s=i.pop(),n=[];try{n=u.readdirSync(s,{withFileTypes:!0})}catch{continue}for(let a of n){let c=m.join(s,a.name);if(!a.isDirectory())continue;if(a.name==="include"&&c.includes(`${m.sep}VC${m.sep}Tools${m.sep}MSVC${m.sep}`)){e.push(c);continue}i.push(c)}}if(e.length===0)return null;return e.sort((s,n)=>n.localeCompare(s,void 0,{numeric:!0,sensitivity:"base"})),e[0]}async function _(t,e,i){return new Promise((s,n)=>{Z.execFile(t,e,{cwd:i||void 0,windowsHide:!0,timeout:15000},(a,c,p)=>{if(a){n(Error(`${t} ${e.join(" ")} failed: ${p||a.message}`));return}s(String(c).trim())})})}async function li(t,e){if(process.platform==="win32")try{return await _("where",[t],e),!0}catch{return!1}try{return await _("which",[t],e),!0}catch{return!1}}async function Rt(t,e,i,s){await new Promise((n,a)=>{let c=Z.spawn(t,e,{cwd:i||void 0,windowsHide:!0,stdio:["ignore","pipe","pipe"]});c.stdout.on("data",(p)=>{s.appendLine(`[slab-heal] ${p.toString().trimEnd()}`)}),c.stderr.on("data",(p)=>{s.appendLine(`[slab-heal] ${p.toString().trimEnd()}`)}),c.on("error",a),c.on("exit",(p)=>{if(p===0)n();else a(Error(`${t} ${e.join(" ")} exited with code ${p??-1}`))})})}function pi(t,e){let i=t.trim();if(!i)return"";switch(e){case"go":return i.replace(/^go/i,"");case"rust":return i.replace(/^rustc\s+/i,"").split(/\s+/)[0]??"";case"solana":return i.replace(/^solana-cli\s+/i,"").split(/\s+/)[0]??"";case"visual-studio":return i.split(/\s+/)[0]??"";default:return i}}function hi(t,e){let i=e.split(".");if(t==="go")return i.slice(0,2).join(".");if(t==="solana")return i.slice(0,1).join(".");if(t==="visual-studio")return i.slice(0,2).join(".");return i.slice(0,2).join(".")}function ui(t){switch(t){case"solana":return["solana","agave","solana-cli"];case"visual-studio":return["visual-studio"];default:return[t]}}function N(t){if(t instanceof Error)return`${t.name}: ${t.message}`;return String(t)}function mi(t){console.log("☥ Chthonic Archive extension activated");let e=r.window.createOutputChannel("Chthonic SDK"),i=r.workspace.workspaceFolders?.[0]?.uri.fsPath||null,s=r.workspace.getConfiguration("chthonic"),n=U.join(i||"","meta-ide","copilot-sdk","harness.ts"),a=new F(t.extensionUri,n,(o)=>e.appendLine(`[${new Date().toISOString()}] ${o}`));t.subscriptions.push(r.window.registerWebviewViewProvider(F.viewType,a));let c=new Et(t.extensionUri,e),p=new kt(e),g=new wt(e),et=new X,I=new Lt(e,t.environmentVariableCollection,i);t.subscriptions.push(c,et,I,r.window.registerWebviewViewProvider(X.viewType,et));let h=s,de=h.get("entropy.enabled",!0),le=h.get("entropy.maxFiles",1e4),pe=h.get("entropy.scanIntervalMs",20000),he=h.get("entropy.decorationDebounceMs",120),ue=h.get("entropy.decorationBatchSize",240),me=h.get("entropy.polyglotEnabled",!0),ge=h.get("entropy.pythonScanIntervalMs",30000),fe=h.get("entropy.ledgerSettleDebounceMs",1400),ye=h.get("entropy.ledgerMode","validator"),ve=h.get("entropy.solanaRpcUrl","http://127.0.0.1:8899"),be=h.get("entropy.solanaAutostartValidator",!1),xe=tt(h.get("entropy.solanaLedgerHostBinaryPath","")),Se=tt(h.get("entropy.solanaWalletPath","")),Ee=tt(h.get("entropy.solanaIdlPath","")),b=new ct(t,e),V,$=new vt(e,b,{enabled:me,pythonScanIntervalMs:ge,settleDebounceMs:fe,ledgerMode:ye,solanaRpcUrl:ve,solanaAutostartValidator:be,solanaLedgerHostBinaryPath:xe,solanaWalletPath:Se,solanaIdlPath:Ee},(o)=>V?.enqueueExternalUpdates(o));V=new dt(b,he,ue,(o)=>$.getTooltipFragments(o));let R=new Q(t.extensionUri,b);R.setRootPath(i),t.subscriptions.push(b,V,R,$,r.window.registerFileDecorationProvider(V),r.window.registerWebviewViewProvider(Q.viewType,R));let C=async(o)=>{if(!i)return;let l=await te(i);et.update(l),await c.update(l),e.appendLine(`[monolith] rustification ${l.score}% (${l.tier}) via ${o}`)};if(i){C("startup");let o=r.workspace.createFileSystemWatcher(new r.RelativePattern(i,"{uv.lock,Cargo.toml,native/Cargo.toml,mise.toml,.mise.toml,anno-manifest.toml,go.mod,.ruby-version,Gemfile,.node-version,.nvmrc,package.json,bun.lock,.python-version}"));t.subscriptions.push(o,o.onDidCreate(()=>{C("marker-create")}),o.onDidChange(()=>{C("marker-change")}),o.onDidDelete(()=>{C("marker-delete")}))}if(i&&de)b.start(i,le,pe),$.start(i);t.subscriptions.push(r.workspace.onDidSaveTextDocument((o)=>{b.refreshFile(o.uri),$.onDidSaveDocument(o)})),t.subscriptions.push(r.commands.registerCommand("chthonic.entropyRefresh",()=>{b.rescanNow(),b.requestGraph(260),$.requestManualScan(),r.window.showInformationMessage("Chthonic entropy scan requested")}));let ke=h.get("reactor.enabled",!0),Pe=h.get("reactor.headlessVulkan",!0),we=h.get("reactor.cockpitAutoLayout",!1),Re=h.get("reactor.transport","auto"),Le=tt(h.get("reactor.daemonBinaryPath","")),Me=h.get("slab.selfHealingEnabled",!0),$t=h.get("slab.selfHealingIntervalMs",21600000),Ct=h.get("slab.eolApiBase","https://endoflife.date/api"),$e=yi(Ct),Ce=Math.max(60000,Math.floor($t/2)),f=new bt(e,Pe,Le,$e,Ce),J=new xt(e,t.environmentVariableCollection),it=new SynapseBridge(e,t.extensionPath,Re),st=null,nt=null,q=null,Dt=(o,l)=>{let S=l?`${o} (${l.toLocaleString()} tps)`:o;e.appendLine(`[loom-reflex] panel lane ${S}`),g.activate()},De=(o)=>{e.appendLine(`[loom-reflex] primary lane ${o}`),r.commands.executeCommand("workbench.view.extension.chthonic-archive"),r.commands.executeCommand("chthonic.loomView.focus")};t.subscriptions.push(f,J,it);let Bt=(o)=>{if(c.updateEntropy(o),e.appendLine(`[lens] decay ${Math.round(o.decay_score*100)}% (${o.status}) from ${o.source_mise??"no-mise"}`),o.validator_active){let y=`${o.validator_process??"validator"}:${o.validator_source_mise}`;if(y!==nt)nt=y,De(`validator-online:${y}`)}else nt=null;if(o.firedancer_surge&&o.validator_active){let y=`${o.checked_at_epoch_ms}:${o.simulated_tps}`;if(y!==q)q=y,Dt("entropy-surge",o.simulated_tps)}else q=null;if(!o.critical||!o.auto_update_enabled){st=null;return}let l=`${o.status}:${o.auto_update}:${[...o.critical_tools].sort().join(",")}`;if(l===st)return;st=l;let S=o.critical_tools.length>0?o.critical_tools.join(", "):"runtime toolchain";r.window.showWarningMessage(`Chthonic decay is critical (${Math.round(o.decay_score*100)}%). ${S} needs healing.`,"Run mise upgrade","Later").then((y)=>{if(y==="Run mise upgrade")I.runNow("manual")})};if(t.subscriptions.push(f.onDidReceiveEnv((o)=>{J.applyTerminalEnv(o)}),f.onDidReceiveSediment((o)=>{R.postSedimentData(o)}),f.onDidReceiveSedimentChunk((o)=>{R.postSedimentChunk(o)}),f.onDidReceiveSynapse((o)=>{it.updateDescriptor(o)}),f.onDidReceiveEntropyState((o)=>{Bt(o)}),f.onDidReceiveFiredancerSurge((o)=>{if(o.surge){let l=`${o.slot}:${o.simulated_tps}`;if(l!==q)q=l,Dt("daemon-surge",o.simulated_tps)}})),R.onRequestSediment(()=>{fi(f,R,it,e)}),i&&ke){if(f.start(i),f.requestEntropyState().then((l)=>{Bt(l)}).catch((l)=>{e.appendLine(`[lens] initial entropy snapshot unavailable: ${l}`)}),we)J.activate();let o=U.join(i,".git","HEAD");if(M.existsSync(o)){let l=null,S=M.watch(U.join(i,".git"),{persistent:!1},(y,_t)=>{if(_t==="HEAD"||_t?.startsWith("refs")){if(l)clearTimeout(l);l=setTimeout(()=>{e.appendLine("[reactor] git change detected, recomputing sediment"),f.requestSediment(10,500).catch((Be)=>{e.appendLine(`[reactor] live-loop sediment failed: ${Be}`)})},800)}});t.subscriptions.push({dispose:()=>S.close()})}}if(i&&Me)I.start({intervalMs:$t,eolApiBase:Ct}),I.runNow("interval");if(t.subscriptions.push(r.commands.registerCommand("chthonic.activateCockpit",()=>{J.activate()}),r.commands.registerCommand("chthonic.deepFocus",()=>{p.activate()}),r.commands.registerCommand("chthonic.restoreOrder",()=>{g.activate()}),r.commands.registerCommand("chthonic.slabHeal",()=>{I.runNow("manual")}),r.commands.registerCommand("chthonic.refreshRustification",()=>{C("manual-command")}),r.commands.registerCommand("chthonic.annoDetect",()=>{if(i)f.start(i);r.window.showInformationMessage("ANNO project detection triggered")}),r.commands.registerCommand("chthonic.reactorSediment",async()=>{try{let o=await f.requestSediment(10,500);r.window.showInformationMessage(`Sediment computed: ${o.file_count} files, ${o.layer_count} layers (${o.backend}, ${o.compute_time_ms}ms)`)}catch(o){r.window.showErrorMessage(`Sediment computation failed: ${o}`)}}),r.commands.registerCommand("chthonic.openWebCockpit",()=>{let o=vi(s);r.env.openExternal(r.Uri.parse(o))}),r.commands.registerCommand("chthonic.startWebCockpit",()=>{if(!i){r.window.showWarningMessage("Workspace root is required to start the Bun/Next cockpit.");return}let o=r.window.createTerminal({name:"Chthonic Web Cockpit",cwd:i});o.show(),o.sendText("bun run web:dev"),e.appendLine("[web-cockpit] started via bun run web:dev")}),r.commands.registerCommand("chthonic.openBunTrainingDocs",async()=>{let o=[{label:"Bun React Guide",description:"Build a React app with Bun",url:"https://bun.com/docs/guides/ecosystem/react#build-a-react-app-with-bun"},{label:"Bun Next.js Guide",description:"Build an app with Next.js and Bun",url:"https://bun.com/docs/guides/ecosystem/nextjs#build-an-app-with-next-js-and-bun"},{label:"Bun Tailwind (Fullstack Bundler)",description:"Tailwind plugin lane for Bun fullstack",url:"https://bun.com/docs/bundler/fullstack#tailwindcss-plugin"},{label:"Bun SQLite API",description:"Typed SQL training lane (bun:sqlite)",url:"https://bun.com/docs/api/sqlite"}],l=await r.window.showQuickPick(o,{placeHolder:"Open Bun training docs"});if(!l)return;r.env.openExternal(r.Uri.parse(l.url))}),r.commands.registerCommand("chthonic.postRestartVerify",()=>{if(!i){r.window.showWarningMessage("Workspace root is required to run post-restart verification.");return}let o=r.window.createTerminal({name:"Chthonic Post-Restart Verify",cwd:i});o.show(),o.sendText("bun run --cwd extensions/chthonic-archive insiders:post-restart:verify"),e.appendLine("[insiders] post-restart verification lane started")}),r.commands.registerCommand("chthonic.restartGate",()=>{if(!i){r.window.showWarningMessage("Workspace root is required to run restart gate checks.");return}let o=r.window.createTerminal({name:"Chthonic Restart Gate",cwd:i});o.show(),o.sendText("bun run --cwd extensions/chthonic-archive insiders:restart:gate"),e.appendLine("[insiders] restart gate check lane started")})),i&&s.get("webCockpit.autoStart",!1))r.commands.executeCommand("chthonic.startWebCockpit");let ot=new ae;r.window.registerTreeDataProvider("chthonic.themeView",ot),t.subscriptions.push(r.commands.registerCommand("chthonic.switchTheme",async()=>{let o=[{label:"$(paintcan) Flesh & Earth",description:"Warm earth · WCAG AA · Distribution palette",id:"Chthonic Mandala - Flesh & Earth"},{label:"$(zap) ROGBIV",description:"SSOT spectral · FA¹⁻⁵ canonical hexes",id:"Chthonic Mandala - ROGBIV"}],l=r.workspace.getConfiguration("workbench").get("colorTheme"),S=await r.window.showQuickPick(o.map((y)=>({...y,picked:l===y.id})),{placeHolder:`Current: ${l}`});if(S)await r.workspace.getConfiguration("workbench").update("colorTheme",S.id,r.ConfigurationTarget.Workspace),r.window.showInformationMessage(`Theme: ${S.id}`),ot.refresh()}));let Tt=s;if(Tt.get("showSSOTHash",!0)){let o=r.window.createStatusBarItem(r.StatusBarAlignment.Left,50);o.command="chthonic.verifySSOT",o.tooltip="SSOT integrity hash — click to verify",t.subscriptions.push(o),oe(o),t.subscriptions.push(r.workspace.onDidSaveTextDocument((l)=>{if(l.fileName.includes("copilot-instructions"))oe(o)}))}if(Tt.get("showLineage",!0)){let o=r.window.createStatusBarItem(r.StatusBarAlignment.Left,49);o.text="$(git-branch) ☥ main",o.tooltip="Chthonic lineage",o.show(),t.subscriptions.push(o)}let At=new ce;r.window.registerTreeDataProvider("chthonic.statusView",At),t.subscriptions.push(r.commands.registerCommand("chthonic.verifySSOT",async()=>{let o=Mt();if(o)r.window.showInformationMessage(`SSOT SHA-256: ${o.substring(0,16)}…`);else r.window.showWarningMessage("SSOT file not found")})),t.subscriptions.push(r.commands.registerCommand("chthonic.refreshStatus",()=>{At.refresh(),ot.refresh(),b.rescanNow(),b.requestGraph(260),$.requestManualScan(),C("refresh-status")}))}function gi(){}async function fi(t,e,i,s){try{if(i.isReady()){let n=await t.requestSedimentSynapse(10,500,220);if(n.transport==="shared_memory"){let a=await i.drain(n,(c)=>{e.postSedimentBinary(c)});s.appendLine(`[reactor] synapse drain ${a}/${n.chunks_written} chunks`);return}}await t.requestSedimentStream(10,500)}catch(n){s.appendLine(`[reactor] sediment request failed: ${n}`)}}function Mt(){let t=r.workspace.workspaceFolders?.[0];if(!t)return null;let e=r.workspace.getConfiguration("chthonic").get("ssotPath",".github/copilot-instructions.md"),i=U.join(t.uri.fsPath,e);if(!M.existsSync(i))return null;let n=M.readFileSync(i,"utf-8").replace(/\r\n/g,`
`).replace(/\r/g,`
`).split(`
`).map((a)=>a.trimEnd()).join(`
`).trim();return re.createHash("sha256").update(n,"utf-8").digest("hex")}function oe(t){let e=Mt();if(e)t.text=`$(shield) ${e.substring(0,8)}`,t.show();else t.text="$(shield) SSOT ??",t.show()}function tt(t){let e=t.trim();return e.length>0?e:void 0}function yi(t){let e=t.trim().replace(/\/+$/,"");if(e.endsWith("/api"))return`${e}/v1`;return e.length>0?e:"https://endoflife.date/api/v1"}function vi(t){let e=t.get("webCockpit.url","http://127.0.0.1:3000").trim();if(/^https?:\/\//i.test(e))return e;return`http://${e}`}class ae{_onDidChange=new r.EventEmitter;onDidChangeTreeData=this._onDidChange.event;refresh(){this._onDidChange.fire()}getTreeItem(t){return t}getChildren(){let t=r.workspace.getConfiguration("workbench").get("colorTheme")||"";return[{name:"Chthonic Mandala - Flesh & Earth",short:"Flesh & Earth",icon:"\uD83C\uDF0D",desc:"Warm earth · Distribution"},{name:"Chthonic Mandala - ROGBIV",short:"ROGBIV",icon:"\uD83C\uDF08",desc:"SSOT spectral · Research"}].map((i)=>{let s=t===i.name,n=new r.TreeItem(`${s?"◉":"○"} ${i.icon} ${i.short}`,r.TreeItemCollapsibleState.None);return n.tooltip=`${i.name}
${i.desc}${s?`

✅ ACTIVE`:""}`,n.description=s?"active":"",n.command={command:"chthonic.switchTheme",title:"Switch"},n})}}class ce{_onDidChange=new r.EventEmitter;onDidChangeTreeData=this._onDidChange.event;refresh(){this._onDidChange.fire()}getTreeItem(t){return t}getChildren(){let t=Mt(),e=[],i=new r.TreeItem(`$(shield) SSOT: ${t?t.substring(0,12)+"…":"not found"}`,r.TreeItemCollapsibleState.None);i.command={command:"chthonic.verifySSOT",title:"Verify"},e.push(i);let s=new r.TreeItem(`$(paintcan) Theme: ${(r.workspace.getConfiguration("workbench").get("colorTheme")||"default").replace("Chthonic Mandala - ","")}`,r.TreeItemCollapsibleState.None);return s.command={command:"chthonic.switchTheme",title:"Switch"},e.push(s),e}}
