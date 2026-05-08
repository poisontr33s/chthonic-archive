---
type: scaffold
status: tier-1-stubs
report: docs/design/MILFOLOGICAL_OPPORTUNITY_REPORT.md
python: "3.12"
created: 2025-05-09
---

# milfological — cRPG Asset Generation Pipeline

MILFOLOGICAL entity generation pipeline for the chthonic-archive cRPG.
Maps SD inference candidates → entity asset workflows.

## Tier 1 Modules (P1 — immediately actionable)

| Module | Backend | Purpose |
|--------|---------|---------|
| `auto_caption.py` | SD.NEXT JoyCaption | Auto-caption entity reference images for LoRA training |
| `entity_cutout.py` | InvokeAI Grounding DINO + SAM2 | Background removal + entity segmentation mask |
| `entity_pixelart.py` | SD.NEXT img_to_pixelart pipeline | Entity sprite → pixel-art tileset |

## Environment

```bash
# Python 3.12 venv (see §XV of report for ladder rationale)
uv venv --python 3.12
uv sync
```

## Reference

Full candidate analysis: [MILFOLOGICAL_OPPORTUNITY_REPORT.md](../../docs/design/MILFOLOGICAL_OPPORTUNITY_REPORT.md)
