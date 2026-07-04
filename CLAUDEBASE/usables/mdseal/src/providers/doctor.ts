import { existsSync } from "node:fs";
import { resolve } from "node:path";
import { providerRegistry, providerById } from "./registry";
import type { ProviderDoctorResult, ProviderDoctorCheck, MdsealProviderRegistryEntry } from "./types";
import { defaultProviderConfig } from "../config";
import { diag } from "../diagnostics";
import { refuse } from "../refusals";

const check = (name: string, status: ProviderDoctorCheck["status"], message: string, ...diagnostics: ProviderDoctorCheck["diagnostics"]) => ({ name, status, message, diagnostics });

export const listProviders = () => providerRegistry;

export const doctorProviders = (opts: { strict?: boolean } = {}): ProviderDoctorResult => {
  const diagnostics = [];
  const checks: ProviderDoctorCheck[] = [];
  const configured = [defaultProviderConfig.defaultFormulaOcr, defaultProviderConfig.defaultDocumentOcr, defaultProviderConfig.defaultEmbedding, defaultProviderConfig.defaultReranker].filter((v) => v && v !== "none");
  for (const id of configured) {
    if (!providerById.has(id)) {
      const d = diag("MDSEAL_PROVIDER_UNKNOWN", `unknown provider ${id}`, opts.strict ? "error" : "warning", { suggestedFix: false, source: "provider" });
      diagnostics.push(d);
      checks.push(check(`provider-${id}`, opts.strict ? "failed" : "warning", d.message, d));
    }
  }
  const global = defaultProviderConfig.enabled ? check("providers-enabled", "passed", "providers enabled") : check("providers-disabled", "skipped", "providers disabled globally", diag("MDSEAL_PROVIDER_DISABLED", "providers disabled globally", "info", { source: "provider" }));
  checks.push(global);
  if (!defaultProviderConfig.pythonSidecar.enabled) {
    checks.push(check("python-sidecar", "skipped", "python sidecar disabled", diag("MDSEAL_PROVIDER_PYTHON_SIDECAR_DISABLED", "python sidecar disabled", "info", { source: "provider" })));
  } else {
    const cmd = defaultProviderConfig.pythonSidecar.command;
    const exists = existsSync(cmd) || existsSync(resolve(cmd));
    if (!exists) {
      const d = refuse("MDSEAL_PROVIDER_COMMAND_MISSING", `provider command missing: ${cmd}`, "provider");
      diagnostics.push(d);
      checks.push(check("python-sidecar", "failed", d.message, d));
    } else {
      checks.push(check("python-sidecar", "passed", "python sidecar command available"));
    }
  }
  if (!defaultProviderConfig.allowNetwork) checks.push(check("network", "passed", "network blocked by policy", diag("MDSEAL_PROVIDER_NETWORK_BLOCKED", "network blocked by policy", "info", { source: "provider" })));
  if (!defaultProviderConfig.allowModelDownloads) checks.push(check("downloads", "passed", "model downloads blocked by policy", diag("MDSEAL_PROVIDER_MODEL_DOWNLOAD_BLOCKED", "model downloads blocked by policy", "info", { source: "provider" })));
  const providers = providerRegistry.map((entry) => ({ id: entry.id, kind: entry.kind, enabled: defaultProviderConfig.enabled && entry.status !== "disabled", registryStatus: entry.status, checks: [check("registry", entry.status === "disabled" ? "skipped" : "passed", `${entry.displayName} registered`)] }));
  return { passed: diagnostics.filter((d) => d.severity === "error").length === 0, providersEnabled: defaultProviderConfig.enabled, allowNetwork: defaultProviderConfig.allowNetwork, allowModelDownloads: defaultProviderConfig.allowModelDownloads, providers, checks, diagnostics };
};
