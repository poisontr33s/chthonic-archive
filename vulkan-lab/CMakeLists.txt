cmake_minimum_required(VERSION 3.28)

project(vulkan_lab LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# ── Vulkan SDK ──────────────────────────────────────────────
find_package(Vulkan REQUIRED)
message(STATUS "Vulkan SDK: ${Vulkan_INCLUDE_DIRS}")
message(STATUS "Vulkan Lib: ${Vulkan_LIBRARIES}")

# ── Shader compiler ─────────────────────────────────────────
find_program(GLSLC_EXE glslc HINTS "$ENV{VULKAN_SDK}/Bin")

# ── Probe: device capability enumerator ─────────────────────
add_executable(vk_probe probes/vk_capability_probe.cpp)
target_link_libraries(vk_probe PRIVATE Vulkan::Vulkan)
target_compile_definitions(vk_probe PRIVATE
    NOMINMAX
    WIN32_LEAN_AND_MEAN
)

# ── Shader compilation helper ───────────────────────────────
function(compile_shader TARGET SHADER_SRC)
    get_filename_component(SHADER_NAME ${SHADER_SRC} NAME)
    set(SPV_OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/${SHADER_NAME}.spv")
    add_custom_command(
        OUTPUT  ${SPV_OUTPUT}
        COMMAND ${GLSLC_EXE} --target-env=vulkan1.3 -o ${SPV_OUTPUT} ${SHADER_SRC}
        DEPENDS ${SHADER_SRC}
        COMMENT "Compiling ${SHADER_NAME} → SPIR-V"
    )
    add_custom_target(${TARGET}_shader DEPENDS ${SPV_OUTPUT})
    add_dependencies(${TARGET} ${TARGET}_shader)
endfunction()

# ── Vector 2: Cooperative Matrix ────────────────────────────
add_executable(coop_matrix vectors/coop_matrix/main.cpp)
target_link_libraries(coop_matrix PRIVATE Vulkan::Vulkan)
target_compile_definitions(coop_matrix PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
compile_shader(coop_matrix
    "${CMAKE_CURRENT_SOURCE_DIR}/vectors/coop_matrix/coop_matmul.comp")

# ── Vector 3: AV1 Video Decode ──────────────────────────────
add_executable(v3_video vectors/v3_video/main.cpp)
target_link_libraries(v3_video PRIVATE Vulkan::Vulkan)
target_compile_definitions(v3_video PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)

# ── Future targets ──────────────────────────────────────────
# add_executable(rt_spatial_query  vectors/rt_spatial/main.cpp)
# add_executable(dgc_autonomous    vectors/dgc/main.cpp)
# add_executable(gpu_scheduler     vectors/gpu_sched/main.cpp)
