export interface HardwareFingerprint {
  gpuUuid: string;
  machineGuid: string;
}

export interface HealthReport {
  ok: boolean;
  engine: 'loaded' | 'unloaded' | 'compiling' | 'unknown';
  stream: 'suspended' | 'running' | 'unknown';
  vramUsedMb?: number;
  vramFreeMb?: number;
}

export interface GenerateRequest {
  prompt: string;
  steps: number;
  guidance: number;
  width: number;
  height: number;
  seed: number;
}

export interface GenerateResult {
  buffer: Buffer;
  genMs: number;
  width: number;
  height: number;
  channels: number;
}

export interface StartSatelliteOptions {
  uvPath: string;
  cwd: string;
  pipeName?: string;
  mmfName?: string;
  ditPipeName?: string;
}

export interface LoadEngineOptions {
  enginePath: string;
  /** Optional. Provide together with a prior setMasterSecret() to load a
   * sealed engine (.engine.enc). Omit to load a plaintext engine
   * (.engine.plain) directly -- no master secret required. */
  sealPath?: string;
  ditPipeName?: string;
}

export interface LoadEngineResult {
  ioTensors: string[];
  ditPipeName: string;
}

export function setMasterSecret(secret: string): void;
export function clearMasterSecret(): void;
export function hardwareFingerprint(): HardwareFingerprint;
export function startSatellite(opts: StartSatelliteOptions): Promise<void>;
export function stopSatellite(graceful: boolean): Promise<void>;
export function healthCheck(): Promise<HealthReport>;
export function generate(req: GenerateRequest): Promise<GenerateResult>;
export function loadEngine(opts: LoadEngineOptions): Promise<LoadEngineResult>;
export function unloadEngine(): Promise<void>;
