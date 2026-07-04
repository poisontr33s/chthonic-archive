/**
 * Colophon — proof that a gloss was load-bearing.
 *
 * When the FS broker writes a leaf on behalf of the model, the
 * colophon function appends a signed-footer entry to that leaf's
 * marginalia file. The entry records: what was written, when, by
 * which hand, and (if a marginalia turn was the proximate cause) the
 * rubric that occasioned it. The gloss becomes a thing with weight —
 * it caused a change to the leaf, and the leaf's marginalia knows it.
 *
 * The colophon entry is markdown, not metadata. It reads as prose in
 * the marginalia file and parses as a sigil-bounded block on reload.
 *
 * Made by Claude.
 */

import * as vscode from 'vscode';
import { MarginaliaStore } from './marginalia';

export interface ColophonRecord {
  leaf: string;
  bytes: number;
  causedBy?: string;
  hand?: 'terse' | 'discursive' | 'diagrammatic';
}

export class ColophonScribe {
  constructor(private store: MarginaliaStore) {}

  async stamp(rec: ColophonRecord): Promise<void> {
    const ts = new Date().toISOString();
    const lines: string[] = [];
    lines.push('');
    lines.push('† colophon');
    lines.push(`  · written: ${rec.leaf}`);
    lines.push(`  · bytes:   ${rec.bytes}`);
    if (rec.hand) lines.push(`  · hand:    ${rec.hand}`);
    if (rec.causedBy) {
      const trimmed = rec.causedBy.length > 120
        ? rec.causedBy.slice(0, 117) + '…'
        : rec.causedBy;
      lines.push(`  · caused:  ${trimmed}`);
    }
    lines.push(`  · stamp:   ${ts}`);
    lines.push('');

    await this.store.appendRaw(rec.leaf, lines.join('\n'));
  }
}

/**
 * Wire into the FS broker. The broker emits an event after each
 * successful write; the scribe listens and stamps the relevant
 * marginalia file. The wire is one line in extension activation:
 *
 *   broker.onDidWrite(rec => scribe.stamp(rec));
 *
 * The broker must surface { leaf, bytes, causedBy?, hand? } in its
 * event payload. The marginaliaView, when streaming a gloss that
 * results in a tool_use write, passes the rubric text in as causedBy.
 */
