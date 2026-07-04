import type { DocumentModel } from "../model";
import { imageDiagnostics as collectImageDiagnostics, imageReferences } from "../images";

export const imageRefs = (model: DocumentModel) => imageReferences(model);
export const imageDiagnostics = (model: DocumentModel) => collectImageDiagnostics(model);
