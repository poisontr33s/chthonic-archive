/**
 * Chthonic Chat Webview - React 19
 * 
 * Runs inside VSCode webview panel, communicates with extension via postMessage.
 */

import React, { useState, useEffect, useRef } from 'react';
import { createRoot } from 'react-dom/client';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

// VSCode API (injected by webview)
declare const acquireVsCodeApi: () => {
  postMessage: (message: any) => void;
  getState: () => any;
  setState: (state: any) => void;
};

const vscode = acquireVsCodeApi();

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Notify extension that webview is ready
    console.log('🔥 Webview: Initializing, sending ready signal');
    vscode.postMessage({ type: 'ready' });

    // Listen for messages from extension
    const handleMessage = (event: MessageEvent) => {
      console.log('🔥 Webview: Received message from extension:', event.data);
      const message = event.data;
      switch (message.type) {
        case 'response':
          console.log('🔥 Webview: Adding assistant response to chat');
          setMessages(prev => [
            ...prev,
            {
              id: Date.now().toString(),
              role: 'assistant',
              content: message.text,
              timestamp: message.timestamp,
            },
          ]);
          break;
        default:
          console.log('🔥 Webview: Unknown message type:', message.type);
      }
    };

    window.addEventListener('message', handleMessage);
    console.log('🔥 Webview: Message listener attached');
    return () => window.removeEventListener('message', handleMessage);
  }, []);

  useEffect(() => {
    // Auto-scroll to bottom
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    
    console.log('🔥 Webview: Sending message to extension:', input);
    console.log('🔥 Webview: vscode API available:', typeof vscode);
    console.log('🔥 Webview: postMessage type:', typeof vscode.postMessage);
    
    vscode.postMessage({ type: 'sendMessage', text: input });
    console.log('🔥 Webview: Message sent');
    
    setInput('');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <>
      <div className="messages">
        {messages.length === 0 && (
          <div style={{ opacity: 0.5, textAlign: 'center', marginTop: '2rem' }}>
            🔥💀⚓ Chthonic Archive Assistant
            <br />
            <small>Connected to ASC Framework MCP Servers</small>
          </div>
        )}
        {messages.map((msg) => (
          <div key={msg.id} className={`message ${msg.role}`}>
            {msg.content}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      <div className="input-container">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask the Triumvirate..."
          autoFocus
        />
        <button onClick={handleSend}>Send</button>
      </div>
    </>
  );
}

// Mount React app
const root = createRoot(document.getElementById('root')!);
root.render(<App />);
