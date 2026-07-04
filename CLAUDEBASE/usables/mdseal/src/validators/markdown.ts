import { diag } from "../diagnostics";
import type { DocumentModel } from "../model";
export const markdownDiagnostics = (model: DocumentModel) => {
  const fenceCount = (model.text.match(/```/g) ?? []).length;
  return fenceCount % 2 ? [diag("MDSEAL_FENCE_UNCLOSED", "code fence count is odd", "error")] : [];
};

