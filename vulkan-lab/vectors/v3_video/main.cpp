// vulkan-lab/vectors/v3_video/main.cpp
// ────────────────────────────────────────────────────────────
// Vector 3: AV1 Video Decode — Session Initialization Probe
// Queries RTX 4090 AV1 decode capabilities on Q3, creates a
// VkVideoSessionKHR, binds session memory, verifies pipeline.
// No bitstream required — this proves the decode path is alive.
// ────────────────────────────────────────────────────────────

#include <vulkan/vulkan.h>

#include <cstdint>
#include <cstdio>
#include <cstring>
#include <vector>

#define VK_CHECK(call)                                                 \
    do {                                                               \
        VkResult r = (call);                                           \
        if (r != VK_SUCCESS) {                                         \
            fprintf(stderr, "FATAL [%d]: %s\n", (int)r, #call);       \
            return 1;                                                  \
        }                                                              \
    } while (0)

// ── AV1 Level → string ────────────────────────────────────
static const char* av1_level_str(int level) {
    // StdVideoAV1Level: 0=2.0, 1=2.1, ..., 23=7.3
    static const char* names[] = {
        "2.0","2.1","2.2","2.3",
        "3.0","3.1","3.2","3.3",
        "4.0","4.1","4.2","4.3",
        "5.0","5.1","5.2","5.3",
        "6.0","6.1","6.2","6.3",
        "7.0","7.1","7.2","7.3",
    };
    if (level >= 0 && level < 24) return names[level];
    return "UNKNOWN";
}

// ── VkFormat → string (common video formats) ──────────────
static const char* format_str(VkFormat fmt) {
    switch (fmt) {
        case VK_FORMAT_G8_B8R8_2PLANE_420_UNORM:    return "NV12 (G8_B8R8_2PLANE_420)";
        case VK_FORMAT_G8_B8_R8_3PLANE_420_UNORM:   return "I420 (G8_B8_R8_3PLANE_420)";
        case VK_FORMAT_G10X6_B10X6R10X6_2PLANE_420_UNORM_3PACK16:
            return "P010 (10-bit 2PLANE_420)";
        case VK_FORMAT_G10X6_B10X6_R10X6_3PLANE_420_UNORM_3PACK16:
            return "I010 (10-bit 3PLANE_420)";
        case VK_FORMAT_G8_B8R8_2PLANE_422_UNORM:    return "NV16 (G8_B8R8_2PLANE_422)";
        case VK_FORMAT_G8_B8_R8_3PLANE_422_UNORM:   return "I422 (3PLANE_422)";
        case VK_FORMAT_G8_B8R8_2PLANE_444_UNORM:    return "NV24 (2PLANE_444)";
        default: break;
    }
    static char buf[32];
    snprintf(buf, sizeof(buf), "VkFormat(%d)", (int)fmt);
    return buf;
}

int main() {
    printf("╔══════════════════════════════════════════════════════╗\n");
    printf("║  Vector 3: AV1 Video Decode — Session Init Probe    ║\n");
    printf("║  VK_KHR_video_decode_av1 on Q3 (dedicated decode)   ║\n");
    printf("╚══════════════════════════════════════════════════════╝\n\n");

    // ── Instance ───────────────────────────────────────────
    VkApplicationInfo app_info{};
    app_info.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO;
    app_info.pApplicationName = "v3-av1-decode";
    app_info.apiVersion = VK_API_VERSION_1_3;

    VkInstanceCreateInfo inst_ci{};
    inst_ci.sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;
    inst_ci.pApplicationInfo = &app_info;

    VkInstance instance;
    VK_CHECK(vkCreateInstance(&inst_ci, nullptr, &instance));

    // ── Load video extension function pointers ─────────────
    // Video KHR functions are not exported by vulkan-1.lib
    auto pfn_GetVideoCapabilities = (PFN_vkGetPhysicalDeviceVideoCapabilitiesKHR)
        vkGetInstanceProcAddr(instance, "vkGetPhysicalDeviceVideoCapabilitiesKHR");
    auto pfn_GetVideoFormats = (PFN_vkGetPhysicalDeviceVideoFormatPropertiesKHR)
        vkGetInstanceProcAddr(instance, "vkGetPhysicalDeviceVideoFormatPropertiesKHR");

    if (!pfn_GetVideoCapabilities || !pfn_GetVideoFormats) {
        fprintf(stderr, "Failed to load video instance functions.\n");
        vkDestroyInstance(instance, nullptr);
        return 1;
    }

    // ── Physical device (discrete GPU) ─────────────────────
    uint32_t dev_count = 0;
    VK_CHECK(vkEnumeratePhysicalDevices(instance, &dev_count, nullptr));
    std::vector<VkPhysicalDevice> devs(dev_count);
    VK_CHECK(vkEnumeratePhysicalDevices(instance, &dev_count, devs.data()));

    VkPhysicalDevice gpu = devs[0];
    VkPhysicalDeviceProperties gpu_props;
    for (auto& d : devs) {
        vkGetPhysicalDeviceProperties(d, &gpu_props);
        if (gpu_props.deviceType == VK_PHYSICAL_DEVICE_TYPE_DISCRETE_GPU) {
            gpu = d;
            break;
        }
    }
    vkGetPhysicalDeviceProperties(gpu, &gpu_props);
    printf("Device: %s\n\n", gpu_props.deviceName);

    // ── Find VIDEO_DECODE queue family ─────────────────────
    uint32_t qf_count = 0;
    vkGetPhysicalDeviceQueueFamilyProperties(gpu, &qf_count, nullptr);
    std::vector<VkQueueFamilyProperties> qf_props(qf_count);
    vkGetPhysicalDeviceQueueFamilyProperties(gpu, &qf_count, qf_props.data());

    uint32_t video_qf = UINT32_MAX;
    for (uint32_t i = 0; i < qf_count; i++) {
        if (qf_props[i].queueFlags & VK_QUEUE_VIDEO_DECODE_BIT_KHR) {
            video_qf = i;
            break;
        }
    }
    if (video_qf == UINT32_MAX) {
        fprintf(stderr, "No VIDEO_DECODE queue family found.\n");
        vkDestroyInstance(instance, nullptr);
        return 1;
    }
    printf("=== Queue Family %u ===\n", video_qf);
    printf("  Queues: %u\n", qf_props[video_qf].queueCount);
    printf("  Flags :");
    if (qf_props[video_qf].queueFlags & VK_QUEUE_VIDEO_DECODE_BIT_KHR) printf(" VIDEO_DECODE");
    if (qf_props[video_qf].queueFlags & VK_QUEUE_TRANSFER_BIT)         printf(" TRANSFER");
    if (qf_props[video_qf].queueFlags & VK_QUEUE_SPARSE_BINDING_BIT)   printf(" SPARSE");
    printf("\n");

    // Query codec operations supported by this queue family
    std::vector<VkQueueFamilyProperties2> qf2_all(qf_count);
    std::vector<VkQueueFamilyVideoPropertiesKHR> qf_video_all(qf_count);
    for (uint32_t i = 0; i < qf_count; i++) {
        qf_video_all[i] = {};
        qf_video_all[i].sType = VK_STRUCTURE_TYPE_QUEUE_FAMILY_VIDEO_PROPERTIES_KHR;
        qf2_all[i] = {};
        qf2_all[i].sType = VK_STRUCTURE_TYPE_QUEUE_FAMILY_PROPERTIES_2;
        qf2_all[i].pNext = &qf_video_all[i];
    }
    vkGetPhysicalDeviceQueueFamilyProperties2(gpu, &qf_count, qf2_all.data());

    auto video_ops = qf_video_all[video_qf].videoCodecOperations;
    printf("  Codecs:");
    if (video_ops & VK_VIDEO_CODEC_OPERATION_DECODE_H264_BIT_KHR) printf(" H264");
    if (video_ops & VK_VIDEO_CODEC_OPERATION_DECODE_H265_BIT_KHR) printf(" H265");
    if (video_ops & VK_VIDEO_CODEC_OPERATION_DECODE_AV1_BIT_KHR)  printf(" AV1");
    printf("\n");

    if (!(video_ops & VK_VIDEO_CODEC_OPERATION_DECODE_AV1_BIT_KHR)) {
        fprintf(stderr, "Queue family %u does not support AV1 decode.\n", video_qf);
        vkDestroyInstance(instance, nullptr);
        return 1;
    }

    // ── AV1 Profile (Main, 8-bit, 4:2:0) ──────────────────
    printf("\n=== AV1 Profile ===\n");
    printf("  Profile: Main\n");
    printf("  Luma   : 8-bit\n");
    printf("  Chroma : 4:2:0 (8-bit)\n");

    VkVideoDecodeAV1ProfileInfoKHR av1_profile{};
    av1_profile.sType = VK_STRUCTURE_TYPE_VIDEO_DECODE_AV1_PROFILE_INFO_KHR;
    av1_profile.stdProfile = STD_VIDEO_AV1_PROFILE_MAIN;

    VkVideoProfileInfoKHR video_profile{};
    video_profile.sType = VK_STRUCTURE_TYPE_VIDEO_PROFILE_INFO_KHR;
    video_profile.pNext = &av1_profile;
    video_profile.videoCodecOperation = VK_VIDEO_CODEC_OPERATION_DECODE_AV1_BIT_KHR;
    video_profile.lumaBitDepth   = VK_VIDEO_COMPONENT_BIT_DEPTH_8_BIT_KHR;
    video_profile.chromaSubsampling = VK_VIDEO_CHROMA_SUBSAMPLING_420_BIT_KHR;
    video_profile.chromaBitDepth = VK_VIDEO_COMPONENT_BIT_DEPTH_8_BIT_KHR;

    // ── Query AV1 Capabilities ─────────────────────────────
    VkVideoDecodeAV1CapabilitiesKHR av1_caps{};
    av1_caps.sType = VK_STRUCTURE_TYPE_VIDEO_DECODE_AV1_CAPABILITIES_KHR;

    VkVideoDecodeCapabilitiesKHR decode_caps{};
    decode_caps.sType = VK_STRUCTURE_TYPE_VIDEO_DECODE_CAPABILITIES_KHR;
    decode_caps.pNext = &av1_caps;

    VkVideoCapabilitiesKHR video_caps{};
    video_caps.sType = VK_STRUCTURE_TYPE_VIDEO_CAPABILITIES_KHR;
    video_caps.pNext = &decode_caps;

    VK_CHECK(pfn_GetVideoCapabilities(gpu, &video_profile, &video_caps));

    printf("\n=== AV1 Decode Capabilities ===\n");
    printf("  Max AV1 Level  : %s\n", av1_level_str((int)av1_caps.maxLevel));
    printf("  Min resolution : %ux%u\n",
           video_caps.minCodedExtent.width, video_caps.minCodedExtent.height);
    printf("  Max resolution : %ux%u\n",
           video_caps.maxCodedExtent.width, video_caps.maxCodedExtent.height);
    printf("  DPB slots (max): %u\n", video_caps.maxDpbSlots);
    printf("  Active refs    : %u\n", video_caps.maxActiveReferencePictures);
    printf("  BS buf align   : offset=%llu  size=%llu\n",
           (unsigned long long)video_caps.minBitstreamBufferOffsetAlignment,
           (unsigned long long)video_caps.minBitstreamBufferSizeAlignment);
    printf("  Picture granul : %ux%u\n",
           video_caps.pictureAccessGranularity.width,
           video_caps.pictureAccessGranularity.height);
    printf("  Std header     : %s (v%u.%u.%u)\n",
           video_caps.stdHeaderVersion.extensionName,
           VK_VERSION_MAJOR(video_caps.stdHeaderVersion.specVersion),
           VK_VERSION_MINOR(video_caps.stdHeaderVersion.specVersion),
           VK_VERSION_PATCH(video_caps.stdHeaderVersion.specVersion));

    // Decode capability flags
    printf("  DPB mode       :");
    if (decode_caps.flags & VK_VIDEO_DECODE_CAPABILITY_DPB_AND_OUTPUT_COINCIDE_BIT_KHR)
        printf(" COINCIDENT");
    if (decode_caps.flags & VK_VIDEO_DECODE_CAPABILITY_DPB_AND_OUTPUT_DISTINCT_BIT_KHR)
        printf(" DISTINCT");
    printf("\n");

    // ── Query Supported Formats ────────────────────────────
    VkVideoProfileListInfoKHR profile_list{};
    profile_list.sType = VK_STRUCTURE_TYPE_VIDEO_PROFILE_LIST_INFO_KHR;
    profile_list.profileCount = 1;
    profile_list.pProfiles = &video_profile;

    // Decode output formats
    VkPhysicalDeviceVideoFormatInfoKHR fmt_info{};
    fmt_info.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VIDEO_FORMAT_INFO_KHR;
    fmt_info.pNext = &profile_list;
    fmt_info.imageUsage = VK_IMAGE_USAGE_VIDEO_DECODE_DST_BIT_KHR;

    uint32_t fmt_count = 0;
    VK_CHECK(pfn_GetVideoFormats(gpu, &fmt_info, &fmt_count, nullptr));
    std::vector<VkVideoFormatPropertiesKHR> fmts(fmt_count);
    for (auto& f : fmts) {
        f = {};
        f.sType = VK_STRUCTURE_TYPE_VIDEO_FORMAT_PROPERTIES_KHR;
    }
    VK_CHECK(pfn_GetVideoFormats(gpu, &fmt_info, &fmt_count, fmts.data()));

    printf("\n=== Decode Output Formats (%u) ===\n", fmt_count);
    VkFormat output_format = VK_FORMAT_UNDEFINED;
    for (uint32_t i = 0; i < fmt_count; i++) {
        printf("  [%u] %s\n", i, format_str(fmts[i].format));
        if (output_format == VK_FORMAT_UNDEFINED)
            output_format = fmts[i].format;
    }

    // DPB (reference picture) formats
    fmt_info.imageUsage = VK_IMAGE_USAGE_VIDEO_DECODE_DPB_BIT_KHR;
    uint32_t dpb_fmt_count = 0;
    VK_CHECK(pfn_GetVideoFormats(gpu, &fmt_info, &dpb_fmt_count, nullptr));
    std::vector<VkVideoFormatPropertiesKHR> dpb_fmts(dpb_fmt_count);
    for (auto& f : dpb_fmts) {
        f = {};
        f.sType = VK_STRUCTURE_TYPE_VIDEO_FORMAT_PROPERTIES_KHR;
    }
    VK_CHECK(pfn_GetVideoFormats(gpu, &fmt_info, &dpb_fmt_count, dpb_fmts.data()));

    printf("\n=== DPB Reference Formats (%u) ===\n", dpb_fmt_count);
    VkFormat dpb_format = VK_FORMAT_UNDEFINED;
    for (uint32_t i = 0; i < dpb_fmt_count; i++) {
        printf("  [%u] %s\n", i, format_str(dpb_fmts[i].format));
        if (dpb_format == VK_FORMAT_UNDEFINED)
            dpb_format = dpb_fmts[i].format;
    }

    if (output_format == VK_FORMAT_UNDEFINED) {
        fprintf(stderr, "No decode output format found.\n");
        vkDestroyInstance(instance, nullptr);
        return 1;
    }
    VkFormat ref_format = (dpb_format != VK_FORMAT_UNDEFINED) ? dpb_format : output_format;
    printf("\n  Selected output: %s\n", format_str(output_format));
    printf("  Selected DPB   : %s\n", format_str(ref_format));

    // ── Create Logical Device with Video Queue ─────────────
    float queue_pri = 1.0f;
    VkDeviceQueueCreateInfo q_ci{};
    q_ci.sType = VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO;
    q_ci.queueFamilyIndex = video_qf;
    q_ci.queueCount = 1;
    q_ci.pQueuePriorities = &queue_pri;

    const char* dev_exts[] = {
        VK_KHR_VIDEO_QUEUE_EXTENSION_NAME,
        VK_KHR_VIDEO_DECODE_QUEUE_EXTENSION_NAME,
        VK_KHR_VIDEO_DECODE_AV1_EXTENSION_NAME,
    };

    VkDeviceCreateInfo dev_ci{};
    dev_ci.sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO;
    dev_ci.queueCreateInfoCount = 1;
    dev_ci.pQueueCreateInfos = &q_ci;
    dev_ci.enabledExtensionCount = sizeof(dev_exts) / sizeof(dev_exts[0]);
    dev_ci.ppEnabledExtensionNames = dev_exts;

    VkDevice device;
    VK_CHECK(vkCreateDevice(gpu, &dev_ci, nullptr, &device));

    VkQueue video_queue;
    vkGetDeviceQueue(device, video_qf, 0, &video_queue);
    printf("\nDevice created. Video decode queue acquired (Q%u).\n", video_qf);

    // Load device-level video function pointers
    auto pfn_CreateVideoSession = (PFN_vkCreateVideoSessionKHR)
        vkGetDeviceProcAddr(device, "vkCreateVideoSessionKHR");
    auto pfn_DestroyVideoSession = (PFN_vkDestroyVideoSessionKHR)
        vkGetDeviceProcAddr(device, "vkDestroyVideoSessionKHR");
    auto pfn_GetSessionMemReqs = (PFN_vkGetVideoSessionMemoryRequirementsKHR)
        vkGetDeviceProcAddr(device, "vkGetVideoSessionMemoryRequirementsKHR");
    auto pfn_BindSessionMem = (PFN_vkBindVideoSessionMemoryKHR)
        vkGetDeviceProcAddr(device, "vkBindVideoSessionMemoryKHR");

    if (!pfn_CreateVideoSession || !pfn_DestroyVideoSession ||
        !pfn_GetSessionMemReqs || !pfn_BindSessionMem) {
        fprintf(stderr, "Failed to load video device functions.\n");
        vkDestroyDevice(device, nullptr);
        vkDestroyInstance(instance, nullptr);
        return 1;
    }

    // ── Create Video Session (1080p AV1 Main) ──────────────
    VkExtent2D target_extent = {1920, 1080};

    // Clamp to device limits
    if (target_extent.width > video_caps.maxCodedExtent.width)
        target_extent.width = video_caps.maxCodedExtent.width;
    if (target_extent.height > video_caps.maxCodedExtent.height)
        target_extent.height = video_caps.maxCodedExtent.height;

    // AV1: up to 8 DPB slots (7 references + 1 current), 7 active refs
    uint32_t dpb_slots  = (video_caps.maxDpbSlots > 8) ? 8 : video_caps.maxDpbSlots;
    uint32_t active_refs = (video_caps.maxActiveReferencePictures > 7)
                           ? 7 : video_caps.maxActiveReferencePictures;

    VkVideoSessionCreateInfoKHR session_ci{};
    session_ci.sType = VK_STRUCTURE_TYPE_VIDEO_SESSION_CREATE_INFO_KHR;
    session_ci.queueFamilyIndex = video_qf;
    session_ci.pVideoProfile = &video_profile;
    session_ci.pictureFormat = output_format;
    session_ci.maxCodedExtent = target_extent;
    session_ci.referencePictureFormat = ref_format;
    session_ci.maxDpbSlots = dpb_slots;
    session_ci.maxActiveReferencePictures = active_refs;
    session_ci.pStdHeaderVersion = &video_caps.stdHeaderVersion;

    VkVideoSessionKHR video_session;
    VK_CHECK(pfn_CreateVideoSession(device, &session_ci, nullptr, &video_session));
    printf("Video session created (%ux%u, %u DPB slots, %u active refs)\n",
           target_extent.width, target_extent.height, dpb_slots, active_refs);

    // ── Bind Session Memory ────────────────────────────────
    uint32_t mem_req_count = 0;
    VK_CHECK(pfn_GetSessionMemReqs(
        device, video_session, &mem_req_count, nullptr));

    std::vector<VkVideoSessionMemoryRequirementsKHR> mem_reqs(mem_req_count);
    for (auto& m : mem_reqs) {
        m = {};
        m.sType = VK_STRUCTURE_TYPE_VIDEO_SESSION_MEMORY_REQUIREMENTS_KHR;
    }
    VK_CHECK(pfn_GetSessionMemReqs(
        device, video_session, &mem_req_count, mem_reqs.data()));

    printf("\n=== Session Memory (%u bindings) ===\n", mem_req_count);

    VkPhysicalDeviceMemoryProperties mem_props;
    vkGetPhysicalDeviceMemoryProperties(gpu, &mem_props);

    auto find_mem_type = [&](uint32_t type_bits, VkMemoryPropertyFlags flags) -> uint32_t {
        for (uint32_t i = 0; i < mem_props.memoryTypeCount; i++) {
            if ((type_bits & (1 << i)) &&
                (mem_props.memoryTypes[i].propertyFlags & flags) == flags)
                return i;
        }
        // Fallback: any matching type bit
        for (uint32_t i = 0; i < mem_props.memoryTypeCount; i++) {
            if (type_bits & (1 << i)) return i;
        }
        return UINT32_MAX;
    };

    std::vector<VkDeviceMemory> session_mems(mem_req_count);
    std::vector<VkBindVideoSessionMemoryInfoKHR> bind_infos(mem_req_count);
    VkDeviceSize total_mem = 0;

    for (uint32_t i = 0; i < mem_req_count; i++) {
        auto& req = mem_reqs[i].memoryRequirements;
        printf("  [%u] bind=%u  size=%llu  align=%llu  types=0x%X\n",
               i, mem_reqs[i].memoryBindIndex,
               (unsigned long long)req.size,
               (unsigned long long)req.alignment,
               req.memoryTypeBits);
        total_mem += req.size;

        VkMemoryAllocateInfo ai{};
        ai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
        ai.allocationSize = req.size;
        ai.memoryTypeIndex = find_mem_type(
            req.memoryTypeBits, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);

        VK_CHECK(vkAllocateMemory(device, &ai, nullptr, &session_mems[i]));

        bind_infos[i] = {};
        bind_infos[i].sType = VK_STRUCTURE_TYPE_BIND_VIDEO_SESSION_MEMORY_INFO_KHR;
        bind_infos[i].memoryBindIndex = mem_reqs[i].memoryBindIndex;
        bind_infos[i].memory = session_mems[i];
        bind_infos[i].memoryOffset = 0;
        bind_infos[i].memorySize = req.size;
    }

    VK_CHECK(pfn_BindSessionMem(
        device, video_session, mem_req_count, bind_infos.data()));
    printf("  Total: %llu bytes (%.2f MB) bound to session\n",
           (unsigned long long)total_mem, (double)total_mem / (1024.0 * 1024.0));

    printf("\n  >>> AV1 VIDEO SESSION READY — decode pipeline initialized <<<\n");

    // ── Cleanup ────────────────────────────────────────────
    pfn_DestroyVideoSession(device, video_session, nullptr);
    for (auto& m : session_mems) vkFreeMemory(device, m, nullptr);
    vkDestroyDevice(device, nullptr);
    vkDestroyInstance(instance, nullptr);

    printf("\n╔══════════════════════════════════════════════════════╗\n");
    printf("║  Vector 3 probe complete — AV1 session verified.    ║\n");
    printf("╚══════════════════════════════════════════════════════╝\n");
    return 0;
}
