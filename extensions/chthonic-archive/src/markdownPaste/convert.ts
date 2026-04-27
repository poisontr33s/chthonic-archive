import TurndownService from 'turndown';
import { gfm } from 'turndown-plugin-gfm';

const fence = '```';

type HtmlNodeLike = {
    nodeName: string;
    firstChild: HtmlNodeLike | null;
    textContent?: string | null;
    getAttribute?(name: string): string | null;
};

function languageFromCodeElement(node: HtmlNodeLike): string {
    const className = node.getAttribute?.('class') ?? '';
    const match = className.match(/(?:^|\s)(?:language|lang)-([A-Za-z0-9_+.#-]+)/);
    return match?.[1] ?? '';
}

function fenceForCode(text: string): string {
    const runs = text.match(/`{3,}/g) ?? [];
    const longest = runs.reduce((max, run) => Math.max(max, run.length), 2);
    return '`'.repeat(Math.max(3, longest + 1));
}

export function normalizeMarkdown(markdown: string): string {
    return markdown
        .replace(/\r\n?/g, '\n')
        .split('\n')
        .map((line) =>
            line
                .replace(/^(\s*[-+*]) {2,}/u, '$1 ')
                .replace(/^(\s*\d+\.) {2,}/u, '$1 ')
                .replace(/[ \t]+$/g, ''),
        )
        .join('\n')
        .replace(/\n{3,}/g, '\n\n')
        .trim()
        .concat('\n');
}

export function htmlToMarkdown(html: string): string {
    const turndown = new TurndownService({
        headingStyle: 'atx',
        codeBlockStyle: 'fenced',
        fence,
        bulletListMarker: '-',
        emDelimiter: '*',
        strongDelimiter: '**',
        linkStyle: 'inlined',
    });

    turndown.use(gfm);
    turndown.keep(['kbd', 'sub', 'sup', 'details', 'summary']);

    turndown.addRule('fencedCodeBlockWithLanguage', {
        filter(node) {
            return (
                node.nodeName === 'PRE'
                && node.firstChild !== null
                && node.firstChild.nodeName === 'CODE'
            );
        },
        replacement(_content, node) {
            const codeElement = node.firstChild as HtmlNodeLike;
            const language = languageFromCodeElement(codeElement);
            const text = codeElement.textContent?.replace(/\n$/u, '') ?? '';
            const codeFence = fenceForCode(text);
            return `\n\n${codeFence}${language}\n${text}\n${codeFence}\n\n`;
        },
    });

    return normalizeMarkdown(turndown.turndown(html));
}
