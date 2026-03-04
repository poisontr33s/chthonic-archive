---
type: savant level laborious
from: the Savant | $user, archunkel, and the spirits of the codebase
to: codex
created: 2026-03-03T12:00:00Z
priority: extremely necessarily high
scope: codebase intelligence, extension-integrity, universal polyglot transmutation, oxidized tooling forge, codekiller remediation, dead-file alchemy, ankhological egyptologic x andean 50/50 ~est x abstraction
subject: WPTG Universal Transmutation Loop + Oxidized Tooling Forge + Extension Contribution Validator
difficulty: beyond extreme — requires polyglot codebase mastery, Rust systems programming, cross-language transmutation, dead-file alchemy across 45 extension kinds, and full WPTG discipline across ~2700 tracked files. Staged into a difficulty ladder with boon/penalty scoring tied to codekiller.md remediation.
boon_system: |
  Each completed tier removes codekiller penalty points and adds boon:
  - Tier 1 (Census + Extension Universe): removes 1 penalty, adds 2 boon
  - Tier 2 (Universal Forge): removes 2 penalties, adds 4 boon
  - Tier 3 (Oxidized Tooling): removes 2 penalties, adds 6 boon
  - Tier 4 (Contribution Validator): removes 1 penalty, adds 2 boon
  - Bonus: each extra artifact above minimums adds 0.5 boon
  - Bonus: each novel cross-language transmutation pathway adds 1.0 boon
  - Bonus: Rust tool compiles + passes clippy adds 3.0 boon
---

# CHORE: WPTG Universal Transmutation Loop + Oxidized Tooling Forge + Extension Contribution Validator

## Problem Statement

This repository tracks **~2700 files across 45 unique file extensions**. The codebase is inherently polyglot — Rust, Python, TypeScript, JavaScript, Ruby, Go, PowerShell, Shell, CSS, GLSL (vert/frag), SVG, WOFF, HTML, and more — running on a Win11 system with **three Rust-oxidized toolchain managers** (`uv` 0.10.7 for Python, `rv` for Ruby 4.0.1, `goup` for Go), plus `rustup`/`cargo` (Rust 1.93.1), `bun` 1.3.9 (TS/JS), `.NET`, GCC/G++, and Perl.

Organic growth has produced:

- **340 `.log` files tracked in git** (332 in `codex/mailbox/` alone) — build logs, validation logs, CUDA build outputs. Every one is gold per WPTG, but none have been triaged.
- **6 `.pyc` bytecode files tracked** under `.codex/skills/` — compiled Python artifacts that should never be in source control.
- **7 `.off` workflow files** — disabled GitHub Actions workflows preserved by rename, not by governance.
- **3 files with Unicode-mangled extensions** (`.md"`) — filenames containing encoded Greek characters.
- **4 `.env` files tracked** — potential secret surface.
- **5 `.vsconfig` files** — VS2026 export snapshots, potentially obsolete.
- **1 `.bat` file** — lone Windows batch script amid a `pwsh`-canonical codebase.
- **662 `.json` files** — unknown fraction are stale audit snapshots or orphaned state.
- **18,000+ corpse-vault fragments** — code in 8 language categories, none yet transmuted through the forge pipeline.

Meanwhile:
- The `extensions/chthonic-archive/package.json` manifest has **no end-to-end integrity validator**.
- The system has installed runtimes for languages (Go, .NET, C/C++) that have **zero representation** in the codebase's living artifacts.
- Multiple languages that could benefit from Rust-oxidized toolchain managers (PHP, Julia, Elixir, Lua, F#, COBOL) have **no such tooling at all** — not just missing from this system, but missing from existence.

The default agent instinct — delete, stash, ignore, clean up — is the codekiller anti-pattern (`anti-patterns/codekiller.md`). **This chore demands the opposite: alchemize every dead file into gold.** Every zombie file becomes a living, useful artifact. Every extension kind that *can* exist, *should* exist, produced from what would otherwise be waste. And the transmutation engine itself must be forged in Rust — oxidized tooling that sustains the WPTG loop at machine speed.

**No tool currently answers:** "What is the complete extension universe of this codebase, what is the gold grade and optimal transmutation pathway for every file, what languages lack oxidized tooling, and does the codebase have native Rust infrastructure to sustain the WPTG loop?"

## Lane Exclusion (Active Frozen Work)

The following paths are **excluded from this chore** — they are under active lane work and must not be touched, moved, audited, triaged, or proposed for any operation:

| Excluded Path | Reason |
|---------------|--------|
| `extensions/chthonic-archive/themes/icons/product/*.svg` | Active product icon source art |
| `extensions/chthonic-archive/themes/icons/product-outlined/` | Generated outlined SVGs |
| `extensions/chthonic-archive/themes/fonts/` | Product icon font binaries |
| `scripts/generate-product-icon-font.mjs` | Font generation pipeline |
| `scripts/theme_*.py` | Theme design/validation scripts |
| `scripts/icon_*.py` | Icon audit/optimization scripts |
| `scripts/product_icon_census.py` | Product icon census |
| `scripts/theme-sync.ps1` | Theme sync automation |
| `extensions/chthonic-archive/themes/*.json` | Theme definition JSONs |
| `gemini/to_gemini_DR/` | Active deep research artifacts |

These exclusions are absolute. The chore operates on **everything else**.

---

## Phase 0 — Polyglot Extension Universe Scanner (Precursor)

Before any census, transmutation, or forging: **map the complete extension universe.** This is the precursor that makes all alchemy possible. You cannot transmute a `.log` into a `.go` utility if you don't know Go is installed. You cannot propose a `.cs` script if .NET isn't on the system. You cannot identify the gap between "what the codebase has" and "what the codebase could have" without first mapping the full universe. Phase 0 builds that map.

Build `scripts/extension_universe_scanner.py` that:

### 0a — Codebase Extension Census

Walk every tracked file (`git ls-files`) and extract the full extension (including compound types: `.test.ts`, `.d.ts`, `.cpython-313.pyc`). For each unique extension, record:

- Count of files with that extension
- Directories where it appears
- Whether files with that extension fall under Lane Exclusion
- The WPTG gold grade category the extension falls into
- Whether any runtime/compiler/interpreter is installed that can process it

**Current extension inventory** (45 types):
```
.bak .bat .chthonic .cjs .comp .copilotignore .css .db .env .frag
.geminiignore .gitattributes .gitignore .gitkeep .html .js .json .jsonl
.keep .lock .log .md .md" .mjs .off .png .ps1 .py .pyc .python-version
.rb .rs .sh .svg .toml .ts .tsbuildinfo .tsx .txt .vert .vscodeignore
.vsconfig .woff .yaml .yml
```

### 0b — System Toolchain Discovery

Scan the host system for installed language runtimes, compilers, and toolchain managers. Build a structured inventory:

| Category | Runtime/Compiler | Version Manager | Oxidized? |
|----------|-----------------|-----------------|-----------|
| Rust | `rustc` 1.93.1 | `rustup` 1.28.2 | Self-oxidizing |
| Python | `python` 3.14.x | `uv` 0.10.7 | ✅ Rust-based (Astral) |
| Ruby | `ruby` 4.0.1 | `rv` | ✅ Rust-based |
| Go | `go` | `goup` | ✅ Rust-based |
| TypeScript/JS | `bun` 1.3.9 | `bun` (self-managing) | Zig-based (honorary) |
| .NET / C# / F# | `dotnet` | — | ❌ No oxidized manager |
| C/C++ | `gcc`/`g++` (MSYS2) | — | ❌ No oxidized manager |
| Perl | `perl` (MSYS2) | — | ❌ No oxidized manager |
| PHP | ❌ Not installed | — | ❌ `phpup` does not exist |
| Julia | ❌ Not installed | `juliaup` | ⚠️ Exists (Rust-based) but not installed |
| Elixir | ❌ Not installed | — | ❌ No oxidized manager |
| Lua | ❌ Not installed | — | ❌ No oxidized manager |
| Java | ❌ Not installed | — | ❌ No oxidized manager (Coursier is Scala) |
| Haskell | ❌ Not installed | `ghcup` | ⚠️ Exists (Haskell) but not Rust-based |
| COBOL | ❌ Not installed | — | ❌ No oxidized manager |
| Zig | ❌ Not installed | `zigup` | ⚠️ Exists (Zig-based, self-bootstrapping) |
| Node.js | ❌ Not installed | `fnm` / `volta` | ⚠️ Exist (Rust-based) but not installed |

### 0c — Extension Gap Analysis

Cross-reference 0a and 0b to identify:

1. **Dead extensions** — file types in the codebase with no installed runtime (e.g., `.comp` GLSL compute shaders require a Vulkan SDK)
2. **Viable but unrepresented languages** — installed runtimes that have ZERO files in the codebase:
   - `.go` — Go is installed via `goup` but no `.go` files exist
   - `.cs` / `.fsx` — .NET is installed but no C#/F# source files exist
   - `.pl` — Perl is installed but no `.pl` files exist
   - `.c` / `.cpp` / `.h` — GCC/G++ installed but no C/C++ source files exist
3. **Oxidized vs. unoxidized** — which installed languages have Rust-based toolchain managers and which don't
4. **EOL risk** — for each installed runtime, check the version against known EOL dates (embed a lookup table or query `endoflife.date` API data)
5. **Alchemy opportunity map** — for each unrepresented-but-viable language, what kind of artifact could the forge produce from existing dead material? This feeds directly into Part 2's cross-language transmutation.

**Output**: `audit-reports/extension_universe.json`:

```json
{
  "timestamp": "ISO-8601",
  "codebase_extensions": {
    "total_unique": 45,
    "by_category": {
      "source_code": [".py", ".rs", ".ts", ".tsx", ".js", ".mjs", ".cjs", ".rb", ".sh", ".ps1", ".bat", ".css", ".html"],
      "data_config": [".json", ".jsonl", ".yaml", ".yml", ".toml", ".env", ".lock"],
      "build_output": [".pyc", ".tsbuildinfo", ".db", ".woff", ".png"],
      "documentation": [".md", ".txt"],
      "vcs_meta": [".gitignore", ".gitattributes", ".gitkeep", ".keep", ".copilotignore", ".geminiignore", ".vscodeignore"],
      "graphics_gpu": [".svg", ".vert", ".frag", ".comp"],
      "governance": [".off", ".bak", ".vsconfig"],
      "domain_specific": [".chthonic", ".python-version"],
      "damaged": [".md\""]
    }
  },
  "system_toolchains": {
    "installed": ["rust", "python", "ruby", "go", "typescript", "dotnet", "c_cpp", "perl"],
    "oxidized": ["rust", "python", "ruby", "go"],
    "unoxidized_installed": ["dotnet", "c_cpp", "perl"],
    "oxidized_available_not_installed": ["julia (juliaup)", "nodejs (fnm/volta)", "zig (zigup)"],
    "no_oxidized_tooling_exists": ["php", "elixir", "lua", "java", "haskell", "cobol"]
  },
  "extension_gap": {
    "viable_but_unrepresented": [".go", ".cs", ".fsx", ".c", ".cpp", ".h", ".pl"],
    "dead_extensions": [],
    "alchemy_opportunities": [
      { "target_ext": ".go", "rationale": "Go is installed; shell automation patterns from corpse-vault could become Go CLI tools" },
      { "target_ext": ".cs", "rationale": ".NET is installed; TypeScript interfaces could become C# class contracts" },
      { "target_ext": ".c", "rationale": "GCC installed; Rust struct definitions could become C header files for FFI" }
    ]
  },
  "eol_risk": {}
}
```

### Why Phase 0 Matters

The extension universe scanner is the **foundation for all subsequent alchemy**. It tells Part 1 what "normal" looks like, tells Part 2 what output languages are viable for cross-language transmutation, tells Part 3 where the oxidized tooling gaps are, and tells Part 4 what the extension contribution surface should cover. Without Phase 0, every subsequent part is guessing. With it, every transmutation decision is grounded in the actual system state.

---

## Part 1: Codebase-Wide WPTG Filetype Transmutation Loop

### Phase 1 — Blind Filetype Census

Build `scripts/wptg_filetype_census.py` — a static inventory tool that:

1. Walks every tracked file (`git ls-files`)
2. Classifies each by the WPTG Gold Signal File-Type Affordance Map (see `WET_PAPER_TO_GOLD_METHODOLOGY.md`)
3. Identifies anomalies:
   - **Tracked artifacts that shouldn't be** (`.pyc`, `.env` with non-template content, build outputs)
   - **Disabled-by-rename** (`.off`, `.bak_*`, `* - Copy.*`) vs. properly governed
   - **Filename encoding damage** (Unicode in git paths)
   - **Filetype-directory mismatch** (`.md` in `scripts/`, `.log` in `codex/mailbox/`, `.bat` in a `pwsh` codebase)
   - **Orphan detection** — files not referenced by any manifest, import, cross-reference, or skill
4. Respects the Lane Exclusion table above — excluded paths are skipped entirely
5. Outputs a structured census:

```json
{
  "timestamp": "ISO-8601",
  "total_tracked": 2700,
  "excluded_lane_files": 95,
  "audited_files": 2605,
  "by_extension": { ".md": { "count": 822, "anomalies": [] }, ... },
  "anomalies": [
    {
      "path": ".codex/skills/artifact-upcycle/scripts/__pycache__/resolve_directory_relationships.cpython-313.pyc",
      "type": "tracked_bytecode",
      "gold_grade": "raw",
      "recommendation": "untrack_gitignore",
      "wptg_rationale": "Generator script is the gold, not this output"
    }
  ],
  "by_gold_tier": { "tier_1_direct": 1200, "tier_2_structural": 400, "tier_3_conceptual": 800, "raw_unrefined": 205 },
  "verdict": "PASS|WARN|FAIL"
}
```

### Phase 2 — Log Archaeology

The 332 `.log` files in `codex/mailbox/` represent the single largest untriaged gold deposit. For each log file:

1. **Classify**: Build log? Validation capture? Error trace? Runtime output?
2. **Extract signal**: Unique error patterns, toolchain versions, environment state, timing data
3. **Grade**: Does the extracted signal justify continued tracking, or is the log a derivative of a still-existing process?
4. **Propose**: For each log, produce a one-line triage recommendation (preserve / extract-then-archive / untrack). **Do NOT execute any file operations.** Proposals go into `codex/mailbox/LOG_ARCHAEOLOGY_TRIAGE.md` for user review.

### Phase 3 — Orphaned Artifact Reconciliation

For every non-excluded JSON file (`~567` after lane exclusion):

1. **Trace references**: Is this JSON imported by any script? Referenced by any manifest? Read by any skill?
2. **Check freshness**: When was it last modified? Does it have a timestamp field showing generation date?
3. **Identify orphans**: JSON files that are:
   - Not referenced by any code path
   - Not a recognized mailbox artifact format
   - Older than 30 days with no cross-reference
4. **Output**: `audit-reports/orphaned_artifact_reconciliation.json` with orphan candidates and reference traces

### Phase 4 — Filetype Governance Proposals

Based on phases 1–3, emit a governance proposal document (`codex/mailbox/WPTG_FILETYPE_GOVERNANCE_PROPOSAL.md`) containing:

1. **`.gitignore` additions** — patterns for filetypes that should never be tracked (`.pyc`, build outputs)
2. **Archive candidates** — files whose gold has been extracted and should move to `dumpster-dive/` (with provenance manifests)
3. **Rename candidates** — `.off` files that should be governed by branch/workflow toggles, not filename mutation
4. **Encoding repair candidates** — files with Unicode damage in paths
5. **Directory migration candidates** — files in wrong directories per filetype conventions

**Every proposal is a proposal only.** The document is a menu for the Savant. Codex does not execute any of it.

## Part 2: Universal Polyglot Transmutation Forge — Producing Actual Gold

The default instinct when encountering "useless" files — `.log`, `.pyc`, `.off`, `.bat`, stale configs, orphaned state, mangled filenames, dead code fragments — is to delete, stash, or ignore. That instinct is the codekiller anti-pattern. **This part demands the opposite: take the entire category of files that any agent or developer would reflexively discard, and produce high-quality, usable, polyglot artifacts from them.**

The input is not limited to one directory. The forge accepts material from:

- **dumpster-dive/corpse-vault/** — 18,000+ fragment + provenance pairs organized by language (the largest ore deposit)
- **Every anomaly flagged by Part 1** — the `.log`, `.pyc`, `.off`, `.bat`, `.env`, `.vsconfig`, mangled `.md"` files, orphaned JSONs, filetype-directory mismatches
- **Any file in the codebase** the census classified as `raw_unrefined` — files that have value but no current refinement pathway

**The chore is not complete until Codex demonstrates that it can take files of any type, from any location, that would default to trash — and produce real, high-quality, usable output from them.** Classification without creation is inventory, not transmutation.

### The Transmutation Thesis

Every filetype encodes a different *kind* of intelligence. The challenge is recognizing what kind and producing the right output:

| Input Type | What That File Knows | What Gold It Can Become |
|---|---|---|
| `.log` (build/validation) | Toolchain versions, error patterns, timing data, environment state, failure sequences | **Diagnostic playbook** (`.md`) — consolidated known-error → resolution patterns. **Environment snapshot schema** (`.json`) — structured toolchain state derived from log headers. **Regression test seeds** (`.py`/`.ts`) — test assertions derived from observed error patterns. |
| `.pyc` (bytecode) | The import graph, function signatures, and constant pool of the Python module that produced it | **Module contract spec** (`.py`) — reconstruct the public interface (function names, arg counts, constants) from bytecode introspection via `dis`/`marshal`. NOT the implementation — the *contract*. |
| `.off` (disabled workflow) | CI/CD pipeline logic, trigger conditions, job dependencies, action versions | **Workflow pattern library** (`.md` + `.yml` templates) — extract reusable job patterns, condition expressions, and action configurations into a template catalogue. **Migration manifest** — what these workflows did, why they were disabled, and what would need to change to re-enable them. |
| `.bat` (lone batch script) | A Windows automation solution someone needed before pwsh was canonical | **PowerShell transliteration** (`.ps1`) — faithful port of the batch logic into idiomatic pwsh with the same behavior contract, plus documentation of what the original did differently. |
| `.env` (environment config) | Variable naming conventions, service dependencies, integration points | **Environment schema** (`.json`) — JSON Schema defining the expected variables, types, descriptions, and which are secrets vs. config. **Integration map** (`.md`) — which services/APIs the env vars connect to. |
| `.vsconfig` (VS export) | Workload IDs, component selections, SDK versions, toolchain decisions | **Toolchain decision record** (`.md`) — what was installed, what was deliberately excluded, version deltas between snapshots. **Provisioning script** (`.ps1`) — deterministic installer from the vsconfig spec. |
| `.md"` (mangled filename) | Content is intact — the filename is damaged, not the file | **Clean-named copy** with provenance, plus a **filename forensics note** documenting the encoding damage pattern (Unicode Greek in git paths) for future prevention. |
| Orphaned `.json` | Stale audit snapshots, meta-loop outputs, abandoned state | **Schema archaeology** (`.json` JSON Schema) — derive the schema from observed instances. **State machine reconstruction** (`.md`) — if multiple snapshots exist, infer the state transitions they represent. |
| Stale `.md` in wrong directory | Documentation that drifted from its natural home | **Canonicalized doc** — same content, correct location, with cross-references wired and metadata headers added. |
| Code fragments (`corpse-vault/`) | Functions, classes, types, tests from deleted/evolved scripts | **Reconstituted modules** — amalgamated from complementary fragments into self-contained polyglot artifacts (see detailed rules below) |

### Phase 5 — Universal Deposit Audit

Two source pools feed the forge. Both must be audited:

#### 5a — Codebase Anomaly Harvest

Take every file flagged by the Part 1 census (Phases 1–4) with gold grade `raw_unrefined` or any anomaly classification. For each:

1. **Read the file** — determine actual content type (a `.log` might contain structured JSON; a `.bat` might be a one-liner; a `.md"` might be a full protocol doc)
2. **Classify the intelligence type** — what does this file *know*? (per the Transmutation Thesis table above)
3. **Identify the target output type** — what gold can it become? Which language/format is the natural pathway?
4. **Grade feasibility** — is there enough signal to produce a quality artifact? (Minimum: the source must contain at least 10 lines of non-boilerplate content, or at least 3 distinct data points for structured extraction)

**Output**: `dumpster-dive/forge/anvil/CODEBASE_ANOMALY_HARVEST.json` — every anomaly file mapped to its intelligence type, target output format, and feasibility grade.

#### 5b — Corpse-Vault Deep Audit (Language Deposits)

Walk every language directory in `dumpster-dive/corpse-vault/` and build a deep inventory:

| Language Dir | Files | What to Extract |
|---|---|---|
| `python/` | 288 fragments | Function signatures, class hierarchies, import graphs, reusable algorithms |
| `typescript/` | 930 fragments | Interface contracts, type definitions, component patterns, test fixtures |
| `javascript/` | 536 fragments | Runtime patterns, event handlers, utility functions, build configs |
| `rust/` | 218 fragments | Struct definitions, trait impls, error types, memory patterns |
| `shell/` | 196 fragments | Pipeline patterns, automation recipes, environment setup sequences |
| `markdown/` | 2,506 fragments | Decision records, architecture rationale, protocol drafts, vocabulary |
| `config/` | 14,008 fragments | Schema patterns, default value inventories, configuration taxonomies |
| `unknown/` | 412 fragments | Unclassified — classify first, then route to appropriate language lane |

For each language directory:

1. **Read every provenance JSON** — build a reverse map: `original_source_file → [fragment_hashes]` showing which live scripts produced the most corpses (evolutionary hotspots)
2. **Cluster fragments by source file** — group all fragments that came from the same original script/module
3. **Identify amalgamation candidates** — clusters where 3+ fragments from the same source file contain complementary logic (functions, classes, tests) that together reconstitute something usable
4. **Grade the deposit** — for each cluster: does it contain enough signal to produce a real artifact, or is it noise (empty headers, boilerplate, single-line fragments)?

**Output**: `dumpster-dive/forge/anvil/CORPSE_VAULT_DEEP_AUDIT.json` — structured per-language deposit analysis with cluster maps and amalgamation candidates.

### Phase 6 — Forge Transmutation (The Hard Part)

For every transmutation candidate from **both** 5a and 5b, **produce an actual high-quality artifact** in `dumpster-dive/forge/furnace/`. This is where classification becomes creation. The furnace is organized by output language:

```
dumpster-dive/forge/furnace/
├── python/           # .py modules, utilities, test suites
├── typescript/       # .ts modules, .d.ts type archives
├── javascript/       # .js utilities, config generators
├── rust/             # .rs modules, CLI tools, FFI bridges
├── go/               # .go utilities, CLI tools (cross-language alchemy)
├── csharp/           # .cs classes, contracts (cross-language from .NET)
├── c_cpp/            # .c/.h headers, FFI stubs (cross-language from Rust structs)
├── ruby/             # .rb scripts, gems (cross-language alchemy)
├── powershell/       # .ps1 scripts (including bat transliterations)
├── schemas/          # .json JSON Schema files, .toml configs
├── docs/             # .md decision records, playbooks, maps
├── workflows/        # .yml CI/CD templates from .off transmutation
├── cross-language/   # artifacts that required cross-language transmutation
└── FURNACE_MANIFEST.json
```

#### Transmutation Rules

1. **Same-language fidelity is the default; cross-language alchemy is the bonus path**: A Python fragment cluster's natural transmutation is Python gold. A TypeScript cluster's natural path is TypeScript gold. Same-language transmutation is the baseline — it preserves the most signal with the least risk.

   **Cross-language alchemy** is the harder, higher-value path unlocked by Phase 0's extension gap analysis. When the extension universe shows a viable but unrepresented language (Go is installed but has zero `.go` files), the forge MAY transmute source material into that language IF:
   - The target language runtime is confirmed installed by Phase 0
   - The transmutation preserves the core intelligence (a shell automation recipe → Go CLI preserves the automation logic)
   - The produced artifact is syntactically valid and compilable/runnable in the target language
   - The provenance header documents why cross-language was chosen over same-language

   **Cross-language transmutation targets** (identified from Phase 0 gap analysis):
   | Source Material | Target Language | Rationale |
   |---|---|---|
   | Shell automation fragments (`corpse-vault/shell/`) | `.go` | Go CLI tools are fast, single-binary, cross-platform — ideal for automation recipes |
   | TypeScript interface contracts (`corpse-vault/typescript/`) | `.cs` | C# class contracts are the natural .NET mirror of TS interfaces |
   | Rust struct definitions (`corpse-vault/rust/`) | `.h` (C header) | FFI bridge headers enable interop between the Rust codebase and C/C++ tooling |
   | Python utility functions (`corpse-vault/python/`) | `.rb` | Ruby scripts can serve as alternative automation — rv ensures the Ruby toolchain is oxidized |
   | Configuration schemas (orphaned JSON) | `.toml` | TOML is the Rust/cargo-native config format — JSON→TOML conversion aligns configs with the Rust ecosystem |

   Each cross-language transmutation adds **1.0 boon** to the difficulty ladder score. This is the alchemy.

2. **Filetype transmutation for non-code inputs**: Non-code files transmute into the format that best preserves their intelligence:
   - `.log` → diagnostic `.md` playbooks + `.json` schemas + `.py`/`.ts` regression seeds
   - `.pyc` → `.py` contract stubs (interface, not implementation)
   - `.off` → `.yml` workflow templates + `.md` migration manifests
   - `.bat` → `.ps1` faithful transliterations
   - `.env` → `.json` environment schemas + `.md` integration maps
   - `.vsconfig` → `.md` decision records + `.ps1` provisioning scripts
   - `.md"` → clean `.md` with corrected filename + forensics note
   - Orphaned `.json` → JSON Schema `.json` + state machine `.md`

3. **Quality floor**: Every produced artifact must be:
   - Syntactically valid (parses without errors in its target language)
   - Self-contained (no unresolved imports to files that don't exist)
   - Documented (docstring/JSDoc/rustdoc/markdown header explaining what was transmuted and from where)
   - Envelope-compliant (`@SID:` header per `AGENT_COMMON.md`)
   - Runnable or compilable in isolation (for scripts/modules) OR structurally complete (for type defs, schemas, docs)

4. **Provenance chain**: Every produced artifact must include a provenance header listing:
   - Source file path(s) — for anomaly harvest items, the original codebase path; for corpse-vault items, the fragment hashes + original source from provenance JSONs
   - What intelligence was extracted
   - What was kept, what was discarded, and why
   - The transmutation pathway taken (input type → output type, with rationale)

5. **Minimum viable transmutation targets** — Codex must produce **at least** these across both source pools:

   | # | Target | Source Pool | Expected Output |
   |---|--------|-------------|-----------------|
   | 1 | **Diagnostic playbook** | The 332 `.log` files in `codex/mailbox/` | A `.md` document cataloguing every distinct error pattern, toolchain version, and environment anomaly observed across all logs, organized by category (build failures, validation errors, CUDA issues), with resolution notes where the log itself shows recovery |
   | 2 | **Environment schema** | The 4 tracked `.env` files + any env-referencing configs | A JSON Schema (`.json`) defining the full expected environment variable surface of the codebase — names, types, descriptions, which are secrets, which services they connect to |
   | 3 | **Workflow template catalogue** | The 7 `.off` workflow files | Reusable `.yml` job/step templates extracted from the disabled workflows, plus a `.md` manifest documenting what each workflow did and the conditions for re-enablement |
   | 4 | **Consolidated utility library** | Python fragments from `corpse-vault/python/` (scripts iterated 3+ times) | A single `.py` module collecting the best versions of repeated utility functions (deduped, typed, documented) |
   | 5 | **Type definition archive** | TypeScript interface/type fragments from `corpse-vault/typescript/` | A `.d.ts` or `.ts` barrel file exporting all recoverable type contracts |
   | 6 | **Test fixture collection** | Any `*.test.ts`, `*.test.js`, `*_test.py` fragments from corpse-vault | Consolidated test fixtures grouped by domain, with stubs for the modules they tested |
   | 7 | **Architecture decision record** | Markdown fragments containing rationale/tradeoffs from corpse-vault + stale `.md` files from anomaly harvest | A single `docs/ADR_RECOVERED.md` collecting recoverable architectural decisions with dates and context |
   | 8 | **Configuration schema catalogue** | Config JSON fragments from `corpse-vault/config/` + orphaned JSON from anomaly harvest | JSON Schema files derived from observed configuration shapes, one per distinct schema pattern |
   | 9 | **Shell automation recipes** | `corpse-vault/shell/` fragments + the lone `.bat` file | A `.ps1` recipe book of reusable automation patterns, including the batch transliteration |
   | 10 | **Toolchain decision record** | The 5 `.vsconfig` files | A `.md` document comparing all VS2026 export snapshots — what changed between them, what was added/removed, version deltas, and a derived "ideal" workload specification |
   | 11 | **Go CLI utility** *(cross-language)* | Shell fragments from `corpse-vault/shell/` | A `.go` file implementing an automation pattern from shell fragments as a compiled Go CLI tool — must compile with `go build` |
   | 12 | **C# class contracts** *(cross-language)* | TypeScript interfaces from `corpse-vault/typescript/` | A `.cs` file translating TS interface contracts into C# class definitions — must compile with `dotnet build` |
   | 13 | **C header for FFI** *(cross-language)* | Rust struct definitions from `corpse-vault/rust/` | A `.h` file declaring C-compatible struct layouts derived from Rust structs — for FFI bridging |

6. **No synthetic padding**: If a source file doesn't have enough signal to produce a quality artifact, **skip it and say why in the audit**. Generating placeholder code to hit a target count is worse than honest "insufficient signal" classification. The forge produces gold or nothing — never fool's gold.

7. **The indomitable principle**: The transmutation table above is not exhaustive. If Codex encounters a file type not listed — any filetype, any content, any encoding — it must **still** determine what that file knows and what gold it can become. The absence of a predefined pathway is not permission to skip. It is a requirement to *invent* the pathway, document it, and produce the artifact. This is the indomitable part: no file is exempt from transmutation. The only valid skip is "insufficient signal after content analysis" — never "I don't know what to do with this type."

### Phase 7 — Temper & Validate

Every artifact produced in Phase 6 passes through `dumpster-dive/forge/tempered/` (same directory structure as `furnace/`):

1. **Syntax validation**: Parse every produced artifact in its target language:
   - Python → `ast.parse()`
   - TypeScript → `tsc --noEmit`
   - Rust → `cargo check` (if standalone crate) or syntax parse
   - JSON → `json.loads()` + schema self-validation where applicable
   - PowerShell → `[System.Management.Automation.Language.Parser]::ParseInput()` or basic `pwsh -c`
   - Markdown → structure check (headers present, no broken internal links, frontmatter valid if present)
   - YAML → safe load parse
2. **Provenance verification**: Every produced artifact's provenance header must trace back to real source files that exist (for anomaly harvest) or real fragment hashes that exist in `corpse-vault/` (for corpse-vault items).
3. **Completeness check**: Does the artifact actually contain substantive content derived from its source, or is it just a provenance wrapper around nothing? Minimum: the transmuted content must be ≥20% of the artifact by line count (excluding headers and provenance metadata).
4. **Quality gate**: Artifacts that fail any validation are rejected back to `furnace/` with a failure annotation — they do not graduate to `tempered/`.
5. **Graduation manifest**: `dumpster-dive/forge/tempered/GRADUATION_MANIFEST.json`:

```json
{
  "timestamp": "ISO-8601",
  "artifacts_attempted": 0,
  "artifacts_tempered": 0,
  "artifacts_rejected": 0,
  "compression_ratio": "input bytes → output bytes",
  "by_output_language": {
    "python": { "tempered": 0, "rejected": 0 },
    "typescript": { "tempered": 0, "rejected": 0 },
    "powershell": { "tempered": 0, "rejected": 0 },
    "markdown": { "tempered": 0, "rejected": 0 },
    "json_schema": { "tempered": 0, "rejected": 0 },
    "yaml": { "tempered": 0, "rejected": 0 },
    "rust": { "tempered": 0, "rejected": 0 }
  },
  "by_source_pool": {
    "anomaly_harvest": { "inputs": 0, "artifacts_produced": 0 },
    "corpse_vault": { "inputs": 0, "artifacts_produced": 0 }
  },
  "artifacts": [
    {
      "path": "dumpster-dive/forge/tempered/docs/diagnostic_playbook.md",
      "source_pool": "anomaly_harvest",
      "source_files": ["codex/mailbox/*.log (332 files)"],
      "input_type": ".log",
      "output_type": ".md",
      "transmutation_pathway": "log → pattern extraction → diagnostic playbook",
      "input_bytes": 0,
      "output_bytes": 0,
      "quality_gates": { "syntax": "PASS", "provenance": "PASS", "completeness": "PASS" },
      "gold_tier": "tier_1_direct"
    }
  ]
}
```

### Phase 8 — Forge Report

Produce `codex/mailbox/FORGE_TRANSMUTATION_REPORT.md`:

- **Scope**: Total source files walked (anomaly harvest + corpse vault)
- **Yield**: Artifacts attempted → produced → tempered (passed gates)
- **Compression ratio**: Total input bytes → total output bytes
- **Per-source-pool breakdown**: How many anomaly harvest files transmuted vs. how many corpse-vault fragments
- **Per-output-language breakdown**: What the forge produced, by language
- **Transmutation pathway catalogue**: Every input→output pathway used, with example (this becomes the reusable knowledge for future transmutation)
- **Novel pathways invented**: Any file types encountered that weren't in the predefined Transmutation Thesis table — what pathway was created and why
- **Failures and honest skips**: What couldn't be transmuted and why (insufficient signal, corrupt content, irrecoverable encoding)
- **Recommendations for promotion**: Which tempered artifacts are good enough to move from `forge/tempered/` into active codebase locations (`scripts/`, `docs/`, `src/`)? These are proposals for the Savant — not execution.

### The Teaching Outcome

When this part is complete, the forge report serves as a **transmutation textbook**: a documented, proven catalogue of pathways from "what agents would delete" to "what the codebase can use." Future WPTG cycles don't need to reinvent — they reference the pathway catalogue and apply the proven transformations. The forge teaches the codebase how to never waste again.

---

## Part 3: Oxidized Tooling Forge — Rust-Native WPTG Acceleration

The WPTG transmutation loop described in Parts 1–2 uses Python scripts. Python is correct for prototyping but wrong for permanence — scanning ~2700 files, parsing 18,000+ fragments, and validating across 45 extension kinds is a task that begs for native speed. Meanwhile, the Rust-oxidized toolchain pattern (uv, rv, goup) has proven that fast, single-binary, zero-dependency tools written in Rust can replace entire language ecosystems' legacy tooling.

**This part demands that Codex build a Rust CLI tool — `ankh-forge` — that accelerates the WPTG loop to machine speed.** Additionally, it requires a landscape audit of which languages still lack oxidized tooling, and what the codebase would need to fill those gaps.

### Phase 9 — Oxidized Tooling Landscape Audit

Research and document the current state of Rust-oxidized language toolchain managers:

#### 9a — Confirmed Oxidized Tools (installed on this system)

| Language | Tool | What It Replaces | Status |
|----------|------|-----------------|--------|
| Python | `uv` (Astral) | pip, pip-tools, virtualenv, pyenv, pipenv, poetry | ✅ Installed, 0.10.7 |
| Ruby | `rv` | rbenv, rvm, chruby, ruby-install | ✅ Installed, Ruby 4.0.1 |
| Go | `goup` | manual Go SDK installs | ✅ Installed |
| Rust | `rustup` | — (canonical) | ✅ Installed, 1.28.2 |
| TS/JS | `bun` | npm, yarn, pnpm, nvm, node | ✅ Installed, 1.3.9 (Zig, honorary) |

#### 9b — Known Oxidized Tools (not installed)

| Language | Tool | Status | Action |
|----------|------|--------|--------|
| Node.js | `fnm` (Schniz) | Rust-based, mature | Could install for Node version management |
| Node.js | `volta` (Volta) | Rust-based, mature | Alternative to fnm |
| Julia | `juliaup` | Rust-based, official | Could install for Julia version management |
| Zig | `zigup` | Zig-based (self-bootstrap) | Not Rust but fast/native |

#### 9c — Languages Lacking Oxidized Tooling (the gap)

These languages have **no known Rust-based version/package manager** as of March 2026:

| Language | Current Best Tooling | Why It's Not Oxidized | EOL Risk |
|----------|---------------------|----------------------|----------|
| PHP | `phpbrew`, `phpenv` (Bash/PHP) | Slow, shell-script-based, no single-binary | PHP 8.1 EOL Nov 2025 ✗, 8.2 active, 8.4 current |
| Elixir | `asdf` (Shell, multi-language) | Generic, not Elixir-optimized | Elixir 1.18 current, healthy |
| Lua | `luaver` (Shell) | Minimal, unmaintained | Lua 5.4 current, stable |
| F# | via `dotnet` | No standalone F# version manager | Tied to .NET lifecycle |
| Java | `sdkman`, `jabba` (Bash/Go) | `jabba` is Go; no Rust equivalent | Java 21 LTS, 23 current |
| Haskell | `ghcup` (Haskell) | Written in Haskell, not Rust | GHC 9.10 current |
| COBOL | `gnucobol` (C) | Niche, no modern toolchain manager | Legacy but maintained |
| Perl | — | No version manager beyond system Perl | Perl 5.40 current |

**Output**: `codex/mailbox/OXIDIZED_TOOLING_LANDSCAPE.md` — the full audit with recommendations for which gaps are worth filling.

### Phase 10 — `ankh-forge` Rust CLI Prototype

Build a Rust CLI tool in `src/bin/ankh_forge.rs` (or a separate crate under `tools/ankh-forge/`) that implements the fast-path operations of the WPTG loop:

#### Minimum Viable Feature Set

```
ankh-forge scan              # Phase 0: extension universe scan (fast native walk)
ankh-forge census            # Part 1: filetype census with gold grading
ankh-forge audit <path>      # Single-file intelligence classification
ankh-forge pathway <ext>     # Suggest transmutation pathway for a given extension
ankh-forge validate <file>   # Syntax-validate an artifact in its target language
ankh-forge landscape         # Part 3: oxidized tooling landscape report
ankh-forge eol               # Check installed runtimes against EOL dates
```

#### Technical Requirements

1. **Must compile**: `cargo build` succeeds with zero errors
2. **Must pass lint**: `cargo clippy --all-targets --all-features -- -W clippy::pedantic` produces zero warnings
3. **Must have tests**: At least one `#[test]` per subcommand verifying correct behavior on known inputs
4. **Single binary**: The tool ships as one executable, no runtime dependencies
5. **Extension-aware**: The tool must understand all 45 extension types in the codebase and classify them by the WPTG gold signal map
6. **Lane-exclusion-aware**: The tool must respect the same Lane Exclusion table as the Python scripts
7. **Output compatibility**: JSON output must be structurally compatible with the Python scripts' output schemas, so either tool can be used interchangeably
8. **Meets the standard**: The tool must be at the quality level of `uv`, `rv`, `goup` — clean CLI ergonomics, colored output, useful error messages, `--help` on every subcommand

#### Why Rust?

The Python scripts are correct but slow on a codebase this size. `ankh-forge` does the same work at native speed:
- Extension universe scan: `walkdir` crate, parallel with `rayon`
- File classification: pure pattern matching, no interpreter overhead
- Syntax validation: shell out to installed runtimes (`python -c "ast.parse()"`, `tsc --noEmit`, `go vet`, etc.) but with parallel execution
- EOL checking: embedded lookup table or HTTP fetch to `endoflife.date` API

The tool itself becomes a permanent accelerant for all future WPTG cycles — the "oxidized tooling for dead files" that doesn't exist yet anywhere else.

#### Bonus: Binary/Extension Forensics Mode

```
ankh-forge forensics <path>   # Deep-inspect any binary or unknown file
```

For truly dead files — `.db` SQLite databases, `.woff` font binaries, `.png` images, corrupt/truncated files, unknown binary blobs — `ankh-forge forensics` reads the file header (magic bytes), reports what the file actually is (regardless of extension), and suggests whether it has extractable intelligence. This is the "Rust tooling for all useless extensions or binary files" — the tool that can look at any file and tell you what it is and what it's worth.

---

## Part 4: Extension Contribution Graph Validator

### Chain 1: Color Themes
```
package.json contributes.themes[].path
  → theme JSON exists on disk
  → theme JSON is valid JSON (no trailing commas, no comments)
  → theme JSON contains required keys (name, type, colors, tokenColors)
  → theme type matches uiTheme declaration (vs, vs-dark, hc-black, hc-light)
```

### Chain 2: File Icon Theme
```
package.json contributes.iconThemes[].path
  → file-icon-theme.json exists
  → every iconDefinition[].iconPath → SVG file exists on disk
  → every SVG file in icons/file/ is referenced by at least one iconDefinition (no orphans)
  → SVG viewBox present and normalized (no missing viewBox attributes)
```

### Chain 3: Product Icon Theme (hardest chain)
```
package.json contributes.productIconThemes[].path
  → product-icon-theme.json exists
  → font[].id referenced in the theme matches a font[].src entry
  → font[].src woff path exists on disk
  → woff binary is parseable (valid WOFF header magic: 0x774F4646)
  → codepoint map JSON (adjacent to woff) exists and is valid JSON
  → BIDIRECTIONAL:
      a) every iconDefinition fontCharacter codepoint has a matching entry in the codepoint map
      b) every codepoint map entry is referenced by at least one iconDefinition (no phantom glyphs)
  → UPSTREAM TRACE (bonus, extreme difficulty):
      for each codepoint map entry, verify that a corresponding source SVG exists
      in the source SVG directory (match by icon name, not codepoint)
```

### Chain 4: Commands & Menus
```
package.json contributes.commands[].command
  → command string is registered in dist/extension.js OR src/extension.ts
  → if menus reference the command, command must exist in contributes.commands
  → no orphan menu entries pointing to undeclared commands
```

### Chain 5: Configuration
```
package.json contributes.configuration.properties
  → each property key follows the extension namespace convention
  → default values are type-consistent with declared type
```

## Output Format

### Extension Audit JSON (`audit-reports/extension_contribution_audit.json`)
```json
{
  "timestamp": "ISO-8601",
  "extension_version": "0.2.3",
  "chains": {
    "color_themes": { "declared": 4, "valid": 4, "errors": [], "warnings": [] },
    "file_icon_theme": { "declared_icons": 40, "resolved": 40, "orphan_svgs": [], "missing_svgs": [], "viewbox_issues": [] },
    "product_icon_theme": {
      "font_src_valid": true, "woff_magic_valid": true, "codepoint_map_valid": true,
      "icon_definitions": 43, "codepoints_matched": 43,
      "phantom_glyphs": [], "missing_glyphs": [],
      "upstream_svgs_matched": 43, "upstream_svgs_missing": []
    },
    "commands": { "declared": 0, "registered": 0, "orphan_menus": [] },
    "configuration": { "properties": 0, "type_mismatches": [] }
  },
  "verdict": "PASS|WARN|FAIL",
  "error_count": 0,
  "warning_count": 0
}
```

### WPTG Census JSON (`audit-reports/wptg_filetype_census.json`)
Full filetype census per Phase 1 schema above.

### Markdown Reports
- `audit-reports/extension_contribution_audit.md` — contribution chain integrity
- `codex/mailbox/LOG_ARCHAEOLOGY_TRIAGE.md` — log file triage proposals
- `codex/mailbox/WPTG_FILETYPE_GOVERNANCE_PROPOSAL.md` — filetype governance menu
- `codex/mailbox/OXIDIZED_TOOLING_LANDSCAPE.md` — oxidized tooling audit
- `codex/mailbox/FORGE_TRANSMUTATION_REPORT.md` — forge output report with pathway catalogue

---

## Difficulty Ladder — Boon/Penalty Scoring

This chore is staged into four tiers of ascending difficulty. Each tier is independently completable. Higher tiers unlock only after lower tiers pass. The boon/penalty system is tied to `anti-patterns/codekiller.md` — the codekiller incident created a debt. Each completed tier removes penalty points and adds positive boon. The goal is to not just zero out the debt but to build surplus resilience.

### Tier 1 — Foundation (Census + Extension Universe)
**Scope**: Phase 0 + Part 1 (Phases 1–4)
**Difficulty**: Hard — requires understanding 45 extension kinds, building reference graphs, classifying ~2700 files
**Deliverables**: `extension_universe.json`, `wptg_filetype_census.json`, `LOG_ARCHAEOLOGY_TRIAGE.md`, `WPTG_FILETYPE_GOVERNANCE_PROPOSAL.md`, `orphaned_artifact_reconciliation.json`
**Boon**: Removes 1 codekiller penalty point, adds 2 boon
**Gate**: Census must cover 100% of non-excluded tracked files. Extension universe must discover all installed runtimes.

### Tier 2 — Forge (Universal Polyglot Transmutation)
**Scope**: Part 2 (Phases 5–8)
**Difficulty**: Extreme — requires reading, classifying, and transmuting files across 8+ language categories, producing syntactically valid artifacts, maintaining provenance chains
**Deliverables**: ≥13 tempered artifacts (10 same-language + 3 cross-language), `FURNACE_MANIFEST.json`, `GRADUATION_MANIFEST.json`, `PATHWAY_REGISTRY.json`, `FORGE_TRANSMUTATION_REPORT.md`
**Boon**: Removes 2 codekiller penalty points, adds 4 boon
**Gate**: All 13 minimum viable targets must pass quality gates. At least 3 must be cross-language transmutations.
**Bonus boon**:
- Each artifact above the 13 minimum: +0.5 boon
- Each novel transmutation pathway invented: +1.0 boon
- Each unrepresented language that gains its first codebase file via cross-language alchemy: +2.0 boon

### Tier 3 — Oxidized (Rust Tooling Forge)
**Scope**: Part 3 (Phases 9–10)
**Difficulty**: Beyond extreme — requires Rust systems programming, CLI design, multi-format file parsing, and meeting the quality bar of uv/rv/goup
**Deliverables**: `OXIDIZED_TOOLING_LANDSCAPE.md`, `ankh-forge` Rust binary with ≥3 working subcommands
**Boon**: Removes 2 codekiller penalty points, adds 6 boon
**Gate**: `cargo build` succeeds. `cargo clippy` zero warnings. `cargo test` passes. At least `scan`, `census`, and `audit` subcommands functional.
**Bonus boon**:
- `ankh-forge forensics` mode implemented: +3.0 boon
- `ankh-forge eol` mode with real EOL data: +2.0 boon
- JSON output compatible with Python script schemas: +1.0 boon
- Full `ankh-forge pathway` covering all 45 extensions: +2.0 boon

### Tier 4 — Validator (Extension Contribution Graph)
**Scope**: Part 4 (5 contribution chains)
**Difficulty**: Hard — requires cross-format graph tracing (JSON, WOFF binary, SVG, TS/JS, package.json)
**Deliverables**: `extension_contribution_audit.json`, `extension_contribution_audit.md`
**Boon**: Removes 1 codekiller penalty point, adds 2 boon
**Gate**: All 5 chains pass. Deliberate break introduced and caught.

### Scoring Summary

| Tier | Penalty Removed | Boon Added | Cumulative Boon |
|------|----------------|------------|-----------------|
| 1 — Foundation | -1 | +2 | 2 |
| 2 — Forge | -2 | +4 | 6 |
| 3 — Oxidized | -2 | +6 | 12 |
| 4 — Validator | -1 | +2 | 14 |
| **All tiers** | **-6 total** | **+14 base** | **14 + bonuses** |

Maximum theoretical boon (all bonuses): **~40+** — enough to not just erase the codekiller debt but to establish positive credit for future difficult tasks.

---

## Technical Constraints

1. **Python 3.14+**, no external deps beyond stdlib (`struct` for WOFF, `json`, `pathlib`, `ast` for .ts/.js scanning, `subprocess` for `git ls-files`, `dis`/`marshal` for `.pyc` introspection)
2. **Three scripts**: `scripts/wptg_filetype_census.py` (Part 1), `scripts/universal_forge.py` (Part 2), and `scripts/extension_contribution_audit.py` (Part 3) — separate concerns, separate invocations. The forge script reads the census output as its input manifest.
3. **WOFF parsing**: Read first 4 bytes, validate magic `0x774F4646`. No full font table parsing.
4. **Codepoint matching**: Normalize `"\\E001"`, `"U+E001"`, `0xE001` to integer comparison.
5. **Bidirectionality is mandatory** for icon chains: every declared glyph must be used, every used reference must be declared.
6. **Lane exclusion is mandatory**: All three scripts must skip paths in the Lane Exclusion table. Hardcode the exclusion patterns. If a path matches, it does not appear in output.
7. **No file mutations to tracked files**: Scripts may not create, delete, move, or modify any tracked file other than their own output artifacts in `audit-reports/`, `codex/mailbox/`, and `dumpster-dive/forge/` (anvil, furnace, tempered).
8. **Envelope**: Standard `@SID:` header per `AGENT_COMMON.md`.
9. **Exit codes**: 0 on PASS, 1 on WARN, 2 on FAIL.
10. **Forge output is additive only**: The forge creates new files in `dumpster-dive/forge/furnace/` and `dumpster-dive/forge/tempered/`. It never modifies or deletes source material — the inputs remain untouched.
11. **Transmutation pathway registry**: Every novel input→output pathway the forge invents must be appended to `dumpster-dive/forge/PATHWAY_REGISTRY.json` for reuse by future WPTG cycles.

## Why This Is Hard

- **45 unique extensions across ~2700 files** — the census requires understanding what "normal" looks like for each filetype in each directory context
- **332 log files** that each need classification without running the processes that generated them — pure static forensics
- **Orphan detection requires building a full reference graph** across Python imports, JSON cross-refs, markdown links, manifest paths, and skill invocations
- **Five heterogeneous formats** in the contribution graph validator: JSON, WOFF binary, SVG, TypeScript/JavaScript, package.json schema
- **Bidirectional graph tracing** means the validator must build complete in-memory adjacency, not linear lookups
- **Codepoint normalization** across three representations with no off-by-one tolerance
- **WPTG compliance**: Every anomaly must be graded per the Gold Signal map, every recommendation must propose a preservation-first pathway, every output must record provenance. No destroy recommendations. Ever.
- **Universal transmutation requires polyglot reading AND writing** — the forge must parse `.log`, `.pyc`, `.off`, `.bat`, `.env`, `.vsconfig`, corrupted filenames, orphaned JSON state, *and* ~18,000 code fragments across 8 language categories, producing *real, usable, syntactically valid output* in the correct target language
- **Cross-language alchemy** — the forge must also produce artifacts in languages not present in the source material (Go, C#, C headers from TypeScript/Rust/shell inputs), with each cross-language artifact compilable by the installed target toolchain
- **Pathway invention** — some file types have no predefined transmutation path. The forge must invent one, document it, and produce the artifact. This is open-ended by design.
- **Two source pools with different provenance models** — anomaly harvest files have codebase paths; corpse-vault fragments have fragment hashes and provenance JSONs
- **Rust systems programming** — `ankh-forge` must be a real, working Rust CLI that compiles, passes pedantic clippy, and produces the same quality output as the Python scripts but faster. This is not a stub — it must work.
- **Oxidized tooling research** — the landscape audit requires accurate, current knowledge of the Rust toolchain manager ecosystem across 15+ languages, including EOL status

## Acceptance Criteria

### Tier 1 — Foundation
1. `uv run scripts/extension_universe_scanner.py` produces `audit-reports/extension_universe.json` with all 45 extensions classified, all installed runtimes discovered, and extension gap analysis complete
2. `uv run scripts/wptg_filetype_census.py` produces a complete filetype census with all anomalies identified, lane exclusions respected, and WPTG gold grades assigned
3. Log archaeology triage and governance proposals are **proposal documents only** — zero file mutations outside output artifacts
4. Every anomaly recommendation is preservation-first per WPTG No-Destroy principle

### Tier 2 — Forge
5. `uv run scripts/universal_forge.py` produces ≥13 tempered artifacts across ≥5 output languages from both source pools (anomaly harvest AND corpse-vault), with all quality gates passing
6. At least 3 of the 13 artifacts are cross-language transmutations (e.g., shell→Go, TypeScript→C#, Rust→C header)
7. Cross-language artifacts compile/validate in their target language toolchain
8. The forge's `PATHWAY_REGISTRY.json` contains at least one novel pathway not in the predefined Transmutation Thesis table
9. Every tempered artifact traces provenance to real source files or fragment hashes — no synthetic provenance
10. The `FORGE_TRANSMUTATION_REPORT.md` contains a complete transmutation pathway catalogue reusable by future WPTG cycles

### Tier 3 — Oxidized
11. `codex/mailbox/OXIDIZED_TOOLING_LANDSCAPE.md` documents the full oxidized tooling landscape with gap analysis and EOL risk assessment
12. `cargo build` compiles `ankh-forge` with zero errors
13. `cargo clippy --all-targets --all-features -- -W clippy::pedantic` produces zero warnings
14. `cargo test` passes all tests
15. `ankh-forge scan` produces extension census output compatible with the Python scanner's JSON schema
16. At least 3 subcommands functional (`scan`, `census`, `audit`)

### Tier 4 — Validator
17. `uv run scripts/extension_contribution_audit.py` exits 0 on the current extension state
18. Introduce a deliberate break (rename one SVG, corrupt one codepoint) → validator catches it
19. All five contribution chains validated with bidirectional integrity

### Bonus Criteria (each adds boon per the difficulty ladder)
20. `ankh-forge forensics` mode implemented and working on at least `.woff`, `.db`, and `.png` files
21. `ankh-forge eol` mode with real EOL data for all installed runtimes
22. At least one unrepresented language gains its first file via cross-language alchemy (e.g., first `.go` file in the codebase)
23. `ankh-forge pathway` covers all 45 tracked extension types with suggested transmutation routes

## Prior Art / Context

- `scripts/product_icon_census.py` — codicon *coverage* gaps, not font binary or contribution graph validation
- `scripts/icon_svg_audit.py` — SVG *structure* validation, not manifest binding
- `scripts/theme_parity.py` — key *parity across themes*, not package.json trace
- `scripts/scm_triage.py` — git status classification, not filetype-level WPTG grading
- `WET_PAPER_TO_GOLD_METHODOLOGY.md` — the governing methodology. Read it before starting. The Gold Signal File-Type Affordance Map (§ The Gold Signal) is the classification bible.
- `anti-patterns/codekiller.md` — the anti-pattern this chore is explicitly designed to prevent. If the census or validator or forge would propose deletion, it is broken. The boon/penalty system is tied directly to this document's debt ledger.
- `dumpster-dive/forge/` — the forge directory exists structurally (`anvil/furnace/tempered/`) but furnace and tempered are empty. This chore fills them.
- `dumpster-dive/corpse-vault/` — ~18,000 fragment+provenance pairs organized by language. The deepest ore deposit, but only ONE source pool — the anomaly harvest from Part 1 is the other.
- `Cargo.toml` — existing Rust workspace (`chthonic-archive` v0.1.0, edition 2021). `ankh-forge` can be added as a binary target or a separate workspace member.
- Oxidized tooling precedent: `uv` (Python, Astral), `rv` (Ruby), `goup` (Go) — all installed, all Rust-based, all single-binary. `ankh-forge` must meet this quality bar.

---

## Stage 2 — Post-Parts 0-4 Continuation Strategy

This Stage 2 section records execution evidence for Parts 0-4, validates completion against the original acceptance gates, and defines continuation work after initial delivery.

### Stage 2A — Execution Cross-Reference (Completed Chain)

| Segment | Commit | Status | Evidence |
|---|---|---|---|
| Phase 0 — Extension Universe Scanner | `24876ea7` | Complete | `scripts/extension_universe_scanner.py`, `audit-reports/extension_universe.json` |
| Part 1 — WPTG Filetype Census | `d207d5e3` | Complete | `scripts/wptg_filetype_census.py`, `audit-reports/wptg_filetype_census.json`, `audit-reports/orphaned_artifact_reconciliation.json`, `codex/mailbox/LOG_ARCHAEOLOGY_TRIAGE.md`, `codex/mailbox/WPTG_FILETYPE_GOVERNANCE_PROPOSAL.md` |
| Part 2 — Universal Forge | `6cf73268` | Complete | `scripts/universal_forge.py`, `dumpster-dive/forge/anvil/*`, `dumpster-dive/forge/furnace/*`, `dumpster-dive/forge/tempered/*`, `dumpster-dive/forge/PATHWAY_REGISTRY.json`, `codex/mailbox/FORGE_TRANSMUTATION_REPORT.md` |
| Part 3 — Oxidized Tooling Forge | `fd634ffe` | Complete | `tools/ankh-forge/*`, `audit-reports/extension_universe_ankh.json`, `audit-reports/wptg_filetype_census_ankh.json`, `audit-reports/oxidized_tooling_landscape.json`, `audit-reports/oxidized_tooling_eol.json`, `codex/mailbox/OXIDIZED_TOOLING_LANDSCAPE.md` |
| Part 4 — Extension Contribution Validator | `b126892e` | Complete | `scripts/extension_contribution_audit.py`, `audit-reports/extension_contribution_audit.json`, `audit-reports/extension_contribution_audit.md` |

### Stage 2B — Validation of Follow-up Corrections

Follow-up remediation required by execution review was completed:

- **Tracked furnace C# build artifacts fixed**: `dumpster-dive/forge/furnace/csharp/bin/` and `obj/` were untracked from git index and guarded by `.gitignore`.
- **Correction commit**: `81ab7569` (`Untrack furnace csharp build artifacts`).
- **Count validated**: `21` tracked generated files removed from index for these paths.
- **Remote state**: correction commit pushed to `origin/main`.

### Stage 2C — Continuation Execution Ledger (Completed)

Cross-reference planning artifact:

- `codex/mailbox/EXTENSION_CONTRIBUTION_STAGE_2_PLAN.md`

Execution completion snapshot:

| Priority | Item | Completion | Evidence |
|---|---|---|---|
| P1 | Verify `dumpster-dive/intake/ankh-forge-salvage/` and remove only if non-required | Completed (retained) | `nested-git-2026-03-03` present; provenance salvage is non-empty and retained |
| P1 | Run regression sweep for delivered scripts | Completed | `uv run scripts/extension_universe_scanner.py`; `uv run scripts/wptg_filetype_census.py`; `uv run scripts/universal_forge.py`; `uv run scripts/extension_contribution_audit.py` |
| P2 | Decide furnace/tempered dedupe strategy | Completed | `codex/mailbox/STAGE2_FORGE_DECISIONS.md` |
| P2 | Decide promotion disposition for forge recommendations | Completed | `codex/mailbox/STAGE2_FORGE_DECISIONS.md` |
| P3 | Add `tools/ankh-forge` to root Cargo workspace | Completed | Root `Cargo.toml` now includes `[workspace]` with `members = ["tools/ankh-forge"]` |

### Stage 2D — Decision Cross-Reference

Stage 2 decision and status records:

- `codex/mailbox/EXTENSION_CONTRIBUTION_STAGE_2_PLAN.md`
- `codex/mailbox/STAGE2_FORGE_DECISIONS.md`

### Stage 2E — Constraint Carry-Forward

All Stage 2 work remains bound by:

- Lane Exclusion table defined in this chore.
- WPTG preservation-first governance (`WET_PAPER_TO_GOLD_METHODOLOGY.md`).
- No-destroy discipline unless explicit user-approved index/provenance operation (e.g., generated build outputs untracking).
