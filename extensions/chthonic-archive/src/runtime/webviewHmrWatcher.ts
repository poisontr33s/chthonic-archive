// @SID: EXT_RUNTIME_WEBVIEW_HMR_WATCHER_V1
import * as vscode from 'vscode';
import type { LaneRegistry } from './laneState';

const DEBOUNCE_MS = 250;

type HmrSurface = 'stylus' | 'loom' | 'ankh' | 'abyssal';

interface LoadedMessage {
    type: 'webviewHmr.loaded' | 'webviewHmr.reloadRequested';
    surface?: string;
    reloadCount?: number;
    html?: string;
}

interface ProbeRequest {
    surface: HmrSurface;
    marker: string;
    timeoutMs?: number;
}

interface ProbeResult {
    surface: HmrSurface;
    marker: string;
    reloadLatencyMs: number;
    reloadCount: number;
    watchEvents: number;
    windowReloadInvoked: false;
}

interface ProbeWaiter {
    request: ProbeRequest;
    startedAt: number;
    resolve: (result: ProbeResult) => void;
    reject: (error: Error) => void;
    timeout: ReturnType<typeof setTimeout>;
}

const trackedViews = new Map<string, Set<vscode.WebviewView>>();
const waiters: ProbeWaiter[] = [];

let registry: LaneRegistry | undefined;
let outputChannel: vscode.OutputChannel | undefined;
let watchEventCount = 0;
let reloadSequence = 0;
let debounceHandle: ReturnType<typeof setTimeout> | undefined;
let degradedReason: string | undefined;
let lastPostResults: Array<{ surface: string; accepted: boolean }> = [];
let lastLoadedBySurface: Array<{ surface: string; reloadCount: number }> = [];
let refreshRequests: Array<{ surface: string; count: number }> = [];

export function registerWebviewHmrWatcher(
    context: vscode.ExtensionContext,
    output: vscode.OutputChannel,
    laneRegistry: LaneRegistry,
): void {
    registry = laneRegistry;
    outputChannel = output;

    let watcher: vscode.FileSystemWatcher | undefined;

    const stop = (): void => {
        if (debounceHandle) {
            clearTimeout(debounceHandle);
            debounceHandle = undefined;
        }
        watcher?.dispose();
        watcher = undefined;
    };

    const start = (): void => {
        if (watcher) return;
        try {
            const pattern = new vscode.RelativePattern(context.extensionPath, 'media/views/**');
            watcher = vscode.workspace.createFileSystemWatcher(pattern, false, false, false);
            const onChange = (uri: vscode.Uri): void => scheduleReload(uri);
            context.subscriptions.push(
                watcher,
                watcher.onDidCreate(onChange),
                watcher.onDidChange(onChange),
                watcher.onDidDelete(onChange),
            );
            setLane('LIVE', 'watching media/views/**');
            output.appendLine('[webview-hmr] watching media/views/**');
        } catch (error) {
            degradedReason = stringifyError(error);
            setLane('DEGRADED', degradedReason);
            output.appendLine(`[webview-hmr] watcher init failed: ${degradedReason}`);
        }
    };

    const sync = (): void => {
        const enabled = vscode.workspace.getConfiguration('chthonic').get<boolean>('dev.autoReload', false);
        if (enabled) {
            start();
        } else {
            stop();
            setLane('PARKED', 'chthonic.dev.autoReload=false');
        }
    };

    context.subscriptions.push(
        vscode.workspace.onDidChangeConfiguration((event) => {
            if (event.affectsConfiguration('chthonic.dev.autoReload')) {
                sync();
            }
        }),
        vscode.commands.registerCommand('chthonic.__webviewHmrProbe', (request: ProbeRequest) => waitForProbe(request)),
        vscode.commands.registerCommand('chthonic.__webviewHmrState', () => ({
            lane: registry?.get('webviewHmr') ?? null,
            tracked: Array.from(trackedViews.entries()).map(([surface, views]) => ({ surface, count: views.size })),
            watchEventCount,
            reloadSequence,
            degradedReason,
            lastPostResults,
            lastLoadedBySurface,
            refreshRequests,
        })),
        { dispose: stop },
    );

    sync();
}

export function trackWebview(
    surface: HmrSurface,
    webviewView: vscode.WebviewView,
    refreshHtml?: () => void,
): void {
    let views = trackedViews.get(surface);
    if (!views) {
        views = new Set();
        trackedViews.set(surface, views);
    }
    views.add(webviewView);

    const messageDisposable = webviewView.webview.onDidReceiveMessage((message: unknown) => {
        if (!message || typeof message !== 'object') {
            return;
        }
        const payload = message as LoadedMessage;
        if (payload.type === 'webviewHmr.reloadRequested') {
            refreshRequests = bumpSurfaceCount(refreshRequests, surface);
            refreshHtml?.();
            return;
        }
        if (payload.type === 'webviewHmr.loaded') {
            handleLoaded(surface, payload);
        }
    });

    const dispose = (): void => {
        messageDisposable.dispose();
        views?.delete(webviewView);
        if (views?.size === 0) {
            trackedViews.delete(surface);
        }
    };

    webviewView.onDidDispose(dispose);
}

export function markWebviewHmrDegraded(reason: string): void {
    degradedReason = reason;
    setLane('DEGRADED', reason);
}

function scheduleReload(uri: vscode.Uri): void {
    watchEventCount += 1;
    if (debounceHandle) {
        clearTimeout(debounceHandle);
    }
    debounceHandle = setTimeout(() => {
        debounceHandle = undefined;
        void broadcastReload(uri);
    }, DEBOUNCE_MS);
}

async function broadcastReload(uri: vscode.Uri): Promise<void> {
    reloadSequence += 1;
    const message = {
        type: 'reload',
        changedUri: uri.toString(),
        sequence: reloadSequence,
    };

    const posts: Promise<void>[] = [];
    const results: Array<{ surface: string; accepted: boolean }> = [];
    for (const [surface, views] of trackedViews.entries()) {
        for (const view of views) {
            posts.push(Promise.resolve(view.webview.postMessage(message)).then((accepted) => {
                results.push({ surface, accepted });
            }));
        }
    }
    await Promise.allSettled(posts);
    lastPostResults = results;
    outputChannel?.appendLine(`[webview-hmr] reload broadcast ${reloadSequence} (${trackedViews.size} surfaces)`);
}

function waitForProbe(request: ProbeRequest): Promise<ProbeResult> {
    const timeoutMs = request.timeoutMs ?? 1500;
    return new Promise<ProbeResult>((resolve, reject) => {
        const waiter: ProbeWaiter = {
            request,
            startedAt: Date.now(),
            resolve,
            reject,
            timeout: setTimeout(() => {
                removeWaiter(waiter);
                reject(new Error(`Timed out waiting for ${request.surface} HMR marker ${request.marker}`));
            }, timeoutMs),
        };
        waiters.push(waiter);
    });
}

function handleLoaded(surface: HmrSurface, message: LoadedMessage): void {
    const html = typeof message.html === 'string' ? message.html : '';
    const reloadCount = typeof message.reloadCount === 'number' ? message.reloadCount : 0;
    lastLoadedBySurface = [
        ...lastLoadedBySurface.filter((entry) => entry.surface !== surface),
        { surface, reloadCount },
    ];
    for (const waiter of [...waiters]) {
        if (waiter.request.surface !== surface) {
            continue;
        }
        if (!html.includes(waiter.request.marker) || reloadCount < 1) {
            continue;
        }
        removeWaiter(waiter);
        waiter.resolve({
            surface,
            marker: waiter.request.marker,
            reloadLatencyMs: Date.now() - waiter.startedAt,
            reloadCount,
            watchEvents: watchEventCount,
            windowReloadInvoked: false,
        });
    }
}

function removeWaiter(waiter: ProbeWaiter): void {
    const index = waiters.indexOf(waiter);
    if (index >= 0) {
        waiters.splice(index, 1);
    }
    clearTimeout(waiter.timeout);
}

function bumpSurfaceCount(
    entries: Array<{ surface: string; count: number }>,
    surface: string,
): Array<{ surface: string; count: number }> {
    const current = entries.find((entry) => entry.surface === surface);
    return [
        ...entries.filter((entry) => entry.surface !== surface),
        { surface, count: (current?.count ?? 0) + 1 },
    ];
}

function setLane(state: 'LIVE' | 'PARKED' | 'DEGRADED', reason: string): void {
    registry?.set({
        name: 'webviewHmr',
        state,
        reason,
    });
}

function stringifyError(error: unknown): string {
    if (error instanceof Error) {
        return `${error.name}: ${error.message}`;
    }
    return String(error);
}
