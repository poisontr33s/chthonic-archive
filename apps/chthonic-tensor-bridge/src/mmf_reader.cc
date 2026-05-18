#include "mmf_reader.h"

#include <cstring>
#include <stdexcept>
#include <string>

namespace chthonic {
namespace {

[[noreturn]] void ThrowLastError(const char* op) {
    DWORD code = ::GetLastError();
    std::string msg = std::string(op) + " failed (Win32 ";
    msg += std::to_string(code) + ")";
    throw std::runtime_error(msg);
}

}  // namespace

MappedFile::MappedFile(const std::string& name) {
    handle_ = ::OpenFileMappingA(FILE_MAP_READ, FALSE, name.c_str());
    if (!handle_) {
        ThrowLastError("OpenFileMappingA");
    }
    LPVOID view = ::MapViewOfFile(handle_, FILE_MAP_READ, 0, 0, 0);
    if (!view) {
        ::CloseHandle(handle_);
        handle_ = nullptr;
        ThrowLastError("MapViewOfFile");
    }
    MEMORY_BASIC_INFORMATION info{};
    if (::VirtualQuery(view, &info, sizeof(info)) == 0) {
        ::UnmapViewOfFile(view);
        ::CloseHandle(handle_);
        handle_ = nullptr;
        ThrowLastError("VirtualQuery(view)");
    }
    base_ = static_cast<std::uint8_t*>(view);
    size_ = info.RegionSize;
}

MappedFile::~MappedFile() {
    if (base_) ::UnmapViewOfFile(base_);
    if (handle_) ::CloseHandle(handle_);
}

std::vector<std::uint8_t> ReadMmfPayload(
    const std::string& mmf_name,
    std::size_t expected_size) {

    MappedFile mmf(mmf_name);
    if (mmf.size() < 4 + expected_size) {
        throw std::runtime_error(
            "MMF region smaller than promised payload "
            "(region=" + std::to_string(mmf.size()) +
            ", needed=" + std::to_string(4 + expected_size) + ")");
    }

    std::uint32_t prefix = 0;
    std::memcpy(&prefix, mmf.data(), sizeof(prefix));
    if (prefix != expected_size) {
        throw std::runtime_error(
            "MMF length prefix mismatch (prefix=" + std::to_string(prefix) +
            ", expected=" + std::to_string(expected_size) + ")");
    }

    std::vector<std::uint8_t> out(expected_size);
    std::memcpy(out.data(), mmf.data() + 4, expected_size);
    return out;
}

}  // namespace chthonic
