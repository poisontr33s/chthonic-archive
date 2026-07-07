---
- Plan-By: Dispatch · Claude Sonnet 4.6
- SID: MDSEAL_FIX_PLAN_V1
- Date: 2026-06-28
- Assessment-Ref: ./mdseal-assessment.md
- Project: CLAUDEBASE/usables/mdseal
- Status: Ready-To-Execute
- Lifecycle: reference-memory — update gate status as work progresses
---

# mdseal — Fix Plan & Improvement Gates

> Gates ordered by dependency. Earlier gates unlock later ones. Mark `[x]` when closed.

---

## Gate 0 — Read-First

Before touching any file, re-read:
- `./mdseal-assessment.md` — the grilling findings that justify each gate below
- `CLAUDEBASE/usables/mdseal/src/zones.ts` — Bug 1 and Bug 2 live here
- `CLAUDEBASE/usables/mdseal/src/cli.ts` — Bug 3 and Bug 4 live here
- `CLAUDEBASE/usables/mdseal/src/restore.ts` — Bug 4 specifics

**Acceptance:** You have read all four files in the current session before making any edit.

---

## Gate 1 — Fix: Frontmatter kills fence detection [BLOCKER]

**What:** In `zones.ts`, `frontmatterDone` is `true` after parsing frontmatter. The fence detection branch is `if (!frontmatterDone && line.startsWith("``\`"))` — so fences are never detected in any file that has YAML frontmatter.

**Fix:** Separate the two concerns. `frontmatterDone` should only skip the frontmatter block during the line loop — it should not gate fence detection. Rename the flag to something like `inFrontmatter` that is false after the frontmatter section ends, or simply remove the frontmatter guard from the fence branch entirely (fences cannot appear inside frontmatter by definition).

**Suggested fix:**
```ts
// Before the loop, replace:
if (!frontmatterDone && line.startsWith("```")) {

// With — fence detection is never inside frontmatter anyway:
if (!inFence && line.startsWith("```")) {
  inFence = true;
  fenceStart = lineStart;
} else if (inFence && line.startsWith("```")) {
  push(zones, "code_fence", fenceStart, lineEnd, text.slice(fenceStart, lineEnd));
  inFence = false;
}
```

**Acceptance criteria:**
- [ ] A file with YAML frontmatter + code fences produces zone entries with `kind: "code_fence"`
- [ ] `cargo test` / `bun test` passes (scan.test.ts, repair.test.ts, validate.test.ts)
- [ ] Idempotence test passes on frontmatter+fence documents

---

## Gate 2 — Fix: Multi-line display math not detected [BLOCKER]

**What:** The math regex in `zones.ts` runs per-line inside the line loop. Display math spanning multiple lines (`$$` → content → `$$`) is never detected as a zone.

**Fix:** Display math (`$$...$$`) must be detected with a pre-pass over the full text before the line loop, or the zone scanner must be refactored to track multi-line math state across lines (similar to how fences are tracked). The simplest approach: pre-scan the full text for `$$...$$` blocks spanning newlines, record their offsets, then in the line loop skip zones already claimed by a display-math block.

**Acceptance criteria:**
- [ ] A file with a multi-line `$$...$$` block produces a `math_display` zone spanning all lines
- [ ] Repair rules do not touch content inside multi-line display math blocks
- [ ] KaTeX validation correctly processes multi-line display math

---

## Gate 3 — Fix: Hardcoded workspace root [PORTABILITY BLOCKER]

**What:** `cli.ts` line: `const workspaceRoot = resolve(import.meta.dir, "..", "..", "..", "..");` — hardcoded 4-level ascent. Tool is non-portable.

**Fix options (pick one):**
- **A (preferred):** Accept `--root <path>` CLI flag; default to `process.cwd()` if not supplied
- **B:** Walk up from the file being processed to find the nearest `.mdseal/` directory or a sentinel file (e.g. `package.json`)
- **C:** Walk up from `process.cwd()` to find workspace root by sentinel

Option A is simplest and most predictable for CI use.

**Acceptance criteria:**
- [ ] Tool works when invoked from any directory
- [ ] `--root` flag correctly scopes seal paths and file resolution
- [ ] No hardcoded `import.meta.dir` ascent remains

---

## Gate 4 — Fix: Restore command does not write

**What:** The `restore` branch in `cli.ts` validates conditions but never calls `restoreText()` or writes to disk. It exits as diagnostic-only even when all conditions are met.

**Fix:** After all validation checks pass, call `restoreText(model, seal)` from `restore.ts` and write the result if `has("--write")` is passed (or make write the default with `--dry-run` to suppress).

**Suggested structure:**
```ts
const { text, proposal } = restoreText(model, seal);
if (!has("--dry-run") && proposal.patches.length > 0) {
  writeFileSync(file, text, "utf-8");
  // record as wrote: true in result
}
```

**Acceptance criteria:**
- [ ] `restore --write` actually modifies the file
- [ ] `restore` without `--write` (or with `--dry-run`) reports what would be restored without writing
- [ ] `restore.test.ts` covers the write path

---

## Gate 5 — CLI: Add --help and --version

**What:** No help text. Unknown command throws a raw Error. No version output.

**Fix:** Add a `help()` function that prints usage. Handle missing/unknown command gracefully. Add `--version` that reads from `package.json`.

**Acceptance criteria:**
- [ ] `bun run mdseal --help` prints usage for all commands
- [ ] `bun run mdseal` (no args) prints usage, exits 0
- [ ] Unknown command prints usage + error message, exits 1
- [ ] `bun run mdseal --version` prints `0.1.0`

---

## Gate 6 — Fix: loneDollar zone marking too broad

**What:** A single unmatched `$` marks everything to end-of-line as `"unknown"` zone.

**Fix:** Only mark the lone `$` character itself as unknown, not the entire remainder of the line. Or: only mark as unknown if the `$` is followed by content that looks like it might be math (letter, digit, backslash).

**Acceptance criteria:**
- [ ] A price like `$19.99` does not poison subsequent zone detection on that line
- [ ] A shell variable like `$HOME` does not create an unknown zone spanning the rest of the line

---

## Gate 7 — Providers: Label as roadmap, not capability

**What:** 14 providers listed in registry, all `"status": "planned"`, zero functional. Docs present these as features.

**Fix:** Add a `ROADMAP.md` that lists planned providers. Update `providers list` output to clearly distinguish `planned` from `available`. Consider removing provider docs from the main README surface until at least one provider is functional.

**Acceptance criteria:**
- [ ] `providers list` output labels planned providers as `[planned — not yet functional]`
- [ ] A user running `providers doctor` gets a clear message that no providers are currently active

---

## Gate 8 — Expand repair rules (post-blocker work)

**What:** Two rules (inline math balance, unicode minus normalization) is thin for the positioning. This gate is downstream of Gates 1–2 because new rules need correct zone detection to be safe.

**Candidates for next rules (in priority order):**
1. Normalize escaped-bracket display math `\[...\]` to `$$...$$` or vice versa per dialect config
2. Strip zero-width spaces and other invisible Unicode from prose zones
3. Normalize em-dash `—` inserted by paste from word processors where an en-dash `–` was intended
4. Fix broken markdown link syntax `[text(url)` → `[text](url)` in safe zones

**Acceptance criteria per rule:**
- [ ] Rule has a corpus fixture (broken.md + golden.md + meta.json)
- [ ] Rule is blocked by zone protection (code fences, math, inline code)
- [ ] Rule is idempotent (running twice produces same result as once)
- [ ] Rule passes `bun test`

---

## Execution Order

```
Gate 1 (frontmatter/fence) → Gate 2 (multi-line math) → Gate 3 (workspace root) → Gate 4 (restore write)
                                                                                   ↓
                                                                    Gate 5 (--help) — parallel
                                                                    Gate 6 (loneDollar) — parallel
                                                                    Gate 7 (providers) — parallel
                                                                                   ↓
                                                                    Gate 8 (expand rules) — last
```

Gates 1–4 are blockers. Gates 5–7 are parallel improvements. Gate 8 is only safe after Gates 1–2 are closed.

---

## Graduation Criteria

mdseal graduates from `usables/` to the main repo when:

- [ ] Gates 1, 2, 3, 4 are closed
- [ ] `bun test` passes with no skips on the blocker paths
- [ ] The tool works when invoked from a directory other than its current nesting location
- [ ] The restore command demonstrably writes a file in a real test

Gates 5–8 are preferred but not required for graduation.

---

*Plan authored by Dispatch · 2026-06-28 · Evidence base: mdseal-assessment.md*

---
