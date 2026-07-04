// src/scriptorium/patina.ts
//
// Time is legible. Files acquire patina as they age.
// The interface visibly knows the difference between fresh and weathered.
//
// One function, one variable derivation. The CSS side reads the level
// off `data-patina="…"` on the file's row/tile and applies the visual
// treatment from a small lookup table.

export type PatinaLevel = 'fresh' | 'recent' | 'week' | 'month' | 'season' | 'archive';

const DAY = 24 * 60 * 60 * 1000;

export function patinaFromMtime(mtimeMs: number, now: number = Date.now()): PatinaLevel {
  const age = now - mtimeMs;
  if (age < 1 * DAY)   return 'fresh';
  if (age < 3 * DAY)   return 'recent';
  if (age < 14 * DAY)  return 'week';
  if (age < 60 * DAY)  return 'month';
  if (age < 240 * DAY) return 'season';
  return 'archive';
}

// CSS lookup. Each level is a tuple of (border-color, filter, label).
// The colors are workspace-theme-derived in webview; here we ship
// the filter and label only and let CSS supply the rest.
export const PATINA_CSS: Record<PatinaLevel, { filter: string; label: string }> = {
  fresh:   { filter: 'none',                                    label: 'fresh' },
  recent:  { filter: 'none',                                    label: 'recent' },
  week:    { filter: 'contrast(.94) brightness(1.02)',          label: 'a week' },
  month:   { filter: 'contrast(.88) brightness(1.04) blur(.2px)', label: 'a month' },
  season:  { filter: 'contrast(.80) brightness(1.06) blur(.4px)', label: 'a season' },
  archive: { filter: 'contrast(.72) brightness(1.08) blur(.6px)', label: 'archived by time' },
};

// Approval overrides time — once approved, the file gains gold-fleck patina
// regardless of age. The webview applies this as a separate rule.
export const APPROVED_PATINA_FILTER = 'sepia(.15) saturate(1.1)';
