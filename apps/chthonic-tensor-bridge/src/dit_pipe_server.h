// dit_pipe_server.h -- Pipe-B server thread.
//
// The satellite (Python) acts as a *client* on this pipe per DiT step. The
// bridge (C++ in the extension process) is the *server*. Each request carries
// CUDA IPC handles for the FLUX DiT inputs + output; the bridge maps them,
// calls TrtEngine::RunDitIpc, returns timing info.
//
// Lifecycle: spawned on TrtEngine load (from bridge.cc), joined on bridge
// shutdown or engine teardown. Single-threaded — only one DiT step in flight
// at a time, which matches the satellite's sequential diffusion loop.

#pragma once

#include <atomic>
#include <string>
#include <thread>

namespace chthonic {

class TrtEngine;

class DitPipeServer {
public:
    DitPipeServer(TrtEngine* engine, std::wstring pipe_name);
    ~DitPipeServer();

    DitPipeServer(const DitPipeServer&) = delete;
    DitPipeServer& operator=(const DitPipeServer&) = delete;

    void Start();
    void Stop();

private:
    void ServeLoop();
    std::string HandleRequest(const std::string& request_json);

    TrtEngine* engine_;
    std::wstring pipe_name_;
    std::thread thread_;
    std::atomic<bool> stop_{false};
};

}  // namespace chthonic
