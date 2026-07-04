// src/extension.ts
import * as vscode15 from "vscode";

// src/inference/cli.ts
import { spawn } from "node:child_process";
import { EventEmitter } from "node:events";

class CliInference extends EventEmitter {
  cliPath;
  child = null;
  constructor(cliPath = "claude") {
    super();
    this.cliPath = cliPath;
  }
  send(prompt, opts = {}) {
    if (this.child)
      this.child.kill();
    this.child = spawn(this.cliPath, ["--print", "--output-format", "stream-json", "--include-partial-messages", prompt], { cwd: opts.cwd, shell: false, windowsHide: true, stdio: ["ignore", "pipe", "pipe"] });
    let buf = "";
    this.child.stdout?.on("data", (chunk) => {
      buf += chunk.toString();
      let nl;
      while ((nl = buf.indexOf(`
`)) !== -1) {
        const line = buf.slice(0, nl).trim();
        buf = buf.slice(nl + 1);
        if (!line)
          continue;
        try {
          const evt = JSON.parse(line);
          this.emit("event", evt);
        } catch {}
      }
    });
    this.child.stderr?.on("data", (d) => this.emit("event", { type: "error", data: d.toString() }));
    this.child.on("close", (code) => this.emit("event", { type: "done", data: { code } }));
  }
  dispose() {
    this.child?.kill();
    this.child = null;
  }
}
function streamEventText(e) {
  if (e.type === "message") {
    return textFromUnknown(e.data?.delta ?? e.data?.text ?? e.data);
  }
  if (e.type === "content_block_delta") {
    return textFromUnknown(e.delta?.text ?? e.data?.delta?.text);
  }
  if (e.type === "assistant") {
    const message = e.message ?? e.data?.message ?? e.data;
    return textFromContent(message?.content ?? message);
  }
  if (e.type === "partial_message") {
    const message = e.message ?? e.data?.message ?? e.data;
    return textFromContent(message?.content ?? message);
  }
  return "";
}
function streamEventError(e) {
  if (e.type === "error")
    return textFromUnknown(e.data ?? e.error ?? e.message) || "stream error";
  if (e.type === "result" && (e.is_error || e.subtype === "error")) {
    return textFromUnknown(e.result ?? e.data ?? e.error) || "Claude CLI result error";
  }
  return null;
}
function streamEventDone(e) {
  return e.type === "done" || e.type === "result" || e.type === "message_stop";
}
function textFromContent(value) {
  if (Array.isArray(value)) {
    return value.map((item) => textFromUnknown(item?.text ?? item?.content)).filter(Boolean).join("");
  }
  return textFromUnknown(value);
}
function textFromUnknown(value) {
  if (typeof value === "string")
    return value;
  if (value && typeof value === "object") {
    const obj = value;
    return textFromUnknown(obj.text ?? obj.delta ?? obj.content);
  }
  return "";
}

// src/fs/broker.ts
import * as vscode from "vscode";
import * as path from "node:path";
var ALLOWED_PREFIXES = ["designs/", "assets/", ".claude-design/"];

class FsBroker {
  ctx;
  locks = new Map;
  _onDidWrite = new vscode.EventEmitter;
  onDidWrite = this._onDidWrite.event;
  constructor(ctx) {
    this.ctx = ctx;
    ctx.subscriptions.push(this._onDidWrite);
  }
  async write(relPath, content) {
    const root = vscode.workspace.workspaceFolders?.[0];
    if (!root)
      throw new Error("No workspace open");
    const normalized = relPath.replace(/\\/g, "/").replace(/^\.\//, "");
    const allowed = ALLOWED_PREFIXES.some((p) => normalized.startsWith(p));
    if (!allowed) {
      const ok = await vscode.window.showWarningMessage(`Claude wants to write outside the design sandbox: ${normalized}`, { modal: true }, "Allow once", "Block");
      if (ok !== "Allow once")
        throw new Error("Write blocked by user");
    }
    const uri = vscode.Uri.joinPath(root.uri, normalized);
    const now = Date.now();
    const last = this.locks.get(uri.fsPath) ?? 0;
    if (now - last < 200)
      await new Promise((r) => setTimeout(r, 200 - (now - last)));
    this.locks.set(uri.fsPath, Date.now());
    const dir = vscode.Uri.joinPath(uri, "..");
    try {
      await vscode.workspace.fs.createDirectory(dir);
    } catch {}
    const bytes = typeof content === "string" ? new TextEncoder().encode(content) : content;
    await vscode.workspace.fs.writeFile(uri, bytes);
    this._onDidWrite.fire({
      path: normalized,
      bytes: bytes.byteLength,
      at: Date.now()
    });
    return uri;
  }
  async readManifest() {
    const root = vscode.workspace.workspaceFolders?.[0];
    if (!root)
      return { items: [] };
    const uri = vscode.Uri.joinPath(root.uri, ".claude-design", "manifest.json");
    try {
      const raw = await vscode.workspace.fs.readFile(uri);
      return JSON.parse(new TextDecoder().decode(raw));
    } catch {
      return { items: [] };
    }
  }
  workspaceRoot() {
    return vscode.workspace.workspaceFolders?.[0]?.uri ?? null;
  }
  relativize(uri) {
    const root = this.workspaceRoot();
    if (!root)
      return uri.fsPath;
    return path.relative(root.fsPath, uri.fsPath).replace(/\\/g, "/");
  }
}

// src/scriptorium/marginalia.ts
import * as vscode2 from "vscode";
import * as path2 from "path";
var MARGINALIA_DIR = ".scriptorium/marginalia";
var SIGIL = { rubric: "❦", gloss: "¶", colophon: "⌘" };
function leafToMarginaliaPath(leafPath) {
  return path2.posix.join(MARGINALIA_DIR, leafPath + ".md");
}
function marginaliaToLeafPath(marginaliaPath) {
  const rel = path2.posix.relative(MARGINALIA_DIR, marginaliaPath);
  return rel.replace(/\.md$/, "");
}

class MarginaliaStore {
  workspaceRoot;
  constructor(workspaceRoot) {
    this.workspaceRoot = workspaceRoot;
  }
  uri(relativePath) {
    return vscode2.Uri.joinPath(this.workspaceRoot, relativePath);
  }
  async load(leafPath) {
    const marginaliaPath = leafToMarginaliaPath(leafPath);
    const uri = this.uri(marginaliaPath);
    let raw = "";
    try {
      const bytes = await vscode2.workspace.fs.readFile(uri);
      raw = new TextDecoder().decode(bytes);
    } catch {}
    return { path: leafPath, marginaliaPath, entries: parseMarginalia(raw) };
  }
  async append(leafPath, entry) {
    const marginaliaPath = leafToMarginaliaPath(leafPath);
    const uri = this.uri(marginaliaPath);
    try {
      await vscode2.workspace.fs.createDirectory(vscode2.Uri.joinPath(uri, ".."));
    } catch {}
    const leaf = await this.load(leafPath);
    leaf.entries.push(entry);
    const serialized = serializeMarginalia(leaf.entries);
    await vscode2.workspace.fs.writeFile(uri, new TextEncoder().encode(serialized));
  }
  async list() {
    const root = this.uri(MARGINALIA_DIR);
    const out = [];
    const walk = async (dir, prefix) => {
      let entries;
      try {
        entries = await vscode2.workspace.fs.readDirectory(dir);
      } catch {
        return;
      }
      for (const [name, kind] of entries) {
        const next = prefix ? `${prefix}/${name}` : name;
        if (kind === vscode2.FileType.Directory) {
          await walk(vscode2.Uri.joinPath(dir, name), next);
        } else if (kind === vscode2.FileType.File && name.endsWith(".md")) {
          out.push(marginaliaToLeafPath(path2.posix.join(MARGINALIA_DIR, next)));
        }
      }
    };
    await walk(root, "");
    return out;
  }
}
function serializeMarginalia(entries) {
  const head = `# Marginalia

`;
  return head + entries.map(serializeEntry).join(`
`);
}
function serializeEntry(e) {
  const header = `## ${SIGIL[e.kind]} ${e.kind} · ${e.timestamp.toISOString()} · ${e.hand}

`;
  if (e.kind === "colophon" && e.colophon) {
    return header + `— ${e.colophon.path} · ${e.colophon.bytes} bytes · ${e.colophon.sig}
`;
  }
  return header + e.text.trim() + `
`;
}
var ENTRY_RE = /^## (?:❦|¶|⌘)\s+(rubric|gloss|colophon)\s+·\s+(\S+)\s+·\s+(master|scribe|system)\s*$/;
var COLOPHON_RE = /^—\s+(\S+)\s+·\s+(\d+)\s+bytes\s+·\s+(.+)$/;
function parseMarginalia(raw) {
  if (!raw.trim())
    return [];
  const lines = raw.split(/\r?\n/);
  const entries = [];
  let current = null;
  let buffer = [];
  const flush = () => {
    if (!current || !current.kind || !current.hand || !current.timestamp)
      return;
    const text = buffer.join(`
`).trim();
    let colophon;
    if (current.kind === "colophon") {
      const m = text.match(COLOPHON_RE);
      if (m)
        colophon = { path: m[1], bytes: parseInt(m[2], 10), sig: m[3].trim() };
    }
    entries.push({
      kind: current.kind,
      hand: current.hand,
      timestamp: current.timestamp,
      text,
      colophon
    });
    current = null;
    buffer = [];
  };
  for (const line of lines) {
    const m = line.match(ENTRY_RE);
    if (m) {
      flush();
      current = {
        kind: m[1],
        timestamp: new Date(m[2]),
        hand: m[3]
      };
      buffer = [];
    } else if (current) {
      buffer.push(line);
    }
  }
  flush();
  return entries;
}

// src/scriptorium/colophon.ts
class ColophonScribe {
  store;
  constructor(store) {
    this.store = store;
  }
  async stamp(rec) {
    const ts = new Date().toISOString();
    const lines = [];
    lines.push("");
    lines.push("† colophon");
    lines.push(`  · written: ${rec.leaf}`);
    lines.push(`  · bytes:   ${rec.bytes}`);
    if (rec.hand)
      lines.push(`  · hand:    ${rec.hand}`);
    if (rec.causedBy) {
      const trimmed = rec.causedBy.length > 120 ? rec.causedBy.slice(0, 117) + "…" : rec.causedBy;
      lines.push(`  · caused:  ${trimmed}`);
    }
    lines.push(`  · stamp:   ${ts}`);
    lines.push("");
    await this.store.appendRaw(rec.leaf, lines.join(`
`));
  }
}

// src/scriptorium/focus.ts
import * as vscode3 from "vscode";

class FocusBridge {
  _onDidFocus = new vscode3.EventEmitter;
  onDidFocus = this._onDidFocus.event;
  async focus(leaf) {
    const folders = vscode3.workspace.workspaceFolders;
    if (!folders?.length)
      return;
    const uri = vscode3.Uri.joinPath(folders[0].uri, leaf);
    try {
      const doc = await vscode3.workspace.openTextDocument(uri);
      await vscode3.window.showTextDocument(doc, { preview: false });
    } catch {}
    await vscode3.commands.executeCommand("claudeDesign.marginalia.focus", leaf);
    this._onDidFocus.fire(leaf);
  }
}
var focusBridge = new FocusBridge;
function registerFocusBridge(context) {
  context.subscriptions.push(vscode3.commands.registerCommand("claudeDesign.focusLeaf", (leaf) => focusBridge.focus(leaf)));
}

// src/scriptorium/rune.ts
import * as vscode4 from "vscode";
var DEFAULT_RUNE = "\uD83D\uDF02";
var TILT_FRAMES = ["", "̀", "́", "̀"];

class Rune {
  item;
  timer;
  frame = 0;
  attention = false;
  glyph;
  constructor() {
    this.item = vscode4.window.createStatusBarItem(vscode4.StatusBarAlignment.Right, 100);
    this.item.command = "claudeDesign.runeAction";
    this.glyph = this.readGlyph();
    this.render();
    this.item.show();
    vscode4.workspace.onDidChangeConfiguration((e) => {
      if (e.affectsConfiguration("claudeDesign.rune")) {
        this.glyph = this.readGlyph();
        this.render();
      }
    });
  }
  readGlyph() {
    return vscode4.workspace.getConfiguration("claudeDesign").get("rune", DEFAULT_RUNE);
  }
  rest() {
    this.attention = false;
    this.stopTilt();
    this.frame = 0;
    this.render();
  }
  call(reason) {
    this.attention = true;
    if (reason)
      this.item.tooltip = reason;
    this.startTilt();
  }
  block(reason) {
    this.attention = true;
    this.item.tooltip = reason;
    this.item.backgroundColor = new vscode4.ThemeColor("statusBarItem.warningBackground");
    this.startTilt();
  }
  setTooltip(s) {
    this.item.tooltip = s;
  }
  setLabel(s) {
    this.label = s;
    this.render();
  }
  label;
  render() {
    const tilt = this.attention ? TILT_FRAMES[this.frame % TILT_FRAMES.length] : "";
    const g = this.glyph + tilt;
    this.item.text = this.label ? `${g}  ${this.label}` : g;
  }
  startTilt() {
    if (this.timer)
      return;
    this.timer = setInterval(() => {
      this.frame = (this.frame + 1) % TILT_FRAMES.length;
      this.render();
    }, 1400);
  }
  stopTilt() {
    if (!this.timer)
      return;
    clearInterval(this.timer);
    this.timer = undefined;
    this.item.backgroundColor = undefined;
  }
  dispose() {
    this.stopTilt();
    this.item.dispose();
  }
}

// src/scriptorium/session.ts
import * as vscode5 from "vscode";
var SESSION_DIR = ".scriptorium";
var SESSION_FILE = "session.md";
function sessionUri() {
  const root = vscode5.workspace.workspaceFolders?.[0];
  if (!root)
    return;
  return vscode5.Uri.joinPath(root.uri, SESSION_DIR, SESSION_FILE);
}
async function hibernate(snap) {
  const uri = sessionUri();
  if (!uri)
    return;
  const dir = vscode5.Uri.joinPath(uri, "..");
  try {
    await vscode5.workspace.fs.createDirectory(dir);
  } catch {}
  const lines = [];
  lines.push("# .scriptorium/session.md");
  lines.push("");
  lines.push("## Last touched");
  if (snap.lastTouched.file)
    lines.push(`- file:   ${snap.lastTouched.file}`);
  if (snap.lastTouched.line != null)
    lines.push(`- line:   ${snap.lastTouched.line}`);
  lines.push(`- when:   ${snap.lastTouched.when}`);
  lines.push("");
  if (snap.draftMessage) {
    lines.push("## Draft message");
    for (const l of snap.draftMessage.split(`
`))
      lines.push(`> ${l}`);
    lines.push("");
  }
  lines.push("## Open vivaria");
  for (const f of snap.openVivaria)
    lines.push(`- ${f}`);
  lines.push("");
  if (snap.conversationTail) {
    lines.push("## Conversation tail");
    lines.push("");
    lines.push(snap.conversationTail);
    lines.push("");
  }
  await vscode5.workspace.fs.writeFile(uri, new TextEncoder().encode(lines.join(`
`)));
}
async function rehydrate() {
  const uri = sessionUri();
  if (!uri)
    return;
  let raw;
  try {
    const bytes = await vscode5.workspace.fs.readFile(uri);
    raw = new TextDecoder().decode(bytes);
  } catch {
    return;
  }
  const snap = {
    lastTouched: { when: "" },
    openVivaria: []
  };
  const sections = raw.split(/^##\s+/m).slice(1);
  for (const sec of sections) {
    const [title, ...rest] = sec.split(`
`);
    const body = rest.join(`
`);
    if (/last touched/i.test(title)) {
      for (const m of body.matchAll(/^- (\w+):\s*(.+)$/gm)) {
        const k = m[1], v = m[2].trim();
        if (k === "file")
          snap.lastTouched.file = v;
        else if (k === "line")
          snap.lastTouched.line = Number(v);
        else if (k === "when")
          snap.lastTouched.when = v;
      }
    } else if (/draft message/i.test(title)) {
      const draft = body.replace(/^>\s?/gm, "").trim();
      if (draft)
        snap.draftMessage = draft;
    } else if (/open vivaria/i.test(title)) {
      for (const m of body.matchAll(/^- (.+)$/gm))
        snap.openVivaria.push(m[1].trim());
    } else if (/conversation tail/i.test(title)) {
      snap.conversationTail = body.trim();
    }
  }
  return snap;
}

// src/scriptorium/bestiary.ts
import * as vscode6 from "vscode";
var BESTIARY = [
  {
    sigil: "⌬",
    name: "The Quota Spectrometer",
    latin: "Metrum designi separatum",
    sighting: "rumored",
    description: "Reportedly meters Claude Design usage independently of chat and Claude Code allowances. " + "Its API surface has not been sighted. Until it is, the rune in the status bar shows a soft pulse rather than a percentage."
  },
  {
    sigil: "↺",
    name: "The Lossless Teleport",
    latin: "Migratio sessionis",
    sighting: "never",
    description: "A surface that would carry a server-side claude.ai session into a local editor without loss of artifact or thread. " + "The Scriptorium imports dropped export files in the interim."
  },
  {
    sigil: "⚯",
    name: "The Claude Code Exports",
    latin: "Interfacium ad alter extensio",
    sighting: "partial",
    description: "The companion extension may, in some versions, expose a public API on its activate() return. " + "When present, the Scriptorium routes inference through it instead of a subprocess."
  },
  {
    sigil: "☖",
    name: "The Editable Workspace Provider",
    latin: "Fons sancti scripti",
    sighting: "documented",
    description: "VS Code's FileSystemProvider API, used to mount design-system folders read-only via canvas-ds:// scheme. " + "Verified present in 1.97+."
  },
  {
    sigil: "☷",
    name: "The Webview Theme Bridge",
    latin: "Varietates colorum",
    sighting: "documented",
    description: "The --vscode-* CSS variables injected into every webview. The Scriptorium's chrome reads these directly; " + "theme switches at the editor level recolor the extension in place."
  }
];
function bestiaryAsMarkdown(creatures) {
  const lines = [];
  lines.push("# Scriptorium Bestiary");
  lines.push("");
  lines.push("*Probe report. Each entry is a surface the extension cooperates with or hopes to.*");
  lines.push("");
  for (const c of creatures) {
    lines.push(`## ${c.sigil}  ${c.name}`);
    lines.push(`*${c.latin}*`);
    lines.push("");
    lines.push(`**Sighting:** ${sightingLabel(c.sighting)}`);
    lines.push("");
    lines.push(c.description);
    lines.push("");
    lines.push("---");
    lines.push("");
  }
  lines.push(`*${creatures.length} entries. Bestiary updates as surfaces ship.*`);
  return lines.join(`
`);
}
function sightingLabel(s) {
  switch (s) {
    case "documented":
      return "documented · in active use";
    case "partial":
      return "partially documented";
    case "rumored":
      return "rumored · awaiting public surface";
    case "never":
      return "never observed in the wild";
  }
}

class BestiaryProvider {
  ctx;
  _onDidChange = new vscode6.EventEmitter;
  onDidChangeTreeData = this._onDidChange.event;
  constructor(ctx) {
    this.ctx = ctx;
    ctx.subscriptions.push(vscode6.commands.registerCommand("claudeDesign.openBestiary", async () => {
      const doc = await vscode6.workspace.openTextDocument({
        language: "markdown",
        content: bestiaryAsMarkdown(BESTIARY)
      });
      await vscode6.window.showTextDocument(doc, { preview: false });
    }));
  }
  refresh() {
    this._onDidChange.fire();
  }
  getTreeItem(c) {
    const item = new vscode6.TreeItem(`${c.sigil}  ${c.name}`, vscode6.TreeItemCollapsibleState.None);
    item.description = sightingLabel(c.sighting);
    item.tooltip = c.description;
    item.iconPath = new vscode6.ThemeIcon(c.sighting === "documented" ? "pass" : c.sighting === "partial" ? "circle-large-outline" : c.sighting === "rumored" ? "question" : "circle-slash");
    item.command = { command: "claudeDesign.openBestiary", title: "Open Bestiary" };
    return item;
  }
  getChildren() {
    return BESTIARY;
  }
}

// src/scriptorium/manifest.ts
import * as vscode7 from "vscode";
var MANIFEST_FILENAME = "designs.md";
function manifestUri() {
  const root = vscode7.workspace.workspaceFolders?.[0];
  if (!root)
    return;
  return vscode7.Uri.joinPath(root.uri, MANIFEST_FILENAME);
}
async function ensureManifest() {
  const uri = manifestUri();
  if (!uri)
    return;
  try {
    await vscode7.workspace.fs.stat(uri);
  } catch {
    const seed = [
      "# designs.md",
      "",
      "The asset ledger for this workspace.",
      "Human and machine read this same file.",
      "",
      "## Pages",
      "",
      "## Components",
      ""
    ].join(`
`);
    await vscode7.workspace.fs.writeFile(uri, new TextEncoder().encode(seed));
  }
  return uri;
}
function watchManifest(onChange) {
  const root = vscode7.workspace.workspaceFolders?.[0];
  if (!root)
    return new vscode7.Disposable(() => {});
  const watcher = vscode7.workspace.createFileSystemWatcher(new vscode7.RelativePattern(root, MANIFEST_FILENAME));
  watcher.onDidChange(onChange);
  watcher.onDidCreate(onChange);
  watcher.onDidDelete(onChange);
  return watcher;
}

// src/scriptorium/substrate.ts
import * as fs from "node:fs";
import * as path3 from "node:path";
import { pathToFileURL } from "node:url";
import * as vscode8 from "vscode";
var MAIN_BEGIN = "/* claudeDesign.substrate.main.begin */";
var MAIN_END = "/* claudeDesign.substrate.main.end */";
var CSS_BEGIN = "<!-- claudeDesign.substrate.css.begin -->";
var CSS_END = "<!-- claudeDesign.substrate.css.end -->";
var CSS_FILENAME = "vibrancy-obsidian.css";
async function enableSubstrate(context) {
  const cssPath = resolveCssPath(context);
  if (!cssPath) {
    console.warn(`Claude Design substrate: ${CSS_FILENAME} not found; skipping install patch.`);
    return;
  }
  const install = locateInstall();
  let changed = false;
  changed = patchMainJs(install.mainJs) || changed;
  changed = patchWorkbenchHtml(install.workbenchHtml, cssPath) || changed;
  return { changed, cssPath, ...install };
}
async function disableSubstrate() {
  const install = locateInstall();
  let changed = false;
  changed = stripMainJs(install.mainJs) || changed;
  changed = stripWorkbenchHtml(install.workbenchHtml) || changed;
  return { changed, ...install };
}
function resolveCssPath(context) {
  const configured = vscode8.workspace.getConfiguration("claudeDesign").get("substrateCssPath", "").trim();
  const candidates = [
    configured,
    ...(vscode8.workspace.workspaceFolders ?? []).map((folder) => path3.join(folder.uri.fsPath, "designs", CSS_FILENAME)),
    path3.join(context.extensionPath, "media", CSS_FILENAME)
  ].filter(Boolean);
  return candidates.find((candidate) => path3.isAbsolute(candidate) && isFile(candidate));
}
function locateInstall() {
  const appRoot = findAppRoot(process.execPath);
  const mainJs = path3.join(appRoot, "out", "main.js");
  if (!isFile(mainJs)) {
    throw new Error(`VS Code main.js not found under ${appRoot}`);
  }
  const workbenchHtml = findWorkbenchHtml(appRoot);
  return { appRoot, mainJs, workbenchHtml };
}
function findAppRoot(execPath) {
  const start = isFile(execPath) ? path3.dirname(execPath) : execPath;
  const seen = new Set;
  for (let dir = start;; dir = path3.dirname(dir)) {
    for (const candidate of appRootCandidates(dir)) {
      const normalized = path3.normalize(candidate);
      if (seen.has(normalized))
        continue;
      seen.add(normalized);
      if (isDirectory(normalized) && isFile(path3.join(normalized, "out", "main.js"))) {
        return normalized;
      }
    }
    const parent = path3.dirname(dir);
    if (parent === dir)
      break;
  }
  throw new Error(`Could not locate VS Code resources/app from ${execPath}`);
}
function appRootCandidates(dir) {
  const direct = path3.join(dir, "resources", "app");
  const candidates = [direct];
  try {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      if (entry.isDirectory()) {
        candidates.push(path3.join(dir, entry.name, "resources", "app"));
      }
    }
  } catch {}
  return candidates;
}
function findWorkbenchHtml(appRoot) {
  const candidates = [
    path3.join(appRoot, "out", "vs", "code", "electron-sandbox", "workbench", "workbench.esm.html"),
    path3.join(appRoot, "out", "vs", "code", "electron-sandbox", "workbench", "workbench.html"),
    path3.join(appRoot, "out", "vs", "code", "electron-browser", "workbench", "workbench.esm.html"),
    path3.join(appRoot, "out", "vs", "code", "electron-browser", "workbench", "workbench.html")
  ];
  const known = candidates.find(isFile);
  if (known)
    return known;
  const fallbackRoot = path3.join(appRoot, "out", "vs", "code");
  const found = findFirst(fallbackRoot, (file) => /^workbench.*\.html$/i.test(path3.basename(file)));
  if (found)
    return found;
  throw new Error(`VS Code workbench HTML not found under ${appRoot}`);
}
function patchMainJs(mainJs) {
  const original = fs.readFileSync(mainJs, "utf8");
  const stripped = stripMainMarkers(original);
  const markerBlock = `${MAIN_BEGIN},(()=>{try{const browserWindow=this._win;browserWindow.setBackgroundMaterial?.("mica")}catch{}})()${MAIN_END}`;
  const exactNeedle = "this._win=new vn.BrowserWindow(Je)";
  let patched;
  if (stripped.includes(exactNeedle)) {
    patched = stripped.replace(exactNeedle, `${exactNeedle}${markerBlock}`);
  } else {
    patched = stripped.replace(/(this\._win=new [A-Za-z_$][\w$]*\.BrowserWindow\([^)]*\))/, `$1${markerBlock}`);
  }
  if (patched === stripped || !patched.includes(MAIN_BEGIN)) {
    throw new Error(`Could not patch BrowserWindow creation in ${mainJs}`);
  }
  if (patched === original)
    return false;
  fs.writeFileSync(mainJs, patched, "utf8");
  return true;
}
function stripMainJs(mainJs) {
  const original = fs.readFileSync(mainJs, "utf8");
  const stripped = stripMainMarkers(original);
  if (stripped === original)
    return false;
  fs.writeFileSync(mainJs, stripped, "utf8");
  return true;
}
function patchWorkbenchHtml(workbenchHtml, cssPath) {
  const original = fs.readFileSync(workbenchHtml, "utf8");
  let patched = stripCssMarkers(original);
  patched = ensureStyleSrcFile(patched);
  const cssHref = escapeHtml(pathToFileURL(cssPath).href);
  const block = [
    "",
    `		${CSS_BEGIN}`,
    `		<link rel="stylesheet" data-claude-design-substrate="vibrancy-obsidian" href="${cssHref}">`,
    `		${CSS_END}`
  ].join(`
`);
  patched = patched.replace(/\n\s*<\/head>/i, `${block}
	</head>`);
  if (patched === original)
    return false;
  if (!patched.includes(CSS_BEGIN)) {
    throw new Error(`Could not inject substrate CSS into ${workbenchHtml}`);
  }
  fs.writeFileSync(workbenchHtml, patched, "utf8");
  return true;
}
function stripWorkbenchHtml(workbenchHtml) {
  const original = fs.readFileSync(workbenchHtml, "utf8");
  let stripped = stripCssMarkers(original);
  stripped = removeStyleSrcFile(stripped);
  if (stripped === original)
    return false;
  fs.writeFileSync(workbenchHtml, stripped, "utf8");
  return true;
}
function stripMainMarkers(value) {
  return value.replace(new RegExp(escapeRegExp(MAIN_BEGIN) + "[\\s\\S]*?" + escapeRegExp(MAIN_END), "g"), "");
}
function stripCssMarkers(value) {
  return value.replace(new RegExp("\\n?\\s*" + escapeRegExp(CSS_BEGIN) + "[\\s\\S]*?" + escapeRegExp(CSS_END), "g"), "");
}
function ensureStyleSrcFile(value) {
  return value.replace(/(style-src[\s\S]*?)(\s*;)/i, (match, body, end) => {
    if (/\bfile:/.test(body))
      return match;
    return `${body}
					file:${end}`;
  });
}
function removeStyleSrcFile(value) {
  return value.replace(/(style-src[\s\S]*?)(\s*;)/i, (match, body, end) => {
    return `${body.replace(/\s*file:/g, "")}${end}`;
  });
}
function findFirst(root, predicate) {
  const stack = [root];
  while (stack.length) {
    const current = stack.pop();
    let entries;
    try {
      entries = fs.readdirSync(current, { withFileTypes: true });
    } catch {
      continue;
    }
    for (const entry of entries) {
      const next = path3.join(current, entry.name);
      if (entry.isDirectory())
        stack.push(next);
      else if (entry.isFile() && predicate(next))
        return next;
    }
  }
  return;
}
function isFile(candidate) {
  try {
    return fs.statSync(candidate).isFile();
  } catch {
    return false;
  }
}
function isDirectory(candidate) {
  try {
    return fs.statSync(candidate).isDirectory();
  } catch {
    return false;
  }
}
function escapeHtml(value) {
  return value.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;");
}
function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

// src/views/constellation.ts
import * as vscode9 from "vscode";

// src/scriptorium/patina.ts
var DAY = 24 * 60 * 60 * 1000;
function patinaFromMtime(mtimeMs, now = Date.now()) {
  const age = now - mtimeMs;
  if (age < 1 * DAY)
    return "fresh";
  if (age < 3 * DAY)
    return "recent";
  if (age < 14 * DAY)
    return "week";
  if (age < 60 * DAY)
    return "month";
  if (age < 240 * DAY)
    return "season";
  return "archive";
}
var PATINA_CSS = {
  fresh: { filter: "none", label: "fresh" },
  recent: { filter: "none", label: "recent" },
  week: { filter: "contrast(.94) brightness(1.02)", label: "a week" },
  month: { filter: "contrast(.88) brightness(1.04) blur(.2px)", label: "a month" },
  season: { filter: "contrast(.80) brightness(1.06) blur(.4px)", label: "a season" },
  archive: { filter: "contrast(.72) brightness(1.08) blur(.6px)", label: "archived by time" }
};

// src/views/constellation.ts
class ConstellationView {
  context;
  static viewType = "claudeDesign.constellation";
  view;
  coeditWindow = 5 * 60 * 1000;
  editHistory = [];
  constructor(context) {
    this.context = context;
    vscode9.workspace.onDidSaveTextDocument((doc) => {
      this.editHistory.push({ path: doc.uri.fsPath, at: Date.now() });
      if (this.editHistory.length > 500)
        this.editHistory.shift();
      this.refresh();
    });
    vscode9.workspace.onDidChangeConfiguration((e) => {
      if (e.affectsConfiguration("claudeDesign"))
        this.refresh();
    });
  }
  resolveWebviewView(view) {
    this.view = view;
    view.webview.options = { enableScripts: true };
    view.webview.html = this.html();
    view.webview.onDidReceiveMessage((msg) => this.onMessage(msg));
    this.refresh();
  }
  async refresh() {
    if (!this.view)
      return;
    const { nodes, edges } = await this.gather();
    this.view.webview.postMessage({ type: "graph", nodes, edges });
  }
  async onMessage(msg) {
    if (msg.type === "open" && msg.path) {
      const uri = vscode9.Uri.file(msg.path);
      await vscode9.window.showTextDocument(uri, { preview: true });
    }
  }
  async gather() {
    const root = vscode9.workspace.workspaceFolders?.[0];
    if (!root)
      return { nodes: [], edges: [] };
    const pattern = new vscode9.RelativePattern(root, "designs/**/*.{html,jsx,tsx,css,svg,md}");
    const uris = await vscode9.workspace.findFiles(pattern, "**/node_modules/**", 300);
    const nodes = [];
    for (const uri of uris) {
      try {
        const stat = await vscode9.workspace.fs.stat(uri);
        const patina = patinaFromMtime(stat.mtime);
        nodes.push({
          path: uri.fsPath,
          name: uri.path.split("/").pop() ?? uri.fsPath,
          mtimeMs: stat.mtime,
          patina
        });
      } catch {}
    }
    const edges = this.inferEdges(nodes);
    return { nodes, edges };
  }
  inferEdges(nodes) {
    const known = new Set(nodes.map((n) => n.path));
    const pairs = new Map;
    for (let i = 0;i < this.editHistory.length; i++) {
      const a = this.editHistory[i];
      if (!known.has(a.path))
        continue;
      for (let j = i + 1;j < this.editHistory.length; j++) {
        const b = this.editHistory[j];
        if (b.at - a.at > this.coeditWindow)
          break;
        if (b.path === a.path)
          continue;
        if (!known.has(b.path))
          continue;
        const key = a.path < b.path ? `${a.path}\x01${b.path}` : `${b.path}\x01${a.path}`;
        pairs.set(key, (pairs.get(key) ?? 0) + 1);
      }
    }
    const edges = [];
    for (const [key, weight] of pairs) {
      const [a, b] = key.split("\x01");
      edges.push({ a, b, weight });
    }
    return edges;
  }
  html() {
    const css = Object.entries(PATINA_CSS).map(([k, v]) => `.n-${k} circle { filter: ${v.filter}; }`).join(`
`);
    return `<!doctype html>
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

// src/views/marginaliaView.ts
import * as vscode11 from "vscode";

// src/scriptorium/workspacePath.ts
import * as path4 from "node:path";
import * as vscode10 from "vscode";
function workspaceRelativePath(uri) {
  const folder = vscode10.workspace.getWorkspaceFolder(uri);
  if (!folder)
    return;
  const rel = path4.relative(folder.uri.fsPath, uri.fsPath).replace(/\\/g, "/");
  if (!rel || rel.startsWith("..") || path4.isAbsolute(rel))
    return;
  return { folder, path: rel };
}
function designLeafPath(uri, pattern) {
  const rel = workspaceRelativePath(uri);
  if (!rel || !rel.path.startsWith("designs/"))
    return;
  if (pattern && !pattern.test(rel.path))
    return;
  return rel;
}
function designResourceRoots() {
  const roots = [];
  for (const folder of vscode10.workspace.workspaceFolders ?? []) {
    roots.push(vscode10.Uri.joinPath(folder.uri, "designs"));
    roots.push(vscode10.Uri.joinPath(folder.uri, "assets"));
  }
  return roots;
}

// src/views/marginaliaView.ts
class MarginaliaView {
  context;
  store;
  inference;
  static viewType = "claudeDesign.marginalia";
  view;
  activeLeaf;
  hand = "terse";
  selectionExcerpt;
  constructor(context, store, inference) {
    this.context = context;
    this.store = store;
    this.inference = inference;
    vscode11.window.onDidChangeActiveTextEditor((e) => this.onEditorChanged(e), null, context.subscriptions);
    vscode11.window.onDidChangeTextEditorSelection((e) => this.onSelectionChanged(e), null, context.subscriptions);
    const saved = context.workspaceState.get("claudeDesign.hand");
    if (saved === "terse" || saved === "discursive" || saved === "diagrammatic") {
      this.hand = saved;
    }
  }
  cycleHand() {
    const order = ["terse", "discursive", "diagrammatic"];
    const next = order[(order.indexOf(this.hand) + 1) % order.length];
    this.setHand(next);
  }
  async show(leaf) {
    const folders = vscode11.workspace.workspaceFolders;
    if (!folders?.length)
      return;
    const uri = vscode11.Uri.joinPath(folders[0].uri, leaf);
    try {
      const doc = await vscode11.workspace.openTextDocument(uri);
      await vscode11.window.showTextDocument(doc, { preview: false });
    } catch {
      this.activeLeaf = leaf;
      this.refresh();
    }
  }
  setHand(hand) {
    this.hand = hand;
    this.context.workspaceState.update("claudeDesign.hand", hand);
    this.view?.webview.postMessage({ type: "hand", hand });
  }
  resolveWebviewView(view) {
    this.view = view;
    view.webview.options = { enableScripts: true };
    view.webview.html = renderHtml();
    view.webview.onDidReceiveMessage((msg) => this.onMessage(msg), null, this.context.subscriptions);
    this.onEditorChanged(vscode11.window.activeTextEditor);
    if (this.activeLeaf)
      this.refresh();
    view.webview.postMessage({ type: "hand", hand: this.hand });
  }
  onEditorChanged(editor) {
    if (!editor)
      return;
    const rel = designLeafPath(editor.document.uri);
    if (!rel)
      return;
    this.activeLeaf = rel.path;
    this.selectionExcerpt = undefined;
    this.refresh();
  }
  onSelectionChanged(e) {
    if (!this.view || !this.activeLeaf)
      return;
    const rel = designLeafPath(e.textEditor.document.uri);
    if (!rel || rel.path !== this.activeLeaf)
      return;
    const sel = e.selections[0];
    if (!sel || sel.isEmpty) {
      this.selectionExcerpt = undefined;
      this.view.webview.postMessage({ type: "selection", clear: true });
      return;
    }
    const startLine = sel.start.line + 1;
    const endLine = sel.end.line + 1;
    const lines = startLine === endLine ? `L${startLine}` : `L${startLine}–${endLine}`;
    const raw = e.textEditor.document.getText(sel).replace(/\s+/g, " ").trim();
    const excerpt = raw.length > 140 ? raw.slice(0, 140) + "…" : raw;
    this.selectionExcerpt = { lines, text: excerpt };
    this.view.webview.postMessage({ type: "selection", lines, excerpt });
  }
  async refresh() {
    if (!this.view || !this.activeLeaf)
      return;
    const leaf = await this.store.load(this.activeLeaf);
    const masterText = await readLeafText(this.activeLeaf);
    this.view.webview.postMessage({
      type: "leaf",
      path: leaf.path,
      masterText,
      entries: leaf.entries.map(serializeForView)
    });
  }
  async onMessage(msg) {
    if (msg.type === "set-hand" && (msg.hand === "terse" || msg.hand === "discursive" || msg.hand === "diagrammatic")) {
      this.setHand(msg.hand);
      return;
    }
    if (!this.activeLeaf)
      return;
    if (msg.type === "rubric" && typeof msg.text === "string" && msg.text.trim()) {
      const text = msg.text.trim();
      const bound = this.selectionExcerpt;
      const annotated = bound ? `[${bound.lines}] «${bound.text}» — ${text}` : text;
      const rubric = {
        kind: "rubric",
        hand: "master",
        timestamp: new Date,
        text: annotated
      };
      await this.store.append(this.activeLeaf, rubric);
      this.selectionExcerpt = undefined;
      this.view?.webview.postMessage({ type: "selection", clear: true });
      await this.refresh();
      await this.invokeScribe(this.activeLeaf, annotated);
    }
    if (msg.type === "open-leaf" && typeof msg.path === "string") {
      const uri = vscode11.Uri.joinPath(vscode11.workspace.workspaceFolders[0].uri, msg.path);
      const doc = await vscode11.workspace.openTextDocument(uri);
      await vscode11.window.showTextDocument(doc);
    }
  }
  async invokeScribe(leafPath, rubricText) {
    if (!this.view)
      return;
    const leaf = await this.store.load(leafPath);
    const masterText = await readLeafText(leafPath);
    const recent = leaf.entries.slice(-12).map((e) => `[${e.hand}/${e.kind}] ${e.text}`).join(`
`);
    const handGuidance = {
      terse: "Reply as gloss — terse, scribal, useful. One paragraph at most. " + "No preamble. If you write a file, name it explicitly so a colophon can be signed.",
      discursive: "Reply as discursive gloss — unfold reasoning, name tradeoffs, " + "cite the master’s rubric when relevant. Multiple paragraphs welcome. " + "If you write a file, name it explicitly so a colophon can be signed.",
      diagrammatic: "Reply as diagrammatic gloss — prefer lists, tables, small ASCII layouts, " + "or structured outlines over prose. Be visual on the page. " + "If you write a file, name it explicitly so a colophon can be signed."
    };
    const prompt = `You are the scribe of the Scriptorium. The master is annotating ` + `${leafPath}. Recent marginalia:
${recent}

` + sourceBlock(leafPath, masterText) + `The master writes: ${rubricText}

` + handGuidance[this.hand];
    let glossBuffer = "";
    await this.inference.stream({
      prompt,
      onChunk: (text) => {
        glossBuffer += text;
        this.view?.webview.postMessage({ type: "gloss-stream", text: glossBuffer });
      },
      onDone: async () => {
        if (!glossBuffer.trim())
          return;
        await this.store.append(leafPath, {
          kind: "gloss",
          hand: "scribe",
          timestamp: new Date,
          text: glossBuffer
        });
        await this.refresh();
      },
      onError: (err) => {
        this.view?.webview.postMessage({
          type: "gloss-stream",
          text: `(scribal hand falters — ${err.message})`
        });
      }
    });
  }
}
async function readLeafText(leafPath) {
  try {
    const folders = vscode11.workspace.workspaceFolders;
    if (!folders?.length)
      return "";
    const uri = vscode11.Uri.joinPath(folders[0].uri, leafPath);
    const bytes = await vscode11.workspace.fs.readFile(uri);
    return new TextDecoder().decode(bytes);
  } catch {
    return "";
  }
}
function sourceBlock(leafPath, text) {
  if (!text.trim()) {
    return `Active leaf source for ${leafPath}: unavailable.

`;
  }
  const maxChars = 24000;
  const truncated = text.length > maxChars;
  const excerpt = truncated ? text.slice(0, maxChars) : text;
  return `Active leaf source for ${leafPath}` + `${truncated ? ` (first ${maxChars} of ${text.length} chars)` : ` (${text.length} chars)`}:
` + "```html\n" + excerpt + "\n```\n\n";
}
function serializeForView(e) {
  return {
    kind: e.kind,
    hand: e.hand,
    timestamp: e.timestamp.toISOString(),
    text: e.text,
    colophon: e.colophon
  };
}
function renderHtml() {
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<style>
  :root {
    color-scheme: light dark;
    --parchment: var(--vscode-editor-background);
    --ink: var(--vscode-editor-foreground);
    --ink-dim: color-mix(in oklab, var(--ink) 60%, transparent);
    --ink-faint: color-mix(in oklab, var(--ink) 35%, transparent);
    --rubric: var(--vscode-charts-red, var(--vscode-errorForeground, #b85450));
    --gloss-rule: color-mix(in oklab, var(--ink) 15%, transparent);
    --colophon: var(--vscode-charts-orange, var(--vscode-textLink-foreground));
    --serif: ui-serif, 'Iowan Old Style', 'Georgia', 'Garamond', serif;
    --mono: var(--vscode-editor-font-family, 'Cascadia Code', ui-monospace, monospace);
  }
  * { box-sizing: border-box; }
  html, body {
    margin: 0; padding: 0;
    background: var(--parchment); color: var(--ink);
    font-family: var(--serif);
    font-size: 13px; line-height: 1.55;
    height: 100vh; overflow: hidden;
  }

  .stage {
    display: grid; grid-template-rows: auto 1fr auto auto auto;
    height: 100vh; overflow: hidden;
  }

  .leaf-head {
    padding: 10px 14px;
    border-bottom: 1px solid var(--gloss-rule);
    display: flex; align-items: baseline; gap: 10px;
    font-family: var(--mono); font-size: 10px;
    letter-spacing: .12em; text-transform: uppercase;
    color: var(--ink-dim);
  }
  .leaf-head .sigil { color: var(--rubric); font-family: var(--serif); font-size: 14px; }
  .leaf-head .path { color: var(--ink); letter-spacing: .04em; text-transform: none; font-family: var(--mono); }

  .leaf {
    display: grid;
    grid-template-columns: 1fr minmax(280px, 1.1fr);
    min-height: 0;
  }
  .master {
    overflow: auto;
    padding: 18px 18px 18px 22px;
    border-right: 1px solid var(--gloss-rule);
    font-family: var(--mono);
    font-size: 11.5px;
    line-height: 1.6;
    white-space: pre-wrap;
    color: var(--ink-dim);
  }
  .master:empty::before {
    content: 'no leaf chosen — open a file under designs/';
    color: var(--ink-faint);
    font-style: italic;
    font-family: var(--serif);
    font-size: 12px;
  }

  .marginalia {
    overflow: auto;
    padding: 14px 16px 18px 18px;
    display: flex; flex-direction: column; gap: 18px;
  }
  .marginalia:empty::before {
    content: 'no marginalia yet — write a rubric below';
    color: var(--ink-faint);
    font-style: italic;
  }

  .entry { position: relative; padding-left: 18px; }
  .entry .meta {
    font-family: var(--mono); font-size: 10px;
    letter-spacing: .08em; color: var(--ink-faint);
    margin-bottom: 4px;
  }
  .entry .sigil {
    position: absolute; left: 0; top: 0;
    font-size: 14px; line-height: 1.2;
  }
  .entry.rubric .sigil { color: var(--rubric); }
  .entry.gloss .sigil { color: var(--ink-dim); }
  .entry.colophon .sigil { color: var(--colophon); }

  .entry.rubric .text {
    color: var(--rubric); font-style: italic;
  }
  .entry.gloss .text {
    color: var(--ink);
  }
  .entry.colophon .text {
    color: var(--colophon);
    font-family: var(--mono); font-size: 11px;
  }
  .text { white-space: pre-wrap; }

  .gloss-stream {
    border-left: 2px solid var(--colophon);
    padding-left: 10px; margin-left: 18px;
    color: var(--ink); font-style: italic;
  }
  .gloss-stream::after {
    content: '▍'; animation: blink 1s steps(2) infinite;
    color: var(--colophon); margin-left: 2px;
  }
  @keyframes blink { 50% { opacity: 0; } }

  .selection-bar {
    border-top: 1px solid var(--gloss-rule);
    padding: 6px 14px;
    display: none;
    align-items: center; gap: 8px;
    font-family: var(--mono); font-size: 10px;
    letter-spacing: .04em; color: var(--ink-dim);
    background: color-mix(in oklab, var(--rubric) 6%, var(--parchment));
  }
  .selection-bar.on { display: flex; }
  .selection-bar .lines { color: var(--rubric); }
  .selection-bar .excerpt {
    color: var(--ink); font-family: var(--serif); font-style: italic;
    font-size: 11.5px; letter-spacing: 0;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    flex: 1; min-width: 0;
  }
  .selection-bar .clear {
    background: transparent; border: 0; color: var(--ink-faint);
    font-family: var(--mono); font-size: 10px; cursor: pointer; padding: 0 4px;
  }
  .selection-bar .clear:hover { color: var(--rubric); }

  .hand-bar {
    border-top: 1px solid var(--gloss-rule);
    padding: 6px 14px;
    display: flex; align-items: center; gap: 8px;
    font-family: var(--mono); font-size: 10px;
    letter-spacing: .08em; color: var(--ink-faint); text-transform: uppercase;
  }
  .hand-bar .label { padding-right: 4px; }
  .hand-bar .seg {
    display: inline-flex; border: 1px solid var(--gloss-rule); border-radius: 2px;
    overflow: hidden;
  }
  .hand-bar .seg button {
    background: transparent; border: 0;
    padding: 2px 8px; font-family: var(--mono); font-size: 10px;
    letter-spacing: .08em; text-transform: uppercase;
    color: var(--ink-dim); cursor: pointer;
  }
  .hand-bar .seg button + button { border-left: 1px solid var(--gloss-rule); }
  .hand-bar .seg button.on {
    background: color-mix(in oklab, var(--rubric) 14%, transparent);
    color: var(--rubric);
  }
  .hand-bar .seg button:hover:not(.on) { color: var(--ink); }

  .composer {
    border-top: 1px solid var(--gloss-rule);
    padding: 10px 14px;
    display: flex; align-items: flex-start; gap: 8px;
    background: var(--parchment);
  }
  .composer .sigil {
    color: var(--rubric); font-size: 16px; padding-top: 3px;
  }
  .composer textarea {
    flex: 1;
    background: transparent;
    border: 0; outline: 0; resize: none;
    color: var(--rubric); font-family: var(--serif); font-style: italic;
    font-size: 13.5px; line-height: 1.5;
    padding: 4px 0; min-height: 22px; max-height: 160px;
  }
  .composer textarea::placeholder { color: var(--ink-faint); font-style: italic; }
  .composer .hint {
    font-family: var(--mono); font-size: 9.5px;
    color: var(--ink-faint); letter-spacing: .08em;
    padding-top: 7px; white-space: nowrap;
  }

  .credit {
    position: fixed; right: 10px; bottom: 6px;
    font-family: var(--mono); font-size: 9px;
    color: var(--ink-faint); letter-spacing: .14em; text-transform: uppercase;
    pointer-events: none;
  }
</style>
</head>
<body>
  <div class="stage">
    <header class="leaf-head">
      <span class="sigil">❦</span>
      <span>marginalia ·</span>
      <span class="path" id="leaf-path">—</span>
    </header>
    <div class="leaf">
      <pre class="master" id="master"></pre>
      <div class="marginalia" id="marginalia"></div>
    </div>
    <div class="selection-bar" id="selbar">
      <span class="lines" id="sel-lines">—</span>
      <span class="excerpt" id="sel-excerpt"></span>
      <button class="clear" id="sel-clear" type="button" title="unbind selection">✕</button>
    </div>
    <div class="hand-bar">
      <span class="label">hand</span>
      <span class="seg" id="hand-seg">
        <button type="button" data-hand="terse">terse</button>
        <button type="button" data-hand="discursive">discursive</button>
        <button type="button" data-hand="diagrammatic">diagrammatic</button>
      </span>
    </div>
    <form class="composer" id="composer" autocomplete="off">
      <span class="sigil">❦</span>
      <textarea id="rubric" rows="1" placeholder="write a rubric…"></textarea>
      <span class="hint">⏎ to send · ⇧⏎ for line</span>
    </form>
  </div>
  <div class="credit">marginalia · made by claude</div>

<script>
  const vscode = acquireVsCodeApi();
  const masterEl = document.getElementById('master');
  const margEl = document.getElementById('marginalia');
  const pathEl = document.getElementById('leaf-path');
  const rubricEl = document.getElementById('rubric');
  const composerEl = document.getElementById('composer');

  let streamEl = null;

  function renderEntries(entries) {
    margEl.innerHTML = '';
    streamEl = null;
    for (const e of entries) {
      const node = document.createElement('div');
      node.className = 'entry ' + e.kind;
      const sigil = { rubric: '❦', gloss: '¶', colophon: '⌘' }[e.kind] || '·';
      const when = new Date(e.timestamp);
      const stamp = when.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
      const meta = e.kind + ' · ' + stamp + ' · ' + e.hand;
      let body = e.text;
      if (e.kind === 'colophon' && e.colophon) {
        body = '— ' + e.colophon.path + ' · ' + e.colophon.bytes + ' bytes · ' + e.colophon.sig;
      }
      node.innerHTML =
        '<span class="sigil">' + sigil + '</span>' +
        '<div class="meta">' + meta + '</div>' +
        '<div class="text"></div>';
      node.querySelector('.text').textContent = body;
      margEl.appendChild(node);
    }
    margEl.scrollTop = margEl.scrollHeight;
  }

  const selBar = document.getElementById('selbar');
  const selLines = document.getElementById('sel-lines');
  const selExcerpt = document.getElementById('sel-excerpt');
  const selClear = document.getElementById('sel-clear');
  const handSeg = document.getElementById('hand-seg');

  function paintHand(hand) {
    handSeg.querySelectorAll('button').forEach(b => {
      b.classList.toggle('on', b.dataset.hand === hand);
    });
  }

  handSeg.addEventListener('click', ev => {
    const btn = ev.target.closest('button[data-hand]');
    if (!btn) return;
    paintHand(btn.dataset.hand);
    vscode.postMessage({ type: 'set-hand', hand: btn.dataset.hand });
  });

  selClear.addEventListener('click', () => {
    selBar.classList.remove('on');
    vscode.postMessage({ type: 'selection-cleared' });
  });

  window.addEventListener('message', ev => {
    const m = ev.data;
    if (m.type === 'leaf') {
      pathEl.textContent = m.path;
      masterEl.textContent = m.masterText || '';
      renderEntries(m.entries);
    } else if (m.type === 'gloss-stream') {
      if (!streamEl) {
        streamEl = document.createElement('div');
        streamEl.className = 'gloss-stream';
        margEl.appendChild(streamEl);
      }
      streamEl.textContent = m.text;
      margEl.scrollTop = margEl.scrollHeight;
    } else if (m.type === 'hand') {
      paintHand(m.hand);
    } else if (m.type === 'selection') {
      if (m.clear) {
        selBar.classList.remove('on');
      } else {
        selLines.textContent = m.lines;
        selExcerpt.textContent = '«' + m.excerpt + '»';
        selBar.classList.add('on');
      }
    }
  });

  function autosize() {
    rubricEl.style.height = 'auto';
    rubricEl.style.height = Math.min(rubricEl.scrollHeight, 160) + 'px';
  }
  rubricEl.addEventListener('input', autosize);

  composerEl.addEventListener('submit', ev => {
    ev.preventDefault();
    const text = rubricEl.value.trim();
    if (!text) return;
    vscode.postMessage({ type: 'rubric', text });
    rubricEl.value = '';
    autosize();
  });

  rubricEl.addEventListener('keydown', ev => {
    if (ev.key === 'Enter' && !ev.shiftKey) {
      ev.preventDefault();
      composerEl.requestSubmit();
    }
  });
</script>
</body>
</html>`;
}

// src/views/vivarium.ts
import * as vscode12 from "vscode";
class VivariumView {
  context;
  static viewType = "claudeDesign.vivarium";
  view;
  activeLeaf;
  saveListener;
  constructor(context) {
    this.context = context;
    vscode12.window.onDidChangeActiveTextEditor((e) => this.onEditorChanged(e), null, context.subscriptions);
    this.saveListener = vscode12.workspace.onDidSaveTextDocument((doc) => this.onDocumentSaved(doc), null, context.subscriptions);
  }
  resolveWebviewView(view) {
    this.view = view;
    const roots = designResourceRoots();
    view.webview.options = { enableScripts: true, localResourceRoots: roots };
    view.webview.html = renderShell();
    view.webview.onDidReceiveMessage((msg) => this.onMessage(msg), null, this.context.subscriptions);
    this.onEditorChanged(vscode12.window.activeTextEditor);
    if (this.activeLeaf)
      this.loadSpecimen();
  }
  onEditorChanged(editor) {
    if (!editor)
      return;
    const rel = designLeafPath(editor.document.uri, /\.(html?|svg)$/i);
    if (!rel)
      return;
    this.activeLeaf = editor.document.uri;
    this.loadSpecimen();
  }
  onDocumentSaved(doc) {
    if (!this.activeLeaf)
      return;
    if (doc.uri.toString() === this.activeLeaf.toString()) {
      this.loadSpecimen();
    }
  }
  onMessage(msg) {
    if (msg.type === "set-frame" && this.view) {
      this.context.workspaceState.update("claudeDesign.vivarium.frame", msg.frame);
    }
  }
  async loadSpecimen() {
    if (!this.view || !this.activeLeaf)
      return;
    const rel = designLeafPath(this.activeLeaf, /\.(html?|svg)$/i)?.path ?? this.activeLeaf.fsPath.replace(/\\/g, "/");
    const webviewUri = this.view.webview.asWebviewUri(this.activeLeaf);
    let stamp = Date.now();
    try {
      const stat = await vscode12.workspace.fs.stat(this.activeLeaf);
      stamp = stat.mtime;
    } catch {}
    this.view.webview.postMessage({
      type: "specimen",
      path: rel,
      src: `${webviewUri.toString()}?v=${stamp}`,
      frame: this.context.workspaceState.get("claudeDesign.vivarium.frame", "parchment")
    });
  }
}
function renderShell() {
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<style>
  :root {
    color-scheme: light dark;
    --bg: var(--vscode-editor-background);
    --fg: var(--vscode-editor-foreground);
    --fg-dim: color-mix(in oklab, var(--fg) 55%, transparent);
    --fg-faint: color-mix(in oklab, var(--fg) 28%, transparent);
    --rule: color-mix(in oklab, var(--fg) 14%, transparent);
    --rubric: var(--vscode-charts-red, var(--vscode-errorForeground, #b85450));
    --colophon: var(--vscode-charts-orange, var(--vscode-textLink-foreground));
    --mat: color-mix(in oklab, var(--bg) 88%, #e6dcc0 12%);
    --serif: ui-serif, 'Iowan Old Style', 'Georgia', serif;
    --mono: var(--vscode-editor-font-family, 'Cascadia Code', ui-monospace, monospace);
  }
  * { box-sizing: border-box; }
  html, body {
    margin: 0; padding: 0; height: 100vh; overflow: hidden;
    background: var(--bg); color: var(--fg);
    font-family: var(--serif); font-size: 12px;
  }

  .stage { display: grid; grid-template-rows: auto 1fr auto; height: 100vh; }

  .head {
    padding: 8px 12px;
    border-bottom: 1px solid var(--rule);
    display: flex; align-items: baseline; gap: 10px;
    font-family: var(--mono); font-size: 10px;
    letter-spacing: .12em; text-transform: uppercase;
    color: var(--fg-dim);
  }
  .head .sigil { color: var(--rubric); font-family: var(--serif); font-size: 14px; }
  .head .path { color: var(--fg); letter-spacing: .04em; text-transform: none; }

  .plate {
    overflow: auto;
    display: grid; place-items: center;
    padding: 24px;
    background:
      radial-gradient(ellipse at center top,
        color-mix(in oklab, var(--bg) 92%, var(--colophon) 8%) 0%,
        var(--bg) 60%);
  }

  .frame {
    position: relative;
    background: var(--mat);
    border: 1px solid var(--rule);
    box-shadow: 0 30px 60px -25px rgba(0,0,0,.5),
                0 0 0 1px color-mix(in oklab, var(--colophon) 18%, transparent);
    border-radius: 4px;
  }
  .frame.bare { background: transparent; box-shadow: none; border-color: transparent; padding: 0; }
  .frame.parchment { padding: 24px; }
  .frame.device {
    padding: 14px;
    border-radius: 18px;
    background:
      linear-gradient(180deg,
        color-mix(in oklab, var(--bg) 80%, #000 20%),
        color-mix(in oklab, var(--bg) 70%, #000 30%));
  }
  .frame.device::before {
    content: '';
    position: absolute; top: 6px; left: 50%; transform: translateX(-50%);
    width: 40%; height: 4px; border-radius: 2px;
    background: color-mix(in oklab, var(--fg) 30%, transparent);
  }

  .specimen-shell {
    background: #fff;
    border-radius: 2px;
    overflow: hidden;
    box-shadow: inset 0 0 0 1px var(--rule);
    width: min(900px, 78vw);
    aspect-ratio: 16 / 10;
    display: block;
  }
  .frame.device .specimen-shell {
    width: min(360px, 86vw);
    aspect-ratio: 9 / 16;
    border-radius: 10px;
  }
  iframe.specimen {
    width: 100%; height: 100%;
    border: 0; display: block; background: #fff;
  }

  .empty {
    color: var(--fg-faint); font-style: italic; font-size: 13px;
    font-family: var(--serif);
    text-align: center; max-width: 24em; line-height: 1.6;
  }

  .foot {
    border-top: 1px solid var(--rule);
    padding: 6px 12px;
    display: flex; align-items: center; gap: 10px;
    background: var(--bg);
    font-family: var(--mono); font-size: 10px;
    letter-spacing: .1em; text-transform: uppercase;
    color: var(--fg-dim);
  }
  .foot .frames { display: flex; gap: 6px; margin-left: auto; }
  .foot button {
    background: transparent; border: 1px solid var(--rule);
    color: var(--fg-dim); cursor: pointer;
    padding: 3px 9px; border-radius: 3px;
    font-family: var(--mono); font-size: 10px;
    letter-spacing: .1em; text-transform: uppercase;
  }
  .foot button:hover { color: var(--fg); border-color: var(--colophon); }
  .foot button.active {
    color: var(--colophon); border-color: var(--colophon);
    background: color-mix(in oklab, var(--colophon) 10%, transparent);
  }
  .foot .stamp { color: var(--colophon); }

  .credit {
    position: fixed; right: 10px; bottom: 28px;
    font-family: var(--mono); font-size: 9px;
    color: var(--fg-faint); letter-spacing: .14em; text-transform: uppercase;
    pointer-events: none;
  }
</style>
</head>
<body>
  <div class="stage">
    <header class="head">
      <span class="sigil">◑</span>
      <span>vivarium ·</span>
      <span class="path" id="path">—</span>
    </header>
    <main class="plate" id="plate">
      <div class="empty">no specimen — open an .html or .svg leaf under designs/</div>
    </main>
    <footer class="foot">
      <span class="stamp" id="stamp">awaiting specimen</span>
      <div class="frames">
        <button data-frame="bare">bare</button>
        <button data-frame="parchment" class="active">parchment</button>
        <button data-frame="device">device</button>
      </div>
    </footer>
  </div>
  <div class="credit">vivarium · made by claude</div>

<script>
  const vscode = acquireVsCodeApi();
  const plate = document.getElementById('plate');
  const pathEl = document.getElementById('path');
  const stampEl = document.getElementById('stamp');
  let currentFrame = 'parchment';
  let currentSrc = null;
  let currentPath = null;

  function render() {
    if (!currentSrc) {
      plate.innerHTML = '<div class="empty">no specimen — open an .html or .svg leaf under designs/</div>';
      return;
    }
    plate.innerHTML =
      '<div class="frame ' + currentFrame + '">' +
        '<div class="specimen-shell">' +
          '<iframe class="specimen" sandbox="allow-scripts" src="' + currentSrc + '"></iframe>' +
        '</div>' +
      '</div>';
  }

  function setFrame(name) {
    currentFrame = name;
    document.querySelectorAll('.foot button').forEach(b => {
      b.classList.toggle('active', b.dataset.frame === name);
    });
    vscode.postMessage({ type: 'set-frame', frame: name });
    render();
  }

  document.querySelectorAll('.foot button').forEach(b => {
    b.addEventListener('click', () => setFrame(b.dataset.frame));
  });

  window.addEventListener('message', ev => {
    const m = ev.data;
    if (m.type === 'specimen') {
      currentSrc = m.src;
      currentPath = m.path;
      pathEl.textContent = m.path;
      stampEl.textContent = 'rendered · ' + new Date().toLocaleTimeString();
      if (m.frame && m.frame !== currentFrame) {
        setFrame(m.frame);
      } else {
        render();
      }
    }
  });
</script>
</body>
</html>`;
}

// src/views/previewPanel.ts
import * as vscode13 from "vscode";
import * as path5 from "node:path";

class PreviewPanel {
  ctx;
  static current = null;
  panel;
  currentUri = null;
  constructor(panel, ctx) {
    this.ctx = ctx;
    this.panel = panel;
    this.panel.onDidDispose(() => {
      PreviewPanel.current = null;
    });
    this.panel.webview.onDidReceiveMessage((msg) => this.handleMessage(msg));
    this.render(null);
  }
  static show(ctx, _bridge) {
    if (PreviewPanel.current) {
      PreviewPanel.current.panel.reveal();
      return;
    }
    const panel = vscode13.window.createWebviewPanel("claudeDesignPreview", "Claude Design — Preview", vscode13.ViewColumn.Beside, { enableScripts: true, retainContextWhenHidden: true });
    PreviewPanel.current = new PreviewPanel(panel, ctx);
    PreviewPanel.current.loadLatest();
  }
  static toggleTweaks() {
    PreviewPanel.current?.panel.webview.postMessage({ type: "__activate_edit_mode" });
  }
  static onFileSaved(uri) {
    if (!PreviewPanel.current)
      return;
    if (uri.fsPath.includes(path5.sep + "designs" + path5.sep)) {
      PreviewPanel.current.render(uri);
    }
  }
  static dispose() {
    PreviewPanel.current?.panel.dispose();
  }
  async loadLatest() {
    const root = vscode13.workspace.workspaceFolders?.[0];
    if (!root)
      return;
    const dir = vscode13.Uri.joinPath(root.uri, "designs");
    try {
      const entries = await vscode13.workspace.fs.readDirectory(dir);
      const html = entries.find(([n, t]) => t === vscode13.FileType.File && n.endsWith(".html"));
      if (html)
        this.render(vscode13.Uri.joinPath(dir, html[0]));
    } catch {}
  }
  async render(uri) {
    this.currentUri = uri;
    let body = `<div class="empty">Open <code>Claude Design: Open Preview Beside</code> on a design file.</div>`;
    if (uri) {
      try {
        const raw = await vscode13.workspace.fs.readFile(uri);
        body = new TextDecoder().decode(raw);
      } catch (e) {
        body = `<pre>${String(e)}</pre>`;
      }
    }
    this.panel.webview.html = this.wrap(body, uri);
  }
  wrap(body, uri) {
    const title = uri ? path5.basename(uri.fsPath) : "Claude Design";
    return `<!doctype html><html><head><meta charset="utf-8"><title>${title}</title>
<style>
  :root {
    --bg: var(--vscode-editor-background);
    --fg: var(--vscode-foreground);
    --line: var(--vscode-panel-border, var(--vscode-editorWidget-border));
    --accent: var(--vscode-charts-orange, var(--vscode-statusBarItem-warningBackground, #e8b339));
  }
  html, body { margin: 0; padding: 0; background: var(--bg); color: var(--fg); font-family: var(--vscode-font-family); }
  .chrome { display: flex; align-items: center; gap: 10px; padding: 6px 10px; border-bottom: 1px solid var(--line); font-size: 12px; }
  .chrome .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--accent); box-shadow: 0 0 8px var(--accent); }
  .chrome .file { font-family: var(--vscode-editor-font-family); opacity: .7; }
  .chrome .grow { flex: 1; }
  iframe.preview { width: 100%; height: calc(100vh - 30px); border: 0; background: white; }
  .empty { padding: 40px; opacity: .6; font-family: var(--vscode-editor-font-family); }
</style></head>
<body>
  <div class="chrome"><span class="dot"></span><span>Design</span><span class="file">${uri ? path5.basename(uri.fsPath) : ""}</span><span class="grow"></span><span>live</span></div>
  <iframe class="preview" sandbox="allow-scripts" srcdoc="${escapeAttr(body)}"></iframe>
  <script>
    const vscode = acquireVsCodeApi();
    window.addEventListener("message", e => {
      // Forward Tweaks protocol messages from extension → iframe.
      const ifr = document.querySelector("iframe.preview");
      if (ifr && e.data && typeof e.data === "object" && e.data.type) ifr.contentWindow.postMessage(e.data, "*");
    });
  </script>
</body></html>`;
  }
  handleMessage(_msg) {}
}
function escapeAttr(s) {
  return s.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// src/views/chatPanel.ts
class ChatPanel {
  ctx;
  fs;
  static viewType = "claudeDesign.chat";
  view = null;
  inference;
  constructor(ctx, fs2, cliPath = "claude") {
    this.ctx = ctx;
    this.fs = fs2;
    this.inference = new CliInference(cliPath);
    this.inference.on("event", (e) => this.handleStream(e));
  }
  resolveWebviewView(view) {
    this.view = view;
    view.webview.options = { enableScripts: true };
    view.webview.html = this.html();
    view.webview.onDidReceiveMessage((msg) => this.onMessage(msg));
  }
  onMessage(msg) {
    if (msg.type === "send" && typeof msg.text === "string") {
      const cwd = this.fs.workspaceRoot()?.fsPath;
      this.inference.send(msg.text, { cwd });
      this.post({ type: "user", text: msg.text });
    }
  }
  async handleStream(e) {
    const error = streamEventError(e);
    if (error) {
      this.post({ type: "tool", line: `! ${error.trim()}` });
    }
    const delta = streamEventText(e);
    if (delta) {
      this.post({ type: "claude", delta });
    }
    if (e.type === "tool_use") {
      const d = e.data || {};
      if (d.name === "write_file" && d.input?.path && typeof d.input?.content === "string") {
        try {
          const uri = await this.fs.write(d.input.path, d.input.content);
          this.post({ type: "tool", line: `✎ wrote ${this.fs.relativize(uri)} · ok` });
          PreviewPanel.onFileSaved(uri);
        } catch (err) {
          this.post({ type: "tool", line: `✗ ${String(err)}` });
        }
      } else {
        this.post({ type: "tool", line: `· ${d.name ?? "tool"}` });
      }
    }
    if (e.type === "usage") {
      this.post({ type: "usage", data: e.data });
    }
    if (streamEventDone(e)) {
      this.post({ type: "done" });
    }
  }
  post(msg) {
    this.view?.webview.postMessage(msg);
  }
  dispose() {
    this.inference.dispose();
  }
  html() {
    return `<!doctype html><html><head><meta charset="utf-8"><style>
  :root {
    --bg: var(--vscode-sideBar-background, var(--vscode-editor-background));
    --fg: var(--vscode-foreground);
    --line: var(--vscode-panel-border, var(--vscode-editorWidget-border));
    --muted: var(--vscode-descriptionForeground);
    --accent: var(--claude-accent, var(--vscode-charts-orange, #e8b339));
    --user-bg: var(--vscode-textBlockQuote-background, rgba(127,127,127,.12));
    --claude-bg: transparent;
    --input-bg: var(--vscode-input-background);
    --input-fg: var(--vscode-input-foreground);
    --input-border: var(--vscode-input-border, var(--line));
  }
  html, body { margin:0; padding:0; height:100%; background:var(--bg); color:var(--fg); font-family: var(--vscode-font-family); font-size: var(--vscode-font-size); }
  body { display:flex; flex-direction:column; }
  .stream { flex:1; overflow-y:auto; padding: 10px 12px; display:flex; flex-direction:column; gap: 10px; }
  .msg { padding: 8px 10px; border-radius: 4px; line-height: 1.5; max-width: 100%; white-space: pre-wrap; word-wrap: break-word; }
  .msg.user   { background: var(--user-bg); align-self: flex-end; max-width: 85%; }
  .msg.claude { align-self: flex-start; }
  .msg.claude .name { color: var(--accent); font-size: 11px; letter-spacing: .08em; text-transform: uppercase; margin-bottom: 4px; font-weight: 600; }
  .msg.tool   { font-family: var(--vscode-editor-font-family); font-size: 11px; color: var(--muted); border-left: 2px solid var(--line); padding: 4px 8px; }
  .composer { border-top: 1px solid var(--line); padding: 8px; display:flex; gap: 6px; }
  textarea {
    flex: 1; resize: none; min-height: 28px; max-height: 120px;
    background: var(--input-bg); color: var(--input-fg); border: 1px solid var(--input-border);
    border-radius: 3px; padding: 6px 8px; font-family: inherit; font-size: inherit;
  }
  textarea:focus { outline: 1px solid var(--vscode-focusBorder); border-color: transparent; }
  button {
    background: var(--vscode-button-background); color: var(--vscode-button-foreground);
    border: 0; padding: 0 12px; border-radius: 3px; cursor: pointer; font-family: inherit;
  }
  button:hover { background: var(--vscode-button-hoverBackground); }
  .caret::after { content:"▍"; color: var(--accent); animation: blk 1s infinite; }
  @keyframes blk { 50% { opacity: 0; } }
</style></head>
<body>
  <div class="stream" id="stream"></div>
  <div class="composer">
    <textarea id="input" placeholder="Message Claude · Enter to send · Shift+Enter for newline"></textarea>
    <button id="send">Send</button>
  </div>
<script>
  const vscode = acquireVsCodeApi();
  const stream = document.getElementById("stream");
  const input = document.getElementById("input");
  const send = document.getElementById("send");
  let currentClaude = null;

  function scroll() { stream.scrollTop = stream.scrollHeight; }
  function add(cls, html) {
    const d = document.createElement("div");
    d.className = "msg " + cls;
    d.innerHTML = html;
    stream.appendChild(d);
    scroll();
    return d;
  }

  function doSend() {
    const t = input.value.trim();
    if (!t) return;
    vscode.postMessage({ type: "send", text: t });
    input.value = "";
    currentClaude = null;
  }
  send.addEventListener("click", doSend);
  input.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); doSend(); }
  });

  window.addEventListener("message", e => {
    const m = e.data;
    if (m.type === "user")   { add("user", escape(m.text)); }
    if (m.type === "claude") {
      if (!currentClaude) {
        currentClaude = add("claude", '<div class="name">Claude</div><div class="body caret"></div>');
      }
      const body = currentClaude.querySelector(".body");
      body.textContent += m.delta || "";
      scroll();
    }
    if (m.type === "tool")   { add("tool", escape(m.line)); }
    if (m.type === "done")   {
      if (currentClaude) currentClaude.querySelector(".body")?.classList.remove("caret");
      currentClaude = null;
    }
  });

  function escape(s) { return String(s).replace(/[&<>]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;"}[c])); }
</script>
</body></html>`;
  }
}

// src/diagnostics/selfTest.ts
import * as vscode14 from "vscode";
import { spawn as spawn2 } from "node:child_process";
import * as os from "node:os";
async function runSelfTest(ctx) {
  const results = [];
  const t0 = Date.now();
  results.push({ name: "platform", status: "ok", detail: `${os.platform()} ${os.release()} · ${os.arch()}` });
  results.push({ name: "node", status: "ok", detail: process.version });
  results.push({ name: "vscode", status: "ok", detail: vscode14.version });
  results.push({
    name: "workspace",
    status: vscode14.workspace.workspaceFolders ? "ok" : "warn",
    detail: vscode14.workspace.workspaceFolders?.[0]?.uri.fsPath ?? "no folder open"
  });
  const cliPath = vscode14.workspace.getConfiguration("claudeDesign").get("cliPath", "claude");
  const cliVersion = await probeCommand(cliPath, ["--version"]);
  results.push({
    name: "claude CLI",
    status: cliVersion.ok ? "ok" : "miss",
    detail: cliVersion.ok ? cliVersion.stdout.trim() : "not on PATH — install Claude Code or `claude` CLI"
  });
  const bunVersion = await probeCommand("bun", ["--version"]);
  results.push({
    name: "bun",
    status: bunVersion.ok ? "ok" : "warn",
    detail: bunVersion.ok ? bunVersion.stdout.trim() : "not on PATH — only needed for development, not runtime"
  });
  if (cliVersion.ok) {
    const ping = await probeCommand(cliPath, ["--print", "--output-format=json", "ping"], 8000);
    results.push({
      name: "auth liveness",
      status: ping.ok ? "ok" : "warn",
      detail: ping.ok ? "completion succeeded — Pro/Max quota reachable" : "completion failed — run `claude /login`"
    });
  } else {
    results.push({ name: "auth liveness", status: "unknown", detail: "skipped — CLI missing" });
  }
  const claudeCode = vscode14.extensions.getExtension("anthropic.claude-code");
  results.push({
    name: "Claude Code extension",
    status: claudeCode ? "ok" : "warn",
    detail: claudeCode ? `installed · v${claudeCode.packageJSON.version} · ${claudeCode.isActive ? "active" : "inactive"}` : "not installed — Claude Design works standalone"
  });
  if (claudeCode && claudeCode.isActive) {
    const exp = claudeCode.exports;
    results.push({
      name: "Claude Code API surface",
      status: exp ? "ok" : "unknown",
      detail: exp ? `keys: ${Object.keys(exp).join(", ")}` : "no public exports yet — falling back to CLI subprocess"
    });
  }
  const ws = vscode14.workspace.workspaceFolders?.[0]?.uri;
  if (ws) {
    for (const rel of ["designs", "assets", ".claude-design", "CLAUDE.md"]) {
      const target = vscode14.Uri.joinPath(ws, rel);
      try {
        const stat = await vscode14.workspace.fs.stat(target);
        results.push({ name: rel, status: "ok", detail: stat.type === vscode14.FileType.Directory ? "directory" : `file · ${stat.size}B` });
      } catch {
        results.push({ name: rel, status: "miss", detail: "not present — created on first write" });
      }
    }
  }
  results.push({
    name: "Anthropic Labs design meter API",
    status: "unknown",
    detail: "no public endpoint observed at time of writing — status bar uses local heuristics"
  });
  results.push({
    name: "project-export → editor handoff",
    status: "unknown",
    detail: "no claude-design://import deep-link observed — Phase 2 importer reads dropped export files instead"
  });
  const took = Date.now() - t0;
  const md = renderMarkdown(results, took);
  const doc = await vscode14.workspace.openTextDocument({ language: "markdown", content: md });
  await vscode14.window.showTextDocument(doc, { preview: false });
}
function renderMarkdown(rows, tookMs) {
  const icon = (s) => s === "ok" ? "✓" : s === "warn" ? "!" : s === "miss" ? "·" : "?";
  const lines = [];
  lines.push("# Claude Design — Self-Test");
  lines.push("");
  lines.push(`_${new Date().toISOString()} · completed in ${tookMs}ms_`);
  lines.push("");
  lines.push("| | check | detail |");
  lines.push("|---|---|---|");
  for (const r of rows)
    lines.push(`| ${icon(r.status)} | **${r.name}** | ${r.detail} |`);
  lines.push("");
  lines.push("## Legend");
  lines.push("- `✓` ok · everything responds as expected");
  lines.push("- `!` warn · works without it, better with it");
  lines.push("- `·` miss · absent · usually created on first write");
  lines.push("- `?` unknown · gated by an upstream surface we can't yet probe");
  lines.push("");
  lines.push("## Notes");
  lines.push("- This test never sends a chargeable completion beyond a single one-word ping.");
  lines.push("- The ledger entries (`?`) are intentional — they will flip to `✓` when Anthropic ships the corresponding surfaces.");
  return lines.join(`
`);
}
function probeCommand(cmd, args, timeoutMs = 4000) {
  return new Promise((resolve) => {
    let stdout = "", stderr = "", done = false;
    const finish = (ok) => {
      if (!done) {
        done = true;
        resolve({ ok, stdout, stderr });
      }
    };
    try {
      const child = spawn2(cmd, args, { shell: process.platform === "win32" });
      const timer = setTimeout(() => {
        try {
          child.kill();
        } catch {}
        finish(false);
      }, timeoutMs);
      child.stdout?.on("data", (d) => stdout += d);
      child.stderr?.on("data", (d) => stderr += d);
      child.on("error", () => {
        clearTimeout(timer);
        finish(false);
      });
      child.on("exit", (code) => {
        clearTimeout(timer);
        finish(code === 0);
      });
    } catch {
      finish(false);
    }
  });
}

// src/extension.ts
function makeAdapter(cli) {
  return {
    stream({ prompt, onChunk, onDone, onError }) {
      return new Promise((resolve) => {
        let finished = false;
        const finish = () => {
          if (finished)
            return;
          finished = true;
          cli.off("event", handler);
          Promise.resolve(onDone()).finally(() => resolve());
        };
        const handler = (evt) => {
          const error = streamEventError(evt);
          if (error) {
            onError?.(new Error(error));
          }
          const text = streamEventText(evt);
          if (text)
            onChunk(text);
          if (streamEventDone(evt)) {
            finish();
          }
        };
        cli.on("event", handler);
        cli.send(prompt, { cwd: vscode15.workspace.workspaceFolders?.[0]?.uri.fsPath });
      });
    }
  };
}
async function activate(context) {
  const cliPath = vscode15.workspace.getConfiguration("claudeDesign").get("cliPath", "claude");
  const substrateEnabled = vscode15.workspace.getConfiguration("claudeDesign").get("substrate.enabled", true);
  if (substrateEnabled) {
    try {
      const result = await enableSubstrate(context);
      if (result?.changed) {
        vscode15.window.showWarningMessage("Claude Design: Mica substrate patched into VS Code Insiders. Reload Insiders to activate it.");
      }
    } catch (error) {
      console.warn("Claude Design substrate patch failed:", error);
      vscode15.window.showWarningMessage(`Claude Design substrate patch failed: ${String(error)}`);
    }
  }
  const cli = new CliInference(cliPath);
  const adapter = makeAdapter(cli);
  const broker = new FsBroker(context);
  const root = vscode15.workspace.workspaceFolders?.[0]?.uri;
  if (!root) {
    vscode15.window.showInformationMessage("Claude Design: open a folder to use the Scriptorium.");
  }
  const marginaliaStore = root ? new MarginaliaStore(root) : new MarginaliaStore(vscode15.Uri.file(context.globalStorageUri.fsPath));
  const scribe = new ColophonScribe(marginaliaStore);
  const rune = new Rune;
  context.subscriptions.push(rune);
  broker.onDidWrite((ev) => {
    if (ev.path.startsWith("designs/")) {
      scribe.stamp({ leaf: ev.path, bytes: ev.bytes });
    }
  });
  await ensureManifest();
  context.subscriptions.push(watchManifest(() => {}));
  registerFocusBridge(context);
  context.subscriptions.push(vscode15.commands.registerCommand("claudeDesign.marginalia.focus", (leaf) => {
    return marginaliaView.show(leaf);
  }));
  const constellationView = new ConstellationView(context);
  const marginaliaView = new MarginaliaView(context, marginaliaStore, adapter);
  const vivariumView = new VivariumView(context);
  const chatPanel = new ChatPanel(context, broker, cliPath);
  const bestiary = new BestiaryProvider(context);
  context.subscriptions.push(vscode15.window.registerWebviewViewProvider(ConstellationView.viewType, constellationView), vscode15.window.registerWebviewViewProvider(MarginaliaView.viewType, marginaliaView), vscode15.window.registerWebviewViewProvider(VivariumView.viewType, vivariumView), vscode15.window.registerWebviewViewProvider(ChatPanel.viewType, chatPanel), vscode15.window.registerTreeDataProvider("claudeDesign.bestiary", bestiary));
  context.subscriptions.push(focusBridge.onDidFocus((leaf) => {
    constellationView.brighten?.(leaf);
  }));
  context.subscriptions.push(vscode15.commands.registerCommand("claudeDesign.signIn", () => {
    const term = vscode15.window.createTerminal("Claude Design — sign in");
    term.sendText(`${quoteCommand(cliPath)} auth login`);
    term.show();
  }), vscode15.commands.registerCommand("claudeDesign.focusChat", () => {
    return vscode15.commands.executeCommand("claudeDesign.chat.focus");
  }), vscode15.commands.registerCommand("claudeDesign.selfTest", () => runSelfTest(context)), vscode15.commands.registerCommand("claudeDesign.toggleHand", () => {
    marginaliaView.cycleHand();
    rune.call("hand cycled");
    setTimeout(() => rune.rest(), 1200);
  }), vscode15.commands.registerCommand("claudeDesign.enableSubstrate", async () => {
    await vscode15.workspace.getConfiguration("claudeDesign").update("substrate.enabled", true, vscode15.ConfigurationTarget.Global);
    const result = await enableSubstrate(context);
    vscode15.window.showInformationMessage(result?.changed ? "Claude Design: substrate enabled. Reload VS Code Insiders." : "Claude Design: substrate already enabled.");
  }), vscode15.commands.registerCommand("claudeDesign.disableSubstrate", async () => {
    await vscode15.workspace.getConfiguration("claudeDesign").update("substrate.enabled", false, vscode15.ConfigurationTarget.Global);
    const result = await disableSubstrate();
    vscode15.window.showInformationMessage(result?.changed ? "Claude Design: substrate markers removed. Reload VS Code Insiders." : "Claude Design: no substrate markers found.");
  }));
  const snap = await rehydrate();
  if (snap?.lastTouched?.file) {
    const folders = vscode15.workspace.workspaceFolders;
    if (folders?.length) {
      const uri = vscode15.Uri.joinPath(folders[0].uri, snap.lastTouched.file);
      try {
        const doc = await vscode15.workspace.openTextDocument(uri);
        await vscode15.window.showTextDocument(doc, { preview: true, preserveFocus: true });
      } catch {}
    }
  }
  context.subscriptions.push({
    dispose: () => {
      const editor = vscode15.window.activeTextEditor;
      const snap2 = {
        lastTouched: {
          file: editor ? designLeafPath(editor.document.uri)?.path : undefined,
          line: editor?.selection.active.line,
          when: new Date().toISOString()
        },
        openVivaria: vscode15.window.visibleTextEditors.map((e) => designLeafPath(e.document.uri)?.path).filter((p) => Boolean(p))
      };
      hibernate(snap2);
    }
  });
  context.subscriptions.push({ dispose: () => cli.dispose() });
  rune.setLabel("Design");
  rune.setTooltip("Claude Design — Scriptorium open");
}
function deactivate() {}
function quoteCommand(command) {
  return /\s/.test(command) ? `"${command.replace(/"/g, '`"')}"` : command;
}
export {
  deactivate,
  activate
};
