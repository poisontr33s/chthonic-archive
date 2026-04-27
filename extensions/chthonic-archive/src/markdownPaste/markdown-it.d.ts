declare module 'markdown-it' {
    type RenderOptions = {
        html?: boolean;
        linkify?: boolean;
        typographer?: boolean;
    };

    class MarkdownIt {
        constructor(options?: RenderOptions);
        render(markdown: string): string;
    }

    export = MarkdownIt;
}
