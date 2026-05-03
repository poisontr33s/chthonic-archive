# Gate 9 Run State

## Current Action
Rebuilding `chthonic-tabby-modern-gpu:latest` in WSL2 NVIDIA-Workbench.
Terminal ID: `c20da2bc-5595-4d0f-885e-c874f73835cb`

## What Changed in Containerfile (commit eea98a37)
- Added COPY layers: `apps/tabby-modern/pyproject.toml` + `src/` → `/workspace/app/`
- Added `uv pip install -e /workspace/app/ --no-build-isolation`
- CMD: P-08.py → P-09.py

## After Build Completes
Run: `wsl -d NVIDIA-Workbench -- bash -c "cd /mnt/c/Users/eldno/chthonic-archive && podman run --rm --security-opt=label=disable --hooks-dir=/usr/share/containers/oci/hooks.d/ --volume /mnt/c/Users/eldno/chthonic-archive/manifest:/workspace/manifest chthonic-tabby-modern-gpu:latest 2>&1; echo RUN_EXIT=$?"`

## Expected P-09 output (manifest/tabby_modern_import_gate.json)
- status: admitted_import_gate OR failed_import_gate
- module_imports: dict of all 9 tabby_modern modules
- settings_check, app_factory_check
- level: admitted_import_gate = L4_useful

## FAF State
- v0.8 committed at eea98a37
- Gate 9: probe_declared → waiting for probe_executed + admitted/failed

## Prior gate state
- G1-G7: all admitted/warned as documented
- G8 (P-08): admitted_L2_source_linux (exllamav2 source build)
- Image hash before rebuild: 3062c46dac1b (P-08 era)
