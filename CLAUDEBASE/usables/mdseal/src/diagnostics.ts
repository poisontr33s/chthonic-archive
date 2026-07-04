import type { Diagnostic } from "./types";
export const diag = (code: string, message: string, severity: Diagnostic["severity"] = "warning", extra: Partial<Diagnostic> = {}): Diagnostic => ({ code, message, severity, ...extra });

