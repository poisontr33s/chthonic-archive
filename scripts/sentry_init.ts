#!/usr/bin/env bun
// @SID: SCRIPT_SENTRY_INIT_V1

// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: sentry_init.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: ORANGE
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ║ Ogdoad-Ceque Radiance:
// ║   └─◄ scripts/mcp_artisan_server.ts
// ║   └─◄ scripts/overnight_daemon.ts
// ║   └─◄ scripts/sentry_test.ts
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * Sentry SDK initialization for Bun runtime
 *
 * @SID           LIB_SENTRY_INIT_V1
 * @Shabti        Library Module
 * @Heka-Ayni     CONCEPT_SENTRY_OBSERVABILITY
 * @Ankh-Tinku    STATE_SENTRY_INIT_ACTIVE
 * @Purpose       Smallest-correct-change Sentry bootstrap. Exports initSentry()
 *                which guards against double-init, validates DSN, and hooks
 *                uncaughtException / unhandledRejection for the process.
 */

import * as Sentry from "@sentry/bun";

let didInit = false;

export type SentryInitOptions = {
  dsn?: string;
  environment?: string;
  release?: string;
  enabled?: boolean;
};

export function initSentry(opts: SentryInitOptions = {}): void {
  if (didInit) return;

  const dsn = opts.dsn ?? process.env.SENTRY_DSN ?? "";
  const enabled = opts.enabled ?? process.env.SENTRY_ENABLED !== "0";

  // Smallest-correct-change: if no DSN, stay a no-op.
  if (!enabled || !dsn) return;

  Sentry.init({
    dsn,
    environment: opts.environment ?? process.env.SENTRY_ENVIRONMENT,
    release: opts.release ?? process.env.SENTRY_RELEASE,
  });

  // Best-effort capture of process-level failures.
  try {
    process.on("uncaughtException", (error) => {
      Sentry.captureException(error);
      void Sentry.flush(2000);
    });

    process.on("unhandledRejection", (reason) => {
      Sentry.captureException(reason);
      void Sentry.flush(2000);
    });
  } catch {
    // Ignore if process hooks aren't available in this runtime.
  }

  didInit = true;
}
