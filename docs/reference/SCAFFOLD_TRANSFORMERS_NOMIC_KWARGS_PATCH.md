<!--
@SID:           REF_SCAFFOLD_TRANSFORMERS_PATCH_V1
@Type:          Scaffold
@Context:       CocoIndex / chthonic-archive — transformers NomicBertModel **kwargs fragile patch
@SessionOrigin: COCOINDEX_SEMANTIC_SEARCH_2026-04-30
@References:    FAF_COCOINDEX_SEMANTIC_SEARCH.md §G1, CLAUDINE_MD_TYPE_LEXICON.md
-->

---
type: scaffold
name: TRANSFORMERS_NOMIC_KWARGS_PATCH
holds_up: >
  CocoIndex semantic search in both chthonic-archive and PsychoNoir-Kontrapunkt.
  Without this patch, loading nomic-ai/CodeRankEmbed raises:
  TypeError: NomicBertModel.__init__() got an unexpected keyword argument 'safe_serialization'
removal_condition: >
  transformers upstream merges a fix for NomicBertModel.__init__ to accept **kwargs
  OR cocoindex-code pins transformers to a compatible version in its own dependency spec.
  Reopen gate G_TRANSFORMERS_PATCH_PERSISTENCE when either condition is true.
deadline: >
  No hard deadline. Re-check on each uv tool upgrade cocoindex-code.
  If cocoindex-code ships a version that bundles this fix, remove immediately.
risk_if_left: >
  Patch is silently lost every time uv tool upgrade cocoindex-code runs.
  Symptom: ccc index fails with TypeError. No semantic search until patch is re-applied.
  Risk: undetected degradation if upgrade happens in a session where the symptom isn't exercised.
filed: 2026-05-01
status: active
ssot_note: >
  FAF_COCOINDEX_SEMANTIC_SEARCH.md §G1 (gate: G_TRANSFORMERS_PATCH_PERSISTENCE,
  status: impossible-currently).
---

# Scaffold: TRANSFORMERS_NOMIC_KWARGS_PATCH

**Status:** Active  
**Filed:** 2026-05-01  
**Removal condition:** See frontmatter.

---

## What This Scaffold Is

`nomic-ai/CodeRankEmbed` is loaded by CocoIndex during `ccc index`.  
The HuggingFace model loader passes `safe_serialization=True` as a keyword argument to `NomicBertModel.__init__`.  
`NomicBertModel` in transformers ≤5.7.0 does not accept this keyword — it lacks `**kwargs`.

**The patch:**

File: `C:\Users\eldno\AppData\Roaming\uv\tools\cocoindex-code\Lib\site-packages\transformers\models\nomic_bert\modeling_nomic_bert.py`  
Line: ~392  

Before:
```python
def __init__(self, config, add_pooling_layer=False):
```

After:
```python
def __init__(self, config, add_pooling_layer=False, **kwargs):
```

---

## Why This Is a Scaffold, Not a Fix

The patch is applied to a file inside a `uv`-managed tool environment. Every `uv tool upgrade cocoindex-code` regenerates the environment and wipes the patch.

This is not a fix — it is a temporary load-bearing structure. The load it bears is "CocoIndex works." The structure it temporarily replaces is "upstream transformers ships the correct signature."

A scaffold.md file exists to ensure this temporary structure is:
1. Named (not invisible)
2. Tracked with a removal condition (not carried forward indefinitely)
3. Flagged for each session that upgrades the tool

---

## Re-Application Procedure

If the patch is lost after a `uv tool upgrade`:

```powershell
# Find the file
$site = uv run --with cocoindex-code python -c "import transformers; print(transformers.__file__)" 2>&1
# Navigate to the nomic_bert directory and apply the one-line patch
# OR run:
uv run scripts/restore_transformers_patch.py  # (if this script exists — check scripts/ first)
```

If `scripts/restore_transformers_patch.py` does not exist, apply manually:
1. Open `modeling_nomic_bert.py` at the path above
2. Find `def __init__(self, config, add_pooling_layer=False):`
3. Add `, **kwargs` before the closing `)`
4. Verify: `ccc index` runs without TypeError

---

## Removal Procedure

When the removal condition is met (transformers upstream fix OR cocoindex-code pins the version):

1. Run `uv tool upgrade cocoindex-code` (patch is already lost at this point)
2. Run `ccc index` — if it succeeds without manual patch, the scaffold is no longer needed
3. Update this file's frontmatter: `status: removed`
4. Delete the `impossible-currently` entry from `FAF_COCOINDEX_SEMANTIC_SEARCH.md §G1`
5. Commit with message: `remove transformers scaffold — upstream fix landed`
