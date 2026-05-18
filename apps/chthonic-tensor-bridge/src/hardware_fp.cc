#include "hardware_fp.h"

#include <windows.h>
#include <winreg.h>

#include <array>
#include <stdexcept>
#include <string>

namespace chthonic {
namespace {

// Minimal NVML dynamic surface — we link nothing at build time so the addon
// is loadable on machines without the CUDA SDK headers present.
using nvmlReturn_t = int;
using nvmlDevice_t = void*;

constexpr int kNvmlSuccess = 0;
constexpr std::size_t kNvmlUuidLen = 96;

using PFN_nvmlInit_v2          = nvmlReturn_t (*)();
using PFN_nvmlShutdown         = nvmlReturn_t (*)();
using PFN_nvmlDeviceGetHandle  = nvmlReturn_t (*)(unsigned int, nvmlDevice_t*);
using PFN_nvmlDeviceGetUUID    = nvmlReturn_t (*)(nvmlDevice_t, char*, unsigned int);

struct NvmlLibrary {
    HMODULE mod = nullptr;
    PFN_nvmlInit_v2 init = nullptr;
    PFN_nvmlShutdown shutdown = nullptr;
    PFN_nvmlDeviceGetHandle get_handle = nullptr;
    PFN_nvmlDeviceGetUUID get_uuid = nullptr;

    NvmlLibrary() {
        mod = ::LoadLibraryW(L"nvml.dll");
        if (!mod) {
            // Try the alternate driver-store path
            mod = ::LoadLibraryW(L"C:\\Windows\\System32\\nvml.dll");
        }
        if (!mod) return;
        init        = reinterpret_cast<PFN_nvmlInit_v2>(::GetProcAddress(mod, "nvmlInit_v2"));
        shutdown    = reinterpret_cast<PFN_nvmlShutdown>(::GetProcAddress(mod, "nvmlShutdown"));
        get_handle  = reinterpret_cast<PFN_nvmlDeviceGetHandle>(::GetProcAddress(mod, "nvmlDeviceGetHandleByIndex_v2"));
        get_uuid    = reinterpret_cast<PFN_nvmlDeviceGetUUID>(::GetProcAddress(mod, "nvmlDeviceGetUUID"));
    }
    ~NvmlLibrary() {
        if (mod) ::FreeLibrary(mod);
    }
    bool ok() const { return mod && init && shutdown && get_handle && get_uuid; }
};

std::string QueryGpuUuid() {
    NvmlLibrary lib;
    if (!lib.ok()) {
        throw std::runtime_error("nvml.dll not loadable; install NVIDIA driver");
    }
    if (lib.init() != kNvmlSuccess) {
        throw std::runtime_error("nvmlInit_v2 failed");
    }
    nvmlDevice_t dev = nullptr;
    nvmlReturn_t rc = lib.get_handle(0u, &dev);
    if (rc != kNvmlSuccess || dev == nullptr) {
        lib.shutdown();
        throw std::runtime_error("nvmlDeviceGetHandleByIndex_v2 failed (no GPU 0?)");
    }
    std::array<char, kNvmlUuidLen> buf{};
    rc = lib.get_uuid(dev, buf.data(), static_cast<unsigned int>(buf.size()));
    lib.shutdown();
    if (rc != kNvmlSuccess) {
        throw std::runtime_error("nvmlDeviceGetUUID failed");
    }
    return std::string(buf.data());
}

std::string QueryMachineGuid() {
    HKEY key = nullptr;
    LSTATUS rc = ::RegOpenKeyExW(
        HKEY_LOCAL_MACHINE,
        L"SOFTWARE\\Microsoft\\Cryptography",
        0,
        KEY_READ | KEY_WOW64_64KEY,
        &key);
    if (rc != ERROR_SUCCESS) {
        throw std::runtime_error("RegOpenKeyExW(HKLM\\SOFTWARE\\Microsoft\\Cryptography) failed");
    }
    wchar_t buf[128] = {};
    DWORD buflen = sizeof(buf);
    DWORD type = 0;
    rc = ::RegQueryValueExW(
        key,
        L"MachineGuid",
        nullptr,
        &type,
        reinterpret_cast<LPBYTE>(buf),
        &buflen);
    ::RegCloseKey(key);
    if (rc != ERROR_SUCCESS || type != REG_SZ) {
        throw std::runtime_error("RegQueryValueExW(MachineGuid) failed");
    }
    int needed = ::WideCharToMultiByte(CP_UTF8, 0, buf, -1, nullptr, 0, nullptr, nullptr);
    if (needed <= 0) {
        throw std::runtime_error("WideCharToMultiByte sizing failed");
    }
    std::string out(static_cast<std::size_t>(needed - 1), '\0');
    ::WideCharToMultiByte(CP_UTF8, 0, buf, -1, out.data(), needed, nullptr, nullptr);
    return out;
}

}  // namespace

HardwareFingerprint QueryHardwareFingerprint() {
    HardwareFingerprint fp;
    fp.gpu_uuid = QueryGpuUuid();
    fp.machine_guid = QueryMachineGuid();
    return fp;
}

}  // namespace chthonic
