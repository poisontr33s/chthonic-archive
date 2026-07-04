// src/scriptorium/rune.ts
//
// The status bar carries a single glyph — a workspace rune.
// Color is reserved for permanent state. Motion is reserved for current state.
// When something wants attention, the rune slowly tilts. Not blinks.
//
// VS Code's StatusBarItem text does not support animation directly, so the
// "tilt" is rendered as a rotation among a small set of unicode glyphs that
// progressively lean — the eye reads it as motion at the cadence of a slow
// breath.

import * as vscode from 'vscode';

// Default rune. The workspace may set claudeDesign.rune to anything.
const DEFAULT_RUNE = '🜂';

// Tilt frames — same glyph in subtly rotated positions, achieved through
// combining diacritics. The viewer sees one character that breathes.
const TILT_FRAMES = ['', '\u0300', '\u0301', '\u0300']; // none, grave, acute, grave

export class Rune implements vscode.Disposable {
  private item: vscode.StatusBarItem;
  private timer: NodeJS.Timeout | undefined;
  private frame = 0;
  private attention = false;
  private glyph: string;

  constructor() {
    this.item = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    this.item.command = 'claudeDesign.runeAction';
    this.glyph = this.readGlyph();
    this.render();
    this.item.show();

    vscode.workspace.onDidChangeConfiguration(e => {
      if (e.affectsConfiguration('claudeDesign.rune')) {
        this.glyph = this.readGlyph();
        this.render();
      }
    });
  }

  private readGlyph(): string {
    return vscode.workspace.getConfiguration('claudeDesign').get<string>('rune', DEFAULT_RUNE);
  }

  /** Steady state: just the rune. */
  rest(): void {
    this.attention = false;
    this.stopTilt();
    this.frame = 0;
    this.render();
  }

  /** Wants attention. The rune begins to tilt slowly. */
  call(reason?: string): void {
    this.attention = true;
    if (reason) this.item.tooltip = reason;
    this.startTilt();
  }

  /** Critical/blocking state. Uses VS Code's warning color but does not blink. */
  block(reason: string): void {
    this.attention = true;
    this.item.tooltip = reason;
    this.item.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
    this.startTilt();
  }

  setTooltip(s: string): void { this.item.tooltip = s; }

  setLabel(s: string | undefined): void {
    this.label = s;
    this.render();
  }
  private label: string | undefined;

  private render(): void {
    const tilt = this.attention ? TILT_FRAMES[this.frame % TILT_FRAMES.length] : '';
    const g = this.glyph + tilt;
    this.item.text = this.label ? `${g}  ${this.label}` : g;
  }

  private startTilt(): void {
    if (this.timer) return;
    this.timer = setInterval(() => {
      this.frame = (this.frame + 1) % TILT_FRAMES.length;
      this.render();
    }, 1400);
  }

  private stopTilt(): void {
    if (!this.timer) return;
    clearInterval(this.timer);
    this.timer = undefined;
    this.item.backgroundColor = undefined;
  }

  dispose(): void {
    this.stopTilt();
    this.item.dispose();
  }
}
