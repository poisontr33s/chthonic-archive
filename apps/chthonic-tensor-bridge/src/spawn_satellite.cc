#include "spawn_satellite.h"

#include <stdexcept>
#include <string>
#include <system_error>
#include <vector>

namespace chthonic {
namespace {

struct ScopedHandle {
    HANDLE h = INVALID_HANDLE_VALUE;
    ScopedHandle() = default;
    explicit ScopedHandle(HANDLE handle) : h(handle) {}
    ~ScopedHandle() { reset(); }
    ScopedHandle(const ScopedHandle&) = delete;
    ScopedHandle& operator=(const ScopedHandle&) = delete;
    ScopedHandle(ScopedHandle&& o) noexcept : h(o.h) { o.h = INVALID_HANDLE_VALUE; }
    ScopedHandle& operator=(ScopedHandle&& o) noexcept {
        if (this != &o) { reset(); h = o.h; o.h = INVALID_HANDLE_VALUE; }
        return *this;
    }
    HANDLE release() { HANDLE r = h; h = INVALID_HANDLE_VALUE; return r; }
    void reset(HANDLE handle = INVALID_HANDLE_VALUE) {
        if (h != INVALID_HANDLE_VALUE && h != nullptr) {
            ::CloseHandle(h);
        }
        h = handle;
    }
};

[[noreturn]] void ThrowLastError(const char* op) {
    DWORD code = ::GetLastError();
    std::string msg = std::string(op) + " failed (Win32 ";
    msg += std::to_string(code) + ")";
    throw std::runtime_error(msg);
}

}  // namespace

SatelliteHandles SpawnSatelliteWithSecret(
    const std::wstring& uv_path,
    const std::wstring& args,
    const std::wstring& cwd,
    const std::vector<std::uint8_t>& secret_bytes) {

    // -- 1. Anonymous pipe for child stdin --------------------------------
    SECURITY_ATTRIBUTES sa{};
    sa.nLength = sizeof(sa);
    sa.bInheritHandle = TRUE;     // read end inherits
    sa.lpSecurityDescriptor = nullptr;

    HANDLE stdin_r = nullptr;
    HANDLE stdin_w = nullptr;
    if (!::CreatePipe(&stdin_r, &stdin_w, &sa, 0)) {
        ThrowLastError("CreatePipe(stdin)");
    }
    ScopedHandle pipe_read(stdin_r);
    ScopedHandle pipe_write(stdin_w);

    // Parent's write end MUST NOT be inheritable.
    if (!::SetHandleInformation(pipe_write.h, HANDLE_FLAG_INHERIT, 0)) {
        ThrowLastError("SetHandleInformation(stdin_w, !inherit)");
    }

    // -- 2. Build an explicit handle-inheritance allow-list ---------------
    // PROC_THREAD_ATTRIBUTE_HANDLE_LIST restricts inheritance to ONLY the
    // listed handles. Without this, every inheritable handle in the parent
    // (sockets, files, the SecretSlot if it had handles) would leak.
    SIZE_T attr_size = 0;
    ::InitializeProcThreadAttributeList(nullptr, 1, 0, &attr_size);
    std::vector<unsigned char> attr_storage(attr_size);
    auto attr_list = reinterpret_cast<LPPROC_THREAD_ATTRIBUTE_LIST>(attr_storage.data());
    if (!::InitializeProcThreadAttributeList(attr_list, 1, 0, &attr_size)) {
        ThrowLastError("InitializeProcThreadAttributeList");
    }

    HANDLE inheritable[] = { pipe_read.h };
    if (!::UpdateProcThreadAttribute(
            attr_list, 0, PROC_THREAD_ATTRIBUTE_HANDLE_LIST,
            inheritable, sizeof(inheritable), nullptr, nullptr)) {
        ::DeleteProcThreadAttributeList(attr_list);
        ThrowLastError("UpdateProcThreadAttribute(HANDLE_LIST)");
    }

    STARTUPINFOEXW si{};
    si.StartupInfo.cb = sizeof(STARTUPINFOEXW);
    si.StartupInfo.dwFlags = STARTF_USESTDHANDLES;
    si.StartupInfo.hStdInput  = pipe_read.h;
    si.StartupInfo.hStdOutput = ::GetStdHandle(STD_OUTPUT_HANDLE);
    si.StartupInfo.hStdError  = ::GetStdHandle(STD_ERROR_HANDLE);
    si.lpAttributeList = attr_list;

    PROCESS_INFORMATION pi{};

    // CreateProcessW mutates lpCommandLine — pass a writable copy.
    std::wstring cmdline = L"\"" + uv_path + L"\" " + args;
    std::vector<wchar_t> cmd_buf(cmdline.begin(), cmdline.end());
    cmd_buf.push_back(L'\0');

    BOOL ok = ::CreateProcessW(
        nullptr,                  // application name (read from cmdline)
        cmd_buf.data(),           // command line (writable)
        nullptr,                  // process security
        nullptr,                  // thread security
        TRUE,                     // bInheritHandles -- required for the listed set
        EXTENDED_STARTUPINFO_PRESENT | CREATE_UNICODE_ENVIRONMENT | CREATE_NO_WINDOW,
        nullptr,                  // environment (inherit)
        cwd.empty() ? nullptr : cwd.c_str(),
        &si.StartupInfo,
        &pi);

    ::DeleteProcThreadAttributeList(attr_list);

    if (!ok) {
        ThrowLastError("CreateProcessW");
    }

    // -- 3. Drop the child's end in the parent (child holds it via inherit)
    pipe_read.reset();

    // -- 4. Stream the secret to child stdin, then close ------------------
    // Child blocks on sys.stdin.read() until we close stdin_w.
    if (!secret_bytes.empty()) {
        const std::uint8_t* p = secret_bytes.data();
        std::size_t remaining = secret_bytes.size();
        while (remaining > 0) {
            DWORD wrote = 0;
            DWORD chunk = remaining > 0x10000 ? 0x10000 : static_cast<DWORD>(remaining);
            if (!::WriteFile(pipe_write.h, p, chunk, &wrote, nullptr) || wrote == 0) {
                // Child may have exited; clean up and surface the failure.
                ::TerminateProcess(pi.hProcess, 1);
                ::CloseHandle(pi.hThread);
                ::CloseHandle(pi.hProcess);
                ThrowLastError("WriteFile(stdin pipe)");
            }
            p += wrote;
            remaining -= wrote;
        }
    }
    // Closing the write end signals EOF to the child's stdin.read() loop.
    pipe_write.reset();

    SatelliteHandles out;
    out.process = pi.hProcess;
    out.thread  = pi.hThread;
    out.pid     = pi.dwProcessId;
    return out;
}

void CloseSatelliteHandles(SatelliteHandles& h) {
    if (h.thread != INVALID_HANDLE_VALUE && h.thread != nullptr) {
        ::CloseHandle(h.thread);
        h.thread = INVALID_HANDLE_VALUE;
    }
    if (h.process != INVALID_HANDLE_VALUE && h.process != nullptr) {
        ::CloseHandle(h.process);
        h.process = INVALID_HANDLE_VALUE;
    }
    h.pid = 0;
}

}  // namespace chthonic
