export type MdsealProviderKind = "formula-ocr" | "document-ocr" | "embedding" | "reranker";

export type ProviderRequest =
  | { kind: "formula-ocr"; imagePath: string; profile: string }
  | { kind: "document-ocr"; imagePath: string; profile: string }
  | { kind: "embedding"; text: string };

export type ProviderResult =
  | { kind: "formula-ocr"; latex: string; markdown?: string; confidence: number; model: string }
  | { kind: "document-ocr"; markdown: string; confidence: number; model: string }
  | { kind: "embedding"; vector: number[]; model: string };

export type MdsealProviderAdapter = "python-stdio" | "transformers-js" | "external-command" | "null";
export type ProviderRegistryStatus = "available" | "experimental" | "planned" | "disabled";
export type ProviderRuntime = "cpu" | "gpu" | "webgpu" | "cuda" | "unknown";
export type ProviderSupport = "yes" | "partial" | "no" | "unknown";

export type MdsealProviderRegistryEntry = {
  id: string;
  displayName: string;
  kind: MdsealProviderKind;
  modelId: string | null;
  adapter: MdsealProviderAdapter;
  status: ProviderRegistryStatus;
  offlineSupport: ProviderSupport;
  expectedRuntime: ProviderRuntime;
  windowsSupport: ProviderSupport;
  licenseNote: string;
  installHint: string;
  knownWeaknesses: string[];
  outputContract: string;
  requiresNetworkForInstall: boolean;
  mayTriggerModelDownload: boolean;
};

export type ProviderDoctorStatus = "passed" | "warning" | "failed" | "skipped";
export type ProviderDoctorCheck = { name: string; status: ProviderDoctorStatus; message: string; diagnostics: import("../types").Diagnostic[] };
export type ProviderDoctorProviderResult = { id: string; kind: MdsealProviderKind; enabled: boolean; registryStatus: string; checks: ProviderDoctorCheck[] };
export type ProviderDoctorResult = {
  passed: boolean;
  providersEnabled: boolean;
  allowNetwork: boolean;
  allowModelDownloads: boolean;
  providers: ProviderDoctorProviderResult[];
  checks: ProviderDoctorCheck[];
  diagnostics: import("../types").Diagnostic[];
};

export type ProviderConfig = {
  enabled: boolean;
  defaultFormulaOcr: string;
  defaultDocumentOcr: string;
  defaultEmbedding: string;
  defaultReranker: string;
  allowNetwork: boolean;
  allowModelDownloads: boolean;
  pythonSidecar: {
    enabled: boolean;
    command: string;
    args: string[];
    cwd?: string;
  };
  transformersJs: {
    enabled: boolean;
    device: "cpu" | "webgpu" | "wasm";
    dtype: "fp32" | "fp16" | "q8" | "q4";
  };
};
