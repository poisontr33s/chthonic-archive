// hardware_fp.h -- Hardware identity probes (NVML GPU UUID + Windows MachineGuid).

#pragma once

#include <string>

namespace chthonic {

struct HardwareFingerprint {
    std::string gpu_uuid;
    std::string machine_guid;
};

// Throws std::runtime_error on failure with a message safe to surface to JS.
HardwareFingerprint QueryHardwareFingerprint();

}  // namespace chthonic
