#include "win32_crypto.h"

#include <windows.h>
#include <bcrypt.h>
#include <ntstatus.h>
#include <wincrypt.h>

#include <cstring>
#include <sstream>

#pragma comment(lib, "bcrypt.lib")
#pragma comment(lib, "crypt32.lib")

namespace chthonic {

namespace {

constexpr std::size_t kAesGcmTagLen = 16;
constexpr std::size_t kSha256DigestLen = 32;

class ScopedAlg {
public:
    BCRYPT_ALG_HANDLE handle = nullptr;
    ~ScopedAlg() {
        if (handle) ::BCryptCloseAlgorithmProvider(handle, 0);
    }
};

class ScopedKey {
public:
    BCRYPT_KEY_HANDLE handle = nullptr;
    ~ScopedKey() {
        if (handle) ::BCryptDestroyKey(handle);
    }
};

class ScopedHash {
public:
    BCRYPT_HASH_HANDLE handle = nullptr;
    ~ScopedHash() {
        if (handle) ::BCryptDestroyHash(handle);
    }
};

inline void Check(NTSTATUS s, const char* op) {
    if (!BCRYPT_SUCCESS(s)) {
        throw CryptoError(op, static_cast<long>(s));
    }
}

}  // namespace

std::string CryptoError::BuildMessage(const std::string& op, long status) {
    std::ostringstream os;
    os << "BCrypt op '" << op << "' failed with NTSTATUS 0x"
       << std::hex << static_cast<unsigned long>(status);
    return os.str();
}

std::vector<std::uint8_t> HkdfSha256(
    const std::vector<std::uint8_t>& ikm,
    const std::vector<std::uint8_t>& salt,
    const std::vector<std::uint8_t>& info,
    std::size_t out_len) {

    // BCRYPT_HKDF_ALGORITHM (Windows 10 1903+). We import the IKM as a
    // generic key, set the underlying hash to SHA-256, then derive with
    // salt + info as parameters.
    ScopedAlg alg;
    Check(::BCryptOpenAlgorithmProvider(
            &alg.handle, BCRYPT_HKDF_ALGORITHM, nullptr, 0),
          "BCryptOpenAlgorithmProvider(HKDF)");

    ScopedKey key;
    Check(::BCryptGenerateSymmetricKey(
            alg.handle, &key.handle, nullptr, 0,
            const_cast<PUCHAR>(ikm.data()),
            static_cast<ULONG>(ikm.size()),
            0),
          "BCryptGenerateSymmetricKey(IKM)");

    // Underlying PRF hash
    Check(::BCryptSetProperty(
            key.handle,
            BCRYPT_HKDF_HASH_ALGORITHM,
            reinterpret_cast<PUCHAR>(const_cast<wchar_t*>(BCRYPT_SHA256_ALGORITHM)),
            sizeof(BCRYPT_SHA256_ALGORITHM),
            0),
          "BCryptSetProperty(HKDF_HASH=SHA256)");

    if (!salt.empty()) {
        Check(::BCryptSetProperty(
                key.handle,
                BCRYPT_HKDF_SALT_AND_FINALIZE,
                const_cast<PUCHAR>(salt.data()),
                static_cast<ULONG>(salt.size()),
                0),
              "BCryptSetProperty(HKDF_SALT)");
    } else {
        // CNG requires SALT_AND_FINALIZE before key derivation even if salt
        // is empty; pass a single zero byte (matches RFC 5869 fallback).
        UCHAR zero = 0;
        Check(::BCryptSetProperty(
                key.handle, BCRYPT_HKDF_SALT_AND_FINALIZE, &zero, 1, 0),
              "BCryptSetProperty(HKDF_SALT empty)");
    }

    BCryptBuffer params[1] = {};
    params[0].BufferType = KDF_HKDF_INFO;
    params[0].cbBuffer = static_cast<ULONG>(info.size());
    params[0].pvBuffer = info.empty()
        ? nullptr
        : const_cast<PUCHAR>(info.data());
    BCryptBufferDesc param_desc = {};
    param_desc.ulVersion = BCRYPTBUFFER_VERSION;
    param_desc.cBuffers = info.empty() ? 0u : 1u;
    param_desc.pBuffers = params;

    std::vector<std::uint8_t> out(out_len);
    ULONG result_len = 0;
    Check(::BCryptKeyDerivation(
            key.handle,
            &param_desc,
            out.data(),
            static_cast<ULONG>(out.size()),
            &result_len,
            0),
          "BCryptKeyDerivation");
    out.resize(result_len);
    return out;
}

std::vector<std::uint8_t> AesGcm256Decrypt(
    const std::vector<std::uint8_t>& key_bytes,
    const std::vector<std::uint8_t>& nonce,
    const std::vector<std::uint8_t>& ciphertext_with_tag,
    const std::vector<std::uint8_t>& aad) {

    if (key_bytes.size() != 32) {
        throw CryptoError("AesGcm256Decrypt(key length)", -1);
    }
    if (ciphertext_with_tag.size() < kAesGcmTagLen) {
        throw CryptoError("AesGcm256Decrypt(ciphertext too short)", -1);
    }

    ScopedAlg alg;
    Check(::BCryptOpenAlgorithmProvider(
            &alg.handle, BCRYPT_AES_ALGORITHM, nullptr, 0),
          "BCryptOpenAlgorithmProvider(AES)");
    Check(::BCryptSetProperty(
            alg.handle,
            BCRYPT_CHAINING_MODE,
            reinterpret_cast<PUCHAR>(const_cast<wchar_t*>(BCRYPT_CHAIN_MODE_GCM)),
            sizeof(BCRYPT_CHAIN_MODE_GCM),
            0),
          "BCryptSetProperty(CHAIN_MODE=GCM)");

    ScopedKey key;
    Check(::BCryptGenerateSymmetricKey(
            alg.handle, &key.handle, nullptr, 0,
            const_cast<PUCHAR>(key_bytes.data()),
            static_cast<ULONG>(key_bytes.size()),
            0),
          "BCryptGenerateSymmetricKey(AES256)");

    const std::size_t ct_len = ciphertext_with_tag.size() - kAesGcmTagLen;
    const PUCHAR ct_base =
        const_cast<PUCHAR>(ciphertext_with_tag.data());
    const PUCHAR tag_ptr = ct_base + ct_len;

    BCRYPT_AUTHENTICATED_CIPHER_MODE_INFO auth_info{};
    BCRYPT_INIT_AUTH_MODE_INFO(auth_info);
    auth_info.pbNonce = const_cast<PUCHAR>(nonce.data());
    auth_info.cbNonce = static_cast<ULONG>(nonce.size());
    auth_info.pbAuthData = aad.empty()
        ? nullptr : const_cast<PUCHAR>(aad.data());
    auth_info.cbAuthData = static_cast<ULONG>(aad.size());

    // MAC context buffer required when chaining BCryptDecrypt calls for GCM.
    // GCM auth tag is at most 16 bytes; the running MAC state shares that size.
    std::uint8_t mac_context[16] = {};
    auth_info.pbMacContext = mac_context;
    auth_info.cbMacContext = sizeof(mac_context);

    std::vector<std::uint8_t> plaintext(ct_len);
    PUCHAR in_ptr  = ct_base;
    PUCHAR out_ptr = plaintext.data();

    // BCryptDecrypt's cbInput is ULONG (max ~4 GiB). Chunk at 1 GiB to stay
    // comfortably inside that range across all callers + give predictable
    // memory pressure. GCM cumulative ciphertext limit per RFC 5288 is
    // ~64 GiB (2^39 - 256 bits), so any FLUX-class engine fits.
    constexpr std::size_t kChunk = static_cast<std::size_t>(1) << 30;  // 1 GiB
    std::size_t remaining = ct_len;
    bool first_chunk = true;

    while (remaining > 0) {
        const bool is_last = (remaining <= kChunk);
        const ULONG this_chunk = is_last
            ? static_cast<ULONG>(remaining)
            : static_cast<ULONG>(kChunk);

        if (is_last) {
            // Final call: clear chain flag, attach the GCM auth tag.
            auth_info.dwFlags &= ~BCRYPT_AUTH_MODE_CHAIN_CALLS_FLAG;
            auth_info.pbTag = tag_ptr;
            auth_info.cbTag = static_cast<ULONG>(kAesGcmTagLen);
        } else {
            auth_info.dwFlags |= BCRYPT_AUTH_MODE_CHAIN_CALLS_FLAG;
            auth_info.pbTag = nullptr;
            auth_info.cbTag = 0;
        }
        if (!first_chunk) {
            // AAD is supplied only on the first call in chain mode.
            auth_info.pbAuthData = nullptr;
            auth_info.cbAuthData = 0;
        }

        ULONG out_len = 0;
        NTSTATUS s = ::BCryptDecrypt(
            key.handle,
            in_ptr, this_chunk,
            &auth_info,
            nullptr, 0,
            out_ptr, this_chunk,
            &out_len, 0);
        if (s == STATUS_AUTH_TAG_MISMATCH) {
            throw CryptoError(
                "AesGcm256Decrypt(STATUS_AUTH_TAG_MISMATCH)",
                static_cast<long>(s));
        }
        Check(s, "BCryptDecrypt(chunk)");

        in_ptr     += this_chunk;
        out_ptr    += out_len;
        remaining  -= this_chunk;
        first_chunk = false;
    }

    plaintext.resize(static_cast<std::size_t>(out_ptr - plaintext.data()));
    return plaintext;
}

std::vector<std::uint8_t> Base64Decode(const std::string& b64) {
    DWORD needed = 0;
    BOOL ok = ::CryptStringToBinaryA(
        b64.c_str(), static_cast<DWORD>(b64.size()),
        CRYPT_STRING_BASE64,
        nullptr, &needed, nullptr, nullptr);
    if (!ok || needed == 0) {
        throw CryptoError("Base64Decode(sizing)", static_cast<long>(::GetLastError()));
    }
    std::vector<std::uint8_t> out(needed);
    ok = ::CryptStringToBinaryA(
        b64.c_str(), static_cast<DWORD>(b64.size()),
        CRYPT_STRING_BASE64,
        out.data(), &needed, nullptr, nullptr);
    if (!ok) {
        throw CryptoError("Base64Decode", static_cast<long>(::GetLastError()));
    }
    out.resize(needed);
    return out;
}

std::string Base64Encode(const std::vector<std::uint8_t>& bytes) {
    DWORD needed = 0;
    BOOL ok = ::CryptBinaryToStringA(
        bytes.data(), static_cast<DWORD>(bytes.size()),
        CRYPT_STRING_BASE64 | CRYPT_STRING_NOCRLF,
        nullptr, &needed);
    if (!ok || needed == 0) {
        throw CryptoError("Base64Encode(sizing)", static_cast<long>(::GetLastError()));
    }
    std::string out(needed, '\0');
    ok = ::CryptBinaryToStringA(
        bytes.data(), static_cast<DWORD>(bytes.size()),
        CRYPT_STRING_BASE64 | CRYPT_STRING_NOCRLF,
        out.data(), &needed);
    if (!ok) {
        throw CryptoError("Base64Encode", static_cast<long>(::GetLastError()));
    }
    // CryptBinaryToStringA may include trailing NUL; trim.
    while (!out.empty() && out.back() == '\0') out.pop_back();
    return out;
}

std::string Sha256Hex(const std::vector<std::uint8_t>& bytes) {
    ScopedAlg alg;
    Check(::BCryptOpenAlgorithmProvider(
            &alg.handle, BCRYPT_SHA256_ALGORITHM, nullptr, 0),
          "BCryptOpenAlgorithmProvider(SHA256)");

    ScopedHash hash;
    Check(::BCryptCreateHash(
            alg.handle, &hash.handle, nullptr, 0, nullptr, 0, 0),
          "BCryptCreateHash");
    Check(::BCryptHashData(
            hash.handle,
            const_cast<PUCHAR>(bytes.data()),
            static_cast<ULONG>(bytes.size()),
            0),
          "BCryptHashData");

    std::uint8_t digest[kSha256DigestLen];
    Check(::BCryptFinishHash(hash.handle, digest, kSha256DigestLen, 0),
          "BCryptFinishHash");

    static const char* kHex = "0123456789abcdef";
    std::string out(kSha256DigestLen * 2, '\0');
    for (std::size_t i = 0; i < kSha256DigestLen; ++i) {
        out[i * 2]     = kHex[digest[i] >> 4];
        out[i * 2 + 1] = kHex[digest[i] & 0x0F];
    }
    return out;
}

}  // namespace chthonic
