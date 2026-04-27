import * as vscode from 'vscode';
import { htmlToMarkdown } from './convert';

const htmlMime = 'text/html';
const diagnostic = 'Clipboard did not include text/html; pasted source may only provide plain text.';

export function registerRenderedMarkdownPasteLane(
    context: vscode.ExtensionContext,
    output: vscode.OutputChannel,
): void {
    const kind = vscode.DocumentDropOrPasteEditKind.Text.append('markdown', 'renderedAiHtml');

    const htmlProvider = vscode.languages.registerDocumentPasteEditProvider(
        { language: 'markdown' },
        {
            async provideDocumentPasteEdits(_document, _ranges, dataTransfer, _context, token) {
                const htmlItem = dataTransfer.get(htmlMime);

                if (!htmlItem) {
                    void vscode.window.showInformationMessage(diagnostic);
                    return [];
                }

                const html = await htmlItem.asString();
                if (token.isCancellationRequested || html.trim().length === 0) {
                    return [];
                }

                const markdown = htmlToMarkdown(html);
                output.appendLine(`[markdown-paste] converted text/html clipboard payload (${html.length} html bytes -> ${markdown.length} markdown chars)`);
                return [
                    new vscode.DocumentPasteEdit(
                        markdown,
                        'Chthonic: Paste Rendered AI HTML as Markdown',
                        kind,
                    ),
                ];
            },
        },
        {
            providedPasteEditKinds: [kind],
            pasteMimeTypes: [htmlMime],
        },
    );

    const plainTextDiagnosticProvider = vscode.languages.registerDocumentPasteEditProvider(
        { language: 'markdown' },
        {
            provideDocumentPasteEdits(_document, _ranges, dataTransfer) {
                if (!dataTransfer.get(htmlMime)) {
                    void vscode.window.showInformationMessage(diagnostic);
                }

                return [];
            },
        },
        {
            providedPasteEditKinds: [kind],
            pasteMimeTypes: ['text/plain'],
        },
    );

    const pasteCommand = vscode.commands.registerCommand(
        'chthonic.pasteRenderedAiMarkdown',
        () => vscode.commands.executeCommand('editor.action.clipboardPasteAction'),
    );

    context.subscriptions.push(htmlProvider, plainTextDiagnosticProvider, pasteCommand);
    output.appendLine('[markdown-paste] rendered AI Markdown paste lane registered');
}
