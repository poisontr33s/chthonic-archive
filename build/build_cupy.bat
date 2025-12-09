@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
set CUDA_PATH=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.0
set CUPY_CUDA_VERSION=130
set CUPY_NVCC_GENERATE_CODE=arch=compute_89,code=sm_89
set CUPY_USE_NVRTC=1
cd /d C:\Users\erdno\chthonic-archive\build\cupy
C:\Users\erdno\chthonic-archive\mas_mcp\.venv\Scripts\pip.exe install -v --no-build-isolation .
