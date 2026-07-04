// src/scriptorium/manifest.ts
//
// The asset ledger lives at `designs.md` in the workspace root.
// Human and machine read the same file. No JSON, no .canvas/ folder.
// If the extension is uninstalled, the document still works.
//
// Format (loose, the parser is forgiving):
//
//   ## <Group name>
//   - [x] <Asset name>   · approved · 2026-04-12
//   - [ ] <Asset name>   · needs review
//   - [ ] <Asset name>   · changes requested · note text
//
// The parser walks line by line. Headings (##) start groups.
// Each `- [ ]` or `- [x]` line is an entry. Status is inferred
// from the checkbox + the trailing tag after the first `·`.

import * as vscode from 'vscode';

export type AssetStatus = 'needs-review' | 'approved' | 'changes-requested';

export interface AssetEntry {
  name: string;
  group: string;
  status: AssetStatus;
  note?: string;
  date?: string;
  // Source line index in designs.md, for in-place editing.
  line: number;
}

export interface Manifest {
  uri: vscode.Uri;
  entries: AssetEntry[];
  raw: string;
}

const MANIFEST_FILENAME = 'designs.md';

const STATUS_TAGS: Record<string, AssetStatus> = {
  'approved': 'approved',
  'needs review': 'needs-review',
  'changes requested': 'changes-requested',
};

function manifestUri(): vscode.Uri | undefined {
  const root = vscode.workspace.workspaceFolders?.[0];
  if (!root) return undefined;
  return vscode.Uri.joinPath(root.uri, MANIFEST_FILENAME);
}

export async function readManifest(): Promise<Manifest | undefined> {
  const uri = manifestUri();
  if (!uri) return undefined;
  let raw: string;
  try {
    const bytes = await vscode.workspace.fs.readFile(uri);
    raw = new TextDecoder().decode(bytes);
  } catch {
    return { uri, entries: [], raw: '' };
  }

  const lines = raw.split(/\r?\n/);
  let group = 'Unsorted';
  const entries: AssetEntry[] = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const h = line.match(/^##\s+(.+?)\s*$/);
    if (h) { group = h[1]; continue; }

    const item = line.match(/^- \[( |x|X)\]\s+(.+?)\s*$/);
    if (!item) continue;
    const checked = item[1].toLowerCase() === 'x';
    const rest = item[2];

    const parts = rest.split('·').map(s => s.trim());
    const name = parts[0];
    let status: AssetStatus = checked ? 'approved' : 'needs-review';
    let note: string | undefined;
    let date: string | undefined;

    for (const tag of parts.slice(1)) {
      const lower = tag.toLowerCase();
      if (STATUS_TAGS[lower]) { status = STATUS_TAGS[lower]; continue; }
      // ISO-ish date
      if (/^\d{4}-\d{2}-\d{2}/.test(tag)) { date = tag; continue; }
      note = tag;
    }

    entries.push({ name, group, status, note, date, line: i });
  }

  return { uri, entries, raw };
}

export async function ensureManifest(): Promise<vscode.Uri | undefined> {
  const uri = manifestUri();
  if (!uri) return undefined;
  try {
    await vscode.workspace.fs.stat(uri);
  } catch {
    const seed = [
      '# designs.md',
      '',
      'The asset ledger for this workspace.',
      'Human and machine read this same file.',
      '',
      '## Pages',
      '',
      '## Components',
      '',
    ].join('\n');
    await vscode.workspace.fs.writeFile(uri, new TextEncoder().encode(seed));
  }
  return uri;
}

export async function setStatus(entry: AssetEntry, next: AssetStatus): Promise<void> {
  const uri = manifestUri();
  if (!uri) return;
  const bytes = await vscode.workspace.fs.readFile(uri);
  const raw = new TextDecoder().decode(bytes);
  const lines = raw.split(/\r?\n/);
  const original = lines[entry.line];
  if (!original) return;

  // Rewrite checkbox + the status tag if present, leave the rest.
  const box = next === 'approved' ? '[x]' : '[ ]';
  const head = original.match(/^(- )\[[ xX]\](\s+.+)$/);
  if (!head) return;
  let body = head[2];

  // Strip any existing known status tag.
  const segments = body.split('·').map(s => s.trim());
  const name = segments[0];
  const kept = segments.slice(1).filter(seg => {
    const lower = seg.toLowerCase();
    return !STATUS_TAGS[lower];
  });

  const statusTag = invertStatusTag(next);
  const rebuilt = ` ${name}` + [statusTag, ...kept].map(s => ` · ${s}`).join('');
  lines[entry.line] = `- ${box}${rebuilt}`;
  await vscode.workspace.fs.writeFile(uri, new TextEncoder().encode(lines.join('\n')));
}

function invertStatusTag(s: AssetStatus): string {
  if (s === 'approved') return 'approved';
  if (s === 'changes-requested') return 'changes requested';
  return 'needs review';
}

export function watchManifest(onChange: () => void): vscode.Disposable {
  const root = vscode.workspace.workspaceFolders?.[0];
  if (!root) return new vscode.Disposable(() => {});
  const watcher = vscode.workspace.createFileSystemWatcher(
    new vscode.RelativePattern(root, MANIFEST_FILENAME),
  );
  watcher.onDidChange(onChange);
  watcher.onDidCreate(onChange);
  watcher.onDidDelete(onChange);
  return watcher;
}
