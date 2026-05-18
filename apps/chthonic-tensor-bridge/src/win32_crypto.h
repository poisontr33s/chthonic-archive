// win32_crypto.h -- BCrypt-backed HKDF-SHA256 + AES-256-GCM.
//
// Symmetric inverse of flux_engine_forge.forge.seal() in C++:
//   * HKDF(SHA256, ikm=hw_fingerprint||master_secret, salt, info) -> 32 bytes
//   * AES-256-GCM decrypt with 12-byte nonce + 16-byte tag + AAD = "flux1-dev-sm89"
//
// We use the Win32 CNG/BCrypt API (advapi32 doesn't suffice for GCM/HKDF;
// bcrypt.lib is required). No OpenSSL dependency — keeps the bridge's
// transitive surface minimal.

#pragma once

#include <cstdint>
#include <stdexcept>
#include <string>
#include <vector>

namespace chthonic {

class CryptoError : public std::runtime_error {
public:
    CryptoError(const std::string& op, long status)
        : std::runtime_error(BuildMessage(op, status)),
          op_(op),
          status_(status) {}
    long status() const noexcept { return status_; }
    const std::string& op() const noexcept { return op_; }

private:
    static std::string BuildMessage(const std::string& op, long status);
    std::string op_;
    long status_;
};

// HKDF-SHA256(ikm, salt, info) -> out_len bytes.
// Matches Python: HKDF(algorithm=hashes.SHA256(), length=out_len, salt=salt,
//                      info=info).derive(ikm)
std::vector<std::uint8_t> HkdfSha256(
    const std::vector<std::uint8_t>& ikm,
    const std::vector<std::uint8_t>& salt,
    const std::vector<std::uint8_t>& info,
    std::size_t out_len);

// AES-256-GCM decrypt. Returns plaintext on success; throws CryptoError on
// tag mismatch (BCrypt returns STATUS_AUTH_TAG_MISMATCH).
//
// The Python forge writes ciphertext = AESGCM(key).encrypt(nonce, plaintext, aad)
// where AESGCM appends the 16-byte tag to the ciphertext output. So our
// `ciphertext_with_tag` argument is the raw bytes from .engine.enc.
std::vector<std::uint8_t> AesGcm256Decrypt(
    const std::vector<std::uint8_t>& key,
    const std::vector<std::uint8_t>& nonce,
    const std::vector<std::uint8_t>& ciphertext_with_tag,
    const std::vector<std::uint8_t>& aad);

// SHA-256 hex digest of `bytes`. Used to verify hw_fp_sha256_hex and
// master_secret_sha256_hex in the seal manifest before attempting AES decrypt
// (cheap fast-fail; matches the Python sealed_engine.verify_and_unseal flow).
std::string Sha256Hex(const std::vector<std::uint8_t>& bytes);

// Base64 decode/encode via Win32 CryptStringToBinaryA / CryptBinaryToStringA.
// Used to transport raw cudaIpcMemHandle_t blobs (64 bytes) over JSON.
std::vector<std::uint8_t> Base64Decode(const std::string& b64);
std::string Base64Encode(const std::vector<std::uint8_t>& bytes);

}  // namespace chthonic
