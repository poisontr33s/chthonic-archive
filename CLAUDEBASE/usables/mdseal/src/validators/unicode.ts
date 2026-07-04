import { diag } from "../diagnostics";
import type { DocumentModel } from "../model";
export const hiddenSymbolDiagnostics = (model: DocumentModel) => {
  const out = [];
  const chars: Record<string, string> = { "\u200b": "zero-width space", "\u200c": "zero-width non-joiner", "\u200d": "zero-width joiner", "\u2060": "word joiner", "\ufeff": "BOM", "\u00a0": "non-breaking space", "\u202f": "narrow non-breaking space", "\u00ad": "soft hyphen", "\u202e": "bidirectional override/control" };
  for (let i = 0; i < model.text.length; i++) if (chars[model.text[i]]) out.push(diag("MDSEAL_HIDDEN_SYMBOL", chars[model.text[i]], "info", { startOffset: i }));
  return out;
};

