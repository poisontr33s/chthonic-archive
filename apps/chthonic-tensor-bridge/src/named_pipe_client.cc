#include "named_pipe_client.h"

#include <windows.h>

#include <stdexcept>
#include <string>
#include <vector>

namespace chthonic {
namespace {

[[noreturn]] void ThrowLastError(const char* op) {
    DWORD code = ::GetLastError();
    std::string msg = std::string(op) + " failed (Win32 ";
    msg += std::to_string(code) + ")";
    throw std::runtime_error(msg);
}

}  // namespace

std::string PipeRoundtrip(
    const std::wstring& pipe_name,
    const std::string& request_json,
    unsigned int timeout_ms) {

    // Wait until the satellite has created the pipe.
    if (!::WaitNamedPipeW(pipe_name.c_str(), timeout_ms)) {
        ThrowLastError("WaitNamedPipeW");
    }

    HANDLE pipe = ::CreateFileW(
        pipe_name.c_str(),
        GENERIC_READ | GENERIC_WRITE,
        0,
        nullptr,
        OPEN_EXISTING,
        FILE_ATTRIBUTE_NORMAL,
        nullptr);
    if (pipe == INVALID_HANDLE_VALUE) {
        ThrowLastError("CreateFileW(pipe)");
    }

    DWORD mode = PIPE_READMODE_MESSAGE;
    if (!::SetNamedPipeHandleState(pipe, &mode, nullptr, nullptr)) {
        ::CloseHandle(pipe);
        ThrowLastError("SetNamedPipeHandleState(MESSAGE)");
    }

    DWORD written = 0;
    if (!::WriteFile(pipe, request_json.data(), static_cast<DWORD>(request_json.size()),
                     &written, nullptr) || written != request_json.size()) {
        ::CloseHandle(pipe);
        ThrowLastError("WriteFile(pipe request)");
    }

    std::string out;
    std::vector<char> chunk(64 * 1024);
    for (;;) {
        DWORD got = 0;
        BOOL ok = ::ReadFile(pipe, chunk.data(),
                             static_cast<DWORD>(chunk.size()), &got, nullptr);
        if (got > 0) {
            out.append(chunk.data(), got);
        }
        if (ok) {
            break;  // full message received
        }
        DWORD err = ::GetLastError();
        if (err == ERROR_MORE_DATA) {
            continue;
        }
        if (err == ERROR_BROKEN_PIPE) {
            break;  // server closed -- treat as end-of-message
        }
        ::CloseHandle(pipe);
        ::SetLastError(err);
        ThrowLastError("ReadFile(pipe response)");
    }

    ::CloseHandle(pipe);
    return out;
}

}  // namespace chthonic
