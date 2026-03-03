// @SID: FORGE_TYPE_ARCHIVE_V1
// Purpose: Recovered TypeScript declaration archive from corpse-vault fragments.
// Source-Files: PrismBand, TopologyNode, TopologyData, DependencyGraph, ExecCaptureResult, MoveViewFn, DevKitReport, ProposedApiFn, ToolOwner
// Pathway: typescript fragments -> recoverable declaration blocks -> .d.ts archive
// Kept: Recoverable type contracts and interface shells.
// Discarded: Unbalanced fragments that could not be closed without invention.
declare interface PrismBandRecovered {
  [key: string]: unknown;
}

declare interface TopologyNodeRecovered {
  path: string;
  prism_band: string;
}

declare interface TopologyDataRecovered {
  nodes_count: number;
  edges_count: number;
  generated: string;
  nodes: TopologyNode[];
}

declare interface DependencyGraphRecovered {
  [key: string]: unknown;
}

declare interface ExecCaptureResultRecovered {
  stdout: string;
  stderr: string;
  error: NodeJS.ErrnoException | null;
}

declare interface MoveViewFnRecovered {
  [key: string]: unknown;
}

declare interface DevKitReportRecovered {
  msys2_home: string;
  ucrt64_bin: string;
  perl_path: string;
  cc: string;
  cxx: string;
  env_vars: Array<[string, string]>;
  path_prepend: string[];
}

declare interface ProposedApiFnRecovered {
  [key: string]: unknown;
}

declare interface ToolOwnerRecovered {
  [key: string]: unknown;
}

