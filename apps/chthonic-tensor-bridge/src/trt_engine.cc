#include "trt_engine.h"

#include <windows.h>     // SecureZeroMemory (used to wipe key + plaintext)
#include <NvInfer.h>
#include <NvInferRuntime.h>
#include <cuda_runtime.h>

#include <cstring>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

#include "win32_crypto.h"

namespace chthonic {
namespace {

// ─── TRT logger ──────────────────────────────────────────────────────────────

class TrtLogger : public nvinfer1::ILogger {
public:
    void log(Severity severity, const char* msg) noexcept override {
        // Drop INFO + VERBOSE; surface WARNING and above only.
        if (severity > Severity::kWARNING) return;
        const char* tag = "TRT";
        switch (severity) {
            case Severity::kINTERNAL_ERROR: tag = "TRT-FATAL"; break;
            case Severity::kERROR:          tag = "TRT-ERR";   break;
            case Severity::kWARNING:        tag = "TRT-WARN";  break;
            default: break;
        }
        std::cerr << "[" << tag << "] " << msg << std::endl;
    }
};

TrtLogger& Logger() {
    static TrtLogger instance;
    return instance;
}

// ─── helpers ─────────────────────────────────────────────────────────────────

[[noreturn]] void ThrowCuda(const char* op, cudaError_t err) {
    std::ostringstream os;
    os << "CUDA op '" << op << "' failed: "
       << cudaGetErrorName(err) << " (" << static_cast<int>(err) << ") "
       << cudaGetErrorString(err);
    throw std::runtime_error(os.str());
}

void CheckCuda(cudaError_t err, const char* op) {
    if (err != cudaSuccess) ThrowCuda(op, err);
}

std::vector<std::uint8_t> HexDecode(const std::string& hex) {
    if (hex.size() % 2 != 0) {
        throw std::runtime_error("hex string has odd length: '" + hex + "'");
    }
    std::vector<std::uint8_t> out;
    out.reserve(hex.size() / 2);
    auto nibble = [](char c) -> int {
        if (c >= '0' && c <= '9') return c - '0';
        if (c >= 'a' && c <= 'f') return c - 'a' + 10;
        if (c >= 'A' && c <= 'F') return c - 'A' + 10;
        return -1;
    };
    for (std::size_t i = 0; i < hex.size(); i += 2) {
        int hi = nibble(hex[i]);
        int lo = nibble(hex[i + 1]);
        if (hi < 0 || lo < 0) {
            throw std::runtime_error("invalid hex digit in '" + hex + "'");
        }
        out.push_back(static_cast<std::uint8_t>((hi << 4) | lo));
    }
    return out;
}

// Minimal JSON field extractor for our seal.json schema (flat object only).
// Matches "key": "value" (string) and "key": value (number). Whitespace
// between is tolerated. Returns the unescaped value, or throws on missing.
std::string ExtractStringField(const std::string& json, const std::string& key) {
    std::string needle = "\"" + key + "\"";
    auto pos = json.find(needle);
    if (pos == std::string::npos) {
        throw std::runtime_error("seal.json missing field: " + key);
    }
    pos += needle.size();
    while (pos < json.size() && (json[pos] == ' ' || json[pos] == ':' || json[pos] == '\t')) ++pos;
    if (pos >= json.size() || json[pos] != '"') {
        throw std::runtime_error("seal.json field '" + key + "' is not a string");
    }
    ++pos;
    std::string out;
    while (pos < json.size() && json[pos] != '"') {
        if (json[pos] == '\\' && pos + 1 < json.size()) {
            char esc = json[pos + 1];
            if (esc == 'n') out += '\n';
            else if (esc == 't') out += '\t';
            else if (esc == '"') out += '"';
            else if (esc == '\\') out += '\\';
            else out += esc;
            pos += 2;
        } else {
            out += json[pos++];
        }
    }
    return out;
}

int ExtractIntField(const std::string& json, const std::string& key) {
    std::string needle = "\"" + key + "\"";
    auto pos = json.find(needle);
    if (pos == std::string::npos) {
        throw std::runtime_error("seal.json missing field: " + key);
    }
    pos += needle.size();
    while (pos < json.size() && (json[pos] == ' ' || json[pos] == ':' || json[pos] == '\t')) ++pos;
    std::size_t end = pos;
    while (end < json.size() && (json[end] >= '0' && json[end] <= '9')) ++end;
    if (end == pos) {
        throw std::runtime_error("seal.json field '" + key + "' is not an integer");
    }
    return std::stoi(json.substr(pos, end - pos));
}

constexpr std::size_t kCudaIpcHandleSize = 64;

}  // namespace

// ─── SealManifest parser ─────────────────────────────────────────────────────

SealManifest ParseSealManifest(const std::string& seal_json) {
    SealManifest m;
    m.version = ExtractIntField(seal_json, "version");
    m.kdf     = ExtractStringField(seal_json, "kdf");
    m.aead    = ExtractStringField(seal_json, "aead");
    std::string aad_str = ExtractStringField(seal_json, "aad");
    m.aad.assign(aad_str.begin(), aad_str.end());
    m.salt    = HexDecode(ExtractStringField(seal_json, "salt_hex"));
    m.nonce   = HexDecode(ExtractStringField(seal_json, "nonce_hex"));
    m.hw_fp_sha256_hex          = ExtractStringField(seal_json, "hw_fp_sha256_hex");
    m.master_secret_sha256_hex  = ExtractStringField(seal_json, "master_secret_sha256_hex");
    m.target_sm  = ExtractStringField(seal_json, "target_sm");
    m.model_id   = ExtractStringField(seal_json, "model_id");

    if (m.version != 1) {
        throw std::runtime_error(
            "unsupported seal version " + std::to_string(m.version) +
            "; expected 1");
    }
    if (m.kdf != "HKDF-SHA256") {
        throw std::runtime_error("unsupported KDF in seal: " + m.kdf);
    }
    if (m.aead != "AES-256-GCM") {
        throw std::runtime_error("unsupported AEAD in seal: " + m.aead);
    }
    return m;
}

// ─── OpenedIpcHandle ─────────────────────────────────────────────────────────

void TrtEngine::OpenedIpcHandle::close() noexcept {
    if (base) {
        // Best-effort close. If this fails the VRAM region leaks until the
        // producer's process exits — surface to stderr for debugging.
        cudaError_t err = cudaIpcCloseMemHandle(base);
        if (err != cudaSuccess) {
            std::cerr << "[trt-engine] cudaIpcCloseMemHandle failed: "
                      << cudaGetErrorName(err) << " ("
                      << cudaGetErrorString(err) << ")" << std::endl;
        }
        base = nullptr;
    }
}

// ─── TrtEngine ───────────────────────────────────────────────────────────────

TrtEngine::TrtEngine(
    const std::vector<std::uint8_t>& encrypted_engine_bytes,
    const SealManifest& manifest,
    const std::vector<std::uint8_t>& hw_fingerprint,
    const std::string& master_secret) {

    // ── 1. Fast-fail seal verification (cheap; avoids opaque AES failure) ──
    if (Sha256Hex(hw_fingerprint) != manifest.hw_fp_sha256_hex) {
        throw std::runtime_error(
            "hardware fingerprint mismatch — GPU or motherboard changed since "
            "forge. Re-run flux-engine-forge to reseal.");
    }
    std::vector<std::uint8_t> secret_bytes(
        master_secret.begin(), master_secret.end());
    if (Sha256Hex(secret_bytes) != manifest.master_secret_sha256_hex) {
        throw std::runtime_error(
            "master secret mismatch — wrong secret supplied via setMasterSecret.");
    }

    // ── 2. HKDF-derive the AES-GCM key ────────────────────────────────────
    std::vector<std::uint8_t> ikm;
    ikm.reserve(hw_fingerprint.size() + secret_bytes.size());
    ikm.insert(ikm.end(), hw_fingerprint.begin(), hw_fingerprint.end());
    ikm.insert(ikm.end(), secret_bytes.begin(), secret_bytes.end());
    static const std::vector<std::uint8_t> kHkdfInfo = []{
        const char* s = "chthonic-flux-engine/v1";
        return std::vector<std::uint8_t>(s, s + std::strlen(s));
    }();
    std::vector<std::uint8_t> key = HkdfSha256(ikm, manifest.salt, kHkdfInfo, 32);
    // Wipe the IKM after derivation — it contained the secret.
    if (!ikm.empty()) ::SecureZeroMemory(ikm.data(), ikm.size());

    // ── 3. AES-256-GCM decrypt the engine ─────────────────────────────────
    std::vector<std::uint8_t> engine_plaintext;
    try {
        engine_plaintext = AesGcm256Decrypt(
            key, manifest.nonce, encrypted_engine_bytes, manifest.aad);
    } catch (...) {
        ::SecureZeroMemory(key.data(), key.size());
        throw;
    }
    ::SecureZeroMemory(key.data(), key.size());

    // ── 4. Shared init (TRT runtime + engine + context + stream) ──────────
    InitializeFromPlaintext(engine_plaintext);

    // Wipe the plaintext now that the engine is resident in VRAM.
    ::SecureZeroMemory(engine_plaintext.data(), engine_plaintext.size());
}

TrtEngine::TrtEngine(const std::vector<std::uint8_t>& plaintext_engine_bytes) {
    // Crypto-free lane. No hardware binding, no AES, no HKDF.
    // The bridge took the path of plaintext-on-disk; trust the operator.
    InitializeFromPlaintext(plaintext_engine_bytes);
}

void TrtEngine::InitializeFromPlaintext(
    const std::vector<std::uint8_t>& plaintext) {

    runtime_ = nvinfer1::createInferRuntime(Logger());
    if (!runtime_) {
        throw std::runtime_error("nvinfer1::createInferRuntime returned null");
    }
    engine_ = runtime_->deserializeCudaEngine(plaintext.data(), plaintext.size());
    if (!engine_) {
        delete runtime_;
        runtime_ = nullptr;
        throw std::runtime_error(
            "ICudaEngine::deserializeCudaEngine returned null (engine bytes "
            "do not parse — wrong TRT version or wrong SM target?)");
    }

    context_ = engine_->createExecutionContext();
    if (!context_) {
        delete engine_;
        delete runtime_;
        engine_ = nullptr;
        runtime_ = nullptr;
        throw std::runtime_error("createExecutionContext returned null");
    }

    CheckCuda(
        cudaStreamCreateWithFlags(&stream_, cudaStreamNonBlocking),
        "cudaStreamCreateWithFlags");
}

TrtEngine::~TrtEngine() {
    if (stream_) cudaStreamDestroy(stream_);
    if (context_) delete context_;
    if (engine_) delete engine_;
    if (runtime_) delete runtime_;
}

int TrtEngine::NumIoTensors() const noexcept {
    std::lock_guard<std::mutex> lock(mu_);
    return engine_ ? engine_->getNbIOTensors() : 0;
}

std::vector<std::string> TrtEngine::IoTensorNames() const {
    std::lock_guard<std::mutex> lock(mu_);
    std::vector<std::string> out;
    if (!engine_) return out;
    int n = engine_->getNbIOTensors();
    out.reserve(static_cast<std::size_t>(n));
    for (int i = 0; i < n; ++i) {
        out.emplace_back(engine_->getIOTensorName(i));
    }
    return out;
}

void TrtEngine::RunDitIpc(const TrtRunRequest& req) {
    std::lock_guard<std::mutex> lock(mu_);
    if (!engine_ || !context_) {
        throw std::runtime_error("RunDitIpc called on uninitialized engine");
    }

    // RAII container for every IPC mapping we make this call -- guarantees
    // cudaIpcCloseMemHandle even if TRT execute throws.
    std::vector<OpenedIpcHandle> open_guards;
    open_guards.reserve(req.inputs.size() + req.outputs.size());

    auto bind = [&](const std::string& name, const IpcBinding& b, bool is_input) {
        if (b.handle_bytes.size() != kCudaIpcHandleSize) {
            throw std::runtime_error(
                "IPC handle for tensor '" + name + "' has size " +
                std::to_string(b.handle_bytes.size()) + "; expected " +
                std::to_string(kCudaIpcHandleSize));
        }
        cudaIpcMemHandle_t handle{};
        std::memcpy(&handle, b.handle_bytes.data(), kCudaIpcHandleSize);

        void* base = nullptr;
        cudaError_t err = cudaIpcOpenMemHandle(
            &base, handle, cudaIpcMemLazyEnablePeerAccess);
        if (err != cudaSuccess) {
            ThrowCuda(("cudaIpcOpenMemHandle(" + name + ")").c_str(), err);
        }
        open_guards.emplace_back(base);
        void* tensor_ptr = static_cast<char*>(base) + b.storage_offset;

        if (is_input) {
            // Dynamic shapes — engine was compiled with a profile that pins
            // these at the 1024x1024 / 22-step values, but we still must call
            // setInputShape if any dim is dynamic.
            nvinfer1::Dims dims{};
            dims.nbDims = static_cast<int32_t>(b.shape.size());
            for (int i = 0; i < dims.nbDims; ++i) {
                dims.d[i] = static_cast<int32_t>(b.shape[i]);
            }
            if (!context_->setInputShape(name.c_str(), dims)) {
                throw std::runtime_error("setInputShape failed for: " + name);
            }
        }
        if (!context_->setTensorAddress(name.c_str(), tensor_ptr)) {
            throw std::runtime_error("setTensorAddress failed for: " + name);
        }
    };

    for (const auto& [name, b] : req.inputs)  bind(name, b, true);
    for (const auto& [name, b] : req.outputs) bind(name, b, false);

    if (!context_->allInputDimensionsSpecified()) {
        throw std::runtime_error("not all input dimensions specified before enqueueV3");
    }

    if (!context_->enqueueV3(stream_)) {
        throw std::runtime_error("IExecutionContext::enqueueV3 returned false");
    }
    CheckCuda(cudaStreamSynchronize(stream_), "cudaStreamSynchronize");

    // open_guards goes out of scope here -- every mapped handle is closed.
}

}  // namespace chthonic
