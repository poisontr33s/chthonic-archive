const vscode = acquireVsCodeApi();

const messages = document.querySelector('[data-role="messages"]');
const form = document.querySelector('[data-role="form"]');
const input = document.querySelector('[data-role="input"]');
const stop = document.querySelector('[data-role="stop"]');

function appendMessage(id, role, content, streaming = false) {
  messages.querySelector('.empty')?.remove();

  const node = document.createElement('article');
  node.className = `message ${role}`;
  node.dataset.id = id;

  const text = document.createElement('pre');
  text.className = 'message-text';
  text.textContent = content;
  node.appendChild(text);

  if (streaming) {
    const caret = document.createElement('span');
    caret.className = 'streaming-caret';
    caret.textContent = '|';
    node.appendChild(caret);
  }

  messages.appendChild(node);
  messages.scrollTop = messages.scrollHeight;
}

function updateStreamingMessage(id, delta) {
  const node = messages.querySelector(`[data-id="${CSS.escape(id)}"]`);
  const text = node?.querySelector('.message-text');
  if (!text) return;
  text.textContent += delta;
  messages.scrollTop = messages.scrollHeight;
}

function finishStreamingMessage(id) {
  const node = messages.querySelector(`[data-id="${CSS.escape(id)}"]`);
  node?.querySelector('.streaming-caret')?.remove();
}

form.addEventListener('submit', (event) => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text) return;

  appendMessage(String(Date.now()), 'user', text);
  document.body.dataset.streaming = 'true';
  vscode.postMessage({ type: 'sendMessage', text });
  input.value = '';
});

stop?.addEventListener('click', () => {
  vscode.postMessage({ type: 'cancel' });
  document.body.dataset.streaming = 'false';
});

window.addEventListener('message', (event) => {
  const message = event.data;

  switch (message.type) {
    case 'responseStart':
      appendMessage(message.id, 'assistant', '', true);
      break;
    case 'responseChunk':
      updateStreamingMessage(message.id, message.delta);
      break;
    case 'responseEnd':
      finishStreamingMessage(message.id);
      document.body.dataset.streaming = 'false';
      break;
    case 'response':
      appendMessage(String(Date.now()), 'assistant', message.text);
      document.body.dataset.streaming = 'false';
      break;
    default:
      break;
  }
});

vscode.postMessage({ type: 'ready' });
