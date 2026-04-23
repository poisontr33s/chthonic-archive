require 'mkmf'

# nvrtc_rb — NVIDIA Runtime Compilation: compile CUDA C strings to PTX at runtime
# Enables Ruby-driven GPU kernel authoring without offline nvcc.
# nvrtc.h ships with the CUDA toolkit alongside cuda_runtime_api.h.
# Library: libnvrtc.so (Linux) / nvrtc64_*.dll (Win32, import lib in CUDA lib/x64/)

cuda_base = ENV['CUDA_PATH'] ||
            (Dir.exist?('/usr/local/cuda') ? '/usr/local/cuda' : nil) ||
            Dir.glob('/usr/local/cuda-*').sort.last ||
            '/usr/local/cuda'

$INCFLAGS += " -I#{cuda_base}/include"

$LIBPATH = [
  "#{cuda_base}/lib64",
  "#{cuda_base}/lib/x64",
  '/usr/lib64',
  '/usr/lib/x86_64-linux-gnu',
].compact + $LIBPATH

$LOCAL_LIBS += ' -lnvrtc'

unless find_header('nvrtc.h', "#{cuda_base}/include")
  abort "Cannot find nvrtc.h — expected at #{cuda_base}/include/nvrtc.h\n" \
        "Install CUDA toolkit (nvrtc component) or set CUDA_PATH"
end

unless find_library('nvrtc', 'nvrtcVersion',
                    "#{cuda_base}/lib64", "#{cuda_base}/lib/x64")
  abort "Cannot find libnvrtc — check CUDA installation (nvrtc component)"
end

create_makefile('nvrtc_rb')
