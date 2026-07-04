---
title: NVIDIA DLL Inventory
status: living-document
tier: T1-operational
last-snapshot: 2026-06-30
driver: 610.62
---

# NVIDIA DLL Inventory

Canonical path map for all NVIDIA DLLs that are part of the natural runtime environment on this machine. Snapshotted against driver 610.62 / CUDA UMD 13.3. Authoritative hardware baseline lives in `COMPUTE_FRONTIER_LANDSCAPE.md §0.2`.

---

## Driver DLLs — System32 (610.62)

All installed and owned by the driver. Available to any process without elevation. The version string `32.0.16.1062` is NVIDIA's internal encoding of driver build 610.62.

| DLL | Version | Purpose |
|-----|---------|---------|
| `nvapi64.dll` | 32.0.16.1062 | NVAPI — GPU feature queries, OC, power policy |
| `nvcuda.dll` | 32.0.16.1062 | CUDA driver API — interop surface for vulkan-lab and forge |
| `nvcuvid.dll` | 7.17.16.1062 (30.7 MB) | CUDA Video Decode — V3 vector dependency |
| `nvEncodeAPI64.dll` | 32.0.16.1062 | NVENC encode API — V3 encode lane |
| `NvFBC64.dll` | 6.14.16.1062 | Frame Buffer Capture (desktop → GPU texture) |
| `NvIFR64.dll` | 6.14.16.1062 | Inband Frame Readback (legacy capture) |
| `nvml.dll` | 8.17.16.1062 | Management Library — nvidia-smi, process GPU tracking |
| `nvofapi64.dll` | 32.0.16.1062 | Optical Flow API — NVOF vectors for motion estimation |
| `nvcpl.dll` | 8.17.16.1062 | Control Panel driver layer |
| `nvaudcap64v.dll` | 4.65.0.12 | Audio capture (ShadowPlay / NVIDIA App) |
| `nvspcap64.dll` | 11.0.8.244 | ShadowPlay capture |

Path: `C:\Windows\System32\`

---

## NGX / AI Features (app-bundled)

The driver does NOT bundle `nvngx_dlss.dll` — it ships the NGX framework loader (`nvngx.dll`) and each app/game supplies its own DLSS DLL. Versions therefore vary per install.

| DLL | Version | Where | Notes |
|-----|---------|-------|-------|
| `nvngx_dlss.dll` | **310.7.0.0** | Streamline SDK v2.12.0 (`CLAUDEBASE/.../streamline-sdk-v2.12.0/bin/x64/`) | Newest on disk — DLSS 4, revision 7 |
| `nvngx_dlss.dll` | 310.6.0.0 | WoW `_retail_`, `target/debug` | One revision behind |
| `nvngx_dlss.dll` | 310.1.0.0 | KCD2 `Bin\Win64Shared` | Game-bundled at ship time |
| `nvngx_dlss.dll` | 3.8.10.0 | NVIDIA App OTA cache | Old pre-v4 artifact; ignore |
| `nvngx_dlisr.dll` | 1.2.0.0 (56 MB) | `C:\Program Files\NVIDIA Corporation\NVIDIA App\NvBackend\` | Image Scaling / DLSR model — different from DLSS SR |

DLSS versioning note: `310.x.x.x` = DLSS 4 era (new scheme); `3.x.x.x` = DLSS 3 era (old scheme). The third `310.1/6/7` digit maps to DLSS 4 revision.

`nvngx_dlssg.dll` (Frame Gen) and `nvngx_dlssd.dll` (Ray Reconstruction) were not found on disk — RTX 4090 supports both capabilities but no installed game has shipped them to this machine.

**NGX loader (`nvngx.dll` / `_nvngx.dll`) status:** not present in System32 or `Program Files\NVIDIA Corporation\NGX\`. Only copy on disk is a Driver Store residual from a prior driver install (`DriverStore\FileRepository\nv_dispi.inf_amd64_6f3cfb7117944855\nvngx.dll`, version 30.0.14.9516). Driver 610.62 does not deploy the NGX loader to a standard user-accessible path — DLSS operates via game-bundled DLLs directly.

---

## CUDA Toolkit (12.8 installed)

CUDA 12.8 is the only toolkit with DLLs on disk. Directories for 12.9 / 13.2 / 13.3 exist but are empty stubs — the driver's UMD 13.3 max does not install separate toolkit binaries.

Path: `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8\bin\`

| DLL | Version | Purpose |
|-----|---------|---------|
| `cudart64_12.dll` | 6.14.11.12080 | CUDA runtime |
| `cublas64_12.dll` | 6.14.11.1284 | cuBLAS |
| `cublasLt64_12.dll` | 6.14.11.1284 | cuBLAS-Lt (lightweight) |
| `curand64_10.dll` | 6.14.11.1039 | cuRAND |
| `cusolver64_11.dll` | 6.14.11.1173 | cuSOLVER |
| `cusolverMg64_11.dll` | 6.14.11.1173 | cuSOLVER multi-GPU |
| `nvrtc64_120_0.dll` | 6.14.11.9000 | NVRTC — runtime compilation |

---

## cuDNN

Path: `C:\Program Files\NVIDIA\CUDNN\v9.20\bin\13.2\x64\`

| DLL | Version | Purpose |
|-----|---------|---------|
| `cudnn_adv64_9.dll` | 9.20.0.48 | Advanced ops (RNN, attention) |
| `cudnn_cnn64_9.dll` | 9.20.0.48 | CNN convolutions |
| `cudnn_engines_precompiled64_9.dll` | 9.20.0.48 | Pre-compiled engine cache |
| `cudnn_engines_runtime_compiled64_9.dll` | 9.20.0.48 | Runtime-compiled engines |
| `cudnn_graph64_9.dll` | — | Graph-mode execution |

Targets CUDA 13.2 runtime (path encodes this). cuDNN 9.20 is the v9 generation — compatible with PyTorch ≥ 2.5, TensorRT 10.x.

`CUDNN_PATH` env var is not set — cuDNN is not on a discovered system path. Frameworks find it through their own resolution or explicit path configuration.

### CUDA Env Var State (verified 2026-06-30)

| Var | Points To | Status |
|-----|-----------|--------|
| `CUDA_PATH` | `v13.3\` | Correct — nvcc 13.3 (Apr 2026), headers, import libs; runtime DLLs NOT present in 13.3 |
| `CUDA_PATH_V12_8` | `v12.8\` | Runtime DLL layer — `cudart64_12.dll`, `cublas64_12.dll`, etc. live here |
| `CUDA_PATH_V13_2` | `v13.2\` | Stub (no binaries confirmed) |
| `CUDA_PATH_V13_3` | `v13.3\` | Same as `CUDA_PATH` |
| `CUDA_PATH_V12_9` | — | Not set |
| `CUDNN_PATH` | — | Not set |
| `NGX_SDK_DIR` | — | Not set |

**Layered install pattern:** compile via `nvcc` from 13.3 (`CUDA_PATH`); runtime DLLs resolve from `v12.8\bin` via PATH (12.8 bin appears after 13.3 on PATH). Code compiled targeting `sm_89` (RTX 4090) with 13.3 nvcc links successfully against 12.8 runtime.

---

## Developer / Profiling Tools

| Suite | Version | Path |
|-------|---------|------|
| Nsight Visual Studio | 2026.2.0.26084 | `C:\Program Files\NVIDIA Corporation\Nsight Visual Studio Edition\` |
| Nsight Compute | 2026.2.0.26099–26104 | `C:\Program Files\NVIDIA Corporation\Nsight Compute\` |
| Nsight Systems | 2026.2.0.26099–26104 | `C:\Program Files\NVIDIA Corporation\Nsight Systems\` |
| FrameView SDK | — (no versioned DLLs) | `C:\Program Files\NVIDIA Corporation\FrameViewSDK\` |

---

## NVIDIA App Layer

| DLL | Version | Role |
|-----|---------|------|
| `NvAppApi.dll` | 11.0.8.244 | NVIDIA App public API |
| `NvBackend64.dll` | 43.5.0.0 | Backend engine (GeForce Experience successor) |
| `NvCamera.dll` | 11.0.8.244 | Ansel / RTX camera |
| `NvAccount.dll` | 11.0.8.244 | Account / identity layer |

---

## Access Verification (2026-06-30)

Vulkan SDK `C:\VulkanSDK\1.4.350.0` owned by `erd\eldno`. All key binaries (`glslc.exe`, `vulkaninfoSDK.exe`, `vulkan-1.lib`, `vulkan.h`) verified readable without elevation. No admin scope on any DLL listed above.
