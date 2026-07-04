// src/scriptorium/session.ts
//
// Hibernate, not close. The workspace state — open files, scroll positions,
// draft messages, last conversation turn — saves to a single markdown file
// at .scriptorium/session.md. Reopening rehydrates. Handing the file to
// another scriptorium installs the session there.
//
// The format is intentionally markdown — readable by a human, diffable in
// git, portable across machines because portable across humans.

import * as vscode from 'vscode';

export interface SessionSnapshot {
  lastTouched: {
    file?: string;
    line?: number;
    when: string;
  };
  draftMessage?: string;
  openVivaria: string[];
  conversationTail?: string; // last user/assistant exchange, freeform
}

const SESSION_DIR = '.scriptorium';
const SESSION_FILE = 'session.md';

function sessionUri(): vscode.Uri | undefined {
  const root = vscode.workspace.workspaceFolders?.[0];
  if (!root) return undefined;
  return vscode.Uri.joinPath(root.uri, SESSION_DIR, SESSION_FILE);
}

export async function hibernate(snap: SessionSnapshot): Promise<void> {
  const uri = sessionUri();
  if (!uri) return;
  const dir = vscode.Uri.joinPath(uri, '..');
  try { await vscode.workspace.fs.createDirectory(dir); } catch {}

  const lines: string[] = [];
  lines.push('# .scriptorium/session.md');
  lines.push('');
  lines.push('## Last touched');
  if (snap.lastTouched.file) lines.push(`- file:   ${snap.lastTouched.file}`);
  if (snap.lastTouched.line != null) lines.push(`- line:   ${snap.lastTouched.line}`);
  lines.push(`- when:   ${snap.lastTouched.when}`);
  lines.push('');

  if (snap.draftMessage) {
    lines.push('## Draft message');
    for (const l of snap.draftMessage.split('\n')) lines.push(`> ${l}`);
    lines.push('');
  }

  lines.push('## Open vivaria');
  for (const f of snap.openVivaria) lines.push(`- ${f}`);
  lines.push('');

  if (snap.conversationTail) {
    lines.push('## Conversation tail');
    lines.push('');
    lines.push(snap.conversationTail);
    lines.push('');
  }

  await vscode.workspace.fs.writeFile(uri, new TextEncoder().encode(lines.join('\n')));
}

export async function rehydrate(): Promise<SessionSnapshot | undefined> {
  const uri = sessionUri();
  if (!uri) return undefined;
  let raw: string;
  try {
    const bytes = await vscode.workspace.fs.readFile(uri);
    raw = new TextDecoder().decode(bytes);
  } catch {
    return undefined;
  }

  // Forgiving parser: section → key/value or list.
  const snap: SessionSnapshot = {
    lastTouched: { when: '' },
    openVivaria: [],
  };

  const sections = raw.split(/^##\s+/m).slice(1);
  for (const sec of sections) {
    const [title, ...rest] = sec.split('\n');
    const body = rest.join('\n');

    if (/last touched/i.test(title)) {
      for (const m of body.matchAll(/^- (\w+):\s*(.+)$/gm)) {
        const k = m[1], v = m[2].trim();
        if (k === 'file') snap.lastTouched.file = v;
        else if (k === 'line') snap.lastTouched.line = Number(v);
        else if (k === 'when') snap.lastTouched.when = v;
      }
    } else if (/draft message/i.test(title)) {
      const draft = body.replace(/^>\s?/gm, '').trim();
      if (draft) snap.draftMessage = draft;
    } else if (/open vivaria/i.test(title)) {
      for (const m of body.matchAll(/^- (.+)$/gm)) snap.openVivaria.push(m[1].trim());
    } else if (/conversation tail/i.test(title)) {
      snap.conversationTail = body.trim();
    }
  }

  return snap;
}
