import type { DocumentModel } from "../model";
export const protectedZonePreserved = (before: DocumentModel, after: string) => before.zones.every((z) => ["frontmatter", "code_fence", "inline_code", "html_block", "html_inline", "link_destination", "image_destination"].includes(z.kind) ? before.text.slice(z.startOffset, z.endOffset) === after.slice(z.startOffset, z.endOffset) : true);
