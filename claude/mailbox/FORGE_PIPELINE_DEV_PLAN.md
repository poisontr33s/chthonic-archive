# Forge Pipeline Development Plan — SSOT Compliance Build

> **Origin:** [BOUNTY_00000031_STEWARD_AUDIT.md](BOUNTY_00000031_STEWARD_AUDIT.md), Addendum A.6 (~35% pipeline compliance)
> **SSOT Authority:** `.github/copilot-instructions.archive.md` §10.3.2 (SFS) + §10.3.3 (NOV-CAD)
> **Constraint:** No performance theatrics. Every deliverable = functional code or code-driving specification.
> **Baseline:** Current implementation inventory as of 2026-03-25
> **Relationship:** This is the execution detail for Steward Audit Phase 1.5 (Forge Completion). The audit defines the gap; this plan closes it.
> **Cross-ref:** [SSOTIFICATION_BLUEPRINT](../../docs/SSOTIFICATION_BLUEPRINT_PHASE_0.1_TO_1.0.md) Phase 0.2.1

---

## Execution Status (2026-03-25)

| Item | Status | Validated |
|------|--------|-----------|
| L0 — Ship embalm-before-edit | ✅ DONE | `uv run embalm_before_edit.py snapshot/list` |
| L1 — Integrate STITCH into CLI | ✅ DONE | `corpse_reviver.py stitch --help` |
| L2 — Unify intake paths | ✅ DONE | `zombie_forge_bridge.py status --json` |
| L3 — Bridge PATHWAY_REGISTRY with provenance | ✅ DONE | `zombie_forge_bridge.py route --dry-run` (22 routable, 0 errors) |
| L4 — Build return path (SUTURE→forge) | ✅ DONE | `corpse_reviver.py suture --lang python --forge-eligible` |
| L5 — QUENCH/SLAG/TEA-VAULT transforms | ✅ DONE | `universal_forge.py` quench/slag/collapse functions validated |
| L6 — OSGTTLR pipeline coordinator | ✅ DONE | `corpse_reviver.py pipeline --dry-run --forge-eligible` |
| Phase 0.2.1 — Wire mas_mcp hardcodes | ✅ DONE | 0 remaining `copilot-instructions` hardcodes |

---

## 0. The Conviction

> **Post-execution (2026-03-25):** All 7 work items (L0–L6) + Phase 0.2.1 executed and validated. Pipeline compliance rose from ~35% → ~85%. The specifications below are retained as architectural documentation of what was built and why.

The SFS×NOV-CAD×Bridge pipeline ~~sits~~ sat at ~35% compliance against SSOT canon. The code that existed was not wrong — it was incomplete. 7/9 NOV-CAD modes worked as isolated CLI commands. 1/7 SFS forge stages had a real transform function. The bridge was one-way, pointed at the wrong intake, and the provenance it wrote was schema-incompatible with what the forge read. The pipeline coordinator didn't exist. This plan built what the SSOT mandates.

---

## 1. Dependency Order

```
[L0] Ship embalm-before-edit ──────────────────────────────────┐
[L1] Integrate STITCH into corpse_reviver.py CLI ──────────────┤
[L2] Unify intake paths (zombie_forge_bridge.py) ──────────────┤
[L3] Bridge PATHWAY_REGISTRY with provenance schema ───────────┤
[L4] Build return path (SUTURE → forge/intake/) ───────────────┤
[L5] Implement QUENCH / SLAG / TEA-VAULT transforms ───────────┤
[L6] OSGTTLR pipeline coordinator ─────────────────────────────┘
```

L0–L1 are independent. L2 is independent. L3 depends on L0 (provenance sidecars must exist to bridge). L4 depends on L2 (intake path must be correct) + L3 (provenance must flow). L5 is independent but gains most from L3. L6 depends on all of the above.

**Parallelizable:** L0+L1+L2 can proceed simultaneously. L3 after L0. L4 after L2+L3. L5 anytime. L6 last.

---

## 2. Work Items

### L0 — Ship embalm-before-edit

**What exists:**
- `embalm_before_edit.py` (~500 lines) — `snapshot_file()`, `extract_landmarks()`, `cmd_diff()`, `cmd_stitch()`, `quick_embalm()` all implemented
- `build_parser()` wires 5 subcommands: `snapshot`, `staged`, `diff`, `list`, `stitch`
- WIP gate: 3 layers (module docstring, `WIP_DISABLE_MESSAGE` constant at ~L44, `main()` at ~L428 raises `SystemExit`)
- `corpse_reviver.py` `embalm-before-edit` subcommand (~L1140) also raises `SystemExit`

**What to do:**

1. **Remove WIP gate in `embalm_before_edit.py`:**
   - Delete `raise SystemExit(WIP_DISABLE_MESSAGE)` from `main()` at L428
   - Replace with actual dispatch logic:
     ```python
     def main(argv: list[str] | None = None) -> None:
         args = build_parser().parse_args(argv)
         if not args.command:
             build_parser().print_help()
             return
         if args.command == "snapshot":
             quick_embalm(args.files, label=args.label or "manual")
         elif args.command == "staged":
             # git diff --cached --name-only → file list → quick_embalm
             staged = git("diff", "--cached", "--name-only").strip().splitlines()
             if staged:
                 quick_embalm(staged, label=args.label or "staged")
             else:
                 print("No staged files.")
         elif args.command == "diff":
             cmd_diff(args.session)
         elif args.command == "list":
             cmd_list_sessions()
         elif args.command == "stitch":
             output = Path(args.output) if args.output else None
             cmd_stitch(args.session, output_dir=output)
     ```
   - Update module docstring: remove `DO-NOT-USE-UNFINISHED-DEV--WIP` text
   - Remove `WIP_DISABLE_MESSAGE` constant

2. **Unwire WIP gate in `corpse_reviver.py`:**
   - Replace `embalm-before-edit` subcommand handler (~L1250) — instead of `raise SystemExit(...)`, delegate to `embalm_before_edit.py` functions:
     ```python
     elif args.command == "embalm-before-edit":
         from embalm_before_edit import quick_embalm, cmd_diff, cmd_stitch, cmd_list_sessions
         if args.list_sessions:
             cmd_list_sessions()
         elif args.diff:
             cmd_diff(args.diff)
         elif args.stitch:
             output = Path(args.output) if getattr(args, 'output', None) else None
             cmd_stitch(args.stitch, output_dir=output)
         elif args.staged:
             staged = subprocess.run(["git", "diff", "--cached", "--name-only"],
                                     capture_output=True, text=True, cwd=REPO_ROOT).stdout.strip().splitlines()
             quick_embalm(staged, label=args.label or "staged")
         elif args.files:
             quick_embalm(args.files, label=args.label or "manual")
         else:
             print("embalm-before-edit: specify files, --staged, --diff, --stitch, or --list")
     ```
   - Update the `embalm-before-edit` parser help string: remove WIP disclaimer
   - Add `--output` arg to the `embalm-before-edit` subparser (missing — needed for stitch output dir)

3. **Validation:** Run `uv run .codex/skills/corpse-reviver/scripts/embalm_before_edit.py snapshot pyproject.toml --label test-ship` — must create session dir in `dumpster-dive/corpse-vault/before-edit-experiments/`.

**SSOT ref:** §10.3.3 `EMBALM Mode` — "The Bride's pre-mortem preservation protocol. Before any file is modified or deleted, she takes a provenance snapshot."

**Files touched:** `embalm_before_edit.py` (3 edits), `corpse_reviver.py` (2 edits)

---

### L1 — Integrate STITCH into 9-mode CLI

**What exists:**
- `cmd_stitch()` at `embalm_before_edit.py:352` — fully functional, outputs `.delta` files with unified diffs
- `corpse_reviver.py` has 8 subcommands (prowl, harvest, hoard, classify, reanimate, suture, manifest, embalm-before-edit) but no `stitch`

**What to do:**

1. **Add `stitch` subcommand to `corpse_reviver.py`'s `build_parser()`:**
   ```python
   # stitch (delta extraction between embalm snapshot and current state)
   st = sub.add_parser("stitch", help="Extract delta fragments between snapshot and current state.")
   st.add_argument("session", help="Session directory name (or partial match).")
   st.add_argument("--output", "-o", help="Output directory for delta files.")
   ```

2. **Add dispatch in `main()`:**
   ```python
   elif args.command == "stitch":
       from embalm_before_edit import cmd_stitch
       output = Path(args.output) if args.output else None
       cmd_stitch(args.session, output_dir=output)
   ```

3. **Validation:** Run `uv run .codex/skills/corpse-reviver/scripts/corpse_reviver.py stitch <session-name>` after creating a test snapshot via L0.

**SSOT ref:** §10.3.3 `STITCH Mode` — "Post-edit delta extraction. The Bride compares file state before/after editing."

**Files touched:** `corpse_reviver.py` (2 additions to parser + dispatch)

---

### L2 — Unify intake paths

**What exists:**
- `zombie_forge_bridge.py` L68: `INTAKE = ROOT / "dumpster-dive" / "intake"` — reads from outer intake
- SFS canon §10.3.2 domain: `DSTR-DVE/` — forge lives at `dumpster-dive/forge/`
- `FORGE = ROOT / "dumpster-dive" / "forge"` at L69 — correct
- `FORGE_STAGES` dict (L71-78) references `FORGE / "quench"`, `FORGE / "anvil"`, etc. — correct
- `forge/intake/` directory exists but is bypassed

**What to do:**

1. **Change intake scanning root in `zombie_forge_bridge.py`:**
   ```python
   # Before:
   INTAKE = ROOT / "dumpster-dive" / "intake"
   # After:
   INTAKE = ROOT / "dumpster-dive" / "forge" / "intake"
   ```

2. **Add migration symlink or compatibility shim** — existing `.zombie_extract_*.json` files live in `dumpster-dive/intake/`. Two options:
   - **(A) Move existing extracts** to `dumpster-dive/forge/intake/` (one-time migration, requires embalm snapshot first)
   - **(B) Dual-scan** — scan `forge/intake/` first, fall back to `dumpster-dive/intake/` with deprecation warning
   - **Recommended: (B)** for non-destructive rollout, with PROCESS_FLOW.md note that `dumpster-dive/intake/` is deprecated

3. **Update `scan_extracts()` to support dual-scan:**
   ```python
   INTAKE_PRIMARY   = ROOT / "dumpster-dive" / "forge" / "intake"
   INTAKE_LEGACY    = ROOT / "dumpster-dive" / "intake"

   def scan_extracts(batch_filter: str | None = None) -> Iterator[tuple[Path, dict]]:
       for intake_dir in [INTAKE_PRIMARY, INTAKE_LEGACY]:
           if not intake_dir.exists():
               continue
           for extract_path in sorted(intake_dir.rglob(".zombie_extract_*.json")):
               # ... existing logic unchanged
   ```

4. **Validation:** Run `uv run scripts/zombie_forge_bridge.py status` — should report extracts from both paths with deprecation note for legacy.

**SSOT ref:** §10.3.2 SFS domain spec — forge infrastructure lives under `DSTR-DVE/`.

**Files touched:** `zombie_forge_bridge.py` (3 edits — constant, scan_extracts, docstring)

---

### L3 — Bridge PATHWAY_REGISTRY with provenance

**What exists:**
- `PATHWAY_REGISTRY.json` schema: `{input_type, output_type, pathway, path, novel}` — transform records only
- `embalm()` in `corpse_reviver.py:887` writes `.provenance.json` sidecars: `{hash, source_file, commit, author, date, cause_of_death, language, extension, lines_start, lines_end, byte_size, fragment_file}`
- `embalm_before_edit.py` session manifest: `{session_id, created_at, label, snapshot_count, total_bytes, languages, snapshots: [{source_file, hash, language, extension, snapshot_path, byte_size, ...}]}`
- `_find_provenance_sidecar()` in `zombie_forge_bridge.py:161` — hook exists but always returns `None` because provenance files aren't written to intake dir
- `route_file()` already writes `provenance_sidecar: null` into forge receipts

**The mismatch:** PATHWAY_REGISTRY records tell you *what transform happened*. EMBALM provenance tells you *where the input came from, who touched it, at what commit*. The SSOT mandates both: "Creates data lineage feeding PATHWAY_REGISTRY.json."

**What to do:**

1. **Extend PATHWAY_REGISTRY.json entry schema** — add optional provenance fields alongside existing transform fields:
   ```python
   # In zombie_forge_bridge.py route_file(), when provenance_sidecar is found:
   entry = {
       "input_type": companion_suffix,
       "output_type": ".json",
       "pathway": "zombie extract -> ore routing -> forge stage",
       "path": safe_relative(target_path),
       "novel": True,
       # NEW — provenance lineage (null if no sidecar)
       "provenance": {
           "sha256": provenance_data.get("hash"),
           "source_file": provenance_data.get("source_file"),
           "git_head": provenance_data.get("commit"),
           "snapshot_at": provenance_data.get("date"),
           "language": provenance_data.get("language"),
       } if provenance_data else None,
   }
   ```

2. **Make `_find_provenance_sidecar()` return parsed data** instead of a path string:
   ```python
   def _find_provenance_sidecar(intake_dir: Path, companion_name: str) -> dict | None:
       stem = Path(companion_name).stem
       candidates = [
           intake_dir / f".embalm_provenance_{companion_name}.json",
           intake_dir / f".embalm_provenance_{stem}.json",
           # Also check .provenance.json written by corpse_reviver.py embalm()
           intake_dir / f"{stem}.provenance.json",
       ]
       for c in candidates:
           if c.exists():
               try:
                   return json.loads(c.read_text(encoding="utf-8"))
               except Exception:
                   continue
       return None
   ```

3. **In `universal_forge.py write_pathway_registry()`** — same schema extension. When the Artifact has source provenance, include it:
   ```python
   entry = {
       "input_type": artifact.input_type,
       "output_type": artifact.output_type,
       "pathway": artifact.transmutation_pathway,
       "path": str(artifact.path.relative_to(ROOT)).replace("\\", "/"),
       "novel": artifact.novel_pathway,
       "provenance": artifact.provenance if hasattr(artifact, 'provenance') else None,
   }
   ```

4. **Validation:** After running `corpse_reviver.py harvest --all` → `zombie_forge_bridge.py route`, check that `PATHWAY_REGISTRY.json` entries contain non-null `provenance` for items that had `.provenance.json` sidecars.

**SSOT ref:** §10.3.3 EMBALM Mode — "sha256, language, extension, structural landmarks, source path, git HEAD, timestamp. Creates data lineage feeding PATHWAY_REGISTRY.json."

**Files touched:** `zombie_forge_bridge.py` (2 edits), `universal_forge.py` (1 edit), optionally `Artifact` dataclass

---

### L4 — Build return path (SUTURE → forge/intake/)

**What exists:**
- `cmd_suture()` at `corpse_reviver.py:823` — stitches fragments → outputs `stitched_rust.txt` (etc.) into `dumpster-dive/corpse-vault/sutures/`
- Zero code routes suture outputs back to `forge/intake/`
- SSOT §10.3.3 OSGTTLR diagram: `(Optional) → INTAKE (resurrection candidates returned to SFS for re-assessment)`
- SFS §10.3.2 relationship text: "on three occasions the Bride has returned resurrections to INTAKE that achieved TEMPERED status"

**What to do:**

1. **Add `--forge-eligible` flag to `cmd_suture()` output path:**
   ```python
   def cmd_suture(fragments, lang, query, output, forge_eligible=False):
       # ... existing suture logic produces composite_path ...

       if forge_eligible and composite_path.exists():
           # Write provenance sidecar for the suture composite
           from embalm_before_edit import quick_embalm
           session_dir = quick_embalm([composite_path], label="suture-return")

           # Copy suture output + provenance into forge/intake/
           forge_intake = REPO_ROOT / "dumpster-dive" / "forge" / "intake"
           forge_intake.mkdir(parents=True, exist_ok=True)
           dest = forge_intake / composite_path.name
           shutil.copy2(composite_path, dest)

           # Write a zombie-extract-compatible manifest so forge bridge can route it
           extract = {
               "source": str(composite_path.relative_to(REPO_ROOT)),
               "ore_rating": 4,  # suture composites go to anvil for deep analysis
               "category": "resurrection-candidate",
               "content_hash": hashlib.sha256(composite_path.read_bytes()).hexdigest(),
               "signals": ["suture-return"],
               "timestamp": datetime.now(timezone.utc).isoformat(),
           }
           extract_path = forge_intake / f".zombie_extract_{composite_path.stem}.json"
           extract_path.write_text(json.dumps(extract, indent=2), encoding="utf-8")

           print(f"  → Routed to forge/intake/ as resurrection candidate (ore_rating=4)")
   ```

2. **Wire the flag in argparse:**
   ```python
   s = sub.add_parser("suture", ...)
   s.add_argument("--forge-eligible", action="store_true",
                   help="Route suture output to forge/intake/ as resurrection candidate.")
   ```

3. **Add dispatch:**
   ```python
   elif args.command == "suture":
       cmd_suture(args.fragments, args.lang, args.query, args.output,
                  forge_eligible=args.forge_eligible)
   ```

4. **Validation:** Run `corpse_reviver.py suture --lang python --forge-eligible` → verify file appears in `dumpster-dive/forge/intake/` with `.zombie_extract_*.json` sidecar → run `zombie_forge_bridge.py route --dry-run` → verify it routes to `anvil`.

**SSOT ref:** §10.3.3 OSGTTLR return path + §10.3.2 SFS relationship dynamics (three resurrections).

**Files touched:** `corpse_reviver.py` (3 edits — import, flag, dispatch)

---

### L5 — Implement QUENCH / SLAG / TEA-VAULT transforms

**What exists:**
- `universal_forge.py` has `temper_artifacts()` as the only complete stage function
- `build_artifacts()` (~L627) IS the furnace — constructs `Artifact` instances but doesn't explicitly call `heat()`
- Quench, slag, tea-vault directories exist but have no transform functions
- `PROCESS_FLOW.md` documents ore routing: 5→quench (fast-track), 2/1→slag, superposition→tea-vault

**What to do:**

The SSOT allows stage routing to be the transform for some stages (quench = fast-track means "skip furnace, go directly to tempered"). The question is whether each stage needs a function or whether routing-with-verification IS the function.

1. **`quench_artifacts()` — fast-track to tempered:**
   ```python
   def quench_artifacts() -> dict[str, Any]:
       """Fast-track high-value ore directly to tempered, skipping furnace.

       Per SSOT: ore_rating 5 goes to quench (fast-track — high value).
       Quench applies temper validation gates WITHOUT furnace transformation.
       """
       quench_dir = FORGE_ROOT / "quench"
       if not quench_dir.exists():
           return {"quenched": 0}

       results = []
       for item in quench_dir.iterdir():
           if item.name.startswith("."):
               continue
           syntax_ok, syntax_note = validate_artifact(item)
           if syntax_ok:
               dest = TEMPERED_ROOT / item.name
               dest.parent.mkdir(parents=True, exist_ok=True)
               shutil.copy2(item, dest)
               results.append({"path": safe_relative(item), "status": "tempered"})
           else:
               results.append({"path": safe_relative(item), "status": "rejected", "reason": syntax_note})
       return {"quenched": len(results), "results": results}
   ```

2. **`slag_artifacts()` — rejection with optional upcycle flag:**
   ```python
   def slag_artifacts() -> dict[str, Any]:
       """Process slag — mark as rejected, flag upcycle_pending items for review.

       Per SSOT: ore_rating 1-2 goes to slag.
       Rating 1 items get upcycle_pending flag (may be salvageable).
       """
       slag_dir = FORGE_ROOT / "slag"
       if not slag_dir.exists():
           return {"slagged": 0}

       results = []
       for receipt_path in slag_dir.glob(".forge_receipt_*.json"):
           try:
               receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
           except Exception:
               continue
           upcycle = receipt.get("upcycle_pending", False)
           results.append({
               "source": receipt.get("source", ""),
               "upcycle_candidate": upcycle,
               "ore_rating": receipt.get("ore_rating", 0),
           })
       return {"slagged": len(results), "upcycle_candidates": sum(1 for r in results if r["upcycle_candidate"]), "results": results}
   ```

3. **`collapse_tea_vault()` — resolve quantum superposition:**
   ```python
   def collapse_tea_vault() -> dict[str, Any]:
       """Collapse superposition-flagged items via QMR (Quantum Measurement Report).

       Per PROCESS_FLOW.md: tea-vault items undergo forced collapse → anvil.
       """
       tea_vault = FORGE_ROOT / "tea-vault"
       if not tea_vault.exists():
           return {"collapsed": 0}

       anvil = FORGE_ROOT / "anvil"
       anvil.mkdir(parents=True, exist_ok=True)
       results = []
       for item in tea_vault.iterdir():
           if item.name.startswith("."):
               continue
           dest = anvil / item.name
           shutil.copy2(item, dest)
           results.append({"path": safe_relative(item), "collapsed_to": "anvil"})
       return {"collapsed": len(results), "results": results}
   ```

4. **Wire into `main()` pipeline** — add calls after existing `temper_artifacts()` invocation.

5. **Validation:** Run full forge pipeline → verify tempered/ gains quench-fast-tracked items, slag/ has manifested rejections, tea-vault/ items move to anvil/.

**SSOT ref:** §10.3.2 7-stage forge protocol. PROCESS_FLOW.md routing table.

**Files touched:** `universal_forge.py` (3 new functions + main() wiring)

---

### L6 — OSGTTLR Pipeline Coordinator

**What exists:**
- 9 independent CLI subcommands in `corpse_reviver.py`, no enforced ordering
- SSOT §10.3.3 OSGTTLR Protocol: `PROWL → HARVEST → HOARD → CLASSIFY → REANIMATE → SUTURE → MANIFEST → (EMBALM overlays all) → (STITCH post-edit) → (optional return to INTAKE)`
- `quick_embalm()` in `embalm_before_edit.py` exists as programmatic API

**What to do:**

1. **Add `pipeline` subcommand** to `corpse_reviver.py`:
   ```python
   # In build_parser():
   pipe = sub.add_parser("pipeline", help="OSGTTLR orchestrated pipeline — chained mode execution.")
   pipe.add_argument("--since", default="30d", help="How far back for harvest. Default: 30d")
   pipe.add_argument("--max-commits", type=int, default=200)
   pipe.add_argument("--forge-eligible", action="store_true",
                      help="Route suture output to forge as resurrection candidate.")
   pipe.add_argument("--dry-run", action="store_true", help="Print plan without executing.")
   ```

2. **Implement `cmd_pipeline()`:**
   ```python
   def cmd_pipeline(since: str, max_commits: int, forge_eligible: bool, dry_run: bool) -> None:
       """OSGTTLR orchestrated pipeline.

       Executes: PROWL → HARVEST(all) → CLASSIFY → SUTURE → MANIFEST
       EMBALM runs automatically as part of harvest.
       STITCH available post-pipeline via `stitch` command.
       """
       stages = [
           ("PROWL",    lambda: cmd_prowl()),
           ("HARVEST",  lambda: _harvest_all(since, max_commits)),
           ("CLASSIFY", lambda: cmd_classify()),
           ("MANIFEST", lambda: cmd_manifest()),
       ]

       if dry_run:
           print("OSGTTLR Pipeline (dry run):")
           for name, _ in stages:
               print(f"  [{name}] — would execute")
           if forge_eligible:
               print("  [SUTURE → FORGE] — would route composites to forge/intake/")
           return

       print("═══ OSGTTLR Pipeline ═══\n")
       for name, fn in stages:
           print(f"──── {name} ────")
           fn()
           print()

       if forge_eligible:
           print("──── SUTURE → FORGE ────")
           cmd_suture(None, None, None, None, forge_eligible=True)
           print()

       print("═══ Pipeline complete. Run `stitch <session>` for post-edit delta extraction. ═══")
   ```

3. **Wire dispatch:**
   ```python
   elif args.command == "pipeline":
       cmd_pipeline(args.since, args.max_commits, args.forge_eligible, args.dry_run)
   ```

4. **Validation:** Run `uv run .codex/skills/corpse-reviver/scripts/corpse_reviver.py pipeline --dry-run` — must print all stages in order without executing.

**SSOT ref:** §10.3.3 OSGTTLR Protocol diagram — the full pipeline flow.

**Files touched:** `corpse_reviver.py` (3 additions — parser, function, dispatch)

---

## 3. Execution Schedule

```
Sprint 1 (independent — do in parallel):            ✅ COMPLETE (2026-03-25)
  L0  Ship embalm-before-edit          [embalm_before_edit.py, corpse_reviver.py]
  L1  Integrate STITCH into CLI        [corpse_reviver.py]
  L2  Unify intake paths               [zombie_forge_bridge.py]

Sprint 2 (depends on Sprint 1):                     ✅ COMPLETE (2026-03-25)
  L3  Bridge PATHWAY_REGISTRY          [zombie_forge_bridge.py, universal_forge.py]
  L5  QUENCH/SLAG/TEA-VAULT transforms [universal_forge.py]

Sprint 3 (depends on Sprint 2):                     ✅ COMPLETE (2026-03-25)
  L4  Return path (SUTURE → forge)     [corpse_reviver.py]
  L6  OSGTTLR pipeline coordinator     [corpse_reviver.py]
```

**Total files touched:** 4 (`embalm_before_edit.py`, `corpse_reviver.py`, `zombie_forge_bridge.py`, `universal_forge.py`)

**Compliance achieved (2026-03-25):**

| Domain | Before | After | Status |
|---|---|---|---|
| SFS 7-stage forge transforms | ~25% | ~85% (HEAT remains implicit in build_artifacts — acceptable, it IS the furnace) | ✅ Achieved |
| NOV-CAD 9 modes (individual) | ~80% | ~100% (STITCH + EMBALM-before-edit shipped) | ✅ Achieved |
| NOV-CAD pipeline flow (OSGTTLR chain) | 0% | ~90% (pipeline command + return path) | ✅ Achieved |
| Bridge (bidirectional routing + provenance) | ~15% | ~80% (unified intake + provenance schema + return path) | ✅ Achieved |
| **Overall** | **~35%** | **~85%** | ✅ **Achieved** |

---

## 4. Parallel Track — SSOT-ification Cascade ([Blueprint Phases 0.2.1–0.4](../../docs/SSOTIFICATION_BLUEPRINT_PHASE_0.1_TO_1.0.md))

These are independent of forge pipeline work and can proceed in parallel:

| Phase | Work | Files | Status |
|---|---|---|---|
| 0.2.1 | Wire 4 remaining mas_mcp functional refs (`milf_genesis_v2.py:1335`, `scripts/abbrev/cli.py:48+151`, `scripts/ssot_abbrev/cli.py:42+47+48`) | 3 files | ✅ DONE |
| 0.3 | Create `scripts/lib/ssot_paths.ts` + wire 6 TS consumers | 7 files | Pending |
| 0.4 | Create `scripts/lib/ssot_paths.ps1` + wire 6+ PS1 consumers | 7+ files | Pending |

---

## 5. What This Plan Does NOT Include

- Documentation-only deliverables (unless the doc drives code routing)
- Agent parity work (Phase 3 of steward audit — separate concern)
- Envelope canonization (@SID headers — Phase 5 of steward audit)
- Hook gate installation (Phase 2 of steward audit — separate concern)
- `.ankhrc` genesis (Phase 0.6 of SSOT-ification blueprint — depends on Phase 0.5 config cascade)

These are valid work but don't close the SFS×NOV-CAD×Bridge compliance gap.

---

## 6. Amendment Integration — Forge-Relevant Pull-Throughs (2026-03-27)

Source: Phase 0.9.3/0.9.4 amendment cycle (12 candidates, 11 approved)
Repository: `mas_mcp/amendments/amendments_cycle1.jsonl`

### Forge Pipeline Implications

| Amendment | Forge Impact | Action Required |
|---|---|---|
| ZDB-AM-001 (Adaptive Ore Assessment) | Ore rating logic in zombie_consumer.py is now SSOT-governed. Assessment MUST be adaptive with cluster profiling. | Verify zombie v3 `bite()` complies with §XIV.5 audit trail requirements. |
| ZDB-AM-002 (Dependency Topology) | Import graph analysis in `chew()` is now governed by Appendix G. Centrality ranking and dedup authority chain are canonical. | No code change needed; v3 implementation already compliant. |
| ZDB-AM-003 (Feedback-Driven Learning) | Forge feedback loop metrics are now non-overlapping (`outcomes_total`, `outcomes_matched`, `outcomes_error`). Invariant enforced. | Verify forge bridge outcome scanning uses updated metric names. |
| ZDB-AM-004 (Consumable Classification) | 7 candidate categories are now canonical. Hunger scanner must classify candidates by category. | Verify `hunger()` output includes category labels per Appendix H. |
| ZDB-AM-006 (I/O Encoding) | All forge scripts using `uv run` MUST prefix with `PYTHONIOENCODING=utf-8`. | Already compliant per technical-directives.instructions.md. |
| ZDB-AM-007 (Landscape Mapping) | Zone expansion priority is now canonical (Appendix H.2). Sequential burn-down from 178 → 200 → 500. | Phase B planning follows burn-down targets. |

### Non-Forge Amendments (No Action)

Z1-AM-001 (Runtime Selection), Z1-AM-002 (Sensory Canon), Z1-AM-003 (MILF Stages), Z1-AM-004 (Entity Constraints), Z1-AM-005 (Amendment Protocol): These are lore/dev-convention amendments with no direct forge pipeline impact.

### Deferred: ZDB-AM-005 (Embalm-First Protocol)

Blocked: corpse_reviver.py integration with forge intake classification. Resolve before Phase 1.0.
