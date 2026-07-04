import * as fs from 'node:fs';
import * as path from 'node:path';
import { pathToFileURL } from 'node:url';
import * as vscode from 'vscode';

const MAIN_BEGIN = '/* claudeDesign.substrate.main.begin */';
const MAIN_END = '/* claudeDesign.substrate.main.end */';
const CSS_BEGIN = '<!-- claudeDesign.substrate.css.begin -->';
const CSS_END = '<!-- claudeDesign.substrate.css.end -->';
const CSS_FILENAME = 'vibrancy-obsidian.css';

export interface SubstrateResult {
  changed: boolean;
  appRoot: string;
  mainJs: string;
  workbenchHtml: string;
  cssPath?: string;
}

export async function enableSubstrate(context: vscode.ExtensionContext): Promise<SubstrateResult | undefined> {
  const cssPath = resolveCssPath(context);
  if (!cssPath) {
    console.warn(`Claude Design substrate: ${CSS_FILENAME} not found; skipping install patch.`);
    return undefined;
  }

  const install = locateInstall();
  let changed = false;
  changed = patchMainJs(install.mainJs) || changed;
  changed = patchWorkbenchHtml(install.workbenchHtml, cssPath) || changed;
  return { changed, cssPath, ...install };
}

export async function disableSubstrate(): Promise<SubstrateResult | undefined> {
  const install = locateInstall();
  let changed = false;
  changed = stripMainJs(install.mainJs) || changed;
  changed = stripWorkbenchHtml(install.workbenchHtml) || changed;
  return { changed, ...install };
}

function resolveCssPath(context: vscode.ExtensionContext): string | undefined {
  const configured = vscode.workspace
    .getConfiguration('claudeDesign')
    .get<string>('substrateCssPath', '')
    .trim();

  const candidates = [
    configured,
    ...((vscode.workspace.workspaceFolders ?? []).map(folder =>
      path.join(folder.uri.fsPath, 'designs', CSS_FILENAME)
    )),
    path.join(context.extensionPath, 'media', CSS_FILENAME),
  ].filter(Boolean);

  return candidates.find(candidate => path.isAbsolute(candidate) && isFile(candidate));
}

function locateInstall() {
  const appRoot = findAppRoot(process.execPath);
  const mainJs = path.join(appRoot, 'out', 'main.js');
  if (!isFile(mainJs)) {
    throw new Error(`VS Code main.js not found under ${appRoot}`);
  }

  const workbenchHtml = findWorkbenchHtml(appRoot);
  return { appRoot, mainJs, workbenchHtml };
}

function findAppRoot(execPath: string): string {
  const start = isFile(execPath) ? path.dirname(execPath) : execPath;
  const seen = new Set<string>();

  for (let dir = start; ; dir = path.dirname(dir)) {
    for (const candidate of appRootCandidates(dir)) {
      const normalized = path.normalize(candidate);
      if (seen.has(normalized)) continue;
      seen.add(normalized);
      if (isDirectory(normalized) && isFile(path.join(normalized, 'out', 'main.js'))) {
        return normalized;
      }
    }

    const parent = path.dirname(dir);
    if (parent === dir) break;
  }

  throw new Error(`Could not locate VS Code resources/app from ${execPath}`);
}

function appRootCandidates(dir: string): string[] {
  const direct = path.join(dir, 'resources', 'app');
  const candidates = [direct];

  try {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      if (entry.isDirectory()) {
        candidates.push(path.join(dir, entry.name, 'resources', 'app'));
      }
    }
  } catch {
    // Some parent directories are not readable; they are irrelevant here.
  }

  return candidates;
}

function findWorkbenchHtml(appRoot: string): string {
  const candidates = [
    path.join(appRoot, 'out', 'vs', 'code', 'electron-sandbox', 'workbench', 'workbench.esm.html'),
    path.join(appRoot, 'out', 'vs', 'code', 'electron-sandbox', 'workbench', 'workbench.html'),
    path.join(appRoot, 'out', 'vs', 'code', 'electron-browser', 'workbench', 'workbench.esm.html'),
    path.join(appRoot, 'out', 'vs', 'code', 'electron-browser', 'workbench', 'workbench.html'),
  ];

  const known = candidates.find(isFile);
  if (known) return known;

  const fallbackRoot = path.join(appRoot, 'out', 'vs', 'code');
  const found = findFirst(fallbackRoot, file => /^workbench.*\.html$/i.test(path.basename(file)));
  if (found) return found;

  throw new Error(`VS Code workbench HTML not found under ${appRoot}`);
}

function patchMainJs(mainJs: string): boolean {
  const original = fs.readFileSync(mainJs, 'utf8');
  const stripped = stripMainMarkers(original);
  const markerBlock = `${MAIN_BEGIN},(()=>{try{const browserWindow=this._win;browserWindow.setBackgroundMaterial?.("mica")}catch{}})()${MAIN_END}`;

  const exactNeedle = 'this._win=new vn.BrowserWindow(Je)';
  let patched: string;
  if (stripped.includes(exactNeedle)) {
    patched = stripped.replace(exactNeedle, `${exactNeedle}${markerBlock}`);
  } else {
    patched = stripped.replace(
      /(this\._win=new [A-Za-z_$][\w$]*\.BrowserWindow\([^)]*\))/,
      `$1${markerBlock}`
    );
  }

  if (patched === stripped || !patched.includes(MAIN_BEGIN)) {
    throw new Error(`Could not patch BrowserWindow creation in ${mainJs}`);
  }

  if (patched === original) return false;
  fs.writeFileSync(mainJs, patched, 'utf8');
  return true;
}

function stripMainJs(mainJs: string): boolean {
  const original = fs.readFileSync(mainJs, 'utf8');
  const stripped = stripMainMarkers(original);
  if (stripped === original) return false;
  fs.writeFileSync(mainJs, stripped, 'utf8');
  return true;
}

function patchWorkbenchHtml(workbenchHtml: string, cssPath: string): boolean {
  const original = fs.readFileSync(workbenchHtml, 'utf8');
  let patched = stripCssMarkers(original);
  patched = ensureStyleSrcFile(patched);

  const cssHref = escapeHtml(pathToFileURL(cssPath).href);
  const block = [
    '',
    `\t\t${CSS_BEGIN}`,
    `\t\t<link rel="stylesheet" data-claude-design-substrate="vibrancy-obsidian" href="${cssHref}">`,
    `\t\t${CSS_END}`,
  ].join('\n');

  patched = patched.replace(/\n\s*<\/head>/i, `${block}\n\t</head>`);
  if (patched === original) return false;
  if (!patched.includes(CSS_BEGIN)) {
    throw new Error(`Could not inject substrate CSS into ${workbenchHtml}`);
  }
  fs.writeFileSync(workbenchHtml, patched, 'utf8');
  return true;
}

function stripWorkbenchHtml(workbenchHtml: string): boolean {
  const original = fs.readFileSync(workbenchHtml, 'utf8');
  let stripped = stripCssMarkers(original);
  stripped = removeStyleSrcFile(stripped);
  if (stripped === original) return false;
  fs.writeFileSync(workbenchHtml, stripped, 'utf8');
  return true;
}

function stripMainMarkers(value: string): string {
  return value.replace(new RegExp(escapeRegExp(MAIN_BEGIN) + '[\\s\\S]*?' + escapeRegExp(MAIN_END), 'g'), '');
}

function stripCssMarkers(value: string): string {
  return value.replace(new RegExp('\\n?\\s*' + escapeRegExp(CSS_BEGIN) + '[\\s\\S]*?' + escapeRegExp(CSS_END), 'g'), '');
}

function ensureStyleSrcFile(value: string): string {
  return value.replace(/(style-src[\s\S]*?)(\s*;)/i, (match, body: string, end: string) => {
    if (/\bfile:/.test(body)) return match;
    return `${body}\n\t\t\t\t\tfile:${end}`;
  });
}

function removeStyleSrcFile(value: string): string {
  return value.replace(/(style-src[\s\S]*?)(\s*;)/i, (match, body: string, end: string) => {
    return `${body.replace(/\s*file:/g, '')}${end}`;
  });
}

function findFirst(root: string, predicate: (file: string) => boolean): string | undefined {
  const stack = [root];
  while (stack.length) {
    const current = stack.pop()!;
    let entries: fs.Dirent[];
    try {
      entries = fs.readdirSync(current, { withFileTypes: true });
    } catch {
      continue;
    }
    for (const entry of entries) {
      const next = path.join(current, entry.name);
      if (entry.isDirectory()) stack.push(next);
      else if (entry.isFile() && predicate(next)) return next;
    }
  }
  return undefined;
}

function isFile(candidate: string): boolean {
  try {
    return fs.statSync(candidate).isFile();
  } catch {
    return false;
  }
}

function isDirectory(candidate: string): boolean {
  try {
    return fs.statSync(candidate).isDirectory();
  } catch {
    return false;
  }
}

function escapeHtml(value: string): string {
  return value.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;');
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}
