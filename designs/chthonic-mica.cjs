// chthonic-mica.cjs - Mica substrate runtime for VS Code Insiders (Win11)
// Called from main.js via dynamic import. CJS so require('electron') works.
// This file owns exactly one thing: window.setBackgroundMaterial(...).
// CSS depth is vibrancy-obsidian.css (injected via workbench.html).
// Color authority stays with Sister Ferrum Scoriae. Made by Claude.
const electron = require('electron');
const fs = require('fs');
const path = require('path');

const DIAG = path.join(__dirname, '..', '.chthonic', 'mica-diag.txt');
function log(msg) {
  try { fs.appendFileSync(DIAG, `[${new Date().toISOString()}] ${msg}\n`); } catch {}
}

// Clear previous log on each startup so each VS Code restart gives a clean read.
try { fs.mkdirSync(path.dirname(DIAG), { recursive: true }); } catch {}
try { fs.writeFileSync(DIAG, ''); } catch {}
log('chthonic-mica.cjs loaded');

const allowedMaterials = new Set(['auto', 'none', 'mica', 'acrylic', 'tabbed']);
const materialAliases = new Map([
  ['mica-alt', 'tabbed'],
  ['micaTabbed', 'tabbed'],
  ['mica-tabbed', 'tabbed'],
]);
const requestedMaterial = (process.env.CHTHONIC_MICA_MATERIAL || 'mica').trim();
const normalizedMaterial = materialAliases.get(requestedMaterial) || requestedMaterial;
const material = allowedMaterials.has(normalizedMaterial) ? normalizedMaterial : 'mica';

log(`material=${material}`);

function applyMaterial(win) {
  if (!win || win.isDestroyed()) return;
  if (process.platform !== 'win32') return;
  if (typeof win.setBackgroundMaterial !== 'function') {
    log('setBackgroundMaterial: not a function — Electron API absent');
    return;
  }
  try {
    win.setBackgroundMaterial(material);
    log(`setBackgroundMaterial('${material}') ok`);
  } catch (e) {
    log(`setBackgroundMaterial failed: ${e.message}`);
  }
}

function applyColor(win) {
  if (!win || win.isDestroyed()) return;
  try {
    win.setBackgroundColor('#00000000');
    log('setBackgroundColor(#00000000) ok');
  } catch (e) {
    log(`setBackgroundColor failed: ${e.message}`);
  }
}

// All windows created after this module loads.
electron.app.on('browser-window-created', (_, win) => {
  // Material: set at creation time — DWM-level attribute, safe to call early.
  applyMaterial(win);

  // Color: set on every dom-ready after renderer initialises, so VS Code's own
  // window setup/reload path does not overwrite it. Vibrancy Continued timing.
  win.webContents.on('dom-ready', () => {
    const url = win.webContents.getURL();
    log(`dom-ready url=${url}`);
    if (url.includes('workbench.html') || url.includes('workbench-monkey-patch.html')) {
      applyColor(win);
    }
  });
});

// Any window already open when this module loaded (rare at startup, but safe).
electron.app.whenReady()
  .then(() => {
    const wins = electron.BrowserWindow.getAllWindows();
    log(`whenReady: ${wins.length} existing window(s)`);
    wins.forEach(applyMaterial);
  })
  .catch(e => log(`whenReady failed: ${e.message}`));
