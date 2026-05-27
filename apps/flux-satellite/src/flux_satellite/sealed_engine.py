#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""Decrypt a sealed FLUX engine using the operator's master secret + local hardware.

Mirrors flux_engine_forge.forge.seal() exactly. Any divergence breaks unseal.
"""
from __future__ import annotations

import hashlib
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from cryptography.hazmat.primitives import hashes as crypto_hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

log: Final[logging.Logger] = logging.getLogger("flux.sealed_engine")

HKDF_INFO: Final[bytes] = b"chthonic-flux-engine/v1"
AEAD_AAD: Final[bytes] = b"flux1-dev-sm89"


class SealVerificationError(RuntimeError):
    """Raised when the seal cannot be verified before AES decryption."""


@dataclass(frozen=True)
class UnsealedEngine:
    engine_bytes: bytes
    seal_doc: dict
    hw_fp_sha256_hex: str
    secret_sha256_hex: str


def hw_fingerprint() -> bytes:
    """Concatenate NVML GPU UUID and Windows MachineGuid as raw bytes."""
    return _query_gpu_uuid().encode("utf-8") + b"|" + _query_machine_guid().encode("utf-8")


def _query_gpu_uuid() -> str:
    import pynvml
    pynvml.nvmlInit()
    try:
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        raw = pynvml.nvmlDeviceGetUUID(handle)
        return raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
    finally:
        pynvml.nvmlShutdown()


def _query_machine_guid() -> str:
    if sys.platform != "win32":
        raise RuntimeError("MachineGuid lookup requires Windows")
    import winreg
    with winreg.OpenKey(
        winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography"
    ) as key:
        value, _ = winreg.QueryValueEx(key, "MachineGuid")
    return str(value)


def derive_key(hw: bytes, master_secret: str, salt: bytes) -> bytes:
    kdf = HKDF(
        algorithm=crypto_hashes.SHA256(),
        length=32,
        salt=salt,
        info=HKDF_INFO,
    )
    return kdf.derive(hw + master_secret.encode("utf-8"))


def verify_and_unseal(
    engine_enc_path: Path,
    seal_json_path: Path,
    master_secret: str,
) -> UnsealedEngine:
    """Decrypt a sealed engine. Raises SealVerificationError on any mismatch."""
    seal_doc = json.loads(seal_json_path.read_text(encoding="utf-8"))
    expected_version = 1
    if seal_doc.get("version") != expected_version:
        raise SealVerificationError(
            f"seal version mismatch (file={seal_doc.get('version')}, expected={expected_version})"
        )
    if seal_doc.get("aead") != "AES-256-GCM" or seal_doc.get("kdf") != "HKDF-SHA256":
        raise SealVerificationError(
            f"unsupported algorithms in seal: kdf={seal_doc.get('kdf')} aead={seal_doc.get('aead')}"
        )

    hw = hw_fingerprint()
    hw_fp_hash = hashlib.sha256(hw).hexdigest()
    secret_hash = hashlib.sha256(master_secret.encode("utf-8")).hexdigest()

    if hw_fp_hash != seal_doc["hw_fp_sha256_hex"]:
        raise SealVerificationError(
            "hardware fingerprint mismatch — GPU or motherboard changed since forge. "
            "Re-run flux-engine-forge to reseal."
        )
    if secret_hash != seal_doc["master_secret_sha256_hex"]:
        raise SealVerificationError(
            "master secret mismatch — wrong secret supplied via stdin."
        )

    salt = bytes.fromhex(seal_doc["salt_hex"])
    nonce = bytes.fromhex(seal_doc["nonce_hex"])
    ciphertext = engine_enc_path.read_bytes()

    key = derive_key(hw, master_secret, salt)
    try:
        plaintext = AESGCM(key).decrypt(nonce, ciphertext, associated_data=AEAD_AAD)
    finally:
        del key

    log.info(
        "engine unsealed (%d bytes plaintext, %d bytes ciphertext)",
        len(plaintext), len(ciphertext),
    )
    return UnsealedEngine(
        engine_bytes=plaintext,
        seal_doc=seal_doc,
        hw_fp_sha256_hex=hw_fp_hash,
        secret_sha256_hex=secret_hash,
    )
