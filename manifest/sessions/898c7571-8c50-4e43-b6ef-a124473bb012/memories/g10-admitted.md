# G10 Admitted — HEAD b85c5476 (2026-04-26)

## State
- Gate 10: `admitted_model_load_gate` L2 — `load_time_s=18.2`, `state_loaded=True`
- FAF: v0.10
- CI membrane: 10 gates, 9 admitted (G1-G3, G5-G10), 1 impossible_currently (G4)
- Image: `0a625eec29f6` (33-STEP, ubuntu22.04, exllamav2 backend)

## Backend pivot (committed 49e6e33f)
- exllamav3 → exllamav2: EXL2 format not supported by exllamav3
- API: `ExLlamaV2Config(str(model_path))` / `ExLlamaV2(cfg)` / `model.load()` / `ExLlamaV2Tokenizer(cfg)`

## GPU passthrough
- CDI device: `--device nvidia.com/gpu=all` via `/etc/cdi/nvidia.json`
- Hooks path (`/usr/share/containers/oci/hooks.d/`) absent in NVIDIA-Workbench — CDI is correct
- WSL distro: `NVIDIA-Workbench` (exact case)

## Deviation log (Claudine directive)
- flash_attn CUDA kernel NOT compiled — Python-only patch (`patch-flash-attn-cuda-optional.py`)
- G11 generation will need flash_attn CUDA or torch SDPA fallback — unproven
- CMD in image bakes P-09 (build cached through); runtime override validates P-10; fix before G12

## Pending
- G11: P-11 generation gate — single completion + TTFT measurement
- CMD fix in Containerfile (P-09 → P-10)
- FAF v1.0 after G12 (OAI-compat endpoint E2E)

## Run command for G11 (template)
```bash
wsl -d NVIDIA-Workbench -- podman run --rm --device nvidia.com/gpu=all \
  -v /mnt/c/Users/eldno/chthonic-archive/probes/python:/ext-probes:ro \
  -v /mnt/c/Users/eldno/chthonic-archive/models/Llama-3.1-8B-Instruct-exl2-8.0bpw:/models/test-model:ro \
  -v /mnt/c/Users/eldno/chthonic-archive/manifest:/workspace/manifest \
  0a625eec29f6 python /ext-probes/P-11.py 2>&1
```
