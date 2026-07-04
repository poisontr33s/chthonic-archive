#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: sonic_vocal_probe.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
sonic_vocal_probe -- GPU audio analyzer for the sonic loop (the "receiver").

Runs a pretrained AudioSet tagger (PANNs Cnn14) on the RTX 4090. Given audio, it returns:
  - voice/music probabilities (Speech vs Singing vs Music vs Musical instrument vs Silence) --
    the honest version of the daemon's `voiceness` proxy, resolving the voice/music/silence
    "sub-between" that the 2-8 Hz amplitude-modulation heuristic collapses on.
  - a 2048-d embedding -- the dense "texture vector" the later clustering / texture index runs on.

PRIVACY: audio is processed in memory only. Nothing audio is written to disk -- only the derived
probabilities + embedding leave this process. Same contract as the daemon: scalars out, never raw audio.

Usage:
  uv run --no-sync python scripts/sonic_vocal_probe.py            # self-test on a synthetic signal
  uv run --no-sync python scripts/sonic_vocal_probe.py clip.wav   # analyze a real clip

@SID:           SCRIPT_SONIC_VOCAL_PROBE_V1
@Shabti:        CLI Script
@Purpose:       sonic_vocal_probe -- GPU audio analyzer for the sonic loop (the "receiver").
"""

# @SID: SCRIPT_SONIC_VOCAL_PROBE_V1

from __future__ import annotations

import sys
import time

import numpy as np

SR = 32000  # PANNs Cnn14 expects 32 kHz mono
TARGETS = ["Speech", "Singing", "Music", "Musical instrument", "Silence"]


def load_audio(path: str | None) -> np.ndarray:
    """Load `path` as 32 kHz mono float32, or synthesize a test signal when None."""
    if path is None:
        # Synthetic: 3 s of a 220 Hz tone (tonal / instrument-like) plus light noise.
        t = np.linspace(0, 3.0, SR * 3, endpoint=False, dtype=np.float32)
        tone = 0.3 * np.sin(2 * np.pi * 220.0 * t)
        noise = 0.02 * np.random.randn(len(t)).astype(np.float32)
        return (tone + noise).astype(np.float32)
    import librosa

    audio, _ = librosa.load(path, sr=SR, mono=True)
    return audio.astype(np.float32)


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else None

    import torch
    from panns_inference import AudioTagging

    try:
        from panns_inference import labels
    except ImportError:
        from panns_inference.config import labels

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dev_name = torch.cuda.get_device_name(0) if device == "cuda" else "cpu"
    print(f"device: {device} ({dev_name})")

    audio = load_audio(path)
    src = "synthetic test signal" if path is None else path
    print(f"audio: {len(audio) / SR:.1f}s @ {SR} Hz -- {src}")

    t0 = time.time()
    tagger = AudioTagging(checkpoint_path=None, device=device)  # downloads Cnn14 on first use
    t1 = time.time()
    clipwise, embedding = tagger.inference(audio[None, :])  # clipwise (1,527), embedding (1,2048)
    t2 = time.time()

    probs = clipwise[0]
    idx = {lab: i for i, lab in enumerate(labels)}
    print(f"\nmodel load {t1 - t0:.1f}s | inference {t2 - t1:.3f}s | embedding {embedding.shape[1]}-d")

    print("\nvoice/music read (the honest voiceness):")
    for name in TARGETS:
        if name in idx:
            print(f"  {name:<20} {probs[idx[name]]:.3f}")

    top = np.argsort(probs)[::-1][:5]
    print("\ntop-5 AudioSet tags:")
    for i in top:
        print(f"  {labels[i]:<28} {probs[i]:.3f}")

    head = np.round(embedding[0][:6], 3).tolist()
    print(f"\nembedding[:6] = {head}  (this is the texture vector clustering will use)")
    print("\nOK -- GPU audio model live; tags + embedding produced, no audio written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
