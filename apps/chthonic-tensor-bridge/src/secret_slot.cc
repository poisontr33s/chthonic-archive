#include "secret_slot.h"

#include <windows.h>

namespace chthonic {

SecretSlot& SecretSlot::Instance() {
    static SecretSlot instance;
    return instance;
}

SecretSlot::~SecretSlot() {
    Clear();
}

void SecretSlot::Set(const std::uint8_t* data, std::size_t len) {
    std::lock_guard<std::mutex> lock(mu_);
    if (!bytes_.empty()) {
        ::SecureZeroMemory(bytes_.data(), bytes_.size());
    }
    bytes_.assign(data, data + len);
}

void SecretSlot::Clear() {
    std::lock_guard<std::mutex> lock(mu_);
    if (!bytes_.empty()) {
        ::SecureZeroMemory(bytes_.data(), bytes_.size());
    }
    bytes_.clear();
    bytes_.shrink_to_fit();
}

bool SecretSlot::IsSet() const {
    std::lock_guard<std::mutex> lock(mu_);
    return !bytes_.empty();
}

std::vector<std::uint8_t> SecretSlot::CopyOut() const {
    std::lock_guard<std::mutex> lock(mu_);
    return bytes_;
}

}  // namespace chthonic
