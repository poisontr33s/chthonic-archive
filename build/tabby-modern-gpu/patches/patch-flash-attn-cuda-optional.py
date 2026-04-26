"""
patch-flash-attn-cuda-optional.py
Guards `import flash_attn_2_cuda as flash_attn_gpu` with try/except so that
flash_attn can be imported without the compiled CUDA kernel (Python-only mode).

Context: FLASH_ATTENTION_SKIP_CUDA_BUILD=TRUE installs the Python layer only,
but flash_attn/__init__.py → flash_attn_interface.py:15 unconditionally imports
the CUDA extension at module load time, causing ModuleNotFoundError on import.
This patch makes the CUDA extension import soft — attention functions that call
flash_attn_gpu.fwd() will raise AttributeError at call time (not import time).
For the G10 model-load gate, no attention calls are made — patch is sufficient.
For G11 generation gate, flash_attn CUDA kernel must be built.

FAF membrane: Gate 7 parallel (cessation-adjacent patch layer).
"""

import pathlib
import sys

TARGET = pathlib.Path(
    "/workspace/.venv/lib/python3.14/site-packages/flash_attn/flash_attn_interface.py"
)

if not TARGET.exists():
    print(f"SKIP: {TARGET} not found")
    sys.exit(0)

text = TARGET.read_text()

OLD = "import flash_attn_2_cuda as flash_attn_gpu"
NEW = (
    "try:\n"
    "    import flash_attn_2_cuda as flash_attn_gpu\n"
    "except ImportError:\n"
    "    flash_attn_gpu = None  # Python-only mode; CUDA kernels not compiled"
)

if OLD not in text:
    print(f"SKIP: pattern not found in {TARGET} — already patched or different version")
    sys.exit(0)

patched = text.replace(OLD, NEW, 1)
TARGET.write_text(patched)
print(f"PATCHED: {TARGET}")
print("flash_attn CUDA import is now optional (Python-only mode active)")
