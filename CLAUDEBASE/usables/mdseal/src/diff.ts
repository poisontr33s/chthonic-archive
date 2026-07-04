export const unifiedDiff = (before: string, after: string) => before === after ? "" : `--- before\n+++ after\n@@\n-${before}\n+${after}\n`;

