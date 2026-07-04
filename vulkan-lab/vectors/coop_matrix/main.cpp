// vulkan-lab/vectors/coop_matrix/main.cpp
// ────────────────────────────────────────────────────────────
// Vector 2: Cooperative Matrix — Tensor-core GEMM via Vulkan
// Dispatches a 16x16x16 FP16→FP32 matmul on the RTX 4090's
// async compute queue (Q2). Verifies result on CPU.
// ────────────────────────────────────────────────────────────

#include <vulkan/vulkan.h>

#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <vector>

// FP16 helper — IEEE 754 half-precision
static uint16_t fp32_to_fp16(float v) {
    uint32_t f;
    memcpy(&f, &v, 4);
    uint32_t sign = (f >> 16) & 0x8000;
    int32_t  exp  = ((f >> 23) & 0xFF) - 127 + 15;
    uint32_t mant = (f >> 13) & 0x3FF;
    if (exp <= 0)      return (uint16_t)(sign);          // flush to zero
    if (exp >= 0x1F)   return (uint16_t)(sign | 0x7C00); // inf
    return (uint16_t)(sign | (exp << 10) | mant);
}

#define VK_CHECK(call)                                                 \
    do {                                                               \
        VkResult r = (call);                                           \
        if (r != VK_SUCCESS) {                                         \
            fprintf(stderr, "FATAL [%d]: %s\n", (int)r, #call);       \
            return 1;                                                  \
        }                                                              \
    } while (0)

// ── SPIR-V loader ──────────────────────────────────────────
static std::vector<uint32_t> load_spirv(const char* path) {
    std::ifstream f(path, std::ios::binary | std::ios::ate);
    if (!f.is_open()) {
        fprintf(stderr, "Cannot open SPIR-V: %s\n", path);
        return {};
    }
    size_t sz = f.tellg();
    f.seekg(0);
    std::vector<uint32_t> code(sz / 4);
    f.read(reinterpret_cast<char*>(code.data()), sz);
    return code;
}

// ── Constants ──────────────────────────────────────────────
constexpr uint32_t M = 16, N = 16, K = 16;
constexpr float    A_VAL = 2.0f;
constexpr float    B_VAL = 3.0f;
constexpr float    EXPECTED = A_VAL * B_VAL * K; // 2*3*16 = 96

int main(int argc, char** argv) {
    printf("╔══════════════════════════════════════════════════════╗\n");
    printf("║  Vector 2: Cooperative Matrix — Tensor-Core GEMM    ║\n");
    printf("║  16x16x16 FP16→FP32 on async compute queue          ║\n");
    printf("╚══════════════════════════════════════════════════════╝\n\n");

    // Default shader path — next to executable or passed as arg
    const char* spirv_path = (argc > 1) ? argv[1] : "coop_matmul.comp.spv";

    // ── Instance ───────────────────────────────────────────
    VkApplicationInfo app_info{};
    app_info.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO;
    app_info.pApplicationName = "coop-matrix-gemm";
    app_info.apiVersion = VK_API_VERSION_1_3;

    VkInstanceCreateInfo inst_ci{};
    inst_ci.sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;
    inst_ci.pApplicationInfo = &app_info;

    VkInstance instance;
    VK_CHECK(vkCreateInstance(&inst_ci, nullptr, &instance));

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
    printf("Device: %s\n", gpu_props.deviceName);

    // ── Find async compute queue family (compute+transfer, no graphics)
    uint32_t qf_count = 0;
    vkGetPhysicalDeviceQueueFamilyProperties(gpu, &qf_count, nullptr);
    std::vector<VkQueueFamilyProperties> qf_props(qf_count);
    vkGetPhysicalDeviceQueueFamilyProperties(gpu, &qf_count, qf_props.data());

    uint32_t compute_qf = UINT32_MAX;
    for (uint32_t i = 0; i < qf_count; i++) {
        auto flags = qf_props[i].queueFlags;
        if ((flags & VK_QUEUE_COMPUTE_BIT) && !(flags & VK_QUEUE_GRAPHICS_BIT)) {
            compute_qf = i;
            break;
        }
    }
    if (compute_qf == UINT32_MAX) {
        // Fallback to first queue with compute
        for (uint32_t i = 0; i < qf_count; i++) {
            if (qf_props[i].queueFlags & VK_QUEUE_COMPUTE_BIT) {
                compute_qf = i;
                break;
            }
        }
    }
    printf("Using queue family %u (async compute, %u queues)\n",
           compute_qf, qf_props[compute_qf].queueCount);

    // ── Logical device ─────────────────────────────────────
    float queue_pri = 1.0f;
    VkDeviceQueueCreateInfo q_ci{};
    q_ci.sType = VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO;
    q_ci.queueFamilyIndex = compute_qf;
    q_ci.queueCount = 1;
    q_ci.pQueuePriorities = &queue_pri;

    // Required extensions
    const char* dev_exts[] = {
        VK_KHR_COOPERATIVE_MATRIX_EXTENSION_NAME,
        VK_KHR_SHADER_FLOAT16_INT8_EXTENSION_NAME,
        VK_KHR_16BIT_STORAGE_EXTENSION_NAME,
        VK_KHR_VULKAN_MEMORY_MODEL_EXTENSION_NAME,
    };

    // Feature chain: cooperative matrix + FP16 + 16-bit storage
    VkPhysicalDevice16BitStorageFeatures f_16bit{};
    f_16bit.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_16BIT_STORAGE_FEATURES;
    f_16bit.storageBuffer16BitAccess = VK_TRUE;

    VkPhysicalDeviceShaderFloat16Int8Features f_fp16{};
    f_fp16.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_FLOAT16_INT8_FEATURES;
    f_fp16.shaderFloat16 = VK_TRUE;
    f_fp16.pNext = &f_16bit;

    VkPhysicalDeviceVulkanMemoryModelFeatures f_mem_model{};
    f_mem_model.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_MEMORY_MODEL_FEATURES;
    f_mem_model.vulkanMemoryModel = VK_TRUE;
    f_mem_model.pNext = &f_fp16;

    VkPhysicalDeviceCooperativeMatrixFeaturesKHR f_coop{};
    f_coop.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_COOPERATIVE_MATRIX_FEATURES_KHR;
    f_coop.cooperativeMatrix = VK_TRUE;
    f_coop.pNext = &f_mem_model;

    VkPhysicalDeviceFeatures2 features2{};
    features2.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FEATURES_2;
    features2.pNext = &f_coop;

    VkDeviceCreateInfo dev_ci{};
    dev_ci.sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO;
    dev_ci.queueCreateInfoCount = 1;
    dev_ci.pQueueCreateInfos = &q_ci;
    dev_ci.enabledExtensionCount = sizeof(dev_exts) / sizeof(dev_exts[0]);
    dev_ci.ppEnabledExtensionNames = dev_exts;
    dev_ci.pNext = &features2;

    VkDevice device;
    VK_CHECK(vkCreateDevice(gpu, &dev_ci, nullptr, &device));

    VkQueue compute_queue;
    vkGetDeviceQueue(device, compute_qf, 0, &compute_queue);
    printf("Device created. Cooperative matrix enabled.\n");

    // ── Memory helpers ─────────────────────────────────────
    auto find_mem_type = [&](uint32_t type_bits, VkMemoryPropertyFlags props) -> uint32_t {
        VkPhysicalDeviceMemoryProperties mem_props;
        vkGetPhysicalDeviceMemoryProperties(gpu, &mem_props);
        for (uint32_t i = 0; i < mem_props.memoryTypeCount; i++) {
            if ((type_bits & (1 << i)) &&
                (mem_props.memoryTypes[i].propertyFlags & props) == props)
                return i;
        }
        return UINT32_MAX;
    };

    // Create buffer + allocate host-visible memory
    struct BufMem { VkBuffer buf; VkDeviceMemory mem; VkDeviceSize size; };
    auto create_buffer = [&](VkDeviceSize size, VkBufferUsageFlags usage) -> BufMem {
        BufMem bm{};
        bm.size = size;

        VkBufferCreateInfo bi{};
        bi.sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
        bi.size = size;
        bi.usage = usage;
        bi.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
        vkCreateBuffer(device, &bi, nullptr, &bm.buf);

        VkMemoryRequirements req;
        vkGetBufferMemoryRequirements(device, bm.buf, &req);

        VkMemoryAllocateInfo ai{};
        ai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
        ai.allocationSize = req.size;
        ai.memoryTypeIndex = find_mem_type(req.memoryTypeBits,
            VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
        vkAllocateMemory(device, &ai, nullptr, &bm.mem);
        vkBindBufferMemory(device, bm.buf, bm.mem, 0);
        return bm;
    };

    // ── Buffers: A(FP16), B(FP16), C(FP32) ────────────────
    VkDeviceSize a_size = M * K * sizeof(uint16_t);  // 16*16*2 = 512 bytes
    VkDeviceSize b_size = K * N * sizeof(uint16_t);
    VkDeviceSize c_size = M * N * sizeof(float);     // 16*16*4 = 1024 bytes

    auto buf_a = create_buffer(a_size, VK_BUFFER_USAGE_STORAGE_BUFFER_BIT);
    auto buf_b = create_buffer(b_size, VK_BUFFER_USAGE_STORAGE_BUFFER_BIT);
    auto buf_c = create_buffer(c_size, VK_BUFFER_USAGE_STORAGE_BUFFER_BIT);

    // Fill A with 2.0f16, B with 3.0f16, C with 0
    {
        uint16_t* pa;
        vkMapMemory(device, buf_a.mem, 0, a_size, 0, (void**)&pa);
        uint16_t h2 = fp32_to_fp16(A_VAL);
        for (uint32_t i = 0; i < M * K; i++) pa[i] = h2;
        vkUnmapMemory(device, buf_a.mem);

        uint16_t* pb;
        vkMapMemory(device, buf_b.mem, 0, b_size, 0, (void**)&pb);
        uint16_t h3 = fp32_to_fp16(B_VAL);
        for (uint32_t i = 0; i < K * N; i++) pb[i] = h3;
        vkUnmapMemory(device, buf_b.mem);

        float* pc;
        vkMapMemory(device, buf_c.mem, 0, c_size, 0, (void**)&pc);
        memset(pc, 0, c_size);
        vkUnmapMemory(device, buf_c.mem);
    }
    printf("Buffers: A[16x16]=%.0f B[16x16]=%.0f C[16x16]=0  (expect %.0f)\n",
           A_VAL, B_VAL, EXPECTED);

    // ── Descriptor set layout + pool + set ─────────────────
    VkDescriptorSetLayoutBinding bindings[3]{};
    for (int i = 0; i < 3; i++) {
        bindings[i].binding = i;
        bindings[i].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
        bindings[i].descriptorCount = 1;
        bindings[i].stageFlags = VK_SHADER_STAGE_COMPUTE_BIT;
    }

    VkDescriptorSetLayoutCreateInfo dsl_ci{};
    dsl_ci.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO;
    dsl_ci.bindingCount = 3;
    dsl_ci.pBindings = bindings;

    VkDescriptorSetLayout dsl;
    VK_CHECK(vkCreateDescriptorSetLayout(device, &dsl_ci, nullptr, &dsl));

    VkDescriptorPoolSize pool_size{VK_DESCRIPTOR_TYPE_STORAGE_BUFFER, 3};
    VkDescriptorPoolCreateInfo dp_ci{};
    dp_ci.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;
    dp_ci.maxSets = 1;
    dp_ci.poolSizeCount = 1;
    dp_ci.pPoolSizes = &pool_size;

    VkDescriptorPool dpool;
    VK_CHECK(vkCreateDescriptorPool(device, &dp_ci, nullptr, &dpool));

    VkDescriptorSetAllocateInfo ds_ai{};
    ds_ai.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
    ds_ai.descriptorPool = dpool;
    ds_ai.descriptorSetCount = 1;
    ds_ai.pSetLayouts = &dsl;

    VkDescriptorSet dset;
    VK_CHECK(vkAllocateDescriptorSets(device, &ds_ai, &dset));

    // Update descriptors
    VkDescriptorBufferInfo buf_infos[3] = {
        {buf_a.buf, 0, a_size},
        {buf_b.buf, 0, b_size},
        {buf_c.buf, 0, c_size},
    };
    VkWriteDescriptorSet writes[3]{};
    for (int i = 0; i < 3; i++) {
        writes[i].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
        writes[i].dstSet = dset;
        writes[i].dstBinding = i;
        writes[i].descriptorCount = 1;
        writes[i].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
        writes[i].pBufferInfo = &buf_infos[i];
    }
    vkUpdateDescriptorSets(device, 3, writes, 0, nullptr);

    // ── Compute pipeline ───────────────────────────────────
    auto spirv = load_spirv(spirv_path);
    if (spirv.empty()) return 1;

    VkShaderModuleCreateInfo sm_ci{};
    sm_ci.sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;
    sm_ci.codeSize = spirv.size() * 4;
    sm_ci.pCode = spirv.data();

    VkShaderModule shader;
    VK_CHECK(vkCreateShaderModule(device, &sm_ci, nullptr, &shader));

    VkPipelineLayoutCreateInfo pl_ci{};
    pl_ci.sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;
    pl_ci.setLayoutCount = 1;
    pl_ci.pSetLayouts = &dsl;

    VkPipelineLayout pipe_layout;
    VK_CHECK(vkCreatePipelineLayout(device, &pl_ci, nullptr, &pipe_layout));

    VkComputePipelineCreateInfo cp_ci{};
    cp_ci.sType = VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO;
    cp_ci.stage.sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    cp_ci.stage.stage = VK_SHADER_STAGE_COMPUTE_BIT;
    cp_ci.stage.module = shader;
    cp_ci.stage.pName = "main";
    cp_ci.layout = pipe_layout;

    VkPipeline pipeline;
    VK_CHECK(vkCreateComputePipelines(device, VK_NULL_HANDLE, 1, &cp_ci, nullptr, &pipeline));
    printf("Pipeline created from %s\n", spirv_path);

    // ── Command buffer ─────────────────────────────────────
    VkCommandPoolCreateInfo cp_pool_ci{};
    cp_pool_ci.sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO;
    cp_pool_ci.queueFamilyIndex = compute_qf;

    VkCommandPool cmd_pool;
    VK_CHECK(vkCreateCommandPool(device, &cp_pool_ci, nullptr, &cmd_pool));

    // ── Timestamp query pool ───────────────────────────────
    VkQueryPoolCreateInfo qp_ci{};
    qp_ci.sType = VK_STRUCTURE_TYPE_QUERY_POOL_CREATE_INFO;
    qp_ci.queryType = VK_QUERY_TYPE_TIMESTAMP;
    qp_ci.queryCount = 2;
    VkQueryPool query_pool;
    VK_CHECK(vkCreateQueryPool(device, &qp_ci, nullptr, &query_pool));

    VkCommandBufferAllocateInfo cb_ai{};
    cb_ai.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO;
    cb_ai.commandPool = cmd_pool;
    cb_ai.level = VK_COMMAND_BUFFER_LEVEL_PRIMARY;
    cb_ai.commandBufferCount = 1;

    VkCommandBuffer cmd;
    VK_CHECK(vkAllocateCommandBuffers(device, &cb_ai, &cmd));

    VkCommandBufferBeginInfo cb_bi{};
    cb_bi.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    cb_bi.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
    VK_CHECK(vkBeginCommandBuffer(cmd, &cb_bi));

    vkCmdBindPipeline(cmd, VK_PIPELINE_BIND_POINT_COMPUTE, pipeline);
    vkCmdBindDescriptorSets(cmd, VK_PIPELINE_BIND_POINT_COMPUTE,
                            pipe_layout, 0, 1, &dset, 0, nullptr);

    // Timestamps + dispatch: 1 workgroup = 1 subgroup = 1 tensor-core tile
    vkCmdResetQueryPool(cmd, query_pool, 0, 2);
    vkCmdWriteTimestamp(cmd, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, query_pool, 0);
    vkCmdDispatch(cmd, 1, 1, 1);
    vkCmdWriteTimestamp(cmd, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, query_pool, 1);

    // Memory barrier: make compute writes visible to host reads
    VkMemoryBarrier barrier{};
    barrier.sType = VK_STRUCTURE_TYPE_MEMORY_BARRIER;
    barrier.srcAccessMask = VK_ACCESS_SHADER_WRITE_BIT;
    barrier.dstAccessMask = VK_ACCESS_HOST_READ_BIT;
    vkCmdPipelineBarrier(cmd,
        VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
        VK_PIPELINE_STAGE_HOST_BIT,
        0, 1, &barrier, 0, nullptr, 0, nullptr);

    VK_CHECK(vkEndCommandBuffer(cmd));

    // ── Submit + wait ──────────────────────────────────────
    VkSubmitInfo submit{};
    submit.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO;
    submit.commandBufferCount = 1;
    submit.pCommandBuffers = &cmd;

    VkFenceCreateInfo fence_ci{};
    fence_ci.sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO;
    VkFence fence;
    VK_CHECK(vkCreateFence(device, &fence_ci, nullptr, &fence));

    printf("\nDispatching to async compute queue...\n");
    VK_CHECK(vkQueueSubmit(compute_queue, 1, &submit, fence));
    VK_CHECK(vkWaitForFences(device, 1, &fence, VK_TRUE, UINT64_MAX));
    printf("Dispatch complete.\n");

    // ── Read timestamps ────────────────────────────────────
    uint64_t timestamps[2] = {0, 0};
    vkGetQueryPoolResults(device, query_pool, 0, 2, sizeof(timestamps),
                          timestamps, sizeof(uint64_t),
                          VK_QUERY_RESULT_64_BIT | VK_QUERY_RESULT_WAIT_BIT);
    double ns = (double)(timestamps[1] - timestamps[0]) * (double)gpu_props.limits.timestampPeriod;
    double flops = 2.0 * M * N * K;  // GEMM: 2*M*N*K FLOPs
    double gflops = flops / ns;      // ns already in nanoseconds, flops/ns = GFLOPS
    printf("  GPU time: %.0f ns (%.3f us)\n", ns, ns / 1000.0);
    printf("  Effective: %.6f GFLOPS (single 16x16 tile, launch overhead dominates)\n", gflops);

    // ── Read back + verify ─────────────────────────────────
    float* result;
    vkMapMemory(device, buf_c.mem, 0, c_size, 0, (void**)&result);

    int errors = 0;
    float max_err = 0.0f;
    for (uint32_t r = 0; r < M; r++) {
        for (uint32_t c = 0; c < N; c++) {
            float val = result[r * N + c];
            float err = fabsf(val - EXPECTED);
            if (err > max_err) max_err = err;
            if (err > 0.1f) {
                if (errors < 5)
                    printf("  MISMATCH [%u,%u]: got %.2f expected %.2f\n",
                           r, c, val, EXPECTED);
                errors++;
            }
        }
    }

    printf("\n=== Result ===\n");
    printf("  C[0,0]=%.2f  C[8,8]=%.2f  C[15,15]=%.2f\n",
           result[0], result[8 * N + 8], result[15 * N + 15]);
    printf("  Expected: %.2f  Max error: %.6f  Mismatches: %d/%u\n",
           EXPECTED, max_err, errors, M * N);

    if (errors == 0)
        printf("\n  >>> TENSOR CORES CONFIRMED — cooperative matrix GEMM passed <<<\n");
    else
        printf("\n  >>> VERIFICATION FAILED — %d mismatches <<<\n", errors);

    vkUnmapMemory(device, buf_c.mem);

    // ── Cleanup ────────────────────────────────────────────
    vkDestroyFence(device, fence, nullptr);
    vkDestroyQueryPool(device, query_pool, nullptr);
    vkDestroyCommandPool(device, cmd_pool, nullptr);
    vkDestroyPipeline(device, pipeline, nullptr);
    vkDestroyPipelineLayout(device, pipe_layout, nullptr);
    vkDestroyShaderModule(device, shader, nullptr);
    vkDestroyDescriptorPool(device, dpool, nullptr);
    vkDestroyDescriptorSetLayout(device, dsl, nullptr);
    vkDestroyBuffer(device, buf_c.buf, nullptr); vkFreeMemory(device, buf_c.mem, nullptr);
    vkDestroyBuffer(device, buf_b.buf, nullptr); vkFreeMemory(device, buf_b.mem, nullptr);
    vkDestroyBuffer(device, buf_a.buf, nullptr); vkFreeMemory(device, buf_a.mem, nullptr);
    vkDestroyDevice(device, nullptr);
    vkDestroyInstance(instance, nullptr);

    printf("\n╔══════════════════════════════════════════════════════╗\n");
    printf("║  Vector 2 complete.                                 ║\n");
    printf("╚══════════════════════════════════════════════════════╝\n");
    return errors > 0 ? 1 : 0;
}
