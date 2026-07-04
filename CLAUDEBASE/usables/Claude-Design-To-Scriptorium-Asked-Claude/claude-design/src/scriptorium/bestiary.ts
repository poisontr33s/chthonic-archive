// src/scriptorium/bestiary.ts
//
// The bestiary reformulation of the Self-Test. Same probe data, drawn.
// Each unknown surface is a creature with a name and a sighting status.
// As Anthropic ships the surfaces, the creatures shift from "never observed"
// to "documented."
//
// The bestiary is rendered into a markdown document that opens in a new
// editor tab — same delivery as the original Self-Test, different content.

export type Sighting = 'documented' | 'partial' | 'rumored' | 'never';

export interface Creature {
  sigil: string;
  name: string;
  latin: string;
  sighting: Sighting;
  description: string;
  probe?: () => Promise<{ found: boolean; detail?: string }>;
}

export const BESTIARY: Creature[] = [
  {
    sigil: '⌬',
    name: 'The Quota Spectrometer',
    latin: 'Metrum designi separatum',
    sighting: 'rumored',
    description:
      'Reportedly meters Claude Design usage independently of chat and Claude Code allowances. ' +
      'Its API surface has not been sighted. Until it is, the rune in the status bar shows a soft pulse rather than a percentage.',
  },
  {
    sigil: '↺',
    name: 'The Lossless Teleport',
    latin: 'Migratio sessionis',
    sighting: 'never',
    description:
      'A surface that would carry a server-side claude.ai session into a local editor without loss of artifact or thread. ' +
      'The Scriptorium imports dropped export files in the interim.',
  },
  {
    sigil: '⚯',
    name: 'The Claude Code Exports',
    latin: 'Interfacium ad alter extensio',
    sighting: 'partial',
    description:
      'The companion extension may, in some versions, expose a public API on its activate() return. ' +
      'When present, the Scriptorium routes inference through it instead of a subprocess.',
  },
  {
    sigil: '☖',
    name: 'The Editable Workspace Provider',
    latin: 'Fons sancti scripti',
    sighting: 'documented',
    description:
      'VS Code\'s FileSystemProvider API, used to mount design-system folders read-only via canvas-ds:// scheme. ' +
      'Verified present in 1.97+.',
  },
  {
    sigil: '☷',
    name: 'The Webview Theme Bridge',
    latin: 'Varietates colorum',
    sighting: 'documented',
    description:
      'The --vscode-* CSS variables injected into every webview. The Scriptorium\'s chrome reads these directly; ' +
      'theme switches at the editor level recolor the extension in place.',
  },
];

export function bestiaryAsMarkdown(creatures: Creature[]): string {
  const lines: string[] = [];
  lines.push('# Scriptorium Bestiary');
  lines.push('');
  lines.push('*Probe report. Each entry is a surface the extension cooperates with or hopes to.*');
  lines.push('');

  for (const c of creatures) {
    lines.push(`## ${c.sigil}  ${c.name}`);
    lines.push(`*${c.latin}*`);
    lines.push('');
    lines.push(`**Sighting:** ${sightingLabel(c.sighting)}`);
    lines.push('');
    lines.push(c.description);
    lines.push('');
    lines.push('---');
    lines.push('');
  }

  lines.push(`*${creatures.length} entries. Bestiary updates as surfaces ship.*`);
  return lines.join('\n');
}

function sightingLabel(s: Sighting): string {
  switch (s) {
    case 'documented': return 'documented · in active use';
    case 'partial':    return 'partially documented';
    case 'rumored':    return 'rumored · awaiting public surface';
    case 'never':      return 'never observed in the wild';
  }
}

/* ------------------------------------------------------------------ */
/*  BestiaryProvider — the tree contribution the activator registers.  */
/*  Renders each creature as a tree item; clicking opens the markdown  */
/*  bestiary in a new editor tab.                                      */
/* ------------------------------------------------------------------ */

import * as vscode from 'vscode';

export class BestiaryProvider implements vscode.TreeDataProvider<Creature> {
  private _onDidChange = new vscode.EventEmitter<void>();
  readonly onDidChangeTreeData = this._onDidChange.event;

  constructor(private ctx: vscode.ExtensionContext) {
    ctx.subscriptions.push(
      vscode.commands.registerCommand('claudeDesign.openBestiary', async () => {
        const doc = await vscode.workspace.openTextDocument({
          language: 'markdown',
          content: bestiaryAsMarkdown(BESTIARY),
        });
        await vscode.window.showTextDocument(doc, { preview: false });
      })
    );
  }

  refresh() { this._onDidChange.fire(); }

  getTreeItem(c: Creature): vscode.TreeItem {
    const item = new vscode.TreeItem(`${c.sigil}  ${c.name}`, vscode.TreeItemCollapsibleState.None);
    item.description = sightingLabel(c.sighting);
    item.tooltip = c.description;
    item.iconPath = new vscode.ThemeIcon(
      c.sighting === 'documented' ? 'pass'
      : c.sighting === 'partial' ? 'circle-large-outline'
      : c.sighting === 'rumored' ? 'question'
      : 'circle-slash'
    );
    item.command = { command: 'claudeDesign.openBestiary', title: 'Open Bestiary' };
    return item;
  }

  getChildren(): Creature[] { return BESTIARY; }
}
