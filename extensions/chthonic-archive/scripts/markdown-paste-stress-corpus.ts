import MarkdownIt = require('markdown-it');
import { htmlToMarkdown } from '../src/markdownPaste/convert';

const corpusPath = '../../.claude/skills/markdown-bridge/fixtures/outbound/stress_corpus_v1.md';
const source = await Bun.file(corpusPath).text();
const renderedHtml = new MarkdownIt({ html: true, linkify: true, typographer: false }).render(source);
const converted = htmlToMarkdown(renderedHtml);

const requiredSubstrings = [
    '# Markdown Bridge — Outbound Stress Corpus v1',
    '| Lane | Status | Owner |',
    '| `loader_truth/cuda_driver` | L0–L1 | `Fiddle.dlopen("nvcuda.dll")` | `blocked` |',
    '```python\ndef htmlToMarkdown(node):',
    '```powershell\n$ext = "$env:USERPROFILE\\.vscode-insiders\\extensions\\anthropic.claude-code-2.1.120-win32-x64"',
    '```json\n{\n  "artifact_type": "impossible_currently_boundary"',
    '```yaml\nmarkdown_bridge:',
    '```mermaid\ngraph LR',
    '```dot\ndigraph triad',
    '````markdown\nThis block is wrapped in four backticks',
    '```python\nprint("hello from inside a literal markdown sample")\n```',
    '> Single-level blockquote with **bold** and a [link](https://example.com) and `inline code`.',
    '> ```js\n> const reverseEngineer = (rendered) => sourceCache.get(rendered.id) ?? null;\n> ```',
    '[chthonic-archive](https://example.com/chthonic)',
    '[hover me](https://example.com "title attribute text")',
    'Press <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>P</kbd> to open the palette.',
    '<details>',
    '| `paste_inbound/callable` | `for(let F of D.allComms)F.send(...)` | webview receives request | `D.send is not a function` |',
    'End of corpus.',
];

const checks: Array<[string, boolean]> = [
    ['ATX headings survive', converted.includes(requiredSubstrings[0])],
    ['GFM tables survive', converted.includes(requiredSubstrings[1])],
    ['wide inline-code table survives', converted.includes(requiredSubstrings[2])],
    ['language-tagged code fences survive', ['python', 'powershell', 'json', 'yaml', 'mermaid', 'dot'].every((lang) => converted.includes(`\`\`\`${lang}`))],
    ['nested fence uses four-backtick outer fence', converted.includes(requiredSubstrings[9]) && converted.includes(requiredSubstrings[10])],
    ['blockquotes and quoted fences survive', converted.includes(requiredSubstrings[11]) && converted.includes(requiredSubstrings[12])],
    ['links and titles survive', converted.includes(requiredSubstrings[13]) && converted.includes(requiredSubstrings[14])],
    ['raw HTML inline/islands survive', converted.includes(requiredSubstrings[15]) && converted.includes(requiredSubstrings[16])],
    ['final boss table survives', converted.includes(requiredSubstrings[17])],
    ['corpus ending survives', converted.includes(requiredSubstrings[18])],
    ['no trailing whitespace remains', !converted.split('\n').some((line) => /[ \t]+$/u.test(line))],
    ['excessive blank lines collapsed', !/\n{3,}/u.test(converted)],
];

const missingRequired = requiredSubstrings.filter((snippet) => !converted.includes(snippet));
const failedChecks = checks.filter(([, passed]) => !passed);

if (missingRequired.length > 0 || failedChecks.length > 0) {
    console.error('Markdown paste stress corpus benchmark failed.');
    for (const [name] of failedChecks) {
        console.error(`- ${name}`);
    }
    if (missingRequired.length > 0) {
        console.error('Missing required snippets:');
        for (const snippet of missingRequired) {
            console.error(`---\n${snippet}`);
        }
    }
    process.exit(1);
}

console.log(`Markdown paste stress corpus survived (${source.length} source chars -> ${renderedHtml.length} html chars -> ${converted.length} markdown chars).`);
