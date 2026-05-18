// trt_engine.h -- Native TensorRT engine wrapper for the C++ bridge.
//
// Owns a deserialized ICudaEngine + IExecutionContext + dedicated CUDA stream.
// Decrypts the sealed engine bytes via win32_crypto (HKDF-SHA256 + AES-256-GCM),
// then runs the DiT forward pass against caller-supplied CUDA IPC handles
// imported from the Python satellite's PyTorch tensors.
//
// Symmetric to flux_engine_forge.forge.seal() — any drift in HKDF info / AEAD
// AAD / hash order breaks unseal.

#pragma once

#include <cstdint>
#include <cuda_runtime.h>
#include <map>
#include <memory>
#include <mutex>
#include <string>
#include <vector>

// Forward-declared to avoid pulling NvInfer.h into headers that don't need it.
namespace nvinfer1 {
class IRuntime;
class ICudaEngine;
class IExecutionContext;
}  // namespace nvinfer1

namespace chthonic {

// Seal manifest as parsed from `.seal.json`. Mirrors the fields written by
// flux_engine_forge.forge.seal().
struct SealManifest {
    int version = 0;
    std::string kdf;                       // "HKDF-SHA256"
    std::string aead;                      // "AES-256-GCM"
    std::vector<std::uint8_t> aad;         // "flux1-dev-sm89" bytes
    std::vector<std::uint8_t> salt;        // 32 bytes
    std::vector<std::uint8_t> nonce;       // 12 bytes
    std::string hw_fp_sha256_hex;          // verify before decrypt
    std::string master_secret_sha256_hex;  // verify before decrypt
    std::string target_sm;                 // "8.9"
    std::string model_id;                  // "black-forest-labs/FLUX.1-dev"
};

// One IPC binding -- mirrors PyTorch's tensor.untyped_storage()._share_cuda_()
// for a single tensor. The handle bytes are RAW (NOT base64); the caller is
// responsible for decoding any wire encoding before constructing this.
struct IpcBinding {
    std::vector<std::uint8_t> handle_bytes;  // 64-byte cudaIpcMemHandle_t blob
    std::size_t storage_size = 0;             // total IPC region size in bytes
    std::size_t storage_offset = 0;           // offset within the region to tensor start
    std::vector<std::int64_t> shape;          // tensor shape
    std::string dtype;                        // "bf16" / "fp32" / ... (advisory; TRT uses engine's)
};

// All bindings needed for one FLUX DiT step. Both maps are keyed by the TRT
// IO tensor names exported from forge.py:
//   inputs:  hidden_states, encoder_hidden_states, pooled_projections,
//            timestep, img_ids, txt_ids, guidance
//   outputs: sample
struct TrtRunRequest {
    std::map<std::string, IpcBinding> inputs;
    std::map<std::string, IpcBinding> outputs;
};

// Parse seal.json text into a SealManifest. Throws std::runtime_error on
// missing / malformed fields. Hand-rolled (no external JSON dep — matches the
// existing micro-parser pattern in bridge.cc).
SealManifest ParseSealManifest(const std::string& seal_json);

class TrtEngine {
public:
    // Decrypts `encrypted_engine_bytes` via HKDF(hw_fingerprint || master_secret)
    // + AES-256-GCM, then deserializes the result into an ICudaEngine and
    // creates an IExecutionContext + a dedicated CUDA stream.
    //
    // hw_fingerprint matches what flux_engine_forge.forge.hw_fingerprint()
    // produces:  utf8(gpu_uuid) + b"|" + utf8(machine_guid).
    //
    // Throws std::runtime_error on any verification / decryption / TRT failure.
    TrtEngine(
        const std::vector<std::uint8_t>& encrypted_engine_bytes,
        const SealManifest& manifest,
        const std::vector<std::uint8_t>& hw_fingerprint,
        const std::string& master_secret);

    // Plaintext path -- bridge "make it work first" lane. No seal, no
    // hardware binding. Use only when the operator has explicitly chosen the
    // unencrypted artifact. Takes ownership of the bytes for the duration of
    // deserialization (TRT copies internally).
    explicit TrtEngine(const std::vector<std::uint8_t>& plaintext_engine_bytes);

    ~TrtEngine();

    TrtEngine(const TrtEngine&) = delete;
    TrtEngine& operator=(const TrtEngine&) = delete;

    // Map all input + output IPC handles into this process's CUDA context,
    // bind them to the execution context, run enqueueV3, synchronize, then
    // close every opened handle (RAII even on exception). The Python side's
    // PyTorch tensor for the `sample` output will see the result in its own
    // VRAM after this returns because IPC backing memory is shared.
    void RunDitIpc(const TrtRunRequest& req);

    int NumIoTensors() const noexcept;
    std::vector<std::string> IoTensorNames() const;

private:
    // RAII guard for cudaIpcOpenMemHandle. Closes on destruction so any
    // exception during binding/run still releases the VRAM mapping.
    struct OpenedIpcHandle {
        void* base = nullptr;
        OpenedIpcHandle() = default;
        explicit OpenedIpcHandle(void* b) : base(b) {}
        OpenedIpcHandle(const OpenedIpcHandle&) = delete;
        OpenedIpcHandle& operator=(const OpenedIpcHandle&) = delete;
        OpenedIpcHandle(OpenedIpcHandle&& o) noexcept : base(o.base) { o.base = nullptr; }
        OpenedIpcHandle& operator=(OpenedIpcHandle&& o) noexcept {
            if (this != &o) { close(); base = o.base; o.base = nullptr; }
            return *this;
        }
        ~OpenedIpcHandle() { close(); }
        void close() noexcept;
    };

    // Shared post-plaintext init: deserialize, create execution context, create
    // suspended CUDA stream. Both constructors funnel here.
    void InitializeFromPlaintext(const std::vector<std::uint8_t>& plaintext);

    mutable std::mutex mu_;
    nvinfer1::IRuntime* runtime_ = nullptr;
    nvinfer1::ICudaEngine* engine_ = nullptr;
    nvinfer1::IExecutionContext* context_ = nullptr;
    cudaStream_t stream_ = nullptr;
};

}  // namespace chthonic
