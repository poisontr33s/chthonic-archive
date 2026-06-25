// streamline_bridge.cpp
// Thin C++ bridge between Rust (ash/Vulkan) and NVIDIA Streamline SDK 2.12.
// All Vulkan handles cross the ABI boundary as void*; the bridge casts them
// to the opaque handle types Streamline expects.  No C++ types leak into Rust.

// Pull in Vulkan handle type definitions only — no function prototypes.
// Ash loads function pointers at runtime so we must NOT link vulkan-1.dll here.
#define VK_NO_PROTOTYPES
#include <vulkan/vulkan.h>

// Streamline core + Vulkan helper + DLSS (provides DLSSMode::eDLAA)
#include "sl.h"
#include "sl_helpers_vk.h"
#include "sl_dlss.h"

#include <cstdio>

#if defined(_WIN32)
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#endif

// ---- helpers ------------------------------------------------------------

// Transpose a 4×4 column-major float array (glam layout) into
// a Streamline row-major float4x4.  flat[col * 4 + row] → out.row[row][col].
static void col_to_row(const float* col_maj, sl::float4x4& out) {
    float* dst = &out.row[0].x;  // float4 members are contiguous: x,y,z,w
    for (int r = 0; r < 4; ++r)
        for (int c = 0; c < 4; ++c)
            dst[r * 4 + c] = col_maj[c * 4 + r];
}

// ---- Streamline log callback (writes to stderr → captured in smoke log) ----

static void sl_log_callback(sl::LogType type, const char* msg) {
    fprintf(stderr, "[SL:%d] %s\n", static_cast<int>(type), msg);
    fflush(stderr);
}

static PFN_vkQueuePresentKHR s_sl_vk_queue_present = nullptr;
static PFN_vkQueueSubmit s_sl_vk_queue_submit = nullptr;
static PFN_vkCreateSwapchainKHR s_sl_vk_create_swapchain = nullptr;
static PFN_vkDestroySwapchainKHR s_sl_vk_destroy_swapchain = nullptr;

template <typename T>
static sl::Result load_common_proxy(const char* name, T& out) {
    void* fn = nullptr;
    sl::Result r = slGetFeatureFunction(sl::kFeatureCommon, name, fn);
    if (r != sl::Result::eOk) {
#if defined(_WIN32)
        HMODULE interposer = GetModuleHandleW(L"sl.interposer.dll");
        if (!interposer) {
            interposer = LoadLibraryW(L"sl.interposer.dll");
        }
        if (interposer) {
            fn = reinterpret_cast<void*>(GetProcAddress(interposer, name));
        }
#endif
    }
    if (fn) {
        out = reinterpret_cast<T>(fn);
    }
    fprintf(stderr, "[SL] proxy %-24s result=%d ptr=%p\n", name, static_cast<int>(r), fn);
    fflush(stderr);
    return r;
}

static sl::DLSSOptions make_dlaa_options(uint32_t width, uint32_t height) {
    sl::DLSSOptions dlss_opts{};
    dlss_opts.mode = sl::DLSSMode::eDLAA;
    dlss_opts.outputWidth = width;
    dlss_opts.outputHeight = height;
    dlss_opts.colorBuffersHDR = sl::Boolean::eFalse;
    dlss_opts.dlaaPreset = sl::DLSSPreset::ePresetK;
    return dlss_opts;
}

static void describe_texture(
    sl::Resource& resource,
    uint32_t width,
    uint32_t height,
    uint32_t native_format,
    uint32_t usage
) {
    resource.width = width;
    resource.height = height;
    resource.nativeFormat = native_format;
    resource.mipLevels = 1;
    resource.arrayLayers = 1;
    resource.flags = 0;
    resource.usage = usage;
}

// ---- C ABI --------------------------------------------------------------

extern "C" {

// Initialize Streamline.  Must be called before any other function.
// plugin_path — UTF-16 path to the directory containing sl.*.dll files (may be null).
// app_id      — ignored; we use the Project ID path which bypasses executable signature checks.
// Returns sl::Result cast to int (0 = eOk).
int chthonic_sl_init(const wchar_t* plugin_path, uint32_t /*app_id*/) {
    sl::Feature dlss = sl::kFeatureDLSS;

    sl::Preferences prefs{};
    prefs.renderAPI         = sl::RenderAPI::eVulkan;
    prefs.engine            = sl::EngineType::eCustom;
    // Using Project ID path: NGX then uses NVSDK_NGX_Application_Identifier_Type_Project_Id
    // which does NOT validate the calling executable's signature — required for unsigned
    // development binaries.  applicationId left 0; only engineVersion + projectId matter.
    prefs.engineVersion     = "1.0.0";
    prefs.projectId         = "4a1b2c3d-5e6f-7890-abcd-ef1234567890";
    prefs.featuresToLoad    = &dlss;
    prefs.numFeaturesToLoad = 1;
    // eUseManualHooking:          we create VkInstance/VkDevice ourselves (ash).
    // eUseFrameBasedResourceTagging: use slSetTagForFrame (modern API).
    // eLoadDownloadedPlugins: allow OTA-downloaded plugin binaries alongside SDK ones.
    prefs.flags = sl::PreferenceFlags::eDisableCLStateTracking
                | sl::PreferenceFlags::eUseManualHooking
                | sl::PreferenceFlags::eUseFrameBasedResourceTagging
                | sl::PreferenceFlags::eLoadDownloadedPlugins;
    if (plugin_path) {
        prefs.pathsToPlugins    = &plugin_path;
        prefs.numPathsToPlugins = 1;
    }
    // Verbose logging → stderr so it appears in render-smoke.log.
    prefs.logLevel           = sl::LogLevel::eVerbose;
    prefs.logMessageCallback = sl_log_callback;

    sl::Result r = slInit(prefs, sl::kSDKVersion);
    // Check whether the DLSS feature actually loaded after init.
    bool dlss_loaded = false;
    slIsFeatureLoaded(sl::kFeatureDLSS, dlss_loaded);
    fprintf(stderr, "[SL] slInit=%d  kFeatureDLSS loaded=%s\n",
            static_cast<int>(r), dlss_loaded ? "true" : "false");
    fflush(stderr);
    return static_cast<int>(r);
}

// Hand the already-created Vulkan objects to Streamline.
// Must be called immediately after vkCreateDevice, before any feature use.
int chthonic_sl_set_vulkan_info(
    void*    vk_instance,
    void*    vk_physical_device,
    void*    vk_device,
    uint32_t graphics_queue_index,
    uint32_t graphics_queue_family,
    uint32_t compute_queue_index,
    uint32_t compute_queue_family
) {
    sl::VulkanInfo info{};
    info.instance            = reinterpret_cast<VkInstance>(vk_instance);
    info.physicalDevice      = reinterpret_cast<VkPhysicalDevice>(vk_physical_device);
    info.device              = reinterpret_cast<VkDevice>(vk_device);
    info.graphicsQueueIndex  = graphics_queue_index;
    info.graphicsQueueFamily = graphics_queue_family;
    info.computeQueueIndex   = compute_queue_index;
    info.computeQueueFamily  = compute_queue_family;
    sl::Result r = slSetVulkanInfo(info);
    if (r == sl::Result::eOk) {
        load_common_proxy("vkQueuePresentKHR", s_sl_vk_queue_present);
        load_common_proxy("vkQueueSubmit", s_sl_vk_queue_submit);
        load_common_proxy("vkCreateSwapchainKHR", s_sl_vk_create_swapchain);
        load_common_proxy("vkDestroySwapchainKHR", s_sl_vk_destroy_swapchain);
    }
    return static_cast<int>(r);
}

int chthonic_sl_set_dlaa_options(uint32_t width, uint32_t height) {
    sl::ViewportHandle viewport(0u);
    sl::DLSSOptions dlss_opts = make_dlaa_options(width, height);
    return static_cast<int>(slDLSSSetOptions(viewport, dlss_opts));
}

int chthonic_sl_vk_queue_present(void* queue, const void* present_info) {
    if (!s_sl_vk_queue_present) return -1;
    return static_cast<int>(s_sl_vk_queue_present(
        reinterpret_cast<VkQueue>(queue),
        reinterpret_cast<const VkPresentInfoKHR*>(present_info)
    ));
}

int chthonic_sl_vk_queue_submit(
    void* queue,
    uint32_t submit_count,
    const void* submits,
    void* fence
) {
    if (!s_sl_vk_queue_submit) return -1;
    return static_cast<int>(s_sl_vk_queue_submit(
        reinterpret_cast<VkQueue>(queue),
        submit_count,
        reinterpret_cast<const VkSubmitInfo*>(submits),
        reinterpret_cast<VkFence>(fence)
    ));
}

// Obtain a frame token for the given frame index.
// Returns an opaque pointer; the caller stores it and passes it back per-frame.
// Returns null on failure.
void* chthonic_sl_new_frame_token(uint32_t frame_index) {
    sl::FrameToken* token = nullptr;
    sl::Result r = slGetNewFrameToken(token, &frame_index);
    if (r != sl::Result::eOk) return nullptr;
    return token;
}

// Set per-frame common constants.
// All matrices are passed column-major (glam default); transposed here to row-major.
// jitter_x/y: sub-pixel offset in pixel space, range [-0.5, 0.5] (Halton-0.5).
// mvec_scale_x/y: convert the tagged motion vector texture units into pixels.
// motion_vectors_jittered: 1 if MVs still contain jitter (we remove it in shader -> pass 0).
// reset: 1 on camera cut or resize to discard temporal history.
int chthonic_sl_set_constants(
    void*        frame_token_ptr,
    float        jitter_x,
    float        jitter_y,
    const float* proj_col_major,              // unjittered projection, 16 floats col-maj
    const float* inv_proj_col_major,          // inverse of above
    const float* clip_to_prev_clip_col_major, // reprojection matrix, col-maj
    const float* prev_clip_to_clip_col_major,
    float        near_z,
    float        far_z,
    float        fov_y,
    float        aspect,
    float        mvec_scale_x,
    float        mvec_scale_y,
    int          motion_vectors_jittered,
    int          reset
) {
    auto* token = reinterpret_cast<sl::FrameToken*>(frame_token_ptr);
    if (!token) return -1;

    sl::Constants c{};
    col_to_row(proj_col_major,              c.cameraViewToClip);
    col_to_row(inv_proj_col_major,          c.clipToCameraView);
    col_to_row(clip_to_prev_clip_col_major, c.clipToPrevClip);
    col_to_row(prev_clip_to_clip_col_major, c.prevClipToClip);

    c.jitterOffset      = { jitter_x, jitter_y };
    c.mvecScale         = { mvec_scale_x, mvec_scale_y };
    c.cameraNear        = near_z;
    c.cameraFar         = far_z;
    c.cameraFOV         = fov_y;
    c.cameraAspectRatio = aspect;

    c.depthInverted          = sl::Boolean::eFalse;
    c.cameraMotionIncluded   = sl::Boolean::eTrue;
    c.motionVectors3D        = sl::Boolean::eFalse;
    c.orthographicProjection = sl::Boolean::eFalse;
    c.motionVectorsDilated   = sl::Boolean::eFalse;
    c.motionVectorsJittered  = motion_vectors_jittered ? sl::Boolean::eTrue : sl::Boolean::eFalse;
    c.reset                  = reset ? sl::Boolean::eTrue : sl::Boolean::eFalse;

    sl::ViewportHandle viewport(0u);
    return static_cast<int>(slSetConstants(c, *token, viewport));
}

// Tag the four render targets and evaluate DLAA — all in one call to minimise
// the Rust/C++ crossing overhead per frame.
//
// native_* : VkImage handles (uint64 on 64-bit Windows, pass via as_raw() as *mut c_void)
// view_*   : VkImageView handles (same scheme)
// state_*  : VkImageLayout value of each image at the point of tagging.
//            Typical values: COLOR_ATTACHMENT_OPTIMAL=2, GENERAL=1, DEPTH_ATTACHMENT_OPTIMAL=0x3B9ACB68
// Returns sl::Result cast to int.
int chthonic_sl_evaluate_dlaa(
    void*    frame_token_ptr,
    void*    cmd_buffer,     // VkCommandBuffer → sl::CommandBuffer (void*)
    void*    native_color,   void* view_color,  uint32_t state_color,
    void*    native_depth,   void* view_depth,  uint32_t state_depth,
    void*    native_mvec,    void* view_mvec,   uint32_t state_mvec,
    void*    native_output,  void* view_output, uint32_t state_output,
    uint32_t width,
    uint32_t height,
    uint32_t color_format,
    uint32_t depth_format,
    uint32_t mvec_format,
    uint32_t output_format,
    uint32_t color_usage,
    uint32_t depth_usage,
    uint32_t mvec_usage,
    uint32_t output_usage
) {
    auto* token = reinterpret_cast<sl::FrameToken*>(frame_token_ptr);
    if (!token) return -1;

    sl::Extent full{ 0, 0, width, height };
    sl::ViewportHandle viewport(0u);

    // sl::Resource takes (type, native, memory, view, state).
    // All pointer fields are void* — no Vulkan types needed.
    sl::Resource r_color  { sl::ResourceType::eTex2d, native_color,  nullptr, view_color,  state_color  };
    sl::Resource r_depth  { sl::ResourceType::eTex2d, native_depth,  nullptr, view_depth,  state_depth  };
    sl::Resource r_mvec   { sl::ResourceType::eTex2d, native_mvec,   nullptr, view_mvec,   state_mvec   };
    sl::Resource r_output { sl::ResourceType::eTex2d, native_output, nullptr, view_output, state_output };

    describe_texture(r_color, width, height, color_format, color_usage);
    describe_texture(r_depth, width, height, depth_format, depth_usage);
    describe_texture(r_mvec, width, height, mvec_format, mvec_usage);
    describe_texture(r_output, width, height, output_format, output_usage);

    sl::ResourceTag tags[] = {
        sl::ResourceTag(&r_color,  sl::kBufferTypeScalingInputColor,  sl::ResourceLifecycle::eValidUntilEvaluate, &full),
        sl::ResourceTag(&r_depth,  sl::kBufferTypeDepth,              sl::ResourceLifecycle::eValidUntilEvaluate, &full),
        sl::ResourceTag(&r_mvec,   sl::kBufferTypeMotionVectors,      sl::ResourceLifecycle::eValidUntilEvaluate, &full),
        sl::ResourceTag(&r_output, sl::kBufferTypeScalingOutputColor, sl::ResourceLifecycle::eValidUntilEvaluate, &full),
    };

    sl::Result r = slSetTagForFrame(
        *token, viewport,
        tags, 4,
        static_cast<sl::CommandBuffer*>(cmd_buffer)
    );
    if (r != sl::Result::eOk) return static_cast<int>(r);

    // DLAA = DLSS feature running in eDLAA mode.
    sl::DLSSOptions dlss_opts = make_dlaa_options(width, height);

    // slEvaluateFeature requires a viewport handle chained into the inputs array.
    const sl::BaseStructure* inputs[] = { &dlss_opts, &viewport };
    r = slEvaluateFeature(
        sl::kFeatureDLSS,
        *token,
        inputs, 2,
        static_cast<sl::CommandBuffer*>(cmd_buffer)
    );
    return static_cast<int>(r);
}

// Shut down Streamline.  Call on renderer teardown.
void chthonic_sl_shutdown() {
    slShutdown();
}

} // extern "C"
