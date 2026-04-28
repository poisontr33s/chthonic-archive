// @SID: EXT_ACTIVATION_TYPES_V1
import * as vscode from 'vscode';
import type { ActivityBarMorph } from '../monolith/activityBarMorph';
import type { LoomViewProvider } from '../monolith/loomView';
import type { RestoreOrderLayout } from '../monolith/restoreOrderLayout';
import type { LaneRegistry } from '../runtime/laneState';

export interface ActivationDeps {
    readonly context: vscode.ExtensionContext;
    readonly outputChannel: vscode.OutputChannel;
    readonly workspaceRoot: string | null;
    readonly chthonicConfig: vscode.WorkspaceConfiguration;
    readonly laneRegistry: LaneRegistry;
    readonly activityBarMorph: ActivityBarMorph;
    readonly restoreOrderLayout: RestoreOrderLayout;
    readonly loomProvider: LoomViewProvider;
}
