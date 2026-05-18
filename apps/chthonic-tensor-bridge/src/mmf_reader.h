// mmf_reader.h -- Read a sized RGBA payload from a memory-mapped file.

#pragma once

#include <windows.h>

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace chthonic {

// RAII wrapper for an OpenFileMappingA + MapViewOfFile pair.
class MappedFile {
public:
    explicit MappedFile(const std::string& name);
    ~MappedFile();

    MappedFile(const MappedFile&) = delete;
    MappedFile& operator=(const MappedFile&) = delete;

    const std::uint8_t* data() const { return base_; }
    std::size_t size() const { return size_; }

private:
    HANDLE handle_ = nullptr;
    std::uint8_t* base_ = nullptr;
    std::size_t size_ = 0;
};

// Reads the length-prefixed payload from the MMF named `mmf_name`.
// MMF layout: [uint32 LE length][raw bytes]. Returns the raw bytes copied.
// `expected_size` is the size promised by the satellite in its JSON response;
// the function asserts the prefix matches before copying.
std::vector<std::uint8_t> ReadMmfPayload(
    const std::string& mmf_name,
    std::size_t expected_size);

}  // namespace chthonic
