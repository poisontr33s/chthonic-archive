// @SID: EXT_EXTENSION_V1
/**
 * Chthonic Archive VSCode Extension
 * 
 * Provides a sidebar chat interface using GitHub Copilot Chat API.
 * Built with Bun, React 19, and the ASC Framework.
 * 
 * KISS Architecture: Leverages existing Copilot Pro/Plus subscription
 * instead of local MCP servers.
 */

import * as vscode from 'vscode';
import { join } from 'path';
import { readFile } from 'fs/promises';

let chatPanel: vscode.WebviewPanel | undefined;

export function activate(context: vscode.ExtensionContext) {
  console.log('🔥 Chthonic Archive Assistant activating...');

  // Register chat panel provider
  const provider = new ChthonicChatProvider(context.extensionUri);
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider('chthonic.chatView', provider)
  );

  // Register commands
  context.subscriptions.push(
    vscode.commands.registerCommand('chthonic.openChat', () => {
      if (chatPanel) {
        chatPanel.reveal(vscode.ViewColumn.Beside);
      } else {
        chatPanel = vscode.window.createWebviewPanel(
          'chthonicChat',
          'Chthonic Chat',
          vscode.ViewColumn.Beside,
          {
            enableScripts: true,
            retainContextWhenHidden: true,
          }
        );
        chatPanel.webview.html = provider.getHtmlForWebview(chatPanel.webview);
        chatPanel.onDidDispose(() => {
          chatPanel = undefined;
        });
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('chthonic.injectSSOT', async () => {
      const ssotPath = await getSSOTPath();
      if (!ssotPath) {
        vscode.window.showErrorMessage('SSOT file not found');
        return;
      }
      const content = await readFile(ssotPath, 'utf-8');
      vscode.window.showInformationMessage(`SSOT loaded (${content.length} bytes)`);
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand('chthonic.validateHash', async () => {
      const ssotPath = await getSSOTPath();
      if (!ssotPath) return;
      
      // TODO: Implement hash validation using ssot_hash.py
      vscode.window.showInformationMessage('SSOT hash validation: TODO');
    })
  );

  console.log('🔥💀⚓ Chthonic Archive Assistant activated');
}

export function deactivate() {
  console.log('Chthonic Archive Assistant deactivated');
}

class ChthonicChatProvider implements vscode.WebviewViewProvider {
  constructor(private readonly extensionUri: vscode.Uri) {}

  public resolveWebviewView(
    webviewView: vscode.WebviewView,
    context: vscode.WebviewViewResolveContext,
    _token: vscode.CancellationToken
  ) {
    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [this.extensionUri],
    };

    webviewView.webview.html = this.getHtmlForWebview(webviewView.webview);

    // Handle messages from webview
    webviewView.webview.onDidReceiveMessage(async (message) => {
      console.log('🔥 Extension: Received message from webview:', message);
      switch (message.type) {
        case 'sendMessage':
          console.log('🔥 Extension: Handling sendMessage:', message.text);
          await this.handleChatMessage(message.text, webviewView.webview);
          break;
        case 'ready':
          console.log('🔥 Extension: Webview ready');
          break;
        default:
          console.log('🔥 Extension: Unknown message type:', message.type);
      }
    });
  }

  private async handleChatMessage(text: string, webview: vscode.Webview) {
    const debugLog: string[] = [];
    
    try {
      debugLog.push('✓ Step 1: handleChatMessage called');

      // Check if vscode.lm API is available
      if (!vscode.lm) {
        throw new Error('✗ vscode.lm API not available. Update VSCode to 1.90+');
      }
      debugLog.push('✓ Step 2: vscode.lm API available');

      // Load SSOT context
      const ssotPath = await getSSOTPath();
      let systemPrompt = 'You are the Chthonic Archive Assistant powered by the ASC Framework.';
      
      if (ssotPath) {
        try {
          const ssotContent = await readFile(ssotPath, 'utf-8');
          systemPrompt = ssotContent;
          debugLog.push(`✓ Step 3: SSOT loaded (${ssotContent.length} bytes)`);
        } catch (err) {
          debugLog.push(`⚠ Step 3: SSOT not loaded - ${err}`);
        }
      } else {
        debugLog.push('⚠ Step 3: SSOT path not found');
      }

      // Try to select Copilot models (with fallback)
      debugLog.push('→ Step 4: Attempting to select Copilot models...');
      let models = await vscode.lm.selectChatModels({
        vendor: 'copilot',
        family: 'gpt-4o',
      });

      if (models.length === 0) {
        debugLog.push('⚠ Step 4a: gpt-4o not found, trying vendor-only...');
        models = await vscode.lm.selectChatModels({ vendor: 'copilot' });
      }

      if (models.length === 0) {
        debugLog.push('⚠ Step 4b: No copilot models, trying any model...');
        models = await vscode.lm.selectChatModels();
      }

      if (models.length === 0) {
        throw new Error('✗ No language models available. Ensure GitHub Copilot is enabled and authenticated.');
      }

      const model = models[0];
      debugLog.push(`✓ Step 5: Model selected: ${model.vendor}/${model.family} (${model.name})`);

      const messages = [
        vscode.LanguageModelChatMessage.User(systemPrompt),
        vscode.LanguageModelChatMessage.User(text),
      ];
      debugLog.push(`✓ Step 6: Messages prepared (${messages.length} messages)`);

      debugLog.push('→ Step 7: Sending request to Copilot API...');
      const response = await model.sendRequest(messages, {}, new vscode.CancellationTokenSource().token);
      debugLog.push('✓ Step 7: Response received');

      // Stream response back to webview
      debugLog.push('→ Step 8: Streaming response...');
      let fullResponse = '';
      for await (const chunk of response.text) {
        fullResponse += chunk;
      }
      debugLog.push(`✓ Step 8: Response complete (${fullResponse.length} chars)`);

      webview.postMessage({
        type: 'response',
        text: fullResponse,
        timestamp: new Date().toISOString(),
      });

      debugLog.push('✓ Step 9: SUCCESS - Response sent to webview');
      console.log('🔥 Debug Log:\n' + debugLog.join('\n'));

    } catch (error) {
      console.error('🔥 Copilot API error:', error);
      const errorMsg = error instanceof Error ? error.message : 'Unknown error';
      const stackTrace = error instanceof Error ? error.stack : '';
      
      debugLog.push(`✗ FAILED at current step`);
      debugLog.push(`✗ Error: ${errorMsg}`);
      
      webview.postMessage({
        type: 'response',
        text: `🔥 CHTHONIC DEBUG TRACE:\n\n${debugLog.join('\n')}\n\n━━━━━━━━━━━━━━━━━━━━━━\nERROR DETAILS:\n${errorMsg}\n\nSTACK TRACE:\n${stackTrace}`,
        timestamp: new Date().toISOString(),
      });
      
      console.log('🔥 Debug Log:\n' + debugLog.join('\n'));
    }
  }

  public getHtmlForWebview(webview: vscode.Webview): string {
    const scriptUri = webview.asWebviewUri(
      vscode.Uri.joinPath(this.extensionUri, 'dist', 'index.js')
    );

    const nonce = getNonce();

    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src ${webview.cspSource} 'unsafe-inline' 'unsafe-eval'; style-src ${webview.cspSource} 'unsafe-inline';">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Chthonic Chat</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: var(--vscode-font-family);
      font-size: var(--vscode-font-size);
      color: var(--vscode-foreground);
      background: var(--vscode-editor-background);
      height: 100vh;
      display: flex;
      flex-direction: column;
    }
    #root { flex: 1; display: flex; flex-direction: column; }
    .messages {
      flex: 1;
      overflow-y: auto;
      padding: 1rem;
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }
    .message {
      padding: 0.75rem;
      border-radius: 4px;
      max-width: 85%;
    }
    .message.user {
      background: var(--vscode-inputValidation-infoBorder);
      align-self: flex-end;
    }
    .message.assistant {
      background: var(--vscode-editorWidget-background);
      align-self: flex-start;
      border: 1px solid var(--vscode-editorWidget-border);
    }
    .input-container {
      padding: 1rem;
      border-top: 1px solid var(--vscode-panel-border);
      display: flex;
      gap: 0.5rem;
    }
    input {
      flex: 1;
      background: var(--vscode-input-background);
      color: var(--vscode-input-foreground);
      border: 1px solid var(--vscode-input-border);
      padding: 0.5rem;
      font-family: inherit;
      font-size: inherit;
    }
    button {
      background: var(--vscode-button-background);
      color: var(--vscode-button-foreground);
      border: none;
      padding: 0.5rem 1rem;
      cursor: pointer;
      font-family: inherit;
    }
    button:hover {
      background: var(--vscode-button-hoverBackground);
    }
  </style>
</head>
<body>
  <div id="root"></div>
  <script type="module" src="${scriptUri}"></script>
</body>
</html>`;
  }
}

async function getSSOTPath(): Promise<string | undefined> {
  const workspaceFolders = vscode.workspace.workspaceFolders;
  if (!workspaceFolders) return undefined;

  const config = vscode.workspace.getConfiguration('chthonic');
  const relativePath = config.get<string>('ssotPath', '.github/copilot-instructions.md');
  
  return join(workspaceFolders[0].uri.fsPath, relativePath);
}

function getNonce(): string {
  let text = '';
  const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  for (let i = 0; i < 32; i++) {
    text += possible.charAt(Math.floor(Math.random() * possible.length));
  }
  return text;
}
