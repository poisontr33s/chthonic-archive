// ╔════════════════════════════════════════════════════════════════════════════╗
// ║  ARCHIVED — mandala_viewer_legacy.ts                                     ║
// ╠════════════════════════════════════════════════════════════════════════════╣
// ║  Status: NEUTRALIZED (2026-02-20)                                        ║
// ║  Reason: contained duplicate registrations for chthonic.themeView and    ║
// ║          chthonic.switchTheme that collide with chthonic-archive.        ║
// ║  History: original 1021-line monolith that was the first mandala viewer. ║
// ║           Superseded by the bridge pattern in extension.ts and the       ║
// ║           archive's own ThemeTreeProvider + AbyssalPaneProvider.          ║
// ║  Git: full history preserved in git log for this path.                   ║
// ║  Reactivation: DO NOT re-import. If mandala needs standalone views,      ║
// ║                use unique view IDs (chthonic.mandala.*) and register     ║
// ║                via the bridge delegation pattern in extension.ts.        ║
// ╚════════════════════════════════════════════════════════════════════════════╝

// This file intentionally exports nothing.
// It exists solely to preserve git blame history and prevent accidental re-creation.
export {};
