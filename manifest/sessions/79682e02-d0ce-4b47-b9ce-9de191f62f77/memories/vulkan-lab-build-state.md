# Vulkan Lab Session State — 2026-04-18

## Environment (verified)
- Vulkan SDK 1.4.341.1 at C:\VulkanSDK\1.4.341.1
- Device: RTX 4090, Vulkan API 1.4.329, Driver 596.21
- glslc: shaderc v2026.1
- dxc: 1.9.0.5180
- cmake: 4.2.3-msvc3 at `C:\Program Files\Microsoft Visual Studio\18\Insiders\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe`
- NOTE: `cmake` on PATH is a broken uv shim — must use VS Insiders cmake directly
- cl.exe: available on PATH
- ninja: 1.13.0
- C++ compiler picked by CMake: GCC 15.2.0 from MSYS2 ucrt64 (via ruby rv)
- vulkaninfo: C:\WINDOWS\system32\vulkaninfo.exe (NOT in SDK Bin — SDK has vulkaninfoSDK.exe)

## Queue Families (RTX 4090)
- Q0: 16 queues — GRAPHICS | COMPUTE | TRANSFER | SPARSE_BINDING
- Q1: 2 queues — TRANSFER | SPARSE_BINDING (DMA)
- Q2: 8 queues — COMPUTE | TRANSFER | SPARSE_BINDING (async compute)
- Q3: 1 queue — TRANSFER | SPARSE | VIDEO_DECODE
- Q4: 2 queues — TRANSFER | SPARSE | VIDEO_ENCODE
- Q5: 1 queue — TRANSFER | SPARSE | OPTICAL_FLOW

## All 5 frontier extensions confirmed present
- V1 RT: acceleration_structure, ray_query, ray_tracing_pipeline, deferred_host_ops, rt_maintenance1, rt_position_fetch
- V2 CoopMatrix: cooperative_matrix (KHR), shader_float16_int8, 16bit_storage, 8bit_storage
- V3 Video: video_queue, decode_queue, decode h264/h265/av1/vp9, encode_queue, encode h264/h265/av1
- V4 DGC: device_generated_commands (EXT), mesh_shader (EXT+NV)
- V5 Infra: timeline_semaphore, synchronization2, dynamic_rendering, buffer_device_address, push_descriptor, descriptor_indexing

## Project Structure
```
vulkan-lab/
  CMakeLists.txt         (CXX project, finds Vulkan, builds vk_probe)
  CMakePresets.json       (dev + release presets)
  probes/
    vk_capability_probe.cpp  (full 5-vector probe)
  rust-lane/
    Cargo.toml            (ash 0.38 dep)
    src/main.rs           (stub)
```

## Build Status
- CMake configured OK (preset=dev, Ninja, GCC 15.2)
- vk_probe: BUILT + RAN — 41/41 frontier extensions, all data correct
- coop_matrix: BUILT + RAN — tensor-core GEMM confirmed, 0 errors, all 256 elements = 96.00
- Shader compiled via glslc --target-env=vulkan1.3 to coop_matmul.comp.spv
- Build dir: vulkan-lab/build/dev

## Current Edit Pass (iteration 2 — review fixes)
### Done:
- Probe type_str: changed `default: return "???"` to print raw enum value `?(N)` — identifies TF32/BF16/unknown types
- Probe: added VkPhysicalDeviceSubgroupProperties query (subgroup size, supported ops)

### In progress — EXACT EDIT TARGETS for timestamp insertion (main.cpp):

EDIT 1 — After cmd pool creation (~line 330-340), before cb_ai:
Insert after `VK_CHECK(vkCreateCommandPool(device, &cp_pool_ci, nullptr, &cmd_pool));`:
```cpp
    // ── Timestamp query pool ───────────────────────────────
    VkQueryPoolCreateInfo qp_ci{};
    qp_ci.sType = VK_STRUCTURE_TYPE_QUERY_POOL_CREATE_INFO;
    qp_ci.queryType = VK_QUERY_TYPE_TIMESTAMP;
    qp_ci.queryCount = 2;
    VkQueryPool query_pool;
    VK_CHECK(vkCreateQueryPool(device, &qp_ci, nullptr, &query_pool));
```

EDIT 2 — After vkCmdBindDescriptorSets, BEFORE vkCmdDispatch:
Insert before `// Dispatch: 1 workgroup`:
```cpp
    vkCmdResetQueryPool(cmd, query_pool, 0, 2);
    vkCmdWriteTimestamp(cmd, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, query_pool, 0);
```

EDIT 3 — After `vkCmdDispatch(cmd, 1, 1, 1);`, BEFORE memory barrier:
Insert after dispatch line:
```cpp
    vkCmdWriteTimestamp(cmd, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, query_pool, 1);
```

EDIT 4 — After fence wait `VK_CHECK(vkWaitForFences(...))`, before result readback:
Insert after `printf("Dispatch complete.\n");`:
```cpp
    // ── Read timestamps ────────────────────────────────────
    uint64_t timestamps[2] = {0, 0};
    vkGetQueryPoolResults(device, query_pool, 0, 2, sizeof(timestamps),
                          timestamps, sizeof(uint64_t),
                          VK_QUERY_RESULT_64_BIT | VK_QUERY_RESULT_WAIT_BIT);
    double ns = (double)(timestamps[1] - timestamps[0]) * (double)gpu_props.limits.timestampPeriod;
    double flops = 2.0 * M * N * K;
    double gflops = flops / ns;  // ns already in nanoseconds, so flops/ns = GFLOPS
    printf("  GPU time: %.0f ns (%.3f us)\n", ns, ns / 1000.0);
    printf("  Effective: %.6f GFLOPS (single tile, launch overhead dominates)\n", gflops);
```

EDIT 5 — Cleanup: add `vkDestroyQueryPool(device, query_pool, nullptr);` before `vkDestroyCommandPool`

### Still need:
- Apply timestamp edits to main.cpp
- Rebuild both targets (vk_probe + coop_matrix) and rerun

## Build Command (verified working)
```powershell
$cmake = 'C:\Program Files\Microsoft Visual Studio\18\Insiders\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe'
cd c:\Users\eldno\chthonic-archive\vulkan-lab
& $cmake --preset dev
& $cmake --build build/dev
```

## Run Commands (verified working)
```powershell
.\build\dev\vk_probe.exe
cd build\dev; .\coop_matrix.exe coop_matmul.comp.spv
```

## Key file locations:
- vulkan-lab/CMakeLists.txt — main build, has compile_shader() helper
- vulkan-lab/probes/vk_capability_probe.cpp — probe (just edited type_str + subgroup)
- vulkan-lab/vectors/coop_matrix/main.cpp — GEMM host (~275 lines)
- vulkan-lab/vectors/coop_matrix/coop_matmul.comp — GLSL compute shader
- vulkan-lab/rust-lane/ — ash stub (Cargo.toml + src/main.rs)

## Build Command
```powershell
$cmake = 'C:\Program Files\Microsoft Visual Studio\18\Insiders\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe'
& $cmake --preset dev
& $cmake --build build/dev --target vk_probe
```

## Also in progress (from earlier session)
- nvidia_drs_tool.ps1 -Audit mode completed: 16 active, 13 dead, 8 marginal for WoW
- User confirmed: OpenGL/Vulkan NVCP settings are NOT dead — driver shares paths across APIs
- HDR stack verified: Windows HDR ON + Auto HDR ON, RTX HDR OFF, WoW has no native HDR toggle
- Monitor: AOC AGON PRO AG276QZD (QD-OLED 1440p 240Hz) — real HDR panel
