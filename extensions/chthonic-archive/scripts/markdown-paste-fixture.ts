import { htmlToMarkdown } from '../src/markdownPaste/convert';

const html = await Bun.file('fixtures/rendered-sample.html').text();
const expected = await Bun.file('fixtures/rendered-sample.md').text();
const actual = htmlToMarkdown(html);

if (actual !== expected) {
    console.error('Markdown paste fixture mismatch.');
    console.error('--- expected');
    console.error(expected);
    console.error('--- actual');
    console.error(actual);
    process.exit(1);
}

console.log('Markdown paste fixture matched expected Markdown.');
