cmake_minimum_required(VERSION 3.28)

project(chthonic_archive_surfaces LANGUAGES NONE)

set(CHTHONIC_ROOT "${CMAKE_SOURCE_DIR}")
set(CHTHONIC_BINARY_ROOT "${CMAKE_BINARY_DIR}")

find_program(CARGO_EXE cargo REQUIRED)
find_program(PWSH_EXE pwsh REQUIRED)
find_program(GLSLC_EXE glslc)
find_program(DXC_EXE dxc)
find_program(NVCC_EXE nvcc)

set(GLSL_SHADER_DIR "${CHTHONIC_ROOT}/assets/shaders")
set(HLSL_SHADER_DIR "${CHTHONIC_ROOT}/assets/shaders/hlsl")
set(CUDA_PROBE_SOURCE "${CHTHONIC_ROOT}/native/cuda/chthonic_probe.cu")

file(GLOB GLSL_SOURCES CONFIGURE_DEPENDS
    "${GLSL_SHADER_DIR}/*.vert"
    "${GLSL_SHADER_DIR}/*.frag"
    "${GLSL_SHADER_DIR}/*.comp"
    "${GLSL_SHADER_DIR}/*.geom"
    "${GLSL_SHADER_DIR}/*.tesc"
    "${GLSL_SHADER_DIR}/*.tese"
)

file(GLOB HLSL_SOURCES CONFIGURE_DEPENDS
    "${HLSL_SHADER_DIR}/*.vert.hlsl"
    "${HLSL_SHADER_DIR}/*.frag.hlsl"
    "${HLSL_SHADER_DIR}/*.comp.hlsl"
)

add_custom_target(cargo_debug
    COMMAND "${CARGO_EXE}" build
    WORKING_DIRECTORY "${CHTHONIC_ROOT}"
    COMMENT "Build Rust runtime (debug)"
    VERBATIM
)

add_custom_target(cargo_release
    COMMAND "${CARGO_EXE}" build --release
    WORKING_DIRECTORY "${CHTHONIC_ROOT}"
    COMMENT "Build Rust runtime (release)"
    VERBATIM
)

add_custom_target(graphics_lane
    COMMAND "${PWSH_EXE}" -NoProfile -File "${CHTHONIC_ROOT}/scripts/chthonic.ps1" graphics lane
    WORKING_DIRECTORY "${CHTHONIC_ROOT}"
    COMMENT "Emit graphics lane summary"
    VERBATIM
)

if(GLSLC_EXE AND GLSL_SOURCES)
    set(GLSL_OUTPUTS "")
    foreach(shader IN LISTS GLSL_SOURCES)
        get_filename_component(shader_name "${shader}" NAME)
        set(out_file "${CHTHONIC_BINARY_ROOT}/glsl/${shader_name}.spv")
        list(APPEND GLSL_OUTPUTS "${out_file}")
        add_custom_command(
            OUTPUT "${out_file}"
            COMMAND "${CMAKE_COMMAND}" -E make_directory "${CHTHONIC_BINARY_ROOT}/glsl"
            COMMAND "${GLSLC_EXE}" --target-env=vulkan1.4 --target-spv=spv1.6 -O "${shader}" -o "${out_file}"
            DEPENDS "${shader}"
            COMMENT "GLSL -> SPIR-V ${shader_name}"
            VERBATIM
        )
    endforeach()
    add_custom_target(shaders_glsl ALL DEPENDS ${GLSL_OUTPUTS})
else()
    add_custom_target(shaders_glsl
        COMMAND "${CMAKE_COMMAND}" -E echo "GLSL compile surface unavailable (missing glslc or GLSL sources)"
    )
endif()

if(DXC_EXE AND HLSL_SOURCES)
    set(HLSL_OUTPUTS "")
    foreach(shader IN LISTS HLSL_SOURCES)
        get_filename_component(shader_name "${shader}" NAME)
        if(shader_name MATCHES "\\.vert\\.hlsl$")
            set(shader_profile "vs_6_0")
        elseif(shader_name MATCHES "\\.frag\\.hlsl$")
            set(shader_profile "ps_6_0")
        elseif(shader_name MATCHES "\\.comp\\.hlsl$")
            set(shader_profile "cs_6_0")
        else()
            continue()
        endif()

        set(out_file "${CHTHONIC_BINARY_ROOT}/hlsl/${shader_name}.cso")
        list(APPEND HLSL_OUTPUTS "${out_file}")
        add_custom_command(
            OUTPUT "${out_file}"
            COMMAND "${CMAKE_COMMAND}" -E make_directory "${CHTHONIC_BINARY_ROOT}/hlsl"
            COMMAND "${DXC_EXE}" -T "${shader_profile}" -E main -Fo "${out_file}" "${shader}"
            DEPENDS "${shader}"
            COMMENT "HLSL compile ${shader_name}"
            VERBATIM
        )
    endforeach()
    add_custom_target(shaders_hlsl DEPENDS ${HLSL_OUTPUTS})
else()
    add_custom_target(shaders_hlsl
        COMMAND "${CMAKE_COMMAND}" -E echo "HLSL compile surface unavailable (missing dxc or HLSL sources)"
    )
endif()

if(NVCC_EXE AND EXISTS "${CUDA_PROBE_SOURCE}")
    set(CUDA_OUTPUT "${CHTHONIC_BINARY_ROOT}/cuda/chthonic_probe.exe")
    add_custom_command(
        OUTPUT "${CUDA_OUTPUT}"
        COMMAND "${CMAKE_COMMAND}" -E make_directory "${CHTHONIC_BINARY_ROOT}/cuda"
        COMMAND "${NVCC_EXE}" -std=c++17 "${CUDA_PROBE_SOURCE}" -o "${CUDA_OUTPUT}"
        DEPENDS "${CUDA_PROBE_SOURCE}"
        COMMENT "Compile CUDA probe"
        VERBATIM
    )
    add_custom_target(cuda_probe DEPENDS "${CUDA_OUTPUT}")
else()
    add_custom_target(cuda_probe
        COMMAND "${CMAKE_COMMAND}" -E echo "CUDA probe unavailable (missing nvcc or CUDA probe source)"
    )
endif()
