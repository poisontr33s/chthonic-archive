// @SID: SCRIPT_GEMINI_MODEL_ROUTER_TEST_V1
import { describe, expect, test } from "bun:test";

import {
  matchesCompatFallback,
  resolveRoutingDecision,
  syncWorkspaceSettings,
} from "./gemini-model-router";

const registry = {
  version: 1,
  workspaceModel: "chthonic-fast",
  aliases: {
    "chthonic-fast": {
      targetModel: "gemini-3.1-flash-lite-preview",
      fallbackAlias: "chthonic-fast-stable",
      fallbackModel: "gemini-3-flash-preview",
      thinkingLevel: "LOW" as const,
    },
    "chthonic-fast-stable": {
      targetModel: "gemini-3-flash-preview",
      thinkingLevel: "LOW" as const,
    },
    "chthonic-thinking": {
      targetModel: "gemini-3-flash-preview",
      thinkingLevel: "HIGH" as const,
      includeThoughts: true,
    },
  },
  models: {
    "gemini-3.1-flash-lite-preview": {
      extends: "gemini-3-flash-preview",
      fallbackModel: "gemini-3-flash-preview",
      matchers: [
        "was not found or is invalid",
        "not found or is invalid",
        "requested entity was not found",
        "modelnotfounderror",
        "404",
        "403",
        "forbidden",
      ],
    },
  },
};

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
