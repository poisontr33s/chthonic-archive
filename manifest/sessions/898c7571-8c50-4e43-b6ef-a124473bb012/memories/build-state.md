# Build State — chthonic-tabby-modern-gpu

## Active Build
- Terminal ID: `f219b10d-b24e-4581-aa2f-9895173c204c` (PowerShell async, via wsl -d NVIDIA-Workbench)
- Command: `wsl -d NVIDIA-Workbench -- bash -c "cd /mnt/c/Users/eldno/chthonic-archive ; podman build --tag chthonic-tabby-modern-gpu:latest --file build/tabby-modern-gpu/Containerfile . 2>&1; echo BUILD_EXIT=$?"`
- STEPs 1-25: ALL cache-hit
- STEP 26: Actively compiling — nvcc + 4x cc1plus processes running at 100% CPU
- Started: ~21:07-21:09 CEST 2026-04-25
- Files being compiled: ext_gemm.cpp, ext_element.cpp, ext_bindings.cpp, ext_cache.cpp (C++ exts), unit_exl2_3b.cu (CUDA)
- Architecture: arch=compute_89,code=sm_89 (TORCH_CUDA_ARCH_LIST="8.9" working)
- Time: 21:10:13 at last ps check — ~2 min into compile

## Commit landed
- `953ca105` — fix(containerfile): restore TORCH_CUDA_ARCH_LIST for exllamav2 IndexError
- HEAD chain: 953ca105 → e5345e3c → 6f0c9591 → 0b2191f6

## After Build Succeeds — Next Steps
1. Run P-08: `podman run --rm --device nvidia.com/gpu=all -v /mnt/c/Users/eldno/chthonic-archive/manifest:/workspace/manifest:Z chthonic-tabby-modern-gpu:latest`
2. Read manifest: `cat /mnt/c/Users/eldno/chthonic-archive/manifest/exllamav2_source_gate.json`
3. Update FAF G4 row in `docs/reference/FAF_TABBYAPI_PY314_GPU_INFERENCE_HOST.md` from `source_build_unprobed` to admitted status
4. Commit FAF update (git add -f, --no-verify, Co-authored-by: Pentea trailer)

## WSL Notes
- WSL distro: `NVIDIA-Workbench` (not `Ubuntu`)
- Sync terminal runs IN WSL2 (`workbench@erd` prompt)  
- Async terminal runs in PowerShell — use `wsl -d NVIDIA-Workbench --` to get WSL2
- Git commit: use execution_subagent (direct git commands hang via sync terminal)
- `build/` is gitignored — always `git add -f`
