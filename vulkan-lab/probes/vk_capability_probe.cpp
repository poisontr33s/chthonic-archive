// vulkan-lab/probes/vk_capability_probe.cpp
// ─────────────────────────────────────────────────────────────
// Enumerates RTX 4090 Vulkan capabilities for five frontier
// exploration vectors. Outputs a structured report.
// ─────────────────────────────────────────────────────────────

#include <vulkan/vulkan.h>

#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

// ── Helpers ────────────────────────────────────────────────

#define VK_CHECK(call)                                                 \
    do {                                                               \
        VkResult r = (call);                                           \
        if (r != VK_SUCCESS) {                                         \
            fprintf(stderr, "FATAL: %s returned %d\n", #call, (int)r); \
            return 1;                                                  \
        }                                                              \
    } while (0)

static const char* queue_flag_str(VkQueueFlags flags) {
    static char buf[256];
    buf[0] = '\0';
    if (flags & VK_QUEUE_GRAPHICS_BIT)       strcat(buf, "GRAPHICS ");
    if (flags & VK_QUEUE_COMPUTE_BIT)        strcat(buf, "COMPUTE ");
    if (flags & VK_QUEUE_TRANSFER_BIT)       strcat(buf, "TRANSFER ");
    if (flags & VK_QUEUE_SPARSE_BINDING_BIT) strcat(buf, "SPARSE ");
    if (flags & VK_QUEUE_VIDEO_DECODE_BIT_KHR) strcat(buf, "VIDEO_DECODE ");
    if (flags & VK_QUEUE_VIDEO_ENCODE_BIT_KHR) strcat(buf, "VIDEO_ENCODE ");
    if (flags & VK_QUEUE_OPTICAL_FLOW_BIT_NV)  strcat(buf, "OPTICAL_FLOW ");
    return buf;
}

struct FrontierExt {
    const char* name;
    int         vector;  // 1-5 matching our exploration vectors
    const char* purpose;
    bool        found = false;
};

// ── Main ───────────────────────────────────────────────────

int main() {
    printf("╔══════════════════════════════════════════════════════╗\n");
    printf("║  Vulkan Lab — Device Capability Probe               ║\n");
    printf("║  chthonic-archive/vulkan-lab                        ║\n");
    printf("╚══════════════════════════════════════════════════════╝\n\n");

    // ── Instance creation ──────────────────────────────────
    VkApplicationInfo app_info{};
    app_info.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO;
    app_info.pApplicationName = "vulkan-lab-probe";
    app_info.applicationVersion = VK_MAKE_VERSION(0, 1, 0);
    app_info.pEngineName = "chthonic";
    app_info.engineVersion = VK_MAKE_VERSION(0, 1, 0);
    app_info.apiVersion = VK_API_VERSION_1_3;

    VkInstanceCreateInfo inst_ci{};
    inst_ci.sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;
    inst_ci.pApplicationInfo = &app_info;

    VkInstance instance;
    VK_CHECK(vkCreateInstance(&inst_ci, nullptr, &instance));

    // ── Physical device ────────────────────────────────────
    uint32_t dev_count = 0;
    VK_CHECK(vkEnumeratePhysicalDevices(instance, &dev_count, nullptr));
    if (dev_count == 0) {
        fprintf(stderr, "No Vulkan physical devices found.\n");
        return 1;
    }

    std::vector<VkPhysicalDevice> devices(dev_count);
    VK_CHECK(vkEnumeratePhysicalDevices(instance, &dev_count, devices.data()));

    // Pick first discrete GPU (or first device)
    VkPhysicalDevice gpu = devices[0];
    VkPhysicalDeviceProperties props;
    for (auto& d : devices) {
        vkGetPhysicalDeviceProperties(d, &props);
        if (props.deviceType == VK_PHYSICAL_DEVICE_TYPE_DISCRETE_GPU) {
            gpu = d;
            break;
        }
    }
    vkGetPhysicalDeviceProperties(gpu, &props);

    printf("=== Device ===\n");
    printf("  Name       : %s\n", props.deviceName);
    printf("  API Version: %u.%u.%u\n",
           VK_VERSION_MAJOR(props.apiVersion),
           VK_VERSION_MINOR(props.apiVersion),
           VK_VERSION_PATCH(props.apiVersion));
    printf("  Driver Ver : %u.%u.%u.%u\n",
           (props.driverVersion >> 22) & 0x3FF,
           (props.driverVersion >> 14) & 0xFF,
           (props.driverVersion >> 6) & 0xFF,
           props.driverVersion & 0x3F);
    printf("  Vendor ID  : 0x%04X\n", props.vendorID);
    printf("  Device ID  : 0x%04X\n", props.deviceID);
    printf("  Type       : %s\n",
           props.deviceType == VK_PHYSICAL_DEVICE_TYPE_DISCRETE_GPU ? "Discrete GPU" :
           props.deviceType == VK_PHYSICAL_DEVICE_TYPE_INTEGRATED_GPU ? "Integrated GPU" :
           "Other");

    // ── Subgroup properties ────────────────────────────────
    VkPhysicalDeviceSubgroupProperties subgroup_props{};
    subgroup_props.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SUBGROUP_PROPERTIES;

    VkPhysicalDeviceProperties2 props2_sg{};
    props2_sg.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PROPERTIES_2;
    props2_sg.pNext = &subgroup_props;
    vkGetPhysicalDeviceProperties2(gpu, &props2_sg);

    printf("  Subgroup sz: %u\n", subgroup_props.subgroupSize);
    printf("  Subgroup ops: %s%s%s%s%s%s\n",
           (subgroup_props.supportedOperations & VK_SUBGROUP_FEATURE_BASIC_BIT) ? "BASIC " : "",
           (subgroup_props.supportedOperations & VK_SUBGROUP_FEATURE_VOTE_BIT) ? "VOTE " : "",
           (subgroup_props.supportedOperations & VK_SUBGROUP_FEATURE_ARITHMETIC_BIT) ? "ARITH " : "",
           (subgroup_props.supportedOperations & VK_SUBGROUP_FEATURE_BALLOT_BIT) ? "BALLOT " : "",
           (subgroup_props.supportedOperations & VK_SUBGROUP_FEATURE_SHUFFLE_BIT) ? "SHUFFLE " : "",
           (subgroup_props.supportedOperations & VK_SUBGROUP_FEATURE_QUAD_BIT) ? "QUAD " : "");

    // ── Memory ─────────────────────────────────────────────
    VkPhysicalDeviceMemoryProperties mem_props;
    vkGetPhysicalDeviceMemoryProperties(gpu, &mem_props);

    printf("\n=== Memory Heaps ===\n");
    for (uint32_t i = 0; i < mem_props.memoryHeapCount; i++) {
        auto& heap = mem_props.memoryHeaps[i];
        printf("  Heap %u: %llu MB [%s%s]\n", i,
               (unsigned long long)(heap.size / (1024 * 1024)),
               (heap.flags & VK_MEMORY_HEAP_DEVICE_LOCAL_BIT) ? "DEVICE_LOCAL " : "",
               (heap.flags & VK_MEMORY_HEAP_MULTI_INSTANCE_BIT) ? "MULTI_INSTANCE " : "");
    }

    // ── Queue Families ─────────────────────────────────────
    uint32_t qf_count = 0;
    vkGetPhysicalDeviceQueueFamilyProperties(gpu, &qf_count, nullptr);
    std::vector<VkQueueFamilyProperties> queue_fams(qf_count);
    vkGetPhysicalDeviceQueueFamilyProperties(gpu, &qf_count, queue_fams.data());

    printf("\n=== Queue Families ===\n");
    for (uint32_t i = 0; i < qf_count; i++) {
        printf("  [%u] count=%u  flags: %s\n", i,
               queue_fams[i].queueCount,
               queue_flag_str(queue_fams[i].queueFlags));
    }

    // ── Device Extensions ──────────────────────────────────
    uint32_t ext_count = 0;
    VK_CHECK(vkEnumerateDeviceExtensionProperties(gpu, nullptr, &ext_count, nullptr));
    std::vector<VkExtensionProperties> exts(ext_count);
    VK_CHECK(vkEnumerateDeviceExtensionProperties(gpu, nullptr, &ext_count, exts.data()));

    // Frontier extensions grouped by exploration vector
    FrontierExt frontier[] = {
        // Vector 1: RT cores for spatial queries
        {"VK_KHR_acceleration_structure",      1, "BVH build/query"},
        {"VK_KHR_ray_query",                   1, "Inline ray queries in compute"},
        {"VK_KHR_ray_tracing_pipeline",        1, "Full RT pipeline"},
        {"VK_KHR_deferred_host_operations",    1, "Async BVH build on CPU"},
        {"VK_KHR_ray_tracing_maintenance1",    1, "RT pipeline maintenance"},
        {"VK_KHR_ray_tracing_position_fetch",  1, "Fetch hit position in shader"},

        // Vector 2: Cooperative matrix ML inference
        {"VK_KHR_cooperative_matrix",          2, "KHR tensor-core matrix ops"},
        {"VK_NV_cooperative_matrix",           2, "NV tensor-core matrix ops (legacy)"},
        {"VK_KHR_shader_float16_int8",         2, "FP16/INT8 in shaders"},
        {"VK_KHR_16bit_storage",               2, "16-bit storage buffers"},
        {"VK_KHR_8bit_storage",                2, "8-bit storage buffers"},
        {"VK_EXT_shader_atomic_float",         2, "Atomic float ops"},

        // Vector 3: Video queue compositing
        {"VK_KHR_video_queue",                 3, "Video queue family"},
        {"VK_KHR_video_decode_queue",          3, "Video decode dispatch"},
        {"VK_KHR_video_decode_h264",           3, "H.264 decode"},
        {"VK_KHR_video_decode_h265",           3, "H.265/HEVC decode"},
        {"VK_KHR_video_decode_av1",            3, "AV1 decode"},
        {"VK_KHR_video_encode_queue",          3, "Video encode dispatch"},
        {"VK_KHR_video_encode_h264",           3, "H.264 encode"},
        {"VK_KHR_video_encode_h265",           3, "H.265/HEVC encode"},
        {"VK_KHR_video_encode_av1",            3, "AV1 encode"},
        {"VK_KHR_video_maintenance1",          3, "Video maintenance"},

        // Vector 4: GPU-autonomous rendering
        {"VK_EXT_device_generated_commands",   4, "GPU writes own cmd buffers"},
        {"VK_NV_device_generated_commands",    4, "NV GPU cmd gen (legacy)"},
        {"VK_EXT_mesh_shader",                 4, "KHR mesh shaders"},
        {"VK_NV_mesh_shader",                  4, "NV mesh shaders (legacy)"},

        // Vector 5: GPU-as-primary-processor (infrastructure)
        {"VK_KHR_timeline_semaphore",          5, "Timeline semaphores (condition vars)"},
        {"VK_KHR_synchronization2",            5, "Sync2 (pipeline barriers)"},
        {"VK_KHR_dynamic_rendering",           5, "Renderpass-less rendering"},
        {"VK_KHR_buffer_device_address",       5, "GPU-visible buffer pointers"},
        {"VK_KHR_push_descriptor",             5, "Inline descriptor updates"},
        {"VK_EXT_descriptor_indexing",         5, "Bindless descriptors"},
        {"VK_KHR_maintenance4",               5, "Maintenance4"},
        {"VK_KHR_maintenance5",               5, "Maintenance5"},
        {"VK_KHR_maintenance6",               5, "Maintenance6"},
        {"VK_KHR_spirv_1_4",                  5, "SPIR-V 1.4 support"},
        {"VK_KHR_shader_float_controls",      5, "Float rounding/denorm control"},
        {"VK_KHR_external_memory",            5, "Cross-process memory sharing"},
        {"VK_KHR_external_semaphore",         5, "Cross-process sync"},
        {"VK_EXT_memory_budget",              5, "VRAM budget queries"},
        {"VK_EXT_memory_priority",            5, "Allocation priority hints"},
    };

    constexpr int frontier_count = sizeof(frontier) / sizeof(frontier[0]);

    // Match extensions
    for (auto& f : frontier) {
        for (auto& e : exts) {
            if (strcmp(f.name, e.extensionName) == 0) {
                f.found = true;
                break;
            }
        }
    }

    // ── Report by vector ───────────────────────────────────
    const char* vector_names[] = {
        "",
        "RT Cores for Spatial Queries",
        "Cooperative Matrix ML Inference",
        "Video Queue Compositing",
        "GPU-Autonomous Rendering",
        "GPU-as-Primary-Processor"
    };

    printf("\n=== Frontier Extension Support ===\n");
    int total_supported = 0, total_missing = 0;

    for (int v = 1; v <= 5; v++) {
        printf("\n  Vector %d: %s\n", v, vector_names[v]);
        int v_ok = 0, v_miss = 0;
        for (int i = 0; i < frontier_count; i++) {
            if (frontier[i].vector != v) continue;
            const char* status = frontier[i].found ? "  YES" : "  ---";
            printf("    %-50s %s  (%s)\n", frontier[i].name, status, frontier[i].purpose);
            if (frontier[i].found) { v_ok++; total_supported++; }
            else { v_miss++; total_missing++; }
        }
        printf("    >> %d/%d supported\n", v_ok, v_ok + v_miss);
    }

    printf("\n=== Summary ===\n");
    printf("  Extensions: %u total on device\n", ext_count);
    printf("  Frontier  : %d/%d supported (%d missing)\n",
           total_supported, frontier_count, total_missing);
    printf("  Queue families: %u\n", qf_count);

    // Queue family recommendations for each vector
    printf("\n=== Queue Family Assignments ===\n");
    for (uint32_t i = 0; i < qf_count; i++) {
        auto flags = queue_fams[i].queueFlags;
        std::string uses;
        if ((flags & VK_QUEUE_GRAPHICS_BIT) && (flags & VK_QUEUE_COMPUTE_BIT))
            uses += "V1(RT)/V4(DGC)/V5(main) ";
        else if ((flags & VK_QUEUE_COMPUTE_BIT) && !(flags & VK_QUEUE_GRAPHICS_BIT))
            uses += "V2(coop_matrix)/V5(compute) ";
        if (flags & VK_QUEUE_VIDEO_DECODE_BIT_KHR)
            uses += "V3(decode) ";
        if (flags & VK_QUEUE_VIDEO_ENCODE_BIT_KHR)
            uses += "V3(encode) ";
        if (flags & VK_QUEUE_OPTICAL_FLOW_BIT_NV)
            uses += "OPTICAL_FLOW ";
        if ((flags & VK_QUEUE_TRANSFER_BIT) && !(flags & VK_QUEUE_COMPUTE_BIT) &&
            !(flags & VK_QUEUE_GRAPHICS_BIT) && !(flags & VK_QUEUE_VIDEO_DECODE_BIT_KHR) &&
            !(flags & VK_QUEUE_VIDEO_ENCODE_BIT_KHR) && !(flags & VK_QUEUE_OPTICAL_FLOW_BIT_NV))
            uses += "DMA(copy) ";
        if (uses.empty()) uses = "(general)";
        printf("  [%u] count=%-2u  %-40s  -> %s\n", i,
               queue_fams[i].queueCount, queue_flag_str(queue_fams[i].queueFlags),
               uses.c_str());
    }

    // ── Compute limits ─────────────────────────────────────
    printf("\n=== Compute Limits ===\n");
    printf("  Max compute shared memory : %u bytes\n", props.limits.maxComputeSharedMemorySize);
    printf("  Max compute work group cnt: %u x %u x %u\n",
           props.limits.maxComputeWorkGroupCount[0],
           props.limits.maxComputeWorkGroupCount[1],
           props.limits.maxComputeWorkGroupCount[2]);
    printf("  Max compute work group sz : %u x %u x %u\n",
           props.limits.maxComputeWorkGroupSize[0],
           props.limits.maxComputeWorkGroupSize[1],
           props.limits.maxComputeWorkGroupSize[2]);
    printf("  Max compute invocations   : %u\n", props.limits.maxComputeWorkGroupInvocations);
    printf("  Max push constant size    : %u bytes\n", props.limits.maxPushConstantsSize);
    printf("  Max bound descriptor sets : %u\n", props.limits.maxBoundDescriptorSets);
    printf("  Max storage buffer range  : %u bytes\n", props.limits.maxStorageBufferRange);
    printf("  Timestamp compute+graphics: %s\n",
           props.limits.timestampComputeAndGraphics ? "yes" : "no");

    // ── RT properties (if available) ───────────────────────
    VkPhysicalDeviceRayTracingPipelinePropertiesKHR rt_props{};
    rt_props.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_RAY_TRACING_PIPELINE_PROPERTIES_KHR;

    VkPhysicalDeviceAccelerationStructurePropertiesKHR as_props{};
    as_props.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_ACCELERATION_STRUCTURE_PROPERTIES_KHR;
    as_props.pNext = &rt_props;

    VkPhysicalDeviceProperties2 props2{};
    props2.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PROPERTIES_2;
    props2.pNext = &as_props;
    vkGetPhysicalDeviceProperties2(gpu, &props2);

    printf("\n=== Ray Tracing Properties ===\n");
    printf("  Max ray recursion depth     : %u\n", rt_props.maxRayRecursionDepth);
    printf("  Max ray dispatch invocations: %u\n", rt_props.maxRayDispatchInvocationCount);
    printf("  Max ray hit attribute size  : %u bytes\n", rt_props.maxRayHitAttributeSize);
    printf("  Shader group handle size    : %u bytes\n", rt_props.shaderGroupHandleSize);
    printf("  Max geometry count (BLAS)   : %llu\n",
           (unsigned long long)as_props.maxGeometryCount);
    printf("  Max instance count (TLAS)   : %llu\n",
           (unsigned long long)as_props.maxInstanceCount);
    printf("  Max primitive count (BLAS)  : %llu\n",
           (unsigned long long)as_props.maxPrimitiveCount);

    // ── Cooperative matrix properties ──────────────────────
    // Query supported matrix types
    PFN_vkGetPhysicalDeviceCooperativeMatrixPropertiesKHR getCoop =
        (PFN_vkGetPhysicalDeviceCooperativeMatrixPropertiesKHR)
        vkGetInstanceProcAddr(instance, "vkGetPhysicalDeviceCooperativeMatrixPropertiesKHR");

    if (getCoop) {
        uint32_t coop_count = 0;
        getCoop(gpu, &coop_count, nullptr);
        if (coop_count > 0) {
            std::vector<VkCooperativeMatrixPropertiesKHR> coop_props(coop_count);
            for (auto& c : coop_props) {
                c.sType = VK_STRUCTURE_TYPE_COOPERATIVE_MATRIX_PROPERTIES_KHR;
                c.pNext = nullptr;
            }
            getCoop(gpu, &coop_count, coop_props.data());

            printf("\n=== Cooperative Matrix Types (%u) ===\n", coop_count);
            int shown = 0;
            for (auto& c : coop_props) {
                if (shown >= 20) {
                    printf("  ... and %u more\n", coop_count - shown);
                    break;
                }
                auto type_str = [](VkComponentTypeKHR t) -> const char* {
                    switch (t) {
                        case VK_COMPONENT_TYPE_FLOAT16_KHR:    return "FP16";
                        case VK_COMPONENT_TYPE_FLOAT32_KHR:    return "FP32";
                        case VK_COMPONENT_TYPE_FLOAT64_KHR:    return "FP64";
                        case VK_COMPONENT_TYPE_SINT8_KHR:      return "INT8";
                        case VK_COMPONENT_TYPE_SINT16_KHR:     return "INT16";
                        case VK_COMPONENT_TYPE_SINT32_KHR:     return "INT32";
                        case VK_COMPONENT_TYPE_UINT8_KHR:      return "UINT8";
                        case VK_COMPONENT_TYPE_UINT16_KHR:     return "UINT16";
                        case VK_COMPONENT_TYPE_UINT32_KHR:     return "UINT32";
                        case (VkComponentTypeKHR)1000141000:    return "BF16";       // VK_COMPONENT_TYPE_BFLOAT16_KHR
                        case (VkComponentTypeKHR)1000491002:    return "FP8e4m3";    // VK_COMPONENT_TYPE_FLOAT8_E4M3_EXT
                        case (VkComponentTypeKHR)1000491003:    return "FP8e5m2";    // VK_COMPONENT_TYPE_FLOAT8_E5M2_EXT
                        default: {
                            static char buf[32];
                            snprintf(buf, sizeof(buf), "?(%d)", (int)t);
                            return buf;
                        }
                    }
                };
                printf("  %ux%ux%u  A=%s B=%s C=%s Result=%s  scope=%s\n",
                       c.MSize, c.NSize, c.KSize,
                       type_str(c.AType), type_str(c.BType),
                       type_str(c.CType), type_str(c.ResultType),
                       c.scope == VK_SCOPE_SUBGROUP_KHR ? "subgroup" : "other");
                shown++;
            }
        }
    } else {
        printf("\n=== Cooperative Matrix: vkGetPhysicalDeviceCooperativeMatrixPropertiesKHR not available ===\n");
    }

    printf("\n╔══════════════════════════════════════════════════════╗\n");
    printf("║  Probe complete. All vectors mapped.                ║\n");
    printf("╚══════════════════════════════════════════════════════╝\n");

    vkDestroyInstance(instance, nullptr);
    return 0;
}
