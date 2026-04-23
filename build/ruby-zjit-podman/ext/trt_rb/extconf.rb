require 'mkmf'

# trt_rb — TensorRT version + capability probe (C++ extension)
# Requires: libnvinfer-devel (Linux) or TensorRT SDK (Win32)
# Depends on: CUDA headers (NvInfer.h includes cuda_runtime_api.h)

cuda_base = ENV['CUDA_PATH'] ||
            (Dir.exist?('/usr/local/cuda') ? '/usr/local/cuda' : '/usr/local/cuda-13.2')

trt_base  = ENV['TRT_PATH'] ||
            (Dir.exist?('/usr/include/NvInfer.h') ? '' : nil) ||
            ENV.fetch('TRT_PATH', '')

# Attempt known Win32 TRT location
if trt_base.empty? && RUBY_PLATFORM =~ /mswin|mingw/
  candidate = 'C:/Program Files/NVIDIA/TensorRT-10.16.0.72'
  trt_base  = candidate if Dir.exist?(candidate)
end

$INCFLAGS  += " -I#{cuda_base}/include"
$INCFLAGS  += " -I#{trt_base}/include" unless trt_base.empty?
$INCFLAGS  += " -I/usr/include"         # Fedora nvinfer package path

$LIBPATH    = [
  "#{cuda_base}/lib64",
  "#{cuda_base}/lib/x64",
  ("#{trt_base}/lib" unless trt_base.empty?),
  '/usr/lib64',
].compact + $LIBPATH

$LOCAL_LIBS += " -lcudart"

# nvinfer — TensorRT core library
nvinfer_lib = if RUBY_PLATFORM =~ /mswin|mingw/
               "nvinfer_10"
             else
               "nvinfer"
             end
$LOCAL_LIBS += " -l#{nvinfer_lib}"

# Enable C++17 — NvInfer.h requires it
$CXXFLAGS += " -std=c++17"

unless find_header('NvInfer.h',
                   "#{cuda_base}/include",
                   ("#{trt_base}/include" unless trt_base.empty?),
                   '/usr/include')
  abort "Cannot find NvInfer.h — install libnvinfer-devel or set TRT_PATH"
end

create_makefile('trt_rb')
