// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: sentry_test.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: ORANGE
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ║ Ogdoad-Ceque Radiance:
// ║   └─◄ scripts/sentry_init.ts
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * Sentry integration test
 *
 * @SID           TEST_SENTRY_INTEGRATION_V1
 * @Shabti        Test Script
 * @Purpose       Captures a test exception via Sentry SDK and flushes it.
 *                Validates that SENTRY_DSN is configured and reachable.
 */

import * as Sentry from "@sentry/bun";
import { initSentry } from "./sentry_init";

initSentry();

try {
  throw new Error("chthonic-archive sentry_test.ts: test exception");
} catch (e) {
  Sentry.captureException(e);
  // Give the SDK a chance to send before exit.
  await Sentry.flush(2000);
}

console.log("sentry_test: captured + flushed (if SENTRY_DSN set)");
