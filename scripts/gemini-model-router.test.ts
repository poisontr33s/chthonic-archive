// @SID: SCRIPT_GEMINI_MODEL_ROUTER_TEST_V1
import { describe, expect, test } from "bun:test";

import {
  matchesCompatFallback,
  resolveRoutingDecision,
  syncWorkspaceSettings,
} from "./gemini-model-router";
import {
  noFallbackRegistry,
  registry,
} from "./__fixtures__/gemini-model-router-registry";

describe("syncWorkspaceSettings", () => {
  test("aligns the workspace aliases with the local registry", () => {
    const synced = syncWorkspaceSettings(
      {
        model: { name: "chthonic-fast" },
        modelConfigs: {
          customAliases: {
            "chthonic-fast": {
              modelConfig: {
                model: "gemini-3-flash-preview",
              },
            },
          },
        },
      },
      registry,
    );

    expect(synced.model?.name).toBe("chthonic-fast");
    expect(synced.modelConfigs?.customAliases?.["chthonic-fast"]?.modelConfig.model).toBe(
      "gemini-3.1-flash-lite-preview",
    );
    expect(
      synced.modelConfigs?.customAliases?.["chthonic-fast-stable"]?.modelConfig.model,
    ).toBe("gemini-3-flash-preview");
  });
});

describe("resolveRoutingDecision", () => {
  test("routes interactive flash-lite requests to the stable alias in auto mode", () => {
    const decision = resolveRoutingDecision(
      [],
      "interactive",
      { model: { name: "chthonic-fast" } },
      registry,
      "auto",
    );

    expect(decision.effectiveRequestModel).toBe("chthonic-fast-stable");
    expect(decision.fallbackRequestModel).toBe("chthonic-fast-stable");
    expect(decision.appliedPolicy).toBe("interactive-fallback");
  });

  test("keeps headless flash-lite requests on primary first and enables retry", () => {
    const decision = resolveRoutingDecision(
      ["-m", "chthonic-fast"],
      "headless",
      { model: { name: "chthonic-fast" } },
      registry,
      "auto",
    );

    expect(decision.effectiveRequestModel).toBe("chthonic-fast");
    expect(decision.fallbackRequestModel).toBe("chthonic-fast-stable");
    expect(decision.headlessRetryAllowed).toBe(true);
    expect(decision.appliedPolicy).toBe("headless-primary-then-fallback");
  });
});

describe("matchesCompatFallback", () => {
  test("detects known flash-lite catalog and permission failures", () => {
    expect(
      matchesCompatFallback(
        'Model "gemini-3.1-flash-lite-preview" was not found or is invalid',
        registry.models["gemini-3.1-flash-lite-preview"].matchers,
      ),
    ).toBe(true);

    expect(
      matchesCompatFallback(
        "HTTP 403 Forbidden",
        registry.models["gemini-3.1-flash-lite-preview"].matchers,
      ),
    ).toBe(true);

    expect(
      matchesCompatFallback(
        "ModelNotFoundError: Requested entity was not found.",
        registry.models["gemini-3.1-flash-lite-preview"].matchers,
      ),
    ).toBe(true);
  });
});

describe("resolveRoutingDecision — edge cases", () => {
  test("returns passthrough-no-fallback when alias has no fallback and model carries no fallbackModel", () => {
    const decision = resolveRoutingDecision(
      [],
      "interactive",
      { model: { name: "chthonic-direct" } },
      noFallbackRegistry as Parameters<typeof resolveRoutingDecision>[3],
      "auto",
    );

    expect(decision.appliedPolicy).toBe("passthrough-no-fallback");
    expect(decision.fallbackRequestModel).toBeUndefined();
    expect(decision.headlessRetryAllowed).toBe(false);
  });
});
