require 'mkmf'

# cuda_rb — CUDA runtime device query extension
# Detects CUDA_PATH from environment or common install locations.
# On Linux: /usr/local/cuda (NVIDIA official)
# On Win32 (MSYS2): set CUDA_PATH to C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.2

cuda_base = ENV['CUDA_PATH'] ||
            (Dir.exist?('/usr/local/cuda') ? '/usr/local/cuda' : nil) ||
            (Dir.exist?('/usr/local/cuda-13.2') ? '/usr/local/cuda-13.2' : nil) ||
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
