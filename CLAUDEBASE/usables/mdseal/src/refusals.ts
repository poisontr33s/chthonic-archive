import type { Diagnostic } from "./types";
export const refuse = (code: string, message: string, source: Diagnostic["source"] = "cli", extra: Partial<Diagnostic> = {}): Diagnostic => ({
  code,
  message,
  severity: "error",
  suggestedFix: false,
  confidence: 1,
  source,
  ...extra,
});
