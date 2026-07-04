/**
 * Marginalia — per-leaf conversation storage.
 *
 * Each leaf (file under designs/**) accretes its own marginalia at
 *   .scriptorium/marginalia/<leaf-path>.md
 *
 * The marginalia file is append-only and human-readable: a markdown
 * document of rubrics (written by the master), gloss (written by the
 * scribe), and colophons (signed records of file writes). It travels
 * with the leaf, can be committed, and is read back on the next sitting
 * so continuity is recovered without round-tripping through a database.
 *
 * On-disk format:
 *
 *   # Marginalia
 *
 *   ## ❦ rubric · 2025-04-12T14:22:11.000Z · master
 *
 *   Make the hero feel less corporate.
 *
 *   ## ¶ gloss · 2025-04-12T14:22:38.000Z · scribe
 *
 *   Swapped to serif italic; CTA pill in graphite.
 *
 *   ## ⌘ colophon · 2025-04-12T14:22:39.000Z · scribe
 *
 *   — designs/Landing.html · 1432 bytes · sha1:ab12cd…
 *
 * Sigils are part of the format. They are not decorative — the parser
 * uses them as section boundaries.
 */

import * as vscode from 'vscode';
import * as path from 'path';

export type MarginalKind = 'rubric' | 'gloss' | 'colophon';
export type Hand = 'master' | 'scribe' | 'system';

export interface Colophon {
  path: string;
  bytes: number;
  sig: string;
}

export interface MarginalEntry {
  timestamp: Date;
  kind: MarginalKind;
  hand: Hand;
  text: string;
  colophon?: Colophon;
}

export interface Leaf {
  /** Workspace-relative path of the leaf, e.g. designs/Landing.html */
  path: string;
  /** Workspace-relative path of the marginalia file. */
  marginaliaPath: string;
  entries: MarginalEntry[];
}

const MARGINALIA_DIR = '.scriptorium/marginalia';
const SIGIL = { rubric: '❦', gloss: '¶', colophon: '⌘' } as const;

function leafToMarginaliaPath(leafPath: string): string {
  return path.posix.join(MARGINALIA_DIR, leafPath + '.md');
}

function marginaliaToLeafPath(marginaliaPath: string): string {
  const rel = path.posix.relative(MARGINALIA_DIR, marginaliaPath);
  return rel.replace(/\.md$/, '');
}

export class MarginaliaStore {
  constructor(private workspaceRoot: vscode.Uri) {}

  private uri(relativePath: string): vscode.Uri {
    return vscode.Uri.joinPath(this.workspaceRoot, relativePath);
  }

  async load(leafPath: string): Promise<Leaf> {
    const marginaliaPath = leafToMarginaliaPath(leafPath);
    const uri = this.uri(marginaliaPath);
    let raw = '';
    try {
      const bytes = await vscode.workspace.fs.readFile(uri);
      raw = new TextDecoder().decode(bytes);
    } catch {
      // no marginalia yet — that's fine
    }
    return { path: leafPath, marginaliaPath, entries: parseMarginalia(raw) };
  }

  async append(leafPath: string, entry: MarginalEntry): Promise<void> {
    const marginaliaPath = leafToMarginaliaPath(leafPath);
    const uri = this.uri(marginaliaPath);
    try {
      await vscode.workspace.fs.createDirectory(vscode.Uri.joinPath(uri, '..'));
    } catch {
      /* dir may already exist */
    }
    const leaf = await this.load(leafPath);
    leaf.entries.push(entry);
    const serialized = serializeMarginalia(leaf.entries);
    await vscode.workspace.fs.writeFile(uri, new TextEncoder().encode(serialized));
  }

  async list(): Promise<string[]> {
    const root = this.uri(MARGINALIA_DIR);
    const out: string[] = [];
    const walk = async (dir: vscode.Uri, prefix: string) => {
      let entries: [string, vscode.FileType][];
      try {
        entries = await vscode.workspace.fs.readDirectory(dir);
      } catch {
        return;
      }
      for (const [name, kind] of entries) {
        const next = prefix ? `${prefix}/${name}` : name;
        if (kind === vscode.FileType.Directory) {
          await walk(vscode.Uri.joinPath(dir, name), next);
        } else if (kind === vscode.FileType.File && name.endsWith('.md')) {
          out.push(marginaliaToLeafPath(path.posix.join(MARGINALIA_DIR, next)));
        }
      }
    };
    await walk(root, '');
    return out;
  }
}

/* ---------- serialization ---------- */

function serializeMarginalia(entries: MarginalEntry[]): string {
  const head = '# Marginalia\n\n';
  return head + entries.map(serializeEntry).join('\n');
}

function serializeEntry(e: MarginalEntry): string {
  const header = `## ${SIGIL[e.kind]} ${e.kind} · ${e.timestamp.toISOString()} · ${e.hand}\n\n`;
  if (e.kind === 'colophon' && e.colophon) {
    return header + `— ${e.colophon.path} · ${e.colophon.bytes} bytes · ${e.colophon.sig}\n`;
  }
  return header + e.text.trim() + '\n';
}

const ENTRY_RE = /^## (?:❦|¶|⌘)\s+(rubric|gloss|colophon)\s+·\s+(\S+)\s+·\s+(master|scribe|system)\s*$/;
const COLOPHON_RE = /^—\s+(\S+)\s+·\s+(\d+)\s+bytes\s+·\s+(.+)$/;

function parseMarginalia(raw: string): MarginalEntry[] {
  if (!raw.trim()) return [];
  const lines = raw.split(/\r?\n/);
  const entries: MarginalEntry[] = [];
  let current: Partial<MarginalEntry> | null = null;
  let buffer: string[] = [];

  const flush = () => {
    if (!current || !current.kind || !current.hand || !current.timestamp) return;
    const text = buffer.join('\n').trim();
    let colophon: Colophon | undefined;
    if (current.kind === 'colophon') {
      const m = text.match(COLOPHON_RE);
      if (m) colophon = { path: m[1], bytes: parseInt(m[2], 10), sig: m[3].trim() };
    }
    entries.push({
      kind: current.kind,
      hand: current.hand,
      timestamp: current.timestamp,
      text,
      colophon,
    });
    current = null;
    buffer = [];
  };

  for (const line of lines) {
    const m = line.match(ENTRY_RE);
    if (m) {
      flush();
      current = {
        kind: m[1] as MarginalKind,
        timestamp: new Date(m[2]),
        hand: m[3] as Hand,
      };
      buffer = [];
    } else if (current) {
      buffer.push(line);
    }
  }
  flush();
  return entries;
}
