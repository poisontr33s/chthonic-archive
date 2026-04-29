(function() {
  const vscode = acquireVsCodeApi();
  const hmrKey = 'chthonic.hmr.stylus.reloadCount';
  const reloadCount = Number(sessionStorage.getItem(hmrKey) || '0');
  const pad    = document.getElementById('pad');
  const count  = document.getElementById('char-count');
  const status = document.getElementById('status');
  const penInd = document.getElementById('pen-indicator');

  let penActive = false;

  // ── Pen detection via Pointer Events ─────────────────────────
  function onPointerMove(e) {
    const isPen = e.pointerType === 'pen';
    if (isPen !== penActive) {
      penActive = isPen;
      penInd.classList.toggle('active', isPen);
      if (isPen) pad.focus();
    }
  }
  window.addEventListener('pointermove', onPointerMove, { passive: true });
  window.addEventListener('pointerdown', onPointerMove, { passive: true });

  // ── Char count ────────────────────────────────────────────────
  pad.addEventListener('input', () => {
    count.textContent = pad.value.length + ' chars';
  });

  // ── Status helpers ────────────────────────────────────────────
  let statusTimer;
  function setStatus(msg, type = '') {
    status.textContent = msg;
    status.className = type;
    clearTimeout(statusTimer);
    statusTimer = setTimeout(() => { status.textContent = ''; status.className = ''; }, 3000);
  }

  function getText() {
    const t = pad.value.trim();
    if (!t) { setStatus('Pad is empty.', 'warn'); return null; }
    return t;
  }

  // ── Route buttons ─────────────────────────────────────────────
  document.getElementById('btn-editor').addEventListener('click', () => {
    const t = getText(); if (!t) return;
    vscode.postMessage({ type: 'insert', text: t });
    setStatus('Sent to editor ✓', 'ok');
  });

  document.getElementById('btn-terminal').addEventListener('click', () => {
    const t = getText(); if (!t) return;
    vscode.postMessage({ type: 'terminal', text: t });
    setStatus('Sent to terminal ✓', 'ok');
  });

  document.getElementById('btn-chat').addEventListener('click', () => {
    const t = getText(); if (!t) return;
    vscode.postMessage({ type: 'chat', text: t });
    setStatus('Sent to chat ✓', 'ok');
  });

  document.getElementById('btn-copy').addEventListener('click', async () => {
    const t = getText(); if (!t) return;
    try {
      await navigator.clipboard.writeText(t);
      setStatus('Copied ✓', 'ok');
    } catch {
      vscode.postMessage({ type: 'insert', text: '' }); // fallback: no-op
      setStatus('Use browser copy (Ctrl+C / long-press)', 'warn');
    }
  });

  document.getElementById('btn-clear').addEventListener('click', () => {
    pad.value = '';
    count.textContent = '0 chars';
    pad.focus();
    setStatus('Cleared.', '');
  });

  function postHmrLoaded() {
    vscode.postMessage({
      type: 'webviewHmr.loaded',
      surface: 'stylus',
      reloadCount,
      html: document.documentElement.outerHTML,
    });
  }

  // ── Focus / HMR messages from extension ───────────────────────
  window.addEventListener('message', (e) => {
    if (e.data?.type === 'focus') {
      pad.focus();
      return;
    }
    if (e.data?.type === 'reload') {
      sessionStorage.setItem(hmrKey, String(reloadCount + 1));
      vscode.postMessage({ type: 'webviewHmr.reloadRequested', surface: 'stylus' });
      setTimeout(() => location.reload(), 100);
    }
  });
  postHmrLoaded();
})();
