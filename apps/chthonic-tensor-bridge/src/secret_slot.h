// secret_slot.h -- Process-local master-secret holder with explicit wipe.
//
// Stores the FLUX master secret strictly in C++ memory, never in V8 strings
// (which can leak into snapshots, V8 zone allocations, or GC heap dumps).
// All access is mutex-guarded; clear() does a SecureZeroMemory before
// releasing the storage.

#pragma once

#include <cstddef>
#include <cstdint>
#include <mutex>
#include <vector>

namespace chthonic {

class SecretSlot {
public:
    static SecretSlot& Instance();

    void Set(const std::uint8_t* data, std::size_t len);
    void Clear();
    bool IsSet() const;
    std::vector<std::uint8_t> CopyOut() const;

    SecretSlot(const SecretSlot&) = delete;
    SecretSlot& operator=(const SecretSlot&) = delete;

private:
    SecretSlot() = default;
    ~SecretSlot();

    mutable std::mutex mu_;
    std::vector<std::uint8_t> bytes_;
};

}  // namespace chthonic
