#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: embed_registry_switch.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
embed_registry_switch.py — Script logic for embed_registry_switch.py.

@SID:           embed_registry_switch
@Shabti:        CLI Script
@Purpose:       Script logic for embed_registry_switch.py.
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


# @SID: embed_registry_switch — switch the active embedding model in the corpus stack
#
# Safely updates three surfaces in one atomic pass:
#   1. scripts/embed_model_registry.json  — active_model_id + active_since
#   2. scripts/embed.py                   — MODEL_ID + DIMS constants
#   3. manifest/corpus-state.json         — vec_model + vec_dims + vec_count (reset if dims change)
#
# Requires the target model to already be in the registry (add it first if not).
# If dimensions change, vec_count is reset to 0 and schema_version bumps are warned.
#
# Usage:
#   uv run scripts/embed_registry_switch.py --model-id NVIDIA/NV-Embed-v2
#   uv run scripts/embed_registry_switch.py --task-profile high_accuracy
#   uv run scripts/embed_registry_switch.py --model-id BAAI/bge-m3 --dry-run
#   uv run scripts/embed_registry_switch.py --list
#
# Dry-run: prints migration plan, writes nothing.

import os
import sys
import re
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone

# ── Paths ─────────────────────────────────────────────────────────────────────
_SCRIPTS = Path(__file__).parent
_ROOT = _SCRIPTS.parent
REGISTRY_PATH   = _SCRIPTS / "embed_model_registry.json"
EMBED_PY_PATH   = _SCRIPTS / "embed.py"
CORPUS_STATE_PATH = _ROOT / "manifest" / "corpus-state.json"


def _load_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def _save_json(p: Path, data: dict) -> None:
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _patch_embed_py(model_id: str, dims: int, dry_run: bool) -> bool:
    """
    Update MODEL_ID and DIMS constants in embed.py.
    Returns True if a change was needed.
    """
    text = EMBED_PY_PATH.read_text(encoding="utf-8")
    original = text

    # MODEL_ID = "..."   — replace quoted value
    text = re.sub(
        r'^(MODEL_ID\s*=\s*)["\'].*?["\']',
        rf'\1"{model_id}"',
        text,
        flags=re.MULTILINE,
    )
    # DIMS = NNN
    text = re.sub(
        r'^(DIMS\s*=\s*)\d+',
        rf'\g<1>{dims}',
        text,
        flags=re.MULTILINE,
    )

    changed = text != original
    if changed and not dry_run:
        EMBED_PY_PATH.write_text(text, encoding="utf-8")
    return changed


def _print_plan(plan: dict) -> None:
    print(json.dumps(plan, indent=2, ensure_ascii=False))


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Switch the active embedding model across registry + embed.py + corpus-state.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    target_group = ap.add_mutually_exclusive_group()
    target_group.add_argument("--model-id", metavar="ID",
                               help="Target model ID (must already be in registry)")
    target_group.add_argument("--task-profile", metavar="PROFILE",
                               help="Resolve target via task_profiles key (e.g. high_accuracy)")
    target_group.add_argument("--list", action="store_true",
                               help="List all registered models + task profiles and exit")
    ap.add_argument("--dry-run", action="store_true",
                    help="Show migration plan without writing any files")
    ap.add_argument("--force", action="store_true",
                    help="Allow switching to same active model (no-op without --force)")
    ap.add_argument("--json", dest="json_out", action="store_true",
                    help="Print JSON plan to stdout")
    args = ap.parse_args()

    if not REGISTRY_PATH.exists():
        print(f"[error] registry not found: {REGISTRY_PATH}", file=sys.stderr)
        sys.exit(1)

    registry = _load_json(REGISTRY_PATH)
    models: dict = registry.get("models", {})
    task_profiles: dict = registry.get("task_profiles", {})
    current_active: str = registry.get("active_model_id", "")

    # ── --list ────────────────────────────────────────────────────────────────
    if args.list:
        print(f"\n{'─'*80}")
        print(f"  EMBED MODEL REGISTRY  |  active: {current_active}")
        print(f"{'─'*80}")
        print(f"\n  TASK PROFILES:")
        for profile, mid in task_profiles.items():
            marker = "◄ ACTIVE" if mid == current_active else ""
            dims = models.get(mid, {}).get("dims", "?")
            gated = models.get(mid, {}).get("gated", "?")
            print(f"    {profile:<32}  →  {mid:<52}  dims={dims}  gated={gated}  {marker}")
        print(f"\n  ALL MODELS ({len(models)}):")
        header = f"  {'MODEL ID':<52}  {'DIMS':>5}  {'CTX':>6}  {'GATED':>5}  {'SCHEMA':>6}  STATUS"
        print(header)
        print("  " + "─" * 78)
        for mid, info in models.items():
            dims = info.get("dims", "?")
            ctx  = info.get("context_tokens", "?")
            gated = str(info.get("gated", False))[:5]
            sv   = f"v{info.get('schema_version_required', '?')}"
            status = "◄ ACTIVE" if mid == current_active else ""
            print(f"  {mid:<52}  {str(dims):>5}  {str(ctx):>6}  {gated:>5}  {sv:>6}  {status}")
        print()
        sys.exit(0)

    # ── Resolve target model ──────────────────────────────────────────────────
    if args.task_profile:
        if args.task_profile not in task_profiles:
            print(f"[error] unknown task_profile '{args.task_profile}'. "
                  f"Available: {', '.join(task_profiles)}", file=sys.stderr)
            sys.exit(1)
        target_id = task_profiles[args.task_profile]
    elif args.model_id:
        target_id = args.model_id
    else:
        print("[error] provide --model-id, --task-profile, or --list", file=sys.stderr)
        sys.exit(1)

    # Validate target is in registry
    if target_id not in models:
        print(f"[error] '{target_id}' not found in registry. "
              f"Add it to scripts/embed_model_registry.json models{{}} first.", file=sys.stderr)
        sys.exit(1)

    target_info = models[target_id]
    target_dims: int = target_info.get("dims")
    target_ctx: int  = target_info.get("context_tokens")
    target_schema: int = target_info.get("schema_version_required", 4)
    target_gated = target_info.get("gated", False)

    # Check same-model no-op
    if target_id == current_active and not args.force:
        print(f"[info] '{target_id}' is already the active model. Use --force to re-apply.", file=sys.stderr)
        sys.exit(0)

    # Load corpus state
    corpus_state: dict = {}
    if CORPUS_STATE_PATH.exists():
        corpus_state = _load_json(CORPUS_STATE_PATH)

    current_dims: int = corpus_state.get("vec_dims", 0)
    current_vec_count: int = corpus_state.get("vec_count", 0)
    current_schema: int = corpus_state.get("schema_version", 4)

    dims_change = (target_dims != current_dims)
    schema_change = (target_schema != current_schema)
    reindex_needed = dims_change and current_vec_count > 0

    # ── Migration plan ────────────────────────────────────────────────────────
    plan = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "dry_run": args.dry_run,
        "from": {
            "model_id": current_active,
            "dims": current_dims,
            "schema_version": current_schema,
            "vec_count": current_vec_count,
        },
        "to": {
            "model_id": target_id,
            "dims": target_dims,
            "context_tokens": target_ctx,
            "schema_version": target_schema,
            "gated": target_gated,
        },
        "migration": {
            "dims_change": dims_change,
            "schema_change": schema_change,
            "reindex_needed": reindex_needed,
            "vec_count_reset": dims_change,
            "action": (
                "full_reindex" if reindex_needed else
                "schema_migration_only" if schema_change else
                "swap_only"
            ),
        },
        "surfaces_updated": [],
        "warnings": [],
    }

    if target_gated not in (False, "false", None):
        plan["warnings"].append(
            f"Model '{target_id}' is gated (type: {target_gated}). "
            "Run `bun run embed:gate:list` to check acceptance status before first use."
        )

    if reindex_needed:
        plan["warnings"].append(
            f"Dimension change {current_dims}d → {target_dims}d: "
            f"{current_vec_count} existing embeddings must be re-generated. "
            "Run: bun run session:corpus:rebuild --embed"
        )

    if schema_change:
        plan["warnings"].append(
            f"schema_version bump {current_schema} → {target_schema}: "
            "vec_embeddings DDL ALTER or DROP/CREATE required. "
            "Run: bun run session:corpus:rebuild to rebuild the corpus DB."
        )

    if not dims_change and current_vec_count == 0:
        plan["migration"]["action"] = "zero_cost_swap"

    # ── Print plan / JSON ─────────────────────────────────────────────────────
    if args.json_out or args.dry_run:
        print(json.dumps(plan, indent=2, ensure_ascii=False))
        if args.dry_run:
            print(f"\n[dry-run] no files written", file=sys.stderr)
            sys.exit(0)

    # ── Apply changes ─────────────────────────────────────────────────────────
    # 1. Registry
    registry["active_model_id"] = target_id
    registry["active_since"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    # Update recommended_next to the migration_to chain from the new active
    migration_to = target_info.get("migration_to")
    if migration_to and migration_to in models:
        registry["recommended_next"] = migration_to
    _save_json(REGISTRY_PATH, registry)
    plan["surfaces_updated"].append("scripts/embed_model_registry.json")

    # 2. embed.py
    if target_dims:
        changed = _patch_embed_py(target_id, target_dims, dry_run=False)
        if changed:
            plan["surfaces_updated"].append("scripts/embed.py")

    # 3. corpus-state.json
    if CORPUS_STATE_PATH.exists():
        corpus_state["vec_model"] = target_id
        corpus_state["vec_dims"] = target_dims
        corpus_state["schema_version"] = target_schema
        if dims_change:
            corpus_state["vec_count"] = 0   # invalidate — must re-embed
        _save_json(CORPUS_STATE_PATH, corpus_state)
        plan["surfaces_updated"].append("manifest/corpus-state.json")

    plan["dry_run"] = False

    # ── Summary ───────────────────────────────────────────────────────────────
    if not args.json_out:
        print(f"\n  ✓ switched: {current_active}  →  {target_id}")
        print(f"  dims:    {current_dims}d  →  {target_dims}d  {'(change!)' if dims_change else '(same)'}")
        print(f"  schema:  v{current_schema}  →  v{target_schema}")
        print(f"  action:  {plan['migration']['action']}")
        print(f"  updated: {', '.join(plan['surfaces_updated'])}")
        if plan["warnings"]:
            for w in plan["warnings"]:
                print(f"  [warn]   {w}")
        print()
    else:
        print(json.dumps(plan, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
