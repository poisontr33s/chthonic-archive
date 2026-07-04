import { defaultProfile } from "./config";
import { readDocument } from "./fs";
import { scanZones } from "./zones";
import { hiddenSymbolDiagnostics } from "./validators/unicode";
import { imageDiagnostics } from "./validators/images";
import type { DocumentModel } from "./model";

export const loadModel = (file: string): DocumentModel => {
  const doc = readDocument(file);
  const { zones, images } = scanZones({ text: doc.text });
  const model: DocumentModel = { file, raw: doc.raw, text: doc.text, encoding: doc.encoding, eol: doc.eol, zones, images, diagnostics: [], dialect: defaultProfile };
  model.diagnostics.push(...hiddenSymbolDiagnostics(model), ...imageDiagnostics(model));
  return model;
};
