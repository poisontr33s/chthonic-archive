import type { ProviderRequest, ProviderResult } from "./types";
export const nullProvider = async (_req: ProviderRequest): Promise<ProviderResult | null> => null;

