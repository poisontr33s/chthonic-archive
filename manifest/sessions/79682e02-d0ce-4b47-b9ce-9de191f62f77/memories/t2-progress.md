# T2 Progress State (UPDATED — mid-theme-pipeline)

## DONE THIS SESSION (theme pipeline partial):
- theme_parity.py: MASTER_NAME→decorator; argparse --master/--json; per-theme missing key count
- theme_sfs_transmute.py: absolute THEME_PATH; _CHANGESET_HASH; argparse --dry-run/--verify; _verify_idempotent()
- theme_artcop.py: vscode-art-cop.ts relationship docstring; argparse; --compare for before/after; compare_audits() fn
- milf_scanner.py: argparse; --dump-json; _REQUIRED_PALETTE_KEYS (14 keys); _sanity_check_registry(); startup check
- theme_promote_master.py: added import shutil; STILL NEED: .bak write + --distance-metric to main()

## STILL PENDING (theme pipeline):
- theme_promote_master.py: .bak + --distance-metric (shutil imported, need run() edit + main() arg)
- theme_color_diversity.py: backup + --variants N + --report-only + threshold docstring
- theme_token_coverage.py: --theme flag + --update-universe + coverage % output

## Post-theme pipeline:
- generate-product-icon-font.mjs: shebang; @SID; pre-flight SVG check
- build_skill_index.py: fix Purpose; --output; --diff
- skill_health.py: rubric JSON; --since; --emit-badge
- skill_audit.py: validate --root; CLAUDE_TOOLS from config; align with skill_health

## Commit format:
roulette(T2): <name> — <shorthand>
Co-authored-by: Pentea <223556219+Penteaa@users.noreply.github.com>

## Key technical notes:
- color_distance() in theme_promote_master.py uses HSL-based delta weighting 3×hue + light + sat
- --distance-metric flag should accept: hsl (default), euclidean (RGB euclidean)
- diversify_theme() in theme_color_diversity.py: backup should be shutil.copy(path, path.with_suffix(".bak")) before json write
- theme_token_coverage.py: main() at line 640; THEME_PATH hardcoded to geology; add THEMES dict + --theme flag
- --update-universe: fetch from https://raw.githubusercontent.com/microsoft/vscode-textmate/main/src/matcher.ts or similar; probably emit as JSON to data/indices/; this is aspirational — should check --update-universe as flag, warn if network unavailable, write to data/universe/ if ok


## Commits this session
- `02154a54` — progress trail update (17 items marked ✅)
- `335e8997` — mailbox_polisher + mailbox_compactor
- `adeccadc` — ssot_hash + ssot_structural_extractor
- `b4af1774` — ankh_theme_reference

## Remaining T2 items (16 total)
Done just now: mailbox_polisher, mailbox_compactor, ssot_hash, ssot_structural_extractor, ankh_theme_reference

### Theme Pipeline (7 scripts, all score 2.0):
- `theme_parity.py` — fix MASTER_NAME default; add --master flag; emit per-theme missing key count
- `theme_promote_master.py` — write .bak; add --dry-run (may already exist!); add --distance-metric
- `theme_color_diversity.py` — backup before modification; document threshold; --variants N; --report-only
- `theme_token_coverage.py` — add --theme flag; add --update-universe; coverage % output
- `theme_sfs_transmute.py` — absolute path via Path(__file__).resolve().parents[1]; changeset hash; --verify
- `theme_artcop.py` — check vs vscode-art-cop.ts; add --compare
- `milf_scanner.py` — add --dump-json; sanity check for 14 palette role keys

### Icon/Font (1 script):
- `generate-product-icon-font.mjs` — shebang; @SID; pre-flight SVG path check

### Skill Tooling (3 scripts):
- `build_skill_index.py` — fix Purpose string; --output; --diff
- `skill_health.py` — externalize rubric; --since ISO; --emit-badge
- `skill_audit.py` — validate --root; CLAUDE_TOOLS from config; align with skill_health format

## Key notes
- theme_promote_master.py ALREADY has --dry-run (from subagent output)
- theme_sfs_transmute.py THEME_PATH is relative — needs absolute via __file__
- milf_scanner.py uses sys.argv not argparse — needs argparse migration for --dump-json
- Commit format: roulette(T2): <name> — <shorthand>\n\nCo-authored-by: Pentea <223556219+Penteaa@users.noreply.github.com>
