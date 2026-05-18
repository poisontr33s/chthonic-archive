cmake_minimum_required(VERSION 3.15)
cmake_policy(SET CMP0091 NEW)

project(chthonic_tensor_bridge LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(NOT WIN32)
    message(FATAL_ERROR "chthonic-tensor-bridge is Windows-only (NVML + Win32 IPC).")
endif()

# cmake-js injects CMAKE_JS_INC (node + node-addon-api headers) and CMAKE_JS_LIB.
include_directories(${CMAKE_JS_INC})

# ─── TensorRT C++ SDK ───────────────────────────────────────────────────────
# Native NVIDIA TensorRT (NOT the Python wheel — bypasses the cp314 gap on
# Python 3.14 by linking the C++ SDK directly). The bridge owns engine load
# + execution; Python satellite owns text encoders + VAE only.
#
# Setup: install from https://developer.nvidia.com/tensorrt-download, then
#   $env:TENSORRT_ROOT = 'C:\Program Files\NVIDIA\TensorRT-10.x.y.z'
# or pass -DTENSORRT_ROOT=<path> to cmake.
#
if(DEFINED ENV{TENSORRT_ROOT} AND NOT DEFINED TENSORRT_ROOT)
    set(TENSORRT_ROOT "$ENV{TENSORRT_ROOT}" CACHE PATH "TensorRT C++ SDK install root")
endif()

set(_TRT_SEARCH_HINTS
    ${TENSORRT_ROOT}
    "C:/Program Files/NVIDIA/TensorRT"
    "C:/Program Files/NVIDIA GPU Computing Toolkit/TensorRT"
    "C:/Program Files/NVIDIA Corporation/TensorRT"
)
# Allow versioned dirs like TensorRT-10.16.1.11 alongside the bare name
file(GLOB _TRT_VERSIONED_DIRS
    "C:/Program Files/NVIDIA/TensorRT-*"
    "C:/Program Files/NVIDIA GPU Computing Toolkit/TensorRT-*"
)
list(APPEND _TRT_SEARCH_HINTS ${_TRT_VERSIONED_DIRS})

find_path(TRT_INCLUDE_DIR
    NAMES NvInfer.h
    HINTS ${_TRT_SEARCH_HINTS}
    PATH_SUFFIXES include
    DOC "TensorRT include directory (contains NvInfer.h)"
)
find_library(TRT_NVINFER_LIB
    NAMES nvinfer nvinfer_10 nvinfer_11
    HINTS ${_TRT_SEARCH_HINTS}
    PATH_SUFFIXES lib lib/x64
    DOC "TensorRT runtime (nvinfer.lib)"
)
find_library(TRT_NVONNXPARSER_LIB
    NAMES nvonnxparser nvonnxparser_10 nvonnxparser_11
    HINTS ${_TRT_SEARCH_HINTS}
    PATH_SUFFIXES lib lib/x64
    DOC "TensorRT ONNX parser (nvonnxparser.lib)"
)
find_library(TRT_NVINFER_PLUGIN_LIB
    NAMES nvinfer_plugin nvinfer_plugin_10 nvinfer_plugin_11
    HINTS ${_TRT_SEARCH_HINTS}
    PATH_SUFFIXES lib lib/x64
    DOC "TensorRT built-in plugins (nvinfer_plugin.lib)"
)

if(NOT TRT_INCLUDE_DIR OR NOT TRT_NVINFER_LIB OR NOT TRT_NVONNXPARSER_LIB)
    message(FATAL_ERROR
        "TensorRT C++ SDK not found.\n"
        "Install from https://developer.nvidia.com/tensorrt-download (Windows zip),\n"
        "extract, then set:\n"
        "  $env:TENSORRT_ROOT = '<path-to-TensorRT-X.Y.Z.W>'\n"
        "and re-run the build (bunx cmake-js rebuild).\n"
        "Probed paths: ${_TRT_SEARCH_HINTS}\n"
        "Found:\n"
        "  TRT_INCLUDE_DIR     = ${TRT_INCLUDE_DIR}\n"
        "  TRT_NVINFER_LIB     = ${TRT_NVINFER_LIB}\n"
        "  TRT_NVONNXPARSER_LIB= ${TRT_NVONNXPARSER_LIB}"
    )
endif()

message(STATUS "TensorRT include:        ${TRT_INCLUDE_DIR}")
message(STATUS "TensorRT nvinfer:        ${TRT_NVINFER_LIB}")
message(STATUS "TensorRT nvonnxparser:   ${TRT_NVONNXPARSER_LIB}")
message(STATUS "TensorRT nvinfer_plugin: ${TRT_NVINFER_PLUGIN_LIB}")

# ─── CUDA Runtime ───────────────────────────────────────────────────────────
# TensorRT engines execute on a CUDA stream. We need cudart for stream
# management (cudaStreamCreate, cudaMemcpyAsync, IPC handle import/export).
# CMake's CUDAToolkit module covers CUDA 11.x — 13.x without per-version
# tweaks; matches the user's CUDA 12.8 / 12.9 / 13.2 side-by-side installs.
find_package(CUDAToolkit REQUIRED)
message(STATUS "CUDA Toolkit:            ${CUDAToolkit_VERSION} (${CUDAToolkit_LIBRARY_DIR})")

file(GLOB SOURCE_FILES "src/*.cc" "src/*.h")

add_library(${PROJECT_NAME} SHARED ${SOURCE_FILES} ${CMAKE_JS_SRC})
set_target_properties(${PROJECT_NAME} PROPERTIES PREFIX "" SUFFIX ".node")

target_link_libraries(${PROJECT_NAME} PRIVATE ${CMAKE_JS_LIB})

# Win32 system libraries
target_link_libraries(${PROJECT_NAME} PRIVATE
    advapi32       # registry (RegOpenKeyExW, RegQueryValueExW)
    user32
    shell32
    kernel32
    bcrypt         # CNG: HKDF-SHA256, AES-256-GCM, SHA-256 (win32_crypto.cc)
    crypt32        # base64 encode/decode for CUDA IPC handle transport over JSON
)

# TensorRT C++ SDK + CUDA runtime — the load-bearing addition for the
# bridge's loadEngine() / runDit() path. nvinfer_plugin only linked if found
# (some lean SDK extracts omit it).
target_include_directories(${PROJECT_NAME} PRIVATE ${TRT_INCLUDE_DIR})
target_link_libraries(${PROJECT_NAME} PRIVATE
    ${TRT_NVINFER_LIB}
    ${TRT_NVONNXPARSER_LIB}
    CUDA::cudart
    CUDA::cuda_driver
)
if(TRT_NVINFER_PLUGIN_LIB)
    target_link_libraries(${PROJECT_NAME} PRIVATE ${TRT_NVINFER_PLUGIN_LIB})
endif()

# Find node-addon-api via npm-installed path
execute_process(
    COMMAND node -p "require('node-addon-api').include"
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
    OUTPUT_VARIABLE NODE_ADDON_API_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE
)
string(REGEX REPLACE "[\r\n\"]" "" NODE_ADDON_API_DIR ${NODE_ADDON_API_DIR})
target_include_directories(${PROJECT_NAME} PRIVATE ${NODE_ADDON_API_DIR})

# NAPI exception handling
target_compile_definitions(${PROJECT_NAME} PRIVATE
    NAPI_VERSION=9
    NAPI_CPP_EXCEPTIONS
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    UNICODE
    _UNICODE
    _WIN32_WINNT=0x0A00     # Windows 10+ APIs (PROC_THREAD_ATTRIBUTE_HANDLE_LIST)
)

if(MSVC)
    target_compile_options(${PROJECT_NAME} PRIVATE /W4 /permissive- /Zc:__cplusplus /EHsc /utf-8)
    set_property(TARGET ${PROJECT_NAME} PROPERTY MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>DLL")
endif()

# Generate node.lib delay-load helper if cmake-js provided one
if(MSVC AND CMAKE_JS_NODELIB_DEF AND CMAKE_JS_NODELIB_TARGET)
    execute_process(
        COMMAND ${CMAKE_AR} /def:${CMAKE_JS_NODELIB_DEF} /out:${CMAKE_JS_NODELIB_TARGET} ${CMAKE_STATIC_LINKER_FLAGS}
    )
endif()
