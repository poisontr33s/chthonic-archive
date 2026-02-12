var D=Object.create;var{getPrototypeOf:S,defineProperty:p,getOwnPropertyNames:w,getOwnPropertyDescriptor:F}=Object,E=Object.prototype.hasOwnProperty;var l=(e,t,s)=>{s=e!=null?D(S(e)):{};let a=t||!e||!e.__esModule?p(s,"default",{value:e,enumerable:!0}):s;for(let o of w(e))if(!E.call(a,o))p(a,o,{get:()=>e[o],enumerable:!0});return a},k=new WeakMap,_=(e)=>{var t=k.get(e),s;if(t)return t;if(t=p({},"__esModule",{value:!0}),e&&typeof e==="object"||typeof e==="function")w(e).map((a)=>!E.call(t,a)&&p(t,a,{get:()=>e[a],enumerable:!(s=F(e,a))||s.enumerable}));return k.set(e,t),t};var q=(e,t)=>{for(var s in t)p(e,s,{get:t[s],enumerable:!0,configurable:!0,set:(a)=>t[s]=()=>a})};var W={};q(W,{deactivate:()=>N,activate:()=>H});module.exports=_(W);var n=l(require("vscode")),I=l(require("crypto")),h=l(require("fs")),f=l(require("path"));var A=l(require("vscode")),v=l(require("child_process"));var M=l(require("child_process")),C=l(require("readline")),g=l(require("path"));class m{harnessPath;log;process=null;rl=null;handlers=new Set;authenticated=!1;ready=!1;constructor(e,t){this.harnessPath=e;this.log=t}async start(){if(this.process)return;let e=g.dirname(this.harnessPath),t=g.basename(this.harnessPath);this.process=M.spawn("bun",["run",t],{cwd:e,stdio:["pipe","pipe","pipe"],env:{...process.env}}),this.process.stderr?.on("data",(s)=>{this.log(`[harness stderr] ${s.toString().trim()}`)}),this.process.on("close",(s)=>{this.log(`[harness] exited with code ${s}`),this.process=null,this.rl=null,this.ready=!1,this.authenticated=!1}),this.rl=C.createInterface({input:this.process.stdout}),this.rl.on("line",(s)=>{try{let a=JSON.parse(s);if(a.type==="ready")this.ready=!0,this.log(`[harness] ready: ${a.sdk}`);for(let o of this.handlers)o(a)}catch{this.log(`[harness] non-JSON: ${s.substring(0,200)}`)}}),await new Promise((s,a)=>{let o=setTimeout(()=>a(Error("Harness startup timeout")),15000),r=(c)=>{if(c.type==="ready")clearTimeout(o),this.handlers.delete(r),s()};this.handlers.add(r)})}async authenticate(e,t){this.send({cmd:"auth",token:e,login:t}),await this.waitFor("auth_ok"),this.authenticated=!0,this.log(`[harness] authenticated as ${t}`)}query(e,t,s,a,o){return new Promise((r,c)=>{let i=(d)=>{if(d.id!==e)return;if(d.type==="event"&&d.event)a(d.event);else if(d.type==="done")this.handlers.delete(i),r();else if(d.type==="cancelled")this.handlers.delete(i),r();else if(d.type==="error")this.handlers.delete(i),c(Error(d.message||"Query failed"))};this.handlers.add(i),this.send({cmd:"query",id:e,prompt:t,workingDirectory:s,model:o?.model,reasoningEffort:o?.reasoningEffort})})}cancel(e){this.send({cmd:"cancel",id:e})}async getModels(){return this.send({cmd:"models"}),(await this.waitFor("models")).data||[]}isReady(){return this.ready&&this.authenticated&&this.process!==null}stop(){if(this.process)this.process.kill(),this.process=null;this.rl=null,this.ready=!1,this.authenticated=!1,this.handlers.clear()}send(e){if(!this.process?.stdin?.writable)throw Error("Harness not running");this.process.stdin.write(JSON.stringify(e)+`
`)}waitFor(e,t=15000){return new Promise((s,a)=>{let o=setTimeout(()=>{this.handlers.delete(r),a(Error(`Timeout waiting for ${e}`))},t),r=(c)=>{if(c.type===e)clearTimeout(o),this.handlers.delete(r),s(c);else if(c.type==="error")clearTimeout(o),this.handlers.delete(r),a(Error(c.message||"Error"))};this.handlers.add(r)})}}class u{extensionUri;harnessPath;log;static viewType="chthonic.chatView";view;connection=null;isConnecting=!1;activeQueryId=null;constructor(e,t,s){this.extensionUri=e;this.harnessPath=t;this.log=s}resolveWebviewView(e,t,s){this.view=e,e.webview.options={enableScripts:!0,localResourceRoots:[this.extensionUri]},e.webview.html=this.getHtml(),e.webview.onDidReceiveMessage(async(a)=>{switch(a.type){case"connect":await this.connectAgent();break;case"prompt":await this.sendPrompt(a.text);break;case"cancel":this.cancelQuery();break;case"disconnect":this.disconnectAgent();break}})}async connectAgent(){if(this.isConnecting||this.connection?.isReady())return;this.isConnecting=!0,this.postMessage({type:"status",status:"connecting"});try{this.connection=new m(this.harnessPath,this.log),await this.connection.start();let e=v.execSync("gh auth token",{encoding:"utf-8"}).trim(),t=v.execSync("gh api user --jq .login",{encoding:"utf-8"}).trim();await this.connection.authenticate(e,t),this.postMessage({type:"connected",agentName:"Chthonic SDK",agentVersion:"0.1.0",login:t}),this.log(`Chat connected: ${t}`)}catch(e){this.log(`Chat connect failed: ${e.message}`),this.postMessage({type:"error",message:e.message}),this.connection?.stop(),this.connection=null}finally{this.isConnecting=!1}}async sendPrompt(e){if(!this.connection?.isReady()){this.postMessage({type:"error",message:"Not connected"});return}let t=crypto.randomUUID();this.activeQueryId=t,this.postMessage({type:"prompt-start"});let s=A.workspace.workspaceFolders?.[0]?.uri.fsPath||process.cwd();try{await this.connection.query(t,e,s,(a)=>this.handleSdkEvent(a))}catch(a){this.postMessage({type:"error",message:a.message})}finally{this.activeQueryId=null,this.postMessage({type:"prompt-end"})}}handleSdkEvent(e){switch(e.type){case"assistant.message":if(e.data?.content)this.postMessage({type:"agent-message",content:e.data.content});break;case"assistant.message.delta":if(e.data?.delta)this.postMessage({type:"agent-delta",delta:e.data.delta});break;case"tool.execution_start":this.postMessage({type:"tool-start",name:e.data?.name,args:e.data?.arguments});break;case"tool.execution_complete":this.postMessage({type:"tool-end",name:e.data?.name});break;case"assistant.reasoning":this.postMessage({type:"reasoning"});break;case"assistant.usage":this.postMessage({type:"usage",model:e.data?.model,inputTokens:e.data?.inputTokens,outputTokens:e.data?.outputTokens,duration:e.data?.duration});break;case"session.usage_info":this.postMessage({type:"context-info",tokenLimit:e.data?.tokenLimit,currentTokens:e.data?.currentTokens});break}}cancelQuery(){if(this.activeQueryId&&this.connection)this.connection.cancel(this.activeQueryId)}disconnectAgent(){this.connection?.stop(),this.connection=null,this.activeQueryId=null,this.postMessage({type:"disconnected"})}postMessage(e){this.view?.webview.postMessage(e)}dispose(){this.connection?.stop()}getHtml(){return`<!DOCTYPE html>
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
</html>`}}function H(e){console.log("☥ Chthonic Archive extension activated");let t=n.window.createOutputChannel("Chthonic SDK"),s=f.join(n.workspace.workspaceFolders?.[0]?.uri.fsPath||"","meta-ide","copilot-sdk","harness.ts"),a=new u(e.extensionUri,s,(i)=>t.appendLine(`[${new Date().toISOString()}] ${i}`));e.subscriptions.push(n.window.registerWebviewViewProvider(u.viewType,a));let o=new Q;n.window.registerTreeDataProvider("chthonic.themeView",o),e.subscriptions.push(n.commands.registerCommand("chthonic.switchTheme",async()=>{let i=[{label:"$(paintcan) Flesh & Earth",description:"Warm earth · WCAG AA · Distribution palette",id:"Chthonic Mandala - Flesh & Earth"},{label:"$(zap) ROGBIV",description:"SSOT spectral · FA¹⁻⁵ canonical hexes",id:"Chthonic Mandala - ROGBIV"}],d=n.workspace.getConfiguration("workbench").get("colorTheme"),y=await n.window.showQuickPick(i.map((x)=>({...x,picked:d===x.id})),{placeHolder:`Current: ${d}`});if(y)await n.workspace.getConfiguration("workbench").update("colorTheme",y.id,n.ConfigurationTarget.Workspace),n.window.showInformationMessage(`Theme: ${y.id}`),o.refresh()}));let r=n.workspace.getConfiguration("chthonic");if(r.get("showSSOTHash",!0)){let i=n.window.createStatusBarItem(n.StatusBarAlignment.Left,50);i.command="chthonic.verifySSOT",i.tooltip="SSOT integrity hash — click to verify",e.subscriptions.push(i),B(i),e.subscriptions.push(n.workspace.onDidSaveTextDocument((d)=>{if(d.fileName.includes("copilot-instructions"))B(i)}))}if(r.get("showLineage",!0)){let i=n.window.createStatusBarItem(n.StatusBarAlignment.Left,49);i.text="$(git-branch) ☥ main",i.tooltip="Chthonic lineage",i.show(),e.subscriptions.push(i)}let c=new z;n.window.registerTreeDataProvider("chthonic.statusView",c),e.subscriptions.push(n.commands.registerCommand("chthonic.verifySSOT",async()=>{let i=b();if(i)n.window.showInformationMessage(`SSOT SHA-256: ${i.substring(0,16)}…`);else n.window.showWarningMessage("SSOT file not found")})),e.subscriptions.push(n.commands.registerCommand("chthonic.refreshStatus",()=>{c.refresh(),o.refresh()}))}function N(){}function b(){let e=n.workspace.workspaceFolders?.[0];if(!e)return null;let t=n.workspace.getConfiguration("chthonic").get("ssotPath",".github/copilot-instructions.md"),s=f.join(e.uri.fsPath,t);if(!h.existsSync(s))return null;let o=h.readFileSync(s,"utf-8").replace(/\r\n/g,`
`).replace(/\r/g,`
`).split(`
`).map((r)=>r.trimEnd()).join(`
`).trim();return I.createHash("sha256").update(o,"utf-8").digest("hex")}function B(e){let t=b();if(t)e.text=`$(shield) ${t.substring(0,8)}`,e.show();else e.text="$(shield) SSOT ??",e.show()}class Q{_onDidChange=new n.EventEmitter;onDidChangeTreeData=this._onDidChange.event;refresh(){this._onDidChange.fire()}getTreeItem(e){return e}getChildren(){let e=n.workspace.getConfiguration("workbench").get("colorTheme")||"";return[{name:"Chthonic Mandala - Flesh & Earth",short:"Flesh & Earth",icon:"\uD83C\uDF0D",desc:"Warm earth · Distribution"},{name:"Chthonic Mandala - ROGBIV",short:"ROGBIV",icon:"\uD83C\uDF08",desc:"SSOT spectral · Research"}].map((s)=>{let a=e===s.name,o=new n.TreeItem(`${a?"◉":"○"} ${s.icon} ${s.short}`,n.TreeItemCollapsibleState.None);return o.tooltip=`${s.name}
${s.desc}${a?`

✅ ACTIVE`:""}`,o.description=a?"active":"",o.command={command:"chthonic.switchTheme",title:"Switch"},o})}}class z{_onDidChange=new n.EventEmitter;onDidChangeTreeData=this._onDidChange.event;refresh(){this._onDidChange.fire()}getTreeItem(e){return e}getChildren(){let e=b(),t=[],s=new n.TreeItem(`$(shield) SSOT: ${e?e.substring(0,12)+"…":"not found"}`,n.TreeItemCollapsibleState.None);s.command={command:"chthonic.verifySSOT",title:"Verify"},t.push(s);let a=new n.TreeItem(`$(paintcan) Theme: ${(n.workspace.getConfiguration("workbench").get("colorTheme")||"default").replace("Chthonic Mandala - ","")}`,n.TreeItemCollapsibleState.None);return a.command={command:"chthonic.switchTheme",title:"Switch"},t.push(a),t}}
