// chthonic-mica.cjs - Mica substrate runtime for VS Code Insiders (Win11)
// Called from main.js via dynamic import. CJS so require('electron') works.
// This file owns exactly one thing: window.setBackgroundMaterial(...).
// CSS depth is vibrancy-obsidian.css (injected via workbench.html).
// Color authority stays with Sister Ferrum Scoriae. Made by Claude.
const electron = require('electron');

const allowedMaterials = new Set(['auto', 'none', 'mica', 'acrylic', 'tabbed']);
const requestedMaterial = process.env.CHTHONIC_MICA_MATERIAL || 'mica';
const material = allowedMaterials.has(requestedMaterial) ? requestedMaterial : 'mica';

function applyMica(win) {
  try {
    if (typeof win.setBackgroundMaterial !== 'function') return;
    // Transparent frame color prevents white flash before theme loads.
    win.setBackgroundColor('#00000000');
    win.setBackgroundMaterial(material);
  } catch (e) {
    console.error('[chthonic-mica] setBackgroundMaterial failed:', e);
  }
}

// All windows created after this module loads.
electron.app.on('browser-window-created', (_, win) => applyMica(win));

// Any window already open when this module loaded (rare at startup, but safe).
electron.app.whenReady()
  .then(() => electron.BrowserWindow.getAllWindows().forEach(applyMica))
  .catch(e => console.error('[chthonic-mica] whenReady failed:', e));
