import * as path from 'node:path';
import * as vscode from 'vscode';

export interface WorkspaceRelativePath {
  folder: vscode.WorkspaceFolder;
  path: string;
}

export function workspaceRelativePath(uri: vscode.Uri): WorkspaceRelativePath | undefined {
  const folder = vscode.workspace.getWorkspaceFolder(uri);
  if (!folder) return undefined;
  const rel = path.relative(folder.uri.fsPath, uri.fsPath).replace(/\\/g, '/');
  if (!rel || rel.startsWith('..') || path.isAbsolute(rel)) return undefined;
  return { folder, path: rel };
}

export function designLeafPath(uri: vscode.Uri, pattern?: RegExp): WorkspaceRelativePath | undefined {
  const rel = workspaceRelativePath(uri);
  if (!rel || !rel.path.startsWith('designs/')) return undefined;
  if (pattern && !pattern.test(rel.path)) return undefined;
  return rel;
}

export function designResourceRoots(): vscode.Uri[] {
  const roots: vscode.Uri[] = [];
  for (const folder of vscode.workspace.workspaceFolders ?? []) {
    roots.push(vscode.Uri.joinPath(folder.uri, 'designs'));
    roots.push(vscode.Uri.joinPath(folder.uri, 'assets'));
  }
  return roots;
}
