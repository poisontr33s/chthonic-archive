#include "dit_pipe_server.h"

#include <windows.h>

#include <chrono>
#include <iostream>
#include <map>
#include <sstream>
#include <string>
#include <vector>

#include "trt_engine.h"
#include "win32_crypto.h"

namespace chthonic {
namespace {

constexpr DWORD kPipeBufBytes = 1 << 20;  // 1 MiB — comfortably fits IPC handle JSON
constexpr DWORD kPollMs = 200;

// ── Minimal JSON helpers (we only parse our own well-formed payloads) ──────

// Find the value substring for `"key":` in `text`, starting at `from`. Returns
// (start, end) of the value, or {npos, npos} if not found. The value includes
// surrounding quotes for strings; for arrays it includes the brackets; for
// objects, the braces; for numbers, just the digits.
struct ValueSpan { std::size_t start = std::string::npos; std::size_t end = std::string::npos; };

ValueSpan FindValue(const std::string& text, const std::string& key, std::size_t from = 0) {
    std::string needle = "\"" + key + "\"";
    auto pos = text.find(needle, from);
    if (pos == std::string::npos) return {};
    pos += needle.size();
    while (pos < text.size() && (text[pos] == ' ' || text[pos] == ':' || text[pos] == '\t')) ++pos;
    if (pos >= text.size()) return {};
    char open = text[pos];
    if (open == '"') {
        std::size_t end = pos + 1;
        while (end < text.size() && text[end] != '"') {
            if (text[end] == '\\') end += 2;
            else ++end;
        }
        if (end >= text.size()) return {};
        return { pos, end + 1 };
    }
    if (open == '{' || open == '[') {
        char close = open == '{' ? '}' : ']';
        int depth = 1;
        std::size_t end = pos + 1;
        bool in_str = false;
        while (end < text.size() && depth > 0) {
            char c = text[end];
            if (in_str) {
                if (c == '\\') { end += 2; continue; }
                if (c == '"') in_str = false;
            } else {
                if (c == '"') in_str = true;
                else if (c == open) ++depth;
                else if (c == close) --depth;
            }
            ++end;
        }
        if (depth != 0) return {};
        return { pos, end };
    }
    // number / true / false / null
    std::size_t end = pos;
    while (end < text.size() && text[end] != ',' && text[end] != '}' && text[end] != ']'
           && text[end] != ' ' && text[end] != '\t' && text[end] != '\n' && text[end] != '\r') {
        ++end;
    }
    return { pos, end };
}

std::string ExtractString(const std::string& text, const std::string& key, std::size_t from = 0) {
    auto v = FindValue(text, key, from);
    if (v.start == std::string::npos || text[v.start] != '"') {
        throw std::runtime_error("missing string field: " + key);
    }
    std::string out;
    for (std::size_t i = v.start + 1; i + 1 < v.end; ++i) {
        if (text[i] == '\\' && i + 1 < v.end - 1) {
            char esc = text[i + 1];
            if (esc == 'n') out += '\n';
            else if (esc == '"') out += '"';
            else if (esc == '\\') out += '\\';
            else out += esc;
            ++i;
        } else {
            out += text[i];
        }
    }
    return out;
}

long long ExtractInt(const std::string& text, const std::string& key, std::size_t from = 0) {
    auto v = FindValue(text, key, from);
    if (v.start == std::string::npos) {
        throw std::runtime_error("missing int field: " + key);
    }
    return std::stoll(text.substr(v.start, v.end - v.start));
}

std::vector<std::int64_t> ExtractIntArray(const std::string& text, const std::string& key,
                                          std::size_t from = 0) {
    auto v = FindValue(text, key, from);
    if (v.start == std::string::npos || text[v.start] != '[') {
        throw std::runtime_error("missing int-array field: " + key);
    }
    std::vector<std::int64_t> out;
    std::size_t i = v.start + 1;
    while (i < v.end - 1) {
        while (i < v.end - 1 && (text[i] == ' ' || text[i] == ',' || text[i] == '\t' || text[i] == '\n')) ++i;
        if (i >= v.end - 1) break;
        std::size_t end = i;
        while (end < v.end - 1 && text[end] != ',' && text[end] != ']' && text[end] != ' ') ++end;
        if (end == i) break;
        out.push_back(std::stoll(text.substr(i, end - i)));
        i = end;
    }
    return out;
}

IpcBinding ParseBinding(const std::string& text, const std::string& tensor_obj) {
    IpcBinding b;
    std::string handle_b64 = ExtractString(tensor_obj, "handle_b64");
    b.handle_bytes = Base64Decode(handle_b64);
    b.storage_size = static_cast<std::size_t>(ExtractInt(tensor_obj, "storage_size"));
    b.storage_offset = static_cast<std::size_t>(ExtractInt(tensor_obj, "storage_offset"));
    b.shape = ExtractIntArray(tensor_obj, "shape");
    (void)text;
    return b;
}

// Parse {name: {handle_b64, storage_size, storage_offset, shape}, ...}
std::map<std::string, IpcBinding> ParseBindingMap(const std::string& text,
                                                  const std::string& parent_key) {
    auto v = FindValue(text, parent_key);
    if (v.start == std::string::npos || text[v.start] != '{') {
        throw std::runtime_error("missing object: " + parent_key);
    }
    std::string body = text.substr(v.start, v.end - v.start);

    std::map<std::string, IpcBinding> out;
    // Walk top-level keys in `body`. Each key is "name": { ... }. Use FindValue
    // to extract per-key sub-objects, advancing past each.
    std::size_t cursor = 1;  // past the opening '{'
    while (cursor < body.size() - 1) {
        while (cursor < body.size() - 1 && (body[cursor] == ' ' || body[cursor] == ',' ||
               body[cursor] == '\t' || body[cursor] == '\n' || body[cursor] == '\r')) {
            ++cursor;
        }
        if (cursor >= body.size() - 1 || body[cursor] != '"') break;
        std::size_t key_end = cursor + 1;
        while (key_end < body.size() && body[key_end] != '"') ++key_end;
        std::string name = body.substr(cursor + 1, key_end - cursor - 1);

        auto sub = FindValue(body, name, cursor);
        if (sub.start == std::string::npos) break;
        std::string sub_obj = body.substr(sub.start, sub.end - sub.start);
        out[name] = ParseBinding(body, sub_obj);
        cursor = sub.end;
    }
    return out;
}

// ── Win32 helpers ───────────────────────────────────────────────────────────

void WriteAll(HANDLE pipe, const std::string& payload) {
    const char* p = payload.data();
    DWORD remaining = static_cast<DWORD>(payload.size());
    while (remaining > 0) {
        DWORD wrote = 0;
        if (!::WriteFile(pipe, p, remaining, &wrote, nullptr) || wrote == 0) break;
        p += wrote;
        remaining -= wrote;
    }
}

}  // namespace

DitPipeServer::DitPipeServer(TrtEngine* engine, std::wstring pipe_name)
    : engine_(engine), pipe_name_(std::move(pipe_name)) {}

DitPipeServer::~DitPipeServer() {
    Stop();
}

void DitPipeServer::Start() {
    if (thread_.joinable()) return;
    stop_.store(false);
    thread_ = std::thread(&DitPipeServer::ServeLoop, this);
}

void DitPipeServer::Stop() {
    stop_.store(true);
    if (thread_.joinable()) thread_.join();
}

void DitPipeServer::ServeLoop() {
    while (!stop_.load()) {
        HANDLE pipe = ::CreateNamedPipeW(
            pipe_name_.c_str(),
            PIPE_ACCESS_DUPLEX | FILE_FLAG_OVERLAPPED,
            PIPE_TYPE_MESSAGE | PIPE_READMODE_MESSAGE | PIPE_WAIT,
            1, kPipeBufBytes, kPipeBufBytes, 0, nullptr);
        if (pipe == INVALID_HANDLE_VALUE) {
            std::cerr << "[dit-pipe] CreateNamedPipeW failed: "
                      << ::GetLastError() << std::endl;
            std::this_thread::sleep_for(std::chrono::seconds(1));
            continue;
        }

        OVERLAPPED ov{};
        ov.hEvent = ::CreateEventW(nullptr, TRUE, FALSE, nullptr);
        BOOL connected = ::ConnectNamedPipe(pipe, &ov);
        if (!connected && ::GetLastError() == ERROR_IO_PENDING) {
            for (;;) {
                if (stop_.load()) {
                    ::CancelIoEx(pipe, &ov);
                    break;
                }
                DWORD wait = ::WaitForSingleObject(ov.hEvent, kPollMs);
                if (wait == WAIT_OBJECT_0) { connected = TRUE; break; }
                if (wait == WAIT_TIMEOUT) continue;
                break;
            }
        }
        ::CloseHandle(ov.hEvent);

        if (stop_.load() || !connected) {
            ::DisconnectNamedPipe(pipe);
            ::CloseHandle(pipe);
            continue;
        }

        std::string accumulated;
        std::vector<char> buf(kPipeBufBytes);
        for (;;) {
            DWORD got = 0;
            BOOL ok = ::ReadFile(pipe, buf.data(), static_cast<DWORD>(buf.size()), &got, nullptr);
            if (got > 0) accumulated.append(buf.data(), got);
            if (ok) break;
            if (::GetLastError() == ERROR_MORE_DATA) continue;
            break;
        }

        std::string response = HandleRequest(accumulated);
        WriteAll(pipe, response);
        ::FlushFileBuffers(pipe);
        ::DisconnectNamedPipe(pipe);
        ::CloseHandle(pipe);
    }
}

std::string DitPipeServer::HandleRequest(const std::string& req_json) {
    try {
        std::string op = ExtractString(req_json, "op");
        if (op != "run_dit") {
            return R"({"ok":false,"err_code":"BAD_OP","err_msg":"unknown op"})";
        }
        TrtRunRequest tr;
        tr.inputs  = ParseBindingMap(req_json, "inputs");
        tr.outputs = ParseBindingMap(req_json, "outputs");

        auto t0 = std::chrono::steady_clock::now();
        engine_->RunDitIpc(tr);
        auto t1 = std::chrono::steady_clock::now();
        long long ms = std::chrono::duration_cast<std::chrono::milliseconds>(t1 - t0).count();

        std::ostringstream os;
        os << R"({"ok":true,"ms":)" << ms << "}";
        return os.str();
    } catch (const std::exception& e) {
        std::ostringstream os;
        os << R"({"ok":false,"err_code":"RUN_DIT","err_msg":")";
        // crude string escape
        for (char c : std::string(e.what())) {
            if (c == '"') os << "\\\"";
            else if (c == '\\') os << "\\\\";
            else if (static_cast<unsigned char>(c) < 0x20) os << ' ';
            else os << c;
        }
        os << R"("})";
        return os.str();
    }
}

}  // namespace chthonic
