---
- Assessment-By: Dispatch · Claude Sonnet 4.6
- SID: PROJECT_ASSESSMENT_MDSEAL_V1
- Date: 2026-06-28
- Project: CLAUDEBASE/usables/mdseal
- Version-Assessed: 0.1.0
- Verdict: Not-Yet — two blockers, strong core
---

# mdseal — Quality Audit

> *The manifest lies to the customs-house, never to the captain. This assessment lies to neither.*

---

## What It Is

A deterministic Markdown integrity tool for research packets carrying math, tables, code, images, and pasted/exported damage. Commands: `check`, `fix`, `seal`, `restore`, `sweep`, `corpus test`, `providers list/doctor`. Written in TypeScript/Bun. Creates sidecar JSON manifests in `.mdseal/` with hash records, zone spans, math spans, image witnesses, and hidden Unicode inventory.

The architectural philosophy is **refusal-first**: the tool explicitly refuses what it cannot do safely rather than guessing. This is sound.

---

## What Works and Works Well

**Refusal-first core.** The tool knows its own limits and encodes them. Seals refuse overwrite without `--force`. Hash-only seals refuse raw restoration. Restore refuses when source hash or context no longer matches. This is the right orientation for a tool that touches research documents — better to abort than corrupt.

**Protected zone awareness.** Repairs will not touch code fences, inline code, frontmatter, link destinations, image destinations, HTML blocks, or HTML inlines. The zone-aware repair gating is correctly implemented and the `safe()` / `mathSafe()` predicates in repairs.ts are defensible.

**KaTeX validation is real.** It actually calls the KaTeX parser, classifies failure kinds (syntax-error, unsafe-command, macro-error, unicode-warning, delimiter-error, unsupported-command), and refuses repairs that make math less parseable. The unsupported-command and unsafe-command lists are appropriate. This is the strongest individual feature in the tool.

**Test coverage is strong for 0.1.0.** Seventeen test files: idempotence, roundtrip, refusal, repair, restore, seal, validate, scan, rules-batch1, katex-validation, parser-comparison, html-image-parsing, image-ocr, image-witness, provider-doctor, seal-richness, parser-validation. For a tool this early, this is discipline.

**Seal format is well-designed.** Full vs hash-only modes are clearly distinguished. Context matching uses hashes around the candidate span, not offsets alone — this means restoration is robust to minor edits that shift byte positions. That's a non-obvious correctness decision made correctly.

**`IMPLEMENTATION_REPORT.md` is honest.** It lists explicitly what the tool does *not* do: live OCR, provider-driven mutation, whole-document rewriting, heuristic guessing inside protected zones, hard dependency on Pandoc, auto-restoration of tables or fences, rewriting unsupported KaTeX commands by guesswork. A tool that documents its own negative space is a tool that understands itself.

**Types are thorough.** `types.ts` at 393 lines with `Diagnostic`, `Patch`, `MdsealZoneSeal`, `MdsealMathSeal`, `MdsealFenceSeal`, `MdsealTableSeal`, `MdsealImageSeal`, `KatexValidationResult`, `MdsealManifest` and more — the domain model is well-articulated.

---

## What Is Genuinely Weak

### Bug 1 — Frontmatter kills fence detection (critical)

In `zones.ts`, the variable `frontmatterDone` controls code fence scanning:

```ts
let frontmatterDone = false;
if (text.startsWith("---\n")) {
  // ... parse frontmatter, set offset
  frontmatterDone = true;
}
for (const line of lines) {
  if (!frontmatterDone && line.startsWith("```")) {
    // fence detection
  }
}
```

When a file has frontmatter, `frontmatterDone` is set to `true` before the loop. Inside the loop, the fence detection condition `!frontmatterDone` is therefore always `false` — **fences are never detected for any file that opens with YAML frontmatter**. Research packets (the stated use case) almost always carry frontmatter. This means the core protection mechanism for code blocks silently fails on the exact document profile the tool targets. This is the most serious bug in the codebase.

### Bug 2 — Multi-line display math is not detected

The math zone regex in `zones.ts`:

```ts
const math = /\$\$[^]*?\$\$|\$[^$\n]+?\$/g;
```

...is applied per-line, inside the line iteration loop. Display math that spans multiple lines (`$$` on one line, content on the next, `$$` on the third) will not be detected. The zone scanner only finds display math if both delimiters appear on the same line. This means multi-line display math blocks — the dominant form in research documents — are processed as plain text and are not protected from repairs.

### Bug 3 — Hardcoded workspace root (portability blocker)

```ts
const workspaceRoot = resolve(import.meta.dir, "..", "..", "..", "..");
```

This resolves to four levels above `src/`, which happens to land at the chthonic-archive root given the current nesting at `CLAUDEBASE/usables/mdseal/src/`. Move the project to any other location — or try to install it as an actual tool — and all path resolution breaks silently. There is no error when the resolved root doesn't exist or doesn't contain the expected files. This is not portable and not suitable for any form of distribution.

### Vaporware providers dominate the feature surface

The provider registry has 14 entries. All 14 are `"status": "planned"`. The only functional provider is `null-provider`, which returns nothing by design. The OCR pillar (formula OCR, document OCR) and the embedding pillar are entirely scaffolded without implementation. This is fine at 0.1.0, but the docs (HF_PROVIDER_GUIDE.md, PROVIDER_REGISTRY.md, PROVIDER_DOCTOR.md) present this as a capability rather than a roadmap, which overstates what the tool currently does.

### Repair rules are thin for the positioning

Two repair rules: inline math balance, and unicode minus normalization. This is correctly conservative given the refusal-first philosophy. But the tool positions itself as a "Markdown integrity tool for research packets" — the gap between what the positioning suggests and what actually gets repaired is large. The rules should either be expanded or the positioning narrowed.

### No CLI help, usage, or version

```
$ bun run mdseal
Error: unknown command: undefined
```

No `--help`, no usage text, no `--version`. The CLI throws a raw error when called without arguments. This is not acceptable for a user-facing tool regardless of maturity. Even a two-line usage string changes the experience.

### loneDollar zone marking is too broad

When a line contains an unmatched `$`, the code marks everything from that dollar sign to the end of the line as `"unknown"` zone:

```ts
const loneDollar = line.indexOf("$");
if (loneDollar >= 0 && !line.match(/\$[^$\n]+?\$/)) push(zones, "unknown", lineStart + loneDollar, lineStart + line.length, line.slice(loneDollar));
```

This is too aggressive. A lone `$` followed by a price, a variable name, or a shell variable will poison all subsequent zone classification on that line.

### Restore command does not write

The `restore` command runs through condition checks and produces diagnostics but never calls `restoreText()` or writes output to disk — even when all conditions are satisfied. The implementation in `restore.ts` has the logic (`proposeRestoration`, `restoreText`) but the CLI branch does not call it. The command currently only validates whether a restore *would* be possible, then exits without doing it.

---

## Graduation Candidacy

**Not yet.** Two blockers:

1. The frontmatter/fence bug. Fix the condition: `frontmatterDone` should gate the frontmatter parsing only, not fence detection. Fences must be detected regardless.
2. The hardcoded workspace root. Resolve from the file being processed or from an explicit `--root` flag, not from `import.meta.dir`.

The restore command's non-write behavior is also a blocker if the command is meant to be functional, not just diagnostic.

Fix those three and the core — seal, check, KaTeX validation, zone-aware repair, refusal-first — is genuinely solid. The provider vaporware is fine to ship as scaffolding if it's clearly labelled as roadmap. The thin repair rules are acceptable at 0.1.0 given the correct conservative posture.

**Structural integrity assessment:** The architecture is sound. The philosophy is right. The test coverage shows intent. The bugs are real but addressable in a focused session. This is not abandoned — it is stopped at a fixable point.

---

*Assessed by Dispatch from CLAUDEBASE. Grilling evidence: zones.ts (fence/frontmatter logic), cli.ts (workspaceRoot, restore branch), restore.ts (proposeRestoration not called), providers/registry.ts (all planned), IMPLEMENTATION_REPORT.md.*
