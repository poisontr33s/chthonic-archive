import { readFileSync } from "node:fs";
import type { DocumentModel } from "./model";
import { applyRepairs } from "./repairs";
import { readSeal, sealExists } from "./seal";
import { matchSealContext } from "./seal-helpers";
import { validateCandidate } from "./validation";
import { refuse, existingSealWithoutForce, sealHashOnlyRefuse, sealContextMismatch } from "./refusals";
import type { MdsealManifest, Patch, SealContextMatch } from "./types";

const applyPatch = (text: string, patch: Patch) => {
  const r = patch.replacements[0];
  return text.slice(0, r.startOffset) + r.after + text.slice(r.endOffset);
};

export const restoreFromSeal = (root: string, file: string) => readSeal(root, file);
export const canRestore = (root: string, file: string) => sealExists(root, file);

export const proposeRestoration = (model: DocumentModel, seal: MdsealManifest) => {
  const patches: Patch[] = [];
  const diagnostics = [];
  for (const math of seal.math) {
    const match: SealContextMatch = matchSealContext(seal, model, math);
    if (!match.matched || match.confidence < 0.9) {
      diagnostics.push(sealContextMismatch());
      continue;
    }
    const current = model.text.slice(match.matchedStartOffset!, match.matchedEndOffset!);
    const after = math.raw ?? current;
    if (current !== after) patches.push({ file: model.file, code: "MDSEAL_RESTORE_MATH", description: "restore sealed math span", confidence: match.confidence, replacements: [{ startOffset: match.matchedStartOffset!, endOffset: match.matchedEndOffset!, before: current, after }], protectedZoneTouches: [] });
  }
  return { patches, diagnostics };
};

export const restoreText = (model: DocumentModel, seal: MdsealManifest) => {
  const proposal = proposeRestoration(model, seal);
  let text = model.text;
  for (const patch of proposal.patches) text = applyPatch(text, patch);
  return { text, proposal };
};

