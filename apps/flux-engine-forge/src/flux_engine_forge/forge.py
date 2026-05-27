#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""FLUX.1-dev DiT -> ONNX -> trtexec (FP8 + BF16, SM89) -> AES-GCM seal.

The seal binds the engine to:
  1. The forging GPU's NVML UUID
  2. The forging machine's Windows MachineGuid
  3. A caller-supplied master_secret (>= 32 chars, read from stdin only)

All three inputs must be reproduced at unseal time. The hex hashes stored in
.seal.json let the daemon detect a mismatch with a typed error before
attempting AES decryption (which would otherwise fail opaquely).

Note: TensorRT compilation is delegated to the native trtexec.exe binary
(part of the NVIDIA TensorRT C++ SDK install) rather than the Python tensorrt
package. This bypasses the cp314 wheel gap so the forge stays on Python 3.14.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import secrets
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from cryptography.hazmat.primitives import hashes as crypto_hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

log = logging.getLogger("flux.forge")
logging.basicConfig(level=logging.INFO, format="[%(name)s] %(message)s")

HKDF_INFO: Final[bytes] = b"chthonic-flux-engine/v1"
AEAD_AAD: Final[bytes] = b"flux1-dev-sm89"
ENGINE_BASENAME: Final[str] = "flux1-dev-sm89"
SM89_CAPABILITY: Final[tuple[int, int]] = (8, 9)
MIN_FREE_GB: Final[int] = 60


# --- Preflight --------------------------------------------------------------

def run_preflight(target: str, scratch_dir: Path) -> None:
    """Strict environment check. Raises RuntimeError on any failure."""
    if target != "sm89":
        raise RuntimeError(f"unsupported target '{target}' (only sm89 is implemented)")

    if sys.platform != "win32":
        log.warning("forge tested on Windows; running on %s — proceed with caution.", sys.platform)

    _assert_cuda_present()
    _assert_sm89_gpu()
    _assert_scratch_capacity(scratch_dir)
    log.info("preflight OK")


def _assert_cuda_present() -> None:
    import re
    nvcc = shutil.which("nvcc")
    if nvcc is None:
        raise RuntimeError("nvcc not on PATH — install CUDA Toolkit (>= 12.0)")
    out = subprocess.run([nvcc, "--version"], capture_output=True, text=True, check=True)
    match = re.search(r"release\s+(\d+)\.(\d+)", out.stdout)
    if match is None:
        raise RuntimeError(f"could not parse CUDA version from nvcc output:\n{out.stdout}")
    major, minor = int(match.group(1)), int(match.group(2))
    if major < 12:
        raise RuntimeError(f"CUDA >= 12.0 required; nvcc reports {major}.{minor}")
    log.info("CUDA detected: release %d.%d (>= 12.0 satisfied)", major, minor)


def _extract_cuda_version(nvcc_output: str) -> str:
    for line in nvcc_output.splitlines():
        if "release" in line:
            return line.strip()
    return "(unknown)"


def _assert_sm89_gpu() -> None:
    import pynvml
    pynvml.nvmlInit()
    try:
        if pynvml.nvmlDeviceGetCount() < 1:
            raise RuntimeError("no NVIDIA GPU detected via NVML")
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        major, minor = pynvml.nvmlDeviceGetCudaComputeCapability(handle)
        if (major, minor) != SM89_CAPABILITY:
            name = pynvml.nvmlDeviceGetName(handle)
            raise RuntimeError(
                f"GPU 0 reports SM {major}.{minor}; SM 8.9 required (RTX 4090). "
                f"Detected: {name}"
            )
        log.info("GPU 0: %s (SM %d.%d)", pynvml.nvmlDeviceGetName(handle), major, minor)
    finally:
        pynvml.nvmlShutdown()


def _assert_scratch_capacity(scratch_dir: Path) -> None:
    scratch_dir.mkdir(parents=True, exist_ok=True)
    usage = shutil.disk_usage(scratch_dir)
    free_gb = usage.free // (1024 ** 3)
    if free_gb < MIN_FREE_GB:
        raise RuntimeError(
            f"scratch dir {scratch_dir} has only {free_gb} GB free; "
            f">= {MIN_FREE_GB} GB required for ONNX intermediates."
        )
    log.info("scratch dir %s: %d GB free", scratch_dir, free_gb)


# --- Hardware fingerprint ---------------------------------------------------

def hw_fingerprint() -> bytes:
    """Concatenate GPU UUID (NVML) and Windows MachineGuid into raw fingerprint bytes."""
    gpu_uuid = _query_gpu_uuid()
    machine_guid = _query_machine_guid()
    return gpu_uuid.encode("utf-8") + b"|" + machine_guid.encode("utf-8")


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
        value, _kind = winreg.QueryValueEx(key, "MachineGuid")
    return str(value)


# --- ONNX / TensorRT compilation -------------------------------------------

@dataclass(frozen=True)
class ForgeArtifacts:
    engine_enc_path: Path
    seal_path: Path
    onnx_path: Path


def export_dit_to_onnx(scratch_dir: Path, model_id: str) -> Path:
    import torch
    from diffusers import FluxTransformer2DModel

    # ── ONNX-friendly RMSNorm swap (nested so torch stays lazily imported) ──
    # torch.nn.RMSNorm (added in 2.4) lowers to aten::rms_norm, which the
    # legacy TorchScript exporter has no symbolic for. Replace those modules
    # with a primitive-op form before export. TensorRT pattern-matches back
    # to fused RMSNorm kernels at compile time -- no runtime perf cost.
    class _PrimitiveRMSNorm(torch.nn.Module):
        def __init__(self, original: torch.nn.Module) -> None:
            super().__init__()
            self.normalized_shape = tuple(original.normalized_shape)  # type: ignore[attr-defined]
            self.eps = float(getattr(original, "eps", 1e-6))
            self.elementwise_affine = bool(getattr(original, "elementwise_affine", True))
            self.weight = getattr(original, "weight", None)  # reused, not copied

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            dtype = x.dtype
            x32 = x.float()
            var = x32.pow(2).mean(-1, keepdim=True)
            out = (x32 * torch.rsqrt(var + self.eps)).to(dtype)
            if self.elementwise_affine and self.weight is not None:
                out = out * self.weight
            return out

    def _replace_rms_norm_in_place(module: torch.nn.Module) -> int:
        swapped = 0
        for name, child in list(module.named_children()):
            if isinstance(child, torch.nn.RMSNorm):
                setattr(module, name, _PrimitiveRMSNorm(child))
                swapped += 1
            else:
                swapped += _replace_rms_norm_in_place(child)
        return swapped

    # CPU-resident trace. FLUX bf16 weights are ~22 GB and the TorchScript tracer
    # doubles peak memory by retaining activations with autograd metadata; on a
    # 24 GB card that OOMs. Tracing on CPU uses the 64 GB system pool which has
    # plenty of room. The emitted ONNX is device-agnostic -- trtexec compiles
    # it for the GPU regardless of where tracing happened.
    log.info("loading DiT from %s (bfloat16, CPU-resident for ONNX trace)", model_id)
    dit = FluxTransformer2DModel.from_pretrained(
        model_id, subfolder="transformer", torch_dtype=torch.bfloat16
    )
    dit.eval()
    # Free any GPU allocations from earlier in the process before we even start.
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    swapped = _replace_rms_norm_in_place(dit)
    log.info("swapped %d torch.nn.RMSNorm modules for ONNX-exportable primitives", swapped)

    seq_img: Final[int] = (1024 // 8 // 2) ** 2  # patchified latent grid for 1024x1024
    seq_txt: Final[int] = 512
    dummy: dict[str, torch.Tensor] = {
        "hidden_states": torch.randn(1, seq_img, 64, dtype=torch.bfloat16),
        "encoder_hidden_states": torch.randn(1, seq_txt, 4096, dtype=torch.bfloat16),
        "pooled_projections": torch.randn(1, 768, dtype=torch.bfloat16),
        "timestep": torch.tensor([1.0], dtype=torch.bfloat16),
        "img_ids": torch.zeros(seq_img, 3, dtype=torch.bfloat16),
        "txt_ids": torch.zeros(seq_txt, 3, dtype=torch.bfloat16),
        "guidance": torch.tensor([3.5], dtype=torch.bfloat16),
    }

    onnx_path = scratch_dir / "flux1-dev.dit.onnx"
    log.info("exporting DiT -> %s (opset 19, legacy exporter, CPU trace ~5-10 min)", onnx_path)
    # dynamo=False forces the legacy TorchScript exporter (broader op coverage
    # than the v2.11 dynamo path; handles primitive RMSNorm cleanly).
    # inference_mode kills autograd metadata so activations don't double-allocate.
    with torch.inference_mode():
        torch.onnx.export(
            dit,
            tuple(dummy.values()),
            str(onnx_path),
            opset_version=19,
            input_names=list(dummy.keys()),
            output_names=["sample"],
            dynamic_axes={
                "hidden_states": {0: "B"},
                "encoder_hidden_states": {0: "B"},
                "sample": {0: "B"},
            },
            dynamo=False,
        )
    log.info("ONNX export complete; freeing DiT from memory")
    del dit
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return onnx_path


def _locate_trtexec() -> Path:
    """Find trtexec.exe via TENSORRT_ROOT env, PATH, or standard install locations.

    The native NVIDIA TensorRT C++ SDK ships trtexec.exe in its bin/ dir.
    Python tensorrt wheels are NOT used — this is the cp314 bypass.
    """
    # 1. Explicit env var (preferred — operator points us at the SDK install)
    root_env = os.environ.get("TENSORRT_ROOT")
    if root_env:
        candidate = Path(root_env) / "bin" / ("trtexec.exe" if sys.platform == "win32" else "trtexec")
        if candidate.is_file():
            return candidate

    # 2. PATH search
    on_path = shutil.which("trtexec")
    if on_path:
        return Path(on_path)

    # 3. Standard Windows install roots — try every TensorRT-* dir under each
    if sys.platform == "win32":
        roots = [
            Path(r"C:\Program Files\NVIDIA\TensorRT"),
            Path(r"C:\Program Files\NVIDIA GPU Computing Toolkit\TensorRT"),
            Path(r"C:\Program Files\NVIDIA Corporation\TensorRT"),
        ]
        for root in roots:
            if root.is_dir():
                # Match either `TensorRT/bin/trtexec.exe` or `TensorRT-X.Y.Z.W/bin/trtexec.exe`
                direct = root / "bin" / "trtexec.exe"
                if direct.is_file():
                    return direct
                for sub in sorted(root.parent.glob(f"{root.name}-*"), reverse=True):
                    candidate = sub / "bin" / "trtexec.exe"
                    if candidate.is_file():
                        return candidate

    raise RuntimeError(
        "trtexec.exe not found.\n"
        "Install the NVIDIA TensorRT C++ SDK from https://developer.nvidia.com/tensorrt-download\n"
        "and either:\n"
        "  - set TENSORRT_ROOT=<path-to-TensorRT-X.Y.Z.W>, or\n"
        "  - add <TensorRT-X.Y.Z.W>\\bin to PATH"
    )


def build_tensorrt_engine_via_trtexec(onnx_path: Path, engine_path: Path) -> bytes:
    """Compile the DiT ONNX -> SM89 FP8 TensorRT .engine via the native trtexec.exe.

    Equivalent to the previous Python `tensorrt.Builder` path but works on Python 3.14
    where TRT has no cp314 wheels yet. trtexec ships in the TensorRT C++ SDK installer
    and is independent of Python ABI.

    Flags chosen to match the original Builder config:
      --fp8                                 -> BuilderFlag.FP8
      --bf16                                -> BuilderFlag.BF16
      --builderOptimizationLevel=5          -> config.builder_optimization_level
      --memPoolSize=workspace:8192          -> 8 GiB workspace
      --minShapes/--optShapes/--maxShapes   -> optimization profile (fixed for now)
      --noTF32                              -> we are FP8/BF16 only; no implicit TF32
    """
    trtexec = _locate_trtexec()
    seq_img = (1024 // 8 // 2) ** 2
    shapes = (
        f"hidden_states:1x{seq_img}x64,"
        f"encoder_hidden_states:1x512x4096,"
        f"pooled_projections:1x768,"
        f"timestep:1,"
        f"img_ids:{seq_img}x3,"
        f"txt_ids:512x3,"
        f"guidance:1"
    )
    args = [
        str(trtexec),
        f"--onnx={onnx_path}",
        f"--saveEngine={engine_path}",
        "--fp8",
        "--bf16",
        "--noTF32",
        "--builderOptimizationLevel=5",
        "--memPoolSize=workspace:8192",
        f"--minShapes={shapes}",
        f"--optShapes={shapes}",
        f"--maxShapes={shapes}",
        "--useCudaGraph",
    ]
    log.info("invoking trtexec: %s", trtexec)
    log.info("trtexec args: %s", " ".join(args[1:]))
    t0 = time.perf_counter()
    # Stream output to the forge's stderr so the operator can watch progress;
    # capture for return-code analysis.
    proc = subprocess.run(
        args,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    elapsed = time.perf_counter() - t0
    if proc.returncode != 0:
        log.error("trtexec failed (exit %d) after %.1f s", proc.returncode, elapsed)
        log.error("---- trtexec output (last 60 lines) ----")
        for line in proc.stdout.splitlines()[-60:]:
            log.error("trtexec: %s", line)
        raise RuntimeError(f"trtexec exited with {proc.returncode}")
    if not engine_path.is_file():
        raise RuntimeError(f"trtexec returned 0 but {engine_path} was not produced")
    engine_bytes = engine_path.read_bytes()
    log.info(
        "engine compiled via trtexec in %.1f s (%d MB)",
        elapsed, len(engine_bytes) >> 20,
    )
    return engine_bytes


# --- Cryptographic seal -----------------------------------------------------

def derive_key(hw: bytes, master_secret: str, salt: bytes) -> bytes:
    """HKDF-SHA256(hw_fingerprint || master_secret, salt, info) -> 32 bytes."""
    kdf = HKDF(
        algorithm=crypto_hashes.SHA256(),
        length=32,
        salt=salt,
        info=HKDF_INFO,
    )
    return kdf.derive(hw + master_secret.encode("utf-8"))


def seal(
    engine_plain_path: Path,
    master_secret: str,
    out_enc: Path,
    out_seal: Path,
) -> None:
    """Streaming AES-256-GCM seal.

    The high-level `AESGCM.encrypt()` has a hard 2 GiB-1 byte limit on the
    plaintext argument, so we drive the low-level `Cipher` API in 256 MB
    chunks. File layout on disk is unchanged: `[ciphertext bytes][16-byte tag]`.
    Single nonce, single tag, single GCM operation -- the chunking is purely
    on the update() call boundaries. C++ unseal side reads tag-suffix as before.
    """
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    hw = hw_fingerprint()
    salt = secrets.token_bytes(32)
    nonce = secrets.token_bytes(12)
    key = derive_key(hw, master_secret, salt)

    engine_size = engine_plain_path.stat().st_size
    log.info(
        "sealing %s via streaming GCM (%d MB plaintext)",
        engine_plain_path.name, engine_size >> 20,
    )

    cipher = Cipher(algorithms.AES(key), modes.GCM(nonce))
    encryptor = cipher.encryptor()
    encryptor.authenticate_additional_data(AEAD_AAD)

    plaintext_hasher = hashlib.sha256()
    CHUNK_SIZE: Final[int] = 1 << 28  # 256 MB
    out_enc.parent.mkdir(parents=True, exist_ok=True)
    try:
        with engine_plain_path.open("rb") as fin, out_enc.open("wb") as fout:
            while True:
                chunk = fin.read(CHUNK_SIZE)
                if not chunk:
                    break
                plaintext_hasher.update(chunk)
                fout.write(encryptor.update(chunk))
            tail = encryptor.finalize()
            if tail:
                fout.write(tail)
            fout.write(encryptor.tag)  # 16-byte GCM tag at end of file
    finally:
        del key

    ciphertext_size = out_enc.stat().st_size

    seal_doc = {
        "version": 1,
        "kdf": "HKDF-SHA256",
        "aead": "AES-256-GCM",
        "aad": AEAD_AAD.decode("ascii"),
        "salt_hex": salt.hex(),
        "nonce_hex": nonce.hex(),
        "hw_fp_sha256_hex": hashlib.sha256(hw).hexdigest(),
        "master_secret_sha256_hex": hashlib.sha256(
            master_secret.encode("utf-8")
        ).hexdigest(),
        "target_sm": "8.9",
        "model_id": "black-forest-labs/FLUX.1-dev",
        "forged_at_unix": int(time.time()),
        "engine_size_bytes": engine_size,
        "ciphertext_size_bytes": ciphertext_size,
        "plaintext_sha256_hex": plaintext_hasher.hexdigest(),
    }
    out_seal.write_text(json.dumps(seal_doc, indent=2), encoding="utf-8")
    log.info(
        "sealed engine -> %s (%d MB ciphertext)",
        out_enc, ciphertext_size >> 20,
    )
    log.info("seal manifest -> %s", out_seal)


def seal_from_bytes(
    engine_bytes: bytes,
    master_secret: str,
    out_enc: Path,
    out_seal: Path,
) -> None:
    """Convenience for tests / small payloads. Materializes a temp file and
    routes through the streaming seal(). Use seal() directly in production."""
    import tempfile
    fd, tmp = tempfile.mkstemp(suffix=".engine.plain")
    os.close(fd)
    tmp_path = Path(tmp)
    try:
        tmp_path.write_bytes(engine_bytes)
        seal(engine_plain_path=tmp_path, master_secret=master_secret,
             out_enc=out_enc, out_seal=out_seal)
    finally:
        try:
            tmp_path.unlink()
        except OSError:
            pass


def inspect_seal(seal_path: Path) -> None:
    doc = json.loads(seal_path.read_text(encoding="utf-8"))
    print(json.dumps(doc, indent=2))


# --- Top-level orchestration ------------------------------------------------

def run_forge(
    master_secret: str,
    model_id: str,
    target: str,
    out_dir: Path,
    scratch_dir: Path,
) -> ForgeArtifacts:
    run_preflight(target=target, scratch_dir=scratch_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    scratch_dir.mkdir(parents=True, exist_ok=True)

    onnx_path = export_dit_to_onnx(scratch_dir=scratch_dir, model_id=model_id)

    engine_plain = scratch_dir / f"{ENGINE_BASENAME}.engine.plain"
    build_tensorrt_engine_via_trtexec(
        onnx_path=onnx_path, engine_path=engine_plain
    )

    engine_enc = out_dir / f"{ENGINE_BASENAME}.engine.enc"
    seal_json = out_dir / f"{ENGINE_BASENAME}.seal.json"
    seal(engine_plain_path=engine_plain, master_secret=master_secret,
         out_enc=engine_enc, out_seal=seal_json)

    # Plaintext engine is no longer needed; wipe it.
    try:
        engine_plain.unlink()
    except OSError:
        log.warning("could not unlink plaintext engine at %s", engine_plain)

    return ForgeArtifacts(engine_enc_path=engine_enc, seal_path=seal_json, onnx_path=onnx_path)


def reseal_from_scratch(
    master_secret: str,
    out_dir: Path,
    scratch_dir: Path,
) -> ForgeArtifacts:
    """Skip ONNX export + trtexec. Re-run seal() on the existing
    scratch/<basename>.engine.plain. Use after a sealing-only failure to avoid
    repeating the 25-30 min trtexec compile."""
    engine_plain = scratch_dir / f"{ENGINE_BASENAME}.engine.plain"
    if not engine_plain.is_file():
        raise RuntimeError(
            f"no plaintext engine at {engine_plain}; run a full forge first"
        )
    out_dir.mkdir(parents=True, exist_ok=True)
    engine_enc = out_dir / f"{ENGINE_BASENAME}.engine.enc"
    seal_json = out_dir / f"{ENGINE_BASENAME}.seal.json"
    seal(engine_plain_path=engine_plain, master_secret=master_secret,
         out_enc=engine_enc, out_seal=seal_json)
    # Leave the plaintext on disk -- operator may want to re-seal again with
    # a new secret, and we already verified it's compile-correct. They can
    # delete it manually when satisfied (it's ~22 GB).
    log.info("reseal complete; engine.plain left in place at %s", engine_plain)
    return ForgeArtifacts(engine_enc_path=engine_enc, seal_path=seal_json, onnx_path=engine_plain)


def install_plain_only(out_dir: Path, scratch_dir: Path) -> Path:
    """Plaintext install path -- the 'make it work first' lane.

    Crypto-free: copies scratch/<basename>.engine.plain to
    out_dir/<basename>.engine.plain so the bridge can load it as raw bytes
    with no seal, no HKDF, no AES, no hardware binding. The reseal path
    stays available as opt-in for later. Decoupling crypto from the
    critical path -- it's horizontal polish, not a gatekeeper.
    """
    engine_plain_src = scratch_dir / f"{ENGINE_BASENAME}.engine.plain"
    if not engine_plain_src.is_file():
        raise RuntimeError(
            f"no plaintext engine at {engine_plain_src}; run a full forge first"
        )
    out_dir.mkdir(parents=True, exist_ok=True)
    engine_plain_dst = out_dir / f"{ENGINE_BASENAME}.engine.plain"
    src_size = engine_plain_src.stat().st_size
    log.info("installing plaintext engine: %d MB", src_size >> 20)
    # Copy not move -- keeps the scratch artifact for future reseal.
    import shutil as _sh
    _sh.copy2(engine_plain_src, engine_plain_dst)
    log.info("plaintext engine -> %s", engine_plain_dst)
    return engine_plain_dst
