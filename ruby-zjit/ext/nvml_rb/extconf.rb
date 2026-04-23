require 'mkmf'

# nvml_rb — NVIDIA Management Library: power, thermals, clocks, utilization
# nvml.h ships inside the CUDA toolkit at CUDA_PATH/include/nvml.h
# Library:
#   Linux : libnvidia-ml  (driver-provided, stub in CUDA_PATH/lib64/stubs/)
#   Win32 : nvml.lib      (CUDA_PATH/lib/x64/nvml.lib)

cuda_base = ENV['CUDA_PATH'] ||
            (Dir.exist?('/usr/local/cuda') ? '/usr/local/cuda' : nil) ||
            Dir.glob('/usr/local/cuda-*').sort.last ||
            '/usr/local/cuda'

$INCFLAGS += " -I#{cuda_base}/include"

$LIBPATH = [
  "#{cuda_base}/lib64",
  "#{cuda_base}/lib64/stubs",   # Linux stub .so for link-time resolution
  "#{cuda_base}/lib/x64",
  '/usr/lib64',
  '/usr/lib/x86_64-linux-gnu',
].compact + $LIBPATH

# Win32: nvml.lib; Linux: libnvidia-ml.so (driver provides at runtime)
nvml_lib = RUBY_PLATFORM =~ /mswin|mingw/ ? 'nvml' : 'nvidia-ml'
$LOCAL_LIBS += " -l#{nvml_lib}"

unless find_header('nvml.h', "#{cuda_base}/include")
  abort "Cannot find nvml.h — expected at #{cuda_base}/include/nvml.h\n" \
        "Install CUDA toolkit or set CUDA_PATH"
end

create_makefile('nvml_rb')
