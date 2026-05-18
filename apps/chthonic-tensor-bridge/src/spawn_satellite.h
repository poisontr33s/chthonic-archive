// spawn_satellite.h -- CreateProcessW + anonymous-pipe stdin redirection.
//
// Spawns the python flux-satellite daemon and writes the master secret to
// its stdin BEFORE the secret reaches any OS-visible argv. The child sees the
// command line `uv run -m flux_satellite ...` only — Process Explorer / ETW
// / wmic cannot recover the secret.

#pragma once

#include <windows.h>

#include <cstdint>
#include <string>
#include <vector>

namespace chthonic {

struct SatelliteHandles {
    HANDLE process = INVALID_HANDLE_VALUE;
    HANDLE thread  = INVALID_HANDLE_VALUE;
    DWORD  pid     = 0;
};

// Spawns `uv_path` with the supplied `args` from `cwd`. Writes `secret_bytes`
// to the child's stdin then closes the write handle so the child unblocks.
// Throws std::runtime_error on any Win32 failure (all handles cleaned up).
SatelliteHandles SpawnSatelliteWithSecret(
    const std::wstring& uv_path,
    const std::wstring& args,
    const std::wstring& cwd,
    const std::vector<std::uint8_t>& secret_bytes);

// Best-effort graceful shutdown: closes the process handle. Caller is
// expected to send a `shutdown` op over the control pipe first.
void CloseSatelliteHandles(SatelliteHandles& h);

}  // namespace chthonic
