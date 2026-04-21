// @SID: FIXTURE_GEMINI_MODEL_ROUTER_REGISTRY_V1
// Test fixture for gemini-model-router.test.ts
// Extracted from inline test registry — single-source for all router tests.

export const registry = {
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

/**
 * Registry with an alias that has no fallbackAlias and no fallbackModel,
 * and whose target model carries an empty fallbackModel — exercising the
 * "passthrough-no-fallback" policy branch in resolveRoutingDecision.
 */
export const noFallbackRegistry = {
  version: 1,
  workspaceModel: "chthonic-direct",
  aliases: {
    "chthonic-direct": {
      targetModel: "gemini-direct-preview",
      thinkingLevel: "LOW" as const,
      // deliberately no fallbackAlias / fallbackModel
    },
  },
  models: {
    "gemini-direct-preview": {
      fallbackModel: "", // empty → resolveFallbackRequestModel returns "" (falsy)
      matchers: ["model-not-available"],
    },
  },
};
