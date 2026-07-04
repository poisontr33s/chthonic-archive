import { writeText } from "./fs";
export const writePatch = (file: string, text: string) => writeText(file, text);

