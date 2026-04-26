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

lines = TARGET.read_text().splitlines(keepends=True)

MARKER = "import flash_attn_2_cuda as flash_attn_gpu"
patch_idx = None
for i, line in enumerate(lines):
    if MARKER in line and not line.lstrip().startswith("#"):
        patch_idx = i
        break

if patch_idx is None:
    print(f"SKIP: pattern not found in {TARGET} — already patched or different version")
    sys.exit(0)

original_line = lines[patch_idx]
# Detect leading whitespace of the target line
indent = len(original_line) - len(original_line.lstrip())
pad = " " * indent

replacement = (
    f"{pad}try:\n"
    f"{pad}    import flash_attn_2_cuda as flash_attn_gpu\n"
    f"{pad}except ImportError:\n"
    f"{pad}    flash_attn_gpu = None  # Python-only mode; CUDA kernels not compiled\n"
)

lines[patch_idx] = replacement
TARGET.write_text("".join(lines))
print(f"PATCHED: {TARGET} (line {patch_idx + 1}, indent={indent})")
print("flash_attn CUDA import is now optional (Python-only mode active)")
