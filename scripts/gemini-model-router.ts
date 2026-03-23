#!/usr/bin/env bun

import { readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

type ThinkingLevel = "LOW" | "HIGH";
type RoutingMode = "interactive" | "headless";
type PreferenceMode = "auto" | "primary" | "fallback";
type RequestedSource = "cli" | "env" | "settings" | "default";

type RegistryAlias = {
  targetModel: string;
  fallbackAlias?: string;
  fallbackModel?: string;
  thinkingLevel?: ThinkingLevel;
  includeThoughts?: boolean;
};

type RegistryModel = {
  extends?: string;
  fallbackModel: string;
  matchers: string[];
};

type RegistryFile = {
  version: number;
  workspaceModel: string;
  aliases: Record<string, RegistryAlias>;
  models: Record<string, RegistryModel>;
};

type GeminiSettings = {
  model?: {
    name?: string;
  };
  modelConfigs?: {
    customAliases?: Record<
      string,
      {
        modelConfig: {
          model: string;
          generateContentConfig?: {
            thinkingConfig?: {
              thinkingLevel?: ThinkingLevel;
              includeThoughts?: boolean;
            };
          };
        };
      }
    >;
  };
  [key: string]: unknown;
};

type RoutingDecision = {
  requestedModel: string;
  requestedSource: RequestedSource;
  resolvedRequestedModel: string;
  effectiveRequestModel: string;
  fallbackRequestModel?: string;
  fallbackMatchers: string[];
  headlessRetryAllowed: boolean;
  forceModelFlag: boolean;
  appliedPolicy: string;
  modePreference: PreferenceMode;
};

type SyncResult = {
  changed: boolean;
  registryPath: string;
  settingsPath: string;
  workspaceModel: string;
  aliasNames: string[];
};

const SCRIPT_DIR = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(SCRIPT_DIR, "..");
const DEFAULT_REGISTRY_PATH = resolve(REPO_ROOT, ".gemini", "local-model-registry.json");
const DEFAULT_SETTINGS_PATH = resolve(REPO_ROOT, ".gemini", "settings.json");
const DEFAULT_MODE_PREFERENCE: PreferenceMode = "auto";

function readJsonFile<T>(path: string): T {
  return JSON.parse(readFileSync(path, "utf-8")) as T;
}

function writeJsonFile(path: string, value: unknown): void {
  writeFileSync(path, `${JSON.stringify(value, null, 2)}\n`, "utf-8");
}

function getRegistryPath(): string {
  return process.env.CHTHONIC_GEMINI_MODEL_REGISTRY?.trim() || DEFAULT_REGISTRY_PATH;
}

function getSettingsPath(): string {
  return process.env.CHTHONIC_GEMINI_SETTINGS_PATH?.trim() || DEFAULT_SETTINGS_PATH;
}

function getPreferenceMode(): PreferenceMode {
  const raw = process.env.CHTHONIC_GEMINI_FLASH_LITE_MODE?.trim().toLowerCase();
  if (raw === "primary" || raw === "fallback" || raw === "auto") {
    return raw;
  }
  return DEFAULT_MODE_PREFERENCE;
}

function buildAliasModelConfig(alias: RegistryAlias) {
  const thinkingConfig: { thinkingLevel?: ThinkingLevel; includeThoughts?: boolean } = {};

  if (alias.thinkingLevel) {
    thinkingConfig.thinkingLevel = alias.thinkingLevel;
  }

  if (alias.includeThoughts) {
    thinkingConfig.includeThoughts = true;
  }

  return {
    modelConfig: {
      model: alias.targetModel,
      generateContentConfig: {
        thinkingConfig,
      },
    },
  };
}

function syncWorkspaceSettings(settings: GeminiSettings, registry: RegistryFile): GeminiSettings {
  const next: GeminiSettings = JSON.parse(JSON.stringify(settings));

  next.model ??= {};
  next.model.name = registry.workspaceModel;

  next.modelConfigs ??= {};
  next.modelConfigs.customAliases ??= {};

  for (const [aliasName, alias] of Object.entries(registry.aliases)) {
    next.modelConfigs.customAliases[aliasName] = buildAliasModelConfig(alias);
  }

  return next;
}

function getModelFromArgs(args: string[]): string | undefined {
  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "-m" || arg === "--model") {
      return args[index + 1];
    }
    if (arg.startsWith("--model=")) {
      return arg.slice("--model=".length);
    }
  }
  return undefined;
}

function resolveAliasTarget(model: string, registry: RegistryFile): string {
  return registry.aliases[model]?.targetModel ?? model;
}

function resolveFallbackRequestModel(requestedModel: string, registry: RegistryFile): string | undefined {
  const alias = registry.aliases[requestedModel];
  if (alias?.fallbackAlias) {
    return alias.fallbackAlias;
  }
  if (alias?.fallbackModel) {
    return alias.fallbackModel;
  }
  const resolvedRequested = resolveAliasTarget(requestedModel, registry);
  const registryModel = registry.models[resolvedRequested];
  return registryModel?.fallbackModel;
}

function extractRequestedModel(
  args: string[],
  envModel: string | undefined,
  settingsModel: string | undefined,
  registry: RegistryFile,
): { model: string; source: RequestedSource } {
  const cliModel = getModelFromArgs(args);
  if (cliModel) {
    return { model: cliModel, source: "cli" };
  }
  if (envModel) {
    return { model: envModel, source: "env" };
  }
  if (settingsModel) {
    return { model: settingsModel, source: "settings" };
  }
  return { model: registry.workspaceModel, source: "default" };
}

function resolveRoutingDecision(
  args: string[],
  mode: RoutingMode,
  settings: GeminiSettings,
  registry: RegistryFile,
  preferenceMode = getPreferenceMode(),
): RoutingDecision {
  const requested = extractRequestedModel(
    args,
    process.env.GEMINI_MODEL,
    settings.model?.name,
    registry,
  );
  const resolvedRequestedModel = resolveAliasTarget(requested.model, registry);
  const registryModel = registry.models[resolvedRequestedModel];

  if (!registryModel) {
    return {
      requestedModel: requested.model,
      requestedSource: requested.source,
      resolvedRequestedModel,
      effectiveRequestModel: requested.model,
      fallbackMatchers: [],
      headlessRetryAllowed: false,
      forceModelFlag: false,
      appliedPolicy: "passthrough",
      modePreference: preferenceMode,
    };
  }

  const fallbackRequestModel = resolveFallbackRequestModel(requested.model, registry);

  if (!fallbackRequestModel) {
    return {
      requestedModel: requested.model,
      requestedSource: requested.source,
      resolvedRequestedModel,
      effectiveRequestModel: requested.model,
      fallbackMatchers: registryModel.matchers,
      headlessRetryAllowed: false,
      forceModelFlag: false,
      appliedPolicy: "passthrough-no-fallback",
      modePreference: preferenceMode,
    };
  }

  if (preferenceMode === "primary") {
    return {
      requestedModel: requested.model,
      requestedSource: requested.source,
      resolvedRequestedModel,
      effectiveRequestModel: requested.model,
      fallbackRequestModel,
      fallbackMatchers: registryModel.matchers,
      headlessRetryAllowed: mode === "headless",
      forceModelFlag: true,
      appliedPolicy: "force-primary",
      modePreference: preferenceMode,
    };
  }

  if (preferenceMode === "fallback") {
    return {
      requestedModel: requested.model,
      requestedSource: requested.source,
      resolvedRequestedModel,
      effectiveRequestModel: fallbackRequestModel,
      fallbackRequestModel,
      fallbackMatchers: registryModel.matchers,
      headlessRetryAllowed: false,
      forceModelFlag: true,
      appliedPolicy: "force-fallback",
      modePreference: preferenceMode,
    };
  }

  if (mode === "interactive") {
    return {
      requestedModel: requested.model,
      requestedSource: requested.source,
      resolvedRequestedModel,
      effectiveRequestModel: fallbackRequestModel,
      fallbackRequestModel,
      fallbackMatchers: registryModel.matchers,
      headlessRetryAllowed: false,
      forceModelFlag: true,
      appliedPolicy: "interactive-fallback",
      modePreference: preferenceMode,
    };
  }

  return {
    requestedModel: requested.model,
    requestedSource: requested.source,
    resolvedRequestedModel,
    effectiveRequestModel: requested.model,
    fallbackRequestModel,
    fallbackMatchers: registryModel.matchers,
    headlessRetryAllowed: true,
    forceModelFlag: true,
    appliedPolicy: "headless-primary-then-fallback",
    modePreference: preferenceMode,
  };
}

function matchesCompatFallback(output: string, matchers: string[]): boolean {
  const haystack = output.toLowerCase();
  return matchers.some((matcher) => haystack.includes(matcher.toLowerCase()));
}

function parseCliArgs(argv: string[]) {
  const values = [...argv];
  const command = values.shift();
  const flags = new Map<string, string | boolean>();

  for (let index = 0; index < values.length; index += 1) {
    const arg = values[index];
    if (arg.startsWith("--")) {
      const [name, inlineValue] = arg.split("=", 2);
      if (inlineValue !== undefined) {
        flags.set(name, inlineValue);
        continue;
      }
      const next = values[index + 1];
      if (!next || next.startsWith("--")) {
        flags.set(name, true);
        continue;
      }
      flags.set(name, next);
      index += 1;
    }
  }

  return { command, flags };
}

function syncCommand(writeChanges: boolean): SyncResult {
  const registryPath = getRegistryPath();
  const settingsPath = getSettingsPath();
  const registry = readJsonFile<RegistryFile>(registryPath);
  const settings = readJsonFile<GeminiSettings>(settingsPath);
  const nextSettings = syncWorkspaceSettings(settings, registry);
  const changed = JSON.stringify(settings) !== JSON.stringify(nextSettings);

  if (changed && writeChanges) {
    writeJsonFile(settingsPath, nextSettings);
  }

  return {
    changed,
    registryPath,
    settingsPath,
    workspaceModel: registry.workspaceModel,
    aliasNames: Object.keys(registry.aliases),
  };
}

function resolveCommand(flags: Map<string, string | boolean>): RoutingDecision {
  const modeFlag = String(flags.get("--mode") || "interactive").toLowerCase();
  const mode: RoutingMode = modeFlag === "headless" ? "headless" : "interactive";
  const argsJson = String(flags.get("--args-json") || "[]");
  const rawArgs = JSON.parse(argsJson) as string[];
  const registry = readJsonFile<RegistryFile>(getRegistryPath());
  const settings = readJsonFile<GeminiSettings>(getSettingsPath());
  return resolveRoutingDecision(rawArgs, mode, settings, registry);
}

function classifyErrorCommand(flags: Map<string, string | boolean>) {
  const text = String(flags.get("--text") || "");
  const matchersValue = flags.get("--matchers");
  const matchers =
    typeof matchersValue === "string" && matchersValue.trim().length > 0
      ? (JSON.parse(matchersValue) as string[])
      : [];
  return {
    matches: matchesCompatFallback(text, matchers),
  };
}

function main() {
  const { command, flags } = parseCliArgs(process.argv.slice(2));

  switch (command) {
    case "sync": {
      const writeChanges = flags.get("--write") !== false;
      console.log(JSON.stringify(syncCommand(writeChanges), null, 2));
      return;
    }
    case "resolve": {
      console.log(JSON.stringify(resolveCommand(flags), null, 2));
      return;
    }
    case "classify-error": {
      console.log(JSON.stringify(classifyErrorCommand(flags), null, 2));
      return;
    }
    default: {
      console.error("Usage: bun run scripts/gemini-model-router.ts <sync|resolve|classify-error> [flags]");
      process.exit(1);
    }
  }
}

if (import.meta.main) {
  main();
}

export {
  buildAliasModelConfig,
  matchesCompatFallback,
  resolveRoutingDecision,
  syncWorkspaceSettings,
};
