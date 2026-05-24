#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: data_rewiring.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Data Rewiring - Identify scripts/docs for narrative-functional balance adjustment

@SID:           TOOL_DATA_REWIRING_V1
@Shabti:        CLI Script
@Purpose:       Data Rewiring - Identify scripts/docs for narrative-functional balance adjustment
"""

from __future__ import annotations

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


from pathlib import Path
import re

def iter_files(root: Path, rel_root: str):
    base = root / rel_root
    if not base.exists():
        return []
    return [p for p in base.rglob('*') if p.is_file()]

root = Path('.').resolve()
files = iter_files(root, 'scripts') + iter_files(root, 'docs')

emoji_re = re.compile(r'[\u2600-\u27BF\U0001F300-\U0001FAFF]')

narrative_keywords = [
    'sacred','mandala','myth','decorator','supremacy','hedonistic','ritual','blessing','oracle',
    'transcend','asc','axiom','sovereign','resurrection','void','chromatic','tesseract','eternal',
    'prismatic','ornamental','visual truth','fa⁵','fa5','fa4','milf','agents','triumvirate'
]
functional_keywords = [
    'def ','class ','import ','argparse','json','yaml','toml','read','write','path','validate','schema',
    'output','stdin','stdout','error','exit','return','cli','parser','config','report','metrics','test'
]

rows = []
for p in files:
    try:
        text = p.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        continue
    emoji_count = len(emoji_re.findall(text))
    narrative_hits = sum(text.lower().count(k) for k in narrative_keywords)
    functional_hits = sum(text.lower().count(k) for k in functional_keywords)

    if functional_hits >= 5 and narrative_hits <= 2 and emoji_count <= 2:
        cls = 'High Signal'
    elif narrative_hits >= 6 or emoji_count >= 10:
        cls = 'High Narrative'
    else:
        cls = 'Mixed'

    pros = []
    cons = []
    if functional_hits:
        pros.append('Functional markers present')
    if emoji_count <= 2:
        pros.append('Low emoji density')
    if narrative_hits <= 2:
        pros.append('Low narrative density')

    if emoji_count >= 5:
        cons.append('Emoji-heavy')
    if narrative_hits >= 4:
        cons.append('Narrative-heavy')
    if not functional_hits:
        cons.append('Low functional signal')

    rows.append({
        'path': str(p.relative_to(root)).replace('\\','/'),
        'emoji': emoji_count,
        'narr': narrative_hits,
        'func': functional_hits,
        'cls': cls,
        'pros': '; '.join(pros) if pros else '—',
        'cons': '; '.join(cons) if cons else '—'
    })

rows.sort(key=lambda r: (r['cls'], -r['narr'], -r['emoji'], -r['func'], r['path']))

report = []
report.append('# Classification State: scripts/ + docs/\n')
report.append('Generated via heuristic scan (emoji + narrative + functional markers).\n')
report.append('## Legend\n')
report.append('- **High Signal**: concrete, functional cues; minimal narrative overhead.\n')
report.append('- **Mixed**: functional cues present but narrative/emoji density elevated.\n')
report.append('- **High Narrative**: dominant narrative/emoji signaling; low functional cues.\n')

report.append('## File Classification (scripts/ + docs/)\n')
report.append('| File | Class | Emoji | Narrative | Functional | Pros | Cons |\n')
report.append('|---|---|---:|---:|---:|---|---|\n')
for r in rows:
    report.append(f"| {r['path']} | {r['cls']} | {r['emoji']} | {r['narr']} | {r['func']} | {r['pros']} | {r['cons']} |\n")

# Summaries
high_narr = [r for r in rows if r['cls'] == 'High Narrative']
high_signal = [r for r in rows if r['cls'] == 'High Signal']
report.append('\n## Summary\n')
report.append(f"- High Narrative: {len(high_narr)} files\n")
report.append(f"- High Signal: {len(high_signal)} files\n")
report.append(f"- Mixed: {len(rows) - len(high_narr) - len(high_signal)} files\n")

# Top candidates to rewire (scripts, high narrative)
rewire = [r for r in high_narr if r['path'].startswith('scripts/')]
rewire = rewire[:20]
report.append('\n## Top Rewire Candidates (scripts/)\n')
if rewire:
    for r in rewire:
        report.append(f"- {r['path']} (emoji={r['emoji']}, narr={r['narr']}, func={r['func']})\n")
else:
    report.append('- (none detected)\n')

out_path = root / 'docs' / 'CLASSIFICATION_STATE.md'
out_path.write_text(''.join(report), encoding='utf-8')
print(f'Wrote {out_path}')
