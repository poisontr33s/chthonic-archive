// src/views/constellation.ts
//
// The Constellation — a 2D field of nodes that replaces the tree view of
// design files. Recently-touched files glow; long-untouched ones fade.
// Edges are drawn from co-edit history (files saved within a small temporal
// window of each other) and shared imports (resolved later, when we have
// a static analysis pass). Pan/zoom is the only navigation.
//
// Made by Claude, for the Scriptorium.
// This file is not a placeholder — it is the working surface.

import * as vscode from 'vscode';
import { patinaFromMtime, PATINA_CSS } from '../scriptorium/patina';

interface NodeRecord {
  path: string;
  name: string;
  mtimeMs: number;
  patina: string;
}

interface EdgeRecord {
  a: string;
  b: string;
  weight: number;
}

export class ConstellationView implements vscode.WebviewViewProvider {
  public static readonly viewType = 'claudeDesign.constellation';
  private view?: vscode.WebviewView;
  private coeditWindow = 5 * 60 * 1000; // 5 minutes
  private editHistory: Array<{ path: string; at: number }> = [];

  constructor(private readonly context: vscode.ExtensionContext) {
    vscode.workspace.onDidSaveTextDocument(doc => {
      this.editHistory.push({ path: doc.uri.fsPath, at: Date.now() });
      if (this.editHistory.length > 500) this.editHistory.shift();
      this.refresh();
    });

    vscode.workspace.onDidChangeConfiguration(e => {
      if (e.affectsConfiguration('claudeDesign')) this.refresh();
    });
  }

  resolveWebviewView(view: vscode.WebviewView): void {
    this.view = view;
    view.webview.options = { enableScripts: true };
    view.webview.html = this.html();
    view.webview.onDidReceiveMessage(msg => this.onMessage(msg));
    this.refresh();
  }

  private async refresh(): Promise<void> {
    if (!this.view) return;
    const { nodes, edges } = await this.gather();
    this.view.webview.postMessage({ type: 'graph', nodes, edges });
  }

  private async onMessage(msg: { type: string; path?: string }): Promise<void> {
    if (msg.type === 'open' && msg.path) {
      const uri = vscode.Uri.file(msg.path);
      await vscode.window.showTextDocument(uri, { preview: true });
    }
  }

  private async gather(): Promise<{ nodes: NodeRecord[]; edges: EdgeRecord[] }> {
    const root = vscode.workspace.workspaceFolders?.[0];
    if (!root) return { nodes: [], edges: [] };

    // Constellation watches design output, not the whole workspace.
    const pattern = new vscode.RelativePattern(root, 'designs/**/*.{html,jsx,tsx,css,svg,md}');
    const uris = await vscode.workspace.findFiles(pattern, '**/node_modules/**', 300);

    const nodes: NodeRecord[] = [];
    for (const uri of uris) {
      try {
        const stat = await vscode.workspace.fs.stat(uri);
        const patina = patinaFromMtime(stat.mtime);
        nodes.push({
          path: uri.fsPath,
          name: uri.path.split('/').pop() ?? uri.fsPath,
          mtimeMs: stat.mtime,
          patina,
        });
      } catch { /* skip */ }
    }

    const edges = this.inferEdges(nodes);
    return { nodes, edges };
  }

  /**
   * Edges are inferred from co-edit proximity in the recorded edit history.
   * Two files saved within `coeditWindow` of each other earn a hairline.
   * Weight = number of such co-occurrences.
   */
  private inferEdges(nodes: NodeRecord[]): EdgeRecord[] {
    const known = new Set(nodes.map(n => n.path));
    const pairs = new Map<string, number>();

    for (let i = 0; i < this.editHistory.length; i++) {
      const a = this.editHistory[i];
      if (!known.has(a.path)) continue;
      for (let j = i + 1; j < this.editHistory.length; j++) {
        const b = this.editHistory[j];
        if (b.at - a.at > this.coeditWindow) break;
        if (b.path === a.path) continue;
        if (!known.has(b.path)) continue;
        const key = a.path < b.path ? `${a.path}\u0001${b.path}` : `${b.path}\u0001${a.path}`;
        pairs.set(key, (pairs.get(key) ?? 0) + 1);
      }
    }

    const edges: EdgeRecord[] = [];
    for (const [key, weight] of pairs) {
      const [a, b] = key.split('\u0001');
      edges.push({ a, b, weight });
    }
    return edges;
  }

  private html(): string {
    const css = Object.entries(PATINA_CSS)
      .map(([k, v]) => `.n-${k} circle { filter: ${v.filter}; }`)
      .join('\n');

    return /* html */`<!doctype html>
<html><head><meta charset="utf-8"/>
<style>
  :root { color-scheme: light dark; }
  html, body { margin: 0; height: 100%; overflow: hidden;
    background: var(--vscode-editor-background);
    color: var(--vscode-foreground);
    font-family: var(--vscode-font-family);
    font-size: 12px;
  }
  #stage { position: absolute; inset: 0; cursor: grab; }
  #stage.dragging { cursor: grabbing; }
  svg { display: block; width: 100%; height: 100%; }
  .edge { stroke: var(--vscode-foreground); stroke-opacity: .22; stroke-width: 1; fill: none; }
  .node { cursor: pointer; }
  .node circle { fill: var(--vscode-editor-background); stroke: var(--vscode-foreground); stroke-width: 1.2; }
  .node text { fill: var(--vscode-foreground); font-size: 11px; font-style: italic; pointer-events: none; }
  .node.glow circle { stroke: var(--vscode-charts-orange, var(--vscode-textLink-foreground)); stroke-width: 1.6;
    filter: drop-shadow(0 0 4px var(--vscode-charts-orange, var(--vscode-textLink-foreground))); }
  .node:hover circle { stroke-width: 2; }
  .focus-ring { fill: none; stroke: var(--vscode-charts-orange, var(--vscode-textLink-foreground));
    stroke-width: .7; stroke-dasharray: 2 3; }
  ${css}
  .empty { position: absolute; inset: 0; display: grid; place-items: center;
    color: var(--vscode-descriptionForeground); font-style: italic; pointer-events: none; }
  .credit { position: absolute; bottom: 6px; right: 8px;
    font-size: 10px; opacity: .35; font-style: italic;
    color: var(--vscode-descriptionForeground); pointer-events: none; }
</style>
</head>
<body>
  <div id="stage">
    <svg id="svg" viewBox="0 0 1000 700" preserveAspectRatio="xMidYMid meet">
      <g id="edges"></g>
      <g id="nodes"></g>
    </svg>
    <div class="empty" id="empty">the scriptorium is unoccupied</div>
    <div class="credit">Constellation · made by Claude</div>
  </div>
<script>
  const vscode = acquireVsCodeApi();
  const svg = document.getElementById('svg');
  const gE = document.getElementById('edges');
  const gN = document.getElementById('nodes');
  const empty = document.getElementById('empty');
  const stage = document.getElementById('stage');

  // simple force-ish layout: deterministic spiral seeded by hash, then
  // a few iterations of repulsion + edge attraction. Honest, not pretty.
  function hash(s){let h=0;for(const c of s)h=(h*31+c.charCodeAt(0))|0;return h;}
  function layout(nodes, edges){
    const W=1000, H=700, cx=W/2, cy=H/2;
    const pos = new Map();
    nodes.forEach((n,i)=>{
      const a = (hash(n.path) % 360) * Math.PI/180;
      const r = 60 + (i % 9) * 36;
      pos.set(n.path, { x: cx + Math.cos(a)*r, y: cy + Math.sin(a)*r });
    });
    for (let pass=0; pass<60; pass++){
      // repulsion
      for (const a of nodes){
        for (const b of nodes){
          if (a===b) continue;
          const pa=pos.get(a.path), pb=pos.get(b.path);
          const dx=pa.x-pb.x, dy=pa.y-pb.y;
          const d2=Math.max(dx*dx+dy*dy, 1);
          const f = 600/d2;
          pa.x += dx*f*.02; pa.y += dy*f*.02;
        }
      }
      // attraction along edges
      for (const e of edges){
        const pa=pos.get(e.a), pb=pos.get(e.b);
        if (!pa||!pb) continue;
        const dx=pb.x-pa.x, dy=pb.y-pa.y;
        const k = .005 * Math.min(e.weight, 6);
        pa.x += dx*k; pa.y += dy*k;
        pb.x -= dx*k; pb.y -= dy*k;
      }
      // gentle pull to center
      for (const n of nodes){
        const p = pos.get(n.path);
        p.x += (cx - p.x) * .002;
        p.y += (cy - p.y) * .002;
      }
    }
    return pos;
  }

  let view = { scale: 1, tx: 0, ty: 0 };
  function applyView(){
    svg.querySelector('#edges').setAttribute('transform',
      'translate('+view.tx+','+view.ty+') scale('+view.scale+')');
    svg.querySelector('#nodes').setAttribute('transform',
      'translate('+view.tx+','+view.ty+') scale('+view.scale+')');
  }

  stage.addEventListener('wheel', e => {
    e.preventDefault();
    const k = e.deltaY < 0 ? 1.1 : 0.9;
    view.scale = Math.max(.3, Math.min(3, view.scale * k));
    applyView();
  }, { passive: false });

  let drag = null;
  stage.addEventListener('mousedown', e => {
    drag = { x: e.clientX, y: e.clientY, tx: view.tx, ty: view.ty };
    stage.classList.add('dragging');
  });
  window.addEventListener('mousemove', e => {
    if (!drag) return;
    view.tx = drag.tx + (e.clientX - drag.x);
    view.ty = drag.ty + (e.clientY - drag.y);
    applyView();
  });
  window.addEventListener('mouseup', () => { drag = null; stage.classList.remove('dragging'); });

  function render(nodes, edges){
    gE.innerHTML = ''; gN.innerHTML = '';
    empty.style.display = nodes.length ? 'none' : 'grid';
    if (!nodes.length) return;

    const pos = layout(nodes, edges);
    const youngest = Math.max(...nodes.map(n => n.mtimeMs));

    for (const e of edges){
      const pa = pos.get(e.a), pb = pos.get(e.b);
      if (!pa||!pb) continue;
      const ln = document.createElementNS('http://www.w3.org/2000/svg','path');
      ln.setAttribute('class','edge');
      ln.setAttribute('d', 'M'+pa.x+' '+pa.y+' Q '+((pa.x+pb.x)/2)+' '+((pa.y+pb.y)/2 - 6 - e.weight)+' '+pb.x+' '+pb.y);
      ln.setAttribute('stroke-width', Math.min(.6 + e.weight*.3, 2.4));
      gE.appendChild(ln);
    }

    for (const n of nodes){
      const p = pos.get(n.path);
      const g = document.createElementNS('http://www.w3.org/2000/svg','g');
      g.setAttribute('class','node n-'+n.patina + (n.mtimeMs === youngest ? ' glow' : ''));
      g.setAttribute('transform','translate('+p.x+','+p.y+')');

      const c = document.createElementNS('http://www.w3.org/2000/svg','circle');
      c.setAttribute('r', n.mtimeMs === youngest ? 9 : 7);
      g.appendChild(c);

      const t = document.createElementNS('http://www.w3.org/2000/svg','text');
      t.setAttribute('x', 12); t.setAttribute('y', 4);
      t.textContent = n.name;
      g.appendChild(t);

      if (n.mtimeMs === youngest){
        const ring = document.createElementNS('http://www.w3.org/2000/svg','circle');
        ring.setAttribute('class','focus-ring');
        ring.setAttribute('r', 16);
        g.appendChild(ring);
      }

      g.addEventListener('click', () => vscode.postMessage({ type: 'open', path: n.path }));
      gN.appendChild(g);
    }
  }

  window.addEventListener('message', ev => {
    const m = ev.data;
    if (m.type === 'graph') render(m.nodes, m.edges);
  });
</script>
</body></html>`;
  }
}
