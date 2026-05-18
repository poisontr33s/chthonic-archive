// named_pipe_client.h -- Blocking Win32 named-pipe message client.

#pragma once

#include <string>

namespace chthonic {

// Connects to the flux-satellite control pipe, sends `request_json`,
// and returns the JSON response (one message, newline-terminated by the server).
// Blocks the calling thread; intended for use inside Napi::AsyncWorker::Execute().
// Throws std::runtime_error on Win32 failure.
std::string PipeRoundtrip(
    const std::wstring& pipe_name,
    const std::string& request_json,
    unsigned int timeout_ms = 60'000);

}  // namespace chthonic
