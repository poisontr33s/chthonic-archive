require 'mkmf'

# cuda_rb — CUDA runtime device query extension
# Version-agnostic: picks the latest CUDA toolkit found, or uses CUDA_PATH env.
# On Linux: /usr/local/cuda (symlink managed by NVIDIA installer)
# On Win32 (MSYS2): set CUDA_PATH, or auto-detects latest under
#   C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v*

cuda_base = ENV['CUDA_PATH'] ||
            (Dir.exist?('/usr/local/cuda') ? '/usr/local/cuda' : nil) ||
            Dir.glob('/usr/local/cuda-*').sort.last ||
            abort('Cannot find CUDA — set CUDA_PATH environment variable')

$INCFLAGS  += " -I#{cuda_base}/include"
$LIBPATH    = ["#{cuda_base}/lib64", "#{cuda_base}/lib/x64"] + $LIBPATH
$LOCAL_LIBS += " -lcudart"

unless find_header('cuda_runtime_api.h', "#{cuda_base}/include")
  abort "Cannot find cuda_runtime_api.h under #{cuda_base}/include"
end

unless find_library('cudart', 'cudaGetDeviceCount',
                    "#{cuda_base}/lib64", "#{cuda_base}/lib/x64")
  abort "Cannot find libcudart — check CUDA installation"
end

create_makefile('cuda_rb')
