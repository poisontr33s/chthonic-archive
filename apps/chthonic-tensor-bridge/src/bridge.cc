// bridge.cc -- N-API surface for chthonic-tensor-bridge.
//
// JS API:
//   setMasterSecret(secret: string): void
//   clearMasterSecret(): void
//   hardwareFingerprint(): { gpuUuid: string, machineGuid: string }
//   startSatellite({ uvPath, cwd, pipeName?, mmfName? }): Promise<void>
//   stopSatellite(graceful: boolean): Promise<void>
//   healthCheck(): Promise<HealthReport>
//   generate({ prompt, steps, guidance, width, height, seed }): Promise<{buffer, genMs, ...}>
//
// All ops except setMasterSecret/clearMasterSecret reject with
// ERR_FLUX_UNAUTHENTICATED when SecretSlot is empty.

#include <napi.h>
#include <windows.h>

#include <atomic>
#include <cstdint>
#include <cstring>
#include <memory>
#include <mutex>
#include <sstream>
#include <string>
#include <vector>

#include "dit_pipe_server.h"
#include "hardware_fp.h"
#include "mmf_reader.h"
#include "named_pipe_client.h"
#include "secret_slot.h"
#include "spawn_satellite.h"
#include "trt_engine.h"
#include "win32_crypto.h"

#include <fstream>

namespace {

constexpr const wchar_t kDefaultPipeNameW[]    = L"\\\\.\\pipe\\chthonic-flux";
constexpr const wchar_t kDefaultDitPipeNameW[] = L"\\\\.\\pipe\\chthonic-flux-dit";
constexpr const char    kDefaultMmfName[]      = "Local\\chthonic-flux-img";

// ── TrtEngineHolder ─────────────────────────────────────────────────────────
// Singleton that owns the deserialized TRT engine plus the DiT pipe server
// thread. Set on loadEngine(), torn down on unloadEngine() or process exit.
struct TrtEngineHolder {
    std::mutex mu;
    std::unique_ptr<chthonic::TrtEngine> engine;
    std::unique_ptr<chthonic::DitPipeServer> server;
    std::wstring dit_pipe_name = kDefaultDitPipeNameW;
};

TrtEngineHolder& Trt() {
    static TrtEngineHolder t;
    return t;
}

struct SatelliteState {
    std::mutex mu;
    chthonic::SatelliteHandles handles{};
    std::wstring pipe_name = kDefaultPipeNameW;
    std::string  mmf_name  = kDefaultMmfName;
    std::atomic<bool> running{false};
};

SatelliteState& State() {
    static SatelliteState s;
    return s;
}

std::wstring Utf8ToWide(const std::string& s) {
    if (s.empty()) return {};
    int n = ::MultiByteToWideChar(CP_UTF8, 0, s.data(), static_cast<int>(s.size()), nullptr, 0);
    std::wstring w(static_cast<std::size_t>(n), L'\0');
    ::MultiByteToWideChar(CP_UTF8, 0, s.data(), static_cast<int>(s.size()), w.data(), n);
    return w;
}

Napi::Error MakeError(Napi::Env env, const char* code, const std::string& msg) {
    auto err = Napi::Error::New(env, msg);
    err.Set("code", Napi::String::New(env, code));
    return err;
}

bool RequireAuth(Napi::Env env) {
    if (chthonic::SecretSlot::Instance().IsSet()) return true;
    auto err = MakeError(env, "ERR_FLUX_UNAUTHENTICATED",
                         "master secret not set; call setMasterSecret() first");
    err.ThrowAsJavaScriptException();
    return false;
}

// --- Sync entrypoints ------------------------------------------------------

Napi::Value SetMasterSecret(const Napi::CallbackInfo& info) {
    Napi::Env env = info.Env();
    if (info.Length() < 1 || !info[0].IsString()) {
        Napi::TypeError::New(env, "setMasterSecret(secret: string)").ThrowAsJavaScriptException();
        return env.Undefined();
    }
    std::string s = info[0].As<Napi::String>().Utf8Value();
    if (s.size() < 32) {
        Napi::RangeError::New(env, "master secret must be >= 32 chars")
            .ThrowAsJavaScriptException();
        return env.Undefined();
    }
    chthonic::SecretSlot::Instance().Set(
        reinterpret_cast<const std::uint8_t*>(s.data()), s.size());
    // Best-effort wipe of the local std::string buffer.
    ::SecureZeroMemory(s.data(), s.size());
    return env.Undefined();
}

Napi::Value ClearMasterSecret(const Napi::CallbackInfo& info) {
    chthonic::SecretSlot::Instance().Clear();
    return info.Env().Undefined();
}

Napi::Value HardwareFingerprint(const Napi::CallbackInfo& info) {
    Napi::Env env = info.Env();
    try {
        auto fp = chthonic::QueryHardwareFingerprint();
        auto obj = Napi::Object::New(env);
        obj.Set("gpuUuid", Napi::String::New(env, fp.gpu_uuid));
        obj.Set("machineGuid", Napi::String::New(env, fp.machine_guid));
        return obj;
    } catch (const std::exception& e) {
        MakeError(env, "ERR_FLUX_HW_PROBE", e.what()).ThrowAsJavaScriptException();
        return env.Undefined();
    }
}

// --- Async workers ---------------------------------------------------------

class StartSatelliteWorker : public Napi::AsyncWorker {
public:
    StartSatelliteWorker(
        Napi::Promise::Deferred deferred,
        std::wstring uv_path,
        std::wstring args,
        std::wstring cwd,
        std::wstring pipe_name,
        std::string mmf_name)
        : Napi::AsyncWorker(deferred.Env()),
          deferred_(std::move(deferred)),
          uv_path_(std::move(uv_path)),
          args_(std::move(args)),
          cwd_(std::move(cwd)),
          pipe_name_(std::move(pipe_name)),
          mmf_name_(std::move(mmf_name)) {}

    void Execute() override {
        try {
            auto secret = chthonic::SecretSlot::Instance().CopyOut();
            if (secret.empty()) {
                SetError("ERR_FLUX_UNAUTHENTICATED: master secret not set");
                return;
            }
            auto handles = chthonic::SpawnSatelliteWithSecret(
                uv_path_, args_, cwd_, secret);
            ::SecureZeroMemory(secret.data(), secret.size());

            std::lock_guard<std::mutex> lock(State().mu);
            chthonic::CloseSatelliteHandles(State().handles);
            State().handles = handles;
            State().pipe_name = pipe_name_;
            State().mmf_name  = mmf_name_;
            State().running.store(true);
        } catch (const std::exception& e) {
            SetError(std::string("ERR_FLUX_SPAWN: ") + e.what());
        }
    }

    void OnOK() override { deferred_.Resolve(Env().Undefined()); }
    void OnError(const Napi::Error& e) override { deferred_.Reject(e.Value()); }

private:
    Napi::Promise::Deferred deferred_;
    std::wstring uv_path_, args_, cwd_, pipe_name_;
    std::string mmf_name_;
};

Napi::Value StartSatellite(const Napi::CallbackInfo& info) {
    Napi::Env env = info.Env();
    auto deferred = Napi::Promise::Deferred::New(env);

    if (!chthonic::SecretSlot::Instance().IsSet()) {
        deferred.Reject(MakeError(env, "ERR_FLUX_UNAUTHENTICATED",
                                  "master secret not set").Value());
        return deferred.Promise();
    }
    if (info.Length() < 1 || !info[0].IsObject()) {
        deferred.Reject(MakeError(env, "ERR_FLUX_ARGS",
                                  "startSatellite(opts: object) required").Value());
        return deferred.Promise();
    }
    auto opts = info[0].As<Napi::Object>();
    if (!opts.Has("uvPath") || !opts.Has("cwd")) {
        deferred.Reject(MakeError(env, "ERR_FLUX_ARGS",
                                  "opts.uvPath and opts.cwd are required").Value());
        return deferred.Promise();
    }

    std::wstring uv_path  = Utf8ToWide(opts.Get("uvPath").As<Napi::String>());
    std::wstring cwd      = Utf8ToWide(opts.Get("cwd").As<Napi::String>());
    std::wstring pipe_nm  = opts.Has("pipeName")
        ? Utf8ToWide(opts.Get("pipeName").As<Napi::String>())
        : kDefaultPipeNameW;
    std::string  mmf_nm   = opts.Has("mmfName")
        ? opts.Get("mmfName").As<Napi::String>().Utf8Value()
        : kDefaultMmfName;
    std::wstring dit_pipe_nm  = opts.Has("ditPipeName")
        ? Utf8ToWide(opts.Get("ditPipeName").As<Napi::String>())
        : kDefaultDitPipeNameW;

    // Default args: `run -m flux_satellite --pipe <a> --mmf <b> --dit-pipe <c>`
    std::wstring args = L"run -m flux_satellite --pipe \"" + pipe_nm +
                        L"\" --mmf \"" + Utf8ToWide(mmf_nm) +
                        L"\" --dit-pipe \"" + dit_pipe_nm + L"\"";

    auto* w = new StartSatelliteWorker(
        deferred, std::move(uv_path), std::move(args), std::move(cwd),
        std::move(pipe_nm), std::move(mmf_nm));
    w->Queue();
    return deferred.Promise();
}

class StopSatelliteWorker : public Napi::AsyncWorker {
public:
    StopSatelliteWorker(Napi::Promise::Deferred deferred, bool graceful)
        : Napi::AsyncWorker(deferred.Env()),
          deferred_(std::move(deferred)),
          graceful_(graceful) {}

    void Execute() override {
        try {
            if (graceful_ && State().running.load()) {
                try {
                    chthonic::PipeRoundtrip(
                        State().pipe_name,
                        R"({"op":"shutdown","graceful":true})",
                        5000);
                } catch (...) {
                    // best-effort; fall through to handle cleanup
                }
            }
            std::lock_guard<std::mutex> lock(State().mu);
            if (State().handles.process != INVALID_HANDLE_VALUE) {
                ::WaitForSingleObject(State().handles.process, graceful_ ? 5000 : 0);
                if (!graceful_) {
                    ::TerminateProcess(State().handles.process, 1);
                }
                chthonic::CloseSatelliteHandles(State().handles);
            }
            State().running.store(false);
        } catch (const std::exception& e) {
            SetError(std::string("ERR_FLUX_STOP: ") + e.what());
        }
    }

    void OnOK() override { deferred_.Resolve(Env().Undefined()); }
    void OnError(const Napi::Error& e) override { deferred_.Reject(e.Value()); }

private:
    Napi::Promise::Deferred deferred_;
    bool graceful_;
};

Napi::Value StopSatellite(const Napi::CallbackInfo& info) {
    Napi::Env env = info.Env();
    auto deferred = Napi::Promise::Deferred::New(env);
    bool graceful = info.Length() > 0 && info[0].IsBoolean()
        ? info[0].As<Napi::Boolean>().Value() : true;
    auto* w = new StopSatelliteWorker(deferred, graceful);
    w->Queue();
    return deferred.Promise();
}

class HealthWorker : public Napi::AsyncWorker {
public:
    explicit HealthWorker(Napi::Promise::Deferred deferred)
        : Napi::AsyncWorker(deferred.Env()), deferred_(std::move(deferred)) {}

    void Execute() override {
        try {
            response_ = chthonic::PipeRoundtrip(
                State().pipe_name, R"({"op":"health"})", 5000);
        } catch (const std::exception& e) {
            SetError(std::string("ERR_FLUX_HEALTH: ") + e.what());
        }
    }

    void OnOK() override {
        Napi::Env env = Env();
        auto obj = Napi::Object::New(env);
        obj.Set("raw", Napi::String::New(env, response_));
        deferred_.Resolve(obj);
    }
    void OnError(const Napi::Error& e) override { deferred_.Reject(e.Value()); }

private:
    Napi::Promise::Deferred deferred_;
    std::string response_;
};

Napi::Value HealthCheck(const Napi::CallbackInfo& info) {
    Napi::Env env = info.Env();
    auto deferred = Napi::Promise::Deferred::New(env);
    if (!RequireAuth(env)) {
        deferred.Reject(MakeError(env, "ERR_FLUX_UNAUTHENTICATED",
                                  "master secret not set").Value());
        return deferred.Promise();
    }
    auto* w = new HealthWorker(deferred);
    w->Queue();
    return deferred.Promise();
}

class GenerateWorker : public Napi::AsyncWorker {
public:
    GenerateWorker(Napi::Promise::Deferred deferred, std::string payload)
        : Napi::AsyncWorker(deferred.Env()),
          deferred_(std::move(deferred)),
          payload_(std::move(payload)) {}

    void Execute() override {
        try {
            response_ = chthonic::PipeRoundtrip(State().pipe_name, payload_, 120'000);

            // Quick & dirty JSON field parse — avoids pulling in a JSON dep.
            auto get_size = [&](const char* key) -> std::size_t {
                std::string needle = std::string("\"") + key + "\":";
                auto pos = response_.find(needle);
                if (pos == std::string::npos) return 0;
                pos += needle.size();
                while (pos < response_.size() && (response_[pos] == ' ' || response_[pos] == '\t')) ++pos;
                std::size_t end = pos;
                while (end < response_.size() && (response_[end] >= '0' && response_[end] <= '9')) ++end;
                if (end == pos) return 0;
                return static_cast<std::size_t>(std::stoull(response_.substr(pos, end - pos)));
            };

            if (response_.find("\"ok\":true") == std::string::npos) {
                SetError(std::string("ERR_FLUX_SATELLITE: ") + response_);
                return;
            }
            gen_ms_  = get_size("gen_ms");
            width_   = get_size("w");
            height_  = get_size("h");
            channels_ = get_size("channels");
            std::size_t mmf_size = get_size("mmf_size");
            if (mmf_size == 0) {
                SetError("ERR_FLUX_PROTOCOL: missing mmf_size in response");
                return;
            }
            image_ = chthonic::ReadMmfPayload(State().mmf_name, mmf_size);
        } catch (const std::exception& e) {
            SetError(std::string("ERR_FLUX_GENERATE: ") + e.what());
        }
    }

    void OnOK() override {
        Napi::Env env = Env();
        auto out = Napi::Object::New(env);
        out.Set("buffer", Napi::Buffer<std::uint8_t>::Copy(env, image_.data(), image_.size()));
        out.Set("genMs", Napi::Number::New(env, static_cast<double>(gen_ms_)));
        out.Set("width", Napi::Number::New(env, static_cast<double>(width_)));
        out.Set("height", Napi::Number::New(env, static_cast<double>(height_)));
        out.Set("channels", Napi::Number::New(env, static_cast<double>(channels_)));
        deferred_.Resolve(out);
    }
    void OnError(const Napi::Error& e) override { deferred_.Reject(e.Value()); }

private:
    Napi::Promise::Deferred deferred_;
    std::string payload_;
    std::string response_;
    std::vector<std::uint8_t> image_;
    std::size_t gen_ms_ = 0;
    std::size_t width_ = 0, height_ = 0, channels_ = 0;
};

std::string BuildGeneratePayload(const Napi::Object& opts) {
    auto get_string = [&](const char* key, const std::string& fallback) {
        if (!opts.Has(key)) return fallback;
        return opts.Get(key).As<Napi::String>().Utf8Value();
    };
    auto get_num = [&](const char* key, double fallback) -> double {
        if (!opts.Has(key)) return fallback;
        return opts.Get(key).As<Napi::Number>().DoubleValue();
    };
    auto escape = [](const std::string& s) {
        std::string out;
        out.reserve(s.size() + 8);
        for (char c : s) {
            switch (c) {
                case '"':  out += "\\\""; break;
                case '\\': out += "\\\\"; break;
                case '\b': out += "\\b";  break;
                case '\f': out += "\\f";  break;
                case '\n': out += "\\n";  break;
                case '\r': out += "\\r";  break;
                case '\t': out += "\\t";  break;
                default:
                    if (static_cast<unsigned char>(c) < 0x20) {
                        char buf[8];
                        std::snprintf(buf, sizeof(buf), "\\u%04x",
                                      static_cast<unsigned int>(c));
                        out += buf;
                    } else {
                        out += c;
                    }
            }
        }
        return out;
    };

    std::ostringstream os;
    os << "{\"op\":\"generate\","
       << "\"prompt\":\"" << escape(get_string("prompt", "")) << "\","
       << "\"steps\":"    << static_cast<int>(get_num("steps", 22))     << ","
       << "\"guidance\":" << get_num("guidance", 3.5)                   << ","
       << "\"width\":"    << static_cast<int>(get_num("width", 1024))   << ","
       << "\"height\":"   << static_cast<int>(get_num("height", 1024))  << ","
       << "\"seed\":"     << static_cast<long long>(get_num("seed", 0)) << ","
       << "\"req_id\":\"" << ::GetTickCount64() << "\"}";
    return os.str();
}

Napi::Value Generate(const Napi::CallbackInfo& info) {
    Napi::Env env = info.Env();
    auto deferred = Napi::Promise::Deferred::New(env);
    if (!chthonic::SecretSlot::Instance().IsSet()) {
        deferred.Reject(MakeError(env, "ERR_FLUX_UNAUTHENTICATED",
                                  "master secret not set; call setMasterSecret() first").Value());
        return deferred.Promise();
    }
    if (info.Length() < 1 || !info[0].IsObject()) {
        deferred.Reject(MakeError(env, "ERR_FLUX_ARGS",
                                  "generate(req: object) required").Value());
        return deferred.Promise();
    }
    std::string payload = BuildGeneratePayload(info[0].As<Napi::Object>());
    auto* w = new GenerateWorker(deferred, std::move(payload));
    w->Queue();
    return deferred.Promise();
}

// ── LoadEngine ──────────────────────────────────────────────────────────────
// Reads .engine.enc + .seal.json, decrypts via SecretSlot, deserializes a
// TensorRT ICudaEngine in this process, and starts the DiT Pipe-B server so
// the Python satellite can issue runDit requests per diffusion step.
//
// JS: bridge.loadEngine({ enginePath, sealPath, ditPipeName? }): Promise<{ ioTensors: string[] }>

class LoadEngineWorker : public Napi::AsyncWorker {
public:
    LoadEngineWorker(Napi::Promise::Deferred deferred,
                     std::string engine_path,
                     std::string seal_path,
                     std::wstring dit_pipe_name)
        : Napi::AsyncWorker(deferred.Env()),
          deferred_(std::move(deferred)),
          engine_path_(std::move(engine_path)),
          seal_path_(std::move(seal_path)),
          dit_pipe_name_(std::move(dit_pipe_name)) {}

    void Execute() override {
        try {
            // Read the engine file (plaintext OR ciphertext -- both are blobs)
            std::ifstream eng_in(engine_path_, std::ios::binary);
            if (!eng_in) throw std::runtime_error("cannot open " + engine_path_);
            std::vector<std::uint8_t> engine_bytes(
                (std::istreambuf_iterator<char>(eng_in)),
                std::istreambuf_iterator<char>());

            std::unique_ptr<chthonic::TrtEngine> engine;

            if (seal_path_.empty()) {
                // ── Plaintext lane: no seal, no secret, no hardware binding ──
                engine = std::make_unique<chthonic::TrtEngine>(engine_bytes);
            } else {
                // ── Encrypted lane: secret + seal manifest + hw fingerprint ──
                auto secret = chthonic::SecretSlot::Instance().CopyOut();
                if (secret.empty()) {
                    SetError("ERR_FLUX_UNAUTHENTICATED: master secret not set "
                             "(required when sealPath is provided)");
                    return;
                }
                std::string master_secret(secret.begin(), secret.end());
                ::SecureZeroMemory(secret.data(), secret.size());

                std::ifstream seal_in(seal_path_);
                if (!seal_in) throw std::runtime_error("cannot open " + seal_path_);
                std::string seal_json(
                    (std::istreambuf_iterator<char>(seal_in)),
                    std::istreambuf_iterator<char>());
                chthonic::SealManifest manifest = chthonic::ParseSealManifest(seal_json);

                auto fp = chthonic::QueryHardwareFingerprint();
                std::string hw_str = fp.gpu_uuid + "|" + fp.machine_guid;
                std::vector<std::uint8_t> hw_bytes(hw_str.begin(), hw_str.end());

                engine = std::make_unique<chthonic::TrtEngine>(
                    engine_bytes, manifest, hw_bytes, master_secret);
                ::SecureZeroMemory(master_secret.data(), master_secret.size());
            }

            io_names_ = engine->IoTensorNames();

            std::lock_guard<std::mutex> lock(Trt().mu);
            // If a server was already running, stop it before swapping engines
            if (Trt().server) Trt().server->Stop();
            Trt().engine = std::move(engine);
            Trt().dit_pipe_name = dit_pipe_name_;
            Trt().server = std::make_unique<chthonic::DitPipeServer>(
                Trt().engine.get(), dit_pipe_name_);
            Trt().server->Start();
        } catch (const std::exception& e) {
            SetError(std::string("ERR_FLUX_LOAD_ENGINE: ") + e.what());
        }
    }

    void OnOK() override {
        Napi::Env env = Env();
        auto obj = Napi::Object::New(env);
        auto arr = Napi::Array::New(env, io_names_.size());
        for (std::size_t i = 0; i < io_names_.size(); ++i) {
            arr.Set(static_cast<std::uint32_t>(i), Napi::String::New(env, io_names_[i]));
        }
        obj.Set("ioTensors", arr);
        std::string pipe_utf8;
        pipe_utf8.reserve(dit_pipe_name_.size());
        for (wchar_t wc : dit_pipe_name_) pipe_utf8.push_back(static_cast<char>(wc));
        obj.Set("ditPipeName", Napi::String::New(env, pipe_utf8));
        deferred_.Resolve(obj);
    }
    void OnError(const Napi::Error& e) override { deferred_.Reject(e.Value()); }

private:
    Napi::Promise::Deferred deferred_;
    std::string engine_path_, seal_path_;
    std::wstring dit_pipe_name_;
    std::vector<std::string> io_names_;
};

Napi::Value LoadEngine(const Napi::CallbackInfo& info) {
    Napi::Env env = info.Env();
    auto deferred = Napi::Promise::Deferred::New(env);
    if (info.Length() < 1 || !info[0].IsObject()) {
        deferred.Reject(MakeError(env, "ERR_FLUX_ARGS",
                                  "loadEngine(opts: object) required").Value());
        return deferred.Promise();
    }
    auto opts = info[0].As<Napi::Object>();
    if (!opts.Has("enginePath")) {
        deferred.Reject(MakeError(env, "ERR_FLUX_ARGS",
                                  "loadEngine: opts.enginePath required").Value());
        return deferred.Promise();
    }
    std::string engine_path = opts.Get("enginePath").As<Napi::String>().Utf8Value();
    // sealPath is OPTIONAL. Empty / missing -> plaintext lane (no secret needed).
    std::string seal_path;
    if (opts.Has("sealPath")) {
        auto v = opts.Get("sealPath");
        if (v.IsString()) {
            seal_path = v.As<Napi::String>().Utf8Value();
        }
    }
    // Only enforce the secret requirement when the caller asked for the sealed
    // lane. Plaintext lane has no auth gate -- caller chose that explicitly.
    if (!seal_path.empty() && !chthonic::SecretSlot::Instance().IsSet()) {
        deferred.Reject(MakeError(env, "ERR_FLUX_UNAUTHENTICATED",
                                  "master secret not set (required when sealPath is provided)").Value());
        return deferred.Promise();
    }
    std::wstring dit_pipe_name = opts.Has("ditPipeName")
        ? Utf8ToWide(opts.Get("ditPipeName").As<Napi::String>())
        : kDefaultDitPipeNameW;

    auto* w = new LoadEngineWorker(deferred, std::move(engine_path),
                                   std::move(seal_path), std::move(dit_pipe_name));
    w->Queue();
    return deferred.Promise();
}

// ── UnloadEngine ────────────────────────────────────────────────────────────
Napi::Value UnloadEngine(const Napi::CallbackInfo& info) {
    Napi::Env env = info.Env();
    auto deferred = Napi::Promise::Deferred::New(env);
    std::lock_guard<std::mutex> lock(Trt().mu);
    if (Trt().server) { Trt().server->Stop(); Trt().server.reset(); }
    Trt().engine.reset();
    deferred.Resolve(env.Undefined());
    return deferred.Promise();
}

Napi::Object Init(Napi::Env env, Napi::Object exports) {
    exports.Set("setMasterSecret",    Napi::Function::New(env, SetMasterSecret));
    exports.Set("clearMasterSecret",  Napi::Function::New(env, ClearMasterSecret));
    exports.Set("hardwareFingerprint",Napi::Function::New(env, HardwareFingerprint));
    exports.Set("startSatellite",     Napi::Function::New(env, StartSatellite));
    exports.Set("stopSatellite",      Napi::Function::New(env, StopSatellite));
    exports.Set("healthCheck",        Napi::Function::New(env, HealthCheck));
    exports.Set("generate",           Napi::Function::New(env, Generate));
    exports.Set("loadEngine",         Napi::Function::New(env, LoadEngine));
    exports.Set("unloadEngine",       Napi::Function::New(env, UnloadEngine));
    return exports;
}

}  // namespace

NODE_API_MODULE(chthonic_tensor_bridge, Init)
